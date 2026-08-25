# Browser fingerprinting

Browser fingerprinting 通过客户端经由 JavaScript API、HTTP 头和渲染引擎所暴露的属性来识别它们。[network fingerprinting](network-fingerprinting.md) 检查的是来自操作系统内核和 TLS 库的协议级信号，而 browser fingerprinting 瞄准的是应用层：具体的浏览器、它的版本、它的配置，以及它运行其上的硬件。任何网站都能通过标准的 web API 读取这些信号，而足够多的信号组合起来所创建的 fingerprint，在数百万访客中往往是唯一的。

<iframe scrolling="no" src="/docs/resources/visuals/fingerprint-uniqueness.html" aria-label="Dozens of individually common browser signals combine into one near-unique fingerprint, and a single contradiction between two of them (User-Agent vs platform, timezone vs language) flags you" style="width: 100%; height: 920px; border: 0;" loading="lazy"></iframe>

## JavaScript navigator 属性

`navigator` 对象是浏览器 fingerprinting 数据最丰富的单一来源。它暴露了数十个属性，揭示浏览器、它的能力以及它运行其上的系统。检测系统收集这些属性，把它们相互交叉引用、并与 HTTP 头交叉引用，然后标记不一致之处。

下面这段 JavaScript 收集了 fingerprinting 系统通常会检查的核心属性集：

```javascript
const fingerprint = {
    // 身份
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    vendor: navigator.vendor,

    // 语言和区域设置
    language: navigator.language,
    languages: navigator.languages,

    // 硬件
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory,
    maxTouchPoints: navigator.maxTouchPoints,

    // 特性
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    webdriver: navigator.webdriver,

    // 屏幕
    screenWidth: screen.width,
    screenHeight: screen.height,
    colorDepth: screen.colorDepth,
    devicePixelRatio: window.devicePixelRatio,

    // 窗口边框（工具栏、滚动条尺寸）
    chromeHeight: window.outerHeight - window.innerHeight,
    chromeWidth: window.outerWidth - window.innerWidth,

    // 时区
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
};
```

其中有几个属性值得单独关注，因为它们承载了更多的 fingerprinting 权重，或者更常被自动化工具错误配置。

### Platform 与 User-Agent 的一致性

`navigator.platform` 属性返回一个类似 `Win32`、`MacIntel` 或 `Linux x86_64` 的字符串。检测系统会把它与 User-Agent 头比较。如果 HTTP User-Agent 声称是 `Windows NT 10.0`，但 `navigator.platform` 返回 `Linux x86_64`，这个不匹配就是一个强信号。这是自动化中最常见的错误之一：通过 `--user-agent=` 设置自定义 User-Agent，却没有同时覆盖 platform。

### 硬件属性

`navigator.hardwareConcurrency` 返回逻辑 CPU 核心数。值为 1 或 2 暗示是一台极简的虚拟机或容器，而不是真实用户的机器。`navigator.deviceMemory` 报告以 GB 为单位的近似 RAM（0.25、0.5、1、2、4、8）。这个属性只在 Chromium 浏览器中可用；Firefox 和 Safari 返回 `undefined`。这两个值都应与所声称的设备一致：一个声称是现代桌面机的 User-Agent，却报告 1 个核心和 0.5 GB 的 RAM，是可疑的。

### WebDriver 属性

当浏览器由基于 WebDriver 的自动化控制时（Selenium、处于 WebDriver 模式的 Playwright），`navigator.webdriver` 属性为 `true`。这是最明显的单一自动化指标。现代 Chrome 把该属性定义为一个 getter，在正常会话中返回 `false`，只有在自动化标志下才翻转为 `true`。Pydoll 在不带那些标志的情况下通过 CDP 驱动 Chrome，因此 `navigator.webdriver` 报告 `false`，与正常用户会话相同。它不是 `undefined`；`undefined` 的值本身就会是不寻常的，也不是 Pydoll 所产生的。

### 插件

`navigator.plugins` 属性在历史上是一个强 fingerprinting 向量，因为不同的浏览器和操作系统配置会暴露不同的插件列表。现代 Chromium 浏览器（Chrome 90+）无论实际插件状态如何，都返回一个固定的、由五个与 PDF 相关的插件组成的列表：

```javascript
// 现代 Chrome 始终返回这 5 个插件：
// 1. PDF Viewer
// 2. Chrome PDF Viewer
// 3. Chromium PDF Viewer
// 4. Microsoft Edge PDF Viewer
// 5. WebKit built-in PDF
console.log(navigator.plugins.length); // 5
```

