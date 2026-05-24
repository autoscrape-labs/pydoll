"""Translate-only FirefoxBrowser methods against an in-memory FakeBiDiConnection.

The BiDi counterpart of tests/cdp/unit/test_browser_commands.py: browser-level
methods that turn a Python call into a WebDriver BiDi command and return simple
state — download behaviour, cookies, user contexts, windows, permissions and
request interception. Assertions check the command shape and resulting state, not
that some command was merely emitted. Event-driven flows run against real Firefox
in the integration suite.
"""

from __future__ import annotations

import pytest

from pydoll.browser.firefox.tab import BiDiTab
from pydoll.protocol.types import DownloadBehavior, Permission


@pytest.mark.asyncio
async def test_set_download_behavior_allow_carries_destination(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_download_behavior(DownloadBehavior.ALLOW, '/tmp/dl')
    behavior = fake_bidi_conn.last_command('browser.setDownloadBehavior')['params']['downloadBehavior']
    assert behavior['type'] == 'allowed'
    assert behavior['destinationFolder'] == '/tmp/dl'


@pytest.mark.asyncio
async def test_set_download_behavior_deny(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_download_behavior(DownloadBehavior.DENY)
    behavior = fake_bidi_conn.last_command('browser.setDownloadBehavior')['params']['downloadBehavior']
    assert behavior['type'] == 'denied'


@pytest.mark.asyncio
async def test_set_download_path_uses_allow_with_path(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_download_path('/tmp/here')
    behavior = fake_bidi_conn.last_command('browser.setDownloadBehavior')['params']['downloadBehavior']
    assert behavior == {'type': 'allowed', 'destinationFolder': '/tmp/here'}


@pytest.mark.asyncio
async def test_set_cookies_sends_set_cookie_per_cookie(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_cookies([{'name': 'a', 'value': '1', 'domain': 'example.com'}])
    cookie = fake_bidi_conn.last_command('storage.setCookie')['params']['cookie']
    assert cookie['name'] == 'a'
    assert cookie['value'] == {'type': 'string', 'value': '1'}
    assert cookie['domain'] == 'example.com'


@pytest.mark.asyncio
async def test_get_cookies_returns_generic_cookies(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'storage.getCookies',
        {'cookies': [{
            'name': 'sid', 'value': {'type': 'string', 'value': 'xyz'},
            'domain': 'example.com', 'path': '/', 'size': 6,
            'httpOnly': True, 'secure': True, 'sameSite': 'lax',
        }]},
    )
    cookies = await fake_bidi_browser.get_cookies()
    assert cookies[0]['name'] == 'sid'
    assert cookies[0]['value'] == 'xyz'
    assert cookies[0]['httpOnly'] is True


@pytest.mark.asyncio
async def test_delete_all_cookies_sends_command(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.delete_all_cookies()
    assert fake_bidi_conn.commands_for('storage.deleteCookies')


@pytest.mark.asyncio
async def test_create_browser_context_returns_user_context_id(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('browser.createUserContext', {'userContext': 'ctx-1'})
    context_id = await fake_bidi_browser.create_browser_context()
    assert context_id == 'ctx-1'


@pytest.mark.asyncio
async def test_create_browser_context_with_proxy_carries_manual_config(
    fake_bidi_browser, fake_bidi_conn
):
    fake_bidi_conn.set_result('browser.createUserContext', {'userContext': 'ctx-2'})
    await fake_bidi_browser.create_browser_context(proxy_server='http://127.0.0.1:8080')
    proxy = fake_bidi_conn.last_command('browser.createUserContext')['params']['proxy']
    assert proxy['proxyType'] == 'manual'
    assert proxy['httpProxy'] == 'http://127.0.0.1:8080'


@pytest.mark.asyncio
async def test_delete_browser_context_sends_command(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.delete_browser_context('ctx-1')
    assert fake_bidi_conn.last_command('browser.removeUserContext')['params']['userContext'] == 'ctx-1'


@pytest.mark.asyncio
async def test_get_browser_contexts_lists_ids(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'browser.getUserContexts',
        {'userContexts': [{'userContext': 'default'}, {'userContext': 'ctx-1'}]},
    )
    assert await fake_bidi_browser.get_browser_contexts() == ['default', 'ctx-1']


@pytest.mark.asyncio
async def test_get_opened_tabs_builds_tabs_from_tree(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'browsingContext.getTree',
        {'contexts': [{'context': 'c1'}, {'context': 'c2'}]},
    )
    tabs = await fake_bidi_browser.get_opened_tabs()
    assert all(isinstance(tab, BiDiTab) for tab in tabs)
    assert [tab._context_id for tab in tabs] == ['c1', 'c2']


@pytest.mark.asyncio
async def test_new_tab_creates_context_and_returns_tab(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('browsingContext.create', {'context': 'new-ctx'})
    tab = await fake_bidi_browser.new_tab()
    assert isinstance(tab, BiDiTab)
    assert tab._context_id == 'new-ctx'


@pytest.mark.asyncio
async def test_get_version_reads_cached_capabilities(fake_bidi_browser):
    fake_bidi_browser._capabilities = {
        'browserName': 'Firefox', 'browserVersion': '142.0', 'userAgent': 'UA/1',
    }
    version = await fake_bidi_browser.get_version()
    assert version['browserName'] == 'Firefox'
    assert version['browserVersion'] == '142.0'
    assert version['userAgent'] == 'UA/1'


@pytest.mark.asyncio
async def test_set_window_maximized_sets_state(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'browser.getClientWindows', {'clientWindows': [{'clientWindow': 'w1'}]}
    )
    await fake_bidi_browser.set_window_maximized()
    command = fake_bidi_conn.last_command('browser.setClientWindowState')
    assert command['params']['clientWindow'] == 'w1'
    assert command['params']['state'] == 'maximized'


@pytest.mark.asyncio
async def test_set_window_bounds_carries_dimensions(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'browser.getClientWindows', {'clientWindows': [{'clientWindow': 'w1'}]}
    )
    await fake_bidi_browser.set_window_bounds({'width': 800, 'height': 600})
    params = fake_bidi_conn.last_command('browser.setClientWindowState')['params']
    assert params['width'] == 800
    assert params['height'] == 600


@pytest.mark.asyncio
async def test_grant_permissions_maps_name_and_requires_origin(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.grant_permissions(
        [Permission.GEOLOCATION], origin='https://example.com'
    )
    params = fake_bidi_conn.last_command('permissions.setPermission')['params']
    assert params['descriptor']['name'] == 'geolocation'
    assert params['origin'] == 'https://example.com'
    assert params['state'] == 'granted'


@pytest.mark.asyncio
async def test_grant_permissions_without_origin_raises(fake_bidi_browser):
    with pytest.raises(ValueError):
        await fake_bidi_browser.grant_permissions([Permission.GEOLOCATION])


@pytest.mark.asyncio
async def test_grant_permissions_warns_on_unsupported(fake_bidi_browser):
    with pytest.warns(UserWarning):
        await fake_bidi_browser.grant_permissions(
            [Permission.PROTECTED_MEDIA_IDENTIFIER], origin='https://example.com'
        )


@pytest.mark.asyncio
async def test_reset_permissions_resets_previously_granted(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.grant_permissions(
        [Permission.GEOLOCATION], origin='https://example.com'
    )
    await fake_bidi_browser.reset_permissions()
    states = [c['params']['state'] for c in fake_bidi_conn.commands_for('permissions.setPermission')]
    assert 'prompt' in states


@pytest.mark.asyncio
async def test_on_subscribes_and_registers_callback(fake_bidi_browser, fake_bidi_conn):
    async def cb(_event):
        return None

    await fake_bidi_browser.on('browsingContext.load', cb)
    assert fake_bidi_conn.commands_for('session.subscribe')


@pytest.mark.asyncio
async def test_intercept_requests_adds_intercept_and_subscribes(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('network.addIntercept', {'intercept': 'i1'})

    async def cb(_req):
        return None

    intercept_id = await fake_bidi_browser.intercept_requests(cb)
    assert intercept_id == 'i1'
    subscribe = fake_bidi_conn.last_command('session.subscribe')
    assert 'network.beforeRequestSent' in subscribe['params']['events']


@pytest.mark.asyncio
async def test_intercept_callback_receives_blocked_request(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('network.addIntercept', {'intercept': 'i1'})
    received = []

    async def cb(req):
        received.append(req)
        await req.continue_()

    await fake_bidi_browser.intercept_requests(cb)
    handler = next(iter(fake_bidi_conn._callbacks.values()))['callback']
    await handler({'params': {
        'isBlocked': True,
        'request': {'request': 'r1', 'url': 'http://x/a', 'method': 'GET', 'headers': []},
    }})

    assert received and received[0].url == 'http://x/a'
    assert fake_bidi_conn.commands_for('network.continueRequest')


@pytest.mark.asyncio
async def test_intercept_callback_ignores_unblocked_request(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('network.addIntercept', {'intercept': 'i1'})
    received = []

    async def cb(req):
        received.append(req)

    await fake_bidi_browser.intercept_requests(cb)
    handler = next(iter(fake_bidi_conn._callbacks.values()))['callback']
    await handler({'params': {'isBlocked': False, 'request': {'request': 'r1', 'url': 'http://x'}}})
    assert received == []


@pytest.mark.asyncio
async def test_remove_intercept_unsubscribes_on_last(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('network.addIntercept', {'intercept': 'i1'})

    async def cb(_req):
        return None

    intercept_id = await fake_bidi_browser.intercept_requests(cb)
    await fake_bidi_browser.remove_intercept(intercept_id)
    assert fake_bidi_conn.last_command('network.removeIntercept')['params']['intercept'] == 'i1'
    assert fake_bidi_conn.commands_for('session.unsubscribe')


@pytest.mark.asyncio
async def test_browser_set_cookies_carries_optional_attributes(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_cookies([{
        'name': 'a', 'value': '1', 'domain': 'example.com',
        'path': '/p', 'httpOnly': True, 'secure': True, 'expiry': 99, 'sameSite': 'Lax',
    }])
    cookie = fake_bidi_conn.last_command('storage.setCookie')['params']['cookie']
    assert cookie['path'] == '/p'
    assert cookie['httpOnly'] is True
    assert cookie['secure'] is True
    assert cookie['expiry'] == 99
    assert cookie['sameSite'] == 'lax'


@pytest.mark.asyncio
async def test_set_download_path_delegates_to_allow(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.set_download_path('/tmp/dl')
    behavior = fake_bidi_conn.last_command('browser.setDownloadBehavior')['params']['downloadBehavior']
    assert behavior['type'] == 'allowed'
    assert behavior['destinationFolder'] == '/tmp/dl'


@pytest.mark.asyncio
async def test_delete_all_cookies_with_context_uses_partition(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.delete_all_cookies(browser_context_id='ctx-1')
    params = fake_bidi_conn.last_command('storage.deleteCookies')['params']
    assert params['partition']['userContext'] == 'ctx-1'


@pytest.mark.asyncio
async def test_set_window_minimized_sets_state(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result(
        'browser.getClientWindows', {'clientWindows': [{'clientWindow': 'w1'}]}
    )
    await fake_bidi_browser.set_window_minimized()
    assert fake_bidi_conn.last_command('browser.setClientWindowState')['params']['state'] == 'minimized'


@pytest.mark.asyncio
async def test_create_browser_context_warns_on_proxy_bypass(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('browser.createUserContext', {'userContext': 'c'})
    with pytest.warns(UserWarning):
        await fake_bidi_browser.create_browser_context(proxy_bypass_list='localhost')


@pytest.mark.asyncio
async def test_reset_permissions_filters_by_context(fake_bidi_browser, fake_bidi_conn):
    await fake_bidi_browser.grant_permissions(
        [Permission.GEOLOCATION], origin='https://a.com', browser_context_id='ctx-1'
    )
    await fake_bidi_browser.grant_permissions(
        [Permission.NOTIFICATIONS], origin='https://b.com', browser_context_id='ctx-2'
    )
    fake_bidi_conn.commands.clear()
    await fake_bidi_browser.reset_permissions(browser_context_id='ctx-1')
    reset = fake_bidi_conn.commands_for('permissions.setPermission')
    assert len(reset) == 1
    assert reset[0]['params']['origin'] == 'https://a.com'


@pytest.mark.asyncio
async def test_connect_establishes_session_and_returns_first_tab(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('session.new', {'sessionId': 's1', 'capabilities': {}})
    fake_bidi_conn.set_result('browsingContext.getTree', {'contexts': [{'context': 'c1'}]})
    tab = await fake_bidi_browser.connect('ws://127.0.0.1/session/abc')
    assert tab._context_id == 'c1'
    assert fake_bidi_browser._session_id == 's1'


@pytest.mark.asyncio
async def test_connect_opens_new_tab_when_no_contexts(fake_bidi_browser, fake_bidi_conn):
    fake_bidi_conn.set_result('session.new', {'sessionId': 's1', 'capabilities': {}})
    fake_bidi_conn.set_result('browsingContext.getTree', {'contexts': []})
    fake_bidi_conn.set_result('browsingContext.create', {'context': 'fresh'})
    tab = await fake_bidi_browser.connect('ws://127.0.0.1/session/abc')
    assert tab._context_id == 'fresh'
