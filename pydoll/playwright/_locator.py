"""Locator and FrameLocator: lazy, strict, auto-waiting element references."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Pattern, Sequence, TypedDict

from pydoll.elements.web_element import WebElement
from pydoll.playwright._actions import Resolver
from pydoll.playwright._element_handle import ElementHandle
from pydoll.playwright._errors import Error
from pydoll.playwright._selectors import (
    ENTER_FRAME,
    TextMatch,
    get_by_alt_text_selector,
    get_by_label_selector,
    get_by_placeholder_selector,
    get_by_role_selector,
    get_by_test_id_selector,
    get_by_text_selector,
    get_by_title_selector,
    with_has,
    with_has_not,
    with_has_not_text,
    with_has_text,
    with_visible,
)

if TYPE_CHECKING:
    from pydoll.playwright._frame import Frame
    from pydoll.playwright._page import Page


class FilePayload(TypedDict, total=False):
    name: str
    mimeType: str
    buffer: bytes


class SelectOption(TypedDict, total=False):
    value: str
    label: str
    index: int


Position = dict[str, float]


class Locator:
    """A way to find element(s) on the page at any moment."""

    def __init__(
        self,
        frame: Frame,
        selector: str,
        has_text: TextMatch | None = None,
        has_not_text: TextMatch | None = None,
        has: Locator | None = None,
        has_not: Locator | None = None,
        visible: bool | None = None,
    ) -> None:
        self._frame = frame
        self._selector = selector
        if has_text is not None:
            self._selector = with_has_text(self._selector, has_text)
        if has is not None:
            if has._frame is not frame:
                raise Error('Inner "has" locator must belong to the same frame.')
            self._selector = with_has(self._selector, has._selector)
        if has_not_text is not None:
            self._selector = with_has_not_text(self._selector, has_not_text)
        if has_not is not None:
            if has_not._frame is not frame:
                raise Error('Inner "has_not" locator must belong to the same frame.')
            self._selector = with_has_not(self._selector, has_not._selector)
        if visible is not None:
            self._selector = with_visible(self._selector, visible)

    def __repr__(self) -> str:
        return f'<Locator frame={self._frame!r} selector={self._selector!r}>'

    @property
    def page(self) -> Page:
        return self._frame.page

    @property
    def selector(self) -> str:
        """The resolved selector string, in Playwright's ``>>`` syntax."""
        return self._selector

    def _resolver(self, strict: bool = True) -> Resolver:
        async def find() -> WebElement | None:
            return await self._frame._query_one(self._selector, strict=strict)

        return Resolver(find, f'locator({json.dumps(self._selector)})')

    def _equals(self, other: Locator) -> bool:
        return self._frame is other._frame and self._selector == other._selector

    # ---------------------------------------------------------- composition

    def locator(
        self,
        selector_or_locator: str | Locator,
        has_text: TextMatch | None = None,
        has_not_text: TextMatch | None = None,
        has: Locator | None = None,
        has_not: Locator | None = None,
    ) -> Locator:
        if isinstance(selector_or_locator, str):
            return Locator(
                self._frame,
                f'{self._selector} >> {selector_or_locator}',
                has_text=has_text,
                has_not_text=has_not_text,
                has=has,
                has_not=has_not,
            )
        if selector_or_locator._frame is not self._frame:
            raise Error('Locators must belong to the same frame.')
        return Locator(
            self._frame,
            f'{self._selector} >> internal:chain={json.dumps(selector_or_locator._selector)}',
            has_text=has_text,
            has_not_text=has_not_text,
            has=has,
            has_not=has_not,
        )

    def get_by_alt_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_alt_text_selector(text, exact=exact))

    def get_by_label(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_label_selector(text, exact=exact))

    def get_by_placeholder(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_placeholder_selector(text, exact=exact))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return self.locator(get_by_role_selector(role, **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return self.locator(get_by_test_id_selector(test_id))

    def get_by_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_text_selector(text, exact=exact))

    def get_by_title(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_title_selector(text, exact=exact))

    def frame_locator(self, selector: str) -> FrameLocator:
        return FrameLocator(self._frame, f'{self._selector} >> {selector}')

    @property
    def first(self) -> Locator:
        return Locator(self._frame, f'{self._selector} >> nth=0')

    @property
    def last(self) -> Locator:
        return Locator(self._frame, f'{self._selector} >> nth=-1')

    def nth(self, index: int) -> Locator:
        return Locator(self._frame, f'{self._selector} >> nth={index}')

    @property
    def content_frame(self) -> FrameLocator:
        return FrameLocator(self._frame, self._selector)

    def describe(self, description: str) -> Locator:
        return Locator(
            self._frame, f'{self._selector} >> internal:describe={json.dumps(description)}'
        )

    @property
    def description(self) -> str | None:
        match = re.search(r' >> internal:describe=("(?:[^"\\]|\\.)*")$', self._selector)
        return json.loads(match.group(1)) if match else None

    def filter(
        self,
        has_text: TextMatch | None = None,
        has_not_text: TextMatch | None = None,
        has: Locator | None = None,
        has_not: Locator | None = None,
        visible: bool | None = None,
    ) -> Locator:
        return Locator(
            self._frame,
            self._selector,
            has_text=has_text,
            has_not_text=has_not_text,
            has=has,
            has_not=has_not,
            visible=visible,
        )

    def or_(self, locator: Locator) -> Locator:
        if locator._frame is not self._frame:
            raise Error('Locators must belong to the same frame.')
        return Locator(
            self._frame, f'{self._selector} >> internal:or={json.dumps(locator._selector)}'
        )

    def and_(self, locator: Locator) -> Locator:
        if locator._frame is not self._frame:
            raise Error('Locators must belong to the same frame.')
        return Locator(
            self._frame, f'{self._selector} >> internal:and={json.dumps(locator._selector)}'
        )

    # ---------------------------------------------------------- resolution

    async def element_handle(self, timeout: float | None = None) -> ElementHandle:
        element = await self._frame.wait_for_selector(
            self._selector, state='attached', timeout=timeout, strict=True
        )
        if element is None:
            raise Error(f'Could not resolve {self._selector} to DOM Element')
        return element

    async def element_handles(self) -> list[ElementHandle]:
        return [
            ElementHandle(self._frame, element)
            for element in await self._frame._query_all(self._selector)
        ]

    async def all(self) -> list[Locator]:
        return [self.nth(index) for index in range(await self.count())]

    async def count(self) -> int:
        return len(await self._frame._query_all(self._selector))

    async def all_inner_texts(self) -> list[str]:
        elements = await self._frame._query_all(self._selector)
        return await self._frame._evaluate_on_elements(
            elements, 'elements => elements.map(e => e.innerText)'
        )

    async def all_text_contents(self) -> list[str]:
        elements = await self._frame._query_all(self._selector)
        return await self._frame._evaluate_on_elements(
            elements, "elements => elements.map(e => e.textContent || '')"
        )

    async def wait_for(self, timeout: float | None = None, state: str = 'visible') -> None:
        await self._frame.wait_for_selector(
            self._selector, state=state, timeout=timeout, strict=True
        )

    async def wait_for_function(
        self, expression: str, arg: Any = None, timeout: float | None = None, polling: Any = None
    ) -> Any:
        handle = await self._frame.wait_for_selector(
            self._selector, state='attached', timeout=timeout, strict=True
        )
        if handle is None:
            raise Error(f'Could not resolve {self._selector} to DOM Element')
        return await self._frame._wait_for_function(
            expression, arg, timeout=timeout, polling=polling, element=handle.web_element
        )

    # ---------------------------------------------------------- evaluate

    async def evaluate(self, expression: str, arg: Any = None, timeout: float | None = None) -> Any:
        handle = await self.element_handle(timeout=timeout)
        return await handle.evaluate(expression, arg)

    async def evaluate_handle(
        self, expression: str, arg: Any = None, timeout: float | None = None
    ) -> Any:
        handle = await self.element_handle(timeout=timeout)
        return await handle.evaluate_handle(expression, arg)

    async def evaluate_all(self, expression: str, arg: Any = None) -> Any:
        elements = await self._frame._query_all(self._selector)
        return await self._frame._evaluate_on_elements(elements, expression, arg)

    # ---------------------------------------------------------- actions

    async def click(self, **kwargs: Any) -> None:
        await self._frame._actions.click(self._resolver(), **kwargs)

    async def dblclick(self, **kwargs: Any) -> None:
        await self._frame._actions.dblclick(self._resolver(), **kwargs)

    async def hover(self, **kwargs: Any) -> None:
        await self._frame._actions.hover(self._resolver(), **kwargs)

    async def tap(self, **kwargs: Any) -> None:
        await self._frame._actions.tap(self._resolver(), **kwargs)

    async def fill(
        self,
        value: str,
        timeout: float | None = None,
        force: bool | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.fill(self._resolver(), value, timeout=timeout, force=force)

    async def clear(
        self,
        timeout: float | None = None,
        force: bool | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.fill(self._resolver(), '', timeout=timeout, force=force)

    async def type(
        self,
        text: str,
        delay: float | None = None,
        timeout: float | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.type(self._resolver(), text, delay=delay, timeout=timeout)

    async def press_sequentially(
        self,
        text: str,
        delay: float | None = None,
        timeout: float | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.type(self._resolver(), text, delay=delay, timeout=timeout)

    async def press(
        self,
        key: str,
        delay: float | None = None,
        timeout: float | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.press(self._resolver(), key, delay=delay, timeout=timeout)

    async def focus(self, timeout: float | None = None) -> None:
        await self._frame._actions.focus(self._resolver(), timeout=timeout)

    async def blur(self, timeout: float | None = None) -> None:
        await self._frame._actions.blur(self._resolver(), timeout=timeout)

    async def check(self, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), True, **kwargs)

    async def uncheck(self, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), False, **kwargs)

    async def set_checked(self, checked: bool, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), checked, **kwargs)

    async def select_option(
        self,
        value: str | Sequence[str] | None = None,
        *,
        index: int | Sequence[int] | None = None,
        label: str | Sequence[str] | None = None,
        element: ElementHandle | Sequence[ElementHandle] | None = None,
        timeout: float | None = None,
        force: bool | None = None,
        no_wait_after: bool | None = None,
    ) -> list[str]:
        return await self._frame._actions.select_option(
            self._resolver(),
            value=value,
            index=index,
            label=label,
            element=element,
            timeout=timeout,
            force=force,
        )

    async def select_text(self, force: bool | None = None, timeout: float | None = None) -> None:
        await self._frame._actions.select_text(self._resolver(), force=force, timeout=timeout)

    async def set_input_files(
        self,
        files: str | Path | FilePayload | Sequence[str | Path] | Sequence[FilePayload],
        timeout: float | None = None,
        no_wait_after: bool | None = None,
    ) -> None:
        await self._frame._actions.set_input_files(self._resolver(), files, timeout=timeout)

    async def dispatch_event(
        self,
        type: str,
        event_init: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> None:
        await self._frame._actions.dispatch_event(
            self._resolver(), type, event_init, timeout=timeout
        )

    async def scroll_into_view_if_needed(self, timeout: float | None = None) -> None:
        await self._frame._actions.scroll_into_view(self._resolver(), timeout=timeout)

    async def drag_to(self, target: Locator, **kwargs: Any) -> None:
        await self._frame._actions.drag_to(self._resolver(), target._resolver(), **kwargs)

    async def highlight(self) -> None:
        return None

    async def hide_highlight(self) -> None:
        return None

    # ---------------------------------------------------------- readers

    async def get_attribute(self, name: str, timeout: float | None = None) -> str | None:
        return await self._frame._actions.get_attribute(self._resolver(), name, timeout=timeout)

    async def text_content(self, timeout: float | None = None) -> str | None:
        return await self._frame._actions.text_content(self._resolver(), timeout=timeout)

    async def inner_text(self, timeout: float | None = None) -> str:
        return await self._frame._actions.inner_text(self._resolver(), timeout=timeout)

    async def inner_html(self, timeout: float | None = None) -> str:
        return await self._frame._actions.inner_html(self._resolver(), timeout=timeout)

    async def input_value(self, timeout: float | None = None) -> str:
        return await self._frame._actions.input_value(self._resolver(), timeout=timeout)

    async def is_checked(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(
            self._resolver(), 'checked', timeout=timeout
        )

    async def is_disabled(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(
            self._resolver(), 'disabled', timeout=timeout
        )

    async def is_editable(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(
            self._resolver(), 'editable', timeout=timeout
        )

    async def is_enabled(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(
            self._resolver(), 'enabled', timeout=timeout
        )

    async def is_hidden(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'hidden', timeout=timeout)

    async def is_visible(self, timeout: float | None = None) -> bool:
        return await self._frame._actions.element_state(
            self._resolver(), 'visible', timeout=timeout
        )

    async def bounding_box(self, timeout: float | None = None) -> dict[str, float] | None:
        return await self._frame._actions.bounding_box(self._resolver(), timeout=timeout)

    async def screenshot(self, **kwargs: Any) -> bytes:
        return await self._frame._actions.screenshot(self._resolver(), **kwargs)


class FrameLocator:
    """Entry point to a child frame found by a selector, with the same lazy semantics."""

    def __init__(self, frame: Frame, frame_selector: str) -> None:
        self._frame = frame
        self._frame_selector = frame_selector

    def __repr__(self) -> str:
        return f'<FrameLocator frame={self._frame!r} selector={self._frame_selector!r}>'

    def _child_selector(self, selector: str) -> str:
        return f'{self._frame_selector} >> {ENTER_FRAME} >> {selector}'

    def locator(
        self,
        selector_or_locator: str | Locator,
        has_text: TextMatch | None = None,
        has_not_text: TextMatch | None = None,
        has: Locator | None = None,
        has_not: Locator | None = None,
    ) -> Locator:
        if isinstance(selector_or_locator, Locator):
            selector = f'internal:chain={json.dumps(selector_or_locator._selector)}'
        else:
            selector = selector_or_locator
        return Locator(
            self._frame,
            self._child_selector(selector),
            has_text=has_text,
            has_not_text=has_not_text,
            has=has,
            has_not=has_not,
        )

    def get_by_alt_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_alt_text_selector(text, exact=exact))

    def get_by_label(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_label_selector(text, exact=exact))

    def get_by_placeholder(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_placeholder_selector(text, exact=exact))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return self.locator(get_by_role_selector(role, **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return self.locator(get_by_test_id_selector(test_id))

    def get_by_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_text_selector(text, exact=exact))

    def get_by_title(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_title_selector(text, exact=exact))

    def frame_locator(self, selector: str) -> FrameLocator:
        return FrameLocator(self._frame, self._child_selector(selector))

    @property
    def first(self) -> FrameLocator:
        return FrameLocator(self._frame, f'{self._frame_selector} >> nth=0')

    @property
    def last(self) -> FrameLocator:
        return FrameLocator(self._frame, f'{self._frame_selector} >> nth=-1')

    def nth(self, index: int) -> FrameLocator:
        return FrameLocator(self._frame, f'{self._frame_selector} >> nth={index}')

    @property
    def owner(self) -> Locator:
        return Locator(self._frame, self._frame_selector)


__all__ = ['FilePayload', 'FrameLocator', 'Locator', 'Pattern', 'Position', 'SelectOption']
