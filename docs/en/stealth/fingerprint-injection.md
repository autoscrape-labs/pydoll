# Fingerprint injection

## Introduction

`tab.apply_fingerprint()` gives the browser a new identity. It overrides the signals fingerprinting scripts read, User-Agent and Client Hints, `navigator`, WebGL, screen metrics, fonts, audio, timezone, and locale, across the page, its workers, and its cross-origin iframes, before the first navigation. You don't hand-build a fingerprint or patch `navigator` yourself; you pass a profile and Pydoll applies it coherently.

The payoff is concrete. With a matched profile, headless Chrome goes from an instant bot flag to reading as an ordinary desktop, enough to [clear Cloudflare's managed challenge in headless mode](#clear-cloudflares-challenge-headless).

One honest limit up front: this is identity substitution, not anonymity. It does not change your egress IP or the network-layer fingerprint, and an inconsistent profile is more detectable than an untouched browser. Making the profile *match* your machine and IP is the whole job, and [the rules below](#making-a-profile-pass) are that checklist.

**You will learn**

- [How to apply a fingerprint](#quick-start)
- [How it clears Cloudflare headless](#clear-cloudflares-challenge-headless)
- [How to prove it is working](#prove-it-with-a-bot-score)
- [How to make a profile pass](#making-a-profile-pass)
- [How to use your own profiles](#bring-your-own-profiles)

## Quick start {#quick-start}

Call `apply_fingerprint()` before the first navigation. Only the fields present in the profile are overridden; the rest keep the real browser values.

```python
import asyncio

from pydoll.browser.chromium import Chrome

from examples.fingerprints import FINGERPRINTS

async def spoof_fingerprint():
    async with Chrome() as browser:
        tab = await browser.start()

        # Apply before the first navigation.
        await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

        await tab.go_to('https://abrahamjuliot.github.io/creepjs/')
        await asyncio.sleep(5)

asyncio.run(spoof_fingerprint())
```

!!! note "Where `FINGERPRINTS` comes from"
    Pydoll does not ship fingerprint profiles. `FINGERPRINTS` lives in `examples/fingerprints.py` in the [pydoll repository](https://github.com/autoscrape-labs/pydoll), as reference profiles for the `FingerprintConfig` shape (a typed dictionary from `pydoll.protocol.fingerprint.types`). Copy that file into your project, then adapt each profile to your own machine and IP, [the rules below](#making-a-profile-pass) explain why. A profile reused as-is is a shared signature, not a disguise.

## Clear Cloudflare's challenge headless {#clear-cloudflares-challenge-headless}

Headless Chrome normally fails bot checks on sight: a software WebGL renderer, a hardcoded 800x600 screen, empty plugin lists. A matched profile neutralizes those rendering signals, so a headless session reads as headful. With the identity also replayed into the cross-origin challenge frame (`cross_origin_iframes`, on by default), that is enough to pass Cloudflare's managed challenge, no captcha solver involved.

<p align="center">
  <img src="/docs/resources/images/cloudflare-headless-bypass.gif" alt="Pydoll in headless mode loading a Cloudflare-protected site and clearing the managed challenge with a fingerprint applied" width="760" />
</p>
<p align="center"><sub>Headless, with a matched fingerprint: the managed challenge clears.</sub></p>

```python
async with Chrome() as browser:
    tab = await browser.start(headless=True)

    # Match the profile to THIS host and IP (see the rules below).
    await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

    await tab.go_to('https://a-site-behind-cloudflare.com')
    # The interstitial clears when the identity is coherent.
```

Two conditions make it work, both from [the rules below](#making-a-profile-pass): the profile has to be coherent (OS, Chrome version, and locale all matching your host and IP), and the IP has to be clean. A datacenter IP with poor reputation is still challenged headless and headful alike. On a marginal IP, prefer headful, or headful under Xvfb.

Under the hood, headless also has one client-side leak a cross-origin frame reads directly: its own `window.screen`. Without the reshape the frame reads the raw 800x600 headless screen and contradicts the page; with it, they match.

<iframe scrolling="no" src="/docs/resources/visuals/headless-screen-oopif.html" aria-label="A headless page and its cross-origin iframe each reading window.screen; toggling the reshape flips the iframe from the raw 800x600 headless screen to matching the page" style="width: 100%; height: 460px; border: 0;" loading="lazy"></iframe>

For the full breakdown of what the challenge reads and why coherence passes it, see [Cloudflare's managed challenge](../deep-dive/fingerprinting/cloudflare-challenge.md).

## Prove it with a bot score {#prove-it-with-a-bot-score}

Whether a fingerprint helps or hurts is measurable. [fingerprint-scan.com](https://fingerprint-scan.com/), built by the engineer behind the Castle anti-bot blog, reports a **bot score** from 0 to 100, lower reads as more human. Headless is the sharpest demonstration: with no profile, headless Chrome scores the maximum; a matched profile drops it to the headful level.

| Run (same Mac, Chrome 151) | Bot score |
|---|---|
| Headless, no profile | 100 / 100 |
| Headless, matched macOS profile | 15 / 100 |
| Headful, no profile | 15 / 100 |
| Headful, matched macOS profile | 15 / 100 |
| Headful, mismatched Windows profile | 57 / 100 |

<p align="center">
  <img src="/docs/resources/images/fp-scan-headless-nofp.png" alt="fingerprint-scan.com reporting a bot score of 100/100 for headless Chrome with no fingerprint" width="380" />
  <img src="/docs/resources/images/fp-scan-headless-mac.png" alt="fingerprint-scan.com reporting a bot score of 15/100 for headless Chrome with a macOS fingerprint applied" width="380" />
</p>
<p align="center"><sub>Headless: 100/100 with no profile, 15/100 with a matched macOS profile.</sub></p>

Two things this proves. The profile does not make the browser invisible: even matched, it scores 15, not 0 (real Chrome over CDP is already human-like, and closing the last gap is an open area). And a *mismatched* profile scores worse than no profile at all, the last row jumps to 57 because one field (the OS) contradicts the hardware underneath. That is the whole reason these rules exist.

!!! warning "These numbers are a snapshot"
    One machine, one IP, one Chrome build, one moment. Yours will differ and detection sites change their scoring. Treat them as direction (matched stays low, mismatched jumps), not a guaranteed result.

For the full audit method, reading a signal back and comparing realms, see [Auditing a fingerprint](../deep-dive/fingerprinting/auditing.md).

## Making a profile pass {#making-a-profile-pass}

A profile passes when it agrees with the machine and IP it runs on. Most of these rules describe a layer `apply_fingerprint()` cannot reach, so you match it instead of fighting it. They are all the same rule underneath: **coherence across every layer**.

### Match the profile OS to your host OS

The kernel TCP/IP stack and the OS text rendering expose the real OS in layers no override reaches. A Windows profile on a Mac is a contradiction Cloudflare blocks on, and the mismatch that pushes the bot score to 57 above. Run a macOS profile on macOS, a Windows profile on Windows. A forwarding proxy re-originates the TCP connection from the proxy's kernel, so a Windows profile then needs a proxy running on Windows. Full measurement: [The OS must match the host](../deep-dive/fingerprinting/cloudflare-challenge.md#the-os-must-match-the-host).

### Match the Chrome version to your binary

The TLS handshake and the JavaScript engine report the real binary version; the User-Agent is the only part `apply_fingerprint()` changes. A profile claiming Chrome 145 on a Chrome 151 binary is a contradiction, and the most common cause of Turnstile failure with a fingerprint applied. Read the binary version and keep the profile's `CHROME_DESKTOP` / `CHROME_MOBILE` major equal to it, updating on every Chrome upgrade.

```python
version = await browser.get_version()
print(version['product'])  # e.g. 'Chrome/151.0.7922.137'
```

Full breakdown: [The Chrome version must match the binary](../deep-dive/fingerprinting/cloudflare-challenge.md#the-chrome-version-must-match-the-binary).

### Match locale and timezone to your egress IP

`Accept-Language`, `navigator.languages`, and the timezone are cross-referenced against the IP's country. A US profile behind a Brazilian IP made a plain Google search return a captcha; setting a Brazilian locale, matching the IP, removed the block with no other change.

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google serving a captcha because the injected fingerprint's US locale contradicts the Brazilian egress IP" width="640" />
</p>
<p align="center"><sub>US locale over a Brazilian IP: Google returns a captcha.</sub></p>

### Cover cross-origin iframes

Leave `cross_origin_iframes` on (the default) so a challenge or captcha frame in its own process reads the injected identity, not the real machine. It is scoped to frames that actually read a fingerprint, so it does not slow ordinary third-party iframes.

```python
# Default: the identity also covers cross-origin iframes.
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])

# Opt out to cover only the top page, same-origin frames, and workers.
await tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'], cross_origin_iframes=False)
```

How the identity reaches each realm: [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md).

### One fingerprint per browser context

Service and shared workers are shared across a browser context, so a context holds one identity. Applying a second fingerprint to the same context raises `FingerprintContextConflict`. Run different identities in separate contexts.

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

See [Browser contexts](../guides/browser-contexts.md).

A few smaller rules round it out: apply the fingerprint before the first navigation; do not combine the `--user-agent` option with `apply_fingerprint()` (the profile owns the User-Agent); match the WebGL vendor/renderer and color-gamut to the host GPU and display; use a clean residential IP. For why some signals can be overridden and others cannot be faked at all, see [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md).

## Bring your own profiles {#bring-your-own-profiles}

Pydoll does not generate or ship fingerprints. The profiles in `examples/fingerprints.py` are a reference for the coherence a profile requires and the `FingerprintConfig` shape, not a catalog to deploy as-is. A profile has to match the Chrome binary in use (the network layer is authentic and cannot be overridden) and the egress IP geography (locale, timezone, geolocation). A public profile reused widely becomes a shared signature rather than a disguise.

## What's next

- [Auditing a fingerprint](../deep-dive/fingerprinting/auditing.md): read a signal back, compare realms, and confirm a profile took effect.
- [Cloudflare's managed challenge](../deep-dive/fingerprinting/cloudflare-challenge.md): the per-layer breakdown of what passes headless and why.
- [The limits of spoofing](../deep-dive/fingerprinting/spoofing-limits.md): which signals are safe to override and which cannot be faked.
- [Workers and cross-origin iframes](../deep-dive/fingerprinting/execution-realms.md): how the identity is replayed into every realm.
- [Network fingerprinting](../deep-dive/fingerprinting/network-fingerprinting.md): the TLS/TCP/HTTP2 layer injection cannot reach.
- [Evasion techniques](evasion-techniques.md): User-Agent consistency, WebRTC leak protection, and what Pydoll gives you for free.
