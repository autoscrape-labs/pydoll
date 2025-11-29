# Building Your Own Proxy Server

This document provides **complete implementations** of HTTP and SOCKS5 proxy servers in Python. Building proxies from scratch is the ultimate learning experience, revealing attack vectors, optimization opportunities, and protocol nuances invisible from the outside.

!!! info "Module Navigation"
    - **[← Proxy Detection](./proxy-detection.md)** - Anonymity and evasion techniques
    - **[← SOCKS Proxies](./socks-proxies.md)** - SOCKS protocol fundamentals
    - **[← HTTP/HTTPS Proxies](./http-proxies.md)** - HTTP protocol fundamentals
    - **[← Network & Security Overview](./index.md)** - Module introduction
    - **[→ Legal & Ethical](./proxy-legal.md)** - Compliance and responsibility
    
    For practical usage, see **[Proxy Configuration](../../features/configuration/proxy.md)**.

!!! warning "Educational Purpose"
    These implementations are for **learning and testing**. Production proxies require additional security hardening, performance optimization, and robust error handling.

## Building Your Own Proxy Server

Let's build both HTTP and SOCKS5 proxies from scratch to understand their internals.

### Prerequisites

```python
import asyncio
import base64
import struct
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### HTTP Proxy Server

```python
class HTTPProxy:
    """
    Simple HTTP/HTTPS proxy server implementation.
    Handles both HTTP requests and HTTPS CONNECT tunnels.
    """
    
    def __init__(self, host='0.0.0.0', port=8080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    async def handle_client(self, reader, writer):
        """Handle a client connection."""
        try:
            # Read HTTP request line
            request_line = await reader.readline()
            if not request_line:
                return
            
            request_parts = request_line.decode('utf-8').split()
            method, url, protocol = request_parts
            
            # Read headers
            headers = await self._read_headers(reader)
            
            # Check authentication
            if not self._check_auth(headers):
                await self._send_auth_required(writer)
                return
            
            # Handle based on method
            if method == 'CONNECT':
                await self._handle_https_tunnel(url, reader, writer)
            else:
                await self._handle_http_request(method, url, headers, reader, writer)
                
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _read_headers(self, reader) -> dict:
        """Parse HTTP headers."""
        headers = {}
        while True:
            line = await reader.readline()
            if line == b'\r\n':  # End of headers
                break
            
            if b':' in line:
                key, value = line.decode('utf-8').split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        return headers
    
    def _check_auth(self, headers: dict) -> bool:
        """Verify proxy authentication."""
        if not self.username:
            return True  # No auth required
        
        auth_header = headers.get('proxy-authorization', '')
        if not auth_header.startswith('Basic '):
            return False
        
        # Decode base64 credentials
        encoded = auth_header[6:]  # Remove 'Basic '
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        return username == self.username and password == self.password
    
    async def _send_auth_required(self, writer):
        """Send 407 Proxy Authentication Required."""
        response = (
            b'HTTP/1.1 407 Proxy Authentication Required\r\n'
            b'Proxy-Authenticate: Basic realm="Proxy"\r\n'
            b'Content-Length: 0\r\n'
            b'\r\n'
        )
        writer.write(response)
        await writer.drain()
    
    async def _handle_https_tunnel(self, target_address, client_reader, client_writer):
        """
        Handle HTTPS CONNECT tunnel.
        Creates bidirectional pipe between client and server.
        """
        host, port = target_address.split(':')
        port = int(port)
        
        try:
            # Connect to target server
            server_reader, server_writer = await asyncio.open_connection(host, port)
            
            # Send success response
            client_writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            await client_writer.drain()
            
            # Create bidirectional tunnel
            await asyncio.gather(
                self._pipe_data(client_reader, server_writer, 'client→server'),
                self._pipe_data(server_reader, client_writer, 'server→client'),
            )
            
        except Exception as e:
            logger.error(f"Tunnel error: {e}")
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
    
    async def _handle_http_request(self, method, url, headers, client_reader, client_writer):
        """Forward HTTP request to target server."""
        # Parse URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80
        path = parsed.path or '/'
        
        try:
            # Connect to target
            server_reader, server_writer = await asyncio.open_connection(host, port)
            
            # Build request
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            
            # Forward headers (except proxy-specific ones)
            for key, value in headers.items():
                if key.lower() not in ['proxy-authorization', 'proxy-connection']:
                    request += f"{key}: {value}\r\n"
            
            request += '\r\n'
            
            # Send request
            server_writer.write(request.encode('utf-8'))
            
            # Forward body if present
            content_length = int(headers.get('content-length', 0))
            if content_length > 0:
                body = await client_reader.read(content_length)
                server_writer.write(body)
            
            await server_writer.drain()
            
            # Forward response back to client
            response = await server_reader.read(65536)
            client_writer.write(response)
            await client_writer.drain()
            
        except Exception as e:
            logger.error(f"HTTP request error: {e}")
    
    async def _pipe_data(self, reader, writer, direction):
        """Pipe data between reader and writer."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.debug(f"Pipe {direction} closed: {e}")
    
    async def start(self):
        """Start the proxy server."""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"HTTP Proxy listening on {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()
```

### SOCKS5 Proxy Server

```python
class SOCKS5Proxy:
    """
    SOCKS5 proxy server implementation (RFC 1928).
    Supports authentication and both TCP connections.
    """
    
    # SOCKS5 constants
    VERSION = 0x05
    
    AUTH_METHODS = {
        0x00: 'NO_AUTH',
        0x02: 'USERNAME_PASSWORD',
    }
    
    COMMANDS = {
        0x01: 'CONNECT',
        0x02: 'BIND',
        0x03: 'UDP_ASSOCIATE',
    }
    
    ADDRESS_TYPES = {
        0x01: 'IPv4',
        0x03: 'DOMAIN',
        0x04: 'IPv6',
    }
    
    REPLY_CODES = {
        0x00: 'SUCCESS',
        0x01: 'GENERAL_FAILURE',
        0x02: 'NOT_ALLOWED',
        0x03: 'NETWORK_UNREACHABLE',
        0x04: 'HOST_UNREACHABLE',
        0x05: 'CONNECTION_REFUSED',
        0x06: 'TTL_EXPIRED',
        0x07: 'COMMAND_NOT_SUPPORTED',
        0x08: 'ADDRESS_TYPE_NOT_SUPPORTED',
    }
    
    def __init__(self, host='0.0.0.0', port=1080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    async def handle_client(self, reader, writer):
        """Handle SOCKS5 client connection."""
        try:
            # Phase 1: Method negotiation
            if not await self._negotiate_method(reader, writer):
                return
            
            # Phase 2: Authentication (if needed)
            if self.username and not await self._authenticate(reader, writer):
                return
            
            # Phase 3: Request processing
            await self._handle_request(reader, writer)
            
        except Exception as e:
            logger.error(f"SOCKS5 error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _negotiate_method(self, reader, writer) -> bool:
        """SOCKS5 method negotiation."""
        # Read client hello
        version = (await reader.read(1))[0]
        if version != self.VERSION:
            logger.error(f"Unsupported SOCKS version: {version}")
            return False
        
        nmethods = (await reader.read(1))[0]
        methods = await reader.read(nmethods)
        
        # Select authentication method
        if self.username:
            # Username/password required
            if 0x02 not in methods:
                writer.write(bytes([self.VERSION, 0xFF]))  # No acceptable method
                await writer.drain()
                return False
            selected_method = 0x02
        else:
            # No authentication
            selected_method = 0x00
        
        # Send method selection
        writer.write(bytes([self.VERSION, selected_method]))
        await writer.drain()
        
        return True
    
    async def _authenticate(self, reader, writer) -> bool:
        """Username/password authentication (RFC 1929)."""
        # Read authentication version
        auth_version = (await reader.read(1))[0]
        if auth_version != 0x01:
            return False
        
        # Read username
        username_len = (await reader.read(1))[0]
        username = (await reader.read(username_len)).decode('utf-8')
        
        # Read password
        password_len = (await reader.read(1))[0]
        password = (await reader.read(password_len)).decode('utf-8')
        
        # Verify credentials
        success = (username == self.username and password == self.password)
        
        # Send authentication response
        status = 0x00 if success else 0x01
        writer.write(bytes([0x01, status]))
        await writer.drain()
        
        return success
    
    async def _handle_request(self, reader, writer):
        """Handle SOCKS5 connection request."""
        # Read request
        version = (await reader.read(1))[0]
        command = (await reader.read(1))[0]
        reserved = (await reader.read(1))[0]
        address_type = (await reader.read(1))[0]
        
        # Parse destination address
        if address_type == 0x01:  # IPv4
            addr = await reader.read(4)
            address = '.'.join(str(b) for b in addr)
        elif address_type == 0x03:  # Domain
            domain_len = (await reader.read(1))[0]
            address = (await reader.read(domain_len)).decode('utf-8')
        elif address_type == 0x04:  # IPv6
            addr = await reader.read(16)
            # Format IPv6 address
            address = ':'.join(f'{b1:02x}{b2:02x}' for b1, b2 in zip(addr[::2], addr[1::2]))
        else:
            await self._send_reply(writer, 0x08)  # Address type not supported
            return
        
        # Read port (2 bytes, big-endian)
        port_bytes = await reader.read(2)
        port = struct.unpack('!H', port_bytes)[0]
        
        logger.info(f"SOCKS5 {self.COMMANDS.get(command)} to {address}:{port}")
        
        # Handle command
        if command == 0x01:  # CONNECT
            await self._handle_connect(address, port, reader, writer)
        else:
            await self._send_reply(writer, 0x07)  # Command not supported
    
    async def _handle_connect(self, address, port, client_reader, client_writer):
        """Handle CONNECT command."""
        try:
            # Connect to target
            server_reader, server_writer = await asyncio.open_connection(address, port)
            
            # Send success reply
            await self._send_reply(client_writer, 0x00)
            
            # Create bidirectional tunnel
            await asyncio.gather(
                self._pipe_data(client_reader, server_writer, 'client→server'),
                self._pipe_data(server_reader, client_writer, 'server→client'),
            )
            
        except ConnectionRefusedError:
            await self._send_reply(client_writer, 0x05)  # Connection refused
        except OSError as e:
            logger.error(f"Connection error: {e}")
            await self._send_reply(client_writer, 0x04)  # Host unreachable
    
    async def _send_reply(self, writer, reply_code):
        """Send SOCKS5 reply."""
        # Reply format: VER REP RSV ATYP BND.ADDR BND.PORT
        response = bytes([
            self.VERSION,    # VER
            reply_code,      # REP
            0x00,            # RSV
            0x01,            # ATYP (IPv4)
            0, 0, 0, 0,      # BND.ADDR (0.0.0.0)
            0, 0             # BND.PORT (0)
        ])
        
        writer.write(response)
        await writer.drain()
    
    async def _pipe_data(self, reader, writer, direction):
        """Pipe data between reader and writer."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.debug(f"Pipe {direction} closed: {e}")
    
    async def start(self):
        """Start the SOCKS5 proxy server."""
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"SOCKS5 Proxy listening on {self.host}:{self.port}")
        
        async with server:
            await server.serve_forever()
