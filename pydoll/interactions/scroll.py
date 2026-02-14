from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from pydoll.commands import InputCommands, RuntimeCommands
from pydoll.constants import Scripts, ScrollPosition
from pydoll.interactions.utils import CubicBezier
from pydoll.protocol.input.types import MouseEventType
from pydoll.protocol.runtime.methods import EvaluateResponse

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab


@dataclass(frozen=True)
class ScrollTimingConfig:
    """Configuration for realistic scroll physics."""

    min_duration: float = 0.5
    max_duration: float = 1.5

    bezier_points: tuple[float, float, float, float] = (0.645, 0.045, 0.355, 1.0)

    frame_interval: float = 0.012

    delta_jitter: int = 3

    micro_pause_probability: float = 0.05
    micro_pause_min: float = 0.02
    micro_pause_max: float = 0.05

    overshoot_probability: float = 0.15
    overshoot_factor_min: float = 1.02
    overshoot_factor_max: float = 1.08


class Scroll:
    """
    API for controlling page scroll behavior.

    Provides methods for scrolling the page in different directions,
    to specific positions, or by relative distances. Supports humanized
    scrolling with realistic physics simulation.
    """

    def __init__(
        self,
        tab: Tab,
        timing: Optional[ScrollTimingConfig] = None,
    ):
        """
        Initialize the Scroll with a Tab instance.

        Args:
            tab: Tab instance to execute scroll commands on.
            timing: Optional custom timing configuration for humanized scroll.
        """
        self._tab = tab
        self._timing = timing or ScrollTimingConfig()

    async def by(
        self,
        position: ScrollPosition,
        distance: int | float,
        smooth: bool = True,
        humanize: bool = True,
    ):
        """
        Scroll the page by a relative distance in the specified direction.

        Args:
            position: Direction to scroll (UP, DOWN, LEFT, RIGHT).
            distance: Number of pixels to scroll.
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        if humanize:
            await self._scroll_humanized(position, distance)
            return

        axis, scroll_distance = self._get_axis_and_distance(position, distance)
        behavior = self._get_behavior(smooth)

        script = Scripts.SCROLL_BY.format(
            axis=axis,
            distance=scroll_distance,
            behavior=behavior,
        )

        await self._execute_script_await_promise(script)

    async def to_top(self, smooth: bool = True, humanize: bool = True):
        """
        Scroll to the top of the page (Y=0).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        if humanize:
            await self._scroll_to_end_humanized(ScrollPosition.UP)
            return

        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_TOP.format(behavior=behavior)
        await self._execute_script_await_promise(script)

    async def to_bottom(self, smooth: bool = True, humanize: bool = True):
        """
        Scroll to the bottom of the page (Y=document.body.scrollHeight).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
            humanize: Simulate human-like scrolling with momentum and inertia.
        """
        if humanize:
            await self._scroll_to_end_humanized(ScrollPosition.DOWN)
            return

        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_BOTTOM.format(behavior=behavior)
        await self._execute_script_await_promise(script)

    async def _scroll_to_end_humanized(self, position: ScrollPosition):
        """
        Scroll to top or bottom with multiple human-like flicks.

        Humans don't scroll thousands of pixels in one motion - they do
        multiple scroll gestures with brief pauses in between.
        """
        max_flick_distance = random.uniform(600, 1200)
        min_remaining_threshold = 30
        min_stuck_threshold = 5
        min_flick_distance = 100

        # Failsafe for stuck scroll
        last_remaining = float('inf')
        stuck_counter = 0
        max_stuck_attempts = 10

        while True:
            if position == ScrollPosition.DOWN:
                remaining = await self._get_remaining_scroll_to_bottom()
            else:
                remaining = await self._get_current_scroll_y()

            if remaining <= min_remaining_threshold:
                break

            # Check if we are stuck
            has_progressed = abs(remaining - last_remaining) >= min_stuck_threshold

            if has_progressed:
                stuck_counter = 0

            if not has_progressed:
                stuck_counter += 1
                if stuck_counter >= max_stuck_attempts:
                    break

            last_remaining = remaining

            flick_distance = min(remaining, max_flick_distance)
            if flick_distance < min_flick_distance and remaining > min_flick_distance:
                flick_distance = min_flick_distance

            await self._scroll_humanized(position, flick_distance)

            pause = random.uniform(0.05, 0.15)
            await asyncio.sleep(pause)

            max_flick_distance = random.uniform(600, 1200)

    async def _scroll_humanized(self, position: ScrollPosition, target_distance: float):
        """
        Perform scroll with realistic human-like physics.

        Simulates momentum-based scrolling with:
        - Smooth deceleration curve
        - Variable frame intervals
        - Random jitter in scroll deltas
        - Occasional micro-pauses
        - Optional overshoot and correction
        """
        is_vertical = position in {ScrollPosition.UP, ScrollPosition.DOWN}
        direction = -1 if position in {ScrollPosition.UP, ScrollPosition.LEFT} else 1

        effective_distance = self._calculate_effective_distance(target_distance)
        duration = self._calculate_duration(effective_distance)

        scrolled_so_far = await self._perform_scroll_loop(
            effective_distance, duration, is_vertical, direction
        )

        if effective_distance > target_distance and scrolled_so_far > target_distance:
            correction_distance = scrolled_so_far - target_distance
            correction_direction = -direction

            await asyncio.sleep(random.uniform(0.1, 0.2))

            await self._scroll_correction(
                is_vertical=is_vertical,
                direction=correction_direction,
                distance=correction_distance,
            )

    async def _perform_scroll_loop(
        self,
        effective_distance: float,
        duration: float,
        is_vertical: bool,
        direction: int,
    ) -> float:
        """Execute the main scroll loop using Bezier timing."""
        timing = self._timing
        bezier = CubicBezier(*timing.bezier_points)

        start_time = asyncio.get_running_loop().time()
        current_time = 0.0
        scrolled_so_far = 0.0

        while current_time < duration:
            now = asyncio.get_running_loop().time()
            current_time = now - start_time

            if current_time >= duration:
                break

            progress = current_time / duration
            eased_progress = bezier.solve(progress)

            target_pos = effective_distance * eased_progress
            delta = target_pos - scrolled_so_far

            jitter = random.randint(-timing.delta_jitter, timing.delta_jitter)
            delta += jitter

            delta = max(delta, 0)

            if delta >= 1:
                await self._dispatch_scroll_event(
                    delta_x=0 if is_vertical else int(delta * direction),
                    delta_y=int(delta * direction) if is_vertical else 0,
                )
                scrolled_so_far += delta

            frame_delay = timing.frame_interval + random.uniform(-0.002, 0.002)
            await asyncio.sleep(frame_delay)

            if random.random() < timing.micro_pause_probability:
                pause_duration = random.uniform(timing.micro_pause_min, timing.micro_pause_max)
                await asyncio.sleep(pause_duration)
                start_time += pause_duration

        return scrolled_so_far

    def _calculate_effective_distance(self, target_distance: float) -> float:
        """Calculate effective distance including overshoot."""
        timing = self._timing
        should_overshoot = random.random() < timing.overshoot_probability
        overshoot_factor = (
            random.uniform(timing.overshoot_factor_min, timing.overshoot_factor_max)
            if should_overshoot
            else 1.0
        )
        return target_distance * overshoot_factor

    def _calculate_duration(self, distance: float) -> float:
        """Calculate scroll duration based on distance."""
        timing = self._timing
        base_duration = random.uniform(timing.min_duration, timing.max_duration)
        duration = base_duration * (1 + 0.2 * (distance / 1000))
        return min(duration, 3.0)

    async def _scroll_correction(self, is_vertical: bool, direction: int, distance: float):
        """Perform small correction scroll after overshoot."""
        timing = self._timing
        scrolled = 0.0

        correction_velocity = random.uniform(200, 400)

        while scrolled < distance:
            frame_delta = correction_velocity * timing.frame_interval
            frame_delta = min(frame_delta, distance - scrolled)

            await self._dispatch_scroll_event(
                delta_x=0 if is_vertical else int(frame_delta * direction),
                delta_y=int(frame_delta * direction) if is_vertical else 0,
            )

            scrolled += frame_delta
            correction_velocity *= 0.85

            await asyncio.sleep(timing.frame_interval)

    async def _dispatch_scroll_event(self, delta_x: int, delta_y: int):
        """Dispatch a mouse wheel event for scrolling."""
        viewport = await self._get_viewport_center()
        command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_WHEEL,
            x=viewport[0],
            y=viewport[1],
            delta_x=delta_x,
            delta_y=delta_y,
        )
        await self._tab._execute_command(command)

    async def _get_viewport_center(self) -> tuple[int, int]:
        """Get the center coordinates of the viewport."""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_VIEWPORT_CENTER)
        result: EvaluateResponse = await self._tab._execute_command(command)

        value_str = result.get('result', {}).get('result', {}).get('value', '[]')
        expected_dimensions = 2
        try:
            value = json.loads(value_str)
            if value and isinstance(value, list) and len(value) == expected_dimensions:
                return (int(value[0]), int(value[1]))
        except (json.JSONDecodeError, TypeError):
            pass
        return (400, 300)

    async def _get_current_scroll_y(self) -> float:
        """Get current vertical scroll position."""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_SCROLL_Y)
        result: EvaluateResponse = await self._tab._execute_command(command)
        return float(result.get('result', {}).get('result', {}).get('value', 0))

    async def _get_remaining_scroll_to_bottom(self) -> float:
        """Get remaining distance to scroll to reach the bottom."""
        command = RuntimeCommands.evaluate(expression=Scripts.GET_REMAINING_SCROLL_TO_BOTTOM)
        result: EvaluateResponse = await self._tab._execute_command(command)
        return float(result.get('result', {}).get('result', {}).get('value', 0))

    @staticmethod
    def _get_axis_and_distance(
        position: ScrollPosition, distance: int | float
    ) -> tuple[str, int | float]:
        """
        Convert scroll position to axis and signed distance.

        Args:
            position: Direction to scroll.
            distance: Absolute distance to scroll.

        Returns:
            Tuple of (axis, signed_distance) where axis is 'left' or 'top'
            and signed_distance is positive or negative based on direction.
        """
        if position in {ScrollPosition.UP, ScrollPosition.DOWN}:
            axis = 'top'
            scroll_distance = -distance if position == ScrollPosition.UP else distance
            return axis, scroll_distance

        axis = 'left'
        scroll_distance = -distance if position == ScrollPosition.LEFT else distance
        return axis, scroll_distance

    @staticmethod
    def _get_behavior(smooth: bool) -> str:
        """
        Convert smooth boolean to CSS scroll behavior value.

        Args:
            smooth: Whether to use smooth scrolling.

        Returns:
            'smooth' if smooth is True, 'auto' otherwise.
        """
        return 'smooth' if smooth else 'auto'

    async def _execute_script_await_promise(self, script: str):
        """
        Execute JavaScript and await promise resolution.

        Args:
            script: JavaScript code that returns a Promise.
        """
        command = RuntimeCommands.evaluate(expression=script, await_promise=True)
        return await self._tab._execute_command(command)


# Backward compatibility alias
ScrollAPI = Scroll
