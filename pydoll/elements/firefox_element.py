from __future__ import annotations

import asyncio
import base64
import logging
from typing import TYPE_CHECKING, Any, Optional

import aiofiles

from pydoll.elements.firefox_shadow_root import FirefoxShadowRoot
from pydoll.elements.mixins.firefox_find_mixin import FirefoxFindMixin
from pydoll.exceptions import ElementNotInteractable, WaitElementTimeout
from pydoll.protocol.bidi import browsing_context, script
from pydoll.protocol.bidi import input as bidi_input

if TYPE_CHECKING:
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler

logger = logging.getLogger(__name__)

_ELEMENT_VISIBLE = """
(el) => {
    const rect = el.getBoundingClientRect();
    return (
        rect.width > 0 && rect.height > 0
        && getComputedStyle(el).visibility !== 'hidden'
        && getComputedStyle(el).display !== 'none'
    );
}
"""

_ELEMENT_INTERACTABLE = """
(el) => {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (
        rect.width <= 0 || rect.height <= 0 ||
        style.visibility === 'hidden' ||
        style.display === 'none' ||
        style.pointerEvents === 'none'
    ) { return false; }
    const x = rect.x + rect.width / 2;
    const y = rect.y + rect.height / 2;
    const elementFromPoint = document.elementFromPoint(x, y);
    if (!elementFromPoint || (elementFromPoint !== el && !el.contains(elementFromPoint))) {
        return false;
    }
    if (el.disabled) { return false; }
    return true;
}
"""

_IS_EDITABLE = """
(el) => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        return !el.disabled && !el.readOnly;
    }
    let current = el;
    while (current) {
        if (current.isContentEditable) { return true; }
        current = current.parentElement;
    }
    return false;
}
"""

_CLEAR_INPUT = """
(el) => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.value = '';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }
    if (el.isContentEditable) {
        el.focus();
        el.innerHTML = '';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        return true;
    }
    return false;
}
"""

KEYS = {
    'ctrl': '\ue009',
    'shift': '\ue008',
    'alt': '\ue00a',
    'enter': '\ue006',
    'return': '\ue006',
    'backspace': '\ue003',
    'delete': '\ue017',
    'escape': '\ue00c',
    'esc': '\ue00c',
    'tab': '\ue004',
    'space': ' ',
    'up': '\ue013',
    'down': '\ue015',
    'left': '\ue012',
    'right': '\ue014',
    'home': '\ue011',
    'end': '\ue010',
    'pageup': '\ue00e',
    'pagedown': '\ue00f',
}


