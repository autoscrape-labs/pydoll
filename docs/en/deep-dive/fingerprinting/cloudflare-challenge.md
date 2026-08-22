# Cloudflare's managed challenge

Cloudflare's managed challenge, the "Just a moment…" interstitial, is the strictest real-world test of a fingerprint. It correlates every layer at once and decides on its own server, so it catches contradictions a single-page bot score misses. This page is a full case study: the pass/block matrix, why each mismatch is caught, and a reverse-engineering pass on the one row a perfect fingerprint still fails, headless.

It applies [network](network-fingerprinting.md) and [browser](browser-fingerprinting.md) fingerprinting and [the limits of spoofing](spoofing-limits.md) to a live target. Read those for the mechanisms; read this for how they combine, and where they run out.

## The controlled test

One machine, one Chrome 151 binary, one residential IP. The only things that change between runs are the profile and the headless flag; [`apply_fingerprint()`](../../stealth/fingerprint-injection.md) is applied before navigating.

| Profile | Mode | UA Chrome major | Result |
|---|---|---|---|
| macOS (matches the host) | headful | 151 (matches the binary) | passes |
| macOS | headless | 151 | blocked |
| macOS | headful | 140 (mismatched) | blocked |
| Windows (mismatched OS) | headful | 151 | blocked |
| Windows | headless | 151 | blocked |

Only the fully-consistent, headful run passes. Every other row is a single deviation, and each is caught by a different layer.

## The OS must match the host

A Windows profile on a Mac is blocked even in headful, because the OS leaks through paths `apply_fingerprint()` cannot touch:

- **Fonts.** The profile's font list is a JavaScript value, but `measureText` and element sizing render through the real OS font engine. A "Windows" browser with no Segoe UI or Calibri, and with Helvetica Neue present, is a Mac.
- **Rasterization.** Canvas and WebGL text draw through CoreText on macOS, DirectWrite on Windows, FreeType on Linux. The pixels differ, so the hash betrays the real OS. This is the [hard floor](spoofing-limits.md): a rendered signal no override reaches.
- **The TCP/IP stack.** The kernel sets the initial TTL (64 on macOS and Linux, 128 on Windows) and other options the browser cannot change. Cloudflare reads them passively at the edge (see [Network fingerprinting](network-fingerprinting.md)).

The client-side font leak alone is enough; the TCP signal is the floor underneath it.

## The Chrome version must match the binary

A User-Agent that claims Chrome 140 on a 151 binary is blocked, because the version leaks through the engine, not just the string.

Declare Chrome 110 and the feature surface still answers to 151: `Promise.withResolvers` (added in Chrome 119), `Array.fromAsync` (121), and `Uint8Array.prototype.toBase64` (140+) are all present. One API newer than the version you claim exposes the lie. The engine leaks it a second way: `Math` precision to the last bit, error-message text, and syntax support change between V8 versions, so two Chrome builds produce different `Math` fingerprint hashes. The string is spoofable; the engine behind it is not.

These two rows are [the limits of spoofing](spoofing-limits.md) in practice. The third, headless, is different, and it is worth the rest of this page.

## Anatomy of the headless block

Under a matched profile, headful and headless look identical across the tools and signals below. That is the puzzle: the challenge passes one and blocks the other, though these read the same. Everything in this table was measured directly, identical between the two runs:

| Signal | headful vs headless |
|---|---|
| CreepJS full report | byte-identical (same hashes, "0% headless") |
| Canvas / WebGL / audio hashes | identical (real GPU; SwiftShader is not used on macOS) |
| WebGL renderer, WebGPU adapter | identical (Apple Metal) |
| Widevine / EME, codecs (H.264 / AAC / HEVC) | identical |
| `navigator.*`, plugins, permissions, `isUVPAA` | identical |
| 40+ flat window / navigator signals | identical |

`navigator.webdriver` is false, there is no `--enable-automation`, and Pydoll never calls `Runtime.enable`, so the classic CDP tells are absent too. Whatever separates the two runs is below the layer these tools read.

### The plausible leaks, and why they are dead ends

Two signals do differ. Both are worth recording so you do not chase them:

| Signal | headful | headless | fix tried | still blocked? |
|---|---|---|---|---|
| `matchMedia('(color-gamut: p3)')` | true | false | `setEmulatedMedia` / `--force-color-profile` | yes |
| `matchMedia('(dynamic-range: high)')` | true | false | `setEmulatedMedia` | yes |
| `requestAnimationFrame` interval | 8.3ms (120Hz) | 16.7ms (60Hz) | `--disable-gpu-vsync` (no effect) | yes |

The display-media pair is real: a headless virtual display reports sRGB and SDR. Forcing both to match changes nothing. The frame cadence is the "no real display" signature: with no surface to present to, Chrome's compositor falls back to a synthetic 60Hz source (`BeginFrameArgs::DefaultInterval()`, one 60th of a second), where a ProMotion Mac runs 120Hz. But 60Hz is what most real machines report, so cadence alone cannot be the discriminator, and it cannot be raised without a display. All three are consequences of the same root, no presented surface, and none is the deciding signal.

### Reverse-engineering what the challenge reads

