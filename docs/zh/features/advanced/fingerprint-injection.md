# 指纹注入

`tab.apply_fingerprint()` 覆盖指纹识别脚本读取的浏览器身份信号：User-Agent 和 Client Hints、`navigator` 属性、WebGL、屏幕指标、字体、音频、时区和 locale。被覆盖的值必须与彼此以及与 `apply_fingerprint()` 无法控制的层保持一致（见[跨层一致性](#consistency-is-the-whole-game)）。一个不一致的指纹比未修改的浏览器更容易被检测。

这是身份替换，不是匿名：它不改变网络层指纹，也不改变出口 IP。

## 快速开始

在首次导航之前调用 `apply_fingerprint()`。JavaScript 覆盖通过 `Page.addScriptToEvaluateOnNewDocument` 注册，因此只对调用之后加载的文档生效。

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

`FingerprintConfig`（来自 `pydoll.protocol.fingerprint.types`）是一个类型化字典。只有存在的字段会被覆盖；其余保持浏览器的真实值。`examples/fingerprints.py` 中的配置是关于 config 结构的完整且内部一致的参考（见[提供你自己的配置](#bring-your-own-fingerprints)）。

## 检查清单

一个不被检测的配置的规则。大多数描述的是 `apply_fingerprint()` 无法控制的层，所以配置必须被选择来与之匹配，而不是与之对抗。

- 配置的操作系统 = 主机操作系统。不要在 macOS 上运行 Windows 配置，反之亦然；内核 TCP/IP 栈以及 GPU/文本渲染会在 CDP 无法触及的层暴露真实操作系统（[操作系统不匹配](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)）。
- User-Agent 的 Chrome 版本 = 真实二进制文件版本。让 `CHROME_DESKTOP` / `CHROME_MOBILE` 等于 `browser.get_version()` 的主版本，并在每次 Chrome 升级时更新（[Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。
- Locale、时区和地理位置 = 出口 IP 的国家。`Accept-Language` 和时区会与 IP 交叉核对（[Locale/IP 不匹配](#case-study-a-locale-mismatch-triggering-googles-captcha)）。
- WebGL 的 vendor/renderer = 主机 GPU 家族（Apple 硬件上用 Apple renderer，依此类推）。渲染出的像素来自真实 GPU，无法伪造。
- 在首次导航之前应用指纹。
- 每个浏览器上下文一个身份；对不同身份使用不同的上下文（[跨上下文的多个指纹](#multiple-fingerprints-across-contexts)）。
- 不要把 `--user-agent` 选项与 `apply_fingerprint()` 组合；指纹拥有 User-Agent。
- 使用干净的住宅 IP。注入不改变 IP 声誉。

## 覆盖

覆盖通过两种机制应用。

### 通过 CDP 的覆盖

Chrome 自身能够覆盖的信号通过 DevTools Protocol 的 `Emulation` 域设置。浏览器在 JavaScript 层之下应用这些更改，因此检测脚本读取的 getter 仍然是原生的，没有 JavaScript 包装器可供检查。当某个信号存在 CDP 覆盖时，会使用它而不是 JavaScript 覆盖。

| 信号 | CDP 命令 |
|--------|-------------|
| User-Agent、`navigator.platform` / `vendor` / `appVersion`、Client Hints（`Sec-CH-UA*`） | `Emulation.setUserAgentOverride` |
| 时区（`Intl`、`Date`） | `Emulation.setTimezoneOverride` |
| 地理位置 | `Emulation.setGeolocationOverride` |
| 屏幕尺寸、`devicePixelRatio`、viewport、方向 | `Emulation.setDeviceMetricsOverride` |
| Locale（`Intl` 格式化） | `Emulation.setLocaleOverride` |
| `navigator.hardwareConcurrency` | `Emulation.setHardwareConcurrencyOverride` |

`hardwareConcurrency` 说明了区别：JavaScript getter 是可检测的（见下文），而 `Emulation.setHardwareConcurrencyOverride` 改变值的同时 getter 保持原生。

### 通过 JavaScript 注入的覆盖

CDP 无法触及的信号由一个脚本设置，该脚本在每个新文档上先于任何页面脚本注入，并在 Web Workers 中重放。这涵盖：

- `navigator` 额外项：`deviceMemory`、`maxTouchPoints`、`doNotTrack`、`pdfViewerEnabled`
- `screen.availWidth` / `availHeight`（CDP 强制这些等于屏幕尺寸，是一个 headless 信号）、`colorDepth`、`pixelDepth`，以及 `window.outerWidth` / `outerHeight`
- WebGL 的 vendor、renderer 以及参数/精度值
- `navigator.mediaDevices`、Web Audio、`speechSynthesis` 语音
- 字体可用性（`document.fonts.check` / `FontFace.load`）
- `navigator.connection`（Network Information API）
- `navigator.permissions` 查询结果
- WebRTC IP 处理策略

canvas 和 WebGL 读回不被修改。检测系统会重复请求指纹，因此一个在多次读取之间变化的值本身就是一个自动化信号；真实 Chrome 的 canvas 是稳定的。WebGL 的 vendor 和 renderer 字符串被覆盖以匹配所声明的平台，但渲染出的像素保持不变。

## 检测 JavaScript 覆盖

指纹识别脚本不只是读取属性值；它们检查它是如何被定义的，以及周围的对象是否被修改。三种检查是标准的，一个幼稚的覆盖在这三者上都失败。CreepJS 是参考实现。

自有属性 vs prototype accessor。在真实浏览器中，`hardwareConcurrency` 是 `Navigator.prototype` 上的一个 accessor，而不是 `navigator` 实例上的数据属性：

```javascript
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
// navigator.hasOwnProperty('hardwareConcurrency') === true   （真实 Chrome：false）
```

`Object.getOwnPropertyNames(navigator)` 或与 prototype 的比较会暴露新增的自有属性。

getter 的 `toString`。原生 getter 报告为原生代码：

```javascript
Object.getOwnPropertyDescriptor(Navigator.prototype, 'hardwareConcurrency').get.toString();
// 真实：  "function get hardwareConcurrency() { [native code] }"
// 幼稚：  "() => 8"
```

`Function.prototype.toString` 返回手写 getter 的 JavaScript 源码，因此一次调用就暴露了它。

跨 realm 读取。同源 `iframe` 或 Web Worker 是一个新的 realm，其 `navigator` 和 prototype 未被仅安装在主 realm 的 hook 触及。worker 的 `WorkerNavigator` 报告真实值而页面报告覆盖值，这就是一个矛盾。

### pydoll 如何避免这些信号

- getter 定义在 prototype 上（`Navigator.prototype`、`Screen.prototype`），因此实例不获得任何自有属性。
- 被修改的 getter 和方法在 `toString` 下报告为原生，且对 `toString` 本身的补丁也不会成为新的信号。
- 覆盖在专用、共享和服务 workers 中重放，因此页面和它派生的 realm 报告相同的值。

这就是为什么注入的配置能通过 CreepJS 的谎言检测、prototype、workers 和字体检查，而不仅仅是改变可见的值。

## Headless 模式

Headless Chrome 暴露有界面浏览器不会暴露的信号，这就是在指纹注入之前机器人检查经常失败的原因：

- WebGL renderer。没有 GPU 直通时，headless Chrome 通过软件光栅化器（SwiftShader）渲染。`UNMASKED_RENDERER_WEBGL` 报告 `ANGLE (Google, Vulkan 1.3.0 (SwiftShader))` 或 `Google SwiftShader`，而不是真实 GPU 字符串，例如 `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)` 或 `Apple M3`。仅覆盖字符串是不够的：GPU 能力表面（支持的扩展、shader 精度、最大纹理尺寸）仍然反映软件光栅化器，并被与所声明的 GPU 交叉核对。
- 空的 `navigator.plugins` / `mimeTypes`，而有界面的 Chrome 会暴露内置 PDF 查看器条目。
- `screen.availWidth` / `availHeight` 等于整个屏幕尺寸（没有任务栏或程序坞的间隙），以及一个归零的外部窗口。
- 缺失的媒体设备，以及与有显示器的机器不同的字体/音频光栅化。
- 在旧的 `--headless` 上，User-Agent 中有一个 `HeadlessChrome` 令牌（在 `--headless=new` 中已移除；上述渲染信号仍然存在）。

`apply_fingerprint()` 覆盖 WebGL 的 vendor/renderer 以及参数/精度表面，以任务栏间隙报告 `availWidth`/`availHeight`，恢复媒体设备和字体，并通过 CDP 固定 User-Agent。应用配置后，测试过的检测站点将浏览器报告为有界面，headless 不再改变结果。这就是让一次 Google 搜索在 headless 模式下运行的原因：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

from examples.fingerprints import FINGERPRINTS

async def headless_google_search():
    async with Chrome() as browser:
        tab = await browser.start(headless=True)

        # 在首次导航前中和 headless 渲染信号。
        await tab.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])

        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.type_text('pydoll', humanize=True)
        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(3)
        print('Google 搜索在 headless 模式下完成。')

asyncio.run(headless_google_search())
```

指纹注入只移除 headless 的渲染信号。它不改变 IP：一个声誉不佳的数据中心 IP 在 headless 和有界面下同样会被挑战（见[什么决定成功](behavioral-captcha-bypass.md#what-determines-success)）。

对于 Cloudflare Turnstile，应用指纹后最常见的失败是 Chrome 版本不匹配，而不是 headless（见 [Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。headless Turnstile 仍在验证中；对它请优先使用有界面模式。

## 跨层一致性 {#consistency-is-the-whole-game}

反机器人系统跨层关联信号。`apply_fingerprint()` 保持它所控制的层一致，但有三层在 CDP 的触及范围之外，必须单独匹配：

1. Chrome 二进制文件版本。网络层指纹（TLS JA3/JA4、HTTP/2 `SETTINGS`）和 JavaScript 引擎版本来自真实二进制文件，无法被覆盖。一个声明 Chrome 145 的配置必须运行在 Chrome 145 二进制文件上（见 [Chrome 版本不匹配](#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge)）。
2. 出口 IP 的地理位置。`Accept-Language` 头和时区会与 IP 的国家交叉核对。美国身份出现在巴西 IP 上是一个矛盾（见 [Locale/IP 不匹配](#case-study-a-locale-mismatch-triggering-googles-captcha)）。
3. 主机操作系统。内核 TCP/IP 栈是一个被动的操作系统指纹（macOS/Linux 上初始 TTL 64，Windows 上 128），GPU/文本渲染也反映真实操作系统。两者都无法通过 CDP 触及。Mac 上的 Windows 配置是一个操作系统矛盾（见[操作系统不匹配](#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge)）。

关于关联模型，见[浏览器指纹识别](../../deep-dive/fingerprinting/index.md)和[时区与 Locale 一致性](../../deep-dive/fingerprinting/evasion-techniques.md)。

## Locale/IP 不匹配（Google） {#case-study-a-locale-mismatch-triggering-googles-captcha}

应用一个美国配置会让一次普通的 Google 搜索返回验证码；移除 `apply_fingerprint()` 调用就移除了拦截。该配置通过了每一个专门的指纹识别站点，所以触发是 Google 特有的。

该配置在一台位于巴西 IP 后、带有巴西系统语言的机器上声明了美国身份（`locale.languages = ['en-US', 'en']`）。Google 会将 `Accept-Language` 头和 Client Hints 与 IP 的国家交叉核对。来自圣保罗 IP 的 `en-US` 是一个不寻常的组合，请求头与其他信号不一致，把信任分数降到了验证码阈值以下。

`locale` 字段驱动：

- 每次请求发送的 `Accept-Language` HTTP 头，
- `navigator.language` 和 `navigator.languages`，
- `Intl` 格式化默认值（日期、数字、货币）。

这三者都被反滥用系统读取，且必须与时区和 IP 一致。设置巴西 locale（与 IP 匹配）在不做其他任何更改的情况下移除了拦截。

<p align="center">
  <img src="../../../../resources/images/fingerprint-inconsistent-captcha.png" alt="Google 因为注入指纹的美国 locale 与巴西出口 IP 矛盾而提供验证码" width="720" />
</p>
<p align="center"><sub>美国 locale 覆盖在巴西 IP 之上：Google 返回一个验证码。</sub></p>

## Chrome 版本不匹配（Cloudflare Turnstile） {#case-study-a-chrome-version-mismatch-triggering-cloudflares-challenge}

要将 [Cloudflare Turnstile](behavioral-captcha-bypass.md) 交互与指纹组合，声明的 Chrome 版本必须与真实二进制文件匹配。这是应用指纹后 Turnstile 失败最常见的原因。

应用 `macos_m3_new_york` 配置会让 Turnstile 即使在有界面下也失败：页面停在"Just a moment…"中间页上，而移除 `apply_fingerprint()` 调用就让它通过。该配置在 User-Agent 中硬编码了 Chrome 145，而二进制文件是 Chrome 151；`apply_fingerprint()` 将 `navigator.userAgent`、`Sec-CH-UA` 和 `navigator.userAgentData` 设为 145，而 TLS/HTTP2 握手和引擎仍是 151。一次单变量二分确认了这一点：仅把声明的主版本从 145 改为 151 就把每一次失败变成了通过。

有两层报告真实版本，且无法通过 CDP 覆盖：

- TLS 指纹（JA3/JA4）和 HTTP/2 `SETTINGS` 帧，在任何 JavaScript 运行之前由真实二进制文件产生。
- JavaScript 引擎表面（可用 API 及其行为），它反映真实的 V8/Blink 构建。

Cloudflare 的托管挑战将声明的版本（User-Agent + Client Hints）与观察到的版本（握手和引擎）比较。真实浏览器不会声明一个它没有在运行的版本，因此在 151 握手之上声明 145 是一个不一致，中间页不会放行。

读取二进制文件版本，并让配置的 User-Agent 与之匹配：

```python
async with Chrome() as browser:
    tab = await browser.start()

    version = await browser.get_version()
    print(version['product'])  # 例如 'Chrome/151.0.7922.137'
```

在 `examples/fingerprints.py` 中，`CHROME_DESKTOP` 和 `CHROME_MOBILE` 设置每个配置 User-Agent 中的版本。将它们设为二进制文件的主版本（完整构建号供给 `Sec-CH-UA-Full-Version-List`；`navigator.userAgent` 会缩减为 `Chrome/<MAJOR>.0.0.0`）。Chrome 更新时更新它们。

## 操作系统不匹配（Cloudflare） {#case-study-an-os-mismatch-triggering-cloudflares-managed-challenge}

在 Chrome 版本对齐后，第二个配置仍然失败。在这台主机上（Apple Silicon、Chrome 151、巴西 IP），`macos_m3_new_york` 通过 Cloudflare，而 `windows11_rtx3060_nyc` 失败。版本匹配（都是 151），且失败的配置是与 IP 地理一致的那个，所以版本和 locale 都不是原因。差别在于声明的操作系统。

从通过的配置向失败的配置进行的单变量二分只跟踪 User-Agent 中的操作系统：

- 在失败的配置上把 User-Agent/platform 从 Windows 改为 macOS：通过。
- 在通过的配置上把 User-Agent/platform 从 macOS 改为 Windows：失败。
- 一个 Linux User-Agent：失败。
- GPU/WebGL（renderer、params、扩展）、canvas、字体、屏幕、硬件、音频、语音、geo、locale：无影响。

在这台 macOS 主机上，任何非 macOS 操作系统都失败。声明 NVIDIA GPU 的 macOS 配置通过；声明真实 Apple GPU 的 Windows 配置失败。

逐层测量，两个配置，同一 Chrome：

- TCP/IP：服务器对两个配置观察到相同的初始 TTL 64（macOS/Unix）；Windows 主机发出 128。无法通过 CDP 触及。
- TLS（JA3/JA4）：每个连接变化（Chrome 的 padding 扩展切换）；无指纹的基线产生两种变体。不编码操作系统。
- HTTP/2（Akamai）：两个配置之间相同。不编码操作系统。
- Client Hints：完全覆盖为声明的操作系统（Windows 报告 `architecture` `x86`，不泄露 `arm`）。
- Canvas/WebGL：两个配置之间渲染图像哈希相同（两者都是真实 Apple GPU 像素）。不是区别因素。

`apply_fingerprint()` 控制的一切都报告 Windows；内核 TCP/IP 栈报告 macOS。Cloudflare 的托管挑战将声明的操作系统与被动栈签名比较，当它们不一致时保持中间页。

TTL、window scaling 和 TCP 选项顺序来自主机内核，而非浏览器，没有 CDP 或 JavaScript 覆盖能触及它们。GPU 渲染和文本指标（macOS 上的 CoreText）也是主机的。伪造 TLS 的客户端（curl_cffi、tls-client）在这里没有帮助：失败不在 TLS，而且它们仍然使用主机内核的 TCP/IP 栈。

要通过，让配置的操作系统（和 GPU 家族）与主机匹配：这台 Mac 上用 macOS 配置，Windows 主机上用 Windows 配置。转发代理（SOCKS5/HTTP CONNECT）从代理的内核重新发起 TCP 连接，因此观察到的操作系统变成代理主机的；这样一个 Windows 配置就需要一个运行在 Windows 上的代理（Linux 代理给出 Linux 签名，仍与 Windows User-Agent 不一致）。

## 跨上下文的多个指纹 {#multiple-fingerprints-across-contexts}

服务 worker 和共享 worker 在一个浏览器上下文的所有标签页之间共享，因此一个上下文承载单一身份。向一个已有指纹的上下文应用不同的指纹会抛出 `FingerprintContextConflict`：

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

要同时运行不同的指纹，为每个身份使用一个单独的浏览器上下文：

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

关于隔离上下文如何工作，见[浏览器上下文](../browser-management/contexts.md)。

## 提供你自己的配置 {#bring-your-own-fingerprints}

pydoll 不生成也不分发指纹。`examples/fingerprints.py` 中的配置是关于一个配置所需的连贯性以及 `FingerprintConfig` 结构的参考；它们不是一个可以照搬部署的目录。

一个配置必须与环境匹配：

- 使用中的 Chrome 二进制文件（网络层是真实的，无法被覆盖），以及
- 出口 IP 的地理位置（locale、时区、地理位置）。

一个被广泛重用的公开配置会变成一个共享签名，而不是一个伪装。

## 另见

- [浏览器指纹识别](../../deep-dive/fingerprinting/index.md) - 逐层检测
- [规避技术](../../deep-dive/fingerprinting/evasion-techniques.md) - 时区/locale 一致性、User-Agent 一致性、WebRTC 泄漏防护
- [浏览器指纹识别（检测表面）](../../deep-dive/fingerprinting/browser-fingerprinting.md) - canvas、WebGL、navigator 和字体检测
- [浏览器上下文](../browser-management/contexts.md) - 隔离的身份
- [代理配置](../configuration/proxy.md) - 让出口 IP 与配置匹配
