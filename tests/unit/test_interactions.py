"""Dispatch-glue tests for mouse/keyboard/scroll via an in-memory FakeConnection.

Non-humanized paths produce deterministic CDP event sequences; these assert the
commands emitted. Humanized behaviour is exercised end-to-end against real
Chrome in the integration suite.
"""

from __future__ import annotations

import pytest

from pydoll.constants import Key, ScrollPosition


def _mouse_events(fake_conn):
    return fake_conn.commands_for('Input.dispatchMouseEvent')


def _key_events(fake_conn):
    return fake_conn.commands_for('Input.dispatchKeyEvent')


@pytest.mark.asyncio
async def test_mouse_click_dispatches_move_press_release(fake_conn, fake_tab):
    await fake_tab.mouse.click(50, 60)
    events = _mouse_events(fake_conn)
    assert [e['params']['type'] for e in events] == ['mouseMoved', 'mousePressed', 'mouseReleased']
    assert all(e['params']['x'] == 50 and e['params']['y'] == 60 for e in events)


@pytest.mark.asyncio
async def test_mouse_move_dispatches_moved(fake_conn, fake_tab):
    await fake_tab.mouse.move(10, 20)
    events = _mouse_events(fake_conn)
    assert [e['params']['type'] for e in events] == ['mouseMoved']
    assert events[0]['params']['x'] == 10
    assert events[0]['params']['y'] == 20


@pytest.mark.asyncio
async def test_mouse_down_then_up(fake_conn, fake_tab):
    await fake_tab.mouse.down()
    await fake_tab.mouse.up()
    assert [e['params']['type'] for e in _mouse_events(fake_conn)] == [
        'mousePressed',
        'mouseReleased',
    ]


@pytest.mark.asyncio
async def test_mouse_double_click_sets_click_count(fake_conn, fake_tab):
    await fake_tab.mouse.double_click(5, 5)
    pressed = [e for e in _mouse_events(fake_conn) if e['params']['type'] == 'mousePressed']
    assert pressed[0]['params']['clickCount'] == 2


@pytest.mark.asyncio
async def test_mouse_drag_moves_presses_moves_releases(fake_conn, fake_tab):
    await fake_tab.mouse.drag(0, 0, 100, 100)
    assert [e['params']['type'] for e in _mouse_events(fake_conn)] == [
        'mouseMoved',
        'mousePressed',
        'mouseMoved',
        'mouseReleased',
    ]


@pytest.mark.asyncio
async def test_keyboard_down_then_up(fake_conn, fake_tab):
    await fake_tab.keyboard.down(Key.A)
    await fake_tab.keyboard.up(Key.A)
    events = _key_events(fake_conn)
    assert [e['params']['type'] for e in events] == ['keyDown', 'keyUp']
    assert all(e['params']['key'] == 'A' for e in events)


@pytest.mark.asyncio
async def test_keyboard_press_dispatches_down_up(fake_conn, fake_tab):
    await fake_tab.keyboard.press(Key.ENTER, interval=0)
    events = _key_events(fake_conn)
    assert [e['params']['type'] for e in events] == ['keyDown', 'keyUp']
    assert all(e['params']['key'] == 'Enter' for e in events)


@pytest.mark.asyncio
async def test_keyboard_type_text_dispatches_each_char(fake_conn, fake_tab):
    await fake_tab.keyboard.type_text('hi')
    events = _key_events(fake_conn)
    assert [e['params']['type'] for e in events] == ['keyDown', 'keyUp', 'keyDown', 'keyUp']
    typed = [e['params']['key'] for e in events if e['params']['type'] == 'keyDown']
    assert typed == ['h', 'i']


@pytest.mark.asyncio
async def test_keyboard_hotkey_applies_modifier_to_key(fake_conn, fake_tab):
    await fake_tab.keyboard.hotkey(Key.CONTROL, Key.C)
    downs = [e for e in _key_events(fake_conn) if e['params']['type'] == 'keyDown']
    assert downs[0]['params']['key'] == 'C'
    assert downs[0]['params']['modifiers'] == 2


@pytest.mark.asyncio
async def test_scroll_by_evaluates_scroll_script(fake_conn, fake_tab):
    await fake_tab.scroll.by(ScrollPosition.DOWN, 500, smooth=False)
    sent = fake_conn.last_command('Runtime.evaluate')
    assert sent['params']['awaitPromise'] is True
    assert '500' in sent['params']['expression']


@pytest.mark.asyncio
async def test_scroll_to_top_and_bottom_evaluate_scripts(fake_conn, fake_tab):
    await fake_tab.scroll.to_top(smooth=False)
    await fake_tab.scroll.to_bottom(smooth=False)
    assert len(fake_conn.commands_for('Runtime.evaluate')) == 2
