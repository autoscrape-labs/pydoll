"""Translate-only BiDiWebElement methods against an in-memory FakeBiDiConnection.

The BiDi counterpart of tests/cdp/unit/test_web_element.py: cached state and the
BiDi commands an element emits (trusted input via input.performActions). Real DOM
behaviour (actual visibility, the click's effect) is covered in
tests/bidi/integration.
"""

from __future__ import annotations

import pytest


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
