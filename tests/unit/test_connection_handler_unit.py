"""Unit tests for ConnectionHandler internals.

These exercise the private address-parsing and URL-building logic directly,
without any network I/O.
"""

from __future__ import annotations

import pytest

from pydoll.connection import ConnectionHandler
from pydoll.exceptions import InvalidWebSocketAddress


class TestUseWsAddress:
    """Tests for ConnectionHandler._use_ws_address."""

    def test_sets_port_from_explicit_url_port(self):
        handler = ConnectionHandler()
        handler._use_ws_address('ws://host:9223')
        assert handler._connection_port == 9223

    def test_with_port_zero_does_not_default_to_80(self):
        handler = ConnectionHandler()
        handler._use_ws_address('ws://host:0')
        assert handler._connection_port == 0

    def test_wss_no_port_defaults_to_443(self):
        handler = ConnectionHandler()
        handler._use_ws_address('wss://host')
        assert handler._connection_port == 443

    def test_ws_no_port_defaults_to_80(self):
        handler = ConnectionHandler()
        handler._use_ws_address('ws://host')
        assert handler._connection_port == 80

    def test_raises_on_no_hostname(self):
        handler = ConnectionHandler()
        with pytest.raises(InvalidWebSocketAddress):
            handler._use_ws_address('ws://')

    def test_raises_on_invalid_scheme(self):
        handler = ConnectionHandler()
        with pytest.raises(InvalidWebSocketAddress):
            handler._use_ws_address('http://host')


class TestResolveWsAddress:
    """Tests for ConnectionHandler._resolve_ws_address."""

    @pytest.mark.asyncio
    async def test_ipv6_host_gets_brackets(self):
        handler = ConnectionHandler(
            connection_host='::1', connection_port=9223, page_id='abc'
        )
        address = await handler._resolve_ws_address()
        assert address == 'ws://[::1]:9223/devtools/page/abc'

    @pytest.mark.asyncio
    async def test_ipv6_host_gets_brackets_secure(self):
        handler = ConnectionHandler(
            connection_host='::1', connection_port=9223, page_id='abc', use_secure=True
        )
        address = await handler._resolve_ws_address()
        assert address == 'wss://[::1]:9223/devtools/page/abc'

    @pytest.mark.asyncio
    async def test_regular_hostname_no_brackets(self):
        handler = ConnectionHandler(
            connection_host='localhost', connection_port=9223, page_id='abc'
        )
        address = await handler._resolve_ws_address()
        assert address == 'ws://localhost:9223/devtools/page/abc'

    @pytest.mark.asyncio
    async def test_regular_hostname_no_brackets_secure(self):
        handler = ConnectionHandler(
            connection_host='localhost', connection_port=9223, page_id='abc', use_secure=True
        )
        address = await handler._resolve_ws_address()
        assert address == 'wss://localhost:9223/devtools/page/abc'

    @pytest.mark.asyncio
    async def test_resolve_no_page_id_calls_resolver(self):
        async def fake_resolver(params):
            scheme = 'wss' if params["use_secure"] else 'ws'
            return f'{scheme}://{params["host"]}:{params["port"]}/devtools/browser/fake-resolved'

        handler = ConnectionHandler(
            connection_host='myhost',
            connection_port=9999,
            ws_address_resolver=fake_resolver,
            use_secure=True
        )
        address = await handler._resolve_ws_address()
        assert address == 'wss://myhost:9999/devtools/browser/fake-resolved'


class TestGetWsScheme:
    """Tests for ConnectionHandler._get_ws_scheme."""

    def test_use_secure_true_returns_wss(self):
        handler = ConnectionHandler(use_secure=True)
        assert handler._get_ws_scheme() == 'wss'

    def test_use_secure_false_returns_ws(self):
        handler = ConnectionHandler(use_secure=False)
        assert handler._get_ws_scheme() == 'ws'

    def test_use_secure_default_returns_ws(self):
        handler = ConnectionHandler()
        assert handler._get_ws_scheme() == 'ws'

    def test_ws_address_scheme_used_over_use_secure(self):
        handler = ConnectionHandler(ws_address='wss://host:9222', use_secure=False)
        assert handler._get_ws_scheme() == 'wss'

    def test_ws_address_ws_scheme(self):
        handler = ConnectionHandler(ws_address='ws://host:9222', use_secure=True)
        assert handler._get_ws_scheme() == 'ws'