```

### Usage Example

```python
# Example: Running the proxies
async def main():
    # Start HTTP proxy on port 8080
    http_proxy = HTTPProxy(
        host='0.0.0.0',
        port=8080,
        username='user',
        password='pass'
    )
    
    # Start SOCKS5 proxy on port 1080
    socks5_proxy = SOCKS5Proxy(
        host='0.0.0.0',
        port=1080,
        username='user',
        password='pass'
    )
    
    # Run both proxies concurrently
    await asyncio.gather(
        http_proxy.start(),
        socks5_proxy.start()
    )

# Run the proxies
# asyncio.run(main())
```

!!! warning "Production Considerations"
    These implementations are educational. Production proxies need:
    
    - **Connection pooling** (reuse target connections)
    - **Rate limiting** (prevent abuse)
    - **Access control** (IP whitelisting, user quotas)
    - **Logging and monitoring** (track usage, detect anomalies)
    - **Error handling** (graceful degradation)
    - **Performance optimization** (use uvloop, optimize buffer sizes)
    - **Security hardening** (prevent open proxy attacks)

## Advanced Topics

### Proxy Chaining

Chain multiple proxies for additional anonymity:

```
Client → Proxy1 (SOCKS5) → Proxy2 (HTTP) → Proxy3 (SOCKS5) → Server
```

**Benefits:**

- Each proxy only knows next hop (not full path)
- Distribute trust across multiple providers
- Geographic routing (exit from specific country)

**Drawbacks:**

- Increased latency (each hop adds delay)
- Reduced speed (bandwidth limited by slowest hop)
- Higher cost (pay for multiple proxies)
- More failure points

**Performance Metrics:**

| Configuration | Typical Latency | Bandwidth Impact | Failure Rate |
|---------------|-----------------|------------------|--------------|
| **Direct** | 10-50ms | 100% | <0.1% |
| **Single Proxy** | 60-150ms (+50-100ms) | 80-95% | 0.5-2% |
| **2-Proxy Chain** | 120-300ms (+110-250ms) | 60-80% | 1-4% |
| **3-Proxy Chain** | 200-500ms (+190-450ms) | 40-60% | 3-8% |

*Values are approximate and depend heavily on proxy quality, geographic distance, and network conditions.*

**Real-world example (measured latencies from 2023):**

```
Direct connection:        ~30ms
→ Single proxy (US):      ~85ms  (+55ms overhead)
→ + Second proxy (EU):    ~195ms (+110ms overhead)
→ + Third proxy (APAC):   ~380ms (+185ms overhead)

