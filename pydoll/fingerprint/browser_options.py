"""
Browser options manager with fingerprint spoofing support.

This module extends the standard browser options manager to include
fingerprint spoofing capabilities.
"""

from typing import Optional

from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions

from .manager import FingerprintManager
from .models import FingerprintConfig


class FingerprintBrowserOptionsManager(ChromiumOptionsManager):
    """
    Browser options manager with fingerprint spoofing support.

    This class extends the standard ChromiumOptionsManager to automatically
    apply fingerprint spoofing arguments when enabled.
    """

    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        enable_fingerprint_spoofing: bool = False,
        fingerprint_config: Optional[FingerprintConfig] = None
    ):
        """
        Initialize the fingerprint-aware options manager.

        Args:
            options: Browser options. Creates default if None.
            enable_fingerprint_spoofing: Whether to enable fingerprint spoofing.
            fingerprint_config: Configuration for fingerprint generation.
        """
        super().__init__(options)
        self.enable_fingerprint_spoofing = enable_fingerprint_spoofing
        self.fingerprint_manager = (
            FingerprintManager(fingerprint_config)
            if enable_fingerprint_spoofing
            else None
        )

    def initialize_options(self) -> ChromiumOptions:
        """
        Initialize options with fingerprint spoofing if enabled.

        Returns:
            Configured ChromiumOptions with fingerprint arguments if enabled.
        """
        # Initialize base options
        options = super().initialize_options()

        # Apply fingerprint spoofing if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            self._apply_fingerprint_spoofing(options)

        return options

    def _apply_fingerprint_spoofing(self, options: ChromiumOptions):
        """
        Apply fingerprint spoofing arguments to browser options.

        Args:
            options: The browser options to modify.
        """
        # Only apply if fingerprint manager exists
        if self.fingerprint_manager is None:
            return

        # Generate fingerprint if not already done
        browser_type = 'chrome'  # Default, could be detected from options
        self.fingerprint_manager.generate_new_fingerprint(browser_type)

        # Get fingerprint arguments
        fingerprint_args = self.fingerprint_manager.get_fingerprint_arguments(browser_type)

        # Add fingerprint arguments to options
        for arg in fingerprint_args:
            if arg not in options.arguments:
                options.add_argument(arg)

    def get_fingerprint_manager(self) -> Optional[FingerprintManager]:
        """
        Get the fingerprint manager instance.

        Returns:
            The fingerprint manager if fingerprint spoofing is enabled, None otherwise.
        """
        return self.fingerprint_manager
