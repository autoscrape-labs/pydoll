"""
SOCKS5 Proxy Forwarder — Local no-auth proxy that forwards to a remote
authenticated SOCKS5 proxy.

Chrome/Chromium does NOT support SOCKS5 authentication natively
(Chromium issue #40323993). This module works around that limitation by
running a lightweight local SOCKS5 proxy (no authentication required)
that performs the SOCKS5 handshake with username/password on behalf of
the browser.

Data flow:
    Chrome ──► localhost:{local_port} (no auth)
                    │
              SOCKS5Forwarder
                    │  (authenticates with remote)
                    ▼
           remote_host:remote_port (user/pass auth)
                    │
                    ▼
              destination server

Usage as CLI:
    python -m pydoll.utils.socks5_proxy_forwarder \\
        --remote-host proxy.example.com \\
        --remote-port 1080 \\
        --username myuser \\
        --password mypass \\
        --local-port 1081

Usage with Pydoll:
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
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')
            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())

Requirements: Python >= 3.10, no external dependencies.
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import logging
import signal
import struct
from types import TracebackType

logger = logging.getLogger(__name__)

SOCKS5_VERSION = 0x05
AUTH_NO_AUTH = 0x00
AUTH_USERNAME_PASSWORD = 0x02
AUTH_NO_ACCEPTABLE = 0xFF

CMD_CONNECT = 0x01

ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04

REPLY_SUCCESS = 0x00
REPLY_GENERAL_FAILURE = 0x01
REPLY_CONNECTION_REFUSED = 0x05
REPLY_COMMAND_NOT_SUPPORTED = 0x07
REPLY_ADDRESS_TYPE_NOT_SUPPORTED = 0x08

BUFFER_SIZE = 65536
HANDSHAKE_TIMEOUT = 30
MAX_CREDENTIAL_BYTES = 255


class _suppress_closed:
    """Tiny context manager that silences errors on already-closed transports."""

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is not None and issubclass(exc_type, OSError)


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    """Close a stream writer and wait for the transport to finish."""
    with _suppress_closed():
        writer.close()
        await writer.wait_closed()


async def _pipe(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    label: str,
) -> None:
    """Forward data from *reader* to *writer* until EOF."""
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        await _close_writer(writer)


class SOCKS5Forwarder:
    """Local SOCKS5 proxy (no auth) that forwards to a remote authenticated
    SOCKS5 proxy.

    Can be used as an async context manager::

        async with SOCKS5Forwarder(...) as fwd:
            # fwd.local_port is now listening
            ...
    """

    def __init__(
        self,
        remote_host: str,
        remote_port: int,
        username: str,
        password: str,
        local_host: str = '127.0.0.1',
        local_port: int = 0,
    ) -> None:
        if len(username.encode()) > MAX_CREDENTIAL_BYTES:
            raise ValueError('SOCKS5 username must be at most 255 bytes (UTF-8 encoded)')
        if len(password.encode()) > MAX_CREDENTIAL_BYTES:
            raise ValueError('SOCKS5 password must be at most 255 bytes (UTF-8 encoded)')
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.username = username
        self.password = password
        self.local_host = local_host
        self.local_port = local_port
        self._server: asyncio.Server | None = None

    async def __aenter__(self) -> SOCKS5Forwarder:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def start(self) -> None:
        """Start accepting connections on *local_host*:*local_port*."""
        try:
            addr = ipaddress.ip_address(self.local_host)
        except ValueError:
            addr = None

        if addr is not None and not addr.is_loopback:
            logger.warning(
                'Binding to non-loopback address %s — the forwarder will be '
                'accessible from the network without authentication!',
                self.local_host,
            )
        elif addr is None and self.local_host != 'localhost':
            logger.debug(
                'local_host=%r is not an IP literal; skipping loopback check',
                self.local_host,
            )
        self._server = await asyncio.start_server(
            self._handle_client,
            self.local_host,
            self.local_port,
        )
        sockets = list(self._server.sockets or [])
        ports = {s.getsockname()[1] for s in sockets}
        if len(ports) != 1:
            await self.stop()
            raise RuntimeError(
                f'start_server created sockets with different ports: {sorted(ports)}. '
                "Use an explicit IP (e.g. '127.0.0.1' or '::1') instead of a hostname, "
                'or specify --local-port explicitly.'
            )
        self.local_port = ports.pop()
        logger.info(
            'SOCKS5 forwarder listening on %s:%s -> %s:%s',
            self.local_host,
            self.local_port,
            self.remote_host,
            self.remote_port,
        )

    async def stop(self) -> None:
        """Gracefully shut down the server."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info('SOCKS5 forwarder stopped')

    async def serve_forever(self) -> None:
        """Block until the server is closed (useful for CLI mode)."""
        if self._server is None:
            raise RuntimeError('Server not started — call start() first')
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        """Handle one incoming browser connection."""
        remote_writer: asyncio.StreamWriter | None = None
        try:
            addr_payload, dest_port = await self._accept_local_handshake(
                client_reader,
                client_writer,
            )
            r_reader, r_writer = await asyncio.wait_for(
                asyncio.open_connection(self.remote_host, self.remote_port),
                timeout=HANDSHAKE_TIMEOUT,
            )
            remote_writer = r_writer
            await self._remote_handshake(
                r_reader,
                r_writer,
                addr_payload,
                dest_port,
            )
            await self._send_reply(client_writer, REPLY_SUCCESS)
            await asyncio.gather(
                _pipe(client_reader, r_writer, 'client->remote'),
                _pipe(r_reader, client_writer, 'remote->client'),
            )
        except _HandshakeError as exc:
            logger.warning('Handshake failed: %s', exc)
            if exc.send_reply:
                with _suppress_closed():
                    await self._send_reply(client_writer, exc.reply_code)
        except asyncio.TimeoutError:
            logger.warning('Connection to remote proxy timed out')
            with _suppress_closed():
                await self._send_reply(client_writer, REPLY_GENERAL_FAILURE)
        except (ConnectionRefusedError, OSError) as exc:
            logger.warning('Connection to remote proxy failed: %s', exc)
            reply = (
                REPLY_CONNECTION_REFUSED
                if isinstance(exc, ConnectionRefusedError)
                else REPLY_GENERAL_FAILURE
            )
            with _suppress_closed():
                await self._send_reply(client_writer, reply)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('Unexpected error in client handler')
        finally:
            await _close_writer(client_writer)
            if remote_writer is not None:
                await _close_writer(remote_writer)

    async def _accept_local_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> tuple[bytes, int]:
        """Accept the SOCKS5 greeting from Chrome (no-auth) and read the
        CONNECT request.

        Returns ``(addr_payload, dest_port)`` where *addr_payload* is the raw
        SOCKS5 address field (ATYP byte + address bytes) exactly as Chrome
        sent it, ready to be forwarded verbatim to the remote proxy."""
        try:
            header = await _read_exact(reader, 2, peer='client')
        except _HandshakeError as exc:
            raise _HandshakeError(str(exc), send_reply=False) from exc
        version, nmethods = header[0], header[1]
        if version != SOCKS5_VERSION:
            raise _HandshakeError(
                f'Unsupported SOCKS version from client: {version}', send_reply=False
            )

        try:
            methods = await _read_exact(reader, nmethods, peer='client')
        except _HandshakeError as exc:
            raise _HandshakeError(str(exc), send_reply=False) from exc
        if AUTH_NO_AUTH not in methods:
            writer.write(bytes([SOCKS5_VERSION, AUTH_NO_ACCEPTABLE]))
            await writer.drain()
            raise _HandshakeError('Client does not offer no-auth method', send_reply=False)

        writer.write(bytes([SOCKS5_VERSION, AUTH_NO_AUTH]))
        await writer.drain()

        req = await _read_exact(reader, 4, peer='client')
        if req[0] != SOCKS5_VERSION:
            raise _HandshakeError('Bad SOCKS version in request')
        if req[1] != CMD_CONNECT:
            raise _HandshakeError(
                f'Unsupported command: {req[1]}',
                reply_code=REPLY_COMMAND_NOT_SUPPORTED,
            )

        atyp = req[3]
        addr_payload = await self._read_raw_address(reader, atyp, peer='client')
        dest_port = struct.unpack('!H', await _read_exact(reader, 2, peer='client'))[0]
        logger.debug('Client CONNECT to %s port %d', addr_payload.hex(), dest_port)
        return addr_payload, dest_port

    async def _remote_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        addr_payload: bytes,
        dest_port: int,
    ) -> None:
        """Perform full SOCKS5 handshake with the remote proxy including
        username/password authentication, then send the CONNECT request.

        *addr_payload* is the raw ATYP + address bytes from the client,
        forwarded verbatim so the address type is preserved."""
        greeting = bytes([SOCKS5_VERSION, 0x02, AUTH_NO_AUTH, AUTH_USERNAME_PASSWORD])
        writer.write(greeting)
        await writer.drain()
        logger.debug('-> greeting: %s', greeting.hex())

        resp = await _read_exact(reader, 2, peer='remote proxy')
        logger.debug('<- method selection: %s', resp.hex())

        if resp[0] != SOCKS5_VERSION:
            raise _HandshakeError(f'Remote proxy bad version (response: {resp.hex()})')

        selected_method = resp[1]
        if selected_method == AUTH_NO_ACCEPTABLE:
            raise _HandshakeError('Remote proxy rejected all auth methods')

        if selected_method == AUTH_USERNAME_PASSWORD:
            uname = self.username.encode()
            passwd = self.password.encode()
            auth_req = bytes([0x01, len(uname)]) + uname + bytes([len(passwd)]) + passwd
            writer.write(auth_req)
            await writer.drain()
            logger.debug('-> auth request: ulen=%d plen=%d', len(uname), len(passwd))

            auth_resp = await _read_exact(reader, 2, peer='remote proxy')
            logger.debug('<- auth response: %s', auth_resp.hex())
            if auth_resp[1] != 0x00:
                raise _HandshakeError(
                    f'Remote proxy authentication failed (status: {auth_resp[1]:#04x})'
                )
        elif selected_method == AUTH_NO_AUTH:
            logger.debug('Remote proxy selected no-auth (0x00)')
        else:
            raise _HandshakeError(
                f'Remote proxy selected unsupported method: {selected_method:#04x}'
            )

        connect_req = bytes([SOCKS5_VERSION, CMD_CONNECT, 0x00])
        connect_req += addr_payload
        connect_req += struct.pack('!H', dest_port)
        writer.write(connect_req)
        await writer.drain()
        logger.debug('-> CONNECT: %s', connect_req.hex())

        reply_header = await _read_exact(reader, 4, peer='remote proxy')
        logger.debug('<- reply header: %s', reply_header.hex())

        rep = reply_header[1]
        if rep != REPLY_SUCCESS:
            extra = b''
            try:
                extra = await asyncio.wait_for(reader.read(256), timeout=0.5)
            except (asyncio.TimeoutError, OSError):
                pass
            raise _HandshakeError(
                f'Remote proxy CONNECT failed '
                f'(rep={rep:#04x}, reply: {reply_header.hex()}, '
                f'extra: {extra.hex() if extra else "none"})',
                reply_code=rep,
            )

        atyp = reply_header[3]
        await self._read_raw_address(reader, atyp, peer='remote proxy')
        await _read_exact(reader, 2, peer='remote proxy')

    @staticmethod
    async def _read_raw_address(
        reader: asyncio.StreamReader,
        atyp: int,
        *,
        peer: str = 'peer',
    ) -> bytes:
        """Read a SOCKS5 address field and return raw bytes including the
        ATYP prefix, suitable for forwarding verbatim to another proxy."""
        if atyp == ATYP_IPV4:
            raw = await _read_exact(reader, 4, peer=peer)
            return bytes([atyp]) + raw
        if atyp == ATYP_DOMAIN:
            length_byte = await _read_exact(reader, 1, peer=peer)
            domain = await _read_exact(reader, length_byte[0], peer=peer)
            return bytes([atyp]) + length_byte + domain
        if atyp == ATYP_IPV6:
            raw = await _read_exact(reader, 16, peer=peer)
            return bytes([atyp]) + raw
        raise _HandshakeError(
            f'Unsupported address type: {atyp}',
            reply_code=REPLY_ADDRESS_TYPE_NOT_SUPPORTED,
        )

    @staticmethod
    async def _send_reply(
        writer: asyncio.StreamWriter,
        reply_code: int,
    ) -> None:
        """Send a minimal SOCKS5 reply to the client."""
        writer.write(
            bytes([
                SOCKS5_VERSION,
                reply_code,
                0x00,
                ATYP_IPV4,
                0,
                0,
                0,
                0,
                0,
                0,
            ])
        )
        await writer.drain()


