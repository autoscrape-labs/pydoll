"""Browser and BrowserType: launching pydoll's Chrome with Playwright's signatures."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union, cast

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.commands import TargetCommands
from pydoll.exceptions import PydollException
from pydoll.playwright._browser_context import BrowserContext
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._events import EventEmitter
from pydoll.playwright._page import Page
from pydoll.protocol.target.events import TargetEvent

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydoll.playwright._playwright import BrowserType
    from pydoll.protocol.target.types import TargetInfo

_CONTEXT_OPTION_NAMES = {
    'viewport',
    'no_viewport',
    'user_agent',
    'locale',
    'timezone_id',
    'geolocation',
    'permissions',
    'extra_http_headers',
    'offline',
    'http_credentials',
    'device_scale_factor',
    'is_mobile',
    'has_touch',
    'color_scheme',
    'reduced_motion',
    'forced_colors',
    'accept_downloads',
    'ignore_https_errors',
    'bypass_csp',
    'java_script_enabled',
    'base_url',
    'storage_state',
    'downloads_path',
    'screen',
    'proxy',
    'record_har_path',
    'record_video_dir',
    'strict_selectors',
    'service_workers',
    'client_certificates',
    'contrast',
    'user_gesture_on_evaluate',
}


class Browser(EventEmitter):
    """A running Chromium controlled by pydoll, exposed with Playwright's API."""

    def __init__(self, browser_type: BrowserType, chrome: Chrome) -> None:
        super().__init__()
        self._browser_type = browser_type
        self._chrome = chrome
        self._contexts: list[BrowserContext] = []
        self._connected = True
        self._version = ''
        self._user_agent_cache = ''
        self._initial_tab: Any = None
        self._callback_ids: list[int] = []
        self._default_context: Optional[BrowserContext] = None

    def __repr__(self) -> str:
        return f'<Browser type={self._browser_type.name} version={self._version}>'

    async def _initialize(self, initial_tab: Any) -> None:
        self._initial_tab = initial_tab
        try:
            version = await self._chrome.get_version()
            self._version = (
                version.get('product', '').replace('Chrome/', '').replace('HeadlessChrome/', '')
            )
            self._user_agent_cache = version.get('userAgent', '')
            await self._chrome.execute_command(TargetCommands.set_discover_targets(discover=True))
            self._callback_ids.append(
                await self._chrome.on(TargetEvent.TARGET_CREATED, self._on_target_created)
            )
            self._callback_ids.append(
                await self._chrome.on(TargetEvent.TARGET_DESTROYED, self._on_target_destroyed)
            )
        except PydollException as error:
            raise translate(error) from error

    async def _user_agent(self) -> str:
        return self._user_agent_cache

    def _on_target_created(self, event: dict[str, Any]) -> None:
        info = event['params']['targetInfo']
        if info.get('type') != 'page' or not info.get('openerId'):
            return
        asyncio.ensure_future(self._adopt_popup(info))

    async def _adopt_popup(self, info: dict[str, Any]) -> None:
        opener: Optional[Page] = None
        context: Optional[BrowserContext] = None
        for candidate in self._contexts:
            for page in candidate._pages:
                if page.tab.target_id == info['openerId']:
                    opener = page
                    context = candidate
        if context is None:
            return
        try:
            tab = await self._chrome.get_tab_by_target(cast('TargetInfo', info))
            await context._adopt(tab, opener=opener, emit_popup=True)
        except (PydollException, Error):
            logger.debug(
                'Popup target %s could not be adopted', info.get('targetId'), exc_info=True
            )

    def _on_target_destroyed(self, event: dict[str, Any]) -> None:
        target_id = event['params'].get('targetId')
        for context in self._contexts:
            for page in list(context._pages):
                if page.tab.target_id == target_id:
                    page._on_target_closed()

    @property
    def browser_type(self) -> BrowserType:
        return self._browser_type

    @property
    def contexts(self) -> list[BrowserContext]:
        return list(self._contexts)

    @property
    def version(self) -> str:
        return self._version

    @property
    def chrome(self) -> Chrome:
        """The underlying pydoll Chrome, for code that mixes both APIs."""
        return self._chrome

    def is_connected(self) -> bool:
        return self._connected

    async def new_context(self, **options: Any) -> BrowserContext:
        _validate_context_options(options)
        try:
            proxy = options.get('proxy')
            context_id = await self._chrome.create_browser_context(
                proxy_server=_proxy_server(proxy) if proxy else None,
                proxy_bypass_list=proxy.get('bypass') if proxy else None,
            )
        except PydollException as error:
            raise translate(error) from error
        context = BrowserContext(self, context_id, options)
        await context._initialize()
        self._contexts.append(context)
        return context

    async def _default_browser_context(self, options: dict[str, Any]) -> BrowserContext:
        if self._default_context is None:
            self._default_context = BrowserContext(self, None, options)
            await self._default_context._initialize()
            self._contexts.append(self._default_context)
        return self._default_context

    async def new_page(self, **options: Any) -> Page:
        context = await self.new_context(**options)
        page = await context.new_page()
        original_close = page.close

        async def close_with_context(
            run_before_unload: Optional[bool] = None, reason: Optional[str] = None
        ) -> None:
            await original_close(run_before_unload=run_before_unload, reason=reason)
            await context.close()

        page.close = close_with_context  # type: ignore[method-assign]
        return page

    async def close(self, reason: Optional[str] = None) -> None:
        if not self._connected:
            return
        self._connected = False
        for context in list(self._contexts):
            try:
                await context.close()
            except Error:
                pass
        try:
            if self._browser_type._owns_process(self):
                await self._chrome.stop()
            else:
                await self._chrome.close()
        except PydollException:
            pass
        self.emit('disconnected', self)

    async def new_browser_cdp_session(self) -> Any:
        raise Error(
            'new_browser_cdp_session is not supported; '
            'use browser.chrome.execute_command for raw CDP'
        )

    async def start_tracing(self, **kwargs: Any) -> None:
        raise Error('Tracing is not supported by pydoll.playwright')

    async def stop_tracing(self) -> bytes:
        raise Error('Tracing is not supported by pydoll.playwright')


