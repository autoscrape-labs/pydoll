"""Tests for pydoll.utils.socks5_proxy_forwarder."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydoll.utils.socks5_proxy_forwarder import (
    HANDSHAKE_TIMEOUT,
    REPLY_ADDRESS_TYPE_NOT_SUPPORTED,
    REPLY_COMMAND_NOT_SUPPORTED,
    REPLY_CONNECTION_REFUSED,
    REPLY_GENERAL_FAILURE,
    REPLY_SUCCESS,
    SOCKS5Forwarder,
    _close_writer,
    _HandshakeError,
    _pipe,
    _read_exact,
    _skip_bnd_address,
    _suppress_closed,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def forwarder():
    return SOCKS5Forwarder(
        remote_host='proxy.example.com',
        remote_port=1080,
        username='user',
        password='pass',
        local_host='127.0.0.1',
        local_port=0,
    )


@pytest.fixture
def mock_reader():
    reader = AsyncMock(spec=asyncio.StreamReader)
    return reader


@pytest.fixture
def mock_writer():
    writer = MagicMock(spec=asyncio.StreamWriter)
    writer.close = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.wait_closed = AsyncMock()
    return writer


# ---------------------------------------------------------------------------
# _suppress_closed
# ---------------------------------------------------------------------------


class TestSuppressClosed:
    def test_suppresses_os_error(self):
        with _suppress_closed():
            raise OSError('transport closed')

    def test_suppresses_connection_reset(self):
        with _suppress_closed():
            raise ConnectionResetError('reset')

    def test_does_not_suppress_value_error(self):
        with pytest.raises(ValueError, match='not an os error'):
            with _suppress_closed():
                raise ValueError('not an os error')

    def test_no_error_passes_through(self):
        with _suppress_closed():
            pass  # no exception


# ---------------------------------------------------------------------------
# _HandshakeError
# ---------------------------------------------------------------------------


class TestHandshakeError:
    def test_default_reply_code(self):
        exc = _HandshakeError('something failed')
        assert exc.reply_code == REPLY_GENERAL_FAILURE
        assert str(exc) == 'something failed'

    def test_custom_reply_code(self):
        exc = _HandshakeError('cmd not supported', reply_code=REPLY_COMMAND_NOT_SUPPORTED)
        assert exc.reply_code == REPLY_COMMAND_NOT_SUPPORTED

    def test_connection_refused_reply_code(self):
        exc = _HandshakeError('refused', reply_code=REPLY_CONNECTION_REFUSED)
        assert exc.reply_code == REPLY_CONNECTION_REFUSED

    def test_send_reply_defaults_to_true(self):
        exc = _HandshakeError('fail')
        assert exc.send_reply is True

    def test_send_reply_false(self):
        exc = _HandshakeError('no auth', send_reply=False)
        assert exc.send_reply is False


# ---------------------------------------------------------------------------
# _read_exact
# ---------------------------------------------------------------------------


class TestReadExact:
    @pytest.mark.asyncio
    async def test_returns_exact_bytes(self, mock_reader):
        mock_reader.readexactly = AsyncMock(return_value=b'\x05\x01')
        result = await _read_exact(mock_reader, 2)
        assert result == b'\x05\x01'
        mock_reader.readexactly.assert_awaited_once_with(2)

    @pytest.mark.asyncio
    async def test_incomplete_read_raises_handshake_error(self, mock_reader):
        mock_reader.readexactly = AsyncMock(
            side_effect=asyncio.IncompleteReadError(partial=b'\x05', expected=2)
        )
        with pytest.raises(_HandshakeError, match='Connection closed prematurely'):
            await _read_exact(mock_reader, 2)

    @pytest.mark.asyncio
    async def test_incomplete_read_has_general_failure_code(self, mock_reader):
        mock_reader.readexactly = AsyncMock(
            side_effect=asyncio.IncompleteReadError(partial=b'', expected=4)
        )
        with pytest.raises(_HandshakeError) as exc_info:
            await _read_exact(mock_reader, 4)
        assert exc_info.value.reply_code == REPLY_GENERAL_FAILURE

    @pytest.mark.asyncio
    async def test_timeout_raises_handshake_error(self, mock_reader):
        async def hang_forever(n):
            await asyncio.sleep(999)

        mock_reader.readexactly = hang_forever

        with patch(
            'pydoll.utils.socks5_proxy_forwarder.HANDSHAKE_TIMEOUT', 0.01
        ):
            with pytest.raises(_HandshakeError, match='Timed out reading'):
                await _read_exact(mock_reader, 2)

    @pytest.mark.asyncio
    async def test_timeout_has_general_failure_code(self, mock_reader):
        async def hang_forever(n):
            await asyncio.sleep(999)

        mock_reader.readexactly = hang_forever

        with patch(
            'pydoll.utils.socks5_proxy_forwarder.HANDSHAKE_TIMEOUT', 0.01
        ):
            with pytest.raises(_HandshakeError) as exc_info:
                await _read_exact(mock_reader, 2)
            assert exc_info.value.reply_code == REPLY_GENERAL_FAILURE

    @pytest.mark.asyncio
    async def test_peer_label_in_timeout_message(self, mock_reader):
        async def hang_forever(n):
            await asyncio.sleep(999)

        mock_reader.readexactly = hang_forever

        with patch(
            'pydoll.utils.socks5_proxy_forwarder.HANDSHAKE_TIMEOUT', 0.01
        ):
            with pytest.raises(_HandshakeError, match='from remote proxy'):
                await _read_exact(mock_reader, 2, peer='remote proxy')

    @pytest.mark.asyncio
    async def test_peer_label_in_incomplete_read_message(self, mock_reader):
        mock_reader.readexactly = AsyncMock(
            side_effect=asyncio.IncompleteReadError(partial=b'\x05', expected=4)
        )
        with pytest.raises(_HandshakeError, match='from client'):
            await _read_exact(mock_reader, 4, peer='client')


# ---------------------------------------------------------------------------
# _skip_bnd_address (uses _read_exact, not raw readexactly)
# ---------------------------------------------------------------------------


class TestSkipBndAddress:
    @pytest.mark.asyncio
    async def test_ipv4(self, mock_reader):
        mock_reader.readexactly = AsyncMock(return_value=b'\x00' * 6)
        await _skip_bnd_address(mock_reader, 0x01)
        mock_reader.readexactly.assert_awaited_once_with(6)

    @pytest.mark.asyncio
    async def test_domain(self, mock_reader):
        call_count = 0
        responses = [b'\x0b', b'\x00' * 13]

        async def fake_readexactly(n):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        mock_reader.readexactly = fake_readexactly
        await _skip_bnd_address(mock_reader, 0x03)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_ipv6(self, mock_reader):
        mock_reader.readexactly = AsyncMock(return_value=b'\x00' * 18)
        await _skip_bnd_address(mock_reader, 0x04)
        mock_reader.readexactly.assert_awaited_once_with(18)

    @pytest.mark.asyncio
    async def test_incomplete_read_propagates(self, mock_reader):
        mock_reader.readexactly = AsyncMock(
            side_effect=asyncio.IncompleteReadError(partial=b'', expected=6)
        )
        with pytest.raises(_HandshakeError, match='Connection closed prematurely'):
            await _skip_bnd_address(mock_reader, 0x01)


# ---------------------------------------------------------------------------
# _close_writer
# ---------------------------------------------------------------------------


class TestCloseWriter:
    @pytest.mark.asyncio
    async def test_calls_close_and_wait_closed(self, mock_writer):
        await _close_writer(mock_writer)
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_suppresses_os_error_on_close(self):
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.close = MagicMock(side_effect=OSError('already closed'))
        writer.wait_closed = AsyncMock()
        await _close_writer(writer)  # should not raise

    @pytest.mark.asyncio
    async def test_suppresses_os_error_on_wait_closed(self):
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock(side_effect=OSError('transport closed'))
        await _close_writer(writer)  # should not raise


# ---------------------------------------------------------------------------
# _pipe
# ---------------------------------------------------------------------------


class TestPipe:
    @pytest.mark.asyncio
    async def test_forwards_data_until_eof(self, mock_reader, mock_writer):
        mock_reader.read = AsyncMock(side_effect=[b'hello', b'world', b''])
        await _pipe(mock_reader, mock_writer, 'test')
        assert mock_writer.write.call_count == 2
        mock_writer.write.assert_any_call(b'hello')
        mock_writer.write.assert_any_call(b'world')

    @pytest.mark.asyncio
    async def test_closes_writer_on_eof(self, mock_reader, mock_writer):
        mock_reader.read = AsyncMock(return_value=b'')
        await _pipe(mock_reader, mock_writer, 'test')
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_closes_writer_on_connection_reset(self, mock_reader, mock_writer):
        mock_reader.read = AsyncMock(side_effect=ConnectionResetError)
        await _pipe(mock_reader, mock_writer, 'test')
        mock_writer.close.assert_called_once()


# ---------------------------------------------------------------------------
# SOCKS5Forwarder.__init__ — credential length validation
# ---------------------------------------------------------------------------


class TestCredentialValidation:
    def test_valid_credentials(self):
        fwd = SOCKS5Forwarder(
            remote_host='host',
            remote_port=1080,
            username='user',
            password='pass',
        )
        assert fwd.username == 'user'
        assert fwd.password == 'pass'

    def test_username_too_long(self):
        long_user = 'a' * 256
        with pytest.raises(ValueError, match='username must be at most 255 bytes'):
            SOCKS5Forwarder(
                remote_host='host',
                remote_port=1080,
                username=long_user,
                password='pass',
            )

    def test_password_too_long(self):
        long_pass = 'b' * 256
        with pytest.raises(ValueError, match='password must be at most 255 bytes'):
            SOCKS5Forwarder(
                remote_host='host',
                remote_port=1080,
                username='user',
                password=long_pass,
            )

    def test_max_length_credentials_accepted(self):
        fwd = SOCKS5Forwarder(
            remote_host='host',
            remote_port=1080,
            username='a' * 255,
            password='b' * 255,
        )
        assert len(fwd.username) == 255

    def test_multibyte_username_too_long(self):
        # Each emoji is 4 bytes in UTF-8; 64 emojis = 256 bytes > 255
        long_user = '\U0001f600' * 64
        with pytest.raises(ValueError, match='username must be at most 255 bytes'):
            SOCKS5Forwarder(
                remote_host='host',
                remote_port=1080,
                username=long_user,
                password='pass',
            )


# ---------------------------------------------------------------------------
# SOCKS5Forwarder.start — non-loopback warning
# ---------------------------------------------------------------------------


class TestNonLoopbackWarning:
    @pytest.mark.asyncio
    async def test_loopback_no_warning(self, forwarder, caplog):
        mock_server = AsyncMock()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ('127.0.0.1', 9999)
        mock_server.sockets = [mock_sock]

        with patch('asyncio.start_server', return_value=mock_server):
            with caplog.at_level(logging.WARNING):
                await forwarder.start()
            assert 'non-loopback' not in caplog.text

    @pytest.mark.asyncio
    async def test_non_loopback_warns(self, caplog):
        fwd = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='user',
            password='pass',
            local_host='0.0.0.0',
        )
        mock_server = AsyncMock()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ('0.0.0.0', 9999)
        mock_server.sockets = [mock_sock]

        with patch('asyncio.start_server', return_value=mock_server):
            with caplog.at_level(logging.WARNING):
                await fwd.start()
            assert 'non-loopback' in caplog.text
            assert '0.0.0.0' in caplog.text

    @pytest.mark.asyncio
    async def test_ipv6_non_loopback_warns(self, caplog):
        fwd = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='user',
            password='pass',
            local_host='::',
        )
        mock_server = AsyncMock()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ('::', 9999)
        mock_server.sockets = [mock_sock]

        with patch('asyncio.start_server', return_value=mock_server):
            with caplog.at_level(logging.WARNING):
                await fwd.start()
            assert 'non-loopback' in caplog.text

    @pytest.mark.asyncio
    async def test_hostname_does_not_crash(self, caplog):
        """local_host='localhost' should not raise ValueError from ip_address()."""
        fwd = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='user',
            password='pass',
            local_host='localhost',
        )
        mock_server = AsyncMock()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ('127.0.0.1', 9999)
        mock_server.sockets = [mock_sock]

        with patch('asyncio.start_server', return_value=mock_server):
            with caplog.at_level(logging.WARNING):
                await fwd.start()
            assert 'non-loopback' not in caplog.text

    @pytest.mark.asyncio
    async def test_non_localhost_hostname_logs_debug(self, caplog):
        """A non-'localhost' hostname triggers a debug-level message."""
        fwd = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='user',
            password='pass',
            local_host='myhost.local',
        )
        mock_server = AsyncMock()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ('192.168.1.5', 9999)
        mock_server.sockets = [mock_sock]

        with patch('asyncio.start_server', return_value=mock_server):
            with caplog.at_level(logging.DEBUG):
                await fwd.start()
            assert 'not an IP literal' in caplog.text

    @pytest.mark.asyncio
    async def test_multi_socket_divergent_ports_raises(self, forwarder):
        """start() raises RuntimeError if sockets have different ports."""
        mock_server = AsyncMock()
        sock1 = MagicMock()
        sock1.getsockname.return_value = ('127.0.0.1', 9998)
        sock2 = MagicMock()
        sock2.getsockname.return_value = ('::1', 9999)
        mock_server.sockets = [sock1, sock2]
        mock_server.close = MagicMock()
        mock_server.wait_closed = AsyncMock()

        with patch('asyncio.start_server', return_value=mock_server):
            with pytest.raises(RuntimeError, match='different ports'):
                await forwarder.start()

    @pytest.mark.asyncio
    async def test_multi_socket_same_port_ok(self, forwarder):
        """start() succeeds when all sockets share the same port."""
        mock_server = AsyncMock()
        sock1 = MagicMock()
        sock1.getsockname.return_value = ('127.0.0.1', 9999)
        sock2 = MagicMock()
        sock2.getsockname.return_value = ('::1', 9999)
        mock_server.sockets = [sock1, sock2]

        with patch('asyncio.start_server', return_value=mock_server):
            await forwarder.start()
        assert forwarder.local_port == 9999


# ---------------------------------------------------------------------------
# Credential masking in logs
# ---------------------------------------------------------------------------


class TestCredentialMasking:
    @pytest.mark.asyncio
    async def test_remote_handshake_does_not_log_credentials(self, forwarder, caplog):
        """Verify that _remote_handshake logs ulen/plen instead of raw hex."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        # method selection: server picks username/password auth
        method_resp = bytes([0x05, 0x02])
        # auth response: success
        auth_resp = bytes([0x01, 0x00])
        # connect reply: success + IPv4
        connect_reply = bytes([0x05, 0x00, 0x00, 0x01])
        # BND.ADDR (IPv4) + BND.PORT
        bnd_addr = b'\x00\x00\x00\x00'
        bnd_port = b'\x00\x00'

        call_count = 0
        responses = [method_resp, auth_resp, connect_reply, bnd_addr, bnd_port]

        async def fake_readexactly(n):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        reader.readexactly = fake_readexactly

        with caplog.at_level(logging.DEBUG):
            await forwarder._remote_handshake(
                reader, writer, bytes([0x01, 127, 0, 0, 1]), 80
            )

        log_text = caplog.text
        # The raw username/password should NOT appear in hex form
        username_hex = forwarder.username.encode().hex()
        password_hex = forwarder.password.encode().hex()
        assert username_hex not in log_text or 'ulen=' in log_text
        # But we should see the safe format
        assert 'ulen=4 plen=4' in log_text

    @pytest.mark.asyncio
    async def test_remote_connect_failure_propagates_rep_code(self, forwarder):
        """Remote proxy CONNECT failure REP code is forwarded to _HandshakeError."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        # method selection: no-auth
        method_resp = bytes([0x05, 0x00])
        # connect reply: 0x05 = connection refused
        connect_reply = bytes([0x05, 0x05, 0x00, 0x01])

        call_count = 0
        responses = [method_resp, connect_reply]

        async def fake_readexactly(n):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        reader.readexactly = fake_readexactly
        reader.read = AsyncMock(return_value=b'')

        with pytest.raises(_HandshakeError) as exc_info:
            await forwarder._remote_handshake(
                reader, writer, bytes([0x01, 127, 0, 0, 1]), 80
            )

        assert exc_info.value.reply_code == REPLY_CONNECTION_REFUSED
        assert 'rep=0x05' in str(exc_info.value)


# ---------------------------------------------------------------------------
# _handle_client — reply code routing
# ---------------------------------------------------------------------------


class TestHandleClientReplyCodes:
    @pytest.mark.asyncio
    async def test_handshake_error_uses_exc_reply_code(self, forwarder):
        """_HandshakeError.reply_code flows to _send_reply."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            side_effect=_HandshakeError('bad cmd', reply_code=REPLY_COMMAND_NOT_SUPPORTED),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock) as mock_reply:
            await forwarder._handle_client(client_reader, client_writer)
            mock_reply.assert_awaited_once_with(client_writer, REPLY_COMMAND_NOT_SUPPORTED)

    @pytest.mark.asyncio
    async def test_connection_refused_uses_specific_code(self, forwarder):
        """ConnectionRefusedError -> REPLY_CONNECTION_REFUSED."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            return_value=(b'\x01\x7f\x00\x00\x01', 80),
        ), patch(
            'asyncio.open_connection',
            side_effect=ConnectionRefusedError('refused'),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock) as mock_reply:
            await forwarder._handle_client(client_reader, client_writer)
            mock_reply.assert_awaited_once_with(
                client_writer, REPLY_CONNECTION_REFUSED
            )

    @pytest.mark.asyncio
    async def test_generic_os_error_uses_general_failure(self, forwarder):
        """Non-ConnectionRefused OSError -> REPLY_GENERAL_FAILURE."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            return_value=(b'\x01\x7f\x00\x00\x01', 80),
        ), patch(
            'asyncio.open_connection',
            side_effect=OSError('network unreachable'),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock) as mock_reply:
            await forwarder._handle_client(client_reader, client_writer)
            mock_reply.assert_awaited_once_with(client_writer, REPLY_GENERAL_FAILURE)

    @pytest.mark.asyncio
    async def test_open_connection_timeout_sends_general_failure(self, forwarder):
        """asyncio.TimeoutError from open_connection -> REPLY_GENERAL_FAILURE."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            return_value=(b'\x01\x7f\x00\x00\x01', 80),
        ), patch(
            'asyncio.open_connection',
            new_callable=AsyncMock,
        ), patch(
            'asyncio.wait_for',
            side_effect=asyncio.TimeoutError(),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock) as mock_reply:
            await forwarder._handle_client(client_reader, client_writer)
            mock_reply.assert_awaited_once_with(client_writer, REPLY_GENERAL_FAILURE)

    @pytest.mark.asyncio
    async def test_send_reply_false_skips_reply(self, forwarder):
        """_HandshakeError with send_reply=False should not call _send_reply."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            side_effect=_HandshakeError('no auth', send_reply=False),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock) as mock_reply:
            await forwarder._handle_client(client_reader, client_writer)
            mock_reply.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_client_closes_both_writers(self, forwarder):
        """Both client and remote writers are closed in the finally block."""
        client_reader = AsyncMock(spec=asyncio.StreamReader)
        client_writer = MagicMock(spec=asyncio.StreamWriter)
        client_writer.write = MagicMock()
        client_writer.drain = AsyncMock()
        client_writer.close = MagicMock()
        client_writer.wait_closed = AsyncMock()

        remote_writer = MagicMock(spec=asyncio.StreamWriter)
        remote_writer.write = MagicMock()
        remote_writer.drain = AsyncMock()
        remote_writer.close = MagicMock()
        remote_writer.wait_closed = AsyncMock()

        remote_reader = AsyncMock(spec=asyncio.StreamReader)

        with patch.object(
            forwarder,
            '_accept_local_handshake',
            return_value=(b'\x01\x7f\x00\x00\x01', 80),
        ), patch(
            'asyncio.open_connection',
            return_value=(remote_reader, remote_writer),
        ), patch.object(
            forwarder,
            '_remote_handshake',
            side_effect=_HandshakeError('fail'),
        ), patch.object(forwarder, '_send_reply', new_callable=AsyncMock):
            await forwarder._handle_client(client_reader, client_writer)

        client_writer.close.assert_called_once()
        client_writer.wait_closed.assert_awaited_once()
        remote_writer.close.assert_called_once()
        remote_writer.wait_closed.assert_awaited_once()


