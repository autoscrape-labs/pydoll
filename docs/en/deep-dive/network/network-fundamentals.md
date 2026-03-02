# Network Fundamentals

This document covers the foundational network protocols that power the internet and how they can expose or protect your identity in automation scenarios. A working understanding of TCP, UDP, the OSI model, and WebRTC will make proxy configuration far less mysterious and far more effective.

!!! info "Module Navigation"
    - [Network & Security Overview](./index.md): Module introduction and learning path
    - [HTTP/HTTPS Proxies](./http-proxies.md): Application-layer proxying
    - [SOCKS Proxies](./socks-proxies.md): Session-layer proxying

    For practical Pydoll usage, see [Proxy Configuration](../../features/configuration/proxy.md) and [Browser Options](../../features/configuration/browser-options.md).

## The Network Stack

Every HTTP request your browser makes travels through a layered network stack. Each layer has specific responsibilities, protocols, and security implications. Proxies operate at different layers, and the layer determines what the proxy can see, modify, and hide. Network characteristics at lower layers can fingerprint your real system even through proxies, so understanding the stack helps you see where identity leaks happen and how to prevent them.

### The OSI Model

The OSI (Open Systems Interconnection) model, developed by ISO in 1984, provides a conceptual framework for understanding how network protocols interact. Real-world networks use the TCP/IP model (which predates OSI and has only 4 layers), but OSI terminology remains the standard way to describe where proxies operate and what they can access.