一种常见的误解声称现代浏览器为 `navigator.plugins` 返回空数组。这是不正确的。返回空数组本身就是一个检测信号，暗示 headless 模式或非浏览器的 HTTP 客户端。

### 屏幕和窗口尺寸

`window.outerWidth`/`outerHeight` 与 `window.innerWidth`/`innerHeight` 之间的差距代表浏览器边框（工具栏、滚动条、窗口框架）。headless 浏览器常常报告零差异，因为它们没有可见的 UI。检测系统会把 `outerWidth` 等于 `innerWidth` 的客户端标记为可能是 headless。同样地，`screen.width` 与 `innerWidth` 完全相等暗示的是一个最大化的 headless 窗口，而不是正常的桌面会话。

`devicePixelRatio` 因显示器而异：标准显示器报告 `1.0`，MacBook Retina 显示器报告 `2.0`，智能手机报告 `2.0` 到 `3.0`。这个值应与 User-Agent 中所声称的设备一致。

## User-Agent client hints

现代 Chromium 浏览器（Chrome、Edge、Opera）用 Client Hints 头来补充传统的 User-Agent 字符串：`Sec-CH-UA`、`Sec-CH-UA-Platform`、`Sec-CH-UA-Mobile`，以及（在请求时）更高熵的值，如 `Sec-CH-UA-Full-Version-List`、`Sec-CH-UA-Arch` 和 `Sec-CH-UA-Bitness`。

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
```

Client Hints 提供结构化的、机器可读的数据，更难被不一致地伪造。服务器可以把 `Sec-CH-UA-Platform` 头与 `navigator.platform`、User-Agent 字符串以及 TCP/IP fingerprint 进行比较。这些层次之间的任何不一致都是一个检测信号。

在 JavaScript 一侧的等价物是 `navigator.userAgentData`，它把 `brands`、`mobile` 和 `platform` 作为低熵值暴露，并提供 `getHighEntropyValues()` 以获取详细的版本、架构和位数信息：

```javascript
// 低熵（始终可用，无需权限）
console.log(navigator.userAgentData.brands);
// [{brand: "Chromium", version: "120"}, {brand: "Google Chrome", version: "120"}, ...]
console.log(navigator.userAgentData.platform); // "Windows"
console.log(navigator.userAgentData.mobile);   // false

// 高熵（需要 promise，可能需要权限）
const highEntropy = await navigator.userAgentData.getHighEntropyValues([
    'architecture', 'bitness', 'platformVersion', 'uaFullVersion'
]);
// {architecture: "x86", bitness: "64", platformVersion: "15.0.0", ...}
```

!!! warning "浏览器支持情况"
    Client Hints 是 Chromium 独有的特性。Firefox 和 Safari 不发送 `Sec-CH-UA` 头，也不暴露 `navigator.userAgentData`。如果 User-Agent 声称是 Firefox，但服务器却收到了 Client Hints 头，那么这个客户端不是 Firefox。

## Canvas fingerprinting

Canvas fingerprinting 利用了这样一个事实：HTML5 Canvas API 在 GPU、图形驱动、操作系统和浏览器的不同组合下会产生微妙不同的像素输出。这种差异来自字体栅格化的差异（子像素渲染、hinting、抗锯齿）、GPU 特有的着色器执行、图形管线中浮点精度的差异，以及操作系统级别的文本渲染库（Windows 上的 DirectWrite、macOS 上的 Core Text、Linux 上的 FreeType）。

该技术在一个隐藏的 canvas 上绘制文本、形状和渐变，提取像素数据，并对其做哈希：

```javascript
function generateCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');

    // 彩色矩形（暴露混合差异）
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);

    // 带 emoji 的文本（使渲染差异最大化）
    ctx.font = '14px Arial';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);

    // 半透明叠加层（暴露 alpha 合成差异）
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);

    return canvas.toDataURL();
}
```

之所以选择全字母句 "Cwm fjordbank glyphs vext quiz"，是因为它使用了不寻常的字符组合，会给字体渲染带来压力。emoji 增加了另一个维度，因为 emoji 渲染在各操作系统之间有所不同。半透明叠加层测试的是 alpha 合成，它在各 GPU 实现之间有所不同。

Canvas fingerprinting 在区分设备的大类别时是有效的，但它的唯一性有时被夸大了。Laperdrix 等人（2016）的研究发现，单靠 canvas fingerprint 只提供中等的区分能力，它们的真正价值来自与其他信号（WebGL、navigator 属性、时区）组合以达到高唯一性。

!!! note "Canvas 噪声注入"
    一些隐私工具会向 canvas 输出注入随机噪声来破坏 fingerprinting。检测系统通过在同一会话中多次请求 canvas fingerprint 来反制这一点。如果哈希在多次请求之间发生变化，就说明存在噪声注入，而这本身就是一个检测信号。因此，随机化 canvas 输出适得其反：它既不能阻止识别，又暴露了反 fingerprinting 工具的使用。

由于 Pydoll 控制的是一个带有真实 GPU 渲染的真实 Chrome 实例，canvas fingerprint 是真实的，并且在反复读取之间保持一致。无需任何注入或伪造。

## WebGL fingerprinting

WebGL fingerprinting 把 canvas fingerprinting 延伸到了 3D 渲染管线。它更具揭示性，因为它直接暴露了难以伪造的硬件标识符。

最有区分度的数据来自 `WEBGL_debug_renderer_info` 扩展，它揭示了 GPU 的厂商和型号：

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    if (!gl) return null;

    // GPU 识别（最具区分度）
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        : gl.getParameter(gl.RENDERER);

    return {
        vendor,    // 例如 "Google Inc. (NVIDIA)"
        renderer,  // 例如 "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
        version: gl.getParameter(gl.VERSION),
        shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
        extensions: gl.getSupportedExtensions(),
    };
}
```

