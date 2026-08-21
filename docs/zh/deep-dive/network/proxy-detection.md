# Proxy 检测

Proxy 检测是概率性的：一个站点把几十个微弱的信号（从一次简单的 IP 信誉查询到 TCP/IP 栈分析）汇成一个置信度分数。没有任何单一信号能算作证据，但足够多的信号加在一起就能产生一个高置信度的判定。本页涵盖主要的技术手段、它们如何工作，以及它们对自动化意味着什么。

它建立在网络章节其余部分之上：[网络基础](network-fundamentals.md) 讲相关的各层，[HTTP/HTTPS proxy](http-proxies.md) 和 [SOCKS proxy](socks-proxies.md) 讲每种 proxy 类型的行为。

## IP 信誉

IP 信誉是部署最广泛的技术。它把公开数据（ASN 记录、WHOIS、地理定位数据库）与专有情报结合起来，把 IP 地址归入不同的风险类别。

### ASN 分类

每个 IP 都属于一个自治系统（Autonomous System），由一个 ASN 标识，而拥有某个 IP 的 AS 类型，是判断它是否为 proxy 的单一最强指标。

来自云和主机托管提供商（AWS、DigitalOcean、OVH、Hetzner）的 IP 会被标记为高风险，因为真实用户不会从 datacenter 服务器上浏览。来自 residential ISP（Comcast、Deutsche Telekom、BT）的 IP 是低风险，因为它们看起来像家庭连接。移动运营商的 IP（Verizon Wireless、AT&T Mobility）风险最低，因为运营商 NAT 使它们很难与真实的移动用户区分开。

大型 residential proxy 提供商并不运营自己的 ASN；它们通过属于 ISP ASN 的真实 residential IP 来路由。这正是 residential proxy 比 datacenter proxy 更难检测的原因。

检测系统查询 ASN 数据库（Team Cymru、RIPE NCC、ARIN）和商用的 IP 情报 API 来对每个连入的 IP 分类。datacenter IP 大约以 95% 的准确率被抓到，因为 ASN 是明确无疑的。residential proxy 要难得多（大约 40% 到 70%），因为这些 IP 确实属于 ISP，而 mobile proxy 是所有里面最难的（大约 20% 到 40%）。正是这条准确率梯度，使得 residential 和 mobile proxy 的价格数倍于 datacenter proxy。

### 已知 proxy 数据库

