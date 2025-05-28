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
    Dict,
    Optional,
    TypeVar,
    Union,
    cast,
)

import websockets
from websockets.legacy.client import Connect, WebSocketClientProtocol

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
    Manages WebSocket connections to Chrome DevTools Protocol endpoints.

    This class establishes and maintains WebSocket connections to either browser-level
    or page-level CDP endpoints, providing a reliable communication channel for sending
    commands and receiving events and responses. It handles connection lifecycle,
    message routing, and event subscription.

    Key responsibilities:
    1. Establishing and maintaining WebSocket connections
    2. Sending CDP commands and handling responses
    3. Managing event subscriptions and callbacks
    4. Processing incoming messages (both command responses and events)
    5. Handling connection interruptions and reconnection

    This is a core component of the automation framework, acting as the communication
    layer between Python code and the browser's DevTools Protocol.
    """

    def __init__(
        self,
        connection_port: int,
        page_id: Optional[str] = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
    ):
        """
        Initializes a new ConnectionHandler instance.

        Creates a handler that will establish and manage a WebSocket connection
        to either a browser-level CDP endpoint or a specific page's CDP endpoint.
        The connection is not established until needed (lazy initialization).

        Args:
            connection_port: Port number the browser's debugging server is listening on.
                This is typically the Chrome --remote-debugging-port value.
            page_id: Target ID of the specific page to connect to.
                If None, connects to the browser-level endpoint instead.
            ws_address_resolver: Function to determine the WebSocket URL from the port.
                Default implementation queries the browser's JSON API.
            ws_connector: Factory for creating WebSocket connections.
                Primarily used for testing to inject mock connections.
        """
        self._connection_port = connection_port
        self._page_id = page_id
        self._ws_address_resolver = ws_address_resolver
        self._ws_connector = ws_connector
        self._ws_connection: Optional[WebSocketClientProtocol] = None
        self._command_manager = CommandsManager()
        self._events_handler = EventsManager()
        self._receive_task: Optional[asyncio.Task] = None
        logger.info('ConnectionHandler initialized.')

    @property
    def network_logs(self):
        """
        Access all captured network request and response logs.

        Provides access to network activity logs that have been captured during
        the browser session through Network domain events.

        Returns:
            list: Collection of network request/response log entries.
                Each entry contains details about a network request.
        """
        return self._events_handler.network_logs

    @property
    def dialog(self):
        """
        Access information about the currently active JavaScript dialog.

        Provides details about any active JavaScript dialog (alert, confirm, prompt)
        that is currently being displayed in the page.

        Returns:
            dict or None: Dialog information if a dialog is present, containing
                type (alert, confirm, prompt), message text, and other details.
                Returns None if no dialog is currently displayed.
        """
        return self._events_handler.dialog

    async def ping(self) -> bool:
        """
        Tests if the WebSocket connection is active and responsive.

        Sends a WebSocket protocol-level ping to check if the connection
        is still alive and functioning correctly.

        Returns:
            bool: True if the connection is active and responded to the ping,
                False if the connection is closed or unresponsive.
        """
        with suppress(Exception):
            await self._ensure_active_connection()
            await cast(WebSocketClientProtocol, self._ws_connection).ping()
            return True
        return False

    async def execute_command(self, command: Command[T], timeout: int = 10) -> T:
        """
        Sends a CDP command to the browser and awaits its response.

        This is the primary method for interacting with the browser via CDP.
        It serializes the command, sends it over the WebSocket, and waits
        for the corresponding response with matching ID.

        Args:
            command: CDP command object to send
            timeout: Maximum seconds to wait for the command response.
                Default is 10 seconds.

        Returns:
            T: The parsed response object from the browser, with type matching
                the command's expected return type.

        Raises:
            CommandExecutionTimeout: If the browser doesn't respond within the timeout period.
            WebSocketConnectionClosed: If the connection closes during command execution.
        """
        await self._ensure_active_connection()
        future = self._command_manager.create_command_future(command)
        command_str = json.dumps(command)

        try:
            ws = cast(WebSocketClientProtocol, self._ws_connection)
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
        callback: Callable[[Dict], Awaitable[None]],
        temporary: bool = False,
    ) -> int:
        """
        Registers an event listener for a specific CDP event.

        Sets up a callback function to be called whenever a specified CDP event
        occurs. This allows reacting to browser events like page loads, network
        activity, dialog appearance, etc.

        Args:
            event_name: CDP event name to listen for (e.g., 'Page.loadEventFired',
                'Network.responseReceived'). Should include both domain and event.
            callback: Async function to call when the event occurs.
                Must accept a single dict parameter containing the event data.
            temporary: If True, the callback will be automatically removed
                after being triggered once. Default is False (persistent).

        Returns:
            int: Callback ID that can be used to remove the listener later
                with remove_callback().

        Note:
            The corresponding CDP domain must be enabled before events will fire.
            For example, enable Page.enable() before listening for Page events.
        """
        return self._events_handler.register_callback(event_name, callback, temporary)

    async def remove_callback(self, callback_id: int) -> bool:
        """
        Removes a previously registered event callback.

        Unsubscribes from an event by removing the callback with the specified ID.
        Once removed, the callback will no longer be triggered by events.

        Args:
            callback_id: ID of the callback to remove, as returned by
                register_callback().

        Returns:
            bool: True if the callback was successfully removed,
                False if the callback ID was not found.
        """
        return self._events_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """
        Removes all registered event callbacks.

        Unsubscribes from all events by removing all registered callbacks.
        This is useful for cleanup when the connection is no longer needed
        or when resetting the event handling state.
        """
        self._events_handler.clear_callbacks()

    async def close(self):
        """
        Closes the WebSocket connection and releases resources.

        Performs a clean shutdown of the connection by removing all
        event callbacks and closing the WebSocket connection. After
        calling this, the ConnectionHandler should not be used until
        a new connection is established.
        """
        await self.clear_callbacks()
        if self._ws_connection is None:
            return

        with suppress(websockets.ConnectionClosed):
            await self._ws_connection.close()
        logger.info('WebSocket connection closed.')

    async def _ensure_active_connection(self):
        """
        Guarantees that an active connection exists before proceeding.

        This method checks if the WebSocket connection is established
        and active. If not, it establishes a new connection.
        """
        if self._ws_connection is None or self._ws_connection.closed:
            await self._establish_new_connection()

    async def _establish_new_connection(self):
        """
        Creates a fresh WebSocket connection and starts listening for events.

        Resolves the appropriate WebSocket address, establishes a new
        connection, and initiates an asynchronous task to receive events.
        """
        ws_address = await self._resolve_ws_address()
        logger.info(f'Connecting to {ws_address}')
        self._ws_connection = await self._ws_connector(
            ws_address,
            max_size=1024 * 1024 * 10,  # 10MB
        )
        self._receive_task = asyncio.create_task(self._receive_events())
        logger.debug('WebSocket connection established')

    async def _resolve_ws_address(self):
        """
        Determines the correct WebSocket address based on the page ID.

        For browser-level connections, queries the browser's debugging API.
        For page-level connections, constructs the URL based on the page ID.

        Returns:
            str: Complete WebSocket URL to connect to.
        """
        if not self._page_id:
            return await self._ws_address_resolver(self._connection_port)
        return f'ws://localhost:{self._connection_port}/devtools/page/{self._page_id}'

    async def _handle_connection_loss(self):
        """
        Cleans up resources after a WebSocket connection loss.

        Closes the connection if it's still open, nullifies the
        connection reference, and cancels any ongoing receive tasks.
        This prepares the handler for establishing a new connection
        on the next command.
        """
        if self._ws_connection and not self._ws_connection.closed:
            await self._ws_connection.close()
        self._ws_connection = None

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        logger.info('Connection resources cleaned up')

    async def _receive_events(self):
        """
        Main loop for receiving and processing incoming WebSocket messages.

        This long-running task continuously reads messages from the WebSocket
        and delegates processing to specialized handlers based on message type.
        It handles both command responses and event notifications.
        """
        try:
            async for raw_message in self._incoming_messages():
                await self._process_single_message(raw_message)
        except websockets.ConnectionClosed as e:
            logger.info(f'Connection closed gracefully: {e}')
        except Exception as e:
            logger.error(f'Unexpected error in event loop: {e}')
            raise

    async def _incoming_messages(self) -> AsyncGenerator[Union[str, bytes], None]:
        """
        Generator that yields raw messages from the WebSocket connection.

        This asynchronous generator continuously receives messages from the
        WebSocket connection as long as it remains open.

        Yields:
            str: Raw message string received from the WebSocket.
        """
        ws = cast(WebSocketClientProtocol, self._ws_connection)
        while not ws.closed:
            yield await ws.recv()

    async def _process_single_message(self, raw_message: str):
        """
        Processes a single raw WebSocket message.

        Parses the raw message string into a JSON object and routes it
        to the appropriate handler based on whether it's a command
        response or an event notification.

        Args:
            raw_message: Raw message string to process.
        """
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
        """
        Attempts to parse a raw message string into a JSON object.

        Safely parses the message and handles any JSON parsing errors.

        Args:
            raw_message: Raw message string to parse.

        Returns:
            dict or None: Parsed JSON object if successful, None if parsing fails.
        """
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse message: {raw_message[:200]}...')
            return None

    @staticmethod
    def _is_command_response(message: Union[Event, Response]) -> bool:
        """
        Determines if a message is a response to a previously sent command.

        Command responses have an integer 'id' field matching the original command ID.
        Event notifications have a 'method' field but no 'id' field.

        Args:
            message (dict): The message to check.

        Returns:
            bool: True if the message is a command response, False if it's an event.
        """
        return 'id' in message and isinstance(message.get('id'), int)

    async def _handle_command_message(self, message: Response):
        """
        Processes command response messages.

        Resolves the future associated with the command ID, allowing the
        calling code to continue execution with the response data.

        Args:
            message: Command response message to process.
        """
        logger.debug(f'Processing command response: {message.get("id")}')
        self._command_manager.resolve_command(message['id'], json.dumps(message))

    async def _handle_event_message(self, message: Event):
        """
        Processes event notification messages.

        Delegates event processing to the events handler, which will invoke
        any registered callbacks for the event type.

        Args:
            message: Event message to process, containing method and params.
        """
        event_type = message.get('method', 'unknown-event')
        logger.debug(f'Processing {event_type} event')
        await self._events_handler.process_event(message)

    def __repr__(self):
        """
        Returns a string representation for debugging.

        Returns:
            str: String representation with connection details.
        """
        return f'ConnectionHandler(port={self._connection_port})'

    def __str__(self):
        """
        Returns a user-friendly string representation.

        Returns:
            str: String representation with connection details.
        """
        return f'ConnectionHandler(port={self._connection_port})'

    async def __aenter__(self):
        """
        Async context manager entry point.

        Allows using the ConnectionHandler in an async with statement.

        Returns:
            ConnectionHandler: This instance.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.

        Ensures proper cleanup when exiting an async with block.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        await self.close()
