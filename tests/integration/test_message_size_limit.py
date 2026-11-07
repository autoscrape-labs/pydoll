"""The CDP message size limit set on the browser options reaches every connection.

A page decides how large some CDP messages are (a POST body in
``Network.requestWillBeSent``, a WebSocket frame), so the limit has to apply to
the tab connections Pydoll opens internally, not only to the browser one.
"""

from __future__ import annotations

import asyncio
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.commands import PageCommands
from pydoll.browser.tab import Tab
from pydoll.exceptions import PydollException, WebSocketConnectionClosed
from pydoll.protocol.input.methods import InputMethod

LARGE_STRING = "'x'.repeat(512 * 1024)"


async def _evaluate(tab: Tab, expression: str) -> object:
    """Run a script on the tab and return the value it produced."""
    response = await tab.execute_script(f'return {expression}')
    return response['result']['result']['value']


@pytest.mark.asyncio
async def test_tab_connection_closes_on_a_message_over_the_configured_limit(ci_chrome_options):
    ci_chrome_options.max_message_size = 256 * 1024
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        assert await _evaluate(tab, '1 + 1') == 2
        with pytest.raises(WebSocketConnectionClosed, match='max_message_size'):
            await _evaluate(tab, LARGE_STRING)
        assert await _evaluate(tab, '2 + 2') == 4


@pytest.mark.asyncio
async def test_tab_connection_accepts_the_same_message_under_the_default_limit(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        value = await _evaluate(tab, LARGE_STRING)
        assert value == 'x' * (512 * 1024)


UPLOAD_PAGE = b"""<!doctype html><title>upload</title>
<script>fetch('/upload', {method: 'POST', body: 'y'.repeat(1024 * 1024)});</script>
<img src="/slow.png">"""


class _UploadHandler(BaseHTTPRequestHandler):
    """Serve a page that posts a large body while an image holds its load event."""

    def do_GET(self):
        if self.path == '/slow.png':
            time.sleep(2)
            self._send(404, b'', 'image/png')
            return
        self._send(200, UPLOAD_PAGE, 'text/html')

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self._send(200, b'ok', 'text/plain')

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def upload_site():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _UploadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_go_to_raises_at_once_when_the_page_sends_an_oversized_message(
    ci_chrome_options, upload_site
):
    ci_chrome_options.max_message_size = 256 * 1024
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        started = time.monotonic()
        with pytest.raises(WebSocketConnectionClosed, match='max_message_size'):
            await tab.go_to(upload_site, timeout=30)
        assert time.monotonic() - started < 10
        assert await _evaluate(tab, '1 + 1') == 2


STORM_PAGE = b"""<!doctype html><title>storm</title><script>
const body = 'x'.repeat(200000);
setInterval(() => { fetch('/sink', {method: 'POST', body}).catch(() => {}); }, 5);
</script>"""


class _StormHandler(BaseHTTPRequestHandler):
    """Serve a page that keeps posting bodies larger than the test's message limit."""

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(STORM_PAGE)))
        self.end_headers()
        self.wfile.write(STORM_PAGE)

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def storm_site():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _StormHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}/'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_commands_amid_repeated_oversized_messages_raise_only_pydoll_errors(
    ci_chrome_options, storm_site
):
    """Each oversized message drops the connection, and every reconnect enables
    Network again while the page keeps posting: commands may fail, but only
    with Pydoll errors, and none is left pending."""
    ci_chrome_options.max_message_size = 64 * 1024
    move = {
        'method': InputMethod.DISPATCH_MOUSE_EVENT,
        'params': {'type': 'mouseMoved', 'x': 10, 'y': 10},
    }
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.enable_page_events()
        await tab._connection_handler.execute_command_nowait(PageCommands.navigate(storm_site))
        foreign: list[BaseException] = []
        for index in range(300):
            try:
                if index % 2:
                    await tab._connection_handler.execute_command_nowait(dict(move))
                else:
                    await tab.execute_script('return 1')
            except PydollException:
                pass
            except Exception as error:
                foreign.append(error)
            await asyncio.sleep(0.002)
        assert foreign == []
        await asyncio.sleep(0.5)
        assert tab._connection_handler._command_manager._pending_commands == {}
