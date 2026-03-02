# Building Proxy Servers

This document implements HTTP and SOCKS5 proxy servers from scratch in Python using asyncio. The goal is not production readiness but protocol comprehension: seeing how each byte is parsed, where security boundaries lie, and why certain design decisions exist in real proxy software.

!!! info "Module Navigation"
    - [Network Fundamentals](./network-fundamentals.md): TCP/IP, UDP, WebRTC
    - [HTTP/HTTPS Proxies](./http-proxies.md): Application-layer proxying
    - [SOCKS Proxies](./socks-proxies.md): Session-layer proxying
    - [Proxy Detection](./proxy-detection.md): Detection techniques and evasion

    For practical proxy usage in Pydoll, see [Proxy Configuration](../../features/configuration/proxy.md).

!!! warning "Educational Code"
    These implementations prioritize clarity over robustness. They lack connection limits, access control lists, and many error recovery paths that a production proxy requires. Do not expose them to untrusted networks.

## HTTP Proxy

An HTTP proxy operates in two modes. For plaintext HTTP, it receives the full request (with an absolute-form URL like `GET http://example.com/path HTTP/1.1`), rewrites the request-target to origin-form (`GET /path HTTP/1.1`), connects to the target server, forwards the request, and pipes the response back. For HTTPS, the client sends a `CONNECT host:port` request, the proxy opens a TCP connection to the target, responds with `200 Connection Established`, and then blindly relays bytes in both directions without inspecting the encrypted content.

The implementation below handles both modes. A few things to note as you read through it. The `_pipe_data` method calls `write_eof()` when one side closes, which sends a TCP FIN to the other side. Without this, the tunnel hangs indefinitely because the other `read()` never returns empty bytes. The HTTP forwarding path uses the same piping approach rather than a single `read()` call, because HTTP responses can be arbitrarily large and a fixed-size read would silently truncate them. The request-target rewrite preserves query strings, which `urlparse().path` alone would drop.

