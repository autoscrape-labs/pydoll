from typing import Optional

from pydoll.browser.interfaces import BrowserOptionsManager, Options
from pydoll.browser.options import ChromiumOptions
from pydoll.exceptions import InvalidOptionsObject


class ChromiumOptionsManager(BrowserOptionsManager):
    """
    Manages browser options configuration for Chromium-based browsers.

    Handles options creation, validation, and applies default CDP arguments
    for Chrome and Edge browsers.
    """

    def __init__(self, options: Optional[Options] = None):
        self.options = options

    def initialize_options(
        self,
    ) -> ChromiumOptions:
        """
        Initialize and validate browser options.

        Creates ChromiumOptions if none provided, validates existing options,
        and applies default CDP arguments.

        Returns:
            Properly configured ChromiumOptions instance.

        Raises:
            InvalidOptionsObject: If provided options is not ChromiumOptions.
        """
        if self.options is None:
            self.options = ChromiumOptions()

        if not isinstance(self.options, ChromiumOptions):
            raise InvalidOptionsObject(f'Expected ChromiumOptions, got {type(self.options)}')

        self.add_default_arguments()
        return self.options

    def add_default_arguments(self):
        """Add default arguments required for CDP integration."""
        self.options.add_argument('--no-first-run')
        self.options.add_argument('--no-default-browser-check')
