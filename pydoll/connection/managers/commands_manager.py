from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydoll.protocol.base import Command

logger = logging.getLogger(__name__)


class CommandsManager:
    """
    Manages command lifecycle and ID assignment for CDP commands.

    Handles command future creation, ID generation, and response resolution
    for asynchronous command execution.
    """

    def __init__(self) -> None:
        """Initialize command manager with empty state."""
        self._pending_commands: dict[int, asyncio.Future] = {}
        self._id = 1
        logger.debug('CommandsManager initialized')

    def create_command_future(self, command: Command) -> asyncio.Future:
        """
        Create future for command and assign unique ID.

        Args:
            command: Command to prepare for execution.

        Returns:
            Future that resolves when command completes.
        """
        command['id'] = self._id
        future = asyncio.Future()  # type: ignore
        self._pending_commands[self._id] = future
        self._id += 1
        logger.debug(
            f'Created future for command id={command["id"]} method={command.get("method")}'
        )
        return future

    def resolve_command(self, response_id: int, result: str):
        """Resolve pending command with its result."""
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(result)
            del self._pending_commands[response_id]
            logger.debug(f'Resolved command future id={response_id}')

    def remove_pending_command(self, command_id: int):
        """Remove pending command without resolving (for timeouts/cancellations)."""
        if command_id in self._pending_commands:
            del self._pending_commands[command_id]
            logger.debug(f'Removed pending command id={command_id}')
