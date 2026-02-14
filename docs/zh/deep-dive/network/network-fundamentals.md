# 网络基础

本文档涵盖了驱动互联网的基础网络协议，以及它们如何在自动化场景中暴露或保护您的身份。在深入研究代理协议之前，理解 TCP、UDP、OSI 模型和 WebRTC 是 **至关重要** 的。

!!! info "模块导航"
    - **[← 网络与安全概述](./index.md)** - 模块介绍和学习路径
    - **[→ HTTP/HTTPS 代理](./http-proxies.md)** - 应用层代理
    - **[→ SOCKS 代理](./socks-proxies.md)** - 会话层代理
    
    有关 Pydoll 的实际用法，请参阅 **[代理配置](../../features/configuration/proxy.md)** 和 **[浏览器选项](../../features/configuration/browser-options.md)**。

!!! warning "基础先行"
    这是理解代理协议的 **先决知识**。不掌握这些基础知识，代理配置就会变成“试错式”的猜测。

## 简介：网络堆栈

您的浏览器发出的每一个 HTTP 请求（每一次代理连接，每一条 WebSocket 消息）都会经过一个 **分层的网络堆栈**。每一层都有特定的职责、协议和安全影响。

**为什么这对自动化很重要：**

- 代理在 **不同的层级** 运行，各自具有不同的能力
- 底层网络特征可以 **指纹识别** 您的真实系统（即使通过代理）
- 理解协议栈可以揭示 **身份泄露发生在哪里** 以及如何防止它们

在深入研究代理之前，我们需要了解它们运行所在的网络堆栈。这不是抽象的理论。这里的每一个概念都对浏览器自动化的隐蔽性、性能和可靠性有着 **直接的影响**。

### OSI 模型背景

OSI（开放系统互连）模型由国际标准化组织（ISO）于 1984 年制定，它提供了一个 **概念框架** 来理解网络协议是如何交互的。虽然现实世界的网络主要使用 TCP/IP 模型（早于 OSI），但理解 OSI 分层有助于概念化 **代理在何处运行** 以及 **它们能检查或修改什么**。

