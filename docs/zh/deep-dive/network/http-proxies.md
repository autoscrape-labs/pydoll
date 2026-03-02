# HTTP/HTTPS Proxy 架构

HTTP proxy 是互联网上最常见的代理协议。几乎每个企业网络都在使用它们，大多数商业代理服务也将其作为默认选项。它们在 OSI 模型的第 7 层（应用层）运行，这意味着它们能够理解 HTTP，并可以解析、修改、缓存和过滤流量。然而，这种与协议的深度集成也是它们最大的局限：它们只能处理 HTTP 流量，会通过可识别的标头暴露代理的使用，并且无法代理 UDP，导致 WebRTC 和 DNS 容易泄露。

本文档涵盖 HTTP proxy 在协议层面的工作原理、用于 HTTPS 隧道的 CONNECT 方法、身份验证机制，以及 HTTP/2 和 HTTP/3 等现代协议的影响。

!!! info "模块导航"
    - [网络基础](./network-fundamentals.md)：TCP/IP、UDP、OSI 模型
    - [网络与安全概述](./index.md)：模块介绍
    - [SOCKS Proxy](./socks-proxies.md)：协议无关的替代方案
    - [Proxy 检测](./proxy-detection.md)：如何避免被检测

    有关实际配置，请参阅 [Proxy 配置](../../features/configuration/proxy.md)。

## HTTP Proxy 的工作原理

HTTP proxy 位于客户端和目标服务器之间，维护两个独立的 TCP 连接：一个从客户端到 proxy，另一个从 proxy 到目标服务器。由于 proxy 理解 HTTP，它可以对经过的流量做出智能决策。

### 请求流程

当客户端配置为使用 HTTP proxy 时，它会将完整的 HTTP 请求发送到 proxy，而不是直接发送到目标服务器。与直接请求的关键区别在于，请求行包含绝对 URI，而不仅仅是路径。例如，客户端发送的不是 `GET /page HTTP/1.1`，而是 `GET http://example.com/page HTTP/1.1`。这告诉 proxy 应将请求转发到哪里。

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Proxy as HTTP Proxy
    participant Server as Target Server

    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: TCP connection #1

    Note over Proxy: Parse request, check auth,<br/>check cache, apply rules

    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: TCP connection #2

    Server->>Proxy: HTTP/1.1 200 OK<br/>[response body]

    Note over Proxy: Cache response if allowed,<br/>filter content, log transaction

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[possibly modified body]
```

Proxy 接收到完整的 HTTP 请求后，会解析方法、URL 和标头，然后决定如何处理。它可能会检查身份验证凭据、根据访问控制列表验证 URL、查找资源的缓存副本，并在转发前修改标头。然后它会打开一个到目标服务器的独立 TCP 连接并发送请求，可能带有修改过的标头。

当响应到达时，proxy 可以根据 HTTP 语义（`Cache-Control`、`ETag`）缓存响应，过滤恶意软件或被拦截的关键词，在客户端支持时进行压缩，并在将响应转发回客户端之前记录事务。

### Proxy 标头与隐私

HTTP proxy 通常会添加标头来暴露它们的存在以及客户端的真实 IP 地址。`Via` 标头（RFC 9110）标识请求链中的 proxy。`X-Forwarded-For` 标头包含原始客户端 IP，如果涉及多个 proxy 则会形成链。`X-Forwarded-Proto` 标头指示原始请求是 HTTP 还是 HTTPS。一些 proxy 还会添加 `X-Real-IP` 作为 `X-Forwarded-For` 的简化替代。

还有一个标准化的 `Forwarded` 标头（RFC 7239），将所有这些信息整合到一个字段中，例如 `Forwarded: for=192.168.1.100;proto=http;by=proxy.example.com`。实际上，大多数 proxy 仍然使用 `X-Forwarded-*` 变体，因为它们有更广泛的支持。

旧版客户端和一些老旧浏览器在通过 proxy 路由时，可能还会发送 `Proxy-Connection: keep-alive` 标头而非 `Connection: keep-alive`。这个标头是一个众所周知的 proxy 使用指标，也是经典的检测信号。

!!! danger "标头检测"
    检测系统会查找 `Via`、`X-Forwarded-For` 或 `Forwarded` 标头的存在来确认 proxy 的使用。如果 `X-Real-IP` 与连接 IP 不匹配，则可以确认使用了 proxy。高级 proxy 可以剥离这些标头，但许多商业 proxy 服务默认会保留它们。请务必使用 [browserleaks.com/ip](https://browserleaks.com/ip) 等工具验证你的 proxy 行为。

### 能力与限制

由于 HTTP proxy 能够解析和理解 HTTP 协议，它们可以读取和修改未加密 HTTP 请求和响应的每个部分：URL、标头、Cookie 和正文。这使它们能够智能缓存响应、按 URL 或关键词过滤内容、注入或剥离标头、验证用户身份，以及详细记录所有流量。

代价是与 HTTP 的深度耦合意味着 proxy 仅限于 HTTP 流量。它无法原生代理 FTP、SSH、SMTP 或自定义协议（尽管下面描述的 CONNECT 方法为任何基于 TCP 的协议提供了隧道解决方案）。它不支持 UDP，这意味着 WebRTC、DNS 查询和 QUIC/HTTP/3 流量会完全绕过它。而检查 HTTPS 内容需要 TLS 终止，这会破坏端到端加密。

## CONNECT 方法：HTTPS 隧道

CONNECT 方法（RFC 9110，第 9.3.6 节）解决了一个根本问题：HTTP proxy 如何转发它无法读取的加密流量？答案是成为一个盲目的 TCP 隧道。

当客户端想要通过 proxy 访问 HTTPS 站点时，它会发送一个 `CONNECT` 请求，要求 proxy 建立到目标的原始 TCP 连接。一旦 proxy 确认隧道已建立，它就不再是 HTTP proxy，而是变成第 4 层的透明 TCP 中继，在两个方向上转发字节而不解释它们。

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Note over Client,Proxy: Unencrypted HTTP request

    Proxy->>Server: TCP three-way handshake
    Note over Proxy,Server: TCP connection established

    Proxy->>Client: HTTP/1.1 200 Connection Established

    Note right of Proxy: Proxy is now a transparent<br/>TCP relay (Layer 4)

    Client->>Server: TLS ClientHello
    Note over Client,Server: TLS handshake (proxy sees<br/>this in plaintext)
    Server->>Client: TLS ServerHello, Certificate

    Client->>Server: Encrypted HTTP/2 request
    Server->>Client: Encrypted HTTP/2 response

    Note over Proxy: Proxy blindly forwards<br/>all encrypted data
```