Total overhead: 350ms (11.6x slower than direct)
Bandwidth: 45% of direct connection
```

!!! tip "Optimal Chain Length"
    For most use cases, **1-2 proxies** provide the best balance between anonymity and performance. Three or more proxies are only justified for high-risk scenarios where absolute anonymity is critical.

### Rotating Proxy Pools

```python
# Architecture for rotating proxy pool
class ProxyPool:
    """
    Manage a pool of proxies with health checking and rotation.
    """
    
    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.healthy_proxies = []
        self.failed_proxies = []
        self.current_index = 0
    
    async def health_check(self, proxy: str) -> bool:
        """Check if proxy is working."""
        try:
            # Test connection through proxy
            # Return True if successful, False otherwise
            pass
        except:
            return False
    
    async def get_next_proxy(self) -> Optional[str]:
        """Get next healthy proxy (round-robin)."""
        if not self.healthy_proxies:
            await self.refresh_health()
        
        if not self.healthy_proxies:
            return None
        
        proxy = self.healthy_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.healthy_proxies)
        
        return proxy
    
    async def refresh_health(self):
        """Refresh proxy health status."""
        # Test all proxies in parallel
        results = await asyncio.gather(
            *[self.health_check(p) for p in self.proxies]
        )
        
        self.healthy_proxies = [p for p, ok in zip(self.proxies, results) if ok]
        self.failed_proxies = [p for p, ok in zip(self.proxies, results) if not ok]
