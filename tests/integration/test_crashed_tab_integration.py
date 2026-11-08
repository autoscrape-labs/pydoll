"""A tab whose renderer crashed fails fast instead of waiting out each command's timeout.

Chrome reports the crash with ``Inspector.targetCrashed`` on the tab's own
connection and stops answering every command that needs the renderer, so
without acting on the event each of them would wait the full 60 s.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pydoll.browser.tab import Tab
from pydoll.commands import PageCommands, RuntimeCommands
from pydoll.exceptions import TargetCrashed
from pydoll.protocol.network.events import NetworkEvent
from tests.integration._waits import wait_until


async def _crash(tab: Tab) -> None:
    await tab._connection_handler.execute_command_nowait(PageCommands.crash())


async def _evaluate(tab: Tab, expression: str) -> object:
    response = await tab.execute_script(f'return {expression}')
    return response['result']['result']['value']


@pytest.mark.asyncio
async def test_running_and_later_scripts_fail_at_once_when_the_renderer_crashes(browser, tab):
    await tab.go_to('data:text/html,<title>crash</title>')
    started = time.monotonic()
    running = asyncio.create_task(tab.execute_script('while (true) {}'))
    await asyncio.sleep(0.3)
    await _crash(tab)
    with pytest.raises(TargetCrashed):
        await running
    with pytest.raises(TargetCrashed):
        await tab.execute_script('return 1 + 1')
    assert time.monotonic() - started < 10

    other = await browser.new_tab(browser_context_id=tab.browser_context_id)
    assert await _evaluate(other, '1 + 1') == 2


@pytest.mark.asyncio
async def test_unawaited_script_cut_short_by_a_crash_raises_nothing_in_the_loop(tab, caplog):
    caplog.set_level(logging.ERROR, logger='asyncio')
    await tab.go_to('data:text/html,<title>crash</title>')
    handler = tab._connection_handler
    await handler.execute_command_nowait(RuntimeCommands.evaluate('while (true) {}'))
    await asyncio.sleep(0.3)
    await _crash(tab)
    await _wait_crashed(tab)
    await asyncio.sleep(0.1)
    assert [record for record in caplog.records if record.name == 'asyncio'] == []


@pytest.mark.asyncio
async def test_go_to_recovers_a_crashed_tab(tab):
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.go_to('data:text/html,<title>after</title>', timeout=10)
    assert await tab.title() == 'after'
    assert await _evaluate(tab, '1 + 1') == 2


@pytest.mark.asyncio
async def test_go_to_recovers_a_crashed_tab_that_had_page_events_on(tab):
    await tab.enable_page_events()
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.go_to('data:text/html,<title>after</title>', timeout=10)
    assert await tab.title() == 'after'
    assert tab.page_events_enabled is True


@pytest.mark.asyncio
async def test_refresh_loads_the_crashed_page_again(tab):
    await tab.go_to('data:text/html,<title>crashed page</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.refresh()
    assert await tab.title() == 'crashed page'


@pytest.mark.asyncio
async def test_a_crashed_tab_can_still_be_closed(browser, tab):
    await _crash(tab)
    await _wait_crashed(tab)
    await tab.close()
    targets = await browser.get_targets()
    assert tab.target_id not in [target['targetId'] for target in targets]


async def _wait_crashed(tab: Tab) -> None:
    async def crashed() -> bool:
        return tab._connection_handler.target_crashed

    await wait_until(crashed, timeout=15, message='the crash event never arrived')


@pytest.mark.asyncio
async def test_a_crashed_tab_whose_connection_dropped_recovers_with_its_domains(tab):
    """A session opened after the crash never hears that the renderer is back."""
    seen: list[str] = []
    await tab.enable_page_events()
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.REQUEST_WILL_BE_SENT,
        lambda event: seen.append(event['params']['request']['url']),
    )
    await tab.go_to('data:text/html,<title>before</title>')
    await _crash(tab)
    await _wait_crashed(tab)
    handler = tab._connection_handler
    await handler._ws_connection.close()
    await asyncio.wait_for(handler.wait_disconnected(), timeout=5)
    seen.clear()

    await tab.go_to('data:text/html,<title>after</title>', timeout=10)

    assert await tab.title() == 'after'
    assert seen


class _HeldImageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/held'):
            self.server.held_requested.set()
            self.server.release.wait(30)
            return
        body = b'<!doctype html><title>loading</title><img src="/held.png">'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def held_load_site():
    server = ThreadingHTTPServer(('127.0.0.1', 0), _HeldImageHandler)
    server.daemon_threads = True
    server.held_requested = threading.Event()
    server.release = threading.Event()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.release.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_a_go_to_waiting_for_the_load_fails_at_once_when_the_renderer_crashes(
    tab, held_load_site
):
    url = f'http://127.0.0.1:{held_load_site.server_address[1]}/'
    loading = asyncio.create_task(tab.go_to(url, timeout=30))

    async def image_requested() -> bool:
        return held_load_site.held_requested.is_set()

    await wait_until(image_requested, timeout=10, message='the page never asked for its image')
    await _crash(tab)

    with pytest.raises(TargetCrashed):
        await asyncio.wait_for(loading, timeout=15)

