"""Unit tests for the humanized scrolling engine of Scroll.

The momentum-based scroller dispatches mouse-wheel events and reads back the
page's scroll position via injected JavaScript. ``FakeScrollPage`` simulates a
real scrollable document: each wheel event moves ``scrollY`` (clamped to the
content bounds) and the JS reads (scrollY / remaining-to-bottom / viewport
center) report that simulated state. Tests therefore assert the observable
outcome — the page ended up at the top/bottom, the wheel went the right way, an
overshoot produced a corrective reverse flick — not the per-frame deltas.

Physics knobs come from the public ``ScrollTimingConfig`` so timing collapses to
near-instant and overshoot/micro-pause can be forced without touching ``random``.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from pydoll.constants import Scripts, ScrollPosition
from pydoll.interactions.scroll import Scroll, ScrollTimingConfig

FAST = ScrollTimingConfig(
    min_duration=0.06,
    max_duration=0.06,
    frame_interval=0.001,
    delta_jitter=0,
    micro_pause_probability=0.0,
    overshoot_probability=0.0,
)


class FakeScrollPage:
    """Simulates a scrollable page driven by CDP mouse-wheel events."""

    def __init__(self, content_height=4000, viewport_height=800, viewport_width=1200):
        self.scroll_y = 0.0
        self.content_height = content_height
        self.viewport_height = viewport_height
        self.viewport_width = viewport_width
        self.wheel_events: list[dict] = []
        self.broken_viewport = False

    @property
    def max_scroll(self) -> float:
        return float(max(0, self.content_height - self.viewport_height))

    async def _execute_command(self, command):
        method = command['method']
        if method == 'Input.dispatchMouseEvent':
            params = command['params']
            if params.get('type') == 'mouseWheel':
                self.wheel_events.append(params)
                self.scroll_y = min(self.max_scroll, max(0.0, self.scroll_y + params['deltaY']))
            return {}
        if method == 'Runtime.evaluate':
            return self._evaluate(command['params']['expression'])
        return {}

    def _evaluate(self, expression: str):
        if expression == Scripts.GET_VIEWPORT_CENTER:
            if self.broken_viewport:
                value = 'not-json'
            else:
                value = json.dumps([self.viewport_width // 2, self.viewport_height // 2])
        elif expression == Scripts.GET_SCROLL_Y:
            value = self.scroll_y
        elif expression == Scripts.GET_REMAINING_SCROLL_TO_BOTTOM:
            value = self.max_scroll - self.scroll_y
        else:
            value = ''
        return {'result': {'result': {'value': value}}}


def _delta_ys(page: FakeScrollPage) -> list[int]:
    return [event['deltaY'] for event in page.wheel_events]


@pytest.mark.asyncio
async def test_humanized_scroll_down_advances_the_page():
    page = FakeScrollPage()
    await Scroll(page, timing=FAST).by(ScrollPosition.DOWN, 500, humanize=True)

    assert page.wheel_events
    assert all(delta >= 0 for delta in _delta_ys(page))
    assert 300 < page.scroll_y <= 520


@pytest.mark.asyncio
async def test_humanized_scroll_up_moves_the_page_back():
    page = FakeScrollPage()
    page.scroll_y = 1000.0
    await Scroll(page, timing=FAST).by(ScrollPosition.UP, 400, humanize=True)

    assert any(delta < 0 for delta in _delta_ys(page))
    assert page.scroll_y < 1000.0


@pytest.mark.asyncio
async def test_overshoot_triggers_a_corrective_reverse_flick():
    timing = dataclasses.replace(FAST, overshoot_probability=1.0)
    page = FakeScrollPage()
    await Scroll(page, timing=timing).by(ScrollPosition.DOWN, 500, humanize=True)

    deltas = _delta_ys(page)
    assert any(delta > 0 for delta in deltas)
    assert any(delta < 0 for delta in deltas)


@pytest.mark.asyncio
async def test_micro_pauses_do_not_break_scrolling():
    timing = dataclasses.replace(
        FAST, micro_pause_probability=1.0, micro_pause_min=0.0, micro_pause_max=0.0
    )
    page = FakeScrollPage()
    await Scroll(page, timing=timing).by(ScrollPosition.DOWN, 300, humanize=True)

    assert page.scroll_y > 0


@pytest.mark.asyncio
async def test_humanized_scroll_to_bottom_reaches_the_end():
    page = FakeScrollPage(content_height=2000, viewport_height=800)
    await Scroll(page, timing=FAST).to_bottom(humanize=True)

    assert page.scroll_y >= page.max_scroll - 30


@pytest.mark.asyncio
async def test_humanized_scroll_to_top_returns_to_origin():
    page = FakeScrollPage(content_height=2000, viewport_height=800)
    page.scroll_y = page.max_scroll
    await Scroll(page, timing=FAST).to_top(humanize=True)

    assert page.scroll_y <= 30


@pytest.mark.asyncio
async def test_wheel_uses_viewport_center_fallback_on_bad_json():
    page = FakeScrollPage()
    page.broken_viewport = True
    await Scroll(page, timing=FAST).by(ScrollPosition.DOWN, 200, humanize=True)

    assert page.wheel_events
    assert all(event['x'] == 400 and event['y'] == 300 for event in page.wheel_events)
