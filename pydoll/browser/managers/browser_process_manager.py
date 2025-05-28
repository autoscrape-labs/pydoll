import subprocess
from typing import Callable, Optional


class BrowserProcessManager:
    """
    Manages browser process lifecycle for CDP-based browser automation.

    This manager handles browser process creation, monitoring, and termination
    to ensure proper resource management during automation sessions. It provides:

    1. Configurable process creation with support for custom process handlers
    2. Standardized browser launch with CDP debugging port configuration
    3. Clean process termination with graceful shutdown attempts
    4. Resource cleanup to prevent orphaned processes

    The class serves as a critical component in the CDP automation flow by
    maintaining the connection between the Python automation code and the
    actual browser process running on the system.
    """

    def __init__(
        self,
        process_creator: Optional[Callable[[list[str]], subprocess.Popen]] = None,
    ):
        """
        Initializes a new browser process manager.

        Creates a manager that will handle browser process lifecycle events.
        The manager can use either the default subprocess-based implementation
        or a custom process creation function for specialized environments.

        Args:
            process_creator: Optional custom function to create browser processes.
                If provided, this function must accept a list of command arguments
                and return a subprocess.Popen-compatible object. If None, the
                default subprocess-based implementation will be used.

        Note:
            Custom process creators are useful for environments with special
            process handling needs, containerized environments, or when additional
            process monitoring is required.
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
        Launches a browser process with CDP debugging enabled.

        Starts the browser at the specified binary location, configures it
        to listen for CDP connections on the given port, and applies any
        additional browser-specific arguments. This creates the browser
        process that the CDP client will connect to.

        Args:
            binary_location: Absolute path to the browser executable.
                Must be a valid, executable browser binary compatible with CDP.
            port: TCP port to use for CDP WebSocket connections.
                Should be an available port not used by other processes.
            arguments: Additional command-line arguments to pass to the browser.
                These typically include configuration for headless mode, window size,
                user data directory, and other browser behavior settings.

        Returns:
            subprocess.Popen: The started browser process instance, which can
                be used for direct process interaction if needed.

        Note:
            The remote-debugging-port argument is automatically added to enable
            CDP connections. The process runs asynchronously and doesn't block
            execution - the connection to it is established separately.
        """
        self._process = self._process_creator([
            binary_location,
            f'--remote-debugging-port={port}',
            *arguments,
        ])
        return self._process

    @staticmethod
    def _default_process_creator(command: list[str]) -> subprocess.Popen:
        """
        Creates a browser process using standard subprocess handling.

        This default implementation launches the browser with stdout and stderr
        redirected to pipes, preventing browser output from appearing in the
        console while still allowing it to be captured if needed.

        Args:
            command: List containing the executable path and all command-line
                arguments to pass to the browser process.

        Returns:
            subprocess.Popen: A process object connected to the started browser.
                The process runs asynchronously with standard output captured.

        Note:
            This method is used internally when no custom process creator is provided.
            It intentionally captures output to prevent browser messages from
            cluttering the console during automation.
        """
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_process(self):
        """
        Terminates the browser process with graceful shutdown attempt.

        Attempts to cleanly shut down the browser process by first sending a
        termination signal (SIGTERM on Unix, taskkill on Windows) and waiting
        for the process to exit. If the browser doesn't exit within the timeout
        period, forces termination with a kill signal.

        This two-phase shutdown helps ensure:
        1. Clean browser exit with proper profile saving when possible
        2. Definite process termination even if the browser is unresponsive
        3. No orphaned browser processes after automation completes

        Note:
            This method is safe to call even if no browser is running.
            It includes a 15-second timeout for graceful termination before
            forcing the process to close, which balances clean shutdown with
            automation speed requirements.
        """
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
