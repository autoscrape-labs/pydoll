from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import websockets

from pydoll.connection.base_connection_handler import BaseConnectionHandler
from pydoll.connection.managers.event_trackers import BiDiEventTracker

if TYPE_CHECKING:
    from typing import Optional

    from websockets.asyncio.client import connect as Connect

logger = logging.getLogger(__name__)


class BiDiConnectionHandler(BaseConnectionHandler):
    """
    WebDriver BiDi WebSocket connection handler.

    Implements BiDi-specific URL resolution, message parsing,
    and error extraction.
    """

    def __init__(
        self,
        connection_port: Optional[int] = None,
        ws_address: Optional[str] = None,
        ws_connector: type[Connect] = websockets.connect,
    ):
        super().__init__(
            connection_port=connection_port,
            ws_address=ws_address,
            ws_connector=ws_connector,
        )

    def _create_event_tracker(self) -> BiDiEventTracker:
        return BiDiEventTracker()

    async def _resolve_ws_address(self) -> str:
        if self._ws_address:
            logger.debug('Using provided WebSocket address')
            return self._ws_address
        address = f'ws://localhost:{self._connection_port}/session'
        logger.debug(f'Resolved BiDi WebSocket address: {address}')
        return address

    def _is_command_response(self, message: dict) -> bool:
        return message.get('type') in ('success', 'error')

    def _extract_error(self, message: dict) -> str | None:
        if message.get('type') == 'error':
            error_code = message.get('error', 'unknown_error')
            error_msg = message.get('message', '')
            return f'{error_code}: {error_msg}'
        return None
