# HTTP/HTTPS Proxy Architecture

HTTP proxies are the most common proxy protocol on the internet. Nearly every corporate network uses them, and most commercial proxy services offer them as the default option. They operate at Layer 7 (Application) of the OSI model, which means they understand HTTP and can parse, modify, cache, and filter traffic. This same deep integration with the protocol is also their biggest limitation: they can only handle HTTP traffic, they reveal proxy usage through identifiable headers, and they cannot proxy UDP, which leaves WebRTC and DNS vulnerable to leaks.

This document covers how HTTP proxies work at the protocol level, the CONNECT method for HTTPS tunneling, authentication mechanisms, and the implications of modern protocols like HTTP/2 and HTTP/3.

!!! info "Module Navigation"
    - [Network Fundamentals](./network-fundamentals.md): TCP/IP, UDP, OSI model
    - [Network & Security Overview](./index.md): Module introduction
    - [SOCKS Proxies](./socks-proxies.md): Protocol-agnostic alternative
    - [Proxy Detection](./proxy-detection.md): How to avoid detection

    For practical configuration, see [Proxy Configuration](../../features/configuration/proxy.md).

## How HTTP Proxies Work

An HTTP proxy sits between the client and the target server, maintaining two separate TCP connections: one from the client to the proxy, and another from the proxy to the target server. Because the proxy understands HTTP, it can make intelligent decisions about the traffic passing through it.

### Request Flow

When a client is configured to use an HTTP proxy, it sends the full HTTP request to the proxy rather than directly to the target server. The key difference from a direct request is that the request line includes the absolute URI, not just the path. For example, instead of `GET /page HTTP/1.1`, the client sends `GET http://example.com/page HTTP/1.1`. This tells the proxy where to forward the request.

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Proxy as HTTP Proxy
    participant Server as Target Server

    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: TCP connection #1

    Note over Proxy: Parse request, check auth,<br/>check cache, apply rules

    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: TCP connection #2

    Server->>Proxy: HTTP/1.1 200 OK<br/>[response body]

    Note over Proxy: Cache response if allowed,<br/>filter content, log transaction

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[possibly modified body]
```

The proxy receives the full HTTP request, parses the method, URL, and headers, then decides what to do. It may check authentication credentials, verify the URL against an access control list, look for a cached copy of the resource, and modify headers before forwarding. It then opens a separate TCP connection to the target server and sends the request, potentially with altered headers.

When the response arrives, the proxy can cache it according to HTTP semantics (`Cache-Control`, `ETag`), filter the content for malware or blocked keywords, compress it if the client supports it, and log the transaction before forwarding the response back to the client.

### Proxy Headers and Privacy

HTTP proxies commonly add headers that reveal their presence and the client's real IP address. The `Via` header (RFC 9110) identifies the proxy in the request chain. The `X-Forwarded-For` header contains the original client IP, often forming a chain if multiple proxies are involved. The `X-Forwarded-Proto` header indicates whether the original request was HTTP or HTTPS. Some proxies also add `X-Real-IP` as a simpler alternative to `X-Forwarded-For`.

There is also a standardized `Forwarded` header (RFC 7239) that combines all of this information into a single field, for example `Forwarded: for=192.168.1.100;proto=http;by=proxy.example.com`. In practice, most proxies still use the `X-Forwarded-*` variants since they have broader support.

Legacy clients and some older browsers may also send a `Proxy-Connection: keep-alive` header instead of `Connection: keep-alive` when routing through a proxy. This header is a well-known indicator of proxy usage and a classic detection signal.

!!! danger "Header Detection"
    Detection systems look for the presence of `Via`, `X-Forwarded-For`, or `Forwarded` headers to confirm proxy usage. If `X-Real-IP` does not match the connecting IP, the proxy is confirmed. Sophisticated proxies can strip these headers, but many commercial proxy services leave them in by default. Always verify your proxy's behavior using a tool like [browserleaks.com/ip](https://browserleaks.com/ip).

### Capabilities and Limitations

Because HTTP proxies parse and understand the HTTP protocol, they can read and modify every part of an unencrypted HTTP request and response: URLs, headers, cookies, and bodies. This lets them cache responses intelligently, filter content by URL or keyword, inject or strip headers, authenticate users, and log all traffic in detail.

The trade-off is that this deep coupling with HTTP means the proxy is limited to HTTP traffic. It cannot natively proxy FTP, SSH, SMTP, or custom protocols (though the CONNECT method, described below, provides a tunneling workaround for any TCP-based protocol). It has no support for UDP, which means WebRTC, DNS queries, and QUIC/HTTP/3 traffic bypass it entirely. And inspecting HTTPS content requires TLS termination, which breaks end-to-end encryption.

## The CONNECT Method: HTTPS Tunneling

The CONNECT method (RFC 9110, Section 9.3.6) solves a fundamental problem: how can an HTTP proxy forward encrypted traffic it cannot read? The answer is to become a blind TCP tunnel.

When a client wants to access an HTTPS site through a proxy, it sends a `CONNECT` request asking the proxy to establish a raw TCP connection to the destination. Once the proxy confirms the tunnel is established, it stops being an HTTP proxy entirely and becomes a transparent TCP relay at Layer 4, forwarding bytes in both directions without interpreting them.

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Note over Client,Proxy: Unencrypted HTTP request

    Proxy->>Server: TCP three-way handshake
    Note over Proxy,Server: TCP connection established

    Proxy->>Client: HTTP/1.1 200 Connection Established

    Note right of Proxy: Proxy is now a transparent<br/>TCP relay (Layer 4)

    Client->>Server: TLS ClientHello
    Note over Client,Server: TLS handshake (proxy sees<br/>this in plaintext)
    Server->>Client: TLS ServerHello, Certificate

    Client->>Server: Encrypted HTTP/2 request
    Server->>Client: Encrypted HTTP/2 response

    Note over Proxy: Proxy blindly forwards<br/>all encrypted data
```

