"""Auto-waiting element actions shared by Locator, ElementHandle and Frame.

Every action follows Playwright's actionability protocol: resolve the element,
wait for the required states (visible, stable, enabled, editable), scroll it
into view, check that the point it will receive input at is not covered, then
act. Anything that fails is retried until the deadline expires.
"""

from __future__ import annotations

import asyncio
import base64
import mimetypes
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Sequence, Union

from pydoll.commands import InputCommands, PageCommands
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import PydollException
from pydoll.playwright._errors import Error, TimeoutError
from pydoll.playwright._events import Deadline
from pydoll.playwright._keys import modifier_bits
from pydoll.protocol.input.types import MouseButton, MouseEventType, TouchEventType
from pydoll.protocol.runtime.types import CallArgument

if TYPE_CHECKING:
    from pydoll.playwright._element_handle import ElementHandle
    from pydoll.playwright._frame import Frame
    from pydoll.playwright._locator import FilePayload

_BUTTONS = {'left': MouseButton.LEFT, 'right': MouseButton.RIGHT, 'middle': MouseButton.MIDDLE}
_RETRY_DELAYS_MS = (0, 20, 100, 100, 500)
_POLL_SECONDS = 0.1


@dataclass
class Resolver:
    """Where an action finds its element and how it is described in errors."""

    find: Callable[[], Awaitable[Optional[WebElement]]]
    description: str


def fixed_resolver(element: WebElement, description: str) -> Resolver:
    async def find() -> Optional[WebElement]:
        return element

    return Resolver(find, description)


class Retry(Exception):
    """Internal: the current attempt failed for a transient reason; try again."""


@dataclass
class _Point:
    hit_x: float
    hit_y: float
    input_x: float
    input_y: float


