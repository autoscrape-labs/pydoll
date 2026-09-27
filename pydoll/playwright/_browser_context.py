"""BrowserContext: an isolated session (cookies, storage) holding pages."""

from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence

from pydoll.browser.tab import Tab
from pydoll.commands import BrowserCommands, EmulationCommands, PageCommands, RuntimeCommands
from pydoll.exceptions import PydollException
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._events import (
    DEFAULT_TIMEOUT_MS,
    Deadline,
    EventContextManager,
    EventEmitter,
    create_future,
    schedule,
)
from pydoll.playwright._glob import URLMatch
from pydoll.playwright._network import RouteEntry, RouteHandler, make_entry
from pydoll.playwright._page import Page
from pydoll.protocol.browser.types import DownloadBehavior, PermissionType
from pydoll.utils.user_agent_parser import UserAgentParser

if TYPE_CHECKING:
    from pydoll.playwright._browser import Browser

_PERMISSIONS = {
    'geolocation': PermissionType.GEOLOCATION,
    'notifications': PermissionType.NOTIFICATIONS,
    'camera': PermissionType.VIDEO_CAPTURE,
    'microphone': PermissionType.AUDIO_CAPTURE,
    'clipboard-read': PermissionType.CLIPBOARD_READ_WRITE,
    'clipboard-write': PermissionType.CLIPBOARD_SANITIZED_WRITE,
    'midi': PermissionType.MIDI,
    'midi-sysex': PermissionType.MIDI_SYSEX,
    'background-sync': PermissionType.BACKGROUND_SYNC,
    'payment-handler': PermissionType.PAYMENT_HANDLER,
    'accelerometer': PermissionType.SENSORS,
    'gyroscope': PermissionType.SENSORS,
    'magnetometer': PermissionType.SENSORS,
    'ambient-light-sensor': PermissionType.SENSORS,
    'storage-access': PermissionType.STORAGE_ACCESS,
}


