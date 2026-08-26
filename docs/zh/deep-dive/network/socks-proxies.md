# SOCKS proxy

一个 SOCKS proxy 转发原始的 TCP（在 SOCKS5 中还有 UDP）连接，而不理解其中跑的是什么，这使它成为一种底层的、与协议无关的、把流量经由另一台主机路由出去的方式。本页涵盖 SOCKS 如何工作、SOCKS4 与 SOCKS5 的区别、SOCKS5 握手、DNS 行为，以及那件会咬伤自动化的事：Chrome 不做 SOCKS5 认证。

实际配置见 [Proxy](../../guides/proxies.md) 指南；本页是它背后的理论。

## SOCKS 与 HTTP proxy 有何不同

区别在于每种 proxy 能看到什么。一个 HTTP proxy 工作在应用层并理解 HTTP：它能读取 URL、header 和 cookie（对未加密流量而言）、在传输途中修改它们、缓存响应，并添加像 `Via` 和 `X-Forwarded-For` 这样的 header。这对过滤很有用，但也意味着你要把你的应用数据托付给运营方。

一个 SOCKS proxy 工作在应用层之下。它能看到目的地址、端口和数据量，除此之外什么都看不到。HTTP、HTTPS、SSH、WebSocket，或任何自定义协议，在它看来都一个样：在两个端点之间中转的字节。把一个 HTTPS 请求经由 SOCKS5 发出，proxy 看到的是 `example.com:443` 和一条加密的 TLS 流。它读不了 URL、header 或响应，它不添加可识别的 header，也不终结 TLS。加密隧道端到端地贯通。

SOCKS 是一个代理协议，不是一个加密协议。这个名字指的是安全的防火墙穿越，而非密码学。经由 SOCKS5 发送的未加密 HTTP，对 proxy 运营方仍然是可读的，即便这个 proxy 并非为检视它而设计。要真正的加密，你需要在其上加 TLS，或在 SOCKS 连接外面套一个加密隧道（SSH、VPN）。

!!! note "信任模型"
    对一个 HTTP proxy，你要信任运营方不记录你的历史、不窃取令牌、不修改响应。对 SOCKS5，你只需信任它转发数据包、不记录连接元数据。攻击面更小，但并非为零。

## SOCKS4 与 SOCKS5

SOCKS4 出自 NEC，诞生于 1990 年代初，没有正式的 RFC。SOCKS5 于 1996 年被标准化为 RFC 1928，以修复 SOCKS4 的局限。

| 特性 | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| 标准 | 事实标准（1992），无 RFC | RFC 1928（1996） |
| 认证 | 仅识别（USERID，无密码） | 无、用户名/密码，或 GSSAPI |
| IP 版本 | 仅 IPv4 | IPv4 和 IPv6 |
| UDP 支持 | 无 | 有（UDP ASSOCIATE） |
| DNS 解析 | 客户端侧（SOCKS4A 增加服务器侧） | 对域名走服务器侧（ATYP=0x03） |

在每一个实际场景里，SOCKS5 都是更好的选择。只有当一个 proxy 不支持 SOCKS5 时才用 SOCKS4。

## SOCKS5 握手

一个 SOCKS5 连接遵循 RFC 1928，分三个阶段：方法协商、可选的认证，然后是连接请求。

<iframe scrolling="no" src="/docs/resources/visuals/socks5-handshake.html" aria-label="The SOCKS5 handshake in real RFC 1928/1929 bytes: method negotiation, optional username/password auth, then the CONNECT request, decoded field by field" style="width: 100%; height: 860px; border: 0;" loading="lazy"></iframe>

### 阶段 1：方法协商

客户端打开一条到 proxy 的 TCP 连接，并发送协议版本（`0x05`）以及它所支持的认证方法。

```python
# 客户端 hello
[
    0x05,        # VER：版本 5
    0x02,        # NMETHODS：提供的方法数量
    0x00, 0x02,  # METHODS：无认证 (0x00) 和 用户名/密码 (0x02)
]
```

proxy 回复它所选的方法。如果它需要认证且客户端提供了 `0x02`，它就选中那个。如果没有可接受的方法被提供，它回复 `0xFF` 并关闭连接。

```python
# 服务器响应
[
    0x05,  # VER：版本 5
    0x02,  # METHOD：选择了用户名/密码
]
```

方法码（RFC 1928）：`0x00` 无认证，`0x01` GSSAPI，`0x02` 用户名/密码（RFC 1929），`0xFF` 无可接受的方法。

### 阶段 2：认证

如果 proxy 选中了 `0x02`，客户端就按 RFC 1929 发送凭据。这个子协商使用它自己的版本字节（`0x01`，而不是 `0x05`）。

