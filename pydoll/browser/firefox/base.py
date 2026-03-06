from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from random import randint
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, overload

from pydoll.browser.firefox.tab import FirefoxTab
from pydoll.browser.managers import BrowserProcessManager, TempDirectoryManager
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.exceptions import (
    BrowserNotRunning,
    FailedToStartBrowser,
    InvalidConnectionPort,
)
from pydoll.protocol.bidi import browsing_context, script, session

if TYPE_CHECKING:
    from pydoll.browser.firefox.options import FirefoxOptions
    from pydoll.browser.interfaces import BrowserOptionsManager

logger = logging.getLogger(__name__)


class FirefoxBrowser(ABC):
    """
    Abstract base class for Firefox automation via WebDriver BiDi.

    Manages browser lifecycle (start, stop, tab creation) using the
    BiDi WebSocket protocol instead of CDP.
    """

    def __init__(
        self,
        options_manager: BrowserOptionsManager,
        connection_port: Optional[int] = None,
    ):
        """
        Initialize Firefox browser instance.

        Args:
            options_manager: Manages FirefoxOptions initialization.
            connection_port: BiDi WebSocket port. Random port (9223-9322) if None.
        """
        self._validate_connection_port(connection_port)
        self.options: FirefoxOptions = options_manager.initialize_options()
        self._connection_port = connection_port if connection_port else randint(9223, 9322)
        self._browser_process_manager = BrowserProcessManager()
        self._temp_directory_manager = TempDirectoryManager()
        self._connection_handler = BiDiConnectionHandler(self._connection_port)
        self._tabs: dict[str, FirefoxTab] = {}
        logger.debug(
            f'FirefoxBrowser initialized: port={self._connection_port}, '
            f'headless={self.options.headless}'
        )

    async def __aenter__(self) -> FirefoxBrowser:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if await self._is_browser_running(timeout=2):
            await self.stop()
        await self._connection_handler.close()

    async def start(self) -> FirefoxTab:
        """
        Start Firefox and return the initial tab.

        Returns:
            FirefoxTab ready for interaction.

        Raises:
            FailedToStartBrowser: If Firefox fails to start or connect.
        """
        binary_location = self.options.binary_location or self._get_default_binary_location()
        logger.debug(f'Resolved Firefox binary: {binary_location}')

        profile_dir = self._setup_user_dir()
        self.options.arguments.append('--profile')
        self.options.arguments.append(profile_dir)

        logger.info(f'Starting Firefox on port {self._connection_port}')
        self._browser_process_manager.start_browser_process(
            binary_location, self._connection_port, self.options.arguments
        )

        await self._verify_browser_running()
        logger.info('Firefox is running; establishing BiDi session')

        await self._connection_handler.new_session({
            'moz:firefoxOptions': {
                'prefs': {
                    'dom.webdriver.enabled': False,
                }
            }
        })
        await self._hide_automation_signals()

        response = await self._connection_handler.execute_command(browsing_context.get_tree())
        contexts = response.get('result', {}).get('contexts', [])
        if not contexts:
            raise FailedToStartBrowser('No browsing contexts found after start')

        context_id = contexts[0]['context']
        tab = FirefoxTab(context_id, self._connection_handler)
        self._tabs[context_id] = tab
        logger.info(f'Initial FirefoxTab ready: context_id={context_id}')
        return tab

    async def stop(self):
        """
        Stop the Firefox process and clean up resources.

        Raises:
            BrowserNotRunning: If the browser is not currently running.
        """
        if not await self._is_browser_running():
            raise BrowserNotRunning()

        logger.info('Stopping Firefox')
        self._browser_process_manager.stop_process()
        await self._connection_handler.close()
        await asyncio.sleep(0.1)
        self._temp_directory_manager.cleanup()
        if hasattr(self, '_profile_temp_dir'):
            self._profile_temp_dir.cleanup()
        logger.info('Firefox stopped and resources cleaned up')

    async def new_tab(self, url: str = '') -> FirefoxTab:
        """
        Open a new browser tab.

        Args:
            url: URL to navigate to (stays on about:blank if empty).

        Returns:
            New FirefoxTab instance.
        """
        logger.info('Creating new Firefox tab')
        response = await self._connection_handler.execute_command(browsing_context.create())
        context_id = response['result']['context']
        tab = FirefoxTab(context_id, self._connection_handler)
        self._tabs[context_id] = tab
        if url:
            await tab.go_to(url)
        return tab

    async def get_opened_tabs(self) -> list[FirefoxTab]:
        """
        Get all open browser tabs.

        Returns:
            List of FirefoxTab instances.
        """
        response = await self._connection_handler.execute_command(browsing_context.get_tree())
        contexts = response.get('result', {}).get('contexts', [])
        tabs = []
        for ctx in contexts:
            context_id = ctx['context']
            if context_id not in self._tabs:
                self._tabs[context_id] = FirefoxTab(context_id, self._connection_handler)
            tabs.append(self._tabs[context_id])
        return tabs

    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Awaitable[Any]],
        temporary: bool = False,
    ) -> int: ...
    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """
        Subscribe to a BiDi event at the browser level.

        Args:
            event_name: BiDi event name (e.g., 'browsingContext.load').
            callback: Function to call when event fires (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for later removal.
        """
        import asyncio

        await self._connection_handler.execute_command(session.subscribe([event_name]))

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        function_to_register = (
            callback_wrapper if asyncio.iscoroutinefunction(callback) else callback
        )
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int) -> bool:
        """Remove a registered event callback by ID."""
        return await self._connection_handler.remove_callback(callback_id)

    async def _verify_browser_running(self):
        """
        Wait until the Firefox BiDi WebSocket is responsive.

        Raises:
            FailedToStartBrowser: If Firefox doesn't respond within timeout.
        """
        if not await self._is_browser_running(self.options.start_timeout):
            logger.error('Firefox failed to start within timeout')
            raise FailedToStartBrowser()

    async def _is_browser_running(self, timeout: int = 10) -> bool:
        """Check if Firefox BiDi endpoint is responsive."""
        for _ in range(timeout):
            if await self._connection_handler.ping():
                return True
            await asyncio.sleep(1)
        return False

    async def _hide_automation_signals(self) -> None:
        """
        Inject a preload script that runs before every page load to remove
        common browser-automation fingerprints detectable by websites.
        """
        stealth_script = """() => {
  // --- navigator.webdriver ---
  // Strategy 1: delete the property from the prototype entirely (cleanest).
  // Strategy 2: if not configurable/deletable, override with a spoofed getter.
  try {
    if (Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver')?.configurable) {
      delete Navigator.prototype.webdriver;
    } else {
      throw new Error('not configurable');
    }
  } catch (_) {
    // Fallback: redefine with a getter whose toString looks native
    try {
      const webdriverGetter = () => undefined;
      try {
        webdriverGetter.toString = () => 'function get webdriver() { [native code] }';
      } catch (_) {}
      Object.defineProperty(Navigator.prototype, 'webdriver', {
        get: webdriverGetter,
        configurable: true,
        enumerable: true,
      });
    } catch (_) {}
  }
  // Also remove any own property that may have been set on the instance
  try {
    if (Object.getOwnPropertyDescriptor(navigator, 'webdriver')?.configurable) {
      delete navigator.webdriver;
    }
  } catch (_) {}

  // --- navigator.languages ---
  try {
    if (!navigator.languages || navigator.languages.length === 0) {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
        configurable: true,
      });
    }
  } catch (_) {}

  // --- navigator.plugins ---
  try {
    if (navigator.plugins.length === 0) {
      Object.defineProperty(navigator, 'plugins', {
        get: () => {
          const arr = [{ name: 'PDF Viewer', filename: 'internal-pdf-viewer' }];
          Object.setPrototypeOf(arr, PluginArray.prototype);
          return arr;
        },
        configurable: true,
      });
    }
  } catch (_) {}

  // --- navigator.mimeTypes ---
  try {
    if (!navigator.mimeTypes || navigator.mimeTypes.length === 0) {
      Object.defineProperty(navigator, 'mimeTypes', {
        get: () => {
          const arr = [{ type: 'application/pdf', suffixes: 'pdf', description: '' }];
          Object.setPrototypeOf(arr, MimeTypeArray.prototype);
          return arr;
        },
        configurable: true,
      });
    }
  } catch (_) {}

  // --- permissions.query ---
  try {
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (params) =>
      params.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(params);
  } catch (_) {}

  // --- hardwareConcurrency ---
  try {
    Object.defineProperty(navigator, 'hardwareConcurrency', {
      get: () => 4,
      configurable: true,
    });
  } catch (_) {}
}"""
        await self._connection_handler.execute_command(script.add_preload_script(stealth_script))
        logger.debug('Automation signals hidden via preload script')

    def _setup_user_dir(self) -> str:
        """
        Create a temporary Firefox profile directory with stealth preferences.

        The profile is placed under ~/.cache/pydoll/profiles/ rather than /tmp
        because snap Firefox uses a private /tmp namespace and silently ignores
        --profile paths outside $HOME.

        Returns:
            Path to the created profile directory.
        """
        import tempfile

        home_profiles = os.path.expanduser('~/.cache/pydoll/profiles')
        os.makedirs(home_profiles, exist_ok=True)
        self._profile_temp_dir = tempfile.TemporaryDirectory(dir=home_profiles)
        profile_dir = self._profile_temp_dir.name
        self._write_user_js(profile_dir)
        self._write_user_chrome_css(profile_dir)
        logger.info(f'Firefox profile directory: {profile_dir}')
        return profile_dir

    @staticmethod
    def _write_user_js(profile_dir: str) -> None:
        """Write user.js with stealth preferences to the Firefox profile."""
        prefs = [
            ('dom.webdriver.enabled', False),
            ('marionette.enabled', False),
            ('toolkit.legacyUserProfileCustomizations.stylesheets', True),
            ('devtools.debugger.prompt-connection', False),
            # Disable automation/testing-specific UI and features
            ('browser.aboutConfig.showWarning', False),
            ('browser.shell.checkDefaultBrowser', False),
            ('browser.startup.homepage_override.mstone', 'ignore'),
            # Reduce fingerprinting surface without breaking functionality
            ('privacy.resistFingerprinting', False),
            ('privacy.trackingprotection.enabled', False),
            # Suppress first-run dialogs and telemetry
            ('datareporting.healthreport.uploadEnabled', False),
            ('datareporting.policy.dataSubmissionEnabled', False),
            ('toolkit.telemetry.enabled', False),
            ('toolkit.telemetry.unified', False),
            ('browser.newtabpage.activity-stream.feeds.telemetry', False),
            ('browser.ping-centre.telemetry', False),
        ]
        lines = [f'user_pref("{key}", {str(val).lower()});\n' for key, val in prefs]
        user_js_path = os.path.join(profile_dir, 'user.js')
        with open(user_js_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.debug(f'Wrote user.js to {user_js_path}')

    @staticmethod
    def _write_user_chrome_css(profile_dir: str) -> None:
        """Write userChrome.css to hide the remote control notification bar."""
        chrome_dir = os.path.join(profile_dir, 'chrome')
        os.makedirs(chrome_dir, exist_ok=True)
        css = (
            '#remote-control-box {\n'
            '  display: none !important;\n'
            '}\n'
            '\n'
            ':root[remotecontrol] #urlbar-background {\n'
            '  background: unset !important;\n'
            '}\n'
        )
        css_path = os.path.join(chrome_dir, 'userChrome.css')
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css)
        logger.debug(f'Wrote userChrome.css to {css_path}')

    @staticmethod
    def _validate_connection_port(connection_port: Optional[int]):
        if connection_port and connection_port < 0:
            raise InvalidConnectionPort()

    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """Get default Firefox executable path (implemented by subclasses)."""
        pass
