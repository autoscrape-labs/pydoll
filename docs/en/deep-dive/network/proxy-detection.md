# Proxy detection

Proxy detection is probabilistic: a site combines dozens of weak signals, from a simple IP reputation lookup to TCP/IP stack analysis, into a confidence score. No single signal is proof, but enough of them together produce a high-confidence decision. This page covers the main techniques, how they work, and what they mean for automation.

It builds on the rest of the network section: [Network fundamentals](network-fundamentals.md) for the layers involved, and [HTTP/HTTPS proxies](http-proxies.md) and [SOCKS proxies](socks-proxies.md) for how each proxy type behaves.

## IP reputation

IP reputation is the most widely deployed technique. It combines public data (ASN records, WHOIS, geolocation databases) with proprietary intelligence to sort IP addresses into risk categories.

### ASN classification

Every IP belongs to an Autonomous System, identified by an ASN, and the type of AS that owns an IP is the single strongest indicator of whether it is a proxy.

IPs from cloud and hosting providers (AWS, DigitalOcean, OVH, Hetzner) are flagged as high risk, because real users do not browse from datacenter servers. IPs from residential ISPs (Comcast, Deutsche Telekom, BT) are low risk, because they look like home connections. Mobile carrier IPs (Verizon Wireless, AT&T Mobility) are the lowest risk, because carrier NAT makes them hard to tell apart from real mobile users.

Large residential proxy providers do not run their own ASNs; they route through real residential IPs that belong to ISP ASNs. That is exactly what makes residential proxies harder to detect than datacenter ones.

Detection systems query ASN databases (Team Cymru, RIPE NCC, ARIN) and commercial IP-intelligence APIs to classify each connecting IP. Datacenter IPs are caught with roughly 95% accuracy because the ASN is unambiguous. Residential proxies are much harder (roughly 40% to 70%) because the IPs genuinely belong to ISPs, and mobile proxies are hardest of all (roughly 20% to 40%). That accuracy gradient is why residential and mobile proxies cost many times more than datacenter proxies.

### Known-proxy databases

Beyond ASN classification, specialized services (IPQualityScore, proxycheck.io, Spur.us) maintain real-time databases of known proxy, VPN, and Tor exit IPs. The Tor exit list is public at [check.torproject.org](https://check.torproject.org/torbulkexitlist).

These databases also track behavior: IPs that rotate frequently (typical of proxy pools), IPs with abnormally high concurrent session counts (a residential IP normally has a handful of connections, not hundreds), and IPs previously seen in bot activity.

### Geolocation consistency

Proxies often give themselves away through geographic contradictions: the IP points to one place while browser-reported signals point to another.

The common mismatches are between the IP's location and the browser timezone (`Intl.DateTimeFormat().resolvedOptions().timeZone`), between the IP's country and the `Accept-Language` header, and between this session's location and the last one's. A user in Los Angeles with a `Europe/Berlin` timezone is suspicious. A user in Tokyo ten minutes after their last session was in New York is impossible.

!!! note "Geolocation false positives"
    Legitimate cases trip these alarms: travelers on VPNs, expats keeping their home-country settings, corporate VPN users, and multilingual users with non-default language preferences. Good systems use risk scoring rather than binary blocking to absorb these cases.

## HTTP header analysis

Headers are the simplest detection vector. Transparent and anonymous proxies add headers like `Via`, `X-Forwarded-For`, `X-Real-IP`, and `Forwarded` (RFC 7239) that reveal proxy use directly. Elite proxies strip them, but their absence alone is not proof of a direct connection.

Detection goes further than looking for proxy headers. Missing headers a real browser always sends (`Accept-Language`, `Accept-Encoding`, a realistic `User-Agent`) are suspicious, and header ordering matters: browsers send headers in a consistent, version-specific order, and tools that build headers by hand often get it wrong. The legacy `Proxy-Connection: keep-alive` header is another classic tell.

Proxies are traditionally graded by header behavior, though the distinction matters less now that IP reputation and fingerprinting dominate. An elite proxy on a datacenter IP is still caught instantly by ASN lookup:

| Level | Behavior | Detection |
|-------|----------|-----------|
| Transparent | Forwards your real IP in `X-Forwarded-For`, adds `Via` | Trivial |
| Anonymous | Hides your IP but adds `Via` or other proxy headers | Easy |
| Elite | Strips all proxy-identifying headers | Requires deeper analysis |

## Network fingerprinting

Network-layer fingerprinting operates below the proxy, so it can expose a proxy even when the proxy itself is configured perfectly. This is the theory covered in depth in [Network fingerprinting](../fingerprinting/network-fingerprinting.md); here is how it feeds proxy detection.

**TCP/IP fingerprinting.** Every OS has a distinct TCP stack. The initial window size, TCP options order, TTL, and window scale are set by the kernel, not the browser, and a proxy cannot change them. If the `User-Agent` claims Windows 10 (TTL 128, window 65535) but the TCP fingerprint shows Linux (TTL 64, window around 29200), the mismatch is a strong proxy signal. TTL also decreases by one per hop, so a value that does not fit the expected hop count for the IP's location suggests routing through a proxy.

**TLS fingerprinting (JA3/JA4).** The TLS ClientHello is sent in plaintext and carries enough parameters (version, cipher suites, extensions, curves) to identify the client. Detection systems match its JA3/JA4 hash against known-browser databases. A key nuance: SOCKS5 proxies and HTTP CONNECT tunnels pass the ClientHello through unmodified, so the server sees the real browser fingerprint; only a MITM proxy that terminates TLS changes it, and then the fingerprint belongs to the proxy software, which is itself a signal.

**HTTP/2 fingerprinting.** The HTTP/2 `SETTINGS` frame, pseudo-header order, and stream priorities vary by browser. Automation frameworks and proxies with their own HTTP/2 stacks often produce a fingerprint that matches no real browser.

**Latency.** Round-trip time during the handshake reveals the physical path. If the IP geolocates to New York but the RTT suggests a path through Asia, the connection is likely proxied. Systems may also run JavaScript timing challenges and compare browser-observed latency against server-observed latency; a large gap implies an intermediary.

## Behavioral detection

The most advanced systems examine behavior: request timing, mouse movement (via JavaScript listeners), scrolling, keystroke cadence, and overall browsing patterns. Machine-learning models trained on millions of real sessions combine dozens of features (navigation patterns, session duration, click positions, form timing) to separate humans from automation.

Pydoll's humanized interactions (curved mouse paths with Fitts's-Law timing, variable typing) are aimed at this layer. See [Human-like interactions](../../stealth/human-like-interactions.md) for the practical side and [Behavioral fingerprinting](../fingerprinting/behavioral-fingerprinting.md) for the theory.

