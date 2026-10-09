# 规避技术

检测系统会跨层关联各种信号：网络 fingerprint（TCP/TLS/HTTP2）、浏览器 fingerprint（canvas、WebGL、navigator）以及行为（鼠标、键盘、时序）。通过了一层却在另一层失败，仍然会让你被标记。一个住宅 IP 却带着不匹配的 TCP fingerprint，或者一个完美的浏览器 fingerprint 却配上机器人式的点击，都会被任何做交叉比对的系统抓住。本页讲的是 Pydoll 免费提供给你的部分，以及你能掌控、用来保持各层一致的杠杆。

<iframe scrolling="no" src="/docs/resources/visuals/evasion-layers.html" aria-label="网络、浏览器、行为和 IP 各层必须全部保持一致才能通过" style="width: 100%; height: 320px; border: 0;" loading="lazy"></iframe>

## 你免费获得的部分

因为 Pydoll 通过 CDP 驱动真实的 Chrome，而不是凭空构造请求，所以有几层无需任何配置就是真实的：

- **真实的网络 fingerprint。** Chrome 的 TCP/IP 栈、TLS（BoringSSL）和 HTTP/2 栈会产生真正的 fingerprint：TLS ClientHello、HTTP/2 `SETTINGS` 帧、伪首部顺序和流优先级都与真实的 Chrome 一致。而以编程方式构造请求的工具（requests、httpx、curl）做不到这一点。
- **真实的浏览器 fingerprint。** Canvas、WebGL 和 AudioContext 都来自真实的 GPU 和音频硬件。Navigator 属性、内置的 PDF 插件和 MIME 类型都反映了真实的浏览器状态。
- **`navigator.webdriver` 为 `false`。** Selenium、Playwright 和 Puppeteer 会把它设为 `true`。Pydoll 启动时不带自动化标志，所以它报告 `false`，和普通会话一样。你无需修补它。
- **完整的输入事件序列。** 通过 CDP 派发的输入会生成完整的事件链（`pointermove`、`pointerdown`、`mousedown`、`pointerup`、`mouseup`、`click`），与真实用户完全一样。

本页接下来讲的是你确实能掌控的那些层。

## 保持 User-Agent 一致

最常见的自动化破绽是一个自相矛盾的 User-Agent：HTTP `User-Agent` 首部说的是一回事，而 `navigator.userAgent`、`navigator.platform` 和 Client Hints（`Sec-CH-UA`、`Sec-CH-UA-Platform`）说的又是另一回事。把 `--user-agent=` 作为普通的 Chrome 标志来设置，只会改变 HTTP 首部，而不会改动 JavaScript 和 Client Hints，这种不匹配会被检测器立刻读出来。

Pydoll 会帮你修正这一点。当它检测到 `--user-agent=` 参数时，会用匹配的 `platform` 和完整的 Client Hints 元数据（greased brand 和 brand 顺序按 Chromium 对那个主版本的算法算出）来应用 `Emulation.setUserAgentOverride`，并暴露真实 Chrome 所报告的精简形式 `Chrome/MAJOR.0.0.0`。于是每一层都一致：网络上的首部、`navigator.userAgent`、`platform`、`vendor` 和 `appVersion`、低熵和高熵的 hints（`Sec-CH-UA`、`brands`、`fullVersionList`），在第一个标签页、之后打开的每个标签页以及 workers 内部都是如此。页面本身不会被注入任何脚本，这些值来自 override 本身。Workers 是唯一会运行一段脚本的地方：CDP 的 override 触及不到 `WorkerNavigator.platform`，也触及不到 shared worker 和 service worker 的 User-Agent，所以 Pydoll 会在每个 worker 的代码开始之前附加上去，在那里设置这两个值。

=== "Sync"

    ```python
    from pydoll.sync import Chrome, ChromiumOptions

    def main():
        options = ChromiumOptions()
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/154.0.0.0 Safari/537.36'
        )

        with Chrome(options=options) as browser:
            tab = browser.start()
            tab.go_to('https://browserleaks.com/javascript')

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome, ChromiumOptions


    async def main():
        options = ChromiumOptions()
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/154.0.0.0 Safari/537.36'
        )

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://browserleaks.com/javascript')

    asyncio.run(main())
    ```