```python
import asyncio
import base64
import contextlib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTPProxy:
    """Async HTTP/HTTPS proxy with optional Basic authentication."""

    def __init__(self, host='0.0.0.0', port=8080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def start(self):
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f'HTTP proxy listening on {self.host}:{self.port}')
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        try:
            request_line = await asyncio.wait_for(
                reader.readline(), timeout=30
            )
            if not request_line:
                return

            parts = request_line.decode('latin-1').split()
            if len(parts) != 3:
                writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
                await writer.drain()
                return

            method, url, _ = parts
            headers = await self._read_headers(reader)

            if not self._check_auth(headers):
                writer.write(
                    b'HTTP/1.1 407 Proxy Authentication Required\r\n'
                    b'Proxy-Authenticate: Basic realm="Proxy"\r\n'
                    b'Content-Length: 0\r\n\r\n'
                )
                await writer.drain()
                return

            if method == 'CONNECT':
                await self._handle_connect(url, reader, writer)
            else:
                await self._handle_http(method, url, headers, reader, writer)
        except Exception as e:
            logger.error(f'Client handler error: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def _read_headers(self, reader):
        headers = {}
        while True:
            line = await reader.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            if b':' in line:
                key, value = line.decode('latin-1').split(':', 1)
                headers[key.strip().lower()] = value.strip()
        return headers

    def _check_auth(self, headers):
        if not self.username:
            return True
        auth = headers.get('proxy-authorization', '')
        if not auth.startswith('Basic '):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode('utf-8')
            if ':' not in decoded:
                return False
            user, pwd = decoded.split(':', 1)
            return user == self.username and pwd == self.password
        except Exception:
            return False

    async def _handle_connect(self, target, client_reader, client_writer):
        """Establish a blind TCP tunnel for HTTPS."""
        # Parse host:port, handling IPv6 literals like [::1]:443
        if target.startswith('['):
            bracket_end = target.index(']')
            host = target[1:bracket_end]
            port = int(target[bracket_end + 2:])
        elif ':' in target:
            host, port_str = target.rsplit(':', 1)
            port = int(port_str)
        else:
            client_writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            await client_writer.drain()
            return

        try:
            server_reader, server_writer = await asyncio.open_connection(
                host, port
            )
        except OSError as e:
            logger.error(f'CONNECT failed to {host}:{port}: {e}')
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
            return

        client_writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await client_writer.drain()

        await asyncio.gather(
            self._pipe(client_reader, server_writer),
            self._pipe(server_reader, client_writer),
        )

    async def _handle_http(self, method, url, headers, client_reader, client_writer):
        """Forward a plaintext HTTP request."""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80

        # Preserve query string in the request-target
        path = parsed.path or '/'
        if parsed.query:
            path += f'?{parsed.query}'

        try:
            server_reader, server_writer = await asyncio.open_connection(
                host, port
            )
        except OSError as e:
            logger.error(f'HTTP forward failed to {host}:{port}: {e}')
            client_writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
            await client_writer.drain()
            return

        # Rewrite request-target from absolute-form to origin-form
        request = f'{method} {path} HTTP/1.1\r\n'

        # Host header must include the port if it is non-standard
        if port != 80:
            request += f'Host: {host}:{port}\r\n'
        else:
            request += f'Host: {host}\r\n'

        # Remove hop-by-hop headers that must not be forwarded
        hop_by_hop = {
            'proxy-authorization', 'proxy-connection',
            'connection', 'keep-alive', 'te', 'trailer', 'upgrade',
        }
        for key, value in headers.items():
            if key not in hop_by_hop:
                request += f'{key}: {value}\r\n'

        # Force Connection: close so the server does not keep-alive,
        # which would prevent the response stream from ending
        request += 'Connection: close\r\n\r\n'

        server_writer.write(request.encode('latin-1'))

        # Forward request body if present
        content_length = int(headers.get('content-length', 0))
        if content_length > 0:
            body = await client_reader.readexactly(content_length)
            server_writer.write(body)

        await server_writer.drain()

        # Pipe the entire response back (not a single fixed-size read)
        while True:
            chunk = await server_reader.read(65536)
            if not chunk:
                break
            client_writer.write(chunk)
            await client_writer.drain()

        server_writer.close()
        await server_writer.wait_closed()

    async def _pipe(self, reader, writer):
        """Bidirectional data relay with proper half-close."""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            with contextlib.suppress(Exception):
                if writer.can_write_eof():
                    writer.write_eof()
```

A few protocol details worth understanding. HTTP headers are encoded as ISO-8859-1 (Latin-1), not UTF-8. Latin-1 maps every byte value 0-255 to a character, so `decode('latin-1')` never raises a `UnicodeDecodeError`, while `decode('utf-8')` would crash on certain header values. The `Proxy-Authorization` header uses Base64 encoding, but Base64 is not encryption: the credentials travel in cleartext (or rather, trivially reversible encoding) unless the connection between client and proxy is itself protected by TLS. The hop-by-hop headers (`Connection`, `Keep-Alive`, `TE`, `Trailer`, `Upgrade`, `Proxy-Connection`) are meant for the immediate connection between two nodes, not for end-to-end forwarding. RFC 9110 Section 7.6.1 requires proxies to strip them before forwarding.

!!! warning "SSRF Risk"
    This implementation does not validate destination addresses. A client could request `CONNECT 127.0.0.1:6379` to reach a local Redis instance, or `CONNECT 169.254.169.254:80` to access cloud instance metadata (AWS, GCP, Azure). Any proxy exposed to untrusted clients must validate destinations against a deny list of private and link-local ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).

## SOCKS5 Proxy

A SOCKS5 proxy operates at a lower level than HTTP. It uses a binary protocol defined in RFC 1928, consisting of three phases: method negotiation, optional authentication, and the connection request. The proxy does not parse HTTP at all. Once the tunnel is established, it relays raw bytes without understanding what protocol flows through it.

The binary nature of SOCKS5 means every read must receive exactly the expected number of bytes. TCP is a stream protocol and does not guarantee that `read(4)` returns 4 bytes: it may return 1, 2, or 3 bytes depending on network conditions. The implementation below uses `readexactly()` from asyncio, which buffers internally until the requested number of bytes arrives or the connection closes (raising `IncompleteReadError`).

