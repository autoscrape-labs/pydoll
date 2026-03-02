# 网络基础

本文档涵盖了驱动互联网的基础网络协议，以及它们如何在自动化场景中暴露或保护您的身份。充分理解 TCP、UDP、OSI 模型和 WebRTC，将使代理配置不再神秘，并且更加有效。

!!! info "模块导航"
    - [网络与安全概述](./index.md)：模块介绍和学习路径
    - [HTTP/HTTPS 代理](./http-proxies.md)：应用层代理
    - [SOCKS 代理](./socks-proxies.md)：会话层代理

    有关 Pydoll 的实际用法，请参阅[代理配置](../../features/configuration/proxy.md)和[浏览器选项](../../features/configuration/browser-options.md)。

## 网络堆栈

浏览器发出的每一个 HTTP 请求都会经过一个分层的网络堆栈。每一层都有特定的职责、协议和安全影响。代理在不同的层运行，运行的层决定了代理能看到、修改和隐藏什么。低层的网络特征即使通过代理也能对您的真实系统进行 fingerprinting，因此理解协议栈有助于了解身份泄露发生在哪里，以及如何防止它们。

### OSI 模型

OSI（开放系统互连）模型由 ISO 于 1984 年制定，提供了一个概念框架来理解网络协议是如何交互的。现实世界的网络使用 TCP/IP 模型（早于 OSI，只有 4 层），但 OSI 术语仍然是描述代理运行位置及其可访问内容的标准方式。