## Multi-signal risk scoring

Modern systems do not rely on one technique. They fold every signal into a risk score (typically 0 to 100) and apply a threshold that varies by context. IP reputation usually carries the largest weight (it is the cheapest, most reliable signal), followed by network fingerprinting, header and protocol analysis, behavioral scoring, and consistency checks.

Thresholds follow the business. Banking blocks aggressively, e-commerce presents CAPTCHAs at moderate scores, and content sites tend to be permissive. The lesson for automation is that passing one layer is not enough: a residential IP with a mismatched TCP fingerprint and robotic behavior is still flagged. Consistency across layers is what matters.

## Detection by proxy type

| Proxy type | Detection difficulty | Primary methods |
|------------|----------------------|-----------------|
| Transparent HTTP | Trivial | Headers (`Via`, `X-Forwarded-For`) |
| Anonymous HTTP | Easy | Headers + IP reputation |
| Elite HTTP (datacenter) | Medium | IP reputation (ASN) |
| Datacenter SOCKS5 | Medium | IP reputation (ASN) |
| Residential | Difficult | Behavior, connection patterns, latency |
| Mobile | Very difficult | Mostly behavioral, few network signals |
| Rotating | Difficult | Session inconsistencies, rotation patterns |

## What consistency requires

Evasion is about agreement across layers, not perfecting any single one. In practice that means: prefer residential or mobile IPs when stealth matters; match the browser's timezone, language, and locale to the IP's location; keep a session on one IP rather than rotating mid-session; run automation on the same OS you claim in the `User-Agent` so the TCP fingerprint agrees; humanize behavior; and test for WebRTC, DNS, and timezone leaks before running at scale. Pydoll's [Evasion techniques](../../stealth/evasion-techniques.md) covers the practical levers, including WebRTC leak protection and matching the locale.

!!! warning "No proxy is undetectable"
    With enough resources, any proxy can be detected. Even top-tier residential proxies reach only about 70% to 90% success against sophisticated systems like Akamai, Cloudflare Enterprise, and DataDome. The practical question is whether detecting you is worth the cost to the target.

## Related

- [Network fundamentals](network-fundamentals.md): the layers a request passes through.
- [HTTP/HTTPS proxies](http-proxies.md) and [SOCKS proxies](socks-proxies.md): how each proxy type behaves.
- [Network fingerprinting](../fingerprinting/network-fingerprinting.md): TCP/IP, TLS, and HTTP/2 signatures in detail.
- [Proxies](../../guides/proxies.md): configuring a proxy in Pydoll.
- [Evasion techniques](../../stealth/evasion-techniques.md): the levers you control.

## References

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (anonymous IP detection): https://spur.us/
- Team Cymru IP to ASN mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering, TLS fingerprinting with JA3 and JA3S: https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai, Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017): https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas, TCP/IP fingerprinting for VPN and proxy detection: https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas, detecting proxies and VPNs with latencies: https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 fingerprint: https://browserleaks.com/http2
- RFC 7239, Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110, HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
