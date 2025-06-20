import asyncio
import json
import logging
from contextlib import suppress
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Coroutine,
    Optional,
    TypeVar,
    Union,
    cast,
)

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect as Connect
from websockets.protocol import State

from pydoll.connection.managers import CommandsManager, EventsManager
from pydoll.exceptions import (
    CommandExecutionTimeout,
    WebSocketConnectionClosed,
)
from pydoll.protocol.base import Command, Event, Response
from pydoll.utils import get_browser_ws_address

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar('T')


class ConnectionHandler:
    """
    WebSocket connection manager for Chrome DevTools Protocol endpoints.

    Handles connection lifecycle, command execution, and event subscription
    for both browser-level and page-level CDP endpoints.
    """

    def __init__(
        self,
        connection_port: int,
        page_id: Optional[str] = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
    ):
        """
        Initialize connection handler.

        Args:
            connection_port: Browser's debugging server port.
            page_id: Target page ID. If None, connects to browser-level endpoint.
            ws_address_resolver: Function to resolve WebSocket URL from port.
            ws_connector: WebSocket connection factory (mainly for testing).
        """
        self._connection_port = connection_port
        self._page_id = page_id
        self._ws_address_resolver = ws_address_resolver
        self._ws_connector = ws_connector
        self._ws_connection: Optional[ClientConnection] = None
        self._command_manager = CommandsManager()
        self._events_handler = EventsManager()
        self._receive_task: Optional[asyncio.Task] = None
        logger.info('ConnectionHandler initialized.')

    @property
    def network_logs(self):
        """Access captured network request and response logs."""
        return self._events_handler.network_logs

    @property
    def dialog(self):
        """Access currently active JavaScript dialog information."""
        return self._events_handler.dialog

    async def ping(self) -> bool:
        """Test if WebSocket connection is active and responsive."""
        with suppress(Exception):
            await self._ensure_active_connection()
            await cast(ClientConnection, self._ws_connection).ping()
            return True
        return False

    async def execute_command(self, command: Command[T], timeout: int = 10) -> T:
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
            await ws.send(command_str)
            response: str = await asyncio.wait_for(future, timeout)
            return json.loads(response)
        except asyncio.TimeoutError:
            self._command_manager.remove_pending_command(command['id'])
            raise CommandExecutionTimeout()
        except websockets.ConnectionClosed:
            await self._handle_connection_loss()
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
        return self._events_handler.register_callback(event_name, callback, temporary)

    async def remove_callback(self, callback_id: int) -> bool:
        """Remove registered event callback by ID."""
        return self._events_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """Remove all registered event callbacks."""
        self._events_handler.clear_callbacks()

    async def close(self):
        """Close WebSocket connection and release resources."""
        await self.clear_callbacks()
        if self._ws_connection is None:
            return

        with suppress(websockets.ConnectionClosed):
            await self._ws_connection.close()
        logger.info('WebSocket connection closed.')

    async def _ensure_active_connection(self):
        """Ensure active connection exists, establishing new one if needed."""
        if self._ws_connection is None or self._ws_connection.state is State.CLOSED:
            await self._establish_new_connection()

    async def _establish_new_connection(self):
        """Create fresh WebSocket connection and start event listening."""
        ws_address = await self._resolve_ws_address()
        logger.info(f'Connecting to {ws_address}')
        self._ws_connection = await self._ws_connector(
            ws_address,
            max_size=1024 * 1024 * 10,  # 10MB
        )
        self._receive_task = asyncio.create_task(self._receive_events())
        logger.debug('WebSocket connection established')

    async def _resolve_ws_address(self):
        """Determine correct WebSocket address based on page ID."""
        if not self._page_id:
            return await self._ws_address_resolver(self._connection_port)
        return f'ws://localhost:{self._connection_port}/devtools/page/{self._page_id}'

    async def _handle_connection_loss(self):
        """Clean up resources after connection loss."""
        if self._ws_connection and self._ws_connection.state is not State.CLOSED:
            await self._ws_connection.close()
        self._ws_connection = None

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        logger.info('Connection resources cleaned up')

    async def _receive_events(self):
        """Main loop for receiving and processing WebSocket messages."""
        try:
            async for raw_message in self._incoming_messages():
                await self._process_single_message(raw_message)
        except websockets.ConnectionClosed as e:
            logger.info(f'Connection closed gracefully: {e}')
        except Exception as e:
            logger.error(f'Unexpected error in event loop: {e}')
            raise

    async def _incoming_messages(self) -> AsyncGenerator[Union[str, bytes], None]:
        """Generator yielding raw messages from WebSocket connection."""
        ws = cast(ClientConnection, self._ws_connection)

        while ws.state is not State.CLOSED:
            yield await ws.recv()

    async def _process_single_message(self, raw_message: str):
        """Process single raw WebSocket message."""
        message = self._parse_message(raw_message)
        if not message:
            return

        if self._is_command_response(message):
            message = cast(Response, message)
            await self._handle_command_message(message)
        else:
            message = cast(Event, message)
            await self._handle_event_message(message)

    @staticmethod
    def _parse_message(raw_message: str) -> Union[Event, Response, None]:
        """Parse raw message string into JSON object."""
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse message: {raw_message[:200]}...')
            return None

    @staticmethod
    def _is_command_response(message: Union[Event, Response]) -> bool:
        """Determine if message is command response or event notification."""
        return 'id' in message and isinstance(message.get('id'), int)

    async def _handle_command_message(self, message: Response):
        """Process command response messages."""
        logger.debug(f'Processing command response: {message.get("id")}')
        self._command_manager.resolve_command(message['id'], json.dumps(message))

    async def _handle_event_message(self, message: Event):
        """Process event notification messages."""
        event_type = message.get('method', 'unknown-event')
        logger.debug(f'Processing {event_type} event')
        await self._events_handler.process_event(message)

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
