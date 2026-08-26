# SOCKS proxies

A SOCKS proxy forwards raw TCP (and, in SOCKS5, UDP) connections without understanding what runs through them, which makes it a low-level, protocol-agnostic way to route traffic through another host. This page covers how SOCKS works, the difference between SOCKS4 and SOCKS5, the SOCKS5 handshake, DNS behavior, and the one thing that bites automation: Chrome does not do SOCKS5 authentication.

For practical setup, see the [Proxies](../../guides/proxies.md) guide; this page is the theory behind it.

## How SOCKS differs from HTTP proxies

The difference is what each proxy can see. An HTTP proxy works at the application layer and understands HTTP: it can read URLs, headers, and cookies (for unencrypted traffic), modify them in transit, cache responses, and add headers like `Via` and `X-Forwarded-For`. That is useful for filtering, but it means you trust the operator with your application data.

A SOCKS proxy works below the application layer. It sees the destination address, the port, and the volume of data, and nothing else. HTTP, HTTPS, SSH, WebSocket, or any custom protocol all look the same to it: bytes relayed between two endpoints. Send an HTTPS request through SOCKS5 and the proxy sees `example.com:443` and an encrypted TLS stream. It cannot read the URL, headers, or response, it does not add identifying headers, and it does not terminate TLS. The encrypted tunnel runs end to end.

SOCKS is a proxying protocol, not an encryption one. The name refers to secure firewall traversal, not cryptography. Unencrypted HTTP sent through SOCKS5 is still readable by the proxy operator, even though the proxy is not built to inspect it. For actual encryption you need TLS on top, or an encrypted tunnel (SSH, VPN) around the SOCKS connection.

!!! note "Trust model"
    With an HTTP proxy you trust the operator not to log your history, steal tokens, or modify responses. With SOCKS5 you trust it only to forward packets and not log connection metadata. The attack surface is smaller, not zero.

## SOCKS4 vs SOCKS5

SOCKS4 came from NEC in the early 1990s with no formal RFC. SOCKS5 was standardized as RFC 1928 in 1996 to fix SOCKS4's limitations.

| Feature | SOCKS4 | SOCKS5 |
|---------|--------|--------|
| Standard | De facto (1992), no RFC | RFC 1928 (1996) |
| Authentication | Identification only (USERID, no password) | None, username/password, or GSSAPI |
| IP version | IPv4 only | IPv4 and IPv6 |
| UDP support | No | Yes (UDP ASSOCIATE) |
| DNS resolution | Client-side (SOCKS4A adds server-side) | Server-side for domain names (ATYP=0x03) |

SOCKS5 is the better choice in every practical case. Use SOCKS4 only when a proxy does not support SOCKS5.

## The SOCKS5 handshake

A SOCKS5 connection follows RFC 1928 in three phases: method negotiation, optional authentication, then the connection request.

<iframe scrolling="no" src="/docs/resources/visuals/socks5-handshake.html" aria-label="The SOCKS5 handshake in real RFC 1928/1929 bytes: method negotiation, optional username/password auth, then the CONNECT request, decoded field by field" style="width: 100%; height: 860px; border: 0;" loading="lazy"></iframe>

### Phase 1: method negotiation

The client opens a TCP connection to the proxy and sends the protocol version (`0x05`) and the authentication methods it supports.

```python
# Client hello
[
    0x05,        # VER: version 5
    0x02,        # NMETHODS: number of methods offered
    0x00, 0x02,  # METHODS: no auth (0x00) and username/password (0x02)
]
```

The proxy replies with the method it chose. If it requires authentication and the client offered `0x02`, it selects that. If nothing acceptable was offered, it replies `0xFF` and closes the connection.

```python
# Server response
[
    0x05,  # VER: version 5
    0x02,  # METHOD: username/password selected
]
```

Method codes (RFC 1928): `0x00` no authentication, `0x01` GSSAPI, `0x02` username/password (RFC 1929), `0xFF` no acceptable methods.

### Phase 2: authentication

If the proxy selected `0x02`, the client sends credentials per RFC 1929. This subnegotiation uses its own version byte (`0x01`, not `0x05`).

```python
# Client authentication
[
    0x01,             # VER: subnegotiation version 1
    len(username),    # ULEN: username length (max 255)
    *username_bytes,  # UNAME
    len(password),    # PLEN: password length (max 255)
    *password_bytes,  # PASSWD
]

# Server response
[
    0x01,  # VER: subnegotiation version 1
    0x00,  # STATUS: 0 = success, non-zero = failure
]
```

