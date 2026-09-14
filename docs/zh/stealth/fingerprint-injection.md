# Fingerprint 注入

## 简介

`tab.apply_fingerprint()` 给浏览器一个新身份。它在第一次导航之前，覆盖 fingerprinting 脚本读取的信号，User-Agent 和 Client Hints、`navigator`、WebGL 和 WebGPU、屏幕参数、字体、音频、权限、时区和 locale，覆盖范围包括页面、它的 workers（嵌套的也算）以及它的 cross-origin iframes。你不用手写 fingerprint，也不用给 `navigator` 打补丁；你传入一个 profile，Pydoll 会一致地应用它：凡是浏览器自带 override 命令的地方就走那条路，只有在没有命令的地方才用加固过的 JavaScript。

收益很具体。配上一个匹配的 profile，headless Chrome 就从一眼被判为 bot 变成读起来像一台普通桌面机，足以[在 headless 模式下通过 Cloudflare 的托管挑战](#clear-cloudflares-challenge-headless)。

先说清楚一个界限：这是身份替换，不是匿名。它不改变你的出口 IP，也不改变网络层 fingerprint，而且一个不一致的 profile 比未经修改的浏览器更容易被检测。让 profile *匹配*你的机器和 IP 才是全部的工作，[下面的规则](#making-a-profile-pass)就是这份清单。

!!! warning "这些都不是保证"
    本页以及它链接到的各篇 deep dive 里的一切，描述的是检测器*可以*读取什么：文献和逆向出来的 agent 所记录的那些检查。某个站点具体跑哪几项、每一项权重多大，是那个站点自己的秘密。一个最小 profile（User-Agent、locale、时区与 host 和 IP 匹配）单靠自己就能通过许多目标，而一处微小的残留不一致可能根本不会被读到。从简单开始，对着真实站点测试，只在测量表明某个具体信号就是拦住你的原因时才添加字段。为一致而追求彻底一致，是目标可能永远不会奖励的功夫。

**你将学到**

- [如何应用一个 fingerprint](#quick-start)
- [它如何在 headless 下通过 Cloudflare](#clear-cloudflares-challenge-headless)
- [如何证明它在起作用](#prove-it-with-a-bot-score)
- [如何让一个 profile 通过](#making-a-profile-pass)
- [哪些是原生的，哪些是 JavaScript](#native-first)
- [如何使用你自己的 profile](#bring-your-own-profiles)

## 快速开始 {#quick-start}

在第一次导航之前调用 `apply_fingerprint()`。只有 profile 中存在的字段会被覆盖；其余保持浏览器的真实值。

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # 在第一次导航之前应用。
        await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

!!! note "`FINGERPRINTS` 从哪来"
    Pydoll 不附带 fingerprint profile。`FINGERPRINTS` 位于 [pydoll 仓库](https://github.com/autoscrape-labs/pydoll) 的 `examples/fingerprints.py`，是 `FingerprintConfig` 结构（来自 `pydoll.protocol.fingerprint.types` 的一个 typed dict）的参考 profile。把这个文件复制到你的项目里，再把每个 profile 适配到你自己的机器和 IP，[下面的规则](#making-a-profile-pass)会解释原因。原样复用一个 profile 是一个共享签名，而不是伪装。

## 在 headless 下通过 Cloudflare 挑战 {#clear-cloudflares-challenge-headless}

headless Chrome 通常一上来就通不过 bot 检查：软件 WebGL 渲染器、写死的 800x600 屏幕、空的插件列表。一个匹配的 profile 会中和这些渲染信号，于是 headless 会话读起来就像 headful。再把身份也复制进 cross-origin 挑战 iframe（`cross_origin_iframes`，默认开启），这就足以通过 Cloudflare 的托管挑战，完全不需要 captcha solver。

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Pydoll 在 headless 模式下加载一个受 Cloudflare 保护的站点，并在应用了 fingerprint 后通过托管挑战" width="760" />
</p>
<p align="center"><sub>Headless 没有可见窗口，这是它的 CDP screencast。配上一个匹配的 fingerprint，托管挑战通过。</sub></p>

```python
async with Chrome() as browser:
    tab = await browser.start(headless=True)

    # 把 profile 匹配到这台 host 和这个 IP（见下面的规则）。
    await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

    await tab.go_to('https://a-site-behind-cloudflare.com')
    # 身份一致时，interstitial 就会通过。
```

让它成立有两个条件，都来自[下面的规则](#making-a-profile-pass)：profile 必须一致（OS、Chrome 版本和 locale 都要匹配你的 host 和 IP），并且 IP 要干净。信誉差的机房 IP 在 headless 和 headful 下一样会被挑战。IP 不理想时，优先用 headful，或在 Xvfb 下跑 headful。

在底层，headless 还有一个 cross-origin frame 会直接读取的 client-side 泄漏：它自己的 `window.screen`。不做 reshape，这个 frame 会读到原始的 800x600 headless 屏幕，与页面矛盾；做了 reshape，两者就一致。

<iframe scrolling="no" src="/docs/resources/visuals/headless-screen-oopif.html" aria-label="一个 headless 页面和它的 cross-origin iframe 各自读取 window.screen；切换 reshape 会让 iframe 从原始的 800x600 headless 屏幕翻转到与页面一致" style="width: 100%; height: 460px; border: 0;" loading="lazy"></iframe>

关于挑战究竟读取了什么，以及为什么一致就能通过的完整拆解，见 [Cloudflare 的托管挑战](../deep-dive/fingerprinting/cloudflare-challenge.md)。

## 用 bot score 来证明 {#prove-it-with-a-bot-score}

一个 fingerprint 是帮忙还是帮倒忙，是可以量化的。[fingerprint-scan.com](https://fingerprint-scan.com/) 由 Castle 反 bot 博客背后的工程师打造，给出一个 0 到 100 的 **bot score**，越低越像人。headless 是最鲜明的演示：没有 profile 时，headless Chrome 拿满分；一个匹配的 profile 会把它降到 headful 的水平。

| 运行（同一台 Mac，Chrome 151） | Bot score |
|---|---|
| Headless，无 profile | 100 / 100 |
| Headless，匹配的 macOS profile | 15 / 100 |
| Headful，无 profile | 15 / 100 |
| Headful，匹配的 macOS profile | 15 / 100 |
| Headful，不匹配的 Windows profile | 57 / 100 |

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com 对没有 fingerprint 的 headless Chrome 报告 100/100 的 bot score" width="380" />
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com 对应用了 macOS fingerprint 的 headless Chrome 报告 15/100 的 bot score" width="380" />
</p>
<p align="center"><sub>Headless：无 profile 时 100/100，匹配的 macOS profile 时 15/100。</sub></p>

这证明了两点。profile 不会让浏览器隐形：即便匹配，也是 15，不是 0（CDP 上的真实 Chrome 本来就读起来像人，把最后这点差距抹平是一个开放问题）。而一个*不匹配*的 profile 比完全没有 profile 还差，最后一行跳到 57，因为有一个字段（OS）和底层硬件矛盾。这正是这些规则存在的原因。

!!! warning "这些数字只是一个快照"
    一台机器、一个 IP、一个 Chrome build、一个时间点。你的会不同，检测站点也会改评分。把它当成方向（匹配的偏低，不匹配的跳高），而不是保证的结果。

完整的审计方法，读回一个信号、比较各个 realm，见 [审计一个 fingerprint](../deep-dive/fingerprinting/auditing.md)。

## 让一个 profile 通过 {#making-a-profile-pass}

一个 profile 能通过，是因为它和运行它的机器与 IP 相符。这些规则大多描述的是 `apply_fingerprint()` 触及不到的层，所以你要去匹配它，而不是硬碰。它们本质上是同一条规则：**每一层都要一致**。

### 让 profile 的 OS 匹配你的 host OS

内核的 TCP/IP 栈和 OS 的文本渲染，会在任何 override 都触及不到的层里暴露真实的 OS。在 Mac 上用 Windows profile 是一个矛盾，Cloudflare 会据此拦截，也正是上面把 bot score 推到 57 的那个不匹配。在 macOS 上跑 macOS profile，在 Windows 上跑 Windows profile。转发代理会从代理的内核重新发起 TCP 连接，所以 Windows profile 这时就需要一个跑在 Windows 上的代理。完整测量：[The OS must match the host](../deep-dive/fingerprinting/cloudflare-challenge.md#the-os-must-match-the-host)。

### 让 Chrome 版本匹配你的二进制

TLS 握手和 JavaScript 引擎会报告二进制的真实版本；User-Agent 是 `apply_fingerprint()` 唯一改动的部分。一个声称 Chrome 145 却跑在 Chrome 151 二进制上的 profile 是一个矛盾，也是应用 fingerprint 后 Turnstile 失败最常见的原因。读出二进制的版本，把 profile 的 `CHROME_DESKTOP` / `CHROME_MOBILE` 主版本号与之保持一致，并在每次 Chrome 升级时更新。

```python
version = await browser.get_version()
print(version['product'])  # 例如 'Chrome/151.0.7922.137'
```

完整拆解：[The Chrome version must match the binary](../deep-dive/fingerprinting/cloudflare-challenge.md#the-chrome-version-must-match-the-binary)。

### 让 locale 和时区匹配你的出口 IP {#match-locale-and-timezone-to-your-egress-ip}

`Accept-Language`、`navigator.languages` 和时区会和 IP 所在国家做交叉核对。一个 US profile 在巴西 IP 后面，会让一次普通的 Google 搜索返回 captcha；改成巴西的 locale、和 IP 相符，就在不做任何其他改动的情况下解除了拦截。

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google 返回一个 captcha，因为注入的 fingerprint 的 US locale 与巴西出口 IP 矛盾" width="640" />
</p>
<p align="center"><sub>US locale 配巴西 IP：Google 返回一个 captcha。</sub></p>

### 覆盖 cross-origin iframes

保持 `cross_origin_iframes` 开启（默认），让在自己进程里的挑战或 captcha frame 读到注入的身份，而不是真实机器。它只作用于真正会读 fingerprint 的 frame，所以不会拖慢普通的第三方 iframe。

```python
# 默认：身份也覆盖 cross-origin iframes。
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

# 关掉后只覆盖顶层页面、same-origin frame 和 workers。
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'], cross_origin_iframes=False)
```

身份如何抵达每个 realm：[Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md)。

### Service worker 与嵌套 worker 的脚本 {#service-worker-and-nested-worker-scripts}

有两个请求是在任何 worker target 存在之前、由浏览器进程发出的：service worker 脚本的抓取，以及从另一个 worker 内部派生出的 worker 的脚本抓取。任何按会话的 override 都触及不到它们，所以放任不管的话，它们会带着真实的 User-Agent 和 `Accept-Language` 出去，而其他每一个请求带的都是 profile 的，一个注册了 service worker 的站点就会在它的服务器上看到两个身份。Pydoll 从浏览器连接上把这个口子堵上：它用 `Fetch` 域只暂停那些被 Chrome 归类为 `Other` 的请求（这两个脚本抓取、favicon 之类；页面的文档、脚本、图片和 fetch 永远不会被暂停），并根据为该请求所属 browser context 登记的 fingerprint 重写这两个首部。在本地测试服务器上实测，两个脚本随后都带着 profile 的身份到达，不涉及任何启动标志。

如果你同时设置了 `--user-agent`，让它与 profile 的精简版 User-Agent（`Chrome/MAJOR.0.0.0`）保持一致；不同的值会记录一条 warning 日志。

### 钉住 User-Agent 承载不了的 Client Hints

自 User-Agent 精简以来，这个字符串被冻结了（`Mac OS X 10_15_7`、`Android 10; K`、`Chrome/152.0.0.0`），而真实 Chrome 仍然在 `Sec-CH-UA-Platform-Version`、`Sec-CH-UA-Model` 和 `navigator.userAgentData.getHighEntropyValues()` 里报告真实的 OS 版本、设备型号和形态。解析器会按 OS 填入合理的默认值。设置 `client_hints`，把它钉在你所模仿的那台设备上读到的精确值：Windows 11 host 根据 build 不同报告 `'13.0.0'` 及以上，Galaxy S24 Ultra 报告 `'SM-S928B'`。在一台真实机器上用 `navigator.userAgentData.getHighEntropyValues(['platformVersion', 'model'])` 读出来，而不是靠猜。

```python
fingerprint = FingerprintConfig(
    user_agent=UA_WINDOWS,
    client_hints=ClientHintsFingerprint(platform_version='15.0.0'),
)
```

greased brand（`"Not?A_Brand";v="24"`）和三个 brand 的顺序也不是自由文本。Chromium 会根据主版本号算出这两者，所以检测器可以重新算出那个主版本的真实 Chrome 会发送的精确 `Sec-CH-UA`。Pydoll 运行同一套算法；你永远不用手写 brand。

### 让你声称的字体与你安装的字体相匹配

`fonts` 部分覆盖的是 `FontFace.load()` 的存在性探测（`document.fonts.check()` 保持原生：真实 Chrome 对任何字体族都回答 `true`，所以在那里强制返回 `false` 本身就是一个破绽）。最古老的字体探测两者都不读：它测量一段文本 span 在所声称字体族下与回退字体的宽度差，而布局引擎用真正安装的字体来作答。在一台 Mac 上，无论 profile 怎么说，一个 Windows profile 都会测出 Segoe UI 和 Calibri 缺席、Menlo 和 Helvetica Neue 在场。要通过这项探测，所声称的字体必须安装在 host 上，而且 `available_fonts` 必须只列出已安装的字体，一个不多。

### 每个 browser context 一个 fingerprint {#one-fingerprint-per-browser-context}

service 和 shared workers 在一个 browser context 内共享，所以一个 context 持有一个身份。给已经有身份的同一个 context 再应用第二个 fingerprint，会抛出 `FingerprintContextConflict`。把不同身份放到各自独立的 context 里跑。

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

见 [Browser contexts](../guides/browser-contexts.md)。

还有几条小规则：在第一次导航之前应用 fingerprint；如果你设置了 `--user-agent` 选项，让它与 profile 的保持一致（User-Agent 由 profile 掌管）；让 WebGL 的 vendor/renderer、WebGPU adapter 和 color-gamut 匹配 host 的 GPU 和显示器，并从同一类别的真实设备上捕获 WebGPU 的 limits 和 features；用一个干净的住宅 IP。关于哪些信号可以安全覆盖、哪些根本无法伪造，见 [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md)。

### Headless 模式 {#headless-mode}

headless Chrome 只有一块写死的虚拟屏幕（800x600，没有工作区）和一个没有窗口边框的窗口。profile 的 `screen` 部分会以原生方式重塑这两者：`Emulation.updateScreen` 为浏览器里的每一个 frame（包括 cross-origin iframes）设置虚拟屏幕的尺寸、工作区（`availTop`、`availHeight`）、色深和整数像素比，`Browser.setWindowBounds` 把窗口调到 `outer_width` x `outer_height`，于是 `outerWidth`、`innerWidth` 和每一个 `screen.*` 值都来自 Chrome 自身，背后没有任何 JavaScript getter。小数的 `device_pixel_ratio`（Windows 的显示缩放）是虚拟屏幕唯一装不下的值；它通过 `setDeviceMetricsOverride` 应用到页面，并在 cross-origin iframes 里取整。

在 headful 模式下真实屏幕就是真实的，所以 `screen.width`、`screen.height` 和像素比通过 `setDeviceMetricsOverride` 覆盖，窗口被调整为 `outer_*`，只有工作区的附加值（`availHeight`、`availTop`、`colorDepth`）还保留一个 JavaScript getter。

## 原生优先，JavaScript 垫底 {#native-first}

凡是 Chrome 能通过它自己的协议覆盖的信号，都在那里应用，profile 的 JavaScript 从不碰它们：User-Agent、`navigator.platform` / `appVersion` / `vendor`、`navigator.language` 和 `languages`（全部由 `Emulation.setUserAgentOverride` 设置）、Client Hints、`hardwareConcurrency`、时区、地理位置、locale、CSS 媒体特性、触摸事件、权限（`Browser.setPermission`，所以 `navigator.permissions.query()` 返回一个货真价实的 `PermissionStatus`，`Notification.permission` 也与之一致），以及在 headless 下的整块屏幕。

原生覆盖背后没有函数。这对于一项 JavaScript getter 无法通过的检查至关重要：在一个外来对象上调用这个 getter，然后读取调用栈。原生 accessor 抛出 `Illegal invocation`，没有属于自己的栈帧；JavaScript accessor 抛出同样的错误，却多出一行 `at get userAgent`。检测厂商描述的正是这种探测。把身份移到原生覆盖上，就为上面每一个信号消除了那一帧。

留在 JavaScript 里的，是 Chrome 没有提供命令的那一组：`deviceMemory`、`maxTouchPoints`、WebGL、WebGPU、媒体设备、语音合成的 voices、音频设备能力、`navigator.connection`、字体、WebRTC 策略，以及 headful 下的工作区附加值。每一个都按原生的形态来写。getter 和方法在 `toString` 下报告 `[native code]`，位于真实的 prototype 上，先调用原始的原生实现以便外来 receiver 抛出真实的错误，并且从不创建自有属性：一个假的麦克风是一个 `InputDeviceInfo`，一个假的 voice 是一个 `SpeechSynthesisVoice`，两者的 `Object.getOwnPropertyNames()` 都为空。值也保持在物理上可能的范围内：`OfflineAudioContext` 报告它被构造时的采样率，GPU 不具备的 WebGL 扩展会从列表中删除而不是伪造成一个空对象，`WEBGL_debug_shaders` 则被隐藏，因为它翻译后的 shader 源码会点名真实的后端。

有一处残留是与生俱来的：那些 JavaScript getter 仍然是函数，所以那一帧额外的栈帧对它们来说依然存在。这无法从 JavaScript 里去掉；上面的策略只是把这一组压到 Chrome 允许的最小。用两种方式读同一个信号，看看你处在哪里：[审计一个 fingerprint](../deep-dive/fingerprinting/auditing.md)。

## 使用你自己的 profile {#bring-your-own-profiles}

Pydoll 不生成也不附带 fingerprint。`examples/fingerprints.py` 里的 profile 是一份参考，说明一个 profile 需要怎样的一致性以及 `FingerprintConfig` 的结构，而不是一份可以原样部署的目录。一个 profile 必须匹配在用的 Chrome 二进制（网络层是真实的，无法覆盖）和出口 IP 的地理位置（locale、时区、地理定位）。一个被广泛复用的公开 profile，会变成共享签名，而不是伪装。

## 下一步

- [审计一个 fingerprint](../deep-dive/fingerprinting/auditing.md)：读回一个信号、比较各个 realm，确认一个 profile 生效了。
- [Cloudflare 的托管挑战](../deep-dive/fingerprinting/cloudflare-challenge.md)：按层拆解 headless 下什么能通过、为什么。
- [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md)：哪些信号可以安全覆盖，哪些无法伪造。
- [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md)：身份如何被复制到每个 realm。
- [Network fingerprinting](../deep-dive/fingerprinting/network-fingerprinting.md)：注入触及不到的 TLS/TCP/HTTP2 层。
- [Evasion techniques](evasion-techniques.md)：User-Agent 一致性、WebRTC 泄漏防护，以及 Pydoll 免费给你的东西。
