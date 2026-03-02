# Browser Fingerprinting

Browser fingerprinting identifies clients by analyzing properties exposed through JavaScript APIs, HTTP headers, and rendering engines. Unlike network fingerprinting, which examines protocol-level signals from the OS kernel and TLS library, browser fingerprinting targets the application layer: the specific browser, its version, its configuration, and the hardware it runs on. These signals are accessible to any website through standard web APIs, and the combination of enough properties creates a fingerprint that is often unique across millions of visitors.

!!! info "Module Navigation"
    - [Network Fingerprinting](./network-fingerprinting.md): TCP/IP, TLS, HTTP/2 protocol fingerprinting
    - [Behavioral Fingerprinting](./behavioral-fingerprinting.md): Mouse, keyboard, scroll analysis
    - [Evasion Techniques](./evasion-techniques.md): Practical countermeasures

## JavaScript Navigator Properties

The `navigator` object is the richest single source of browser fingerprinting data. It exposes dozens of properties that reveal the browser, its capabilities, and the system it runs on. Detection systems collect these properties, cross-reference them against each other and against HTTP headers, and flag inconsistencies.

The following JavaScript collects the core set of properties that fingerprinting systems typically examine:

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

Several of these properties deserve individual attention because they carry more fingerprinting weight or are more commonly misconfigured by automation tools.

### Platform and User-Agent Consistency

The `navigator.platform` property returns a string like `Win32`, `MacIntel`, or `Linux x86_64`. Detection systems compare this against the User-Agent header. If the HTTP User-Agent claims `Windows NT 10.0` but `navigator.platform` returns `Linux x86_64`, the mismatch is a strong signal. This is one of the most common mistakes in automation: setting a custom User-Agent via `--user-agent=` without also overriding the platform.

### Hardware Properties

`navigator.hardwareConcurrency` returns the number of logical CPU cores. A value of 1 or 2 suggests a minimal VM or container rather than a real user's machine. `navigator.deviceMemory` reports approximate RAM in gigabytes (0.25, 0.5, 1, 2, 4, 8). This property is only available in Chromium browsers; Firefox and Safari return `undefined`. Both values should be consistent with the claimed device: a User-Agent claiming a modern desktop but reporting 1 core and 0.5 GB of RAM is suspicious.

### WebDriver Property

The `navigator.webdriver` property is `true` when the browser is controlled by WebDriver-based automation (Selenium, Playwright in WebDriver mode). This is the single most obvious automation indicator. Pydoll uses CDP (Chrome DevTools Protocol) directly, which does not set this flag. In a Pydoll-controlled browser, `navigator.webdriver` is `undefined`, matching the behavior of a normal user session.

### Plugins

The `navigator.plugins` property was historically a strong fingerprinting vector because different browsers and OS configurations exposed different plugin lists. Modern Chromium browsers (Chrome 90+) return a fixed list of five PDF-related plugins regardless of actual plugin state:

```javascript
// Modern Chrome always returns these 5 plugins:
// 1. PDF Viewer
// 2. Chrome PDF Viewer
// 3. Chromium PDF Viewer
// 4. Microsoft Edge PDF Viewer
// 5. WebKit built-in PDF
console.log(navigator.plugins.length); // 5
```

A common misconception claims that modern browsers return empty arrays for `navigator.plugins`. This is incorrect. Returning an empty array is itself a detection signal that suggests headless mode or a non-browser HTTP client.

### Screen and Window Dimensions

The gap between `window.outerWidth`/`outerHeight` and `window.innerWidth`/`innerHeight` represents the browser chrome (toolbars, scrollbars, window frame). Headless browsers often report zero difference because they have no visible UI. Detection systems flag clients where `outerWidth` equals `innerWidth` as potentially headless. Similarly, `screen.width` matching `innerWidth` exactly suggests a maximized headless window rather than a normal desktop session.

The `devicePixelRatio` varies by display: standard monitors report `1.0`, MacBook Retina displays report `2.0`, and smartphones report `2.0` to `3.0`. This value should be consistent with the claimed device in the User-Agent.

## User-Agent Client Hints

