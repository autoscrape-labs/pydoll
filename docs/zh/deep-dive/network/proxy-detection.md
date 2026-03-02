# Proxy 检测

Proxy 检测是一个概率性过程。网站结合数十种信号来评估连接是否经过 proxy，从简单的 IP 信誉查询到 TCP/IP 协议栈分析和行为画像，不一而足。任何单一信号都无法提供确定性证据，但将足够多的弱信号组合在一起，就能产生高置信度的判断。

本文档涵盖主要的检测技术、其技术层面的工作原理，以及它们对使用 Pydoll 进行浏览器自动化意味着什么。

!!! info "模块导航"
    - [SOCKS Proxy](./socks-proxies.md)：会话层代理
    - [HTTP/HTTPS Proxy](./http-proxies.md)：应用层代理
    - [网络基础](./network-fundamentals.md)：TCP/IP、UDP、WebRTC

    有关 fingerprinting 的详细信息，请参阅[网络 Fingerprinting](../fingerprinting/network-fingerprinting.md) 和[浏览器 Fingerprinting](../fingerprinting/browser-fingerprinting.md)。

## IP 信誉

IP 信誉分析是部署最广泛的 proxy 检测技术。它结合公开可用的数据（ASN 记录、WHOIS、地理定位数据库）和专有情报，将 IP 地址分类为不同的风险等级。

### ASN 分类

每个 IP 地址都属于一个自治系统（AS），由 ASN 标识。拥有该 IP 的 AS 类型是判断其是否为 proxy 的最强单一指标。

属于云服务和托管提供商（AWS、DigitalOcean、OVH、Hetzner）的 IP 被标记为高风险，因为真实用户不会从数据中心服务器浏览网页。来自住宅 ISP（Comcast、Deutsche Telekom、BT）的 IP 风险较低，因为它们看起来像普通的家庭连接。移动运营商 IP（Verizon Wireless、AT&T Mobility）风险最低，因为它们最难与真实的移动用户区分开来。

一些 ASN 与已知的 proxy 基础设施相关联，但这比表面看起来更复杂。像 BrightData 或 Smartproxy 这样的大型住宅 proxy 提供商并不运营自己的 ASN；它们通过属于 ISP ASN 的真实住宅 IP 路由流量。这正是住宅 proxy 比数据中心 proxy 更难检测的原因。

检测系统查询 ASN 数据库（Team Cymru、RIPE NCC、ARIN）和商业 IP 情报 API 来分类每个连接 IP。数据中心 IP 的检测准确率大约在 95% 以上，因为 ASN 分类是明确的。住宅 proxy 的检测要困难得多（准确率大约 40-70%），因为这些 IP 确实属于 ISP。移动 proxy 的检测最为困难（大约 20-40%），因为移动运营商 NAT 使许多真实用户共享 IP。

这种准确率梯度正是住宅和移动 proxy 价格比数据中心 proxy 高出 10-100 倍的原因。

### 已知 Proxy 数据库

