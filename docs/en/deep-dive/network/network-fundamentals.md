# Network Fundamentals

This document covers the foundational network protocols that power the internet and how they expose or protect your identity in automation scenarios. Understanding TCP, UDP, the OSI model, and WebRTC is **essential** before diving into proxy protocols.

!!! info "Module Navigation"
    - **[← Network & Security Overview](./index.md)** - Module introduction and learning path
    - **[→ HTTP/HTTPS Proxies](./http-proxies.md)** - Application-layer proxying
    - **[→ SOCKS Proxies](./socks-proxies.md)** - Session-layer proxying
    
    For practical Pydoll usage, see **[Proxy Configuration](../../features/configuration/proxy.md)** and **[Browser Options](../../features/configuration/browser-options.md)**.

!!! warning "Foundation First"
    This is **prerequisite knowledge** for understanding proxy protocols. Without grasping these fundamentals, proxy configuration becomes trial-and-error guesswork.

## Introduction: The Network Stack

Every HTTP request your browser makes (every proxy connection, every WebSocket message) travels through a **layered network stack**. Each layer has specific responsibilities, protocols, and security implications.

**Why this matters for automation:**

- Proxies operate at **different layers**, each with different capabilities
- Network characteristics at lower layers can **fingerprint** your real system (even through proxies)
- Understanding the stack reveals **where identity leaks occur** and how to prevent them

Before diving into proxies, we need to understand the network stack they operate within. This isn't abstract theory. Every concept here has **direct implications** for stealth, performance, and reliability in browser automation.

### The OSI Model Context

The OSI (Open Systems Interconnection) model, developed by the International Organization for Standardization (ISO) in 1984, provides a **conceptual framework** for understanding how network protocols interact. While real-world networks primarily use the TCP/IP model (which predates OSI), understanding OSI layers helps conceptualize **where proxies operate** and **what they can inspect or modify**.

```mermaid
graph TD
    L7[Layer 7: Application - HTTP, FTP, SMTP]
    L6[Layer 6: Presentation - SSL/TLS, Encryption]
    L5[Layer 5: Session - SOCKS]
    L4[Layer 4: Transport - TCP, UDP]
    L3[Layer 3: Network - IP, ICMP]
    L2[Layer 2: Data Link - Ethernet, WiFi]
    L1[Layer 1: Physical - Cables, Radio Waves]
    
    L7 --> L6 --> L5 --> L4 --> L3 --> L2 --> L1
```

#### Layer-by-Layer Breakdown

**Layer 7 (Application)**: Where user-facing protocols live. HTTP, HTTPS, FTP, SMTP, DNS all operate here. This layer contains the **actual data** your application cares about: HTML documents, JSON responses, file transfers. HTTP proxies operate at this layer, giving them **full visibility** into request/response content.

**Layer 6 (Presentation)**: Handles data format translation, encryption, and compression. SSL/TLS encryption occurs here (though TLS is often considered to straddle Layers 5-6). This is where **HTTPS encryption** happens, encrypting Layer 7 data before passing it down to Layer 5.

**Layer 5 (Session)**: Manages connections between applications. SOCKS proxies operate here, below the application layer but above transport. This position makes SOCKS **protocol-agnostic**, it can proxy any Layer 7 protocol (HTTP, FTP, SMTP, SSH) without understanding their specifics.

**Layer 4 (Transport)**: Provides end-to-end data delivery. TCP (connection-oriented, reliable) and UDP (connectionless, fast) are the dominant protocols. This layer handles **port numbers**, **flow control**, and **error correction**. All proxies ultimately rely on Layer 4 for actual data transmission.

**Layer 3 (Network)**: Handles routing and addressing between networks. IP (Internet Protocol) operates here, managing **IP addresses** and **routing decisions**. This is where your **real IP address** lives, and where proxies aim to substitute it.

**Layer 2 (Data Link)**: Manages communication on the same physical network segment. Ethernet, Wi-Fi, and PPP operate here, handling **MAC addresses** and **frame transmission**. Network fingerprinting at this layer can reveal **physical network characteristics**.

**Layer 1 (Physical)**: The actual hardware (cables, radio waves, voltage levels). While rarely relevant to software, physical-layer characteristics can be measured (signal timing, electrical properties) for **advanced fingerprinting**.

