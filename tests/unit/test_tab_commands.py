"""Translate-only Tab methods tested against an in-memory FakeConnection.

These cover the bulk of Tab's surface: methods that turn a Python call into a
CDP command and update simple state. Assertions check the meaningful parts —
the parameters carried and the resulting state — not merely that some command
was emitted. Event-driven and wire-contract behaviour lives in the integration
suite (tests/integration/test_tab.py).
"""

from __future__ import annotations

import pytest

from pydoll.browser.requests import Request
from pydoll.exceptions import NetworkEventsNotEnabled, NoDialogPresent
from pydoll.interactions import KeyboardAPI, MouseAPI, ScrollAPI
from pydoll.protocol.cdp.fetch.types import AuthChallengeResponseType
from pydoll.protocol.cdp.network.types import ErrorReason


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'enable_method, disable_method, command, flag',
    [
        ('_enable_page_events', '_disable_page_events', 'Page.disable', '_page_events_enabled'),
        ('_enable_network_events', '_disable_network_events', 'Network.disable', '_network_events_enabled'),
        ('_enable_dom_events', '_disable_dom_events', 'DOM.disable', '_dom_events_enabled'),
        ('_enable_runtime_events', '_disable_runtime_events', 'Runtime.disable', '_runtime_events_enabled'),
        ('_enable_fetch_events', '_disable_fetch_events', 'Fetch.disable', '_fetch_events_enabled'),
    ],
)
async def test_disable_event_domain_clears_flag_and_sends_command(
    fake_conn, fake_tab, enable_method, disable_method, command, flag
):
    await getattr(fake_tab, enable_method)()
    await getattr(fake_tab, disable_method)()
    assert getattr(fake_tab, flag) is False
    assert fake_conn.commands_for(command)


@pytest.mark.asyncio
async def test_enable_fetch_events_carries_handle_auth(fake_conn, fake_tab):
    await fake_tab._enable_fetch_events(handle_auth=True)
    assert fake_tab._fetch_events_enabled is True
    assert fake_conn.last_command('Fetch.enable')['params']['handleAuthRequests'] is True


@pytest.mark.asyncio
async def test_intercept_file_chooser_toggles_flag_and_carries_enabled(fake_conn, fake_tab):
    await fake_tab._enable_intercept_file_chooser_dialog()
    assert fake_tab._intercept_file_chooser_dialog_enabled is True
    assert fake_conn.last_command('Page.setInterceptFileChooserDialog')['params']['enabled'] is True

    await fake_tab._disable_intercept_file_chooser_dialog()
    assert fake_tab._intercept_file_chooser_dialog_enabled is False
    assert fake_conn.last_command('Page.setInterceptFileChooserDialog')['params']['enabled'] is False


@pytest.mark.asyncio
async def test_bring_to_front_sends_command(fake_conn, fake_tab):
    await fake_tab.bring_to_front()
    assert fake_conn.commands_for('Page.bringToFront')


@pytest.mark.asyncio
async def test_title_evaluates_document_title_and_returns_value(fake_conn, fake_tab):
    fake_conn.set_response('Runtime.evaluate', {'result': {'value': 'Hello'}})
    assert await fake_tab.title == 'Hello'
    assert fake_conn.last_command('Runtime.evaluate')['params']['expression'] == 'document.title'


@pytest.mark.asyncio
async def test_page_source_evaluates_outer_html_and_returns_value(fake_conn, fake_tab):
    fake_conn.set_response('Runtime.evaluate', {'result': {'value': '<html></html>'}})
    assert await fake_tab.page_source == '<html></html>'
    expression = fake_conn.last_command('Runtime.evaluate')['params']['expression']
    assert expression == 'document.documentElement.outerHTML'


@pytest.mark.asyncio
async def test_set_cookies_carries_cookies(fake_conn, fake_tab):
    cookies = [{'name': 'a', 'value': '1'}]
    await fake_tab.set_cookies(cookies)
    assert fake_conn.last_command('Storage.setCookies')['params']['cookies'] == cookies


@pytest.mark.asyncio
async def test_delete_all_cookies_sends_command(fake_conn, fake_tab):
    await fake_tab.delete_all_cookies()
    assert fake_conn.commands_for('Storage.clearCookies')


