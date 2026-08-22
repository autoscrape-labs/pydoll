# 伪造的极限

Fingerprint 注入会改变浏览器所报告的内容，但并非每个信号都能被改变，而强行改变错误的那个信号只会让你更容易、而不是更难被检测。本页划清了这条界线：一次伪造能够干净利落地改动哪些信号，完全无法改动哪些信号，以及为什么去覆盖那些它无法改动的信号，会留下一个检测器一眼就能读出的矛盾。

这是 [Fingerprint 注入](../../stealth/fingerprint-injection.md) 检查清单背后的理论。实用步骤请先读那一页；而要理解那份清单为什么是现在这个样子，请读本页。

## 原生覆盖会被读作真相

一个浏览器信号往往有不止一条读取路径。`matchMedia('(color-gamut: p3)')` 和一条 CSS `@media (color-gamut: p3)` 规则问的是同一个问题，而答案来自同一个地方：渲染引擎，在 C++ 里，位于你能触及的 JavaScript 之下。

这正是区分一个好的覆盖与一个可被检测的覆盖的关键：

- **原生覆盖**在引擎层改变值。Pydoll 通过 CDP 的 `Emulation` 域来应用这些覆盖，用于 User-Agent、时区、屏幕、locale、`hardwareConcurrency` 以及 CSS 媒体特性。之后每一条读取路径都会返回新值，而且它们彼此一致。没有可供检查的 JavaScript 包装器。
- **JavaScript 覆盖**只包装某一个 API，一个 `navigator` getter 或 `matchMedia`。它只改变那一条路径。任何其他读取同一信号的路径仍然返回真实值。

一个媒体特性存在于引擎的 `MediaValues` 中，而两条读取路径都会针对它来解析。切换下面的覆盖类型，看看每一种分别能触及哪些路径：

<iframe src="/docs/resources/visuals/media-read-paths.html" aria-label="一个 CDP 覆盖会编辑引擎的 MediaValues，使 matchMedia 和 CSS 级联都发生改变；而一个 JavaScript 覆盖只包装 matchMedia，让 CSS 路径读到真实值" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

一个 CDP 覆盖会编辑 `MediaValues`，所以 `matchMedia` 和 `@media` 级联都会返回新值。一个 JavaScript 覆盖会替换 `matchMedia` 函数；级联从不调用它，所以 CSS 仍然针对真实的 `MediaValues` 来解析。那个缺口就是矛盾。

下面这个演示运行在你自己的显示器上。两张卡片都读取你真实的 `dynamic-range` 并保持一致。应用一个 JavaScript 覆盖后，只有 `matchMedia` 在撒谎；而引擎的 `@media` 规则仍然报告真相。

<iframe src="/docs/resources/visuals/js-override-lie.html" aria-label="matchMedia 和一条 CSS @media 规则读取相同的 dynamic-range；一个 JavaScript 覆盖只让 matchMedia 撒谎，而 CSS 路径保持真实" style="width: 100%; height: 340px; border: 0;" loading="lazy"></iframe>

这正是为什么 Pydoll 不伪造 `dynamic-range`。Chrome 保留着一份固定的、可覆盖的媒体特性白名单。在 Blink 的 `MediaFeatureOverrides::SetOverride` 中，有七个名字会被处理，`color-gamut`、`prefers-color-scheme`、`prefers-contrast`、`prefers-reduced-motion`、`prefers-reduced-data`、`prefers-reduced-transparency` 以及 `forced-colors`，任何其他名字都会落空、什么也不改变。`dynamic-range`、`inverted-colors` 和 `monochrome` 在那里没有分支，所以这个 CDP 命令会被接受、然后被悄悄丢弃。这是引擎里缺失的一条代码路径，而不是一个值格式的问题。

Pydoll 暴露了这七个里的六个。被排除在外的那一个是 `prefers-reduced-data`：它在白名单里，但在 Chrome 中是禁用发布的，所以 `matchMedia` 对任何值都报告不匹配，而设置它就会声称一个真实 Chrome 从不会返回的东西。对于那些未列入白名单的特性，唯一剩下的杠杆就是 JavaScript，而它只能在一条路径上撒谎，所以 Pydoll 让 `dynamic-range` 保持真实，转而要求你把 `color-gamut` 与之匹配。

