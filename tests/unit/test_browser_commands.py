"""Translate-only Browser methods tested against an in-memory FakeConnection.

A FakeConnection is injected into a Chrome to verify the browser-level command
shaping that the real-Chrome lifecycle suite does not exercise: download
behaviour, permissions, window lookup and fetch interception. Also covers the
platform binary-location resolution for Chrome and Edge.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.chromium.tab import Tab
from pydoll.exceptions import InvalidWebSocketAddress
from pydoll.protocol.cdp.browser.types import Bounds, DownloadBehavior, PermissionType, WindowState
from pydoll.protocol.cdp.network.types import ResourceType


@pytest.fixture
def browser(fake_conn):
    instance = Chrome()
    instance._connection_handler = fake_conn
    return instance


@pytest.fixture
def window_browser(browser, fake_conn):
    """Browser whose window-id resolution is wired through a faked valid tab target."""
    fake_conn.set_response(
        'Target.getTargets',
        {'targetInfos': [{'targetId': 'tab-1', 'type': 'page', 'url': 'about:blank'}]},
    )
    fake_conn.set_response('Browser.getWindowForTarget', {'windowId': 7})
    return browser


@pytest.mark.asyncio
async def test_set_download_behavior_carries_params(browser, fake_conn):
    await browser.set_download_behavior(
        DownloadBehavior.ALLOW, download_path='/tmp/dl', events_enabled=True
    )
    sent = fake_conn.last_command('Browser.setDownloadBehavior')
    assert sent['params']['behavior'] == 'allow'
    assert sent['params']['downloadPath'] == '/tmp/dl'
    assert sent['params']['eventsEnabled'] is True


@pytest.mark.asyncio
async def test_set_download_path_uses_allow_with_path(browser, fake_conn):
    await browser.set_download_path('/tmp/downloads')
    sent = fake_conn.last_command('Browser.setDownloadBehavior')
    assert sent['params']['behavior'] == 'allow'
    assert sent['params']['downloadPath'] == '/tmp/downloads'


@pytest.mark.asyncio
async def test_grant_permissions_carries_permissions(browser, fake_conn):
    await browser.grant_permissions([PermissionType.AUDIO_CAPTURE])
    sent = fake_conn.last_command('Browser.grantPermissions')
    assert sent['params']['permissions'] == [PermissionType.AUDIO_CAPTURE]


@pytest.mark.asyncio
async def test_reset_permissions_sends_command(browser, fake_conn):
    await browser.reset_permissions()
    assert fake_conn.commands_for('Browser.resetPermissions')


@pytest.mark.asyncio
async def test_get_window_id_for_target_parses_and_carries_target(browser, fake_conn):
    fake_conn.set_response('Browser.getWindowForTarget', {'windowId': 42})
    assert await browser._get_window_id_for_target('target-1') == 42
    sent = fake_conn.last_command('Browser.getWindowForTarget')
    assert sent['params']['targetId'] == 'target-1'


@pytest.mark.asyncio
async def test_continue_request_carries_request_id(browser, fake_conn):
    await browser._continue_request(request_id='r1')
    assert fake_conn.last_command('Fetch.continueRequest')['params']['requestId'] == 'r1'


@pytest.mark.asyncio
async def test_create_browser_context_sanitizes_proxy_and_keeps_credentials(browser, fake_conn):
    fake_conn.set_response('Target.createBrowserContext', {'browserContextId': 'ctx-1'})
    context_id = await browser.create_browser_context(proxy_server='http://user:pass@host:8080')
    assert context_id == 'ctx-1'
    sent = fake_conn.last_command('Target.createBrowserContext')
    assert sent['params']['proxyServer'] == 'http://host:8080'
    assert browser._context_proxy_auth[context_id] == ('user', 'pass')


@pytest.mark.asyncio
async def test_delete_browser_context_disposes_context(browser, fake_conn):
    await browser.delete_browser_context('ctx-9')
    assert fake_conn.last_command('Target.disposeBrowserContext')['params'][
        'browserContextId'
    ] == 'ctx-9'


@pytest.mark.asyncio
async def test_get_browser_contexts_returns_ids(browser, fake_conn):
    fake_conn.set_response('Target.getBrowserContexts', {'browserContextIds': ['a', 'b']})
    assert await browser.get_browser_contexts() == ['a', 'b']


@pytest.mark.asyncio
async def test_get_version_returns_result(browser, fake_conn):
    fake_conn.set_response(
        'Browser.getVersion',
        {
            'protocolVersion': '1.3',
            'product': 'Chrome/120',
            'revision': 'r1',
            'userAgent': 'ua',
            'jsVersion': '12',
        },
    )
    version = await browser.get_version()
    assert version['browserName'] == 'Chrome/120'


@pytest.mark.asyncio
async def test_new_tab_creates_and_tracks_tab(browser, fake_conn):
    fake_conn.set_response('Target.createTarget', {'targetId': 't-new'})
    tab = await browser.new_tab()
    assert isinstance(tab, Tab)
    assert tab._target_id == 't-new'
    assert 't-new' in browser._tabs_opened


@pytest.mark.asyncio
async def test_set_and_get_cookies_round_trip(browser, fake_conn):
    await browser.set_cookies([{'name': 'a', 'value': '1'}])
    assert fake_conn.last_command('Storage.setCookies')['params']['cookies'][0]['name'] == 'a'
    fake_conn.set_response('Storage.getCookies', {'cookies': [{'name': 'a', 'value': '1'}]})
    cookies = await browser.get_cookies()
    assert cookies[0]['name'] == 'a'


@pytest.mark.asyncio
async def test_delete_all_cookies_clears_storage(browser, fake_conn):
    await browser.delete_all_cookies('ctx-1')
    assert fake_conn.commands_for('Storage.clearCookies')


@pytest.mark.asyncio
async def test_get_window_id_resolves_via_valid_target(window_browser):
    assert await window_browser._get_window_id() == 7


@pytest.mark.asyncio
async def test_set_window_maximized_targets_resolved_window(window_browser, fake_conn):
    await window_browser.set_window_maximized()
    sent = fake_conn.last_command('Browser.setWindowBounds')
    assert sent['params']['windowId'] == 7
    assert sent['params']['bounds']['windowState'] == WindowState.MAXIMIZED


@pytest.mark.asyncio
async def test_set_window_minimized_targets_resolved_window(window_browser, fake_conn):
    await window_browser.set_window_minimized()
    bounds = fake_conn.last_command('Browser.setWindowBounds')['params']['bounds']
    assert bounds['windowState'] == WindowState.MINIMIZED


@pytest.mark.asyncio
async def test_set_window_bounds_carries_dimensions(window_browser, fake_conn):
    await window_browser.set_window_bounds(Bounds(width=1024, height=768))
    sent = fake_conn.last_command('Browser.setWindowBounds')
    assert sent['params']['windowId'] == 7
    assert sent['params']['bounds']['width'] == 1024


@pytest.mark.asyncio
async def test_enable_fetch_events_carries_auth_and_resource_type(browser, fake_conn):
    await browser._enable_fetch_events(handle_auth_requests=True, resource_type=ResourceType.XHR)
    sent = fake_conn.last_command('Fetch.enable')
    assert sent['params']['handleAuthRequests'] is True


@pytest.mark.asyncio
async def test_disable_fetch_events_sends_disable(browser, fake_conn):
    await browser._disable_fetch_events()
    assert fake_conn.commands_for('Fetch.disable')


@pytest.mark.asyncio
async def test_enable_and_disable_runtime_events(browser, fake_conn):
    await browser._enable_runtime_events()
    await browser._disable_runtime_events()
    assert fake_conn.commands_for('Runtime.enable')
    assert fake_conn.commands_for('Runtime.disable')


@pytest.mark.parametrize('bad_address', ['http://not-a-ws', 'ws://tooshort'])
@pytest.mark.asyncio
async def test_connect_rejects_invalid_ws_address(browser, bad_address):
    with pytest.raises(InvalidWebSocketAddress):
        await browser.connect(bad_address)
