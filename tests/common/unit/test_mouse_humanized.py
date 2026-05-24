"""Unit tests for the humanized movement engine of Mouse.

A FakeMouseTab records the dispatched CDP mouse events (and any debug scripts),
playing the role of the browser. The humanized paths run real physics — Bezier
curves, Fitts's-law timing, overshoot/correction, tremor — so the assertions
target the observable outcome: the cursor ends on the target, a click presses
and releases there, a drag presses at the start and releases at the end, and an
overshoot still lands on target. Timing is collapsed via the public
``MouseTimingConfig`` seam so the tests stay fast.
"""

from __future__ import annotations

import dataclasses

import pytest

from pydoll.interactions.mouse import Mouse, MouseTimingConfig

FAST = MouseTimingConfig(
    frame_interval=0.001,
    frame_interval_variance=0.0,
    min_duration=0.01,
    max_duration=0.02,
    micro_pause_probability=0.0,
    pre_click_pause_min=0.0,
    pre_click_pause_max=0.0,
    click_hold_min=0.0,
    click_hold_max=0.0,
    double_click_interval_min=0.0,
    double_click_interval_max=0.0,
    drag_start_pause_min=0.0,
    drag_start_pause_max=0.0,
    drag_end_pause_min=0.0,
    drag_end_pause_max=0.0,
    overshoot_probability=0.0,
)


class FakeMouseTab:
    """Stand-in browser that records dispatched mouse events and debug scripts."""

    def __init__(self):
        self.events: list[dict] = []
        self.scripts: list[str] = []

    async def _execute_command(self, command):
        method = command['method']
        if method == 'Input.dispatchMouseEvent':
            self.events.append(command['params'])
        elif method == 'Runtime.evaluate':
            self.scripts.append(command['params']['expression'])
        return {'result': {'result': {'value': ''}}}


def _of_type(events, event_type):
    return [event for event in events if event['type'] == event_type]


@pytest.fixture
def fake_tab():
    return FakeMouseTab()


@pytest.mark.asyncio
async def test_humanized_move_lands_on_target_via_curved_path(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    await mouse.move(120, 80, humanize=True)

    moves = _of_type(fake_tab.events, 'mouseMoved')
    assert len(moves) > 2
    assert (moves[-1]['x'], moves[-1]['y']) == (120, 80)
    assert mouse._position == (120, 80)


@pytest.mark.asyncio
async def test_humanized_move_under_one_pixel_dispatches_once(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    await mouse.move(0.4, 0.4, humanize=True)

    assert len(_of_type(fake_tab.events, 'mouseMoved')) == 1


@pytest.mark.asyncio
async def test_humanized_click_presses_and_releases_on_target(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    await mouse.click(60, 40, humanize=True)

    pressed = _of_type(fake_tab.events, 'mousePressed')
    released = _of_type(fake_tab.events, 'mouseReleased')
    assert [(pressed[-1]['x'], pressed[-1]['y'])] == [(60, 40)]
    assert [(released[-1]['x'], released[-1]['y'])] == [(60, 40)]


@pytest.mark.asyncio
async def test_humanized_double_click_increments_click_count(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    await mouse.double_click(30, 30, humanize=True)

    counts = [event['clickCount'] for event in _of_type(fake_tab.events, 'mousePressed')]
    assert counts == [1, 2]


@pytest.mark.asyncio
async def test_humanized_move_with_overshoot_still_lands_on_target(fake_tab):
    timing = dataclasses.replace(FAST, overshoot_probability=1.0, overshoot_speed_threshold=0.0)
    mouse = Mouse(fake_tab, timing=timing)
    await mouse.move(300, 300, humanize=True)

    moves = _of_type(fake_tab.events, 'mouseMoved')
    assert (moves[-1]['x'], moves[-1]['y']) == (300, 300)
    assert mouse._position == (300, 300)


@pytest.mark.asyncio
async def test_humanized_drag_presses_at_start_and_releases_at_end(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    await mouse.drag(0, 0, 200, 150, humanize=True)

    pressed = _of_type(fake_tab.events, 'mousePressed')
    released = _of_type(fake_tab.events, 'mouseReleased')
    assert (pressed[0]['x'], pressed[0]['y']) == (0, 0)
    assert (released[-1]['x'], released[-1]['y']) == (200, 150)


@pytest.mark.asyncio
async def test_micro_pauses_during_move_still_land_on_target(fake_tab):
    timing = dataclasses.replace(
        FAST, micro_pause_probability=1.0, micro_pause_min=0.0, micro_pause_max=0.0
    )
    mouse = Mouse(fake_tab, timing=timing)
    await mouse.move(150, 90, humanize=True)

    moves = _of_type(fake_tab.events, 'mouseMoved')
    assert (moves[-1]['x'], moves[-1]['y']) == (150, 90)


@pytest.mark.asyncio
async def test_debug_mode_draws_overlay_dots(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST, debug=True)
    await mouse.click(50, 50, humanize=True)

    assert any('__pydoll_mouse_debug' in script for script in fake_tab.scripts)


def test_timing_property_can_be_replaced(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    assert mouse.timing is FAST
    replacement = dataclasses.replace(FAST, tremor_amplitude=0.0)
    mouse.timing = replacement
    assert mouse.timing is replacement


def test_debug_property_toggles(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST)
    assert mouse.debug is False
    mouse.debug = True
    assert mouse.debug is True


@pytest.mark.asyncio
async def test_debug_overlay_recreated_on_every_draw_so_it_survives_navigation(fake_tab):
    mouse = Mouse(fake_tab, timing=FAST, debug=True)
    await mouse.click(50, 50, humanize=True)

    overlay_scripts = [script for script in fake_tab.scripts if '__pydoll_mouse_debug' in script]
    assert overlay_scripts
    assert all('createElement' in script for script in overlay_scripts)
