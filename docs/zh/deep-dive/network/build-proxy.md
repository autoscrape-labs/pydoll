# 构建代理服务器

本文档使用 Python asyncio 从零实现 HTTP 和 SOCKS5 代理服务器。目标不是生产就绪，而是协议理解：观察每个字节如何被解析、安全边界在哪里，以及为什么真实的代理软件中存在某些设计决策。

!!! info "模块导航"
    - [网络基础](./network-fundamentals.md)：TCP/IP、UDP、WebRTC
    - [HTTP/HTTPS 代理](./http-proxies.md)：应用层代理
    - [SOCKS 代理](./socks-proxies.md)：会话层代理
    - [代理检测](./proxy-detection.md)：检测技术与规避

    有关在 Pydoll 中实际使用代理的方法，请参阅[代理配置](../../features/configuration/proxy.md)。

!!! warning "教育用途代码"
    这些实现以清晰度为优先，而非健壮性。它们缺少连接限制、访问控制列表以及生产代理所需的许多错误恢复路径。请勿将它们暴露于不受信任的网络中。

## HTTP 代理

HTTP 代理以两种模式运行。对于明文 HTTP，它接收完整的请求（带有绝对形式的 URL，例如 `GET http://example.com/path HTTP/1.1`），将请求目标重写为原始形式（`GET /path HTTP/1.1`），连接到目标服务器，转发请求，然后将响应传回。对于 HTTPS，客户端发送 `CONNECT host:port` 请求，代理打开到目标的 TCP 连接，以 `200 Connection Established` 响应，然后在两个方向之间盲目中继字节，不检查加密内容。

下面的实现处理了这两种模式。阅读代码时需要注意几点。`_pipe_data` 方法在一端关闭时调用 `write_eof()`，这会向另一端发送 TCP FIN。如果不这样做，隧道会无限挂起，因为另一端的 `read()` 永远不会返回空字节。HTTP 转发路径使用相同的管道方法而不是单次 `read()` 调用，因为 HTTP 响应可以任意大，固定大小的读取会静默截断它们。请求目标重写保留了查询字符串，仅使用 `urlparse().path` 会丢失它们。

```python
import asyncio
import base64
import contextlib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTPProxy:
    """带有可选 Basic 认证的异步 HTTP/HTTPS 代理。"""

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
        """为 HTTPS 建立盲 TCP 隧道。"""
        # 解析 host:port，处理 IPv6 字面量如 [::1]:443
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
        """转发明文 HTTP 请求。"""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80

        # 在请求目标中保留查询字符串
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

        # 将请求目标从绝对形式重写为原始形式
        request = f'{method} {path} HTTP/1.1\r\n'

        # 如果端口不是标准端口，Host 头必须包含端口号
        if port != 80:
            request += f'Host: {host}:{port}\r\n'
        else:
            request += f'Host: {host}\r\n'

        # 移除不应转发的 hop-by-hop 头
        hop_by_hop = {
            'proxy-authorization', 'proxy-connection',
            'connection', 'keep-alive', 'te', 'trailer', 'upgrade',
        }
        for key, value in headers.items():
            if key not in hop_by_hop:
                request += f'{key}: {value}\r\n'

        # 强制 Connection: close，使服务器不保持连接，
        # 否则响应流不会结束
        request += 'Connection: close\r\n\r\n'

        server_writer.write(request.encode('latin-1'))

        # 如果存在请求体则转发
        content_length = int(headers.get('content-length', 0))
        if content_length > 0:
            body = await client_reader.readexactly(content_length)
            server_writer.write(body)

        await server_writer.drain()

        # 将整个响应传回（而不是单次固定大小读取）
        while True:
            chunk = await server_reader.read(65536)
            if not chunk:
                break
            client_writer.write(chunk)
            await client_writer.drain()

        server_writer.close()
        await server_writer.wait_closed()

    async def _pipe(self, reader, writer):
        """带有正确半关闭处理的双向数据中继。"""
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

有几个值得理解的协议细节。HTTP 头使用 ISO-8859-1（Latin-1）编码，而非 UTF-8。Latin-1 将每个字节值 0-255 映射到一个字符，因此 `decode('latin-1')` 永远不会抛出 `UnicodeDecodeError`，而 `decode('utf-8')` 在某些头部值上会崩溃。`Proxy-Authorization` 头使用 Base64 编码，但 Base64 不是加密：凭据以明文（或者更准确地说，可轻易还原的编码）传输，除非客户端与代理之间的连接本身受到 TLS 保护。hop-by-hop 头（`Connection`、`Keep-Alive`、`TE`、`Trailer`、`Upgrade`、`Proxy-Connection`）是用于两个节点之间直接连接的，不应端到端转发。RFC 9110 第 7.6.1 节要求代理在转发前将其剥离。

!!! warning "SSRF 风险"
    此实现不验证目标地址。客户端可以请求 `CONNECT 127.0.0.1:6379` 来访问本地 Redis 实例，或请求 `CONNECT 169.254.169.254:80` 来访问云实例元数据（AWS、GCP、Azure）。任何暴露给不受信任客户端的代理都必须针对私有和链路本地地址范围（`127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`、`::1`、`fc00::/7`）建立拒绝列表来验证目标。

## SOCKS5 代理

SOCKS5 代理在比 HTTP 更低的层级运行。它使用 RFC 1928 中定义的二进制协议，包含三个阶段：方法协商、可选的认证和连接请求。代理完全不解析 HTTP。一旦隧道建立，它只是中继原始字节，不理解流经其中的是什么协议。

SOCKS5 的二进制特性意味着每次读取都必须精确接收预期数量的字节。TCP 是流协议，不保证 `read(4)` 返回 4 个字节：根据网络条件，它可能返回 1、2 或 3 个字节。下面的实现使用 asyncio 的 `readexactly()`，它在内部进行缓冲，直到请求数量的字节到达或连接关闭（抛出 `IncompleteReadError`）。

```python
import asyncio
import contextlib
import struct
import logging

