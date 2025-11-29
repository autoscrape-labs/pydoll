from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pydoll.browser.interfaces import BrowserOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.exceptions import InvalidOptionsObject

if TYPE_CHECKING:
    from pydoll.browser.options import Options

logger = logging.getLogger(__name__)


class ChromiumOptionsManager(BrowserOptionsManager):
    """
    Manages browser options configuration for Chromium-based browsers.

    Handles options creation, validation, and applies default CDP arguments
    for Chrome and Edge browsers.
    """

    def __init__(self, options: Optional[Options] = None):
        self.options = options
        logger.debug(
            f'ChromiumOptionsManager initialized with options='
            f'{type(options).__name__ if options is not None else "None"}'
        )

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
            logger.debug('No options provided; created default ChromiumOptions')

        if not isinstance(self.options, ChromiumOptions):
            logger.error(f'Invalid options type: {type(self.options)}; expected ChromiumOptions')
            raise InvalidOptionsObject(f'Expected ChromiumOptions, got {type(self.options)}')

        self.add_default_arguments()
        logger.debug('Options initialized and default arguments applied')
        return self.options

    def add_default_arguments(self):
        """Add default arguments required for CDP integration."""
        logger.debug('Adding default arguments for Chromium-based browsers')
        self.options.add_argument('--no-first-run')
        self.options.add_argument('--no-default-browser-check')
