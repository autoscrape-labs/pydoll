"""Playwright, BrowserType and the ``async_playwright()`` entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import PydollException
from pydoll.playwright._browser import Browser, build_options
from pydoll.playwright._browser_context import BrowserContext
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._selectors import set_test_id_attribute_name

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

    def __init__(self, name: str) -> None:
        self._name = name
        self._owned: set[int] = set()

    def __repr__(self) -> str:
        return f'<BrowserType name={self._name}>'

    @property
    def name(self) -> str:
        return self._name

    @property
    def executable_path(self) -> str:
        return ''

    def _owns_process(self, browser: Browser) -> bool:
        return id(browser) in self._owned

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
        self._owned.add(id(browser))
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
        self._owned.add(id(browser))
        await browser._initialize(initial_tab)
        context = await browser._default_browser_context(context_kwargs)
        await context._adopt(initial_tab, opener=None, emit_popup=False)
        original_close = context.close

        async def close_browser(reason: str | None = None) -> None:
            await original_close(reason=reason)
            await browser.close()

        context.close = close_browser
        return context

    async def connect_over_cdp(
        self,
        endpoint_url: str,
        timeout: float | None = None,
        slow_mo: float | None = None,
        headers: dict[str, str] | None = None,
    ) -> Browser:
        self._check_supported()
        chrome = Chrome()
        try:
            initial_tab = await chrome.connect(endpoint_url)
        except PydollException as error:
            raise translate(error) from error
        browser = Browser(self, chrome)
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

    async def register(
        self,
        name: str,
        script: str | None = None,
        path: str | Path | None = None,
        content_script: bool | None = None,
    ) -> None:
        raise Error('Custom selector engines are not supported by pydoll.playwright')

    def set_test_id_attribute(self, attribute_name: str) -> None:
        set_test_id_attribute_name(attribute_name)


class Playwright:
    """The object yielded by ``async_playwright()``."""

    def __init__(self) -> None:
        self.chromium = BrowserType('chromium')
        self.firefox = BrowserType('firefox')
        self.webkit = BrowserType('webkit')
        self.selectors = Selectors()
        self.devices: dict[str, dict[str, Any]] = dict(_DEVICES)
        self._browsers: list[Browser] = []

    @property
    def request(self) -> Any:
        raise Error('playwright.request (APIRequestContext) is not supported by pydoll.playwright')

    async def stop(self) -> None:
        for browser_type in (self.chromium,):
            browser_type._owned.clear()


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