```mermaid
graph TD
    L7[Layer 7: Application - HTTP, FTP, SMTP, DNS]
    L6[Layer 6: Presentation - Encryption, Compression]
    L5[Layer 5: Session - SOCKS]
    L4[Layer 4: Transport - TCP, UDP]
    L3[Layer 3: Network - IP, ICMP]
    L2[Layer 2: Data Link - Ethernet, WiFi]
    L1[Layer 1: Physical - Cables, Radio Waves]

    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

第 7 层（应用层）是面向用户的协议所在层：HTTP、HTTPS、FTP、SMTP 和 DNS 都在这里运行。这一层包含应用程序关心的实际数据，如 HTML 文档、JSON 响应和文件传输。HTTP 代理在这一层运行，因此对请求和响应内容具有完全的可见性。

第 6 层（表示层）处理数据格式转换、加密和压缩。SSL/TLS 通常与这一层关联，因为它承担加密职责，但实际上 TLS 横跨第 4 层到第 6 层，无法干净地映射到单个 OSI 层。对自动化来说重要的是，HTTPS 加密发生在这里，在数据传递到下层之前对第 7 层数据进行加密。

第 5 层（会话层）管理应用程序之间的连接。SOCKS 代理在这一层运行，低于应用层但高于传输层。这个位置使得 SOCKS 与协议无关：它可以代理任何第 7 层协议（HTTP、FTP、SMTP、SSH），而无需理解它们的具体内容。

第 4 层（传输层）提供端到端的数据传输。TCP（面向连接、可靠）和 UDP（无连接、快速）是这一层的主要协议。这一层处理端口号、流量控制和错误纠正。所有代理最终都依赖第 4 层进行实际的数据传输。

第 3 层（网络层）处理网络之间的路由和寻址。IP（互联网协议）在这一层运行，管理 IP 地址和路由决策。您的真实 IP 地址就在这一层，也是代理试图替换它的地方。

第 2 层（数据链路层）管理同一物理网段上的通信。以太网、Wi-Fi 和 PPP 在这里运行，处理 MAC 地址和帧传输。MAC 地址仅在本地网段可见，远程服务器无法直接访问，但它们可能通过 IPv6 SLAAC（将 MAC 嵌入地址中）等协议暴露。

第 1 层（物理层）是实际的硬件：电缆、无线电波和电压水平。与软件自动化几乎无关。

!!! tip "OSI vs TCP/IP"
    TCP/IP 模型（4 层：链路层、互联网层、传输层、应用层）是网络实际使用的模型。OSI（7 层）是教学工具和参考模型。当人们说"第 7 层代理"时，他们使用的是 OSI 术语，但实际实现运行在 TCP/IP 上。

### 层级位置如何影响代理

代理运行的层级决定了它能做什么和不能做什么。

HTTP/HTTPS 代理运行在第 7 层（应用层）。因为它们理解 HTTP，所以可以读取和修改 URL、标头、Cookie 和请求正文。它们可以根据 HTTP 语义智能缓存响应，按 URL 或关键字过滤内容，以及注入身份验证标头。代价是它们只理解 HTTP。它们无法代理 FTP、SMTP、SSH 或其他协议，而且检查 HTTPS 内容需要 TLS 终止，即解密然后重新加密流量。

SOCKS 代理运行在第 5 层（会话层）。因为它们位于应用层之下，所以与协议无关，可以在不修改的情况下代理任何第 7 层协议。HTTPS 流量以端到端加密方式通过，因为 SOCKS 代理无需对其解密。SOCKS5 还支持 UDP，使其能够代理 DNS 查询、VoIP 和其他基于 UDP 的协议。代价是 SOCKS 代理对应用层数据没有可见性：它们无法缓存、按 URL 过滤或检查内容。它们只能按 IP 和端口进行过滤。

!!! note "根本性的权衡"
    更高层（第 7 层）给您更多控制，但灵活性更低。更低层（第 5 层）给您更少控制，但灵活性更高。需要内容控制时选择 HTTP 代理，需要协议灵活性或端到端加密时选择 SOCKS 代理。

### 层泄露问题

即使有完美的第 7 层代理，低层的特征也能暴露您的真实身份。您操作系统的 TCP 堆栈在第 4 层有独特的 fingerprint，由窗口大小、选项顺序和 TTL 值定义。第 3 层的 IP 标头字段（如 TTL 和分片行为）会揭示您的操作系统和网络拓扑。

例如，如果您配置代理来显示 "Windows 10" 的 User-Agent，但您实际 Linux 系统的 TCP fingerprint 在第 4 层与此相矛盾，复杂的检测系统就能将这种不一致标记为强烈的机器人指标。这就是网络级 fingerprinting（在[网络指纹](../fingerprinting/network-fingerprinting.md)中介绍）如此危险的原因：它运行在代理层之下，即使应用层代理完美无缺，也会暴露您的真实系统。

## TCP vs UDP

在第 4 层（传输层），两种根本不同的协议主导着互联网通信。它们代表了相反的设计理念：可靠性与速度。

TCP 是面向连接的。可以把它想象成打电话：您建立连接，确认对方正在收听，可靠地交换数据，然后挂断。每个字节都会被确认、排序，并保证到达。UDP 是无连接的。您发送数据，希望它能到达。没有 handshake，没有确认，没有保证。只有原始的速度和最小的开销。

| 特性 | TCP | UDP |
|---------|-----|-----|
| 连接 | 面向连接（需要 handshake） | 无连接（无需 handshake） |
| 可靠性 | 保证交付，有序数据包 | 尽力而为交付，数据包可能丢失 |
| 速度 | 较慢（可靠性机制带来开销） | 较快（最小开销） |
| 用例 | 网页浏览、文件传输、电子邮件 | 视频流、DNS 查询、游戏 |
| 标头大小 | 最小 20 字节（带选项时可达 60） | 固定 8 字节 |
| 流量控制 | 有（滑动窗口，接收方驱动） | 无（发送方随意传输） |
| 拥塞控制 | 有（网络拥塞时减速） | 无（应用程序的责任） |
| 错误检查 | 广泛（校验和 + 确认） | 基本（仅校验和；在 IPv4 中可选，在 IPv6 中强制） |
| 排序 | 乱序接收时重新排序数据包 | 无排序，按接收顺序交付 |
| 重传 | 自动（丢失的数据包会重传） | 无（应用程序必须处理） |

### TCP 与代理

所有代理协议（HTTP、HTTPS、SOCKS4、SOCKS5）都使用 TCP 作为其控制通道。这是因为代理身份验证和命令交换需要保证交付，代理协议有严格的命令序列（handshake，然后认证，然后数据），代理需要持久连接来跟踪客户端状态。

然而，SOCKS5 还可以代理 UDP 流量，这与 SOCKS4 或 HTTP 代理不同。这使得 SOCKS5 对于代理 DNS 查询、WebRTC 音频/视频、VoIP 和游戏协议至关重要。

!!! danger "UDP 与 IP 泄露"
    大多数浏览器连接使用 TCP（HTTP、WebSocket 等），但 WebRTC 直接使用 UDP，绕过了浏览器的代理配置。这是代理浏览器自动化中 IP 泄露的最常见原因：您的 TCP 流量通过代理传输，而 UDP 流量却泄露了您的真实 IP。

### TCP 三次握手

在传输任何数据之前，TCP 需要三次 handshake 来建立连接。这个协商过程同步序列号，商定窗口大小，并在两端建立连接状态。

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: SYN (Synchronize, seq=x)
    Note over Client,Server: Client requests connection

    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: Server acknowledges and sends its own SYN

    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: Connection established, data transfer begins
```

