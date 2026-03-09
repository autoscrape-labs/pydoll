from __future__ import annotations

import logging
import platform
from typing import Optional

from pydoll.browser.firefox.base import FirefoxBrowser
from pydoll.browser.managers.firefox_options_manager import FirefoxOptionsManager
from pydoll.exceptions import UnsupportedOS
from pydoll.utils import validate_browser_paths

logger = logging.getLogger(__name__)


class Firefox(FirefoxBrowser):
    """Firefox browser implementation using WebDriver BiDi."""

    def __init__(
        self,
        options=None,
        connection_port: Optional[int] = None,
    ):
        """
        Initialize Firefox browser instance.

        Args:
            options: FirefoxOptions configuration (default if None).
            connection_port: BiDi WebSocket port (random if None).
        """
        options_manager = FirefoxOptionsManager(options)
        super().__init__(options_manager, connection_port)

    @staticmethod
    def _get_default_binary_location() -> str:
        """
        Get default Firefox executable path based on OS.

        Returns:
            Path to Firefox executable.

        Raises:
            UnsupportedOS: If OS is not supported.
            InvalidBrowserPath: If Firefox is not found at default locations.
        """
        os_name = platform.system()
        logger.debug(f'Resolving default Firefox binary for OS: {os_name}')

        browser_paths = {
            'Windows': [
                r'C:\Program Files\Mozilla Firefox\firefox.exe',
                r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
            ],
            'Linux': [
                # Prefer the real snap binary over the wrapper scripts —
                # the wrappers (/usr/bin/firefox, /snap/bin/firefox) silently
                # drop unknown flags like --remote-debugging-port.
                '/snap/firefox/current/usr/lib/firefox/firefox',
                '/usr/lib/firefox/firefox',
                '/usr/bin/firefox-esr',
            ],
            'Darwin': [
                '/Applications/Firefox.app/Contents/MacOS/firefox',
            ],
        }

        paths = browser_paths.get(os_name)
        if not paths:
            logger.error(f'Unsupported OS: {os_name}')
            raise UnsupportedOS(f'Unsupported OS: {os_name}')

        path = validate_browser_paths(paths)
        logger.debug(f'Using Firefox binary: {path}')
        return path