logger = logging.getLogger(__name__)


class SOCKS5Proxy:
    """支持 CONNECT 和可选认证的异步 SOCKS5 代理（RFC 1928）。"""

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
        """第一阶段：客户端提供认证方法，服务器选择一个。"""
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
        """第二阶段：用户名/密码子协商（RFC 1929）。"""
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
        """第三阶段：解析 CONNECT 请求并建立隧道。"""
        header = await reader.readexactly(4)
        version, command, _, atyp = header

        # 根据地址类型解析目标地址
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

        # BND.ADDR 和 BND.PORT 应反映连接成功后的本地套接字地址。
        # 大多数客户端对 CONNECT 命令忽略这些字段，但正确填充
        # 满足 RFC 1928 的要求。
        local = server_writer.get_extra_info('sockname')
        await self._reply(writer, 0x00, local[0], local[1])

        await asyncio.gather(
            self._pipe(reader, server_writer),
            self._pipe(server_reader, writer),
        )

    async def _reply(self, writer, status, bind_addr='0.0.0.0', bind_port=0):
        """发送带有指定状态和绑定地址的 SOCKS5 回复。"""
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

当地址类型为 `0x03`（域名）时，代理通过 `asyncio.open_connection()` 自行解析 DNS。这是 SOCKS5 代理的核心隐私特性：客户端发送域名而不是在本地解析，从而防止 DNS 查询泄露到客户端的本地网络。这与 Chrome 配置 `--proxy-server=socks5://...` 时的行为相同，如[SOCKS 代理](./socks-proxies.md)中所述。

`_reply` 方法在成功连接后用实际的本地套接字地址填充 `BND.ADDR` 和 `BND.PORT`，这是 RFC 1928 的要求。许多 SOCKS5 实现在这里返回 `0.0.0.0:0`，因为大多数客户端对 CONNECT 命令忽略这些字段，但正确填充它们没有任何代价，还能避免协议违规。

## 同时运行两个代理

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

可以使用 curl 进行测试：

```bash
# HTTP proxy
curl -x http://user:pass@localhost:8080 http://httpbin.org/ip

# HTTPS through HTTP proxy (CONNECT tunnel)
curl -x http://user:pass@localhost:8080 https://httpbin.org/ip

# SOCKS5 proxy
curl --socks5 localhost:1080 --proxy-user user:pass https://httpbin.org/ip
```

## 代码未处理的内容

这些实现省略了生产代理需要处理的若干事项。理解缺少什么与理解已有什么同样具有教育意义。

没有连接限制。`asyncio.start_server` 无限制地接受连接，因此单个客户端打开数千个连接会耗尽文件描述符。生产代理使用信号量或连接池来限制并发数。

没有目标验证。两个代理都会连接到客户端请求的任何地址，包括 `127.0.0.1`、`169.254.169.254`（云元数据）和内部网络范围。这是一个服务端请求伪造（SSRF）向量。生产代理维护私有和链路本地地址范围的拒绝列表。

没有流量日志或指标。生产代理跟踪请求数量、传输字节数、错误率和延迟百分位数，通常导出到 Prometheus 或类似系统。

HTTP 代理没有添加 `Via` 头。RFC 9110 第 7.6.3 节要求中间节点在转发消息时附加 `Via` 字段。为了简洁起见这里省略了，但符合标准的代理必须包含它。

两个代理都没有实现优雅关闭。当服务器停止时，活跃的隧道会被突然终止，而不是被排空。生产代理跟踪活跃连接并等待它们完成（有截止时间），然后才关闭。

## 代理链

代理链是指将流量依次通过多个代理路由：客户端到代理 A，代理 A 到代理 B，代理 B 到目标服务器。链中的每个代理只知道其直接邻居，而非完整路径。

主要用例是分散信任。如果你不完全信任任何单一代理提供商，将两个提供商链接在一起意味着没有一个能同时看到你的真实 IP 和你的目标地址。代价是延迟：每一跳都会增加自己的连接建立时间和转发延迟。单个代理通常增加 50 到 100ms 的开销。两个代理大约翻倍，三个代理可以使总开销超过 300ms。

超过两跳后，边际隐私收益递减，而延迟和故障概率增加。大多数实际部署使用一到两个代理。Tor 使用三个中继节点（守卫节点、中间节点、出口节点），因为其威胁模型假设某些中继节点已被入侵，但 Tor 将延迟惩罚视为明确的设计权衡。

```
Client --> Proxy A (SOCKS5) --> Proxy B (SOCKS5) --> Target
           sees: client IP          sees: Proxy A IP
           sees: Proxy B addr       sees: target addr
```

通过另一个 SOCKS5 代理链接 SOCKS5 代理的工作方式是让代理 A 将代理 B 视为目标。客户端连接到代理 A 并发送指向代理 B 地址的 CONNECT 请求。一旦该隧道建立，客户端通过隧道发送第二次 SOCKS5 握手，这次请求真正的目标。代理 A 看到流向代理 B 的流量，但如果内部连接已加密，则无法读取其内容。

## 参考资料

- RFC 1928: SOCKS Protocol Version 5 - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- mitmproxy (Python HTTPS intercepting proxy) - https://mitmproxy.org/
