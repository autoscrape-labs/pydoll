"""State-based glue tests for Tab driven through a real ConnectionHandler.

The Tab uses the production ConnectionHandler wired to a FakeCDPServer, so each
test asserts observable results: the value returned, the Tab's own state, and
the commands the server actually received. Events are pushed from the server,
never injected into the connection.
"""

from __future__ import annotations

import asyncio
from typing import Callable

import pytest


async def _wait_until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    """Poll an observable condition instead of sleeping a fixed amount."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError('condition not met within timeout')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'enable_method, command, flag',
    [
        ('enable_page_events', 'Page.enable', 'page_events_enabled'),
        ('enable_network_events', 'Network.enable', 'network_events_enabled'),
        ('enable_dom_events', 'DOM.enable', 'dom_events_enabled'),
        ('enable_runtime_events', 'Runtime.enable', 'runtime_events_enabled'),
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
async def test_enable_fetch_events_sets_flag_and_sends_command(cdp_server, fake_tab):
    await fake_tab.enable_fetch_events(handle_auth=True)
    assert fake_tab.fetch_events_enabled is True
    assert cdp_server.commands_for('Fetch.enable')


@pytest.mark.asyncio
async def test_disable_page_events_clears_flag_and_sends_command(cdp_server, fake_tab):
    await fake_tab.enable_page_events()
    await fake_tab.disable_page_events()
    assert fake_tab.page_events_enabled is False
    assert cdp_server.commands_for('Page.disable')


@pytest.mark.asyncio
async def test_current_url_evaluates_location_and_returns_value(cdp_server, fake_tab):
    cdp_server.set_result('Runtime.evaluate', {'result': {'value': 'https://example.com/p'}})
    url = await fake_tab.current_url
    assert url == 'https://example.com/p'
    sent = cdp_server.commands_for('Runtime.evaluate')[-1]
    assert sent['params']['expression'] == 'window.location.href'


@pytest.mark.asyncio
async def test_title_evaluates_document_title_and_returns_value(cdp_server, fake_tab):
    cdp_server.set_result('Runtime.evaluate', {'result': {'value': 'Hello World'}})
    title = await fake_tab.title
    assert title == 'Hello World'
    sent = cdp_server.commands_for('Runtime.evaluate')[-1]
    assert sent['params']['expression'] == 'document.title'


@pytest.mark.asyncio
async def test_get_cookies_returns_parsed_cookies(cdp_server, fake_tab):
    cookies = [{'name': 'session', 'value': 'abc'}]
    cdp_server.set_result('Network.getCookies', {'cookies': cookies})
    result = await fake_tab.get_cookies()
    assert result == cookies
    assert cdp_server.commands_for('Network.getCookies')


@pytest.mark.asyncio
async def test_on_sync_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []
    await fake_tab.enable_page_events()
    await fake_tab.on('Page.loadEventFired', received.append)
    await cdp_server.push_event('Page.loadEventFired', {'frame': 'main'})
    await _wait_until(lambda: received)
    assert received[0]['params'] == {'frame': 'main'}


@pytest.mark.asyncio
async def test_on_async_callback_receives_pushed_event(cdp_server, fake_tab):
    received = []

    async def handler(event):
        received.append(event)

    await fake_tab.enable_page_events()
    await fake_tab.on('Page.loadEventFired', handler)
    await cdp_server.push_event('Page.loadEventFired', {'value': 1})
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
async def test_go_to_navigates_and_completes_on_load_event(cdp_server, fake_tab):
    navigation = asyncio.create_task(fake_tab.go_to('https://example.com'))
    await _wait_until(lambda: cdp_server.commands_for('Page.navigate'))
    await cdp_server.push_event('Page.loadEventFired', {})
    await navigation
    navigate = cdp_server.commands_for('Page.navigate')[-1]
    assert navigate['params']['url'] == 'https://example.com'
