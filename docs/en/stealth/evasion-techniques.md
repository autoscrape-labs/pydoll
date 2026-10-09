# Evasion techniques

Detection systems correlate signals across layers: the network fingerprint (TCP/TLS/HTTP2), the browser fingerprint (canvas, WebGL, navigator), and behavior (mouse, keyboard, timing). Passing one layer while failing another still flags you. A residential IP with a mismatched TCP fingerprint, or a perfect browser fingerprint with robotic clicks, gets caught by anything that cross-checks. This page covers what Pydoll gives you for free and the levers you control to keep the layers consistent.

<iframe scrolling="no" src="/docs/resources/visuals/evasion-layers.html" aria-label="How the network, browser, behavior, and IP layers must all stay consistent to pass" style="width: 100%; height: 320px; border: 0;" loading="lazy"></iframe>

## What you get for free

Because Pydoll drives a real Chrome over CDP rather than synthesizing requests, several layers are authentic without any configuration:

- **Real network fingerprints.** Chrome's TCP/IP stack, TLS (BoringSSL), and HTTP/2 stack produce genuine fingerprints: the TLS ClientHello, the HTTP/2 `SETTINGS` frame, pseudo-header order, and stream priorities all match a real Chrome. Tools that build requests programmatically (requests, httpx, curl) do not.
- **Real browser fingerprints.** Canvas, WebGL, and AudioContext come from real GPU and audio hardware. Navigator properties, the built-in PDF plugins, and MIME types reflect genuine browser state.
- **`navigator.webdriver` is `false`.** Selenium, Playwright, and Puppeteer set it to `true`. Pydoll launches without automation flags, so it reports `false`, the same as a normal session. You don't patch it.
- **Complete input event sequences.** Input dispatched through CDP generates the full event chain (`pointermove`, `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click`) exactly as a real user would.

The rest of this page is the layers you do control.

## Keep the User-Agent consistent

The most common automation tell is a User-Agent that disagrees with itself: the HTTP `User-Agent` header saying one thing while `navigator.userAgent`, `navigator.platform`, and the Client Hints (`Sec-CH-UA`, `Sec-CH-UA-Platform`) say another. Setting `--user-agent=` as a plain Chrome flag changes only the HTTP header and leaves the JavaScript and Client Hints untouched, which is a mismatch a detector reads immediately.

Pydoll fixes this for you. When it sees a `--user-agent=` argument, it applies `Emulation.setUserAgentOverride` with the matching `platform` and full Client Hints metadata (greased brand and brand order computed the way Chromium does for that major), and exposes the reduced `Chrome/MAJOR.0.0.0` form that real Chrome reports. Every layer then agrees: the header on the wire, `navigator.userAgent`, `platform`, `vendor` and `appVersion`, the low- and high-entropy hints (`Sec-CH-UA`, `brands`, `fullVersionList`), in the first tab, in every tab you open later, and inside workers. The page gets no injected script; those values come from the override itself. Workers are the one place a script runs: the CDP override does not reach `WorkerNavigator.platform`, nor the User-Agent of shared and service workers, so Pydoll attaches to each worker before its code starts and sets those two there.

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

`154` is the major of the Chrome installed on the machine this page was written on; put yours. The next section is why that number is the one part of the string you cannot choose. The override applies to the first tab, tabs from `browser.new_tab()`, and tabs found via `browser.get_opened_tabs()`.

## Keep the major equal to the binary {#keep-the-major-equal-to-the-binary}

The override rewrites everything the browser *says* about its version. It cannot rewrite what the browser *is*: the JavaScript engine and the web platform of the binary you launched. Every Chrome major ships new APIs, and a detector that parses the major out of the User-Agent and then probes for functions that did not exist at that major reads the real one. This is how Chrome 154 answers when launched with a User-Agent claiming 130:

| Surface | Reports |
|---|---|
| `User-Agent` header, `navigator.userAgent`, `navigator.appVersion` | Chrome 130 |
| `Sec-CH-UA`, `navigator.userAgentData.brands`, `fullVersionList` | 130, with the `Not?A_Brand` GREASE brand Chrome 130 used |
| `RegExp.escape` (shipped in 136), `Float16Array` (135), `Error.isError` (134), `Uint8Array.fromBase64` (140), `Math.sumPrecise` (146) | all present |

