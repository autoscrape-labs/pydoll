"""Translate-only BiDiTab methods tested against an in-memory FakeBiDiConnection.

These cover the BiDi commands a BiDiTab emits and the values it carries — the
WebDriver BiDi equivalent of tests/cdp/unit/test_tab_commands.py. Behaviour that
needs real Firefox (events, real navigation, trusted input) lives in
tests/bidi/integration.
"""

from __future__ import annotations

import pytest


def _success(remote_value: dict) -> dict:
    """A BiDi script EvaluateResult wrapping a RemoteValue."""
    return {'type': 'success', 'result': remote_value, 'realm': 'realm-1'}


@pytest.mark.asyncio
async def test_go_to_navigates_with_context_and_complete_wait(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.go_to('https://example.com')
    command = fake_bidi_conn.last_command('browsingContext.navigate')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['url'] == 'https://example.com'
    assert command['params']['wait'] == 'complete'


@pytest.mark.asyncio
async def test_refresh_reloads_with_complete_wait(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.refresh()
    command = fake_bidi_conn.last_command('browsingContext.reload')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['wait'] == 'complete'


@pytest.mark.asyncio
async def test_current_url_evaluates_location_href(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'script.evaluate', _success({'type': 'string', 'value': 'https://example.com/p'})
    )
    assert await fake_bidi_tab.current_url == 'https://example.com/p'
    assert fake_bidi_conn.last_command('script.evaluate')['params']['expression'] == 'location.href'


@pytest.mark.asyncio
async def test_title_evaluates_document_title(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'string', 'value': 'Hello'}))
    assert await fake_bidi_tab.title == 'Hello'
    assert fake_bidi_conn.last_command('script.evaluate')['params']['expression'] == 'document.title'


@pytest.mark.asyncio
async def test_find_locates_node_by_css_and_builds_element(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'sharedId': 's1', 'value': {
            'localName': 'div', 'attributes': {'id': 'x'}}}]},
    )
    element = await fake_bidi_tab.find(id='x')
    assert element is not None
    assert element.id == 'x'
    command = fake_bidi_conn.last_command('browsingContext.locateNodes')
    assert command['params']['context'] == 'fake-context'
    assert command['params']['locator'] == {'type': 'css', 'value': '#x'}


@pytest.mark.asyncio
async def test_find_all_returns_every_node(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [
            {'type': 'node', 'sharedId': 's1', 'value': {'localName': 'li', 'attributes': {}}},
            {'type': 'node', 'sharedId': 's2', 'value': {'localName': 'li', 'attributes': {}}},
        ]},
    )
    elements = await fake_bidi_tab.find(tag_name='li', find_all=True)
    assert len(elements) == 2


@pytest.mark.asyncio
async def test_execute_script_evaluates_and_deserializes_value(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('script.evaluate', _success({'type': 'number', 'value': 7}))
    assert await fake_bidi_tab.execute_script('return 7') == 7


@pytest.mark.asyncio
async def test_execute_script_with_args_calls_function_with_local_values(
    fake_bidi_conn, fake_bidi_tab
):
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'undefined'}))
    await fake_bidi_tab.execute_script('(a) => a', 5)
    command = fake_bidi_conn.last_command('script.callFunction')
    assert command['params']['arguments'] == [{'type': 'number', 'value': 5}]


@pytest.mark.asyncio
async def test_get_cookies_returns_protocol_agnostic_cookies(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'storage.getCookies',
        {'cookies': [{
            'name': 'session', 'value': {'type': 'string', 'value': 'abc'},
            'domain': 'example.com', 'path': '/', 'size': 10,
            'httpOnly': False, 'secure': True, 'sameSite': 'lax',
        }]},
    )
    cookies = await fake_bidi_tab.get_cookies()
    assert cookies[0]['name'] == 'session'
    assert cookies[0]['value'] == 'abc'
    assert cookies[0]['domain'] == 'example.com'


@pytest.mark.asyncio
async def test_set_cookies_sends_set_cookie_per_cookie(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.set_cookies([{'name': 'a', 'value': '1', 'domain': 'example.com'}])
    cookie = fake_bidi_conn.last_command('storage.setCookie')['params']['cookie']
    assert cookie['name'] == 'a'
    assert cookie['value'] == {'type': 'string', 'value': '1'}
    assert cookie['domain'] == 'example.com'


@pytest.mark.asyncio
async def test_delete_all_cookies_sends_delete_cookies(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.delete_all_cookies()
    assert fake_bidi_conn.commands_for('storage.deleteCookies')