```mermaid
graph TD
    L7[Layer 7: Application - HTTP, FTP, SMTP, DNS]
    L6[Layer 6: Presentation - Encryption, Compression]
    L5[Layer 5: Session - SOCKS]
    L4[Layer 4: Transport - TCP, UDP]
    L3[Layer 3: Network - IP, ICMP]
    L2[Layer 2: Data Link - Ethernet, WiFi]
    L1[Layer 1: Physical - Cables, Radio Waves]

    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

Layer 7 (Application) is where user-facing protocols live: HTTP, HTTPS, FTP, SMTP, and DNS all operate here. This layer contains the actual data your application cares about, such as HTML documents, JSON responses, and file transfers. HTTP proxies operate at this layer, which gives them full visibility into request and response content.

Layer 6 (Presentation) handles data format translation, encryption, and compression. SSL/TLS is commonly associated with this layer for its encryption role, though in practice TLS straddles Layers 4 through 6 and does not map cleanly to any single OSI layer. What matters for automation is that HTTPS encryption happens here, encrypting Layer 7 data before it moves down the stack.

Layer 5 (Session) manages connections between applications. SOCKS proxies operate here, below the application layer but above transport. This position makes SOCKS protocol-agnostic: it can proxy any Layer 7 protocol (HTTP, FTP, SMTP, SSH) without needing to understand their specifics.

Layer 4 (Transport) provides end-to-end data delivery. TCP (connection-oriented, reliable) and UDP (connectionless, fast) are the dominant protocols here. This layer handles port numbers, flow control, and error correction. All proxies ultimately rely on Layer 4 for actual data transmission.

Layer 3 (Network) handles routing and addressing between networks. IP (Internet Protocol) operates here, managing IP addresses and routing decisions. This is where your real IP address lives, and where proxies aim to substitute it.

Layer 2 (Data Link) manages communication on the same physical network segment. Ethernet, Wi-Fi, and PPP operate here, handling MAC addresses and frame transmission. MAC addresses are only visible on the local network segment and are not directly accessible by remote servers, though they can be exposed through protocols like IPv6 SLAAC (which embeds the MAC in the address).

Layer 1 (Physical) is the actual hardware: cables, radio waves, and voltage levels. Rarely relevant to software automation.

!!! tip "OSI vs TCP/IP"
    The TCP/IP model (4 layers: Link, Internet, Transport, Application) is what networks actually use. OSI (7 layers) is a teaching tool and reference model. When people say "Layer 7 proxy," they are using OSI terminology, but the actual implementation runs on TCP/IP.

### How Layer Positioning Affects Proxies

The layer where a proxy operates determines what it can and cannot do.

HTTP/HTTPS proxies operate at Layer 7 (Application). Because they understand HTTP, they can read and modify URLs, headers, cookies, and request bodies. They can cache responses intelligently based on HTTP semantics, filter content by URL or keyword, and inject authentication headers. The trade-off is that they only understand HTTP. They cannot proxy FTP, SMTP, SSH, or other protocols, and inspecting HTTPS content requires TLS termination, which means decrypting and re-encrypting the traffic.

SOCKS proxies operate at Layer 5 (Session). Because they sit below the application layer, they are protocol-agnostic and can proxy any Layer 7 protocol without modification. HTTPS traffic passes through encrypted end-to-end, since the SOCKS proxy never needs to decrypt it. SOCKS5 also supports UDP, enabling it to proxy DNS queries, VoIP, and other UDP-based protocols. The trade-off is that SOCKS proxies have no visibility into application-layer data: they cannot cache, filter by URL, or inspect content. They can only filter by IP and port.

!!! note "The Fundamental Tradeoff"
    Higher layers (Layer 7) give you more control but less flexibility. Lower layers (Layer 5) give you less control but more flexibility. Choose HTTP proxies when you need content control, and SOCKS proxies when you need protocol flexibility or end-to-end encryption.

### The Layer Leak Problem

Even with a perfect Layer 7 proxy, lower-layer characteristics can expose your real identity. Your operating system's TCP stack at Layer 4 has a unique fingerprint defined by window size, options order, and TTL values. IP header fields at Layer 3 such as TTL and fragmentation behavior reveal your OS and network topology.

For example, if you configure a proxy to present a "Windows 10" User-Agent but your actual Linux system's TCP fingerprint contradicts this at Layer 4, sophisticated detection systems can flag this inconsistency as a strong bot indicator. This is why network-level fingerprinting (covered in [Network Fingerprinting](../fingerprinting/network-fingerprinting.md)) is so dangerous: it operates below the proxy layer, exposing your real system even when application-layer proxying is flawless.

## TCP vs UDP

At Layer 4 (Transport), two fundamentally different protocols dominate internet communication. They represent opposite design philosophies: reliability versus speed.

TCP is connection-oriented. Think of it like a phone call: you establish a connection, verify the other party is listening, exchange data reliably, then hang up. Every byte is acknowledged, ordered, and guaranteed to arrive. UDP is connectionless. You send your data and hope it arrives. No handshake, no acknowledgments, no guarantees. Just raw speed with minimal overhead.

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Connection-oriented (handshake required) | Connectionless (no handshake) |
| Reliability | Guaranteed delivery, ordered packets | Best-effort delivery, packets may be lost |
| Speed | Slower (overhead from reliability mechanisms) | Faster (minimal overhead) |
| Use Cases | Web browsing, file transfer, email | Video streaming, DNS queries, gaming |
| Header Size | 20 bytes minimum (up to 60 with options) | 8 bytes fixed |
| Flow Control | Yes (sliding window, receiver-driven) | No (sender transmits at will) |
| Congestion Control | Yes (slows down when network is congested) | No (application's responsibility) |
| Error Checking | Extensive (checksum + acknowledgments) | Basic (checksum only; optional in IPv4, mandatory in IPv6) |
| Ordering | Packets reordered if received out-of-sequence | No ordering, packets delivered as received |
| Retransmission | Automatic (lost packets retransmitted) | None (application must handle) |

### TCP and Proxies

All proxy protocols (HTTP, HTTPS, SOCKS4, SOCKS5) use TCP for their control channel. This is because proxy authentication and command exchange require guaranteed delivery, proxy protocols have strict command sequences (handshake, then auth, then data), and proxies need persistent connections to track client state.

However, SOCKS5 can also proxy UDP traffic, unlike SOCKS4 or HTTP proxies. This makes SOCKS5 essential for proxying DNS queries, WebRTC audio/video, VoIP, and gaming protocols.

!!! danger "UDP and IP Leakage"
    Most browser connections use TCP (HTTP, WebSocket, etc.), but WebRTC uses UDP directly, bypassing the browser's proxy configuration. This is the most common cause of IP leakage in proxied browser automation: your TCP traffic goes through the proxy while your UDP traffic leaks your real IP.

### The TCP Three-Way Handshake

Before any data can be transmitted, TCP requires a three-way handshake to establish a connection. This negotiation synchronizes sequence numbers, agrees on window sizes, and establishes connection state on both ends.

```mermaid
sequenceDiagram
    participant Client
    participant Server

    Client->>Server: SYN (Synchronize, seq=x)
    Note over Client,Server: Client requests connection

    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: Server acknowledges and sends its own SYN

    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: Connection established, data transfer begins
