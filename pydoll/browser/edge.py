import platform
from typing import Optional

from pydoll.browser.base import Browser
from pydoll.browser.constants import BrowserType
from pydoll.browser.managers import BrowserOptionsManager
from pydoll.browser.options import Options


class Edge(Browser):
    """
    A class that implements the Edge browser functionality.

    This class provides specific implementation for launching and
    controlling Microsoft Edge browsers.
    """

    def __init__(
        self,
        options: Optional[Options] = None,
        connection_port: Optional[int] = None,
        enable_fingerprint_spoofing: bool = False,
    ):
        """
        Initializes the Edge browser instance.

        Args:
            options (Options | None): An instance of Options class to configure
                the browser. If None, default options will be used.
            connection_port (int): The port to connect to the browser.
                Defaults to a random port between 9223 and 9322.
            enable_fingerprint_spoofing (bool): Whether to enable browser fingerprint
                spoofing. If True, a unique fingerprint will be generated for each session.
        """
        super().__init__(options, connection_port, BrowserType.EDGE, enable_fingerprint_spoofing)

    @staticmethod
    def _get_default_binary_location():
        """
        Gets the default location of the Edge browser executable.

        This method determines the default Edge executable path based
        on the operating system.

        Returns:
            str: The path to the Edge browser executable.

        Raises:
            ValueError: If the operating system is not supported or
                the browser executable is not found at the default location.
        """
        os_name = platform.system()

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
                (
                    '/Applications/Microsoft Edge.app/Contents/MacOS'
                    '/Microsoft Edge'
                ),
            ],
        }

        browser_path = browser_paths.get(os_name)

        if not browser_path:
            raise ValueError('Unsupported OS')

        return BrowserOptionsManager.validate_browser_paths(browser_path)
