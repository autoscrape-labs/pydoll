# Network fingerprinting

Network fingerprinting 通过分析 TCP/IP 栈、TLS 握手和 HTTP/2 连接的特征来识别客户端。这些信号由操作系统内核和 TLS 库设定，而不是由浏览器的 JavaScript 环境设定，这使得它们比浏览器级别的 fingerprint 更难伪造。proxy 或 VPN 会改变你的 IP 地址，但不会改变你的 TCP 窗口大小、你的 TLS cipher suite 列表，或你的 HTTP/2 SETTINGS 帧。检测系统利用的正是这个缺口。

这是 [Stealth](../../stealth/index.md) 指南背后的理论。它与 [Browser fingerprinting](browser-fingerprinting.md)（JavaScript 可见的信号）和 [Behavioral fingerprinting](behavioral-fingerprinting.md)（你如何移动和打字）相配套。关于这些协议本身如何工作，请参见 [Network fundamentals](../network/network-fundamentals.md)。

## TCP/IP fingerprinting

每个操作系统对 TCP/IP 栈的实现都不同。发起 TCP 连接的 SYN 包携带了足够的信息，能以高置信度识别操作系统：初始 TTL、TCP 窗口大小、最大段大小（Maximum Segment Size），以及 TCP 选项的顺序和选择。这些值没有一个是由浏览器控制的。它们来自内核。

### TTL（time to live）

初始 TTL 是最简单的操作系统标识符之一。Linux 和 macOS 把它设为 64，Windows 设为 128，而网络设备（路由器、防火墙）通常使用 255。每经过一次路由器跳转，TTL 就减一，因此一个到达时 TTL 为 118 的包很可能起始于 128（Windows）并跨越了 10 跳。

TTL 的 fingerprinting 价值来自与 User-Agent 的交叉引用。如果浏览器声称是 Windows 上的 Chrome，但包到达时 TTL 接近 64，那么这个连接要么是通过一台 Linux 服务器代理的，要么 User-Agent 是伪造的。检测系统会把观察到的 TTL 向上取整到最近的已知初始值（64、128、255），并与所声称的操作系统比较。

当流量流经 proxy 时，TTL 会重置，因为 proxy 的内核会生成一条到目标的新 TCP 连接。目标看到的是 proxy 的 TTL，而不是你的。这就是为什么 TTL 不匹配是一个 proxy 检测信号：User-Agent 说是 Windows（TTL 128），但 TCP fingerprint 显示的是 Linux（TTL 64）。

### TCP 窗口大小和缩放

SYN 包中的初始 TCP 窗口大小因操作系统和内核版本而异。现代 Linux 内核（3.x 及更高版本）通常发送 29200 字节的初始窗口，即 `20 * MSS`，其中标准以太网的 MSS 为 1460。一些较新的内核（5.x、6.x）视配置和 `initcwnd` 设置可能使用 64240。Windows 10 和 11 通常在启用窗口缩放的情况下发送 65535，不过确切的值取决于自动调优配置和补丁级别。macOS 也默认为 65535。

窗口缩放因子（一个 TCP 选项）会把 16 位的窗口大小字段放大，以支持更大的接收窗口。Linux 通常使用缩放因子 7（允许窗口最大到 8MB），而 Windows 常用 8。与基础窗口大小相结合，缩放因子创建了一个比任一单值都更细粒度的 fingerprint。

### TCP 选项顺序

SYN 包中 TCP 选项的选择和排序极具区分度。每个操作系统都以固定的、版本特定的顺序排列选项，而内核并不把它作为可配置参数暴露出来。Linux 发送 `MSS, SACK_PERM, TIMESTAMP, NOP, WSCALE`。Windows 发送 `MSS, NOP, WSCALE, NOP, NOP, SACK_PERM`，并在默认配置下省略 TIMESTAMP 选项。macOS 发送 `MSS, NOP, WSCALE, NOP, NOP, TIMESTAMP, SACK_PERM`。

