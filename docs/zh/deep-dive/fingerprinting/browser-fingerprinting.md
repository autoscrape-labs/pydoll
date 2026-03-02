# 浏览器 Fingerprinting

浏览器 fingerprinting 通过分析 JavaScript API、HTTP 标头和渲染引擎暴露的属性来识别客户端。与网络 fingerprinting 检查操作系统内核和 TLS 库的协议级信号不同，浏览器 fingerprinting 针对的是应用层：具体的浏览器、版本、配置以及运行它的硬件。这些信号可以通过标准 Web API 被任何网站访问，而足够多属性的组合往往能在数百万访客中创建出唯一的指纹。

!!! info "模块导航"
    - [网络 Fingerprinting](./network-fingerprinting.md): TCP/IP、TLS、HTTP/2 协议 fingerprinting
    - [行为 Fingerprinting](./behavioral-fingerprinting.md): 鼠标、键盘、滚动分析
    - [规避技术](./evasion-techniques.md): 实用对策

## JavaScript Navigator 属性

`navigator` 对象是浏览器 fingerprinting 数据最丰富的单一来源。它暴露了数十个属性，揭示了浏览器、其功能以及运行它的系统。检测系统会收集这些属性，将它们相互交叉比对并与 HTTP 标头进行对照，标记出不一致之处。

以下 JavaScript 收集了 fingerprinting 系统通常检查的核心属性集：

```javascript
const fingerprint = {
    // Identity
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    vendor: navigator.vendor,

    // Language and locale
    language: navigator.language,
    languages: navigator.languages,

    // Hardware
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory,
    maxTouchPoints: navigator.maxTouchPoints,

    // Features
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    webdriver: navigator.webdriver,

    // Screen
    screenWidth: screen.width,
    screenHeight: screen.height,
    colorDepth: screen.colorDepth,
    devicePixelRatio: window.devicePixelRatio,

    // Window chrome (toolbar, scrollbar dimensions)
    chromeHeight: window.outerHeight - window.innerHeight,
    chromeWidth: window.outerWidth - window.innerWidth,

    // Timezone
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffset: new Date().getTimezoneOffset(),
};
```

其中一些属性值得单独关注，因为它们在 fingerprinting 中权重更高，或者更容易被自动化工具错误配置。

### 平台与 User-Agent 一致性

`navigator.platform` 属性返回一个字符串，如 `Win32`、`MacIntel` 或 `Linux x86_64`。检测系统会将其与 User-Agent 标头进行比较。如果 HTTP User-Agent 声称是 `Windows NT 10.0`，但 `navigator.platform` 返回 `Linux x86_64`，这种不匹配就是一个强烈的信号。这是自动化中最常见的错误之一：通过 `--user-agent=` 设置了自定义 User-Agent，却没有同时覆盖 platform。

### 硬件属性

`navigator.hardwareConcurrency` 返回逻辑 CPU 核心数。值为 1 或 2 通常意味着是最小化的虚拟机或容器，而非真实用户的机器。`navigator.deviceMemory` 以 GB 为单位报告大致的 RAM 容量（0.25、0.5、1、2、4、8）。此属性仅在 Chromium 浏览器中可用；Firefox 和 Safari 返回 `undefined`。这两个值应与声称的设备一致：User-Agent 声称是现代桌面设备，却报告 1 个核心和 0.5 GB RAM，这是可疑的。

### WebDriver 属性

当浏览器被基于 WebDriver 的自动化工具（Selenium、以 WebDriver 模式运行的 Playwright）控制时，`navigator.webdriver` 属性为 `true`。这是最明显的自动化指标。Pydoll 直接使用 CDP（Chrome DevTools Protocol），不会设置此标志。在 Pydoll 控制的浏览器中，`navigator.webdriver` 为 `undefined`，与正常用户会话的行为一致。

### 插件

`navigator.plugins` 属性在历史上是一个强力的 fingerprinting 向量，因为不同的浏览器和操作系统配置会暴露不同的插件列表。现代 Chromium 浏览器（Chrome 90+）无论实际插件状态如何，都返回固定的五个 PDF 相关插件：