```mermaid
graph TD
    L7[第 7 层：应用层 - HTTP, FTP, SMTP]
    L6[第 6 层：表示层 - SSL/TLS, 加密]
    L5[第 5 层：会话层 - SOCKS]
    L4[第 4 层：传输层 - TCP, UDP]
    L3[第 3 层：网络层 - IP, ICMP]
    L2[第 2 层：数据链路层 - Ethernet, WiFi]
    L1[第 1 层：物理层 - 电缆, 无线电波]
    
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

#### 逐层分解

**第 7 层 (应用层)**：面向用户的协议所在层。HTTP、HTTPS、FTP、SMTP、DNS 都在这里运行。这一层包含您的应用程序关心的 **实际数据**：HTML 文档、JSON 响应、文件传输。HTTP 代理在这一层运行，使其对请求/响应内容具有 **完全的可见性**。

**第 6 层 (表示层)**：处理数据格式转换、加密和压缩。SSL/TLS 加密发生在这里（尽管 TLS 通常被认为跨越了第 5-6 层）。**HTTPS 加密** 发生在这里，它在将第 7 层数据传递到第 5 层之前对其进行加密。

**第 5 层 (会话层)**：管理应用程序之间的连接。SOCKS 代理在这一层运行，低于应用层但高于传输层。这个位置使得 SOCKS **与协议无关**，它可以代理任何第 7 层协议（HTTP、FTP、SMTP、SSH），而无需理解它们的具体内容。

**第 4 层 (传输层)**：提供端到端的数据传输。TCP（面向连接、可靠）和 UDP（无连接、快速）是主要的协议。这一层处理 **端口号**、**流量控制** 和 **错误纠正**。所有代理最终都依赖第 4 层进行实际的数据传输。

**第 3 层 (网络层)**：处理网络间的路由和寻址。IP（互联网协议）在这一层运行，管理 **IP 地址** 和 **路由决策**。这是您 **真实 IP 地址** 所在的地方，也是代理试图替换它的地方。

**第 2 层 (数据链路层)**：管理同一物理网段上的通信。以太网、Wi-Fi 和 PPP 在此运行，处理 **MAC 地址** 和 **帧传输**。这一层的网络指纹可以揭示 **物理网络特征**。

**第 1 层 (物理层)**：实际的硬件（电缆、无线电波、电压水平）。虽然与软件很少相关，但物理层特征可以被测量（信号时序、电气特性）以进行 **高级指纹识别**。

!!! tip "OSI vs TCP/IP 模型"
    **TCP/IP 模型**（4 层：链路层、互联网层、传输层、应用层）是网络实际使用的模型。OSI（7 层）是一个 **教学工具** 和参考模型。当人们说“第 7 层代理”时，他们使用的是 OSI 术语，但实际实现使用的是 TCP/IP。

#### 为什么分层位置对代理很重要

代理运行的层级决定了它的 **能力** 和 **局限性**：

**HTTP/HTTPS 代理 (第 7 层 - 应用层)**：

- **完全的 HTTP 可见性**：可以读取/修改 URL、标头、Cookie、请求正文
- **智能缓存**：可以根据 HTTP 语义缓存响应
- **内容过滤**：可以拦截特定的 URL 或关键字
- **身份验证集成**：可以添加身份验证标头
- **仅限 HTTP 的局限性**：无法代理 FTP、SMTP、SSH 或其他协议
- **需要 TLS 终止**：必须解密 HTTPS 才能检查内容

**SOCKS 代理 (第 5 层 - 会话层)**：

- **协议无关**：可以代理任何第 7 层协议 (HTTP, FTP, SSH 等)
- **无需 TLS 终止**：HTTPS 以加密方式通过 (端到端安全)
- **支持 UDP** (SOCKS5)：可以代理 DNS、VoIP、游戏协议
- **无内容可见性**：无法检查或修改应用层数据
- **无智能缓存**：不理解 HTTP 语义
- **无基于 URL 的过滤**：无法拦截特定 URL，只能拦截 IP:端口 组合

!!! warning "根本性的权衡"
    **更高层** (第 7 层) = 更多控制, 更少灵活性
    **更低层** (第 5 层) = 更少控制, 更多灵活性
    
    根据您的需求进行选择：HTTP 代理用于 **内容控制**，SOCKS 代理用于 **协议灵活性** 和 **端到端加密**。

#### 实际含义：“层泄露”问题

理解分层揭示了一个关键的安全问题：**特征会跨层泄露**。

即使有完美的第 7 层代理 (HTTP)，更低层的特征也会暴露您的真实身份：

- **第 4 层 (TCP)**：您操作系统的 TCP 堆栈具有独特的“指纹”（窗口大小、选项、TTL）
- **第 3 层 (网络层)**：IP 标头字段（TTL、分片）揭示了操作系统和网络拓扑
- **第 2 层 (数据链路层)**：MAC 地址供应商揭示了硬件制造商

**示例**：您配置了一个代理来显示 "Windows 10" 的 User-Agent，但是您 **实际 Linux 系统的 TCP 指纹** (第 4 层) 与此相矛盾。机器人检测立即可辨。

这就是为什么 **网络级指纹识别**（在 [网络指纹](../fingerprinting/network-fingerprinting.md) 中涵盖）如此危险：它在 **代理层之下** 运行，即使应用层代理完美无缺，也会暴露您的真实系统。

### TCP vs UDP：传输层协议

在第 4 层 (传输层)，两种根本不同的协议主导着互联网通信：**TCP (传输控制协议)** 和 **UDP (用户数据报协议)**。它们代表了相反的设计理念：可靠性 vs 速度，开销 vs 效率。

#### 根本区别

**TCP** 就像打电话：您建立连接，确认对方正在收听，可靠地交换数据，然后挂断。每个字节都会被确认、排序，并保证到达。

**UDP** 就像在拥挤的房间里大喊：您发送消息，希望它能到达。没有保证，没有确认，没有连接设置。只有原始的速度。

| 特性 | TCP | UDP |
|---|---|---|
| **连接** | 面向连接 (需要握手) | 无连接 (无需握手) |
| **可靠性** | 保证交付, 有序数据包 | 尽力而为交付, 数据包可能丢失 |
| **速度** | 较慢 (可靠性机制带来开销) | 较快 (最小开销) |
| **用例** | 网页浏览, 文件传输, 电子邮件 | 视频流, DNS 查询, 游戏 |
| **标头大小** | 最小 20 字节 (带选项时可达 60) | 固定 8 字节 |
| **流量控制** | 有 (滑动窗口, 接收方驱动) | 无 (发送方随意传输) |
| **拥塞控制** | 有 (网络拥塞时减速) | 无 (应用程序的责任) |
| **错误检查** | 广泛 (校验和 + 确认) | 基本 (仅校验和, 可选丢弃) |
| **排序** | 如果接收顺序混乱，则重新排序数据包 | 无排序, 按接收顺序交付数据包 |
| **重传** | 自动 (丢失的数据包会重传) | 无 (应用程序必须处理) |

#### 为什么这对代理和自动化很重要

**所有代理协议都使用 TCP**。HTTP 代理、HTTPS 代理、SOCKS4 和 SOCKS5 都依赖 TCP 来进行其控制通道，因为：

1.  **可靠性**：代理身份验证和命令交换需要保证交付
2.  **顺序性**：代理协议有严格的命令序列 (握手 → 认证 → 数据)
3.  **连接状态**：代理需要持久连接来跟踪客户端

然而，**SOCKS5 可以代理 UDP 流量** (与 SOCKS4 或 HTTP 代理不同)，这使其对于以下方面至关重要：

- **DNS 查询**：无需 TCP 开销的快速域名解析
- **WebRTC**：实时音频/视频 (使用 UDP 以实现低延迟)
- **VoIP**：语音通信需要速度而非可靠性
- **游戏协议**：低延迟的游戏状态更新

!!! danger "UDP = IP 泄露风险"
    大多数浏览器连接使用 TCP (HTTP, WebSocket 等)。但是 WebRTC 直接使用 **UDP**，绕过了浏览器的网络堆栈和代理配置。这是代理浏览器自动化中 **IP 泄露的头号原因**。当 TCP 流量通过代理时，您的真实 IP 通过 UDP 泄露出去。

#### TCP 三次握手：建立连接

在传输任何数据之前，TCP 需要 **三次握手** 来建立连接。这个协商过程同步序列号，商定窗口大小，并在两端建立连接状态。

```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    Client->>Server: SYN (同步, seq=x)
    Note over Client,Server: 客户端请求连接
    
    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: 服务器确认并发送自己的 SYN
    
    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: 连接已建立
    
    Note over Client,Server: 数据传输开始
