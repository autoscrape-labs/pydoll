# Auditing a fingerprint

You cannot improve what you cannot measure. Once a profile is applied, the question is which signals now read as a real device and which still leak, and no amount of reading the code answers it as well as pointing a detector at the browser. This page covers how to measure that, from a free bot score to reading exactly what a commercial detector collects.

It builds on [The limits of spoofing](spoofing-limits.md): that page explains what can and cannot be faked, this one shows how to check what your setup actually did.

## Read the bot score

[fingerprint-scan.com](https://fingerprint-scan.com/) runs a fingerprinting and bot-detection test inside the page and reports a score from 0 to 100, where lower reads as more human. Drive it with Pydoll and screenshot the result:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from examples.fingerprints import FINGERPRINTS

async def scan(profile):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.apply_fingerprint(FINGERPRINTS[profile])
        await tab.go_to('https://fingerprint-scan.com/')
        await asyncio.sleep(15)          # let the score finish computing
        await tab.take_screenshot(f'{profile}.png')

asyncio.run(scan('macos_m3_new_york'))
```

The number on its own means little. Its value is in the comparison: run the same machine with and without the profile, and with a matched profile versus a deliberately mismatched one, and diff the scores. That is how you attribute a change to a specific signal instead of guessing.

The clearest example is headless. With no profile, headless Chrome scores the maximum:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com reporting a bot score of 100/100 for headless Chrome with no fingerprint" width="720" />
</p>

Apply a matched profile and the same headless run drops to the headful score:

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com reporting a bot score of 15/100 for headless Chrome with a macOS fingerprint applied" width="720" />
</p>

!!! warning "A bot score is a snapshot"
    One machine, one IP, one Chrome build, one moment. Detection sites also change their scoring. Read the *direction* a change moves the score, not the absolute number.

## Cross-check the lie detectors

A bot score is one opinion. [CreepJS](https://abrahamjuliot.github.io/creepjs/) is a second and a stricter one: it does not just read each signal, it inspects how each was defined and reads the whole fingerprint a second time inside a Web Worker, then reports the contradictions as *lies*.

That worker pass is the one a naive override fails. CreepJS reads the identity in the page and again in a `WorkerNavigator`, a separate realm a main-thread hook never reaches. If the page says Windows and the worker says the real macOS, that disagreement is the lie. A profile that is applied correctly reports the same identity in both:

<p align="center">
  <img src="/docs/resources/images/creepjs-worker-windows.png" alt="CreepJS worker panel replaying the injected Windows identity: a Windows User-Agent, an NVIDIA GeForce RTX 3060, Win32 and Windows 11, all inside a service worker on an Apple Mac" width="720" />
</p>

[SannySoft](https://bot.sannysoft.com/) and [BrowserScan](https://www.browserscan.net/bot-detection) are quicker checks for the headless and automation flags. Use them as a fast pass, not the final word.

## Compare the read paths yourself

The strongest audit does not need a third-party site. For any signal, read it two ways and check they agree, because a disagreement is usually a leak your own overrides created:

```python
result = await tab.execute_script('''
    document.head.insertAdjacentHTML('beforeend',
        '<style>.probe{--g: srgb} @media (color-gamut: p3){.probe{--g: p3}}</style>');
    const probe = document.createElement('div');
    probe.className = 'probe';
    document.body.appendChild(probe);
    return {
        matchMedia: matchMedia('(color-gamut: p3)').matches ? 'p3' : 'srgb',
        css: getComputedStyle(probe).getPropertyValue('--g').trim(),
    };
''', return_by_value=True)
```

If `matchMedia` and the CSS path disagree, an override is lying on one path only, the failure mode [The limits of spoofing](spoofing-limits.md) walks through. The same test applies across realms (page versus worker) and across APIs (the WebGL string versus the WebGPU adapter). A coherent profile passes all of them; a contradiction is a signal you introduced.

## Read what a real detector collects

The deepest audit is to stop guessing which signals matter and read the list a production detector actually reads. These agents ship heavily obfuscated, but the surface they measure is public browser API, so it can be reverse-engineered.

A public teardown of **Fingerprint Pro v4** (build `jsl/4.0.0`), measured against the vendor's public demo tenant on one machine in August 2026, catalogs roughly **143 individual signals**, across screen and display, hardware, `navigator`, GPU (WebGL and WebGPU), audio, fonts, media, storage, and automation flags. Those numbers are specific to that build, tenant, and moment, not a universal law, but two findings reshape how you audit:

- **Most of the surface does not decide identity on its own.** In the tested runs, moving canvas, WebGL, the User-Agent, screen, and locale together did not independently mint a new visitor; the fuzzy match tolerated it. Changing the canvas digests did move the reported confidence, from about 0.99 to 0.97, without minting a new id. So most spoofing effort is wasted on identity.
- **The strongest identity signal is not a fingerprint.** It is a bearer token, `s56`, the tenant issues over the agent's initial GET and the client replays on every POST. Once it is bound, the payload answers as that visitor regardless of canvas, GPU, or User-Agent.

!!! note "Identity is a session-token problem, not a fingerprint one"
    To present as a new visitor, start from a clean [browser context](../../guides/browser-contexts.md) so no prior `s56` token is replayed and the agent issues a fresh one. To persist one identity, reuse the context so the same token comes back. In this teardown, spoofing canvas, WebGL, and the User-Agent did not independently change the visitor id, so that effort is better spent on coherence than on a new identity. The egress IP was excluded from the identity analysis; it feeds a separate bot and proxy signal, so rotating the IP alone does not change who the token says you are.

## Capture what the agent sends

!!! warning "Handle a captured payload with care"
    A captured payload carries session tokens, storage identifiers, your IP, and other data that identifies you. Capture only against a site you are authorized to test, run it under a disposable identity you can throw away, and redact the tokens, storage ids, and IP before you store, share, or paste the payload anywhere.

The agent does not only read those signals, it packages them and POSTs them to its server, and that payload is readable. A typical agent serializes the signals to JSON, encodes them to a compact byte form, compresses anything past roughly a kilobyte with raw DEFLATE, and wraps the result in a framed envelope whose key travels inside the frame. That last step is obfuscation, not encryption; there is no secret you are missing.

So the deepest audit is a capture. Use [request interception](../../guides/request-interception.md) to grab the body of the agent's POST, reverse the framing, and inflate it. What comes out is the exact signal set the detector built for your session, read straight from the code that scores you. That is the ground truth for which of your overrides held and which leaked, and it is more reliable than any bot score, because it is the input to the score rather than the output.

## Related

- [The limits of spoofing](spoofing-limits.md): what a spoof can and cannot move.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): applying a coherent profile.
- [Browser contexts](../../guides/browser-contexts.md): one identity per context, the real lever for a fresh visitor.