```javascript
// Modern Chrome always returns these 5 plugins:
// 1. PDF Viewer
// 2. Chrome PDF Viewer
// 3. Chromium PDF Viewer
// 4. Microsoft Edge PDF Viewer
// 5. WebKit built-in PDF
console.log(navigator.plugins.length); // 5
```

一个常见的误解认为现代浏览器会为 `navigator.plugins` 返回空数组。这是不正确的。返回空数组本身就是一个检测信号，表明可能是 headless 模式或非浏览器 HTTP 客户端。

### 屏幕和窗口尺寸

`window.outerWidth`/`outerHeight` 与 `window.innerWidth`/`innerHeight` 之间的差异代表浏览器 chrome（工具栏、滚动条、窗口边框）。Headless 浏览器通常报告零差异，因为它们没有可见的 UI。检测系统会将 `outerWidth` 等于 `innerWidth` 的客户端标记为可能的 headless。同样，`screen.width` 与 `innerWidth` 完全匹配表明这是一个最大化的 headless 窗口，而非正常的桌面会话。

`devicePixelRatio` 因显示器而异：标准显示器报告 `1.0`，MacBook Retina 显示屏报告 `2.0`，智能手机报告 `2.0` 到 `3.0`。此值应与 User-Agent 中声称的设备一致。

## User-Agent Client Hints

现代 Chromium 浏览器（Chrome、Edge、Opera）通过 Client Hints 标头补充传统的 User-Agent 字符串：`Sec-CH-UA`、`Sec-CH-UA-Platform`、`Sec-CH-UA-Mobile`，以及（按需提供的）更高熵值如 `Sec-CH-UA-Full-Version-List`、`Sec-CH-UA-Arch` 和 `Sec-CH-UA-Bitness`。

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
```

Client Hints 提供结构化的、机器可读的数据，更难被不一致地伪造。服务器可以将 `Sec-CH-UA-Platform` 标头与 `navigator.platform`、User-Agent 字符串以及 TCP/IP 指纹进行比较。这些层之间的任何不一致都是检测信号。

JavaScript 端的等价物是 `navigator.userAgentData`，它将 `brands`、`mobile` 和 `platform` 作为低熵值暴露，并通过 `getHighEntropyValues()` 提供详细的版本、架构和位宽信息：

```javascript
// Low-entropy (always available, no permission needed)
console.log(navigator.userAgentData.brands);
// [{brand: "Chromium", version: "120"}, {brand: "Google Chrome", version: "120"}, ...]
console.log(navigator.userAgentData.platform); // "Windows"
console.log(navigator.userAgentData.mobile);   // false

