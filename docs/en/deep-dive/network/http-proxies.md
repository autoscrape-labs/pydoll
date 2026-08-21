# HTTP and HTTPS proxies

An HTTP proxy sits between your browser and the target server and understands HTTP, so it can parse, cache, filter, and modify the traffic passing through it. That deep coupling with the protocol is also its limit: it handles only HTTP, reveals itself through identifiable headers, and cannot carry UDP, which leaves WebRTC and QUIC to leak around it.

This page covers how HTTP proxies move traffic, the CONNECT tunnel that carries HTTPS, how authentication works, and where modern protocols (HTTP/2, HTTP/3) complicate the picture. For configuring a proxy in Pydoll, see [Proxies](../../guides/proxies.md). Related background: [Network fundamentals](network-fundamentals.md), [SOCKS proxies](socks-proxies.md), and [Proxy detection](proxy-detection.md).

## How an HTTP proxy works

An HTTP proxy holds two separate TCP connections: one from the client to the proxy, one from the proxy to the target. Because it reads HTTP, it can decide what to do with each request rather than blindly relay bytes.

When a client is configured to use the proxy, it sends the full request to the proxy instead of the server. The tell is the request line: it carries the absolute URI, not just the path. Instead of `GET /page HTTP/1.1`, the client sends `GET http://example.com/page HTTP/1.1`, which tells the proxy where to forward it.

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

    Proxy->>Client: HTTP/1.1 200 OK<br/>Via: 1.1 proxy.example.com<br/>[possibly modified body]
```

The proxy parses the method, URL, and headers, then decides: check credentials, match the URL against an access list, look for a cached copy, rewrite headers. It opens its own connection to the server and forwards the request. When the response comes back it can cache it per `Cache-Control` and `ETag`, filter the content, compress it, and log the transaction before passing it on.

### Headers that give the proxy away

HTTP proxies commonly add headers that reveal their presence and the client's real IP:

- `Via` (RFC 9110) identifies the proxy in the request chain.
- `X-Forwarded-For` carries the original client IP, chaining if several proxies are involved. `X-Real-IP` is a simpler variant.
- `X-Forwarded-Proto` records whether the original request was HTTP or HTTPS.
- The standardized `Forwarded` header (RFC 7239) combines these into one field, though most proxies still send the `X-Forwarded-*` variants.

Older clients may also send `Proxy-Connection: keep-alive` instead of `Connection: keep-alive`, which is a classic proxy indicator.

!!! warning "Headers confirm a proxy"
    Detection systems look for `Via`, `X-Forwarded-For`, or `Forwarded`, and confirm the proxy when `X-Real-IP` disagrees with the connecting IP. Good proxies strip these, but many commercial services leave them in by default. Check yours with a tool like [browserleaks.com/ip](https://browserleaks.com/ip).

### What it can and cannot do

Because it parses HTTP, a proxy can read and change every part of an unencrypted request and response (URLs, headers, cookies, bodies), which is what enables caching, content filtering, header injection, authentication, and detailed logging.

The cost of that coupling is scope. It cannot natively carry FTP, SSH, or custom protocols (CONNECT, below, is the workaround), it has no UDP path, so WebRTC, DNS, and QUIC bypass it, and inspecting HTTPS content requires terminating TLS, which breaks end-to-end encryption.

## The CONNECT method: tunneling HTTPS

CONNECT (RFC 9110) answers a basic question: how does a proxy forward encrypted traffic it cannot read? By becoming a blind TCP tunnel. The client asks the proxy to open a raw TCP connection to the destination; once it confirms, the proxy stops interpreting HTTP and only relays bytes in both directions.

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server

    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Proxy->>Server: TCP three-way handshake
    Proxy->>Client: HTTP/1.1 200 Connection Established
    Note right of Proxy: Proxy is now a transparent<br/>TCP relay (Layer 4)
    Client->>Server: TLS ClientHello
    Server->>Client: TLS ServerHello, Certificate
    Client->>Server: Encrypted HTTP/2 request
    Server->>Client: Encrypted HTTP/2 response
```

