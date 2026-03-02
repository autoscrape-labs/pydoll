# SOCKS Protocol Architecture

SOCKS (SOCKet Secure) is a proxying protocol that operates between the transport and application layers of the network stack (commonly described as Layer 5 in the OSI model). Unlike HTTP proxies, which parse and understand HTTP traffic, SOCKS proxies forward raw TCP and UDP connections without inspecting their content. This protocol-agnostic design makes SOCKS the preferred choice for privacy-focused automation: the proxy never needs to parse your requests, inject headers, or terminate TLS connections.

This document covers how SOCKS works at the protocol level, the differences between SOCKS4 and SOCKS5, authentication handling in Chrome, DNS resolution behavior, and practical configuration in Pydoll.

!!! info "Module Navigation"
    - [HTTP/HTTPS Proxies](./http-proxies.md): Application-layer proxying
    - [Network Fundamentals](./network-fundamentals.md): TCP/IP, UDP, OSI model
    - [Network & Security Overview](./index.md): Module introduction
    - [Proxy Detection](./proxy-detection.md): Anonymity levels and detection evasion
    - [Building Proxies](./build-proxy.md): SOCKS5 implementation from scratch

    For practical configuration, see [Proxy Configuration](../../features/configuration/proxy.md).

## How SOCKS Differs from HTTP Proxies

The fundamental difference lies in what each proxy can see and do. An HTTP proxy operates at the application layer and understands HTTP: it can read URLs, headers, cookies, and request bodies (for unencrypted traffic), modify them in transit, cache responses, and inject its own headers like `Via` and `X-Forwarded-For`. This is powerful for content filtering but means you must trust the proxy operator with your application data.

A SOCKS proxy operates below the application layer. It sees only the destination address, port, and the volume of data being transferred. It does not parse, modify, or even understand what protocol is flowing through it. HTTP, HTTPS, FTP, SSH, WebSocket, or any custom protocol all look the same to a SOCKS proxy: just bytes being relayed between two endpoints.

This has a direct practical implication. When you send an HTTPS request through a SOCKS5 proxy, the proxy sees `example.com:443` and the encrypted TLS stream. It cannot read the URL, headers, cookies, or response content. It does not add identifying headers. It does not need to terminate TLS. The encrypted tunnel runs end-to-end between your browser and the target server.

However, it is important to understand what SOCKS does not provide. SOCKS is a proxying protocol, not an encryption protocol. The name "SOCKet Secure" refers to secure firewall traversal, not cryptographic security. If you send unencrypted HTTP traffic through a SOCKS5 proxy, the proxy operator can read the bytes passing through, even though the proxy is not designed to inspect them. For actual encryption, you need TLS/HTTPS on top of SOCKS, or an encrypted tunnel (SSH, VPN) wrapping the SOCKS connection.

!!! note "Trust Model"
    With HTTP proxies, you trust the proxy operator not to log your browsing history, steal tokens, modify responses, or perform MITM attacks. With SOCKS5, you trust the proxy only to forward packets correctly and not log connection metadata. The attack surface is smaller, but it is not zero.

## SOCKS4 vs SOCKS5

SOCKS has two versions in common use. SOCKS4 was developed by NEC in the early 1990s as an informal standard with no RFC. SOCKS5 was standardized as RFC 1928 in 1996 to address SOCKS4's limitations.

| Feature | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| Standard | No official RFC (de facto, 1992) | RFC 1928 (1996) |
| Authentication | Identification only (USERID field, no password) | Multiple methods (none, username/password, GSSAPI) |
| IP version | IPv4 only | IPv4 and IPv6 |
| UDP support | No | Yes (UDP ASSOCIATE command) |
| DNS resolution | Client-side (SOCKS4A extension adds server-side) | Server-side when using domain names (ATYP=0x03) |
| Protocol support | TCP only | TCP and UDP |

SOCKS5 is superior in every practical way. Use SOCKS4 only if the proxy does not support SOCKS5.

## The SOCKS5 Handshake