### The CONNECT Request

The CONNECT request is minimal. The method is `CONNECT`, the request URI is the destination `host:port` (not a path), and it includes authentication if the proxy requires it. There is no request body. The proxy validates the credentials, checks its access control rules, and opens a TCP connection to the specified host and port. If everything succeeds, it sends back `HTTP/1.1 200 Connection Established` followed by a blank line. After that blank line, the HTTP conversation ends and the proxy becomes a transparent relay.

### Visibility After CONNECT

Once the tunnel is established, the proxy's visibility is limited. It knows the destination hostname and port from the CONNECT request. It can observe connection timing (when it was established and for how long), the volume of data transferred in each direction, and when either side terminates the connection. It can also observe the TLS handshake that follows, which is particularly relevant.

The TLS ClientHello message, sent immediately after the tunnel is established, is transmitted in plaintext. The proxy (and any network observer) can directly read the TLS version, the full list of supported cipher suites, the extensions and their parameters, the elliptic curves offered, and the SNI (Server Name Indication) extension that contains the target hostname. This is exactly the information used for TLS fingerprinting (JA3/JA4). See [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) for details.

What the proxy cannot see is the encrypted application data: HTTP methods, URLs, request and response headers, cookies, session tokens, and response content are all encrypted inside the TLS tunnel.

!!! note "SNI and Encrypted Client Hello (ECH)"
    The SNI extension in the ClientHello reveals the target hostname in plaintext, which is redundant with the CONNECT request in the proxy scenario but relevant for other network observers. Encrypted Client Hello (ECH), currently being deployed, aims to encrypt the SNI to address this leak. However, ECH adoption is still limited and requires both client and server support.

### CONNECT for Non-HTTPS Protocols

While CONNECT is primarily used for HTTPS, it can tunnel any TCP-based protocol. An IMAPS connection to port 993, an SSH connection to port 22, or FTP-over-TLS to port 990 all work through a CONNECT tunnel. The proxy does not need to understand these protocols because after the tunnel is established, it is simply relaying bytes.

