"""Critical Tab contract tests against a real ConnectionHandler + FakeCDPServer.

This is the "contract/glue" layer: the few scenarios that genuinely need the
real connection stack — event delivery through the real EventsManager worker,
navigation that waits for a load event, response parsing over a real socket,
and domain guards. The bulk of translate-only Tab methods live in the unit
suite against an in-memory FakeConnection (tests/unit/test_tab_commands.py).
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

import pytest

from pydoll.exceptions import WaitTimeout, WebSocketConnectionClosed
from pydoll.protocol.dom.methods import DomMethod
from pydoll.protocol.inspector.events import InspectorEvent
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.network.methods import NetworkMethod
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.page.methods import PageMethod
from pydoll.protocol.runtime.methods import RuntimeMethod


async def _wait_until(condition: Callable[[], Any], timeout: float = 2.0) -> Any:
    """Poll until condition() is truthy and return it; awaits async conditions."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        result = condition()
        if inspect.isawaitable(result):
            result = await result
        if result:
            return result
        await asyncio.sleep(0.01)
    raise AssertionError('condition not met within timeout')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'enable_method, command, flag',
    [
        ('enable_page_events', PageMethod.ENABLE, 'page_events_enabled'),
        ('enable_network_events', NetworkMethod.ENABLE, 'network_events_enabled'),
        ('enable_dom_events', DomMethod.ENABLE, 'dom_events_enabled'),
        ('enable_runtime_events', RuntimeMethod.ENABLE, 'runtime_events_enabled'),
    ],
)
async def test_enable_event_domain_sets_flag_and_sends_command(
    cdp_server, fake_tab, enable_method, command, flag
):
    assert getattr(fake_tab, flag) is False
    await getattr(fake_tab, enable_method)()
    assert getattr(fake_tab, flag) is True
    assert cdp_server.commands_for(command)


@pytest.mark.asyncio
async def test_current_url_evaluates_location_and_returns_value(cdp_server, fake_tab):
    cdp_server.set_result(RuntimeMethod.EVALUATE, {'result': {'value': 'https://example.com/p'}})
    url = await fake_tab.current_url()
    assert url == 'https://example.com/p'
    sent = cdp_server.commands_for(RuntimeMethod.EVALUATE)[-1]
    assert sent['params']['expression'] == 'window.location.href'


@pytest.mark.asyncio
async def test_get_cookies_returns_parsed_cookies(cdp_server, fake_tab):
    cookies = [{'name': 'session', 'value': 'abc'}]
    cdp_server.set_result(NetworkMethod.GET_COOKIES, {'cookies': cookies})
    result = await fake_tab.get_cookies()
    assert result == cookies
    assert cdp_server.commands_for(NetworkMethod.GET_COOKIES)


@pytest.mark.asyncio
async def test_go_to_navigates_waits_for_load_and_restores_page_events(cdp_server, fake_tab):
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com'))
    await _wait_until(lambda: cdp_server.commands_for(PageMethod.NAVIGATE))
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {})
    await navigation
    navigate = cdp_server.commands_for(PageMethod.NAVIGATE)[-1]
    assert navigate['params']['url'] == 'https://example.com'
    assert fake_tab.page_events_enabled is False


@pytest.mark.asyncio
async def test_go_to_fails_fast_when_the_connection_drops_while_waiting_for_load(
    cdp_server, fake_tab
):
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com', timeout=30))
    await _wait_until(lambda: cdp_server.commands_for(PageMethod.NAVIGATE))
    await cdp_server.drop_connections()
    with pytest.raises(WebSocketConnectionClosed):
        await asyncio.wait_for(navigation, timeout=5)


@pytest.mark.asyncio
async def test_go_to_on_a_crashed_tab_does_not_take_the_blank_page_load_for_its_own(
    cdp_server, fake_tab
):
    """The about:blank navigation that recovers a crashed tab fires its own load
    event; with Page events on, go_to must not finish on it."""
    await fake_tab.enable_page_events()
    await cdp_server.push_event(InspectorEvent.TARGET_CRASHED)
    await _wait_until(lambda: fake_tab._connection_handler.target_crashed)

    navigation = asyncio.create_task(fake_tab.go_to('https://example.com', timeout=10))
    await _wait_until(
        lambda: [c['params']['url'] for c in cdp_server.commands_for(PageMethod.NAVIGATE)]
        == ['about:blank']
    )
    await asyncio.sleep(0.1)
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {})
    await _wait_until(lambda: len(cdp_server.commands_for(PageMethod.NAVIGATE)) == 2)
    await asyncio.sleep(0.2)
    assert not navigation.done()

    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {})
    await asyncio.wait_for(navigation, timeout=5)


@pytest.mark.asyncio
async def test_go_to_preserves_page_events_when_already_enabled(cdp_server, fake_tab):
    await fake_tab.enable_page_events()
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com'))
    await _wait_until(lambda: cdp_server.commands_for(PageMethod.NAVIGATE))
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {})
    await navigation
    assert fake_tab.page_events_enabled is True


@pytest.mark.asyncio
async def test_refresh_reloads_waits_for_load_and_restores_page_events(cdp_server, fake_tab):
    reload = asyncio.create_task(fake_tab.refresh())
    await _wait_until(lambda: cdp_server.commands_for(PageMethod.RELOAD))
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {})
    await reload
    assert cdp_server.commands_for(PageMethod.RELOAD)
    assert fake_tab.page_events_enabled is False