The CONNECT request is minimal: the method is `CONNECT`, the target is `host:port` (not a path), there is no body. The proxy validates credentials, checks its rules, opens the TCP connection, and replies `HTTP/1.1 200 Connection Established` followed by a blank line. After that line the HTTP conversation is over and the proxy is a relay.

### What the proxy sees after CONNECT

Once the tunnel is up, the proxy knows the destination host and port, and can observe timing, the volume of data each way, and when either side hangs up. It also sees the TLS ClientHello, which is sent in plaintext: the TLS version, cipher suites, extensions, curves, and the SNI hostname. This is exactly what TLS fingerprinting (JA3/JA4) reads; see [Network fingerprinting](../fingerprinting/network-fingerprinting.md).

What it cannot see is the encrypted application data: methods, URLs, headers, cookies, tokens, and bodies are all inside the TLS tunnel.

!!! note "SNI and Encrypted Client Hello"
    The SNI extension reveals the target hostname in plaintext, redundant with the CONNECT line here but visible to other network observers. Encrypted Client Hello (ECH) aims to hide it, but adoption is still limited and needs both client and server support.

CONNECT can tunnel any TCP protocol (IMAPS, SSH, FTPS), because after the tunnel opens the proxy only relays bytes. In practice many corporate proxies restrict CONNECT to port 443, so `CONNECT example.com:22` often returns `403 Forbidden`.

### Tunnel vs interception

A proxy faces a choice with encrypted traffic. A CONNECT tunnel preserves end-to-end encryption: the client verifies the server certificate directly and certificate pinning works, but the proxy cannot inspect or cache the content. TLS termination (MITM) is the alternative: the proxy decrypts, inspects, and re-encrypts, which requires installing its CA certificate on the client, breaks end-to-end encryption, and is detectable through pinning and Certificate Transparency. Corporate proxies tend to terminate for content filtering; privacy-focused proxies use blind tunnels.

For automation this decides whose TLS fingerprint the server sees. Through a CONNECT tunnel the fingerprint is your browser's, end to end. Through a terminating proxy it is the proxy's.

| Aspect | HTTP (no CONNECT) | HTTPS (CONNECT tunnel) |
|--------|-------------------|------------------------|
| Proxy visibility | Full request and response | Destination host:port + TLS ClientHello |
| Encryption | None (unless it terminates TLS) | End-to-end TLS |
| Caching | Yes, per HTTP semantics | No (encrypted) |
| Content filtering | Yes | Hostname-based only |
| URL visibility | Full URL | Hostname only (CONNECT and SNI) |
| Protocol support | HTTP only | Any TCP protocol |

## Connecting to the proxy over TLS

Proxying HTTPS traffic is different from reaching the proxy itself over HTTPS. Configure `--proxy-server=https://proxy:port` (rather than `http://`) and the hop between your browser and the proxy is TLS-encrypted, which protects your proxy credentials on the local network and hides even the CONNECT hostname from local observers. This matters most on untrusted networks, where the client-to-proxy hop is the least protected.

## Authentication

When a proxy needs credentials it replies `407 Proxy Authentication Required` with a `Proxy-Authenticate` header naming the schemes it accepts, and the client retries with a `Proxy-Authorization` header.

- **Basic** (RFC 7617): sends `base64(username:password)`. Base64 is encoding, not encryption, so it is trivially reversible and has no replay protection. Only use it over a TLS connection to the proxy.
- **Digest** (RFC 7616): a challenge-response over a nonce; the password is never sent and the nonce limits replay. The original MD5 form is weak (SHA-256 was added later), and it is rarely implemented today.
- **NTLM**: Microsoft's proprietary challenge-response, common in Windows networks. It is connection-bound, so it breaks with HTTP/2 multiplexing, and its hashes are weak by modern standards.
- **Negotiate** (RFC 4559): SPNEGO selecting Kerberos or NTLM, preferring Kerberos. Kerberos is the strongest but needs Active Directory, domain-joined machines, and synced clocks, which is hard to arrange in automation.

