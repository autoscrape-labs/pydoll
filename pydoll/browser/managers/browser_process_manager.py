import logging
import subprocess
import threading
from collections import deque
from typing import Callable

from pydoll.exceptions import FailedToStartBrowser

logger = logging.getLogger(__name__)

STDERR_TAIL_LINES = 40
STDERR_LINE_CHARS = 500


def _forward_stderr(process: subprocess.Popen, tail: deque[str]) -> None:
    """Drain the browser's stderr into the debug log and keep its last lines.

    Chrome explains a failed start on stderr (a locked profile, a missing
    library, a bad flag), so the tail is what a start failure reports back.
    """
    stream = process.stderr
    if stream is None:
        return
    with stream:
        for raw in iter(stream.readline, b''):
            line = raw.decode(errors='replace').rstrip()
            tail.append(line[:STDERR_LINE_CHARS])
            logger.debug('browser stderr: %s', line)


class BrowserProcessManager:
    """
    Manages browser process lifecycle for CDP automation.

    Handles process creation, monitoring, and termination with proper
    resource cleanup and graceful shutdown.
    """

    def __init__(
        self,
        process_creator: Callable[[list[str]], subprocess.Popen] | None = None,
    ):
        """
        Initialize browser process manager.

        Args:
            process_creator: Custom function to create browser processes.
                Must accept command list and return subprocess.Popen object.
                Uses default subprocess implementation if None.
        """
        self._process_creator = process_creator or self._default_process_creator
        self._process: subprocess.Popen | None = None
        self._stderr_tail: deque[str] = deque(maxlen=STDERR_TAIL_LINES)
        self._stderr_thread: threading.Thread | None = None
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

        Raises:
            FailedToStartBrowser: If the executable cannot be launched at all
                (missing file, no permission).

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
        self._stderr_tail.clear()
        try:
            self._process = self._process_creator(command)
        except OSError as error:
            raise FailedToStartBrowser(f'Could not launch {binary_location}: {error}') from error
        logger.debug(
            f'Browser process started: pid={self._process.pid if self._process else "unknown"}'
        )
        return self._process

    def exit_code(self) -> int | None:
        """The process exit code, or None while it runs or before it was started."""
        if self._process is None:
            return None
        return self._process.poll()

    def recent_stderr(self) -> str:
        """The last lines the browser wrote to stderr, newest last.

        When the process has already exited, the drain thread is given a moment
        to deliver the lines it wrote on its way out.
        """
        if self._stderr_thread is not None and self.exit_code() is not None:
            self._stderr_thread.join(timeout=1)
        return '\n'.join(self._stderr_tail)

    def _default_process_creator(self, command: list[str]) -> subprocess.Popen:
        """Create the browser process, keeping its output off the console.

        Chrome writes warnings to stderr on almost every navigation. A pipe that
        nobody reads fills after about 64 KB, and from then on Chrome blocks on
        the write and stops answering CDP entirely, which in practice showed up
        as a browser that hung after fifty or so tabs. A daemon thread therefore
        drains stderr into the debug log, and stdout, which Chrome never uses,
        goes to the null device.
        """
        logger.debug(f'Creating process: {command}')
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self._stderr_thread = threading.Thread(
            target=_forward_stderr,
            args=(process, self._stderr_tail),
            name=f'pydoll-browser-stderr-{process.pid}',
            daemon=True,
        )
        self._stderr_thread.start()
        return process

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
