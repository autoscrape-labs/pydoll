"""Unit tests for SOCKS5Forwarder handshake parsing (error paths).

The integration suite covers a working forward; these drive the SOCKS5 greeting/
request parsing deterministically by feeding byte sequences through a real
asyncio.StreamReader, asserting the rejections and the verbatim address parsing
the forwarder must get right.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll.utils.socks5_proxy_forwarder import (
    ATYP_DOMAIN,
    ATYP_IPV4,
    ATYP_IPV6,
    CMD_CONNECT,
    SOCKS5_VERSION,
    SOCKS5Forwarder,
    _HandshakeError,
    _read_exact,
)


def _reader(data: bytes) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    reader.feed_data(data)
    reader.feed_eof()
    return reader


class _FakeWriter:
    def __init__(self) -> None:
        self.buffer = bytearray()

    def write(self, data: bytes) -> None:
        self.buffer.extend(data)

    async def drain(self) -> None:
        return None


def _forwarder() -> SOCKS5Forwarder:
    return SOCKS5Forwarder('proxy.example', 1080, 'user', 'pass')


def test_constructor_rejects_oversized_credentials():
    with pytest.raises(ValueError):
        SOCKS5Forwarder('h', 1, 'u' * 256, 'p')
    with pytest.raises(ValueError):
        SOCKS5Forwarder('h', 1, 'u', 'p' * 256)


@pytest.mark.asyncio
async def test_read_raw_address_ipv4_keeps_atyp_prefix():
    raw = await SOCKS5Forwarder._read_raw_address(_reader(b'\x7f\x00\x00\x01'), ATYP_IPV4)
    assert raw == bytes([ATYP_IPV4]) + b'\x7f\x00\x00\x01'


@pytest.mark.asyncio
async def test_read_raw_address_domain_includes_length():
    reader = _reader(bytes([3]) + b'abc')
    raw = await SOCKS5Forwarder._read_raw_address(reader, ATYP_DOMAIN)
    assert raw == bytes([ATYP_DOMAIN, 3]) + b'abc'


@pytest.mark.asyncio
async def test_read_raw_address_ipv6_reads_16_bytes():
    raw = await SOCKS5Forwarder._read_raw_address(_reader(b'\x00' * 16), ATYP_IPV6)
    assert raw == bytes([ATYP_IPV6]) + b'\x00' * 16


@pytest.mark.asyncio
async def test_read_raw_address_unsupported_type_raises():
    with pytest.raises(_HandshakeError):
        await SOCKS5Forwarder._read_raw_address(_reader(b''), 0x09)


@pytest.mark.asyncio
async def test_send_reply_writes_socks5_frame():
    writer = _FakeWriter()
    await SOCKS5Forwarder._send_reply(writer, 0x00)
    assert writer.buffer[0] == SOCKS5_VERSION
    assert writer.buffer[1] == 0x00


@pytest.mark.asyncio
async def test_read_exact_raises_on_premature_close():
    with pytest.raises(_HandshakeError):
        await _read_exact(_reader(b'\x05'), 4, peer='client')


@pytest.mark.asyncio
async def test_accept_handshake_rejects_bad_version():
    forwarder = _forwarder()
    with pytest.raises(_HandshakeError):
        await forwarder._accept_local_handshake(_reader(b'\x04\x01\x00'), _FakeWriter())


@pytest.mark.asyncio
async def test_accept_handshake_rejects_when_no_no_auth_method():
    forwarder = _forwarder()
    writer = _FakeWriter()
    with pytest.raises(_HandshakeError):
        await forwarder._accept_local_handshake(_reader(b'\x05\x01\x02'), writer)
    assert writer.buffer  # sent a NO_ACCEPTABLE reply


@pytest.mark.asyncio
async def test_accept_handshake_rejects_unsupported_command():
    forwarder = _forwarder()
    # greeting (no-auth) + request with command 2 (BIND) instead of CONNECT
    data = b'\x05\x01\x00' + bytes([SOCKS5_VERSION, 0x02, 0x00, ATYP_IPV4])
    with pytest.raises(_HandshakeError):
        await forwarder._accept_local_handshake(_reader(data), _FakeWriter())


@pytest.mark.asyncio
async def test_accept_handshake_parses_valid_connect():
    forwarder = _forwarder()
    data = (
        b'\x05\x01\x00'
        + bytes([SOCKS5_VERSION, CMD_CONNECT, 0x00, ATYP_IPV4])
        + b'\x7f\x00\x00\x01'
        + b'\x1f\x90'  # port 8080
    )
    addr_payload, port = await forwarder._accept_local_handshake(_reader(data), _FakeWriter())
    assert addr_payload == bytes([ATYP_IPV4]) + b'\x7f\x00\x00\x01'
    assert port == 8080