def _validate_context_options(options: dict[str, Any]) -> None:
    unknown = set(options) - _CONTEXT_OPTION_NAMES
    if unknown:
        raise TypeError(f'Unknown context option(s): {", ".join(sorted(unknown))}')


def _proxy_server(proxy: dict[str, Any]) -> str:
    server = proxy['server']
    username = proxy.get('username')
    password = proxy.get('password')
    if username:
        scheme, _, rest = server.partition('://')
        if not rest:
            scheme, rest = 'http', scheme
        return f'{scheme}://{username}:{password or ""}@{rest}'
    return server


def build_options(
    *,
    headless: bool,
    args: Sequence[str],
    executable_path: Union[str, Path, None],
    proxy: Optional[dict[str, Any]],
    user_data_dir: Union[str, Path, None],
    ignore_default_args: Union[bool, Sequence[str], None],
    downloads_path: Union[str, Path, None],
    chromium_sandbox: Optional[bool],
    timeout: Optional[float],
) -> ChromiumOptions:
    """Translate Playwright launch options into pydoll ChromiumOptions."""
    options = ChromiumOptions()
    options.headless = headless
    if executable_path:
        options.binary_location = str(executable_path)
    if user_data_dir:
        options.add_argument(f'--user-data-dir={Path(user_data_dir).resolve()}')
    if proxy:
        options.add_argument(f'--proxy-server={_proxy_server(proxy)}')
        if proxy.get('bypass'):
            options.add_argument(f'--proxy-bypass-list={proxy["bypass"]}')
    if chromium_sandbox is False:
        options.add_argument('--no-sandbox')
    if downloads_path:
        options.set_default_download_directory(str(downloads_path))
    for argument in args:
        try:
            options.add_argument(argument)
        except PydollException:
            continue
    if timeout:
        options.start_timeout = max(int(timeout / 1000), 1)
    return options
