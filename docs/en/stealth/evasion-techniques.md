# Evasion techniques

Detection systems correlate signals across layers: the network fingerprint (TCP/TLS/HTTP2), the browser fingerprint (canvas, WebGL, navigator), and behavior (mouse, keyboard, timing). Passing one layer while failing another still flags you. A residential IP with a mismatched TCP fingerprint, or a perfect browser fingerprint with robotic clicks, gets caught by anything that cross-checks. This page covers what Pydoll gives you for free and the levers you control to keep the layers consistent.

<iframe src="../evasion-layers.html" aria-label="How the network, browser, behavior, and IP layers must all stay consistent to pass" style="width: 100%; height: 320px; border: 0;" loading="lazy"></iframe>

## What you get for free

Because Pydoll drives a real Chrome over CDP rather than synthesizing requests, several layers are authentic without any configuration:

- **Real network fingerprints.** Chrome's TCP/IP stack, TLS (BoringSSL), and HTTP/2 stack produce genuine fingerprints: the TLS ClientHello, the HTTP/2 `SETTINGS` frame, pseudo-header order, and stream priorities all match a real Chrome. Tools that build requests programmatically (requests, httpx, curl) do not.
- **Real browser fingerprints.** Canvas, WebGL, and AudioContext come from real GPU and audio hardware. Navigator properties, the built-in PDF plugins, and MIME types reflect genuine browser state.
- **`navigator.webdriver` is `false`.** Selenium, Playwright, and Puppeteer set it to `true`. Pydoll launches without automation flags, so it reports `false`, the same as a normal session. You don't patch it.
- **Complete input event sequences.** Input dispatched through CDP generates the full event chain (`pointermove`, `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click`) exactly as a real user would.

The rest of this page is the layers you do control.

## Keep the User-Agent consistent

The most common automation tell is a User-Agent that disagrees with itself: the HTTP `User-Agent` header saying one thing while `navigator.userAgent`, `navigator.platform`, and the Client Hints (`Sec-CH-UA`, `Sec-CH-UA-Platform`) say another. Setting `--user-agent=` as a plain Chrome flag changes only the HTTP header and leaves the JavaScript and Client Hints untouched, which is a mismatch a detector reads immediately.

Pydoll fixes this for you. When it sees a `--user-agent=` argument, it applies `Emulation.setUserAgentOverride` with the matching `platform` and full Client Hints metadata, and injects `navigator.vendor` / `navigator.appVersion`, so every layer agrees, including in new tabs.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/130.0.0.0 Safari/537.36'
    )

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/javascript')

asyncio.run(main())
```

Keep the `Chrome/<version>` in the string equal to the Chrome you actually run; a version you aren't running is itself a mismatch. The override applies to the first tab, tabs from `browser.new_tab()`, and tabs found via `browser.get_opened_tabs()`.

## Match language, timezone, and geolocation to the IP

Behind a proxy, the browser's language, timezone, and location should agree with the IP's country. An IP in Tokyo with `Accept-Language: en-US` and an `America/New_York` timezone is a contradiction.

Language is a standalone option:

```python
options = ChromiumOptions()
options.add_argument('--lang=ja-JP')
options.set_accept_languages('ja-JP,ja;q=0.9,en;q=0.8')
```

This sets both the `Accept-Language` header and `navigator.language` / `navigator.languages`. Timezone and geolocation have to match too, and they need to stay consistent with the User-Agent OS and the IP all at once. Setting them coherently from a single profile is what `apply_fingerprint()` is for; see [Fingerprint Injection](fingerprint-injection.md).

## Stop WebRTC from leaking your IP

WebRTC can reveal the real IP even behind a proxy, through STUN requests that skip the proxy tunnel. Turn on the built-in protection whenever you use a proxy for stealth:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True   # --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

## Behave like a person

Instant clicks and perfectly regular keystrokes are a behavioral fingerprint. Pass `humanize=True` to move the cursor along a curved, human-timed path and type with variable rhythm and occasional corrected typos:

```python
field = await tab.find(id='search')
await field.type_text('browser automation', humanize=True)
await field.click(humanize=True)
```

See [Human-like interactions](human-like-interactions.md) for the timing model and how to tune it.

## Look like a used profile

A brand-new profile with no history and every feature disabled looks nothing like a real user's. Pre-populate the profile through `browser_preferences` (aged timestamps, a matching Chrome version, enabled features), covered in [Browser preferences](../guides/browser-preferences.md#build-a-realistic-profile-for-stealth).

## Common mistakes

**Randomizing everything.** A random `hardwareConcurrency`, `deviceMemory`, and screen size produce impossible devices. Real machines are constrained: 4 cores with 8 GB RAM and a 1920x1080 screen is plausible; 17 cores with 0.5 GB RAM and a 4K screen is not. Use profiles captured from real browsers, not random values.

**Injecting canvas noise.** Adding noise to canvas output backfires: detectors sample the fingerprint repeatedly, and a value that changes between reads is itself an automation signal. Pydoll's canvas is authentic and stable; leave it.

**Outdated User-Agents.** A UA from a Chrome release six months old lacks features and Client Hints the current version has. Stay within the last two or three major versions, and match the binary you run.

**Ignoring session behavior.** Even with a clean fingerprint, loading 100 pages in a minute, never scrolling, and never idling are anomalies. Add reading delays, vary the pace, and include natural pauses.

## Verify your setup

Check your fingerprint against these before running at scale:

| Tool | URL | Tests |
|------|-----|-------|
| BrowserLeaks | `https://browserleaks.com/` | Canvas, WebGL, fonts, IP, WebRTC, HTTP/2 |
| CreepJS | `https://abrahamjuliot.github.io/creepjs/` | Lie detection, consistency checks |
| Pixelscan | `https://pixelscan.net/` | Bot-detection analysis |
| IPLeak | `https://ipleak.net/` | WebRTC, DNS, IP leaks |

A quick self-check with Pydoll:

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

## What's next

- [Fingerprint injection](fingerprint-injection.md): apply a coherent identity (User-Agent, WebGL, timezone, locale) from one profile.
- [Human-like interactions](human-like-interactions.md): the behavioral layer in depth.
- [Proxies](../guides/proxies.md): change and verify your egress IP.
- [Fingerprinting (deep dive)](../deep-dive/fingerprinting/index.md): the detection theory behind these levers.
