from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from pydoll.connection.managers import CommandsManager, EventsManager
from pydoll.exceptions import (
    CommandExecutionTimeout,
    WebSocketConnectionClosed,
)
from pydoll.protocol.base import CDPEvent, Response
from pydoll.utils import get_browser_ws_address

if TYPE_CHECKING:
    from typing import Any, AsyncGenerator, Awaitable, Callable, Coroutine, Optional, Union

    from websockets.asyncio.client import connect as Connect

    from pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse

logger = logging.getLogger(__name__)


class ConnectionHandler:
    """
    WebSocket connection manager for Chrome DevTools Protocol endpoints.

    Handles connection lifecycle, command execution, and event subscription
    for both browser-level and page-level CDP endpoints.
    """

    def __init__(
        self,
        connection_port: Optional[int] = None,
        page_id: Optional[str] = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
        ws_address: Optional[str] = None,
    ):
        """
        Initialize connection handler.

        Args:
            connection_port: Browser's debugging server port.
            page_id: Target page ID. If None, connects to browser-level endpoint.
            ws_address_resolver: Function to resolve WebSocket URL from port.
            ws_connector: WebSocket connection factory (mainly for testing).
            ws_address: WebSocket address. It has priority over connection_port and page_id.
        """
        self._connection_port = connection_port
        self._page_id = page_id
        self._ws_address_resolver = ws_address_resolver
        self._ws_connector = ws_connector
        self._ws_address = ws_address
        self._ws_connection: Optional[ClientConnection] = None
        self._command_manager = CommandsManager()
        self._events_handler = EventsManager()
        self._receive_task: Optional[asyncio.Task] = None
        self._connection_lock = asyncio.Lock()
        logger.info('ConnectionHandler initialized.')
        logger.debug(
            f'Init params: port={self._connection_port}, page_id={self._page_id}, '
            f'ws_address_set={bool(self._ws_address)}'
        )

    @property
    def network_logs(self):
        """Access captured network request and response logs."""
        return list(self._events_handler.network_logs)

    @property
    def dialog(self):
        """Access currently active JavaScript dialog information."""
        return self._events_handler.dialog

    async def ping(self) -> bool:
        """Test if WebSocket connection is active and responsive."""
        with suppress(Exception):
            logger.debug('Pinging WebSocket connection')
            await self._ensure_active_connection()
            await cast(ClientConnection, self._ws_connection).ping()
            logger.debug('Ping OK')
            return True
        return False

    async def execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse], timeout: int = 60
    ) -> T_CommandResponse:
        """
        Send CDP command and await response.

        Args:
            command: CDP command to send.
            timeout: Maximum seconds to wait for response.

        Returns:
            Parsed response object matching command's expected type.

        Raises:
            CommandExecutionTimeout: If browser doesn't respond within timeout.
            WebSocketConnectionClosed: If connection closes during execution.
        """
        await self._ensure_active_connection()
        future = self._command_manager.create_command_future(command)
        command_str = json.dumps(command)

        try:
            ws = cast(ClientConnection, self._ws_connection)
            logger.debug(
                f'Sending command: id={command.get("id")}, method={command.get("method")}, '
                f'timeout={timeout}s'
            )
            start = asyncio.get_event_loop().time()
            await ws.send(command_str)
            response: str = await asyncio.wait_for(future, timeout)
            elapsed = asyncio.get_event_loop().time() - start
            logger.debug(f'Command completed: id={command.get("id")} in {elapsed:.3f}s')
            return json.loads(response)
        except asyncio.TimeoutError:
            self._command_manager.remove_pending_command(command['id'])
            logger.error(
                f'Command timeout: id={command.get("id")}, method={command.get("method")}, '
                f'timeout={timeout}s'
            )
            raise CommandExecutionTimeout()
        except websockets.ConnectionClosed:
            self._command_manager.remove_pending_command(command['id'])
            await self._handle_connection_loss()
            logger.warning(f'WebSocket connection closed during command: id={command.get("id")}')
            raise WebSocketConnectionClosed()

    async def register_callback(
        self,
        event_name: str,
        callback: Callable[[dict], Awaitable[None]],
        temporary: bool = False,
    ) -> int:
        """
        Register event listener for CDP events.

        Args:
            event_name: CDP event name (e.g., 'Page.loadEventFired').
            callback: Async function called when event occurs.
            temporary: If True, callback removed after first trigger.

        Returns:
            Callback ID for later removal.

        Note:
            Corresponding CDP domain must be enabled before events fire.
        """
        callback_id = self._events_handler.register_callback(event_name, callback, temporary)
        logger.debug(
            f'Registered callback: id={callback_id}, event={event_name}, temporary={temporary}'
        )
        return callback_id

    async def remove_callback(self, callback_id: int) -> bool:
        """Remove registered event callback by ID."""
        removed = self._events_handler.remove_callback(callback_id)
        logger.debug(f'Removed callback: id={callback_id}, removed={removed}')
        return removed

    async def clear_callbacks(self):
        """Remove all registered event callbacks."""
        logger.debug('Clearing all callbacks')
        self._events_handler.clear_callbacks()

    async def close(self):
        """Close WebSocket connection and release resources."""
        await self.clear_callbacks()
        await self._events_handler.stop()

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await self._receive_task

        if self._ws_connection is not None:
            with suppress(websockets.ConnectionClosed, Exception):
                await self._ws_connection.close()
        logger.info('WebSocket connection closed.')

    def _is_connection_healthy(self) -> bool:
        """Return True only if the socket is open AND a live reader task is draining it.

        A socket that is still open but whose receive task has died (e.g. an
        oversized frame or a malformed event killed the loop) is NOT healthy:
        nothing would deliver responses, so commands would silently time out.
        """
        return (
            self._ws_connection is not None
            and self._ws_connection.state is State.OPEN
            and self._receive_task is not None
            and not self._receive_task.done()
        )

    async def _ensure_active_connection(self):
        """Ensure a healthy connection exists, establishing a new one if needed."""
        if self._is_connection_healthy():
            return
        async with self._connection_lock:
            if not self._is_connection_healthy():
                logger.debug('No healthy WebSocket connection; establishing new one')
                await self._establish_new_connection()

    async def _establish_new_connection(self):
        """Create fresh WebSocket connection and start event listening."""
        await self._teardown_connection()
        ws_address = await self._resolve_ws_address()
        logger.info(f'Connecting to {ws_address}')
        self._ws_connection = await self._ws_connector(
            ws_address,
            max_size=None,
        )
        self._events_handler.start()
        self._receive_task = asyncio.create_task(self._receive_events())
        logger.debug('WebSocket connection established')

    async def _teardown_connection(self):
        """Cancel the receive task and close any existing socket before reconnecting."""
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await self._receive_task
        self._receive_task = None

        if self._ws_connection is not None and self._ws_connection.state is not State.CLOSED:
            with suppress(Exception):
                await self._ws_connection.close()
        self._ws_connection = None

    async def _resolve_ws_address(self):
        """Determine correct WebSocket address based on page ID."""
        if self._ws_address:
            logger.debug('Using provided WebSocket address')
            return self._ws_address
        if not self._page_id:
            resolved = await self._ws_address_resolver(self._connection_port)
            logger.debug(f'Resolved browser-level WebSocket address: {resolved}')
            return resolved
        address = f'ws://localhost:{self._connection_port}/devtools/page/{self._page_id}'
        logger.debug(f'Resolved page-level WebSocket address: {address}')
        return address

    async def _handle_connection_loss(self):
        """Fail in-flight commands and clean up resources after connection loss."""
        self._command_manager.fail_all_pending(WebSocketConnectionClosed())
        await self._teardown_connection()
        logger.info('Connection resources cleaned up')

    async def _receive_events(self):
        """Main loop for receiving and processing WebSocket messages.

        A single unparseable/malformed message is logged and skipped so it can
        never kill the reader. When the loop exits for any reason, all in-flight
        commands are failed so callers raise immediately instead of hanging
        until their timeout expires on a connection nobody is reading.
        """
        try:
            async for raw_message in self._incoming_messages():
                try:
                    self._process_single_message(raw_message)
                except Exception:
                    logger.exception('Error processing WebSocket message; skipping')
        except websockets.ConnectionClosed as e:
            logger.info(f'WebSocket connection closed: {e}')
        except Exception:
            logger.exception('Fatal error in WebSocket receive loop')
        finally:
            self._command_manager.fail_all_pending(WebSocketConnectionClosed())
            await self._events_handler.stop()

    async def _incoming_messages(self) -> AsyncGenerator[Union[str, bytes], None]:
        """Generator yielding raw messages from WebSocket connection."""
        ws = cast(ClientConnection, self._ws_connection)

        while ws.state is not State.CLOSED:
            yield await ws.recv()

    def _process_single_message(self, raw_message: str):
        """Route a single raw WebSocket message.

        Command responses are resolved inline (fast, synchronous) so they are
        never delayed by event processing; events are handed to the
        EventsManager queue for ordered, non-blocking handling.
        """
        message = self._parse_message(raw_message)
        if not message:
            return

        if self._is_command_response(message):
            self._handle_command_message(cast(Response, message))
        else:
            self._events_handler.enqueue_event(cast(CDPEvent, message))

    @staticmethod
    def _parse_message(raw_message: str) -> Union[CDPEvent, Response, None]:
        """Parse raw message string into JSON object."""
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse message: {raw_message[:200]}...')
            return None

    @staticmethod
    def _is_command_response(message: Union[CDPEvent, Response]) -> bool:
        """Determine if message is command response or event notification."""
        return 'id' in message and isinstance(message.get('id'), int)

    def _handle_command_message(self, message: Response):
        """Resolve the pending future for a command response."""
        logger.debug(f'Processing command response: {message.get("id")}')
        self._command_manager.resolve_command(message['id'], json.dumps(message))

    def __repr__(self):
        """String representation for debugging."""
        return f'ConnectionHandler(port={self._connection_port})'

    def __str__(self):
        """User-friendly string representation."""
        return f'ConnectionHandler(port={self._connection_port})'

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()
