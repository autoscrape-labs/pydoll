# GPU, containers and what a profile cannot reach

A fingerprint profile changes what the browser *reports*. It cannot change what the host *computes*. Every GPU signal exists in both forms, and the split between them decides what a given host can claim, why a Mac that names another vendor's card is a different case from a container with no GPU, and what Xvfb does and does not change.

It applies the rule of [The limits of spoofing](spoofing-limits.md), a string can be moved but rendered output stays real, to one question: what hardware may this host claim? It expands the [container paragraph](../../stealth/fingerprint-injection.md#containers) of the injection guide.

!!! warning "Everything here depends on the target"
    There is no silver bullet. Each site reads its own subset of signals and weighs it its own way: the passive collectors traced in [Auditing a fingerprint](auditing.md#what-passive-collectors-read) never read the GPU at all, while a commercial fingerprinting agent hashes it. Every statement below of the form "a detector sees X" means "a detector that reads X sees it". Before spending on fonts, proxies or a GPU instance, trace what the target actually reads; a contradiction nobody reads costs nothing, and a signal you never thought of may be the one that decides.

## Reported and computed

| Layer | Examples | Reached by the profile |
|---|---|---|
| Reported | renderer string, WebGL limits and extensions, shader precision, WebGPU `adapter.info`, limits, features | yes: the `webgl` and `webgpu` sections replace it |
| Computed | rendered pixels (the hash of a test scene), compute results, their timing, the no-caveat context check | no: the hardware executes it |

The reported layer is replaced on the real prototypes with the native brand checks intact (see [Fingerprint injection](../../stealth/fingerprint-injection.md#native-first)). The computed layer is what [The limits of spoofing](spoofing-limits.md) calls the hard floor: a render hash is the hash of the pixels a test scene draws, and the no-caveat check is `getContext('webgl', {failIfMajorPerformanceCaveat: true})`, a context Chrome grants only when it considers the renderer fast enough.

A detector that reads only the reported layer sees whatever the profile says. A detector that reads the computed layer sees the host. What it can conclude from that depends on what the host is.

## Another vendor's GPU: a bet on the target's reference data

Take this branch's measured case: an Apple M4 running the Windows profile, which names an NVIDIA card in both sections. The reported layer is coherent, NVIDIA everywhere. The computed layer is a real GPU: hardware anti-aliasing, hardware precision, a render finished in hardware time. On its own that output says nothing except "a GPU drew this". To turn it into a contradiction, the detector needs a reference: "an RTX 3060 on Windows produces hash X and takes Y milliseconds". Compared against that, the M4's output does not match.

Only a detector holding per-card reference data can catch the lie. Castle documents string cross-checks (the renderer against the User-Agent OS); a hash-versus-reference comparison is what a commercial fingerprinting agent could do with the render hashes it collects, and no public source shows one doing it per card. The passive reads of reCAPTCHA and hCaptcha, [traced](auditing.md#what-passive-collectors-read), never touched WebGL or WebGPU, and a Windows profile on this Mac cleared a typed Google search once.

The computed output never says "automation" or "container" by itself, because it is genuine hardware output; headless and headful on this Mac measured identical on every GPU signal. So a profile of another vendor's GPU on a real GPU is a calibrated bet: it passes anyone reading values and consistency between values, and fails anyone comparing rendered output with a database of cards. The profile of the host's own GPU is always the stronger one, because both layers agree with no reference needed.

## No GPU: a contradiction with no reference needed

Here the computed layer is recognisable on its own. Without a GPU, current Chrome either creates no WebGL context (the SwiftShader fallback has been removed since Chrome 139 and needs `--enable-unsafe-swiftshader` on current builds) or renders through SwiftShader, Chrome's CPU rasterizer. Measured on Chrome 152 with the GPU disabled:

- The no-caveat context is refused when Chrome fell back to SwiftShader, which no discrete card does. Choosing SwiftShader explicitly with `--use-angle=swiftshader` still grants it, so this is the GPU-less case, not a property of SwiftShader.
- The render hash is the same on every GPU-less Chrome of the same build, whatever the CPU, a value any detector that keeps a table of them recognises.
- A rendered scene takes CPU time: a trivial scene measured tens of times slower than the M4.
- `navigator.gpu.requestAdapter()` resolves `null` without the flags below, so the `webgpu` section has no adapter to attach its values to.

A profile that names a discrete card on such a host contradicts each of those without anyone needing to know what the card would have produced. That is the difference from the Mac: the Mac's computed layer only betrays the profile to a detector with a reference; the container's betrays it to a one-line check.

### Telling a software story instead

What a container really is, a software-rendered browser, is also what millions of real sessions are. Windows on virtual desktops (VDI, Citrix, cloud VMs) renders through the Microsoft Basic Render Driver (Windows' own CPU rasterizer, WARP), and Chrome there reports a renderer of the form `ANGLE (Microsoft, Microsoft Basic Render Driver (0x0000008C) Direct3D11 vs_5_0 ps_5_0, D3D11-10.0.19041.5794)`. Chromium classes WARP as software rendering, so a refused no-caveat context and a `null` WebGPU adapter are expected there too; that pair is still to be confirmed on a Windows VM. Software renderers score as suspicious in their own right, but they describe real machines; a discrete card on a software host describes none.

The values of such a profile (WebGL limits, extensions, the precision table) have to be captured on a real Windows VM, the same rule as every other profile. The remaining gap is the render hash: SwiftShader and WARP draw differently, so a detector with a reference for WARP still sees the difference. That is score-level, not a contradiction.

### Making the APIs exist

`--enable-unsafe-swiftshader` gives the page a WebGL context to read; a desktop with no WebGL at all is rarer than one with a software renderer. `--enable-unsafe-webgpu --use-webgpu-adapter=swiftshader` exposes a software WebGPU adapter that reports vendor `google`, architecture `swiftshader` and `adapter.info.isFallbackAdapter` true, for the `webgpu` section to attach to (set `is_fallback_adapter` in the profile to what the claimed device reports, or the flag stays visible). Together they give detectors that read parameters and existence something coherent to read. They change nothing in the rendered output, and combining them with a hardware GPU claim recreates the contradiction above.

## Xvfb removes the display signals, not the GPU ones

Xvfb (a virtual X display with no screen attached) gives Chrome a display, so the browser runs headful: there is a presented surface (the presentation term, Cloudflare's signal for a browser drawing to a real display, weighed on a marginal IP in [Cloudflare's managed challenge](cloudflare-challenge.md)), `screen` is the virtual display you configure, the window has real chrome and Linux scrollbars, and input can come from the operating system (`xdotool`) instead of the DevTools protocol. The signals that come from having no display go away; what a given target makes of that is its own scoring.

It adds no GPU. Xvfb is a framebuffer in memory; rendering stays SwiftShader or Mesa's llvmpipe (Linux's CPU rasterizer), a software renderer just as recognisable in the renderer string. The kernel, the fonts and the egress IP are unchanged too.

## The order of value on a server

1. **A clean residential egress IP.** Read before any script runs, and nothing below compensates for it on a target that weighs IP reputation, which is most of them.
2. **A profile that matches what the host computes.** On a GPU host, the host's own GPU vendor; on a GPU-less host, a software-rendered Windows story rather than a discrete card.
3. **APIs that exist.** The SwiftShader flags above, and `--use-fake-device-for-media-stream` so Chrome itself exposes a microphone, camera and speaker.
4. **Fonts of the claimed OS installed**, and `available_fonts` listing exactly those; a colour emoji font of that OS too.
5. **Xvfb** when the target weighs presentation.
6. **The kernel.** A Linux SYN under a Windows User-Agent is read at the edge ([Network fingerprinting](network-fingerprinting.md)); a proxy exit on the claimed OS is the only clean fix, and whether a target weighs the SYN is still an open measurement.
7. **A real GPU.** A GPU instance (T4/L4 class) is the only thing that makes the render hash, the WebGPU adapter and the timing genuine; with the same vendor the profile names, the reported and computed layers finally agree.

!!! note "A model, not a verdict"
    The first and the last item are supported by the literature and the measurements; the order of the middle depends on the target. A site that never reads WebGL is not helped by a GPU instance, and a site that hashes it is not fooled by anything short of one. Measure the target first, and expect two targets to disagree.

## Related

- [The limits of spoofing](spoofing-limits.md): the general rule this page applies to hardware.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): applying the `webgl` and `webgpu` sections.
- [Auditing a fingerprint](auditing.md): reading what a target actually collects.
- [Cloudflare's managed challenge](cloudflare-challenge.md): the presentation term and the headless case.
