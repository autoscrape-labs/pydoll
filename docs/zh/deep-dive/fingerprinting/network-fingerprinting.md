# Network Fingerprinting

Network fingerprinting 通过分析 TCP/IP 协议栈、TLS 握手和 HTTP/2 连接的特征来识别客户端。这些信号由操作系统内核和 TLS 库设定，而非浏览器的 JavaScript 环境，因此比浏览器层面的指纹更难伪造。代理或 VPN 可以更改你的 IP 地址，但无法改变你的 TCP 窗口大小、TLS cipher suite 列表或 HTTP/2 SETTINGS 帧。检测系统正是利用了这一差异。

!!! info "模块导航"
    - [Browser Fingerprinting](./browser-fingerprinting.md)：Canvas、WebGL、AudioContext
    - [Evasion Techniques](./evasion-techniques.md)：多层对抗措施

    有关协议基础知识，请参阅 [Network Fundamentals](../network/network-fundamentals.md)。有关代理检测的背景知识，请参阅 [Proxy Detection](../network/proxy-detection.md)。

## TCP/IP Fingerprinting

每个操作系统对 TCP/IP 协议栈的实现方式各不相同。发起 TCP 连接的 SYN 数据包携带了足够的信息来高置信度地识别操作系统：初始 TTL、TCP 窗口大小、最大报文段长度（MSS）以及 TCP 选项的顺序和选择。这些值均不受浏览器控制，它们全部来自内核。

### TTL (Time To Live)

初始 TTL 是最简单的操作系统标识符之一。Linux 和 macOS 将其设为 64，Windows 设为 128，网络设备（路由器、防火墙）通常使用 255。每经过一个路由器跳点，TTL 递减 1，因此一个到达时 TTL 为 118 的数据包很可能起始于 128（Windows），经过了 10 个跳点。

TTL 的 fingerprinting 价值在于将其与 User-Agent 进行交叉验证。如果浏览器声称是 Windows 上的 Chrome，但数据包到达时的 TTL 接近 64，那么该连接要么是通过 Linux 服务器代理的，要么 User-Agent 被伪造了。检测系统会将观察到的 TTL 向上取整到最近的已知初始值（64、128、255），然后与声称的操作系统进行比对。

当流量经过代理时，TTL 会被重置，因为代理的内核会生成一个新的 TCP 连接到目标。目标看到的是代理的 TTL，而不是你的。这就是为什么 TTL 不匹配是代理检测信号：User-Agent 声称是 Windows（TTL 128），但 TCP 指纹显示的是 Linux（TTL 64）。

### TCP 窗口大小和缩放

SYN 数据包中的初始 TCP 窗口大小因操作系统和内核版本而异。现代 Linux 内核（3.x 及更高版本）通常发送 29200 字节的初始窗口，即 `20 * MSS`（标准以太网的 MSS 为 1460）。某些较新的内核（5.x、6.x）根据配置和 `initcwnd` 设置可能使用 64240。Windows 10 和 11 通常发送 65535 并启用窗口缩放，但确切值取决于自动调优配置和补丁级别。macOS 也默认为 65535。

窗口缩放因子（一个 TCP 选项）将 16 位窗口大小字段进行乘法运算以支持更大的接收窗口。Linux 通常使用缩放因子 7（允许最大 8MB 的窗口），而 Windows 通常使用 8。结合基础窗口大小，缩放因子创建出比单独任何一个值都更精细的指纹。

### TCP 选项顺序

SYN 数据包中 TCP 选项的选择和排列顺序具有高度辨识度。每个操作系统按固定的、版本特定的顺序排列选项，且内核不将其作为可配置参数暴露。Linux 发送 `MSS, SACK_PERM, TIMESTAMP, NOP, WSCALE`。Windows 发送 `MSS, NOP, WSCALE, NOP, NOP, SACK_PERM`，并且在默认配置中明显省略了 TIMESTAMP 选项。macOS 发送 `MSS, NOP, WSCALE, NOP, NOP, TIMESTAMP, SACK_PERM`。

