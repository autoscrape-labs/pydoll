from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING, Optional

from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import ChromiumOptionsManager
from pydoll.exceptions import UnsupportedOS
from pydoll.utils import validate_browser_paths

if TYPE_CHECKING:
    from pydoll.browser.options import ChromiumOptions

logger = logging.getLogger(__name__)


class Chrome(Browser):
    """Chrome browser implementation for CDP automation."""

    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        connection_port: Optional[int] = None,
    ):
        """
        Initialize Chrome browser instance.

        Args:
            options: Chrome configuration options (default if None).
            connection_port: CDP WebSocket port (random if None).
        """
        options_manager = ChromiumOptionsManager(options)
        super().__init__(options_manager, connection_port)

    @staticmethod
    def _get_default_binary_location():
        """
        Get default Chrome executable path based on OS.

        Returns:
            Path to Chrome executable.

        Raises:
            UnsupportedOS: If OS is not supported.
            ValueError: If executable not found at default location.
        """
        os_name = platform.system()
        logger.debug(f'Resolving default Chrome binary for OS: {os_name}')

        browser_paths = {
            'Windows': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ],
            'Linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
            ],
            'Darwin': [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ],
        }

        browser_path = browser_paths.get(os_name)

        if not browser_path:
            logger.error(f'Unsupported OS: {os_name}')
            raise UnsupportedOS(f'Unsupported OS: {os_name}')

        path = validate_browser_paths(browser_path)
        logger.debug(f'Using Chrome binary: {path}')
        return path
