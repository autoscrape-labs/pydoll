"""Keyboard, Mouse and Touchscreen with Playwright semantics over CDP Input events."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal, Optional

from pydoll.commands import InputCommands
from pydoll.playwright._keys import (
    MODIFIER_NAMES,
    KeyDescription,
    describe_key,
    modifier_bits,
    resolve_smart_modifier,
    split_key_string,
)
from pydoll.protocol.input.types import (
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
    TouchEventType,
)

if TYPE_CHECKING:
    from pydoll.playwright._page import Page

MouseButtonName = Literal['left', 'right', 'middle']

_BUTTONS = {'left': MouseButton.LEFT, 'right': MouseButton.RIGHT, 'middle': MouseButton.MIDDLE}


class Keyboard:
    """``page.keyboard``: low-level key events routed to the focused element."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._pressed_modifiers: set[str] = set()
        self._pressed_keys: set[str] = set()

    def _modifiers(self) -> Optional[KeyModifier]:
        return modifier_bits(sorted(self._pressed_modifiers))

    async def down(self, key: str) -> None:
        description = describe_key(key, 'Shift' in self._pressed_modifiers)
        auto_repeat = description.code in self._pressed_keys
        self._pressed_keys.add(description.code)
        if description.key in MODIFIER_NAMES:
            self._pressed_modifiers.add(description.key)
        text = description.text
        if len(self._pressed_modifiers - {'Shift'}) > 0:
            text = ''
        await self._page._send(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_DOWN if text else KeyEventType.RAW_KEY_DOWN,
                modifiers=self._modifiers(),
                windows_virtual_key_code=description.key_code_without_location,
                code=description.code,
                key=description.key,
                text=text or None,
                unmodified_text=text or None,
                auto_repeat=auto_repeat,
                location=description.location or None,  # type: ignore[arg-type]
                is_keypad=description.location == 3,  # noqa: PLR2004
            )
        )

    async def up(self, key: str) -> None:
        description = describe_key(key, 'Shift' in self._pressed_modifiers)
        if description.key in MODIFIER_NAMES:
            self._pressed_modifiers.discard(description.key)
        self._pressed_keys.discard(description.code)
        await self._page._send(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_UP,
                modifiers=self._modifiers(),
                key=description.key,
                windows_virtual_key_code=description.key_code_without_location,
                code=description.code,
                location=description.location or None,  # type: ignore[arg-type]
            )
        )

    async def insert_text(self, text: str) -> None:
        await self._page._send(InputCommands.insert_text(text))

    async def type(self, text: str, delay: Optional[float] = None) -> None:
        for char in text:
            description = _safe_describe(char)
            if description is None or not description.code:
                await self.insert_text(char)
            else:
                await self.press(char, delay=delay)
            if delay:
                await asyncio.sleep(delay / 1000)

    async def press(self, key: str, delay: Optional[float] = None) -> None:
        tokens = split_key_string(key)
        last = tokens[-1]
        for token in tokens[:-1]:
            await self.down(token)
        await self.down(last)
        if delay:
            await asyncio.sleep(delay / 1000)
        await self.up(last)
        for token in reversed(tokens[:-1]):
            await self.up(token)

    async def _ensure_modifiers(self, modifiers: list[str]) -> list[str]:
        wanted = {resolve_smart_modifier(name) for name in modifiers}
        for name in wanted:
            if name not in MODIFIER_NAMES:
                raise ValueError(f'Unknown modifier {name}')
        restore = sorted(self._pressed_modifiers)
        for name in MODIFIER_NAMES:
            need_down = name in wanted
            is_down = name in self._pressed_modifiers
            if need_down and not is_down:
                await self.down(name)
            elif not need_down and is_down:
                await self.up(name)
        return restore


def _safe_describe(char: str) -> Optional[KeyDescription]:
    try:
        return describe_key(char, False)
    except ValueError:
        return None


class Mouse:
    """``page.mouse``: pointer events in main-frame CSS pixels."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._x = 0.0
        self._y = 0.0
        self._button: MouseButton = MouseButton.NONE
        self._pressed_buttons: set[MouseButton] = set()

    async def move(self, x: float, y: float, steps: Optional[int] = None) -> None:
        steps = steps or 1
        from_x, from_y = self._x, self._y
        for i in range(1, steps + 1):
            self._x = from_x + (x - from_x) * (i / steps)
            self._y = from_y + (y - from_y) * (i / steps)
            await self._page._send(
                InputCommands.dispatch_mouse_event(
                    type=MouseEventType.MOUSE_MOVED,
                    x=int(self._x),
                    y=int(self._y),
                    button=self._button,
                    modifiers=self._page.keyboard._modifiers(),
                )
            )

    async def down(
        self, button: MouseButtonName = 'left', click_count: Optional[int] = None
    ) -> None:
        self._button = _BUTTONS[button]
        self._pressed_buttons.add(self._button)
        await self._page._send(
            InputCommands.dispatch_mouse_event(
                type=MouseEventType.MOUSE_PRESSED,
                x=int(self._x),
                y=int(self._y),
                button=self._button,
                click_count=click_count or 1,
                modifiers=self._page.keyboard._modifiers(),
            )
        )

    async def up(self, button: MouseButtonName = 'left', click_count: Optional[int] = None) -> None:
        released = _BUTTONS[button]
        self._pressed_buttons.discard(released)
        self._button = MouseButton.NONE
        await self._page._send(
            InputCommands.dispatch_mouse_event(
                type=MouseEventType.MOUSE_RELEASED,
                x=int(self._x),
                y=int(self._y),
                button=released,
                click_count=click_count or 1,
                modifiers=self._page.keyboard._modifiers(),
            )
        )

    async def click(
        self,
        x: float,
        y: float,
        delay: Optional[float] = None,
        button: MouseButtonName = 'left',
        click_count: Optional[int] = None,
    ) -> None:
        await self.move(x, y)
        await self.down(button=button, click_count=click_count)
        if delay:
            await asyncio.sleep(delay / 1000)
        await self.up(button=button, click_count=click_count)

    async def dblclick(
        self,
        x: float,
        y: float,
        delay: Optional[float] = None,
        button: MouseButtonName = 'left',
    ) -> None:
        await self.move(x, y)
        await self.down(button=button, click_count=1)
        if delay:
            await asyncio.sleep(delay / 1000)
        await self.up(button=button, click_count=1)
        await self.down(button=button, click_count=2)
        if delay:
            await asyncio.sleep(delay / 1000)
        await self.up(button=button, click_count=2)

    async def wheel(self, delta_x: float, delta_y: float) -> None:
        await self._page._send(
            InputCommands.dispatch_mouse_event(
                type=MouseEventType.MOUSE_WHEEL,
                x=int(self._x),
                y=int(self._y),
                delta_x=delta_x,
                delta_y=delta_y,
                modifiers=self._page.keyboard._modifiers(),
            )
        )


class Touchscreen:
    """``page.touchscreen``: a single-finger tap."""

    def __init__(self, page: Page) -> None:
        self._page = page

    async def tap(self, x: float, y: float) -> None:
        await self._page._send(
            InputCommands.dispatch_touch_event(
                type=TouchEventType.TOUCH_START,
                touch_points=[{'x': x, 'y': y}],
                modifiers=self._page.keyboard._modifiers(),
            )
        )
        await self._page._send(
            InputCommands.dispatch_touch_event(
                type=TouchEventType.TOUCH_END,
                touch_points=[],
                modifiers=self._page.keyboard._modifiers(),
            )
        )
