import logging
import os
import shutil
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

logger = logging.getLogger(__name__)


class TempDirectoryManager:
    """
    Manages temporary directory lifecycle for CDP browser automation.

    Creates isolated temporary directories for browser profiles and handles
    secure cleanup with retry mechanisms for locked files.
    """

    def __init__(self, temp_dir_factory: Callable[[], TemporaryDirectory] = TemporaryDirectory):
        """
        Initialize temporary directory manager.

        Args:
            temp_dir_factory: Function to create temporary directories.
                Must return TemporaryDirectory-compatible object.
        """
        self._temp_dir_factory = temp_dir_factory
        self._temp_dirs: list[TemporaryDirectory] = []
        logger.debug('TempDirectoryManager initialized')

    def create_temp_dir(self) -> TemporaryDirectory:
        """
        Create and track new temporary directory for browser use.

        Returns:
            TemporaryDirectory object for browser --user-data-dir argument.
        """
        temp_dir = self._temp_dir_factory()
        self._temp_dirs.append(temp_dir)
        logger.debug(f'Created temp directory: {temp_dir.name}')
        return temp_dir

    @staticmethod
    def retry_process_file(func: Callable[[str], None], path: str, retry_times: int = 10):
        """
        Execute file operation with retry logic for locked files.

        Args:
            func: Function to execute on path.
            path: File or directory path to operate on.
            retry_times: Maximum retry attempts (negative = unlimited).

        Raises:
            PermissionError: If operation fails after all retries.
        """
        retry_time = 0
        while retry_times < 0 or retry_time < retry_times:
            retry_time += 1
            try:
                func(path)
                break
            except PermissionError:
                time.sleep(0.1)
                logger.debug(
                    f'Retrying file operation due to PermissionError (attempt {retry_time})'
                )
        else:
            raise PermissionError()

    def handle_cleanup_error(self, func: Callable[[str], None], path: str, exc_info: tuple):
        """
        Handle errors during directory cleanup with browser-specific workarounds.

        Args:
            func: Original function that failed.
            path: Path that could not be processed.
            exc_info: Exception information tuple.

        Note:
            Handles Chromium-specific locked files like CrashpadMetrics.
        """
        matches = ['CrashpadMetrics-active.pma']
        match_substrings = ['Safe Browsing', 'Safe Browsing Cookies']
        # Extra patterns commonly locked on Windows; compare case-insensitively
        windows_locked_substrings = [
            '\\cache\\',
            '/cache/',
            'no_vary_search',
            'journal.baj',
            '\\network\\cookies',
            '/network/cookies',
            'cookies-journal',
            '\\local storage\\',
            '/local storage/',
            '\\local storage\\leveldb\\',
            '/local storage/leveldb/',
            'leveldb',
            'indexeddb',
        ]
        exc_type, exc_value, _ = exc_info

        if exc_type is PermissionError:
            filename = Path(path).name
            # Known Chromium files that may remain locked briefly on Windows
            path_lc = path.lower()
            windows_match = os.name == 'nt' and any(
                substr in path_lc for substr in windows_locked_substrings
            )
            if (
                filename in matches
                or any(substr in path for substr in match_substrings)
                or windows_match
            ):
                try:
                    self.retry_process_file(func, path)
                    return
                except PermissionError:
                    logger.warning(f'Ignoring locked Chrome file during cleanup: {path}')
                    return
        elif exc_type is OSError:
            return
        raise exc_value

    def cleanup(self):
        """
        Remove all tracked temporary directories with error handling.

        Uses custom error handler for browser-specific file lock issues.
        Continues cleanup even if some files resist deletion.
        """
        for temp_dir in self._temp_dirs:
            logger.info(f'Cleaning up temp directory: {temp_dir.name}')
            shutil.rmtree(temp_dir.name, onerror=self.handle_cleanup_error)
            remaining = Path(temp_dir.name)
            if not remaining.exists():
                continue

            for attempt in range(10):
                time.sleep(0.2)
                try:
                    shutil.rmtree(temp_dir.name, onerror=self.handle_cleanup_error)
                except Exception:  # noqa: BLE001 - best-effort cleanup
                    pass
                if not remaining.exists():
                    logger.debug(
                        f'Temp directory removed after retry #{attempt + 1}: {temp_dir.name}'
                    )
                    break
            if remaining.exists():
                logger.warning(
                    f'Temp directory still present after retries (leftover files may remain): '
                    f'{temp_dir.name}'
                )
