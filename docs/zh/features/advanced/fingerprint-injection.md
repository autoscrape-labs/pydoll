# 指纹注入

Pydoll 可以通过一次调用让浏览器**报告一个不同的、完全一致的身份**：`tab.apply_fingerprint()`。它覆盖指纹识别脚本读取的整个表面（User-Agent 和 Client Hints、`navigator`、WebGL、屏幕、字体、音频、时区和 locale），并对齐每一层，让浏览器讲述一个连贯的故事。

!!! warning "这是伪装，不是匿名"
    指纹通过呈现一个合理的、自洽的替代身份来隐藏你*是哪台*真实机器。它**不会**让你隐形，也无法修复被标记的 IP 或网络层的矛盾（见[一致性就是全部](#consistency-is-the-whole-game)）。使用不当时，一个不一致的指纹比未经改动的浏览器*更*容易被检测。

## 快速开始

在导航**之前**应用指纹。JavaScript 覆盖通过 `Page.addScriptToEvaluateOnNewDocument` 注册，因此它们只在调用之后加载的文档上生效。

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # 在首次导航前应用。
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        print('指纹已应用。')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

参数是一个 `FingerprintConfig`（来自 `pydoll.protocol.fingerprint.types` 的类型化字典），用于描述身份。只有你设置的字段会被覆盖；其余一切保持浏览器的真实值。`examples/fingerprints.py` 中的配置是完整且内部一致的参考，你可以阅读它们来了解结构（见[自带你自己的指纹](#bring-your-own-fingerprints)）。

## 伪造了什么，以及如何伪造

Pydoll 通过两种机制覆盖身份，而两者之间的选择是有意为之的。

### 通过 CDP（由浏览器原生应用）

凡是 Chrome 自身能够覆盖的，都通过 DevTools Protocol 的 `Emulation` 域来覆盖。这总是首选：浏览器在 **JavaScript 之下**应用更改，因此检测脚本读取的 getter 仍然是真正的原生 getter。没有 JavaScript 包装器可供检查。

| 信号 | CDP 命令 |
|--------|-------------|
| User-Agent、`navigator.platform` / `vendor` / `appVersion`、Client Hints（`Sec-CH-UA*`） | `Emulation.setUserAgentOverride` |
| 时区（`Intl`、`Date`） | `Emulation.setTimezoneOverride` |
| 地理位置 | `Emulation.setGeolocationOverride` |
| 屏幕尺寸、`devicePixelRatio`、viewport、方向 | `Emulation.setDeviceMetricsOverride` |
| Locale（`Intl` 格式化） | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

!!! tip "为什么原生优于 JavaScript"
    用 JavaScript getter 设置 `navigator.hardwareConcurrency` 会留下一个脚本能抓到的伪造（见下文）。用 `Emulation.setHardwareConcurrencyOverride` 设置它会改变值，同时 getter 保持逐字节原生。当存在 CDP 覆盖时，Pydoll 使用它并完全跳过 JavaScript 路径。

### 通过 JavaScript 注入

凡是 CDP 无法触及的，都作为一个脚本注入，该脚本在每个新文档上先于任何页面脚本运行（并在 Web Workers 内重放，见下文）。这涵盖：

- `navigator` 额外项：`deviceMemory`、`maxTouchPoints`、`doNotTrack`、`pdfViewerEnabled`
- `screen.availWidth` / `availHeight`（CDP 强制这些等于屏幕尺寸，是一个 headless 迹象）、`colorDepth`、`pixelDepth`，以及 `window.outerWidth` / `outerHeight`
- WebGL 的 vendor、renderer 以及参数/精度值
- `navigator.mediaDevices`、Web Audio、`speechSynthesis` 语音
- 字体可用性（`document.fonts.check` / `FontFace.load`）
- `navigator.connection`（Network Information API）
- `navigator.permissions` 查询结果
- WebRTC IP 处理策略

!!! note "canvas 被有意保留为真实"
    Pydoll **不会**给 canvas 或 WebGL 读回添加噪声。检测系统会多次请求指纹；一个在多次读取之间变化的哈希本身就是一个强烈的自动化信号。真实 Chrome 的真实 canvas 是一致且不起眼的。重要的是你声明的 *WebGL vendor/renderer* 与你声明的平台一致，而这正是覆盖所对齐的。

## Prototype 问题

伪装的难点不是改变一个值，而是**改变时不被抓到**。现代反机器人脚本（CreepJS 是参考实现）不只是读取 `navigator.hardwareConcurrency`；它们检查该属性*如何*被定义，以及周围的机制是否被篡改。三种迹象已成为标准，而幼稚的伪装在这三者上都失败。

**1. 本该是 prototype getter 的地方却出现自有属性。** 在真实浏览器中，`hardwareConcurrency` 是 `Navigator.prototype` 上的一个 accessor，而不是 `navigator` 实例上的数据属性。幼稚的做法会创建一个自有属性：

```javascript
// 可检测：在实例上创建了一个自有属性
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

// navigator.hasOwnProperty('hardwareConcurrency')  ->  true   （真实 Chrome：false）
```

一个遍历 `Object.getOwnPropertyNames(navigator)` 或将实例与其 prototype 比较的脚本会立即看到这个异常。

**2. 一个出卖伪造的 `toString`。** 每个原生 getter 都报告为原生代码：

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency')
    .get.toString();
// 真实：  "function get hardwareConcurrency() { [native code] }"
// 幼稚：  "() => 8"   或   "function () { ... }"
```

`Function.prototype.toString` 作用于手写的 getter 会返回它的 JavaScript 源码，因此一次 `.toString()` 调用就暴露了覆盖。

**3. 跨 realm 泄漏。** 页面可以创建一个新的 JavaScript realm（同源 `iframe`，或 Web Worker），其 `navigator` 和 prototype 未被仅安装在主 realm 的 hook 触及。worker 有自己的 `WorkerNavigator`；如果它报告真实的 `hardwareConcurrency` 而页面报告一个伪造值，两者就不一致，谎言被证实。

### Pydoll 如何解决

- **getter 定义在 prototype 上**，即原生 getter 所在之处（`Navigator.prototype`、`Screen.prototype`），因此实例不留下任何异常的自有属性。
- **注入的函数在 `toString` 下报告为原生。** 覆盖的安装方式使得对被修改 getter 的 `toString` 内省与真正的 `[native code]` accessor 无法区分，并且对 `toString` 本身的补丁也不会成为新的迹象。
- **身份在 workers 内重放。** Pydoll 自动附加到专用、共享和服务 workers，并对每个 `WorkerNavigator` 应用相同的覆盖，因此页面和它派生的每个 realm 都讲述相同的故事。

这正是让 Pydoll 指纹通过 CreepJS 的谎言检测、prototype、workers 和字体检查的原因，而不仅仅是改变可见的数字。

## Headless 模式

在指纹注入之前，headless Chrome 很容易被检测，这正是机器人检查和验证码在 headless 下如此频繁失败的原因：在任何交互之前，浏览器就已经看起来像机器人了。在没有真实显示器和 GPU 的情况下运行会改变可测量的信号：

- **WebGL renderer（决定性迹象）。** 没有 GPU 直通时，headless Chrome 通过软件光栅化器（SwiftShader）渲染。`UNMASKED_RENDERER_WEBGL` 报告类似 `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` 或 `Google SwiftShader`，而不是真实的 GPU 字符串，例如 `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` 或 `Apple M3`。这个迹象是致命的，因为仅修补字符串无法解决：整个 GPU 能力表面（支持的扩展、shader 精度、最大纹理尺寸）仍然反映软件光栅化器，并被与所声明的 GPU 交叉核对。
- **空的 `navigator.plugins` / `mimeTypes`**，而真实的桌面 Chrome 会暴露内置 PDF 查看器条目。
- **`screen.availWidth` / `availHeight` 等于整个屏幕尺寸**（没有任务栏或程序坞的间隙），加上一个固定或归零的外部窗口。
- **缺失的媒体设备，以及与真实显示器机器不同的字体/音频光栅化**。
- 在旧的 `--headless` 上，User-Agent 中有一个 `HeadlessChrome` 令牌（在 `--headless=new` 中已移除，但上述所有渲染迹象仍然存在）。

指纹注入中和了这些。它覆盖 WebGL 的 vendor 和 renderer **以及**参数和精度表面，让整个 GPU 故事保持连贯，而不只是字符串；以真实的任务栏间隙报告 `availWidth` / `availHeight`；恢复媒体设备和字体；并通过 CDP 固定 User-Agent，使任何 `HeadlessChrome` 令牌都无法幸存。应用配置后，**所有测试过的检测站点都将浏览器报告为一个普通的、有界面的 Chrome**，运行 headless 不再改变结果。

在实践中，这正是让一次普通的 Google 搜索在 headless 模式下运行的原因：同一段在 headless 下被 Google 阻止的自动化，在指纹让浏览器看起来真实之后就通过了。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # 在首次导航前中和 headless 渲染迹象。
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Google 搜索在 headless 模式下完成。')

asyncio.run(headless_google_search())
```

!!! note "将其与 Cloudflare Turnstile 搭配使用"
    应用指纹后 Turnstile 失败最常见的原因是 **Chrome 版本不匹配**，而不是 headless，见[案例研究：Chrome 版本不匹配触发 Cloudflare 的挑战](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)。先让配置的版本与真实二进制文件匹配。即便修复了这一点，可靠的 **headless** Turnstile 仍在验证中，因此目前 Turnstile 请优先使用有界面模式。见 [Cloudflare Turnstile](behavioral-captcha-bypass.md)。

!!! warning "渲染，而非声誉"
    指纹注入移除的是 headless 的*渲染*迹象；它不会改变你的 IP。一个声誉不佳的数据中心 IP 在 headless 和有界面下同样会被挑战（见 [Cloudflare Turnstile，什么决定成功](behavioral-captcha-bypass.md#what-determines-success)）。将一致的指纹与干净的住宅 IP 搭配使用。

## 一致性就是全部 {#consistency-is-the-whole-game}

指纹的强度取决于其最薄弱的一层，而反机器人系统会跨所有层关联信号。一个渲染为 macOS，却在 `Accept-Language` 中说巴西葡萄牙语、时区说东京、IP 地理定位在德国的浏览器，比一个你从未碰过的浏览器*更*可疑。

`apply_fingerprint()` 保持**它所控制的**各层内部一致。你负责它无法控制的三层：

1. **你所驱动的 Chrome 二进制文件。** 网络层指纹（TLS JA3/JA4、HTTP/2 `SETTINGS`）由真实浏览器产生，无法通过 CDP 伪造，JavaScript 引擎的真实版本也无法。一个声明 Chrome 145 的配置必须运行在 Chrome 145 二进制文件上，否则 User-Agent 会与真实握手矛盾。这正是阻止 Cloudflare Turnstile 的原因，见[案例研究：Chrome 版本不匹配触发 Cloudflare 的挑战](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)。
2. **你出口 IP 的地理位置。** `Accept-Language` 头和时区会与 IP 的国家交叉核对。美国身份出现在巴西 IP 上是一个矛盾（这正是[案例研究：Locale 不匹配触发 Google 的验证码](#case-study-a-locale-mismatch-triggering-googles-captcha)中记录的失败）。
3. **主机的真实操作系统。** 内核的 TCP/IP 栈是一种被动操作系统指纹（例如，macOS/Linux 上初始 TTL 为 64，而 Windows 为 128），真实的 GPU/文本渲染同样会暴露真实的操作系统。两者都无法通过 CDP 触及。在 Mac 上驱动一个声明 Windows 的配置是一个操作系统矛盾，Cloudflare 的托管挑战会因此拦截它，见[案例研究：操作系统不匹配触发 Cloudflare 的托管挑战](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)。

!!! tip "黄金法则"
    **每一层都必须讲述同一个故事。** 关于这一原则见[浏览器指纹识别](../../deep-dive/fingerprinting/index.md)，关于 locale、时区和 IP 地理位置如何被关联见[规避技术，时区与 Locale 一致性](../../deep-dive/fingerprinting/evasion-techniques.md)。

## 案例研究：Locale 不匹配触发 Google 的验证码 {#case-study-a-locale-mismatch-triggering-googles-captcha}

在测试期间，应用一个美国指纹配置会让一次普通的 Google 搜索开始返回验证码。注释掉那一行 `apply_fingerprint()` 就让拦截消失。该指纹通过了每一个专门的指纹识别站点，那么 Google 有什么不同？

**不匹配之处。** 该配置声明了一个美国身份（`locale.languages = ['en-US', 'en']`），但机器运行在一个**巴西 IP** 后面，且带有**巴西系统语言**。Google 会将 `Accept-Language` 头和 Client Hints 与 IP 的国家交叉核对。一个来自圣保罗 IP 的 `en-US` 浏览器不是真实用户通常会产生的组合，请求头到达时与其余信号不一致。这一个矛盾就足以把信任分数降到 Google 的验证码阈值以下。

**`locale` 实际控制什么。** 它不是表面功夫。`locale` 字段驱动：

- 每次请求发送的 `Accept-Language` **HTTP 头**，
- `navigator.language` 和 `navigator.languages`，
- `Intl` 格式化默认值（日期、数字、货币）。

这三者都被反滥用系统读取，且都必须与时区和 IP 一致。将配置修正为巴西 locale（与 IP 和系统匹配）在不改变其他任何东西的情况下移除了拦截。

<!-- PLACEHOLDER: 替换为由不一致指纹（美国 locale 在巴西 IP 上）产生的 Google 验证码截图。建议文件：docs/resources/images/fingerprint-inconsistent-captcha.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-inconsistent-captcha.png" alt="Google 因为注入指纹的美国 locale 与巴西出口 IP 矛盾而提供验证码" width="720" />
</p>
<p align="center"><sub>不一致的指纹：美国 locale 覆盖在巴西 IP 之上。Google 返回一个验证码。</sub></p>

<!-- PLACEHOLDER: 替换为 locale 与 IP 对齐后一个正常 Google 结果页面的截图。建议文件：docs/resources/images/fingerprint-consistent-pass.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-consistent-pass.png" alt="当指纹 locale 与出口 IP 国家匹配后，Google 返回正常搜索结果" width="720" />
</p>
<p align="center"><sub>一致的指纹：locale、时区和 IP 全部一致。搜索得以通过。</sub></p>

!!! danger "结论"
    一个通过了每一项指纹识别测试的指纹，如果**一**层与你的环境矛盾，仍然可能被拦截。检测关乎关联，而非任何单一的值。在归咎于指纹之前，先让 `locale`、`timezone` 和地理位置与你的出口 IP 匹配。

## 案例研究：Chrome 版本不匹配触发 Cloudflare 的挑战 {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

要将 [Cloudflare Turnstile](behavioral-captcha-bypass.md) 交互与指纹**一起**使用，浏览器所声明的版本必须与你所驱动的真实 Chrome 二进制文件匹配。这不是可选项，而弄错它是指纹注入破坏 Turnstile 的最常见方式。

**观察。** 应用 `macos_m3_new_york` 配置会让 Cloudflare Turnstile 即使在**非 headless** 下也失败：页面卡在"Just a moment…"中间页上，永不放行。移除那一个 `apply_fingerprint()` 调用会让它在四秒内通过。所以问题既不是 headless，也不是 JavaScript 注入（它通过了每一个专门的指纹识别套件）：而是覆盖引入的某个东西。

**不匹配之处。** 该配置在其 User-Agent 中硬编码了 **Chrome 145**，但机器驱动的是真实的 **Chrome 151** 二进制文件。`apply_fingerprint()` 将 `navigator.userAgent`、`Sec-CH-UA` 和 `navigator.userAgentData` 覆盖为声明 145，而真实的 TLS/HTTP2 握手和 JavaScript 引擎仍是 151。一次单变量二分确认了这一点：在保持其他一切不变、只把声明的主版本从 145 翻到 151 后，每一次失败都变成了通过。

**为什么版本必须匹配。** 有两层报告浏览器的真实版本，且**无法**通过 CDP 伪造：

- **网络握手。** TLS 指纹（JA3/JA4）和 HTTP/2 `SETTINGS` 帧在任何 JavaScript 运行之前就由真实的 Chrome 构建产生。它们编码了真实的引擎版本。
- **JavaScript 引擎表面。** 可用 API 的集合及其行为反映真实的 V8/Blink 构建。

Cloudflare 的托管挑战会把你**声明**的版本（User-Agent + Client Hints）与它能**观察**到的版本（握手和引擎）交叉核对。真实浏览器绝不会声明一个与其运行版本不同的版本，因此在 151 握手之上声明 145 是任何真实客户端都不会产生的矛盾。Turnstile 降低信任分数，中间页永不放行。

**如何匹配。** 读取真实二进制文件的版本，并让配置的 User-Agent 与之一致：

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # 例如 'Chrome/151.0.7922.137'
```

在 `examples/fingerprints.py` 中，`CHROME_DESKTOP` / `CHROME_MOBILE` 常量设置了烘焙进每个配置 User-Agent 的版本。将它们设为你的二进制文件所报告的主版本（完整构建号供给 `Sec-CH-UA-Full-Version-List`；可见的 `navigator.userAgent` 会自动缩减为 `Chrome/<MAJOR>.0.0.0`）。当你升级 Chrome 时，把它们一起调高，否则下一次挑战会抓到这个落差。

!!! danger "Cloudflare + 指纹的规则"
    一个 Chrome 版本与真实二进制文件不匹配的指纹**将会**被 Turnstile 挑战，无论有无界面。在把指纹注入与 Cloudflare 交互搭配之前，先让配置的版本与 `browser.get_version()` 对齐。

## 案例研究：操作系统不匹配触发 Cloudflare 的托管挑战 {#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge}

在对齐 Chrome 版本（上面的案例）之后，第二个配置仍然失败。原因更为根本：你无法声明一个机器并不运行的操作系统。

**观察。** 在这台主机上（Apple Silicon、真实 Chrome 151、巴西 IP），`macos_m3_new_york` 配置通过 Cloudflare，而 `windows11_rtx3060_nyc` 失败（卡在"Um momento…"）。Chrome 版本已经匹配（都是 151），所以不是上面那个案例。而失败的那个配置恰恰是与巴西 IP **在地理上一致**的，通过的那个反而是覆盖在巴西 IP 之上的美国身份，所以也不是 locale。唯一重要的区别是**操作系统**：一个作为 macOS 通过（与主机匹配），另一个作为 Windows。

**二分。** 从通过的配置出发，一次一个轴地朝失败的配置变异，结果**只跟随 User-Agent 中声明的操作系统**：

- 在失败的配置上只把 User-Agent/平台从 Windows 换成 macOS：**通过**。
- 在通过的配置上只把 User-Agent/平台从 macOS 换成 Windows：**失败**。
- 换成 Linux User-Agent：**同样失败**。
- 换 GPU/WebGL（renderer 字符串、参数、扩展）、canvas、字体、屏幕、硬件、音频、语音、地理位置和 locale：**没有一个能翻转结果**。

在这台 macOS 主机上，任何非 macOS 的操作系统都失败；任何 macOS 身份都通过。GPU 无关紧要：一个声明 NVIDIA GPU 的 macOS 配置通过，而一个声明真实 Apple GPU 的 Windows 配置失败。

**它发生在哪一层。** 在同一个 Chrome 上，测量两个配置下每一层实际向服务器报告的内容：

- **TCP/IP（无法伪造）：** 服务器为两个配置观察到相同的 TTL，推断出初始 TTL 为 **64**（macOS/Unix 家族）。Windows 主机会发出 128。无论 User-Agent 声称什么，内核栈都说"macOS"。
- **TLS（JA3/JA4）：** 每次连接都在变化（Chrome 的 padding 扩展切换）；同一个未加指纹的基线会产生两种变体。它不编码操作系统。
- **HTTP/2（Akamai 指纹）：** 两个配置之间完全相同。它不编码操作系统。
- **Client Hints：** 完全覆盖为所声明的操作系统（在 Windows 下，`architecture` 报告 `x86`，没有泄露真实的 `arm`）。
- **Canvas/WebGL：** 渲染图像的哈希在两个配置之间**完全相同**（两者都是真实 Apple GPU 的像素）。渲染图像不是区分点。

`apply_fingerprint()` 所控制的一切都一致地说 Windows；唯一剩下的一层，即内核 TCP/IP 栈，说 macOS。Cloudflare 的托管挑战会把你**声明**的操作系统（User-Agent + Client Hints）与它能**观察**到的操作系统（被动栈签名）交叉核对，当它们不一致时保持中间页。

**为什么无法通过 CDP 伪造。** TTL、窗口缩放和 TCP 选项顺序来自主机内核，而非浏览器。没有任何 JavaScript 或 CDP 覆盖能触及它们。真实的 GPU 渲染和文本度量（macOS 上的 CoreText）也属于主机。这就是为什么一个外来操作系统的配置无法仅靠浏览器指纹伪造通过，也是为什么伪造 TLS 的工具（curl_cffi、tls-client）没有帮助：问题不在 TLS，而它们仍然使用主机内核的 TCP/IP 栈。

**修复。** 让配置的操作系统（和 GPU 家族）与真实主机匹配。在这台 Mac 上，使用 macOS/Apple 配置；在 Windows 主机上运行 Windows/NVIDIA 配置。转发代理（SOCKS5/HTTP CONNECT）会从代理的内核重新发起 TCP 连接，因此 Cloudflare 观察到的操作系统变成代理主机的操作系统：要作为 Windows 通过，代理必须运行在 Windows 上（Linux 代理会给出 Linux 签名，仍与 Windows User-Agent 不一致）。需要调整的不是 GPU、canvas 或字体，而是声明的操作系统必须与发起数据包的内核匹配。

<!-- PLACEHOLDER: 替换为在 macOS 主机上驱动 Windows 配置时，Cloudflare 托管挑战卡住（"Um momento…"）的截图。建议文件：docs/resources/images/fingerprint-os-mismatch-challenge.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-os-mismatch-challenge.png" alt="因为配置声明 Windows 而主机是 macOS，Cloudflare 卡在中间页上" width="720" />
</p>
<p align="center"><sub>macOS 主机上的 Windows 配置：内核 TCP/IP 说 macOS，User-Agent 说 Windows。Cloudflare 保持挑战。</sub></p>

<!-- PLACEHOLDER: 替换为使用操作系统与主机匹配的配置后页面放行的截图。建议文件：docs/resources/images/fingerprint-os-match-pass.png -->
<p align="center">
  <img src="../../resources/images/fingerprint-os-match-pass.png" alt="当配置的操作系统与 macOS 主机匹配时 Cloudflare 放行" width="720" />
</p>
<p align="center"><sub>macOS 主机上的 macOS 配置：每一层都一致。挑战放行。</sub></p>

!!! danger "操作系统规则"
    你无法声明一个机器并不运行的操作系统。内核 TCP/IP 栈和主机的真实渲染会在 CDP 无法触及的层暴露真实操作系统。选择操作系统与主机匹配的配置（Mac 上用 macOS 配置，Windows 上用 Windows），不要试图仅靠浏览器指纹在 Apple 硬件上伪造 Windows。

## 多个指纹与浏览器上下文

服务 worker 和共享 worker 在**一个浏览器上下文的所有标签页之间共享**，因此一个上下文只能承载一个连贯的身份。Pydoll 强制这一点：向一个已有指纹的上下文应用一个*不同的*指纹会抛出 `FingerprintContextConflict`。

```python
from pydoll.exceptions import FingerprintContextConflict

# 同一上下文，两个不同的指纹 -> 冲突
tab_a = await browser.start()
await tab_a.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

tab_b = await browser.new_tab()               # 同一（默认）上下文
try:
    await tab_b.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
except FingerprintContextConflict:
    print('一个上下文承载一个身份。')
```

要让**不同的**指纹并排运行，把每个放进它自己的浏览器上下文：

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

关于隔离上下文如何工作，见[浏览器上下文](../browser-management/contexts.md)。

## 自带你自己的指纹 {#bring-your-own-fingerprints}

!!! important "Pydoll 不生成也不分发指纹"
    `examples/fingerprints.py` 中的配置**仅作为参考**存在：它们展示一个配置需要多么连贯，以及你传给 `apply_fingerprint()` 的 `FingerprintConfig` 的确切结构。它们不是一个可以照搬部署的目录，也不是为你生成的。

    一个可用的指纹是你为**你自己的**环境构建的。它必须匹配：

    - 你所驱动的**真实 Chrome 二进制文件**（网络层是真实且不可伪造的），以及
    - 你**出口 IP 的地理位置**（locale、时区、地理位置）。

    把一个公开配置重用得足够广泛，它就不再是伪装，而变成了一个签名。构建你自己的。

## 另见

- **[浏览器指纹识别](../../deep-dive/fingerprinting/index.md)** - 黄金法则以及检测如何逐层工作
- **[规避技术](../../deep-dive/fingerprinting/evasion-techniques.md)** - 时区/locale 一致性、User-Agent 一致性、WebRTC 泄漏防护
- **[浏览器指纹识别（检测表面）](../../deep-dive/fingerprinting/browser-fingerprinting.md)** - 深入了解 Canvas、WebGL、navigator 和字体检测
- **[浏览器上下文](../browser-management/contexts.md)** - 隔离地运行多个身份
- **[代理配置](../configuration/proxy.md)** - 让你的出口 IP 与指纹的地理位置匹配
