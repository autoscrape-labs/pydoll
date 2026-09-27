"""Fixtures for the Playwright-compatible layer, all against real headless Chrome."""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.playwright.async_api import async_playwright

from _pages import PAGES, page_url


@pytest_asyncio.fixture
async def chrome(ci_chrome_options):
    """A started pydoll Chrome, stopped after the test."""
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        yield browser


@pytest_asyncio.fixture
async def engine_tab(chrome):
    """The first tab, navigated to the engine fixture page."""
    tab = (await chrome.get_opened_tabs())[0]
    await tab.go_to(page_url('playwright_engine.html'))
    return tab


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return

    def end_headers(self) -> None:
        if getattr(self, '_set_cookie', False):
            self.send_header('Set-Cookie', 'session=abc; Path=/')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith('/echo-headers'):
            body = str(dict(self.headers)).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith('/redirect'):
            self.send_response(302)
            self.send_header('Location', '/test_core_simple.html')
            self.end_headers()
            return
        if self.path.startswith('/set-cookie'):
            self._set_cookie = True
            self.path = '/test_core_simple.html'
        super().do_GET()


@pytest.fixture(scope='session')
def http_server():
    """Serve tests/integration/pages over HTTP on an ephemeral port."""
    handler = functools.partial(_QuietHandler, directory=str(PAGES))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()


@pytest_asyncio.fixture
async def playwright():
    async with async_playwright() as instance:
        yield instance


@pytest_asyncio.fixture
async def browser(playwright):
    instance = await playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu'])
    try:
        yield instance
    finally:
        await instance.close()


@pytest_asyncio.fixture
async def context(browser):
    instance = await browser.new_context()
    try:
        yield instance
    finally:
        await instance.close()


@pytest_asyncio.fixture
async def page(context):
    return await context.new_page()
