import asyncio
import logging
from typing import Dict

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
        self._pending_commands: Dict[int, asyncio.Future] = {}
        self._id = 1

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
        return future

    def resolve_command(self, response_id: int, result: str):
        """Resolve pending command with its result."""
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(result)
            del self._pending_commands[response_id]

    def remove_pending_command(self, command_id: int):
        """Remove pending command without resolving (for timeouts/cancellations)."""
        if command_id in self._pending_commands:
            del self._pending_commands[command_id]