该过程从客户端发送 SYN（同步）包开始，其中包含一个随机的初始序列号（ISN），例如 `seq=1000`。除了 ISN 之外，还会协商 TCP 选项：窗口大小、最大分段大小（MSS）、时间戳和 SACK 支持。

服务器以 SYN-ACK 响应：它选择自己的随机 ISN（例如 `seq=5000`），并通过设置 `ack=1001`（客户端的 ISN + 1）来确认客户端的 ISN。这个单一的包既建立了服务器到客户端的方向（SYN），又确认了客户端到服务器的方向（ACK）。服务器还会返回自己的 TCP 选项。

然后客户端发送最终的 ACK，确认服务器的 ISN（`ack=5001`）。此时连接在两个方向上都已完全建立，数据传输可以开始。

ISN 是随机化的而非从零开始，以防止 TCP 劫持攻击。如果 ISN 是可预测的，攻击者可以通过猜测序列号将数据包注入到现有连接中。现代系统使用加密随机性来选择 ISN（RFC 6528）。

### TCP Fingerprinting

TCP handshake 揭示了能够 fingerprint 您操作系统的特征。不同操作系统对初始窗口大小、TCP 选项顺序、TTL（生存时间）、窗口缩放因子和时间戳行为使用不同的默认值。这些值由内核设置，而不是浏览器，因此代理无法更改它们。

以下是现代操作系统的示例值。请注意，实际值因操作系统版本、内核配置和网络调优而异：

```
Windows 10/11 (modern builds):
    Window Size: 65535
    MSS: 1460
    Options: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (kernel 5.x+, Ubuntu 20.04+):
    Window Size: 29200
    MSS: 1460
    Options: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64

macOS (Monterey+):
    Window Size: 65535
    TTL: 64
```

这些差异烙印在内核中。代理无法更改它们，因为它们是由您的操作系统而不是浏览器设置的。这就是复杂的检测系统即使通过代理也能识别您的原因。

!!! warning "代理的局限性"
    HTTP 和 SOCKS 代理运行在 TCP 层之上。它们无法修改 TCP handshake 特征。您操作系统的 TCP fingerprint 始终暴露给代理服务器以及您和代理之间的任何网络观察者。只有 VPN 级别的解决方案或操作系统级的 TCP 堆栈配置才能解决这个问题。

!!! note "TCP Fingerprinting 之外"
    TCP handshake 只是第一个 fingerprinting 机会。紧接着，TLS handshake 会揭示另一个独特的 fingerprint，即 JA3/JA4。详情请参阅[网络指纹](../fingerprinting/network-fingerprinting.md)。

### UDP