To stop guessing, instrument what the challenge actually touches. Register a probe with `Page.addScriptToEvaluateOnNewDocument` (it runs before the challenge's own code) that wraps `matchMedia`, `requestAnimationFrame`, `performance.now`, canvas, WebGL `getParameter`, and the suspect `screen` / `navigator` getters, and record every access.

On the challenge page the main thread reads almost nothing: one `matchMedia('(prefers-color-scheme: dark)')` and a handful of `Date.now`. The work happens elsewhere. Hooking `URL.createObjectURL` catches it: the challenge spawns two Web Workers from blobs, and their source is a small bootstrap.

```js
var _p = self.trustedTypes.createPolicy('Kssz2', { createScript: s => s });
onmessage = e => e.isTrusted && e.origin === '' && e.source === null
                 && eval(_p ? _p.createScript(e.data) : e.data);
```

The worker is an eval sink: the real detection code is sent to it from the main thread and run inside the worker, off the instrumentable page. To read it, attach a CDP session to the worker target (`Target.setAutoAttach` with `waitForDebuggerOnStart`), enable `Debugger`, and capture every parsed script with `Debugger.scriptParsed` and `Debugger.getScriptSource`; or hook `self.eval` in the worker before resuming it.

Doing that reveals the twist. On the blocked headless path the worker is never fed. It parses only its own bootstrap and sits idle (no inbound message, no eval'd payload). Cloudflare does not send the second-stage collector once the first-stage telemetry has already failed the client. The worker is the stage after the verdict, not the detector. This is why hooking the main-thread `postMessage` catches nothing, and why the challenge reads as a black box to ordinary JavaScript instrumentation.

### The real client leak: cross-origin iframe geometry

The challenge renders inside a cross-origin iframe on `challenges.cloudflare.com`, an out-of-process iframe (OOPIF) with its own renderer process and its own CDP session. Page-injected scripts and `setDeviceMetricsOverride` never reach it, which is the layer every earlier probe missed. Attach to the OOPIF's own session and read its `window.screen` directly, and the leak is there:

| Read inside the OOPIF | headless | headful |
|---|---|---|
| `screen.width × height` | 800 × 600 | 1440 × 900 |
| `screen.availTop` | 0 | 25 |
| `devicePixelRatio` | 1 | 2 |

800x600 with `availTop` 0 is Chrome's hardcoded headless virtual screen: no window manager, impossible for the claimed Mac, and in direct contradiction with the top page, which reports the profile's 1440x900. `setDeviceMetricsOverride` fixed the top page but is session-scoped; the iframe never saw it.

Pydoll closes this with `Emulation.updateScreen` on the browser-global virtual screen, which every frame reads, OOPIFs included (see [Fingerprint injection → Headless mode](../../stealth/fingerprint-injection.md#headless-mode)). After it, the iframe reports the same 1440x900 / `availTop 25` / dpr 2 as the page. The one catch is that the virtual screen accepts only an integer `devicePixelRatio`, so a fractional dpr is rounded for the iframe.

### The wall: a server-side verdict

Make the OOPIF geometry byte-perfect, matching the page on every field, and the challenge still blocks. So the geometry was a real leak but not the deciding one.

The verdict is not a client value you can read or override. The first-stage script on the challenge page is a ~226KB string-table VM interpreter: its config lives in `_cf_chl_opt`, it carries a XOR decryptor (`o[i] = k[i] ^ s.charCodeAt(i % s.length)`), base64 blobs, and whitespace-padded `honk` canary scripts. It collects its telemetry, encrypts it, and POSTs it to `/cdn-cgi/challenge-platform/h/b/fo/<numbers>:<ray>/<token>`; Cloudflare scores it server-side and re-serves the interstitial with a fresh Ray ID on a fail. The payload is opaque, so the deciding input cannot be isolated from the client without breaking the encryption.

What survives a flawless client fingerprint is something the browser produces only with a real display, a compositor or frame-timing trait, or a behavioral one, computed inside that rotating obfuscated payload. That is as far as client-side reverse engineering reaches.

**The honest conclusion:** headless Chrome does not clear the managed challenge, even with a perfect fingerprint. The reliable fix is a real display, run headful, or headful under a virtual framebuffer (Xvfb) on a server. Every serious stealth project converges on the same answer.

!!! warning "The screen fix is a hardening, not a bypass"
    `updateScreen` removes a genuine cross-frame leak, and it helps against detectors that read screen geometry in iframes. It does not pass Cloudflare's managed challenge on its own. Nothing at the fingerprint layer does; the deciding signal lives below it.

## What actually works

- **Match the host and the binary.** OS equals the host OS, Chrome major equals the binary major.
- **Match locale, timezone, and geolocation to the egress IP.** A separate consistency check the challenge also runs (see [Locale/IP mismatch](../../stealth/fingerprint-injection.md#case-study-a-locale-mismatch-triggering-googles-captcha)).
- **Use a display for managed challenges.** Headful, or headful under Xvfb on a server. Displayless headless is a losing configuration here.
- **Treat injection as necessary, not sufficient.** It removes the contradictions you can fix. IP reputation and the display requirement are not among them.

## Reproducing this

The reverse-engineering pass above is a method you can rerun on any challenge:

- **A/B on one variable.** Change only the headless flag, or one profile field, between runs and diff the outcome. Attribute a block to a signal instead of guessing.
- **Instrument the client, everywhere it runs.** `Page.addScriptToEvaluateOnNewDocument` before navigation logs main-thread API access; `URL.createObjectURL` hooks catch blob workers; a CDP session per worker and per cross-origin OOPIF reaches the code that page-injected scripts do not, since neither inherits them.
- **Read the OOPIF on its own session.** The challenge lives in a cross-origin iframe; its `window.screen` and every other read are visible only through its own target.
- **Measure, do not assume.** [Auditing a fingerprint](auditing.md) covers the read-two-paths method that turns "it is blocked" into "this exact field leaks".

## Related

- [The limits of spoofing](spoofing-limits.md): what a spoof can and cannot move.
- [Network fingerprinting](network-fingerprinting.md): the TCP and TLS layers Cloudflare reads at the edge.
- [Browser fingerprinting](browser-fingerprinting.md): the fonts, canvas, and GPU signals that carry the OS.
- [Auditing a fingerprint](auditing.md): measure which of your signals leak before you point them at a challenge.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): applying a coherent profile.