class Actions:
    """Element operations bound to one frame."""

    def __init__(self, frame: Frame) -> None:
        self._frame = frame

    # ------------------------------------------------------------ helpers

    def _deadline(self, timeout: Optional[float]) -> Deadline:
        return Deadline(self._frame.page._timeout(timeout))

    async def _wait(self, deadline: Deadline, log: list[str], resolver: Resolver) -> None:
        if deadline.expired():
            raise deadline.error(f'waiting for {resolver.description}', log)
        await asyncio.sleep(_POLL_SECONDS)

    async def _resolve(self, resolver: Resolver, deadline: Deadline, log: list[str]) -> WebElement:
        while True:
            element = await resolver.find()
            if element is not None:
                return element
            if not log or log[-1] != 'waiting for element to be attached':
                log.append('waiting for element to be attached')
            await self._wait(deadline, log, resolver)

    async def _engine(
        self, element: WebElement, body: str, args: list[Any], await_promise: bool = False
    ) -> Any:
        return await self._frame._engine_on_element(
            element, body, args, await_promise=await_promise
        )

    async def _check_states(self, element: WebElement, states: list[str], log: list[str]) -> bool:
        result = await self._engine(element, 'return engine.checkStates(this, a0);', [states], True)
        if result == 'error:notconnected':
            log.append('element was detached from the DOM, retrying')
            raise Retry()
        if result:
            missing = result['missingState']
            entry = f'element is not {missing}'
            if not log or log[-1] != entry:
                log.append(entry)
            return False
        return True

    async def _retry(
        self,
        resolver: Resolver,
        deadline: Deadline,
        attempt: Callable[[WebElement, list[str]], Awaitable[Any]],
        action_name: str,
    ) -> Any:
        log: list[str] = [f'waiting for {resolver.description}']
        retries = 0
        while True:
            element = await self._resolve(resolver, deadline, log)
            try:
                return await attempt(element, log)
            except Retry:
                pass
            except Error as error:
                if not _is_stale(error):
                    raise
                log.append('element context was destroyed, retrying')
            delay = _RETRY_DELAYS_MS[min(retries, len(_RETRY_DELAYS_MS) - 1)] / 1000
            retries += 1
            if retries > 1:
                log.append(f'retrying {action_name} action')
            if deadline.expired():
                raise deadline.error(f'waiting for {resolver.description}', log)
            await asyncio.sleep(max(delay, _POLL_SECONDS if retries > 3 else delay))  # noqa: PLR2004

    async def _scroll_into_view(self, element: WebElement, log: list[str]) -> None:
        result = await self._engine(element, 'return engine.scrollWhenNeeded(this);', [], True)
        if result == 'error:notconnected':
            raise Retry()
        if isinstance(result, dict):
            log.append(f'element is not {result["missingState"]}')
            raise Retry()

    async def _absolute(
        self, element: WebElement, offset_x: float, offset_y: float, x: float, y: float
    ) -> _Point:
        """Input coordinates for a prepared point: frame-local unless inside a child frame."""
        if self._frame._owner(element).parent_frame is None:
            return _Point(hit_x=x, hit_y=y, input_x=x, input_y=y)
        try:
            quad = await element.bounds()
            box_x = min(quad[0], quad[2], quad[4], quad[6])
            box_y = min(quad[1], quad[3], quad[5], quad[7])
        except PydollException:
            return _Point(hit_x=x, hit_y=y, input_x=x, input_y=y)
        return _Point(hit_x=x, hit_y=y, input_x=box_x + offset_x, input_y=box_y + offset_y)

    async def _pointer_action(
        self,
        resolver: Resolver,
        action_name: str,
        wait_for_enabled: bool,
        perform: Callable[[WebElement, _Point], Awaitable[None]],
        *,
        timeout: Optional[float],
        force: Optional[bool],
        position: Optional[dict[str, float]],
        trial: Optional[bool],
        modifiers: Optional[Sequence[str]],
    ) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            states = ['visible', 'enabled', 'stable'] if wait_for_enabled else ['visible', 'stable']
            prepared = await self._engine(
                element,
                'return engine.prepareForAction(this, a0);',
                [{'states': states, 'position': position, 'force': bool(force), 'scroll': 'auto'}],
                True,
            )
            status = prepared.get('status') if isinstance(prepared, dict) else None
            if status == 'notconnected':
                log.append('element was detached from the DOM, retrying')
                raise Retry()
            if status == 'missing':
                entry = f'element is not {prepared["state"]}'
                if not log or log[-1] != entry:
                    log.append(entry)
                raise Retry()
            if status == 'notinviewport':
                log.append('element is outside of the viewport')
                raise Retry()
            if status == 'intercepted':
                entry = (
                    f'{prepared.get("description", "another element")} intercepts pointer events'
                )
                if not log or log[-1] != entry:
                    log.append(entry)
                raise Retry()
            if status != 'done':
                raise Error(f'Unexpected action preparation result: {prepared!r}')
            point = await self._absolute(
                element, prepared['offsetX'], prepared['offsetY'], prepared['x'], prepared['y']
            )
            if trial:
                return
            keyboard = self._frame.page.keyboard
            restore = await keyboard._ensure_modifiers(list(modifiers or []))
            try:
                await perform(element, point)
            finally:
                await keyboard._ensure_modifiers(restore)

        await self._retry(resolver, deadline, attempt, action_name)

    async def _mouse(
        self,
        element: WebElement,
        event_type: MouseEventType,
        point: _Point,
        button: MouseButton = MouseButton.NONE,
        click_count: int = 0,
        modifiers: Optional[Sequence[str]] = None,
    ) -> None:
        await self._frame._send_for_element(
            element,
            InputCommands.dispatch_mouse_event(
                type=event_type,
                x=int(round(point.input_x)),
                y=int(round(point.input_y)),
                button=button,
                click_count=click_count or None,
                modifiers=modifier_bits(list(modifiers or [])),
                force=0.5 if button not in {MouseButton.NONE, None} else None,
            ),
        )

    # ------------------------------------------------------------ pointer

    async def click(
        self,
        resolver: Resolver,
        *,
        modifiers: Optional[Sequence[str]] = None,
        position: Optional[dict[str, float]] = None,
        delay: Optional[float] = None,
        button: str = 'left',
        click_count: Optional[int] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        trial: Optional[bool] = None,
    ) -> None:
        count = click_count or 1
        mouse_button = _BUTTONS[button]

        async def perform(element: WebElement, point: _Point) -> None:
            await self._mouse(element, MouseEventType.MOUSE_MOVED, point, modifiers=modifiers)
            for index in range(1, count + 1):
                await self._mouse(
                    element, MouseEventType.MOUSE_PRESSED, point, mouse_button, index, modifiers
                )
                await asyncio.sleep(_hold_seconds(delay))
                await self._mouse(
                    element, MouseEventType.MOUSE_RELEASED, point, mouse_button, index, modifiers
                )

        await self._pointer_action(
            resolver,
            'click',
            True,
            perform,
            timeout=timeout,
            force=force,
            position=position,
            trial=trial,
            modifiers=modifiers,
        )

    async def dblclick(self, resolver: Resolver, **kwargs: Any) -> None:
        await self.click(resolver, click_count=2, **kwargs)

    async def hover(
        self,
        resolver: Resolver,
        *,
        modifiers: Optional[Sequence[str]] = None,
        position: Optional[dict[str, float]] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        trial: Optional[bool] = None,
    ) -> None:
        async def perform(element: WebElement, point: _Point) -> None:
            await self._mouse(element, MouseEventType.MOUSE_MOVED, point, modifiers=modifiers)

        await self._pointer_action(
            resolver,
            'hover',
            False,
            perform,
            timeout=timeout,
            force=force,
            position=position,
            trial=trial,
            modifiers=modifiers,
        )

    async def tap(
        self,
        resolver: Resolver,
        *,
        modifiers: Optional[Sequence[str]] = None,
        position: Optional[dict[str, float]] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        trial: Optional[bool] = None,
    ) -> None:
        async def perform(element: WebElement, point: _Point) -> None:
            bits = modifier_bits(list(modifiers or []))
            await self._frame._send_for_element(
                element,
                InputCommands.dispatch_touch_event(
                    type=TouchEventType.TOUCH_START,
                    touch_points=[{'x': point.input_x, 'y': point.input_y}],
                    modifiers=bits,
                ),
            )
            await self._frame._send_for_element(
                element,
                InputCommands.dispatch_touch_event(
                    type=TouchEventType.TOUCH_END, touch_points=[], modifiers=bits
                ),
            )

        await self._pointer_action(
            resolver,
            'tap',
            True,
            perform,
            timeout=timeout,
            force=force,
            position=position,
            trial=trial,
            modifiers=modifiers,
        )

    async def drag_to(
        self,
        source: Resolver,
        target: Resolver,
        *,
        source_position: Optional[dict[str, float]] = None,
        target_position: Optional[dict[str, float]] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        trial: Optional[bool] = None,
    ) -> None:
        async def press(element: WebElement, point: _Point) -> None:
            await self._mouse(element, MouseEventType.MOUSE_MOVED, point)
            await self._mouse(element, MouseEventType.MOUSE_PRESSED, point, MouseButton.LEFT, 1)

        async def release(element: WebElement, point: _Point) -> None:
            await self._mouse(element, MouseEventType.MOUSE_MOVED, point, MouseButton.LEFT)
            await self._mouse(element, MouseEventType.MOUSE_RELEASED, point, MouseButton.LEFT, 1)

        await self._pointer_action(
            source,
            'move and down',
            False,
            press,
            timeout=timeout,
            force=force,
            position=source_position,
            trial=trial,
            modifiers=None,
        )
        await self._pointer_action(
            target,
            'move and up',
            False,
            release,
            timeout=timeout,
            force=force,
            position=target_position,
            trial=trial,
            modifiers=None,
        )

    # ------------------------------------------------------------ keyboard

    async def fill(
        self,
        resolver: Resolver,
        value: str,
        *,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
    ) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            result = await self._engine(
                element, 'return engine.fillChecked(this, a0, a1);', [value, bool(force)], True
            )
            if result == 'error:notconnected':
                raise Retry()
            if isinstance(result, dict):
                entry = f'element is not {result["missingState"]}'
                if not log or log[-1] != entry:
                    log.append(entry)
                raise Retry()
            if result == 'needsinput':
                if value:
                    await self._frame._send_for_element(element, InputCommands.insert_text(value))
                else:
                    await self._frame.page.keyboard.press('Delete')

        await self._retry(resolver, deadline, attempt, 'fill')

    async def clear(self, resolver: Resolver, **kwargs: Any) -> None:
        await self.fill(resolver, '', **kwargs)

    async def select_text(
        self, resolver: Resolver, *, timeout: Optional[float] = None, force: Optional[bool] = None
    ) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            if not force and not await self._check_states(element, ['visible'], log):
                raise Retry()
            if (
                await self._engine(element, 'return engine.selectContents(this);', [])
                == 'error:notconnected'
            ):
                raise Retry()

        await self._retry(resolver, deadline, attempt, 'selectText')

    async def focus(self, resolver: Resolver, timeout: Optional[float] = None) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            if (
                await self._engine(element, 'return engine.focusElement(this, true);', [])
                == 'error:notconnected'
            ):
                raise Retry()

        await self._retry(resolver, deadline, attempt, 'focus')

    async def blur(self, resolver: Resolver, timeout: Optional[float] = None) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            await self._frame._call_on_element(element, 'function() { this.blur(); }', [])

        await self._retry(resolver, deadline, attempt, 'blur')

    async def type(
        self,
        resolver: Resolver,
        text: str,
        *,
        delay: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        await self.focus(resolver, timeout=timeout)
        await self._frame.page.keyboard.type(text, delay=delay)

    async def press(
        self,
        resolver: Resolver,
        key: str,
        *,
        delay: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        await self.focus(resolver, timeout=timeout)
        await self._frame.page.keyboard.press(key, delay=delay)

    async def select_option(
        self,
        resolver: Resolver,
        *,
        value: Union[str, Sequence[str], None] = None,
        index: Union[int, Sequence[int], None] = None,
        label: Union[str, Sequence[str], None] = None,
        element: Union[ElementHandle, Sequence[ElementHandle], None] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
    ) -> list[str]:
        options: list[dict[str, Any]] = []
        for item in _listify(value):
            options.append({'valueOrLabel': item})
        for item in _listify(index):
            options.append({'index': item})
        for item in _listify(label):
            options.append({'label': item})
        handles = _listify(element)
        deadline = self._deadline(timeout)

        async def attempt(target: WebElement, log: list[str]) -> list[str]:
            body = (
                'return engine.selectChecked('
                'this, a0.concat(Array.prototype.slice.call(arguments, 3)), a1);'
            )
            extra_arguments: list[CallArgument] = [
                {'objectId': await handle._ensure_object_id()} for handle in handles
            ]
            result = await self._frame._engine_on_element(
                target,
                body,
                [options, bool(force)],
                await_promise=True,
                extra_arguments=extra_arguments,
            )
            if result == 'error:notconnected':
                raise Retry()
            if isinstance(result, dict):
                entry = f'element is not {result["missingState"]}'
                if not log or log[-1] != entry:
                    log.append(entry)
                raise Retry()
            if result == 'error:optionsnotfound':
                if not log or log[-1] != 'did not find some options':
                    log.append('did not find some options')
                raise Retry()
            if result == 'error:optionnotenabled':
                log.append('option being selected is not enabled')
                raise Retry()
            return list(result)

        return await self._retry(resolver, deadline, attempt, 'selectOption')

    async def set_checked(
        self,
        resolver: Resolver,
        checked: bool,
        *,
        position: Optional[dict[str, float]] = None,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        trial: Optional[bool] = None,
    ) -> None:
        deadline = self._deadline(timeout)
        element = await self._resolve(resolver, deadline, [])
        state = await self._engine(element, 'return engine.elementState(this, "checked");', [])
        if state.get('received') == 'error:notconnected':
            raise Error('Element is not attached to the DOM')
        if state['matches'] == checked:
            return
        await self.click(resolver, position=position, timeout=timeout, force=force, trial=trial)
        if trial:
            return
        element = await self._resolve(resolver, deadline, [])
        state = await self._engine(element, 'return engine.elementState(this, "checked");', [])
        if state['matches'] != checked:
            raise Error('Clicking the checkbox did not change its state')

    async def set_input_files(
        self,
        resolver: Resolver,
        files: Union[str, Path, FilePayload, Sequence[Union[str, Path]], Sequence[FilePayload]],
        *,
        timeout: Optional[float] = None,
    ) -> None:
        deadline = self._deadline(timeout)
        items = list(files) if isinstance(files, (list, tuple)) else [files]

        async def attempt(element: WebElement, log: list[str]) -> None:
            if any(isinstance(item, dict) for item in items):
                payloads = []
                for item in items:
                    if isinstance(item, dict):
                        buffer = item['buffer']
                        payloads.append({
                            'name': item['name'],
                            'mimeType': item.get('mimeType') or 'application/octet-stream',
                            'buffer': base64.b64encode(buffer).decode()
                            if isinstance(buffer, bytes)
                            else buffer,
                        })
                        continue
                    path = Path(str(item)).resolve()
                    if not path.exists():
                        raise Error(f'File not found: {path}')
                    payloads.append({
                        'name': path.name,
                        'mimeType': guess_mime(path),
                        'buffer': base64.b64encode(path.read_bytes()).decode(),
                    })
                await self._frame._call_on_element(
                    element, _SET_FILES_FROM_PAYLOADS, [{'value': payloads}]
                )
                return
            paths: list[Union[str, Path]] = []
            for item in items:
                path = Path(str(item)).resolve()
                if not path.exists():
                    raise Error(f'File not found: {path}')
                paths.append(str(path))
            await element.set_input_files(paths)

        await self._retry(resolver, deadline, attempt, 'setInputFiles')

    async def dispatch_event(
        self,
        resolver: Resolver,
        type: str,
        event_init: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            await self._engine(
                element, 'engine.dispatchEvent(this, a0, a1);', [type, event_init or {}]
            )

        await self._retry(resolver, deadline, attempt, 'dispatchEvent')

    async def scroll_into_view(self, resolver: Resolver, timeout: Optional[float] = None) -> None:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> None:
            await self._scroll_into_view(element, log)

        await self._retry(resolver, deadline, attempt, 'scrollIntoViewIfNeeded')

    # ------------------------------------------------------------ readers

    async def _read(
        self, resolver: Resolver, timeout: Optional[float], body: str, args: list[Any]
    ) -> Any:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> Any:
            return await self._frame._call_on_element(
                element, body, [{'value': arg} for arg in args]
            )

        return await self._retry(resolver, deadline, attempt, 'read')

    async def get_attribute(
        self, resolver: Resolver, name: str, timeout: Optional[float] = None
    ) -> Optional[str]:
        return await self._read(
            resolver, timeout, 'function(name) { return this.getAttribute(name); }', [name]
        )

    async def text_content(
        self, resolver: Resolver, timeout: Optional[float] = None
    ) -> Optional[str]:
        return await self._read(resolver, timeout, 'function() { return this.textContent; }', [])

    async def inner_text(self, resolver: Resolver, timeout: Optional[float] = None) -> str:
        return await self._read(
            resolver,
            timeout,
            'function() {'
            ' if (this.namespaceURI === "http://www.w3.org/2000/svg")'
            '   throw new Error("Node is not an HTMLElement");'
            ' return this.innerText; }',
            [],
        )

    async def inner_html(self, resolver: Resolver, timeout: Optional[float] = None) -> str:
        return await self._read(resolver, timeout, 'function() { return this.innerHTML; }', [])

    async def input_value(self, resolver: Resolver, timeout: Optional[float] = None) -> str:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> str:
            return await self._engine(element, 'return engine.inputValue(this);', [])

        return await self._retry(resolver, deadline, attempt, 'inputValue')

    async def element_state(
        self, resolver: Resolver, state: str, timeout: Optional[float] = None
    ) -> bool:
        element = await resolver.find()
        if element is None:
            if state == 'hidden':
                return True
            if state == 'visible':
                return False
            deadline = self._deadline(timeout)
            element = await self._resolve(resolver, deadline, [])
        result = await self._engine(element, 'return engine.elementState(this, a0);', [state])
        if result.get('received') == 'error:notconnected':
            return state == 'hidden'
        return bool(result['matches'])

    async def wait_for_element_state(
        self, resolver: Resolver, state: str, timeout: Optional[float] = None
    ) -> None:
        deadline = self._deadline(timeout)
        if state == 'stable':
            states = ['stable']
        elif state in {'visible', 'hidden', 'enabled', 'disabled', 'editable'}:
            states = [state]
        else:
            raise Error(f'Unsupported element state: {state}')

        async def attempt(element: WebElement, log: list[str]) -> None:
            if not await self._check_states(element, states, log):
                raise Retry()

        await self._retry(resolver, deadline, attempt, 'waitForElementState')

    async def bounding_box(
        self, resolver: Resolver, timeout: Optional[float] = None
    ) -> Optional[dict[str, float]]:
        element = await resolver.find()
        if element is None:
            deadline = self._deadline(timeout)
            element = await self._resolve(resolver, deadline, [])
        try:
            quad = await element.bounds()
        except PydollException:
            return None
        xs = quad[0::2]
        ys = quad[1::2]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        if width == 0 and height == 0:
            return None
        return {'x': min(xs), 'y': min(ys), 'width': width, 'height': height}

    async def screenshot(
        self,
        resolver: Resolver,
        *,
        timeout: Optional[float] = None,
        type: str = 'png',
        path: Optional[Union[str, Path]] = None,
        quality: Optional[int] = None,
        omit_background: Optional[bool] = None,
        **_: Any,
    ) -> bytes:
        deadline = self._deadline(timeout)

        async def attempt(element: WebElement, log: list[str]) -> bytes:
            if not await self._check_states(element, ['visible', 'stable'], log):
                raise Retry()
            await self._scroll_into_view(element, log)
            geometry = await self._engine(element, 'return engine.documentRect(this);', [])
            if geometry['width'] == 0 or geometry['height'] == 0:
                raise Error('Element has no size')
            return await self._frame.page._capture_screenshot(
                type=type,
                quality=quality,
                clip={
                    'x': geometry['x'],
                    'y': geometry['y'],
                    'width': geometry['width'],
                    'height': geometry['height'],
                    'scale': 1,
                },
                omit_background=omit_background,
                path=path,
                capture_beyond_viewport=True,
            )

        return await self._retry(resolver, deadline, attempt, 'screenshot')


_SET_FILES_FROM_PAYLOADS = """
function(payloads) {
  if (this.nodeName !== 'INPUT' || (this.getAttribute('type') || '').toLowerCase() !== 'file')
    throw new Error('Node is not an input[type=file] element');
  const dt = new DataTransfer();
  for (const file of payloads) {
    const bytes = Uint8Array.from(atob(file.buffer), c => c.charCodeAt(0));
    dt.items.add(new File([bytes], file.name, { type: file.mimeType }));
  }
  this.files = dt.files;
  this.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
  this.dispatchEvent(new Event('change', { bubbles: true }));
}
"""


def _hold_seconds(delay: Optional[float]) -> float:
    """Button hold time: the caller's ``delay`` in ms, else a human-like 40-110 ms."""
    if delay:
        return delay / 1000
    return random.uniform(0.04, 0.11)


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _is_stale(error: Error) -> bool:
    text = str(error)
    return (
        'Cannot find context with specified id' in text
        or 'Execution context was destroyed' in text
        or 'Could not find object with given id' in text
        or 'Node with given id does not belong to the document' in text
    )


def guess_mime(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or 'application/octet-stream'


__all__ = [
    'Actions',
    'Resolver',
    'Retry',
    'TimeoutError',
    'PageCommands',
    'fixed_resolver',
    'guess_mime',
]
