# 搭建一个 proxy 服务器

要理解一个 proxy 做了什么，就动手造一个。本页用 Python 和 asyncio 从零实现一个 HTTP proxy 和一个 SOCKS5 proxy，好让你看清每个字节是怎么被解析的、安全边界在哪里，以及真正的 proxy 软件为什么会做出那些选择。要在 Pydoll 中使用一个 proxy 而非自己造，见 [Proxy](../../guides/proxies.md)；Pydoll 还在 `pydoll.utils` 中提供了一个 `SOCKS5Forwarder`，所以带认证的 SOCKS5 场景你不必自己造。

!!! warning "教学用代码"
    这些实现偏重清晰而非健壮。它们缺少连接数限制、访问控制，以及一个生产级 proxy 所需的许多错误恢复路径。不要把它们暴露给不受信任的网络。

## HTTP proxy

一个 HTTP proxy 以两种模式运作。对明文 HTTP，它接收完整的请求（带一个绝对形式的 URL，例如 `GET http://example.com/path HTTP/1.1`），把 request-target 重写为源形式（`GET /path HTTP/1.1`），连接到目标服务器，转发请求，并把响应管道回传。对 HTTPS，客户端发送一个 `CONNECT host:port` 请求，proxy 打开一条到目标的 TCP 连接，回复 `200 Connection Established`，然后在双向上盲目地中继字节，不检视加密内容。

下面的实现同时处理这两种模式。在你读它时有几点值得留意。`_pipe_data` 方法在一侧关闭时调用 `write_eof()`，这会向另一侧发送一个 TCP FIN。没有它，隧道就会无限期挂起，因为另一侧的 `read()` 永远不会返回空字节。HTTP 转发路径用的是同样的管道方式，而非单次 `read()` 调用，因为 HTTP 响应可以任意大，而固定大小的读取会悄无声息地把它们截断。request-target 的重写保留了查询字符串，而单靠 `urlparse().path` 会把它丢掉。

```python
import asyncio
import base64
import contextlib
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTPProxy:
    """带可选 Basic 认证的异步 HTTP/HTTPS proxy。"""

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
        """为 HTTPS 建立一条盲的 TCP 隧道。"""
        # 解析 host:port，处理像 [::1]:443 这样的 IPv6 字面量
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
        """转发一个明文 HTTP 请求。"""
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 80

        # 在 request-target 中保留查询字符串
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

        # 把 request-target 从绝对形式重写为源形式
        request = f'{method} {path} HTTP/1.1\r\n'

        # 如果端口非标准，Host header 必须包含端口
        if port != 80:
            request += f'Host: {host}:{port}\r\n'
        else:
            request += f'Host: {host}\r\n'

        # 移除不得转发的逐跳 header
        hop_by_hop = {
            'proxy-authorization', 'proxy-connection',
            'connection', 'keep-alive', 'te', 'trailer', 'upgrade',
        }
        for key, value in headers.items():
            if key not in hop_by_hop:
                request += f'{key}: {value}\r\n'

        # 强制 Connection: close，好让服务器不做 keep-alive，
        # 否则会阻止响应流结束
        request += 'Connection: close\r\n\r\n'

        server_writer.write(request.encode('latin-1'))

        # 如果存在请求 body 就转发
        content_length = int(headers.get('content-length', 0))
        if content_length > 0:
            body = await client_reader.readexactly(content_length)
            server_writer.write(body)

        await server_writer.drain()

        # 把整个响应回传（而不是一次固定大小的读取）
        while True:
            chunk = await server_reader.read(65536)
            if not chunk:
                break
            client_writer.write(chunk)
            await client_writer.drain()

        server_writer.close()
        await server_writer.wait_closed()

    async def _pipe(self, reader, writer):
        """带正确半关闭的双向数据中继。"""
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

还有几个值得理解的协议细节。HTTP header 是用 ISO-8859-1（Latin-1）编码的，而不是 UTF-8。Latin-1 把每一个字节值 0-255 都映射到一个字符，所以 `decode('latin-1')` 永远不会抛出 `UnicodeDecodeError`，而 `decode('utf-8')` 会在某些 header 值上崩溃。`Proxy-Authorization` header 使用 Base64 编码，但 Base64 不是加密：凭据以明文（或者说，可轻易逆转的编码）传输，除非客户端与 proxy 之间的连接本身受 TLS 保护。逐跳 header（`Connection`、`Keep-Alive`、`TE`、`Trailer`、`Upgrade`、`Proxy-Connection`）是给两个节点之间那一段直连用的，而不是给端到端转发用的。RFC 9110 第 7.6.1 节要求 proxy 在转发前把它们剥除。

!!! warning "SSRF 风险"
    这个实现不校验目的地址。一个客户端可以请求 `CONNECT 127.0.0.1:6379` 去够到一个本地的 Redis 实例，或者 `CONNECT 169.254.169.254:80` 去访问云实例元数据（AWS、GCP、Azure）。任何暴露给不受信任客户端的 proxy 都必须依据一个私有和链路本地范围的拒绝列表来校验目的地（`127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`、`::1`、`fc00::/7`）。

## SOCKS5 proxy

一个 SOCKS5 proxy 工作在比 HTTP 更低的层级。它使用一个由 RFC 1928 定义的二进制协议，包含三个阶段：方法协商、可选的认证，以及连接请求。这个 proxy 完全不解析 HTTP。一旦隧道建立，它就中继原始字节，不理解其中流动的是什么协议。

SOCKS5 的二进制本性意味着每一次读取都必须收到恰好预期数量的字节。TCP 是一个流式协议，并不保证 `read(4)` 会返回 4 个字节：视网络状况它可能返回 1、2 或 3 个字节。下面的实现使用 asyncio 的 `readexactly()`，它会在内部缓冲，直到请求数量的字节到齐，或者连接关闭（抛出 `IncompleteReadError`）。

```python
import asyncio
import contextlib
import struct
import logging

