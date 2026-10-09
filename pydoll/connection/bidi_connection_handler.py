from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import websockets

from pydoll.connection.base_connection_handler import BaseConnectionHandler
from pydoll.connection.managers.event_trackers import BiDiEventTracker
from pydoll.exceptions import CommandFailed

if TYPE_CHECKING:
    from websockets.asyncio.client import connect as Connect

logger = logging.getLogger(__name__)


class BiDiConnectionHandler(BaseConnectionHandler):
    """
    WebSocket connection manager for WebDriver BiDi endpoints.

    Implements BiDi-specific URL resolution, message routing and error
    extraction on top of ``BaseConnectionHandler``.
    """

    _event_tracker: BiDiEventTracker

    def __init__(
        self,
        connection_port: int | None = None,
        ws_address: str | None = None,
        ws_connector: type[Connect] = websockets.connect,
    ):
        """
        Initialize connection handler.

        Args:
            connection_port: Port of the browser's WebDriver BiDi server.
            ws_address: WebSocket address. It has priority over connection_port.
            ws_connector: WebSocket connection factory (mainly for testing).
        """
        super().__init__(
            connection_port=connection_port,
            ws_address=ws_address,
            ws_connector=ws_connector,
        )

    @property
    def network_logs(self) -> list[dict]:
        """Snapshot of the captured ``network.beforeRequestSent`` events."""
        return self._event_tracker.network_logs

    @property
    def dialog(self) -> dict:
        """Currently open ``browsingContext.userPromptOpened`` event; empty when none is open."""
        return self._event_tracker.dialog

    @staticmethod
    def _create_event_tracker() -> BiDiEventTracker:
        return BiDiEventTracker()

    async def _resolve_ws_address(self) -> str:
        if self._ws_address:
            logger.debug('Using provided WebSocket address')
            return self._ws_address
        address = f'ws://localhost:{self._connection_port}/session'
        logger.debug('Resolved BiDi WebSocket address: %s', address)
        return address

    @staticmethod
    def _is_command_response(message: dict) -> bool:
        """BiDi tags every message: command answers are ``success`` or ``error``."""
        return message.get('type') in {'success', 'error'}

    @staticmethod
    def _extract_error(method: str, response: dict) -> CommandFailed | None:
        """Read a BiDi error message (``{type: 'error', error, message, stacktrace?}``).

        BiDi identifies errors by a string code ("no such node", "invalid argument"...)
        rather than a number, so ``CommandFailed.code`` stays 0, ``data`` carries the
        BiDi error code verbatim and the message is prefixed with it.
        """
        if response.get('type') != 'error':
            return None
        error_code = str(response.get('error', 'unknown error'))
        message = str(response.get('message', ''))
        stacktrace = response.get('stacktrace')
        if stacktrace:
            logger.debug('BiDi error stacktrace for %s: %s', method, stacktrace)
        return CommandFailed(
            method=method,
            code=0,
            message=f'{error_code}: {message}' if message else error_code,
            data=error_code,
        )
