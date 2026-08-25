# Cloudflare 的托管挑战

Cloudflare 的托管挑战，也就是那个 "Just a moment…" 过渡页，是对一个 fingerprint 最严格的真实世界测试。它会同时关联每一层，并在它自己的服务器上做出判定，所以它能抓住那些单页 bot score 会漏掉的矛盾。本页是一个完整的案例研究：通过/拦截矩阵，每一处不匹配为什么会被抓住，以及在 headless 下通过这个挑战需要什么，因为在 headless 下，身份必须一路保持一致，直到进入挑战所运行的那个跨源 iframe 里。

它把 [网络](network-fingerprinting.md) 和 [浏览器](browser-fingerprinting.md) fingerprinting 以及 [伪造的极限](spoofing-limits.md) 应用到一个实时目标上。机制请读那几页；而它们如何组合成一个单一的服务器端判定、又如何让每一层都保持一致，请读本页。

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Headless Chrome 通过一个 Cloudflare 托管挑战，从过渡页一路到通过后的页面" width="760" />
</p>
<p align="center"><sub>Headless Chrome 通过一个实时的托管挑战，使用 CDP 屏幕录制（<code>Page.startScreencast</code>）录制。过渡页之所以是葡萄牙语，是因为 profile 的 locale 与巴西的出口 IP 相匹配，这正是挑战所检查的那种一致性。</sub></p>

## 受控测试

一台机器，一个 Chrome 151 二进制文件，一个住宅 IP。各次运行之间唯一变化的就是 profile 和 headless 标志；[`apply_fingerprint()`](../../stealth/fingerprint-injection.md) 在导航之前应用。

| Profile | 模式 | UA Chrome 主版本 | 结果 |
|---|---|---|---|
| macOS（与主机匹配） | headful | 151（与二进制文件匹配） | 通过 |
| macOS | headless | 151 | 拦截 |
| macOS | headful | 140（不匹配） | 拦截 |
| Windows（操作系统不匹配） | headful | 151 | 拦截 |
| Windows | headless | 151 | 拦截 |

