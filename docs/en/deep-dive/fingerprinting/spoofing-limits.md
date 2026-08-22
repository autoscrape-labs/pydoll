# The limits of spoofing

Fingerprint injection changes what the browser reports, but not every signal can be changed, and forcing the wrong one makes you easier to detect, not harder. This page draws the line: which signals a spoof moves cleanly, which it cannot move at all, and why overriding the ones it cannot leaves a contradiction a detector reads instantly.

It is the theory behind the [Fingerprint injection](../../stealth/fingerprint-injection.md) checklist. Read that first for the practical steps; read this to understand why the checklist is shaped the way it is.

## Native overrides read as the truth

A browser signal often has more than one read path. `matchMedia('(color-gamut: p3)')` and a CSS `@media (color-gamut: p3)` rule ask the same question, and the answer comes from the same place: the rendering engine, in C++, below the JavaScript you can reach.

That is what splits a good override from a detectable one:

- A **native override** changes the value at the engine. Pydoll applies these through the CDP `Emulation` domain, for the User-Agent, timezone, screen, locale, `hardwareConcurrency`, and the CSS media features. Every read path then returns the new value, and they agree. There is no JavaScript wrapper to inspect.
- A **JavaScript override** wraps one API, a `navigator` getter or `matchMedia`. It changes that one path. Any other path that reads the same signal still returns the real value.

A media feature lives in the engine's `MediaValues`, and both read paths resolve against it. Toggle the override type below to see which paths each one reaches:

<iframe src="/docs/resources/visuals/media-read-paths.html" aria-label="A CDP override edits the engine's MediaValues so matchMedia and the CSS cascade both change; a JavaScript override wraps only matchMedia, leaving the CSS path reading the real value" style="width: 100%; height: 430px; border: 0;" loading="lazy"></iframe>

A CDP override edits `MediaValues`, so `matchMedia` and the `@media` cascade both return the new value. A JavaScript override replaces the `matchMedia` function; the cascade never calls it, so CSS keeps resolving against the real `MediaValues`. That gap is the contradiction.

The demo below runs on your own display. Both cards read your real `dynamic-range` and agree. Apply a JavaScript override and only `matchMedia` lies; the engine's `@media` rule keeps reporting the truth.

<iframe src="/docs/resources/visuals/js-override-lie.html" aria-label="matchMedia and a CSS @media rule read the same dynamic-range; a JavaScript override makes only matchMedia lie while the CSS path stays truthful" style="width: 100%; height: 340px; border: 0;" loading="lazy"></iframe>

This is exactly why Pydoll does not spoof `dynamic-range`. Chrome keeps a fixed allowlist of overridable media features. In Blink's `MediaFeatureOverrides::SetOverride`, seven names are handled, `color-gamut`, `prefers-color-scheme`, `prefers-contrast`, `prefers-reduced-motion`, `prefers-reduced-data`, `prefers-reduced-transparency`, and `forced-colors`, and any other name falls through and changes nothing. `dynamic-range`, `inverted-colors`, and `monochrome` have no branch there, so the CDP command is accepted and silently dropped. It is a missing code path in the engine, not a value-format problem.

Pydoll exposes six of the seven. The odd one out is `prefers-reduced-data`: it is in the allowlist but shipped disabled in Chrome, so `matchMedia` reports no match for any value, and setting it would claim something a real Chrome never returns. The only lever left for the unlisted features is JavaScript, which can lie on one path only, so Pydoll leaves `dynamic-range` real and asks you to match `color-gamut` to it instead.