!!! note "什么时候一个 JavaScript 覆盖是安全的"
    Pydoll 确实会使用 JS 覆盖，用于 `deviceMemory`、WebGL 字符串、插件等等。它们之所以安全，是因为 CDP 触及不到那些信号，**并且**没有第二条读取路径与之矛盾，而且每一个都经过加固，以经受住 `toString`、prototype 和 worker 检查（参见 [检测 JavaScript 覆盖](../../stealth/fingerprint-injection.md#detecting-javascript-overrides)）。规则是：一个 JS 覆盖只有在它是那个信号的唯一真相来源时才是安全的。

## 硬性底线：任何覆盖都无法伪造的信号 {#the-hard-floor-signals-no-override-can-fake}

有些信号并不是浏览器所存储的一个值。它们是检测器在你真实硬件上运行一次计算、然后做哈希所得到的输出：

- **Canvas** 会把设定好的文本和形状绘制到一个离屏 canvas 上，用 `getImageData` 把像素读回来，并对其做哈希。子像素抗锯齿取决于 GPU、驱动以及操作系统的文本渲染器，所以哈希在同一台机器上是稳定的，在不同机器之间则各不相同。
- **Audio** 会通过一个 `OfflineAudioContext` 渲染一个音调，把一个振荡器接入一个 `DynamicsCompressorNode`，用 `getChannelData` 读取输出，并对其做哈希。这个浮点 DSP 结果因平台而异。
- **WebGL 和 WebGPU** 会渲染一个场景，对图像做哈希，并测量 GPU 花了多长时间。

这些当中没有任何一个存在 CDP 覆盖，而一个 JavaScript 覆盖也触及不到被哈希的输出，只能触及它周围的 API。Chrome 甚至在 DevTools Protocol 中暴露了一个 WebAudio 域，但它只观察音频图；它没有任何命令去重写采样。就连协议本身也无法撼动这一层。

那个幼稚的逃避手段，也就是 hook 读回 API、加入噪声以让哈希在每次读取时都变化，本身就是那个破绽。一项标准检查会把同一个 canvas 渲染两次并做比较：一个真实的 GPU 两次都会返回逐字节相同的像素，所以一个在两次读取之间有所不同的值就是一个 JavaScript hook，而这种不稳定性对会话的标记，比一个稳定的真实哈希所能做到的还要明显得多。

!!! warning "不要加入 canvas 或 audio 噪声"
    一个稳定的真实 fingerprint 比一个在多次读取之间闪烁的 fingerprint 更不可疑。随机化 canvas 或 audio 输出会把会话标记为自动化，而不是把它藏起来。

这些信号所暴露的是*哪一台机器*，而不是*它是不是一个机器人*。对于一个抓取器来说，这意味着它们的重要性在于把你跨多次运行的各个会话彼此关联起来，而不在于一次单独的机器人判定。要让它们与所声称的设备保持连贯，唯一的办法就是在那套硬件上运行。

## 一次伪造的强度取决于它最薄弱的那一层

一个 fingerprint 是跨层读取并加以关联的。覆盖了某一层，而另一层仍然报告真相，就是一个矛盾，而一个矛盾的得分比一个未经修改的浏览器更糟。

以一块 GPU 为例。Pydoll 会覆盖 WebGL renderer 字符串，所以一个 profile 可以声称是一块 NVIDIA 卡，但它不会触碰 WebGPU。在这台主机上（Apple M3，Chrome 151）应用 Windows profile 并读取这两个 API，实测如下：

| 信号 | 读到 | 来自 |
|--------|-------|------------|
| WebGL renderer 字符串 | `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 ...)` | 覆盖 |
| WebGPU adapter vendor | `apple` | 真实的 GPU |
| WebGPU `maxBufferSize` | `4294967292` | 真实的 GPU |
| WebGPU `maxComputeWorkgroupStorageSize` | `32768` | 真实的 GPU |
| Canvas 哈希，此 profile 对比 macOS profile | 相同 | 真实的 GPU |

WebGL 说是 NVIDIA；WebGPU、它的各项上限以及 canvas 全都说是 Apple。这次覆盖只改动了一个字符串，而留下了其他每一个被渲染和被报告的信号去描述真实的 GPU，所以一个跑在 Apple 硬件上的 Windows profile 自相矛盾。一块被伪造了一半的 GPU 比真实的那块更容易被检测。

### 为什么 Pydoll 不去动 WebGPU

你可以尝试去弥合那个缺口，把 WebGPU 也伪造得相匹配，先是 vendor 字符串，然后是那大约三十项 adapter 上限。Pydoll 正是造出了这个东西，然后又把它撤销了。每一项上限都必须是你所声称的那块卡在物理上真实的值，这与那个让错误的 WebGL 参数成为破绽的约束是同一个；真实的逐 GPU 上限集合并未公开，所以你只能靠猜；这份列表还会随 Chrome 版本而变化；而且即便是一套完美的集合，也无法撼动 GPU 计时哈希，那是被渲染出来的，而不是被报告出来的。

所以诚实的工程判断就是干脆完全不去伪造那一层。追逐一种你无法维持的连贯性，是用一个微小而脆弱的收益，去换取一笔庞大的维护成本以及一条新的暴露途径。Pydoll 覆盖 WebGL renderer 字符串，而让 WebGPU 和被渲染出来的输出保持真实，这意味着 profile 必须声称那个实际存在的 GPU 系列。

这就是为什么 [Fingerprint 注入检查清单](../../stealth/fingerprint-injection.md#checklist) 坚持要求 profile 的操作系统和 GPU 与主机相匹配。你可以改动一个字符串，但被渲染出来的输出保持真实，所以这个字符串必须描述那套实际存在的硬件。

### 操作系统是你唯一无法改动的那一个

最清楚的那个你只能匹配、永远无法伪造的信号，就是操作系统。设置 User-Agent、`navigator.platform` 和 Client Hints，浏览器会立刻说自己是 Windows，但操作系统会透过任何覆盖都触及不到的层泄露出来，而且是同时透过不止一层。

那个决定性的层是内核的 TCP/IP 栈。每一次连接的 SYN 包都携带着初始 TTL（macOS 和 Linux 上是 64，Windows 上是 128）、TCP 窗口大小和缩放，以及选项顺序，全都由主机内核在任何 JavaScript 运行之前设定。一个 Windows User-Agent 却经由一条 TTL-64 的连接到达，就是一个在传输层被读出的矛盾，而没有任何 CDP 或 JavaScript 覆盖能触碰它。[Network fingerprinting](network-fingerprinting.md) 深入讲解了这一整套栈；这正是为什么一个跑在 Mac 上的 Windows profile 会在 Cloudflare 的托管挑战面前失败。

渲染同样承载着操作系统信息，所以 canvas 也是答案的一部分。Canvas 和字体是通过操作系统的文本渲染器来绘制的，macOS 上是 CoreText，Windows 上是 DirectWrite，所以一个在 Windows profile 下由 Mac 渲染出来的 canvas，本身就已经描述了错误的操作系统。这处 canvas 泄露是真实的，但无法伪造，而且在实测的那次 Cloudflare 运行中，它并不是那个决定性的信号，内核栈才是。在这台 Mac 上，同一个 canvas 在 Windows profile 和 macOS profile 下都哈希成了 `d65506c6...`，而 `navigator.platform` 读到的是 `Win32` 和 `MacIntel`。相同的哈希只能说明 profile 没有改动 canvas，而不能说明 canvas 与那个 Windows 声称相符；它是这台真实 Mac 的，一个来自 [硬性底线](#the-hard-floor-signals-no-override-can-fake) 的、被渲染出来的信号。底下内核的 TCP/IP 栈第二次泄露了操作系统，而且同样无法触碰。一个真实的挑战如何逐层权衡这些，在 [Cloudflare 案例研究](cloudflare-challenge.md) 中。

一个转发型 proxy 是那唯一的杠杆。它会从 proxy 的内核重新发起 TCP 连接，所以被观察到的操作系统就变成了 proxy 主机的。这样一来，一个 Windows profile 就需要一个运行在 Windows 上的 proxy；一个 Linux proxy 会给出 Linux 签名，矛盾又回来了。

!!! note "贯穿这一切的那一条规则"
    让 profile 与主机相匹配。永远不要声称你并不拥有的硬件或操作系统。检查清单里的每一条规则都是它的一个特例。

## 你真正能够改动的

你能够干净利落地改变的信号，是那些原生覆盖能触及的，或者 JavaScript 覆盖能够独占、而没有第二条路径与之矛盾的：身份（User-Agent、platform、Client Hints）、时区、locale、屏幕、`hardwareConcurrency`、`deviceMemory` 以及 CSS 媒体特性。让这些信号彼此之间，以及与你的 IP 和操作系统保持连贯。

而那道硬性底线，也就是 canvas、audio 和 GPU，你只能通过在真实、匹配的硬件上运行来让它保持连贯。介于两者之间的一切都是一种可能适得其反的权衡，所以把精力花在一致性上，而不是花在伪造更多东西上。

## 相关

- [Fingerprint 注入](../../stealth/fingerprint-injection.md)：应用一个连贯 profile 的实用指南。
- [Browser fingerprinting](browser-fingerprinting.md)：这些覆盖所触及的检测面。
- [审计一个 fingerprint](auditing.md)：测量你的哪些信号会泄露，并看看一个真实的商业检测器读到了什么。
