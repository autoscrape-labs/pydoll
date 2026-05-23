"""Translate-only BiDiWebElement methods against an in-memory FakeBiDiConnection.

The BiDi counterpart of tests/cdp/unit/test_web_element.py: cached state and the
BiDi commands an element emits (trusted input via input.performActions). Real DOM
behaviour (actual visibility, the click's effect) is covered in
tests/bidi/integration.
"""

from __future__ import annotations

import pytest

from pydoll.exceptions import ElementNotVisible


def _success(remote_value: dict) -> dict:
    """A BiDi script EvaluateResult wrapping a RemoteValue."""
    return {'type': 'success', 'result': remote_value, 'realm': 'realm-1'}


async def _find(tab, conn, attributes):
    """Locate a single element with the given cached attributes."""
    conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'sharedId': 's1', 'value': {
            'localName': 'input', 'attributes': attributes}}]},
    )
    return await tab.find(tag_name='input')


@pytest.mark.asyncio
async def test_element_exposes_cached_attributes(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {'id': 'u', 'class': 'field', 'value': 'hi'})
    assert element.id == 'u'
    assert element.class_name == 'field'
    assert element.tag_name == 'input'
    assert element.value == 'hi'


@pytest.mark.asyncio
async def test_get_attribute_reads_from_cache(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {'name': 'q'})
    assert element.get_attribute('name') == 'q'
    assert element.get_attribute('missing') is None


@pytest.mark.asyncio
async def test_text_calls_function_and_deserializes(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'string', 'value': 'hello'}))
    assert await element.text == 'hello'


@pytest.mark.asyncio
async def test_execute_script_returns_deserialized_value(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'number', 'value': 7}))
    assert await element.execute_script('(el) => 7') == 7


@pytest.mark.asyncio
async def test_click_dispatches_trusted_pointer_actions(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    # scroll_into_view + is_visible read truthy via callFunction
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': True}))
    await element.click()
    command = fake_bidi_conn.last_command('input.performActions')
    assert command['params']['context'] == 'fake-context'
    pointer = command['params']['actions'][0]
    assert pointer['type'] == 'pointer'
    action_types = [action['type'] for action in pointer['actions']]
    assert 'pointerDown' in action_types
    assert 'pointerUp' in action_types


@pytest.mark.asyncio
async def test_type_text_dispatches_trusted_key_actions(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': True}))
    await element.type_text('hi')
    key_sources = [
        command['params']['actions'][0]
        for command in fake_bidi_conn.commands_for('input.performActions')
        if command['params']['actions'] and command['params']['actions'][0].get('type') == 'key'
    ]
    assert key_sources, 'expected a key input source'
    typed = [action.get('value') for source in key_sources for action in source['actions']]
    assert 'h' in typed
    assert 'i' in typed


@pytest.mark.asyncio
async def test_scroll_into_view_calls_function(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'undefined'}))
    await element.scroll_into_view()
    assert fake_bidi_conn.commands_for('script.callFunction')


@pytest.mark.asyncio
async def test_click_using_js_when_visible(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': True}))
    await element.click_using_js()
    assert fake_bidi_conn.commands_for('script.callFunction')


@pytest.mark.asyncio
async def test_click_using_js_raises_when_not_visible(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': False}))
    with pytest.raises(ElementNotVisible):
        await element.click_using_js()


@pytest.mark.asyncio
async def test_wait_until_returns_when_condition_met(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': True}))
    await element.wait_until(is_visible=True, timeout=1)


@pytest.mark.asyncio
async def test_wait_until_requires_a_condition(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    with pytest.raises(ValueError):
        await element.wait_until()


@pytest.mark.asyncio
async def test_take_screenshot_as_base64(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('browsingContext.captureScreenshot', {'data': 'Zm9v'})
    assert await element.take_screenshot(as_base64=True) == 'Zm9v'


@pytest.mark.asyncio
async def test_inner_html_reads_via_function(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'string', 'value': '<b>x</b>'}))
    assert await element.inner_html == '<b>x</b>'


@pytest.mark.asyncio
async def test_is_on_top_returns_bool(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': True}))
    assert await element.is_on_top() is True


@pytest.mark.asyncio
async def test_is_editable_returns_bool(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': False}))
    assert await element.is_editable() is False


@pytest.mark.asyncio
async def test_bounds_via_js(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'object', 'value': [
        ['x', {'type': 'number', 'value': 1}],
        ['width', {'type': 'number', 'value': 10}],
    ]}))
    bounds = await element.get_bounds_using_js()
    assert bounds['width'] == 10


@pytest.mark.asyncio
async def test_focus_sends_function_call(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'undefined'}))
    await element.focus()
    assert fake_bidi_conn.commands_for('script.callFunction')


@pytest.mark.asyncio
async def test_clear_raises_when_not_input(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'boolean', 'value': False}))
    with pytest.raises(Exception):
        await element.clear()


@pytest.mark.asyncio
async def test_insert_text_passes_text_argument(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result('script.callFunction', _success({'type': 'undefined'}))
    await element.insert_text('hello')
    args = fake_bidi_conn.last_command('script.callFunction')['params']['arguments']
    assert {'type': 'string', 'value': 'hello'} in args


@pytest.mark.asyncio
async def test_set_input_files_sends_set_files(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    await element.set_input_files('/tmp/a.txt')
    command = fake_bidi_conn.last_command('input.setFiles')
    assert command['params']['files'] == ['/tmp/a.txt']


@pytest.mark.asyncio
async def test_get_children_elements_queries_scope(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result(
        'browsingContext.locateNodes',
        {'nodes': [{'type': 'node', 'sharedId': 'k1', 'value': {'localName': 'li', 'attributes': {}}}]},
    )
    children = await element.get_children_elements()
    assert len(children) == 1
    assert fake_bidi_conn.last_command('browsingContext.locateNodes')['params']['locator']['value'] == ':scope > *'


@pytest.mark.asyncio
async def test_take_screenshot_requires_path_or_base64(fake_bidi_conn, fake_bidi_tab):
    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    with pytest.raises(Exception):
        await element.take_screenshot()


@pytest.mark.asyncio
async def test_take_screenshot_writes_file(fake_bidi_conn, fake_bidi_tab, tmp_path):
    import base64

    element = await _find(fake_bidi_tab, fake_bidi_conn, {})
    fake_bidi_conn.set_result(
        'browsingContext.captureScreenshot', {'data': base64.b64encode(b'img').decode()}
    )
    out = tmp_path / 'el.png'
    await element.take_screenshot(path=str(out))
    assert out.read_bytes() == b'img'