```python
import asyncio
import contextlib
import struct
import logging

logger = logging.getLogger(__name__)


class SOCKS5Proxy:
    """Async SOCKS5 proxy supporting CONNECT with optional auth (RFC 1928)."""

    VERSION = 0x05

    def __init__(self, host='0.0.0.0', port=1080, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def start(self):
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info(f'SOCKS5 proxy listening on {self.host}:{self.port}')
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader, writer):
        try:
            if not await self._negotiate_method(reader, writer):
                return
            if self.username and not await self._authenticate(reader, writer):
                return
            await self._handle_request(reader, writer)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f'SOCKS5 error: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def _negotiate_method(self, reader, writer):
        """Phase 1: client offers authentication methods, server picks one."""
        version = (await reader.readexactly(1))[0]
        if version != self.VERSION:
            return False

        nmethods = (await reader.readexactly(1))[0]
        methods = await reader.readexactly(nmethods)

        if self.username:
            if 0x02 not in methods:
                writer.write(bytes([self.VERSION, 0xFF]))
                await writer.drain()
                return False
            selected = 0x02
        else:
            selected = 0x00

        writer.write(bytes([self.VERSION, selected]))
        await writer.drain()
        return True

    async def _authenticate(self, reader, writer):
        """Phase 2: username/password sub-negotiation (RFC 1929)."""
        auth_ver = (await reader.readexactly(1))[0]
        if auth_ver != 0x01:
            return False

        ulen = (await reader.readexactly(1))[0]
        username = (await reader.readexactly(ulen)).decode('utf-8')
        plen = (await reader.readexactly(1))[0]
        password = (await reader.readexactly(plen)).decode('utf-8')

        ok = username == self.username and password == self.password
        writer.write(bytes([0x01, 0x00 if ok else 0x01]))
        await writer.drain()
        return ok

    async def _handle_request(self, reader, writer):
        """Phase 3: parse the CONNECT request and establish the tunnel."""
        header = await reader.readexactly(4)
        version, command, _, atyp = header

        # Parse destination address based on address type
        if atyp == 0x01:  # IPv4
            raw = await reader.readexactly(4)
            address = '.'.join(str(b) for b in raw)
        elif atyp == 0x03:  # Domain name
            length = (await reader.readexactly(1))[0]
            address = (await reader.readexactly(length)).decode('ascii')
        elif atyp == 0x04:  # IPv6
            raw = await reader.readexactly(16)
            groups = [f'{raw[i]:02x}{raw[i+1]:02x}' for i in range(0, 16, 2)]
            address = ':'.join(groups)
        else:
            await self._reply(writer, 0x08)
            return

        port = struct.unpack('!H', await reader.readexactly(2))[0]
        logger.info(f'SOCKS5 CONNECT {address}:{port}')

        if command != 0x01:  # Only CONNECT is implemented
            await self._reply(writer, 0x07)
            return

        try:
            server_reader, server_writer = await asyncio.open_connection(
                address, port
            )
        except ConnectionRefusedError:
            await self._reply(writer, 0x05)
            return
        except OSError:
            await self._reply(writer, 0x04)
            return

        # BND.ADDR and BND.PORT should reflect the local socket address.
        # Most clients ignore these for CONNECT, but filling them
        # correctly satisfies RFC 1928.
        local = server_writer.get_extra_info('sockname')
        await self._reply(writer, 0x00, local[0], local[1])

        await asyncio.gather(
            self._pipe(reader, server_writer),
            self._pipe(server_reader, writer),
        )

    async def _reply(self, writer, status, bind_addr='0.0.0.0', bind_port=0):
        """Send a SOCKS5 reply with the given status and bound address."""
        import socket
        try:
            packed_ip = socket.inet_aton(bind_addr)
            atyp = 0x01
        except OSError:
            packed_ip = socket.inet_aton('0.0.0.0')
            atyp = 0x01

        writer.write(bytes([
            self.VERSION, status, 0x00, atyp,
            *packed_ip,
            (bind_port >> 8) & 0xFF, bind_port & 0xFF,
        ]))
        await writer.drain()

    async def _pipe(self, reader, writer):
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            with contextlib.suppress(Exception):
                if writer.can_write_eof():
                    writer.write_eof()
```