与 TCP 可靠、面向连接的方法不同，UDP 是一种"发射后不管"的协议。它以可靠性换取最小的延迟和开销，使其成为实时应用的理想选择，因为在这些应用中速度比完美交付更重要。

UDP 数据报只有 8 字节标头（相比 TCP 的 20-60 字节），包含源端口、目标端口、长度和校验和。没有连接建立，没有可靠性保证，没有流量控制，没有拥塞控制。如果数据包丢失，应用程序必须自行决定是否以及如何处理。

UDP 适用于实时通信（通过 WebRTC 和 VoIP 进行的语音/视频通话）、游戏（低延迟的状态更新）、流媒体（偶尔的帧丢失可以接受）和 DNS 查询（小型请求/响应对，应用程序处理重试）。它不适合文件传输、网页浏览、电子邮件或数据库，这些都需要可靠、有序的交付。

DNS 在自动化上下文中是一个特别重要的例子。DNS 使用 UDP 是因为查询通常很小，并且受益于 UDP 零 handshake 的开销优势。虽然 EDNS0（RFC 6891）将最大 UDP DNS 负载增加到了原始 512 字节限制之上，但大多数查询仍然很紧凑。如果响应未在超时时间内到达，DNS 客户端会在应用层处理重试。

对于浏览器自动化，UDP 的关键问题是 WebRTC 使用它进行实时音频和视频，DNS 查询使用它进行域名解析，而大多数代理（HTTP、HTTPS、SOCKS4）只处理 TCP。除非您显式配置 UDP 代理，否则这些流量会绕过您的代理并泄露您的真实 IP。

| 代理类型 | UDP 支持 | 说明 |
|------------|-------------|-------|
| HTTP 代理 | 否 | 只代理基于 TCP 的 HTTP/HTTPS |
| HTTPS 代理 (CONNECT) | 否 | CONNECT 方法只建立 TCP 隧道 |
| SOCKS4 | 否 | 仅 TCP 协议 |
| SOCKS5 | 是 | 通过 `UDP ASSOCIATE` 命令支持 UDP 中继 |
| VPN | 是 | 隧道传输所有 IP 流量（TCP 和 UDP） |

