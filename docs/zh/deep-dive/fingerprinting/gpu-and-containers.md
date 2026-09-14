# GPU、容器与 profile 触及不到的东西

一个 fingerprint profile 改变的是浏览器*报告*什么。它改变不了 host *计算*什么。每一个 GPU 信号都同时以这两种形式存在，而两者之间的分界决定了某台 host 能声称什么，为什么一台声称另一个 vendor 显卡的 Mac 与一个没有 GPU 的容器是两种不同的情况，以及 Xvfb 改变了什么、没改变什么。

本页把 [伪造的极限](spoofing-limits.md) 的那条规则，字符串可以改动但渲染输出保持真实，应用到一个问题上：这台 host 可以声称什么硬件？它展开了注入指南里的 [容器段落](../../stealth/fingerprint-injection.md#containers)。

!!! warning "这里的一切都取决于目标"
    没有银弹。每个站点读取它自己的那一部分信号，并按自己的方式权衡：[审计一个 fingerprint](auditing.md#what-passive-collectors-read) 里追踪到的被动收集器根本不读 GPU，而一个商业 fingerprinting agent 会对它做哈希。下面每一句"检测器看到 X"形式的陈述，意思都是"读取 X 的检测器会看到它"。在为字体、proxy 或 GPU 实例花钱之前，先追踪目标实际读取什么；没人读的矛盾不花任何代价，而你从没想到的某个信号可能才是决定性的那个。

## 被报告的与被计算的

| 层 | 例子 | profile 能否触及 |
|---|---|---|
| 被报告的 | renderer 字符串、WebGL 的 limits 和扩展、shader 精度、WebGPU 的 `adapter.info`、limits、features | 能：`webgl` 和 `webgpu` 部分会替换它 |
| 被计算的 | 渲染出的像素（一个测试场景的哈希）、compute 结果、它们的耗时、无 caveat 上下文检查 | 不能：由硬件执行 |

被报告层在真实的 prototype 上被替换，原生的 brand check 完好无损（见 [Fingerprint 注入](../../stealth/fingerprint-injection.md#native-first)）。被计算层就是 [伪造的极限](spoofing-limits.md) 所说的硬性底线：渲染哈希是一个测试场景所画出的像素的哈希，而无 caveat 检查就是 `getContext('webgl', {failIfMajorPerformanceCaveat: true})`，一个只有在 Chrome 认为渲染器足够快时才会授予的上下文。

一个只读被报告层的检测器，看到的就是 profile 所说的。一个读被计算层的检测器，看到的是 host。它能从中得出什么结论，取决于这台 host 是什么。

## 另一个 vendor 的 GPU：一场押在目标参考数据上的赌注

以这个分支实测的情况为例：一台 Apple M4 跑着 Windows profile，两个部分都声称一块 NVIDIA 显卡。被报告层是一致的，处处都是 NVIDIA。被计算层是一块真实的 GPU：硬件抗锯齿、硬件精度、以硬件速度完成的渲染。这份输出本身只说明"有一块 GPU 画了这个"。要把它变成一个矛盾，检测器需要一份参考："Windows 上的 RTX 3060 产出哈希 X，耗时 Y 毫秒"。与之比对，M4 的输出对不上。

只有握着逐显卡参考数据的检测器才能抓住这个谎言。Castle 记录了字符串交叉核对（renderer 对照 User-Agent 的 OS）；哈希对照参考的比较，是一个商业 fingerprinting agent 用它收集到的渲染哈希可以做的事，但没有任何公开来源显示有谁按显卡这样做。reCAPTCHA 和 hCaptcha 的被动读取，[追踪结果在此](auditing.md#what-passive-collectors-read)，从未碰过 WebGL 或 WebGPU，而这台 Mac 上的 Windows profile 曾一次通过手动输入的 Google 搜索。

被计算的输出本身永远不会说"自动化"或"容器"，因为它是货真价实的硬件输出；这台 Mac 上 headless 和 headful 在每一个 GPU 信号上实测都相同。所以在一块真实 GPU 上使用另一个 vendor 的 GPU profile，是一次经过校准的赌注：它能通过任何只读取值和值之间一致性的检测，也会败给任何把渲染输出与显卡数据库做比对的检测。host 自己 GPU 的 profile 永远是更强的那个，因为两层不需要任何参考就已经一致。

## 没有 GPU：一个不需要参考就成立的矛盾

这里被计算层本身就能被认出来。没有 GPU 时，当前的 Chrome 要么根本不创建 WebGL 上下文（SwiftShader 回退自 Chrome 139 起已被移除，当前 build 需要 `--enable-unsafe-swiftshader`），要么通过 SwiftShader、也就是 Chrome 的 CPU 光栅化器来渲染。在禁用 GPU 的 Chrome 152 上实测：

- 当 Chrome 回退到 SwiftShader 时，无 caveat 上下文会被拒绝，没有任何独立显卡会这样。用 `--use-angle=swiftshader` 显式选择 SwiftShader 仍然会授予它，所以这是没有 GPU 的情况，而不是 SwiftShader 的属性。
- 渲染哈希在同一 build 的每一个没有 GPU 的 Chrome 上都一样，不管什么 CPU，任何维护着这类表的检测器都能认出这个值。
- 渲染一个场景耗的是 CPU 时间：一个简单场景实测比 M4 慢几十倍。
- 不加下面的标志时，`navigator.gpu.requestAdapter()` 解析为 `null`，于是 `webgpu` 部分没有 adapter 可以附着它的值。

在这样的 host 上声称一块独立显卡的 profile，与上面每一条都矛盾，而且不需要任何人知道那块显卡本来会产出什么。这就是与 Mac 的区别：Mac 的被计算层只会向持有参考的检测器出卖 profile；容器的被计算层则向一行检查就出卖了它。

### 改讲一个软件故事

容器真正的样子，一个软件渲染的浏览器，也正是数百万真实会话的样子。虚拟桌面上的 Windows（VDI、Citrix、云 VM）通过 Microsoft Basic Render Driver（Windows 自己的 CPU 光栅化器，WARP）渲染，那里的 Chrome 报告的 renderer 形如 `ANGLE (Microsoft, Microsoft Basic Render Driver (0x0000008C) Direct3D11 vs_5_0 ps_5_0, D3D11-10.0.19041.5794)`。Chromium 把 WARP 归为软件渲染，所以那里同样应当出现被拒绝的无 caveat 上下文和 `null` 的 WebGPU adapter；这一对仍有待在一台 Windows VM 上确认。软件渲染器本身就会被打为可疑，但它们描述的是真实的机器；而在软件 host 上声称一块独立显卡，什么真实机器都描述不了。

这样一个 profile 的值（WebGL limits、扩展、精度表）必须在一台真实的 Windows VM 上捕获，和其他每一个 profile 的规则一样。剩下的缺口是渲染哈希：SwiftShader 和 WARP 画出来的不一样，所以一个持有 WARP 参考的检测器仍然能看出差别。那是评分层面的事，不是一个矛盾。

### 让这些 API 存在

`--enable-unsafe-swiftshader` 给页面一个可读的 WebGL 上下文；一台完全没有 WebGL 的桌面机比一台用软件渲染器的更少见。`--enable-unsafe-webgpu --use-webgpu-adapter=swiftshader` 暴露一个软件 WebGPU adapter，它报告 vendor 为 `google`、architecture 为 `swiftshader`、`adapter.info.isFallbackAdapter` 为 true，供 `webgpu` 部分附着（把 profile 里的 `is_fallback_adapter` 设成所声称设备报告的值，否则这个标志仍然可见）。两者合起来，给那些读取参数和存在性的检测器提供了一些一致的东西可读。它们不改变渲染输出的任何东西，而把它们与硬件 GPU 的声称组合在一起，就会重现上面的矛盾。

## Xvfb 去掉的是显示器信号，不是 GPU 信号

Xvfb（一个没有连接屏幕的虚拟 X 显示器）给 Chrome 一个显示器，于是浏览器以 headful 运行：存在一个被呈现的表面（呈现项，即 Cloudflare 用来判断浏览器是否在往真实显示器上绘制的信号，在 IP 不理想时会在 [Cloudflare 的托管挑战](cloudflare-challenge.md) 里被权衡），`screen` 是你配置的虚拟显示器，窗口有真实的边框和 Linux 滚动条，输入可以来自操作系统（`xdotool`）而不是 DevTools protocol。那些源于没有显示器的信号消失了；某个目标怎么看待这一点，是它自己的评分。

它不添加任何 GPU。Xvfb 是内存里的一块 framebuffer；渲染仍然是 SwiftShader 或 Mesa 的 llvmpipe（Linux 的 CPU 光栅化器），一个在 renderer 字符串里同样容易认出的软件渲染器。内核、字体和出口 IP 也没有变。

## 服务器上的价值顺序

1. **一个干净的住宅出口 IP。** 在任何脚本运行之前就会被读到，而在一个权衡 IP 信誉的目标上（大多数目标都是），下面的任何一条都补偿不了它。
2. **一个与 host 所计算的东西相符的 profile。** 在有 GPU 的 host 上，用 host 自己 GPU 的 vendor；在没有 GPU 的 host 上，讲一个软件渲染的 Windows 故事，而不是一块独立显卡。
3. **存在的 API。** 上面的 SwiftShader 标志，再加 `--use-fake-device-for-media-stream`，让 Chrome 自己暴露一个麦克风、一个摄像头和一个扬声器。
4. **装上所声称 OS 的字体**，并让 `available_fonts` 恰好列出这些；那个 OS 的彩色 emoji 字体也要装。
5. **Xvfb**，当目标会权衡呈现时。
6. **内核。** 一个 Windows User-Agent 下的 Linux SYN 会在边缘被读到（[Network fingerprinting](network-fingerprinting.md)）；一个运行着所声称 OS 的 proxy 出口是唯一干净的解法，而目标是否权衡 SYN 仍然是一个悬而未决的测量。
7. **一块真实的 GPU。** 一台 GPU 实例（T4/L4 一类）是唯一能让渲染哈希、WebGPU adapter 和计时都变得真实的东西；配上 profile 所声称的同一 vendor，被报告层和被计算层终于一致。

!!! note "一个模型，而不是判决"
    第一项和最后一项有文献和测量支撑；中间各项的顺序取决于目标。一个从不读 WebGL 的站点，GPU 实例帮不上忙；一个会对它做哈希的站点，除了真 GPU 之外什么都骗不过。先测量目标，并且要预期两个目标的结论会不一样。

## 相关

- [伪造的极限](spoofing-limits.md)：本页应用到硬件上的那条一般规则。
- [Fingerprint 注入](../../stealth/fingerprint-injection.md)：应用 `webgl` 和 `webgpu` 部分。
- [审计一个 fingerprint](auditing.md)：读取一个目标实际收集了什么。
- [Cloudflare 的托管挑战](cloudflare-challenge.md)：呈现项与 headless 的情况。
