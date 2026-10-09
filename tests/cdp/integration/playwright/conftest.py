"""Fixtures for the Playwright-compatible layer, all against real headless Chrome.

Playwright's own model applies: one browser per pytest worker, one context per
test. The ``page`` fixture is what most tests take; ``pw_browser`` and
``playwright`` exist for the tests that exercise launching and closing.
"""

from __future__ import annotations

import functools
import http.server
import threading

import pytest
import pytest_asyncio

from pydoll.playwright.async_api import async_playwright

from _pages import PAGES, page_url


@pytest_asyncio.fixture
async def engine_tab(tab):
    """The shared pydoll tab, navigated to the engine fixture page."""
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


@pytest_asyncio.fixture(scope='session')
async def playwright():
    async with async_playwright() as instance:
        yield instance


@pytest_asyncio.fixture(scope='session')
async def pw_browser(playwright):
    """One Playwright-API browser per worker; tests isolate themselves with a context."""
    instance = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
        timeout=60_000,
    )
    try:
        yield instance
    finally:
        await instance.close()


@pytest_asyncio.fixture
async def context(pw_browser):
    instance = await pw_browser.new_context()
    try:
        yield instance
    finally:
        await instance.close()


@pytest_asyncio.fixture
async def page(context):
    return await context.new_page()