```

The process starts when the client sends a SYN (Synchronize) packet containing a random Initial Sequence Number (ISN), for example `seq=1000`. Along with the ISN, TCP options are negotiated: window size, Maximum Segment Size (MSS), timestamps, and SACK support.

The server responds with a SYN-ACK: it picks its own random ISN (e.g., `seq=5000`) and acknowledges the client's ISN by setting `ack=1001` (client's ISN + 1). This single packet both establishes the server-to-client direction (SYN) and confirms the client-to-server direction (ACK). The server also returns its own TCP options.

The client then sends a final ACK, acknowledging the server's ISN (`ack=5001`). At this point the connection is fully established in both directions and data transmission can begin.

The ISN is randomized rather than starting from zero to prevent TCP hijacking attacks. If ISNs were predictable, an attacker could inject packets into an existing connection by guessing the sequence numbers. Modern systems use cryptographic randomness for ISN selection (RFC 6528).

### TCP Fingerprinting

The TCP handshake reveals characteristics that fingerprint your operating system. Different OSes use different default values for the initial window size, TCP options order, TTL (Time To Live), window scale factor, and timestamp behavior. These values are set by the kernel, not the browser, so a proxy cannot change them.

Here are illustrative examples for modern operating systems. Note that actual values vary across OS versions, kernel configurations, and network tuning:

```
Windows 10/11 (modern builds):
    Window Size: 65535
    MSS: 1460
    Options: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (kernel 5.x+, Ubuntu 20.04+):
    Window Size: 29200
    MSS: 1460
    Options: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64

macOS (Monterey+):
    Window Size: 65535
    TTL: 64