The SOCKS5 connection process follows RFC 1928 and consists of three phases: method negotiation, optional authentication, and the connection request.

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5 as SOCKS5 Proxy
    participant Server as Target Server

    Note over Client,SOCKS5: Phase 1: Method Negotiation
    Client->>SOCKS5: Hello [VER=5, NMETHODS, METHODS]
    SOCKS5->>Client: Method Selected [VER=5, METHOD]

    Note over Client,SOCKS5: Phase 2: Authentication (if required)
    Client->>SOCKS5: Auth Request [VER=1, ULEN, UNAME, PLEN, PASSWD]
    SOCKS5->>Client: Auth Response [VER=1, STATUS]

    Note over Client,SOCKS5: Phase 3: Connection Request
    Client->>SOCKS5: Connect [VER=5, CMD=CONNECT, DST.ADDR, DST.PORT]
    SOCKS5->>Server: Establish TCP connection
    Server-->>SOCKS5: Connection established
    SOCKS5->>Client: Reply [VER=5, REP=SUCCESS, BND.ADDR, BND.PORT]

    Note over Client,Server: Data relay (proxied)
    Client->>SOCKS5: Application data
    SOCKS5->>Server: Forward data
    Server->>SOCKS5: Response data
    SOCKS5->>Client: Forward response
```

### Phase 1: Method Negotiation

The client opens a TCP connection to the proxy and sends a greeting containing the protocol version (always `0x05` for SOCKS5) and a list of authentication methods it supports.

```python
# Client Hello
[
    0x05,        # VER: Protocol version (5)
    0x02,        # NMETHODS: Number of methods offered
    0x00, 0x02   # METHODS: No auth (0x00) and Username/Password (0x02)
]
```

The proxy responds with the method it selects. If the proxy requires authentication and the client offered `0x02` (username/password), the proxy selects it. If no acceptable method was offered, the proxy responds with `0xFF` and closes the connection.

```python
# Server response
[
    0x05,   # VER: Protocol version (5)
    0x02    # METHOD: Username/Password selected
]
```

Method codes defined by RFC 1928: `0x00` = no authentication, `0x01` = GSSAPI, `0x02` = username/password (RFC 1929), `0x03-0x7F` = IANA assigned, `0x80-0xFE` = reserved for private methods, `0xFF` = no acceptable methods.

### Phase 2: Authentication

If the proxy selected method `0x02`, the client sends credentials following RFC 1929. The subnegotiation uses its own version number (`0x01`, not `0x05`).

```python
# Client authentication
[
    0x01,              # VER: Subnegotiation version (1)
    len(username),     # ULEN: Username length (max 255)
    *username_bytes,   # UNAME: Username
    len(password),     # PLEN: Password length (max 255)
    *password_bytes    # PASSWD: Password
]

# Server response
[
    0x01,   # VER: Subnegotiation version (1)
    0x00    # STATUS: 0 = success, non-zero = failure
]
```

Credentials are transmitted in plaintext during this handshake. This is inherent to the SOCKS5 protocol (RFC 1929). For sensitive environments, wrap the SOCKS connection in an SSH tunnel or VPN.

### Phase 3: Connection Request

After authentication succeeds (or if no authentication was required), the client sends a connection request specifying the command, destination address, and port.

```python
[
    0x05,          # VER: Protocol version (5)
    0x01,          # CMD: 1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,          # RSV: Reserved
    0x03,          # ATYP: 1=IPv4 (4 bytes), 3=Domain (length+name), 4=IPv6 (16 bytes)
    len(domain),   # Domain length (only for ATYP=0x03)
    *domain_bytes, # Domain name
    *port_bytes    # Port (2 bytes, big-endian)
]
```

The address type (ATYP) determines the format: `0x01` means 4 bytes of IPv4 address follow, `0x04` means 16 bytes of IPv6, and `0x03` means a length byte followed by the domain name. When the client sends a domain name (ATYP=0x03), the proxy resolves DNS on its side, which prevents DNS leaks to the client's local network.

The proxy connects to the destination and responds with a reply:

```python
[
    0x05,       # VER: Protocol version (5)
    0x00,       # REP: 0x00=success, 0x01-0x08=various errors
    0x00,       # RSV: Reserved
    0x01,       # ATYP: Address type of bound address
    *bind_addr, # BND.ADDR: Address the proxy bound to
    *bind_port  # BND.PORT: Port the proxy bound to
]
```

Reply codes: `0x00` succeeded, `0x01` general failure, `0x02` connection not allowed, `0x03` network unreachable, `0x04` host unreachable, `0x05` connection refused, `0x06` TTL expired, `0x07` command not supported, `0x08` address type not supported.

After a successful reply, the proxy begins relaying data bidirectionally. The entire SOCKS5 handshake is a binary protocol, making it more efficient than text-based HTTP but harder to debug without hex dumps.

## UDP Support

SOCKS5 supports UDP proxying through the `UDP ASSOCIATE` command (CMD=0x03). This works differently from TCP proxying: the client sends a UDP ASSOCIATE request over the TCP control connection, and the proxy responds with a relay address and port. The client then sends UDP datagrams to this relay, and the proxy forwards them to their destinations.

```mermaid
sequenceDiagram
    participant Client
    participant SOCKS5
    participant UDP_Server as UDP Server

    Note over Client,SOCKS5: TCP control connection (handshake + auth)
    Client->>SOCKS5: UDP ASSOCIATE request (CMD=0x03)
    SOCKS5->>Client: Relay address and port

    Note over Client,SOCKS5: UDP data transfer
    Client->>SOCKS5: UDP datagram to relay
    SOCKS5->>UDP_Server: Forward datagram
    UDP_Server->>SOCKS5: Response datagram
    SOCKS5->>Client: Forward response

    Note over Client,SOCKS5: TCP control connection stays open
