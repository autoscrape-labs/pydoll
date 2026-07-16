"""Translate-only BiDiTab feature methods against an in-memory FakeBiDiConnection.

Covers the BiDiTab surface beyond navigation/find (tested in
test_bidi_tab_commands): screenshots, PDF, dialogs, shadow-root collection, and
network introspection. Assertions check the command shape and returned value;
real event-driven behaviour runs against Firefox in the integration suite.
"""

from __future__ import annotations

import base64

import pytest

from pydoll.exceptions import NetworkEventsNotEnabled


@pytest.mark.asyncio
async def test_take_screenshot_as_base64_returns_data(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.captureScreenshot', {'data': 'Zm9v'})
    data = await fake_bidi_tab.take_screenshot(as_base64=True)
    assert data == 'Zm9v'


@pytest.mark.asyncio
async def test_take_screenshot_writes_file(fake_bidi_conn, fake_bidi_tab, tmp_path):
    payload = base64.b64encode(b'imgbytes').decode()
    fake_bidi_conn.set_result('browsingContext.captureScreenshot', {'data': payload})
    out = tmp_path / 'shot.png'
    result = await fake_bidi_tab.take_screenshot(path=str(out))
    assert result is None
    assert out.read_bytes() == b'imgbytes'


@pytest.mark.asyncio
async def test_take_screenshot_jpeg_uses_jpeg_format(fake_bidi_conn, fake_bidi_tab, tmp_path):
    fake_bidi_conn.set_result('browsingContext.captureScreenshot', {'data': 'Zm9v'})
    await fake_bidi_tab.take_screenshot(path=str(tmp_path / 'shot.jpg'), quality=50)
    image_format = fake_bidi_conn.last_command('browsingContext.captureScreenshot')['params']['format']
    assert image_format['type'] == 'image/jpeg'
    assert image_format['quality'] == 0.5


@pytest.mark.asyncio
async def test_print_to_pdf_as_base64(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.print', {'data': 'cGRm'})
    data = await fake_bidi_tab.print_to_pdf(as_base64=True)
    assert data == 'cGRm'


@pytest.mark.asyncio
async def test_print_to_pdf_landscape_carries_orientation(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('browsingContext.print', {'data': 'cGRm'})
    await fake_bidi_tab.print_to_pdf(landscape=True)
    assert fake_bidi_conn.last_command('browsingContext.print')['params']['orientation'] == 'landscape'


@pytest.mark.asyncio
async def test_refresh_with_ignore_cache(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.refresh(ignore_cache=True)
    assert fake_bidi_conn.last_command('browsingContext.reload')['params']['ignoreCache'] is True


@pytest.mark.asyncio
async def test_has_dialog_reflects_connection_state(fake_bidi_conn, fake_bidi_tab):
    assert await fake_bidi_tab.has_dialog() is False
    fake_bidi_conn.dialog = {'params': {'message': 'are you sure?'}}
    assert await fake_bidi_tab.has_dialog() is True


@pytest.mark.asyncio
async def test_get_dialog_message_reads_connection_dialog(fake_bidi_conn, fake_bidi_tab):
    assert await fake_bidi_tab.get_dialog_message() == ''
    fake_bidi_conn.dialog = {'params': {'message': 'hello?'}}
    assert await fake_bidi_tab.get_dialog_message() == 'hello?'


@pytest.mark.asyncio
async def test_handle_dialog_carries_accept_and_text(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.handle_dialog(accept=True, prompt_text='typed')
    params = fake_bidi_conn.last_command('browsingContext.handleUserPrompt')['params']
    assert params['accept'] is True
    assert params['userText'] == 'typed'


@pytest.mark.asyncio
async def test_set_cookies_carries_optional_attributes(fake_bidi_conn, fake_bidi_tab):
    await fake_bidi_tab.set_cookies([{
        'name': 'a', 'value': '1', 'domain': 'example.com',
        'path': '/x', 'httpOnly': True, 'secure': True, 'expiry': 123, 'sameSite': 'Strict',
    }])
    cookie = fake_bidi_conn.last_command('storage.setCookie')['params']['cookie']
    assert cookie['path'] == '/x'
    assert cookie['httpOnly'] is True
    assert cookie['secure'] is True
    assert cookie['expiry'] == 123
    assert cookie['sameSite'] == 'strict'


@pytest.mark.asyncio
async def test_find_shadow_roots_collects_open_and_closed(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'value': {'shadowRoot': {
            'type': 'node', 'sharedId': 's1', 'value': {'mode': 'open', 'children': []},
        }, 'children': []}}]},
    )
    roots = await fake_bidi_tab.find_shadow_roots()
    assert len(roots) == 1
    assert roots[0].mode == 'open'


@pytest.mark.asyncio
async def test_get_network_response_body_requires_enable(fake_bidi_tab):
    with pytest.raises(NetworkEventsNotEnabled):
        await fake_bidi_tab.get_network_response_body('req-1')


@pytest.mark.asyncio
async def test_get_network_logs_enables_and_filters_by_context(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    fake_bidi_conn.network_logs = [
        {'params': {'context': 'fake-context', 'request': {'url': 'http://x/keep'}}},
        {'params': {'context': 'other', 'request': {'url': 'http://x/drop'}}},
    ]
    logs = await fake_bidi_tab.get_network_logs()
    urls = [log['params']['request']['url'] for log in logs]
    assert urls == ['http://x/keep']
    assert fake_bidi_conn.commands_for('network.addDataCollector')


@pytest.mark.asyncio
async def test_get_network_logs_filter_substring(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    fake_bidi_conn.network_logs = [
        {'params': {'context': 'fake-context', 'request': {'url': 'http://x/api/a'}}},
        {'params': {'context': 'fake-context', 'request': {'url': 'http://x/page'}}},
    ]
    logs = await fake_bidi_tab.get_network_logs(filter='/api/')
    assert [log['params']['request']['url'] for log in logs] == ['http://x/api/a']


@pytest.mark.asyncio
async def test_get_network_response_body_decodes_base64(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    await fake_bidi_tab.get_network_logs()  # enables introspection
    body_b64 = base64.b64encode(b'{"ok":true}').decode()
    fake_bidi_conn.set_result('network.getData', {'bytes': {'type': 'base64', 'value': body_b64}})
    assert await fake_bidi_tab.get_network_response_body('req-1') == '{"ok":true}'


@pytest.mark.asyncio
async def test_get_network_response_body_returns_string_value(fake_bidi_conn, fake_bidi_tab):
    fake_bidi_conn.set_result('network.addDataCollector', {'collector': 'col-1'})
    await fake_bidi_tab.get_network_logs()
    fake_bidi_conn.set_result('network.getData', {'bytes': {'type': 'string', 'value': 'plain'}})
    assert await fake_bidi_tab.get_network_response_body('req-1') == 'plain'