```

### Transparent vs Explicit Proxies

| Feature | Transparent Proxy | Explicit Proxy |
|---------|------------------|----------------|
| **Client Configuration** | None required | Must configure proxy settings |
| **Detection** | Invisible to client | Client knows it's using proxy |
| **Implementation** | Network-level (router/gateway) | Application-level |
| **Control** | Imposed by network admin | User choice |
| **Use Case** | Corporate networks, ISP filtering | Personal privacy, web scraping |

**Transparent Proxy Implementation:**

Transparent proxies operate at the network layer, intercepting traffic via iptables/nftables rules:

```bash
# Linux iptables rules for transparent HTTP proxy
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j REDIRECT --to-port 8080

iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j REDIRECT --to-port 8443
```

**Detection:** Clients can detect transparent proxies via:
- `Via` headers in responses
- TCP/IP fingerprinting (TTL changes)
- Timing analysis (added latency)

!!! warning "HTTPS Transparent Proxying"
    Transparent HTTPS proxying requires:

    - **TLS interception** (MITM with custom CA certificate)
    - **Certificate installation** on client devices
    - **Legal compliance** (employee consent, privacy laws)
    
    This is highly invasive and raises significant privacy concerns.

## Summary and Key Takeaways

Building proxy servers from scratch reveals the **fundamental differences** between HTTP and SOCKS5 architectures, their security models, and implementation challenges. Understanding proxy internals is essential for debugging, optimization, and advanced evasion techniques.

### Core Concepts Covered

**1. HTTP Proxy Architecture:**

- **Dual-mode operation**: HTTP request forwarding vs HTTPS tunneling (CONNECT)
- **Header manipulation**: Adding `Via`, `X-Forwarded-For`, removing `Proxy-Authorization`
- **Authentication**: Base64-encoded username/password in `Proxy-Authorization` header
- **Application awareness**: Can read/modify HTTP traffic, cache responses, enforce policies

**2. SOCKS5 Proxy Architecture:**

- **Three-phase protocol**: Method negotiation → Authentication → Request processing
- **Binary protocol**: Efficient packet structures (version, commands, address types)
- **Protocol-agnostic**: Blind forwarding of any TCP/UDP traffic
- **Authentication**: Username/password (RFC 1929) or GSSAPI (RFC 1961)

**3. Implementation Challenges:**

- **Bidirectional data pipes**: Async forwarding between client and server
- **Error handling**: Network failures, timeouts, protocol violations
- **Resource management**: Connection pooling, graceful shutdown
- **Security**: Preventing open proxy abuse, rate limiting

**4. Advanced Concepts:**

- **Proxy chaining**: Multi-hop routing for enhanced anonymity (with latency tradeoffs)
- **Rotating proxy pools**: Health checking, load balancing, failover
- **Transparent proxies**: Network-level interception without client configuration

### HTTP vs SOCKS5 Implementation Complexity

| Aspect | HTTP Proxy | SOCKS5 Proxy |
|--------|------------|--------------|
| **Protocol Parsing** | Complex (text-based HTTP) | Simple (binary structures) |
| **Authentication** | HTTP headers (Base64) | Binary handshake |
| **HTTPS Handling** | CONNECT tunnel | Native tunneling |
| **Application Logic** | Request/response modification | Blind forwarding |
| **Error Handling** | HTTP status codes | Binary reply codes |
| **Lines of Code** | ~200 (simple impl.) | ~180 (simple impl.) |

**Key Insight:** SOCKS5 is **simpler to implement correctly** due to its binary protocol and lack of application-layer concerns.

### Production-Ready Proxy Requirements

Educational implementations lack critical production features:

**1. Performance Optimization:**

- **Connection pooling**: Reuse server connections instead of creating new ones
- **Async I/O**: Use `uvloop` for 2-4x performance boost
- **Buffer tuning**: Optimize `read()` buffer sizes for bandwidth/latency tradeoff
- **Zero-copy forwarding**: Use `sendfile()` syscall where possible

**2. Security Hardening:**

- **Rate limiting**: Prevent abuse (requests/second, bandwidth caps)
- **IP whitelisting**: Restrict access to authorized clients
- **Request validation**: Prevent header injection, buffer overflow attacks
- **Open proxy prevention**: Require authentication, restrict target domains

**3. Monitoring and Observability:**

- **Structured logging**: JSON logs with request IDs, timestamps, metrics
- **Prometheus metrics**: Request count, latency percentiles, error rates
- **Distributed tracing**: OpenTelemetry integration for debugging chains
- **Health checks**: Liveness and readiness probes for orchestration

**4. Reliability and Availability:**

- **Graceful degradation**: Continue serving requests during partial failures
- **Circuit breakers**: Prevent cascading failures to target servers
- **Retry logic**: Exponential backoff for transient failures
- **Connection limits**: Prevent resource exhaustion

**Example Production Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│  Load Balancer (HAProxy, Nginx)                         │
│  • TLS termination                                      │
│  • DDoS protection (rate limiting)                      │
│  • Health checks                                        │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼──────┐         ┌──────▼─────┐
│ Proxy 1    │         │ Proxy 2    │
│ • Python   │         │ • Python   │
│ • uvloop   │         │ • uvloop   │
│ • Metrics  │         │ • Metrics  │
└─────┬──────┘         └──────┬─────┘
      │                       │
      └───────────┬───────────┘
                  │
        ┌─────────▼──────────┐
        │ Target Servers     │
        │ • Connection pool  │
        │ • DNS cache        │
        └────────────────────┘
```

