"""Tab waits and expect_* context managers against the in-memory FakeConnection.

The fake answers commands and records the callbacks a Tab registers, so a
test drives the events by calling those callbacks, the way the browser would.
"""

from __future__ import annotations

import base64
import re

import pytest

from pydoll.browser.tab import RequestHandle, ResponseHandle
from pydoll.exceptions import WaitTimeout


def _fire(fake_conn, event_name: str, params: dict) -> None:
    for callback in fake_conn.callbacks_for(event_name):
        callback({'method': event_name, 'params': params})


class TestWaitForUrl:
    @pytest.mark.asyncio
    async def test_returns_the_matching_url(self, fake_conn, fake_tab):
        fake_conn.set_response('Runtime.evaluate', {'result': {'value': 'https://shop.test/checkout/7'}})
        assert await fake_tab.wait_for_url('**/checkout/*', timeout=1) == 'https://shop.test/checkout/7'
        assert await fake_tab.wait_for_url(re.compile(r'checkout/\d'), timeout=1)
        assert await fake_tab.wait_for_url(lambda url: url.endswith('/7'), timeout=1)

    @pytest.mark.asyncio
    async def test_times_out_when_the_url_never_matches(self, fake_conn, fake_tab):
        fake_conn.set_response('Runtime.evaluate', {'result': {'value': 'https://shop.test/cart'}})
        with pytest.raises(WaitTimeout):
            await fake_tab.wait_for_url('**/checkout/*', timeout=0.05)


class TestWaitForScript:
    @pytest.mark.asyncio
    async def test_returns_the_first_truthy_value(self, fake_conn, fake_tab):
        fake_conn.set_response('Runtime.evaluate', {'result': {'value': {'ready': True}}})
        assert await fake_tab.wait_for_script('window.app', timeout=1) == {'ready': True}
        sent = fake_conn.last_command('Runtime.evaluate')['params']
        assert sent['expression'] == 'window.app'
        assert sent['returnByValue'] is True

    @pytest.mark.asyncio
    async def test_times_out_while_falsy(self, fake_conn, fake_tab):
        fake_conn.set_response('Runtime.evaluate', {'result': {'value': 0}})
        with pytest.raises(WaitTimeout):
            await fake_tab.wait_for_script('window.count', timeout=0.05)


class TestWaitForAbsence:
    @pytest.mark.asyncio
    async def test_returns_when_nothing_matches(self, fake_conn, fake_tab):
        await fake_tab.wait_for_absence(id='spinner', timeout=1)
        assert fake_conn.commands_for('Runtime.evaluate')

    @pytest.mark.asyncio
    async def test_passes_every_criterion_through_to_find(self, fake_conn, fake_tab):
        await fake_tab.wait_for_absence(class_name='loading', tag_name='div', timeout=1)
        expression = fake_conn.last_command('Runtime.evaluate')['params']['expression']
        assert '//div[' in expression and 'loading' in expression


class TestWaitForNetworkIdle:
    @pytest.mark.asyncio
    async def test_enables_network_events_for_the_wait_and_restores_them(self, fake_conn, fake_tab):
        await fake_tab.wait_for_network_idle(idle_time=0.02, timeout=1)
        assert fake_conn.commands_for('Network.enable')
        assert fake_conn.commands_for('Network.disable')
        assert not fake_tab.network_events_enabled
        assert not fake_conn.callbacks_for('Network.requestWillBeSent')

    @pytest.mark.asyncio
    async def test_a_request_in_flight_keeps_the_page_busy(self, fake_conn, fake_tab):
        import asyncio

        async def busy_then_quiet():
            await asyncio.sleep(0)
            _fire(fake_conn, 'Network.requestWillBeSent', {'requestId': 'r1', 'request': {'url': 'x'}})
            await asyncio.sleep(0.1)
            _fire(fake_conn, 'Network.loadingFinished', {'requestId': 'r1'})

        task = asyncio.ensure_future(busy_then_quiet())
        loop = asyncio.get_running_loop()
        started = loop.time()
        await fake_tab.wait_for_network_idle(idle_time=0.05, timeout=2)
        await task
        assert loop.time() - started >= 0.1

    @pytest.mark.asyncio
    async def test_times_out_while_a_request_never_finishes(self, fake_conn, fake_tab):
        await fake_tab.enable_network_events()
        import asyncio

        async def start_request():
            await asyncio.sleep(0)
            _fire(fake_conn, 'Network.requestWillBeSent', {'requestId': 'r1', 'request': {'url': 'x'}})

        asyncio.ensure_future(start_request())
        with pytest.raises(WaitTimeout):
            await fake_tab.wait_for_network_idle(idle_time=0.05, timeout=0.2)
        assert fake_tab.network_events_enabled