### CONNECT 请求

CONNECT 请求非常简洁。方法是 `CONNECT`，请求 URI 是目标的 `host:port`（而不是路径），如果 proxy 需要则包含身份验证。没有请求体。Proxy 验证凭据，检查访问控制规则，然后打开到指定主机和端口的 TCP 连接。如果一切成功，它会返回 `HTTP/1.1 200 Connection Established`，后跟一个空行。在该空行之后，HTTP 对话结束，proxy 变成透明中继。

### CONNECT 之后的可见性

一旦隧道建立，proxy 的可见性就很有限了。它知道来自 CONNECT 请求的目标主机名和端口。它可以观察连接时间（何时建立以及持续多久）、每个方向传输的数据量，以及任一方终止连接的时刻。它还可以观察随后的 TLS 握手，这一点特别值得关注。

TLS ClientHello 消息在隧道建立后立即发送，且以明文传输。Proxy（以及任何网络观察者）可以直接读取 TLS 版本、完整的支持密码套件列表、扩展及其参数、提供的椭圆曲线，以及包含目标主机名的 SNI（Server Name Indication）扩展。这正是用于 TLS 指纹识别（JA3/JA4）的信息。详情请参阅[网络指纹](../fingerprinting/network-fingerprinting.md)。

Proxy 无法看到的是加密的应用数据：HTTP 方法、URL、请求和响应标头、Cookie、会话令牌和响应内容都在 TLS 隧道内加密。

!!! note "SNI 与 Encrypted Client Hello (ECH)"
    ClientHello 中的 SNI 扩展以明文暴露目标主机名，这在 proxy 场景中与 CONNECT 请求是冗余的，但对其他网络观察者来说很有意义。Encrypted Client Hello (ECH) 目前正在部署中，旨在加密 SNI 来解决这一泄露问题。不过，ECH 的采用仍然有限，需要客户端和服务器双方的支持。

### CONNECT 用于非 HTTPS 协议

虽然 CONNECT 主要用于 HTTPS，但它可以隧道传输任何基于 TCP 的协议。到端口 993 的 IMAPS 连接、到端口 22 的 SSH 连接，或到端口 990 的 FTP-over-TLS 都可以通过 CONNECT 隧道工作。Proxy 不需要理解这些协议，因为隧道建立后它只是简单地中继字节。