`154` 是撰写本页时这台机器上安装的 Chrome 主版本号；请换成你的。下一节解释为什么这个数字是字符串里唯一由不得你选的部分。这个覆盖会应用于第一个标签页、通过 `browser.new_tab()` 创建的标签页，以及通过 `browser.get_opened_tabs()` 获取的标签页。

## 让主版本号与二进制保持一致 {#keep-the-major-equal-to-the-binary}

Override 改写的是浏览器*声称*的版本。它改写不了浏览器*是*什么：你启动的那个二进制的 JavaScript 引擎和 web 平台。每个 Chrome 主版本都会带来新的 API，一个检测器只要从 User-Agent 里解析出主版本号，再探测那个版本尚不存在的函数，就能读出真实的版本。下面是 Chrome 154 在以声称为 130 的 User-Agent 启动时的回答：

| 表面 | 报告 |
|---|---|
| `User-Agent` 首部、`navigator.userAgent`、`navigator.appVersion` | Chrome 130 |
| `Sec-CH-UA`、`navigator.userAgentData.brands`、`fullVersionList` | 130，并带有 Chrome 130 当年使用的 GREASE brand `Not?A_Brand` |
| `RegExp.escape`（136 引入）、`Float16Array`（135）、`Error.isError`（134）、`Uint8Array.fromBase64`（140）、`Math.sumPrecise`（146） | 全部存在 |

五个在 Chrome 130 里并不存在的函数都在，所以这个页面是一个挂着 130 徽章的 Chrome 146 或更新版本。这么廉价的检查很常见：FingerprintJS 的 BotD 和 CreepJS 这类开源检测器都带有每个 Chromium 主版本增删了哪些 API 和 CSS 属性的表格，据此框定引擎的版本区间，并标记落在区间之外的 User-Agent；有些还会去取当前 Stable 发布号，标记声称比它更新的 User-Agent。Google 的 reCAPTCHA 至少从 2016 年起就把 User-Agent 里过时的引擎版本视为可疑（Sivakorn、Polakis 与 Keromytis，*I am Robot*，EuroS&P 2016）。声称比二进制更新的主版本会以相反的方式失败：承诺的 API 不存在。引擎还会以更安静的方式暴露自己，因为错误消息的文本、某些 `Math` 结果的最后几位以及接受的语法都会随 V8 版本变化。在这一切底下，TLS ClientHello 和 HTTP/2 settings 能识别引擎家族和大致年代，所以声称是 Firefox 或 Safari 在任何 JavaScript 运行之前就已失败。

字符串的其余部分由你决定。Chrome 自己在 User-Agent 里报告的就是精简形式 `Chrome/MAJOR.0.0.0`，完整 build 只保留在高熵 hints 里，而 override 会根据你给的值把它们填得一致。所以 build 是唯一可以变动的部分，而且只有在该平台对这个主版本确实有多个 build 时才行。轮换身份意味着轮换二进制（品牌、build），而不是字符串；一个在 Stable 渠道前进时停止更新的二进制，本身就会变成一个很小的群体。把主版本号保持与 `browser.get_version()` 相同，OS 和设备取自 profile，build 保持 `0.0.0`。一行检查就能在下次 Chrome 升级时抓住不一致：

=== "Sync"

    ```python
    claimed = 154
    version = browser.get_version()['product']     # 'Chrome/154.0.8037.58'
    assert int(version.split('/')[1].split('.')[0]) == claimed, version
    ```

=== "Async"

    ```python
    claimed = 154
    version = (await browser.get_version())['product']     # 'Chrome/154.0.8037.58'
    assert int(version.split('/')[1].split('.')[0]) == claimed, version
    ```

## 让语言、时区和地理位置与 IP 匹配

在 proxy 之后，浏览器的语言、时区和位置应当与该 IP 所在的国家一致。一个位于东京的 IP，却带着 `Accept-Language: en-US` 和 `America/New_York` 时区，就是自相矛盾的。

语言是一个独立的选项：

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

这会同时设置 `Accept-Language` 首部和 `navigator.language` / `navigator.languages`。时区和地理位置也必须匹配，而且它们需要同时与 User-Agent 所声明的操作系统以及 IP 保持一致。从单个 profile 出发连贯地设置这些，正是 `apply_fingerprint()` 的用途；参见 [Fingerprint 注入](fingerprint-injection.md)。

## 阻止 WebRTC 泄露你的 IP

WebRTC 即便在 proxy 之后也可能泄露真实 IP，因为 STUN 请求会绕过 proxy 隧道。每当你为了 stealth 而使用 proxy 时，都应打开内置的保护：

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True   # --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

