from __future__ import annotations

import asyncio
import logging
import os
from random import randint
from typing import TYPE_CHECKING, Optional, overload

from pydoll.browser.managers import (
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from pydoll.commands.bidi.browser_commands import BrowserCommands
from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.session_commands import SessionCommands
from pydoll.commands.bidi.storage_commands import StorageCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.exceptions import BrowserNotRunning, UnsupportedOperation
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browser.types import ClientWindowInfo
from pydoll.protocol.types import (
    BrowserVersion,
    Cookie,
    CookieParam,
    DownloadBehavior,
    WindowBounds,
)

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable

    from pydoll.browser.protocols import BrowserOptionsManagerProtocol

logger = logging.getLogger(__name__)


class FirefoxBrowser:
    """Firefox browser automation via WebDriver BiDi protocol."""

    def __init__(
        self,
        options_manager: BrowserOptionsManagerProtocol,
        connection_port: Optional[int] = None,
    ):
        self._validate_connection_port(connection_port)
        self.options = options_manager.initialize_options()
        self._proxy_manager = ProxyManager(self.options)
        self._connection_port = connection_port or randint(9223, 9322)
        self._browser_process_manager = BrowserProcessManager()
        self._temp_directory_manager = TempDirectoryManager()
        self._connection_handler = BiDiConnectionHandler(
            connection_port=self._connection_port,
        )
        self._session_id: Optional[str] = None

    async def __aenter__(self) -> FirefoxBrowser:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if await self._is_browser_running(timeout=2):
            await self.stop()
        await self._connection_handler.close()

    async def start(self, headless: bool = False):
        """Start Firefox and establish BiDi session."""
        if headless:
            self.options.headless = headless

        binary_location = (
            self.options.binary_location or self._get_default_binary_location()
        )
        temp_dir = self._temp_directory_manager.create_temp_dir()

        self._browser_process_manager.start_browser_process(
            binary_location,
            self._connection_port,
            [*self.options.arguments, '--profile', temp_dir.name],
        )
        await self._verify_browser_running()

        response = await self._execute_command(SessionCommands.new())
        self._session_id = response['result']['sessionId']
        logger.info(f'BiDi session established: {self._session_id}')

    async def stop(self):
        """Stop Firefox and cleanup resources."""
        if not await self._is_browser_running():
            raise BrowserNotRunning()

        if self._session_id:
            await self._execute_command(SessionCommands.end())
            self._session_id = None

        self._browser_process_manager.stop_process()
        await self._connection_handler.close()
        await asyncio.sleep(0.5 if os.name == 'nt' else 0.1)
        self._temp_directory_manager.cleanup()

    async def close(self):
        """Close the WebSocket connection."""
        await self._connection_handler.close()

    async def connect(self, ws_address: str):
        """Connect to an already running Firefox instance."""
        self._connection_handler._ws_address = ws_address
        await self._connection_handler._ensure_active_connection()
        response = await self._execute_command(SessionCommands.new())
        self._session_id = response['result']['sessionId']

    async def create_browser_context(
        self,
        proxy_server: Optional[str] = None,
        proxy_bypass_list: Optional[str] = None,
    ) -> str:
        """Create isolated browser context (BiDi UserContext).

        Args:
            proxy_server: Proxy for this context (scheme://host:port).
            proxy_bypass_list: Not supported in BiDi, ignored.

        Returns:
            Context ID (UserContext ID).
        """
        proxy = None
        if proxy_server:
            proxy = {
                'proxyType': 'manual',
                'httpProxy': proxy_server,
                'sslProxy': proxy_server,
            }

        response = await self._execute_command(
            BrowserCommands.create_user_context(proxy=proxy)
        )
        context_id: str = response['result']['userContext']
        logger.info(f'Created browser context: {context_id}')
        return context_id

    async def delete_browser_context(self, browser_context_id: str):
        """Delete browser context (BiDi UserContext)."""
        logger.info(f'Deleting browser context: {browser_context_id}')
        await self._execute_command(
            BrowserCommands.remove_user_context(browser_context_id)
        )

    async def get_browser_contexts(self) -> list[str]:
        """Get all browser context IDs."""
        response = await self._execute_command(
            BrowserCommands.get_user_contexts()
        )
        return [ctx['userContext'] for ctx in response['result']['userContexts']]

    async def get_opened_tabs(self):
        """Get all open tabs. Requires BiDi Tab implementation."""
        raise NotImplementedError('BiDi Tab not yet implemented.')

    async def get_version(self) -> BrowserVersion:
        """Get browser version information."""
        response = await self._execute_command(SessionCommands.new())
        caps = response['result'].get('capabilities', {})
        return BrowserVersion(
            browserName=caps.get('browserName', ''),
            browserVersion=caps.get('browserVersion', ''),
            userAgent=caps.get('userAgent', ''),
        )

    async def set_download_path(
        self, path: str, browser_context_id: Optional[str] = None
    ):
        """Set download directory path."""
        await self.set_download_behavior(
            DownloadBehavior.ALLOW, path, browser_context_id
        )

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ):
        """Configure download handling.

        Args:
            behavior: ALLOW or DENY.
            download_path: Required if behavior is ALLOW.
            browser_context_id: Context to apply to.
        """
        if behavior == DownloadBehavior.ALLOW and download_path:
            bidi_behavior = {
                'type': 'allowed',
                'destinationFolder': download_path,
            }
        else:
            bidi_behavior = {'type': 'denied'}

        user_contexts = [browser_context_id] if browser_context_id else None
        await self._execute_command(
            BrowserCommands.set_download_behavior(
                download_behavior=bidi_behavior,
                user_contexts=user_contexts,
            )
        )

    async def delete_all_cookies(
        self, browser_context_id: Optional[str] = None
    ):
        """Delete all cookies."""
        partition = None
        if browser_context_id:
            partition = {
                'type': 'storageKey',
                'userContext': browser_context_id,
            }
        await self._execute_command(
            StorageCommands.delete_cookies(partition=partition)
        )

    async def set_cookies(
        self,
        cookies: list[CookieParam],
        browser_context_id: Optional[str] = None,
    ):
        """Set cookies."""
        partition = None
        if browser_context_id:
            partition = {
                'type': 'storageKey',
                'userContext': browser_context_id,
            }
        for cookie in cookies:
            bidi_cookie = {
                'name': cookie['name'],
                'value': {'type': 'string', 'value': cookie['value']},
                'domain': cookie['domain'],
            }
            if 'path' in cookie:
                bidi_cookie['path'] = cookie['path']
            if 'httpOnly' in cookie:
                bidi_cookie['httpOnly'] = cookie['httpOnly']
            if 'secure' in cookie:
                bidi_cookie['secure'] = cookie['secure']
            if 'sameSite' in cookie:
                bidi_cookie['sameSite'] = cookie['sameSite'].lower()
            if 'expiry' in cookie:
                bidi_cookie['expiry'] = cookie['expiry']
            await self._execute_command(
                StorageCommands.set_cookie(cookie=bidi_cookie, partition=partition)
            )

    async def get_cookies(
        self, browser_context_id: Optional[str] = None
    ) -> list[Cookie]:
        """Get all cookies."""
        partition = None
        if browser_context_id:
            partition = {
                'type': 'storageKey',
                'userContext': browser_context_id,
            }
        response = await self._execute_command(
            StorageCommands.get_cookies(partition=partition)
        )
        bidi_cookies = response['result']['cookies']
        return [
            Cookie(
                name=c['name'],
                value=c['value'].get('value', '') if isinstance(c['value'], dict) else c['value'],
                domain=c['domain'],
                path=c['path'],
                size=c.get('size', 0),
                httpOnly=c['httpOnly'],
                secure=c['secure'],
                sameSite=c['sameSite'],
                **({'expiry': c['expiry']} if 'expiry' in c else {}),
            )
            for c in bidi_cookies
        ]

    async def set_window_maximized(self):
        """Maximize browser window."""
        windows = await self._get_client_windows()
        if windows:
            await self._execute_command(
                BrowserCommands.set_client_window_state(
                    client_window=windows[0]['clientWindow'],
                    state='maximized',
                )
            )

    async def set_window_minimized(self):
        """Minimize browser window."""
        windows = await self._get_client_windows()
        if windows:
            await self._execute_command(
                BrowserCommands.set_client_window_state(
                    client_window=windows[0]['clientWindow'],
                    state='minimized',
                )
            )

    async def set_window_bounds(self, bounds: WindowBounds):
        """Set window position and/or size.

        Args:
            bounds: WindowBounds with optional keys: width, height, x, y.
        """
        windows = await self._get_client_windows()
        if windows:
            await self._execute_command(
                BrowserCommands.set_client_window_state(
                    client_window=windows[0]['clientWindow'],
                    state='normal',
                    **bounds,
                )
            )

    async def get_window_id_for_tab(self, tab) -> str:
        """Get the client window ID for a tab's context."""
        contexts = await self.get_opened_tabs()
        for ctx in contexts:
            if ctx.get('clientWindow'):
                return ctx['clientWindow']
        raise UnsupportedOperation('No client window found.')

    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Any],
        temporary: bool = False,
    ) -> int: ...

    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Awaitable[Any]],
        temporary: bool = False,
    ) -> int: ...

    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """Register event listener.

        Args:
            event_name: BiDi event name (e.g. 'browsingContext.load').
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.
        """
        await self._execute_command(
            SessionCommands.subscribe(events=[event_name])
        )

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove registered event callback."""
        await self._connection_handler.remove_callback(callback_id)

    async def grant_permissions(self, permissions, origin=None, browser_context_id=None):
        """Not yet supported in BiDi."""
        raise UnsupportedOperation('grant_permissions is not yet supported in BiDi.')

    async def reset_permissions(self, browser_context_id=None):
        """Not yet supported in BiDi."""
        raise UnsupportedOperation('reset_permissions is not yet supported in BiDi.')

    async def _execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Execute a BiDi command and return typed result."""
        return await self._connection_handler.execute_command(command, timeout)

    async def _get_client_windows(self) -> list[ClientWindowInfo]:
        """Get all client windows."""
        response = await self._execute_command(
            BrowserCommands.get_client_windows()
        )
        return response['result']['clientWindows']

    async def _is_browser_running(self, timeout: int = 5) -> bool:
        """Check if browser is alive and WebSocket is responsive."""
        if not self._browser_process_manager._process:
            return False
        return await self._connection_handler.ping()

    async def _verify_browser_running(self):
        """Wait until browser is responsive."""
        timeout = self.options.start_timeout
        for _ in range(timeout * 2):
            if await self._is_browser_running():
                return
            await asyncio.sleep(0.5)
        raise BrowserNotRunning(f'Firefox did not start within {timeout}s')

    @staticmethod
    def _get_default_binary_location() -> str:
        raise NotImplementedError

    @staticmethod
    def _validate_connection_port(connection_port: Optional[int]):
        if connection_port is not None and (
            not isinstance(connection_port, int) or connection_port < 0
        ):
            raise ValueError(f'Invalid connection port: {connection_port}')