renderer 字符串直接给出了 GPU 硬件的名称。一个声称是移动设备、却报告桌面 GPU 的客户端是不一致的。虚拟机常常报告像 "SwiftShader" 或 "llvmpipe" 这样的软件渲染器，而真实用户几乎从不会有这些。

除元数据之外，WebGL 还可以渲染一个 3D 场景（例如一个渐变三角形）并对像素输出做哈希，产生一个类似于 canvas fingerprinting、但处于 3D 管线中的渲染 fingerprint。GPU 标识符、支持的扩展、参数上限（`MAX_TEXTURE_SIZE`、`MAX_VIEWPORT_DIMS`）以及着色器精度格式的组合，创建了一个关于图形栈的详细 fingerprint。

## AudioContext fingerprinting

Web Audio API 通过处理音频并测量输出来生成 fingerprint。标准技术创建一个 `OscillatorNode`，把它经过一个 `DynamicsCompressorNode`，然后从 `AnalyserNode` 或 `OfflineAudioContext` 读取所得的音频采样。各浏览器和操作系统音频栈之间音频处理实现的差异，产生了不同的输出。

```javascript
function getAudioFingerprint() {
    const ctx = new OfflineAudioContext(1, 44100, 44100);
    const oscillator = ctx.createOscillator();
    oscillator.type = 'triangle';
    oscillator.frequency.setValueAtTime(10000, ctx.currentTime);

    const compressor = ctx.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-50, ctx.currentTime);
    compressor.knee.setValueAtTime(40, ctx.currentTime);
    compressor.ratio.setValueAtTime(12, ctx.currentTime);
    compressor.attack.setValueAtTime(0, ctx.currentTime);
    compressor.release.setValueAtTime(0.25, ctx.currentTime);

    oscillator.connect(compressor);
    compressor.connect(ctx.destination);
    oscillator.start(0);

    return ctx.startRendering().then(buffer => {
        const data = buffer.getChannelData(0);
        // 对音频采样的一个子集做哈希
        let hash = 0;
        for (let i = 4500; i < 5000; i++) {
            hash += Math.abs(data[i]);
        }
        return hash;
    });
}
```

AudioContext fingerprinting 的部署没有 canvas 或 WebGL fingerprinting 那么广泛，但它为整体 fingerprint 增加了另一个维度。这个信号在区分同一操作系统上的浏览器时特别有用，因为音频处理在各浏览器引擎之间的差异比在各操作系统版本之间更大。

## Battery Status API

Battery Status API（`navigator.getBattery()`）暴露了设备的电池电量、充电状态以及估计的充电/放电时间。这些值在会话持续期间创建一个短暂但唯一的 fingerprint。

这个 API 只在 Chromium 浏览器中可用。Firefox 出于隐私考虑在第 52 版（2017）移除了它，而 Safari 从未实现它。当检测系统看到一个声称是 Firefox 或 Safari 的客户端返回 Battery API 的结果时，就知道这个客户端在歪曲自己的身份。

## HTTP 头 fingerprinting

除了 JavaScript API 之外，HTTP 头还提供了在任何 JavaScript 执行之前就对服务器可见的 fingerprinting 信号。

