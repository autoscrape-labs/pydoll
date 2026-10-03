from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.exceptions import BiDiCommandError
from pydoll.protocol.bidi import session as session_module

if TYPE_CHECKING:
    from pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse

logger = logging.getLogger(__name__)


class BiDiConnectionHandler(ConnectionHandler):
    """
    WebSocket connection handler for WebDriver BiDi protocol.

    Unlike the CDP handler, BiDi connects directly to ws://localhost:{port}
    without an HTTP discovery step.
    """

    def __init__(self, connection_port: int):
        super().__init__(connection_port=connection_port)
        self._session_id: Optional[str] = None

    async def _resolve_ws_address(self) -> str:
        """Return BiDi WebSocket address directly (no HTTP discovery needed)."""
        return f'ws://localhost:{self._connection_port}/session'

    async def execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResponse],
        timeout: int = 60,
    ) -> T_CommandResponse:
        """
        Send a BiDi command and await the response.

        Extends the base implementation to detect BiDi error responses
        (``{"type": "error", ...}``) and raise :class:`BiDiCommandError`.

        Raises:
            BiDiCommandError: If the browser returns a BiDi error response.
        """
        response: Any = await super().execute_command(command, timeout)
        if response.get('type') == 'error':
            error = response.get('error', 'unknown')
            message = response.get('message', '')
            logger.error(f'BiDi error response: error={error!r}, message={message!r}')
            raise BiDiCommandError(f'{error}: {message}')
        return response

    async def new_session(self, capabilities: Optional[dict] = None) -> dict:
        """
        Establish a new BiDi session with the browser.

        Sends session.new and stores the returned sessionId for future use.

        Args:
            capabilities: Optional BiDi capabilities dict (e.g. moz:firefoxOptions).

        Returns:
            Full response dict from the browser.
        """
        command = session_module.new_session(capabilities)
        response: dict = await self.execute_command(command)
        self._session_id = response.get('result', {}).get('sessionId')
        logger.info(f'BiDi session established: sessionId={self._session_id}')
        return response