特定选项的有无与顺序同样重要。Windows 历史上省略了 TCP 时间戳，而 Linux 和 macOS 默认包含它。所有现代系统都支持 SACK（选择性确认），但某些旧版或嵌入式系统可能不会通告它。哪些选项出现以及它们的顺序组合起来形成一个签名，p0f 等工具会将其与已知操作系统指纹数据库进行匹配。

### p0f

[p0f](https://lcamtuf.coredump.cx/p0f3/) 是被动 TCP/IP fingerprinting 的标准工具。它在不生成任何数据包的情况下观察流量，分析 SYN 和 SYN+ACK 数据包并与签名数据库进行比对。其签名格式编码了关键的 fingerprinting 字段：

```
version:ittl:olen:mss:wsize,scale:olayout:quirks:pclass
```

`ittl` 是推断的初始 TTL，`mss` 是最大报文段长度，`wsize,scale` 是窗口大小（可以是绝对值，也可以是相对于 MSS 的值，如 `mss*20`），`olayout` 是使用简写名称（`mss`、`nop`、`ws`、`sok`、`sack`、`ts`、`eol+N`）表示的 TCP 选项布局。`quirks` 字段捕获异常行为，如 Don't Fragment 标志（`df`）或 DF 数据包上的非零 IP ID（`id+`）。

典型的 Linux 4.x+ 签名在 p0f 中看起来像 `4:64:0:*:mss*20,7:mss,sok,ts,nop,ws:df,id+:0`。Windows 10 的签名可能看起来像 `4:128:0:*:65535,8:mss,nop,ws,nop,nop,sok:df,id+:0`。反机器人服务在内部维护类似的数据库，将传入连接与已知操作系统配置文件进行匹配，并标记与声明的 User-Agent 不一致的情况。

## TLS Fingerprinting

TLS ClientHello 消息在加密建立之前传输，因此对网络路径上的任何观察者都是可见的。它包含 TLS 版本、支持的 cipher suites、TLS 扩展、支持的椭圆曲线（命名组）和 EC 点格式。每个浏览器和 TLS 库都会产生这些字段的特征组合。

### JA3

JA3 由 Salesforce 的 John Althouse、Jeff Atkinson 和 Josh Atkins 开发，是第一个被广泛采用的 TLS fingerprinting 方法。它将 ClientHello 中的五个字段（TLS 版本、cipher suites、扩展、椭圆曲线、EC 点格式）连接起来，每个字段内的值用连字符连接，五个字段之间用逗号分隔，然后对结果字符串取 MD5 哈希。

```
JA3 string: 771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0
JA3 hash:   cd08e31494b9531f560d64c695473da9
```

有一个细微之处：JA3 中的"TLS 版本"字段使用的是 `ClientHello.legacy_version`，而不是 `supported_versions` 扩展。由于 TLS 1.3（RFC 8446）要求客户端为了向后兼容将 `legacy_version` 设为 `0x0303`（TLS 1.2），因此对于现代客户端，JA3 的版本字段几乎总是 `771`，即使它们支持 TLS 1.3。实际的 TLS 1.3 协商通过扩展 43（`supported_versions`）进行，但 JA3 使用的是头部字段。

JA3 在哈希之前必须过滤 GREASE 值。GREASE（RFC 8701）是一种机制，浏览器会将随机选择的保留值插入 cipher suites、扩展和其他字段中，以防止协议僵化。有效的 GREASE 值为 `0x0a0a`、`0x1a1a`、`0x2a2a`，以此类推直到 `0xfafa`。每个值都有两个相同的字节，其中每个字节的低半字节为 `0x0a`。正确的 GREASE 过滤器需要检查两个条件：

```python
def is_grease(value: int) -> bool:
    return (value & 0x0f0f) == 0x0a0a and (value >> 8) == (value & 0xff)
```

!!! warning "JA3 在现代浏览器中的局限性"
    自 Chrome 110（2023 年 1 月）和 Firefox 114 起，浏览器会在每次连接时随机化 TLS 扩展的顺序。这意味着同一个浏览器在每次连接时会产生不同的 JA3 哈希，使得 JA3 对于识别现代浏览器实际上已经失效。JA3 对于 fingerprinting 非浏览器客户端（Python `requests`、`curl`、自定义机器人）仍然有用，因为这些客户端不实现扩展随机化。

### JA4

JA4 是 JA3 的继任者，由同一位主要作者（John Althouse）在 FoxIO 开发。它专门设计用于应对 TLS 扩展随机化，通过在哈希之前对扩展和 cipher suites 进行排序来实现。其格式由三个部分组成，以下划线分隔：`a_b_c`。

`a` 部分是人类可读的元数据字符串：协议（`t` 代表 TCP，`q` 代表 QUIC），TLS 版本（`12` 或 `13`），是否存在 SNI（`d` 代表域名，`i` 代表 IP），cipher suites 的数量（两位数），扩展的数量（两位数），以及第一个和最后一个 ALPN 值（`h2` 代表 HTTP/2，`00` 代表无）。例如，`t13d1516h2` 表示 TCP TLS 1.3 带 SNI，15 个 cipher suites，16 个扩展，以及 HTTP/2 ALPN。

`b` 部分是排序后的 cipher suites 的截断 SHA-256 哈希。`c` 部分是排序后的扩展与签名算法连接后的截断 SHA-256 哈希。因为两个列表在哈希之前都经过排序，所以扩展随机化不会影响输出。

Cloudflare、AWS 和其他主要平台已采用 JA4。完整的 JA4+ 套件还包括 JA4S（服务器 fingerprinting）、JA4H（HTTP 客户端 fingerprinting）、JA4X（X.509 证书 fingerprinting）和 JA4SSH（SSH fingerprinting）。规范和工具可在 [github.com/FoxIO-LLC/ja4](https://github.com/FoxIO-LLC/ja4) 获取。

### JA3S（服务器 Fingerprinting）

JA3S 将相同的概念应用于 ServerHello 消息，但格式更简单，因为服务器选择的是单个 cipher suite 而非提供一个列表。JA3S 字符串为 `version,cipher,extensions`，其 MD5 哈希标识了服务器的 TLS 实现。将 JA3（或 JA4）与 JA3S 配对可以创建双向指纹：特定客户端与特定服务器通信会产生可预测的 JA3+JA3S 对，这比单独任何一个指纹都更具辨识度。

### 代理如何影响 TLS 指纹

代理的类型决定了 TLS 指纹是否被保留。SOCKS5 代理和 HTTP CONNECT 隧道在不终止 TLS 的情况下中继 TCP 流，因此目标服务器看到的是原始客户端的 TLS 指纹，不会发生任何变化。这是这些代理类型在保持指纹一致性方面的主要优势。

MITM 代理（终止 TLS 并与目标重新建立新连接）会用自身的 TLS 指纹替换客户端的指纹。目标看到的是代理软件的 cipher suites 和扩展，而不是浏览器的。如果代理使用标准 TLS 库（如 OpenSSL 或 BoringSSL）的默认设置，指纹将不匹配任何已知浏览器，这本身就是一个检测信号。

这就是为什么 Pydoll 使用 `--proxy-server`（创建 CONNECT 隧道，保留浏览器的 TLS 指纹）的方式优于外部 MITM 代理设置来进行隐蔽自动化。

## HTTP/2 Fingerprinting

HTTP/2 连接暴露了一组与 TLS 不同的独立 fingerprinting 信号。客户端发送的第一个帧是 SETTINGS 帧，包含 `HEADER_TABLE_SIZE`、`ENABLE_PUSH`、`MAX_CONCURRENT_STREAMS`、`INITIAL_WINDOW_SIZE`、`MAX_FRAME_SIZE` 和 `MAX_HEADER_LIST_SIZE` 等参数。每个浏览器使用不同的默认值，并包含这些参数的不同子集。

除了 SETTINGS 之外，WINDOW_UPDATE 帧大小、初始流的优先级/权重以及 HTTP/2 伪头部（`:method`、`:authority`、`:scheme`、`:path`）的顺序在不同实现之间也各不相同。Chrome、Firefox 和 Safari 各自产生独特的这些值的组合。

Akamai 在 2017 年欧洲 Black Hat 大会上发表了关于 HTTP/2 fingerprinting 的基础性研究。他们的指纹格式连接了 SETTINGS 值、WINDOW_UPDATE 大小、PRIORITY 帧和伪头部顺序。JA4+ 套件中的 `JA4H` 用于 HTTP 层 fingerprinting，涵盖了头部顺序和值。

HTTP/2 fingerprinting 对自动化工具特别有效，因为许多机器人框架和 HTTP 库实现了自己的 HTTP/2 协议栈，其默认参数与任何真实浏览器都不匹配。即使工具正确伪造了 TLS 指纹（使用 curl-impersonate 或类似工具），其 HTTP/2 SETTINGS 帧也可能暴露它。

你可以在 [browserleaks.com/http2](https://browserleaks.com/http2) 检查你的 HTTP/2 指纹。因为 Pydoll 通过 CDP 控制真实的 Chrome 实例，HTTP/2 指纹始终是真实的——这是相对于以编程方式构建 HTTP 请求的工具的固有优势。

## 对浏览器自动化的影响

对于使用 Pydoll 进行自动化的实际要点是：network fingerprinting 是控制真实浏览器能提供显著优势的领域。Chrome 的 TCP/IP 协议栈、TLS 实现（BoringSSL）和 HTTP/2 协议栈默认产生真实的指纹。主要风险在于环境不匹配：在 Linux 服务器上运行 Chrome 而 User-Agent 声称是 Windows，会导致 TCP/IP 指纹不一致（TTL 为 64 而非 128，Linux TCP 选项顺序而非 Windows 的）。

对于基于代理的设置，指纹流程是：你的机器的 TCP/IP 协议栈生成到代理的连接（代理的运营商可以看到但目标无法看到），代理的 TCP/IP 协议栈生成到目标的连接。目标看到的是代理服务器的 TTL 和 TCP 选项。如果代理运行 Linux（大多数都是），无论 User-Agent 如何，TCP 指纹都将显示 Linux。这是一个众所周知的检测信号，住宅代理可以部分缓解（代理端点是真实用户的机器，因此其 TCP 指纹是合理的），但数据中心代理无法做到。

另一方面，TLS 和 HTTP/2 指纹通过 SOCKS5 和 CONNECT 隧道不做修改地传递。这些是浏览器的指纹，不是代理的。因此，通过 CONNECT 隧道使用 Pydoll 时，目标看到的是真实的 Chrome TLS 和 HTTP/2 指纹，配合代理的 TCP/IP 指纹。这种组合与真实用户通过 VPN 或企业代理浏览是一致的，这是一种常见且合理的模式。

## 参考资料

- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- FoxIO JA4+ Network Fingerprinting - https://github.com/FoxIO-LLC/ja4
- Cloudflare: JA4 Signals - https://blog.cloudflare.com/ja4-signals/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- p0f v3: Passive OS Fingerprinting - https://lcamtuf.coredump.cx/p0f3/
- RFC 8446: TLS 1.3 - https://datatracker.ietf.org/doc/html/rfc8446
- RFC 8701: GREASE for TLS - https://datatracker.ietf.org/doc/html/rfc8701
- RFC 6528: Defending against Sequence Number Attacks - https://datatracker.ietf.org/doc/html/rfc6528
- BrowserLeaks HTTP/2 Fingerprint - https://browserleaks.com/http2
- Stamus Networks: JA3 Fingerprints Fade as Browsers Embrace Extension Randomization - https://www.stamus-networks.com/blog/ja3-fingerprints-fade-browsers-embrace-tls-extension-randomization
