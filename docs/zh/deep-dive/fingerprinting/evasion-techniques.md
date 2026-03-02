# 规避技术

本文档介绍使用 Pydoll 规避 fingerprinting 检测的实用技术。前面几节分别描述了各层检测的工作原理：[网络 fingerprinting](./network-fingerprinting.md)（TCP/IP、TLS、HTTP/2）、[浏览器 fingerprinting](./browser-fingerprinting.md)（Canvas、WebGL、navigator 属性）以及[行为 fingerprinting](./behavioral-fingerprinting.md)（鼠标、键盘、滚动）。本节聚焦于反制措施。

核心原则是各层之间的一致性。通过了某一检测层却在另一层失败，仍然会被标记。住宅 IP 搭配不匹配的 TCP 指纹，或完美的浏览器指纹搭配机器人式的鼠标移动，都会被任何关联信号的系统捕获。

!!! info "模块导航"
    - [网络 Fingerprinting](./network-fingerprinting.md)：协议级识别
    - [浏览器 Fingerprinting](./browser-fingerprinting.md)：应用层检测
    - [行为 Fingerprinting](./behavioral-fingerprinting.md)：人类行为分析

## Pydoll 默认提供的能力

在配置任何东西之前，了解 Pydoll 通过 CDP 使用真实 Chrome 实例默认提供了什么非常有帮助。

**真实的网络指纹。** Chrome 的 TCP/IP 协议栈、TLS 实现（BoringSSL）和 HTTP/2 协议栈会产生真实的指纹。TLS ClientHello、HTTP/2 SETTINGS 帧、伪标头顺序和流优先级都与真实 Chrome 浏览器一致。以编程方式构造 HTTP 请求的工具（requests、httpx、curl）在这些层会产生非浏览器指纹。使用 Pydoll，这些默认就是真实的。

**真实的浏览器指纹。** Canvas、WebGL 和 AudioContext 指纹来自真实的 GPU 和音频硬件。Navigator 属性、插件（标准的 5 个 PDF 插件）和 MIME 类型反映真实的浏览器状态。这里无需任何配置。

**没有 `navigator.webdriver`。** Selenium、Playwright 和 Puppeteer 会将 `navigator.webdriver` 设置为 `true`。Pydoll 直接使用 CDP，不会设置此标志。该属性为 `undefined`，与正常用户会话一致。

**完整的事件序列。** 当 Pydoll 通过 CDP 的 Input 域分发输入事件时，Chrome 会生成完整的事件链（pointermove、pointerdown、mousedown、pointerup、mouseup、click），与真实用户输入完全一致。

## User-Agent 一致性

自动化中最常见的 fingerprinting 不一致是 HTTP `User-Agent` 标头、JavaScript 中的 `navigator.userAgent`、`navigator.platform` 以及 Client Hints 标头（`Sec-CH-UA`、`Sec-CH-UA-Platform`）之间的不匹配。仅设置 `--user-agent=` 作为 Chrome 标志只会更改 HTTP 标头，而 JavaScript 属性和 Client Hints 保持不变。

Pydoll 自动解决此问题。当它在浏览器参数中检测到 `--user-agent=` 时，会：

1. 解析 UA 字符串以提取浏览器名称、版本和操作系统。
2. 通过 CDP 调用 `Emulation.setUserAgentOverride`，包含完整的 `userAgent`、正确的 `platform` 值（例如 Windows 对应 `Win32`）以及完整的 `userAgentMetadata`（Client Hints 数据，包括 `Sec-CH-UA`、`Sec-CH-UA-Platform`、`Sec-CH-UA-Full-Version-List`）。
3. 通过 `Page.addScriptToEvaluateOnNewDocument` 注入 `navigator.vendor` 和 `navigator.appVersion` 覆盖，确保在新打开的标签页中也保持一致。

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.6099.109 Safari/537.36'
)

async with Chrome(options=options) as browser:
    tab = await browser.start()
    # 现在所有层都保持一致：
    # - HTTP User-Agent 标头
    # - navigator.userAgent / navigator.platform / navigator.appVersion
    # - Sec-CH-UA / Sec-CH-UA-Platform / Sec-CH-UA-Full-Version-List
    # - navigator.userAgentData.brands / .platform
    await tab.go_to('https://example.com')