When the address type is `0x03` (domain name), the proxy resolves DNS itself via `asyncio.open_connection()`. This is the defining privacy property of SOCKS5 proxying: the client sends the domain name rather than resolving it locally, which prevents DNS queries from leaking to the client's local network. This is the same behavior Chrome relies on when configured with `--proxy-server=socks5://...`, as discussed in [SOCKS Proxies](./socks-proxies.md).

The `_reply` method fills `BND.ADDR` and `BND.PORT` with the actual local socket address after a successful connection, as RFC 1928 requires. Many SOCKS5 implementations return `0.0.0.0:0` here because most clients ignore these fields for CONNECT commands, but filling them correctly costs nothing and avoids a protocol violation.

## Running Both Proxies

```python
async def main():
    http_proxy = HTTPProxy(
        port=8080, username='user', password='pass'
    )
    socks5_proxy = SOCKS5Proxy(
        port=1080, username='user', password='pass'
    )
    await asyncio.gather(http_proxy.start(), socks5_proxy.start())

# asyncio.run(main())
```

You can test them with curl:

```bash
# HTTP proxy
curl -x http://user:pass@localhost:8080 http://httpbin.org/ip

# HTTPS through HTTP proxy (CONNECT tunnel)
curl -x http://user:pass@localhost:8080 https://httpbin.org/ip

# SOCKS5 proxy
curl --socks5 localhost:1080 --proxy-user user:pass https://httpbin.org/ip
```

## What the Code Does Not Handle

These implementations omit several things that production proxies handle. Understanding what is missing is as instructive as understanding what is present.

There are no connection limits. `asyncio.start_server` accepts connections without bound, so a single client opening thousands of connections would exhaust file descriptors. Production proxies use semaphores or connection pools to cap concurrency.

There is no destination validation. Both proxies connect to whatever address the client requests, including `127.0.0.1`, `169.254.169.254` (cloud metadata), and internal network ranges. This is a Server-Side Request Forgery (SSRF) vector. Production proxies maintain deny lists of private and link-local address ranges.

There is no traffic logging or metrics. Production proxies track request counts, bytes transferred, error rates, and latency percentiles, typically exporting to Prometheus or similar systems.

The HTTP proxy does not add a `Via` header. RFC 9110 Section 7.6.3 requires intermediaries to append a `Via` field to forwarded messages. This was omitted for simplicity, but a standards-compliant proxy must include it.

Neither proxy implements graceful shutdown. When the server stops, active tunnels are terminated abruptly rather than being drained. Production proxies track active connections and wait for them to complete (with a deadline) before shutting down.

## Proxy Chaining

Chaining proxies means routing traffic through multiple proxies in sequence: client to proxy A, proxy A to proxy B, proxy B to the target server. Each proxy in the chain only knows its immediate neighbors, not the full path.

The main use case is distributing trust. If you do not fully trust any single proxy provider, chaining two providers means neither one sees both your real IP and your destination. The tradeoff is latency: each hop adds its own connection setup time and forwarding delay. A single proxy typically adds 50 to 100ms of overhead. Two proxies roughly double that, and three proxies can push total overhead past 300ms.

Beyond two hops, the marginal privacy gain diminishes while latency and failure probability increase. Most practical setups use one or two proxies. Tor uses three relays (guard, middle, exit) because its threat model assumes some relays are compromised, but Tor accepts the latency penalty as an explicit design tradeoff.

```
Client --> Proxy A (SOCKS5) --> Proxy B (SOCKS5) --> Target
           sees: client IP          sees: Proxy A IP
           sees: Proxy B addr       sees: target addr
```

Chaining a SOCKS5 proxy through another SOCKS5 proxy works by having proxy A treat proxy B as the target. The client connects to proxy A and sends a CONNECT request for proxy B's address. Once that tunnel is established, the client sends a second SOCKS5 handshake through the tunnel, this time requesting the real target. Proxy A sees traffic flowing to proxy B but cannot read it if the inner connection is encrypted.

## References

- RFC 1928: SOCKS Protocol Version 5 - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- mitmproxy (Python HTTPS intercepting proxy) - https://mitmproxy.org/