```

These differences are burned into the kernel. A proxy cannot change them because they are set by your operating system, not your browser. This is how sophisticated detection systems can identify you even through proxies.

!!! warning "Proxy Limitation"
    HTTP and SOCKS proxies operate above the TCP layer. They cannot modify TCP handshake characteristics. Your OS's TCP fingerprint is always exposed to the proxy server and any network observers between you and the proxy. Only VPN-level solutions or OS-level TCP stack configuration can address this.

!!! note "Beyond TCP Fingerprinting"
    The TCP handshake is just the first fingerprinting opportunity. Immediately after, the TLS handshake reveals another unique fingerprint known as JA3/JA4. See [Network Fingerprinting](../fingerprinting/network-fingerprinting.md) for details on TLS and HTTP/2 fingerprinting.

### UDP

Unlike TCP's reliable, connection-oriented approach, UDP is a fire-and-forget protocol. It trades reliability for minimal latency and overhead, making it ideal for real-time applications where speed matters more than perfect delivery.

A UDP datagram has only an 8-byte header (compared to TCP's 20-60 bytes), containing source port, destination port, length, and a checksum. There is no connection establishment, no reliability guarantee, no flow control, and no congestion control. If a packet is lost, the application must decide whether and how to handle it.

UDP is the right choice for real-time communication (voice/video calls via WebRTC and VoIP), gaming (low-latency state updates), streaming (where occasional frame loss is acceptable), and DNS queries (small request/response pairs where the application handles retries). It is a poor choice for file transfers, web browsing, email, or databases, all of which need reliable, ordered delivery.

DNS is a particularly important example in the context of automation. DNS uses UDP because queries are typically small and benefit from UDP's zero-handshake overhead. While EDNS0 (RFC 6891) increased the maximum UDP DNS payload beyond the original 512-byte limit, most queries remain compact. The DNS client handles retries at the application level if a response does not arrive within a timeout.

For browser automation, the key concern with UDP is that WebRTC uses it for real-time audio and video, DNS queries use it for domain resolution, and most proxies (HTTP, HTTPS, SOCKS4) only handle TCP. Unless you explicitly configure UDP proxying, this traffic bypasses your proxy and leaks your real IP.

| Proxy Type | UDP Support | Notes |
|------------|-------------|-------|
| HTTP Proxy | No | Only proxies TCP-based HTTP/HTTPS |
| HTTPS Proxy (CONNECT) | No | CONNECT method only establishes TCP tunnels |
| SOCKS4 | No | TCP-only protocol |
| SOCKS5 | Yes | Supports UDP relay via `UDP ASSOCIATE` command |
| VPN | Yes | Tunnels all IP traffic (TCP and UDP) |

For true anonymity in browser automation, you need either a SOCKS5 proxy with UDP support and WebRTC configured to use it, WebRTC disabled entirely (which breaks video conferencing), a VPN that tunnels all traffic, or the browser flag `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`.

### QUIC and HTTP/3

Modern browsers increasingly use QUIC (RFC 9000), a UDP-based transport protocol that powers HTTP/3. Since QUIC runs over UDP, it shares the same proxy bypass issues as WebRTC and DNS: most HTTP proxies cannot handle QUIC traffic, and it may leak outside your proxy configuration.

In automation scenarios, consider disabling QUIC with the `--disable-quic` Chrome flag to force HTTP/2 over TCP, ensuring all web traffic passes through your proxy. QUIC also has its own fingerprinting characteristics, similar to JA3 for TLS, which adds another vector for detection.

## WebRTC and IP Leakage

WebRTC (Web Real-Time Communication) is a browser API standardized by the W3C that enables peer-to-peer audio, video, and data communication directly between browsers without plugins or intermediary servers. While powerful for real-time applications, WebRTC is the single biggest source of IP leakage in proxied browser automation.

### How WebRTC Leaks Your IP

WebRTC was designed for direct peer-to-peer connections, optimizing for low latency over privacy. To establish P2P connections, WebRTC must discover your real public IP address and share it with the remote peer, even if your browser is configured to use a proxy.

The problem unfolds like this: your browser uses a proxy for HTTP/HTTPS traffic (which is TCP), but WebRTC uses STUN servers to discover your real public IP over UDP. STUN queries bypass the proxy because most proxies only handle TCP. Your real IP is discovered and shared with remote peers as part of the connection negotiation. JavaScript on the page can read these "ICE candidates" and send your real IP to the website's server.

!!! danger "Severity of WebRTC Leaks"
    Even with an HTTP proxy configured correctly, HTTPS proxy working, DNS queries proxied, User-Agent spoofed, and canvas fingerprinting mitigated, WebRTC can still leak your real IP in milliseconds. This is because WebRTC operates below the browser's proxy layer, directly interfacing with the OS network stack.

### The ICE Process

WebRTC uses ICE (Interactive Connectivity Establishment, RFC 8445) to discover possible connection paths and select the best one. This process inherently reveals your network topology by gathering three types of candidates.

```mermaid
sequenceDiagram
    participant Browser
    participant STUN as STUN Server
    participant TURN as TURN Relay
    participant Peer as Remote Peer

    Note over Browser: WebRTC connection initiated

    Browser->>Browser: Gather local IP addresses<br/>(LAN interfaces)
    Note over Browser: Local candidate:<br/>192.168.1.100:54321

    Browser->>STUN: STUN Binding Request (over UDP)
    Note over STUN: STUN server discovers public IP<br/>(bypasses proxy!)
    STUN->>Browser: STUN Response with real public IP
    Note over Browser: Server reflexive candidate:<br/>203.0.113.45:54321

    Browser->>TURN: Allocate relay (if needed)
    TURN->>Browser: Relay address assigned
    Note over Browser: Relay candidate:<br/>198.51.100.10:61234

    Browser->>Peer: Send all ICE candidates<br/>(local + public + relay)
    Note over Peer: Now knows your:<br/>- LAN IP<br/>- Real public IP<br/>- Relay address

    Peer->>Browser: Send ICE candidates

    Note over Browser,Peer: ICE negotiation: try direct P2P first

    alt Direct P2P succeeds
        Browser<<->>Peer: Direct connection (bypasses proxy entirely!)
    else Direct P2P fails (firewall/NAT)
        Browser->>TURN: Use TURN relay
        TURN<<->>Peer: Relayed connection
        Note over Browser,Peer: Higher latency, but works
    end