class FirefoxElement(FirefoxFindMixin):
    """
    Represents a DOM element in a Firefox tab via WebDriver BiDi.

    Wraps a node reference returned by browsingContext.locateNodes and
    provides interaction methods (click, type, hover, etc.) using
    input.performActions with element origins.
    """

    def __init__(
        self,
        node: dict,
        context_id: str,
        connection_handler: BiDiConnectionHandler,
    ):
        """
        Initialize a FirefoxElement.

        Args:
            node: Raw node dict from browsingContext.locateNodes (must have 'sharedId').
            context_id: BiDi browsing context ID of the parent tab.
            connection_handler: Shared BiDi connection handler.
        """
        self._node = node
        self._context_id = context_id
        self._connection_handler = connection_handler
        self._shared_id: str = node.get('sharedId', '')
        logger.debug(f'FirefoxElement initialized: sharedId={self._shared_id}')

    @property
    def _find_start_nodes(self) -> list[dict]:
        """Scope ``find()`` / ``query()`` to within this element."""
        return [{'type': 'node', 'sharedId': self._shared_id}]

    @property
    def shared_id(self) -> str:
        """BiDi shared reference ID for this element."""
        return self._shared_id

    @property
    def node(self) -> dict:
        """Raw node dict returned by locateNodes."""
        return self._node

    async def click(self) -> None:
        """Click the center of the element."""
        logger.debug(f'Clicking element: sharedId={self._shared_id}')
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'pointer',
                        'id': 'mouse1',
                        'parameters': {'pointerType': 'mouse'},
                        'actions': [
                            {
                                'type': 'pointerMove',
                                'x': 0,
                                'y': 0,
                                'origin': {
                                    'type': 'element',
                                    'element': {'sharedId': self._shared_id},
                                },
                            },
                            {'type': 'pointerDown', 'button': 0},
                            {'type': 'pointerUp', 'button': 0},
                        ],
                    }
                ],
            )
        )

    async def hover(self) -> None:
        """Move the mouse over the element without clicking."""
        logger.debug(f'Hovering over element: sharedId={self._shared_id}')
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'pointer',
                        'id': 'mouse1',
                        'parameters': {'pointerType': 'mouse'},
                        'actions': [
                            {
                                'type': 'pointerMove',
                                'x': 0,
                                'y': 0,
                                'origin': {
                                    'type': 'element',
                                    'element': {'sharedId': self._shared_id},
                                },
                            },
                        ],
                    }
                ],
            )
        )

    async def type_text(self, text: str, clear_first: bool = True) -> None:
        """
        Click the element to focus it, then type text character by character.

        Args:
            text: Text to type into the element.
            clear_first: Select all existing content and delete it before typing.
        """
        await self.click()

        key_actions: list[dict] = []

        if clear_first:
            key_actions.extend([
                {'type': 'keyDown', 'value': KEYS['ctrl']},
                {'type': 'keyDown', 'value': 'a'},
                {'type': 'keyUp', 'value': 'a'},
                {'type': 'keyUp', 'value': KEYS['ctrl']},
                {'type': 'keyDown', 'value': KEYS['delete']},
                {'type': 'keyUp', 'value': KEYS['delete']},
            ])

        for char in text:
            key_actions.extend([
                {'type': 'keyDown', 'value': char},
                {'type': 'keyUp', 'value': char},
            ])

        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [{'type': 'key', 'id': 'keyboard1', 'actions': key_actions}],
            )
        )
        logger.debug(f'Typed {len(text)} chars into element: sharedId={self._shared_id}')

    async def press_keyboard_key(self, key: str) -> None:
        """
        Press a single key while this element is focused.

        Args:
            key: Key name from KEYS dict (e.g. 'enter', 'tab', 'escape')
                 or a single character (e.g. 'a', '1').
        """
        value = KEYS.get(key.lower(), key)
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'key',
                        'id': 'keyboard1',
                        'actions': [
                            {'type': 'keyDown', 'value': value},
                            {'type': 'keyUp', 'value': value},
                        ],
                    }
                ],
            )
        )

    async def key_down(self, key: str, *modifiers: str) -> None:
        """
        Send a key-down event, optionally holding modifier keys first.

        The virtual keyboard state is maintained by the browser between calls,
        so keys remain logically held until :meth:`key_up` is called or
        ``input.releaseActions`` is issued.

        Args:
            key: Key name from the :data:`KEYS` dict (e.g. ``'enter'``,
                 ``'escape'``) or a single character (e.g. ``'a'``, ``'1'``).
            *modifiers: Zero or more modifier key names to hold before the
                main key (e.g. ``'ctrl'``, ``'shift'``, ``'alt'``).

        Example:
            await element.key_down('a', 'ctrl')   # Ctrl held, then A pressed
        """
        actions: list[dict] = []
        for mod in modifiers:
            actions.append({'type': 'keyDown', 'value': KEYS.get(mod.lower(), mod)})
        actions.append({'type': 'keyDown', 'value': KEYS.get(key.lower(), key)})

        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [{'type': 'key', 'id': 'keyboard1', 'actions': actions}],
            )
        )

    async def key_up(self, key: str, *modifiers: str) -> None:
        """
        Send a key-up event, releasing modifier keys afterwards.

        Modifiers are released in reverse order so the sequence is the
        mirror image of :meth:`key_down`.

        Args:
            key: Key name from the :data:`KEYS` dict or a single character.
            *modifiers: Modifier key names that were held when :meth:`key_down`
                was called (e.g. ``'ctrl'``, ``'shift'``).

        Example:
            await element.key_up('a', 'ctrl')   # A released, then Ctrl released
        """
        actions: list[dict] = [{'type': 'keyUp', 'value': KEYS.get(key.lower(), key)}]
        for mod in reversed(modifiers):
            actions.append({'type': 'keyUp', 'value': KEYS.get(mod.lower(), mod)})

        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [{'type': 'key', 'id': 'keyboard1', 'actions': actions}],
            )
        )

    async def hotkey(self, *keys: str) -> None:
        """
        Execute a key combination in a single atomic BiDi action sequence.

        All keys are pressed in order, then released in reverse, so the last
        key given is treated as the "main" key and the preceding ones as
        modifiers.

        Args:
            *keys: Two or more key names. The last one is the main key;
                   all others are held as modifiers.
                   E.g. ``hotkey('ctrl', 'a')`` → Ctrl+A.

        Raises:
            ValueError: If fewer than one key is provided.

        Example:
            await element.hotkey('ctrl', 'a')          # Select all
            await element.hotkey('ctrl', 'c')          # Copy
            await element.hotkey('ctrl', 'shift', 's') # Save-as style combo
        """
        if not keys:
            raise ValueError('hotkey requires at least one key')

        resolved = [KEYS.get(k.lower(), k) for k in keys]
        actions: list[dict] = [{'type': 'keyDown', 'value': v} for v in resolved]
        actions += [{'type': 'keyUp', 'value': v} for v in reversed(resolved)]

        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [{'type': 'key', 'id': 'keyboard1', 'actions': actions}],
            )
        )

    async def focus(self) -> None:
        """Focus this element."""
        logger.debug(f'Focusing element: sharedId={self._shared_id}')
        await self._call_function('(el) => el.focus()')

    async def scroll_into_view(self) -> None:
        """Scroll element into the visible viewport."""
        logger.debug(f'Scrolling element into view: sharedId={self._shared_id}')
        await self._call_function(
            '(el) => el.scrollIntoView({ behavior: "smooth", block: "center" })'
        )

    async def clear(self) -> None:
        """
        Clear the current value of the element.

        Supports standard inputs, textareas, and contenteditable elements.
        Dispatches ``input`` and ``change`` events so frameworks detect the update.

        Raises:
            ElementNotInteractable: If the element does not accept text input.
        """
        logger.debug(f'Clearing element: sharedId={self._shared_id}')
        success = await self._call_function(_CLEAR_INPUT)
        if not success:
            raise ElementNotInteractable('Element does not accept text input')

    async def is_visible(self) -> bool:
        """Check if the element is visible (has dimensions and is not hidden)."""
        result = await self._call_function(_ELEMENT_VISIBLE)
        return bool(result)

    async def is_interactable(self) -> bool:
        """Check if the element is interactable (visible, not covered, not disabled)."""
        result = await self._call_function(_ELEMENT_INTERACTABLE)
        return bool(result)

    async def is_editable(self) -> bool:
        """Check if the element can accept text input (input, textarea, or contenteditable)."""
        result = await self._call_function(_IS_EDITABLE)
        return bool(result)

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        timeout: int = 0,
    ) -> None:
        """
        Wait for the element to meet the specified conditions.

        Args:
            is_visible: Wait until the element is visible.
            is_interactable: Wait until the element is interactable.
            timeout: Maximum seconds to wait (0 = wait forever).

        Raises:
            ValueError: If neither ``is_visible`` nor ``is_interactable`` is True.
            WaitElementTimeout: If the condition is not met within ``timeout`` seconds.
        """
        checks_map = [
            (is_visible, self.is_visible),
            (is_interactable, self.is_interactable),
        ]
        checks = [func for flag, func in checks_map if flag]
        if not checks:
            raise ValueError('At least one of is_visible or is_interactable must be True')

        condition_parts = []
        if is_visible:
            condition_parts.append('visible')
        if is_interactable:
            condition_parts.append('interactable')
        condition_msg = ' and '.join(condition_parts)

        logger.info(
            f'Waiting for element: {condition_msg}, timeout={timeout}s, '
            f'sharedId={self._shared_id}'
        )
        loop = asyncio.get_event_loop()
        start_time = loop.time()
        while True:
            results = await asyncio.gather(*(check() for check in checks))
            if all(results):
                logger.info(f'Element condition satisfied: {condition_msg}')
                return

            if timeout and loop.time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out waiting for element to become {condition_msg}'
                )

            await asyncio.sleep(0.5)

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get the value of an HTML attribute (e.g. 'href', 'class')."""
        return await self._call_function(f'(el) => el.getAttribute("{name}")')

    async def get_property(self, name: str) -> Any:
        """Get the value of a DOM property (e.g. 'value', 'checked', 'disabled')."""
        return await self._call_function(f'(el) => el["{name}"]')

    @property
    async def text(self) -> str:
        """Visible text content of the element (innerText)."""
        return await self._call_function('(el) => el.innerText') or ''

    @property
    async def inner_html(self) -> str:
        """Inner HTML of the element."""
        return await self._call_function('(el) => el.innerHTML') or ''

    async def _call_function(self, function_declaration: str) -> Any:
        """Call a JS function with this element as the first argument."""
        response: dict = await self._connection_handler.execute_command(
            script.call_function(
                function_declaration=function_declaration,
                context=self._context_id,
                args=[{'sharedId': self._shared_id}],
            )
        )
        result = response.get('result', {})
        script_result = result.get('result', {})
        return script_result.get('value')

    async def set_input_files(self, files: list[str]) -> None:
        """
        Set files on a file input element directly, without opening a file dialog.

        This works in both headless and headed mode and does not require
        ``expect_file_chooser``.

        Args:
            files: List of absolute file paths to assign to the input.
        """
        await self._connection_handler.execute_command(
            bidi_input.set_files(self._context_id, self._shared_id, files)
        )

    async def take_screenshot(
        self,
        path: Optional[str] = None,
        as_base64: bool = False,
    ) -> Optional[bytes | str]:
        """
        Capture a screenshot clipped to this element's bounding box.

        Uses ``browsingContext.captureScreenshot`` with ``ElementClipRectangle``
        — no JavaScript involved.

        Args:
            path: If provided, save the screenshot to this file path.
            as_base64: If True, return the screenshot as a base64 string.

        Returns:
            PNG bytes, base64 string, or None (if path provided).
        """
        logger.debug(f'Taking element screenshot: sharedId={self._shared_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.capture_screenshot(self._context_id, shared_id=self._shared_id)
        )
        data: str = response.get('result', {}).get('data', '')
        if as_base64:
            return data
        png_bytes = base64.b64decode(data)
        if path is not None:
            async with aiofiles.open(path, 'wb') as f:
                await f.write(png_bytes)
            return None
        return png_bytes

    async def get_shadow_root(self) -> FirefoxShadowRoot:
        """
        Return the shadow root attached to this element.

        Raises:
            ValueError: If the element has no shadow root (``el.shadowRoot`` is ``null``).
        """
        response: dict = await self._connection_handler.execute_command(
            script.call_function(
                function_declaration='(el) => el.shadowRoot',
                context=self._context_id,
                args=[{'sharedId': self._shared_id}],
            )
        )
        result = response.get('result', {}).get('result', {})
        shared_id = result.get('sharedId', '')
        if not shared_id:
            raise ValueError(f'Element {self._shared_id!r} has no shadow root')
        return FirefoxShadowRoot(shared_id, self._context_id, self._connection_handler)

    def __repr__(self) -> str:
        return f'FirefoxElement(sharedId={self._shared_id!r})'
