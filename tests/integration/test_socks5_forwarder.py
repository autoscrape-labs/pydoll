"""Integration tests for the SOCKS5 forwarder over real loopback sockets.

The forwarder is a local no-auth SOCKS5 proxy that authenticates against a remote
SOCKS5 proxy. These tests wire a full real chain:

    client -> SOCKS5Forwarder -> fake remote (auth) proxy -> echo server

and assert observable behaviour: data is forwarded end to end, credentials are
sent to the remote, and the SOCKS5 reply codes are correct for the failure and
edge cases. No mocks — everything talks real SOCKS5 over 127.0.0.1.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import struct

import pytest
import pytest_asyncio

from pydoll.utils.socks5_proxy_forwarder import SOCKS5Forwarder

VERSION = 0x05
NO_AUTH = 0x00
USER_PASS = 0x02
NO_ACCEPTABLE = 0xFF
CMD_CONNECT = 0x01
CMD_BIND = 0x02
ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except OSError:
        pass
    finally:
        with contextlib.suppress(OSError):
            writer.close()


def _port_of(server: asyncio.Server) -> int:
    return server.sockets[0].getsockname()[1]


@pytest_asyncio.fixture
async def echo_server():
    async def handle(reader, writer):
        await _pipe(reader, writer)

    server = await asyncio.start_server(handle, '127.0.0.1', 0)
    try:
        yield '127.0.0.1', _port_of(server)
    finally:
        server.close()
        await server.wait_closed()


def _make_remote_proxy(username: str, password: str, accept_auth: bool = True):
    received: dict = {}

    async def handle(reader, writer):
        try:
            version, nmethods = await reader.readexactly(2)
            await reader.readexactly(nmethods)
            writer.write(bytes([VERSION, USER_PASS]))
            await writer.drain()

            await reader.readexactly(1)
            ulen = (await reader.readexactly(1))[0]
            uname = await reader.readexactly(ulen)
            plen = (await reader.readexactly(1))[0]
            passwd = await reader.readexactly(plen)
            received['username'] = uname.decode()
            received['password'] = passwd.decode()

            ok = accept_auth and uname.decode() == username and passwd.decode() == password
            writer.write(bytes([0x01, 0x00 if ok else 0x01]))
            await writer.drain()
            if not ok:
                writer.close()
                return

            req = await reader.readexactly(4)
            atyp = req[3]
            if atyp == ATYP_IPV4:
                dest_host = socket.inet_ntoa(await reader.readexactly(4))
            elif atyp == ATYP_DOMAIN:
                length = (await reader.readexactly(1))[0]
                dest_host = (await reader.readexactly(length)).decode()
            else:
                writer.close()
                return
            dest_port = struct.unpack('!H', await reader.readexactly(2))[0]

            target_reader, target_writer = await asyncio.open_connection(dest_host, dest_port)
            writer.write(bytes([VERSION, 0x00, 0x00, ATYP_IPV4, 0, 0, 0, 0, 0, 0]))
            await writer.drain()
            await asyncio.gather(
                _pipe(reader, target_writer),
                _pipe(target_reader, writer),
            )
        except (asyncio.IncompleteReadError, OSError):
            with contextlib.suppress(OSError):
                writer.close()

    return handle, received


@pytest_asyncio.fixture
async def remote_proxy():
    handle, received = _make_remote_proxy('user', 'pass')
    server = await asyncio.start_server(handle, '127.0.0.1', 0)
    try:
        yield '127.0.0.1', _port_of(server), received
    finally:
        server.close()
        await server.wait_closed()


@pytest_asyncio.fixture
async def forwarder(remote_proxy):
    remote_host, remote_port, _ = remote_proxy
    fwd = SOCKS5Forwarder(
        remote_host=remote_host,
        remote_port=remote_port,
        username='user',
        password='pass',
        local_port=0,
    )
    await fwd.start()
    try:
        yield fwd
    finally:
        await fwd.stop()


async def _client_connect(port, dest_host, dest_port, *, atyp=ATYP_IPV4, cmd=CMD_CONNECT, offer_no_auth=True):
    """Run the client side of the SOCKS5 no-auth handshake against the forwarder.

    Returns (reader, writer, method_byte, reply_code). reply_code is None when the
    greeting itself was rejected (no CONNECT is attempted).
    """
    reader, writer = await asyncio.open_connection('127.0.0.1', port)
    methods = bytes([NO_AUTH]) if offer_no_auth else bytes([USER_PASS])
    writer.write(bytes([VERSION, len(methods)]) + methods)
    await writer.drain()
    method_selection = await reader.readexactly(2)
    if method_selection[1] != NO_AUTH:
        return reader, writer, method_selection[1], None

    if atyp == ATYP_DOMAIN:
        encoded = dest_host.encode()
        request = bytes([VERSION, cmd, 0x00, ATYP_DOMAIN, len(encoded)]) + encoded
    else:
        request = bytes([VERSION, cmd, 0x00, ATYP_IPV4]) + socket.inet_aton(dest_host)
    request += struct.pack('!H', dest_port)
    writer.write(request)
    await writer.drain()

    reply_header = await reader.readexactly(4)
    await reader.readexactly(4 + 2)
    return reader, writer, method_selection[1], reply_header[1]


@pytest.mark.asyncio
async def test_forwards_data_end_to_end_over_ipv4(forwarder, echo_server):
    echo_host, echo_port = echo_server
    reader, writer, _, reply = await _client_connect(forwarder.local_port, echo_host, echo_port)
    try:
        assert reply == 0x00
        writer.write(b'hello through socks')
        await writer.drain()
        assert await reader.readexactly(len(b'hello through socks')) == b'hello through socks'
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_forwards_credentials_to_remote(forwarder, echo_server, remote_proxy):
    echo_host, echo_port = echo_server
    _, _, received = remote_proxy
    reader, writer, _, reply = await _client_connect(forwarder.local_port, echo_host, echo_port)
    try:
        assert reply == 0x00
        assert received['username'] == 'user'
        assert received['password'] == 'pass'
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_forwards_data_with_domain_address_type(forwarder, echo_server):
    _, echo_port = echo_server
    reader, writer, _, reply = await _client_connect(
        forwarder.local_port, 'localhost', echo_port, atyp=ATYP_DOMAIN
    )
    try:
        assert reply == 0x00
        writer.write(b'domain ping')
        await writer.drain()
        assert await reader.readexactly(len(b'domain ping')) == b'domain ping'
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_remote_auth_failure_reports_general_failure(echo_server):
    echo_host, echo_port = echo_server
    handle, _ = _make_remote_proxy('user', 'pass', accept_auth=False)
    remote = await asyncio.start_server(handle, '127.0.0.1', 0)
    fwd = SOCKS5Forwarder('127.0.0.1', _port_of(remote), 'user', 'pass', local_port=0)
    await fwd.start()
    try:
        _, writer, _, reply = await _client_connect(fwd.local_port, echo_host, echo_port)
        assert reply == 0x01
        writer.close()
    finally:
        await fwd.stop()
        remote.close()
        await remote.wait_closed()


@pytest.mark.asyncio
async def test_client_without_no_auth_is_rejected(forwarder, echo_server):
    echo_host, echo_port = echo_server
    _, writer, method_byte, reply = await _client_connect(
        forwarder.local_port, echo_host, echo_port, offer_no_auth=False
    )
    try:
        assert method_byte == NO_ACCEPTABLE
        assert reply is None
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_unsupported_command_is_rejected(forwarder, echo_server):
    echo_host, echo_port = echo_server
    _, writer, _, reply = await _client_connect(
        forwarder.local_port, echo_host, echo_port, cmd=CMD_BIND
    )
    try:
        assert reply == 0x07
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_unsupported_address_type_is_rejected(forwarder):
    reader, writer = await asyncio.open_connection('127.0.0.1', forwarder.local_port)
    try:
        writer.write(bytes([VERSION, 1, NO_AUTH]))
        await writer.drain()
        await reader.readexactly(2)
        writer.write(bytes([VERSION, CMD_CONNECT, 0x00, 0x09]) + struct.pack('!H', 80))
        await writer.drain()
        reply_header = await reader.readexactly(4)
        assert reply_header[1] == 0x08
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_unreachable_remote_reports_connection_refused(echo_server):
    echo_host, echo_port = echo_server
    closed_port = _find_closed_port()
    fwd = SOCKS5Forwarder('127.0.0.1', closed_port, 'user', 'pass', local_port=0)
    await fwd.start()
    try:
        _, writer, _, reply = await _client_connect(fwd.local_port, echo_host, echo_port)
        assert reply in (0x05, 0x01)
        writer.close()
    finally:
        await fwd.stop()


@pytest.mark.asyncio
async def test_oversized_credentials_are_rejected():
    with pytest.raises(ValueError):
        SOCKS5Forwarder('127.0.0.1', 1080, 'u' * 256, 'pass')
    with pytest.raises(ValueError):
        SOCKS5Forwarder('127.0.0.1', 1080, 'user', 'p' * 256)


def _find_closed_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]
