import os
from typing import Optional

from pydoll.browser.options import ChromeOptions, EdgeOptions, Options
from pydoll.constants import BrowserType
from pydoll.exceptions import InvalidBrowserPath, InvalidOptionsObject


class BrowserOptionsManager:
    """
    Manages browser options configuration for CDP-based browser automation.

    This utility class provides static methods for handling browser options across
    different browser types (Chrome, Edge) while ensuring proper defaults and
    compatibility settings are applied. It centralizes options management to:

    1. Create appropriate browser-specific options objects
    2. Apply default arguments needed for CDP integration
    3. Validate browser binary locations
    4. Handle browser-specific configuration needs

    The class works closely with the Options hierarchy (Options base class and
    browser-specific subclasses like ChromeOptions and EdgeOptions) to ensure
    proper configuration for each browser type.
    """

    @staticmethod
    def initialize_options(
        options: Optional[Options] = None,
        browser_type: Optional[BrowserType] = None,
    ) -> Options:
        """
        Initializes browser options based on browser type.

        Creates a new appropriate options instance if none is provided, or validates
        and returns the existing options instance. This ensures that proper
        browser-specific options are available for browser initialization.

        Args:
            options: Existing Options instance to use. If None, a new instance
                will be created based on browser_type.
            browser_type: Type of browser to create options for. Used when
                options is None to determine the specific Options subclass to create.

        Returns:
            Options: A properly initialized browser options instance.

        Raises:
            InvalidOptionsObject: If provided options is not an instance
                of Options class
        """
        if options is None:
            if browser_type == BrowserType.CHROME:
                return ChromeOptions()
            elif browser_type == BrowserType.EDGE:
                return EdgeOptions()
            else:
                return Options()

        if not isinstance(options, Options):
            raise InvalidOptionsObject()

        return options

    @staticmethod
    def add_default_arguments(options: Options):
        """
        Adds default arguments required for proper CDP integration.

        Applies universal and browser-specific arguments to ensure proper
        functionality of the CDP connection and browser behavior. These arguments
        minimize prompts, disable unnecessary features, and configure security
        settings for automation.

        Args:
            options: The Options instance to modify with default arguments.

        Note:
            This method modifies the options object in-place by appending
            to its arguments list. It detects the specific browser type
            by examining the options class type.
        """
        options.arguments.append('--no-first-run')
        options.arguments.append('--no-default-browser-check')

        if isinstance(options, EdgeOptions):
            BrowserOptionsManager._add_edge_arguments(options)
        elif isinstance(options, ChromeOptions):
            BrowserOptionsManager._add_chrome_arguments(options)
        else:
            raise InvalidOptionsObject()

    @staticmethod
    def _add_edge_arguments(options: Options):
        """
        Adds Microsoft Edge-specific arguments to the options.

        Configures Edge-specific settings needed for proper CDP integration
        and automation, including disabling features that might interfere
        with automated browser control.

        Args:
            options: The Options instance to modify with Edge-specific arguments.

        Note:
            Called internally by add_default_arguments when EdgeOptions are detected.
            The arguments address Edge-specific behaviors that need customization
            for proper automation.
        """
        options.add_argument('--disable-crash-reporter')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-background-networking')
        options.add_argument('--remote-allow-origins=*')

    @staticmethod
    def _add_chrome_arguments(options: Options):
        """
        Adds Google Chrome-specific arguments to the options.

        Configures Chrome-specific settings needed for proper CDP integration
        and automation, focusing on settings that differ from the base
        browser configuration.

        Args:
            options: The Options instance to modify with Chrome-specific arguments.

        Note:
            Called internally by add_default_arguments when ChromeOptions are detected.
            Currently only adds remote origin access, but can be extended for other
            Chrome-specific needs.
        """
        options.add_argument('--remote-allow-origins=*')

    @staticmethod
    def validate_browser_paths(paths: list[str]) -> str:
        """
        Validates potential browser executable paths and returns the first valid one.

        Checks a list of possible browser binary locations to find an existing,
        executable browser. This is used by browser-specific subclasses to locate
        the browser executable when no explicit binary path is provided.

        Args:
            paths: List of potential file paths to check for the browser executable.
                These should be absolute paths appropriate for the current OS.

        Returns:
            str: The first valid browser executable path found.

        Raises:
            InvalidBrowserPath: If the browser executable is not found at the path.
        """
        for path in paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        raise InvalidBrowserPath(f'No valid browser path found in: {paths}')
