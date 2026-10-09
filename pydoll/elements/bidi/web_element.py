from __future__ import annotations

import asyncio
import base64
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, cast

import aiofiles

from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.input_commands import InputCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.constants import By
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.exceptions import (
    CommandFailed,
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    InvalidFileExtension,
    InvalidIFrame,
    MissingScreenshotPath,
    ScriptEvaluationError,
    ShadowRootNotFound,
    WaitElementTimeout,
)
from pydoll.interactions.keyboard import BiDiKeyboard
from pydoll.protocol.bidi.browsing_context.types import ElementClipRectangle, ImageFormat
from pydoll.protocol.bidi.input.types import ElementOrigin, PointerType
from pydoll.protocol.bidi.script.types import ContextTarget, SharedReference
from pydoll.utils import PollInterval, is_script_already_function

if TYPE_CHECKING:
    from pydoll.elements.bidi.shadow_root import BiDiShadowRoot
    from pydoll.interactions.mouse import BiDiMouse
    from pydoll.protocol.bidi.input.types import (
        PointerAction,
        PointerMoveAction,
        PointerSourceActions,
    )
    from pydoll.protocol.bidi.script.types import EvaluateResult, NodeRemoteValue

logger = logging.getLogger(__name__)

ARROW_FUNCTION_PATTERN = re.compile(r'^\s*(async\s+)?(\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>')

SCREENSHOT_MIME_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
}