实际上，许多企业 proxy 会将 CONNECT 限制在端口 443（HTTPS），以防止滥用。尝试 `CONNECT example.com:22` 进行 SSH 连接通常会返回 `403 Forbidden`。

### HTTPS 困境

HTTP proxy 在处理加密流量时面临一个根本性的选择。使用 CONNECT 隧道方式，端到端加密得以保留，客户端直接验证服务器证书，证书固定正常工作。但 proxy 无法检查、缓存或过滤加密内容。

另一种方式是 TLS 终止（MITM），proxy 解密 HTTPS 流量、检查内容，然后重新加密后转发。这需要在客户端上安装 proxy 的 CA 证书，会破坏端到端加密，并且可以通过证书固定和证书透明度日志检测到。大多数企业 proxy 使用这种方式进行内容过滤和安全扫描，而注重隐私的 proxy 则使用盲目 CONNECT 隧道。

对于网页抓取和自动化来说，这一区别对 TLS 指纹识别很重要。如果 proxy 执行 TLS 终止，目标服务器看到的 TLS 指纹属于 proxy，而非你的浏览器。如果你使用的是 CONNECT 隧道，指纹则是端到端保留的。根据你的规避策略，其中一种方式可能比另一种更合适。

| 方面 | HTTP（无 CONNECT） | HTTPS（CONNECT 隧道） |
|--------|-------------------|------------------------|
| Proxy 可见性 | 完整的 HTTP 请求/响应 | 仅目标 host:port + TLS ClientHello |
| 加密 | 无（除非 TLS 终止） | 端到端 TLS |
| 缓存 | 是，基于 HTTP 语义 | 否（加密内容） |
| 内容过滤 | 是 | 否（仅基于主机名拦截） |
| 标头修改 | 是 | 否（加密标头） |
| URL 可见性 | 完整 URL | 仅主机名（通过 CONNECT 和 SNI） |
| 协议支持 | 仅 HTTP | 任何基于 TCP 的协议 |

## HTTPS Proxy（到 Proxy 的 TLS）

有一个值得澄清的区别：代理 HTTPS 流量与通过 HTTPS 连接到 proxy 本身是不同的。当你配置 `--proxy-server=https://proxy:port` 而非 `http://proxy:port` 时，你的浏览器与 proxy 之间的连接是通过 TLS 加密的。这可以保护你的 proxy 身份验证凭据不被本地网络嗅探，并且对本地观察者隐藏 CONNECT 主机名，因为它被封装在到 proxy 的 TLS 连接内。

Chrome 通过 `--proxy-server` 中的 `https://` 方案支持此功能。当在不受信任的网络（公共 Wi-Fi、共享主机）上使用 proxy 时，这一点尤其重要，因为你与 proxy 之间的连接是最薄弱的环节。

## 身份验证

HTTP proxy 身份验证使用标准 HTTP 状态码和标头，遵循 RFC 9110。当 proxy 需要身份验证时，它会返回 `407 Proxy Authentication Required` 以及一个 `Proxy-Authenticate` 标头，指示它支持哪些身份验证方案。然后客户端使用包含凭据的 `Proxy-Authorization` 标头重新传输请求。

### 身份验证方案

有多种身份验证方案，每种都有不同的安全特性。

**Basic**（RFC 7617）是最简单的。客户端发送 `Proxy-Authorization: Basic <base64(username:password)>`。Base64 是一种编码而非加密，因此凭据可以被轻易还原。任何拦截到该标头的人都可以立即解码并无限期地重用，因为没有重放保护。Basic 身份验证应仅通过 TLS 加密的连接使用。

**Digest**（RFC 7616）使用挑战-响应机制。Proxy 发送一个随机 nonce，客户端计算用户名、密码、nonce 和请求 URI 的哈希值。密码永不传输，nonce 提供重放保护。原始版本使用 MD5，其速度足以被高效暴力破解，不过 RFC 7616 增加了 SHA-256 支持。Digest 身份验证很少被现代 proxy 服务实现。

**NTLM** 是微软专有的挑战-响应协议，常见于 Windows 企业环境。它使用三步协商（Type 1 协商、Type 2 挑战、Type 3 认证），并与 Active Directory 集成实现单点登录。NTLMv1 使用 DES（已被攻破），NTLMv2 使用 HMAC-MD5（按现代标准被认为较弱）。微软建议在新部署中使用 Kerberos 替代 NTLM。NTLM 是绑定连接的，这意味着它在 HTTP/2 多路复用下会出问题。

