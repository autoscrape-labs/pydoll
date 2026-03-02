# Network Fingerprinting

Network fingerprinting identifies clients by analyzing characteristics of the TCP/IP stack, TLS handshake, and HTTP/2 connection. These signals are set by the operating system kernel and the TLS library, not by the browser's JavaScript environment, which makes them harder to spoof than browser-level fingerprints. A proxy or VPN changes your IP address but does not alter your TCP window size, your TLS cipher suite list, or your HTTP/2 SETTINGS frame. Detection systems exploit this gap.

!!! info "Module Navigation"
    - [Browser Fingerprinting](./browser-fingerprinting.md): Canvas, WebGL, AudioContext
    - [Evasion Techniques](./evasion-techniques.md): Multi-layer countermeasures

    For protocol fundamentals, see [Network Fundamentals](../network/network-fundamentals.md). For proxy detection context, see [Proxy Detection](../network/proxy-detection.md).

## TCP/IP Fingerprinting

Every operating system implements the TCP/IP stack differently. The SYN packet that initiates a TCP connection carries enough information to identify the OS with high confidence: the initial TTL, the TCP window size, the Maximum Segment Size, and the order and selection of TCP options. None of these values are controlled by the browser. They come from the kernel.

### TTL (Time To Live)

The initial TTL is one of the simplest OS identifiers. Linux and macOS set it to 64, Windows sets it to 128, and network devices (routers, firewalls) typically use 255. Each router hop decrements the TTL by one, so a packet arriving with TTL 118 likely started at 128 (Windows) and crossed 10 hops.

The fingerprinting value of TTL comes from cross-referencing it with the User-Agent. If the browser claims to be Chrome on Windows but the packet arrives with a TTL near 64, the connection is either proxied through a Linux server or the User-Agent is spoofed. Detection systems round the observed TTL up to the nearest known initial value (64, 128, 255) and compare it against the claimed OS.

When traffic flows through a proxy, the TTL resets because the proxy's kernel generates a new TCP connection to the target. The target sees the proxy's TTL, not yours. This is why TTL mismatches are a proxy detection signal: the User-Agent says Windows (TTL 128) but the TCP fingerprint shows Linux (TTL 64).

### TCP Window Size and Scaling

The initial TCP window size in the SYN packet varies by OS and kernel version. Modern Linux kernels (3.x and later) typically send an initial window of 29200 bytes, which is `20 * MSS` where MSS is 1460 for standard Ethernet. Some newer kernels (5.x, 6.x) may use 64240 depending on configuration and `initcwnd` settings. Windows 10 and 11 typically send 65535 with window scaling enabled, though the exact value depends on auto-tuning configuration and patch level. macOS also defaults to 65535.

The window scale factor (a TCP option) multiplies the 16-bit window size field to support larger receive windows. Linux commonly uses a scale factor of 7 (allowing windows up to 8MB), while Windows often uses 8. Combined with the base window size, the scale factor creates a more granular fingerprint than either value alone.

### TCP Options Order

The selection and ordering of TCP options in the SYN packet is highly distinctive. Each OS arranges options in a fixed, version-specific order that the kernel does not expose as a configurable parameter. Linux sends `MSS, SACK_PERM, TIMESTAMP, NOP, WSCALE`. Windows sends `MSS, NOP, WSCALE, NOP, NOP, SACK_PERM` and notably omits the TIMESTAMP option in default configurations. macOS sends `MSS, NOP, WSCALE, NOP, NOP, TIMESTAMP, SACK_PERM`.

The presence or absence of specific options matters as much as the order. Windows historically omitted TCP timestamps, which Linux and macOS include by default. SACK (Selective Acknowledgment) is supported by all modern systems, but older or embedded systems may not advertise it. The combination of which options appear and in what order creates a signature that tools like p0f match against a database of known OS fingerprints.

### p0f

