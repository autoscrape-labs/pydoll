# SOCKS 协议架构

SOCKS（SOCKet Secure）是一种运行在网络栈传输层和应用层之间的代理协议（通常被描述为 OSI 模型的第 5 层）。与解析和理解 HTTP 流量的 HTTP 代理不同，SOCKS 代理在不检查内容的情况下转发原始 TCP 和 UDP 连接。这种协议无关的设计使 SOCKS 成为注重隐私的自动化的首选：代理无需解析您的请求、注入标头或终止 TLS 连接。

本文档涵盖了 SOCKS 在协议层面的工作原理、SOCKS4 与 SOCKS5 的区别、Chrome 中的身份验证处理、DNS 解析行为，以及在 Pydoll 中的实际配置。

!!! info "模块导航"
    - [HTTP/HTTPS 代理](./http-proxies.md)：应用层代理
    - [网络基础](./network-fundamentals.md)：TCP/IP、UDP、OSI 模型
    - [网络与安全概述](./index.md)：模块介绍
    - [代理检测](./proxy-detection.md)：匿名级别和检测规避
    - [构建代理](./build-proxy.md)：从零开始实现 SOCKS5

    有关实际配置，请参阅[代理配置](../../features/configuration/proxy.md)。

## SOCKS 与 HTTP 代理的区别

根本区别在于每种代理能看到和做到什么。HTTP 代理在应用层运行，理解 HTTP：它可以读取 URL、标头、Cookie 和请求体（针对未加密流量），在传输过程中修改它们，缓存响应，并注入自己的标头，如 `Via` 和 `X-Forwarded-For`。这对内容过滤很有用，但意味着您必须信任代理运营商处理您的应用数据。

SOCKS 代理在应用层之下运行。它只能看到目标地址、端口和正在传输的数据量。它不会解析、修改甚至理解通过它流动的是什么协议。HTTP、HTTPS、FTP、SSH、WebSocket 或任何自定义协议对于 SOCKS 代理来说都是一样的：只是在两个端点之间中继的字节流。

这有一个直接的实际影响。当您通过 SOCKS5 代理发送 HTTPS 请求时，代理看到的是 `example.com:443` 和加密的 TLS 流。它无法读取 URL、标头、Cookie 或响应内容。它不会添加识别性标头。它不需要终止 TLS。加密隧道在您的浏览器和目标服务器之间是端到端的。

然而，理解 SOCKS 不提供什么同样重要。SOCKS 是一种代理协议，而不是加密协议。"SOCKet Secure"这个名称指的是安全的防火墙穿越，而非密码学安全。如果您通过 SOCKS5 代理发送未加密的 HTTP 流量，即使代理并非设计用来检查流量，代理运营商也能读取通过的字节。要实现真正的加密，您需要在 SOCKS 之上使用 TLS/HTTPS，或者用加密隧道（SSH、VPN）包裹 SOCKS 连接。

!!! note "信任模型"
    使用 HTTP 代理时，您信任代理运营商不会记录您的浏览历史、窃取令牌、修改响应或执行 MITM 攻击。使用 SOCKS5 时，您只需信任代理能正确转发数据包且不记录连接元数据。攻击面更小，但并非为零。

## SOCKS4 与 SOCKS5

SOCKS 有两个常用版本。SOCKS4 由 NEC 在 20 世纪 90 年代初开发，是一个没有 RFC 的非正式标准。SOCKS5 于 1996 年被标准化为 RFC 1928，以解决 SOCKS4 的局限性。

| 特性 | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| 标准 | 无官方 RFC（1992 年的事实标准） | RFC 1928（1996） |
| 身份验证 | 仅标识（USERID 字段，无密码） | 多种方法（无认证、用户名/密码、GSSAPI） |
| IP 版本 | 仅 IPv4 | IPv4 和 IPv6 |
| UDP 支持 | 否 | 是（UDP ASSOCIATE 命令） |
| DNS 解析 | 客户端（SOCKS4A 扩展添加了服务器端） | 使用域名时由服务器端解析（ATYP=0x03） |
| 协议支持 | 仅 TCP | TCP 和 UDP |

SOCKS5 在各方面都更优越。仅在代理不支持 SOCKS5 时才使用 SOCKS4。

## SOCKS5 握手