**Negotiate**（RFC 4559）使用 SPNEGO 在 Kerberos 和 NTLM 之间选择，优先使用 Kerberos。Kerberos 提供最强的安全性（AES 加密、相互身份验证、有时间限制的票据），但需要 Active Directory 基础设施、加入域的机器和精确的时钟同步。在浏览器自动化中，Kerberos 难以通过编程方式配置。

| 方案 | 安全性 | 机制 | 实用说明 |
|--------|----------|-----------|-----------------|
| Basic | 低 | Base64 编码的凭据 | 通用支持。仅通过 TLS 使用。 |
| Digest | 中 | 使用 MD5/SHA-256 的挑战-响应 | 通过 nonce 提供重放保护。很少被实现。 |
| NTLM | 中 | 挑战-响应（NT 哈希） | Windows SSO。专有，存在已知漏洞。 |
| Negotiate | 高 | Kerberos/SPNEGO | 最强。需要 Active Directory。 |

### Pydoll 中的身份验证

Chrome 不支持在 `--proxy-server` 标志中内联 proxy 凭据。写 `--proxy-server=http://user:pass@proxy:port` 不会生效：Chrome 会静默忽略 `user:pass` 部分并在不进行身份验证的情况下连接。

Pydoll 通过其 `ProxyManager` 透明地解决了这个问题。当你提供带有内嵌凭据的 proxy URL 时，Pydoll 会提取用户名和密码，在传递给 Chrome 之前从 URL 中剥离它们，然后使用 CDP Fetch 域拦截 `407 Proxy Authentication Required` 响应，并通过 `Fetch.continueWithAuth` 自动提供凭据。这种方式适用于 Chrome 支持的所有身份验证方案（Basic、Digest、NTLM、Negotiate），而无需 Pydoll 实现特定于协议的逻辑。

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
# Pydoll extracts credentials, cleans the URL, and handles 407 via CDP
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

!!! tip "身份验证最佳实践"
    始终使用 TLS 加密的 proxy 连接（HTTPS proxy 或 SSH 隧道）来保护传输中的凭据。对于 API proxy，优先使用 Bearer 令牌，因为它们可撤销且有时间限制。切勿通过未加密的 HTTP 连接使用 Basic 身份验证。不要在源代码中硬编码凭据，请使用环境变量。

## 现代协议与代理

### HTTP/2

HTTP/2 引入了多路复用、二进制分帧和 HPACK 标头压缩，从根本上改变了 proxy 处理连接的方式。在 HTTP/1.1 中，每个请求按顺序占用一个连接（虽然存在流水线但实际上已被禁用，因此浏览器通过为每个主机打开六个并行连接来解决这个问题）。在 HTTP/2 中，单个 TCP 连接承载多个并发流，每个流都有自己的请求和响应。

对于 proxy 来说，这意味着需要在连接的两端管理流 ID、优先级和流控窗口。Proxy 必须在客户端侧和服务器侧之间转换流 ID、维护优先级树，并对每个流进行流量控制。这比 HTTP/1.1 简单的请求-响应转发要复杂得多。

从指纹识别的角度来看，HTTP/2 流元数据（窗口大小、优先级设置、HPACK 内的标头排序）可以对单个客户端进行指纹识别，即使多个用户共享同一个 proxy。

| 特性 | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| 连接 | 每个连接按顺序处理（浏览器并行打开 6 个） | 单个连接上的多个并发流 |
| 多路复用 | 否（队头阻塞） | 是（仅流级别） |
| 标头压缩 | 无 | HPACK |
| Proxy 复杂度 | 简单的请求/响应转发 | 流 ID 映射、优先级管理 |

在 HTTP/2 中，CONNECT 方法通过 RFC 8441 进行了扩展，支持 `:protocol` 伪标头，使 WebSocket 隧道和其他协议升级可以直接在 HTTP/2 流中进行，而无需单独的连接。

### HTTP/3 与 QUIC

HTTP/3 运行在 QUIC（RFC 9000）之上，这是一种基于 UDP 的传输协议。这给 HTTP proxy 带来了根本性的挑战。传统 HTTP proxy 运行在 TCP 之上，无法处理 QUIC 的 UDP 流量。QUIC 连接可以在 IP 变化后继续存活（连接迁移），使 proxy 会话管理变得复杂。而且 QUIC 几乎加密了所有内容，包括之前可见的传输层元数据。