为了在浏览器自动化中实现真正的匿名，您需要：支持 UDP 的 SOCKS5 代理并将 WebRTC 配置为使用它、完全禁用 WebRTC（这会破坏视频会议）、隧道传输所有流量的 VPN，或者浏览器标志 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`。

### QUIC 与 HTTP/3

现代浏览器越来越多地使用 QUIC（RFC 9000），这是一种基于 UDP 的传输协议，为 HTTP/3 提供支持。由于 QUIC 运行在 UDP 上，它与 WebRTC 和 DNS 存在相同的代理绕过问题：大多数 HTTP 代理无法处理 QUIC 流量，它可能会泄露到您的代理配置之外。

在自动化场景中，考虑使用 `--disable-quic` Chrome 标志禁用 QUIC，以强制使用基于 TCP 的 HTTP/2，确保所有网页流量通过您的代理。QUIC 还有自己的 fingerprinting 特征，类似于 TLS 的 JA3，增加了另一个检测向量。

## WebRTC 与 IP 泄露

WebRTC（Web 实时通信）是 W3C 标准化的浏览器 API，支持浏览器之间直接进行点对点的音频、视频和数据通信，无需插件或中介服务器。虽然 WebRTC 对实时应用功能强大，但它是代理浏览器自动化中最大的 IP 泄露源。

### WebRTC 如何泄露您的 IP

WebRTC 专为直接的点对点连接设计，优先考虑低延迟而非隐私。为了建立 P2P 连接，WebRTC 必须发现您的真实公共 IP 地址并与远程对等方共享，即使您的浏览器配置为使用代理。

问题是这样展开的：您的浏览器使用代理处理 HTTP/HTTPS 流量（即 TCP），但 WebRTC 使用 STUN 服务器通过 UDP 发现您的真实公共 IP。STUN 查询绕过代理，因为大多数代理只处理 TCP。您的真实 IP 被发现并作为连接协商的一部分与远程对等方共享。页面上的 JavaScript 可以读取这些"ICE 候选者"并将您的真实 IP 发送到网站的服务器。

!!! danger "WebRTC 泄露的严重性"
    即使正确配置了 HTTP 代理、HTTPS 代理工作正常、DNS 查询被代理、User-Agent 被伪造、canvas fingerprinting 被缓解，WebRTC 仍然可以在毫秒内泄露您的真实 IP。这是因为 WebRTC 运行在浏览器的代理层之下，直接与操作系统的网络堆栈交互。

### ICE 过程

WebRTC 使用 ICE（交互式连接建立，RFC 8445）来发现可能的连接路径并选择最佳路径。这个过程本身就会揭示您的网络拓扑，它收集三种类型的候选者。

```mermaid
sequenceDiagram
    participant Browser
    participant STUN as STUN Server
    participant TURN as TURN Relay
    participant Peer as Remote Peer

    Note over Browser: WebRTC connection initiated

    Browser->>Browser: Gather local IP addresses<br/>(LAN interfaces)
    Note over Browser: Local candidate:<br/>192.168.1.100:54321

    Browser->>STUN: STUN Binding Request (over UDP)
    Note over STUN: STUN server discovers public IP<br/>(bypasses proxy!)
    STUN->>Browser: STUN Response with real public IP
    Note over Browser: Server reflexive candidate:<br/>203.0.113.45:54321

    Browser->>TURN: Allocate relay (if needed)
    TURN->>Browser: Relay address assigned
    Note over Browser: Relay candidate:<br/>198.51.100.10:61234

    Browser->>Peer: Send all ICE candidates<br/>(local + public + relay)
    Note over Peer: Now knows your:<br/>- LAN IP<br/>- Real public IP<br/>- Relay address

    Peer->>Browser: Send ICE candidates

    Note over Browser,Peer: ICE negotiation: try direct P2P first

    alt Direct P2P succeeds
        Browser<<->>Peer: Direct connection (bypasses proxy entirely!)
    else Direct P2P fails (firewall/NAT)
        Browser->>TURN: Use TURN relay
        TURN<<->>Peer: Relayed connection
        Note over Browser,Peer: Higher latency, but works
    end
```

### ICE 候选者类型

ICE 发现三种类型的候选者（可能的连接端点），每种类型揭示关于您网络的不同信息。

**主机候选者**是您的本地局域网 IP 地址。浏览器枚举所有本地网络接口，并为每个接口创建候选者。这会揭示您在专用网络上的本地 IP 地址、网络拓扑（是否存在 VPN 接口、虚拟机网桥）以及网络接口的数量。

```javascript
// Example host candidates
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
```

现代浏览器（Chrome 75+、Firefox 78+、Safari）通过在未授予媒体权限（摄像头/麦克风）时将本地 IP 地址替换为临时的 mDNS 名称（例如 `a1b2c3d4.local`）来缓解主机候选者泄露。然而，无论 mDNS 如何，服务器自反候选者（您的公共 IP）仍然会暴露。

**服务器自反候选者**是 STUN 服务器看到的您的公共 IP。浏览器向公共 STUN 服务器发送请求，后者回复您的公共 IP 地址。这就是人们常说的泄露：您的代理显示一个 IP，但 WebRTC 揭示了您的真实 IP，连同您的 NAT 类型、外部端口映射和 ISP 信息。

```javascript
// Server reflexive candidate (your real public IP)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**中继候选者**是在直接 P2P 失败时用作后备的 TURN 服务器地址。根据 TURN 服务器实现的不同，中继候选者的 `raddr`（远程地址）字段中可能仍然包含您的真实 IP。