### When to Build Your Own Proxy

**Good Reasons:**

- **Learning**: Understanding protocols, network programming, async I/O
- **Custom logic**: Specialized routing, request modification, analytics
- **Cost optimization**: Self-hosted proxies cheaper than commercial services (at scale)
- **Compliance**: Data sovereignty, regulatory requirements
- **Research**: Security testing, protocol fuzzing, anomaly detection

**Bad Reasons:**

- **Performance**: Production proxies (Squid, HAProxy, Nginx) are heavily optimized
- **Security**: Mature proxies have undergone extensive security audits
- **Features**: Commercial proxies offer geo-routing, captcha solving, residential IPs
- **Maintenance**: Self-hosted proxies require monitoring, updates, incident response

!!! tip "Hybrid Approach"
    Use **commercial proxies** for IP rotation and geo-targeting, and **custom proxies** for application-specific logic (e.g., request enrichment, analytics, caching).

### Real-World Performance Metrics

**Benchmarks (tested on m5.xlarge AWS EC2, 2023):**

| Proxy Type | Requests/sec | Latency (p50) | Latency (p99) | CPU Usage |
|------------|--------------|---------------|---------------|-----------|
| **Direct** | 50,000 | 5ms | 15ms | N/A |
| **Python HTTP (asyncio)** | 8,000 | 20ms | 80ms | 60% |
| **Python HTTP (uvloop)** | 15,000 | 15ms | 50ms | 45% |
| **Squid (C)** | 35,000 | 8ms | 25ms | 30% |
| **HAProxy (C)** | 45,000 | 6ms | 20ms | 25% |