## 表现得像真人

瞬间点击和完全规律的按键是一种行为 fingerprint。传入 `humanize=True`，就能让光标沿一条曲线、以拟人的节奏移动，并以变化的节奏打字，偶尔出现被纠正的拼写错误：

=== "Sync"

    ```python
    field = tab.find(id='search')
    field.type_text('browser automation', humanize=True)
    field.click(humanize=True)
    ```

=== "Async"

    ```python
    field = await tab.find(id='search')
    await field.type_text('browser automation', humanize=True)
    await field.click(humanize=True)
    ```

关于时序模型以及如何调整它，参见 [拟人化交互](human-like-interactions.md)。

## 看起来像一个用过的 profile

一个全新的、没有任何历史记录、所有功能都被禁用的 profile，和真实用户的 profile 毫不相像。通过 `browser_preferences` 预先填充这个 profile（陈旧的时间戳、匹配的 Chrome 版本、已启用的功能），具体见 [浏览器偏好设置](../guides/browser-preferences.md#build-a-realistic-profile-for-stealth)。

## 常见错误

### 把一切都随机化。

随机的 `hardwareConcurrency`、`deviceMemory` 和屏幕尺寸会拼凑出不可能存在的设备。真实的机器是受约束的：4 核配 8 GB 内存和 1920x1080 的屏幕是合理的；17 核配 0.5 GB 内存和 4K 屏幕则不然。请使用从真实浏览器采集的 profile，而不是随机值。

### 注入 canvas 噪声。

给 canvas 输出添加噪声会适得其反：检测器会反复采样 fingerprint，而一个在多次读取之间发生变化的值，本身就是一个自动化信号。Pydoll 的 canvas 是真实且稳定的；别去动它。

### 过时的 User-Agent。

一个来自六个月前 Chrome 版本的 UA，声称的是二进制早已不是的主版本号，而引擎的功能集合会把这一点暴露出来；见[让主版本号与二进制保持一致](#keep-the-major-equal-to-the-binary)。真实用户的 Chrome 会自动更新，所以当前的主版本号也是大多数流量的样子。

### 忽视会话行为。

即便有一个干净的 fingerprint，一分钟内加载 100 个页面、从不滚动、从不空闲，也都是异常。请加入阅读延迟、变化节奏，并包含自然的停顿。

## 验证你的配置

在大规模运行之前，用以下这些工具检查你的 fingerprint：

| 工具 | URL | 测试内容 |
|------|-----|-------|
| BrowserLeaks | `https://browserleaks.com/` | Canvas、WebGL、字体、IP、WebRTC、HTTP/2 |
| CreepJS | `https://abrahamjuliot.github.io/creepjs/` | 谎言检测、一致性检查 |
| Pixelscan | `https://pixelscan.net/` | 机器人检测分析 |
| IPLeak | `https://ipleak.net/` | WebRTC、DNS、IP 泄露 |

用 Pydoll 做一个快速自检：

=== "Sync"

    ```python
    result = tab.execute_script('''
        return {
            userAgent: navigator.userAgent,
            webdriver: navigator.webdriver,
            languages: navigator.languages,
            plugins: navigator.plugins.length,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        };
    ''')
    fp = result['result']['result']['value']

    assert fp['webdriver'] is False, 'navigator.webdriver should be false'
    assert 'HeadlessChrome' not in fp['userAgent'], 'headless leaking in the UA'
    ```

=== "Async"

    ```python
    result = await tab.execute_script('''
        return {
            userAgent: navigator.userAgent,
            webdriver: navigator.webdriver,
            languages: navigator.languages,
            plugins: navigator.plugins.length,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        };
    ''')
    fp = result['result']['result']['value']

    assert fp['webdriver'] is False, 'navigator.webdriver should be false'
    assert 'HeadlessChrome' not in fp['userAgent'], 'headless leaking in the UA'
    ```

## 下一步

- [Fingerprint 注入](fingerprint-injection.md)：从单个 profile 应用一套连贯的身份（User-Agent、WebGL、时区、locale）。
- [拟人化交互](human-like-interactions.md)：深入讲解行为层。
- [Proxy](../guides/proxies.md)：更改并验证你的出口 IP。
- [指纹识别（深入）](../deep-dive/fingerprinting/index.md)：这些杠杆背后的检测原理。
