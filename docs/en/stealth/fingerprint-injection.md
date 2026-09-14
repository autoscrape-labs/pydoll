# Fingerprint injection

## Introduction

`tab.apply_fingerprint()` gives the browser a new identity. It overrides the signals fingerprinting scripts read, User-Agent and Client Hints, `navigator`, WebGL and WebGPU, screen metrics, fonts, audio, permissions, timezone, and locale, before the first navigation. You pass a profile; Pydoll applies it through the browser's own override commands wherever one exists and through hardened JavaScript only where none does.

One honest limit up front: this is identity substitution, not anonymity. It does not change your egress IP or the network-layer fingerprint, and an inconsistent profile is more detectable than an untouched browser. A profile has to match the machine and the IP it runs on.

!!! warning "None of this is a guarantee"
    Each site reads its own subset of signals and weighs it its own way. A minimal profile (User-Agent, locale, timezone matched to the host and the IP) clears many targets on its own, and a small residual inconsistency may never be read at all. Start simple, test against the actual site, and add fields only when a measurement says a specific signal is what blocks you.

**You will learn**

- [How to apply a fingerprint](#quick-start)
- [What a profile can set](#what-a-profile-can-set)
- [The rules that keep a profile coherent](#making-a-profile-pass)
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
    Pydoll does not ship fingerprint profiles. `FINGERPRINTS` lives in `examples/fingerprints.py` in the [pydoll repository](https://github.com/autoscrape-labs/pydoll), as reference profiles for the `FingerprintConfig` shape (a typed dictionary from `pydoll.protocol.fingerprint.types`). Copy that file into your project, then adapt each profile to your own machine and IP. A profile reused as-is is a shared signature, not a disguise.

## What a profile can set {#what-a-profile-can-set}

`FingerprintConfig` is a typed dictionary; every section is optional and each one covers one surface a fingerprinting script reads.

| Section | Sets |
|---|---|
| `user_agent` | the User-Agent string, `navigator.platform` / `vendor` / `appVersion`, and the `Sec-CH-UA*` Client Hints (brands and their order follow Chromium's own algorithm for the major) |
| `client_hints` | the high-entropy hints the User-Agent string cannot carry: `platform_version`, `model`, `architecture`, `bitness`, `form_factors` |
| `locale` | `navigator.language(s)`, the `Accept-Language` header and the `Intl` locale |
| `timezone`, `geolocation` | `Intl` timezone, `Date`, and the Geolocation API |
| `screen` | `screen.*`, `devicePixelRatio`, window and viewport size |
| `hardware` | `hardwareConcurrency`, `deviceMemory`, `maxTouchPoints` (touch events are enabled for touch profiles) |
| `permissions` | `navigator.permissions.query()` states, in agreement with `Notification.permission` |
| `media_features` | `color-gamut`, `prefers-color-scheme` and the other CSS media features Chrome can emulate |
| `webgl` | vendor and renderer strings, WebGL and WebGL2 limits, extensions, shader precision |
| `webgpu` | `adapter.info`, limits and features of the real adapter |
| `media_devices`, `speech`, `audio`, `network_connection`, `fonts`, `webrtc_ip_policy` | media device counts, speech voices, audio device capabilities, `navigator.connection`, local fonts, the WebRTC ICE policy |

The full field list, with the accepted values and an example per section, is in the docstrings of `pydoll/protocol/fingerprint/types.py`.

## Making a profile pass {#making-a-profile-pass}

A profile passes when it agrees with the machine and the IP it runs on. The rules are all the same rule underneath: coherence across every layer.

### Match the profile OS to your host OS

The kernel and the OS text rendering expose the real OS in layers no override reaches. Run a macOS profile on macOS, a Windows profile on Windows. A forwarding proxy re-originates the connection from the proxy's kernel, so a Windows profile then needs a proxy running on Windows.

### Match the Chrome version to your binary

The TLS handshake and the JavaScript engine report the real binary version; the User-Agent is the only part `apply_fingerprint()` changes. Read the binary version and keep the profile's major equal to it, updating on every Chrome upgrade.

```python
version = await browser.get_version()
print(version['product'])  # e.g. 'Chrome/152.0.7977.83'
```

### Match locale and timezone to your egress IP

`Accept-Language`, `navigator.languages`, the timezone and the geolocation are cross-referenced against the IP's country. A US profile behind a Brazilian IP made a plain Google search return a captcha; a Brazilian locale, matching the IP, removed the block with no other change.

<p align="center">
  <img src="/docs/resources/images/fingerprint-inconsistent-captcha.png" alt="Google serving a captcha because the injected fingerprint's US locale contradicts the Brazilian egress IP" width="640" />
</p>
<p align="center"><sub>US locale over a Brazilian IP: Google returns a captcha.</sub></p>

### Match the GPU and the fonts to the host

The `webgl` and `webgpu` sections change what the browser reports about the GPU; what the GPU draws stays real. Name the GPU family that is actually in the machine, and capture the limits and features from a real device of that class rather than guessing. The `fonts` section covers the JavaScript font probes; the layout engine measures the fonts really installed, so list exactly what is installed.

### Pin the Client Hints the User-Agent cannot carry

The User-Agent string is frozen (`Mac OS X 10_15_7`, `Android 10; K`); real Chrome reports the true OS version, device model and form factor in the Client Hints. The parser fills plausible defaults; set `client_hints` to pin the values read on a real device.

```python
fingerprint = FingerprintConfig(
    user_agent=UA_WINDOWS,
    client_hints=ClientHintsFingerprint(platform_version='15.0.0'),
)
```

### One fingerprint per browser context

A browser context holds one identity. Applying a second, different fingerprint to the same context raises `FingerprintContextConflict`. Run different identities in separate contexts.

```python
ctx_id = await browser.create_browser_context()
tab_us = await browser.start()
tab_br = await browser.new_tab(browser_context_id=ctx_id)

await tab_us.apply_fingerprint(FINGERPRINTS['windows11_rtx3060_nyc'])
await tab_br.apply_fingerprint(FINGERPRINTS['android_s24_ultra_sao_paulo'])
```

See [Browser contexts](../guides/browser-contexts.md).

A few smaller rules round it out: apply the fingerprint before the first navigation; if you set the `--user-agent` option, keep it equal to the profile's (a different value logs a warning); use a clean residential IP; prefer `click(humanize=True)` and the [human-like interactions](human-like-interactions.md), because input is what many targets weigh most.

## Bring your own profiles {#bring-your-own-profiles}

Pydoll does not generate or ship fingerprints. The profiles in `examples/fingerprints.py` are a reference for the coherence a profile requires and the `FingerprintConfig` shape, not a catalog to deploy as-is. A profile has to match the Chrome binary in use and the egress IP geography (locale, timezone, geolocation). A public profile reused widely becomes a shared signature rather than a disguise.

## What's next

- [Auditing a fingerprint](../deep-dive/fingerprinting/auditing.md): read a signal back and confirm a profile took effect.
- [Evasion techniques](evasion-techniques.md): User-Agent consistency, WebRTC leak protection, and what Pydoll gives you for free.
- [Human-like interactions](human-like-interactions.md): the behavioral layer.
