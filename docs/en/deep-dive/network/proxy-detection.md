# Proxy Detection

Proxy detection is a probabilistic process. Websites combine dozens of signals to assess whether a connection is proxied, ranging from simple IP reputation lookups to TCP/IP stack analysis and behavioral profiling. No single signal provides definitive proof, but combining enough weak signals produces high-confidence decisions.

This document covers the main detection techniques, how they work at a technical level, and what they mean for browser automation with Pydoll.

!!! info "Module Navigation"
    - [SOCKS Proxies](./socks-proxies.md): Session-layer proxying
    - [HTTP/HTTPS Proxies](./http-proxies.md): Application-layer proxying
    - [Network Fundamentals](./network-fundamentals.md): TCP/IP, UDP, WebRTC

    For fingerprinting details, see [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) and [Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md).

## IP Reputation

IP reputation analysis is the most widely deployed proxy detection technique. It combines publicly available data (ASN records, WHOIS, geolocation databases) with proprietary intelligence to classify IP addresses into risk categories.

### ASN Classification

Every IP address belongs to an Autonomous System (AS), identified by an ASN. The type of AS that owns an IP is the strongest single indicator of whether it is a proxy.

IPs belonging to cloud and hosting providers (AWS, DigitalOcean, OVH, Hetzner) are flagged as high risk because real users do not browse the web from datacenter servers. IPs from residential ISPs (Comcast, Deutsche Telekom, BT) are low risk because they look like normal home connections. Mobile carrier IPs (Verizon Wireless, AT&T Mobility) are the lowest risk because they are the hardest to distinguish from real mobile users.

Some ASNs are associated with known proxy infrastructure, though this is more nuanced than it might seem. Large residential proxy providers like BrightData or Smartproxy do not operate their own ASNs; they route traffic through real residential IPs belonging to ISP ASNs. This is precisely what makes residential proxies harder to detect than datacenter proxies.

Detection systems query ASN databases (Team Cymru, RIPE NCC, ARIN) and commercial IP intelligence APIs to classify each connecting IP. Datacenter IPs are detected with roughly 95%+ accuracy because the ASN classification is unambiguous. Residential proxy detection is much harder (roughly 40-70% accuracy) because the IPs genuinely belong to ISPs. Mobile proxy detection is the most difficult (roughly 20-40%) because mobile carrier NAT makes many real users share IPs.

This accuracy gradient is why residential and mobile proxies command 10-100x the price of datacenter proxies.

### Known Proxy Databases