[p0f](https://lcamtuf.coredump.cx/p0f3/) is the standard tool for passive TCP/IP fingerprinting. It observes traffic without generating any packets, analyzing SYN and SYN+ACK packets against a signature database. Its signature format encodes the key fingerprinting fields:

```
version:ittl:olen:mss:wsize,scale:olayout:quirks:pclass
```

The `ittl` is the inferred initial TTL, `mss` is the Maximum Segment Size, `wsize,scale` is the window size (which can be absolute, or relative to MSS like `mss*20`), and `olayout` is the TCP options layout using shorthand names (`mss`, `nop`, `ws`, `sok`, `sack`, `ts`, `eol+N`). The `quirks` field captures unusual behaviors like the Don't Fragment flag (`df`) or non-zero IP ID on DF packets (`id+`).

A typical Linux 4.x+ signature in p0f looks like `4:64:0:*:mss*20,7:mss,sok,ts,nop,ws:df,id+:0`. A Windows 10 signature might look like `4:128:0:*:65535,8:mss,nop,ws,nop,nop,sok:df,id+:0`. Anti-bot services maintain similar databases internally, matching incoming connections against known OS profiles and flagging mismatches with the declared User-Agent.

## TLS Fingerprinting

The TLS ClientHello message is transmitted before encryption is established, so it is visible to any observer on the network path. It contains the TLS version, supported cipher suites, TLS extensions, supported elliptic curves (named groups), and EC point formats. Each browser and TLS library produces a characteristic combination of these fields.

### JA3

JA3, developed at Salesforce by John Althouse, Jeff Atkinson, and Josh Atkins, was the first widely adopted TLS fingerprinting method. It concatenates five fields from the ClientHello (TLS version, cipher suites, extensions, elliptic curves, EC point formats), joins values within each field with hyphens, separates the five fields with commas, and takes the MD5 hash of the resulting string.

```
JA3 string: 771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0
JA3 hash:   cd08e31494b9531f560d64c695473da9
```

One subtlety: the "TLS version" field in JA3 uses `ClientHello.legacy_version`, not the `supported_versions` extension. Since TLS 1.3 (RFC 8446) requires clients to set `legacy_version` to `0x0303` (TLS 1.2) for backwards compatibility, the JA3 version field is almost always `771` for modern clients, even when they support TLS 1.3. The actual TLS 1.3 negotiation happens through extension 43 (`supported_versions`), but JA3 uses the header field.

JA3 must filter GREASE values before hashing. GREASE (RFC 8701) is a mechanism where browsers insert randomly selected reserved values into cipher suites, extensions, and other fields to prevent protocol ossification. The valid GREASE values are `0x0a0a`, `0x1a1a`, `0x2a2a`, and so on up to `0xfafa`. Each value has two identical bytes where the low nibble of each byte is `0x0a`. A correct GREASE filter checks both conditions:

```python
def is_grease(value: int) -> bool:
    return (value & 0x0f0f) == 0x0a0a and (value >> 8) == (value & 0xff)
```

!!! warning "JA3 Limitations with Modern Browsers"
    Since Chrome 110 (January 2023) and Firefox 114, browsers randomize the order of TLS extensions in every connection. This means the same browser produces different JA3 hashes on every connection, making JA3 effectively useless for identifying modern browsers. JA3 remains useful for fingerprinting non-browser clients (Python `requests`, `curl`, custom bots) that do not implement extension randomization.

### JA4

JA4 is the successor to JA3, developed by the same lead author (John Althouse) at FoxIO. It was designed specifically to survive TLS extension randomization by sorting extensions and cipher suites before hashing. The format consists of three sections separated by underscores: `a_b_c`.

Section `a` is a human-readable string of metadata: the protocol (`t` for TCP, `q` for QUIC), the TLS version (`12` or `13`), whether SNI is present (`d` for domain, `i` for IP), the number of cipher suites (two digits), the number of extensions (two digits), and the first and last ALPN value (`h2` for HTTP/2, `00` if none). For example, `t13d1516h2` means TCP TLS 1.3 with SNI, 15 cipher suites, 16 extensions, and HTTP/2 ALPN.

Section `b` is a truncated SHA-256 hash of the sorted cipher suites. Section `c` is a truncated SHA-256 hash of the sorted extensions concatenated with the signature algorithms. Because both lists are sorted before hashing, extension randomization does not affect the output.

Cloudflare, AWS, and other major platforms have adopted JA4. The full JA4+ suite also includes JA4S (server fingerprinting), JA4H (HTTP client fingerprinting), JA4X (X.509 certificate fingerprinting), and JA4SSH (SSH fingerprinting). The specification and tools are available at [github.com/FoxIO-LLC/ja4](https://github.com/FoxIO-LLC/ja4).

### JA3S (Server Fingerprinting)

JA3S applies the same concept to the ServerHello message, but the format is simpler because the server selects a single cipher suite rather than offering a list. The JA3S string is `version,cipher,extensions` and its MD5 hash identifies the server's TLS implementation. Pairing JA3 (or JA4) with JA3S creates a bidirectional fingerprint: a specific client talking to a specific server produces a predictable JA3+JA3S pair, which is more distinctive than either fingerprint alone.

### How Proxies Interact with TLS Fingerprints

The type of proxy determines whether the TLS fingerprint is preserved. SOCKS5 proxies and HTTP CONNECT tunnels relay the TCP stream without terminating TLS, so the target server sees the original client's TLS fingerprint unchanged. This is the main advantage of these proxy types for fingerprint consistency.

MITM proxies (which terminate TLS and re-establish a new connection to the target) replace the client's TLS fingerprint with their own. The target sees the proxy software's cipher suites and extensions, not the browser's. If the proxy uses a standard TLS library like OpenSSL or BoringSSL with default settings, the fingerprint will not match any known browser, which is itself a detection signal.

This is why Pydoll's approach of using `--proxy-server` (which creates a CONNECT tunnel, preserving the browser's TLS fingerprint) is preferable to external MITM proxy setups for stealth automation.

## HTTP/2 Fingerprinting

HTTP/2 connections expose a separate set of fingerprinting signals that are distinct from TLS. The first frame sent by the client is a SETTINGS frame containing parameters like `HEADER_TABLE_SIZE`, `ENABLE_PUSH`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE`, `MAX_FRAME_SIZE`, and `MAX_HEADER_LIST_SIZE`. Each browser uses different default values and includes different subsets of these parameters.

Beyond SETTINGS, the WINDOW_UPDATE frame size, the priority/weight of the initial stream, and the order of HTTP/2 pseudo-headers (`:method`, `:authority`, `:scheme`, `:path`) vary between implementations. Chrome, Firefox, and Safari each produce a distinctive combination of these values.

Akamai published the foundational research on HTTP/2 fingerprinting at Black Hat Europe 2017. Their fingerprint format concatenates the SETTINGS values, WINDOW_UPDATE size, PRIORITY frames, and pseudo-header order. The JA4+ suite includes `JA4H` for HTTP-level fingerprinting, covering header order and values.

HTTP/2 fingerprinting is particularly effective against automation tools because many bot frameworks and HTTP libraries implement their own HTTP/2 stacks with default parameters that do not match any real browser. Even when a tool correctly spoofs the TLS fingerprint (using curl-impersonate or similar), its HTTP/2 SETTINGS frame may betray it.

You can check your HTTP/2 fingerprint at [browserleaks.com/http2](https://browserleaks.com/http2). Because Pydoll controls a real Chrome instance via CDP, the HTTP/2 fingerprint is always authentic, which is an inherent advantage over tools that construct HTTP requests programmatically.

## Implications for Browser Automation

The practical takeaway for automation with Pydoll is that network fingerprinting is one area where controlling a real browser provides a significant advantage. Chrome's TCP/IP stack, TLS implementation (BoringSSL), and HTTP/2 stack produce authentic fingerprints by default. The main risk is environmental mismatch: running Chrome on a Linux server while the User-Agent claims Windows creates a TCP/IP fingerprint inconsistency (TTL 64 instead of 128, Linux TCP options order instead of Windows).

For proxy-based setups, the fingerprint flow is: your machine's TCP/IP stack generates the connection to the proxy (which the proxy's operator can see but the target cannot), and the proxy's TCP/IP stack generates the connection to the target. The target sees the proxy server's TTL and TCP options. If the proxy runs Linux (as most do), the TCP fingerprint will indicate Linux regardless of the User-Agent. This is a well-known detection signal that residential proxies partially mitigate (the proxy endpoint is a real user's machine, so its TCP fingerprint is plausible) but datacenter proxies cannot.

The TLS and HTTP/2 fingerprints, on the other hand, pass through SOCKS5 and CONNECT tunnels unmodified. These are the browser's fingerprints, not the proxy's. So with Pydoll through a CONNECT tunnel, the target sees authentic Chrome TLS and HTTP/2 fingerprints paired with the proxy's TCP/IP fingerprint. This combination is consistent with a real user browsing through a VPN or corporate proxy, which is a common and legitimate pattern.

## References

- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- FoxIO JA4+ Network Fingerprinting - https://github.com/FoxIO-LLC/ja4
- Cloudflare: JA4 Signals - https://blog.cloudflare.com/ja4-signals/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- p0f v3: Passive OS Fingerprinting - https://lcamtuf.coredump.cx/p0f3/
- RFC 8446: TLS 1.3 - https://datatracker.ietf.org/doc/html/rfc8446
- RFC 8701: GREASE for TLS - https://datatracker.ietf.org/doc/html/rfc8701
- RFC 6528: Defending against Sequence Number Attacks - https://datatracker.ietf.org/doc/html/rfc6528
- BrowserLeaks HTTP/2 Fingerprint - https://browserleaks.com/http2
- Stamus Networks: JA3 Fingerprints Fade as Browsers Embrace Extension Randomization - https://www.stamus-networks.com/blog/ja3-fingerprints-fade-browsers-embrace-tls-extension-randomization
