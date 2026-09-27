"""Real-Chrome tests for the waits, the expect_* context managers, hover and double_click.

A throwaway HTTP server serves ``waiting.html``, whose timers remove, hide,
enable and append elements 300 ms after a click, and whose buttons fetch a
JSON endpoint or navigate, so every wait has something real to wait for.
"""

from __future__ import annotations

import asyncio
import json
import re
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import pytest_asyncio

from pydoll import RequestHandle, ResponseHandle
from pydoll.exceptions import WaitElementTimeout, WaitTimeout

PAGES = Path(__file__).parent / 'pages'


class _WaitingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PAGES), **kwargs)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get('Content-Length', 0))
        payload = json.loads(self.rfile.read(length) or b'{}')
        body = json.dumps({'total': 42, 'echo': payload}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('X-Served-By', 'waiting-test')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


@pytest.fixture(scope='module')
def waiting_server():
    server = ThreadingHTTPServer(('127.0.0.1', _free_port()), _WaitingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_address[1]}'
    finally:
        server.shutdown()
        server.server_close()


@pytest_asyncio.fixture
async def waiting_tab(tab, waiting_server):
    await tab.go_to(f'{waiting_server}/waiting.html')
    return tab


async def _start_timers(tab) -> None:
    await (await tab.find(id='start')).click()


class TestElementWaitStates:
    @pytest.mark.asyncio
    async def test_wait_until_hidden(self, waiting_tab):
        toggle = await waiting_tab.find(id='toggle')
        assert await toggle.is_visible()
        await _start_timers(waiting_tab)
        await toggle.wait_until(is_hidden=True, timeout=5)
        assert not await toggle.is_visible()

    @pytest.mark.asyncio
    async def test_wait_until_detached(self, waiting_tab):
        spinner = await waiting_tab.find(id='spinner')
        assert not await spinner.is_detached()
        await _start_timers(waiting_tab)
        await spinner.wait_until(is_detached=True, timeout=5)
        assert await spinner.is_detached()

    @pytest.mark.asyncio
    async def test_wait_until_enabled(self, waiting_tab):
        button = await waiting_tab.find(id='enable-me')
        await _start_timers(waiting_tab)
        await button.wait_until(is_enabled=True, timeout=5)
        assert await waiting_tab.wait_for_script(
            "!document.getElementById('enable-me').disabled", timeout=1
        )

    @pytest.mark.asyncio
    async def test_wait_until_times_out_when_the_state_never_comes(self, waiting_tab):
        spinner = await waiting_tab.find(id='spinner')
        with pytest.raises(WaitElementTimeout):
            await spinner.wait_until(is_detached=True, timeout=0.3)

    @pytest.mark.asyncio
    async def test_wait_until_rejects_no_condition(self, waiting_tab):
        spinner = await waiting_tab.find(id='spinner')
        with pytest.raises(ValueError):
            await spinner.wait_until()


class TestTabWaits:
    @pytest.mark.asyncio
    async def test_wait_for_absence_waits_for_the_element_to_go(self, waiting_tab):
        await _start_timers(waiting_tab)
        await waiting_tab.wait_for_absence(id='spinner', timeout=5)
        assert await waiting_tab.find(id='spinner', raise_exc=False) is None

    @pytest.mark.asyncio
    async def test_wait_for_absence_returns_at_once_when_nothing_matches(self, waiting_tab):
        await waiting_tab.wait_for_absence(class_name='never-there', timeout=5)

    @pytest.mark.asyncio
    async def test_wait_for_absence_times_out(self, waiting_tab):
        with pytest.raises(WaitTimeout):
            await waiting_tab.wait_for_absence(id='title', timeout=0.3)

    @pytest.mark.asyncio
    async def test_wait_for_script_returns_the_truthy_value(self, waiting_tab):
        await _start_timers(waiting_tab)
        assert await waiting_tab.wait_for_script('window.appReady', timeout=5) is True
        assert await waiting_tab.wait_for_script("return document.title", timeout=1) == (
            'Waiting fixtures'
        )

    @pytest.mark.asyncio
    async def test_wait_for_script_times_out(self, waiting_tab):
        with pytest.raises(WaitTimeout):
            await waiting_tab.wait_for_script('window.neverSet', timeout=0.3)

    @pytest.mark.asyncio
    async def test_wait_for_url_after_a_navigation(self, waiting_tab):
        await (await waiting_tab.find(id='go-next')).click()
        url = await waiting_tab.wait_for_url('**/waiting_next.html', timeout=5)
        assert url.endswith('/waiting_next.html')
        assert await (await waiting_tab.find(id='next-title')).text() == 'Arrived'

    @pytest.mark.asyncio
    async def test_wait_for_url_sees_push_state_and_takes_regex_and_callables(self, waiting_tab):
        await (await waiting_tab.find(id='push-state')).click()
        assert (await waiting_tab.wait_for_url(re.compile(r'/checkout/\d+$'), timeout=5)).endswith(
            '/app/checkout/42'
        )
        await waiting_tab.wait_for_url(lambda url: 'checkout' in url, timeout=1)

    @pytest.mark.asyncio
    async def test_wait_for_url_times_out(self, waiting_tab):
        with pytest.raises(WaitTimeout):
            await waiting_tab.wait_for_url('**/nowhere', timeout=0.3)

    @pytest.mark.asyncio
    async def test_wait_for_network_idle_waits_for_a_fetch_to_finish(self, waiting_tab):
        await (await waiting_tab.find(id='fetch-data')).click()
        await waiting_tab.wait_for_network_idle(idle_time=0.2, timeout=5)
        assert await (await waiting_tab.find(id='title')).text() == 'total 42'
        assert not waiting_tab.network_events_enabled

    @pytest.mark.asyncio
    async def test_wait_for_network_idle_is_immediate_on_a_quiet_page(self, waiting_tab):
        loop = asyncio.get_running_loop()
        started = loop.time()
        await waiting_tab.wait_for_network_idle(idle_time=0.1, timeout=5)
        assert loop.time() - started < 1


class TestExpectContextManagers:
    @pytest.mark.asyncio
    async def test_expect_response_captures_status_headers_and_json(self, waiting_tab):
        async with waiting_tab.expect_response('**/api/data') as response:
            await (await waiting_tab.find(id='fetch-data')).click()
        assert isinstance(response, ResponseHandle)
        assert response.ok and response.status == 200
        assert response.url.endswith('/api/data')
        assert response.headers['X-Served-By'] == 'waiting-test'
        assert response.mime_type == 'application/json'
        assert response.json() == {'total': 42, 'echo': {'q': 'prices'}}
        assert b'"total": 42' in response.body()
        assert not waiting_tab.network_events_enabled

    @pytest.mark.asyncio
    async def test_expect_response_leaves_network_events_on_when_they_were_on(self, waiting_tab):
        await waiting_tab.enable_network_events()
        async with waiting_tab.expect_response(re.compile(r'/api/data$')) as response:
            await (await waiting_tab.find(id='fetch-data')).click()
        assert response.status == 200
        assert waiting_tab.network_events_enabled
        await waiting_tab.disable_network_events()

    @pytest.mark.asyncio
    async def test_expect_response_handle_is_empty_inside_the_block(self, waiting_tab):
        async with waiting_tab.expect_response('**/api/data') as response:
            with pytest.raises(WaitTimeout):
                response.status
            await (await waiting_tab.find(id='fetch-data')).click()
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_expect_response_times_out_when_nothing_matches(self, waiting_tab):
        with pytest.raises(WaitTimeout):
            async with waiting_tab.expect_response('**/api/other', timeout=0.5):
                await (await waiting_tab.find(id='fetch-data')).click()

    @pytest.mark.asyncio
    async def test_expect_response_captures_an_error_status_with_its_body(self, waiting_tab):
        async with waiting_tab.expect_response('**/api/missing') as response:
            await (await waiting_tab.find(id='fetch-missing')).click()
        assert response.status == 404
        assert not response.ok
        assert 'Error response' in response.text()

    @pytest.mark.asyncio
    async def test_expect_request_captures_method_headers_and_post_data(self, waiting_tab):
        async with waiting_tab.expect_request('**/api/data') as request:
            await (await waiting_tab.find(id='fetch-data')).click()
        assert isinstance(request, RequestHandle)
        assert request.method == 'POST'
        assert request.url.endswith('/api/data')
        assert request.headers['Content-Type'] == 'application/json'
        assert json.loads(request.post_data or '{}') == {'q': 'prices'}
        assert request.resource_type == 'Fetch'
        assert request.request_id

    @pytest.mark.asyncio
    async def test_expect_request_times_out(self, waiting_tab):
        with pytest.raises(WaitTimeout):
            async with waiting_tab.expect_request('**/api/other', timeout=0.5):
                pass

    @pytest.mark.asyncio
    async def test_expect_navigation_waits_for_the_new_page_to_load(self, waiting_tab):
        async with waiting_tab.expect_navigation():
            await (await waiting_tab.find(id='go-next')).click()
        assert (await waiting_tab.current_url()).endswith('/waiting_next.html')
        assert await (await waiting_tab.find(id='next-title', timeout=1)).text() == 'Arrived'
        assert not waiting_tab.page_events_enabled

    @pytest.mark.asyncio
    async def test_expect_navigation_can_require_a_url(self, waiting_tab):
        async with waiting_tab.expect_navigation(url='**/waiting_next.html'):
            await (await waiting_tab.find(id='go-next')).click()
        with pytest.raises(WaitTimeout):
            async with waiting_tab.expect_navigation(url='**/elsewhere', timeout=0.5):
                pass


class TestHoverAndDoubleClick:
    @pytest.mark.asyncio
    async def test_hover_fires_mouseover(self, waiting_tab):
        target = await waiting_tab.find(id='hover-target')
        await target.hover()
        assert await (await waiting_tab.find(id='hover-result')).text() == 'hovered'

    @pytest.mark.asyncio
    async def test_hover_humanized_moves_the_tracked_mouse(self, waiting_tab):
        target = await waiting_tab.find(id='hover-target')
        await target.hover(humanize=True)
        assert await (await waiting_tab.find(id='hover-result')).text() == 'hovered'

    @pytest.mark.asyncio
    async def test_double_click_fires_dblclick_and_two_clicks(self, waiting_tab):
        target = await waiting_tab.find(id='dbl-target')
        await target.double_click()
        assert await (await waiting_tab.find(id='dbl-result')).text() == '1'
        assert await (await waiting_tab.find(id='click-result')).text() == '2'

    @pytest.mark.asyncio
    async def test_double_click_humanized(self, waiting_tab):
        target = await waiting_tab.find(id='dbl-target')
        await target.double_click(humanize=True)
        assert await (await waiting_tab.find(id='dbl-result')).text() == '1'