SOCKS5 连接过程遵循 RFC 1928，由三个阶段组成：方法协商、可选的身份验证和连接请求。

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5 as SOCKS5 Proxy
    participant Server as Target Server

    Note over Client,SOCKS5: Phase 1: Method Negotiation
    Client->>SOCKS5: Hello [VER=5, NMETHODS, METHODS]
    SOCKS5->>Client: Method Selected [VER=5, METHOD]

    Note over Client,SOCKS5: Phase 2: Authentication (if required)
    Client->>SOCKS5: Auth Request [VER=1, ULEN, UNAME, PLEN, PASSWD]
    SOCKS5->>Client: Auth Response [VER=1, STATUS]

    Note over Client,SOCKS5: Phase 3: Connection Request
    Client->>SOCKS5: Connect [VER=5, CMD=CONNECT, DST.ADDR, DST.PORT]
    SOCKS5->>Server: Establish TCP connection
    Server-->>SOCKS5: Connection established
    SOCKS5->>Client: Reply [VER=5, REP=SUCCESS, BND.ADDR, BND.PORT]

    Note over Client,Server: Data relay (proxied)
    Client->>SOCKS5: Application data
    SOCKS5->>Server: Forward data
    Server->>SOCKS5: Response data
    SOCKS5->>Client: Forward response
```

### 阶段 1：方法协商

客户端打开一个到代理的 TCP 连接，发送一个包含协议版本（SOCKS5 始终为 `0x05`）和支持的身份验证方法列表的问候消息。

```python
# Client Hello
[
    0x05,        # VER: Protocol version (5)
    0x02,        # NMETHODS: Number of methods offered
    0x00, 0x02   # METHODS: No auth (0x00) and Username/Password (0x02)
]
```

代理回复它选择的方法。如果代理需要身份验证且客户端提供了 `0x02`（用户名/密码），代理就选择它。如果没有提供可接受的方法，代理回复 `0xFF` 并关闭连接。

```python
# Server response
[
    0x05,   # VER: Protocol version (5)
    0x02    # METHOD: Username/Password selected
]
```

RFC 1928 定义的方法代码：`0x00` = 无身份验证，`0x01` = GSSAPI，`0x02` = 用户名/密码（RFC 1929），`0x03-0x7F` = IANA 分配，`0x80-0xFE` = 保留给私有方法，`0xFF` = 无可接受的方法。

### 阶段 2：身份验证

如果代理选择了方法 `0x02`，客户端按照 RFC 1929 发送凭据。子协商使用自己的版本号（`0x01`，而非 `0x05`）。

```python
# Client authentication
[
    0x01,              # VER: Subnegotiation version (1)
    len(username),     # ULEN: Username length (max 255)
    *username_bytes,   # UNAME: Username
    len(password),     # PLEN: Password length (max 255)
    *password_bytes    # PASSWD: Password
]

# Server response
[
    0x01,   # VER: Subnegotiation version (1)
    0x00    # STATUS: 0 = success, non-zero = failure
]
```

在此握手过程中，凭据以明文传输。这是 SOCKS5 协议（RFC 1929）固有的特性。对于敏感环境，请将 SOCKS 连接包裹在 SSH 隧道或 VPN 中。

### 阶段 3：连接请求

身份验证成功后（或者不需要身份验证时），客户端发送一个连接请求，指定命令、目标地址和端口。

```python
[
    0x05,          # VER: Protocol version (5)
    0x01,          # CMD: 1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,          # RSV: Reserved
    0x03,          # ATYP: 1=IPv4 (4 bytes), 3=Domain (length+name), 4=IPv6 (16 bytes)
    len(domain),   # Domain length (only for ATYP=0x03)
    *domain_bytes, # Domain name
    *port_bytes    # Port (2 bytes, big-endian)
]
```

地址类型（ATYP）决定了格式：`0x01` 表示后面跟 4 字节的 IPv4 地址，`0x04` 表示 16 字节的 IPv6 地址，`0x03` 表示一个长度字节后跟域名。当客户端发送域名（ATYP=0x03）时，代理在其侧解析 DNS，这可以防止 DNS 泄露到客户端的本地网络。

代理连接到目标并回复：

```python
[
    0x05,       # VER: Protocol version (5)
    0x00,       # REP: 0x00=success, 0x01-0x08=various errors
    0x00,       # RSV: Reserved
    0x01,       # ATYP: Address type of bound address
    *bind_addr, # BND.ADDR: Address the proxy bound to
    *bind_port  # BND.PORT: Port the proxy bound to
]
```

回复代码：`0x00` 成功，`0x01` 一般性故障，`0x02` 不允许连接，`0x03` 网络不可达，`0x04` 主机不可达，`0x05` 连接被拒绝，`0x06` TTL 过期，`0x07` 不支持的命令，`0x08` 不支持的地址类型。

成功回复后，代理开始双向中继数据。整个 SOCKS5 握手是二进制协议，比基于文本的 HTTP 更高效，但没有十六进制转储就更难调试。

## UDP 支持

SOCKS5 通过 `UDP ASSOCIATE` 命令（CMD=0x03）支持 UDP 代理。其工作方式与 TCP 代理不同：客户端通过 TCP 控制连接发送 UDP ASSOCIATE 请求，代理回复中继地址和端口。然后客户端将 UDP 数据报发送到该中继，代理将其转发到目标。

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant UDP_Server as UDP Server

    Note over Client,SOCKS5: TCP control connection (handshake + auth)
    Client->>SOCKS5: UDP ASSOCIATE request (CMD=0x03)
    SOCKS5->>Client: Relay address and port

    Note over Client,SOCKS5: UDP data transfer
    Client->>SOCKS5: UDP datagram to relay
    SOCKS5->>UDP_Server: Forward datagram
    UDP_Server->>SOCKS5: Response datagram
    SOCKS5->>Client: Forward response

    Note over Client,SOCKS5: TCP control connection stays open
```