```python
# 客户端认证
[
    0x01,             # VER：子协商版本 1
    len(username),    # ULEN：用户名长度（最长 255）
    *username_bytes,  # UNAME
    len(password),    # PLEN：密码长度（最长 255）
    *password_bytes,  # PASSWD
]

# 服务器响应
[
    0x01,  # VER：子协商版本 1
    0x00,  # STATUS：0 = 成功，非 0 = 失败
]
```

凭据在这次握手中以明文传输；这是 RFC 1929 固有的。对敏感环境，把 SOCKS 连接包在一个 SSH 隧道或 VPN 里。

### 阶段 3：连接请求

在认证之后（或者，如果不需要认证则立即），客户端发送命令、目的地址和端口。

```python
[
    0x05,           # VER：版本 5
    0x01,           # CMD：1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,           # RSV：保留
    0x03,           # ATYP：1=IPv4, 3=domain, 4=IPv6
    len(domain),    # 域名长度（仅 ATYP=0x03）
    *domain_bytes,  # 域名
    *port_bytes,    # 端口（2 字节，big-endian）
]
```

地址类型（ATYP）决定格式：`0x01` 是 4 字节的 IPv4，`0x04` 是 16 字节的 IPv6，`0x03` 是一个长度字节加域名。当客户端发送域名时，proxy 在它这一侧解析 DNS，这就让 DNS 不经过客户端的本地网络。

proxy 连接到目的地并回复：

```python
[
    0x05,        # VER：版本 5
    0x00,        # REP：0x00 成功，0x01-0x08 错误
    0x00,        # RSV：保留
    0x01,        # ATYP：绑定地址的地址类型
    *bind_addr,  # BND.ADDR
    *bind_port,  # BND.PORT
]
```

回复码：`0x00` 成功，`0x01` 一般失败，`0x02` 不允许，`0x03` 网络不可达，`0x04` 主机不可达，`0x05` 连接被拒绝，`0x06` TTL 过期，`0x07` 命令不支持，`0x08` 地址类型不支持。在一个成功回复之后，proxy 就双向中继数据。这次握手是二进制的，所以它高效，但不借助十六进制转储就很难读。

## UDP 支持

SOCKS5 可以通过 `UDP ASSOCIATE` 命令（CMD=0x03）代理 UDP。客户端在 TCP 控制连接上发送请求，proxy 返回一个中继地址和端口。随后客户端把 UDP 数据报发到那个中继，每个数据报前面加一个说明目的地的小 header：

```python
[
    0x00, 0x00,  # RSV：保留
    0x00,        # FRAG：分片编号（0 = 无）
    0x01,        # ATYP：地址类型
    *dst_addr,   # DST.ADDR
    *dst_port,   # DST.PORT
    *data,       # 应用数据
]
```

TCP 控制连接必须在整个关联期间保持打开；如果它关闭，proxy 就会丢弃这个 UDP 中继。

!!! warning "Chrome 不通过 SOCKS5 代理 UDP"
    即便配置了一个 SOCKS5 proxy，Chrome 也只代理 TCP。WebRTC、DNS-over-UDP 以及其他 UDP 流量会绕过 proxy，所以 WebRTC 的 IP 泄露仍有可能。设置 `options.webrtc_leak_protection = True`（它会添加 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`）来缓解它。见 [网络基础](network-fundamentals.md)。

## DNS 解析

一个常见的说法是 HTTP proxy 会泄露 DNS 而 SOCKS5 不会。在 Chrome 里，实情更具体一些。

只要配置了任何 proxy（HTTP、HTTPS 或 SOCKS5），Chrome 就会把主机名交给 proxy，而不是在本地解析它们。对一个 HTTP proxy，主机名在 `CONNECT host:443` 行里；对 SOCKS5，它在带 ATYP=0x03 的连接请求里。两种情况下都是 proxy 解析 DNS，Chrome 对被代理的流量不做本地 DNS 查询。真正的区别不在于谁解析 DNS，而在于 proxy 看到什么：一个 HTTP proxy 看到未加密请求的完整 URL 和 CONNECT 请求的主机名，而一个 SOCKS5 proxy 只看到作为不透明参数的目的主机和端口。

有一个需要注意的地方：Chrome 的 DNS 预取器仍可能为页面内容里发现的主机名发起本地查询，这会把你浏览的域名泄露给你的本地解析器。禁用 DNS 预取以防止它。

!!! note "`socks5://` 对 `socks5h://`"
    许多工具区分 `socks5://`（客户端解析 DNS）与 `socks5h://`（proxy 解析）。Chrome 对 SOCKS5 总是在 proxy 侧解析 DNS，所以无论哪种写法它的行为都像 `socks5h://`。如果你在 Pydoll 之外还用 curl、Firefox 或 Python 库，优先用 `socks5h://` 以避免那里发生 DNS 泄露。

