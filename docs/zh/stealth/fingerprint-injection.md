# Fingerprint 注入

`tab.apply_fingerprint()` 会覆盖 fingerprinting 脚本所读取的浏览器身份信号：User-Agent 和 Client Hints、`navigator` 属性、WebGL、屏幕参数、字体、音频、时区和 locale。被覆盖的这些值必须彼此保持一致，也要与 `apply_fingerprint()` 无法控制的那些层保持一致（参见 [跨层一致性](#consistency-is-the-whole-game)）。一个不一致的 fingerprint 比一个未经修改的浏览器更容易被检测。

这是身份替换，而不是匿名：它不会改变网络层 fingerprint，也不会改变出口 IP。

## 快速开始

在第一次导航之前调用 `apply_fingerprint()`。JavaScript 覆盖是通过 `Page.addScriptToEvaluateOnNewDocument` 注册的，所以它们只对调用之后加载的文档生效。

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # 在第一次导航之前应用。
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        print('Fingerprint applied.')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

`FingerprintConfig`（来自 `pydoll.protocol.fingerprint.types`）是一个带类型的字典。只有存在的字段才会被覆盖；其余字段保留真实的浏览器值。`examples/fingerprints.py` 中的 profile 是完整、内部一致的参考，用于说明这个配置的结构（参见 [提供你自己的 profile](#bring-your-own-fingerprints)）。

!!! note "`FINGERPRINTS` 从何而来"
    Pydoll 不附带 fingerprint profile。`FINGERPRINTS` 位于 [pydoll 仓库](https://github.com/autoscrape-labs/pydoll) 的 `examples/fingerprints.py` 中，作为 `FingerprintConfig` 结构的参考 profile。把那个文件复制到你的项目里就能使用它们，然后根据你自己的机器和 IP 调整每个 profile（下面的检查清单会解释为什么）。一个原样复用的 profile 是一个共享的签名，而不是伪装。

## 看出差别：一次实时的 bot score 测试 {#see-the-difference-a-live-bot-score-test}

一个 fingerprint 是帮了你还是害了你，是可以测量的。[fingerprint-scan.com](https://fingerprint-scan.com/) 由 Castle 反机器人博客背后的工程师打造，会在页面内运行一项 fingerprinting 和机器人检测测试，并给出一个从 0 到 100 的 **bot score**，越低意味着越像人类。下面这三次运行都来自同一台机器（一台 Apple Silicon Mac，Chrome 151，headful），由 Pydoll 驱动浏览器并截图。

**没有 fingerprint**，Pydoll 驱动真实 Chrome 且未应用任何东西：得分 15/100。

<p align="center">
  <img src="/docs/resources/images/fp-scan-no-fingerprint.png" alt="fingerprint-scan.com 显示 Pydoll 在未应用 fingerprint 时的 bot score 为 15/100" width="760" />
</p>
<p align="center"><sub>通过 CDP 驱动的真实 Chrome 本就被判读为人类：15/100。</sub></p>

Pydoll 本身起点就低。它通过 CDP 驱动真实的 Chrome，所以 GPU、canvas 和 TLS 都是真实的，而且 `navigator.webdriver` 为 `false`。把剩下这段到 0 的差距补上，是一个仍在改进中的方向。

**在这台 Mac 上使用 macOS profile**，一个与操作系统匹配的身份：得分 15/100。

<p align="center">
  <img src="/docs/resources/images/fp-scan-mac-on-mac.png" alt="fingerprint-scan.com 显示在 macOS 主机上应用 macOS fingerprint 时的 bot score 为 15/100" width="760" />
</p>
<p align="center"><sub>一个匹配的 macOS profile：仍然是 15/100，一致，但并非隐形。</sub></p>

在 Mac 上应用一个 Mac profile，会改变所报告的身份，而不与底层的硬件相矛盾，所以得分不会变化。一个匹配的 profile 是一致的，而不是隐形的。

**在这台 Mac 上使用 Windows profile**，有一个字段不一致：得分 57/100。

<p align="center">
  <img src="/docs/resources/images/fp-scan-windows-on-mac.png" alt="fingerprint-scan.com 显示在 macOS 主机上应用 Windows fingerprint 时的 bot score 为 57/100" width="760" />
</p>
<p align="center"><sub>仅仅一个操作系统上的矛盾，就让得分几乎翻了两番：57/100。</sub></p>

同样的注入，同样的机器；但这个 profile 现在在一台内核、GPU 和文本渲染都是 macOS 的主机上声称自己是 Windows。仅这一个矛盾，就让得分几乎翻了两番。

| 运行（同一台 Mac，Chrome 151，headful） | Bot score |
|---|---|
| 没有 fingerprint | 15 / 100 |
| macOS profile 用于 macOS（匹配） | 15 / 100 |
| Windows profile 用于 macOS（不匹配） | 57 / 100 |

两点结论。注入让 fingerprint 变得一致；但它并不能让浏览器隐形：即便是匹配的那次运行，得分也是 15，而不是 0，而缩小这段差距的工作仍在进行中。而价值在于*匹配*，这正是为什么一个不一致的 profile 得分比完全不用 profile 还要糟糕，也是为什么下面检查清单里的每一条规则都是关于各层之间的一致性。

!!! warning "这些数字只是一个快照"
    一台机器、一个 IP、一个 Chrome 构建、一个时间点。你的情况会有所不同，而且检测网站也会改变它们的评分。请把这些分数当作方向上的示范（匹配的保持低分，不匹配的会跳高），而不是有保证的结果。

同样的测试在 headless 模式下起点要高得多。在没有 profile 的情况下，headless Chrome 会拿到最高分：

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com 显示没有 fingerprint 的 headless Chrome 的 bot score 为 100/100" width="760" />
</p>
<p align="center"><sub>Headless，无 profile：最高分，100/100。</sub></p>

应用 macOS profile 后，同样的 headless 运行会降到 15，与 headful 的结果持平：

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com 显示应用了 macOS fingerprint 的 headless Chrome 的 bot score 为 15/100" width="760" />
</p>
<p align="center"><sub>带 macOS profile 的 headless：15/100，与 headful 持平。</sub></p>

在 headless 模式下，profile 对结果的改变最大，从最高分一直降到 headful 的分数。[Headless 模式](#headless-mode) 一节讲解了它中和了哪些信号。

## 让覆盖变得可见

确认一个 profile 是否生效，最简单的方式就是把某个硬件信号读回来。[browserleaks.com/webgl](https://browserleaks.com/webgl) 会报告 WebGL 背后的 GPU。在这台 MacBook 上，未应用任何 profile 时，它读到的是真实的芯片，一颗 Apple M4，以及一个 macOS 的 User-Agent：

<p align="center">
  <img src="/docs/resources/images/browserleaks-webgl-real.png" alt="browserleaks WebGL 报告显示一个 macOS User-Agent 和未掩码的 renderer ANGLE (Apple, Apple M4)" width="760" />
</p>
<p align="center"><sub>无 profile：真实的 Apple M4 和一个 macOS User-Agent。</sub></p>

应用 Windows profile 后，同一个页面在同一台机器上，报告的是一颗 NVIDIA GeForce RTX 3060 和一个 Windows User-Agent：

<p align="center">
  <img src="/docs/resources/images/browserleaks-webgl-rtx3060.png" alt="browserleaks WebGL 报告显示一个 Windows User-Agent 和未掩码的 renderer ANGLE (NVIDIA, NVIDIA GeForce RTX 3060)" width="760" />
</p>
<p align="center"><sub>Windows profile，同一台机器：一颗 NVIDIA RTX 3060 和一个 Windows User-Agent。</sub></p>

`apply_fingerprint()` 通过注入的覆盖设置了未掩码的 WebGL vendor 和 renderer，同时也设置了 User-Agent 和 Client Hints。在这同样的两张截图里，有一个诚实的局限是可见的：**WebGL Image Hash 完全相同**（`52497E30...`）。renderer *字符串*现在写的是 NVIDIA，但这些像素仍然是由真实的 Apple GPU 绘制的，所以渲染图像的 fingerprint 并没有变化。覆盖字符串是必要的，但还不够：一个把输出栅格化并对其求哈希的检测器，仍然会看到真实的硬件。这正是为什么在一台 Apple 机器上声称拥有 NVIDIA GPU，会成为上面把得分推到 57 的那个矛盾，也是为什么检查清单坚持要求 profile 的操作系统和 GPU 与主机相匹配。

## 检查清单

让一个 profile 不被检测的规则。其中大多数描述的是 `apply_fingerprint()` 无法控制的层，所以必须选择一个能与之匹配的 profile，而不是去对抗它。

- Profile 的操作系统 = 主机的操作系统。不要在 macOS 上运行 Windows profile，反之亦然；内核的 TCP/IP 栈以及 GPU/文本渲染会在 CDP 触及不到的层里暴露真实的操作系统（[操作系统不匹配](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)）。
- User-Agent 中的 Chrome 版本 = 真实二进制文件的版本。让 `CHROME_DESKTOP` / `CHROME_MOBILE` 等于 `browser.get_version()` 给出的主版本号，并在每次 Chrome 升级时更新它们（[Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。
- Locale、时区和地理位置 = 出口 IP 所在国家。`Accept-Language` 和时区会与 IP 做交叉比对（[Locale/IP 不匹配](#case-study-a-locale-mismatch-triggering-googles-captcha)）。
- WebGL vendor/renderer = 主机的 GPU 系列（Apple 硬件上就用 Apple 的 renderer，以此类推）。渲染出的像素来自真实的 GPU，无法伪造。
- 在第一次导航之前应用 fingerprint。
- 每个浏览器 context 一个身份；不同的身份使用不同的 context（[跨 context 使用多个 fingerprint](#multiple-fingerprints-across-contexts)）。
- 不要把 `--user-agent` 选项和 `apply_fingerprint()` 结合使用；User-Agent 由 fingerprint 掌管。
- 使用一个干净的住宅 IP。注入不会改变 IP 信誉。

## 覆盖

覆盖通过两种机制来应用。

### CDP 覆盖

Chrome 自身能够覆盖的信号，通过 DevTools Protocol 的 `Emulation` 域来设置。浏览器在 JavaScript 层之下应用这些覆盖，所以检测脚本读取的 getter 仍然是原生的，也没有可供检查的 JavaScript 包装器。当某个信号存在 CDP 覆盖时，就会使用它，而不是 JavaScript 覆盖。

| 信号 | CDP 命令 |
|--------|-------------|
| User-Agent、`navigator.platform` / `vendor` / `appVersion`、Client Hints（`Sec-CH-UA*`） | `Emulation.setUserAgentOverride` |
| 时区（`Intl`、`Date`） | `Emulation.setTimezoneOverride` |
| 地理位置 | `Emulation.setGeolocationOverride` |
| 屏幕尺寸、`devicePixelRatio`、视口、朝向 | `Emulation.setDeviceMetricsOverride` |
| Locale（`Intl` 格式化） | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

`hardwareConcurrency` 说明了其中的差别：一个 JavaScript getter 是可检测的（见下文），而 `Emulation.setHardwareConcurrencyOverride` 会改变这个值，同时让 getter 保持原生。

### JavaScript 覆盖

CDP 触及不到的信号，由一段在每个新文档上、先于任何页面脚本注入的脚本来设置，并在 Web Worker 中重放。这涵盖了：

- `navigator` 额外属性：`deviceMemory`、`maxTouchPoints`、`doNotTrack`、`pdfViewerEnabled`
- `screen.availWidth` / `availHeight`（CDP 会强制它们等于屏幕尺寸，这是一个 headless 信号）、`colorDepth`、`pixelDepth`，以及 `window.outerWidth` / `outerHeight`
- WebGL 的 vendor、renderer，以及参数/精度值
- `navigator.mediaDevices`、Web Audio、`speechSynthesis` 语音
- 字体可用性（`document.fonts.check` / `FontFace.load`）
- `navigator.connection`（Network Information API）
- `navigator.permissions` 查询结果
- WebRTC 的 IP 处理策略

Canvas 和 WebGL 的读回结果不会被修改。检测系统会反复请求 fingerprint，所以一个在多次读取之间发生变化的值，本身就是一个自动化信号；而真实 Chrome 的 canvas 是稳定的。WebGL 的 vendor 和 renderer 字符串会被覆盖，以匹配所声称的平台，但渲染出的像素保持不变。

## 检测 JavaScript 覆盖

Fingerprinting 脚本不只是读取一个属性的值；它们还会检查这个属性是如何被定义的，以及周围的对象是否被改动过。有三种标准的检查方法，而一个幼稚的覆盖会在这三项上全部失败。CreepJS 就是其参考实现。

自有属性 vs prototype 访问器。在真实的浏览器上，`hardwareConcurrency` 是 `Navigator.prototype` 上的一个访问器，而不是 `navigator` 实例上的一个数据属性：

```javascript
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
// navigator.hasOwnProperty('hardwareConcurrency') === true   (真实 Chrome：false)
```

`Object.getOwnPropertyNames(navigator)` 或者与 prototype 的一次比较，就会暴露这个被添加的自有属性。

getter 的 `toString`。原生 getter 会报告为原生代码：

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency').get.toString();
// 真实： "function get hardwareConcurrency() { [native code] }"
// 幼稚实现： "() => 8"
```

`Function.prototype.toString` 会返回一个手写 getter 的 JavaScript 源代码，所以一次调用就能暴露它。

跨 realm 读取。一个同源的 `iframe` 或一个 Web Worker 是一个全新的 realm，它的 `navigator` 和 prototype 不会被一个只安装在主 realm 中的 hook 所改动。一个 worker 的 `WorkerNavigator` 报告真实值，而页面报告的却是覆盖值，这就是一个矛盾。

### pydoll 如何规避这些信号

- getter 定义在 prototype 上（`Navigator.prototype`、`Screen.prototype`），所以实例不会新增任何自有属性。
- 被打补丁的 getter 和方法在 `toString` 下会报告为原生，而 `toString` 补丁本身也不会变成一个新的信号。
- 这些覆盖会在专用 worker、共享 worker 和 service worker 中重放，所以页面和它派生出的各个 realm 报告的是相同的值。

这就是为什么一个注入的 profile 能通过 CreepJS 的谎言检测、prototype、worker 和字体检查，而不只是改变了那些可见的值。

worker 检查是幼稚的覆盖最常失败的那一项。CreepJS 会在主页面中读取每个信号，然后在一个 Web Worker 中再次运行整个 fingerprint，那是一个主线程 hook 永远触及不到的独立 realm。下面的截图来自这台 Mac，并应用了 Windows profile。

在主页面中，`navigator` 部分从头到尾报告的都是 Windows 身份：platform `Win32`、`Windows 11`、Windows 的 User-Agent 和 `appVersion`，外加插件和 mimeType 列表、设备内存和核心数。

<p align="center">
  <img src="/docs/resources/images/creepjs-navigator-windows.png" alt="CreepJS 主页面中的 navigator 部分，报告 platform Win32、Windows 11、Windows 的 User-Agent 和 appVersion、插件，以及核心/内存" width="760" />
</p>
<p align="center"><sub>主页面：navigator 报告 Windows 11 身份。</sub></p>

它的 WebGL 部分以高置信度读到一颗 NVIDIA GeForce RTX 3060，旁边是来自 profile 的屏幕参数：

<p align="center">
  <img src="/docs/resources/images/creepjs-webgl-windows.png" alt="CreepJS 主页面中的 WebGL 和 Screen 部分，以高置信度读到一颗 NVIDIA GeForce RTX 3060 和一个 1920x1080 的屏幕" width="760" />
</p>
<p align="center"><sub>主页面：WebGL 读到 NVIDIA RTX 3060。</sub></p>

同样的 fingerprint 在一个 service worker 中被重新读取时，报告的是相同的 GPU，旁边是一个 Windows User-Agent、`Win32` 和 Windows 11：

<p align="center">
  <img src="/docs/resources/images/creepjs-worker-windows.png" alt="CreepJS 的 Worker 面板，展示注入的身份在 ServiceWorkerGlobalScope 中被重放：一个 Windows User-Agent、一颗高置信度的 NVIDIA GeForce RTX 3060、Win32 和 Windows 11，而这一切都在一台 Apple Mac 上" width="760" />
</p>
<p align="center"><sub>在 service worker 内部：同样的身份，被重放。</sub></p>

一个只安装在主 realm 中的覆盖，会在那个 worker 面板里泄露真实的 macOS 和 Apple GPU 值，而页面与它的 worker 之间的不一致，正是 CreepJS 判定为谎言的那个矛盾。因为 Pydoll 会把覆盖重放到专用 worker、共享 worker 和 service worker 中，所以这两个 realm 是一致的。

## Headless 模式 {#headless-mode}

Headless Chrome 会暴露 headful 浏览器不会暴露的信号，这就是为什么在 fingerprint 注入之前，机器人检查经常失败：

- WebGL renderer。在没有 GPU 直通的情况下，headless Chrome 会通过软件光栅化器（SwiftShader）来渲染。`UNMASKED_RENDERER_WEBGL` 报告的是 `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` 或 `Google SwiftShader`，而不是一个真实的 GPU 字符串，比如 `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` 或 `Apple M3`。仅仅覆盖这个字符串是不够的：GPU 的能力面（支持的扩展、着色器精度、最大纹理尺寸）仍然反映的是软件 renderer，而且会与所声称的 GPU 做交叉比对。
- 空的 `navigator.plugins` / `mimeTypes`，而 headful Chrome 会暴露内置 PDF 查看器的条目。
- `screen.availWidth` / `availHeight` 等于完整的屏幕尺寸（没有任务栏或 dock 的空隙），以及一个被清零的外部窗口。
- 缺少媒体设备，以及字体/音频的栅格化结果与一台带显示器的机器存在差异。
- 在旧的 `--headless` 下，User-Agent 中会有一个 `HeadlessChrome` 标记（在 `--headless=new` 中已被移除；但上面那些渲染信号仍然存在）。

`apply_fingerprint()` 会覆盖 WebGL 的 vendor/renderer 以及参数/精度面，用带任务栏空隙的方式报告 `availWidth`/`availHeight`，恢复媒体设备和字体，并通过 CDP 固定 User-Agent。在应用了 profile 之后，所测试的那些检测网站会把浏览器判读为 headful。

正如[上面的 bot score 测试](#see-the-difference-a-live-bot-score-test)所示，headless 从没有 profile 时的 100/100，降到应用 macOS profile 后的 15/100，与 headful 的运行结果相同。正是这一点让一次普通的 Google 搜索能够在 headless 模式下运行：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # 在第一次导航之前中和 headless 渲染信号。
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Google search completed in headless mode.')

asyncio.run(headless_google_search())
```

Fingerprint 注入只移除 headless 的渲染信号。它不会改变 IP：一个信誉不佳的数据中心 IP，无论在 headless 还是 headful 下，同样都会被挑战（参见 [哪些因素决定成败](captcha-bypass.md)）。

对于 Cloudflare Turnstile，在应用了 fingerprint 的情况下最常见的失败原因是 Chrome 版本不匹配，而不是 headless（参见 [Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。Headless 下的 Turnstile 仍在验证中；请优先使用 headful。

## 跨层一致性 {#consistency-is-the-whole-game}

反机器人系统会跨层关联各种信号。`apply_fingerprint()` 会让它所控制的那些层保持一致，但有三层在 CDP 的触及范围之外，必须单独去匹配：

1. Chrome 二进制文件版本。网络层 fingerprint（TLS JA3/JA4、HTTP/2 `SETTINGS`）和 JavaScript 引擎版本都来自真实的二进制文件，无法被覆盖。一个声称是 Chrome 145 的 profile，必须运行在 Chrome 145 的二进制文件上（参见 [Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。
2. 出口 IP 的地理位置。`Accept-Language` 首部和时区会与 IP 所在的国家做核对。一个美国身份配上一个巴西 IP 就是自相矛盾（参见 [Locale/IP 不匹配](#case-study-a-locale-mismatch-triggering-googles-captcha)）。
3. 主机操作系统。内核的 TCP/IP 栈是一种被动的操作系统 fingerprint（macOS/Linux 上初始 TTL 为 64，Windows 上为 128），而 GPU/文本渲染也会反映真实的操作系统。这两者都无法通过 CDP 触及。一个在 Mac 上运行的 Windows profile 就是一个操作系统矛盾（参见 [操作系统不匹配](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)）。

关于这个关联模型，参见 [浏览器指纹识别](../deep-dive/fingerprinting/index.md) 和 [规避技术](evasion-techniques.md)。

## Locale/IP 不匹配（Google） {#case-study-a-locale-mismatch-triggering-googles-captcha}

应用一个美国 profile 会导致一次普通的 Google 搜索返回一个 captcha；移除 `apply_fingerprint()` 调用则解除了这个封锁。这个 profile 通过了每一个专门的 fingerprinting 网站，所以触发因素是 Google 特有的。

这个 profile 在一台位于巴西 IP 之后、操作系统语言为巴西语言的机器上，声明了一个美国身份（`locale.languages = ['en-US', 'en']`）。Google 会把 `Accept-Language` 首部和 Client Hints 与 IP 所在的国家做交叉比对。来自圣保罗 IP 的 `en-US` 是一个不寻常的组合，而且请求首部与其他信号不一致，把信任分拉到了 captcha 阈值之下。

`locale` 字段驱动着：

- 每个请求上发送的 `Accept-Language` HTTP 首部，
- `navigator.language` 和 `navigator.languages`，
- `Intl` 的格式化默认值（日期、数字、货币）。

这三者都会被反滥用系统读取，并且必须与时区和 IP 保持一致。设置一个巴西 locale（与 IP 匹配），在没有做任何其他改动的情况下解除了封锁。

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google 弹出一个 captcha，因为注入的 fingerprint 的美国 locale 与巴西出口 IP 相矛盾" width="720" />
</p>
<p align="center"><sub>美国 locale 配上巴西 IP：Google 返回一个 captcha。</sub></p>

## Chrome 版本不匹配（Cloudflare Turnstile） {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

要把 [Cloudflare Turnstile](captcha-bypass.md) 交互与一个 fingerprint 结合起来，所声明的 Chrome 版本必须与真实的二进制文件相匹配。这是在应用了 fingerprint 的情况下 Turnstile 失败的最常见原因。

应用 `macos_m3_new_york` profile 会让 Turnstile 即便在 headful 下也失败：页面停留在 "Just a moment…" 的过渡页上，而移除 `apply_fingerprint()` 调用就让它通过了。这个 profile 在 User-Agent 中硬编码了 Chrome 145，而二进制文件却是 Chrome 151；`apply_fingerprint()` 把 `navigator.userAgent`、`Sec-CH-UA` 和 `navigator.userAgentData` 设成了 145，而 TLS/HTTP2 握手和引擎仍然是 151。一次单变量二分法确认了这一点：只把所声明的主版本号从 145 改成 151，就把每一次失败都变成了通过。

有两层会报告真实的版本，且无法通过 CDP 覆盖：

- TLS fingerprint（JA3/JA4）和 HTTP/2 `SETTINGS` 帧，它们由真实的二进制文件在任何 JavaScript 运行之前产生。
- JavaScript 引擎面（可用的 API 及其行为），它反映的是真实的 V8/Blink 构建。

Cloudflare 的托管挑战会把所声明的版本（User-Agent + Client Hints）与观察到的版本（握手和引擎）做比对。一个真实的浏览器不会声明一个它并未运行的版本，所以 145 配上一个 151 的握手就是一种不一致，过渡页也就不会消失。

读取二进制文件的版本，并让 profile 的 User-Agent 与之匹配：

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # 例如 'Chrome/151.0.7922.137'
```

在 `examples/fingerprints.py` 中，`CHROME_DESKTOP` 和 `CHROME_MOBILE` 设置每个 profile 的 User-Agent 里的版本。把它们设为二进制文件的主版本号（完整的构建号会供给 `Sec-CH-UA-Full-Version-List`；`navigator.userAgent` 会被精简为 `Chrome/<MAJOR>.0.0.0`）。在 Chrome 更新时更新它们。

## 操作系统不匹配（Cloudflare） {#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge}

在 Chrome 版本对齐之后，第二个 profile 仍然失败了。在这台主机上（Apple Silicon，Chrome 151，巴西 IP），`macos_m3_new_york` 能通过 Cloudflare，而 `windows11_rtx3060_nyc` 失败。两者版本一致（都是 151），而且失败的那个 profile 恰恰是地理上与 IP 一致的那个，所以原因既不是版本也不是 locale。差别在于所声明的操作系统。

从通过的 profile 向失败的 profile 做一次单变量二分法，只追踪 User-Agent 中的操作系统：

- 把失败 profile 的 User-Agent/platform 从 Windows 改成 macOS：通过。
- 把通过 profile 的 User-Agent/platform 从 macOS 改成 Windows：失败。
- 一个 Linux User-Agent：失败。
- GPU/WebGL（renderer、参数、扩展）、canvas、字体、屏幕、硬件、音频、语音、地理位置、locale：没有影响。

在这台 macOS 主机上，任何非 macOS 的操作系统都会失败。一个声明 NVIDIA GPU 的 macOS profile 能通过；而一个声明真实 Apple GPU 的 Windows profile 却失败。

逐层测量，两个 profile，同一个 Chrome：

- TCP/IP：服务器对两个 profile 观察到的都是相同的初始 TTL 64（macOS/Unix）；一台 Windows 主机则会发出 128。无法通过 CDP 触及。
- TLS（JA3/JA4）：每次连接都会变化（Chrome 的 padding 扩展开关）；无 fingerprint 的基线会产生两种变体。它不编码操作系统。
- HTTP/2（Akamai）：两个 profile 之间完全相同。它不编码操作系统。
- Client Hints：被完全覆盖为所声明的操作系统（Windows 报告 `architecture` 为 `x86`，没有 `arm` 泄露）。
- Canvas/WebGL：两个 profile 之间渲染图像的哈希完全相同（两者都是真实的 Apple GPU 像素）。这不是区分因素。

`apply_fingerprint()` 所控制的一切都报告 Windows；而内核的 TCP/IP 栈报告 macOS。Cloudflare 的托管挑战会把所声明的操作系统与被动的协议栈签名做比对，当两者不一致时就保留过渡页。

TTL、窗口缩放和 TCP 选项顺序都来自主机内核，而不是浏览器，任何 CDP 或 JavaScript 覆盖都触及不到它们。GPU 渲染和文本度量（macOS 上的 CoreText）同样属于主机。伪造 TLS 的客户端（curl_cffi、tls-client）在这里帮不上忙：失败并不在 TLS，而且它们仍然使用主机内核的 TCP/IP 栈。

要通过，就让 profile 的操作系统（以及 GPU 系列）与主机相匹配：在这台 Mac 上用 macOS profile，在 Windows 主机上用 Windows profile。一个转发型 proxy（SOCKS5/HTTP CONNECT）会从 proxy 的内核重新发起 TCP 连接，所以被观察到的操作系统会变成 proxy 主机的；这样一来，一个 Windows profile 就需要一个运行在 Windows 上的 proxy（一个 Linux proxy 会给出 Linux 签名，仍然与 Windows 的 User-Agent 不一致）。

## 跨 context 使用多个 fingerprint {#multiple-fingerprints-across-contexts}

service worker 和 shared worker 在一个浏览器 context 内的所有标签页之间是共享的，所以一个 context 只持有单一身份。对一个已经拥有 fingerprint 的 context 再应用另一个不同的 fingerprint，会抛出 `FingerprintContextConflict`：

```python
from pydoll.exceptions import FingerprintContextConflict

# 同一个 context，两个不同的 fingerprint -> 冲突
tab_a = await browser.start()
await tab_a.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

tab_b = await browser.new_tab()               # 同一个（默认）context
try:
    await tab_b.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
except FingerprintContextConflict:
    print('One context holds one identity.')
```

要并发地运行不同的 fingerprint，请为每个身份使用一个单独的浏览器 context：

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

关于隔离的 context 是如何工作的，参见 [浏览器上下文](../guides/browser-contexts.md)。

## 提供你自己的 profile {#bring-your-own-fingerprints}

Pydoll 不生成也不附带 fingerprint。`examples/fingerprints.py` 中的 profile 是一个参考，用于说明一个 profile 所需的连贯性以及 `FingerprintConfig` 的结构；它们不是一份可以原样部署的目录。

一个 profile 必须与它的环境相匹配：

- 正在使用的 Chrome 二进制文件（网络层是真实的，无法被覆盖），以及
- 出口 IP 的地理位置（locale、时区、地理位置）。

一个被广泛复用的公开 profile，会变成一个共享的签名，而不是一种伪装。

## 相关

- [规避技术](evasion-techniques.md)：User-Agent 一致性、语言、WebRTC 泄露保护，以及 Pydoll 免费提供给你的部分。
- [浏览器指纹识别](../deep-dive/fingerprinting/browser-fingerprinting.md)：本页所覆盖的检测面（canvas、WebGL、navigator、字体）。
- [网络指纹识别](../deep-dive/fingerprinting/network-fingerprinting.md)：注入无法触及的 TLS/TCP/HTTP2 层。
- [浏览器上下文](../guides/browser-contexts.md)：每个 context 运行一个身份。
- [Proxy](../guides/proxies.md)：让出口 IP 与 profile 的地理位置相匹配。