class TestExpectRequest:
    @pytest.mark.asyncio
    async def test_captures_the_first_matching_request(self, fake_conn, fake_tab):
        async with fake_tab.expect_request('**/api/data') as request:
            assert isinstance(request, RequestHandle)
            _fire(
                fake_conn,
                'Network.requestWillBeSent',
                {'requestId': 'r0', 'type': 'Image', 'request': {'url': 'https://a.test/logo.png', 'method': 'GET', 'headers': {}}},
            )
            _fire(
                fake_conn,
                'Network.requestWillBeSent',
                {
                    'requestId': 'r1',
                    'type': 'Fetch',
                    'request': {
                        'url': 'https://a.test/api/data',
                        'method': 'POST',
                        'headers': {'Content-Type': 'application/json'},
                        'postData': '{"q": 1}',
                    },
                },
            )
        assert request.request_id == 'r1'
        assert request.url == 'https://a.test/api/data'
        assert request.method == 'POST'
        assert request.headers == {'Content-Type': 'application/json'}
        assert request.post_data == '{"q": 1}'
        assert request.resource_type == 'Fetch'
        assert not fake_tab.network_events_enabled

    @pytest.mark.asyncio
    async def test_reading_inside_the_block_and_timing_out(self, fake_conn, fake_tab):
        with pytest.raises(WaitTimeout):
            async with fake_tab.expect_request('**/api/data', timeout=0.05) as request:
                with pytest.raises(WaitTimeout):
                    request.url


class TestExpectResponse:
    @pytest.mark.asyncio
    async def test_captures_status_headers_and_body(self, fake_conn, fake_tab):
        fake_conn.set_response('Network.getResponseBody', {'body': '{"total": 42}', 'base64Encoded': False})
        async with fake_tab.expect_response(re.compile(r'/api/data$')) as response:
            assert isinstance(response, ResponseHandle)
            _fire(
                fake_conn,
                'Network.responseReceived',
                {
                    'requestId': 'r1',
                    'response': {
                        'url': 'https://a.test/api/data',
                        'status': 200,
                        'headers': {'content-type': 'application/json'},
                        'mimeType': 'application/json',
                    },
                },
            )
            _fire(fake_conn, 'Network.loadingFinished', {'requestId': 'r1'})
        assert response.ok and response.status == 200
        assert response.request_id == 'r1'
        assert response.headers == {'content-type': 'application/json'}
        assert response.mime_type == 'application/json'
        assert response.json() == {'total': 42}
        assert fake_conn.last_command('Network.getResponseBody')['params']['requestId'] == 'r1'
        assert not fake_tab.network_events_enabled

    @pytest.mark.asyncio
    async def test_decodes_a_base64_body(self, fake_conn, fake_tab):
        payload = base64.b64encode(b'\x89PNG').decode()
        fake_conn.set_response('Network.getResponseBody', {'body': payload, 'base64Encoded': True})
        async with fake_tab.expect_response('**/logo.png') as response:
            _fire(
                fake_conn,
                'Network.responseReceived',
                {'requestId': 'r2', 'response': {'url': 'https://a.test/logo.png', 'status': 200, 'headers': {}}},
            )
            _fire(fake_conn, 'Network.loadingFinished', {'requestId': 'r2'})
        assert response.body() == b'\x89PNG'

    @pytest.mark.asyncio
    async def test_a_failed_load_has_status_but_no_body(self, fake_conn, fake_tab):
        async with fake_tab.expect_response('**/api/data') as response:
            _fire(
                fake_conn,
                'Network.responseReceived',
                {'requestId': 'r3', 'response': {'url': 'https://a.test/api/data', 'status': 502, 'headers': {}}},
            )
            _fire(fake_conn, 'Network.loadingFailed', {'requestId': 'r3', 'errorText': 'net::ERR_FAILED'})
        assert response.status == 502
        assert not response.ok
        with pytest.raises(WaitTimeout):
            response.body()
        assert not fake_conn.commands_for('Network.getResponseBody')

    @pytest.mark.asyncio
    async def test_times_out_when_no_response_matches(self, fake_conn, fake_tab):
        with pytest.raises(WaitTimeout):
            async with fake_tab.expect_response('**/api/data', timeout=0.05):
                _fire(
                    fake_conn,
                    'Network.responseReceived',
                    {'requestId': 'r4', 'response': {'url': 'https://a.test/other', 'status': 200, 'headers': {}}},
                )


class TestExpectNavigation:
    @pytest.mark.asyncio
    async def test_waits_for_the_main_frame_and_the_load_event(self, fake_conn, fake_tab):
        async with fake_tab.expect_navigation():
            _fire(fake_conn, 'Page.frameNavigated', {'frame': {'id': 'child', 'parentId': 'main', 'url': 'https://a.test/ad'}})
            _fire(fake_conn, 'Page.frameNavigated', {'frame': {'id': 'main', 'url': 'https://a.test/next'}})
            _fire(fake_conn, 'Page.loadEventFired', {'timestamp': 1})
        assert fake_conn.commands_for('Page.enable') and fake_conn.commands_for('Page.disable')
        assert not fake_tab.page_events_enabled

    @pytest.mark.asyncio
    async def test_url_filter_ignores_other_navigations(self, fake_conn, fake_tab):
        with pytest.raises(WaitTimeout):
            async with fake_tab.expect_navigation(url='**/checkout', timeout=0.05):
                _fire(fake_conn, 'Page.frameNavigated', {'frame': {'id': 'main', 'url': 'https://a.test/cart'}})
                _fire(fake_conn, 'Page.loadEventFired', {'timestamp': 1})

    @pytest.mark.asyncio
    async def test_a_load_event_before_the_navigation_does_not_count(self, fake_conn, fake_tab):
        with pytest.raises(WaitTimeout):
            async with fake_tab.expect_navigation(timeout=0.05):
                _fire(fake_conn, 'Page.loadEventFired', {'timestamp': 1})