In practice, many corporate proxies restrict CONNECT to port 443 (HTTPS) to prevent abuse. Attempting `CONNECT example.com:22` for SSH will often return `403 Forbidden`.

### The HTTPS Dilemma

HTTP proxies face a fundamental choice with encrypted traffic. With the CONNECT tunnel approach, end-to-end encryption is preserved, the client verifies the server's certificate directly, and certificate pinning works normally. But the proxy cannot inspect, cache, or filter the encrypted content.

The alternative is TLS termination (MITM), where the proxy decrypts HTTPS traffic, inspects the content, and re-encrypts it before forwarding. This requires installing the proxy's CA certificate on the client, breaks end-to-end encryption, and is detectable through certificate pinning and Certificate Transparency logs. Most corporate proxies use this approach for content filtering and security scanning, while privacy-focused proxies use blind CONNECT tunnels.

For web scraping and automation, this distinction matters for TLS fingerprinting. If the proxy performs TLS termination, the TLS fingerprint that the target server sees belongs to the proxy, not your browser. If you are using a CONNECT tunnel, the fingerprint is preserved end-to-end. Depending on your evasion strategy, one approach may be preferable to the other.

| Aspect | HTTP (no CONNECT) | HTTPS (CONNECT tunnel) |
|--------|-------------------|------------------------|
| Proxy visibility | Full HTTP request/response | Only destination host:port + TLS ClientHello |
| Encryption | None (unless TLS termination) | End-to-end TLS |
| Caching | Yes, based on HTTP semantics | No (encrypted content) |
| Content filtering | Yes | No (only hostname-based blocking) |
| Header modification | Yes | No (encrypted headers) |
| URL visibility | Full URL | Only hostname (via CONNECT and SNI) |
| Protocol support | HTTP only | Any protocol over TCP |

## HTTPS Proxies (TLS to Proxy)

A distinction worth clarifying is the difference between proxying HTTPS traffic and connecting to the proxy itself over HTTPS. When you configure `--proxy-server=https://proxy:port` instead of `http://proxy:port`, the connection between your browser and the proxy is encrypted with TLS. This protects your proxy authentication credentials from being sniffed on the local network and hides even the CONNECT hostname from local observers, since it is encapsulated inside the TLS connection to the proxy.

Chrome supports this via the `https://` scheme in `--proxy-server`. It is particularly important when using a proxy over untrusted networks (public Wi-Fi, shared hosting), where the connection between you and the proxy is the weakest link.

## Authentication

HTTP proxy authentication uses standard HTTP status codes and headers, following RFC 9110. When a proxy requires authentication, it responds with `407 Proxy Authentication Required` and a `Proxy-Authenticate` header indicating which authentication schemes it supports. The client then retransmits the request with a `Proxy-Authorization` header containing the credentials.

### Authentication Schemes

There are several authentication schemes, each with different security characteristics.

**Basic** (RFC 7617) is the simplest. The client sends `Proxy-Authorization: Basic <base64(username:password)>`. Base64 is an encoding, not encryption, so credentials are trivially reversible. Anyone who intercepts the header can decode it instantly and reuse it indefinitely since there is no replay protection. Basic auth should only be used over TLS-encrypted connections.

**Digest** (RFC 7616) uses a challenge-response mechanism. The proxy sends a random nonce, and the client computes a hash of the username, password, nonce, and request URI. The password is never transmitted, and the nonce provides replay protection. The original version uses MD5, which is fast enough to brute-force efficiently, though RFC 7616 added SHA-256 support. Digest auth is rarely implemented by modern proxy services.

**NTLM** is Microsoft's proprietary challenge-response protocol, common in Windows enterprise environments. It uses a three-step negotiation (Type 1 negotiation, Type 2 challenge, Type 3 authentication) and integrates with Active Directory for single sign-on. NTLMv1 uses DES (broken), and NTLMv2 uses HMAC-MD5 (considered weak by modern standards). Microsoft recommends Kerberos over NTLM for new deployments. NTLM is connection-bound, which means it breaks with HTTP/2 multiplexing.