logger = logging.getLogger(__name__)


class SOCKS5Proxy:
    """支持 CONNECT、带可选认证的异步 SOCKS5 proxy（RFC 1928）。"""

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
        """阶段 1：客户端提供认证方法，服务器选一个。"""
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
        """阶段 2：用户名/密码子协商（RFC 1929）。"""
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
        """阶段 3：解析 CONNECT 请求并建立隧道。"""
        header = await reader.readexactly(4)
        version, command, _, atyp = header

        # 根据地址类型解析目的地址
        if atyp == 0x01:  # IPv4
            raw = await reader.readexactly(4)
            address = '.'.join(str(b) for b in raw)
        elif atyp == 0x03:  # 域名
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

        if command != 0x01:  # 只实现了 CONNECT
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

        # BND.ADDR 和 BND.PORT 应反映本地 socket 地址。
        # 对 CONNECT，大多数客户端会忽略这些，但正确填充它们
        # 符合 RFC 1928。
        local = server_writer.get_extra_info('sockname')
        await self._reply(writer, 0x00, local[0], local[1])

        await asyncio.gather(
            self._pipe(reader, server_writer),
            self._pipe(server_reader, writer),
        )

    async def _reply(self, writer, status, bind_addr='0.0.0.0', bind_port=0):
        """发送一个带给定状态和绑定地址的 SOCKS5 回复。"""
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

当地址类型是 `0x03`（域名）时，proxy 通过 `asyncio.open_connection()` 自己解析 DNS。这是 SOCKS5 代理决定性的隐私属性：客户端发送域名而非在本地解析它，这就防止了 DNS 查询泄露到客户端的本地网络。当 Chrome 配置了 `--proxy-server=socks5://...` 时依赖的就是同样的行为，正如 [SOCKS proxy](./socks-proxies.md) 中所讨论的。

`_reply` 方法在一次成功连接之后，用实际的本地 socket 地址填充 `BND.ADDR` 和 `BND.PORT`，正如 RFC 1928 所要求的。许多 SOCKS5 实现在这里返回 `0.0.0.0:0`，因为大多数客户端对 CONNECT 命令会忽略这些字段，但正确填充它们不费什么力气，还能避免一处协议违规。

## 同时运行两个 proxy

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

你可以用 curl 测试它们：