```javascript
// Relay candidate (TURN server address)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

### STUN 协议

STUN（NAT 会话穿透实用工具，RFC 8489）是一个简单的基于 UDP 的请求-响应协议。它的工作很直接：客户端询问"您看到的我是什么 IP？"，服务器回复客户端的公共 IP 和端口。

客户端发送一个绑定请求，其中包含一个魔法 Cookie（`0x2112A442`，RFC 定义的固定值）和一个随机的 12 字节事务 ID。服务器响应一个绑定成功响应，其中包含一个 `XOR-MAPPED-ADDRESS` 属性，包含从服务器角度看到的客户端公共 IP 和端口。

响应中的 IP 地址与魔法 Cookie 和事务 ID 进行了异或运算。这不是为了安全，而是为了 NAT 兼容性：一些 NAT 设备会错误地修改数据包负载中的 IP 地址，异或运算混淆了地址以防止这种干扰。

浏览器常用的公共 STUN 服务器包括 `stun.l.google.com:19302`（Google）、`stun1.l.google.com:19302`（Google）、`stun.services.mozilla.com`（Mozilla）和 `stun.stunprotocol.org:3478`。

### 为什么代理无法阻止 WebRTC 泄露

WebRTC 泄露发生有几个相互强化的原因。首先，WebRTC 使用 UDP，而大多数代理（HTTP、HTTPS CONNECT、SOCKS4）只处理 TCP。只有 SOCKS5 支持 UDP，即便如此，浏览器也必须显式配置为通过它路由 WebRTC。

其次，WebRTC 是一个运行在 HTTP 层之下的浏览器 API。它直接访问操作系统网络堆栈，绕过为 HTTP/HTTPS 配置的代理设置。STUN 查询直接进入网络接口，操作系统路由表决定它们的路径，而不是浏览器的代理配置。只有 VPN 级别的路由才能拦截它们。

第三，WebRTC 枚举所有网络接口（物理以太网、Wi-Fi、VPN 适配器、虚拟机网桥），包括未用于常规浏览的接口。这会泄露您的内部网络拓扑。

最后，网页可以通过 JavaScript 使用 `RTCPeerConnection.onicecandidate` 事件读取 ICE 候选者，用简单的正则表达式从候选者字符串中提取 IP 地址，并将您的真实 IP 发送到他们的跟踪服务器。

### 在 Pydoll 中防止 WebRTC 泄露

Pydoll 提供了多种策略来防止 WebRTC IP 泄露。

**方法 1：强制 WebRTC 仅使用代理路由（推荐）**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # Adds --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Pydoll 提供了一个便捷的 `webrtc_leak_protection` 属性来管理底层的 Chrome 标志。这会在没有代理支持 UDP 时禁用 UDP，强制 WebRTC 仅使用 TURN 中继（不使用直接 P2P），并阻止对公共服务器的 STUN 查询。代价是视频通话的延迟更高，因为直接 P2P 连接被禁用。

**方法 2：完全禁用 WebRTC**

```python
options.add_argument('--disable-features=WebRTC')
```

这会完全禁用 WebRTC API，消除通过此向量发生 IP 泄露的任何可能性。代价是所有依赖 WebRTC 的网站（视频会议、语音通话）将无法工作。请注意，此标志应在您的特定 Chrome 版本上测试，因为功能标志名称可能因版本而异。

**方法 3：通过浏览器首选项限制 WebRTC**

```python
options.browser_preferences = {
    'webrtc': {
        'ip_handling_policy': 'disable_non_proxied_udp',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        'allow_legacy_tls_protocols': False
    }
}
```

这与方法 1 效果相同，但通过首选项而非命令行标志实现。`multiple_routes_enabled` 防止使用多个网络路径，`nonproxied_udp_enabled` 阻止不通过代理的 UDP。

**方法 4：使用支持 UDP 的 SOCKS5 代理**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

SOCKS5 可以通过其 `UDP ASSOCIATE` 命令代理 UDP，允许 WebRTC 的 STUN 查询通过代理。这需要实际支持 UDP 中继的 SOCKS5 代理，而并非所有代理都支持。

!!! warning "SOCKS5 身份验证"
    Chrome 不支持通过 `--proxy-server` 标志内联 SOCKS5 身份验证（例如 `socks5://user:pass@host:port`）。Pydoll 提供了内置的 `SOCKS5Forwarder` 来解决此限制，它运行一个本地无需身份验证的 SOCKS5 代理，将流量转发到远程经过身份验证的代理，代替 Chrome 处理用户名/密码 handshake。详情请参阅[代理配置](../../features/configuration/proxy.md)。