class _HandshakeError(Exception):
    """Raised when a SOCKS5 handshake step fails."""

    def __init__(
        self,
        message: str,
        reply_code: int = REPLY_GENERAL_FAILURE,
        send_reply: bool = True,
    ) -> None:
        super().__init__(message)
        self.reply_code = reply_code
        self.send_reply = send_reply


async def _read_exact(reader: asyncio.StreamReader, n: int, *, peer: str = 'peer') -> bytes:
    """Read exactly *n* bytes or raise ``_HandshakeError``."""
    try:
        return await asyncio.wait_for(reader.readexactly(n), timeout=HANDSHAKE_TIMEOUT)
    except asyncio.IncompleteReadError as exc:
        raise _HandshakeError(
            f'Connection closed prematurely (expected {n} bytes, '
            f'got {len(exc.partial)} from {peer})'
        ) from exc
    except asyncio.TimeoutError as exc:
        raise _HandshakeError(
            f'Timed out reading {n} bytes from {peer}',
        ) from exc


async def _skip_bnd_address(reader: asyncio.StreamReader, atyp: int, *, peer: str = 'peer') -> None:
    """Consume BND.ADDR + BND.PORT from a SOCKS5 reply."""
    if atyp == ATYP_IPV4:
        await _read_exact(reader, 4 + 2, peer=peer)
    elif atyp == ATYP_DOMAIN:
        length = (await _read_exact(reader, 1, peer=peer))[0]
        await _read_exact(reader, length + 2, peer=peer)
    elif atyp == ATYP_IPV6:
        await _read_exact(reader, 16 + 2, peer=peer)