**Negotiate** (RFC 4559) uses SPNEGO to select between Kerberos and NTLM, preferring Kerberos. Kerberos offers the strongest security (AES encryption, mutual authentication, time-limited tickets) but requires Active Directory infrastructure, domain-joined machines, and accurate clock synchronization. In browser automation, Kerberos is difficult to configure programmatically.

| Scheme | Security | Mechanism | Practical Notes |
|--------|----------|-----------|-----------------|
| Basic | Low | Base64-encoded credentials | Universal support. Only use over TLS. |
| Digest | Medium | Challenge-response with MD5/SHA-256 | Replay protection via nonce. Rarely implemented. |
| NTLM | Medium | Challenge-response (NT hash) | Windows SSO. Proprietary, known vulnerabilities. |
| Negotiate | High | Kerberos/SPNEGO | Strongest. Requires Active Directory. |

### Authentication in Pydoll

Chrome does not support inline proxy credentials in the `--proxy-server` flag. Writing `--proxy-server=http://user:pass@proxy:port` will not work: Chrome silently ignores the `user:pass` portion and connects without authentication.

Pydoll solves this transparently through its `ProxyManager`. When you provide a proxy URL with embedded credentials, Pydoll extracts the username and password, strips them from the URL before passing it to Chrome, and uses the CDP Fetch domain to intercept `407 Proxy Authentication Required` responses and automatically supply the credentials via `Fetch.continueWithAuth`. This approach works for all authentication schemes that Chrome supports (Basic, Digest, NTLM, Negotiate) without Pydoll needing to implement the protocol-specific logic.

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
# Pydoll extracts credentials, cleans the URL, and handles 407 via CDP
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

!!! tip "Authentication Best Practices"
    Always use TLS-encrypted proxy connections (HTTPS proxy or SSH tunnel) to protect credentials in transit. Prefer Bearer tokens for API proxies since they are revocable and time-limited. Never use Basic auth over an unencrypted HTTP connection to the proxy. Do not hardcode credentials in source code; use environment variables instead.

## Modern Protocols and Proxying

### HTTP/2

HTTP/2 introduced multiplexing, binary framing, and HPACK header compression, which fundamentally change how proxies handle connections. In HTTP/1.1, each request occupies a connection sequentially (pipelining exists but is disabled in practice, so browsers work around this by opening six parallel connections per host). In HTTP/2, a single TCP connection carries multiple concurrent streams, each with its own request and response.

For proxies, this means managing stream IDs, priorities, and flow control windows on both sides of the connection. The proxy must translate between stream IDs on the client side and the server side, maintain priority trees, and handle flow control per-stream. This is significantly more complex than the simple request-response forwarding of HTTP/1.1.

From a fingerprinting perspective, HTTP/2 stream metadata (window sizes, priority settings, header ordering within HPACK) can fingerprint individual clients even when multiple users share the same proxy.

| Feature | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Connections | Sequential per connection (browsers open 6 in parallel) | Multiple concurrent streams over one connection |
| Multiplexing | No (head-of-line blocking) | Yes (stream-level only) |
| Header Compression | None | HPACK |
| Proxy Complexity | Simple request/response forwarding | Stream ID mapping, priority management |

In HTTP/2, the CONNECT method was extended by RFC 8441 to support a `:protocol` pseudo-header, enabling WebSocket tunneling and other protocol upgrades directly within HTTP/2 streams without requiring separate connections.

### HTTP/3 and QUIC

HTTP/3 runs over QUIC (RFC 9000), which is a UDP-based transport protocol. This introduces fundamental challenges for HTTP proxies. Traditional HTTP proxies operate over TCP and cannot handle QUIC's UDP traffic. QUIC connections can survive IP changes (connection migration), complicating proxy session management. And QUIC encrypts nearly everything, including transport-level metadata that was previously visible.

Proxying QUIC requires CONNECT-UDP (RFC 9298), a new method for establishing UDP tunnels through HTTP proxies. Most traditional proxies, including many commercial services, do not support this yet. Browsers fall back to HTTP/2 over TCP when the proxy does not support QUIC, which means more metadata may leak than expected if you were relying on HTTP/3's encrypted transport.