通过中继发送的每个 UDP 数据报都包含一个带有目标地址和端口的小标头：

```python
[
    0x00, 0x00,    # RSV: Reserved
    0x00,          # FRAG: Fragment number (0 = no fragmentation)
    0x01,          # ATYP: Address type
    *dst_addr,     # DST.ADDR: Destination address
    *dst_port,     # DST.PORT: Destination port
    *data          # DATA: Application data
]
```

TCP 控制连接在 UDP 关联期间必须保持打开。如果它关闭，代理会丢弃 UDP 中继。

!!! warning "Chrome 中的 UDP"
    Chrome 不会为任何流量使用 SOCKS5 UDP ASSOCIATE。即使配置了 SOCKS5 代理，Chrome 也只代理 TCP 连接。WebRTC、DNS-over-UDP 和其他 UDP 流量不会通过 SOCKS5 代理路由。这意味着在 Chrome 中使用 SOCKS5 时仍可能存在 WebRTC IP 泄露。使用 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` 或 Pydoll 的 `webrtc_leak_protection = True` 来缓解此问题。更多详情请参阅 [网络基础：WebRTC 和 IP 泄露](./network-fundamentals.md#webrtc-and-ip-leakage)。

!!! tip "现代 UDP 代理替代方案"
    对于需要超出 Chrome SOCKS5 实现所提供的完整 UDP 支持的场景，可以考虑 Shadowsocks（带有原生 UDP 的加密类 SOCKS 协议）、WireGuard（性能出色的 VPN）或 V2Ray/VMess（具有全面 UDP 处理能力的灵活代理框架）。

## DNS 解析

一个常见的误解是 HTTP 代理会泄露 DNS 查询，而 SOCKS5 代理不会。Chrome 中的实际情况更加微妙。

当 Chrome 配置了任何代理（HTTP、HTTPS 或 SOCKS5）时，它会将主机名发送给代理，而不是在本地解析 DNS。对于 HTTP 代理，主机名出现在 `CONNECT host:443` 请求中。对于 SOCKS5，它出现在带有 ATYP=0x03（域名）的连接请求中。在这两种情况下，代理在其侧解析 DNS，Chrome 不会对代理流量进行本地 DNS 查询。

两种代理类型之间真正的 DNS 隐私差异不在于谁解析 DNS，而在于代理在应用层能看到什么。HTTP 代理能看到未加密请求的完整 URL 和 CONNECT 请求的主机名。SOCKS5 代理只能看到目标主机名和端口作为不透明的连接参数。

但是，有一个重要的注意事项：即使配置了代理，Chrome 的 DNS 预取器也可能会对页面内容中发现的主机名进行本地 DNS 查询。这可能会将您正在浏览的域名泄露给本地 DNS 解析器。要防止这种情况，请禁用 DNS 预取或使用标志 `--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"`。

!!! note "`socks5://` 与 `socks5h://`"
    Chrome 之外的许多工具区分 `socks5://`（客户端解析 DNS）和 `socks5h://`（代理解析 DNS，"h"代表 hostname）。Chrome 对 SOCKS5 始终在代理侧解析 DNS，无论您使用哪种方案，行为都类似于 `socks5h://`。但如果您在 Pydoll 之外使用 `curl`、Firefox 或 Python 库等工具，这个区别就很重要：请始终使用 `socks5h://` 以防止 DNS 泄露。

