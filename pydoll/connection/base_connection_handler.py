from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, cast

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from pydoll.connection.managers import CommandsManager, EventsManager
from pydoll.connection.managers.event_trackers import BaseEventTracker
from pydoll.exceptions import (
    CommandExecutionTimeout,
    WebSocketConnectionClosed,
)

if TYPE_CHECKING:
    from typing import Any, AsyncGenerator, Awaitable, Callable, Optional, Union

    from websockets.asyncio.client import connect as Connect

logger = logging.getLogger(__name__)


class BaseConnectionHandler(ABC):
    """
    Protocol-agnostic WebSocket connection manager.

    Handles connection lifecycle, command execution, and event subscription.
    Subclasses implement protocol-specific URL resolution, message parsing,
    and error extraction.
    """

    def __init__(
        self,
        connection_port: Optional[int] = None,
        page_id: Optional[str] = None,
        ws_address: Optional[str] = None,
        ws_connector: type[Connect] = websockets.connect,
    ):
        self._connection_port = connection_port
        self._page_id = page_id
        self._ws_address = ws_address
        self._ws_connector = ws_connector
        self._ws_connection: Optional[ClientConnection] = None
        self._command_manager = CommandsManager()
        self._events_handler = EventsManager()
        self._event_tracker = self._create_event_tracker()
        self._receive_task: Optional[asyncio.Task] = None
        logger.info(f'{self.__class__.__name__} initialized.')
        logger.debug(
            f'Init params: port={self._connection_port}, page_id={self._page_id}, '
            f'ws_address_set={bool(self._ws_address)}'
        )

    @abstractmethod
    def _create_event_tracker(self) -> BaseEventTracker:
        """Create protocol-specific event tracker."""

    @abstractmethod
    async def _resolve_ws_address(self) -> str:
        """Resolve WebSocket URL using protocol-specific logic."""

    @abstractmethod
    def _is_command_response(self, message: dict) -> bool:
        """Determine if a parsed message is a command response."""

    @abstractmethod
    def _extract_error(self, message: dict) -> Optional[str]:
        """Extract error information from a response, if any."""

    @property
    def network_logs(self):
        """Access captured network request and response logs."""
        return self._event_tracker.network_logs

    @property
    def dialog(self):
        """Access currently active dialog information."""
        return self._event_tracker.dialog

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
        self, command: dict, timeout: int = 60
    ) -> dict:
        """
        Send command and await response.

        Args:
            command: Command dict to send.
            timeout: Maximum seconds to wait for response.

        Returns:
            Parsed response object.

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
        Register event listener.

        Args:
            event_name: Event name to listen for.
            callback: Async function called when event occurs.
            temporary: If True, callback removed after first trigger.

        Returns:
            Callback ID for later removal.
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
        if self._ws_connection is None:
            logger.debug('Close called but no active WebSocket connection')
            return

        with suppress(websockets.ConnectionClosed):
            await self._ws_connection.close()
        logger.info('WebSocket connection closed.')

    async def _ensure_active_connection(self):
        """Ensure active connection exists, establishing new one if needed."""
        if self._ws_connection is None or self._ws_connection.state is State.CLOSED:
            logger.debug('No active WebSocket connection; establishing new one')
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
        """Parse and route a single WebSocket message."""
        message = self._parse_message(raw_message)
        if not message:
            return

        if self._is_command_response(message):
            await self._handle_command_message(message)
        else:
            await self._handle_event_message(message)

    @staticmethod
    def _parse_message(raw_message: str) -> dict | None:
        """Parse raw message string into JSON object."""
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse message: {raw_message[:200]}...')
            return None

    async def _handle_command_message(self, message: dict):
        """Process command response messages."""
        logger.debug(f'Processing command response: {message.get("id")}')
        self._command_manager.resolve_command(message['id'], json.dumps(message))

    async def _handle_event_message(self, message: dict):
        """Process event notification messages."""
        event_type = message.get('method', 'unknown-event')
        logger.debug(f'Processing {event_type} event')
        await self._event_tracker.track(message)
        await self._events_handler.process_event(message)

    def __repr__(self):
        return f'{self.__class__.__name__}(port={self._connection_port})'

    def __str__(self):
        return f'{self.__class__.__name__}(port={self._connection_port})'

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