// High-entropy (requires promise, may require permission)
const highEntropy = await navigator.userAgentData.getHighEntropyValues([
    'architecture', 'bitness', 'platformVersion', 'uaFullVersion'
]);
// {architecture: "x86", bitness: "64", platformVersion: "15.0.0", ...}
```

!!! warning "浏览器支持"
    Client Hints 是 Chromium 独有的功能。Firefox 和 Safari 不会发送 `Sec-CH-UA` 标头，也不会暴露 `navigator.userAgentData`。如果 User-Agent 声称是 Firefox，但服务器收到了 Client Hints 标头，那么该客户端不是 Firefox。

## Canvas Fingerprinting

Canvas fingerprinting 利用了 HTML5 Canvas API 在不同 GPU、图形驱动、操作系统和浏览器组合下产生微妙不同像素输出的特性。这种差异来自字体光栅化（亚像素渲染、字体微调、抗锯齿）、GPU 特定的着色器执行、图形管线中的浮点精度，以及操作系统级别的文本渲染库（Windows 上的 DirectWrite、macOS 上的 Core Text、Linux 上的 FreeType）。

该技术在隐藏的 canvas 上绘制文本、形状和渐变，提取像素数据，然后进行哈希处理：

```javascript
function generateCanvasFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');

    // Colored rectangle (exposes blending differences)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);

    // Text with emoji (maximizes rendering variation)
    ctx.font = '14px Arial';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);

    // Semi-transparent overlay (exposes alpha compositing differences)
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);

    return canvas.toDataURL();
}
```

全字母句 "Cwm fjordbank glyphs vext quiz" 之所以被选用，是因为它使用了不常见的字符组合，能够充分测试字体渲染。表情符号增加了另一个维度，因为表情符号渲染在不同操作系统之间差异显著。半透明叠加测试了 alpha 合成，这在不同 GPU 实现之间也有所不同。

Canvas fingerprinting 能有效区分大类设备，但其唯一性有时被夸大了。Laperdrix 等人（2016）的研究发现，仅靠 canvas 指纹只能提供中等程度的区分能力，其真正价值在于与其他信号（WebGL、navigator 属性、时区）结合使用以实现高唯一性。

!!! note "Canvas 噪声注入"
    一些隐私工具会向 canvas 输出注入随机噪声以干扰 fingerprinting。检测系统通过在同一会话中多次请求 canvas 指纹来应对。如果哈希值在请求之间发生变化，则说明存在噪声注入，而这本身就是一个检测信号。因此，随机化 canvas 输出适得其反：它既不能防止识别，又暴露了反 fingerprinting 工具的使用。

由于 Pydoll 控制的是一个具有真实 GPU 渲染的 Chrome 实例，canvas 指纹是真实的，并且在多次读取之间保持一致。无需注入或伪造。

## WebGL Fingerprinting

WebGL fingerprinting 将 canvas fingerprinting 扩展到 3D 渲染管线。它更为强大，因为它直接暴露了难以伪造的硬件标识符。

最具辨识度的数据来自 `WEBGL_debug_renderer_info` 扩展，它揭示了 GPU 供应商和型号：

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    if (!gl) return null;

    // GPU identification (most distinctive)
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo
        ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        : gl.getParameter(gl.RENDERER);

    return {
        vendor,    // e.g. "Google Inc. (NVIDIA)"
        renderer,  // e.g. "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
        version: gl.getParameter(gl.VERSION),
        shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
        extensions: gl.getSupportedExtensions(),
    };
}
```

renderer 字符串直接标明了 GPU 硬件。声称是移动设备的客户端却报告了桌面 GPU，这显然是不一致的。虚拟机通常报告软件渲染器如 "SwiftShader" 或 "llvmpipe"，这在真实用户中几乎不会出现。

除了元数据之外，WebGL 还可以渲染一个 3D 场景（例如一个渐变三角形）并对像素输出进行哈希，产生类似于 canvas fingerprinting 的渲染指纹，但针对的是 3D 管线。GPU 标识符、支持的扩展、参数限制（`MAX_TEXTURE_SIZE`、`MAX_VIEWPORT_DIMS`）和着色器精度格式的组合，创建了图形栈的详细指纹。

## AudioContext Fingerprinting