```

**步骤分解：**

**1. SYN (同步)**：客户端发起连接

- 客户端选择一个 **随机的初始序列号 (ISN)** (例如, `seq=1000`)
- 向服务器发送带有此 ISN 的 SYN 包
- 协商 TCP 选项：窗口大小、最大分段大小 (MSS)、时间戳、SACK 支持

**2. SYN-ACK (同步-确认)**：服务器响应

- 服务器选择自己的 **随机 ISN** (例如, `seq=5000`)
- 确认客户端的 ISN：`ack=1001` (客户端的 ISN + 1)
- 同时发送 SYN (以建立服务器→客户端方向) 和 ACK (以确认客户端→服务器方向)
- 返回自己的 TCP 选项

**3. ACK (确认)**：客户端确认

- 客户端确认服务器的 ISN：`ack=5001` (服务器的 ISN + 1)
- 现在连接在两个方向上都 **已建立**
- 数据传输可以开始

!!! tip "为什么 ISN 是随机的？"
    ISN 是随机化的 (不从 0 开始) 以防止 **TCP 劫持攻击**。如果 ISN 是可预测的，攻击者可以通过猜测序列号将数据包注入到现有连接中。现代系统使用加密随机性来选择 ISN (RFC 6528)。

**安全含义：TCP 指纹**

TCP 握手揭示了许多 **指纹识别您的操作系统** 的特征：

- **初始窗口大小**：不同操作系统的默认值不同 (Windows: 8192, Linux: 5840, macOS: 65535)
- **TCP 选项**：选项的顺序和存在因操作系统而异 (MSS, SACK, Timestamps, Window Scale)
- **TTL (生存时间)**：默认值不同 (Windows: 128, Linux: 64, macOS: 64)
- **窗口缩放因子**：揭示缓冲区大小偏好
- **时间戳值**：时序模式揭示系统正常运行时间和时钟分辨率

**TCP 握手指纹示例 (用 Wireshark 捕获)**：

```
Windows 10:
    Window Size: 8192
    MSS: 1460
    Options: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (Ubuntu):
    Window Size: 29200
    MSS: 1460
    Options: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64
