"""
Browser classes with fingerprint spoofing support.

This module provides Chrome and Edge browser classes that extend the standard
browser classes with fingerprint spoofing capabilities.
"""

from typing import Optional

from pydoll.browser.chromium.base import Browser
from pydoll.browser.chromium.chrome import Chrome as BaseChrome
from pydoll.browser.chromium.edge import Edge as BaseEdge
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.commands import PageCommands

from .browser_options import FingerprintBrowserOptionsManager
from .models import FingerprintConfig


class Chrome(Browser):
    """
    Chrome browser with fingerprint spoofing support.

    This class extends the standard Chrome browser to include automatic
    fingerprint spoofing capabilities.
    """

    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        connection_port: Optional[int] = None,
        enable_fingerprint_spoofing: bool = False,
        fingerprint_config: Optional[FingerprintConfig] = None,
    ):
        """
        Initialize Chrome browser with fingerprint spoofing support.

        Args:
            options: Chrome configuration options.
            connection_port: CDP WebSocket port.
            enable_fingerprint_spoofing: Whether to enable fingerprint spoofing.
            fingerprint_config: Configuration for fingerprint generation.
        """
        # Create fingerprint-aware options manager
        self.fingerprint_options_manager = FingerprintBrowserOptionsManager(
            options,
            enable_fingerprint_spoofing,
            fingerprint_config
        )

        # Initialize parent with fingerprint-aware options manager
        super().__init__(
            self.fingerprint_options_manager,
            connection_port
        )

        self.enable_fingerprint_spoofing = enable_fingerprint_spoofing
        self.fingerprint_manager = self.fingerprint_options_manager.get_fingerprint_manager()

        # Generate fingerprint if spoofing is enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            self.fingerprint_manager.generate_new_fingerprint('chrome')

    async def start(self, headless: bool = False) -> Tab:
        """
        Start browser with fingerprint spoofing if enabled.

        Args:
            headless: Run without UI.

        Returns:
            Initial tab for interaction.
        """
        # Start the browser normally
        tab = await super().start(headless)

        # Inject fingerprint spoofing JavaScript if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            await self._inject_fingerprint_script(tab)

        return tab

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> Tab:
        """
        Create new tab with fingerprint spoofing.

        Args:
            url: Initial URL.
            browser_context_id: Context to create tab in.

        Returns:
            New tab with fingerprint spoofing applied.
        """
        # Create new tab normally
        tab = await super().new_tab(url, browser_context_id)

        # Inject fingerprint spoofing JavaScript if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            await self._inject_fingerprint_script(tab)

        return tab

    async def _inject_fingerprint_script(self, tab: Tab):
        """
        Inject fingerprint spoofing JavaScript into a tab.

        Args:
            tab: The tab to inject the script into.
        """
        try:
            # Get the JavaScript injection code
            script = self.fingerprint_manager.get_fingerprint_js()

            # Inject the script using Page.addScriptToEvaluateOnNewDocument
            # This ensures the script runs before any page scripts
            await tab._execute_command(
                PageCommands.add_script_to_evaluate_on_new_document(script)
            )

            # Also evaluate immediately for current page if it exists
            try:
                await tab.execute_script(script)
            except Exception:
                # Ignore errors for immediate execution as page might not be ready
                pass

        except Exception as e:
            # Don't let fingerprint injection failures break the browser
            print(f"Warning: Failed to inject fingerprint spoofing script: {e}")

    def get_fingerprint_summary(self) -> Optional[dict]:
        """
        Get a summary of the current fingerprint.

        Returns:
            Dictionary with fingerprint information, or None if not enabled.
        """
        if self.fingerprint_manager:
            return self.fingerprint_manager.get_fingerprint_summary()
        return None

    @staticmethod
    def _get_default_binary_location() -> str:
        """Get default Chrome executable path."""
        return BaseChrome._get_default_binary_location()


class Edge(Browser):
    """
    Edge browser with fingerprint spoofing support.

    This class extends the standard Edge browser to include automatic
    fingerprint spoofing capabilities.
    """

    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        connection_port: Optional[int] = None,
        enable_fingerprint_spoofing: bool = False,
        fingerprint_config: Optional[FingerprintConfig] = None,
    ):
        """
        Initialize Edge browser with fingerprint spoofing support.

        Args:
            options: Edge configuration options.
            connection_port: CDP WebSocket port.
            enable_fingerprint_spoofing: Whether to enable fingerprint spoofing.
            fingerprint_config: Configuration for fingerprint generation.
        """
        # Create fingerprint-aware options manager
        self.fingerprint_options_manager = FingerprintBrowserOptionsManager(
            options,
            enable_fingerprint_spoofing,
            fingerprint_config
        )

        # Initialize parent with fingerprint-aware options manager
        super().__init__(
            self.fingerprint_options_manager,
            connection_port
        )

        self.enable_fingerprint_spoofing = enable_fingerprint_spoofing
        self.fingerprint_manager = self.fingerprint_options_manager.get_fingerprint_manager()

        # Update fingerprint manager to use Edge
        if self.fingerprint_manager:
            self.fingerprint_manager.config.browser_type = 'edge'
            # Generate fingerprint if spoofing is enabled
            if self.enable_fingerprint_spoofing:
                self.fingerprint_manager.generate_new_fingerprint('edge')

    async def start(self, headless: bool = False) -> Tab:
        """
        Start browser with fingerprint spoofing if enabled.

        Args:
            headless: Run without UI.

        Returns:
            Initial tab for interaction.
        """
        # Start the browser normally
        tab = await super().start(headless)

        # Inject fingerprint spoofing JavaScript if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            await self._inject_fingerprint_script(tab)

        return tab

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> Tab:
        """
        Create new tab with fingerprint spoofing.

        Args:
            url: Initial URL.
            browser_context_id: Context to create tab in.

        Returns:
            New tab with fingerprint spoofing applied.
        """
        # Create new tab normally
        tab = await super().new_tab(url, browser_context_id)

        # Inject fingerprint spoofing JavaScript if enabled
        if self.enable_fingerprint_spoofing and self.fingerprint_manager:
            await self._inject_fingerprint_script(tab)

        return tab

    async def _inject_fingerprint_script(self, tab: Tab):
        """
        Inject fingerprint spoofing JavaScript into a tab.

        Args:
            tab: The tab to inject the script into.
        """
        try:
            # Get the JavaScript injection code
            script = self.fingerprint_manager.get_fingerprint_js()

            # Inject the script using Page.addScriptToEvaluateOnNewDocument
            await tab._execute_command(
                PageCommands.add_script_to_evaluate_on_new_document(script)
            )

            # Also evaluate immediately for current page if it exists
            try:
                await tab.execute_script(script)
            except Exception:
                # Ignore errors for immediate execution
                pass

        except Exception as e:
            # Don't let fingerprint injection failures break the browser
            print(f"Warning: Failed to inject fingerprint spoofing script: {e}")

    def get_fingerprint_summary(self) -> Optional[dict]:
        """
        Get a summary of the current fingerprint.

        Returns:
            Dictionary with fingerprint information, or None if not enabled.
        """
        if self.fingerprint_manager:
            return self.fingerprint_manager.get_fingerprint_summary()
        return None

    @staticmethod
    def _get_default_binary_location() -> str:
        """Get default Edge executable path."""
        return BaseEdge._get_default_binary_location()
