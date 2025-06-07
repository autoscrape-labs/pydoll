from typing import Optional

from pydoll.browser.options import Options


class ProxyManager:
    """
    Manages proxy configuration and credentials for CDP automation.

    Extracts embedded credentials from proxy URLs, secures authentication
    information, and sanitizes command-line arguments.
    """

    def __init__(self, options: Options):
        """
        Initialize proxy manager with browser options.

        Args:
            options: Browser options potentially containing proxy configuration.
                Will be modified if credentials are found.
        """
        self.options = options

    def get_proxy_credentials(self) -> tuple[bool, tuple[Optional[str], Optional[str]]]:
        """
        Extract and secure proxy authentication credentials.

        Searches for proxy settings, extracts embedded credentials,
        and sanitizes options to remove credential exposure.

        Returns:
            Tuple of (has_private_proxy, (username, password)).
        """
        private_proxy = False
        credentials: tuple[Optional[str], Optional[str]] = (None, None)

        proxy_arg = self._find_proxy_argument()

        if proxy_arg is not None:
            index, proxy_value = proxy_arg
            has_credentials, username, password, clean_proxy = self._parse_proxy(proxy_value)

            if has_credentials:
                self._update_proxy_argument(index, clean_proxy)
                private_proxy = True
                credentials = (username, password)

        return private_proxy, credentials

    def _find_proxy_argument(self) -> Optional[tuple[int, str]]:
        """
        Find proxy server configuration in browser options.

        Returns:
            Tuple of (index, proxy_url) if found, None otherwise.
        """
        for index, arg in enumerate(self.options.arguments):
            if arg.startswith('--proxy-server='):
                return index, arg.split('=', 1)[1]
        return None

    @staticmethod
    def _parse_proxy(proxy_value: str) -> tuple[bool, Optional[str], Optional[str], str]:
        """
        Parse proxy URL to extract authentication credentials.

        Args:
            proxy_value: Proxy URL potentially containing username:password@server:port.

        Returns:
            Tuple of (has_credentials, username, password, clean_proxy_url).
        """
        if '@' not in proxy_value:
            return False, None, None, proxy_value

        try:
            creds_part, server_part = proxy_value.split('@', 1)
            username, password = creds_part.split(':', 1)
            return True, username, password, server_part
        except ValueError:
            return False, None, None, proxy_value

    def _update_proxy_argument(self, index: int, clean_proxy: str) -> None:
        """Replace proxy argument with credential-free version."""
        self.options.arguments[index] = f'--proxy-server={clean_proxy}'