```bash
# HTTP proxy
curl -x http://user:pass@localhost:8080 http://httpbin.org/ip

# 经由 HTTP proxy 的 HTTPS（CONNECT 隧道）
curl -x http://user:pass@localhost:8080 https://httpbin.org/ip

# SOCKS5 proxy
curl --socks5 localhost:1080 --proxy-user user:pass https://httpbin.org/ip
```

## 这些代码没有处理什么

这些实现省略了生产级 proxy 会处理的若干东西。理解缺了什么，和理解有什么一样有启发。

没有连接数限制。`asyncio.start_server` 无上限地接受连接，所以单个客户端打开成千上万条连接就会耗尽文件描述符。生产级 proxy 用信号量或连接池来限制并发。

没有目的地校验。两个 proxy 都会连接到客户端所请求的任何地址，包括 `127.0.0.1`、`169.254.169.254`（云元数据）和内部网络范围。这是一个服务端请求伪造（SSRF）的路径。生产级 proxy 会维护私有和链路本地地址范围的拒绝列表。

没有流量日志或指标。生产级 proxy 会跟踪请求数、传输字节数、错误率和延迟百分位，通常导出到 Prometheus 或类似系统。

这个 HTTP proxy 不添加 `Via` header。RFC 9110 第 7.6.3 节要求中间节点向转发的消息追加一个 `Via` 字段。为求简单这里省略了，但一个符合标准的 proxy 必须包含它。

两个 proxy 都没有实现优雅关闭。当服务器停止时，活跃的隧道会被骤然终止，而不是被排空。生产级 proxy 会跟踪活跃连接，并在关闭前等它们完成（带一个截止期限）。

## proxy 链

链接 proxy 意味着让流量依次经过多个 proxy：客户端到 proxy A，proxy A 到 proxy B，proxy B 到目标服务器。链中的每个 proxy 只知道它紧邻的邻居，而不知道完整的路径。

主要的用例是分散信任。如果你不完全信任任何单一的 proxy 提供商，链接两家提供商就意味着没有任何一家能同时看到你的真实 IP 和你的目的地。代价是延迟：每一跳都增加它自己的连接建立时间和转发延迟。单个 proxy 通常增加 50 到 100ms 的开销。两个 proxy 大致翻倍，三个 proxy 能把总开销推过 300ms。

超过两跳之后，隐私的边际收益递减，而延迟和失败概率上升。多数实用配置用一个或两个 proxy。Tor 用三个中继（guard、middle、exit），因为它的威胁模型假设某些中继已被攻陷，但 Tor 把延迟代价当作一个明确的设计取舍来接受。

```
Client --> Proxy A (SOCKS5) --> Proxy B (SOCKS5) --> Target
           看到：客户端 IP         看到：Proxy A 的 IP
           看到：Proxy B 地址       看到：目标地址
```

把一个 SOCKS5 proxy 经由另一个 SOCKS5 proxy 链接起来，做法是让 proxy A 把 proxy B 当作目标。客户端连接到 proxy A，并为 proxy B 的地址发送一个 CONNECT 请求。一旦那条隧道建立，客户端就通过隧道发送第二次 SOCKS5 握手，这次请求真正的目标。proxy A 看到流量流向 proxy B，但如果内层连接是加密的，它读不了。

## 相关内容

- [网络基础](network-fundamentals.md)：这些代码把字节搬过去的那些层。
- [HTTP/HTTPS proxy](http-proxies.md) 和 [SOCKS proxy](socks-proxies.md)：这里所实现的协议。
- [Proxy](../../guides/proxies.md)：在 Pydoll 中配置一个 proxy，而非自己造。

## 参考资料

- RFC 1928: SOCKS Protocol Version 5 - https://datatracker.ietf.org/doc/html/rfc1928
- RFC 1929: Username/Password Authentication for SOCKS V5 - https://datatracker.ietf.org/doc/html/rfc1929
- RFC 9110: HTTP Semantics - https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 9112: HTTP/1.1 - https://www.rfc-editor.org/rfc/rfc9112.html
- OWASP SSRF Prevention Cheat Sheet - https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- mitmproxy (Python HTTPS intercepting proxy) - https://mitmproxy.org/
