from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import websockets

from pydoll.connection.base_connection_handler import BaseConnectionHandler
from pydoll.connection.managers.event_trackers import CDPEventTracker
from pydoll.exceptions import CommandFailed, InvalidConnectionPort
from pydoll.utils import get_browser_ws_address

if TYPE_CHECKING:
    from typing import Any, Callable, Coroutine

    from websockets.asyncio.client import connect as Connect

    from pydoll.protocol.cdp.network.events import RequestWillBeSentEvent
    from pydoll.protocol.cdp.page.events import JavascriptDialogOpeningEvent

logger = logging.getLogger(__name__)


class CDPConnectionHandler(BaseConnectionHandler):
    """
    WebSocket connection manager for Chrome DevTools Protocol endpoints.

    Handles both browser-level and page-level CDP endpoints, implementing
    CDP-specific URL resolution, message routing and error extraction on top
    of ``BaseConnectionHandler``.
    """

    _event_tracker: CDPEventTracker

    def __init__(
        self,
        connection_port: int | None = None,
        page_id: str | None = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
        ws_address: str | None = None,
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
        self._ws_address_resolver = ws_address_resolver
        super().__init__(
            connection_port=connection_port,
            page_id=page_id,
            ws_address=ws_address,
            ws_connector=ws_connector,
        )

    @property
    def network_logs(self) -> list[RequestWillBeSentEvent]:
        """Snapshot of the captured ``Network.requestWillBeSent`` events."""
        return self._event_tracker.network_logs

    @property
    def dialog(self) -> JavascriptDialogOpeningEvent:
        """Currently open JavaScript dialog event; empty (falsy) when none is open."""
        return self._event_tracker.dialog

    @staticmethod
    def _create_event_tracker() -> CDPEventTracker:
        return CDPEventTracker()

    async def _resolve_ws_address(self) -> str:
        """Determine correct WebSocket address based on page ID."""
        if self._ws_address:
            logger.debug('Using provided WebSocket address')
            return self._ws_address
        if not self._page_id:
            if self._connection_port is None:
                raise InvalidConnectionPort()
            resolved = await self._ws_address_resolver(self._connection_port)
            logger.debug('Resolved browser-level WebSocket address: %s', resolved)
            return resolved
        address = f'ws://localhost:{self._connection_port}/devtools/page/{self._page_id}'
        logger.debug('Resolved page-level WebSocket address: %s', address)
        return address

    @staticmethod
    def _is_command_response(message: dict) -> bool:
        """Determine if message is command response or event notification."""
        return 'id' in message and isinstance(message.get('id'), int)

    @staticmethod
    def _extract_error(method: str, response: dict) -> CommandFailed | None:
        """Read the CDP ``error`` object (``{code, message, data?}``), if present."""
        error = response.get('error')
        if error is None:
            return None
        if not isinstance(error, dict):
            return CommandFailed(method=method, message=str(error))
        return CommandFailed(
            method=method,
            code=error.get('code', 0),
            message=error.get('message', ''),
            data=error.get('data', ''),
        )


ConnectionHandler = CDPConnectionHandler
