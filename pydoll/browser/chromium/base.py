import asyncio
from abc import ABC, abstractmethod
from functools import partial
from random import randint
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydoll.browser.managers import (
    BrowserOptionsManager,
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from pydoll.browser.options import Options
from pydoll.browser.tab import Tab
from pydoll.commands import (
    BrowserCommands,
    FetchCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import (
    AuthChallengeResponseValues,
    BrowserType,
    DownloadBehavior,
    PermissionType,
)
from pydoll.exceptions import BrowserNotRunning, FailedToStartBrowser, NoValidTabFound
from pydoll.protocol.base import Command
from pydoll.protocol.browser.responses import (
    GetVersionResponse,
    GetVersionResultDict,
    GetWindowForTargetResponse,
)
from pydoll.protocol.browser.types import WindowBoundsDict
from pydoll.protocol.network.types import Cookie, CookieParam, RequestPausedEvent
from pydoll.protocol.storage.responses import GetCookiesResponse
from pydoll.protocol.target.responses import (
    CreateBrowserContextResponse,
    CreateTargetResponse,
    GetBrowserContextsResponse,
    GetTargetsResponse,
)
from pydoll.protocol.target.types import TargetInfo

T = TypeVar('T')


class Browser(ABC):  # noqa: PLR0904
    """
    Abstract base class for browser automation using Chrome DevTools Protocol.

    This class provides a comprehensive interface to control browser instances,
    manage browser contexts, handle network traffic, manipulate cookies, and
    execute CDP commands. It serves as the foundation for browser-specific
    implementations by abstracting common CDP operations.

    Key capabilities:
    - Browser lifecycle management (start/stop)
    - Browser context/incognito profile handling
    - Tab/target management
    - Network traffic interception and modification
    - Cookie management
    - Window manipulation
    - Permission controls
    - Event handling

    The implementation uses Chrome DevTools Protocol to enable driver-less
    browser automation with full access to browser internals.
    """

    def __init__(
        self,
        options: Optional[Options] = None,
        connection_port: Optional[int] = None,
        browser_type: Optional[BrowserType] = None,
    ):
        """
        Initializes a new Browser instance with specified configuration.

        Args:
            options: Configuration options for the browser. If None,
                default options will be used based on browser type.
            connection_port: Port to use for CDP WebSocket connection.
                If None, a random port between 9223-9322 will be assigned.
            browser_type: Type of browser to use. If None, will be inferred
                from options.

        Note:
            This only configures the instance. To actually start the browser,
            call the `start()` method.
        """
        self.options = BrowserOptionsManager.initialize_options(options, browser_type)
        self._proxy_manager = ProxyManager(self.options)
        self._connection_port = connection_port if connection_port else randint(9223, 9322)
        self._browser_process_manager = BrowserProcessManager()
        self._temp_directory_manager = TempDirectoryManager()
        self._connection_handler = ConnectionHandler(self._connection_port)
        BrowserOptionsManager.add_default_arguments(self.options)

    async def __aenter__(self) -> 'Browser':
        """
        Async context manager entry point.

        Returns:
            Browser: The browser instance.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.

        Args:
            exc_type: The exception type, if raised.
            exc_val: The exception value, if raised.
            exc_tb: The traceback, if an exception was raised.
        """
        if await self._is_browser_running(timeout=2):
            await self.stop()

        await self._connection_handler.close()

    async def start(self, headless: bool = False) -> Tab:
        """
        Starts the browser process and establishes CDP connection.

        This method launches the browser executable, waits for it to initialize,
        establishes a WebSocket connection via CDP, and configures proxy settings
        if needed. The browser runs with a clean user profile by default.

        Args:
            headless: Whether to run the browser in headless mode (without UI).
                If True, adds the --headless flag if not already present.

        Raises:
            BrowserNotRunning: If the browser fails to start or connect.

        Note:
            This is an async method and must be awaited. For typical usage,
            consider using the context manager pattern with async with.
        """
        binary_location = self.options.binary_location or self._get_default_binary_location()

        if headless:
            headless_arg = '--headless'
            if headless_arg not in self.options.arguments:
                self.options.add_argument(headless_arg)

        self._setup_user_dir()
        proxy_config = self._proxy_manager.get_proxy_credentials()

        self._browser_process_manager.start_browser_process(
            binary_location,
            self._connection_port,
            self.options.arguments,
        )
        await self._verify_browser_running()
        await self._configure_proxy(proxy_config[0], proxy_config[1])

        valid_tab_id = await self._get_valid_tab_id(await self.get_targets())
        return Tab(self, self._connection_port, valid_tab_id)

    async def stop(self):
        """
        Stops the browser process and cleans up resources.

        This method:
        1. Sends the Browser.close command via CDP
        2. Terminates the browser process
        3. Removes temporary directories
        4. Closes WebSocket connections

        Raises:
            BrowserNotRunning: If the browser is not currently running.

        Note:
            This method is automatically called when exiting the context manager.
        """
        if not await self._is_browser_running():
            raise BrowserNotRunning()

        await self._execute_command(BrowserCommands.CLOSE)
        self._browser_process_manager.stop_process()
        self._temp_directory_manager.cleanup()
        await self._connection_handler.close()

    async def create_browser_context(
        self, proxy_server: Optional[str] = None, proxy_bypass_list: Optional[str] = None
    ) -> str:
        """
        Creates a new browser context (similar to an incognito profile).

        Browser contexts provide isolated storage for cookies, cache, and local
        storage. Multiple contexts can exist simultaneously, unlike regular
        incognito mode. Each context has its own set of tabs and doesn't share
        session data with other contexts.

        Args:
            proxy_server: Optional proxy server to use for this context only.
                Format: "scheme://host:port"
            proxy_bypass_list: Optional comma-separated list of hosts that
                bypass the proxy. Only applies if proxy_server is specified.

        Returns:
            str: Browser context ID string that can be used with other methods
                that accept a browser_context_id parameter.

        """
        response: CreateBrowserContextResponse = await self._execute_command(
            TargetCommands.create_browser_context(
                proxy_server=proxy_server,
                proxy_bypass_list=proxy_bypass_list,
            )
        )
        return response['result']['browserContextId']

    async def delete_browser_context(self, browser_context_id: str):
        """
        Deletes a browser context and all associated tabs/resources.

        This removes all storage (cookies, localStorage, etc.) associated with
        the specified context and closes all tabs created within it. The default
        browser context cannot be deleted.

        Args:
            browser_context_id: ID of the browser context to delete, as
                returned by create_browser_context().

        Returns:
            The command response object.

        Note:
            Deleting a browser context closes all associated tabs immediately.
        """
        return await self._execute_command(
            TargetCommands.dispose_browser_context(browser_context_id)
        )

    async def get_browser_contexts(self) -> List[str]:
        """
        Retrieves IDs of all available browser contexts.

        Returns:
            List[str]: List of browser context IDs, including the default context.

        Note:
            The default browser context is always available, even if no custom
            contexts have been created.
        """
        response: GetBrowserContextsResponse = await self._execute_command(
            TargetCommands.get_browser_contexts()
        )
        return response['result']['browserContextIds']

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> Tab:
        """
        Creates a new tab and returns a Tab instance for interacting with it.

        This is the primary method for opening new pages. The returned Tab object
        provides methods for page navigation, element selection, and other interactions.

        Args:
            url: Initial URL to navigate to. If empty, opens about:blank.
            browser_context_id: Optional browser context ID. If provided,
                the tab will be created in that context. If None, uses the
                default browser context.

        Returns:
            Tab: A Tab instance representing the newly created page.

        Note:
            This method uses the Target.createTarget CDP command to create a new page
            target, then provides a Tab interface to interact with it.
        """
        response: CreateTargetResponse = await self._execute_command(
            TargetCommands.create_target(
                url=url,
                browser_context_id=browser_context_id,
            )
        )
        target_id = response['result']['targetId']
        return Tab(self, self._connection_port, target_id, browser_context_id)

    async def get_targets(self) -> List[TargetInfo]:
        """
        Retrieves information about all active targets/pages in the browser.

        Targets represent various debuggable entities in Chrome:
        - Page (regular tabs)
        - ServiceWorker
        - SharedWorker
        - Browser (the main browser process)
        - Other types

        Returns:
            List[TargetInfo]: List of target information dictionaries containing:
                - targetId: Unique identifier
                - type: Target type (page, service_worker, etc.)
                - title: Page title
                - url: Target URL
                - attached: Whether DevTools is attached
                - browserContextId: Context ID the target belongs to

        Note:
            This is a useful method for debugging and managing multiple tabs.
        """
        response: GetTargetsResponse = await self._execute_command(TargetCommands.get_targets())
        return response['result']['targetInfos']

    async def set_download_path(self, path: str, browser_context_id: Optional[str] = None):
        """
        Sets the download path for browser downloads.

        This is a convenience method that calls set_download_behavior with
        DownloadBehavior.ALLOW and the specified path.

        Args:
            path: Directory path where downloads should be saved.
            browser_context_id: Optional browser context ID to apply settings to.
                If None, applies to the default browser context.

        Returns:
            The command response object.

        """
        return await self._execute_command(
            BrowserCommands.set_download_behavior(DownloadBehavior.ALLOW, path, browser_context_id)
        )

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        events_enabled: bool = False,
    ):
        """
        Configures how the browser handles downloads.

        Args:
            behavior: Download behavior mode (ALLOW, DENY, DEFAULT).
                - ALLOW: Save downloads to the specified path.
                - DENY: Cancel all downloads.
                - DEFAULT: Use browser's default download handling.
            download_path: Directory path where downloads should be saved.
                Required if behavior is ALLOW, ignored otherwise.
            browser_context_id: Optional browser context ID to apply settings to.
                If None, applies to the default browser context.
            events_enabled: Whether to generate download events that can be
                captured with the on() method. Useful for tracking download progress.

        Returns:
            The command response object.

        """
        return await self._execute_command(
            BrowserCommands.set_download_behavior(
                behavior, download_path, browser_context_id, events_enabled
            )
        )

    async def delete_all_cookies(self, browser_context_id: Optional[str] = None):
        """
        Deletes all cookies from the browser or specific context.

        Removes all cookies including session cookies, persistent cookies,
        and third-party cookies within the specified browser context.

        Args:
            browser_context_id: Optional browser context ID to delete cookies from.
                If None, deletes cookies from the default browser context.

        Returns:
            The command response object.

        """
        return await self._execute_command(StorageCommands.clear_cookies(browser_context_id))

    async def set_cookies(
        self, cookies: List[CookieParam], browser_context_id: Optional[str] = None
    ):
        """
        Sets multiple cookies in the browser.

        Args:
            cookies: List of cookie objects to set. Each cookie must include
                name and value, and may include other attributes like domain,
                path, secure, httpOnly, etc.
            browser_context_id: Optional browser context ID to set cookies in.
                If None, sets cookies in the default browser context.

        Returns:
            The command response object.

        """
        return await self._execute_command(StorageCommands.set_cookies(cookies, browser_context_id))

    async def get_cookies(self, browser_context_id: Optional[str] = None) -> List[Cookie]:
        """
        Retrieves all cookies from the browser or specific context.

        Args:
            browser_context_id: Optional browser context ID to get cookies from.
                If None, gets cookies from the default browser context.

        Returns:
            List[Cookie]: List of cookie objects containing name, value, domain,
                path, expiration time, and other attributes.

        Note:
            This returns all cookies accessible by the browser, including
            session cookies, persistent cookies, and third-party cookies.
        """
        response: GetCookiesResponse = await self._execute_command(
            StorageCommands.get_cookies(browser_context_id)
        )
        return response['result']['cookies']

    async def get_version(self) -> GetVersionResultDict:
        """
        Retrieves browser version and CDP protocol version information.

        Returns:
            GetVersionResultDict: Dictionary containing:
                - protocolVersion: CDP version
                - product: Browser name and version (e.g., "Chrome/91.0.4472.124")
                - revision: Browser revision
                - userAgent: Full user agent string
                - jsVersion: JavaScript engine version
        """
        response: GetVersionResponse = await self._execute_command(BrowserCommands.get_version())
        return response['result']

    async def get_window_id_for_target(self, target_id: str) -> int:
        """
        Gets the window ID associated with a target.

        Window IDs are used for manipulating browser windows (resize, move, etc.)
        via the Browser domain of CDP.

        Args:
            target_id: Target ID to get the window ID for.

        Returns:
            int: Window ID for the specified target.

        Note:
            A single window may contain multiple targets (tabs), but each
            target belongs to exactly one window.
        """
        response: GetWindowForTargetResponse = await self._execute_command(
            BrowserCommands.get_window_for_target(target_id)
        )
        return response['result']['windowId']

    async def get_window_id_for_tab(self, tab: Tab) -> int:
        """
        Gets the window ID for a Tab instance.

        Convenience method that extracts the target ID from the tab
        and calls get_window_id_for_target.

        Args:
            tab: Tab instance to get the window ID for.

        Returns:
            int: Window ID containing the specified tab.
        """
        return await self.get_window_id_for_target(tab._target_id)

    async def get_window_id(self) -> int:
        """
        Gets the window ID for any valid attached tab.

        This is a convenience method that finds a suitable tab
        and returns its window ID.

        Returns:
            int: Window ID for an attached tab.

        Raises:
            NoValidTabFound: If no valid attached tab can be found.
        """
        targets = await self.get_targets()
        valid_tab_id = await self._get_valid_tab_id(targets)
        return await self.get_window_id_for_target(valid_tab_id)

    async def set_window_maximized(self):
        """
        Maximizes the browser window.

        Resizes the window to use the full available screen space
        without entering fullscreen mode.

        Returns:
            The command response object.

        Note:
            This affects all tabs in the window, not just the active one.
        """
        window_id = await self.get_window_id()
        return await self._execute_command(BrowserCommands.set_window_maximized(window_id))

    async def set_window_minimized(self):
        """
        Minimizes the browser window.

        Collapses the window to the taskbar/dock while keeping the
        browser process running.

        Returns:
            The command response object.

        """
        window_id = await self.get_window_id()
        return await self._execute_command(BrowserCommands.set_window_minimized(window_id))

    async def set_window_bounds(self, bounds: WindowBoundsDict):
        """
        Sets the position and/or size of the browser window.

        Args:
            bounds: Dictionary specifying window properties to modify,
                which may include:
                - left: X coordinate
                - top: Y coordinate
                - width: Window width
                - height: Window height
                - windowState: Window state (normal, minimized, maximized, fullscreen)

        Returns:
            The command response object.

        Note:
            Only specified properties will be changed; omitted properties
            retain their current values.
        """
        window_id = await self.get_window_id()
        return await self._execute_command(BrowserCommands.set_window_bounds(window_id, bounds))

    async def grant_permissions(
        self,
        permissions: List[PermissionType],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ):
        """
        Grants specified permissions to the browser.

        Controls access to browser features that normally require user permission:
        - Geolocation
        - Notifications
        - Camera/Microphone
        - Midi devices
        - Clipboard
        - And others

        Args:
            permissions: List of permissions to grant from PermissionType enum.
            origin: Optional origin to grant permissions to (e.g., "https://example.com").
                If None, grants permissions to all origins.
            browser_context_id: Optional browser context ID to apply permissions to.
                If None, applies to the default browser context.

        Returns:
            The command response object.

        Note:
            This bypasses normal permission prompts, allowing automated testing
            of permission-dependent features.
        """
        return await self._execute_command(
            BrowserCommands.grant_permissions(permissions, origin, browser_context_id)
        )

    async def reset_permissions(self, browser_context_id: Optional[str] = None):
        """
        Resets all permission grants to browser defaults.

        Removes any permissions previously granted via grant_permissions
        and restores the default permission prompting behavior.

        Args:
            browser_context_id: Optional browser context ID to reset permissions for.
                If None, resets permissions in the default browser context.

        Returns:
            The command response object.
        """
        return await self._execute_command(BrowserCommands.reset_permissions(browser_context_id))

    async def on(
        self, event_name: str, callback: Callable[[Dict], Any], temporary: bool = False
    ) -> int:
        """
        Registers an event listener for CDP events.

        This method allows subscribing to CDP events at the browser level,
        affecting all pages/targets. Events include network activity,
        console messages, dialog prompts, and many others.

        The callback is automatically wrapped to run in a separate task,
        preventing it from blocking the main event loop. This means your
        callback can perform longer operations without affecting the browser's
        responsiveness.

        Args:
            event_name: CDP event name (e.g., "Network.responseReceived",
                "Page.loadEventFired", "Runtime.consoleAPICalled").
            callback: Function to call when the event occurs. Can be synchronous
                or asynchronous. Should accept a single parameter containing the
                event data. Runs in the background and won't block other operations.
            temporary: If True, the callback will be removed after first invocation.
                If False, it will remain until explicitly removed.

        Returns:
            int: Callback ID that can be used to remove the listener later.

        Note:
            For page-specific events, consider using the Tab.on() method
            which scopes events to a specific page.
        """

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def enable_fetch_events(
        self, handle_auth_requests: bool = False, resource_type: str = ''
    ):
        """
        Enables interception of network requests via the Fetch domain.

        This allows monitoring, modifying, or blocking any network request
        before it's sent. When enabled, all matching requests will be paused
        and emit Fetch.requestPaused events until explicitly continued.

        Args:
            handle_auth_requests: Whether to intercept authentication challenges.
                If True, emits Fetch.authRequired events for auth requests.
            resource_type: Optional resource type filter (e.g., "XHR", "Fetch", "Document").
                If specified, only intercepts requests of that type.
                If empty, intercepts all requests.

        Note:
            - Paused requests must be explicitly continued using Fetch.continueRequest
              or similar methods, or they will time out.
            - This is a powerful feature for request modification, mocking responses,
              and implementing custom network behavior.
            - For page-specific interception, use Tab.enable_fetch_events() instead.
        """
        await self._connection_handler.execute_command(
            FetchCommands.enable(handle_auth_requests, resource_type)
        )

    async def disable_fetch_events(self):
        """
        Disables request interception and releases any paused requests.

        Turns off the Fetch domain, allowing network requests to proceed
        normally without interception. Any currently paused requests will
        be released and continue as if they were never intercepted.

        Note:
            - Call this method when you're done intercepting requests to
              restore normal network behavior.
            - This affects all requests across all pages.
            - For page-specific control, use Tab.disable_fetch_events() instead.
        """
        await self._connection_handler.execute_command(FetchCommands.disable())

    async def enable_runtime_events(self):
        """
        Enables runtime events.
        """
        await self._connection_handler.execute_command(RuntimeCommands.enable())

    async def disable_runtime_events(self):
        """
        Disables runtime events.
        """
        await self._connection_handler.execute_command(RuntimeCommands.disable())

    async def continue_request(self, request_id: str):
        """
        Continues a paused network request without modifications.

        Args:
            request_id: The ID of the request to continue.

        Returns:
            The command response object.

        Note:
            This method is used internally to handle request continuations.
            It is not intended for direct use by the developer.
        """
        return await self._execute_command(FetchCommands.continue_request(request_id))

    async def _continue_request_callback(self, event: RequestPausedEvent):
        """
        Continues a paused network request without modifications.

        Used internally as an event handler for Fetch.requestPaused events
        when you want to monitor requests without modifying them.

        Args:
            event: Event data dictionary containing request information.
                Must include params.requestId to identify the request.
        """
        request_id = event['params']['requestId']
        return await self.continue_request(request_id)

    async def _continue_request_with_auth_callback(
        self, event: RequestPausedEvent, proxy_username: str, proxy_password: str
    ):
        """
        Continues a paused authentication request with proxy credentials.

        Used internally to handle proxy authentication challenges by
        providing the configured username and password.

        Args:
            event: Event data dictionary from Fetch.authRequired event.
            proxy_username: Username for proxy authentication.
            proxy_password: Password for proxy authentication.
        """
        request_id = event['params']['requestId']
        await self.disable_fetch_events()
        return await self._execute_command(
            FetchCommands.continue_request_with_auth(
                request_id,
                auth_challenge_response=AuthChallengeResponseValues.PROVIDE_CREDENTIALS,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )

    async def _verify_browser_running(self):
        """
        Verifies that the browser process has started successfully.

        Raises:
            FailedToStartBrowser: If the browser failed to start.
        """
        if not await self._is_browser_running():
            raise FailedToStartBrowser()

    async def _configure_proxy(self, private_proxy, proxy_credentials):
        """
        Sets up proxy authentication handling if needed.

        If a private proxy requiring authentication is configured, this method
        enables Fetch domain interception and registers handlers for proxy
        authentication challenges.

        Args:
            private_proxy: Boolean indicating if authentication is required.
            proxy_credentials: Tuple of (username, password) for proxy auth.
        """
        if private_proxy:
            await self.enable_fetch_events(handle_auth_requests=True)
            await self.on(
                'Fetch.requestPaused',
                self._continue_request_callback,
                temporary=True,
            )
            await self.on(
                'Fetch.authRequired',
                partial(
                    self._continue_request_with_auth_callback,
                    proxy_username=proxy_credentials[0],
                    proxy_password=proxy_credentials[1],
                ),
                temporary=True,
            )

    @staticmethod
    def _is_valid_tab(target: TargetInfo) -> bool:
        """
        Determines if a target represents a valid browser tab.

        Filters out chrome extensions and other non-page targets.

        Args:
            target: Target information dictionary.

        Returns:
            bool: True if the target is a valid browser tab, False otherwise.
        """
        return target.get('type') == 'page' and 'chrome-extension://' not in target.get('url', '')

    @staticmethod
    async def _get_valid_tab_id(targets: List[TargetInfo]) -> str:
        """
        Finds a valid attached tab ID from the list of targets.

        Args:
            targets: List of target information dictionaries.

        Returns:
            str: Target ID of a valid attached tab.

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
            raise NoValidTabFound()

        tab_id = valid_tab.get('targetId')
        if not tab_id:
            raise NoValidTabFound('Tab missing targetId')

        return tab_id

    async def _is_browser_running(self, timeout: int = 10) -> bool:
        """
        Checks if the browser process is running and CDP endpoint is responsive.

        Args:
            timeout: Maximum number of seconds to wait for a response.

        Returns:
            bool: True if the browser is running, False otherwise.
        """
        for _ in range(timeout):
            if await self._connection_handler.ping():
                return True
            await asyncio.sleep(1)

        return False

    async def _execute_command(self, command: Command[T]) -> T:
        """
        Executes a CDP command and returns the result.

        This is the core method for sending commands to the browser via CDP.
        It handles serialization, transport, and response parsing.

        Args:
            command: Command object containing method and parameters.

        Returns:
            The parsed response data, typed according to the command's
            generic type parameter.

        Note:
            This method has a 60-second timeout to prevent hanging on
            commands that might not complete.
        """
        return await self._connection_handler.execute_command(command, timeout=60)

    def _setup_user_dir(self):
        """
        Sets up a user data directory for the browser.

        If no user-data-dir argument is provided in the options, creates
        a temporary directory and adds it to the launch arguments.
        """
        if '--user-data-dir' not in [arg.split('=')[0] for arg in self.options.arguments]:
            # For all browsers, use a temporary directory
            temp_dir = self._temp_directory_manager.create_temp_dir()
            self.options.arguments.append(f'--user-data-dir={temp_dir.name}')

    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """
        Returns the default path to the browser executable.

        This abstract method must be implemented by browser-specific subclasses
        to locate the browser binary on the current system.

        Returns:
            str: Path to the browser executable.
        """
        pass
