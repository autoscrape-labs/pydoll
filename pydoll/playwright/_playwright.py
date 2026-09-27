"""Playwright, BrowserType and the ``async_playwright()`` entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

import aiohttp

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import PydollException
from pydoll.playwright._browser import Browser, build_options
from pydoll.playwright._browser_context import BrowserContext
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._selectors import DEFAULT_TEST_ID_ATTRIBUTE

_LAUNCH_OPTION_NAMES = {
    'executable_path',
    'channel',
    'args',
    'ignore_default_args',
    'handle_sigint',
    'handle_sigterm',
    'handle_sighup',
    'timeout',
    'env',
    'headless',
    'devtools',
    'proxy',
    'downloads_path',
    'slow_mo',
    'traces_dir',
    'chromium_sandbox',
    'firefox_user_prefs',
}


class BrowserType:
    """``playwright.chromium``: launches or connects to a Chromium driven by pydoll."""

    def __init__(self, name: str, selectors: Selectors) -> None:
        self._selectors = selectors
        self._name = name
        self._launched: list[Browser] = []
        self._attached: list[Browser] = []

    def __repr__(self) -> str:
        return f'<BrowserType name={self._name}>'

    @property
    def name(self) -> str:
        return self._name

    @property
    def executable_path(self) -> str:
        return ''

    def _owns_process(self, browser: Browser) -> bool:
        return any(candidate is browser for candidate in self._launched)

    def _forget(self, browser: Browser) -> None:
        self._launched = [candidate for candidate in self._launched if candidate is not browser]
        self._attached = [candidate for candidate in self._attached if candidate is not browser]

    async def _close_all(self) -> None:
        """Stop every browser launched here and disconnect from the attached ones."""
        for browser in [*self._launched, *self._attached]:
            await browser.close()

    def _check_supported(self) -> None:
        if self._name != 'chromium':
            raise Error(
                f'BrowserType "{self._name}" is not available in pydoll.playwright; '
                'only chromium is supported. '
                'Point chromium.launch(executable_path=...) at a Chromium-based binary instead.'
            )

    async def launch(
        self,
        executable_path: str | Path | None = None,
        channel: str | None = None,
        args: Sequence[str] | None = None,
        ignore_default_args: bool | Sequence[str] | None = None,
        handle_sigint: bool | None = None,
        handle_sigterm: bool | None = None,
        handle_sighup: bool | None = None,
        timeout: float | None = None,
        env: dict[str, Any] | None = None,
        headless: bool | None = None,
        devtools: bool | None = None,
        proxy: dict[str, Any] | None = None,
        downloads_path: str | Path | None = None,
        slow_mo: float | None = None,
        traces_dir: str | Path | None = None,
        chromium_sandbox: bool | None = None,
        firefox_user_prefs: dict[str, Any] | None = None,
    ) -> Browser:
        self._check_supported()
        options = build_options(
            headless=headless if headless is not None else True,
            args=list(args or []),
            executable_path=executable_path,
            proxy=proxy,
            user_data_dir=None,
            ignore_default_args=ignore_default_args,
            downloads_path=downloads_path,
            chromium_sandbox=chromium_sandbox,
            timeout=timeout,
        )
        chrome = Chrome(options=options)
        try:
            initial_tab = await chrome.start()
        except PydollException as error:
            raise translate(error) from error
        browser = Browser(self, chrome)
        self._launched.append(browser)
        await browser._initialize(initial_tab)
        return browser

    async def launch_persistent_context(
        self,
        user_data_dir: str | Path,
        **kwargs: Any,
    ) -> BrowserContext:
        self._check_supported()
        launch_kwargs = {key: value for key, value in kwargs.items() if key in _LAUNCH_OPTION_NAMES}
        context_kwargs = {
            key: value for key, value in kwargs.items() if key not in _LAUNCH_OPTION_NAMES
        }
        options = build_options(
            headless=launch_kwargs.get('headless', True),
            args=list(launch_kwargs.get('args') or []),
            executable_path=launch_kwargs.get('executable_path'),
            proxy=launch_kwargs.get('proxy'),
            user_data_dir=user_data_dir,
            ignore_default_args=launch_kwargs.get('ignore_default_args'),
            downloads_path=launch_kwargs.get('downloads_path'),
            chromium_sandbox=launch_kwargs.get('chromium_sandbox'),
            timeout=launch_kwargs.get('timeout'),
        )
        chrome = Chrome(options=options)
        try:
            initial_tab = await chrome.start()
        except PydollException as error:
            raise translate(error) from error
        browser = Browser(self, chrome)
        self._launched.append(browser)
        await browser._initialize(initial_tab)
        context = await browser._default_browser_context(context_kwargs)
        await context._adopt(initial_tab, opener=None, emit_popup=False)
        context._owned_browser = browser
        return context

    async def connect_over_cdp(
        self,
        endpoint_url: str,
        timeout: float | None = None,
        slow_mo: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> Browser:
        """Attach to a running Chromium by its DevTools ``ws://`` or ``http://`` endpoint.

        An HTTP endpoint is resolved through ``/json/version`` the way Playwright
        does, so ``http://localhost:9222`` works as well as the browser socket URL.
        """
        self._check_supported()
        ws_endpoint = await _websocket_endpoint(endpoint_url, timeout, headers)
        chrome = Chrome()
        try:
            initial_tab = await chrome.connect(ws_endpoint)
        except PydollException as error:
            raise translate(error) from error
        browser = Browser(self, chrome)
        self._attached.append(browser)
        await browser._initialize(initial_tab)
        context = await browser._default_browser_context({})
        try:
            for tab in await chrome.get_opened_tabs():
                await context._adopt(tab, opener=None, emit_popup=False)
        except PydollException as error:
            raise translate(error) from error
        return browser

    async def connect(self, ws_endpoint: str, **kwargs: Any) -> Browser:
        raise Error(
            'connect() targets a Playwright server; '
            'use connect_over_cdp() with a CDP endpoint instead'
        )


class Selectors:
    """``playwright.selectors``: only the test id attribute is configurable."""

    def __init__(self) -> None:
        self._test_id_attribute_name = DEFAULT_TEST_ID_ATTRIBUTE

    async def register(
        self,
        name: str,
        script: str | None = None,
        path: str | Path | None = None,
        content_script: bool | None = None,
    ) -> None:
        raise Error('Custom selector engines are not supported by pydoll.playwright')

    def set_test_id_attribute(self, attribute_name: str) -> None:
        self._test_id_attribute_name = attribute_name


class Playwright:
    """The object yielded by ``async_playwright()``."""

    def __init__(self) -> None:
        self.selectors = Selectors()
        self.chromium = BrowserType('chromium', self.selectors)
        self.firefox = BrowserType('firefox', self.selectors)
        self.webkit = BrowserType('webkit', self.selectors)
        self.devices: dict[str, dict[str, Any]] = dict(_DEVICES)

    @property
    def request(self) -> Any:
        raise Error('playwright.request (APIRequestContext) is not supported by pydoll.playwright')

    async def stop(self) -> None:
        """Close every browser this Playwright launched or attached to."""
        for browser_type in (self.chromium, self.firefox, self.webkit):
            await browser_type._close_all()


class PlaywrightContextManager:
    """``async with async_playwright() as p:`` and ``await async_playwright().start()``."""

    def __init__(self) -> None:
        self._playwright: Playwright | None = None

    async def __aenter__(self) -> Playwright:
        self._playwright = Playwright()
        return self._playwright

    async def start(self) -> Playwright:
        self._playwright = Playwright()
        return self._playwright

    async def __aexit__(self, *args: Any) -> None:
        if self._playwright is not None:
            await self._playwright.stop()


def async_playwright() -> PlaywrightContextManager:
    return PlaywrightContextManager()


async def _websocket_endpoint(
    endpoint_url: str, timeout: float | None, headers: dict[str, str] | None
) -> str:
    """The browser WebSocket URL behind a DevTools endpoint given as ``ws://`` or ``http://``."""
    if urlsplit(endpoint_url).scheme not in {'http', 'https'}:
        return endpoint_url
    version_url = f'{endpoint_url.rstrip("/")}/json/version'
    client_timeout = aiohttp.ClientTimeout(total=timeout / 1000) if timeout else None
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=client_timeout) as session:
            async with session.get(version_url) as response:
                response.raise_for_status()
                data = await response.json()
    except (aiohttp.ClientError, TimeoutError) as error:
        raise Error(f'Could not reach the DevTools endpoint at {version_url}: {error}') from error
    try:
        return str(data['webSocketDebuggerUrl'])
    except (KeyError, TypeError) as error:
        raise Error(f'{version_url} did not report a webSocketDebuggerUrl') from error


_DEVICES: dict[str, dict[str, Any]] = {
    'Desktop Chrome': {
        'user_agent': '',
        'viewport': {'width': 1280, 'height': 720},
        'device_scale_factor': 1,
        'is_mobile': False,
        'has_touch': False,
        'default_browser_type': 'chromium',
    },
    'iPhone 13': {
        'user_agent': (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 '
            '(KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ),
        'viewport': {'width': 390, 'height': 664},
        'device_scale_factor': 3,
        'is_mobile': True,
        'has_touch': True,
        'default_browser_type': 'webkit',
    },
    'Pixel 7': {
        'user_agent': (
            'Mozilla/5.0 (Linux; Android 14; Pixel 7 Build/UP1A.231105.001; wv) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 '
            'Mobile Safari/537.36'
        ),
        'viewport': {'width': 412, 'height': 839},
        'device_scale_factor': 2.625,
        'is_mobile': True,
        'has_touch': True,
        'default_browser_type': 'chromium',
    },
}