特定选项的存在与否和顺序同等重要。Windows 历史上省略了 TCP timestamps，而 Linux 和 macOS 默认包含它。SACK（Selective Acknowledgment，选择性确认）被所有现代系统支持，但较老或嵌入式系统可能不会通告它。哪些选项出现、以什么顺序出现，这种组合创建了一个签名，像 p0f 这样的工具会用它来与已知操作系统 fingerprint 的数据库进行匹配。

### p0f

[p0f](https://lcamtuf.coredump.cx/p0f3/) 是被动 TCP/IP fingerprinting 的标准工具。它在不生成任何包的情况下观察流量，把 SYN 和 SYN+ACK 包与一个签名数据库进行比对分析。它的签名格式编码了关键的 fingerprinting 字段：

```
version:ittl:olen:mss:wsize,scale:olayout:quirks:pclass
```

`ittl` 是推断出的初始 TTL，`mss` 是最大段大小，`wsize,scale` 是窗口大小（可以是绝对值，或相对于 MSS，比如 `mss*20`），而 `olayout` 是使用简写名称（`mss`、`nop`、`ws`、`sok`、`sack`、`ts`、`eol+N`）的 TCP 选项布局。`quirks` 字段捕捉不寻常的行为，比如 Don't Fragment 标志（`df`）或 DF 包上非零的 IP ID（`id+`）。

p0f 中一个典型的 Linux 4.x+ 签名看起来像 `4:64:0:*:mss*20,7:mss,sok,ts,nop,ws:df,id+:0`。一个 Windows 10 签名可能看起来像 `4:128:0:*:65535,8:mss,nop,ws,nop,nop,sok:df,id+:0`。反机器人服务在内部维护着类似的数据库，把传入连接与已知的操作系统 profile 匹配，并标记与所声明的 User-Agent 不匹配之处。

## TLS fingerprinting

TLS ClientHello 消息在加密建立之前传输，因此它对网络路径上的任何观察者都是可见的。它包含 TLS 版本、支持的 cipher suites、TLS 扩展、支持的椭圆曲线（named groups）以及 EC point formats。每个浏览器和 TLS 库都会产生这些字段的一种特征性组合。

### JA3

JA3 由 Salesforce 的 John Althouse、Jeff Atkinson 和 Josh Atkins 开发，是第一个被广泛采用的 TLS fingerprinting 方法。它把 ClientHello 中的五个字段（TLS 版本、cipher suites、扩展、椭圆曲线、EC point formats）串接起来，用连字符连接每个字段内的值，用逗号分隔这五个字段，然后取所得字符串的 MD5 哈希。

```
JA3 string: 771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0
JA3 hash:   cd08e31494b9531f560d64c695473da9
```

有一个微妙之处：JA3 中的 "TLS version" 字段使用的是 `ClientHello.legacy_version`，而不是 `supported_versions` 扩展。由于 TLS 1.3（RFC 8446）要求客户端为了向后兼容把 `legacy_version` 设为 `0x0303`（TLS 1.2），JA3 的版本字段对现代客户端来说几乎总是 `771`，即使它们支持 TLS 1.3。实际的 TLS 1.3 协商是通过扩展 43（`supported_versions`）进行的，但 JA3 使用的是头部字段。

JA3 必须在哈希之前过滤掉 GREASE 值。GREASE（RFC 8701）是一种机制，浏览器把随机选取的保留值插入到 cipher suites、扩展和其他字段中，以防止协议僵化。有效的 GREASE 值是 `0x0a0a`、`0x1a1a`、`0x2a2a`，依此类推直到 `0xfafa`。每个值都有两个相同的字节，且每个字节的低半字节是 `0x0a`。一个正确的 GREASE 过滤器会检查这两个条件：

```python
def is_grease(value: int) -> bool:
    return (value & 0x0f0f) == 0x0a0a and (value >> 8) == (value & 0xff)
```

!!! warning "JA3 对现代浏览器的局限"
    自 Chrome 110（2023 年 1 月）和 Firefox 114 起，浏览器在每次连接中都随机化 TLS 扩展的顺序。这意味着同一个浏览器在每次连接时都会产生不同的 JA3 哈希，使得 JA3 对识别现代浏览器实际上失去了作用。JA3 对于 fingerprint 那些不实现扩展随机化的非浏览器客户端（Python `requests`、`curl`、自定义机器人）仍然有用。

### JA4

JA4 是 JA3 的继任者，由同一位主要作者（John Althouse）在 FoxIO 开发。它专门设计用来在 TLS 扩展随机化中存活下来，做法是在哈希之前对扩展和 cipher suites 进行排序。其格式由用下划线分隔的三个部分组成：`a_b_c`。

部分 `a` 是一个人类可读的元数据字符串：协议（`t` 表示 TCP，`q` 表示 QUIC）、TLS 版本（`12` 或 `13`）、SNI 是否存在（`d` 表示 domain，`i` 表示 IP）、cipher suites 的数量（两位数）、扩展的数量（两位数），以及第一个和最后一个 ALPN 值（`h2` 表示 HTTP/2，若无则为 `00`）。例如，`t13d1516h2` 表示带 SNI 的 TCP TLS 1.3、15 个 cipher suites、16 个扩展，以及 HTTP/2 ALPN。

部分 `b` 是排序后的 cipher suites 的截断 SHA-256 哈希。部分 `c` 是排序后的扩展与签名算法串接后的截断 SHA-256 哈希。因为两个列表在哈希之前都被排序了，扩展随机化不会影响输出。

Cloudflare、AWS 和其他主要平台已经采用了 JA4。完整的 JA4+ 套件还包括 JA4S（服务器 fingerprinting）、JA4H（HTTP 客户端 fingerprinting）、JA4X（X.509 证书 fingerprinting）和 JA4SSH（SSH fingerprinting）。规范和工具可在 [github.com/FoxIO-LLC/ja4](https://github.com/FoxIO-LLC/ja4) 获取。

### JA3S（服务器 fingerprinting）

JA3S 把同样的概念应用于 ServerHello 消息，但格式更简单，因为服务器选择的是单个 cipher suite，而不是提供一个列表。JA3S 字符串是 `version,cipher,extensions`，其 MD5 哈希标识服务器的 TLS 实现。把 JA3（或 JA4）与 JA3S 配对，创建了一个双向 fingerprint：一个特定的客户端与一个特定的服务器通信，会产生一个可预测的 JA3+JA3S 对，这比任一单独的 fingerprint 都更具区分度。

### proxy 如何与 TLS fingerprint 交互

proxy 的类型决定了 TLS fingerprint 是否被保留。SOCKS5 proxy 和 HTTP CONNECT 隧道在不终止 TLS 的情况下中继 TCP 流，因此目标服务器看到的是原始客户端未经改变的 TLS fingerprint。这是这几种 proxy 类型对 fingerprint 一致性的主要优势。

MITM proxy（它终止 TLS 并向目标重新建立一条新连接）会用它们自己的 TLS fingerprint 替换客户端的。目标看到的是 proxy 软件的 cipher suites 和扩展，而不是浏览器的。如果 proxy 使用像 OpenSSL 或 BoringSSL 这样带默认设置的标准 TLS 库，其 fingerprint 将与任何已知浏览器都不匹配，而这本身就是一个检测信号。

这就是为什么 Pydoll 使用 `--proxy-server`（它创建一条 CONNECT 隧道，保留浏览器的 TLS fingerprint）的做法，对于隐身自动化而言优于外部 MITM proxy 设置。

## HTTP/2 fingerprinting

HTTP/2 连接暴露了一组独立于 TLS 的 fingerprinting 信号。客户端发送的第一个帧是一个 SETTINGS 帧，包含 `HEADER_TABLE_SIZE`、`ENABLE_PUSH`、`MAX_CONCURRENT_STREAMS`、`INITIAL_WINDOW_SIZE`、`MAX_FRAME_SIZE` 和 `MAX_HEADER_LIST_SIZE` 等参数。每个浏览器使用不同的默认值，并包含这些参数的不同子集。

除 SETTINGS 之外，WINDOW_UPDATE 帧大小、初始流的优先级/权重，以及 HTTP/2 伪头（`:method`、`:authority`、`:scheme`、`:path`）的顺序，在不同实现之间也有所不同。Chrome、Firefox 和 Safari 各自产生这些值的一种独特组合。

Akamai 在 Black Hat Europe 2017 上发表了 HTTP/2 fingerprinting 的奠基性研究。他们的 fingerprint 格式把 SETTINGS 值、WINDOW_UPDATE 大小、PRIORITY 帧和伪头顺序串接起来。JA4+ 套件包含用于 HTTP 级别 fingerprinting 的 `JA4H`，涵盖头顺序和头值。

HTTP/2 fingerprinting 对自动化工具特别有效，因为许多机器人框架和 HTTP 库实现了它们自己的 HTTP/2 栈，其默认参数与任何真实浏览器都不匹配。即使一个工具正确地伪造了 TLS fingerprint（使用 curl-impersonate 或类似工具），它的 HTTP/2 SETTINGS 帧仍可能出卖它。

你可以在 [browserleaks.com/http2](https://browserleaks.com/http2) 检查你的 HTTP/2 fingerprint。因为 Pydoll 通过 CDP 控制的是一个真实的 Chrome 实例，HTTP/2 fingerprint 始终是真实的，这是相对于那些以编程方式构造 HTTP 请求的工具的一个固有优势。

## 对浏览器自动化的影响

对于用 Pydoll 进行自动化，实际的要点是：network fingerprinting 是控制一个真实浏览器占优势的一个领域。Chrome 的 TCP/IP 栈、TLS 实现（BoringSSL）和 HTTP/2 栈默认产生真实的 fingerprint。主要风险是环境不匹配：在一台 Linux 服务器上运行 Chrome，而 User-Agent 声称是 Windows，会造成 TCP/IP fingerprint 不一致（TTL 64 而不是 128，Linux 的 TCP 选项顺序而不是 Windows 的）。

对于基于 proxy 的设置，fingerprint 的流向是：你的机器的 TCP/IP 栈生成到 proxy 的连接（proxy 的运营者能看到，但目标看不到），而 proxy 的 TCP/IP 栈生成到目标的连接。目标看到的是 proxy 服务器的 TTL 和 TCP 选项。如果 proxy 运行 Linux（大多数如此），那么无论 User-Agent 如何，TCP fingerprint 都会指示 Linux。这是一个众所周知的检测信号，住宅 proxy 能部分缓解（proxy 端点是一台真实用户的机器，因此它的 TCP fingerprint 是合理的），但数据中心 proxy 无法缓解。

另一方面，TLS 和 HTTP/2 fingerprint 会未经改变地穿过 SOCKS5 和 CONNECT 隧道。这些是浏览器的 fingerprint，而不是 proxy 的。所以，用 Pydoll 通过一条 CONNECT 隧道，目标看到的是真实的 Chrome TLS 和 HTTP/2 fingerprint，与 proxy 的 TCP/IP fingerprint 配对。这种组合与一个真实用户通过 VPN 或企业 proxy 浏览是一致的，而这是一种常见且合法的模式。

## 相关内容

- [Browser fingerprinting](browser-fingerprinting.md)：canvas、WebGL 和 navigator 信号。
- [Behavioral fingerprinting](behavioral-fingerprinting.md)：鼠标、键盘和时序分析。
- [Network fundamentals](../network/network-fundamentals.md)：TCP、TLS 和 HTTP 实际上是如何工作的。
- [Evasion techniques](../../stealth/evasion-techniques.md)：Pydoll 在实践中对这些信号做了什么。
- [Fingerprint injection](../../stealth/fingerprint-injection.md)：在各层次之间应用一致的身份。

## 参考文献

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