| Scheme | Security | Mechanism | Notes |
|--------|----------|-----------|-------|
| Basic | Low | Base64 credentials | Universal. Only over TLS. |
| Digest | Medium | Challenge-response (MD5/SHA-256) | Replay protection. Rare. |
| NTLM | Medium | Challenge-response (NT hash) | Windows SSO. Breaks HTTP/2. |
| Negotiate | High | Kerberos/SPNEGO | Strongest. Needs Active Directory. |

Chrome does not accept inline credentials in `--proxy-server`: `http://user:pass@proxy:port` connects without the `user:pass`. Pydoll works around this for you (it strips the credentials from the URL and answers the `407` challenge over CDP), so you can pass a proxy URL with credentials. See [Proxies](../../guides/proxies.md) for the usage.

## Modern protocols

### HTTP/2

HTTP/2 carries multiple concurrent streams over one TCP connection, with binary framing and HPACK header compression. For a proxy that means mapping stream IDs between the two sides, maintaining priority trees, and doing per-stream flow control, which is far more involved than HTTP/1.1's sequential forwarding. It also matters for fingerprinting: HTTP/2 stream metadata (window sizes, priorities, header order in HPACK) can identify individual clients even when many share one proxy.

| Feature | HTTP/1.1 | HTTP/2 |
|---------|----------|--------|
| Connections | Sequential per connection (browsers open ~6 in parallel) | Concurrent streams over one connection |
| Multiplexing | No | Yes (stream level) |
| Header compression | None | HPACK |
| Proxy complexity | Simple forwarding | Stream mapping, priorities |

### HTTP/3 and QUIC

HTTP/3 runs over QUIC, a UDP transport, which breaks the assumptions of TCP-based proxies. Traditional proxies cannot carry QUIC, its connections survive IP changes, and it encrypts nearly all transport metadata. Proxying it needs CONNECT-UDP (RFC 9298), which many services do not support yet, so browsers fall back to HTTP/2 over TCP when the proxy can't do QUIC.

!!! warning "Silent downgrade leaks metadata"
    When a proxy does not support HTTP/3, the browser quietly falls back to HTTP/2 or HTTP/1.1, exposing timing and header metadata that HTTP/3 would have encrypted. In automation, consider forcing TCP with the `--disable-quic` flag so all traffic goes through the proxy and there are no UDP-based leaks.

## HTTP proxy vs SOCKS5

| Need | HTTP proxy | SOCKS5 |
|------|------------|--------|
| Content filtering / caching | Yes | No |
| URL-based blocking | Yes | No (IP:port only) |
| UDP support | No | Yes |
| Protocol flexibility | HTTP (CONNECT for TCP tunnels) | Any TCP/UDP |
| Privacy | Low (parses HTTP, adds headers) | Higher (does not parse or modify) |
| DNS resolution | Proxy resolves | Chrome resolves remotely for SOCKS5 |

HTTP proxies suit environments that need content control and caching. For privacy-focused automation, SOCKS5 gives better stealth and protocol flexibility. In automation, the CONNECT tunnel keeps your TLS fingerprint end to end and gives the proxy only hostname-level visibility.

## Related

- [SOCKS proxies](socks-proxies.md): protocol-agnostic, session-layer proxying.
- [Proxy detection](proxy-detection.md): the signals that expose a proxy.
- [Network fundamentals](network-fundamentals.md): TCP/IP, UDP, and the layers underneath.
- [Network fingerprinting](../fingerprinting/network-fingerprinting.md): TCP/IP and TLS fingerprinting.
- [Proxies](../../guides/proxies.md): configuring proxies in Pydoll.

## References

- RFC 9110: HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9113: HTTP/2: https://www.rfc-editor.org/rfc/rfc9113.html
- RFC 9114: HTTP/3: https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000: QUIC: https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9298: Proxying UDP in HTTP (CONNECT-UDP): https://www.rfc-editor.org/rfc/rfc9298.html
- RFC 7617: Basic Authentication: https://www.rfc-editor.org/rfc/rfc7617.html
- RFC 7616: Digest Authentication: https://www.rfc-editor.org/rfc/rfc7616.html
- RFC 7239: Forwarded HTTP Extension: https://www.rfc-editor.org/rfc/rfc7239.html
- MDN: Proxy servers and tunneling: https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
