import subprocess
from typing import Callable, Optional


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
        self._process = self._process_creator([
            binary_location,
            f'--remote-debugging-port={port}',
            *arguments,
        ])
        return self._process

    @staticmethod
    def _default_process_creator(command: list[str]) -> subprocess.Popen:
        """Create browser process with output capture to prevent console clutter."""
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_process(self):
        """
        Terminate browser process with graceful shutdown.

        Attempts SIGTERM first, then SIGKILL after 15-second timeout.
        Safe to call even if no process is running.
        """
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
