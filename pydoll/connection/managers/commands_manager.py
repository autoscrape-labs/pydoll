from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse

logger = logging.getLogger(__name__)


class CommandsManager:
    """
    Manages command lifecycle and ID assignment for CDP commands.

    Handles command future creation, ID generation, and response resolution
    for asynchronous command execution.
    """

    def __init__(self) -> None:
        """Initialize command manager with empty state."""
        self._pending_commands: dict[int, asyncio.Future[str]] = {}
        self._id = 1
        logger.debug('CommandsManager initialized')

    def create_command_future(
        self, command: Command[T_CommandParams, T_CommandResponse]
    ) -> asyncio.Future[str]:
        """
        Create future for command and assign unique ID.

        Args:
            command: Command to prepare for execution.

        Returns:
            Future that resolves with the raw response payload when the command completes.
        """
        command['id'] = self._id
        future: asyncio.Future[str] = asyncio.Future()
        self._pending_commands[self._id] = future
        self._id += 1
        logger.debug(
            f'Created future for command id={command["id"]} method={command.get("method")}'
        )
        return future

    def resolve_command(self, response_id: int, result: str):
        """Resolve pending command with its result.

        A late response can arrive after the caller already timed out (its future
        was cancelled by asyncio.wait_for) but before the command was removed.
        Popping and checking done() avoids InvalidStateError in that window.
        """
        future = self._pending_commands.pop(response_id, None)
        if future is not None and not future.done():
            future.set_result(result)
            logger.debug(f'Resolved command future id={response_id}')

    def remove_pending_command(self, command_id: int):
        """Remove pending command without resolving (for timeouts/cancellations)."""
        if command_id in self._pending_commands:
            del self._pending_commands[command_id]
            logger.debug(f'Removed pending command id={command_id}')

    def fail_all_pending(self, exc: BaseException):
        """Fail every pending command future with the given exception and clear them.

        Used when the connection is lost so in-flight commands raise immediately
        instead of hanging until their individual timeout expires.
        """
        if not self._pending_commands:
            return
        pending = list(self._pending_commands.items())
        self._pending_commands.clear()
        for command_id, future in pending:
            if not future.done():
                future.set_exception(exc)
        logger.debug(f'Failed {len(pending)} pending command(s): {type(exc).__name__}')