```

### ICE Candidate Types

ICE discovers three types of candidates (possible connection endpoints), each revealing different information about your network.

**Host candidates** are your local LAN IP addresses. The browser enumerates all local network interfaces and creates candidates for each. This reveals your local IP addresses on private networks, your network topology (presence of VPN interfaces, VM bridges), and the number of network interfaces.

```javascript
// Example host candidates
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
```

Modern browsers (Chrome 75+, Firefox 78+, Safari) mitigate host candidate leaks by replacing local IP addresses with ephemeral mDNS names (e.g., `a1b2c3d4.local`) when media permissions (camera/microphone) have not been granted. However, server reflexive candidates (your public IP) remain exposed regardless of mDNS.

**Server reflexive candidates** are your public IP as seen by a STUN server. The browser sends a STUN request to a public server, which replies with your public IP address. This is the leak everyone talks about: your proxy shows one IP but WebRTC reveals your real one, along with your NAT type, external port mapping, and ISP information.

```javascript
// Server reflexive candidate (your real public IP)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**Relay candidates** are TURN server addresses used as fallback when direct P2P fails. The relay candidate may still contain your real IP in the `raddr` (remote address) field, depending on the TURN server implementation.

```javascript
// Relay candidate (TURN server address)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

### The STUN Protocol

STUN (Session Traversal Utilities for NAT, RFC 8489) is a simple request-response protocol over UDP. Its job is straightforward: the client asks "what IP do you see me as?" and the server replies with the client's public IP and port.

The client sends a Binding Request containing a magic cookie (`0x2112A442`, a fixed value defined by the RFC) and a random 12-byte transaction ID. The server responds with a Binding Success Response that includes an `XOR-MAPPED-ADDRESS` attribute containing the client's public IP and port as seen from the server's perspective.

The IP address in the response is XOR'ed with the magic cookie and transaction ID. This is not for security but for NAT compatibility: some NAT devices incorrectly modify IP addresses in packet payloads, and XOR'ing obfuscates the address to prevent this interference.

Common public STUN servers used by browsers include `stun.l.google.com:19302` (Google), `stun1.l.google.com:19302` (Google), `stun.services.mozilla.com` (Mozilla), and `stun.stunprotocol.org:3478`.

### Why Proxies Cannot Stop WebRTC Leaks

WebRTC leaks happen for several reinforcing reasons. First, WebRTC uses UDP, and most proxies (HTTP, HTTPS CONNECT, SOCKS4) only handle TCP. Only SOCKS5 supports UDP, and even then the browser must be explicitly configured to route WebRTC through it.

Second, WebRTC is a browser API that operates below the HTTP layer. It directly accesses the OS network stack, bypassing proxy settings configured for HTTP/HTTPS. STUN queries go directly to the network interface, and the OS routing table determines their path, not the browser's proxy configuration. Only VPN-level routing can intercept them.

Third, WebRTC enumerates all network interfaces (physical ethernet, Wi-Fi, VPN adapters, VM bridges), including interfaces not used for regular browsing. This leaks your internal network topology.

Finally, web pages can read ICE candidates via JavaScript using the `RTCPeerConnection.onicecandidate` event, extract IP addresses from candidate strings with a simple regex, and send your real IP to their tracking server.

### Preventing WebRTC Leaks in Pydoll

Pydoll provides multiple strategies for preventing WebRTC IP leaks.

**Method 1: Force WebRTC to only use proxied routes (recommended)**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # Adds --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Pydoll provides a convenient `webrtc_leak_protection` property that manages the underlying Chrome flag for you. This disables UDP if no proxy supports it, forces WebRTC to use TURN relays only (no direct P2P), and prevents STUN queries to public servers. The trade-off is higher latency for video calls since direct P2P connections are disabled.

**Method 2: Disable WebRTC entirely**

```python
options.add_argument('--disable-features=WebRTC')
```

This completely disables the WebRTC API, eliminating any possibility of IP leaks through this vector. The trade-off is that all WebRTC-dependent sites (video conferencing, voice calls) will break. Note that this flag should be tested with your specific Chrome version, as feature flag names can vary between releases.

**Method 3: Restrict WebRTC via browser preferences**

```python
options.browser_preferences = {
    'webrtc': {
        'ip_handling_policy': 'disable_non_proxied_udp',
        'multiple_routes_enabled': False,
        'nonproxied_udp_enabled': False,
        'allow_legacy_tls_protocols': False
    }
}
```

This achieves the same effect as Method 1 but through preferences rather than command-line flags. `multiple_routes_enabled` prevents using multiple network paths, and `nonproxied_udp_enabled` blocks UDP that does not go through the proxy.

**Method 4: Use a SOCKS5 proxy with UDP support**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

SOCKS5 can proxy UDP via its `UDP ASSOCIATE` command, allowing WebRTC's STUN queries to go through the proxy. This requires a SOCKS5 proxy that actually supports UDP relay, which not all do.

!!! warning "SOCKS5 Authentication"
    Chrome does not support SOCKS5 authentication inline (e.g., `socks5://user:pass@host:port`) via the `--proxy-server` flag. Pydoll provides a built-in `SOCKS5Forwarder` that works around this limitation by running a local unauthenticated SOCKS5 proxy that forwards traffic to the remote authenticated proxy, handling the username/password handshake on Chrome's behalf. See [Proxy Configuration](../../features/configuration/proxy.md) for usage details.

