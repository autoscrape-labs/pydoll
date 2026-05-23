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
        ('_enable_page_events', 'Page.enable', '_page_events_enabled'),
        ('_enable_network_events', 'Network.enable', '_network_events_enabled'),
        ('_enable_dom_events', 'DOM.enable', '_dom_events_enabled'),
        ('_enable_runtime_events', 'Runtime.enable', '_runtime_events_enabled'),
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
    cdp_server.set_result('Runtime.evaluate', {'result': {'value': 'https://example.com/p'}})
    url = await fake_tab.current_url
    assert url == 'https://example.com/p'
    sent = cdp_server.commands_for('Runtime.evaluate')[-1]
    assert sent['params']['expression'] == 'window.location.href'


@pytest.mark.asyncio
async def test_get_cookies_returns_parsed_cookies(cdp_server, fake_tab):
    cdp_server.set_result(
        'Network.getCookies',
        {
            'cookies': [
                {
                    'name': 'session',
                    'value': 'abc',
                    'domain': 'example.com',
                    'path': '/',
                    'expires': -1,
                    'size': 10,
                    'httpOnly': False,
                    'secure': False,
                    'session': True,
                }
            ]
        },
    )
    result = await fake_tab.get_cookies()
    assert result[0]['name'] == 'session'
    assert result[0]['value'] == 'abc'
    assert cdp_server.commands_for('Network.getCookies')


@pytest.mark.asyncio
async def test_go_to_navigates_waits_for_load_and_restores_page_events(cdp_server, fake_tab):
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com'))
    await _wait_until(lambda: cdp_server.commands_for('Page.navigate'))
    await cdp_server.push_event('Page.loadEventFired', {})
    await navigation
    navigate = cdp_server.commands_for('Page.navigate')[-1]
    assert navigate['params']['url'] == 'https://example.com'
    assert fake_tab._page_events_enabled is False


@pytest.mark.asyncio
async def test_go_to_preserves_page_events_when_already_enabled(cdp_server, fake_tab):
    await fake_tab._enable_page_events()
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com'))
    await _wait_until(lambda: cdp_server.commands_for('Page.navigate'))
    await cdp_server.push_event('Page.loadEventFired', {})
    await navigation
    assert fake_tab._page_events_enabled is True


@pytest.mark.asyncio
async def test_refresh_reloads_waits_for_load_and_restores_page_events(cdp_server, fake_tab):
    reload = asyncio.create_task(fake_tab.refresh())
    await _wait_until(lambda: cdp_server.commands_for('Page.reload'))
    await cdp_server.push_event('Page.loadEventFired', {})
    await reload
    assert cdp_server.commands_for('Page.reload')
    assert fake_tab._page_events_enabled is False


@pytest.mark.asyncio
async def test_on_sync_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []
    await fake_tab._enable_page_events()
    await fake_tab.on('Page.loadEventFired', received.append)
    await cdp_server.push_event('Page.loadEventFired', {'frame': 'main'})
    await _wait_until(lambda: received)
    assert received[0]['params'] == {'frame': 'main'}


@pytest.mark.asyncio
async def test_on_async_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []

    async def handler(event):
        received.append(event)

    await fake_tab._enable_page_events()
    await fake_tab.on('Page.loadEventFired', handler)
    await cdp_server.push_event('Page.loadEventFired', {'value': 1})
    await _wait_until(lambda: received)
    assert received[0]['params'] == {'value': 1}


@pytest.mark.asyncio
async def test_temporary_callback_fires_once(cdp_server, fake_tab):
    received = []
    marker = []
    await fake_tab._enable_page_events()
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
    await fake_tab._enable_page_events()
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
    await fake_tab._enable_page_events()
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
    await fake_tab._enable_network_events()
    await cdp_server.push_event(
        'Network.requestWillBeSent',
        {'requestId': 'r1', 'request': {'url': 'https://example.com/api/users'}},
    )
    logs = await _wait_until(fake_tab.get_network_logs)
    assert len(logs) == 1
    assert await fake_tab.get_network_logs(filter='api')
    assert await fake_tab.get_network_logs(filter='nomatch') == []


@pytest.mark.asyncio
async def test_dialog_message_available_after_opening_event(cdp_server, fake_tab):
    await fake_tab._enable_page_events()
    await cdp_server.push_event(
        'Page.javascriptDialogOpening', {'message': 'Confirm?', 'type': 'confirm'}
    )
    await _wait_until(fake_tab.has_dialog)
    assert await fake_tab.get_dialog_message() == 'Confirm?'


@pytest.mark.asyncio
async def test_handle_dialog_sends_command_when_present(cdp_server, fake_tab):
    await fake_tab._enable_page_events()
    await cdp_server.push_event('Page.javascriptDialogOpening', {'message': 'x', 'type': 'alert'})
    await _wait_until(fake_tab.has_dialog)
    await fake_tab.handle_dialog(accept=True)
    sent = cdp_server.commands_for('Page.handleJavaScriptDialog')[-1]
    assert sent['params']['accept'] is True