!!! tip "OSI vs TCP/IP Models"
    The **TCP/IP model** (4 layers: Link, Internet, Transport, Application) is what networks actually use. OSI (7 layers) is a **teaching tool** and reference model. When people say "Layer 7 proxy," they're using OSI terminology, but the actual implementation uses TCP/IP.

#### Why Layer Positioning Matters for Proxies

The layer where a proxy operates determines its **capabilities** and **limitations**:

**HTTP/HTTPS Proxies (Layer 7 - Application)**:

- **Full HTTP visibility**: Can read/modify URLs, headers, cookies, request bodies
- **Intelligent caching**: Can cache responses based on HTTP semantics
- **Content filtering**: Can block specific URLs or keywords
- **Authentication integration**: Can add authentication headers
- **HTTP-only limitation**: Cannot proxy FTP, SMTP, SSH, or other protocols
- **TLS termination required**: Must decrypt HTTPS to inspect content

**SOCKS Proxies (Layer 5 - Session)**:

- **Protocol-agnostic**: Can proxy any Layer 7 protocol (HTTP, FTP, SSH, etc.)
- **No TLS termination**: HTTPS passes through encrypted (end-to-end security)
- **UDP support** (SOCKS5): Can proxy DNS, VoIP, gaming protocols
- **No content visibility**: Cannot inspect or modify application-layer data
- **No intelligent caching**: Doesn't understand HTTP semantics
- **No URL-based filtering**: Cannot block specific URLs, only IP:port combinations

!!! warning "The Fundamental Tradeoff"
    **Higher layers** (Layer 7) = More control, less flexibility
    **Lower layers** (Layer 5) = Less control, more flexibility
    
    Choose based on your needs: HTTP proxy for **content control**, SOCKS proxy for **protocol flexibility** and **end-to-end encryption**.

#### Practical Implication: The "Layer Leak" Problem

Understanding layers reveals a critical security issue: **characteristics leak across layers**.

Even with a perfect Layer 7 proxy (HTTP), lower-layer characteristics can expose your real identity:

- **Layer 4 (TCP)**: Your OS's TCP stack has a unique "fingerprint" (window size, options, TTL)
- **Layer 3 (Network)**: IP header fields (TTL, fragmentation) reveal OS and network topology
- **Layer 2 (Data Link)**: MAC address vendor reveals hardware manufacturer

**Example**: You configure a proxy to show "Windows 10" User-Agent, but your **actual Linux system's TCP fingerprint** (Layer 4) contradicts this. Instant bot detection.

This is why **network-level fingerprinting** (covered in [Network Fingerprinting](../fingerprinting/network-fingerprinting.md)) is so dangerous: it operates **below the proxy layer**, exposing your real system even when application-layer proxying is perfect.

### TCP vs UDP: Transport Layer Protocols

At Layer 4 (Transport), two fundamentally different protocols dominate internet communication: **TCP (Transmission Control Protocol)** and **UDP (User Datagram Protocol)**. They represent opposite design philosophies: reliability vs speed, overhead vs efficiency.

#### The Fundamental Difference

**TCP** is like a phone call: you establish a connection, verify the other party is listening, exchange data reliably, then hang up. Every byte is acknowledged, ordered, and guaranteed to arrive.

**UDP** is like shouting across a crowded room: you send your message and hope it arrives. No guarantees, no acknowledgments, no connection setup. Just raw speed.