### Testing for WebRTC Leaks

You can test manually by visiting [browserleaks.com/webrtc](https://browserleaks.com/webrtc) and checking whether your real IP appears in the "Public IP Address" section. If you see your real IP instead of your proxy IP, you are leaking.

For automated testing with Pydoll:

```python
import asyncio
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_webrtc_leak():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/webrtc')

        await asyncio.sleep(3)

        ips = await tab.execute_script('''
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ''')

        print("Detected IPs:", ips)
        # Should only show proxy IP, not your real IP

asyncio.run(test_webrtc_leak())
```

!!! danger "Always Test WebRTC Leaks"
    Never assume your proxy configuration prevents WebRTC leaks. Always verify with [browserleaks.com/webrtc](https://browserleaks.com/webrtc) or [ipleak.net](https://ipleak.net). Even a single WebRTC leak instantly compromises your entire proxy setup, since the website now knows your real location, ISP, and network topology.

### How Websites Exploit WebRTC Leaks

Websites can intentionally trigger WebRTC to extract your real IP using a few lines of JavaScript:

```javascript
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);

        if (ipMatch) {
            const realIP = ipMatch[1];
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

This code creates an RTCPeerConnection, triggers ICE candidate gathering (which contacts STUN servers), extracts IP addresses from the candidates with a regex, and sends your real IP to a tracking server. Disabling WebRTC or forcing proxied-only routes as described above prevents this.

## Summary

Proxies operate at specific layers of the network stack: HTTP at Layer 7, SOCKS at Layer 5. The layer determines what the proxy can see, modify, and hide. TCP fingerprints (window size, options, TTL) leak from lower layers and reveal your real OS even through a proxy. UDP traffic, including WebRTC and DNS, often bypasses proxies unless explicitly configured. WebRTC is the most common source of IP leakage, and only SOCKS5 or a VPN can proxy UDP traffic effectively. Modern browsers also use QUIC (HTTP/3 over UDP), which adds another potential bypass vector.

**Next steps:**

- [HTTP/HTTPS Proxies](./http-proxies.md): Application-layer proxying
- [SOCKS Proxies](./socks-proxies.md): Session-layer, protocol-agnostic proxying
- [Network Fingerprinting](../fingerprinting/network-fingerprinting.md): TCP/IP and TLS fingerprinting techniques
- [Proxy Configuration](../../features/configuration/proxy.md): Practical Pydoll proxy setup

## References

- RFC 793: Transmission Control Protocol (TCP) - https://tools.ietf.org/html/rfc793
- RFC 768: User Datagram Protocol (UDP) - https://tools.ietf.org/html/rfc768
- RFC 8489: Session Traversal Utilities for NAT (STUN) - https://tools.ietf.org/html/rfc8489
- RFC 8445: Interactive Connectivity Establishment (ICE) - https://tools.ietf.org/html/rfc8445
- RFC 8656: Traversal Using Relays around NAT (TURN) - https://tools.ietf.org/html/rfc8656
- RFC 6528: Defending Against Sequence Number Attacks - https://tools.ietf.org/html/rfc6528
- RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport - https://tools.ietf.org/html/rfc9000
- W3C WebRTC 1.0: Real-Time Communication Between Browsers - https://www.w3.org/TR/webrtc/
- BrowserLeaks: WebRTC Leak Test - https://browserleaks.com/webrtc
- IPLeak: Comprehensive Leak Testing - https://ipleak.net