```

这些差异 **烙印在内核中**。代理无法更改它们，因为它们是由您的 **操作系统** 而不是浏览器设置的。这就是为什么复杂的检测系统 **即使通过代理** 也能识别您的原因。

!!! warning "代理的局限性"
    HTTP 和 SOCKS 代理运行在 **TCP 层之上**。它们无法修改 TCP 握手特征。您操作系统的 TCP 指纹 **始终暴露** 给代理服务器 (以及任何网络观察者)。只有 **VPN 级别的解决方案** 或 **操作系统级的 TCP 堆栈欺骗** 才能解决这个问题。

**为什么 TCP 对代理很重要：**

- **可靠的代理身份验证**：通过 TCP 发送的凭据不会丢失
- **持久连接**：单个 TCP 连接可以处理多个 HTTP 请求 (HTTP/1.1 keep-alive, HTTP/2)
- **有序交付**：代理命令按顺序执行 (对于身份验证流程至关重要)
- **指纹暴露**：TCP 握手特征揭示了您的真实操作系统

#### UDP 特性：速度至上，无需保证

与 TCP 可靠、面向连接的方法不同，UDP 是一种 **“发射后不管”** 的协议。它以可靠性换取 **最小的延迟和开销**，使其成为实时应用的理想选择，因为在这些应用中，速度比完美交付更重要。

**UDP 数据报结构 (RFC 768)**：

```python
# UDP 数据报结构 (实际标头格式)
{
    'source_port': 12345,        # 16 位 - 可选 (0 = 不期望响应)
    'destination_port': 53,       # 16 位 - 必需 (应用程序标识符)
    'length': 42,                 # 16 位 - 数据报大小 (标头 + 数据)
    'checksum': 0x1234,          # 16 位 - 在 IPv4 中可选, 在 IPv6 中必需
    'data': b'...'               # 变量 - 应用程序数据
}
# 总标头: 8 字节 (而 TCP 为 20-60 字节)
```

**关键 UDP 特性：**

1.  **无连接建立**：没有握手，没有状态。只需发送数据包，希望它能到达。
2.  **不可靠**：数据包可能丢失、重复或乱序到达。应用程序必须处理这些情况。
3.  **无流量控制**：发送方随心所欲地快速传输。没有机制来适应接收方的容量。
4.  **无拥塞控制**：UDP 不会检测或响应网络拥塞。可能会压垮网络。
5.  **最小标头**：只有 8 字节，而 TCP 为 20-60 字节。更低的开销意味着更多带宽用于数据。
6.  **基于端口的多路复用**：像 TCP 一样，使用端口号来识别应用程序 (DNS=53, WebRTC=动态)

**何时使用 UDP：**

**好的用例：**
- **实时通信**：语音/视频通话 (WebRTC, VoIP)，其中旧数据无用
- **游戏**：速度 > 准确性的低延迟游戏状态更新
- **流媒体**：视频/音频，其中偶尔的帧丢失是可以接受的
- **DNS 查询**：小的请求/响应，其中重传由应用程序处理
- **网络发现**：广播/多播协议 (DHCP, mDNS)

**坏的用例：**
- **文件传输**：需要应用层可靠性 (所以只管用 TCP)
- **网页浏览**：需要有序、可靠的交付 (HTTP/3 over QUIC 是例外)
- **电子邮件, 数据库**：绝对需要可靠性

**UDP 和 DNS：一个关键示例**

DNS (域名系统) 使用 UDP 是因为：

- **消息小**：DNS 查询和响应通常适合单个数据包 (<512 字节)
- **解析快**：没有握手开销意味着更快的查找
- **应用层重试**：如果超时未收到响应，DNS 客户端会重试
- **广泛使用**：全球每秒数十亿次 DNS 查询

```python
# 典型的基于 UDP 的 DNS 查询
Source Port: 54321 (随机临时端口)
Destination Port: 53 (DNS 标准端口)
Length: 29 字节 (8 字节标头 + 21 字节查询)
Checksum: 0x1a2b
Data: "google.com A?" (查询 A 记录)
```

**为什么 UDP 对浏览器自动化很重要：**

- **WebRTC 使用 UDP** 进行实时音频/视频 (无法通过 HTTP 代理)
- **DNS 查询使用 UDP** (如果不通过代理，可能会泄露 DNS 请求)
- **SOCKS5 支持 UDP** (与 SOCKS4 或 HTTP 代理不同)
- **UDP 会绕过代理**，除非明确配置
- **没有序列号** 意味着无法通过 ISN 进行指纹识别 (与 TCP 不同)

!!! danger "WebRTC UDP 泄露"
    这是个关键问题：您的浏览器通过 **UDP 进行 DNS 查询**，并通过 **UDP 建立 WebRTC 连接**。大多数代理配置只覆盖 **TCP 流量** (HTTP, HTTPS, WebSocket)。
    
    结果：您的 TCP 流量 (网页, API 调用) 通过代理使用代理的 IP，但您的 **UDP 流量直接泄露了您的真实 IP**。
    
    这就是为什么即使使用了代理，网站仍然可以通过 WebRTC 发现您的真实 IP。它正在 **直接使用 UDP**，完全绕过了您的代理。

**按协议划分的 UDP 代理支持：**

| 代理类型 | UDP 支持 | 说明 |
|---|---|---|
| HTTP 代理 | 否 | 只代理基于 TCP 的 HTTP/HTTPS |
| HTTPS 代理 (CONNECT) | 否 | CONNECT 方法只建立 TCP 隧道 |
| SOCKS4 | 否 | 仅 TCP 协议 |
| SOCKS5 | 是 | 通过 `UDP ASSOCIATE` 命令支持 UDP 中继 |
| VPN | 是 | 隧道传输所有 IP 流量 (TCP 和 UDP) |

**实际含义：**

为了在浏览器自动化中实现 **真正的匿名**，您需要 **以下之一**：
1.  **SOCKS5 代理** (以代理 UDP) + 将 WebRTC 配置为使用 SOCKS5
2.  **完全禁用 WebRTC** (防止 UDP 泄露，但会破坏视频会议)
3.  **VPN** (隧道传输所有流量, TCP 和 UDP)
4.  **浏览器标志**：`--force-webrtc-ip-handling-policy=disable_non_proxied_udp`

!!! tip "UDP 指纹"
    与 TCP 不同，UDP 没有握手，标头字段也最少，使其 **更难被指纹识别**。然而，**时序特征** (数据包间隔、抖动) 和 **负载模式** 仍然可以揭示应用程序行为。

## WebRTC 和 IP 泄露

WebRTC (Web 实时通信) 是 W3C 标准化的浏览器 API，支持浏览器之间直接进行 **点对点** 的音频、视频和数据通信，无需插件或中介服务器。虽然 WebRTC 对实时应用功能强大，但它也是代理浏览器自动化中 **最大的 IP 泄露源**。

### 为什么 WebRTC 会泄露您的 IP

WebRTC 专为 **直接的点对点连接** 而设计，优先考虑低延迟而非隐私。为了建立 P2P 连接，WebRTC 必须发现您的 **真实公共 IP 地址** 并与远程对等方共享，即使您的浏览器配置为使用代理。

**根本问题：**
1.  您的浏览器使用代理处理 HTTP/HTTPS (TCP 流量)
2.  WebRTC 使用 **STUN 服务器** 来发现您的真实公共 IP (UDP 流量)
3.  STUN 查询 **绕过了代理** (因为它们是 UDP，而大多数代理只处理 TCP)
4.  您的真实 IP 被发现并 **与远程对等方共享**
5.  JavaScript 可以读取这些 "ICE 候选者" 并 **将您的真实 IP 泄露给网站**

!!! danger "WebRTC 泄露的严重性"
    即使：

    - 正确配置了 HTTP 代理
    - HTTPS 代理工作正常
    - DNS 查询被代理
    - User-Agent 被伪造
    - Canvas 指纹被缓解
    
    **WebRTC 仍然可以在毫秒内泄露您的真实 IP**。这是因为 WebRTC 在 **浏览器的代理层之下** 运行，直接与操作系统的网络堆栈交互。

### WebRTC 如何建立连接：ICE 过程

WebRTC 使用 **ICE (交互式连接建立)**，在 RFC 8445 中定义，以发现可能的连接路径并选择最佳路径。这个过程本身就会揭示您的网络拓扑。

```mermaid
sequenceDiagram
    participant Browser
    participant STUN as STUN 服务器
    participant TURN as TURN 中继
    participant Peer as 远程对等方
    
    Note over Browser: WebRTC 连接已启动
    
    Browser->>Browser: 收集本地 IP 地址<br/>(局域网接口)
    Note over Browser: 本地候选者:<br/>192.168.1.100:54321
    
    Browser->>STUN: STUN 绑定请求 (通过 UDP)
    Note over STUN: STUN 服务器发现公共 IP<br/>(绕过代理！)
    STUN->>Browser: STUN 响应 (带真实公共 IP)
    Note over Browser: 服务器自反候选者:<br/>203.0.113.45:54321
    
    Browser->>TURN: 分配中继 (如果需要)
    TURN->>Browser: 中继地址已分配
    Note over Browser: 中继候选者:<br/>198.51.100.10:61234
    
    Browser->>Peer: 发送所有 ICE 候选者<br/>(本地 + 公共 + 中继)
    Note over Peer: 现在知道了您的：<br/>- 局域网 IP<br/>- 真实公共 IP<br/>- 中继地址
    
    Peer->>Browser: 发送 ICE 候选者
    
    Note over Browser,Peer: ICE 协商：首先尝试直接 P2P
    
    alt 直接 P2P 成功
        Browser<<->>Peer: 直接连接 (完全绕过代理！)
    else 直接 P2P 失败 (防火墙/NAT)
        Browser->>TURN: 使用 TURN 中继
        TURN<<->>Peer: 中继连接
        Note over Browser,Peer: 延迟更高，但可行
    end