除了 ASN 分类之外，专门的数据库会追踪已被观察到参与 proxy 网络的 IP。IPQualityScore、proxycheck.io 和 Spur.us 等服务维护着已知 proxy、VPN 和 Tor 出口节点 IP 的实时数据库。Tor 出口节点列表可在 [check.torproject.org](https://check.torproject.org/torbulkexitlist) 公开获取。

这些数据库还会追踪行为信号：频繁轮换的 IP（proxy 池的典型特征）、并发会话数异常高的 IP（住宅 IP 通常只有 1-5 个并发连接，而不是 100+），以及之前与机器人行为关联的 IP。

### 地理位置一致性

Proxy 经常通过地理不一致性暴露自己。IP 地址指向一个位置，但浏览器报告的信号指向另一个位置。

最常见的不匹配包括：IP 地理位置与浏览器时区之间的不匹配（通过 JavaScript 的 `Intl.DateTimeFormat().resolvedOptions().timeZone` 收集）、IP 所在国家与 `Accept-Language` 标头之间的不匹配，以及当前会话位置与上一个会话位置之间的不匹配。一个出现在洛杉矶但浏览器时区为 `Europe/Berlin` 的用户是可疑的。一个在上一次会话位于纽约后 10 分钟出现在东京的用户在物理上是不可能的。

检测系统还会检查 IP 的地理位置是否与浏览器的区域配置匹配。一个美国数据中心 IP 配上 `Accept-Language: zh-CN` 和时区 `Asia/Shanghai`，强烈暗示这是一个通过美国 proxy 路由的中国用户。

!!! note "误报"
    合法场景也会触发地理位置警报：使用 VPN 的旅行者、浏览器设置保留母国配置的外籍人士、通过公司 VPN 连接的企业用户，以及使用非默认语言偏好的多语言用户。成熟的系统使用风险评分而非二元阻断来处理这些情况。

## HTTP 标头分析

HTTP 标头是最简单的检测途径。透明和匿名 proxy 会添加 `Via`、`X-Forwarded-For`、`X-Real-IP` 和 `Forwarded`（RFC 7239）等标头，直接暴露 proxy 的使用。精英 proxy 会剥离这些标头，但仅凭其缺失并不能证明是直连。

检测不仅限于寻找 proxy 专有标头。缺少真实浏览器总会发送的标头（如 `Accept-Language`、`Accept-Encoding` 或真实的 `User-Agent`）也很可疑。标头顺序同样重要：浏览器以一致的、版本特定的顺序发送标头，手动构造标头的 proxy 或自动化工具往往会搞错顺序。

旧版 `Proxy-Connection: keep-alive` 标头是另一个经典的检测信号，某些老旧客户端在通过 proxy 路由时会发送此标头。

### Proxy 匿名级别

Proxy 传统上根据其标头行为被分为三个匿名级别：

| 级别 | 行为 | 检测难度 |
|------|------|----------|
| 透明 | 在 `X-Forwarded-For` 中转发你的真实 IP，添加 `Via` 标头 | 极易检测 |
| 匿名 | 隐藏你的 IP 但添加 `Via` 或其他 proxy 标头 | 容易检测 |
| 精英 | 剥离所有标识 proxy 的标头 | 需要更深入的分析 |

这种分类来自 HTTP 标头分析作为主要检测方法的时代。现代检测系统使用 IP 信誉、fingerprinting 和行为分析，使得透明/匿名/精英的区分不再那么有意义。一个使用数据中心 IP 的精英 proxy 通过 ASN 查询就能立即被检测到。而一个使用住宅 IP 的透明 proxy 在不太成熟的网站上可能仍然不会被发现。

## 网络 Fingerprinting

网络层 fingerprinting 在 proxy 层之下运作，这意味着即使 proxy 本身配置完美，它也能检测到 proxy 的使用。

### TCP/IP Fingerprinting

每个操作系统都有独特的 TCP 协议栈实现，在 TCP 握手过程中会暴露出来。初始窗口大小、TCP 选项顺序、TTL（生存时间）和窗口缩放因子都由内核设置，而非浏览器，且无法被 proxy 更改。

检测系统将这些 TCP 特征与 `User-Agent` 标头进行比较。如果 User-Agent 声称是 Windows 10，但 TCP fingerprint 显示 Linux 特征（TTL 为 64，窗口大小为 29200），这种不匹配就是一个强 proxy 指标。Windows 使用默认 TTL 128，现代版本通常显示窗口大小 65535，而 Linux 使用 TTL 64，窗口大小约 29200。

TTL 分析增加了另一个层面。TTL 在每个网络跳点递减 1。如果一个 Windows 连接到达时 TTL 为 128，客户端很可能在同一网络上。如果到达时 TTL 为 115，则它经过了大约 13 个跳点。如果 TTL 值与 IP 地理位置的预期跳数不一致，则很可能存在 proxy 路由。

有关 TCP fingerprint 值及其含义的详细信息，请参阅[网络 Fingerprinting](../fingerprinting/network-fingerprinting.md)。

### TLS Fingerprinting（JA3/JA4）

TLS ClientHello 消息以明文传输，包含足够的参数来唯一标识客户端应用程序：TLS 版本、支持的密码套件、扩展、椭圆曲线和签名算法。JA3 fingerprint 是将这些参数按特定顺序拼接后的 MD5 哈希值。JA4 是一种更新、更细粒度的替代方案。

每个浏览器版本都会产生独特的 JA3/JA4 fingerprint。检测系统维护着 Chrome、Firefox、Safari 和其他浏览器的已知 fingerprint 数据库。如果 JA3 fingerprint 与任何已知浏览器不匹配，或者与 User-Agent 中声称的浏览器不匹配，该连接就会被标记。

一个重要的细节：SOCKS5 proxy 和 HTTP CONNECT 隧道会原样传递 TLS ClientHello，因此目标服务器看到的是真实浏览器的 fingerprint。在这些配置中，proxy 不会改变 TLS 参数。只有 MITM proxy（终止并重新建立 TLS 连接的 proxy）才会改变 fingerprint，在这种情况下 fingerprint 属于 proxy 软件而非真实浏览器，这本身就是一个检测信号。

### HTTP/2 Fingerprinting

HTTP/2 连接暴露出与 TLS 不同的 fingerprinting 信号。HTTP/2 连接开始时发送的 SETTINGS 帧包含 `HEADER_TABLE_SIZE`、`MAX_CONCURRENT_STREAMS`、`INITIAL_WINDOW_SIZE` 和 `MAX_HEADER_LIST_SIZE` 等参数。每个浏览器对这些设置使用不同的默认值。

伪标头（`:method`、`:authority`、`:scheme`、`:path`）的顺序和优先级、HPACK 压缩行为以及流优先级权重在不同浏览器之间也有所不同。[browserleaks.com/http2](https://browserleaks.com/http2) 等工具可以展示你的 HTTP/2 fingerprint 是什么样的。

实现了自己 HTTP/2 协议栈的自动化框架和 proxy 软件通常会产生与任何真实浏览器都不匹配的 fingerprint，使其成为一种有效的检测途径。

### 基于延迟的检测

客户端与服务器之间的网络延迟揭示了物理网络路径的信息。如果 IP 地理定位在纽约，但往返时间暗示路径经过了亚洲，则该连接很可能经过了 proxy。

检测系统在 TCP 握手期间测量 RTT（往返时间），并将其与 IP 地理位置的预期延迟进行比较。它们还可能发起基于 JavaScript 的计时挑战，从浏览器角度测量延迟，然后将其与服务器观察到的延迟进行比较。两者之间的显著差异暗示路径中存在中间节点（proxy）。

时钟偏移分析增加了另一个维度：通过 JavaScript（`Date.now()`）或 HTTP `Date` 标头测量客户端的时钟偏移量，检测系统可以推断客户端的实际时区，并将其与 IP 预期时区进行比较。

## 行为检测

最先进的检测系统超越了网络和协议分析，转而检查用户行为。这包括请求时序（请求是否均匀间隔，暗示自动化？）、鼠标移动模式（通过 JavaScript 事件监听器分析）、滚动行为、键盘输入节奏以及整体浏览模式。

基于数百万真实用户会话训练的机器学习模型能够以高准确率区分人类行为和自动化行为。这些模型通常结合 50 多个特征，包括导航模式、会话持续时间分布、点击位置、表单交互时序和 JavaScript 执行特征。

Pydoll 的人性化交互（贝塞尔曲线鼠标移动、Fitts 定律时序、真实的打字节奏）专为通过行为分析而设计。请参阅[规避技术](../fingerprinting/evasion-techniques.md)了解完整的多层规避策略。

## 多信号风险评分

现代检测系统不依赖任何单一技术。它们将所有可用信号组合成一个风险评分（通常为 0-100），并应用因行业和场景而异的阈值。

每类信号的权重各不相同，但粗略来说，IP 信誉占最大份额（它是最廉价且最可靠的信号），其次是网络 fingerprinting（TCP/IP、TLS、HTTP/2）、标头和协议分析、行为评分，以及一致性检查（地理位置、时区、语言）。

阈值取决于业务场景。银行网站阻断策略激进（风险评分超过 50 即阻断），电商网站在中等评分时展示 CAPTCHA（超过 70），内容网站则更为宽松（仅在超过 80 时阻断），因为它们依赖广告展示量。

这对自动化的启示是，仅通过一层检测是不够的。一个住宅 IP（良好的 IP 信誉）如果配上不匹配的 TCP fingerprint 和机器人行为，仍然会被标记。有效的规避需要所有层面的一致性。

## 按 Proxy 类型划分的检测难度

| Proxy 类型 | 检测难度 | 主要检测方法 |
|------------|----------|-------------|
| 透明 HTTP | 极易 | HTTP 标头（`Via`、`X-Forwarded-For`） |
| 匿名 HTTP | 容易 | HTTP 标头 + IP 信誉 |
| 精英 HTTP（数据中心） | 中等 | IP 信誉（ASN 分析） |
| 数据中心 SOCKS5 | 中等 | IP 信誉（ASN 分析） |
| 住宅 proxy | 困难 | 行为分析、连接模式、延迟 |
| 移动 proxy | 非常困难 | 主要靠行为分析，网络信号有限 |
| 轮换 proxy | 困难 | 会话不一致、IP 轮换模式 |

## 规避原则

有效的规避在于所有检测层面的一致性，而不是完善任何单一层面。

当隐蔽性重要时，使用住宅或移动 IP。它们更难被检测，因为这些 IP 确实属于 ISP，价格溢价反映了这一优势。将浏览器的地理位置信号（时区、语言、区域设置）与 proxy IP 的位置匹配。通过不在会话中途轮换 IP 来保持会话持久性，因为这会产生可检测的不连续性。确保你的 TCP/IP fingerprint 与 User-Agent 声明匹配，方法是在你所模拟的相同操作系统上运行自动化。使用 Pydoll 的人性化交互来通过行为分析。并且在大规模运行自动化之前，始终测试是否存在泄露（WebRTC、DNS、时区）。

目标不是使检测变得不可能，而是使其变得昂贵和不确定。迫使检测系统使用多个关联信号，融入合法流量模式，并创造合理的否认空间。

!!! warning "没有 Proxy 是不可检测的"
    拥有足够资源的情况下，任何 proxy 都可以被检测到。即使是顶级住宅 proxy 在面对 Akamai、Cloudflare Enterprise 和 DataDome 等成熟的反机器人系统时，成功率也大约只有 70-90%。实际问题在于，对于目标网站来说，检测是否在经济上值得。

**后续阅读：**

- [网络 Fingerprinting](../fingerprinting/network-fingerprinting.md)：TCP/IP 和 TLS fingerprinting 详解
- [浏览器 Fingerprinting](../fingerprinting/browser-fingerprinting.md)：Canvas、WebGL、HTTP/2 fingerprinting
- [规避技术](../fingerprinting/evasion-techniques.md)：多层规避策略
- [Proxy 配置](../../features/configuration/proxy.md)：Pydoll proxy 实用配置指南

## 参考资料

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (Anonymous IP Detection): https://spur.us/
- Team Cymru IP to ASN Mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas: TCP/IP Fingerprinting for VPN and Proxy Detection - https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas: Detecting Proxies and VPNs with Latencies - https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 Fingerprint: https://browserleaks.com/http2
- BrowserLeaks IP: https://browserleaks.com/ip
- RFC 7239: Forwarded HTTP Extension - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