```

此覆盖会自动应用于初始标签页、通过 `browser.new_tab()` 创建的新标签页，以及通过 `browser.get_opened_tabs()` 发现的所有标签页。

!!! note "支持的平台"
    UA 解析器支持 Chrome、Edge、Windows（NT 6.1 到 10.0）、macOS、Linux、Android、iOS 和 Chrome OS。它按照 Chromium 规范生成正确的 GREASE 品牌值。

## Timezone 和 Locale 一致性

使用 proxy 时，浏览器的 timezone 和语言应与 proxy IP 的地理位置匹配。一个定位到东京的 IP 配合 `America/New_York` 的浏览器 timezone 和 `Accept-Language: en-US` 是可被检测的不一致。

### 语言配置

语言通过 Chrome 标志和 Pydoll 的选项 API 配置：

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

这会同时设置 `Accept-Language` HTTP 标头以及 `navigator.language` / `navigator.languages`。

### Timezone 覆盖

Pydoll 目前没有封装 CDP 的 `Emulation.setTimezoneOverride` 命令，因此 timezone 覆盖需要 JavaScript 注入。需要覆盖的关键 API 是 `Intl.DateTimeFormat().resolvedOptions().timeZone` 和 `Date.prototype.getTimezoneOffset()`：

```python
async def set_timezone(tab, timezone_id: str, offset_minutes: int):
    """
    通过 JavaScript 覆盖 timezone。

    Args:
        timezone_id: IANA timezone 名称（例如 'Asia/Tokyo'）
        offset_minutes: UTC 偏移量，以分钟为单位（例如 JST 为 -540）
    """
    script = f'''
        const _origDTF = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const opts = args[1] || {{}};
            opts.timeZone = '{timezone_id}';
            return new _origDTF(args[0], opts);
        }};
        Object.defineProperty(Intl.DateTimeFormat, 'prototype', {{
            value: _origDTF.prototype
        }});
        Date.prototype.getTimezoneOffset = function() {{ return {offset_minutes}; }};
    '''
    await tab.execute_script(script)
```

!!! warning "`execute_script` 与 `addScriptToEvaluateOnNewDocument`"
    `tab.execute_script()` 在当前页面上下文中运行 JavaScript。如果页面导航，覆盖就会丢失。对于需要在导航间持久保持的覆盖，请使用 CDP 的 `Page.addScriptToEvaluateOnNewDocument`，它会在每次新文档加载时、在任何页面 JavaScript 运行之前注入脚本。Pydoll 内部对 User-Agent 覆盖就使用了此方法。对于 timezone，你可以直接发送 CDP 命令：

    ```python
    await tab._connection_handler.execute_command(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': script}
    )
    ```

### Geolocation 覆盖

对于请求地理位置权限的网站，可以通过 JavaScript 覆盖 Geolocation API：

```python
async def set_geolocation(tab, latitude: float, longitude: float):
    script = f'''
        navigator.geolocation.getCurrentPosition = function(success) {{
            success({{
                coords: {{
                    latitude: {latitude}, longitude: {longitude},
                    accuracy: 1, altitude: null, altitudeAccuracy: null,
                    heading: null, speed: null
                }},
                timestamp: Date.now()
            }});
        }};
        navigator.geolocation.watchPosition = function(success) {{
            return navigator.geolocation.getCurrentPosition(success);
        }};
    '''
    await tab.execute_script(script)
```

## WebRTC 泄露防护

WebRTC 可以通过绕过 proxy 隧道的 STUN/TURN 服务器请求，暴露客户端的真实 IP 地址，即使使用了 proxy。Pydoll 提供了内置选项来防止这种情况：

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
# 添加：--force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

这会强制 Chrome 将所有 WebRTC 流量通过 proxy 路由，防止 IP 泄露。在使用 proxy 进行隐蔽自动化时应始终启用此选项。

## 行为 humanize

Pydoll 通过 `humanize=True` 参数为鼠标、键盘和滚动实现了 humanize 交互。这些不是未来功能或手动变通方案，而是框架内置的功能。

### 鼠标

```python
# humanize 点击：贝塞尔曲线路径、Fitts 定律计时、
# 最小加加速度速度曲线、颤动、过冲 + 修正
await element.click(humanize=True)
```

当 `humanize=True` 传递给 WebElement 的 `click()` 时，Pydoll 会生成一条从当前光标位置到元素的完整鼠标移动路径，使用带有随机控制点的三次贝塞尔曲线。速度遵循最小加加速度曲线。会添加生理性颤动、过冲（70% 概率）和微暂停。移动持续时间根据 Fitts 定律基于距离和目标大小计算。详细参数描述请参见[行为 Fingerprinting](./behavioral-fingerprinting.md#pydolls-mouse-humanization)。

### 键盘

```python
# humanize 打字：可变延迟、逼真的错别字（约 2%）、
# 标点停顿、思考停顿、分心停顿
await element.type_text("Hello, world!", humanize=True)
```

humanize 打字使用可变的按键间延迟（30-120ms 均匀分布）、标点停顿、思考停顿（2% 概率）、分心停顿（0.5% 概率），以及具有五种不同错误类型和自然修正序列的逼真错别字。完整参数说明请参见[行为 Fingerprinting](./behavioral-fingerprinting.md#pydolls-keyboard-humanization)。

### 滚动

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)
# humanize 滚动：贝塞尔缓动、抖动、微暂停、过冲
await scroll.by(ScrollPosition.Y, 800, humanize=True)
```

