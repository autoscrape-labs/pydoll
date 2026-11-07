"""A tab that reconnects keeps the event domains it had on.

A new WebSocket is a new CDP session, and domain state belongs to the session,
so after a dropped connection Chrome has Network, Fetch and Page off again
while the tab still reports them on. Callbacks would stop firing, request
interception would stop, and go_to would wait for a load event never sent.
"""

from __future__ import annotations

import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pydoll.browser.tab import Tab
from pydoll.commands import RuntimeCommands
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.events import NetworkEvent
from tests.integration._waits import wait_until

PAGE = b'<!doctype html><title>t</title><img src="/pixel.png">'


class _PageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGE if not self.path.endswith('.png') else b''
        self.send_response(200 if body else 404)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def site():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _PageHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


async def _drop_tab_connection(tab: Tab) -> None:
    """Close the tab's WebSocket the way a network interruption would."""
    handler = tab._connection_handler
    await handler._ws_connection.close()
    await asyncio.wait_for(handler.wait_disconnected(), timeout=5)


async def _wait_for(condition, timeout: float = 5.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not condition():
        assert loop.time() < deadline, 'condition not met in time'
        await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_network_events_and_interception_survive_a_dropped_connection(tab, site):
    seen: list[str] = []
    paused: list[str] = []

    async def intercept(event):
        paused.append(event['params']['request']['url'])
        await tab.continue_request(event['params']['requestId'])

    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.REQUEST_WILL_BE_SENT, lambda e: seen.append(e['params']['request']['url'])
    )
    await tab.enable_fetch_events()
    await tab.on(FetchEvent.REQUEST_PAUSED, intercept)
    await tab.go_to(f'{site}/before')
    await _wait_for(lambda: len(paused) >= 2)

    await _drop_tab_connection(tab)
    seen.clear()
    paused.clear()
    await tab.go_to(f'{site}/after')
    await _wait_for(lambda: len(paused) >= 2)

    assert f'{site}/after' in seen
    assert f'{site}/after' in paused
    assert tab.network_events_enabled is True
    assert tab.fetch_events_enabled is True


@pytest.mark.asyncio
async def test_go_to_still_sees_the_load_event_after_a_dropped_connection(tab):
    await tab.enable_page_events()
    await tab.go_to('data:text/html,<title>before</title>', timeout=5)
    await _drop_tab_connection(tab)
    await tab.go_to('data:text/html,<title>after</title>', timeout=5)
    assert await tab.title() == 'after'


@pytest.mark.asyncio
async def test_a_tab_with_a_dialog_open_still_answers_after_a_dropped_connection(browser):
    """The new session's Page.enable waits for the dialog; what the browser answers must not.

    The wait for the enables is shortened so the test leaves room for a slow
    reconnect (Windows runners) within its own timeouts.
    """
    tab = await browser.new_tab()
    tab._connection_handler._RESTORE_ANSWER_TIMEOUT = 0.5
    await tab.enable_page_events()
    await tab._connection_handler.execute_command_nowait(RuntimeCommands.evaluate("alert('x')"))
    await wait_until(tab.has_dialog, timeout=5, message='the dialog never opened')
    await _drop_tab_connection(tab)

    cookies = await asyncio.wait_for(tab.get_cookies(), timeout=5)
    await asyncio.wait_for(tab.close(), timeout=5)

    assert cookies == []
    assert tab.target_id not in [target['targetId'] for target in await browser.get_targets()]

