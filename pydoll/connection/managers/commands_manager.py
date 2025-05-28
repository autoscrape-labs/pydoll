import asyncio
import logging
from typing import Dict

from pydoll.protocol.base import Command

logger = logging.getLogger(__name__)


class CommandsManager:
    """
    Manages the lifecycle of commands sent to the browser.

    This class handles the creation of command futures, command ID generation,
    and resolution of command responses. It maintains a mapping of command IDs
    to their corresponding futures, allowing asynchronous command execution.
    """

    def __init__(self) -> None:
        """
        Initializes the CommandManager.

        Sets up internal state for tracking pending commands and
        initializes the command ID counter.

        Returns:
            None
        """
        self._pending_commands: Dict[int, asyncio.Future] = {}
        self._id = 1

    def create_command_future(self, command: Command) -> asyncio.Future:
        """
        Creates a future for a command and assigns it a unique ID.

        This method assigns a unique ID to the command, creates a future
        to track its completion, and stores the future in the pending
        commands dictionary.

        Args:
            command (Command): The command to prepare for execution.

        Returns:
            asyncio.Future: A future that will be resolved when the command
                completes.
        """
        command['id'] = self._id
        future = asyncio.Future()  # type: ignore
        self._pending_commands[self._id] = future
        self._id += 1
        return future

    def resolve_command(self, response_id: int, result: str):
        """
        Resolves a pending command with its result.

        This method sets the result for the future associated with the
        command ID and removes it from the pending commands dictionary.

        Args:
            response_id (int): The ID of the command to resolve.
            result (str): The result data for the command.

        Returns:
            None
        """
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(result)
            del self._pending_commands[response_id]

    def remove_pending_command(self, command_id: int):
        """
        Removes a pending command without resolving it.

        This method is useful for handling timeouts or cancellations,
        allowing cleanup of command futures that will never be resolved.

        Args:
            command_id (int): The ID of the command to remove.

        Returns:
            None
        """
        if command_id in self._pending_commands:
            del self._pending_commands[command_id]