Five functions that did not exist in Chrome 130 are there, so the page is a Chrome 146 or newer wearing a 130 badge. A check that cheap is common: open-source detectors such as FingerprintJS's BotD and CreepJS ship tables of which APIs and CSS properties each Chromium major added or removed, bracket the engine from them, and flag a User-Agent outside the bracket; some also fetch the current Stable release number and flag a User-Agent claiming a newer one. Google's reCAPTCHA has treated an outdated engine version in the User-Agent as suspicious since at least 2016 (Sivakorn, Polakis and Keromytis, *I am Robot*, EuroS&P 2016). Claiming a major newer than the binary fails the same way in reverse: the promised APIs are missing. The engine gives itself away in quieter ways too, because the text of its error messages, the last bits of some `Math` results and the syntax it accepts change between V8 releases. Underneath all of it, the TLS ClientHello and the HTTP/2 settings identify the engine family and roughly its era, so claiming Firefox or Safari fails before any JavaScript runs.

The rest of the string is yours to set. Chrome itself reports the reduced `Chrome/MAJOR.0.0.0` in the User-Agent and keeps the full build only in the high-entropy hints, which the override fills coherently from the value you give. So the build is the one part you can vary, and only when the platform really has more than one build for that major. Rotating identities means rotating the binary (brand, build), not the string, and a binary that stops updating while the Stable channel moves on becomes a small population by itself. Keep the major equal to `browser.get_version()`, take the OS and the device from the profile, and let the build stay `0.0.0`. A one-line check catches the mismatch on the next Chrome upgrade:

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

See [Human-like interactions](human-like-interactions.md) for the timing model and how to tune it.

## Look like a used profile

A brand-new profile with no history and every feature disabled looks nothing like a real user's. Pre-populate the profile through `browser_preferences` (aged timestamps, a matching Chrome version, enabled features), covered in [Browser preferences](../guides/browser-preferences.md#build-a-realistic-profile-for-stealth).

## Common mistakes

### Randomizing everything

A random `hardwareConcurrency`, `deviceMemory`, and screen size produce impossible devices. Real machines are constrained: 4 cores with 8 GB RAM and a 1920x1080 screen is plausible; 17 cores with 0.5 GB RAM and a 4K screen is not. Use profiles captured from real browsers, not random values.

### Injecting canvas noise

Adding noise to canvas output backfires: detectors sample the fingerprint repeatedly, and a value that changes between reads is itself an automation signal. Pydoll's canvas is authentic and stable; leave it.

### Outdated User-Agents

A UA from a Chrome release six months old claims a major the binary no longer is, and the engine's feature set says so; see [Keep the major equal to the binary](#keep-the-major-equal-to-the-binary). Chrome auto-updates for real users, so a current major is also what most of the traffic looks like.

### Ignoring session behavior

Even with a clean fingerprint, loading 100 pages in a minute, never scrolling, and never idling are anomalies. Add reading delays, vary the pace, and include natural pauses.

## Verify your setup

Check your fingerprint against these before running at scale:

| Tool | URL | Tests |
|------|-----|-------|
| BrowserLeaks | `https://browserleaks.com/` | Canvas, WebGL, fonts, IP, WebRTC, HTTP/2 |
| CreepJS | `https://abrahamjuliot.github.io/creepjs/` | Lie detection, consistency checks |
| Pixelscan | `https://pixelscan.net/` | Bot-detection analysis |
| IPLeak | `https://ipleak.net/` | WebRTC, DNS, IP leaks |

A quick self-check with Pydoll:

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

## What's next

- [Fingerprint injection](fingerprint-injection.md): apply a coherent identity (User-Agent, WebGL, timezone, locale) from one profile.
- [Human-like interactions](human-like-interactions.md): the behavioral layer in depth.
- [Proxies](../guides/proxies.md): change and verify your egress IP.
- [Fingerprinting (deep dive)](../deep-dive/fingerprinting/index.md): the detection theory behind these levers.
