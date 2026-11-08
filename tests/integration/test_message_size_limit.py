from __future__ import annotations

import asyncio
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.tab import Tab
from pydoll.commands import PageCommands
from pydoll.exceptions import PydollException, WebSocketConnectionClosed
from pydoll.protocol.input.methods import InputMethod

LARGE_STRING = "'x'.repeat(512 * 1024)"


async def _evaluate(tab: Tab, expression: str) -> object:
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


LONG_URL_PAGE = b"""<!doctype html><title>long url</title>
<script>fetch('/long?q=' + 'a'.repeat(400 * 1024)).catch(() => {});</script>
<script src="/hold.js"></script>"""
"""A page that requests a URL larger than the test's message limit, then waits on a script.

Chrome puts the URL in ``Network.requestWillBeSent`` before the request goes
out. That event comes from the network service and the load event from the
renderer, with no order between them, so the server answers ``/hold.js``, which
holds the load event back, only some time after the long request has arrived.
"""

HOLD_AFTER_LONG_REQUEST = 2


class _LongUrlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/hold.js'):
            self.server.long_request_seen.wait(10)
            time.sleep(HOLD_AFTER_LONG_REQUEST)
            self._send(200, b'', 'text/javascript')
            return
        self._send(200, LONG_URL_PAGE, 'text/html')

    def handle_one_request(self):
        """Note the long request even though the server refuses its request line (414)."""
        line = self.rfile.peek(16)[:16] if hasattr(self.rfile, 'peek') else b''
        if line.startswith(b'GET /long'):
            self.server.long_request_seen.set()
        super().handle_one_request()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def long_url_site():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _LongUrlHandler)
    server.long_request_seen = threading.Event()
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
    ci_chrome_options, long_url_site
):
    """Runs in a new blank tab: the first tab may still be loading Chrome's new tab
    page, and a load event of it arriving late would end go_to before the test page
    sends anything."""
    ci_chrome_options.max_message_size = 256 * 1024
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        tab = await browser.new_tab()
        await tab.enable_network_events()
        started = time.monotonic()
        with pytest.raises(WebSocketConnectionClosed, match='max_message_size'):
            await tab.go_to(long_url_site, timeout=30)
        assert time.monotonic() - started < 10


STORM_PAGE = b"""<!doctype html><title>storm</title><script>
const body = 'x'.repeat(200000);
setInterval(() => { fetch('/sink', {method: 'POST', body}).catch(() => {}); }, 5);
</script>"""


class _StormHandler(BaseHTTPRequestHandler):
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