```

Each UDP datagram sent through the relay includes a small header with the destination address and port:

```python
[
    0x00, 0x00,    # RSV: Reserved
    0x00,          # FRAG: Fragment number (0 = no fragmentation)
    0x01,          # ATYP: Address type
    *dst_addr,     # DST.ADDR: Destination address
    *dst_port,     # DST.PORT: Destination port
    *data          # DATA: Application data
]
```

The TCP control connection must remain open for the duration of the UDP association. If it closes, the proxy drops the UDP relay.

!!! warning "UDP in Chrome"
    Chrome does not use SOCKS5 UDP ASSOCIATE for any traffic. Even when configured with a SOCKS5 proxy, Chrome only proxies TCP connections. WebRTC, DNS-over-UDP, and other UDP traffic are not routed through the SOCKS5 proxy. This means WebRTC IP leaks are still possible with SOCKS5 in Chrome. Use `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` or Pydoll's `webrtc_leak_protection = True` to mitigate this. For more details, see [Network Fundamentals: WebRTC and IP Leakage](./network-fundamentals.md#webrtc-and-ip-leakage).

!!! tip "Modern UDP Proxying Alternatives"
    For scenarios requiring full UDP support beyond what Chrome's SOCKS5 implementation provides, consider Shadowsocks (encrypted SOCKS-like protocol with native UDP), WireGuard (VPN with excellent performance), or V2Ray/VMess (flexible proxy framework with comprehensive UDP handling).

## DNS Resolution

A common misconception is that HTTP proxies leak DNS queries while SOCKS5 proxies do not. The reality in Chrome is more nuanced.

When Chrome is configured with any proxy (HTTP, HTTPS, or SOCKS5), it sends hostnames to the proxy rather than resolving DNS locally. For HTTP proxies, the hostname appears in the `CONNECT host:443` request. For SOCKS5, it appears in the connection request with ATYP=0x03 (domain name). In both cases, the proxy resolves DNS on its side, and Chrome does not make local DNS queries for proxied traffic.

The real DNS privacy difference between the two proxy types is not who resolves DNS, but what the proxy sees at the application layer. An HTTP proxy sees the full URL for unencrypted requests and the hostname for CONNECT requests. A SOCKS5 proxy sees only the destination hostname and port as opaque connection parameters.

However, there is an important caveat: Chrome's DNS prefetcher can make local DNS queries for hostnames found in page content, even when a proxy is configured. This can leak the domains you are browsing to your local DNS resolver. To prevent this, disable DNS prefetching or use the flag `--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"`.