humanize 滚动使用贝塞尔缓动曲线、逐帧抖动（±3px）、微暂停（5% 概率）和过冲修正（15% 概率）。大距离会被拆分为多个"轻弹"手势。详情请参见[行为 Fingerprinting](./behavioral-fingerprinting.md#pydolls-scroll-humanization)。

## 请求拦截

Pydoll 通过 CDP 的 Fetch 域支持请求拦截，允许你在请求到达服务器之前修改标头、阻止请求或提供自定义响应：

```python
from pydoll.protocol.fetch.events import FetchEvent

async def handle_request(event):
    request_id = event['params']['requestId']
    request = event['params']['request']
    headers = request.get('headers', {})

    # 示例：确保声明了 Brotli 支持
    if 'Accept-Encoding' in headers and 'br' not in headers['Accept-Encoding']:
        headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'

    header_list = [{'name': k, 'value': v} for k, v in headers.items()]
    await tab.continue_request(request_id=request_id, headers=header_list)

await tab.enable_fetch_events()
await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)
```

实际上，使用 Pydoll 很少需要修改标头，因为 Chrome 本身就会生成正确的标头。请求拦截更适用于阻止追踪脚本、修改响应内容或调试。

## 浏览器偏好设置增强真实性

Chrome 存储的用户偏好设置可以被 fingerprinting 系统检查。一个全新的浏览器配置文件——没有历史记录、没有保存的偏好设置、一切都是默认值——看起来与已使用数周的配置文件不同。Pydoll 的 `browser_preferences` 选项允许你预填充这些设置：

```python
import time

options = ChromiumOptions()
options.browser_preferences = {
    'profile': {
        'created_by_version': '120.0.6099.130',
        'creation_time': str(time.time() - 90 * 86400),  # 90 天前
        'exit_type': 'Normal',
    },
    'profile.default_content_setting_values': {
        'cookies': 1,
        'images': 1,
        'javascript': 1,
        'notifications': 2,  # "询问"（真实的默认值）
    },
}
```

## 常见错误

### 随机化一切

从头生成随机指纹（随机 hardwareConcurrency、随机 deviceMemory、随机屏幕尺寸）会产生不可能的组合。真实设备有受约束的配置：4 核、8 GB RAM、1920x1080 屏幕、Windows 10 是一个合理的配置。17 核、0.5 GB RAM、3840x2160 屏幕、`navigator.platform: Linux armv7l` 则不是。请使用从真实浏览器捕获的配置文件，而不是随机生成。

### Canvas 噪声注入

向 Canvas 输出添加随机噪声来防止 fingerprinting 会适得其反。检测系统会多次请求指纹。如果哈希值在请求之间发生变化，噪声注入就会被检测到，这本身就是一个强烈的自动化信号。使用 Pydoll，Canvas 指纹是真实且一致的。不要去动它。

### 过时的 User-Agent

使用 6 个月以上的浏览器版本的 User-Agent 是可被检测的，因为该版本缺少当前发行版应有的功能和 Client Hints 值。User-Agent 字符串应保持在最近 2-3 个 Chrome 主要版本之内。

### 忽略会话级行为

即使有完美的指纹和 humanize 的交互，会话级行为仍然很重要。在 60 秒内加载 100 个页面、从不滚动、只点击按钮（从不点击链接）、以及在没有任何标签页切换或空闲期的情况下保持数小时的持续焦点，这些都是行为异常。在导航之间添加阅读延迟，变化多页面工作流的节奏，并包含自然的空闲期。

## 验证

在大规模部署自动化之前，使用以下工具验证你的指纹：

| 工具 | URL | 测试内容 |
|------|-----|----------|
| BrowserLeaks | https://browserleaks.com/ | Canvas、WebGL、字体、IP、WebRTC、HTTP/2 |
| CreepJS | https://abrahamjuliot.github.io/creepjs/ | 欺骗检测、一致性检查 |
| Fingerprint.com | https://fingerprint.com/demo/ | 商业级识别 |
| PixelScan | https://pixelscan.net/ | 机器人检测分析 |
| IPLeak | https://ipleak.net/ | WebRTC、DNS、IP 泄露 |

使用 Pydoll 的基本验证脚本：

```python
async def verify_fingerprint(tab):
    result = await tab.execute_script('''
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            webdriver: navigator.webdriver,
            languages: navigator.languages,
            plugins: navigator.plugins.length,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            colorDepth: screen.colorDepth,
            deviceMemory: navigator.deviceMemory,
            hardwareConcurrency: navigator.hardwareConcurrency,
        };
    ''')
    fp = result['result']['result']['value']

    # 检查明显问题
    assert fp['webdriver'] is None, 'navigator.webdriver should be undefined'
    assert fp['plugins'] == 5, f'Expected 5 plugins, got {fp["plugins"]}'
    assert 'HeadlessChrome' not in fp['userAgent'], 'Headless detected in UA'
```

## 参考资料

- Chrome DevTools Protocol, Emulation Domain: https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
- Chrome DevTools Protocol, Fetch Domain: https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
- Chromium Source, Inspector Emulation Agent: https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc
