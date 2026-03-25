from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import websockets

from pydoll.connection.base_connection_handler import BaseConnectionHandler
from pydoll.connection.managers.event_trackers import CDPEventTracker
from pydoll.utils import get_browser_ws_address

if TYPE_CHECKING:
    from typing import Any, Callable, Coroutine, Optional

    from websockets.asyncio.client import connect as Connect

logger = logging.getLogger(__name__)


class CDPConnectionHandler(BaseConnectionHandler):
    """
    Chrome DevTools Protocol WebSocket connection handler.

    Implements CDP-specific URL resolution, message parsing,
    and error extraction.
    """

    def __init__(
        self,
        connection_port: Optional[int] = None,
        page_id: Optional[str] = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
        ws_address: Optional[str] = None,
    ):
        self._ws_address_resolver = ws_address_resolver
        super().__init__(
            connection_port=connection_port,
            page_id=page_id,
            ws_address=ws_address,
            ws_connector=ws_connector,
        )

    def _create_event_tracker(self) -> CDPEventTracker:
        return CDPEventTracker()

    async def _resolve_ws_address(self) -> str:
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

    def _is_command_response(self, message: dict) -> bool:
        return 'id' in message and isinstance(message.get('id'), int)

    def _extract_error(self, message: dict) -> str | None:
        error = message.get('error')
        if error:
            return error.get('message', str(error)) if isinstance(error, dict) else str(error)
        return None


ConnectionHandler = CDPConnectionHandler