## SOCKS5 与 MITM 抵抗

SOCKS5 经常被描述为"抗 MITM"。在特定意义上这是正确的：因为 SOCKS5 不理解或与 TLS 交互，它没有机制来终止 TLS 连接并重新加密。SOCKS5 代理只是原样中继加密的字节。

相比之下，HTTP 代理可以通过向客户端提供自己的证书来执行 TLS 终止（MITM），解密流量、检查或修改内容，然后重新加密发送给服务器。这需要客户端信任代理的 CA 证书，并且可以通过证书固定和证书透明度日志检测到。HTTP 代理处理 HTTPS 的正常行为（使用 CONNECT）是创建透明隧道而不终止 TLS，但 MITM 的架构可能性是存在的。

使用 SOCKS5 时，TLS 终止在协议层面是不可能的。代理无法将自己注入 TLS 握手，因为它不解析流经的应用数据。客户端和服务器之间的端到端加密在设计上得到了保护。

值得注意的是，提供实际密码学保护的是 TLS，而不是 SOCKS5 本身。如果您通过 SOCKS5 代理发送未加密的 HTTP，代理运营商可以读取所有内容。SOCKS5 的安全优势是架构性的（它不需要也不启用 TLS 终止），而非密码学意义上的。

## TLS 和通过 SOCKS5 的浏览器 fingerprinting

一个需要理解的重要局限：SOCKS5 不会改变浏览器的 fingerprint。TLS 握手（ClientHello）逐字节通过 SOCKS5 代理传递，这意味着目标服务器能看到浏览器的确切 JA3/JA4 fingerprint。HTTP/2 SETTINGS 帧、浏览器特有的标头排序以及所有其他应用层 fingerprinting 信号同样如此。

SOCKS5 隐藏了您的 IP 地址并防止代理注入识别性标头。但它对任何形式的浏览器或行为 fingerprinting 都没有帮助。要实现完整的规避策略，您需要在多个层面应对 fingerprinting。详情请参阅[规避技术](../fingerprinting/evasion-techniques.md)。

## Chrome 中的 SOCKS5 身份验证

