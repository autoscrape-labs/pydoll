from __future__ import annotations

import platform
import sys
from typing import Optional

from pydoll.browser.firefox.base import FirefoxBrowser
from pydoll.browser.firefox.options import FirefoxOptions, FirefoxOptionsManager


class Firefox(FirefoxBrowser):
    """Firefox browser automation.

    Usage:
        async with Firefox() as browser:
            await browser.start()
            contexts = await browser.get_opened_contexts()
    """

    def __init__(
        self,
        options: Optional[FirefoxOptions] = None,
        connection_port: Optional[int] = None,
    ):
        super().__init__(
            options_manager=FirefoxOptionsManager(options),
            connection_port=connection_port,
        )

    @staticmethod
    def _get_default_binary_location() -> str:
        system = platform.system()
        if system == 'Darwin':
            return '/Applications/Firefox.app/Contents/MacOS/firefox'
        if system == 'Linux':
            return '/usr/bin/firefox'
        if system == 'Windows':
            return r'C:\Program Files\Mozilla Firefox\firefox.exe'
        raise FileNotFoundError(
            f'Unsupported platform: {system}. Set options.binary_location manually.'
        )