Web Audio API 通过处理音频并测量输出来生成指纹。标准技术是创建一个 `OscillatorNode`，将其路由通过一个 `DynamicsCompressorNode`，然后从 `AnalyserNode` 或 `OfflineAudioContext` 读取生成的音频采样。不同浏览器和操作系统音频栈在音频处理实现上的差异会产生不同的输出。

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
        // Hash a subset of the audio samples
        let hash = 0;
        for (let i = 4500; i < 5000; i++) {
            hash += Math.abs(data[i]);
        }
        return hash;
    });
}
```

AudioContext fingerprinting 的部署范围不如 canvas 或 WebGL fingerprinting 广泛，但它为整体指纹增加了另一个维度。该信号对于区分同一操作系统上的不同浏览器特别有用，因为音频处理在不同浏览器引擎之间的差异比在不同操作系统版本之间更大。

## Battery Status API

Battery Status API（`navigator.getBattery()`）暴露了设备的电池电量、充电状态以及预估的充电/放电时间。这些值在会话持续期间创建了一个短暂但唯一的指纹。

此 API 仅在 Chromium 浏览器中可用。Firefox 在版本 52（2017 年）中出于隐私考虑将其移除，Safari 从未实现过。如果检测系统从声称是 Firefox 或 Safari 的客户端看到 Battery API 结果，就知道该客户端伪造了身份。

## HTTP 标头 Fingerprinting

除了 JavaScript API 之外，HTTP 标头提供了服务器在任何 JavaScript 执行之前就可见的 fingerprinting 信号。

### 标头顺序

浏览器以一致的、特定于版本的顺序发送 HTTP 标头。Chrome 将 `Sec-CH-UA` 标头放在较前的位置，位于 `User-Agent` 之前。Firefox 以 `User-Agent` 开头，随后是 `Accept` 和 `Accept-Language`。自动化 HTTP 库如 Python 的 `requests` 或 `httpx` 以另一种顺序发送标头，通常以 `Host` 和 `Connection` 开头。

检测系统记录前 10-15 个标头的顺序，并与已知的浏览器签名进行比较。即使所有单独的标头值都正确，以错误的顺序发送也会暴露该请求不是由所声称的浏览器生成的。由于 Pydoll 控制的是真实的 Chrome 实例，标头顺序是真实的。

### Accept-Encoding

现代浏览器除了 `gzip` 和 `deflate` 之外还支持 Brotli 压缩（`br`）。Chrome 还支持 `zstd`。现代 Chrome 的 `Accept-Encoding` 类似于 `gzip, deflate, br, zstd`。声称是 Chrome 但缺少 Brotli 的客户端要么是过时的，要么是自动化的。

### Accept-Language 一致性

`Accept-Language` 标头应与 `navigator.language`、`navigator.languages`、时区以及 IP 地理位置保持一致。来自东京 IP、时区为 `Asia/Tokyo` 的请求带有 `Accept-Language: en-US`，对于旅行者来说是合理的，但与其他信号结合时就显得可疑。来自中国数据中心 IP、带有 `Accept-Language: zh-CN` 和时区 `America/New_York` 的请求则是强烈的代理指标。

## 对 Pydoll 的影响

由于 Pydoll 通过 CDP 驱动真实的 Chromium 浏览器，所有浏览器级别的指纹默认都是真实的。Canvas、WebGL 和 AudioContext 指纹来自实际的 GPU 和音频硬件。Navigator 属性、插件和屏幕尺寸反映了真实的浏览器状态。HTTP 标头（包括其顺序）由 Chrome 的网络栈生成。

自动化中的主要风险是各层之间的不一致。设置自定义 User-Agent 而不同步相关属性会创建容易被检测到的不匹配。Pydoll 会自动处理这个问题：当它检测到浏览器参数中的 `--user-agent=` 时，会使用 `Emulation.setUserAgentOverride` 在所有层同步 User-Agent 字符串、平台和完整的 Client Hints 元数据。它还通过 `Page.addScriptToEvaluateOnNewDocument` 注入 `navigator.vendor` 和 `navigator.appVersion` 覆盖，以确保新打开的标签页中的一致性。

对于时区和地理位置一致性（以匹配代理 IP 的位置），JavaScript 覆盖可以设置 `Intl.DateTimeFormat().resolvedOptions().timeZone` 和 `Date.prototype.getTimezoneOffset`。`--lang` 标志和 `set_accept_languages()` 配置语言标头。`webrtc_leak_protection` 选项可防止 WebRTC 暴露代理背后的真实 IP。

总体原则是，Pydoll 提供真实的浏览器指纹作为基线，开发者只需确保可配置的层（User-Agent、时区、语言、地理位置）彼此一致，并与代理的特征相匹配。

## 参考文献

- Laperdrix, P., Rudametkin, W., & Baudry, B. (2016). Beauty and the Beast: Diverting Modern Web Browsers to Build Unique Browser Fingerprints. IEEE S&P.
- Mowery, K., & Shacham, H. (2012). Pixel Perfect: Fingerprinting Canvas in HTML5. USENIX Security.
- Eckersley, P. (2010). How Unique Is Your Web Browser? Privacy Enhancing Technologies Symposium.
- W3C Client Hints Infrastructure: https://wicg.github.io/client-hints-infrastructure/
- BrowserLeaks: https://browserleaks.com/
- CreepJS: https://abrahamjuliot.github.io/creepjs/