In automation scenarios, consider disabling QUIC with the `--disable-quic` Chrome flag to force HTTP/2 over TCP. This ensures all traffic passes through your proxy and eliminates the risk of UDP-based leaks from QUIC.

| Aspect | TCP + TLS (HTTP/1.1, HTTP/2) | QUIC/UDP (HTTP/3) |
|--------|------------------------------|-------------------|
| Transport | TCP (connection-oriented) | UDP (connectionless) |
| Handshake | Separate TCP + TLS (2 RTT) | Combined (0-1 RTT) |
| Head-of-line blocking | Yes (TCP level) | No (stream-level only) |
| Connection migration | Not supported | Supported (survives IP changes) |
| Proxy compatibility | Excellent | Limited (requires UDP relay support) |

!!! warning "Protocol Downgrade"
    When a proxy does not support HTTP/3, the browser silently falls back to HTTP/2 or HTTP/1.1. This downgrade can expose metadata (headers, timing patterns) that HTTP/3 would have encrypted. Monitor your traffic to understand your actual protocol version, and be aware that HTTP/3 adoption varies by region and CDN.

## Summary

HTTP proxies provide rich functionality at the cost of limited scope and privacy concerns. They can inspect, cache, and filter HTTP traffic, but they cannot handle non-HTTP protocols, UDP traffic, or HTTPS content without breaking encryption. Their presence is revealed through identifiable headers unless explicitly stripped.

For automation, the CONNECT tunnel is the most relevant feature: it preserves end-to-end TLS encryption while giving the proxy only hostname-level visibility. Pydoll handles proxy authentication transparently through the CDP Fetch domain, supporting all schemes Chrome implements.

### HTTP Proxy vs SOCKS5

| Need | HTTP Proxy | SOCKS5 |
|------|------------|--------|
| Content filtering | Yes | No |
| URL-based blocking | Yes | No (only IP:port) |
| Caching | Yes | No |
| UDP support | No | Yes |
| Protocol flexibility | HTTP only (CONNECT for TCP tunneling) | Any TCP/UDP |
| Privacy | Low (parses HTTP, adds revealing headers) | Medium (does not parse or modify traffic, but unencrypted content is still visible to operator) |
| DNS resolution | Proxy resolves (remote) | Depends (SOCKS5: typically client resolves, SOCKS5h: proxy resolves. Chrome always resolves remotely for SOCKS5.) |

For corporate environments that need content control and caching, HTTP proxies are the right choice. For privacy-focused automation, SOCKS5 offers better stealth and protocol flexibility. For maximum security, use SOCKS5 over an SSH tunnel or VPN.

**Next steps:**

- [SOCKS Proxies](./socks-proxies.md): Protocol-agnostic, session-layer proxying
- [Network Fundamentals](./network-fundamentals.md): TCP/IP, UDP, WebRTC
- [Proxy Detection](./proxy-detection.md): How proxies are detected and how to avoid it
- [Proxy Configuration](../../features/configuration/proxy.md): Practical Pydoll proxy setup
- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): TCP/IP and TLS fingerprinting

## References

- RFC 9110: HTTP Semantics (2022, replaces RFC 7230-7237) - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 (2022) - https://www.rfc-editor.org/rfc/rfc9112.html
- RFC 9113: HTTP/2 (2022, replaces RFC 7540) - https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3 (2022) - https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC Transport Protocol (2021) - https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP, 2022) - https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 8441: Bootstrapping WebSockets with HTTP/2 (2018) - https://www.rfc-editor.org/rfc/rfc8441.html
- RFC 7617: Basic Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication (2015) - https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension (2014) - https://www.rfc-editor.org/rfc/rfc7239.html
- RFC 4559: Negotiate Authentication (2006) - https://www.rfc-editor.org/rfc/rfc4559.html
- MDN Web Docs: Proxy servers and tunneling - https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
- Chrome DevTools Protocol: Fetch domain - https://chromedevtools.github.io/devtools-protocol/tot/Fetch/
