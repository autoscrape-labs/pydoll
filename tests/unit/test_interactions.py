"""Behavioural tests for mouse/keyboard/scroll via an in-memory FakeConnection.

Assertions target the observable effect of each interaction — where the click
landed, which characters were typed, that a scroll was issued — rather than the
exact internal sequence of CDP events, so they survive refactors of the dispatch.
"""

from __future__ import annotations

import pytest

from pydoll.constants import Key, ScrollPosition


def _mouse_events(fake_conn):
    return fake_conn.commands_for('Input.dispatchMouseEvent')


def _key_events(fake_conn):
    return fake_conn.commands_for('Input.dispatchKeyEvent')


def _of_type(events, event_type):
    return [event for event in events if event['params']['type'] == event_type]


def _points(events):
    return [(event['params']['x'], event['params']['y']) for event in events]


@pytest.mark.asyncio
async def test_mouse_click_presses_and_releases_at_target(fake_conn, fake_tab):
    await fake_tab.mouse.click(50, 60)
    events = _mouse_events(fake_conn)
    assert _points(_of_type(events, 'mousePressed')) == [(50, 60)]
    assert _points(_of_type(events, 'mouseReleased')) == [(50, 60)]


@pytest.mark.asyncio
async def test_mouse_move_positions_cursor_at_target(fake_conn, fake_tab):
    await fake_tab.mouse.move(10, 20)
    assert _points(_of_type(_mouse_events(fake_conn), 'mouseMoved'))[-1] == (10, 20)


@pytest.mark.asyncio
async def test_mouse_down_presses_and_up_releases(fake_conn, fake_tab):
    await fake_tab.mouse.down()
    assert _of_type(_mouse_events(fake_conn), 'mousePressed')
    await fake_tab.mouse.up()
    assert _of_type(_mouse_events(fake_conn), 'mouseReleased')


@pytest.mark.asyncio
async def test_double_click_uses_click_count_two(fake_conn, fake_tab):
    await fake_tab.mouse.double_click(5, 5)
    assert _of_type(_mouse_events(fake_conn), 'mousePressed')[0]['params']['clickCount'] == 2


@pytest.mark.asyncio
async def test_drag_presses_at_start_and_releases_at_end(fake_conn, fake_tab):
    await fake_tab.mouse.drag(0, 0, 100, 100)
    events = _mouse_events(fake_conn)
    assert _points(_of_type(events, 'mousePressed'))[0] == (0, 0)
    assert _points(_of_type(events, 'mouseReleased'))[0] == (100, 100)


@pytest.mark.asyncio
async def test_keyboard_down_then_up_for_a_key(fake_conn, fake_tab):
    await fake_tab.keyboard.down(Key.A)
    assert _of_type(_key_events(fake_conn), 'keyDown')[-1]['params']['key'] == 'A'
    await fake_tab.keyboard.up(Key.A)
    assert _of_type(_key_events(fake_conn), 'keyUp')[-1]['params']['key'] == 'A'


@pytest.mark.asyncio
async def test_keyboard_press_presses_and_releases_the_key(fake_conn, fake_tab):
    await fake_tab.keyboard.press(Key.ENTER, interval=0)
    assert _of_type(_key_events(fake_conn), 'keyDown')[0]['params']['key'] == 'Enter'
    assert _of_type(_key_events(fake_conn), 'keyUp')[0]['params']['key'] == 'Enter'


@pytest.mark.asyncio
async def test_keyboard_type_text_types_each_character_in_order(fake_conn, fake_tab):
    await fake_tab.keyboard.type_text('hi')
    typed = [event['params']['key'] for event in _of_type(_key_events(fake_conn), 'keyDown')]
    assert typed == ['h', 'i']


@pytest.mark.asyncio
async def test_keyboard_hotkey_applies_modifier_to_key(fake_conn, fake_tab):
    await fake_tab.keyboard.hotkey(Key.CONTROL, Key.C)
    down = _of_type(_key_events(fake_conn), 'keyDown')[0]
    assert down['params']['key'] == 'C'
    assert down['params']['modifiers'] == 2


@pytest.mark.asyncio
async def test_scroll_by_issues_scroll_with_distance(fake_conn, fake_tab):
    await fake_tab.scroll.by(ScrollPosition.DOWN, 500, smooth=False)
    sent = fake_conn.last_command('Runtime.evaluate')
    assert sent['params']['awaitPromise'] is True
    assert '500' in sent['params']['expression']


@pytest.mark.asyncio
async def test_scroll_to_top_issues_a_scroll(fake_conn, fake_tab):
    await fake_tab.scroll.to_top(smooth=False)
    assert fake_conn.commands_for('Runtime.evaluate')


@pytest.mark.asyncio
async def test_scroll_to_bottom_issues_a_scroll(fake_conn, fake_tab):
    await fake_tab.scroll.to_bottom(smooth=False)
    assert fake_conn.commands_for('Runtime.evaluate')