### 头顺序

浏览器以一致的、版本特定的顺序发送 HTTP 头。Chrome 把 `Sec-CH-UA` 头放在前面，位于 `User-Agent` 之前。Firefox 以 `User-Agent` 开头，随后是 `Accept` 和 `Accept-Language`。像 Python 的 `requests` 或 `httpx` 这样的自动化 HTTP 库以又一种不同的顺序发送头，通常以 `Host` 和 `Connection` 开头。

检测系统记录前 10 到 15 个头的顺序，并与已知的浏览器签名比较。即使所有单个头的值都正确，以错误的顺序发送它们也会暴露该请求不是由所声称的浏览器生成的。由于 Pydoll 控制的是一个真实的 Chrome 实例，头顺序是真实的。

### Accept-Encoding

现代浏览器除了 `gzip` 和 `deflate` 之外还支持 Brotli 压缩（`br`）。Chrome 还支持 `zstd`。现代 Chrome 的 `Accept-Encoding` 看起来像 `gzip, deflate, br, zstd`。一个声称是 Chrome、却缺少 Brotli 的客户端，要么是过时的，要么是自动化的。

### Accept-Language 一致性

`Accept-Language` 头应与 `navigator.language`、`navigator.languages`、时区以及 IP 地理位置一致。一个来自东京 IP、时区为 `Asia/Tokyo`、却带有 `Accept-Language: en-US` 的请求，对旅行者来说是合理的，但与其他信号组合时是可疑的。一个来自中国数据中心 IP、带有 `Accept-Language: zh-CN` 和时区 `America/New_York` 的请求，是一个强 proxy 指标。

## 对 Pydoll 的影响

因为 Pydoll 通过 CDP 驱动的是一个真实的 Chromium 浏览器，所有浏览器级别的 fingerprint 默认都是真实的。canvas、WebGL 和 AudioContext fingerprint 来自实际的 GPU 和音频硬件。navigator 属性、插件和屏幕尺寸反映的是真实的浏览器状态。HTTP 头（包括它们的顺序）由 Chrome 的网络栈生成。

自动化中的主要风险是各层次之间的不一致。设置自定义 User-Agent 而不同步相关属性，会造成极易检测的不匹配。Pydoll 会自动处理这一点：当它检测到浏览器参数中的 `--user-agent=` 时，会使用 `Emulation.setUserAgentOverride` 在所有层次之间同步 User-Agent 字符串、platform 以及完整的 Client Hints 元数据。它还通过 `Page.addScriptToEvaluateOnNewDocument` 注入 `navigator.vendor` 和 `navigator.appVersion` 的覆盖，以确保在新打开的标签页中保持一致。

语言头来自 `--lang` 标志和 `set_accept_languages()`，而 `webrtc_leak_protection` 阻止 WebRTC 暴露 proxy 背后的真实 IP。时区和地理位置需要与 proxy IP 的位置匹配，并与其他一切保持一致；[`tab.apply_fingerprint()`](../../stealth/fingerprint-injection.md) 会把它们与来自同一个一致 profile 的区域设置、User-Agent 和 Client Hints 一起应用。

原则是，Pydoll 给你真实的浏览器 fingerprint 作为基线，你只需要让可配置的层次（User-Agent、时区、语言、地理位置）彼此之间以及与 proxy 保持一致。

## 相关内容

- [Network fingerprinting](network-fingerprinting.md)：这些 API 之下的协议层。
- [Behavioral fingerprinting](behavioral-fingerprinting.md)：鼠标、键盘和时序是如何被分析的。
- [Evasion techniques](../../stealth/evasion-techniques.md)：你能控制的实用杠杆。
- [Fingerprint injection](../../stealth/fingerprint-injection.md)：在每一层应用一致的身份。

## 参考文献

- Laperdrix, P., Rudametkin, W., & Baudry, B. (2016). Beauty and the Beast: Diverting Modern Web Browsers to Build Unique Browser Fingerprints. IEEE S&P.
- Mowery, K., & Shacham, H. (2012). Pixel Perfect: Fingerprinting Canvas in HTML5. USENIX Security.
- Eckersley, P. (2010). How Unique Is Your Web Browser? Privacy Enhancing Technologies Symposium.
- W3C Client Hints Infrastructure: https://wicg.github.io/client-hints-infrastructure/
- BrowserLeaks: https://browserleaks.com/
- CreepJS: https://abrahamjuliot.github.io/creepjs/