```

### ICE 候选者类型：泄露了什么

ICE 会发现三种类型的“候选者”(可能的连接端点)：

**1. 主机候选者 (本地 LAN IP 地址)**

您的浏览器会枚举所有本地网络接口，并为每个接口创建候选者：

```javascript
// WebRTC 揭示的主机候选者示例
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
candidate:3 1 UDP 2130706431 172.16.0.10 54323 typ host
```

**这揭示了什么：**

- 您在专用网络上的 **本地 IP 地址**
- 您的 **网络拓扑** (是否存在 VPN 接口、VM 网桥等)
- **网络接口的数量** (单个 Wi-Fi vs 多个以太网/VPN)

即使您在 NAT 之后，这也会揭示您的 **内部网络结构**。

**2. 服务器自反候选者 (通过 STUN 获得的公共 IP)**

浏览器向公共 STUN 服务器发送 STUN 请求，后者回复您从互联网上看到的 **公共 IP 地址**：

```javascript
// 服务器自反候选者 (您的真实公共 IP！)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**这揭示了什么：**

- 您的 **真实公共 IP 地址** (您试图用代理隐藏的那个！)
- 您的 **NAT 类型** 和外部端口映射
- 您的 **ISP** (通过 IP 地理定位/WHOIS)

**这就是** 人们所说的泄露：您的代理显示 `198.51.100.5`，但 WebRTC 揭示了 `203.0.113.45` (您的真实 IP)。

**3. 中继候选者 (TURN 中继地址)**

如果直接 P2P 失败，浏览器会从 TURN 服务器分配一个中继地址：

```javascript
// 中继候选者 (TURN 服务器地址)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

**这揭示了什么：**

- 正在使用的 **TURN 服务器** (可能揭示您的 VoIP 提供商等)
- 在 `raddr` (远程地址) 字段中 **仍然包含您的真实 IP**

### STUN 协议：IP 发现机制

STUN (NAT 会话穿透实用工具)，在 RFC 5389 中定义，是一个简单的基于 UDP 的请求-响应协议，它通过询问服务器“您看到的我是什么 IP？”来发现您的公共 IP 地址。

**STUN 消息结构**：

```python
# STUN 绑定请求 (简化)
{
    'message_type': 0x0001,  # 绑定请求
    'message_length': 0,      # 无附加属性
    'magic_cookie': 0x2112A442,  # 固定值 (RFC 5389)
    'transaction_id': b'\x01\x02\x03...\x0c'  # 随机 12 字节
}

# 通过 UDP 发送到 STUN 服务器 (例如, stun.l.google.com:19302)
```

**STUN 绑定响应**：

```python
# STUN 绑定成功响应
{
    'message_type': 0x0101,  # 绑定成功响应
    'message_length': 12,     # XOR-MAPPED-ADDRESS 属性
    'magic_cookie': 0x2112A442,
    'transaction_id': b'\x01\x02\x03...\x0c',  # 与请求相同
    'attributes': {
        'XOR-MAPPED-ADDRESS': {
            'family': 'IPv4',
            'port': 54321,
            'address': '203.0.113.45'  # 您的真实公共 IP！
        }
    }
}
```

**为什么是 XOR-MAPPED-ADDRESS？**
IP 地址与魔法 Cookie 和事务 ID 进行异或 (XOR) 操作，以实现 **NAT 兼容性**。一些 NAT 设备会错误地修改数据包有效负载中的 IP 地址，从而破坏 STUN。异或操作混淆了 IP，防止 NAT 干扰。

**公共 STUN 服务器** (浏览器常用)：

- `stun.l.google.com:19302` (Google)
- `stun1.l.google.com:19302` (Google)
- `stun.services.mozilla.com` (Mozilla)
- `stun.stunprotocol.org:3478` (开放 STUN 服务器)

### 为什么代理无法阻止 WebRTC 泄露

**1. UDP 协议**：WebRTC 使用 **UDP**，大多数代理只处理 **TCP**

   - HTTP 代理：仅 TCP
   - HTTPS CONNECT：仅 TCP 隧道
   - SOCKS4：仅 TCP
   - 只有 **SOCKS5** 支持 UDP (但必须配置浏览器才能使用它)

**2. 浏览器级实现**：WebRTC 是一个 **浏览器 API**，不是 HTTP 功能

   - 在 HTTP 层之下运行
   - 直接访问操作系统网络堆栈
   - 绕过为 HTTP/HTTPS 配置的代理设置

**3. 直接访问操作系统网络**：STUN 查询 **直接进入网络接口**

   - 浏览器的代理设置不适用于 STUN
   - 操作系统路由表决定路径 (而不是浏览器代理配置)
   - 只有 VPN 级别的路由才能拦截

**4. 多接口枚举**：WebRTC 枚举 **所有** 网络接口

   - 物理以太网、Wi-Fi、VPN 适配器、VM 网桥
   - 即使是未用于浏览的接口
   - 泄露内部网络拓扑

**5. JavaScript 可访问性**：网页可以通过 JavaScript **读取 ICE 候选者**

   - `RTCPeerConnection.onicecandidate` 事件
   - 从候选者字符串中提取 IP 地址
   - 将您的真实 IP 发送到他们的服务器

### 在 Pydoll 中防止 WebRTC 泄露

Pydoll 提供了多种策略来防止 WebRTC IP 泄露：

**方法 1：强制 WebRTC 仅使用代理路由 (推荐)**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # 添加 --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Pydoll 提供了一个便捷的 `webrtc_leak_protection` 属性，自动管理底层的 `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` 参数。

**这会做什么：**

- 如果没有代理支持 UDP，则禁用 UDP
- 强制 WebRTC **仅使用 TURN 中继** (没有直接 P2P)
- 阻止对公共服务器的 STUN 查询
- **权衡**：破坏直接 P2P (视频通话延迟更高)

**方法 2：完全禁用 WebRTC**

```python
options.add_argument('--disable-features=WebRTC')
```

**这会做什么：**

- 完全禁用 WebRTC API
- 不可能发生 IP 泄露
- **权衡**：破坏所有依赖 WebRTC 的网站 (视频会议、语音通话)

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

**这会做什么：**

- `ip_handling_policy`：与方法 1 相同，但通过首选项设置
- `multiple_routes_enabled`：防止使用多个网络路径
- `nonproxied_udp_enabled`：阻止不通过代理的 UDP

**方法 4：使用支持 UDP 的 SOCKS5 代理**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
# 如果代理需要认证，请在 URL 中包含凭证：
# options.add_argument('--proxy-server=socks5://user:pass@proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

**这会做什么：**

- SOCKS5 可以代理 UDP (通过 `UDP ASSOCIATE` 命令)
- WebRTC 使用代理进行 STUN 查询
- **要求**：代理必须支持 UDP (并非所有 SOCKS5 代理都支持)

### 测试 WebRTC 泄露

**手动测试：**

1.  访问 **https://browserleaks.com/webrtc**
2.  检查 "Public IP Address" 部分
3.  如果您看到 **您的真实 IP** (而不是代理 IP)，那么您就泄露了

**使用 Pydoll 自动测试：**

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
        
        # 等待结果加载
        await asyncio.sleep(3)
        
        # 提取检测到的 IP
        ips = await tab.execute_script(```
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ```)
        
        print("检测到的 IP:", ips)
        # 应该只显示代理 IP, 而不是您的真实 IP

asyncio.run(test_webrtc_leak())
```

!!! danger "务必测试 WebRTC 泄露"
    **切勿假设** 您的代理配置能阻止 WebRTC 泄露。始终使用 https://browserleaks.com/webrtc 或 https://ipleak.net 进行测试，以验证您的真实 IP 没有暴露。
    
    即使是单个 WebRTC 泄露也会立即 **危及您的整个代理设置**。网站现在知道了您的真实位置、ISP 和网络拓扑。

### 高级：网站如何检测 WebRTC 泄露

网站使用 JavaScript 有意触发 WebRTC 并提取您的真实 IP：

```javascript
// 恶意网站通过 WebRTC 提取真实 IP 的代码
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');  // 创建虚拟数据通道
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);
        
        if (ipMatch) {
            const realIP = ipMatch[1];
            // 将真实 IP 发送到服务器
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

这段代码：

1.  创建一个 RTCPeerConnection (WebRTC 连接对象)
2.  触发 ICE 候选者收集 (联系 STUN 服务器)
3.  使用正则表达式从候选者中提取 IP 地址
4.  将您的真实 IP 发送到他们的跟踪服务器

**您的防御：** 禁用 WebRTC 或强制仅使用代理路由，如上所示。

## 总结和进一步阅读

理解网络基础知识 (OSI 分层、TCP/UDP 特性以及 WebRTC 的点对点架构) 对于实现有效的基于代理的匿名 **至关重要**。

**关键要点：**

- 代理在 **特定层** 运行 (HTTP 在第 7 层, SOCKS 在第 5 层)，这决定了它们的能力
- **TCP 指纹** (窗口大小、选项、TTL) 从较低层泄露，揭示您的真实操作系统
- **UDP 流量** (WebRTC, DNS) 除非明确配置，否则通常会绕过代理
- **WebRTC** 是 IP 泄露的头号来源。始终使用 browserleaks.com 进行测试
- 只有 **SOCKS5** 或 **VPN** 才能有效代理 UDP 流量

**后续步骤：**

- **[HTTP/HTTPS 代理](./http-proxies.md)** - 深入了解应用层代理
- **[SOCKS 代理](./socks-proxies.md)** - 学习会话层、协议无关的代理
- **[网络指纹](../fingerprinting/network-fingerprinting.md)** - TCP/IP 指纹技术
- **[代理配置](../../features/configuration/proxy.md)** - 实用 Pydoll 代理设置

## 参考资料

- **RFC 793**: 传输控制协议 (TCP) - https://tools.ietf.org/html/rfc793
- **RFC 768**: 用户数据报协议 (UDP) - https://tools.ietf.org/html/rfc768
- **RFC 5389**: NAT 会话穿透实用工具 (STUN) - https://tools.ietf.org/html/rfc5389
- **RFC 8445**: 交互式连接建立 (ICE) - https://tools.ietf.org/html/rfc8445
- **RFC 5766**: NAT 中继穿透 (TURN) - https://tools.ietf.org/html/rfc5766
- **RFC 6528**: 防御序列号攻击 - https://tools.ietf.org/html/rfc6528
- **W3C WebRTC 1.0**: 浏览器之间的实时通信 - https://www.w3.org/TR/webrtc/
- **BrowserLeaks**: WebRTC 泄露测试 - https://browserleaks.com/webrtc
- **IPLeak**: 全面泄露测试 - https://ipleak.net