class BrowserContext(EventEmitter):
    """An isolated browsing session; ``browser.new_context()`` creates one."""

    def __init__(self, browser: Browser, context_id: str | None, options: dict[str, Any]) -> None:
        super().__init__()
        self._browser = browser
        self._context_id = context_id
        self._options = options
        self._pages: list[Page] = []
        self._closed = False
        self._default_timeout: float | None = None
        self._default_navigation_timeout: float | None = None
        self._routes: list[RouteEntry] = []
        self._init_scripts: list[str] = []
        self._bindings: list[tuple[str, Callable[..., Any], bool]] = []
        self._extra_http_headers: dict[str, str] = dict(options.get('extra_http_headers') or {})
        self._offline = bool(options.get('offline'))
        self._geolocation: dict[str, float] | None = options.get('geolocation')
        self._base_url: str | None = options.get('base_url')
        self._device_scale_factor: float = float(options.get('device_scale_factor') or 1)
        self._is_mobile: bool = bool(options.get('is_mobile'))
        self._has_touch: bool = bool(options.get('has_touch'))
        self._screen: dict[str, int] | None = (
            dict(options['screen']) if options.get('screen') else None
        )
        viewport = options.get('viewport', {'width': 1280, 'height': 720})
        self._viewport: dict[str, int] | None = (
            dict(viewport) if viewport and not options.get('no_viewport') else None
        )
        self._downloads_dir = Path(
            options.get('downloads_path') or tempfile.mkdtemp(prefix='pydoll-playwright-downloads-')
        )
        self._owns_downloads_dir = not options.get('downloads_path')
        self._tracing = None
        self._loop = asyncio.get_running_loop()

    def __repr__(self) -> str:
        return f'<BrowserContext id={self._context_id!r} pages={len(self._pages)}>'

    # ------------------------------------------------------------ setup

    async def _initialize(self) -> None:
        self._downloads_dir.mkdir(parents=True, exist_ok=True)
        await self._browser._chrome.execute_command(
            BrowserCommands.set_download_behavior(
                behavior=DownloadBehavior.ALLOW_AND_NAME,
                browser_context_id=self._context_id,
                download_path=str(self._downloads_dir),
                events_enabled=True,
            )
        )
        storage_state = self._options.get('storage_state')
        if storage_state:
            state = (
                json.loads(Path(storage_state).read_text(encoding='utf-8'))
                if isinstance(storage_state, (str, Path))
                else storage_state
            )
            if state.get('cookies'):
                await self.add_cookies(state['cookies'])
            for origin in state.get('origins', []):
                entries = {item['name']: item['value'] for item in origin.get('localStorage', [])}
                if entries:
                    self._init_scripts.append(
                        f'if (location.origin === {json.dumps(origin["origin"])}) {{'
                        f' for (const [k, v] of Object.entries({json.dumps(entries)}))'
                        ' localStorage.setItem(k, v); }'
                    )
        if self._options.get('permissions'):
            await self.grant_permissions(self._options['permissions'])

    def _default_timeout_value(self) -> float:
        return self._default_timeout if self._default_timeout is not None else DEFAULT_TIMEOUT_MS

    def _default_navigation_timeout_value(self) -> float:
        if self._default_navigation_timeout is not None:
            return self._default_navigation_timeout
        return self._default_timeout_value()

    async def _apply_to_page(self, page: Page) -> None:
        options = self._options
        if self._viewport:
            await page.set_viewport_size(self._viewport)
        if options.get('user_agent'):
            parsed = UserAgentParser.parse(options['user_agent'])
            await page._send(
                EmulationCommands.set_user_agent_override(
                    user_agent=parsed.reduced_user_agent or options['user_agent'],
                    platform=parsed.platform,
                    user_agent_metadata=parsed.user_agent_metadata,
                )
            )
        if options.get('locale'):
            await page._send(EmulationCommands.set_locale_override(locale=options['locale']))
            self._extra_http_headers.setdefault(
                'Accept-Language', _accept_language(options['locale'])
            )
        if options.get('timezone_id'):
            await page._send(
                EmulationCommands.set_timezone_override(timezone_id=options['timezone_id'])
            )
        if self._geolocation:
            await page._send(EmulationCommands.set_geolocation_override(**self._geolocation))
        if self._extra_http_headers:
            await page.set_extra_http_headers(self._extra_http_headers)
        if self._offline:
            await page._send({
                'method': 'Network.emulateNetworkConditions',
                'params': {
                    'offline': True,
                    'latency': 0,
                    'downloadThroughput': -1,
                    'uploadThroughput': -1,
                },
            })  # type: ignore[arg-type]
        if options.get('ignore_https_errors'):
            await page._send({
                'method': 'Security.setIgnoreCertificateErrors',
                'params': {'ignore': True},
            })  # type: ignore[arg-type]
        if options.get('bypass_csp'):
            await page._send(PageCommands.set_bypass_csp(enabled=True))
        if options.get('java_script_enabled') is False:
            await page._send({
                'method': 'Emulation.setScriptExecutionDisabled',
                'params': {'value': True},
            })  # type: ignore[arg-type]
        if (
            options.get('color_scheme')
            or options.get('reduced_motion')
            or options.get('forced_colors')
        ):
            await page.emulate_media(
                color_scheme=options.get('color_scheme'),
                reduced_motion=options.get('reduced_motion'),
                forced_colors=options.get('forced_colors'),
            )
        if self._has_touch:
            await page._send({
                'method': 'Emulation.setTouchEmulationEnabled',
                'params': {'enabled': True, 'maxTouchPoints': 5 if self._is_mobile else 10},
            })  # type: ignore[arg-type]
        if options.get('http_credentials'):
            await page._enable_http_credentials(options['http_credentials'])
        for script in self._init_scripts:
            await page._send(PageCommands.add_script_to_evaluate_on_new_document(source=script))
        for name, callback, with_source in self._bindings:
            await page._expose(name, callback, with_source)
        if self._routes:
            await page._enable_fetch()

    # ------------------------------------------------------------ pages

    async def new_page(self) -> Page:
        if self._closed:
            raise Error('Target page, context or browser has been closed')
        try:
            tab = await self._browser._chrome.new_tab(browser_context_id=self._context_id)
        except PydollException as error:
            raise translate(error) from error
        return await self._adopt(tab, opener=None, emit_popup=False)

    async def _adopt(self, tab: Tab, opener: Page | None, emit_popup: bool) -> Page:
        page = Page(self, tab, opener=opener)
        self._pages.append(page)
        await page._initialize()
        self.emit('page', page)
        if emit_popup and opener is not None:
            opener.emit('popup', page)
        return page

    @property
    def pages(self) -> list[Page]:
        return list(self._pages)

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def background_pages(self) -> list[Page]:
        return []

    @property
    def service_workers(self) -> list[Any]:
        return []

    @property
    def tracing(self) -> Any:
        raise Error('context.tracing is not supported by pydoll.playwright')

    @property
    def request(self) -> Any:
        raise Error('context.request (APIRequestContext) is not supported by pydoll.playwright')

    @property
    def clock(self) -> Any:
        raise Error('context.clock is not supported by pydoll.playwright')

    def set_default_timeout(self, timeout: float) -> None:
        self._default_timeout = timeout

    def set_default_navigation_timeout(self, timeout: float) -> None:
        self._default_navigation_timeout = timeout

    # ------------------------------------------------------------ cookies

    async def cookies(self, urls: str | Sequence[str] | None = None) -> list[dict[str, Any]]:
        try:
            raw = await self._browser._chrome.get_cookies(browser_context_id=self._context_id)
        except PydollException as error:
            raise translate(error) from error
        wanted = [urls] if isinstance(urls, str) else list(urls or [])
        result = []
        for cookie in raw:
            item = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie['domain'],
                'path': cookie['path'],
                'expires': cookie.get('expires', -1),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', False),
                'sameSite': cookie.get('sameSite', 'Lax'),
            }
            if wanted and not any(_cookie_matches(item, url) for url in wanted):
                continue
            result.append(item)
        return result

    async def add_cookies(self, cookies: Sequence[dict[str, Any]]) -> None:
        params = []
        for cookie in cookies:
            entry: dict[str, Any] = {'name': cookie['name'], 'value': cookie['value']}
            for key in ('url', 'domain', 'path', 'secure', 'httpOnly', 'sameSite', 'expires'):
                if cookie.get(key) is not None and cookie.get(key) != -1:
                    entry[key] = cookie[key]
            params.append(entry)
        try:
            await self._browser._chrome.set_cookies(params, browser_context_id=self._context_id)  # type: ignore[arg-type]
        except PydollException as error:
            raise translate(error) from error

    async def clear_cookies(self, **kwargs: Any) -> None:
        try:
            await self._browser._chrome.delete_all_cookies(browser_context_id=self._context_id)
        except PydollException as error:
            raise translate(error) from error

    async def storage_state(
        self, path: str | Path | None = None, indexed_db: bool | None = None
    ) -> dict[str, Any]:
        state: dict[str, Any] = {'cookies': await self.cookies(), 'origins': []}
        seen: set[str] = set()
        for page in self._pages:
            try:
                origin = await page.evaluate('() => location.origin')
                if not origin or origin in seen or origin == 'null':
                    continue
                seen.add(origin)
                items = await page.evaluate(
                    '() => Object.entries(localStorage).map(([name, value]) => ({ name, value }))'
                )
                if items:
                    state['origins'].append({'origin': origin, 'localStorage': items})
            except Error:
                continue
        if path is not None:
            Path(path).write_text(json.dumps(state, indent=2), encoding='utf-8')
        return state

    # ------------------------------------------------------------ settings

    async def grant_permissions(
        self, permissions: Sequence[str], origin: str | None = None
    ) -> None:
        mapped = []
        for permission in permissions:
            if permission not in _PERMISSIONS:
                raise Error(f'Unknown permission: {permission}')
            mapped.append(_PERMISSIONS[permission])
        try:
            await self._browser._chrome.grant_permissions(
                mapped, origin=origin, browser_context_id=self._context_id
            )
        except PydollException as error:
            raise translate(error) from error

    async def clear_permissions(self) -> None:
        try:
            await self._browser._chrome.reset_permissions(browser_context_id=self._context_id)
        except PydollException as error:
            raise translate(error) from error

    async def set_geolocation(self, geolocation: dict[str, float] | None) -> None:
        self._geolocation = dict(geolocation) if geolocation else None
        for page in self._pages:
            if self._geolocation:
                await page._send(EmulationCommands.set_geolocation_override(**self._geolocation))
            else:
                await page._send(EmulationCommands.set_geolocation_override())

    async def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        self._extra_http_headers = dict(headers)
        for page in self._pages:
            await page.set_extra_http_headers(headers)

    async def set_offline(self, offline: bool) -> None:
        self._offline = offline
        for page in self._pages:
            await page._send({
                'method': 'Network.emulateNetworkConditions',
                'params': {
                    'offline': offline,
                    'latency': 0,
                    'downloadThroughput': -1,
                    'uploadThroughput': -1,
                },
            })  # type: ignore[arg-type]

    async def add_init_script(
        self, script: str | None = None, path: str | Path | None = None
    ) -> None:
        source = script if script is not None else Path(str(path)).read_text(encoding='utf-8')
        self._init_scripts.append(source)
        for page in self._pages:
            await page._send(PageCommands.add_script_to_evaluate_on_new_document(source=source))

    async def expose_function(self, name: str, callback: Callable[..., Any]) -> None:
        self._bindings.append((name, callback, False))
        for page in self._pages:
            await page._expose(name, callback, False)

    async def expose_binding(
        self, name: str, callback: Callable[..., Any], handle: bool | None = None
    ) -> None:
        self._bindings.append((name, callback, True))
        for page in self._pages:
            await page._expose(name, callback, True)

    async def route(self, url: URLMatch, handler: RouteHandler, times: int | None = None) -> None:
        self._routes.append(make_entry(url, handler, times, self._base_url))
        for page in self._pages:
            await page._enable_fetch()

    async def unroute(self, url: URLMatch, handler: RouteHandler | None = None) -> None:
        self._routes = [
            entry
            for entry in self._routes
            if not (entry.matcher._match == url and (handler is None or entry.handler is handler))
        ]

    async def unroute_all(self, behavior: str | None = None) -> None:
        self._routes = []

    # ------------------------------------------------------------ events

    async def wait_for_event(
        self,
        event: str,
        predicate: Callable[[Any], Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        async with self.expect_event(event, predicate=predicate, timeout=timeout) as info:
            pass
        return await info.value

    def expect_event(
        self,
        event: str,
        predicate: Callable[[Any], Any] | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[Any]:
        deadline = Deadline(self._default_timeout_value() if timeout is None else timeout)
        future = create_future(self._loop)

        def listener(*args: Any) -> None:
            if future.done():
                return
            value = args[0] if args else None
            if predicate is not None and not predicate(value):
                return
            future.set_result(value)

        self.on(event, listener)

        async def guard() -> None:
            remaining = deadline.remaining_seconds()
            try:
                await asyncio.wait_for(
                    asyncio.shield(future), timeout=remaining
                ) if remaining is not None else await asyncio.shield(future)
            except asyncio.TimeoutError:
                if not future.done():
                    future.set_exception(deadline.error(f'waiting for event "{event}"'))
            except Exception:
                pass
            finally:
                self.remove_listener(event, listener)

        schedule(self._loop, guard())
        return EventContextManager(future)

    def expect_page(
        self, predicate: Callable[[Page], bool] | None = None, timeout: float | None = None
    ) -> EventContextManager[Page]:
        return self.expect_event('page', predicate=predicate, timeout=timeout)

    def expect_console_message(
        self, predicate: Any = None, timeout: float | None = None
    ) -> EventContextManager[Any]:
        return self.expect_event('console', predicate=predicate, timeout=timeout)

    # ------------------------------------------------------------ lifecycle

    async def close(self, reason: str | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        for page in list(self._pages):
            await page.close()
        if self._context_id is not None:
            try:
                await self._browser._chrome.delete_browser_context(self._context_id)
            except PydollException:
                pass
        self._browser._contexts = [
            context for context in self._browser._contexts if context is not self
        ]
        if self._owns_downloads_dir:
            shutil.rmtree(self._downloads_dir, ignore_errors=True)
        self.emit('close', self)

    def _on_page_closed(self, page: Page) -> None:
        self._pages = [item for item in self._pages if item is not page]

    async def new_cdp_session(self, page: Page) -> Any:
        raise Error('new_cdp_session is not supported; use page.tab.execute_command for raw CDP')


def _accept_language(locale: str) -> str:
    """Chrome-shaped Accept-Language for a locale (primary, language, English fallbacks)."""
    language = locale.split('-')[0]
    parts = [locale]
    if language != locale:
        parts.append(f'{language};q=0.9')
    if language != 'en':
        parts.extend(['en-US;q=0.8', 'en;q=0.7'])
    return ','.join(parts)


def _cookie_matches(cookie: dict[str, Any], url: str) -> bool:
    from urllib.parse import urlparse  # noqa: PLC0415

    parsed = urlparse(url)
    domain = cookie['domain'].lstrip('.')
    host = parsed.hostname or ''
    if not (host == domain or host.endswith('.' + domain)):
        return False
    if not (parsed.path or '/').startswith(cookie['path']):
        return False
    return not (cookie['secure'] and parsed.scheme != 'https')


__all__ = ['BrowserContext', 'RuntimeCommands']