## SOCKS5 与抗 MITM

SOCKS5 常被称为抗 MITM，在一个特定意义上它确实如此：因为它不理解 TLS，所以它没有办法去终结并重新加密一条 TLS 连接。它原封不动地中继加密字节。

一个 HTTP proxy 可以通过出示自己的证书、解密、检视或修改、再向服务器重新加密来执行 TLS 终结。那要求客户端信任 proxy 的 CA，而且它能通过证书固定和证书透明度被检测到。一个 HTTP proxy 正常的 HTTPS 行为（CONNECT）是一条不做终结的透明隧道，但那种可能性是存在的。对 SOCKS5 则不存在，因为 proxy 从不触碰应用数据。

在这里提供密码学保护的是 TLS，而不是 SOCKS5。SOCKS5 的优势是架构上的，即它既不要求也不启用 TLS 终结，而非密码学上的。

## 透过 SOCKS5 的指纹识别

SOCKS5 不会改变你浏览器的指纹。TLS ClientHello 逐字节穿过，所以服务器看到的是你确切的 JA3/JA4 指纹，HTTP/2 设置、header 顺序以及其他每一个应用层信号也是如此。SOCKS5 隐藏你的 IP，并阻止 proxy 注入 header；它对浏览器指纹或行为指纹毫无作用。要应对那些，还得处理其他各层：见 [规避技术](../../stealth/evasion-techniques.md)。

## Chrome 中的 SOCKS5 认证

Chrome 不支持 SOCKS5 的用户名/密码认证，这是一个长期存在的局限，记录在 [Chromium issue 40323993](https://issues.chromium.org/issues/40323993)。在方法协商期间，Chrome 只提供 `0x00`（无认证）；如果 proxy 需要凭据，连接会静默失败。设置 `--proxy-server=socks5://user:pass@proxy:1080` 不起作用，因为 Chrome 会忽略嵌入的凭据。

这与 HTTP proxy 认证不同。HTTP proxy 用一个 `407 Proxy Authentication Required` 状态来认证，Chrome 会通过 CDP 的 Fetch domain 把它暴露出来；Pydoll 会用你的凭据自动应答那些 `Fetch.authRequired` 事件。SOCKS5 认证发生在任何 HTTP 存在之前的一次二进制握手里，所以没有 407，没有 `Fetch.authRequired`，也没有办法让一个基于 CDP 的工具向其中注入凭据。

### Pydoll 的 SOCKS5Forwarder

标准的修复是一个本地转发器：一个跑在 localhost 上的小型 SOCKS5 服务器，它接受来自 Chrome 的无认证连接，并带着完整的认证把它们转发给远程 proxy。

<iframe scrolling="no" src="/docs/resources/visuals/socks5-forwarder.html" aria-label="The pydoll SOCKS5Forwarder bridges two handshakes: a no-auth SOCKS5 handshake to Chrome on one side and a full authenticated handshake to the remote proxy on the other, injecting the credentials Chrome cannot send" style="width: 100%; height: 900px; border: 0;" loading="lazy"></iframe>

Pydoll 在 `pydoll.utils` 中提供了 `SOCKS5Forwarder`。它是一个纯 Python、零依赖的异步实现，会处理与远程 proxy 的完整握手，包括用户名/密码认证，以及 IPv4、IPv6 和域名地址类型。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.utils import SOCKS5Forwarder


async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,   # 0 让操作系统挑选一个空闲端口
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

这个转发器绑定到 `127.0.0.1`，所以只有从你的机器才能访问到它。不要把它绑定到 `0.0.0.0`，那会把一个无认证的 SOCKS5 proxy 暴露给网络。因为一切都跑在回环接口上，它增加的延迟不到一毫秒。

!!! tip "受限环境"
    某些环境（容器、serverless、加固过的 VM）会限制绑定本地端口。用 `local_port=0` 让操作系统分配一个。如果本地绑定被完全禁止，就改用一个 HTTP CONNECT proxy，Chrome 原生支持它，并为你处理好认证（见 [Proxy](../../guides/proxies.md)）。

## 相关内容

- [HTTP/HTTPS proxy](http-proxies.md)：应用层的替代方案。
- [网络基础](network-fundamentals.md)：底下的那些层。
- [Proxy 检测](proxy-detection.md)：连 SOCKS5 proxy 也是怎么被识破的。
- [搭建一个 proxy 服务器](build-proxy.md)：自己实现一个 SOCKS5 服务器。
- [Proxy](../../guides/proxies.md)：在 Pydoll 中配置 proxy。

## 参考资料

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- Chromium issue 40323993: SOCKS5 authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC leak test - https://browserleaks.com/webrtc
