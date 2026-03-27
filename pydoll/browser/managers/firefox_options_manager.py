from __future__ import annotations

import logging
from typing import Optional

from pydoll.browser.firefox_options import FirefoxOptions
from pydoll.browser.interfaces import BrowserOptionsManager
from pydoll.exceptions import InvalidOptionsObject

logger = logging.getLogger(__name__)


class FirefoxOptionsManager(BrowserOptionsManager):
    """
    Manages browser options configuration for Firefox via WebDriver BiDi.
    """

    def __init__(self, options: Optional[FirefoxOptions] = None):
        self.options = options
        logger.debug(
            f'FirefoxOptionsManager initialized with options='
            f'{type(options).__name__ if options is not None else "None"}'
        )

    def initialize_options(self) -> FirefoxOptions:
        """
        Initialize and validate Firefox browser options.

        Returns:
            Properly configured FirefoxOptions instance.

        Raises:
            InvalidOptionsObject: If provided options is not FirefoxOptions.
        """
        if self.options is None:
            self.options = FirefoxOptions()
            logger.debug('No options provided; created default FirefoxOptions')

        if not isinstance(self.options, FirefoxOptions):
            logger.error(f'Invalid options type: {type(self.options)}; expected FirefoxOptions')
            raise InvalidOptionsObject(f'Expected FirefoxOptions, got {type(self.options)}')

        self.add_default_arguments()
        logger.debug('Options initialized and default arguments applied')
        return self.options

    def add_default_arguments(self):
        """Add default arguments required for Firefox BiDi integration."""
        logger.debug('Adding default arguments for Firefox')
        self.options.add_argument('--no-remote')
        self.options.add_argument('--new-instance')