!!! note "`socks5://` vs `socks5h://`"
    Many tools outside Chrome distinguish between `socks5://` (client resolves DNS) and `socks5h://` (proxy resolves DNS, the "h" stands for hostname). Chrome always resolves DNS proxy-side for SOCKS5, behaving like `socks5h://` regardless of which scheme you use. But if you use tools like `curl`, Firefox, or Python libraries alongside Pydoll, the distinction matters: always use `socks5h://` to prevent DNS leaks.

## SOCKS5 and MITM Resistance

SOCKS5 is often described as "MITM-resistant." This is true in a specific sense: because SOCKS5 does not understand or interact with TLS, it has no mechanism to terminate a TLS connection and re-encrypt it. A SOCKS5 proxy simply relays encrypted bytes without modification.

An HTTP proxy, by contrast, can perform TLS termination (MITM) by presenting its own certificate to the client, decrypting the traffic, inspecting or modifying it, and re-encrypting it toward the server. This requires the client to trust the proxy's CA certificate, and it is detectable through certificate pinning and Certificate Transparency logs. The normal behavior of an HTTP proxy with HTTPS (using CONNECT) is to create a transparent tunnel without termination, but the architectural possibility of MITM exists.

With SOCKS5, TLS termination is not possible at the protocol level. The proxy cannot inject itself into the TLS handshake because it does not parse the application data flowing through it. The end-to-end encryption between client and server is preserved by design.

It is worth noting that TLS is what provides the actual cryptographic protection, not SOCKS5 itself. If you send unencrypted HTTP through a SOCKS5 proxy, the proxy operator can read everything. The security advantage of SOCKS5 is architectural (it does not require or enable TLS termination), not cryptographic.

## TLS and Browser Fingerprinting Through SOCKS5

An important limitation to understand: SOCKS5 does not change your browser's fingerprint. The TLS handshake (ClientHello) passes through the SOCKS5 proxy byte-for-byte, which means the target server sees your browser's exact JA3/JA4 fingerprint. The same applies to HTTP/2 SETTINGS frames, browser-specific header ordering, and all other application-layer fingerprinting signals.

SOCKS5 hides your IP address and prevents the proxy from injecting identifying headers. It does not help with any form of browser or behavioral fingerprinting. For a complete evasion strategy, you need to address fingerprinting at multiple layers. See [Evasion Techniques](../fingerprinting/evasion-techniques.md) for details.

## SOCKS5 Authentication in Chrome

