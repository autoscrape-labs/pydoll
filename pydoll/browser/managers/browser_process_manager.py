import logging
import subprocess
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class BrowserProcessManager:
    """
    Manages browser process lifecycle for CDP automation.

    Handles process creation, monitoring, and termination with proper
    resource cleanup and graceful shutdown.
    """

    def __init__(
        self,
        process_creator: Optional[Callable[[list[str]], subprocess.Popen]] = None,
    ):
        """
        Initialize browser process manager.

        Args:
            process_creator: Custom function to create browser processes.
                Must accept command list and return subprocess.Popen object.
                Uses default subprocess implementation if None.
        """
        self._process_creator = process_creator or self._default_process_creator
        self._process: Optional[subprocess.Popen] = None
        logger.debug(
            f'BrowserProcessManager initialized; custom process_creator={bool(process_creator)}'
        )

    def start_browser_process(
        self,
        binary_location: str,
        port: int,
        arguments: list[str],
    ) -> subprocess.Popen:
        """
        Launch browser process with CDP debugging enabled.

        Args:
            binary_location: Path to browser executable.
            port: TCP port for CDP WebSocket connections.
            arguments: Additional command-line arguments.

        Returns:
            Started browser process instance.

        Note:
            Automatically adds --remote-debugging-port argument.
        """
        logger.info(f'Starting browser process: {binary_location} on port {port}')
        command = [
            binary_location,
            f'--remote-debugging-port={port}',
            *arguments,
        ]
        logger.debug(f'Command: {command}')
        self._process = self._process_creator(command)
        logger.debug(
            f'Browser process started: pid={self._process.pid if self._process else "unknown"}'
        )
        return self._process

    @staticmethod
    def _default_process_creator(command: list[str]) -> subprocess.Popen:
        """Create browser process with output capture to prevent console clutter."""
        logger.debug(f'Creating process: {command}')
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_process(self):
        """
        Terminate browser process with graceful shutdown.

        Attempts SIGTERM first, then SIGKILL after 15-second timeout.
        Safe to call even if no process is running.
        """
        if self._process:
            logger.info(f'Stopping browser process pid={self._process.pid}')
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
                logger.debug('Process terminated gracefully')
            except subprocess.TimeoutExpired:
                logger.warning('Process did not terminate in 15s; sending SIGKILL')
                self._process.kill()
                logger.debug('Process killed')
