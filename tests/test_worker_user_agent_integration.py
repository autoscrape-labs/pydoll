"""Integration tests for User-Agent override propagation into worker contexts.

A spoofed Windows User-Agent must be reflected not only in the page but also
inside dedicated workers and service workers, which run in separate CDP targets.
The discriminating signals are navigator.platform and navigator.userAgentData:
without per-worker propagation they leak the real operating system, producing
the inconsistency that bot detectors look for.

Pages are served over loopback because both Service Worker registration and
navigator.userAgentData require a secure context.
"""

import asyncio
import http.server
import socket
import threading
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome

PAGES_DIR = Path(__file__).parent / 'pages' / 'worker_ua'

SPOOFED_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _wait_for_server(host: str, port: int, timeout: float = 5.0) -> None:
    """Block until the server at host:port accepts a TCP connection."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f'Server {host}:{port} not ready within {timeout}s')


@pytest.fixture(scope='module')
def worker_server():
    """Serve the worker test pages over loopback (a secure context)."""

    class _Handler(_SilentHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(PAGES_DIR), **kwargs)

    server = http.server.HTTPServer(('127.0.0.1', 0), _Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _wait_for_server('127.0.0.1', port)

    yield port

    server.shutdown()


async def _wait_for_worker_result(tab, expression: str, timeout: float = 15.0) -> dict:
    """Poll a page global until the worker has reported its navigator snapshot."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        response = await tab.execute_script(f'return {expression}', return_by_value=True)
        value = response['result']['result'].get('value')
        if value:
            return value
        await asyncio.sleep(0.1)
    raise AssertionError(f'Timed out waiting for {expression}')


class TestWorkerUserAgentOverride:
    """Spoofed User-Agent must reach worker contexts, not just the page."""

    @pytest.mark.asyncio
    async def test_dedicated_worker_inherits_spoofed_user_agent(
        self, ci_chrome_options, worker_server
    ):
        ci_chrome_options.add_argument(f'--user-agent={SPOOFED_UA}')
        url = f'http://127.0.0.1:{worker_server}/main.html'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            result = await _wait_for_worker_result(tab, 'window.__dedicatedResult')

            assert result['uaDataPlatform'] == 'Windows'
            assert result['platform'] == 'Win32'
            assert 'Windows NT 10.0' in result['userAgent']

    @pytest.mark.asyncio
    async def test_service_worker_inherits_spoofed_user_agent(
        self, ci_chrome_options, worker_server
    ):
        ci_chrome_options.add_argument(f'--user-agent={SPOOFED_UA}')
        url = f'http://127.0.0.1:{worker_server}/main.html'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(url)

            result = await _wait_for_worker_result(tab, 'window.__serviceWorkerResult')

            assert result['uaDataPlatform'] == 'Windows'
            assert result['platform'] == 'Win32'
            assert 'Windows NT 10.0' in result['userAgent']