Chrome 不支持 SOCKS5 用户名/密码身份验证。这是一个长期存在的限制，跟踪为 [Chromium Issue #40323993](https://issues.chromium.org/issues/40323993)。当 Chrome 执行 SOCKS5 方法协商时，它只提供方法 `0x00`（无身份验证）。如果代理需要身份验证，连接会静默失败。

这与 HTTP 代理身份验证有本质区别。HTTP 代理通过 HTTP 状态码（`407 Proxy Authentication Required`）进行身份验证，Chrome 通过 CDP 中的 Fetch 域来处理。Pydoll 拦截这些 `Fetch.authRequired` 事件并自动使用存储的凭据响应。而 SOCKS5 身份验证发生在会话层的二进制协议握手期间，在任何 HTTP 流量存在之前。没有 HTTP 407，没有 `Fetch.authRequired` 事件，基于 CDP 的工具也无法将凭据注入此过程。

配置 `--proxy-server=socks5://user:pass@proxy:1080` 不会生效。Chrome 会静默忽略嵌入的凭据。

### Pydoll 的 SOCKS5Forwarder

标准解决方案是本地代理转发器：一个运行在 localhost 上的轻量级 SOCKS5 服务器，接受来自 Chrome 的未认证连接，并将其转发到带有完整身份验证的远程代理。

```mermaid
sequenceDiagram
    participant Chrome
    participant Forwarder as Local Forwarder<br/>(127.0.0.1:1081)
    participant Remote as Remote SOCKS5 Proxy<br/>(proxy:1080)
    participant Server as Destination Server

    Note over Chrome,Forwarder: No authentication
    Chrome->>Forwarder: SOCKS5 Hello [methods: 0x00]
    Forwarder->>Chrome: Method selected [0x00]
    Chrome->>Forwarder: CONNECT example.com:443

    Note over Forwarder,Remote: With authentication
    Forwarder->>Remote: SOCKS5 Hello [methods: 0x02]
    Remote->>Forwarder: Method selected [0x02]
    Forwarder->>Remote: Auth [username, password]
    Remote->>Forwarder: Auth OK
    Forwarder->>Remote: CONNECT example.com:443
    Remote->>Server: TCP connection
    Remote->>Forwarder: Connect OK

    Forwarder->>Chrome: Connect OK

    Note over Chrome,Server: Bidirectional data relay
    Chrome->>Forwarder: TLS + application data
    Forwarder->>Remote: Forward
    Remote->>Server: Forward
    Server->>Remote: Response
    Remote->>Forwarder: Forward
    Forwarder->>Chrome: Forward
```

Pydoll 在 `pydoll.utils` 模块中提供了内置的 `SOCKS5Forwarder`。这是一个纯 Python、零依赖的异步实现，处理与远程代理的完整 SOCKS5 握手，包括用户名/密码身份验证（RFC 1929）、IPv4、IPv6 和域名地址类型。

```python
import asyncio
from pydoll.utils import SOCKS5Forwarder
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,  # Use 0 for auto-assigned port
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

转发器也可以作为独立的 CLI 工具运行，用于测试或与其他应用配合使用：

```bash
python -m pydoll.utils.socks5_proxy_forwarder \
    --remote-host proxy.example.com \
    --remote-port 1080 \
    --username myuser \
    --password mypass \
    --local-port 1081
```

转发器默认绑定到 `127.0.0.1`，使其只能从本机访问。切勿在生产环境中绑定到 `0.0.0.0`，因为这会向网络暴露一个未认证的 SOCKS5 代理。凭据永远不会以明文记录到日志中。由于所有通信都通过本地回环接口进行，转发器增加的延迟不到一毫秒。

!!! tip "受限环境"
    某些环境（Docker 容器、无服务器平台、加固的虚拟机）可能会限制绑定到本地端口。使用 `local_port=0` 让操作系统分配一个可用端口。如果本地绑定完全被阻止，请考虑使用 HTTP CONNECT 代理，Chrome 通过 Pydoll 的 ProxyManager 原生支持其身份验证。

## 实际配置

**基本 SOCKS5（无身份验证）：**

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

**带身份验证的 SOCKS5（通过 SOCKS5Forwarder）：**

请参阅上面的 [SOCKS5Forwarder 章节](#pydolls-socks5forwarder)。

**防止泄露：**

要建立完整的 SOCKS5 配置，您还应该防止 WebRTC 和 DNS 预取泄露：

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.webrtc_leak_protection = True  # Prevents WebRTC IP leaks
options.add_argument('--disable-quic')  # Forces HTTP/2 over TCP through proxy
```

**测试您的配置：**

始终通过泄露测试验证您的代理配置。访问 [browserleaks.com/ip](https://browserleaks.com/ip) 确认您的 IP，访问 [browserleaks.com/webrtc](https://browserleaks.com/webrtc) 检查 WebRTC 泄露，访问 [dnsleaktest.com](https://dnsleaktest.com/) 验证 DNS 是否泄露。

## 总结

SOCKS5 提供协议无关的代理，与 HTTP 代理相比具有更小的信任面。它不会解析、修改或向您的流量注入任何内容。在 Chrome 中，DNS 解析在代理侧进行。TLS 加密端到端保持不变。Chrome 中的主要限制是缺乏原生 SOCKS5 身份验证（通过 Pydoll 的 `SOCKS5Forwarder` 解决）以及不支持 UDP 代理（通过禁用 WebRTC 或使用适当的浏览器标志来缓解）。

SOCKS5 不会改变浏览器的 TLS fingerprint、HTTP/2 设置或任何应用层特征。要实现完整的规避，请将 SOCKS5 与浏览器 fingerprint 管理和行为模拟相结合。

**后续步骤：**

- [代理检测](./proxy-detection.md)：即使 SOCKS5 代理也可能被检测到
- [构建代理](./build-proxy.md)：实现您自己的 SOCKS5 服务器
- [代理配置](../../features/configuration/proxy.md)：Pydoll 代理的实际设置
- [规避技术](../fingerprinting/evasion-techniques.md)：多层规避策略

## 参考资料

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 1961: GSS-API Authentication Method for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1961
- RFC 3089: SOCKS-based IPv6/IPv4 Gateway Mechanism (2001) - https://datatracker.ietf.org/doc/html/rfc3089
- Chromium Proxy Documentation - https://chromium.googlesource.com/chromium/src/+/689912289c/net/docs/proxy.md
- Chromium Issue #40323993: SOCKS5 Authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- DNS Leak Test - https://dnsleaktest.com/
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
