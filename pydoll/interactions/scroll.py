from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.commands import RuntimeCommands
from pydoll.constants import Scripts, ScrollPosition

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab


class ScrollAPI:
    """
    API for controlling page scroll behavior.

    Provides methods for scrolling the page in different directions,
    to specific positions, or by relative distances.
    """

    def __init__(self, tab: Tab):
        """
        Initialize the ScrollAPI with a tab instance.

        Args:
            tab: Tab instance to execute scroll commands on.
        """
        self._tab = tab

    async def by(
        self,
        position: ScrollPosition,
        distance: int | float,
        smooth: bool = True,
    ):
        """
        Scroll the page by a relative distance in the specified direction.

        Args:
            position: Direction to scroll (UP, DOWN, LEFT, RIGHT).
            distance: Number of pixels to scroll.
            smooth: Use smooth scrolling animation if True, instant if False.
        """
        axis, scroll_distance = self._get_axis_and_distance(position, distance)
        behavior = self._get_behavior(smooth)

        script = Scripts.SCROLL_BY.format(
            axis=axis,
            distance=scroll_distance,
            behavior=behavior,
        )

        await self._execute_script_await_promise(script)

    async def to_top(self, smooth: bool = True):
        """
        Scroll to the top of the page (Y=0).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
        """
        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_TOP.format(behavior=behavior)
        await self._execute_script_await_promise(script)

    async def to_bottom(self, smooth: bool = True):
        """
        Scroll to the bottom of the page (Y=document.body.scrollHeight).

        Args:
            smooth: Use smooth scrolling animation if True, instant if False.
        """
        behavior = self._get_behavior(smooth)
        script = Scripts.SCROLL_TO_BOTTOM.format(behavior=behavior)
        await self._execute_script_await_promise(script)

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
            return axis, scroll_distance * 10

        axis = 'left'
        scroll_distance = -distance if position == ScrollPosition.LEFT else distance
        return axis, scroll_distance * 10

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