!!! note "When a JavaScript override is safe"
    Pydoll does use JS overrides, for `deviceMemory`, WebGL strings, plugins, and more. They are safe because CDP cannot reach those signals **and** no second read path contradicts them, and each is hardened to survive `toString`, prototype, and worker inspection (see [Detecting JavaScript overrides](../../stealth/fingerprint-injection.md#detecting-javascript-overrides)). The rule: a JS override is safe only when it is the single source of truth for that signal.

## The hard floor: signals no override can fake

Some signals are not a value the browser stores. They are the output of a computation the detector runs on your real hardware, then hashes:

- **Canvas** draws set text and shapes to an offscreen canvas, reads the pixels back with `getImageData`, and hashes them. The sub-pixel anti-aliasing depends on the GPU, the driver, and the OS text renderer, so the hash is stable on one machine and differs across machines.
- **Audio** renders a tone through an `OfflineAudioContext`, an oscillator into a `DynamicsCompressorNode`, reads the output with `getChannelData`, and hashes it. The floating-point DSP result varies by platform.
- **WebGL and WebGPU** render a scene, hash the image, and time how long the GPU took.

There is no CDP override for any of these, and a JavaScript override cannot reach the hashed output, only the API around it. Chrome even exposes a WebAudio domain in the DevTools Protocol, but it only observes the audio graph; it has no command to rewrite the samples. Not even the protocol can move this layer.

The naive escape, hooking the readback API to add noise so the hash changes on every read, is itself the tell. A standard check renders the same canvas twice and compares: a real GPU returns byte-identical pixels both times, so a value that differs between two reads is a JavaScript hook, and that instability flags the session more clearly than a stable real hash ever would.

!!! warning "Do not add canvas or audio noise"
    A stable real fingerprint is less suspicious than one that flickers between reads. Randomizing canvas or audio output marks the session as automated instead of hiding it.

What these signals expose is *which machine*, not *that it is a bot*. For a scraper that means they matter for linking your sessions to each other across runs, not for a single bot verdict. The only way to make them coherent with a claimed device is to run on that hardware.

## A spoof is only as strong as its weakest layer

A fingerprint is read across layers and correlated. Overriding one layer while another still reports the truth is a contradiction, and a contradiction scores worse than an unmodified browser.

Take a GPU. Pydoll overrides the WebGL renderer string, so a profile can name an NVIDIA card, but it does not touch WebGPU. Applying the Windows profile on this host (Apple M3, Chrome 151) and reading both APIs, measured:

| Signal | Reads | Comes from |
|--------|-------|------------|
| WebGL renderer string | `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 ...)` | the override |
| WebGPU adapter vendor | `apple` | the real GPU |
| WebGPU `maxBufferSize` | `4294967292` | the real GPU |
| WebGPU `maxComputeWorkgroupStorageSize` | `32768` | the real GPU |
| Canvas hash, this profile vs the macOS profile | identical | the real GPU |

WebGL says NVIDIA; WebGPU, its limits, and the canvas all say Apple. The override moved one string and left every other rendered and reported signal describing the real GPU, so a Windows profile on Apple hardware contradicts itself. A half-spoofed GPU is more detectable than the real one.

### Why Pydoll leaves WebGPU alone

You could try to close that gap by spoofing WebGPU to match, the vendor string and then the roughly thirty adapter limits. Pydoll built exactly that and reverted it. Each limit has to be a physically real value for the card you claim, the same constraint that makes a wrong WebGL parameter a tell; real per-GPU limit sets are not published, so you would be guessing; the list changes with Chrome releases; and even a perfect set cannot move the GPU-timing hash, which is rendered, not reported.

So the honest engineering call was to not spoof that layer at all. Chasing a coherence you cannot maintain trades a small, fragile gain for a large upkeep cost and a fresh way to get caught. Pydoll overrides the WebGL renderer string and leaves WebGPU and the rendered output real, which means the profile has to name the GPU family that is actually present.

This is why the [Fingerprint injection checklist](../../stealth/fingerprint-injection.md#checklist) insists the profile OS and GPU match the host. You can move a string, but the rendered output stays real, so the string has to describe the hardware that is actually there.

### The OS is the one you cannot move

The clearest signal you can only match, never fake, is the operating system. Set the User-Agent, `navigator.platform`, and Client Hints and the browser says Windows at once, but the OS leaks through layers no override reaches, and through more than one at the same time.

The decisive one is the kernel's TCP/IP stack. Every connection's SYN packet carries the initial TTL (64 on macOS and Linux, 128 on Windows), the TCP window size and scale, and the option order, all set by the host kernel before any JavaScript runs. A Windows User-Agent arriving over a TTL-64 connection is a contradiction read at the transport layer, and no CDP or JavaScript override touches it. [Network fingerprinting](network-fingerprinting.md) covers this stack in depth; it is why a Windows profile on a Mac fails Cloudflare's managed challenge.

Rendering carries the OS too, so canvas is part of the answer. Canvas and fonts draw through the OS text renderer, CoreText on macOS, DirectWrite on Windows, so a Mac-rendered canvas under a Windows profile already describes the wrong OS. But that leak is not the profile's doing and not spoofable: the same canvas hashed to `d65506c6...` under both the Windows and macOS profiles on this Mac, while `navigator.platform` read `Win32` and `MacIntel`. The canvas is the real Mac's either way, a rendered signal from the [hard floor](#the-hard-floor-signals-no-override-can-fake). The kernel's TCP/IP stack underneath leaks the OS a second time, and is just as untouchable. How a real challenge weighs these, layer by layer, is in the [Cloudflare case study](cloudflare-challenge.md).

A forwarding proxy is the one lever. It re-originates the TCP connection from the proxy's kernel, so the observed OS becomes the proxy host's. A Windows profile then needs a proxy running on Windows; a Linux proxy gives a Linux signature and the contradiction returns.

!!! note "The one rule under all of this"
    Match the profile to the host. Never claim hardware or an OS you do not have. Every rule in the checklist is a special case of it.

## What you can actually move

The signals you can change cleanly are the ones a native override reaches, or that a JavaScript override can own without a second path contradicting it: identity (User-Agent, platform, Client Hints), timezone, locale, screen, `hardwareConcurrency`, `deviceMemory`, and the CSS media features. Make those coherent with each other and with your IP and OS.

The hard floor, canvas and audio and GPU, you make coherent only by running on real, matched hardware. Everything in between is a trade that can backfire, so spend the effort on consistency, not on faking more.

## Related

- [Fingerprint injection](../../stealth/fingerprint-injection.md): the practical guide to applying a coherent profile.
- [Browser fingerprinting](browser-fingerprinting.md): the detection surface these overrides touch.
- [Auditing a fingerprint](auditing.md): measure which of your signals leak, and see what a real commercial detector reads.
