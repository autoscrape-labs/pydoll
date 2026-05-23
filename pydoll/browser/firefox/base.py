from __future__ import annotations

import asyncio
import logging
import os
import warnings
from collections.abc import Sequence
from random import randint
from typing import TYPE_CHECKING, Optional, overload

from pydoll.browser.firefox.tab import BiDiTab
from pydoll.browser.intercepted_request import InterceptedRequest
from pydoll.browser.managers import (
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from pydoll.commands.bidi.browser_commands import BrowserCommands
from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.network_commands import NetworkCommands
from pydoll.commands.bidi.permissions_commands import PermissionsCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.commands.bidi.session_commands import SessionCommands
from pydoll.commands.bidi.storage_commands import StorageCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.exceptions import BrowserNotRunning
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browser.types import (
    ClientWindowInfo,
    ClientWindowState,
    DownloadBehaviorAllowed,
    DownloadBehaviorDenied,
)
from pydoll.protocol.bidi.browsing_context.types import CreateType
from pydoll.protocol.bidi.network.types import (
    InterceptPhase,
    SameSite,
    StringValue,
    UrlPatternPattern,
    UrlPatternString,
)
from pydoll.protocol.bidi.permissions.types import PermissionDescriptor, PermissionState
from pydoll.protocol.bidi.session.types import ManualProxyConfiguration
from pydoll.protocol.bidi.storage.types import PartialCookie, StorageKeyPartitionDescriptor
from pydoll.protocol.events import BIDI_EVENT_MAP, Event
from pydoll.protocol.types import (
    BrowserVersion,
    Cookie,
    CookieParam,
    DownloadBehavior,
    Permission,
    WindowBounds,
)

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable

    from pydoll.browser.protocols import BrowserOptionsManagerProtocol

logger = logging.getLogger(__name__)

# Preload that hides navigator.webdriver from pages. Redefines the getter on
# Navigator.prototype to return false (a non-automated Firefox's value) with a
# native-looking toString, in every realm before page scripts run. No-ops when the
# browser already reports false (e.g. Camoufox / a binary-patched build).
_WEBDRIVER_STEALTH_SCRIPT = r"""() => {
  const proto = Object.getPrototypeOf(navigator);
  if (!proto || !navigator.webdriver) {
    return;
  }
  const NATIVE = 'function webdriver() {\n    [native code]\n}';
  const fakeGet = function webdriver() { return false; };
  const origToString = Function.prototype.toString;
  let proxiedToString;
  proxiedToString = new Proxy(origToString, {
    apply(target, thisArg, args) {
      if (thisArg === fakeGet) {
        return NATIVE;
      }
      if (thisArg === proxiedToString) {
        return Reflect.apply(target, origToString, []);
      }
      return Reflect.apply(target, thisArg, args);
    },
  });
  Object.defineProperty(Function.prototype, 'toString', {
    value: proxiedToString,
    writable: true,
    enumerable: false,
    configurable: true,
  });
  Object.defineProperty(proto, 'webdriver', {
    get: fakeGet,
    set: undefined,
    enumerable: true,
    configurable: true,
  });
}"""

# Maps the portable Permission set to the W3C names BiDi understands. Permissions
# absent here have no Firefox/BiDi equivalent and are skipped with a warning.
_BIDI_PERMISSION_MAP: dict[Permission, str] = {
    Permission.GEOLOCATION: 'geolocation',
    Permission.NOTIFICATIONS: 'notifications',
    Permission.CAMERA: 'camera',
    Permission.MICROPHONE: 'microphone',
    Permission.MIDI: 'midi',
    Permission.BACKGROUND_SYNC: 'background-sync',
    Permission.PERIODIC_BACKGROUND_SYNC: 'periodic-background-sync',
    Permission.PERSISTENT_STORAGE: 'persistent-storage',
    Permission.STORAGE_ACCESS: 'storage-access',
    Permission.CLIPBOARD_READ: 'clipboard-read',
    Permission.CLIPBOARD_WRITE: 'clipboard-write',
    Permission.IDLE_DETECTION: 'idle-detection',
    Permission.PAYMENT_HANDLER: 'payment-handler',
    Permission.SCREEN_WAKE_LOCK: 'screen-wake-lock',
    Permission.DISPLAY_CAPTURE: 'display-capture',
    Permission.SPEAKER_SELECTION: 'speaker-selection',
    Permission.WINDOW_MANAGEMENT: 'window-management',
    Permission.LOCAL_FONTS: 'local-fonts',
}


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
        self._granted_permissions: list[tuple[str, str, Optional[str]]] = []
        self._intercept_callbacks: dict[str, int] = {}

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

        await self._apply_webdriver_stealth()

        tabs = await self.get_opened_tabs()
        if tabs:
            return tabs[0]
        return await self.new_tab()

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

    async def connect(self, ws_address: str) -> BiDiTab:
        """Connect to an already running Firefox instance."""
        self._connection_handler._ws_address = ws_address
        await self._connection_handler._ensure_active_connection()
        response = await self._execute_command(SessionCommands.new())
        self._session_id = response['result']['sessionId']
        await self._apply_webdriver_stealth()
        tabs = await self.get_opened_tabs()
        if tabs:
            return tabs[0]
        return await self.new_tab()

    async def _apply_webdriver_stealth(self) -> None:
        """Hide navigator.webdriver from pages via a preload script.

        Registered before navigation so it runs in every realm (page and
        iframes) ahead of page scripts. Vanilla Firefox forces the flag to true
        whenever the Remote Agent is active, so without this any BiDi-driven
        page can read navigator.webdriver === true.
        """
        await self._execute_command(
            ScriptCommands.add_preload_script(
                function_declaration=_WEBDRIVER_STEALTH_SCRIPT
            )
        )

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
        if proxy_bypass_list is not None:
            warnings.warn(
                'proxy_bypass_list is not supported by WebDriver BiDi and will be ignored.',
                stacklevel=2,
            )

        proxy: Optional[ManualProxyConfiguration] = None
        if proxy_server:
            proxy = ManualProxyConfiguration(
                proxyType='manual', httpProxy=proxy_server, sslProxy=proxy_server
            )

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

    async def get_opened_tabs(self) -> list[BiDiTab]:
        """Get all open browsing contexts (tabs)."""
        response = await self._execute_command(BrowsingContextCommands.get_tree())
        contexts = response['result']['contexts']
        return [
            BiDiTab(ctx['context'], self._connection_handler)
            for ctx in contexts
        ]

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> BiDiTab:
        """Create a new tab.

        Args:
            url: URL to navigate to (empty for blank tab).
            browser_context_id: UserContext to create the tab in.
        """
        response = await self._execute_command(
            BrowsingContextCommands.create(type=CreateType.TAB, user_context=browser_context_id)
        )
        context_id = response['result']['context']
        tab = BiDiTab(context_id, self._connection_handler)

        if url:
            await tab.go_to(url)

        return tab

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
        bidi_behavior: DownloadBehaviorAllowed | DownloadBehaviorDenied
        if behavior == DownloadBehavior.ALLOW and download_path:
            bidi_behavior = DownloadBehaviorAllowed(
                type='allowed', destinationFolder=download_path
            )
        else:
            bidi_behavior = DownloadBehaviorDenied(type='denied')

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
        partition: Optional[StorageKeyPartitionDescriptor] = None
        if browser_context_id:
            partition = StorageKeyPartitionDescriptor(
                type='storageKey', userContext=browser_context_id
            )
        await self._execute_command(
            StorageCommands.delete_cookies(partition=partition)
        )

    async def set_cookies(
        self,
        cookies: list[CookieParam],
        browser_context_id: Optional[str] = None,
    ):
        """Set cookies."""
        partition: Optional[StorageKeyPartitionDescriptor] = None
        if browser_context_id:
            partition = StorageKeyPartitionDescriptor(
                type='storageKey', userContext=browser_context_id
            )
        for cookie in cookies:
            bidi_cookie = PartialCookie(
                name=cookie['name'],
                value=StringValue(type='string', value=cookie['value']),
                domain=cookie['domain'],
            )
            if 'path' in cookie:
                bidi_cookie['path'] = cookie['path']
            if 'httpOnly' in cookie:
                bidi_cookie['httpOnly'] = cookie['httpOnly']
            if 'secure' in cookie:
                bidi_cookie['secure'] = cookie['secure']
            if 'expiry' in cookie:
                bidi_cookie['expiry'] = cookie['expiry']
            if 'sameSite' in cookie:
                bidi_cookie['sameSite'] = SameSite(cookie['sameSite'].lower())
            await self._execute_command(
                StorageCommands.set_cookie(cookie=bidi_cookie, partition=partition)
            )

    async def get_cookies(
        self, browser_context_id: Optional[str] = None
    ) -> list[Cookie]:
        """Get all cookies."""
        partition: Optional[StorageKeyPartitionDescriptor] = None
        if browser_context_id:
            partition = StorageKeyPartitionDescriptor(
                type='storageKey', userContext=browser_context_id
            )
        response = await self._execute_command(
            StorageCommands.get_cookies(partition=partition)
        )
        return [BiDiTab._to_generic_cookie(c) for c in response['result']['cookies']]

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
                    state=ClientWindowState.NORMAL,
                    **bounds,
                )
            )

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
            event_name: Event enum or native BiDi event name.
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.
        """

        native_event = event_name
        if isinstance(event_name, Event):
            native_event = BIDI_EVENT_MAP.get(event_name, event_name)

        await self._execute_command(
            SessionCommands.subscribe(events=[native_event])
        )

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        return await self._connection_handler.register_callback(
            native_event, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove registered event callback."""
        await self._connection_handler.remove_callback(callback_id)

    async def intercept_requests(
        self,
        callback: Callable,
        url_patterns: Optional[list[str]] = None,
    ) -> str:
        """Intercept network requests.

        Args:
            callback: Async function receiving InterceptedRequest.
            url_patterns: URL patterns to match. All if None.

        Returns:
            Intercept ID for later removal.
        """

        bidi_patterns: Optional[list[UrlPatternPattern | UrlPatternString]] = None
        if url_patterns:
            bidi_patterns = [UrlPatternString(type='string', pattern=p) for p in url_patterns]

        response = await self._execute_command(
            NetworkCommands.add_intercept(
                phases=[InterceptPhase.BEFORE_REQUEST_SENT],
                url_patterns=bidi_patterns,
            )
        )
        intercept_id = response['result']['intercept']

        await self._execute_command(
            SessionCommands.subscribe(events=['network.beforeRequestSent'])
        )

        async def _bidi_continue(request_id, url=None, method=None, headers=None, **_):
            bidi_headers = None
            if headers:
                bidi_headers = [
                    {'name': h['name'], 'value': {'type': 'string', 'value': h['value']}}
                    for h in headers
                ]
            await self._execute_command(
                NetworkCommands.continue_request(
                    request=request_id, url=url, method=method, headers=bidi_headers,
                )
            )

        async def _bidi_fail(request_id, **_):
            await self._execute_command(
                NetworkCommands.fail_request(request=request_id)
            )

        async def _bidi_respond(request_id, status=200, headers=None, body=None, **_):
            bidi_headers = None
            if headers:
                bidi_headers = [
                    {'name': h['name'], 'value': {'type': 'string', 'value': h['value']}}
                    for h in headers
                ]
            bidi_body = None
            if body:
                bidi_body = {'type': 'string', 'value': body}
            await self._execute_command(
                NetworkCommands.provide_response(
                    request=request_id,
                    status_code=status,
                    headers=bidi_headers,
                    body=bidi_body,
                )
            )

        async def _on_before_request_sent(event):
            params = event.get('params', {})
            if not params.get('isBlocked'):
                return

            request_data = params.get('request', {})
            raw_headers = request_data.get('headers', [])
            headers_list = [
                {
                    'name': h['name'],
                    'value': (
                        h['value'].get('value', '')
                        if isinstance(h['value'], dict)
                        else h['value']
                    ),
                }
                for h in raw_headers
            ]

            req = InterceptedRequest(
                request_id=request_data.get('request', ''),
                url=request_data.get('url', ''),
                method=request_data.get('method', ''),
                headers=headers_list,
                body=None,
                continue_fn=_bidi_continue,
                fail_fn=_bidi_fail,
                respond_fn=_bidi_respond,
            )
            await callback(req)

        callback_id = await self._connection_handler.register_callback(
            'network.beforeRequestSent', _on_before_request_sent
        )
        self._intercept_callbacks[intercept_id] = callback_id
        return intercept_id

    async def remove_intercept(self, intercept_id: str):
        """Remove a request intercept and its registered handler."""
        await self._execute_command(
            NetworkCommands.remove_intercept(intercept=intercept_id)
        )
        callback_id = self._intercept_callbacks.pop(intercept_id, None)
        if callback_id is not None:
            await self._connection_handler.remove_callback(callback_id)

    async def grant_permissions(
        self,
        permissions: Sequence[Permission],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ):
        """Grant permissions for an origin via permissions.setPermission.

        Permissions that Chromium supports but Firefox/BiDi does not are skipped
        with a warning.

        Args:
            permissions: Permissions to grant.
            origin: Origin to grant for. Required in BiDi (CDP allows all origins).
            browser_context_id: UserContext to scope the permissions to.

        Raises:
            ValueError: If origin is not provided (BiDi requires an explicit origin).
        """
        if not origin:
            raise ValueError('BiDi requires an explicit origin for grant_permissions.')
        for permission in permissions:
            bidi_name = _BIDI_PERMISSION_MAP.get(permission)
            if bidi_name is None:
                warnings.warn(
                    f'Permission {permission.name} is not supported by Firefox/BiDi '
                    'and was skipped.',
                    stacklevel=2,
                )
                continue
            await self._execute_command(
                PermissionsCommands.set_permission(
                    descriptor=PermissionDescriptor(name=bidi_name),
                    state=PermissionState.GRANTED.value,
                    origin=origin,
                    user_context=browser_context_id,
                )
            )
            self._granted_permissions.append((bidi_name, origin, browser_context_id))

    async def reset_permissions(self, browser_context_id: Optional[str] = None):
        """Reset permissions granted through this browser back to 'prompt'.

        BiDi has no reset-all primitive, so only permissions granted via this
        instance are reset (optionally filtered by browser_context_id).
        """
        remaining: list[tuple[str, str, Optional[str]]] = []
        for name, origin, user_context in self._granted_permissions:
            if browser_context_id is not None and user_context != browser_context_id:
                remaining.append((name, origin, user_context))
                continue
            await self._execute_command(
                PermissionsCommands.set_permission(
                    descriptor=PermissionDescriptor(name=name),
                    state=PermissionState.PROMPT.value,
                    origin=origin,
                    user_context=user_context,
                )
            )
        self._granted_permissions = remaining

    async def execute_protocol_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Send a raw WebDriver BiDi command and return its typed result.

        Escape hatch for BiDi features not covered by the portable API. Build the
        command with the ``pydoll.commands.bidi.*`` builders.
        """
        return await self._execute_command(command, timeout)

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