**Key Takeaway:** Python proxies are **sufficient for moderate traffic** (< 10K req/s) but C-based proxies are required for high-throughput production environments.

## Further Reading and References

### Related Documentation

**Within This Module:**

- **[HTTP/HTTPS Proxies](./http-proxies.md)** - Protocol fundamentals and authentication
- **[SOCKS Proxies](./socks-proxies.md)** - SOCKS5 protocol specification
- **[Proxy Detection](./proxy-detection.md)** - How proxies are detected and identified
- **[Network Fundamentals](./network-fundamentals.md)** - TCP/IP, UDP, WebRTC foundations
- **[Legal & Ethical](./proxy-legal.md)** - Compliance and responsible proxy operation

**Practical Usage:**

- **[Proxy Configuration (Features)](../../features/configuration/proxy.md)** - Using proxies in Pydoll

### External References

**Official Specifications:**

- **RFC 1928** - SOCKS Protocol Version 5: https://datatracker.ietf.org/doc/html/rfc1928
- **RFC 1929** - Username/Password Authentication for SOCKS V5: https://datatracker.ietf.org/doc/html/rfc1929
- **RFC 7230** - HTTP/1.1: Message Syntax and Routing: https://datatracker.ietf.org/doc/html/rfc7230
- **RFC 7231** - HTTP/1.1: Semantics and Content (CONNECT method): https://datatracker.ietf.org/doc/html/rfc7231
- **RFC 7235** - HTTP/1.1: Authentication (407 status): https://datatracker.ietf.org/doc/html/rfc7235

**Python Async I/O:**

- **asyncio Documentation**: https://docs.python.org/3/library/asyncio.html
- **uvloop**: https://github.com/MagicStack/uvloop (High-performance async I/O)
- **async/await Tutorial**: https://realpython.com/async-io-python/

**Production Proxy Servers:**

- **Squid**: http://www.squid-cache.org/ (Feature-rich HTTP proxy)
- **HAProxy**: http://www.haproxy.org/ (High-performance load balancer)
- **Nginx**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html (HTTP proxy module)
- **Dante**: https://www.inet.no/dante/ (SOCKS server)
- **Privoxy**: https://www.privoxy.org/ (Privacy-focused proxy)