class BiDiWebElement(BidiFindElementsMixin):  # noqa: PLR0904
    """DOM element wrapper for Firefox automation via the WebDriver BiDi protocol.

    Elements are referenced by sharedId, which is cross-realm and
    persistent across navigations within the same document.
    """

    def __init__(
        self,
        shared_id: str,
        context_id: str,
        connection: BiDiConnectionHandler,
        attributes: dict[str, str],
        tag_name: str,
        method: By | None = None,
        selector: str | None = None,
        mouse: BiDiMouse | None = None,
        shadow_root_id: str | None = None,
        shadow_root_mode: str | None = None,
    ):
        """
        Initialize the BiDi element wrapper.

        Args:
            shared_id: BiDi sharedId referencing the DOM node.
            context_id: Browsing context the node lives in.
            connection: BiDi connection for command execution.
            attributes: Attribute map captured when the node was located.
            tag_name: Lower-case tag name of the node.
            method: Search strategy used to find this element (for debugging).
            selector: Selector used to find this element (for debugging).
            mouse: The tab's shared mouse, used for humanized pointer actions.
            shadow_root_id: sharedId of the attached shadow root, when any.
            shadow_root_mode: Mode of the attached shadow root ('open'/'closed').
        """
        self._shared_id = shared_id
        self._context_id = context_id
        self._connection_handler = connection
        self._attributes = dict(attributes)
        self._attributes['tag_name'] = tag_name
        self._search_method = method
        self._selector = selector
        self._mouse = mouse
        self._keyboard: BiDiKeyboard | None = None
        self._content_context: str | None = None
        self._shadow_root_id = shadow_root_id
        self._shadow_root_mode = shadow_root_mode
        logger.debug(
            'BiDiWebElement initialized: shared_id=%s, method=%s, selector=%s, attributes=%s',
            self._shared_id,
            self._search_method,
            self._selector,
            len(self._attributes),
        )

    def _get_keyboard(self) -> BiDiKeyboard:
        """Get or create the keyboard controller bound to this element."""
        if self._keyboard is None:
            self._keyboard = BiDiKeyboard(self)
        return self._keyboard

    async def _resolve_locate_target(self) -> tuple[str, list[SharedReference] | None]:
        """Search inside an iframe's child context; otherwise scope to this element."""
        if self.is_iframe:
            return await self._get_content_context(), None
        return self._context_id, self._get_start_nodes()

    async def _get_content_context(self) -> str:
        """Resolve (and cache) the child browsing context of this iframe element.

        Reads ``el.contentWindow``: in BiDi a window RemoteValue carries the
        child browsing context id, so the iframe can be searched like a regular
        element (works for same- and cross-origin frames).
        """
        if self._content_context is None:
            result = await self._call_function_raw('(el) => el.contentWindow')
            context: object = None
            if result['type'] == 'success':
                value = result['result'].get('value')
                if isinstance(value, dict):
                    context = value.get('context')
            if not isinstance(context, str) or not context:
                raise InvalidIFrame('Could not resolve the iframe content browsing context')
            self._content_context = context
        return self._content_context

    @property
    def attributes(self) -> dict[str, str]:
        """Read-only copy of the element's cached attributes."""
        return dict(self._attributes)

    @property
    def value(self) -> str | None:
        """Element's value attribute (for form elements)."""
        return self._attributes.get('value')

    @property
    def class_name(self) -> str | None:
        """Element's CSS class name(s)."""
        return self._attributes.get('class')

    @property
    def id(self) -> str | None:
        """Element's ID attribute."""
        return self._attributes.get('id')

    @property
    def tag_name(self) -> str | None:
        """Element's HTML tag name."""
        return self._attributes.get('tag_name')

    @property
    def is_iframe(self) -> bool:
        """Whether the element represents an iframe."""
        return self.tag_name in {'iframe', 'frame'}

    @property
    def is_enabled(self) -> bool:
        """Whether element is enabled (not disabled)."""
        return 'disabled' not in self._attributes

    async def text(self) -> str:
        """Visible text content of the element."""
        text_value = str(await self._call_on_element('(el) => (el.textContent || "").trim()') or '')
        logger.debug('Extracted text length: %s', len(text_value))
        return text_value

    async def inner_html(self) -> str:
        """HTML content of the element (its outer HTML)."""
        return str(await self._call_on_element('(el) => el.outerHTML') or '')

    async def bounds(self) -> dict[str, int]:
        """Element's bounding box (``x``, ``y``, ``width``, ``height``) in CSS pixels."""
        return await self.get_bounds_using_js()

    def get_attribute(self, name: str) -> str | None:
        """
        Get element attribute value.

        Note:
            Only provides attributes available when element was located.
            For dynamic attributes, consider using JavaScript evaluation.
        """
        return self._attributes.get(name)

    async def get_bounds_using_js(self) -> dict[str, int]:
        """Get element bounds using JavaScript getBoundingClientRect()."""
        bounds = await self._call_on_element(
            '(el) => { const r = el.getBoundingClientRect();'
            ' return {x: r.x, y: r.y, width: r.width, height: r.height} }'
        )
        return bounds if isinstance(bounds, dict) else {}

    async def get_parent_element(self) -> BiDiWebElement:
        """Element's parent element."""
        logger.debug('Getting parent element for shared_id=%s', self._shared_id)
        result = await self._call_function_raw('(el) => el.parentElement')
        if result['type'] != 'success':
            raise ElementNotFound('Parent element not found')
        remote = result['result']
        if not remote.get('sharedId'):
            raise ElementNotFound('Parent element not found')
        node = cast('NodeRemoteValue', remote)
        return self._create_element_from_node(node, By.XPATH, '..', self._context_id)

    async def get_shadow_root(self, timeout: float = 0) -> BiDiShadowRoot:
        """
        Get the shadow root attached to this element (open or closed).

        Args:
            timeout: Maximum seconds to wait for the shadow root to appear.
                When > 0, repeatedly re-reads the node until a shadow root is
                attached or the timeout expires.

        Returns:
            BiDiShadowRoot instance for traversing the shadow DOM.

        Raises:
            ShadowRootNotFound: If no shadow root is attached (when timeout=0).
            WaitElementTimeout: If timeout > 0 and no shadow root appears
                within the specified duration.
        """
        if not timeout:
            return await self._get_shadow_root()

        start_time = asyncio.get_running_loop().time()
        interval = PollInterval()
        while True:
            try:
                return await self._get_shadow_root()
            except ShadowRootNotFound:
                pass

            if asyncio.get_running_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow root on element'
                )

            await interval.wait()

    async def _get_shadow_root(self) -> BiDiShadowRoot:
        """Get the shadow root attached to this element (single attempt)."""
        if self._shadow_root_id is None:
            await self._refresh_shadow_root()
        if self._shadow_root_id is None:
            raise ShadowRootNotFound()
        from pydoll.elements.bidi.shadow_root import BiDiShadowRoot  # noqa: PLC0415

        logger.debug(
            'Shadow root resolved: shared_id=%s, mode=%s',
            self._shadow_root_id,
            self._shadow_root_mode,
        )
        return BiDiShadowRoot(
            shadow_root_id=self._shadow_root_id,
            context_id=self._context_id,
            connection=self._connection_handler,
            mode=self._shadow_root_mode or 'open',
            host_element=self,
            mouse=self._mouse,
        )

    async def _refresh_shadow_root(self) -> None:
        """Re-serialize the node to pick up a shadow root attached after location."""
        result = await self._call_function_raw('(el) => el')
        if result['type'] != 'success':
            return
        node_props = result['result'].get('value')
        shadow_root = node_props.get('shadowRoot') if isinstance(node_props, dict) else None
        if not shadow_root:
            return
        shadow_props = shadow_root.get('value')
        self._shadow_root_id = shadow_root.get('sharedId')
        self._shadow_root_mode = shadow_props.get('mode') if shadow_props else None

    async def get_children_elements(
        self, max_depth: int = 1, tag_filter: list[str] | None = None, raise_exc: bool = False
    ) -> list[BiDiWebElement]:
        """
        Retrieve all direct and nested child elements of this element.

        Args:
            max_depth: Maximum depth to traverse when finding children. Defaults
                to 1 for direct children only; any other value returns every
                descendant.
            tag_filter: HTML tag names to keep. If empty, returns all children.
            raise_exc: Raise ElementNotFound when no child matches.

        Returns:
            Child elements found within the depth and matching the tag filter.

        Raises:
            ElementNotFound: If no child elements are found and raise_exc is True.
        """
        logger.debug(
            'Getting children: max_depth=%s, tag_filter=%s, raise_exc=%s',
            max_depth,
            tag_filter,
            raise_exc,
        )
        selector = ':scope > *' if max_depth == 1 else ':scope *'
        children = await self._find_elements(By.CSS_SELECTOR, selector, raise_exc=False)
        if tag_filter:
            allowed = {tag.lower() for tag in tag_filter}
            children = [c for c in children if (c.tag_name or '').lower() in allowed]
        if not children and raise_exc:
            raise ElementNotFound(f'Child element not found for element: {self}')
        logger.debug('Children found: %s', len(children))
        return children

    async def get_siblings_elements(
        self, tag_filter: list[str] | None = None, raise_exc: bool = False
    ) -> list[BiDiWebElement]:
        """
        Retrieve all sibling elements of this element (elements at the same DOM level).

        Args:
            tag_filter: HTML tag names to keep. If empty, returns all siblings.
            raise_exc: Raise ElementNotFound when no sibling matches.

        Returns:
            Sibling elements sharing this element's parent, excluding the element itself.

        Raises:
            ElementNotFound: If no sibling elements are found and raise_exc is True.
        """
        logger.debug('Getting siblings: tag_filter=%s, raise_exc=%s', tag_filter, raise_exc)
        parent = await self.get_parent_element()
        children = await parent.get_children_elements(max_depth=1, tag_filter=tag_filter)
        siblings = [s for s in children if s._shared_id != self._shared_id]
        if not siblings and raise_exc:
            raise ElementNotFound(f'Sibling element not found for element: {self}')
        logger.debug('Siblings found: %s', len(siblings))
        return siblings

    async def take_screenshot(
        self,
        path: str | Path | None = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> str | None:
        """
        Capture screenshot of this element only.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100), used for jpeg/webp.
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            MissingScreenshotPath: If path is None and as_base64 is False.
        """
        if not path and not as_base64:
            raise MissingScreenshotPath()

        if path:
            output_extension = Path(str(path)).suffix.lstrip('.').lower()
        else:
            output_extension = 'png'

        mime_type = SCREENSHOT_MIME_TYPES.get(output_extension)
        if mime_type is None:
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        image_format = ImageFormat(type=mime_type)
        if mime_type != 'image/png':
            image_format['quality'] = quality / 100

        clip = ElementClipRectangle(
            type='element',
            element=SharedReference(sharedId=self._shared_id),
        )
        logger.debug(
            'Taking element screenshot: path=%s, quality=%s, as_base64=%s',
            path,
            quality,
            as_base64,
        )
        response = await self._execute_command(
            BrowsingContextCommands.capture_screenshot(
                context=self._context_id,
                format=image_format,
                clip=clip,
            )
        )
        data = response['result']['data']

        if as_base64:
            logger.info('Element screenshot captured and returned as base64')
            return data

        if path:
            async with aiofiles.open(str(path), 'wb') as file:
                await file.write(base64.b64decode(data))
            logger.info('Element screenshot saved: %s', path)

        return None

    async def scroll_into_view(self):
        """Scroll element into the viewport, centred so it is clear of the edges."""
        logger.info('Scrolling element into view: shared_id=%s', self._shared_id)
        try:
            await self._call_on_element(
                '(el) => el.scrollIntoView({block: "center", inline: "center"})'
            )
        except CommandFailed as exc:
            raise ElementNotVisible(f'Element cannot be scrolled into view: {exc}') from exc

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        is_hidden: bool = False,
        is_detached: bool = False,
        is_enabled: bool = False,
        timeout: float = 0,
    ):
        """Wait for the element to meet every condition you set to True.

        ``is_visible`` and ``is_interactable`` wait for the element to show up
        and accept input; ``is_hidden`` waits for it to leave the screen (a
        spinner finishing), ``is_detached`` for it to leave the DOM, and
        ``is_enabled`` for its ``disabled`` attribute to be cleared. With the
        default ``timeout`` of 0 the conditions are checked once.

        Raises:
            ValueError: If no condition is set to True.
            WaitElementTimeout: If the conditions are not all met within ``timeout``.
        """
        checks_map = [
            (is_visible, 'visible', self.is_visible),
            (is_interactable, 'interactable', self.is_interactable),
            (is_hidden, 'hidden', self._is_hidden),
            (is_detached, 'detached', self.is_detached),
            (is_enabled, 'enabled', self._is_enabled_now),
        ]
        checks = [func for flag, _, func in checks_map if flag]
        if not checks:
            raise ValueError('Set at least one condition on wait_until()')

        condition_msg = ' and '.join(label for flag, label, _ in checks_map if flag)

        logger.info(
            'Waiting for element: visible=%s, interactable=%s, hidden=%s, detached=%s, '
            'enabled=%s, timeout=%ss',
            is_visible,
            is_interactable,
            is_hidden,
            is_detached,
            is_enabled,
            timeout,
        )
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        interval = PollInterval()
        while True:
            results = await asyncio.gather(*(check() for check in checks))
            if all(results):
                logger.info('Element condition satisfied: %s', condition_msg)
                return

            if loop.time() >= deadline:
                logger.error('Timeout waiting for element to become %s', condition_msg)
                raise WaitElementTimeout(f'Timed out waiting for element to become {condition_msg}')

            await interval.wait()

    async def click_using_js(self):
        """
        Click element using JavaScript click() method.

        Raises:
            ElementNotVisible: If element is not visible.
            ElementNotInteractable: If element couldn't be clicked.

        Note:
            For <option> elements, uses specialized selection approach.
            Element is automatically scrolled into view.
        """
        if self._is_option_tag():
            return await self._click_option_tag()

        await self.scroll_into_view()

        if not await self.is_visible():
            raise ElementNotVisible()

        logger.info('Clicking element via JS: shared_id=%s', self._shared_id)
        result = await self._call_on_element('(el) => { el.click(); return true }')
        if not result:
            raise ElementNotInteractable()

    async def _click_option_tag(self) -> None:
        """Select an ``<option>`` via JavaScript (it has no box for a trusted click)."""
        await self._call_on_element(
            '(el) => {'
            '  const select = el.parentElement ? el.parentElement.closest("select") : null;'
            '  if (!select) { return false; }'
            '  for (const opt of select.options) { opt.selected = false; }'
            '  el.selected = true;'
            '  select.value = el.value;'
            '  select.dispatchEvent(new Event("input", {bubbles: true}));'
            '  select.dispatchEvent(new Event("change", {bubbles: true}));'
            '  return true;'
            '}'
        )

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0,
        humanize: bool = False,
    ):
        """
        Click element using simulated mouse events.

        Uses ``input.performActions`` so the events report ``isTrusted=true``,
        instead of a synthetic JS click. Offsets are relative to the element's
        center.

        Args:
            x_offset: Horizontal offset from element center.
            y_offset: Vertical offset from element center.
            hold_time: Seconds to keep the button down between press and release
                (used when humanize=False). Zero by default, so a plain click is
                two back-to-back events; pass humanize=True for human timing.
            humanize: When True and the tab's mouse is available, moves along a
                Bezier curve from the current tracked position to the element
                center before clicking. When False, the pointer jumps to the
                element and clicks.

        Raises:
            ElementNotVisible: If element is not visible.

        Note:
            For <option> elements, delegates to specialized JavaScript approach.
            Element is automatically scrolled into view.
        """
        if self._is_option_tag():
            return await self._click_option_tag()

        if not await self.is_visible():
            raise ElementNotVisible()

        await self.scroll_into_view()

        if humanize and self._mouse is not None:
            x, y = await self._target_point(x_offset, y_offset)
            logger.info('Clicking element (humanized): x=%s, y=%s', x, y)
            await self._mouse.click(x, y, humanize=True)
            return

        logger.info(
            'Clicking element: x_offset=%s, y_offset=%s, hold=%ss', x_offset, y_offset, hold_time
        )
        await self._perform_pointer_actions([
            self._move_to_element_action(x_offset, y_offset),
            {'type': 'pointerDown', 'button': 0},
            {'type': 'pause', 'duration': int(hold_time * 1000)},
            {'type': 'pointerUp', 'button': 0},
        ])

    async def hover(self, x_offset: int = 0, y_offset: int = 0, humanize: bool = False):
        """
        Move the mouse over the element without clicking.

        Scrolls the element into view and moves the pointer to its center plus
        the offsets, so hover styles, tooltips and menus that open on
        ``mouseover`` react as they would for a person.

        Args:
            x_offset: Horizontal offset from the element center.
            y_offset: Vertical offset from the element center.
            humanize: Move along a curved path with human timing instead of
                jumping straight to the point.

        Raises:
            ElementNotVisible: If the element is not visible.
        """
        if not await self.is_visible():
            raise ElementNotVisible()

        await self.scroll_into_view()

        if humanize and self._mouse is not None:
            x, y = await self._target_point(x_offset, y_offset)
            await self._mouse.move(x, y, humanize=True)
            return

        logger.info('Hovering element: x_offset=%s, y_offset=%s', x_offset, y_offset)
        await self._perform_pointer_actions([self._move_to_element_action(x_offset, y_offset)])

    async def double_click(self, x_offset: int = 0, y_offset: int = 0, humanize: bool = False):
        """
        Double-click the element.

        Sends the two press-and-release pairs a real double click produces, so
        the page receives ``dblclick`` as well as the two ``click`` events.

        Args:
            x_offset: Horizontal offset from the element center.
            y_offset: Vertical offset from the element center.
            humanize: Move the mouse along a curved path before clicking.

        Raises:
            ElementNotVisible: If the element is not visible.
        """
        if not await self.is_visible():
            raise ElementNotVisible()

        await self.scroll_into_view()

        if humanize and self._mouse is not None:
            x, y = await self._target_point(x_offset, y_offset)
            await self._mouse.double_click(x, y, humanize=True)
            return

        logger.info('Double-clicking element: x_offset=%s, y_offset=%s', x_offset, y_offset)
        await self._perform_pointer_actions([
            self._move_to_element_action(x_offset, y_offset),
            {'type': 'pointerDown', 'button': 0},
            {'type': 'pointerUp', 'button': 0},
            {'type': 'pointerDown', 'button': 0},
            {'type': 'pointerUp', 'button': 0},
        ])

    def _move_to_element_action(self, x_offset: int, y_offset: int) -> PointerMoveAction:
        """Pointer move whose origin is the element's center plus the offsets."""
        origin = ElementOrigin(type='element', element=SharedReference(sharedId=self._shared_id))
        return {
            'type': 'pointerMove',
            'x': x_offset,
            'y': y_offset,
            'origin': origin,
        }

    async def _perform_pointer_actions(self, actions: list[PointerAction]) -> None:
        """Dispatch a sequence of trusted pointer actions in this element's context."""
        source: PointerSourceActions = {
            'type': 'pointer',
            'id': 'mouse',
            'parameters': {'pointerType': PointerType.MOUSE},
            'actions': actions,
        }
        await self._execute_command(
            InputCommands.perform_actions(context=self._context_id, actions=[source])
        )

    async def _target_point(self, x_offset: int, y_offset: int) -> tuple[float, float]:
        """The element's center in viewport coordinates, plus the offsets."""
        bounds = await self.get_bounds_using_js()
        return (
            bounds['x'] + bounds['width'] / 2 + x_offset,
            bounds['y'] + bounds['height'] / 2 + y_offset,
        )

    async def focus(self):
        """Focus this element."""
        await self._call_on_element('(el) => el.focus()')

    async def clear(self):
        """
        Clear the current value of the element.

        Supports standard inputs, textareas, and contenteditable elements.
        Dispatches ``input`` and ``change`` events so frameworks detect the update.

        Raises:
            ElementNotInteractable: If the element does not accept text input.
        """
        logger.info('Clearing element value')
        result = await self._call_on_element(
            '(el) => {'
            '  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {'
            '    el.value = "";'
            '    el.dispatchEvent(new Event("input", {bubbles: true}));'
            '    el.dispatchEvent(new Event("change", {bubbles: true}));'
            '    return true;'
            '  } else if (el.isContentEditable) {'
            '    el.textContent = "";'
            '    return true;'
            '  }'
            '  return false;'
            '}'
        )
        if not result:
            logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        if self._is_text_field():
            self._attributes['value'] = ''

    async def insert_text(self, text: str):
        """
        Insert text into element using JavaScript.

        Supports standard inputs, textareas and contenteditable elements. The
        value is set in one step (no key events); use ``type_text`` for trusted
        per-character typing.

        Args:
            text: Text to insert.

        Raises:
            ElementNotInteractable: If element does not accept text input.
        """
        logger.info('Inserting text (length=%s)', len(text))
        result = await self._call_on_element(
            '(el, text) => {'
            '  el.focus();'
            '  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {'
            '    el.value = text;'
            '  } else if (el.isContentEditable) {'
            '    el.textContent = text;'
            '  } else {'
            '    return false;'
            '  }'
            '  el.dispatchEvent(new Event("input", {bubbles: true}));'
            '  el.dispatchEvent(new Event("change", {bubbles: true}));'
            '  return true;'
            '}',
            {'type': 'string', 'value': text},
        )
        if result is False:
            logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        if self._is_text_field():
            self._attributes['value'] = text

    async def set_input_files(self, files: str | Path | list[str | Path]):
        """
        Set file paths for file input element.

        Args:
            files: Absolute file paths to existing files.
        """
        files_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
        logger.info('Setting input files: count=%s', len(files_list))
        await self._execute_command(
            InputCommands.set_files(
                context=self._context_id,
                element=SharedReference(sharedId=self._shared_id),
                files=files_list,
            )
        )

    async def type_text(self, text: str, humanize: bool = False):
        """
        Type text character by character with trusted key events.

        Clicks the element to focus it, then dispatches per-character
        keyDown/keyUp through the BiDi keyboard so the events report
        ``isTrusted=true``.

        Args:
            text: Text to type into the element.
            humanize: When True, simulates human-like typing.
        """
        logger.info('Typing text (length=%s, humanize=%s)', len(text), humanize)
        await self.click(humanize=humanize)
        keyboard = self._get_keyboard()
        await keyboard.type_text(text, humanize=humanize)

    async def is_editable(self) -> bool:
        """
        Check if element can accept text input.

        Returns:
            True if element is editable (input, textarea, or contenteditable).
        """
        is_editable = bool(
            await self._call_on_element(
                '(el) => !el.disabled && !el.readOnly && '
                '(el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)'
            )
        )
        logger.debug('Element editable check: %s', is_editable)
        return is_editable

    async def is_visible(self) -> bool:
        """Check if element is visible (rendered, not hidden, with a non-empty box)."""
        try:
            return bool(
                await self._call_on_element(
                    '(el) => {'
                    '  const s = getComputedStyle(el);'
                    '  return s.display !== "none" && s.visibility !== "hidden" '
                    '    && s.opacity !== "0" && el.offsetWidth > 0 && el.offsetHeight > 0'
                    '}'
                )
            )
        except CommandFailed:
            return False

    async def is_detached(self) -> bool:
        """Whether the element is no longer part of a document (removed or replaced)."""
        try:
            return bool(await self._call_on_element('(el) => !el.isConnected'))
        except CommandFailed:
            return True

    async def _is_hidden(self) -> bool:
        """Whether the element is not visible, counting a detached element as hidden."""
        return not await self.is_visible()

    async def _is_enabled_now(self) -> bool:
        """Whether the element accepts input right now, read from the live DOM."""
        try:
            return bool(await self._call_on_element('(el) => !el.disabled'))
        except CommandFailed:
            return False

    async def is_on_top(self) -> bool:
        """Check if element is topmost at its center point (not covered by overlays)."""
        try:
            return bool(
                await self._call_on_element(
                    '(el) => {'
                    '  const r = el.getBoundingClientRect();'
                    '  const top = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);'
                    '  return el === top || el.contains(top)'
                    '}'
                )
            )
        except CommandFailed:
            return False

    async def is_interactable(self) -> bool:
        """Check if element is interactable based on visibility and position."""
        visible = await self.is_visible()
        on_top = await self.is_on_top()
        return visible and on_top

    async def evaluate(self, script: str, *args: object) -> object:
        """
        Run JavaScript with ``this`` bound to the element and return its value.

        The portable counterpart of the CDP element's ``execute_script``: the
        same call works on a Chromium ``WebElement``. ``script`` is either a
        function declaration (``function(a) { return this.value + a }``) or a
        body that may use ``return``; ``args`` are JSON-serialisable values
        forwarded as the function's arguments. An arrow function is called as
        is (it has no ``this``, as in JavaScript itself). A returned promise is
        awaited and its settled value is deserialized (objects and arrays
        become dicts and lists).

        Args:
            script: JavaScript function declaration, arrow function or body.
            *args: Values forwarded to the function as positional arguments.

        Returns:
            The script's return value as a Python object.

        Raises:
            ScriptEvaluationError: If the script throws or its promise rejects.
        """
        from pydoll.browser.firefox.tab import BiDiTab  # noqa: PLC0415

        element_ref: dict = {'type': 'node', 'sharedId': self._shared_id}
        arguments = [BiDiTab._to_local_value(arg) for arg in args]
        if ARROW_FUNCTION_PATTERN.match(script) or is_script_already_function(script):
            function_declaration = script
        else:
            function_declaration = f'function() {{ {script} }}'

        result = await self._call_function_raw(
            function_declaration,
            arguments=arguments,
            this=element_ref,
            await_promise=True,
        )
        if result['type'] == 'exception':
            raise ScriptEvaluationError(result['exceptionDetails']['text'])
        return BiDiTab._deserialize_remote_value(result['result'])

    def __repr__(self):
        """String representation showing attributes and shared ID."""
        attrs = ', '.join(f'{k}={v!r}' for k, v in self._attributes.items())
        return f'{self.__class__.__name__}({attrs})(shared_id={self._shared_id})'

    async def _call_on_element(self, function_declaration: str, *extra_args: dict) -> object:
        """Call a JavaScript function with this element and return its deserialized value."""
        from pydoll.browser.firefox.tab import BiDiTab  # noqa: PLC0415

        result = await self._call_function_raw(function_declaration, arguments=list(extra_args))
        if result['type'] == 'exception':
            raise ScriptEvaluationError(result['exceptionDetails']['text'])
        return BiDiTab._deserialize_remote_value(result['result'])

    async def _call_function_raw(
        self,
        function_declaration: str,
        arguments: list[dict] | None = None,
        this: dict | None = None,
        await_promise: bool = False,
    ) -> EvaluateResult:
        """Call a JavaScript function in this element's context with the element first.

        Unless ``this`` is given, the element is passed as the first argument.
        Returns the raw BiDi ``EvaluateResult`` so callers can inspect node
        RemoteValues (sharedId, shadowRoot, contentWindow).
        """
        call_arguments: list[dict] = list(arguments or [])
        if this is None:
            call_arguments.insert(0, {'type': 'node', 'sharedId': self._shared_id})
        response = await self._execute_command(
            ScriptCommands.call_function(
                function_declaration=function_declaration,
                await_promise=await_promise,
                target=ContextTarget(context=self._context_id),
                arguments=call_arguments,
                this=this,
            )
        )
        return response['result']

    def _is_option_tag(self) -> bool:
        """Check if element is an <option> tag."""
        return (self.tag_name or '').lower() == 'option'

    def _is_text_field(self) -> bool:
        """Check if element is an <input> or <textarea>."""
        return (self.tag_name or '').lower() in {'input', 'textarea'}
