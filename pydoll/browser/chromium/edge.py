from __future__ import annotations

import logging
import platform
from typing import TYPE_CHECKING, Optional

from pydoll.browser.chromium.base import Browser
from pydoll.browser.managers import ChromiumOptionsManager
from pydoll.exceptions import UnsupportedOS
from pydoll.utils import validate_browser_paths

if TYPE_CHECKING:
    from pydoll.browser.options import Options

logger = logging.getLogger(__name__)


class Edge(Browser):
    """Edge browser implementation for CDP automation."""

    def __init__(
        self,
        options: Optional[Options] = None,
        connection_port: Optional[int] = None,
    ):
        """
        Initialize Edge browser instance.

        Args:
            options: Edge configuration options (default if None).
            connection_port: CDP WebSocket port (random if None).
        """
        options_manager = ChromiumOptionsManager(options)
        super().__init__(options_manager, connection_port)

    @staticmethod
    def _get_default_binary_location():
        """
        Get default Edge executable path based on OS.

        Returns:
            Path to Edge executable.

        Raises:
            UnsupportedOS: If OS is not supported.
            ValueError: If executable not found at default location.
        """
        os_name = platform.system()
        logger.debug(f'Resolving default Edge binary for OS: {os_name}')

        browser_paths = {
            'Windows': [
                (
                    r'C:\Program Files\Microsoft\Edge\Application'
                    r'\msedge.exe'
                ),
                (
                    r'C:\Program Files (x86)\Microsoft\Edge'
                    r'\Application\msedge.exe'
                ),
            ],
            'Linux': [
                '/usr/bin/microsoft-edge',
            ],
            'Darwin': [
                ('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
            ],
        }

        browser_path = browser_paths.get(os_name)

        if not browser_path:
            logger.error(f'Unsupported OS: {os_name}')
            raise UnsupportedOS()

        path = validate_browser_paths(browser_path)
        logger.debug(f'Using Edge binary: {path}')
        return path