代理 QUIC 需要 CONNECT-UDP（RFC 9298），这是一种通过 HTTP proxy 建立 UDP 隧道的新方法。大多数传统 proxy，包括许多商业服务，尚不支持此功能。当 proxy 不支持 QUIC 时，浏览器会回退到基于 TCP 的 HTTP/2，这意味着如果你依赖 HTTP/3 的加密传输，实际泄露的元数据可能比预期更多。

在自动化场景中，考虑使用 `--disable-quic` Chrome 标志禁用 QUIC，以强制使用基于 TCP 的 HTTP/2。这可以确保所有流量都通过你的 proxy，并消除 QUIC 导致的 UDP 泄露风险。

| 方面 | TCP + TLS（HTTP/1.1、HTTP/2） | QUIC/UDP（HTTP/3） |
|--------|------------------------------|-------------------|
| 传输 | TCP（面向连接） | UDP（无连接） |
| 握手 | 分离的 TCP + TLS（2 RTT） | 合并（0-1 RTT） |
| 队头阻塞 | 是（TCP 级别） | 否（仅流级别） |
| 连接迁移 | 不支持 | 支持（可在 IP 变化后存活） |
| Proxy 兼容性 | 极好 | 有限（需要 UDP 中继支持） |

!!! warning "协议降级"
    当 proxy 不支持 HTTP/3 时，浏览器会静默回退到 HTTP/2 或 HTTP/1.1。这种降级可能暴露 HTTP/3 本会加密的元数据（标头、时序模式）。请监控你的流量以了解实际的协议版本，并注意 HTTP/3 的采用率因地区和 CDN 而异。

## 总结

HTTP proxy 提供了丰富的功能，但代价是范围有限和隐私问题。它们可以检查、缓存和过滤 HTTP 流量，但无法处理非 HTTP 协议、UDP 流量或 HTTPS 内容（除非破坏加密）。除非明确剥离，否则它们的存在会通过可识别的标头暴露。

对于自动化来说，CONNECT 隧道是最相关的功能：它在保留端到端 TLS 加密的同时，仅让 proxy 获得主机名级别的可见性。Pydoll 通过 CDP Fetch 域透明地处理 proxy 身份验证，支持 Chrome 实现的所有方案。

### HTTP Proxy 与 SOCKS5 对比

| 需求 | HTTP Proxy | SOCKS5 |
|------|------------|--------|
| 内容过滤 | 是 | 否 |
| 基于 URL 拦截 | 是 | 否（仅 IP:port） |
| 缓存 | 是 | 否 |
| UDP 支持 | 否 | 是 |
| 协议灵活性 | 仅 HTTP（CONNECT 可用于 TCP 隧道） | 任何 TCP/UDP |
| 隐私 | 低（解析 HTTP，添加暴露性标头） | 中（不解析或修改流量，但未加密内容对运营商仍然可见） |
| DNS 解析 | Proxy 解析（远程） | 取决于配置（SOCKS5：通常客户端解析，SOCKS5h：proxy 解析。Chrome 对 SOCKS5 始终使用远程解析。） |

对于需要内容控制和缓存的企业环境，HTTP proxy 是正确的选择。对于注重隐私的自动化，SOCKS5 提供更好的隐蔽性和协议灵活性。要获得最高安全性，请使用 SOCKS5 over SSH 隧道或 VPN。

**后续步骤：**

- [SOCKS Proxy](./socks-proxies.md)：协议无关的会话层代理
- [网络基础](./network-fundamentals.md)：TCP/IP、UDP、WebRTC
- [Proxy 检测](./proxy-detection.md)：如何检测 proxy 以及如何避免
- [Proxy 配置](../../features/configuration/proxy.md)：Pydoll 实际 proxy 设置
- [网络指纹](../fingerprinting/network-fingerprinting.md)：TCP/IP 和 TLS 指纹识别

## 参考文献

- RFC 9110: HTTP Semantics (2022, replaces RFC 7230-7237) - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 (2022) - https://www.rfc-editor.org/rfc/rfc9112.html
- RFC 9113: HTTP/2 (2022, replaces RFC 7540) - https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3 (2022) - https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC Transport Protocol (2021) - https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP, 2022) - https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 8441: Bootstrapping WebSockets with HTTP/2 (2018) - https://www.rfc-editor.org/rfc/rfc8441.html
- RFC 7617: Basic Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension (2014) - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 4559: Negotiate Authentication (2006) - https://www.rfc-editor.org/rfc/rfc4559.html
- MDN Web Docs: Proxy servers and tunneling - https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
- Chrome DevTools Protocol: Fetch domain - https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
