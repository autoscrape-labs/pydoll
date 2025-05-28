import shutil
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable


class TempDirectoryManager:
    """
    Manages temporary directory lifecycle for CDP browser automation.

    This manager handles the creation, tracking, and secure cleanup of temporary
    directories used by browser instances for profile data, cache storage, and
    other ephemeral content. Key capabilities include:

    1. Creation of isolated temporary directories for browser profiles
    2. Tracking of all created directories for cleanup
    3. Resilient cleanup with retry mechanisms for locked files
    4. Error handling for browser-specific edge cases

    Temporary directories are essential for browser automation as they provide
    clean, isolated environments for each browser instance without persisting
    potentially sensitive data between runs or affecting the user's default profile.
    """

    def __init__(self, temp_dir_factory: Callable[[], TemporaryDirectory] = TemporaryDirectory):
        """
        Initializes a temporary directory manager with customizable factory.

        Creates a manager that will handle temporary directory creation and cleanup
        for browser instances. The manager can use either the standard library's
        TemporaryDirectory or a custom factory function for specialized environments.

        Args:
            temp_dir_factory: Function that creates temporary directory objects.
                Must return an object compatible with TemporaryDirectory interface.
                Defaults to the standard library's TemporaryDirectory.

        Note:
            Custom directory factories are useful for environments with specific
            security requirements, when directories need to be created in particular
            locations, or when additional cleanup steps are required.
        """
        self._temp_dir_factory = temp_dir_factory
        self._temp_dirs: list[TemporaryDirectory] = []

    def create_temp_dir(self) -> TemporaryDirectory:
        """
        Creates and tracks a new temporary directory for browser use.

        Creates a fresh temporary directory using the configured factory function
        and adds it to the internal tracking list for later cleanup. The directory
        is typically used for browser profiles, cache storage, and other browser data.

        Returns:
            TemporaryDirectory: A temporary directory object that can be used
                with browser --user-data-dir arguments. The .name attribute
                provides the path as a string.

        Note:
            Directories created by this method will be automatically cleaned up
            when the cleanup() method is called, typically during browser shutdown.

        Example:
            ```python
            temp_dir = temp_manager.create_temp_dir()
            browser_args.append(f'--user-data-dir={temp_dir.name}')
            ```
        """
        temp_dir = self._temp_dir_factory()
        self._temp_dirs.append(temp_dir)
        return temp_dir

    @staticmethod
    def retry_process_file(func: Callable[[str], None], path: str, retry_times: int = 10):
        """
        Executes a file operation with retry logic for locked files.

        Attempts to execute the provided file operation function, retrying
        if permission errors occur. This is particularly important during cleanup
        when browser processes may not have fully released file locks.

        Args:
            func: Function to execute on the path (typically an operation like
                os.remove or similar file manipulation function).
            path: File or directory path to operate on.
            retry_times: Maximum number of retry attempts. A negative value means
                unlimited retries. Default is 10 attempts.

        Raises:
            PermissionError: If the operation still fails after all retry attempts.

        Note:
            This method includes a short delay between retries to allow the operating
            system time to release file locks. This is particularly important when
            cleaning up files that were recently used by the browser.
        """
        retry_time = 0
        while retry_times < 0 or retry_time < retry_times:
            retry_time += 1
            try:
                func(path)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            raise PermissionError()

    def handle_cleanup_error(self, func: Callable[[str], None], path: str, exc_info: tuple):
        """
        Handles errors during directory cleanup with browser-specific workarounds.

        This error handler is passed to shutil.rmtree during cleanup to handle
        special cases like locked files or browser-specific temporary files that
        may resist deletion. It implements browser-specific workarounds for known
        problematic files.

        Args:
            func: Original function that failed (from shutil.rmtree).
            path: Path to the file or directory that could not be processed.
            exc_info: Exception information tuple (from sys.exc_info()).
                Contains exception type, value, and traceback.

        Raises:
            Various exceptions if the error cannot be handled.

        Note:
            This handler specifically addresses Chromium browser edge cases like
            locked CrashpadMetrics files. It silently ignores some non-critical
            OSErrors to ensure cleanup continues even with minor issues.
        """
        matches = ['CrashpadMetrics-active.pma']
        exc_type, exc_value, _ = exc_info

        if exc_type is PermissionError:
            if Path(path).name in matches:
                try:
                    self.retry_process_file(func, path)
                    return
                except PermissionError:
                    raise exc_value
        elif exc_type is OSError:
            return
        raise exc_value

    def cleanup(self):
        """
        Removes all tracked temporary directories with error handling.

        Performs a comprehensive cleanup of all temporary directories created by
        this manager, handling browser-specific edge cases and retrying operations
        on locked files. This ensures all temporary data is securely removed
        even in challenging scenarios.

        The cleanup process:
        1. Iterates through all tracked temporary directories
        2. Uses shutil.rmtree with custom error handler for each directory
        3. Handles browser-specific file lock issues gracefully
        4. Continues cleanup even if some non-critical files resist deletion

        Note:
            This method should be called during browser shutdown to ensure proper
            resource cleanup. It's typically invoked automatically when the browser
            is stopped, but can be called manually for additional cleanup if needed.
        """
        for temp_dir in self._temp_dirs:
            shutil.rmtree(temp_dir.name, onerror=self.handle_cleanup_error)