async def _main(args: argparse.Namespace) -> None:
    forwarder = SOCKS5Forwarder(
        remote_host=args.remote_host,
        remote_port=args.remote_port,
        username=args.username,
        password=args.password,
        local_host=args.local_host,
        local_port=args.local_port,
    )
    await forwarder.start()

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set_result, None)
    except NotImplementedError:
        pass  # Windows / ProactorEventLoop — fall back to KeyboardInterrupt

    logger.info(
        'Forwarding socks5://127.0.0.1:%s -> socks5://%s:***@%s:%s',
        forwarder.local_port,
        args.username,
        args.remote_host,
        args.remote_port,
    )
    logger.info('Press Ctrl+C to stop.')

    try:
        await stop
    finally:
        await forwarder.stop()


async def _test_negotiate_auth(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    username: str,
    password: str,
) -> bool:
    """Perform greeting + auth for the --test diagnostic. Returns True on success."""
    greeting = bytes([SOCKS5_VERSION, 0x02, AUTH_NO_AUTH, AUTH_USERNAME_PASSWORD])
    writer.write(greeting)
    await writer.drain()
    logger.info('-> Greeting:  %s', greeting.hex())

    resp = await asyncio.wait_for(reader.readexactly(2), timeout=10)
    logger.info('<- Method:    %s  (selected method: %#04x)', resp.hex(), resp[1])

    if resp[0] != SOCKS5_VERSION:
        logger.error('Bad version byte: %#04x', resp[0])
        return False

    if resp[1] == AUTH_USERNAME_PASSWORD:
        uname = username.encode()
        passwd = password.encode()
        auth_req = bytes([0x01, len(uname)]) + uname + bytes([len(passwd)]) + passwd
        writer.write(auth_req)
        await writer.drain()
        logger.info('-> Auth:      ulen=%d plen=%d', len(uname), len(passwd))

        auth_resp = await asyncio.wait_for(reader.readexactly(2), timeout=10)
        logger.info('<- Auth resp: %s  (status: %#04x)', auth_resp.hex(), auth_resp[1])
        if auth_resp[1] != 0x00:
            logger.error('Authentication rejected')
            return False
        logger.info('Authentication succeeded')
    elif resp[1] == AUTH_NO_AUTH:
        logger.info('Proxy selected no-auth')
    elif resp[1] == AUTH_NO_ACCEPTABLE:
        logger.error('Proxy rejected all auth methods')
        return False

    return True


