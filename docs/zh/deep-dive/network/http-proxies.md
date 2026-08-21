# HTTP 与 HTTPS proxy

一个 HTTP proxy 坐落在你的浏览器和目标服务器之间，并且理解 HTTP，所以它能够解析、缓存、过滤和修改经过它的流量。这种与协议的深度耦合也正是它的局限：它只处理 HTTP，会通过可识别的 header 暴露自己，而且无法承载 UDP，这就让 WebRTC 和 QUIC 从它旁边泄露出去。

本页涵盖 HTTP proxy 如何搬运流量、承载 HTTPS 的 CONNECT 隧道、认证如何工作，以及现代协议（HTTP/2、HTTP/3）在哪里让局面变得复杂。在 Pydoll 中配置 proxy 的方法，见 [Proxy](../../guides/proxies.md)。相关背景：[网络基础](network-fundamentals.md)、[SOCKS proxy](socks-proxies.md) 和 [Proxy 检测](proxy-detection.md)。

## 一个 HTTP proxy 如何工作

一个 HTTP proxy 持有两条独立的 TCP 连接：一条从客户端到 proxy，一条从 proxy 到目标。因为它读取 HTTP，所以它能对每个请求决定该怎么做，而不是盲目地中转字节。

当一个客户端被配置为使用 proxy 时，它会把完整的请求发给 proxy 而不是服务器。破绽在请求行：它携带的是绝对 URI，而不只是路径。客户端发送的不是 `GET /page HTTP/1.1`，而是 `GET http://example.com/page HTTP/1.1`，这就告诉了 proxy 该把它转发到哪里。

```mermaid
sequenceDiagram
    participant Client as 客户端浏览器
    participant Proxy as HTTP Proxy
    participant Server as 目标服务器

    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: TCP 连接 #1

    Note over Proxy: 解析请求、检查认证、<br/>检查缓存、应用规则

    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: TCP 连接 #2

    Server->>Proxy: HTTP/1.1 200 OK<br/>[响应 body]

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[可能被修改的 body]
```

proxy 解析方法、URL 和 header，然后作出决定：核对凭据、把 URL 与一个访问列表匹配、查找一份缓存副本、重写 header。它打开自己到服务器的连接并转发请求。当响应回来时，它可以按 `Cache-Control` 和 `ETag` 缓存它、过滤内容、压缩它，并在放行之前记录这次事务。

### 暴露 proxy 的那些 header

HTTP proxy 常常会添加一些暴露其存在、以及客户端真实 IP 的 header：

- `Via`（RFC 9110）标明了请求链路中的这个 proxy。
- `X-Forwarded-For` 携带原始客户端 IP，若涉及多个 proxy 则会串接起来。`X-Real-IP` 是一个更简单的变体。
- `X-Forwarded-Proto` 记录原始请求是 HTTP 还是 HTTPS。
- 标准化的 `Forwarded` header（RFC 7239）把这些合并进一个字段，尽管大多数 proxy 仍在发送 `X-Forwarded-*` 系列变体。

较老的客户端可能还会发送 `Proxy-Connection: keep-alive` 而不是 `Connection: keep-alive`，这是一个经典的 proxy 标志。