| Feature | TCP | UDP |
|---------|-----|-----|
| **Connection** | Connection-oriented (handshake required) | Connectionless (no handshake) |
| **Reliability** | Guaranteed delivery, ordered packets | Best-effort delivery, packets may be lost |
| **Speed** | Slower (overhead from reliability mechanisms) | Faster (minimal overhead) |
| **Use Cases** | Web browsing, file transfer, email | Video streaming, DNS queries, gaming |
| **Header Size** | 20 bytes minimum (up to 60 with options) | 8 bytes fixed |
| **Flow Control** | Yes (sliding window, receiver-driven) | No (sender transmits at will) |
| **Congestion Control** | Yes (slows down when network is congested) | No (application's responsibility) |
| **Error Checking** | Extensive (checksum + acknowledgments) | Basic (checksum only, optional discard) |
| **Ordering** | Packets reordered if received out-of-sequence | No ordering, packets delivered as received |
| **Retransmission** | Automatic (lost packets retransmitted) | None (application must handle) |

#### Why This Matters for Proxies and Automation

**All proxy protocols use TCP**. HTTP proxies, HTTPS proxies, SOCKS4, and SOCKS5 all rely on TCP for their control channel because:

1. **Reliability**: Proxy authentication and command exchange require guaranteed delivery
2. **Ordering**: Proxy protocols have strict command sequences (handshake → auth → data)
3. **Connection state**: Proxies need persistent connections to track clients

However, **SOCKS5 can proxy UDP traffic** (unlike SOCKS4 or HTTP proxies), making it essential for:

- **DNS queries**: Fast domain resolution without TCP overhead
- **WebRTC**: Real-time audio/video (which uses UDP for low latency)
- **VoIP**: Voice communication requires speed over reliability
- **Gaming protocols**: Low-latency game state updates

!!! danger "UDP = IP Leakage Risk"
    Most browser connections use TCP (HTTP, WebSocket, etc.). But WebRTC uses **UDP directly**, bypassing the browser's network stack and proxy configuration. This is the **#1 cause of IP leakage** in proxied browser automation. Your real IP leaks through UDP while TCP traffic goes through the proxy.

#### TCP Three-Way Handshake: Establishing Connections

Before any data can be transmitted, TCP requires a **three-way handshake** to establish a connection. This negotiation synchronizes sequence numbers, agrees on window sizes, and establishes connection state on both ends.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    Client->>Server: SYN (Synchronize, seq=x)
    Note over Client,Server: Client requests connection
    
    Server->>Client: SYN-ACK (seq=y, ack=x+1)
    Note over Client,Server: Server acknowledges and sends its own SYN
    
    Client->>Server: ACK (ack=y+1)
    Note over Client,Server: Connection established
    
    Note over Client,Server: Data transfer begins
```

**Step-by-step breakdown:**

**1. SYN (Synchronize)**: Client initiates connection

- Client selects a **random Initial Sequence Number (ISN)** (e.g., `seq=1000`)
- Sends SYN packet with this ISN to server
- TCP options negotiated: window size, Maximum Segment Size (MSS), timestamps, SACK support

**2. SYN-ACK (Synchronize-Acknowledge)**: Server responds

- Server selects its own **random ISN** (e.g., `seq=5000`)
- Acknowledges client's ISN: `ack=1001` (client's ISN + 1)
- Sends both SYN (to establish server→client direction) and ACK (to confirm client→server direction)
- Returns its own TCP options

**3. ACK (Acknowledge)**: Client confirms

- Client acknowledges server's ISN: `ack=5001` (server's ISN + 1)
- Connection now **established** in both directions
- Data transmission can begin

!!! tip "Why Random ISN?"
    The ISN is randomized (not starting from 0) to prevent **TCP hijacking attacks**. If ISNs were predictable, an attacker could inject packets into an existing connection by guessing the sequence numbers. Modern systems use cryptographic randomness for ISN selection (RFC 6528).

**Security Implication: TCP Fingerprinting**

The TCP handshake reveals numerous characteristics that **fingerprint your operating system**:

- **Initial Window Size**: Different OSes use different default values (Windows: 8192, Linux: 5840, macOS: 65535)
- **TCP Options**: Order and presence of options vary by OS (MSS, SACK, Timestamps, Window Scale)
- **TTL (Time To Live)**: Default values differ (Windows: 128, Linux: 64, macOS: 64)
- **Window Scale Factor**: Reveals buffer size preferences
- **Timestamp Value**: Timing patterns reveal system uptime and clock resolution

**Example TCP handshake fingerprint (captured with Wireshark)**:

```
Windows 10:
    Window Size: 8192
    MSS: 1460
    Options: MSS, NOP, WS, NOP, NOP, SACK_PERM
    TTL: 128

Linux (Ubuntu):
    Window Size: 29200
    MSS: 1460
    Options: MSS, SACK_PERM, TS, NOP, WS
    TTL: 64
```

These differences are **burned into the kernel**. A proxy cannot change them because they're set by your **operating system**, not your browser. This is how sophisticated detection systems identify you **even through proxies**.

!!! warning "Proxy Limitation"
    HTTP and SOCKS proxies operate **above the TCP layer**. They cannot modify TCP handshake characteristics. Your OS's TCP fingerprint is **always exposed** to the proxy server (and any network observers). Only **VPN-level solutions** or **OS-level TCP stack spoofing** can address this.

**Why TCP matters for proxies:**

- **Reliable proxy authentication**: Credentials sent over TCP won't be lost
- **Persistent connections**: Single TCP connection can handle multiple HTTP requests (HTTP/1.1 keep-alive, HTTP/2)
- **Ordered delivery**: Proxy commands execute in sequence (crucial for authentication flows)
- **Fingerprinting exposure**: TCP handshake characteristics reveal your real OS

#### UDP Characteristics: Speed Without Guarantees

Unlike TCP's reliable, connection-oriented approach, UDP is a **"fire-and-forget" protocol**. It trades reliability for **minimal latency and overhead**, making it ideal for real-time applications where speed matters more than perfect delivery.

**UDP Packet Structure (RFC 768)**:

```python
# UDP datagram structure (actual header format)
{
    'source_port': 12345,        # 16 bits - optional (0 = no response expected)
    'destination_port': 53,       # 16 bits - required (application identifier)
    'length': 42,                 # 16 bits - datagram size (header + data)
    'checksum': 0x1234,          # 16 bits - optional in IPv4, mandatory in IPv6
    'data': b'...'               # Variable - application data
}
# Total header: 8 bytes (vs TCP's 20-60 bytes)
```

**Key UDP Characteristics:**

1. **No Connection Establishment**: No handshake, no state. Just send the packet and hope it arrives.

2. **No Reliability**: Packets can be lost, duplicated, or arrive out of order. Application must handle these scenarios.

3. **No Flow Control**: Sender transmits as fast as it wants. No mechanism to slow down for receiver capacity.

4. **No Congestion Control**: UDP doesn't detect or respond to network congestion. Can overwhelm networks.

5. **Minimal Header**: Only 8 bytes vs TCP's 20-60 bytes. Lower overhead means more bandwidth for data.

6. **Port-Based Multiplexing**: Like TCP, uses port numbers to identify applications (DNS=53, WebRTC=dynamic)

**When to Use UDP:**

**Good use cases:**
- **Real-time communication**: Voice/video calls (WebRTC, VoIP) where old data is useless
- **Gaming**: Low-latency game state updates where speed > accuracy
- **Streaming**: Video/audio where occasional frame loss is acceptable
- **DNS queries**: Small request/response where retransmission is handled by application
- **Network discovery**: Broadcast/multicast protocols (DHCP, mDNS)

**Poor use cases:**
- **File transfer**: Would require application-level reliability (so just use TCP)
- **Web browsing**: Needs ordered, reliable delivery (HTTP/3 over QUIC is exception)
- **Email, databases**: Absolutely require reliability

**UDP and DNS: A Critical Example**

DNS (Domain Name System) uses UDP because:

- **Small messages**: DNS queries and responses typically fit in a single packet (<512 bytes)
- **Fast resolution**: No handshake overhead means faster lookups
- **Application-level retry**: DNS client retries if no response within timeout
- **Widespread**: Billions of DNS queries per second worldwide

```python
# Typical DNS query over UDP
Source Port: 54321 (random ephemeral port)
Destination Port: 53 (DNS standard port)
Length: 29 bytes (8-byte header + 21-byte query)
Checksum: 0x1a2b
Data: "google.com A?" (Query for A record)
```

**Why UDP matters for browser automation:**

- **WebRTC uses UDP** for real-time audio/video (can't be proxied by HTTP proxies)
- **DNS queries use UDP** (can leak DNS requests if not proxied)
- **SOCKS5 supports UDP** (unlike SOCKS4 or HTTP proxies)
- **UDP bypasses proxies** unless explicitly configured
- **No sequence numbers** means no fingerprinting via ISN (unlike TCP)

!!! danger "The WebRTC UDP Leak"
    Here's the critical problem: Your browser makes **DNS queries over UDP** and **WebRTC connections over UDP**. Most proxy configurations only cover **TCP traffic** (HTTP, HTTPS, WebSocket).
    
    Result: Your TCP traffic (web pages, API calls) goes through the proxy with the proxy's IP, but your **UDP traffic leaks your real IP directly**.
    
    This is why even with a proxy, websites can discover your real IP via WebRTC. It's using **UDP directly**, bypassing your proxy entirely.

**UDP Proxy Support by Protocol:**

| Proxy Type | UDP Support | Notes |
|------------|-------------|-------|
| HTTP Proxy | No | Only proxies TCP-based HTTP/HTTPS |
| HTTPS Proxy (CONNECT) | No | CONNECT method only establishes TCP tunnel |
| SOCKS4 | No | TCP-only protocol |
| SOCKS5 | Yes | Supports UDP relay via `UDP ASSOCIATE` command |
| VPN | Yes | Tunnels all IP traffic (TCP and UDP) |

**Practical Implication:**

For **true anonymity** in browser automation, you need **either**:
1. **SOCKS5 proxy** (to proxy UDP) + WebRTC configured to use SOCKS5
2. **Disable WebRTC entirely** (prevents UDP leaks but breaks video conferencing)
3. **VPN** (tunnels all traffic, TCP and UDP)
4. **Browser flags**: `--force-webrtc-ip-handling-policy=disable_non_proxied_udp`

!!! tip "UDP Fingerprinting"
    Unlike TCP, UDP has no handshake and minimal header fields, making it **harder to fingerprint**. However, **timing characteristics** (packet intervals, jitter) and **payload patterns** can still reveal application behavior.

## WebRTC and IP Leakage

WebRTC (Web Real-Time Communication) is a browser API standardized by the W3C that enables **peer-to-peer** audio, video, and data communication directly between browsers, without requiring plugins or intermediary servers. While powerful for real-time applications, WebRTC is the **single biggest source of IP leakage** in proxied browser automation.

### Why WebRTC Leaks Your IP

WebRTC was designed for **direct peer-to-peer connections**, optimizing for low latency over privacy. To establish P2P connections, WebRTC must discover your **real public IP address** and share it with the remote peer, even if your browser is configured to use a proxy.

**The fundamental problem:**
1. Your browser uses a proxy for HTTP/HTTPS (TCP traffic)
2. WebRTC uses **STUN servers** to discover your real public IP (UDP traffic)
3. STUN queries **bypass the proxy** (because they're UDP and most proxies only handle TCP)
4. Your real IP is discovered and **shared with remote peers**
5. JavaScript can read these "ICE candidates" and **leak your real IP to websites**

!!! danger "Severity of WebRTC Leaks"
    Even with:

    - HTTP proxy configured correctly
    - HTTPS proxy working
    - DNS queries proxied
    - User-Agent spoofed
    - Canvas fingerprinting mitigated
    
    **WebRTC can still leak your real IP in milliseconds**. This is because WebRTC operates **below the browser's proxy layer**, directly interfacing with the OS network stack.

### How WebRTC Establishes Connections: The ICE Process

WebRTC uses **ICE (Interactive Connectivity Establishment)**, defined in RFC 8445, to discover possible connection paths and select the best one. This process inherently reveals your network topology.

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

### ICE Candidate Types: What Gets Leaked

ICE discovers three types of "candidates" (possible connection endpoints):

**1. Host Candidates (Local LAN IP addresses)**

Your browser enumerates all local network interfaces and creates candidates for each:

```javascript
// Example host candidates revealed by WebRTC
candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host
candidate:2 1 UDP 2130706431 10.0.0.5 54322 typ host
candidate:3 1 UDP 2130706431 172.16.0.10 54323 typ host
```

**What this reveals:**

- Your **local IP address(es)** on private networks
- Your **network topology** (presence of VPN interfaces, VM bridges, etc.)
- **Number of network interfaces** (single Wi-Fi vs multiple ethernet/VPN)

Even if you're behind NAT, this reveals your **internal network structure**.

**2. Server Reflexive Candidates (Public IP via STUN)**

Browser sends STUN request to public STUN server, which replies with your **public IP address** as seen from the internet:

```javascript
// Server reflexive candidate (YOUR REAL PUBLIC IP!)
candidate:4 1 UDP 1694498815 203.0.113.45 54321 typ srflx raddr 192.168.1.100 rport 54321
```

**What this reveals:**

- Your **real public IP address** (the one you're trying to hide with a proxy!)
- Your **NAT type** and external port mapping
- Your **ISP** (via IP geolocation/WHOIS)

**This is the leak** everyone talks about: your proxy shows `198.51.100.5` but WebRTC reveals `203.0.113.45` (your real IP).

**3. Relay Candidates (TURN relay addresses)**

If direct P2P fails, browser allocates a relay address from a TURN server:

```javascript
// Relay candidate (TURN server address)
candidate:5 1 UDP 16777215 198.51.100.10 61234 typ relay raddr 203.0.113.45 rport 54321
```

**What this reveals:**

- **TURN server** being used (may reveal your VoIP provider, etc.)
- **Still contains your real IP** in `raddr` (remote address) field

### STUN Protocol: The IP Discovery Mechanism

STUN (Session Traversal Utilities for NAT), defined in RFC 5389, is a simple request-response protocol over UDP that discovers your public IP address by asking a server "what IP do you see me as?"

**STUN Message Structure**:

```python
# STUN Binding Request (simplified)
{
    'message_type': 0x0001,  # Binding Request
    'message_length': 0,      # No additional attributes
    'magic_cookie': 0x2112A442,  # Fixed value (RFC 5389)
    'transaction_id': b'\x01\x02\x03...\x0c'  # Random 12 bytes
}

# Sent via UDP to STUN server (e.g., stun.l.google.com:19302)
```

**STUN Binding Response**:

```python
# STUN Binding Success Response
{
    'message_type': 0x0101,  # Binding Success Response
    'message_length': 12,     # XOR-MAPPED-ADDRESS attribute
    'magic_cookie': 0x2112A442,
    'transaction_id': b'\x01\x02\x03...\x0c',  # Same as request
    'attributes': {
        'XOR-MAPPED-ADDRESS': {
            'family': 'IPv4',
            'port': 54321,
            'address': '203.0.113.45'  # YOUR REAL PUBLIC IP!
        }
    }
}
```

**Why XOR-MAPPED-ADDRESS?**
The IP address is XOR'ed with the magic cookie and transaction ID for **NAT compatibility**. Some NAT devices incorrectly modify IP addresses in packet payloads, breaking STUN. XOR'ing obfuscates the IP, preventing NAT interference.

**Public STUN Servers** (commonly used by browsers):

- `stun.l.google.com:19302` (Google)
- `stun1.l.google.com:19302` (Google)
- `stun.services.mozilla.com` (Mozilla)
- `stun.stunprotocol.org:3478` (Open STUN server)

### Why Proxies Can't Stop WebRTC Leaks

**1. UDP Protocol**: WebRTC uses **UDP**, most proxies only handle **TCP**

   - HTTP proxies: TCP-only
   - HTTPS CONNECT: TCP-only tunnel
   - SOCKS4: TCP-only
   - Only **SOCKS5** supports UDP (but browser must be configured to use it)

**2. Browser-Level Implementation**: WebRTC is a **browser API**, not an HTTP feature

   - Operates below HTTP layer
   - Directly accesses OS network stack
   - Bypasses proxy settings configured for HTTP/HTTPS

**3. Direct OS Network Access**: STUN queries go **directly to the network interface**

   - Browser's proxy settings don't apply to STUN
   - OS routing table determines path (not browser proxy config)
   - Only VPN-level routing can intercept

**4. Multiple Interface Enumeration**: WebRTC enumerates **all** network interfaces

   - Physical ethernet, Wi-Fi, VPN adapters, VM bridges
   - Even interfaces not used for browsing
   - Leaks internal network topology

**5. JavaScript Accessibility**: Web pages can **read ICE candidates** via JavaScript

   - `RTCPeerConnection.onicecandidate` event
   - Extracts IP addresses from candidate strings
   - Sends your real IP to their server

### Preventing WebRTC Leaks in Pydoll

Pydoll provides multiple strategies for preventing WebRTC IP leaks:

**Method 1: Force WebRTC to Only Use Proxied Routes (Recommended)**

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.webrtc_leak_protection = True  # Adds --force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Pydoll provides a convenient `webrtc_leak_protection` property that manages the underlying `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` argument for you.

**What this does:**

- Disables UDP if no proxy supports it
- Forces WebRTC to use **TURN relays only** (no direct P2P)
- Prevents STUN queries to public servers
- **Trade-off**: Breaks direct P2P (higher latency for video calls)

**Method 2: Disable WebRTC Entirely**

```python
options.add_argument('--disable-features=WebRTC')
```

**What this does:**

- Completely disables WebRTC API
- No IP leaks possible
- **Trade-off**: Breaks all WebRTC-dependent sites (video conferencing, voice calls)

**Method 3: Restrict WebRTC via Browser Preferences**

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

**What this does:**

- `ip_handling_policy`: Same as Method 1, but via preferences
- `multiple_routes_enabled`: Prevents using multiple network paths
- `nonproxied_udp_enabled`: Blocks UDP that doesn't go through proxy

**Method 4: Use SOCKS5 Proxy with UDP Support**

```python
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
# For proxies requiring authentication:
# options.add_argument('--proxy-server=socks5://user:pass@proxy.example.com:1080')
options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
```

**What this does:**

- SOCKS5 can proxy UDP (via `UDP ASSOCIATE` command)
- WebRTC uses proxy for STUN queries
- **Requires**: Proxy must support UDP (not all SOCKS5 proxies do)

### Testing for WebRTC Leaks

**Manual Testing:**

1. Visit **https://browserleaks.com/webrtc**
2. Check "Public IP Address" section
3. If you see **your real IP** (not proxy IP), you're leaking

**Automated Testing with Pydoll:**

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
        
        # Wait for results to load
        await asyncio.sleep(3)
        
        # Extract detected IPs
        ips = await tab.execute_script('''
            return Array.from(document.querySelectorAll('.ip-address'))
                .map(el => el.textContent.trim());
        ''')
        
        print("Detected IPs:", ips)
        # Should only show proxy IP, not your real IP

asyncio.run(test_webrtc_leak())
```

!!! danger "Always Test WebRTC Leaks"
    **Never assume** your proxy configuration prevents WebRTC leaks. Always test with https://browserleaks.com/webrtc or https://ipleak.net to verify your real IP is not exposed.
    
    Even a single WebRTC leak instantly **compromises your entire proxy setup**. Websites now know your real location, ISP, and network topology.

### Advanced: WebRTC Leak Detection by Websites

Websites use JavaScript to intentionally trigger WebRTC and extract your real IP:

```javascript
// Malicious website code to extract real IP via WebRTC
const pc = new RTCPeerConnection({
    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
});

pc.createDataChannel('');  // Create dummy data channel
pc.createOffer().then(offer => pc.setLocalDescription(offer));

pc.onicecandidate = (event) => {
    if (event.candidate) {
        const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
        const ipMatch = event.candidate.candidate.match(ipRegex);
        
        if (ipMatch) {
            const realIP = ipMatch[1];
            // Send real IP to server
            fetch(`/track?real_ip=${realIP}&proxy_ip=${window.clientIP}`);
        }
    }
};
```

This code:

1. Creates an RTCPeerConnection (WebRTC connection object)
2. Triggers ICE candidate gathering (contacts STUN servers)
3. Extracts IP addresses from candidates with regex
4. Sends your real IP to their tracking server

**Your defense:** Disable WebRTC or force proxied-only routes as shown above.

## Summary and Further Reading

Understanding network fundamentals (OSI layers, TCP/UDP characteristics, and WebRTC's peer-to-peer architecture) is **essential** for implementing effective proxy-based anonymity.

**Key Takeaways:**

- Proxies operate at **specific layers** (HTTP at Layer 7, SOCKS at Layer 5), determining their capabilities

- **TCP fingerprints** (window size, options, TTL) leak from lower layers, revealing your real OS

- **UDP traffic** (WebRTC, DNS) often bypasses proxies unless explicitly configured

- **WebRTC** is the #1 source of IP leakage. Always test with browserleaks.com

- Only **SOCKS5** or **VPN** can proxy UDP traffic effectively

**Next Steps:**

- **[HTTP/HTTPS Proxies](./http-proxies.md)** - Dive into application-layer proxying
- **[SOCKS Proxies](./socks-proxies.md)** - Learn session-layer, protocol-agnostic proxying
- **[Network Fingerprinting](../fingerprinting/network-fingerprinting.md)** - TCP/IP fingerprinting techniques
- **[Proxy Configuration](../../features/configuration/proxy.md)** - Practical Pydoll proxy setup

## References

- **RFC 793**: Transmission Control Protocol (TCP) - https://tools.ietf.org/html/rfc793
- **RFC 768**: User Datagram Protocol (UDP) - https://tools.ietf.org/html/rfc768
- **RFC 5389**: Session Traversal Utilities for NAT (STUN) - https://tools.ietf.org/html/rfc5389
- **RFC 8445**: Interactive Connectivity Establishment (ICE) - https://tools.ietf.org/html/rfc8445
- **RFC 5766**: Traversal Using Relays around NAT (TURN) - https://tools.ietf.org/html/rfc5766
- **RFC 6528**: Defending Against Sequence Number Attacks - https://tools.ietf.org/html/rfc6528
- **W3C WebRTC 1.0**: Real-Time Communication Between Browsers - https://www.w3.org/TR/webrtc/
- **BrowserLeaks**: WebRTC Leak Test - https://browserleaks.com/webrtc
- **IPLeak**: Comprehensive Leak Testing - https://ipleak.net