在 ASN 分类之外，专门的服务（IPQualityScore、proxycheck.io、Spur.us）会维护已知 proxy、VPN 和 Tor 出口 IP 的实时数据库。Tor 出口列表在 [check.torproject.org](https://check.torproject.org/torbulkexitlist) 公开。

这些数据库还跟踪行为：频繁轮换的 IP（proxy 池的典型特征）、并发会话数异常高的 IP（一个 residential IP 通常只有屈指可数的连接，而非成百上千），以及此前被发现有 bot 活动的 IP。

### 地理定位一致性

Proxy 常常通过地理上的自相矛盾来暴露自己：IP 指向一个地方，而浏览器上报的信号却指向另一个。

常见的不一致有：IP 位置与浏览器时区（`Intl.DateTimeFormat().resolvedOptions().timeZone`）之间、IP 所在国家与 `Accept-Language` header 之间，以及本次会话位置与上一次会话位置之间。一个身处洛杉矶却带 `Europe/Berlin` 时区的用户是可疑的。一个用户在东京，而十分钟前上一次会话还在纽约，这是不可能的。

!!! note "地理定位的误报"
    合法的情况也会触发这些警报：用 VPN 的旅行者、保留母国设置的外派人员、用企业 VPN 的用户，以及带非默认语言偏好的多语用户。好的系统用风险评分而非二元封锁，来吸纳这些情况。

## HTTP header 分析

Header 是最简单的检测向量。透明 proxy 和匿名 proxy 会添加像 `Via`、`X-Forwarded-For`、`X-Real-IP` 和 `Forwarded`（RFC 7239）这样的 header，直接暴露了 proxy 的使用。精英（elite）proxy 会剥除它们，但仅仅它们不在，也不能证明这是一次直连。

检测的深度不止于寻找 proxy header。真实浏览器总会发送、却缺失的那些 header（`Accept-Language`、`Accept-Encoding`、一个真实可信的 `User-Agent`）是可疑的，而且 header 的顺序也很重要：浏览器以一种一致的、随版本而定的顺序发送 header，而手工拼装 header 的工具常常搞错。老旧的 `Proxy-Connection: keep-alive` header 是另一个经典的破绽。

Proxy 传统上按 header 行为分级，尽管在 IP 信誉和指纹识别占主导的今天，这种区分已不那么重要。一个位于 datacenter IP 上的精英 proxy，仍会被 ASN 查询立刻抓到：

| 级别 | 行为 | 检测 |
|-------|----------|-----------|
| 透明（Transparent） | 在 `X-Forwarded-For` 中转发你的真实 IP，添加 `Via` | 轻而易举 |
| 匿名（Anonymous） | 隐藏你的 IP，但添加 `Via` 或其他 proxy header | 容易 |
| 精英（Elite） | 剥除所有能标识 proxy 的 header | 需要更深入的分析 |

## 网络指纹

网络层的指纹识别工作在 proxy 之下，所以即便 proxy 本身配置得完美无瑕，它也能暴露一个 proxy。这是 [网络指纹](../fingerprinting/network-fingerprinting.md) 中深入讲述的理论；这里说的是它如何为 proxy 检测供料。

**TCP/IP 指纹。** 每个操作系统都有一个独特的 TCP 栈。初始窗口大小、TCP 选项顺序、TTL 和窗口缩放由内核设定，而非浏览器，proxy 无法改变它们。如果 `User-Agent` 声称是 Windows 10（TTL 128，窗口 65535），而 TCP 指纹显示的却是 Linux（TTL 64，窗口约 29200），这处不一致就是一个强 proxy 信号。TTL 每经一跳减一，所以一个不符合该 IP 所在位置预期跳数的值，就暗示流量经过了 proxy 路由。

**TLS 指纹（JA3/JA4）。** TLS ClientHello 以明文发送，携带足够的参数（版本、加密套件、扩展、曲线）来识别客户端。检测系统会把它的 JA3/JA4 哈希与已知浏览器数据库比对。一个关键的细微之处：SOCKS5 proxy 和 HTTP CONNECT 隧道让 ClientHello 原封不动地穿过，所以服务器看到的是真实的浏览器指纹；只有一个会终结 TLS 的 MITM proxy 才会改变它，而那时指纹就属于 proxy 软件本身，这本身又是一个信号。

**HTTP/2 指纹。** HTTP/2 的 `SETTINGS` 帧、伪 header 顺序和流优先级会因浏览器而异。自动化框架，以及带有自己 HTTP/2 栈的 proxy，常常产生一个不匹配任何真实浏览器的指纹。

**延迟。** 握手期间的往返时间会暴露物理路径。如果 IP 地理定位在纽约，而 RTT 暗示的是一条经过亚洲的路径，那么这条连接很可能被代理了。系统还可能运行 JavaScript 计时挑战，把浏览器观测到的延迟与服务器观测到的延迟做对比；一个大的差距就意味着有一个中间节点。

## 行为检测

最先进的系统会考察行为：请求时序、鼠标移动（通过 JavaScript 监听器）、滚动、击键节奏，以及整体浏览模式。用数百万真实会话训练的机器学习模型，会把几十个特征（导航模式、会话时长、点击位置、表单填写时序）结合起来，把人类与自动化区分开。

Pydoll 的拟人化交互（带 Fitts 定律时序的曲线鼠标路径、有变化的打字）正是针对这一层的。实践的一面见 [拟人化交互](../../stealth/human-like-interactions.md)，理论见 [行为指纹](../fingerprinting/behavioral-fingerprinting.md)。

## 多信号风险评分

现代系统不依赖单一技术。它们把每一个信号折算进一个风险分数（通常 0 到 100），并施加一个随场景变化的阈值。IP 信誉通常占最大权重（它是最便宜、最可靠的信号），其次是网络指纹、header 与协议分析、行为评分，以及一致性检查。

阈值随业务而定。银行会激进地封锁，电商在中等分数时弹出 CAPTCHA，内容站点则往往较为宽松。对自动化的教训是，过了一层还不够：一个带着不一致 TCP 指纹和机械行为的 residential IP，仍会被标记。跨各层的一致性才是关键所在。

## 按 proxy 类型的检测

| Proxy 类型 | 检测难度 | 主要方法 |
|------------|----------------------|-----------------|
| 透明 HTTP | 轻而易举 | Header（`Via`、`X-Forwarded-For`） |
| 匿名 HTTP | 容易 | Header + IP 信誉 |
| 精英 HTTP（datacenter） | 中等 | IP 信誉（ASN） |
| Datacenter SOCKS5 | 中等 | IP 信誉（ASN） |
| Residential | 困难 | 行为、连接模式、延迟 |
| Mobile | 非常困难 | 主要靠行为，网络信号很少 |
| 轮换（Rotating） | 困难 | 会话不一致、轮换模式 |

## 一致性需要什么

规避的关键在于各层之间的相互吻合，而不是把任何单独一层做到极致。实践中这意味着：在隐匿要紧时优先用 residential 或 mobile IP；让浏览器的时区、语言和区域设置与 IP 的位置匹配；把一个会话保持在一个 IP 上，而非会话中途轮换；在你于 `User-Agent` 中所声称的同一操作系统上运行自动化，好让 TCP 指纹相符；让行为拟人化；并在大规模运行前测试 WebRTC、DNS 和时区泄露。Pydoll 的 [规避技术](../../stealth/evasion-techniques.md) 涵盖你能操控的实践杠杆，包括 WebRTC 泄露防护和匹配区域设置。

!!! warning "没有 proxy 是不可检测的"
    只要资源足够，任何 proxy 都能被检测到。即便是顶级的 residential proxy，面对像 Akamai、Cloudflare Enterprise 和 DataDome 这样成熟的系统，也只能达到约 70% 到 90% 的成功率。实际要问的问题是：检测出你，是否值得目标方为此付出的代价。

## 相关内容

- [网络基础](network-fundamentals.md)：一个请求所经过的各层。
- [HTTP/HTTPS proxy](http-proxies.md) 和 [SOCKS proxy](socks-proxies.md)：每种 proxy 类型的行为。
- [网络指纹](../fingerprinting/network-fingerprinting.md)：详解 TCP/IP、TLS 和 HTTP/2 签名。
- [Proxy](../../guides/proxies.md)：在 Pydoll 中配置一个 proxy。
- [规避技术](../../stealth/evasion-techniques.md)：你能操控的那些杠杆。

## 参考资料

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (anonymous IP detection): https://spur.us/
- Team Cymru IP to ASN mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering, TLS fingerprinting with JA3 and JA3S: https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai, Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017): https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas, TCP/IP fingerprinting for VPN and proxy detection: https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas, detecting proxies and VPNs with latencies: https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 fingerprint: https://browserleaks.com/http2
- RFC 7239, Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110, HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
