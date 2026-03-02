# Evasion Techniques

This document covers practical techniques for evading fingerprinting detection using Pydoll. The previous sections described how detection works at each layer: [network fingerprinting](./network-fingerprinting.md) (TCP/IP, TLS, HTTP/2), [browser fingerprinting](./browser-fingerprinting.md) (Canvas, WebGL, navigator properties), and [behavioral fingerprinting](./behavioral-fingerprinting.md) (mouse, keyboard, scroll). This section focuses on countermeasures.

The core principle is consistency across layers. Passing one detection layer while failing another still results in a flag. A residential IP with a mismatched TCP fingerprint, or a perfect browser fingerprint with robotic mouse movements, will be caught by any system that correlates signals.

!!! info "Module Navigation"
    - [Network Fingerprinting](./network-fingerprinting.md): Protocol-level identification
    - [Browser Fingerprinting](./browser-fingerprinting.md): Application-layer detection
    - [Behavioral Fingerprinting](./behavioral-fingerprinting.md): Human behavior analysis

## What Pydoll Provides by Default

Before configuring anything, it helps to understand what Pydoll gives you for free by using a real Chrome instance via CDP.

**Authentic network fingerprints.** Chrome's TCP/IP stack, TLS implementation (BoringSSL), and HTTP/2 stack produce genuine fingerprints. The TLS ClientHello, HTTP/2 SETTINGS frame, pseudo-header order, and stream priorities all match a real Chrome browser. Tools that construct HTTP requests programmatically (requests, httpx, curl) produce non-browser fingerprints at these layers. With Pydoll, they are authentic by default.

**Authentic browser fingerprints.** Canvas, WebGL, and AudioContext fingerprints come from real GPU and audio hardware. Navigator properties, plugins (the standard 5 PDF plugins), and MIME types reflect genuine browser state. There is nothing to configure here.

**No `navigator.webdriver`.** Selenium, Playwright, and Puppeteer set `navigator.webdriver` to `true`. Pydoll uses CDP directly, which does not set this flag. The property is `undefined`, matching a normal user session.

**Complete event sequences.** When Pydoll dispatches input events through CDP's Input domain, Chrome generates the full event chain (pointermove, pointerdown, mousedown, pointerup, mouseup, click) exactly as it would for real user input.

## User-Agent Consistency

The most common fingerprinting inconsistency in automation is a mismatch between the HTTP `User-Agent` header, `navigator.userAgent` in JavaScript, `navigator.platform`, and Client Hints headers (`Sec-CH-UA`, `Sec-CH-UA-Platform`). Setting `--user-agent=` as a Chrome flag only changes the HTTP header, leaving JavaScript properties and Client Hints unchanged.

Pydoll solves this automatically. When it detects `--user-agent=` in the browser arguments, it:

1. Parses the UA string to extract browser name, version, and OS.
2. Calls `Emulation.setUserAgentOverride` via CDP with the full `userAgent`, the correct `platform` value (e.g., `Win32` for Windows), and complete `userAgentMetadata` (Client Hints data including `Sec-CH-UA`, `Sec-CH-UA-Platform`, `Sec-CH-UA-Full-Version-List`).
3. Injects `navigator.vendor` and `navigator.appVersion` overrides via `Page.addScriptToEvaluateOnNewDocument`, ensuring consistency even in newly opened tabs.

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
    # All layers are now consistent:
    # - HTTP User-Agent header
    # - navigator.userAgent / navigator.platform / navigator.appVersion
    # - Sec-CH-UA / Sec-CH-UA-Platform / Sec-CH-UA-Full-Version-List
    # - navigator.userAgentData.brands / .platform
    await tab.go_to('https://example.com')