Credentials travel in plaintext during this handshake; that is inherent to RFC 1929. For sensitive environments, wrap the SOCKS connection in an SSH tunnel or VPN.

### Phase 3: connection request

After authentication (or immediately, if none was required), the client sends the command, destination address, and port.

```python
[
    0x05,           # VER: version 5
    0x01,           # CMD: 1=CONNECT, 2=BIND, 3=UDP ASSOCIATE
    0x00,           # RSV: reserved
    0x03,           # ATYP: 1=IPv4, 3=domain, 4=IPv6
    len(domain),    # domain length (ATYP=0x03 only)
    *domain_bytes,  # domain name
    *port_bytes,    # port (2 bytes, big-endian)
]
```

The address type (ATYP) sets the format: `0x01` is 4 bytes of IPv4, `0x04` is 16 bytes of IPv6, and `0x03` is a length byte plus the domain name. When the client sends a domain name, the proxy resolves DNS on its side, which keeps DNS off the client's local network.

The proxy connects to the destination and replies:

```python
[
    0x05,        # VER: version 5
    0x00,        # REP: 0x00 success, 0x01-0x08 errors
    0x00,        # RSV: reserved
    0x01,        # ATYP: address type of the bound address
    *bind_addr,  # BND.ADDR
    *bind_port,  # BND.PORT
]
```

Reply codes: `0x00` succeeded, `0x01` general failure, `0x02` not allowed, `0x03` network unreachable, `0x04` host unreachable, `0x05` connection refused, `0x06` TTL expired, `0x07` command not supported, `0x08` address type not supported. After a success reply, the proxy relays data both ways. The handshake is binary, so it is efficient but hard to read without a hex dump.

## UDP support

SOCKS5 can proxy UDP through the `UDP ASSOCIATE` command (CMD=0x03). The client sends the request over the TCP control connection, and the proxy returns a relay address and port. The client then sends UDP datagrams to that relay, each prefixed with a small header naming the destination:

```python
[
    0x00, 0x00,  # RSV: reserved
    0x00,        # FRAG: fragment number (0 = none)
    0x01,        # ATYP: address type
    *dst_addr,   # DST.ADDR
    *dst_port,   # DST.PORT
    *data,       # application data
]
```

The TCP control connection must stay open for the life of the association; if it closes, the proxy drops the UDP relay.

!!! warning "Chrome does not proxy UDP over SOCKS5"
    Even with a SOCKS5 proxy configured, Chrome only proxies TCP. WebRTC, DNS-over-UDP, and other UDP traffic bypass the proxy, so a WebRTC IP leak is still possible. Set `options.webrtc_leak_protection = True` (which adds `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`) to mitigate it. See [Network fundamentals](network-fundamentals.md).

## DNS resolution

A common belief is that HTTP proxies leak DNS while SOCKS5 does not. In Chrome the reality is more specific.

With any proxy configured (HTTP, HTTPS, or SOCKS5), Chrome hands hostnames to the proxy instead of resolving them locally. For an HTTP proxy the hostname is in the `CONNECT host:443` line; for SOCKS5 it is in the connection request with ATYP=0x03. In both cases the proxy resolves DNS, and Chrome makes no local DNS query for proxied traffic. The real difference is not who resolves DNS but what the proxy sees: an HTTP proxy sees the full URL of unencrypted requests and the hostname of CONNECT requests, while a SOCKS5 proxy sees only the destination host and port as opaque parameters.

One caveat: Chrome's DNS prefetcher can still make local queries for hostnames found in page content, which leaks the domains you browse to your local resolver. Disable DNS prefetching to prevent it.

!!! note "`socks5://` vs `socks5h://`"
    Many tools distinguish `socks5://` (client resolves DNS) from `socks5h://` (proxy resolves it). Chrome always resolves DNS proxy-side for SOCKS5, so it behaves like `socks5h://` either way. If you use curl, Firefox, or Python libraries alongside Pydoll, prefer `socks5h://` to avoid DNS leaks there.

## SOCKS5 and MITM resistance

SOCKS5 is often called MITM-resistant, and in one specific sense it is: because it does not understand TLS, it has no way to terminate and re-encrypt a TLS connection. It relays encrypted bytes untouched.

An HTTP proxy can perform TLS termination by presenting its own certificate, decrypting, inspecting or modifying, and re-encrypting toward the server. That requires the client to trust the proxy's CA, and it is detectable through certificate pinning and Certificate Transparency. The normal HTTPS behavior of an HTTP proxy (CONNECT) is a transparent tunnel without termination, but the possibility exists. With SOCKS5 it does not, because the proxy never touches the application data.

TLS is what provides the cryptographic protection here, not SOCKS5. The SOCKS5 advantage is architectural, that it neither requires nor enables TLS termination, not cryptographic.

## Fingerprinting through SOCKS5

SOCKS5 does not change your browser's fingerprint. The TLS ClientHello passes through byte for byte, so the server sees your exact JA3/JA4 fingerprint, and the same holds for HTTP/2 settings, header ordering, and every other application-layer signal. SOCKS5 hides your IP and stops the proxy from injecting headers; it does nothing for browser or behavioral fingerprinting. For that, address the other layers too: see [Evasion techniques](../../stealth/evasion-techniques.md).

## SOCKS5 authentication in Chrome

Chrome does not support SOCKS5 username/password authentication, a longstanding limitation tracked as [Chromium issue 40323993](https://issues.chromium.org/issues/40323993). During method negotiation Chrome offers only `0x00` (no authentication); if the proxy requires credentials, the connection fails silently. Setting `--proxy-server=socks5://user:pass@proxy:1080` does not work, because Chrome ignores the embedded credentials.

This differs from HTTP proxy auth. HTTP proxies authenticate with a `407 Proxy Authentication Required` status, which Chrome surfaces through the CDP Fetch domain; Pydoll answers those `Fetch.authRequired` events with your credentials automatically. SOCKS5 auth happens in a binary handshake before any HTTP exists, so there is no 407, no `Fetch.authRequired`, and no way for a CDP-based tool to inject credentials into it.

### Pydoll's SOCKS5Forwarder

The standard fix is a local forwarder: a small SOCKS5 server on localhost that accepts unauthenticated connections from Chrome and forwards them to the remote proxy with full authentication.

<iframe scrolling="no" src="/docs/resources/visuals/socks5-forwarder.html" aria-label="The pydoll SOCKS5Forwarder bridges two handshakes: a no-auth SOCKS5 handshake to Chrome on one side and a full authenticated handshake to the remote proxy on the other, injecting the credentials Chrome cannot send" style="width: 100%; height: 900px; border: 0;" loading="lazy"></iframe>

Pydoll ships `SOCKS5Forwarder` in `pydoll.utils`. It is a pure-Python, zero-dependency async implementation that handles the full handshake with the remote proxy, including username/password authentication and IPv4, IPv6, and domain address types.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.utils import SOCKS5Forwarder


async def main():
    forwarder = SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='myuser',
        password='mypass',
        local_port=1081,   # 0 lets the OS pick a free port
    )
    async with forwarder:
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server=socks5://127.0.0.1:{forwarder.local_port}')

        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to('https://httpbin.org/ip')

asyncio.run(main())
```

The forwarder binds to `127.0.0.1`, so it is reachable only from your machine. Do not bind it to `0.0.0.0`, which would expose an unauthenticated SOCKS5 proxy to the network. Because everything runs over the loopback interface, it adds sub-millisecond latency.

!!! tip "Restricted environments"
    Some environments (containers, serverless, hardened VMs) restrict binding to local ports. Use `local_port=0` to let the OS assign one. If local binding is blocked entirely, use an HTTP CONNECT proxy instead, which Chrome supports natively with authentication handled for you (see [Proxies](../../guides/proxies.md)).

## Related

- [HTTP/HTTPS proxies](http-proxies.md): the application-layer alternative.
- [Network fundamentals](network-fundamentals.md): the layers underneath.
- [Proxy detection](proxy-detection.md): how even SOCKS5 proxies get spotted.
- [Building a proxy server](build-proxy.md): implement a SOCKS5 server yourself.
- [Proxies](../../guides/proxies.md): configure proxies in Pydoll.

## References

- RFC 1928: SOCKS Protocol Version 5 (1996) - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 (1996) - https://datatracker.ietf.org/doc/html/rfc1929
- Chromium issue 40323993: SOCKS5 authentication - https://issues.chromium.org/issues/40323993
- BrowserLeaks: WebRTC leak test - https://browserleaks.com/webrtc
