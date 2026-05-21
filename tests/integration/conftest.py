"""Fixtures for integration tests that exercise real I/O (sockets, browser)."""

from __future__ import annotations

import json
from typing import Optional

import pytest_asyncio
import websockets
from websockets.asyncio.server import Server, ServerConnection, serve


class FakeCDPServer:
    """A real WebSocket server that speaks just enough CDP for tests.

    The production ConnectionHandler connects to it over a real socket, so
    tests exercise real framing, send/recv, close handshakes and the receive
    task instead of a mocked connection. Every command frame receives a
    well-formed response; events can be pushed and connections dropped on
    demand to drive the reconnection and failure paths.
    """

    def __init__(self) -> None:
        self._server: Optional[Server] = None
        self._connections: set[ServerConnection] = set()
        self._received: list[dict] = []
        self._results: dict[str, dict] = {}
        self._hung_methods: set[str] = set()

    async def start(self) -> None:
        """Bind the server to an ephemeral localhost port."""
        self._server = await serve(self._handle_client, 'localhost', 0)

    async def stop(self) -> None:
        """Close the server and wait for it to release the port."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    @property
    def port(self) -> int:
        """The ephemeral port the server is listening on."""
        return list(self._server.sockets)[0].getsockname()[1]

    @property
    def ws_address(self) -> str:
        """WebSocket address to hand to ConnectionHandler(ws_address=...)."""
        return f'ws://localhost:{self.port}'

    @property
    def received_commands(self) -> list[dict]:
        """Every command frame received, in arrival order."""
        return list(self._received)

    @property
    def active_connections(self) -> int:
        """Number of currently open client connections."""
        return len(self._connections)

    def set_result(self, method: str, result: dict) -> None:
        """Configure the result payload returned for a command method."""
        self._results[method] = result

    def hang(self, method: str) -> None:
        """Receive a command method but never answer it, to test timeouts/drops."""
        self._hung_methods.add(method)

    async def push_event(self, method: str, params: Optional[dict] = None) -> None:
        """Send an unsolicited CDP event to every connected client."""
        await self._broadcast(json.dumps({'method': method, 'params': params or {}}))

    async def send_raw(self, payload: str) -> None:
        """Send an arbitrary, possibly malformed, frame to every client."""
        await self._broadcast(payload)

    async def drop_connections(self) -> None:
        """Close every active client connection from the server side."""
        for connection in list(self._connections):
            await connection.close()

    async def _broadcast(self, payload: str) -> None:
        for connection in list(self._connections):
            await connection.send(payload)

    async def _handle_client(self, connection: ServerConnection) -> None:
        self._connections.add(connection)
        try:
            async for raw in connection:
                await self._respond(connection, raw)
        except websockets.ConnectionClosed:
            pass
        finally:
            self._connections.discard(connection)

    async def _respond(self, connection: ServerConnection, raw: str) -> None:
        message = json.loads(raw)
        self._received.append(message)
        if message.get('method') in self._hung_methods:
            return
        result = self._results.get(message.get('method'), {})
        await connection.send(json.dumps({'id': message['id'], 'result': result}))


@pytest_asyncio.fixture
async def cdp_server():
    """Start a FakeCDPServer on an ephemeral port and tear it down afterwards."""
    server = FakeCDPServer()
    await server.start()
    try:
        yield server
    finally:
        await server.stop()