@pytest.mark.asyncio
async def test_get_network_response_body_returns_body_and_carries_request_id(fake_conn, fake_tab):
    await fake_tab._enable_network_events()
    fake_conn.set_response('Network.getResponseBody', {'body': 'hello', 'base64Encoded': False})
    assert await fake_tab.get_network_response_body('req-1') == 'hello'
    assert fake_conn.last_command('Network.getResponseBody')['params']['requestId'] == 'req-1'


@pytest.mark.asyncio
async def test_get_network_response_body_requires_network_events(fake_tab):
    with pytest.raises(NetworkEventsNotEnabled):
        await fake_tab.get_network_response_body('req-1')


@pytest.mark.asyncio
async def test_get_network_logs_requires_network_events(fake_tab):
    with pytest.raises(NetworkEventsNotEnabled):
        await fake_tab.get_network_logs()


@pytest.mark.asyncio
async def test_has_dialog_is_false_without_dialog(fake_tab):
    assert await fake_tab.has_dialog() is False


@pytest.mark.asyncio
async def test_get_dialog_message_raises_without_dialog(fake_tab):
    with pytest.raises(NoDialogPresent):
        await fake_tab.get_dialog_message()


@pytest.mark.asyncio
async def test_handle_dialog_raises_without_dialog(fake_tab):
    with pytest.raises(NoDialogPresent):
        await fake_tab.handle_dialog(accept=True)


@pytest.mark.asyncio
async def test_continue_request_carries_request_id(fake_conn, fake_tab):
    await fake_tab._continue_request(request_id='r1')
    assert fake_conn.last_command('Fetch.continueRequest')['params']['requestId'] == 'r1'


@pytest.mark.asyncio
async def test_continue_with_auth_carries_challenge_and_credentials(fake_conn, fake_tab):
    await fake_tab._continue_with_auth(
        'r1',
        AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='pass',
    )
    sent = fake_conn.last_command('Fetch.continueWithAuth')
    assert sent['params']['requestId'] == 'r1'
    challenge = sent['params']['authChallengeResponse']
    assert challenge['response'] == 'ProvideCredentials'
    assert challenge['username'] == 'user'
    assert challenge['password'] == 'pass'


@pytest.mark.asyncio
async def test_execute_script_evaluates_and_returns_result(fake_conn, fake_tab):
    fake_conn.set_response('Runtime.evaluate', {'result': {'type': 'number', 'value': 3}})
    result = await fake_tab.execute_script('1 + 2')
    assert result == 3
    assert fake_conn.last_command('Runtime.evaluate')['params']['expression'] == '1 + 2'


@pytest.mark.asyncio
async def test_execute_script_wraps_top_level_return(fake_conn, fake_tab):
    fake_conn.set_response('Runtime.evaluate', {'result': {'type': 'number', 'value': 42}})
    await fake_tab.execute_script('return 42')
    expression = fake_conn.last_command('Runtime.evaluate')['params']['expression']
    assert expression == '(function(){ return 42 })()'


@pytest.mark.asyncio
async def test_close_sends_command_and_removes_from_registry(fake_conn, fake_tab):
    fake_tab._browser._tabs_opened['fake-tab'] = fake_tab
    await fake_tab.close()
    assert fake_conn.commands_for('Page.close')
    assert 'fake-tab' not in fake_tab._browser._tabs_opened


@pytest.mark.asyncio
async def test_lazy_api_properties_are_typed_and_cached(fake_tab):
    assert isinstance(fake_tab.request, Request)
    assert fake_tab.request is fake_tab.request
    assert isinstance(fake_tab.scroll, ScrollAPI)
    assert fake_tab.scroll is fake_tab.scroll
    assert isinstance(fake_tab.keyboard, KeyboardAPI)
    assert fake_tab.keyboard is fake_tab.keyboard
    assert isinstance(fake_tab.mouse, MouseAPI)


@pytest.mark.asyncio
async def test_enable_auto_solve_cloudflare_registers_callback_and_enables_page_events(
    fake_conn, fake_tab
):
    await fake_tab.enable_auto_solve_cloudflare_captcha()
    assert fake_tab._page_events_enabled is True
    assert fake_conn.callbacks_for('Page.loadEventFired')


@pytest.mark.asyncio
async def test_enable_auto_solve_cloudflare_warns_on_deprecated_args(fake_tab):
    with pytest.warns(DeprecationWarning):
        await fake_tab.enable_auto_solve_cloudflare_captcha(time_before_click=1.0)