```

This override is applied automatically to the initial tab, new tabs from `browser.new_tab()`, and any tabs discovered via `browser.get_opened_tabs()`.

!!! note "Supported Platforms"
    The UA parser handles Chrome, Edge, Windows (NT 6.1 through 10.0), macOS, Linux, Android, iOS, and Chrome OS. It generates proper GREASE brand values following the Chromium specification.

## Timezone and Locale Consistency

When using a proxy, the browser's timezone and language should match the proxy IP's geographic location. An IP geolocated to Tokyo with a browser timezone of `America/New_York` and `Accept-Language: en-US` is a detectable inconsistency.

### Language Configuration

Language is configured through Chrome flags and Pydoll's options API:

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

This sets both the `Accept-Language` HTTP header and `navigator.language` / `navigator.languages`.

### Timezone Override

Pydoll does not currently wrap CDP's `Emulation.setTimezoneOverride` command, so timezone override requires JavaScript injection. The critical APIs to override are `Intl.DateTimeFormat().resolvedOptions().timeZone` and `Date.prototype.getTimezoneOffset()`:

```python
async def set_timezone(tab, timezone_id: str, offset_minutes: int):
    """
    Override timezone via JavaScript.

    Args:
        timezone_id: IANA timezone name (e.g., 'Asia/Tokyo')
        offset_minutes: UTC offset in minutes (e.g., -540 for JST)
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

!!! warning "`execute_script` vs `addScriptToEvaluateOnNewDocument`"
    `tab.execute_script()` runs JavaScript in the current page context. If the page navigates, the override is lost. For overrides that must persist across navigations, use CDP's `Page.addScriptToEvaluateOnNewDocument`, which injects the script before any page JavaScript runs on every new document load. Pydoll uses this internally for User-Agent overrides. For timezone, you can send the CDP command directly:

    ```python
    await tab._connection_handler.execute_command(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': script}
    )
    ```

### Geolocation Override

For sites that request geolocation permission, the Geolocation API can be overridden via JavaScript:

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

## WebRTC Leak Protection

WebRTC can expose the client's real IP address even when using a proxy, through STUN/TURN server requests that bypass the proxy tunnel. Pydoll provides a built-in option to prevent this:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
# Adds: --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

This forces Chrome to route all WebRTC traffic through the proxy, preventing IP leakage. It should be enabled whenever using a proxy for stealth automation.

## Behavioral Humanization

Pydoll implements humanized interactions for mouse, keyboard, and scroll through the `humanize=True` parameter. These are not future features or manual workarounds; they are built into the framework.

### Mouse

```python
# Humanized click: Bezier curve path, Fitts's Law timing,
# minimum-jerk velocity, tremor, overshoot + correction
await element.click(humanize=True)
```

When `humanize=True` is passed to a WebElement's `click()`, Pydoll generates a complete mouse movement from the current cursor position to the element using a cubic Bezier curve with randomized control points. The velocity follows a minimum-jerk profile. Physiological tremor, overshoot (70% probability), and micro-pauses are added. The movement duration is computed from Fitts's Law based on the distance and target size. See [Behavioral Fingerprinting](./behavioral-fingerprinting.md#pydolls-mouse-humanization) for detailed parameter descriptions.

### Keyboard

```python
# Humanized typing: variable delays, realistic typos (~2%),
# punctuation pauses, thinking pauses, distraction pauses
await element.type_text("Hello, world!", humanize=True)
```

Humanized typing uses variable inter-key delays (30-120ms uniform distribution), punctuation pauses, thinking pauses (2% probability), distraction pauses (0.5% probability), and realistic typos with five distinct error types and natural correction sequences. See [Behavioral Fingerprinting](./behavioral-fingerprinting.md#pydolls-keyboard-humanization) for the full parameter breakdown.

### Scroll

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)
# Humanized scroll: Bezier easing, jitter, micro-pauses, overshoot
await scroll.by(ScrollPosition.Y, 800, humanize=True)
```

Humanized scrolling uses Bezier easing curves, per-frame jitter (±3px), micro-pauses (5% probability), and overshoot correction (15% probability). Large distances are broken into multiple "flick" gestures. See [Behavioral Fingerprinting](./behavioral-fingerprinting.md#pydolls-scroll-humanization) for details.

## Request Interception

Pydoll supports request interception via CDP's Fetch domain, allowing you to modify headers, block requests, or provide custom responses before they reach the server:

```python
from pydoll.protocol.fetch.events import FetchEvent

async def handle_request(event):
    request_id = event['params']['requestId']
    request = event['params']['request']
    headers = request.get('headers', {})

    # Example: ensure Brotli support is advertised
    if 'Accept-Encoding' in headers and 'br' not in headers['Accept-Encoding']:
        headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'

    header_list = [{'name': k, 'value': v} for k, v in headers.items()]
    await tab.continue_request(request_id=request_id, headers=header_list)

await tab.enable_fetch_events()
await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)
```

In practice, header modification is rarely needed with Pydoll because Chrome generates correct headers natively. Request interception is more useful for blocking tracking scripts, modifying response content, or debugging.

## Browser Preferences for Realism

Chrome stores user preferences that fingerprinting systems can inspect. A brand-new browser profile with no history, no saved preferences, and default-everything looks different from a profile that has been used for weeks. Pydoll's `browser_preferences` option lets you pre-populate these:

```python
import time

options = ChromiumOptions()
options.browser_preferences = {
    'profile': {
        'created_by_version': '120.0.6099.130',
        'creation_time': str(time.time() - 90 * 86400),  # 90 days ago
        'exit_type': 'Normal',
    },
    'profile.default_content_setting_values': {
        'cookies': 1,
        'images': 1,
        'javascript': 1,
        'notifications': 2,  # "Ask" (realistic default)
    },
}
```

## Common Mistakes

### Randomizing Everything

Generating a random fingerprint from scratch (random hardwareConcurrency, random deviceMemory, random screen size) creates impossible combinations. Real devices have constrained configurations: a 4-core machine with 8 GB RAM, 1920x1080 screen, and Windows 10 is a plausible profile. A 17-core machine with 0.5 GB RAM, 3840x2160 screen, and `navigator.platform: Linux armv7l` is not. Use profiles captured from real browsers rather than random generation.

### Canvas Noise Injection

Adding random noise to canvas output to prevent fingerprinting is counterproductive. Detection systems request the fingerprint multiple times. If the hash changes between requests, noise injection is detected, which is itself a strong automation signal. With Pydoll, the canvas fingerprint is authentic and consistent. Leave it alone.

### Outdated User-Agents

Using a User-Agent from a browser version that is 6+ months old is detectable because the version lacks features and Client Hints values that the current release would have. Keep User-Agent strings current within the last 2-3 major Chrome versions.

### Ignoring Session-Level Behavior

Even with perfect fingerprints and humanized interactions, session-level behavior matters. Loading 100 pages in 60 seconds, never scrolling, clicking only buttons (never links), and maintaining constant focus for hours without a single tab switch or idle period are all behavioral anomalies. Add reading delays between navigations, vary the pace of multi-page workflows, and include natural idle periods.

## Verification

Before deploying automation at scale, verify your fingerprint using these tools:

| Tool | URL | Tests |
|------|-----|-------|
| BrowserLeaks | https://browserleaks.com/ | Canvas, WebGL, fonts, IP, WebRTC, HTTP/2 |
| CreepJS | https://abrahamjuliot.github.io/creepjs/ | Lie detection, consistency checks |
| Fingerprint.com | https://fingerprint.com/demo/ | Commercial-grade identification |
| PixelScan | https://pixelscan.net/ | Bot detection analysis |
| IPLeak | https://ipleak.net/ | WebRTC, DNS, IP leaks |

A basic verification script with Pydoll:

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

    # Check for obvious issues
    assert fp['webdriver'] is None, 'navigator.webdriver should be undefined'
    assert fp['plugins'] == 5, f'Expected 5 plugins, got {fp["plugins"]}'
    assert 'HeadlessChrome' not in fp['userAgent'], 'Headless detected in UA'
```

## References

- Chrome DevTools Protocol, Emulation Domain: https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
- Chrome DevTools Protocol, Fetch Domain: https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
- Chromium Source, Inspector Emulation Agent: https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc
