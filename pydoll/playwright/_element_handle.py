"""JSHandle and ElementHandle: references to page objects and DOM elements."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from pydoll.commands import RuntimeCommands
from pydoll.elements.web_element import WebElement
from pydoll.playwright._errors import Error
from pydoll.playwright._serialization import parse_remote_value

if TYPE_CHECKING:
    from pydoll.playwright._frame import Frame
    from pydoll.playwright._locator import FilePayload
    from pydoll.playwright._page import Page


class JSHandle:
    """A reference to a JavaScript object living in a frame."""

    def __init__(self, frame: Frame, object_id: str, preview: str = 'JSHandle') -> None:
        self._frame = frame
        self._object_id = object_id
        self._preview = preview

    def __repr__(self) -> str:
        return f'<JSHandle preview={self._preview}>'

    @property
    def object_id(self) -> str:
        return self._object_id

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return await self._frame._evaluate(
            expression, arg, this_object_id=self._object_id, by_value=True
        )

    async def evaluate_handle(self, expression: str, arg: Any = None) -> JSHandle:
        return await self._frame._evaluate(
            expression, arg, this_object_id=self._object_id, by_value=False
        )

    async def get_property(self, property_name: str) -> JSHandle:
        return await self._frame._evaluate(
            '(object, name) => object[name]',
            property_name,
            this_object_id=self._object_id,
            by_value=False,
        )

    async def get_properties(self) -> dict[str, JSHandle]:
        response = await self._frame._send(
            RuntimeCommands.get_properties(object_id=self._object_id, own_properties=True)
        )
        result: dict[str, JSHandle] = {}
        for entry in response.get('result', {}).get('result', []):
            value = entry.get('value')
            if not entry.get('enumerable') or value is None:
                continue
            result[entry['name']] = self._frame._handle_from_remote_object(value)
        return result

    def as_element(self) -> ElementHandle | None:
        return None

    async def dispose(self) -> None:
        await self._frame._send(RuntimeCommands.release_object(self._object_id))

    async def json_value(self) -> Any:
        response = await self._frame._send(
            RuntimeCommands.call_function_on(
                function_declaration='function() { return this; }',
                object_id=self._object_id,
                return_by_value=True,
            )
        )
        return parse_remote_value(response['result']['result'])


class PrimitiveHandle(JSHandle):
    """A JSHandle over a value that came back by value (string, number, boolean, null)."""

    def __init__(self, frame: Frame, value: Any) -> None:
        super().__init__(frame, '', repr(value))
        self._value = value

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return await self._frame._evaluate(
            f'([value, arg]) => ({expression})(value, arg)', [self._value, arg], by_value=True
        )

    async def evaluate_handle(self, expression: str, arg: Any = None) -> JSHandle:
        return await self._frame._evaluate(
            f'([value, arg]) => ({expression})(value, arg)', [self._value, arg], by_value=False
        )

    async def get_property(self, property_name: str) -> JSHandle:
        return PrimitiveHandle(self._frame, None)

    async def get_properties(self) -> dict[str, JSHandle]:
        return {}

    async def dispose(self) -> None:
        return None

    async def json_value(self) -> Any:
        return self._value


class ElementHandle(JSHandle):
    """A reference to a DOM element, wrapping a pydoll WebElement."""

    def __init__(self, frame: Frame, element: WebElement) -> None:
        super().__init__(frame, '', 'ElementHandle')
        self._element = element

    def __repr__(self) -> str:
        return f'<ElementHandle tag={self._element.tag_name}>'

    @property
    def web_element(self) -> WebElement:
        """The underlying pydoll element, for code that mixes both APIs."""
        return self._element

    @property
    def object_id(self) -> str:
        if not self._object_id:
            raise RuntimeError(
                'ElementHandle object id is resolved lazily; await _ensure_object_id() first'
            )
        return self._object_id

    async def _ensure_object_id(self) -> str:
        if not self._object_id:
            self._object_id = await self._frame._main_world_object_id(self._element)
        return self._object_id

    def as_element(self) -> ElementHandle | None:
        return self

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return await self._frame._evaluate_on_element(self._element, expression, arg, by_value=True)

    async def evaluate_handle(self, expression: str, arg: Any = None) -> JSHandle:
        return await self._frame._evaluate_on_element(
            self._element, expression, arg, by_value=False
        )

    async def json_value(self) -> Any:
        await self._ensure_object_id()
        return await super().json_value()

    async def dispose(self) -> None:
        if self._object_id:
            await super().dispose()

    @property
    def page(self) -> Page:
        return self._frame.page

    async def owner_frame(self) -> Frame | None:
        return self._frame

    async def content_frame(self) -> Frame | None:
        if not self._element.is_iframe:
            return None
        return await self._frame._child_frame(self._element)._canonical()

    async def get_attribute(self, name: str) -> str | None:
        return await self._frame._actions.get_attribute(self._resolver(), name)

    async def text_content(self) -> str | None:
        return await self._frame._actions.text_content(self._resolver())

    async def inner_text(self) -> str:
        return await self._frame._actions.inner_text(self._resolver())

    async def inner_html(self) -> str:
        return await self._frame._actions.inner_html(self._resolver())

    async def input_value(self, timeout: float | None = None) -> str:
        return await self._frame._actions.input_value(self._resolver(), timeout=timeout)

    async def is_checked(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'checked')

    async def is_disabled(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'disabled')

    async def is_editable(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'editable')

    async def is_enabled(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'enabled')

    async def is_hidden(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'hidden')

    async def is_visible(self) -> bool:
        return await self._frame._actions.element_state(self._resolver(), 'visible')

    async def dispatch_event(self, type: str, event_init: dict[str, Any] | None = None) -> None:
        await self._frame._actions.dispatch_event(self._resolver(), type, event_init)

    async def scroll_into_view_if_needed(self, timeout: float | None = None) -> None:
        await self._frame._actions.scroll_into_view(self._resolver(), timeout=timeout)

    async def hover(self, **kwargs: Any) -> None:
        await self._frame._actions.hover(self._resolver(), **kwargs)

    async def click(self, **kwargs: Any) -> None:
        await self._frame._actions.click(self._resolver(), **kwargs)

    async def dblclick(self, **kwargs: Any) -> None:
        await self._frame._actions.dblclick(self._resolver(), **kwargs)

    async def tap(self, **kwargs: Any) -> None:
        await self._frame._actions.tap(self._resolver(), **kwargs)

    async def select_option(
        self,
        value: str | Sequence[str] | None = None,
        *,
        index: int | Sequence[int] | None = None,
        label: str | Sequence[str] | None = None,
        element: ElementHandle | Sequence[ElementHandle] | None = None,
        timeout: float | None = None,
        force: bool | None = None,
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

    async def fill(
        self, value: str, timeout: float | None = None, force: bool | None = None
    ) -> None:
        await self._frame._actions.fill(self._resolver(), value, timeout=timeout, force=force)

    async def select_text(self, timeout: float | None = None, force: bool | None = None) -> None:
        await self._frame._actions.select_text(self._resolver(), timeout=timeout, force=force)

    async def set_input_files(
        self,
        files: str | Path | FilePayload | Sequence[str | Path] | Sequence[FilePayload],
        timeout: float | None = None,
    ) -> None:
        await self._frame._actions.set_input_files(self._resolver(), files, timeout=timeout)

    async def focus(self) -> None:
        await self._frame._actions.focus(self._resolver())

    async def type(
        self, text: str, delay: float | None = None, timeout: float | None = None
    ) -> None:
        await self._frame._actions.type(self._resolver(), text, delay=delay, timeout=timeout)

    async def press(
        self, key: str, delay: float | None = None, timeout: float | None = None
    ) -> None:
        await self._frame._actions.press(self._resolver(), key, delay=delay, timeout=timeout)

    async def set_checked(self, checked: bool, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), checked, **kwargs)

    async def check(self, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), True, **kwargs)

    async def uncheck(self, **kwargs: Any) -> None:
        await self._frame._actions.set_checked(self._resolver(), False, **kwargs)

    async def bounding_box(self) -> dict[str, float] | None:
        return await self._frame._actions.bounding_box(self._resolver())

    async def screenshot(self, **kwargs: Any) -> bytes:
        return await self._frame._actions.screenshot(self._resolver(), **kwargs)

    async def query_selector(self, selector: str) -> ElementHandle | None:
        element = await self._frame._query_one(selector, strict=False, root=self._element)
        return ElementHandle(self._frame, element) if element else None

    async def query_selector_all(self, selector: str) -> list[ElementHandle]:
        elements = await self._frame._query_all(selector, root=self._element)
        return [ElementHandle(self._frame, element) for element in elements]

    async def eval_on_selector(self, selector: str, expression: str, arg: Any = None) -> Any:
        handle = await self.query_selector(selector)
        if handle is None:
            raise Error(f'Failed to find element matching selector "{selector}"')
        return await handle.evaluate(expression, arg)

    async def eval_on_selector_all(self, selector: str, expression: str, arg: Any = None) -> Any:
        elements = await self._frame._query_all(selector, root=self._element)
        return await self._frame._evaluate_on_elements(elements, expression, arg)

    async def wait_for_element_state(self, state: str, timeout: float | None = None) -> None:
        await self._frame._actions.wait_for_element_state(self._resolver(), state, timeout=timeout)

    async def wait_for_selector(self, selector: str, **kwargs: Any) -> ElementHandle | None:
        return await self._frame.wait_for_selector(selector, root=self._element, **kwargs)

    def _resolver(self) -> Any:
        from pydoll.playwright._actions import fixed_resolver

        return fixed_resolver(self._element, describe(self._element))


def describe(element: WebElement) -> str:
    identity = element.get_attribute('id')
    return f'<{element.tag_name}#{identity}>' if identity else f'<{element.tag_name}>'
