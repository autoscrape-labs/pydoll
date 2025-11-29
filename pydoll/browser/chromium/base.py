from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import warnings
from abc import ABC, abstractmethod
from contextlib import suppress
from functools import partial
from random import randint
from tempfile import TemporaryDirectory
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Optional,
    overload,
)
from urllib.parse import urlsplit, urlunsplit

from pydoll.browser.managers import (
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from pydoll.browser.tab import Tab
from pydoll.commands import (
    BrowserCommands,
    FetchCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import (
    BrowserNotRunning,
    FailedToStartBrowser,
    InvalidConnectionPort,
    InvalidWebSocketAddress,
    MissingTargetOrWebSocket,
    NoValidTabFound,
    RunInParallelError,
)
from pydoll.protocol.browser.types import DownloadBehavior
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType

if TYPE_CHECKING:  # pragma: no cover
    from tempfile import TemporaryDirectory

    from pydoll.browser.interfaces import BrowserOptionsManager
    from pydoll.protocol.base import (
        Command,
        Response,
        T_CommandParams,
        T_CommandResponse,
    )
    from pydoll.protocol.browser.methods import (
        GetVersionResponse,
        GetVersionResult,
        GetWindowForTargetResponse,
    )
    from pydoll.protocol.browser.types import Bounds, PermissionType
    from pydoll.protocol.fetch.events import RequestPausedEvent
    from pydoll.protocol.fetch.types import HeaderEntry
    from pydoll.protocol.network.types import (
        Cookie,
        CookieParam,
        ErrorReason,
        RequestMethod,
        ResourceType,
    )
    from pydoll.protocol.storage.methods import GetCookiesResponse
    from pydoll.protocol.target.methods import (
        CreateBrowserContextResponse,
        CreateTargetResponse,
        GetBrowserContextsResponse,
        GetTargetsResponse,
    )
    from pydoll.protocol.target.types import TargetInfo

logger = logging.getLogger(__name__)


class Browser(ABC):  # noqa: PLR0904
    """
    Abstract base class for browser automation using Chrome DevTools Protocol.

    Provides comprehensive browser control including lifecycle management,
    context handling, network interception, cookie management, and CDP commands.
    """

    def __init__(
        self,
        options_manager: BrowserOptionsManager,
        connection_port: Optional[int] = None,
    ):
        """
        Initialize browser instance with configuration.

        Args:
            options_manager: Manages browser options initialization and defaults.
                Must implement initialize_options() and add_default_arguments().
            connection_port: CDP WebSocket port. Random port (9223-9322) if None.

        Note:
            Call start() to actually launch the browser.
        """
        self._validate_connection_port(connection_port)
        self.options = options_manager.initialize_options()
        self._proxy_manager = ProxyManager(self.options)
        self._connection_port = connection_port if connection_port else randint(9223, 9322)
        self._browser_process_manager = BrowserProcessManager()
        self._temp_directory_manager = TempDirectoryManager()
        self._ws_address: Optional[str] = None
        self._connection_handler = ConnectionHandler(self._connection_port)
        self._backup_preferences_dir = ''
        self._tabs_opened: dict[str, Tab] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._semaphore_lock: Optional[asyncio.Lock] = None
        self._context_proxy_auth: dict[str, tuple[str, str]] = {}
        logger.debug(
            f'Browser initialized: port={self._connection_port}, '
            f'headless={getattr(self.options, "headless", None)}'
        )

    async def __aenter__(self) -> 'Browser':
        """Async context manager entry."""
        logger.debug('Entering browser async context')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        logger.debug(f'Exiting browser async context: exc_type={exc_type}')
        if self._backup_preferences_dir:
            logger.debug(f'Restoring backup preferences directory: {self._backup_preferences_dir}')
            user_data_dir = self._get_user_data_dir()
            shutil.copy2(
                self._backup_preferences_dir,
                os.path.join(user_data_dir, 'Default', 'Preferences'),
            )
        if await self._is_browser_running(timeout=2):
            await self.stop()

        await self._connection_handler.close()

    async def connect(self, ws_address: str) -> Tab:
        """
        Connect to browser using WebSocket address. When we set
        the _ws_address attribute, the connection handler will use
        this address instead of resolving it from the connection port.

        Args:
            ws_address: WebSocket address of the browser.

        Returns:
            The first tab in the list of opened tabs.

        Note:
            You are supposed to use this method only if you want to connect to a browser
            that is already running.
        """
        logger.info(f'Connecting to browser via WebSocket: {ws_address}')
        await self._setup_ws_address(ws_address)
        tabs = await self.get_opened_tabs()
        logger.info(f'Connected. Tabs available: {len(tabs)}')
        return tabs[0]

    async def start(self, headless: bool = False) -> Tab:
        """
        Start browser process and establish CDP connection.

        Args:
            headless: Deprecated. Use `options.headless = True` instead.

        Returns:
            Initial tab for interaction.

        Raises:
            FailedToStartBrowser: If the browser fails to start or connect.
        """
        self._loop = asyncio.get_running_loop()
        if headless:
            warnings.warn(
                "The 'headless' parameter is deprecated and will be removed in a future version. "
                'Use `options.headless = True` instead.',
                DeprecationWarning,
                stacklevel=2,
            )
            self.options.headless = headless

        binary_location = self.options.binary_location or self._get_default_binary_location()
        logger.debug('Resolved binary location: %s', binary_location)

        self._setup_user_dir()
        logger.debug('User data directory configured')
        proxy_config = self._proxy_manager.get_proxy_credentials()

        logger.info(f'Starting browser process on port {self._connection_port}')
        self._browser_process_manager.start_browser_process(
            binary_location, self._connection_port, self.options.arguments
        )
        await self._verify_browser_running()
        logger.info('Browser process started and responsive')
        await self._configure_proxy(proxy_config[0], proxy_config[1])

        valid_tab_id = await self._get_valid_tab_id(await self.get_targets())
        tab = Tab(self, target_id=valid_tab_id, connection_port=self._connection_port)
        self._tabs_opened[valid_tab_id] = tab
        logger.info(f'Initial tab attached: {valid_tab_id}')
        return tab

    async def stop(self):
        """
        Stop browser process and cleanup resources.

        Sends Browser.close command, terminates process, removes temp directories,
        and closes WebSocket connections.

        Raises:
            BrowserNotRunning: If the browser is not currently running.
        """
        if not await self._is_browser_running():
            logger.error('Stop called but browser is not running')
            raise BrowserNotRunning()

        logger.info('Stopping browser process')
        await self._execute_command(BrowserCommands.close())
        self._browser_process_manager.stop_process()
        await self._connection_handler.close()
        await asyncio.sleep(0.5 if os.name == 'nt' else 0.1)
        self._temp_directory_manager.cleanup()
        logger.info('Browser process stopped and resources cleaned up')

    async def close(self):
        """
        Closes the WebSocket connection and releases resources.
        """
        logger.info('Closing browser WebSocket connection')
        await self._connection_handler.close()

    async def create_browser_context(
        self, proxy_server: Optional[str] = None, proxy_bypass_list: Optional[str] = None
    ) -> str:
        """
        Create isolated browser context (like incognito).

        Browser contexts provide isolated storage and don't share session data.
        Multiple contexts can exist simultaneously.

        Args:
            proxy_server: Optional proxy for this context only (scheme://host:port).
            proxy_bypass_list: Comma-separated hosts that bypass proxy.

        Returns:
            Browser context ID for use with other methods.
        """
        # If proxy_server contains credentials, strip them and store per-context auth
        sanitized_proxy = proxy_server
        extracted_auth: Optional[tuple[str, str]] = None
        if proxy_server:
            sanitized_proxy, extracted_auth = self._sanitize_proxy_and_extract_auth(proxy_server)
            logger.debug(
                f'Creating browser context with proxy: {sanitized_proxy}'
                f'(credentials provided={bool(extracted_auth)})'
            )

        response: CreateBrowserContextResponse = await self._execute_command(
            TargetCommands.create_browser_context(
                proxy_server=sanitized_proxy,
                proxy_bypass_list=proxy_bypass_list,
            )
        )
        context_id = response['result']['browserContextId']
        if extracted_auth:
            self._context_proxy_auth[context_id] = extracted_auth
        logger.info(f'Created browser context: {context_id}')
        return context_id

    async def delete_browser_context(self, browser_context_id: str):
        """
        Delete browser context and all associated tabs/resources.

        Removes all storage (cookies, localStorage, etc.) and closes all tabs.
        The default browser context cannot be deleted.

        Note:
            Closes all associated tabs immediately.
        """
        logger.info(f'Deleting browser context: {browser_context_id}')
        return await self._execute_command(
            TargetCommands.dispose_browser_context(browser_context_id)
        )

    async def get_browser_contexts(self) -> list[str]:
        """Get all browser context IDs including the default context."""
        response: GetBrowserContextsResponse = await self._execute_command(
            TargetCommands.get_browser_contexts()
        )
        logger.debug(f'Fetched {len(response["result"]["browserContextIds"])} browser contexts')
        return response['result']['browserContextIds']

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> Tab:
        """
        Create new tab for page interaction.

        Args:
            url: Initial URL (about:blank if empty).
            browser_context_id: Context to create tab in (default if None).

        Returns:
            Tab instance for page navigation and element interaction.
        """
        logger.info(f'Creating new tab (context={browser_context_id})')
        response: CreateTargetResponse = await self._execute_command(
            TargetCommands.create_target(
                browser_context_id=browser_context_id,
            )
        )
        target_id = response['result']['targetId']
        tab = Tab(self, **self._get_tab_kwargs(target_id, browser_context_id))
        self._tabs_opened[target_id] = tab
        await self._setup_context_proxy_auth_for_tab(tab, browser_context_id)
        if url:
            await tab.go_to(url)
        logger.info(f'New tab created: {target_id}')
        return tab

    async def get_targets(self) -> list[TargetInfo]:
        """
        Get all active targets/pages in browser.

        Targets include pages, service workers, shared workers, and browser process.
        Useful for debugging and managing multiple tabs.

        Returns:
            List of TargetInfo objects.
        """
        response: GetTargetsResponse = await self._execute_command(TargetCommands.get_targets())
        logger.debug(f'Fetched {len(response["result"]["targetInfos"])} targets')
        return response['result']['targetInfos']

    async def get_opened_tabs(self) -> list[Tab]:
        """
        Get all opened tabs that are not extensions and have the type 'page'.
        Tabs that are already opened will be returned as is. If a new target is opened,
        a new Tab instance will be created.

        Returns:
            List of Tab instances. The last tab is the most recent one.
        """
        targets = await self.get_targets()
        valid_tab_targets = [
            target
            for target in targets
            if target['type'] == 'page' and 'extension' not in target['url']
        ]
        all_target_ids = [target['targetId'] for target in valid_tab_targets]
        existing_target_ids = list(self._tabs_opened.keys())
        remaining_target_ids = [
            target_id for target_id in all_target_ids if target_id not in existing_target_ids
        ]
        existing_tabs = [self._tabs_opened[target_id] for target_id in existing_target_ids]
        new_tabs = [
            Tab(self, **self._get_tab_kwargs(target_id))
            for target_id in reversed(remaining_target_ids)
        ]
        self._tabs_opened.update(dict(zip(remaining_target_ids, new_tabs)))
        logger.debug(
            f'Opened tabs resolved: existing={len(existing_tabs)}, new={len(new_tabs)}',
        )
        return existing_tabs + new_tabs

    async def set_download_path(self, path: str, browser_context_id: Optional[str] = None):
        """Set download directory path (convenience method for set_download_behavior)."""
        logger.info(f'Setting download path: {path} (context={browser_context_id})')
        return await self._execute_command(
            BrowserCommands.set_download_behavior(
                behavior=DownloadBehavior.ALLOW,
                download_path=path,
                browser_context_id=browser_context_id,
            )
        )

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        events_enabled: bool = False,
    ):
        """
        Configure download handling.

        Args:
            behavior: ALLOW (save to path), DENY (cancel), or DEFAULT.
            download_path: Required if behavior is ALLOW.
            browser_context_id: Context to apply to (default if None).
            events_enabled: Generate download events for progress tracking.
        """
        logger.info(
            f'Setting download behavior: behavior={behavior},'
            f'path={download_path}, context={browser_context_id},'
            f'events={events_enabled}'
        )
        return await self._execute_command(
            BrowserCommands.set_download_behavior(
                behavior=behavior,
                download_path=download_path,
                browser_context_id=browser_context_id,
                events_enabled=events_enabled,
            )
        )

    async def delete_all_cookies(self, browser_context_id: Optional[str] = None):
        """Delete all cookies (session, persistent, third-party) from browser or context."""
        logger.info(f'Clearing all cookies (context={browser_context_id})')
        return await self._execute_command(StorageCommands.clear_cookies(browser_context_id))

    async def set_cookies(
        self, cookies: list[CookieParam], browser_context_id: Optional[str] = None
    ):
        """Set multiple cookies in browser or context."""
        logger.debug(f'Setting {len(cookies)} cookies (context={browser_context_id})')
        return await self._execute_command(StorageCommands.set_cookies(cookies, browser_context_id))

    async def get_cookies(self, browser_context_id: Optional[str] = None) -> list[Cookie]:
        """Get all cookies from browser or context."""
        response: GetCookiesResponse = await self._execute_command(
            StorageCommands.get_cookies(browser_context_id)
        )
        logger.debug(
            f'Retrieved {len(response["result"]["cookies"])} cookies (context={browser_context_id})'
        )
        return response['result']['cookies']

    async def get_version(self) -> GetVersionResult:
        """Get browser version and CDP protocol information."""
        response: GetVersionResponse = await self._execute_command(BrowserCommands.get_version())
        logger.debug(f'Browser version: {response["result"]}')
        return response['result']

    async def get_window_id_for_target(self, target_id: str) -> int:
        """Get window ID for target (used for window manipulation via CDP)."""
        response: GetWindowForTargetResponse = await self._execute_command(
            BrowserCommands.get_window_for_target(target_id)
        )
        logger.debug(f'Window id for target {target_id}: {response["result"]["windowId"]}')
        return response['result']['windowId']

    async def get_window_id_for_tab(self, tab: Tab) -> int:
        """Get window ID for tab (convenience method)."""
        target_id = tab._target_id or (tab._ws_address.split('/')[-1] if tab._ws_address else None)
        if not target_id:
            logger.error('Missing target id or ws address for tab when getting window id')
            raise MissingTargetOrWebSocket()
        return await self.get_window_id_for_target(target_id)

    async def get_window_id(self) -> int:
        """
        Get window ID for any valid tab.

        Raises:
            NoValidTabFound: If no valid attached tab can be found.
        """
        targets = await self.get_targets()
        valid_tab_id = await self._get_valid_tab_id(targets)
        return await self.get_window_id_for_target(valid_tab_id)

    async def set_window_maximized(self):
        """Maximize browser window (affects all tabs in window)."""
        window_id = await self.get_window_id()
        logger.info(f'Maximizing window: id={window_id}')
        return await self._execute_command(BrowserCommands.set_window_maximized(window_id))

    async def set_window_minimized(self):
        """Minimize browser window to taskbar/dock."""
        window_id = await self.get_window_id()
        logger.info(f'Minimizing window: id={window_id}')
        return await self._execute_command(BrowserCommands.set_window_minimized(window_id))

    async def set_window_bounds(self, bounds: Bounds):
        """
        Set window position and/or size.

        Args:
            bounds: Properties to modify (left, top, width, height, windowState).
                Only specified properties are changed.
        """
        window_id = await self.get_window_id()
        logger.info(f'Setting window bounds: id={window_id}, bounds={bounds}')
        return await self._execute_command(BrowserCommands.set_window_bounds(window_id, bounds))

    async def grant_permissions(
        self,
        permissions: list[PermissionType],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ):
        """
        Grant browser permissions (geolocation, notifications, camera, etc.).

        Bypasses normal permission prompts for automated testing.

        Args:
            permissions: Permissions to grant.
            origin: Origin to grant to (all origins if None).
            browser_context_id: Context to apply to (default if None).
        """
        logger.info(
            f'Granting permissions: {permissions} (origin={origin}, context={browser_context_id})',
        )
        return await self._execute_command(
            BrowserCommands.grant_permissions(permissions, origin, browser_context_id)
        )

    async def reset_permissions(self, browser_context_id: Optional[str] = None):
        """Reset all permissions to defaults and restore prompting behavior."""
        logger.info(f'Resetting permissions (context={browser_context_id})')
        return await self._execute_command(BrowserCommands.reset_permissions(browser_context_id))

    async def run_in_parallel(self, *coroutines: Coroutine[Any, Any, Any]) -> list[Any]:
        """
        Run coroutines in parallel with optional concurrency limiting.

        Args:
            *coroutines: Variable number of coroutines to execute in parallel.

        Returns:
            List of results from all coroutines in the same order as input.

        Raises:
            RuntimeError: If browser loop is not initialized or not running.

        Note:
            Respects max_parallel_tasks option for concurrency control.
        """
        if self._loop is None:
            raise RuntimeError('Browser loop not initialized. Call start() first.')

        # Thread-safe semaphore initialization with double-checked locking pattern
        if self.options.max_parallel_tasks and self._semaphore is None:
            if self._semaphore_lock is None:
                self._semaphore_lock = asyncio.Lock()

            async with self._semaphore_lock:
                # Double-check pattern to avoid creating multiple semaphores
                if self._semaphore is None:
                    self._semaphore = asyncio.Semaphore(self.options.max_parallel_tasks)

        wrapped = [self._limited_coroutine(coro) for coro in coroutines]

        async def run_gather():
            return await asyncio.gather(*wrapped, return_exceptions=False)

        # Check if we're in the same event loop
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop - this shouldn't happen in an async function
            # but if it does, use threadsafe execution
            current_loop = None

        if current_loop is self._loop:
            # Same loop - execute directly
            return await run_gather()

        # Different loop - use threadsafe execution
        if not self._loop.is_running():
            raise RunInParallelError('Browser loop is not running. Cannot execute coroutines.')

        future = asyncio.run_coroutine_threadsafe(run_gather(), self._loop)

        try:
            # Wait for result - no timeout to allow long-running operations
            return future.result()
        except Exception as e:
            raise RunInParallelError(f'Coroutine execution failed: {e}') from e

    async def _limited_coroutine(self, coroutine: Coroutine[Any, Any, Any]) -> Any:
        """
        Execute coroutine with semaphore limiting if configured.

        Args:
            coroutine: The coroutine to execute.

        Returns:
            The result of the coroutine execution.
        """
        if self.options.max_parallel_tasks and self._semaphore is not None:
            async with self._semaphore:
                return await coroutine
        return await coroutine

    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Awaitable[Any]], temporary: bool = False
    ) -> int: ...
    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """
        Register CDP event listener at browser level.

        Callback runs in background task to prevent blocking. Affects all pages/targets.

        Args:
            event_name: CDP event name (e.g., "Network.responseReceived").
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Note:
            For page-specific events, use Tab.on() instead.
        """

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback
        logger.debug(
            f'Registering callback: event={event_name}, temporary={temporary}, '
            f'async={asyncio.iscoroutinefunction(callback)}'
        )
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove callback from browser."""
        logger.debug(f'Removing callback: id={callback_id}')
        return await self._connection_handler.remove_callback(callback_id)

    async def enable_fetch_events(
        self,
        handle_auth_requests: bool = False,
        resource_type: Optional[ResourceType] = None,
    ):
        """
        Enable network request interception via Fetch domain.

        Allows monitoring, modifying, or blocking requests before they're sent.
        All matching requests are paused until explicitly continued.

        Args:
            handle_auth_requests: Intercept authentication challenges.
            resource_type: Filter by type (XHR, Fetch, Document, etc.). Empty = all.

        Note:
            Paused requests must be continued or they will timeout.
        """
        logger.debug(
            f'Enabling Fetch events: handle_auth={handle_auth_requests}, '
            f'resource_type={resource_type}'
        )
        return await self._connection_handler.execute_command(
            FetchCommands.enable(
                handle_auth_requests=handle_auth_requests,
                resource_type=resource_type,
            )
        )

    async def disable_fetch_events(self):
        """Disable request interception and release any paused requests."""
        logger.debug('Disabling Fetch events')
        return await self._connection_handler.execute_command(FetchCommands.disable())

    async def enable_runtime_events(self):
        """Enable runtime events."""
        logger.debug('Enabling Runtime events')
        return await self._connection_handler.execute_command(RuntimeCommands.enable())

    async def disable_runtime_events(self):
        """Disable runtime events."""
        logger.debug('Disabling Runtime events')
        return await self._connection_handler.execute_command(RuntimeCommands.disable())

    async def continue_request(
        self,
        request_id: str,
        url: Optional[str] = None,
        method: Optional[RequestMethod] = None,
        post_data: Optional[str] = None,
        headers: Optional[list[HeaderEntry]] = None,
        intercept_response: Optional[bool] = None,
    ):
        """
        Continue paused request without modifications.
        """
        logger.debug(f'Continuing request: id={request_id}')
        return await self._execute_command(
            FetchCommands.continue_request(
                request_id=request_id,
                url=url,
                method=method,
                post_data=post_data,
                headers=headers,
                intercept_response=intercept_response,
            )
        )

    async def fail_request(self, request_id: str, error_reason: ErrorReason):
        """Fail request with error code."""
        logger.debug(f'Failing request: id={request_id}, reason={error_reason}')
        return await self._execute_command(FetchCommands.fail_request(request_id, error_reason))

    async def fulfill_request(
        self,
        request_id: str,
        response_code: int,
        response_headers: Optional[list[HeaderEntry]] = None,
        body: Optional[str] = None,
        response_phrase: Optional[str] = None,
    ):
        """Fulfill request with response data."""
        logger.debug(
            f'Fulfilling request: id={request_id}, code={response_code}, '
            f'headers={bool(response_headers)}, body={bool(body)}'
        )
        return await self._execute_command(
            FetchCommands.fulfill_request(
                request_id=request_id,
                response_code=response_code,
                response_headers=response_headers,
                body=body,
                response_phrase=response_phrase,
            )
        )

    @staticmethod
    def _validate_connection_port(connection_port: Optional[int]):
        """Validate connection port."""
        if connection_port and connection_port < 0:
            logger.error(f'Invalid connection port: {connection_port}')
            raise InvalidConnectionPort()

    async def _continue_request_callback(self, event: RequestPausedEvent):
        """Internal callback to continue paused requests."""
        request_id = event['params']['requestId']
        logger.debug(f'[Fetch] REQUEST_PAUSED -> continue: id={request_id}')
        return await self.continue_request(request_id)

    async def _continue_request_with_auth_callback(
        self,
        event: RequestPausedEvent,
        proxy_username: Optional[str],
        proxy_password: Optional[str],
    ):
        """Internal callback for proxy authentication."""
        request_id = event['params']['requestId']
        logger.debug(
            f'[Fetch] AUTH_REQUIRED -> provide credentials: id={request_id}, '
            f'user_set={bool(proxy_username)}'
        )
        response: Response = await self._execute_command(
            FetchCommands.continue_request_with_auth(
                request_id,
                auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )
        await self.disable_fetch_events()
        return response

    @staticmethod
    async def _tab_continue_request_callback(event: RequestPausedEvent, tab: Tab):
        """Internal callback to continue paused requests at Tab level."""
        request_id = event['params']['requestId']
        logger.debug(f'[Tab Fetch] REQUEST_PAUSED -> continue: id={request_id}')
        return await tab.continue_request(request_id)

    @staticmethod
    async def _tab_continue_request_with_auth_callback(
        event: RequestPausedEvent,
        tab: Tab,
        proxy_username: Optional[str],
        proxy_password: Optional[str],
    ):
        """Internal callback for proxy/server authentication at Tab level."""
        request_id = event['params']['requestId']
        logger.debug(
            f'[Tab Fetch] AUTH_REQUIRED -> provide credentials: id={request_id}, '
            f'user_set={bool(proxy_username)}'
        )
        response: Response = await tab.continue_with_auth(
            request_id=request_id,
            auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
        await tab.disable_fetch_events()
        return response

    async def _setup_context_proxy_auth_for_tab(
        self, tab: Tab, browser_context_id: Optional[str]
    ) -> None:
        """Enable proxy auth handling for a Tab if its context has credentials stored."""
        if not browser_context_id:
            return
        creds = self._context_proxy_auth.get(browser_context_id)
        if not creds:
            return
        username, password = creds
        logger.debug(
            f'Enabling context-level proxy auth for tab (context={browser_context_id}, '
            f'user_set={bool(username)}'
        )
        await tab.enable_fetch_events(handle_auth=True)
        await tab.on(
            FetchEvent.REQUEST_PAUSED,
            partial(
                self._tab_continue_request_callback,
                tab=tab,
            ),
            temporary=True,
        )
        await tab.on(
            FetchEvent.AUTH_REQUIRED,
            partial(
                self._tab_continue_request_with_auth_callback,
                tab=tab,
                proxy_username=username,
                proxy_password=password,
            ),
            temporary=True,
        )

    async def _verify_browser_running(self):
        """
        Verify browser started successfully.

        Raises:
            FailedToStartBrowser: If the browser failed to start.
        """
        logger.debug(f'Verifying browser is running (timeout={self.options.start_timeout})')
        if not await self._is_browser_running(self.options.start_timeout):
            logger.error('Browser failed to start within timeout')
            raise FailedToStartBrowser()

    async def _configure_proxy(
        self, private_proxy: bool, proxy_credentials: tuple[Optional[str], Optional[str]]
    ):
        """Setup proxy authentication handling if needed."""
        if not private_proxy:
            return

        logger.debug(
            'Configuring proxy authentication: '
            f'credentials provided={bool(proxy_credentials[0] or proxy_credentials[1])}'
        )
        await self.enable_fetch_events(handle_auth_requests=True)
        await self.on(
            FetchEvent.REQUEST_PAUSED,
            self._continue_request_callback,
            temporary=True,
        )
        await self.on(
            FetchEvent.AUTH_REQUIRED,
            partial(
                self._continue_request_with_auth_callback,
                proxy_username=proxy_credentials[0],
                proxy_password=proxy_credentials[1],
            ),
            temporary=True,
        )

    @staticmethod
    def _is_valid_tab(target: TargetInfo) -> bool:
        """Check if target is a valid browser tab (filters out extensions)."""
        return target.get('type') == 'page' and 'chrome-extension://' not in target.get('url', '')

    @staticmethod
    async def _get_valid_tab_id(targets: list[TargetInfo]) -> str:
        """
        Find valid attached tab ID.

        Raises:
            NoValidTabFound: If no valid attached tab is found.
        """
        valid_tab = next(
            (
                tab
                for tab in targets
                if tab.get('type') == 'page' and 'extension' not in tab.get('url', '')
            ),
            None,
        )

        if not valid_tab:
            logger.error(f'No valid tab found among {len(targets)} targets')
            raise NoValidTabFound()

        tab_id = valid_tab.get('targetId')
        if not tab_id:
            logger.error('Valid tab missing targetId')
            raise NoValidTabFound('Tab missing targetId')

        return tab_id

    async def _is_browser_running(self, timeout: int = 10) -> bool:
        """Check if browser process is running and CDP endpoint is responsive."""
        for _ in range(timeout):
            if await self._connection_handler.ping():
                return True
            await asyncio.sleep(1)

        return False

    async def _execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse], timeout: int = 10
    ) -> T_CommandResponse:
        """Execute CDP command and return result (core method for browser communication)."""
        logger.debug(f'Executing command: {command.get("method")} (timeout={timeout})')
        return await self._connection_handler.execute_command(command, timeout=timeout)

    def _setup_user_dir(self):
        """Setup temporary user data directory if not specified in options."""
        user_data_dir = self._get_user_data_dir()
        if user_data_dir and self.options.browser_preferences:
            self._set_browser_preferences_in_user_data_dir(user_data_dir)
        elif not user_data_dir:
            temp_dir = self._temp_directory_manager.create_temp_dir()
            # For all browsers, use a temporary directory
            self.options.arguments.append(f'--user-data-dir={temp_dir.name}')
            if self.options.browser_preferences:
                self._set_browser_preferences_in_temp_dir(temp_dir)
        logger.debug(f'User dir setup complete: {self._get_user_data_dir()}')

    def _set_browser_preferences_in_temp_dir(self, temp_dir: TemporaryDirectory):
        os.mkdir(os.path.join(temp_dir.name, 'Default'))
        preferences = self.options.browser_preferences
        with open(
            os.path.join(temp_dir.name, 'Default', 'Preferences'), 'w', encoding='utf-8'
        ) as json_file:
            json.dump(preferences, json_file)
        logger.debug('Wrote browser preferences to temp user dir')

    def _set_browser_preferences_in_user_data_dir(self, user_data_dir: str):
        """
        Set browser preferences in the user data directory.

        This function will:
        1. Create a backup of the existing Preferences file if it exists
        2. Create Default directory if it doesn't exist
        3. Write the new preferences to the Preferences file

        Args:
            user_data_dir: Path to the user data directory
        """
        default_dir = os.path.join(user_data_dir, 'Default')
        os.makedirs(default_dir, exist_ok=True)

        preferences_path = os.path.join(default_dir, 'Preferences')
        self._backup_preferences_dir = os.path.join(default_dir, 'Preferences.backup')

        if os.path.exists(preferences_path):
            # Backup existing Preferences file
            shutil.copy2(preferences_path, self._backup_preferences_dir)

        preferences = {}
        if os.path.exists(preferences_path):
            with suppress(json.JSONDecodeError):
                with open(preferences_path, 'r', encoding='utf-8') as preferences_file:
                    preferences = json.load(preferences_file)
        preferences.update(self.options.browser_preferences)
        with open(preferences_path, 'w', encoding='utf-8') as json_file:
            json.dump(preferences, json_file, indent=2)
        logger.debug(f'Updated browser preferences in user data dir: {preferences_path}')

    def _get_user_data_dir(self) -> Optional[str]:
        for arg in self.options.arguments:
            if arg.startswith('--user-data-dir='):
                return arg.split('=', 1)[1]
        return None

    @staticmethod
    def _validate_ws_address(ws_address: str):
        """Validate WebSocket address."""
        min_slashes = 4
        if not ws_address.startswith('ws://'):
            logger.error('Invalid WebSocket address: missing ws:// prefix')
            raise InvalidWebSocketAddress('WebSocket address must start with ws://')
        if len(ws_address.split('/')) < min_slashes:
            logger.error('Invalid WebSocket address: not enough slashes')
            raise InvalidWebSocketAddress(
                f'WebSocket address must contain at least {min_slashes} slashes'
            )

    async def _setup_ws_address(self, ws_address: str):
        """Setup WebSocket address for browser."""
        self._validate_ws_address(ws_address)
        self._ws_address = ws_address
        self._connection_handler._ws_address = self._ws_address
        await self._connection_handler._ensure_active_connection()
        logger.info('WebSocket address set for browser-level connection')

    def _get_tab_kwargs(self, target_id: str, browser_context_id: Optional[str] = None) -> dict:
        """
        Get kwargs for creating a tab based on the WebSocket address.
        If the WebSocket address is set, the tab will be created with the WebSocket address.
        Otherwise, the tab will be created with the connection port and target ID.

        Args:
            target_id: Target ID of the tab.
            browser_context_id: Browser context ID of the tab.

        Returns:
            Dict of kwargs for creating a tab.
        """
        kwargs: dict[str, Any] = {
            'target_id': target_id,
            'browser_context_id': browser_context_id,
        }
        if self._ws_address:
            kwargs['ws_address'] = self._get_tab_ws_address(target_id)
        else:
            kwargs['connection_port'] = self._connection_port
        logger.debug(f'Tab kwargs resolved for {target_id}: using_ws={bool(self._ws_address)}')
        return kwargs

    def _get_tab_ws_address(self, tab_id: str) -> str:
        """
        Get WebSocket address for a specific tab, preserving any query or fragment
        components present in the original browser-level WebSocket URL.

        This ensures authentication tokens passed via query string (e.g.,
        ws://host/devtools/browser/abc?token=XYZ) are retained when switching
        to the page-level endpoint (devtools/page/<tab_id>), which is critical
        for providers like Browserless or authenticated CDP proxies.
        """
        if not self._ws_address:
            raise InvalidWebSocketAddress('WebSocket address is not set')

        parts = urlsplit(self._ws_address)
        # Preserve scheme and netloc; build the page path and keep query/fragment
        page_path = f'/devtools/page/{tab_id}'
        ws = urlunsplit((parts.scheme, parts.netloc, page_path, parts.query, parts.fragment))
        logger.debug(f'Resolved tab WebSocket address: {ws}')
        return ws

    @staticmethod
    def _sanitize_proxy_and_extract_auth(
        proxy_server: str,
    ) -> tuple[str, Optional[tuple[str, str]]]:
        """Strip credentials from a proxy URL and return sanitized URL plus (user, pass).

        Accepts inputs like:
        - username:password@host:port
        - http://username:password@host:port
        - socks5://username:password@host:port
        - host:port (no credentials)
        Returns a (sanitized_proxy, (user, pass) | None).
        Ensures scheme is present in the sanitized URL (defaults to http).
        """
        base = proxy_server if '://' in proxy_server else f'http://{proxy_server}'
        parts = urlsplit(base)
        netloc = parts.netloc
        creds: Optional[tuple[str, str]] = None
        if '@' in netloc:
            cred_part, host_part = netloc.split('@', 1)
            if ':' in cred_part:
                user, pwd = cred_part.split(':', 1)
            else:
                user, pwd = cred_part, ''
            creds = (user, pwd)
            sanitized = urlunsplit((
                parts.scheme,
                host_part,
                parts.path,
                parts.query,
                parts.fragment,
            ))
        else:
            # No creds; ensure scheme
            sanitized = urlunsplit((
                parts.scheme,
                parts.netloc,
                parts.path,
                parts.query,
                parts.fragment,
            ))
        return sanitized, creds

    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """Get default browser executable path (implemented by subclasses)."""
        pass