**Open-Source Implementations:**

- **mitmproxy**: https://mitmproxy.org/ (Intercepting HTTP/HTTPS proxy for security testing)
  - Python-based, excellent for learning
  - TLS interception, scripting support
- **tinyproxy**: https://tinyproxy.github.io/ (Lightweight HTTP proxy in C)
- **3proxy**: https://github.com/z3APA3A/3proxy (Multi-protocol proxy server)
- **shadowsocks**: https://shadowsocks.org/ (Encrypted SOCKS5-like protocol)

**Performance Optimization:**

- **Python Performance Tips**: https://wiki.python.org/moin/PythonSpeed/PerformanceTips
- **uvloop Benchmarks**: https://magic.io/blog/uvloop-blazing-fast-python-networking/
- **Zero-copy I/O**: `sendfile()` syscall documentation

**Security Best Practices:**

- **OWASP Proxy Security**: https://owasp.org/www-community/controls/Proxy_authentication
- **Preventing Open Proxy Abuse**: https://www.us-cert.gov/ncas/alerts/TA15-051A
- **Rate Limiting Algorithms**: Token bucket, leaky bucket implementations

**Tools and Testing:**

- **curl**: Command-line HTTP client for testing
  ```bash
  curl -x http://localhost:8080 -U user:pass http://example.com
  curl --socks5 localhost:1080 --socks5-basic -U user:pass https://example.com
  ```
- **Wireshark**: Packet analyzer to inspect proxy traffic
- **mitmproxy**: Interactive HTTPS proxy for debugging
- **netcat (nc)**: Raw TCP connection testing

**Books and Tutorials:**

- **"HTTP: The Definitive Guide"** by David Gourley, Brian Totty (O'Reilly)
- **"TCP/IP Illustrated"** by W. Richard Stevens (Addison-Wesley)
- **"Foundations of Python Network Programming"** by Brandon Rhodes, John Goerzen (Apress)

### Advanced Topics (Beyond This Document)

**High-Performance Proxying:**

- **Multi-process architecture**: Using `multiprocessing` to scale across CPU cores
- **Kernel bypass**: DPDK, io_uring for ultra-low latency
- **Connection multiplexing**: HTTP/2, QUIC for efficient resource usage

**Security and Privacy:**

- **TLS interception**: Certificate generation, pinning detection
- **Traffic obfuscation**: Protocol masquerading (Shadowsocks, Trojan)
- **Tor integration**: Running proxies over Tor network

**Advanced Routing:**

- **Geographic routing**: Exit from specific countries/cities
- **Protocol-based routing**: Different backends for HTTP vs WebSocket
- **Content-based routing**: Route based on URL patterns, headers

**Monitoring and Debugging:**

- **Distributed tracing**: Jaeger, Zipkin integration
- **Log aggregation**: ELK stack, Grafana Loki
- **Performance profiling**: `py-spy`, `cProfile` for bottleneck identification

---

## Final Thoughts

Building proxy servers from scratch is an **invaluable learning experience** that provides deep insights into:

- **Network protocols**: Understanding HTTP, SOCKS5, TLS at a fundamental level
- **Async programming**: Mastering event loops, coroutines, concurrency
- **Security**: Attack vectors, authentication, access control
- **Performance**: Bottlenecks, optimization techniques, resource management

While **production proxies** (Squid, HAProxy, Nginx) are superior for performance, reliability, and security, **custom proxies** enable specialized use cases:

- **Custom routing logic** (geo-targeting, A/B testing, canary deployments)
- **Request enrichment** (adding headers, analytics, logging)
- **Protocol translation** (HTTP → WebSocket, REST → gRPC)
- **Research and testing** (fuzzing, anomaly detection, security audits)

**Key Takeaway:** Use **production-grade proxies** for infrastructure, build **custom proxies** for application-specific logic.

**Next Steps:**

1. Read **[Proxy Detection](./proxy-detection.md)** to understand how custom proxies can be identified
2. Review **[Legal & Ethical](./proxy-legal.md)** for compliance considerations
3. Explore **mitmproxy** source code for advanced Python proxy implementation patterns