Modern Chromium browsers (Chrome, Edge, Opera) supplement the traditional User-Agent string with Client Hints headers: `Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Mobile`, and (on request) higher-entropy values like `Sec-CH-UA-Full-Version-List`, `Sec-CH-UA-Arch`, and `Sec-CH-UA-Bitness`.

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
```

Client Hints provide structured, machine-readable data that is harder to spoof inconsistently. A server can compare the `Sec-CH-UA-Platform` header against `navigator.platform`, the User-Agent string, and the TCP/IP fingerprint. Any inconsistency across these layers is a detection signal.

The JavaScript-side equivalent is `navigator.userAgentData`, which exposes `brands`, `mobile`, and `platform` as low-entropy values, and `getHighEntropyValues()` for detailed version, architecture, and bitness information:

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

!!! warning "Browser Support"
    Client Hints are a Chromium-only feature. Firefox and Safari do not send `Sec-CH-UA` headers and do not expose `navigator.userAgentData`. If the User-Agent claims Firefox but the server receives Client Hints headers, the client is not Firefox.

## Canvas Fingerprinting

Canvas fingerprinting exploits the fact that the HTML5 Canvas API produces subtly different pixel output across different combinations of GPU, graphics driver, OS, and browser. The variation comes from differences in font rasterization (sub-pixel rendering, hinting, anti-aliasing), GPU-specific shader execution, floating-point precision in the graphics pipeline, and OS-level text rendering libraries (DirectWrite on Windows, Core Text on macOS, FreeType on Linux).

The technique draws text, shapes, and gradients onto a hidden canvas, extracts the pixel data, and hashes it:

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

The pangram "Cwm fjordbank glyphs vext quiz" is chosen because it uses unusual character combinations that stress font rendering. The emoji adds another dimension because emoji rendering varies significantly across operating systems. The semi-transparent overlay tests alpha compositing, which differs across GPU implementations.

Canvas fingerprinting is effective for distinguishing broad categories of devices, but its uniqueness is sometimes overstated. Research by Laperdrix et al. (2016) found that canvas fingerprints alone provide moderate distinguishing power, and their real value comes from combining with other signals (WebGL, navigator properties, timezone) to achieve high uniqueness.

!!! note "Canvas Noise Injection"
    Some privacy tools inject random noise into canvas output to break fingerprinting. Detection systems counter this by requesting the canvas fingerprint multiple times in the same session. If the hash changes between requests, noise injection is present, which is itself a detection signal. Randomizing canvas output is therefore counterproductive: it does not prevent identification and it reveals the use of anti-fingerprinting tools.

Since Pydoll controls a real Chrome instance with actual GPU rendering, the canvas fingerprint is authentic and consistent across repeated reads. No injection or spoofing is needed.

## WebGL Fingerprinting

WebGL fingerprinting extends canvas fingerprinting into the 3D rendering pipeline. It is more powerful because it directly exposes hardware identifiers that are difficult to spoof.

The most distinctive data comes from the `WEBGL_debug_renderer_info` extension, which reveals the GPU vendor and model:

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

The renderer string directly names the GPU hardware. A client claiming to be a mobile device but reporting a desktop GPU is obviously inconsistent. Virtual machines often report software renderers like "SwiftShader" or "llvmpipe", which real users almost never have.

Beyond metadata, WebGL can render a 3D scene (a gradient triangle, for instance) and hash the pixel output, producing a render fingerprint analogous to canvas fingerprinting but in the 3D pipeline. The combination of GPU identifiers, supported extensions, parameter limits (`MAX_TEXTURE_SIZE`, `MAX_VIEWPORT_DIMS`), and shader precision formats creates a detailed fingerprint of the graphics stack.

## AudioContext Fingerprinting

The Web Audio API generates fingerprints by processing audio and measuring the output. The standard technique creates an `OscillatorNode`, routes it through a `DynamicsCompressorNode`, and reads the resulting audio samples from an `AnalyserNode` or `OfflineAudioContext`. Differences in audio processing implementations across browsers and OS audio stacks produce distinct output.

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

AudioContext fingerprinting is less widely deployed than canvas or WebGL fingerprinting, but it adds another dimension to the overall fingerprint. The signal is particularly useful for distinguishing browsers on the same OS, since audio processing varies more across browser engines than across OS versions.

## Battery Status API

The Battery Status API (`navigator.getBattery()`) exposes the device's battery level, charging status, and estimated charge/discharge times. These values create a short-lived but unique fingerprint for the duration of a session.

This API is only available in Chromium browsers. Firefox removed it in version 52 (2017) citing privacy concerns, and Safari has never implemented it. Detection systems that see Battery API results from a client claiming to be Firefox or Safari know the client is misrepresenting its identity.

## HTTP Header Fingerprinting

Beyond JavaScript APIs, HTTP headers provide fingerprinting signals visible to the server before any JavaScript executes.

### Header Order

Browsers send HTTP headers in a consistent, version-specific order. Chrome places `Sec-CH-UA` headers early, before `User-Agent`. Firefox leads with `User-Agent` followed by `Accept` and `Accept-Language`. Automated HTTP libraries like Python's `requests` or `httpx` send headers in yet another order, typically starting with `Host` and `Connection`.

Detection systems record the order of the first 10-15 headers and compare against known browser signatures. Even if all individual header values are correct, sending them in the wrong order reveals that the request was not generated by the claimed browser. Since Pydoll controls a real Chrome instance, the header order is authentic.

### Accept-Encoding

Modern browsers support Brotli compression (`br`) in addition to `gzip` and `deflate`. Chrome also supports `zstd`. The `Accept-Encoding` for modern Chrome looks like `gzip, deflate, br, zstd`. A client claiming to be Chrome but missing Brotli is either outdated or automated.

### Accept-Language Consistency

The `Accept-Language` header should be consistent with `navigator.language`, `navigator.languages`, the timezone, and the IP geolocation. A request with `Accept-Language: en-US` from an IP in Tokyo with timezone `Asia/Tokyo` is plausible for a traveler but suspicious in combination with other signals. A request with `Accept-Language: zh-CN` and timezone `America/New_York` from a Chinese datacenter IP is a strong proxy indicator.

## Implications for Pydoll

Because Pydoll drives a real Chromium browser through CDP, all browser-level fingerprints are authentic by default. The canvas, WebGL, and AudioContext fingerprints come from actual GPU and audio hardware. The navigator properties, plugins, and screen dimensions reflect the real browser state. HTTP headers, including their order, are generated by Chrome's networking stack.

The main risk in automation is inconsistency across layers. Setting a custom User-Agent without synchronizing related properties creates trivially detectable mismatches. Pydoll handles this automatically: when it detects `--user-agent=` in the browser arguments, it uses `Emulation.setUserAgentOverride` to synchronize the User-Agent string, platform, and full Client Hints metadata across all layers. It also injects `navigator.vendor` and `navigator.appVersion` overrides via `Page.addScriptToEvaluateOnNewDocument` to ensure consistency in newly opened tabs.

For timezone and geolocation consistency (to match a proxy IP's location), JavaScript overrides can set `Intl.DateTimeFormat().resolvedOptions().timeZone` and `Date.prototype.getTimezoneOffset`. The `--lang` flag and `set_accept_languages()` configure language headers. The `webrtc_leak_protection` option prevents WebRTC from exposing the real IP behind a proxy.

The general principle is that Pydoll provides the authentic browser fingerprint as a baseline, and the developer only needs to ensure that the configurable layers (User-Agent, timezone, language, geolocation) are consistent with each other and with the proxy's characteristics.

## References

- Laperdrix, P., Rudametkin, W., & Baudry, B. (2016). Beauty and the Beast: Diverting Modern Web Browsers to Build Unique Browser Fingerprints. IEEE S&P.
- Mowery, K., & Shacham, H. (2012). Pixel Perfect: Fingerprinting Canvas in HTML5. USENIX Security.
- Eckersley, P. (2010). How Unique Is Your Web Browser? Privacy Enhancing Technologies Symposium.
- W3C Client Hints Infrastructure: https://wicg.github.io/client-hints-infrastructure/
- BrowserLeaks: https://browserleaks.com/
- CreepJS: https://abrahamjuliot.github.io/creepjs/
