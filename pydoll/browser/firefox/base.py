from __future__ import annotations

import asyncio
import logging
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
from pydoll.protocol.bidi import browsing_context, session

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
        self.options.arguments.append(f'--profile')
        self.options.arguments.append(profile_dir)

        logger.info(f'Starting Firefox on port {self._connection_port}')
        self._browser_process_manager.start_browser_process(
            binary_location, self._connection_port, self.options.arguments
        )

        await self._verify_browser_running()
        logger.info('Firefox is running; establishing BiDi session')

        await self._connection_handler.new_session()

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

    def _setup_user_dir(self) -> str:
        """
        Create a temporary Firefox profile directory.

        Returns:
            Path to the created profile directory.
        """
        temp_dir = self._temp_directory_manager.create_temp_dir()
        logger.debug(f'Firefox profile directory: {temp_dir.name}')
        return temp_dir.name

    @staticmethod
    def _validate_connection_port(connection_port: Optional[int]):
        if connection_port and connection_port < 0:
            raise InvalidConnectionPort()

    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """Get default Firefox executable path (implemented by subclasses)."""
        pass