# ---------------------------------------------------------------------------
# SOCKS5Forwarder._send_reply
# ---------------------------------------------------------------------------


class TestSendReply:
    @pytest.mark.asyncio
    async def test_sends_correct_reply(self, mock_writer):
        await SOCKS5Forwarder._send_reply(mock_writer, REPLY_SUCCESS)
        written = mock_writer.write.call_args[0][0]
        assert written[0] == 0x05  # SOCKS5
        assert written[1] == REPLY_SUCCESS
        mock_writer.drain.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sends_failure_reply(self, mock_writer):
        await SOCKS5Forwarder._send_reply(mock_writer, REPLY_CONNECTION_REFUSED)
        written = mock_writer.write.call_args[0][0]
        assert written[1] == REPLY_CONNECTION_REFUSED


# ---------------------------------------------------------------------------
# _accept_local_handshake — pre-CONNECT send_reply=False and reply codes
# ---------------------------------------------------------------------------


class TestAcceptLocalHandshake:
    @pytest.mark.asyncio
    async def test_greeting_eof_has_send_reply_false(self, forwarder):
        """If _read_exact fails during greeting, send_reply must be False."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        reader.readexactly = AsyncMock(
            side_effect=asyncio.IncompleteReadError(partial=b'', expected=2)
        )

        with pytest.raises(_HandshakeError) as exc_info:
            await forwarder._accept_local_handshake(reader, writer)
        assert exc_info.value.send_reply is False

    @pytest.mark.asyncio
    async def test_unsupported_version_has_send_reply_false(self, forwarder):
        """Bad SOCKS version in greeting → send_reply=False."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        reader.readexactly = AsyncMock(return_value=bytes([0x04, 0x01]))

        with pytest.raises(_HandshakeError, match='Unsupported SOCKS version') as exc_info:
            await forwarder._accept_local_handshake(reader, writer)
        assert exc_info.value.send_reply is False

    @pytest.mark.asyncio
    async def test_unsupported_command_uses_reply_code_0x07(self, forwarder):
        """CMD != CONNECT → REPLY_COMMAND_NOT_SUPPORTED."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        call_count = 0
        responses = [
            bytes([0x05, 0x01]),  # VER, NMETHODS
            bytes([0x00]),  # method: no-auth
            bytes([0x05, 0x02, 0x00, 0x01]),  # VER, CMD=BIND(0x02), RSV, ATYP
        ]

        async def fake_readexactly(n):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        reader.readexactly = fake_readexactly

        with pytest.raises(_HandshakeError) as exc_info:
            await forwarder._accept_local_handshake(reader, writer)
        assert exc_info.value.reply_code == REPLY_COMMAND_NOT_SUPPORTED

    @pytest.mark.asyncio
    async def test_unsupported_address_type_uses_reply_code_0x08(self, forwarder):
        """Unknown ATYP → REPLY_ADDRESS_TYPE_NOT_SUPPORTED."""
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = MagicMock(spec=asyncio.StreamWriter)
        writer.write = MagicMock()
        writer.drain = AsyncMock()

        call_count = 0
        responses = [
            bytes([0x05, 0x01]),  # VER, NMETHODS
            bytes([0x00]),  # method: no-auth
            bytes([0x05, 0x01, 0x00, 0xFF]),  # VER, CMD=CONNECT, RSV, ATYP=0xFF (unknown)
        ]

        async def fake_readexactly(n):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        reader.readexactly = fake_readexactly

        with pytest.raises(_HandshakeError) as exc_info:
            await forwarder._accept_local_handshake(reader, writer)
        assert exc_info.value.reply_code == REPLY_ADDRESS_TYPE_NOT_SUPPORTED


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_handshake_timeout_is_positive(self):
        assert HANDSHAKE_TIMEOUT > 0

    def test_reply_codes_are_distinct(self):
        codes = {
            REPLY_SUCCESS,
            REPLY_GENERAL_FAILURE,
            REPLY_CONNECTION_REFUSED,
            REPLY_COMMAND_NOT_SUPPORTED,
            REPLY_ADDRESS_TYPE_NOT_SUPPORTED,
        }
        assert len(codes) == 5