@pytest.mark.asyncio
async def test_expect_response_timeout_does_not_kill_the_event_worker(cdp_server, fake_tab):
    """``wait_for`` cancels the future the finished-callback used to read; the
    ``CancelledError`` that read raised escaped the events worker and stopped
    every later event until the socket reconnected. A slow sibling callback on
    the same event holds the dispatch open past the timeout to hit that window."""

    async def slow(_event):
        await asyncio.sleep(0.2)

    await fake_tab.on(NetworkEvent.LOADING_FINISHED, slow)
    with pytest.raises(WaitTimeout):
        async with fake_tab.expect_response('**/api/data', timeout=0.1):
            await cdp_server.push_event(NetworkEvent.LOADING_FINISHED, {'requestId': 'r1'})
            await asyncio.sleep(0.02)
    await asyncio.sleep(0.3)

    markers: list[dict] = []
    await fake_tab.on('Custom.marker', markers.append)
    await cdp_server.push_event('Custom.marker')
    await _wait_until(lambda: len(markers) == 1)
    assert cdp_server.total_connections == 1


@pytest.mark.asyncio
async def test_on_sync_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []
    await fake_tab.enable_page_events()
    await fake_tab.on(PageEvent.LOAD_EVENT_FIRED, received.append)
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {'frame': 'main'})
    await _wait_until(lambda: received)
    assert received[0]['params'] == {'frame': 'main'}


@pytest.mark.asyncio
async def test_on_async_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []

    async def handler(event):
        received.append(event)

    await fake_tab.enable_page_events()
    await fake_tab.on(PageEvent.LOAD_EVENT_FIRED, handler)
    await cdp_server.push_event(PageEvent.LOAD_EVENT_FIRED, {'value': 1})
    await _wait_until(lambda: received)
    assert received[0]['params'] == {'value': 1}


@pytest.mark.asyncio
async def test_temporary_callback_fires_once(cdp_server, fake_tab):
    received = []
    marker = []
    await fake_tab.enable_page_events()
    await fake_tab.on('Custom.event', received.append, temporary=True)
    await fake_tab.on('Custom.marker', marker.append)
    await cdp_server.push_event('Custom.event', {'n': 1})
    await cdp_server.push_event('Custom.event', {'n': 2})
    await cdp_server.push_event('Custom.marker')
    await _wait_until(lambda: marker)
    assert len(received) == 1
    assert received[0]['params'] == {'n': 1}


@pytest.mark.asyncio
async def test_remove_callback_stops_delivery(cdp_server, fake_tab):
    received = []
    marker = []
    await fake_tab.enable_page_events()
    callback_id = await fake_tab.on('Custom.event', received.append)
    await fake_tab.on('Custom.marker', marker.append)
    await fake_tab.remove_callback(callback_id)
    await cdp_server.push_event('Custom.event', {})
    await cdp_server.push_event('Custom.marker', {})
    await _wait_until(lambda: marker)
    assert received == []


@pytest.mark.asyncio
async def test_clear_callbacks_removes_all(cdp_server, fake_tab):
    received = []
    await fake_tab.enable_page_events()
    await fake_tab.on('Custom.event', received.append)
    await fake_tab.clear_callbacks()
    marker = []
    await fake_tab.on('Custom.marker', marker.append)
    await cdp_server.push_event('Custom.event', {})
    await cdp_server.push_event('Custom.marker', {})
    await _wait_until(lambda: marker)
    assert received == []


@pytest.mark.asyncio
async def test_get_network_logs_records_and_filters_pushed_events(cdp_server, fake_tab):
    await fake_tab.enable_network_events()
    await cdp_server.push_event(
        NetworkEvent.REQUEST_WILL_BE_SENT,
        {'requestId': 'r1', 'request': {'url': 'https://example.com/api/users'}},
    )
    logs = await _wait_until(fake_tab.get_network_logs)
    assert len(logs) == 1
    assert await fake_tab.get_network_logs(filter='api')
    assert await fake_tab.get_network_logs(filter='nomatch') == []


@pytest.mark.asyncio
async def test_dialog_message_available_after_opening_event(cdp_server, fake_tab):
    await fake_tab.enable_page_events()
    await cdp_server.push_event(
        PageEvent.JAVASCRIPT_DIALOG_OPENING, {'message': 'Confirm?', 'type': 'confirm'}
    )
    await _wait_until(fake_tab.has_dialog)
    assert await fake_tab.get_dialog_message() == 'Confirm?'


@pytest.mark.asyncio
async def test_handle_dialog_sends_command_when_present(cdp_server, fake_tab):
    await fake_tab.enable_page_events()
    await cdp_server.push_event(
        PageEvent.JAVASCRIPT_DIALOG_OPENING, {'message': 'x', 'type': 'alert'}
    )
    await _wait_until(fake_tab.has_dialog)
    await fake_tab.handle_dialog(accept=True)
    sent = cdp_server.commands_for(PageMethod.HANDLE_JAVASCRIPT_DIALOG)[-1]
    assert sent['params']['accept'] is True
