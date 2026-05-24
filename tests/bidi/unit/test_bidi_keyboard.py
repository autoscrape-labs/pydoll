"""Unit tests for BiDiKeyboard (trusted key input via input.performActions).

The BiDi keyboard reuses Keyboard's humanized primitives and only swaps the
dispatch backend, so these assert the key-source action list it emits — modifiers
pressed as real keys around the target — against an in-memory FakeBiDiConnection.
"""

from __future__ import annotations

import pytest

from pydoll.constants import Key
from pydoll.interactions.keyboard import BiDiKeyboard, _bidi_key_value
from pydoll.protocol.cdp.input.types import KeyModifier


def _key_actions(fake_bidi_conn) -> list[dict]:
    command = fake_bidi_conn.last_command('input.performActions')
    source = command['params']['actions'][0]
    assert source['type'] == 'key'
    return source['actions']


@pytest.mark.asyncio
async def test_press_emits_keydown_and_keyup(fake_bidi_conn, fake_bidi_tab):
    keyboard = BiDiKeyboard(fake_bidi_tab)
    await keyboard.press(Key.ENTER)
    actions = _key_actions(fake_bidi_conn)
    value = _bidi_key_value(Key.ENTER)
    assert {'type': 'keyDown', 'value': value} in actions
    assert {'type': 'keyUp', 'value': value} in actions


@pytest.mark.asyncio
async def test_press_with_modifier_wraps_target_key(fake_bidi_conn, fake_bidi_tab):
    keyboard = BiDiKeyboard(fake_bidi_tab)
    await keyboard.press(Key.A, modifiers=KeyModifier.CTRL)
    types = [a['type'] for a in _key_actions(fake_bidi_conn)]
    # modifier down ... key down ... key up ... modifier up
    assert types[0] == 'keyDown'
    assert types[-1] == 'keyUp'
    assert types.count('keyDown') >= 2
    assert types.count('keyUp') >= 2


@pytest.mark.asyncio
async def test_down_then_up(fake_bidi_conn, fake_bidi_tab):
    keyboard = BiDiKeyboard(fake_bidi_tab)
    await keyboard.down(Key.A)
    assert {'type': 'keyDown', 'value': 'a'} in _key_actions(fake_bidi_conn)
    await keyboard.up(Key.A)
    assert {'type': 'keyUp', 'value': 'a'} in _key_actions(fake_bidi_conn)


@pytest.mark.asyncio
async def test_hotkey_presses_modifier_as_real_key(fake_bidi_conn, fake_bidi_tab):
    keyboard = BiDiKeyboard(fake_bidi_tab)
    await keyboard.hotkey(Key.CONTROL, Key.A)
    actions = _key_actions(fake_bidi_conn)
    values_down = [a['value'] for a in actions if a['type'] == 'keyDown']
    assert _bidi_key_value(Key.CONTROL) in values_down
    assert _bidi_key_value(Key.A) in values_down