Chrome does not support SOCKS5 username/password authentication. This is a longstanding limitation tracked as [Chromium Issue #40323993](https://issues.chromium.org/issues/40323993). When Chrome performs the SOCKS5 method negotiation, it only offers method `0x00` (no authentication). If the proxy requires authentication, the connection fails silently.

This is fundamentally different from HTTP proxy authentication. HTTP proxies authenticate via HTTP status codes (`407 Proxy Authentication Required`), which Chrome handles through the Fetch domain in CDP. Pydoll intercepts these `Fetch.authRequired` events and responds with stored credentials automatically. SOCKS5 authentication, on the other hand, happens during a binary protocol handshake at the session layer, before any HTTP traffic exists. There is no HTTP 407, no `Fetch.authRequired` event, and no way for CDP-based tools to inject credentials into this process.

Configuring `--proxy-server=socks5://user:pass@proxy:1080` does not work. Chrome silently ignores the embedded credentials.

### Pydoll's SOCKS5Forwarder

The standard solution is a local proxy forwarder: a lightweight SOCKS5 server running on localhost that accepts unauthenticated connections from Chrome and forwards them to the remote proxy with full authentication.

```mermaid
sequenceDiagram
    participant Chrome
    participant Forwarder as Local Forwarder<br/>(127.0.0.1:1081)
    participant Remote as Remote SOCKS5 Proxy<br/>(proxy:1080)
    participant Server as Destination Server

    Note over Chrome,Forwarder: No authentication
    Chrome->>Forwarder: SOCKS5 Hello [methods: 0x00]
    Forwarder->>Chrome: Method selected [0x00]
    Chrome->>Forwarder: CONNECT example.com:443

    Note over Forwarder,Remote: With authentication
    Forwarder->>Remote: SOCKS5 Hello [methods: 0x02]
    Remote->>Forwarder: Method selected [0x02]
    Forwarder->>Remote: Auth [username, password]
    Remote->>Forwarder: Auth OK
    Forwarder->>Remote: CONNECT example.com:443
    Remote->>Server: TCP connection
    Remote->>Forwarder: Connect OK

    Forwarder->>Chrome: Connect OK

    Note over Chrome,Server: Bidirectional data relay
    Chrome->>Forwarder: TLS + application data
    Forwarder->>Remote: Forward
    Remote->>Server: Forward
    Server->>Remote: Response
    Remote->>Forwarder: Forward
    Forwarder->>Chrome: Forward
```

Pydoll provides a built-in `SOCKS5Forwarder` in the `pydoll.utils` module. It is a pure-Python, zero-dependency async implementation that handles the full SOCKS5 handshake with the remote proxy, including username/password authentication (RFC 1929), IPv4, IPv6, and domain address types.

```python
import asyncio
from pydoll.utils import SOCKS5Forwarder
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,  # Use 0 for auto-assigned port
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

The forwarder can also run as a standalone CLI tool for testing or use with other applications:

```bash
python -m pydoll.utils.socks5_proxy_forwarder \
    --remote-host proxy.example.com \
    --remote-port 1080 \
    --username myuser \
    --password mypass \
    --local-port 1081
```

The forwarder binds to `127.0.0.1` by default, making it accessible only from your machine. Never bind to `0.0.0.0` in production, as this would expose an unauthenticated SOCKS5 proxy to the network. Credentials are never logged in plaintext. The forwarder adds sub-millisecond latency since all communication happens over the local loopback interface.

!!! tip "Restricted Environments"
    Some environments (Docker containers, serverless platforms, hardened VMs) may restrict binding to local ports. Use `local_port=0` to let the OS assign an available port. If local binding is completely blocked, consider using an HTTP CONNECT proxy instead, which Chrome supports natively with authentication via Pydoll's ProxyManager.

## Practical Configuration

**Basic SOCKS5 (no authentication):**

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
```

**SOCKS5 with authentication (via SOCKS5Forwarder):**

See the [SOCKS5Forwarder section](#pydolls-socks5forwarder) above.

**Preventing leaks:**

For a complete SOCKS5 setup, you should also prevent WebRTC and DNS prefetch leaks:

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.webrtc_leak_protection = True  # Prevents WebRTC IP leaks
options.add_argument('--disable-quic')  # Forces HTTP/2 over TCP through proxy
```

**Testing your setup:**

Always verify your proxy configuration with leak tests. Visit [browserleaks.com/ip](https://browserleaks.com/ip) to confirm your IP, [browserleaks.com/webrtc](https://browserleaks.com/webrtc) to check for WebRTC leaks, and [dnsleaktest.com](https://dnsleaktest.com/) to verify DNS is not leaking.

## Summary

SOCKS5 provides protocol-agnostic proxying with a smaller trust surface than HTTP proxies. It does not parse, modify, or inject anything into your traffic. DNS resolution happens proxy-side in Chrome. TLS encryption is preserved end-to-end. The main limitation in Chrome is the lack of native SOCKS5 authentication (solved by Pydoll's `SOCKS5Forwarder`) and the absence of UDP proxying (mitigated by disabling WebRTC or using the appropriate browser flags).

SOCKS5 does not change your browser's TLS fingerprint, HTTP/2 settings, or any application-layer characteristics. For complete evasion, combine SOCKS5 with browser fingerprint management and behavioral simulation.

**Next steps:**

- [Proxy Detection](./proxy-detection.md): How even SOCKS5 proxies can be detected
- [Building Proxies](./build-proxy.md): Implement your own SOCKS5 server
- [Proxy Configuration](../../features/configuration/proxy.md): Practical Pydoll proxy setup
- [Evasion Techniques](../fingerprinting/evasion-techniques.md): Multi-layer evasion strategy

## References

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 1961: GSS-API Authentication Method for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1961
- RFC 3089: SOCKS-based IPv6/IPv4 Gateway Mechanism (2001) - https://datatracker.ietf.org/doc/html/rfc3089
- Chromium Proxy Documentation - https://chromium.googlesource.com/chromium/src/+/689912289c/net/docs/proxy.md
- Chromium Issue #40323993: SOCKS5 Authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- DNS Leak Test - https://dnsleaktest.com/
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
