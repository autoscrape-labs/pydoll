# Fingerprinting

Fingerprinting is how a site identifies a browser without cookies or an IP address, by reading characteristics the connection exposes on its own. On their own each characteristic looks harmless; combined, they identify a device or a browser instance, and they reveal automation when the pieces don't fit together.

This section is the theory behind the [Stealth](../../stealth/index.md) guides. You don't need it to stay undetected in practice, but it explains what a detection system actually measures and why a single mismatch gives you away.

## Detection happens across three layers

A request is fingerprinted at three levels, and modern anti-bot systems correlate all of them:

- **Network**: the TCP/IP stack, the TLS handshake, and HTTP/2 settings, all read before any JavaScript runs.
- **Browser**: canvas and WebGL rendering, fonts, audio, and `navigator` properties, read once the page loads.
- **Behavioral**: mouse movement, keystroke timing, and scroll patterns, read as you interact.

The layers are cross-checked. A Chrome User-Agent riding a Firefox TLS fingerprint, or a flawless browser fingerprint with robotic mouse movement, is caught by anything that compares signals. Consistency across all three matters more than perfection in any one.

!!! note "The core rule"
    Every layer has to tell the same story. If your TLS fingerprint says Chrome 120, then your HTTP/2 settings, your User-Agent, and your rendered canvas all have to say Chrome 120 too. One contradiction is enough to flag the session.

## The three layers in depth

- [Network fingerprinting](network-fingerprinting.md): identification at the transport and session layers, before rendering. TCP/IP (TTL, window size, option order), TLS (JA3/JA4, cipher suites, ALPN), and HTTP/2 (SETTINGS, priorities). The hardest layer to change, because it comes from the OS and the real binary.
- [Browser fingerprinting](browser-fingerprinting.md): identification through JavaScript APIs and rendering. Canvas and WebGL artifacts from the real GPU, audio, font enumeration, and `navigator` properties. This is where most detection events land.
- [Behavioral fingerprinting](behavioral-fingerprinting.md): identification from how you interact. Mouse trajectory and velocity, keystroke rhythm, and scroll dynamics, sometimes scored by models trained on large behavioral datasets. It can catch automation even when the other layers are clean.

## Related

This section explains detection. For what Pydoll does about it and the levers you control, see the Stealth guides:

- [Evasion techniques](../../stealth/evasion-techniques.md): what Pydoll gives you for free and how to keep the layers consistent.
- [Fingerprint injection](../../stealth/fingerprint-injection.md): applying a coherent identity across layers.
- [Human-like interactions](../../stealth/human-like-interactions.md): the behavioral layer.

!!! warning "No layer makes you undetectable"
    Fingerprinting knowledge narrows the gap; it does not close it. Getting one layer right while another contradicts it is worse than an unmodified browser. Use this to understand what you are up against, not as a guarantee.