### 测试 WebRTC 泄露

您可以通过访问 [browserleaks.com/webrtc](https://browserleaks.com/webrtc) 并检查"Public IP Address"部分来手动测试。如果您看到的是您的真实 IP 而不是代理 IP，则说明存在泄露。

使用 Pydoll 进行自动化测试：

```python
import asyncio
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_webrtc_leak():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/webrtc')

        await asyncio.sleep(3)

        ips = await tab.execute_script('''
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ''')

        print("Detected IPs:", ips)
        # Should only show proxy IP, not your real IP

asyncio.run(test_webrtc_leak())
```

!!! danger "务必测试 WebRTC 泄露"
    切勿假设您的代理配置能阻止 WebRTC 泄露。始终使用 [browserleaks.com/webrtc](https://browserleaks.com/webrtc) 或 [ipleak.net](https://ipleak.net) 进行验证。即使是单个 WebRTC 泄露也会立即危及您的整个代理设置，因为网站现在知道了您的真实位置、ISP 和网络拓扑。

### 网站如何利用 WebRTC 泄露

网站可以用几行 JavaScript 有意触发 WebRTC 来提取您的真实 IP：

```javascript
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);

        if (ipMatch) {
            const realIP = ipMatch[1];
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

这段代码创建一个 RTCPeerConnection，触发 ICE 候选者收集（联系 STUN 服务器），用正则表达式从候选者中提取 IP 地址，并将您的真实 IP 发送到跟踪服务器。按照上述方法禁用 WebRTC 或强制仅使用代理路由可以防止这种情况。

## 总结

代理运行在网络堆栈的特定层：HTTP 在第 7 层，SOCKS 在第 5 层。层级决定了代理能看到、修改和隐藏什么。TCP fingerprint（窗口大小、选项、TTL）从低层泄露，即使通过代理也会揭示您的真实操作系统。UDP 流量（包括 WebRTC 和 DNS）除非显式配置，否则通常会绕过代理。WebRTC 是 IP 泄露最常见的来源，只有 SOCKS5 或 VPN 才能有效代理 UDP 流量。现代浏览器还使用 QUIC（基于 UDP 的 HTTP/3），增加了另一个潜在的绕过向量。

**后续步骤：**

- [HTTP/HTTPS 代理](./http-proxies.md)：应用层代理
- [SOCKS 代理](./socks-proxies.md)：会话层、协议无关的代理
- [网络指纹](../fingerprinting/network-fingerprinting.md)：TCP/IP 和 TLS fingerprinting 技术
- [代理配置](../../features/configuration/proxy.md)：实用 Pydoll 代理设置

## 参考资料

- RFC 793: Transmission Control Protocol (TCP) - https://tools.ietf.org/html/rfc793
- RFC 768: User Datagram Protocol (UDP) - https://tools.ietf.org/html/rfc768
- RFC 8489: Session Traversal Utilities for NAT (STUN) - https://tools.ietf.org/html/rfc8489
- RFC 8445: Interactive Connectivity Establishment (ICE) - https://tools.ietf.org/html/rfc8445
- RFC 8656: Traversal Using Relays around NAT (TURN) - https://tools.ietf.org/html/rfc8656
- RFC 6528: Defending Against Sequence Number Attacks - https://tools.ietf.org/html/rfc6528
- RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport - https://tools.ietf.org/html/rfc9000
- W3C WebRTC 1.0: Real-Time Communication Between Browsers - https://www.w3.org/TR/webrtc/
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