Beyond ASN classification, specialized databases track IPs that have been observed participating in proxy networks. Services like IPQualityScore, proxycheck.io, and Spur.us maintain real-time databases of known proxy, VPN, and Tor exit node IPs. The Tor exit node list is publicly available at [check.torproject.org](https://check.torproject.org/torbulkexitlist).

These databases also track behavioral signals: IPs that rotate frequently (typical of proxy pools), IPs with abnormally high concurrent session counts (a residential IP normally has 1-5 concurrent connections, not 100+), and IPs previously associated with bot-like activity.

### Geolocation Consistency

Proxies often reveal themselves through geographic inconsistencies. The IP address points to one location, but browser-reported signals point to another.

The most common mismatches are between the IP's geolocation and the browser's timezone (collected via JavaScript's `Intl.DateTimeFormat().resolvedOptions().timeZone`), between the IP's country and the `Accept-Language` header, and between the current session's location and a previous session's location. A user appearing in Los Angeles with a browser timezone of `Europe/Berlin` is suspicious. A user appearing in Tokyo 10 minutes after their last session was in New York is physically impossible.

Detection systems also check whether the IP's geolocation matches the locale configuration of the browser. A US datacenter IP with `Accept-Language: zh-CN` and timezone `Asia/Shanghai` strongly suggests a Chinese user routing through a US proxy.

!!! note "False Positives"
    Legitimate scenarios trigger geolocation alarms: travelers using VPNs, expats with browser settings from their home country, corporate users connecting through company VPNs, and multilingual users with non-default language preferences. Sophisticated systems use risk scoring rather than binary blocking to account for these cases.

## HTTP Header Analysis

HTTP headers are the simplest detection vector. Transparent and anonymous proxies add headers like `Via`, `X-Forwarded-For`, `X-Real-IP`, and `Forwarded` (RFC 7239) that directly reveal proxy usage. Elite proxies strip these headers, but their absence alone is not proof of a direct connection.

Detection goes beyond looking for proxy-specific headers. Missing headers that real browsers always send (like `Accept-Language`, `Accept-Encoding`, or a realistic `User-Agent`) are suspicious. Header ordering matters too: browsers send headers in a consistent, version-specific order, and proxies or automation tools that construct headers manually often get the order wrong.

The legacy `Proxy-Connection: keep-alive` header, sent by some older clients when routing through a proxy, is another classic detection signal.

### Proxy Anonymity Levels

Proxies are traditionally classified into three anonymity levels based on their header behavior:

| Level | Behavior | Detection |
|-------|----------|-----------|
| Transparent | Forwards your real IP in `X-Forwarded-For`, adds `Via` header | Trivial |
| Anonymous | Hides your IP but adds `Via` or other proxy headers | Easy |
| Elite | Strips all proxy-identifying headers | Requires deeper analysis |

This classification dates from an era when header analysis was the primary detection method. Modern detection systems use IP reputation, fingerprinting, and behavioral analysis, making the transparent/anonymous/elite distinction less meaningful. An elite proxy with a datacenter IP is detected instantly through ASN lookup. A transparent proxy on a residential IP might still pass under the radar on less sophisticated sites.

## Network Fingerprinting

Network-layer fingerprinting operates below the proxy layer, which means it can detect proxies even when the proxy itself is configured perfectly.

### TCP/IP Fingerprinting

Every operating system has a unique TCP stack implementation that reveals itself during the TCP handshake. The initial window size, TCP options order, TTL (Time To Live), and window scale factor are all set by the kernel, not the browser, and cannot be changed by a proxy.

Detection systems compare these TCP characteristics against the `User-Agent` header. If the User-Agent claims Windows 10 but the TCP fingerprint shows Linux characteristics (TTL of 64, window size of 29200), the mismatch is a strong proxy indicator. Windows uses a default TTL of 128 and modern builds typically show a window size of 65535, while Linux uses TTL 64 and window sizes around 29200.

TTL analysis adds another layer. The TTL decreases by 1 at each network hop. If a Windows connection arrives with a TTL of 128, the client is likely on the same network. If it arrives with a TTL of 115, it has crossed roughly 13 hops. If the TTL value does not align with the expected hop count for the IP's geographic location, proxy routing is likely.

For detailed TCP fingerprint values and their implications, see [Network Fingerprinting](../fingerprinting/network-fingerprinting.md).

### TLS Fingerprinting (JA3/JA4)

The TLS ClientHello message is transmitted in plaintext and contains enough parameters to uniquely identify the client application: TLS version, supported cipher suites, extensions, elliptic curves, and signature algorithms. The JA3 fingerprint is an MD5 hash of these parameters concatenated in a specific order. JA4 is a newer, more granular alternative.

Each browser version produces a distinctive JA3/JA4 fingerprint. Detection systems maintain databases of known fingerprints for Chrome, Firefox, Safari, and other browsers. If the JA3 fingerprint does not match any known browser, or does not match the browser claimed in the User-Agent, the connection is flagged.

An important nuance: SOCKS5 proxies and HTTP CONNECT tunnels pass the TLS ClientHello through unmodified, so the target server sees the real browser fingerprint. The proxy does not alter TLS parameters in these configurations. Only MITM proxies (which terminate and re-establish TLS) change the fingerprint, and in that case the fingerprint belongs to the proxy software, not a real browser, which is itself a detection signal.

### HTTP/2 Fingerprinting

HTTP/2 connections expose fingerprinting signals that are distinct from TLS. The SETTINGS frame sent at the beginning of an HTTP/2 connection contains parameters like `HEADER_TABLE_SIZE`, `MAX_CONCURRENT_STREAMS`, `INITIAL_WINDOW_SIZE`, and `MAX_HEADER_LIST_SIZE`. Each browser uses different default values for these settings.

The order and priority of pseudo-headers (`:method`, `:authority`, `:scheme`, `:path`), the HPACK compression behavior, and stream priority weights also vary between browsers. Tools like [browserleaks.com/http2](https://browserleaks.com/http2) show what your HTTP/2 fingerprint looks like.

Automation frameworks and proxy software that implement their own HTTP/2 stacks often produce fingerprints that do not match any real browser, making this an effective detection vector.

### Latency-Based Detection

The network latency between a client and a server reveals information about the physical network path. If the IP geolocates to New York but the round-trip time suggests a path through Asia, the connection is likely proxied.

Detection systems measure RTT (round-trip time) during the TCP handshake and compare it against expected latencies for the IP's geographic location. They may also issue JavaScript-based timing challenges that measure latency from the browser's perspective, then compare this with the server-observed latency. A significant discrepancy between the two suggests an intermediary (proxy) in the path.

Clock skew analysis adds another dimension: by measuring the client's clock offset via JavaScript (`Date.now()`) or HTTP `Date` headers, detection systems can infer the client's actual timezone and compare it against the IP's expected timezone.

## Behavioral Detection

The most advanced detection systems go beyond network and protocol analysis to examine user behavior. This includes request timing (are requests evenly spaced, suggesting automation?), mouse movement patterns (analyzed via JavaScript event listeners), scrolling behavior, keyboard input cadence, and overall browsing patterns.

Machine learning models trained on millions of real user sessions can distinguish human behavior from automation with high accuracy. These models typically combine 50+ features including navigation patterns, session duration distribution, click positions, form interaction timing, and JavaScript execution characteristics.

Pydoll's humanized interactions (Bezier curve mouse movement, Fitts's Law timing, realistic typing) are designed specifically to pass behavioral analysis. See [Evasion Techniques](../fingerprinting/evasion-techniques.md) for the full multi-layer evasion strategy.

## Multi-Signal Risk Scoring

Modern detection systems do not rely on any single technique. They combine all available signals into a risk score, typically 0-100, and apply thresholds that vary by industry and context.

The weight of each signal category varies, but a rough approximation is that IP reputation accounts for the largest share (it is the cheapest and most reliable signal), followed by network fingerprinting (TCP/IP, TLS, HTTP/2), header and protocol analysis, behavioral scoring, and consistency checks (geolocation, timezone, language).

Thresholds depend on the business context. Banking sites block aggressively (risk score above 50), e-commerce sites present CAPTCHAs at moderate scores (above 70), and content sites tend to be more permissive (blocking only above 80) since they rely on ad impressions.

The implication for automation is that passing one layer of detection is not enough. A residential IP (good IP reputation) with a mismatched TCP fingerprint and robotic behavior will still be flagged. Effective evasion requires consistency across all layers.

## Detection by Proxy Type

| Proxy Type | Detection Difficulty | Primary Detection Methods |
|------------|----------------------|---------------------------|
| Transparent HTTP | Trivial | HTTP headers (`Via`, `X-Forwarded-For`) |
| Anonymous HTTP | Easy | HTTP headers + IP reputation |
| Elite HTTP (datacenter) | Medium | IP reputation (ASN analysis) |
| Datacenter SOCKS5 | Medium | IP reputation (ASN analysis) |
| Residential proxies | Difficult | Behavioral analysis, connection patterns, latency |
| Mobile proxies | Very difficult | Mostly behavioral, limited network signals |
| Rotating proxies | Difficult | Session inconsistencies, IP rotation patterns |

## Evasion Principles

Effective evasion is about consistency across all detection layers, not perfecting any single one.

Use residential or mobile IPs when stealth matters. They are harder to detect because the IPs genuinely belong to ISPs, and the cost premium reflects this advantage. Match the browser's geolocation signals (timezone, language, locale) to the proxy IP's location. Maintain session persistence by not rotating IPs mid-session, which creates detectable discontinuities. Ensure your TCP/IP fingerprint matches your User-Agent claim by running automation on the same OS you are impersonating. Use Pydoll's humanized interactions to pass behavioral analysis. And always test for leaks (WebRTC, DNS, timezone) before running automation at scale.

The goal is not to make detection impossible but to make it expensive and uncertain. Force the detection system to use multiple correlated signals, blend in with legitimate traffic patterns, and create plausible deniability.

!!! warning "No Proxy is Undetectable"
    With sufficient resources, any proxy can be detected. Even top-tier residential proxies achieve roughly 70-90% success rates against sophisticated anti-bot systems like Akamai, Cloudflare Enterprise, and DataDome. The practical question is whether detection is economically worthwhile for the target site.

**Next steps:**

- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): TCP/IP and TLS fingerprinting in detail
- [Browser Fingerprinting](../fingerprinting/browser-fingerprinting.md): Canvas, WebGL, HTTP/2 fingerprinting
- [Evasion Techniques](../fingerprinting/evasion-techniques.md): Multi-layer evasion strategy
- [Proxy Configuration](../../features/configuration/proxy.md): Practical Pydoll proxy setup

## References

- MaxMind GeoIP2: https://www.maxmind.com/en/geoip2-services-and-databases
- IPQualityScore Proxy Detection: https://www.ipqualityscore.com/proxy-vpn-tor-detection-service
- Spur.us (Anonymous IP Detection): https://spur.us/
- Team Cymru IP to ASN Mapping: https://www.team-cymru.com/ip-asn-mapping
- Salesforce Engineering: TLS Fingerprinting with JA3 and JA3S - https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/
- Akamai: Passive Fingerprinting of HTTP/2 Clients (Black Hat EU 2017) - https://blackhat.com/docs/eu-17/materials/eu-17-Shuster-Passive-Fingerprinting-Of-HTTP2-Clients-wp.pdf
- Incolumitas: TCP/IP Fingerprinting for VPN and Proxy Detection - https://incolumitas.com/2021/03/13/tcp-ip-fingerprinting-for-vpn-and-proxy-detection/
- Incolumitas: Detecting Proxies and VPNs with Latencies - https://incolumitas.com/2021/06/07/detecting-proxies-and-vpn-with-latencies/
- BrowserLeaks HTTP/2 Fingerprint: https://browserleaks.com/http2
- BrowserLeaks IP: https://browserleaks.com/ip
- RFC 7239: Forwarded HTTP Extension - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