只有完全一致的那次 headful 运行才能通过*这个原始 profile*，而每一处不匹配的行都被一个不同的层抓住，下面会逐一讲解。headless 那一行是需要仔细读的：它并不是一堵硬墙。这个 profile 只改变了操作系统、版本和 headless 标志，所以它遗漏了 headless 要通过所同样需要的另外两样东西，即挑战的跨源 iframe 内部的身份，以及一个与出口 IP 相匹配的 locale。把这两样加上，再点击 Turnstile，那次操作系统匹配的 headless 运行同样能通过挑战（参见 [真正有效的做法](#what-actually-works)）。Windows 那几行则不同：操作系统不匹配是无法伪造的，所以它们在两种模式下都会失败。

## 操作系统必须与主机匹配 {#the-os-must-match-the-host}

一个跑在 Mac 上的 Windows profile 即便在 headful 下也会被拦截，因为操作系统会透过 `apply_fingerprint()` 触及不到的路径泄露出来：

- **字体。** profile 的字体列表是一个 JavaScript 值，但 `measureText` 和元素尺寸测量是通过真实的操作系统字体引擎来渲染的。一个没有 Segoe UI 或 Calibri、却存在 Helvetica Neue 的 "Windows" 浏览器，就是一台 Mac。
- **栅格化。** Canvas 和 WebGL 的文本绘制在 macOS 上通过 CoreText，在 Windows 上通过 DirectWrite，在 Linux 上通过 FreeType。像素各不相同，所以哈希会出卖真实的操作系统。这就是那道 [硬性底线](spoofing-limits.md)：一个任何覆盖都触及不到的、被渲染出来的信号。
- **TCP/IP 栈。** 内核设定初始 TTL（macOS 和 Linux 上是 64，Windows 上是 128）以及浏览器无法改变的其他选项。Cloudflare 会在边缘被动地读取它们（参见 [Network fingerprinting](network-fingerprinting.md)）。

单是客户端的字体泄露就已足够；而 TCP 信号是它底下的那道底线。

## Chrome 版本必须与二进制文件匹配 {#the-chrome-version-must-match-the-binary}

一个在 151 二进制文件上声称是 Chrome 140 的 User-Agent 会被拦截，因为版本会透过引擎泄露，而不只是透过那个字符串。

声明一个更老的版本，Chrome 110，而特性面仍然对应 151：`Promise.withResolvers`（在 Chrome 119 中加入）、`Array.fromAsync`（121）以及 `Uint8Array.prototype.toBase64`（140+）全都存在。一个比你所声称的版本更新的 API 就会暴露这个谎言。引擎还会以第二种方式泄露它：`Math` 精确到最后一位的精度、错误消息文本以及语法支持都会在各个 V8 版本之间变化，所以两个 Chrome 构建会产生不同的 `Math` fingerprint 哈希。字符串是可以伪造的；而它背后的引擎不行。

这两行就是 [伪造的极限](spoofing-limits.md) 的实际体现。第三行，headless，则不一样，它是本页余下部分的主题。

## 剖析 headless 拦截

在一个匹配的 profile 下，headful 和 headless 在下面这些工具和信号上看起来完全相同。这正是那个谜题：挑战让其中一个通过、把另一个拦截，尽管这些读数都是一样的。这张表里的一切都是直接测量的，在两次运行之间完全相同：

| 信号 | headful 对比 headless |
|---|---|
| CreepJS 完整报告 | 逐字节相同（相同的哈希，"0% headless"） |
| Canvas / WebGL / audio 哈希 | 相同（真实的 GPU；macOS 上不使用 SwiftShader） |
| WebGL renderer、WebGPU adapter | 相同（Apple Metal） |
| Widevine / EME、编解码器（H.264 / AAC / HEVC） | 相同 |
| `navigator.*`、插件、权限、`isUVPAA` | 相同 |
| 40 多个扁平的 window / navigator 信号 | 相同 |

`navigator.webdriver` 为 false，没有 `--enable-automation`，而且 Pydoll 从不调用 `Runtime.enable`，所以那些经典的 CDP 破绽也都不存在。无论是什么把这两次运行区分开来，它都位于这些工具所读取的那一层之下。

### 那些貌似可能的泄露，以及它们为什么是死胡同

确实有两个信号不同。两个都值得记下来，免得你去追它们：

| 信号 | headful | headless | 尝试的修复 | 仍被拦截？ |
|---|---|---|---|---|
| `matchMedia('(color-gamut: p3)')` | true | false | `setEmulatedMedia` / `--force-color-profile` | 是 |
| `matchMedia('(dynamic-range: high)')` | true | false | `setEmulatedMedia` | 是 |
| `requestAnimationFrame` 间隔 | 8.3ms（120Hz） | 16.7ms（60Hz） | `--disable-gpu-vsync`（无效果） | 是 |

这对显示媒体信号是真实的：一个 headless 虚拟显示器报告 sRGB 和 SDR。强行让两者都匹配，什么也改变不了。帧节奏是那个 "没有真实显示器" 的签名：由于没有可供呈现的表面，Chrome 的合成器会回退到一个合成的 60Hz 源（`BeginFrameArgs::DefaultInterval()`，六十分之一秒），而一台 ProMotion Mac 跑的是 120Hz。但 60Hz 正是大多数真实机器所报告的，所以单靠节奏无法成为那个判别因素，而且在没有显示器的情况下也无法把它提上去。这三者都是同一个根源（没有被呈现的表面）的后果，没有一个是那个决定性的信号。

### 逆向工程挑战所读取的内容

为了不再靠猜，就去检测挑战实际触碰了什么。用 `Page.addScriptToEvaluateOnNewDocument`（它在挑战自己的代码之前运行）注册一个探针，包装 `matchMedia`、`requestAnimationFrame`、`performance.now`、canvas、WebGL 的 `getParameter` 以及可疑的 `screen` / `navigator` getter，并记录每一次访问。

在挑战页面上，主线程几乎什么也不读：一次 `matchMedia('(prefers-color-scheme: dark)')` 和寥寥几次 `Date.now`。真正的工作发生在别处。hook `URL.createObjectURL` 就能抓到它：挑战会从 blob 派生出两个 Web Worker，而它们的源是一小段引导代码。

```js
var _p = self.trustedTypes.createPolicy('Kssz2', { createScript: s => s });
onmessage = e => e.isTrusted && e.origin === '' && e.source === null
                 && eval(_p ? _p.createScript(e.data) : e.data);
```

这个 worker 是一个 eval 汇聚点：真正的检测代码从主线程被发送给它，并在这个 worker 内部运行，脱离了那个可被检测的页面。要读取它，就给这个 worker 目标附加一个 CDP 会话（`Target.setAutoAttach` 配合 `waitForDebuggerOnStart`），启用 `Debugger`，并用 `Debugger.scriptParsed` 和 `Debugger.getScriptSource` 捕获每一个被解析的脚本；或者在恢复这个 worker 之前 hook 它里面的 `self.eval`。

这样做揭示了那个转折。在被拦截的 headless 路径上，这个 worker 从未被喂入任何东西。它只解析自己的引导代码，然后闲置着（没有入站消息，没有被 eval 的负载）。一旦第一阶段的遥测已经让客户端不通过，Cloudflare 就不会再发送第二阶段的收集器。这个 worker 是判定之后的那个阶段，而不是检测器。这就是为什么 hook 主线程的 `postMessage` 什么也抓不到，也是为什么对普通的 JavaScript 检测手段来说，这个挑战读起来就像一个黑盒。

### 真正的客户端泄露：跨源 iframe 几何信息

挑战渲染在一个位于 `challenges.cloudflare.com` 的跨源 iframe 内部，那是一个进程外 iframe（OOPIF），拥有它自己的渲染进程和它自己的 CDP 会话。页面注入的脚本和 `setDeviceMetricsOverride` 都触及不到它，而这正是之前每一个探针都漏掉的那一层。附加到 OOPIF 自己的会话上，直接读取它的 `window.screen`，泄露就在那里：

| 在 OOPIF 内部读取 | headless | headful |
|---|---|---|
| `screen.width × height` | 800 × 600 | 1440 × 900 |
| `screen.availTop` | 0 | 25 |
| `devicePixelRatio` | 1 | 2 |

800x600 加上 `availTop` 为 0，是 Chrome 硬编码的 headless 虚拟屏幕：没有窗口管理器，对所声称的 Mac 而言不可能出现，而且与顶层页面直接矛盾，因为顶层页面报告的是 profile 的 1440x900。`setDeviceMetricsOverride` 修好了顶层页面，但它是会话作用域的；这个 iframe 从没见过它。

Pydoll 用作用于浏览器全局虚拟屏幕的 `Emulation.updateScreen` 来堵住这个缺口，每一个 frame 都会读取这个虚拟屏幕，包括 OOPIF（参见 [Fingerprint 注入 → Headless 模式](../../stealth/fingerprint-injection.md#headless-mode)）。在此之后，这个 iframe 报告的就和页面一样是 1440x900 / `availTop 25` / dpr 2。唯一的一个小问题是，虚拟屏幕只接受整数的 `devicePixelRatio`，所以一个小数 dpr 会为这个 iframe 做四舍五入。

几何信息只是这个 iframe 暴露出来的第一个信号。它的 `navigator`、WebGL、时区和 languages 同样来自它自己的进程，所以单靠 `updateScreen` 会让这些仍然读到真实的机器。`apply_fingerprint(..., cross_origin_iframes=True)`（默认值）会在 iframe 自己的会话上重放完整的身份，所以这个 OOPIF 在每一个信号上都与页面匹配，而不只是屏幕（参见 [Worker 与跨源 iframe](execution-realms.md)）。

### 判定是一个累加的服务器端得分

你无法从客户端读取这个得分。挑战页面上的第一阶段脚本是一个约 226KB 的字符串表 VM 解释器：它的配置存放在 `_cf_chl_opt` 里，它带着一个 XOR 解密器（`o[i] = k[i] ^ s.charCodeAt(i % s.length)`）、base64 数据块，以及用空白填充的 `honk` 金丝雀脚本。它收集自己的遥测，加密它，并把它 POST 到 `/cdn-cgi/challenge-platform/h/b/fo/<numbers>:<ray>/<token>`；Cloudflare 在服务器端为它打分，并在失败时用一个新的 Ray ID 重新提供过渡页。这个负载是不透明的，所以在不破解加密的情况下，无法从客户端把任何单一的输入孤立出来。

这个得分是累加的，而不是单一的关卡。IP 信誉、跨层 fingerprint 一致性，以及一个显示/呈现项，都会汇入其中，而一个可疑的客户端会被*升级*到一个交互式 Turnstile，而不是被硬性拦截。由此有两个推论。一个无显示器的 headless 浏览器所发出的呈现信号，比一个拥有真实表面的浏览器更弱，所以在一个临界的 IP 上，正是这一项把得分推过了那条线，而在那里，一个真实的显示器（headful，或者在服务器上于 Xvfb 之下以 headful 运行）就是解决办法。但当得分的其余部分已经有利时，一个做到了一致*并且与 IP 相匹配*的 fingerprint，再加上点击 Turnstile，就能通过它，headless 也包括在内。

所以，能把一个 headless 客户端带到那条线以下的那些杠杆，是覆盖挑战的跨源 iframe（`cross_origin_iframes`，默认开启），以及让 profile 的时区、locale 和地理位置与出口 IP 相匹配。跨源 iframe 的身份是那个决定性的：如果把它留在真实的机器上，它会与页面矛盾，挑战就会拦截；一旦覆盖了它，再加上点击 Turnstile，headless 就能通过。

!!! note "它仍然取决于 IP"
    一个一致的 headless 客户端能在一个干净的住宅 IP 上通过挑战；而一个被标记的 IP，无论浏览器多么一致，都会被挑战或被拦截。fingerprint 一致性移除的是那些你能修复的矛盾。它并不能洗白一个糟糕的 IP。

## 真正有效的做法 {#what-actually-works}

- **匹配主机和二进制文件。** 操作系统等于主机的操作系统，Chrome 主版本等于二进制文件的主版本。
- **让 locale、时区和地理位置与出口 IP 相匹配。** 挑战会把 `Accept-Language` 和时区与 IP 所在的国家做交叉核对（参见 [Locale/IP 不匹配](../../stealth/fingerprint-injection.md#case-study-a-locale-mismatch-triggering-googles-captcha)）。在一个真实的部署中，这往往是拦截与通过之间唯一的那个杠杆。
- **覆盖跨源 iframe。** 挑战会在它自己的 `challenges.cloudflare.com` frame 内部读取 fingerprint；`apply_fingerprint(..., cross_origin_iframes=True)`（默认值）也会在那里重放身份。如果把它留在真实的机器上，iframe 会与页面矛盾，挑战就会拦截；一旦覆盖，它就是那个让 headless 客户端得以通过的项。
- **点击 Turnstile。** 托管挑战现在会提供一个交互式 Turnstile，所以那个复选框必须被点击。使用 [`expect_and_bypass_cloudflare_captcha()`](../../stealth/captcha-bypass.md)；等待自动通过只会让你继续被拦截。
- **在一个临界的 IP 上回退到真实的显示器。** 当 IP 不够干净、无法让一个一致的 headless 客户端通过时，就以 headful 运行，或者在服务器上于 Xvfb 之下以 headful 运行，好让那个呈现项不再对你不利。
- **把注入当作必要条件，而不总是充分条件。** 它移除了你能修复的那些矛盾；IP 信誉不在其中。

## 复现这一过程

上面那一趟逆向工程是一个你可以在任何挑战上重新运行的方法：

- **对单个变量做 A/B。** 各次运行之间只改变 headless 标志，或者一个 profile 字段，然后对结果做差。把一次拦截归因到某个信号，而不是靠猜。
- **在客户端运行的每一个地方检测它。** 导航之前的 `Page.addScriptToEvaluateOnNewDocument` 会记录主线程的 API 访问；`URL.createObjectURL` 的 hook 会抓住 blob worker；一个作用于每个 worker、每个跨源 OOPIF 的 CDP 会话，能触及那些页面注入脚本触及不到的代码，因为两者都不会继承它们。
- **在 OOPIF 自己的会话上读取它。** 挑战存在于一个跨源 iframe 中；它的 `window.screen` 以及其他每一次读取，都只有透过它自己的目标才能看见。
- **测量，不要假设。** [审计一个 fingerprint](auditing.md) 讲解了那种读取两条路径的方法，它能把 "它被拦截了" 变成 "正是这个字段在泄露"。

## 相关

- [伪造的极限](spoofing-limits.md)：一次伪造能改动什么、不能改动什么。
- [Network fingerprinting](network-fingerprinting.md)：Cloudflare 在边缘读取的 TCP 和 TLS 层。
- [Browser fingerprinting](browser-fingerprinting.md)：承载操作系统信息的字体、canvas 和 GPU 信号。
- [审计一个 fingerprint](auditing.md)：在把你的信号对准一个挑战之前，先测量它们中的哪些会泄露。
- [Fingerprint 注入](../../stealth/fingerprint-injection.md)：应用一个连贯的 profile。