async def _test_connect_and_verify(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bool:
    """Send CONNECT to httpbin.org:80 and verify with an HTTP request."""
    target = b'httpbin.org'
    connect_req = (
        bytes([SOCKS5_VERSION, CMD_CONNECT, 0x00, ATYP_DOMAIN, len(target)])
        + target
        + struct.pack('!H', 80)
    )
    writer.write(connect_req)
    await writer.drain()
    logger.info('-> CONNECT:   %s  (httpbin.org:80)', connect_req.hex())

    reply = await asyncio.wait_for(reader.readexactly(4), timeout=15)
    logger.info('<- Reply:     %s  (rep: %#04x)', reply.hex(), reply[1])

    if reply[1] != REPLY_SUCCESS:
        extra = b''
        try:
            extra = await asyncio.wait_for(reader.read(256), timeout=1)
        except (asyncio.TimeoutError, OSError):
            pass
        logger.error('CONNECT rejected — reply code %#04x', reply[1])
        if extra:
            logger.error('Extra data: %s', extra.hex())
        logger.error(
            'Possible causes: invalid/expired credentials, quota exceeded, '
            'IP not whitelisted, or wrong port'
        )
        return False

    await _skip_bnd_address(reader, reply[3], peer='remote proxy')
    logger.info('CONNECT established')

    http_req = b'GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'
    writer.write(http_req)
    await writer.drain()
    logger.info('-> HTTP GET /ip sent')

    http_resp = await asyncio.wait_for(reader.read(4096), timeout=15)
    decoded = http_resp.decode(errors='replace')
    logger.info('<- HTTP response (%d bytes):\n%s', len(http_resp), decoded)
    logger.info('Proxy is fully working!')
    return True


async def _test_proxy(args: argparse.Namespace) -> None:
    """Perform a direct SOCKS5 handshake test against the remote proxy."""
    logger.info('=== SOCKS5 Direct Test: %s:%s ===', args.remote_host, args.remote_port)

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(args.remote_host, args.remote_port),
            timeout=HANDSHAKE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error('TCP connection timed out')
        return
    except OSError as exc:
        logger.error('TCP connection failed: %s', exc)
        return

    logger.info('TCP connection established')

    try:
        if not await _test_negotiate_auth(reader, writer, args.username, args.password):
            return
        await _test_connect_and_verify(reader, writer)
    except _HandshakeError as exc:
        logger.error('SOCKS5 test failed: %s', exc)
    except asyncio.TimeoutError:
        logger.error('Timed out waiting for proxy response')
    except asyncio.IncompleteReadError as exc:
        logger.error('Connection closed prematurely (got %d bytes)', len(exc.partial))
    except OSError as exc:
        logger.error('Network error: %s', exc)
    finally:
        await _close_writer(writer)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description='Local SOCKS5 forwarder for authenticated remote proxies.',
    )
    parser.add_argument('--remote-host', required=True, help='Remote SOCKS5 proxy host')
    parser.add_argument('--remote-port', type=int, default=1080, help='Remote SOCKS5 proxy port')
    parser.add_argument('--username', required=True, help='Remote proxy username')
    parser.add_argument('--password', required=True, help='Remote proxy password')
    parser.add_argument('--local-host', default='127.0.0.1', help='Local bind address')
    parser.add_argument('--local-port', type=int, default=1081, help='Local bind port (0 = random)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the remote proxy directly (no local server, no Chrome needed)',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    if args.test:
        asyncio.run(_test_proxy(args))
    else:
        asyncio.run(_main(args))


if __name__ == '__main__':
    cli()
