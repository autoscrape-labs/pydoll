from typing import Optional

from pydoll.browser.options import Options


class ProxyManager:
    """
    Manages proxy configuration and credentials for CDP browser automation.

    This specialized manager handles all aspects of proxy integration including:

    1. Extracting embedded credentials from proxy URLs
    2. Securing sensitive proxy authentication information
    3. Reformatting proxy arguments for browser compatibility
    4. Preparing proxy authentication for CDP request interception

    The class works by analyzing browser options for proxy settings, securely
    extracting any credentials, and sanitizing the command line arguments to
    prevent credential exposure while maintaining proper proxy connectivity.
    """

    def __init__(self, options: Options):
        """
        Initializes a proxy manager with browser options.

        Creates a manager that will handle proxy configuration based on the
        provided browser options object. The manager analyzes the options'
        arguments list to find and process proxy settings.

        Args:
            options: Browser options containing command-line arguments,
                potentially including proxy configuration (--proxy-server).
                This object will be modified if credentials are found.

        Note:
            The manager doesn't activate any proxy settings on its own;
            it only processes existing proxy settings in the options object.
        """
        self.options = options

    def get_proxy_credentials(self) -> tuple[bool, tuple[Optional[str], Optional[str]]]:
        """
        Extracts, secures, and returns proxy authentication credentials.

        This method:
        1. Searches for proxy settings in browser options
        2. Extracts any embedded credentials from the proxy URL
        3. Sanitizes the options to remove exposed credentials
        4. Returns authentication status and credentials for CDP configuration

        This is typically called during browser initialization to prepare for
        any authentication challenges that may occur during proxy connection.

        Returns:
            tuple[bool, tuple[str, str]]: A tuple containing:
                - bool: True if private proxy with credentials was found
                - tuple[str, str]: Username and password for proxy
                    authentication
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
        Locates proxy server configuration in browser options.

        Searches through the options' arguments list to find the first
        instance of a --proxy-server argument, which specifies proxy
        settings for the browser.

        Returns:
            Optional[tuple[int, str]]: If found, returns a tuple containing:
                - The index of the argument in the options.arguments list
                - The proxy URL value (everything after --proxy-server=)
                Returns None if no proxy configuration is found.

        Note:
            Only processes the first proxy argument found, as browsers
            typically only support a single proxy configuration.
        """
        for index, arg in enumerate(self.options.arguments):
            if arg.startswith('--proxy-server='):
                return index, arg.split('=', 1)[1]
        return None

    @staticmethod
    def _parse_proxy(proxy_value: str) -> tuple[bool, Optional[str], Optional[str], str]:
        """
        Parses a proxy URL to extract authentication credentials.

        Analyzes a proxy URL string to detect and extract embedded credentials
        using the standard format: username:password@hostname:port.
        Also produces a clean version of the proxy URL with credentials removed.

        Args:
            proxy_value: The proxy URL string to parse, potentially containing
                credentials in the format username:password@server:port

        Returns:
            tuple[bool, str, str, str]: A tuple containing:
                - bool: True if credentials were found
                - str: Username (or None if no credentials)
                - str: Password (or None if no credentials)
                - str: Clean proxy URL without credentials
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
        """
        Updates the proxy argument in options with a credential-free version.

        Replaces the original proxy URL (which may contain embedded credentials)
        with a sanitized version that doesn't expose sensitive authentication
        information while still maintaining the correct proxy server configuration.

        Args:
            index: Position of the proxy argument in the options.arguments list
            clean_proxy: Sanitized proxy URL without credentials
        """
        self.options.arguments[index] = f'--proxy-server={clean_proxy}'