!!! warning "header 会坐实一个 proxy"
    检测系统会寻找 `Via`、`X-Forwarded-For` 或 `Forwarded`，并在 `X-Real-IP` 与连入的 IP 不一致时坐实这个 proxy。好的 proxy 会剥除这些，但许多商用服务默认会把它们留着。用类似 [browserleaks.com/ip](https://browserleaks.com/ip) 的工具检查你自己的。

### 它能做什么，不能做什么

因为它解析 HTTP，一个 proxy 可以读取和更改一个未加密请求和响应的每一个部分（URL、header、cookie、body），这正是缓存、内容过滤、header 注入、认证和详细日志得以实现的基础。

这种耦合的代价是适用范围。它无法原生承载 FTP、SSH 或自定义协议（下文的 CONNECT 是一种变通），它没有 UDP 通路，所以 WebRTC、DNS 和 QUIC 会绕过它，而检视 HTTPS 内容则需要终结 TLS，这会破坏端到端加密。

## CONNECT 方法：为 HTTPS 建立隧道

CONNECT（RFC 9110）回答了一个基本问题：一个 proxy 如何转发它读不懂的加密流量？靠变成一条盲的 TCP 隧道。客户端请求 proxy 打开一条到目的地的原始 TCP 连接；一旦确认，proxy 就停止解释 HTTP，只在双向上中转字节。

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant Proxy as Proxy
    participant Server as 服务器

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Proxy->>Server: TCP 三次握手
    Proxy->>Client: HTTP/1.1 200 Connection Established
    Note right of Proxy: proxy 现在是一个透明的<br/>TCP relay（第 4 层）
    Client->>Server: TLS ClientHello
    Server->>Client: TLS ServerHello, Certificate
    Client->>Server: 加密的 HTTP/2 请求
    Server->>Client: 加密的 HTTP/2 响应
```

CONNECT 请求很精简：方法是 `CONNECT`，目标是 `host:port`（不是路径），没有 body。proxy 校验凭据、检查规则、打开 TCP 连接，然后回复 `HTTP/1.1 200 Connection Established`，后跟一个空行。在那一行之后，HTTP 对话就结束了，proxy 变成了一个中继。

### CONNECT 之后 proxy 能看到什么

一旦隧道建立，proxy 就知道目的主机和端口，并能观察时序、每个方向的数据量，以及任一端何时挂断。它还能看到以明文发送的 TLS ClientHello：TLS 版本、加密套件、扩展、曲线，以及 SNI 主机名。这正是 TLS 指纹（JA3/JA4）所读取的东西；见 [网络指纹](../fingerprinting/network-fingerprinting.md)。

它看不到的是加密的应用数据：方法、URL、header、cookie、令牌和 body 全都在 TLS 隧道内部。

!!! note "SNI 与 Encrypted Client Hello"
    SNI 扩展以明文暴露目标主机名，在这里与 CONNECT 行是冗余的，但对其他网络观察者是可见的。Encrypted Client Hello（ECH）意在隐藏它，但采用率仍然有限，且需要客户端和服务器双方支持。

CONNECT 可以为任何 TCP 协议（IMAPS、SSH、FTPS）建立隧道，因为隧道打开之后 proxy 只中转字节。实际中许多企业 proxy 会把 CONNECT 限制在 443 端口，所以 `CONNECT example.com:22` 常常返回 `403 Forbidden`。

### 隧道对拦截

一个 proxy 面对加密流量时有一个选择。CONNECT 隧道保留端到端加密：客户端直接校验服务器证书，证书固定（certificate pinning）也能工作，但 proxy 无法检视或缓存内容。TLS 终结（MITM）是另一种做法：proxy 解密、检视、再加密，这需要在客户端安装它的 CA 证书，会破坏端到端加密，并且能通过固定和证书透明度（Certificate Transparency）被检测到。企业 proxy 倾向于为内容过滤而终结 TLS；注重隐私的 proxy 则使用盲隧道。

对自动化而言，这决定了服务器看到的是谁的 TLS 指纹。经过一条 CONNECT 隧道，指纹端到端都是你浏览器的。经过一个会终结的 proxy，则是 proxy 的。

| 方面 | HTTP（无 CONNECT） | HTTPS（CONNECT 隧道） |
|--------|-------------------|------------------------|
| proxy 可见性 | 完整的请求和响应 | 目的 host:port + TLS ClientHello |
| 加密 | 无（除非它终结 TLS） | 端到端 TLS |
| 缓存 | 可以，按 HTTP 语义 | 不可（已加密） |
| 内容过滤 | 可以 | 仅基于主机名 |
| URL 可见性 | 完整 URL | 仅主机名（CONNECT 和 SNI） |
| 协议支持 | 仅 HTTP | 任何 TCP 协议 |

## 通过 TLS 连接到 proxy

代理 HTTPS 流量与通过 HTTPS 抵达 proxy 本身是两回事。配置 `--proxy-server=https://proxy:port`（而不是 `http://`），你的浏览器与 proxy 之间那一跳就是 TLS 加密的，这能在本地网络上保护你的 proxy 凭据，甚至对本地观察者隐藏 CONNECT 的主机名。这在不受信任的网络上最为重要，那里客户端到 proxy 的这一跳是最缺乏保护的。

## 认证

当一个 proxy 需要凭据时，它会回复 `407 Proxy Authentication Required`，带一个 `Proxy-Authenticate` header 说明它接受的方案，客户端随即用一个 `Proxy-Authorization` header 重试。

- **Basic**（RFC 7617）：发送 `base64(username:password)`。Base64 是编码，不是加密，所以它可以被轻易逆转，也没有防重放保护。只在到 proxy 的 TLS 连接上使用它。
- **Digest**（RFC 7616）：基于一个 nonce 的挑战-应答；密码从不发送，nonce 限制了重放。最初的 MD5 形式很弱（SHA-256 是后来加入的），如今已很少实现。
- **NTLM**：微软专有的挑战-应答，在 Windows 网络中常见。它是绑定到连接的，所以会因 HTTP/2 多路复用而失效，而且以现代标准衡量它的哈希很弱。
- **Negotiate**（RFC 4559）：由 SPNEGO 选择 Kerberos 或 NTLM，优先 Kerberos。Kerberos 最强，但需要 Active Directory、加入域的机器，以及时钟同步，这在自动化中很难安排。

| 方案 | 安全性 | 机制 | 备注 |
|--------|----------|-----------|-------|
| Basic | 低 | Base64 凭据 | 通用。仅限 TLS 上使用。 |
| Digest | 中 | 挑战-应答（MD5/SHA-256） | 有防重放。少见。 |
| NTLM | 中 | 挑战-应答（NT 哈希） | Windows 单点登录。会破坏 HTTP/2。 |
| Negotiate | 高 | Kerberos/SPNEGO | 最强。需要 Active Directory。 |

Chrome 不接受 `--proxy-server` 中的内联凭据：`http://user:pass@proxy:port` 会在不带 `user:pass` 的情况下连接。Pydoll 为你绕过了这一点（它从 URL 中剥除凭据，并通过 CDP 应答 `407` 挑战），所以你可以传入一个带凭据的 proxy URL。用法见 [Proxy](../../guides/proxies.md)。

## 现代协议

### HTTP/2

HTTP/2 在一条 TCP 连接上承载多个并发的流（stream），带有二进制分帧和 HPACK header 压缩。对一个 proxy 而言，这意味着要在两侧之间映射流 ID、维护优先级树，并做逐流的流控，这比 HTTP/1.1 的顺序转发要复杂得多。它对指纹识别也很重要：HTTP/2 的流元数据（窗口大小、优先级、HPACK 中的 header 顺序）即便在许多客户端共用一个 proxy 时也能识别出各个客户端。

| 特性 | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| 连接 | 每条连接顺序处理（浏览器并行开约 6 条） | 一条连接上的并发流 |
| 多路复用 | 无 | 有（流级别） |
| Header 压缩 | 无 | HPACK |
| proxy 复杂度 | 简单转发 | 流映射、优先级 |

### HTTP/3 与 QUIC

HTTP/3 运行在 QUIC 之上，一个 UDP 传输，这打破了基于 TCP 的 proxy 的种种假设。传统 proxy 无法承载 QUIC，它的连接能在 IP 变化后存续，而且它加密了几乎所有的传输元数据。要代理它需要 CONNECT-UDP（RFC 9298），许多服务尚不支持，所以当 proxy 做不了 QUIC 时，浏览器会回退到 TCP 上的 HTTP/2。

!!! warning "静默降级会泄露元数据"
    当一个 proxy 不支持 HTTP/3 时，浏览器会悄悄回退到 HTTP/2 或 HTTP/1.1，暴露出本会被 HTTP/3 加密的时序和 header 元数据。在自动化中，可以考虑用 `--disable-quic` 标志强制走 TCP，好让所有流量都经过 proxy，也就没有基于 UDP 的泄露。

## HTTP proxy 对 SOCKS5

| 需求 | HTTP proxy | SOCKS5 |
|------|------------|--------|
| 内容过滤 / 缓存 | 可以 | 不可 |
| 基于 URL 的封锁 | 可以 | 不可（仅 IP:port） |
| UDP 支持 | 无 | 有 |
| 协议灵活性 | HTTP（用 CONNECT 建 TCP 隧道） | 任何 TCP/UDP |
| 隐私 | 低（解析 HTTP、添加 header） | 较高（不解析也不修改） |
| DNS 解析 | proxy 解析 | Chrome 为 SOCKS5 远程解析 |

HTTP proxy 适合需要内容控制和缓存的环境。对注重隐私的自动化，SOCKS5 提供更好的隐匿和协议灵活性。在自动化中，CONNECT 隧道让你的 TLS 指纹端到端保持不变，并只给 proxy 主机名层面的可见性。

## 相关内容

- [SOCKS proxy](socks-proxies.md)：与协议无关的会话层代理。
- [Proxy 检测](proxy-detection.md)：暴露一个 proxy 的那些信号。
- [网络基础](network-fundamentals.md)：TCP/IP、UDP，以及底下的那些层。
- [网络指纹](../fingerprinting/network-fingerprinting.md)：TCP/IP 和 TLS 指纹。
- [Proxy](../../guides/proxies.md)：在 Pydoll 中配置 proxy。

## 参考资料

- RFC 9110: HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9113: HTTP/2: https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3: https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC: https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP): https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 7617: Basic Authentication: https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication: https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- MDN: Proxy servers and tunneling: https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
