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

    def __init__(self, options: Optional[Options] = None, enable_fingerprint_spoofing: bool = False, fingerprint_config=None):
        self.options = options
        self.enable_fingerprint_spoofing = enable_fingerprint_spoofing
        self.fingerprint_config = fingerprint_config
        self.fingerprint_manager = None
        
        # Import fingerprint manager only if needed to avoid circular imports
        if enable_fingerprint_spoofing:
            try:
                from pydoll.fingerprint.manager import FingerprintManager
                self.fingerprint_manager = FingerprintManager(fingerprint_config)
            except ImportError:
                # Fingerprint module not available, disable spoofing
                self.enable_fingerprint_spoofing = False

    def initialize_options(
        self,
    ) -> ChromiumOptions:
        """
        Initialize and validate browser options.

        Creates ChromiumOptions if none provided, validates existing options,
        and applies default CDP arguments and fingerprint spoofing if enabled.

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
        
        # Apply fingerprint spoofing if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            self._apply_fingerprint_spoofing()
            
        return self.options

    def add_default_arguments(self):
        """Add default arguments required for CDP integration."""
        self.options.add_argument('--no-first-run')
        self.options.add_argument('--no-default-browser-check')
        
    def _apply_fingerprint_spoofing(self):
        """
        Apply fingerprint spoofing arguments to browser options.
        """
        if self.fingerprint_manager is None:
            return

        # Detect browser type from binary location or default to chrome
        browser_type = self._detect_browser_type()
        self.fingerprint_manager.generate_new_fingerprint(browser_type)

        # Get fingerprint arguments
        fingerprint_args = self.fingerprint_manager.get_fingerprint_arguments(browser_type)

        # Add fingerprint arguments to options
        for arg in fingerprint_args:
            if arg not in self.options.arguments:
                self.options.add_argument(arg)
                
    def _detect_browser_type(self) -> str:
        """
        Detect browser type from options or configuration.
        
        Returns:
            Browser type string ('chrome' or 'edge').
        """
        if self.options and self.options.binary_location:
            binary_path = self.options.binary_location.lower()
            if 'edge' in binary_path or 'msedge' in binary_path:
                return 'edge'
        return 'chrome'  # Default to chrome
                
    def get_fingerprint_manager(self):
        """
        Get the fingerprint manager instance.

        Returns:
            The fingerprint manager if fingerprint spoofing is enabled, None otherwise.
        """
        return self.fingerprint_manager
