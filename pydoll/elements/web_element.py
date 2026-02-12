from __future__ import annotations

import asyncio
import json
import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles

from pydoll.commands import (
    DomCommands,
    InputCommands,
    PageCommands,
    RuntimeCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import (
    Key,
    Scripts,
)
from pydoll.elements.mixins import FindElementsMixin
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    InvalidFileExtension,
    InvalidIFrame,
    MissingScreenshotPath,
    ShadowRootNotFound,
    WaitElementTimeout,
)
from pydoll.interactions.iframe import IFrameContext, IFrameContextResolver
from pydoll.interactions.keyboard import Keyboard
from pydoll.protocol.dom.types import ShadowRootType
from pydoll.protocol.input.types import (
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
)
from pydoll.protocol.page.types import ScreenshotFormat, Viewport
from pydoll.protocol.runtime.methods import (
    CallFunctionOnResponse,
    EvaluateResponse,
    GetPropertiesResponse,
    SerializationOptions,
)
from pydoll.protocol.runtime.types import CallArgument
from pydoll.utils import (
    decode_base64_to_bytes,
    extract_text_from_html,
    is_script_already_function,
)

if TYPE_CHECKING:
    from pydoll.interactions.mouse import Mouse as MouseType
    from pydoll.protocol.dom.methods import (
        DescribeNodeResponse,
        GetBoxModelResponse,
        GetOuterHTMLResponse,
        ResolveNodeResponse,
    )
    from pydoll.protocol.dom.types import Quad
    from pydoll.protocol.page.methods import CaptureScreenshotResponse
    from pydoll.protocol.runtime.methods import GetPropertiesResponse

logger = logging.getLogger(__name__)


class WebElement(FindElementsMixin):  # noqa: PLR0904
    """
    DOM element wrapper for browser automation.

    Provides comprehensive functionality for element interaction, inspection,
    and manipulation using Chrome DevTools Protocol commands.
    """

    if TYPE_CHECKING:
        _routing_session_handler: Optional[ConnectionHandler]
        _routing_session_id: Optional[str]
        _routing_parent_frame_id: Optional[str]

    def __init__(
        self,
        object_id: str,
        connection_handler: ConnectionHandler,
        method: Optional[str] = None,
        selector: Optional[str] = None,
        attributes_list: list[str] = [],
        mouse: Optional['MouseType'] = None,
    ):
        """
        Initialize WebElement wrapper.

        Args:
            object_id: Unique CDP object identifier for this DOM element.
            connection_handler: Connection instance for browser communication.
            method: Search method used to find this element (for debugging).
            selector: Selector string used to find this element (for debugging).
            attributes_list: Flat list of alternating attribute names and values.
            mouse: Optional Mouse instance for humanized click behavior.
        """
        self._object_id = object_id
        self._search_method = method
        self._selector = selector
        self._connection_handler = connection_handler
        self._attributes: dict[str, str] = {}
        self._keyboard: Optional[Keyboard] = None
        self._mouse = mouse
        self._iframe_context: Optional[IFrameContext] = None
        self._iframe_resolver: Optional[IFrameContextResolver] = None
        self._def_attributes(attributes_list)
        logger.debug(
            f'WebElement initialized: object_id={self._object_id}, '
            f'method={self._search_method}, selector={self._selector}, '
            f'attributes={len(self._attributes)}'
        )

    def _get_keyboard(self) -> Keyboard:
        """Get or create the keyboard controller."""
        if self._keyboard is None:
            self._keyboard = Keyboard(self)
        return self._keyboard

    def _get_iframe_resolver(self) -> IFrameContextResolver:
        """Get or create the iframe context resolver."""
        if self._iframe_resolver is None:
            self._iframe_resolver = IFrameContextResolver(self)
        return self._iframe_resolver

    @property
    def attributes(self) -> dict[str, str]:
        """Read-only copy of the element's cached attributes."""
        return dict(self._attributes)

    @property
    def value(self) -> Optional[str]:
        """Element's value attribute (for form elements)."""
        return self._attributes.get('value')

    @property
    def class_name(self) -> Optional[str]:
        """Element's CSS class name(s)."""
        return self._attributes.get('class_name')

    @property
    def id(self) -> Optional[str]:
        """Element's ID attribute."""
        return self._attributes.get('id')

    @property
    def tag_name(self) -> Optional[str]:
        """Element's HTML tag name."""
        return self._attributes.get('tag_name')

    @property
    def is_iframe(self) -> bool:
        """Whether the element represents an iframe."""
        return self.tag_name == 'iframe'

    @property
    def is_enabled(self) -> bool:
        """Whether element is enabled (not disabled)."""
        return bool('disabled' not in self._attributes.keys())

    @property
    async def text(self) -> str:
        """Visible text content of the element."""
        if self._is_inside_iframe():
            response: CallFunctionOnResponse = await self.execute_script(
                'return (this.textContent || "").trim()', return_by_value=True
            )
            text_value = response.get('result', {}).get('result', {}).get('value', '') or ''
            logger.debug(f'Extracted text length (iframe ctx): {len(text_value)}')
            return text_value

        outer_html = await self.inner_html
        text_value = extract_text_from_html(outer_html, strip=True)
        logger.debug(f'Extracted text length: {len(text_value)}')
        return text_value

    @property
    async def bounds(self) -> Quad:
        """
        Element's bounding box coordinates.

        Returns coordinates in CSS pixels relative to document origin.
        """
        command = DomCommands.get_box_model(object_id=self._object_id)
        response: GetBoxModelResponse = await self._execute_command(command)
        content = response['result']['model']['content']
        logger.debug(f'Bounds retrieved (points={len(content)})')
        return content

    @property
    async def inner_html(self) -> str:
        if self.is_iframe:
            return await self._get_iframe_inner_html()

        if self._is_inside_iframe():
            response: CallFunctionOnResponse = await self.execute_script(
                'return this.outerHTML', return_by_value=True
            )
            return response.get('result', {}).get('result', {}).get('value', '')

        command = DomCommands.get_outer_html(object_id=self._object_id)
        response_get_outer_html: GetOuterHTMLResponse = await self._execute_command(command)
        return response_get_outer_html['result']['outerHTML']

    @property
    async def iframe_context(self) -> Optional[IFrameContext]:
        """
        Return the resolved iframe context for this element when it is an <iframe>.

        The context includes: frame_id, document_url, execution_context_id,
        document_object_id and, for OOPIF targets, the session_id and
        session_handler used for routing commands. The first call resolves and
        caches the context. Non-iframe elements return None.

        Returns:
            IFrameContext | None: Cached iframe context or None for non-iframes.
        """
        if not self.is_iframe:
            return None

        if self._iframe_context:
            return self._iframe_context

        resolver = self._get_iframe_resolver()
        self._iframe_context = await resolver.resolve()
        self._apply_routing_from_context()
        return self._iframe_context

    def get_attribute(self, name: str) -> Optional[str]:
        """
        Get element attribute value.

        Note:
            Only provides attributes available when element was located.
            For dynamic attributes, consider using JavaScript execution.
        """
        if name == 'class' and 'class_name' in self._attributes:
            return self._attributes.get('class_name')
        return self._attributes.get(name)

    async def get_bounds_using_js(self) -> dict[str, int]:
        """
        Get element bounds using JavaScript getBoundingClientRect().

        Returns coordinates relative to viewport (alternative to bounds property).
        """
        response = await self.execute_script(Scripts.BOUNDS, return_by_value=True)
        bounds = json.loads(response['result']['result']['value'])
        logger.debug(f'Bounds via JS: {bounds}')
        return bounds

    async def get_parent_element(self) -> WebElement:
        """Element's parent element."""
        logger.debug(f'Getting parent element for object_id={self._object_id}')
        result = await self.execute_script(Scripts.GET_PARENT_NODE)
        if not self._has_object_id_key(result):
            raise ElementNotFound(f'Parent element not found for element: {self}')

        object_id = result['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
        logger.debug(f'Parent element resolved: object_id={object_id}')
        return WebElement(
            object_id, self._connection_handler, attributes_list=attributes, mouse=self._mouse
        )

    async def get_shadow_root(self, timeout: float = 0) -> ShadowRoot:
        """
        Get the shadow root attached to this element.

        Args:
            timeout: Maximum seconds to wait for the shadow root to appear.
                When > 0, repeatedly polls (every 0.5s) until a shadow root
                is found or the timeout expires.

        Returns:
            ShadowRoot instance for traversing the shadow DOM.

        Raises:
            ShadowRootNotFound: If no shadow root is attached (when timeout=0).
            WaitElementTimeout: If timeout > 0 and no shadow root appears
                within the specified duration.
        """
        if not timeout:
            return await self._get_shadow_root()

        start_time = asyncio.get_event_loop().time()
        while True:
            try:
                return await self._get_shadow_root()
            except ShadowRootNotFound:
                pass

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow root on element'
                )

            await asyncio.sleep(0.5)

    async def _get_shadow_root(self) -> ShadowRoot:
        """Get the shadow root attached to this element (single attempt)."""
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=self._object_id, depth=1, pierce=True)
        )
        node_info = response.get('result', {}).get('node', {})
        shadow_roots = node_info.get('shadowRoots', [])
        if not shadow_roots:
            raise ShadowRootNotFound()

        shadow_root_data = shadow_roots[0]
        backend_node_id = shadow_root_data.get('backendNodeId')
        if not backend_node_id:
            raise ShadowRootNotFound('Shadow root found but backend node ID is unavailable')

        resolve_response: ResolveNodeResponse = await self._execute_command(
            DomCommands.resolve_node(backend_node_id=backend_node_id)
        )
        shadow_object_id = resolve_response['result']['object']['objectId']

        mode = ShadowRootType(shadow_root_data.get('shadowRootType', 'open'))

        logger.debug(f'Shadow root resolved: object_id={shadow_object_id}, mode={mode.value}')
        return ShadowRoot(
            object_id=shadow_object_id,
            connection_handler=self._connection_handler,
            mode=mode,
            host_element=self,
        )

    async def get_children_elements(
        self, max_depth: int = 1, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """
        Retrieve all direct and nested child elements of this element.

        Args:
            max_depth (int, optional): Maximum depth to traverse when finding children.
                Defaults to 1 for direct children only.
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all child elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of child WebElement objects found within the specified
                depth and matching the tag filter criteria.

        Raises:
            ElementNotFound: If no child elements are found for this element and raise_exc is True.
        """
        logger.debug(
            f'Getting children: max_depth={max_depth}, '
            f'tag_filter={tag_filter}, raise_exc={raise_exc}'
        )
        children = await self._get_family_elements(
            script=Scripts.GET_CHILDREN_NODE, max_depth=max_depth, tag_filter=tag_filter
        )
        if not children and raise_exc:
            raise ElementNotFound(f'Child element not found for element: {self}')
        logger.debug(f'Children found: {len(children)}')
        return children

    async def get_siblings_elements(
        self, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """
        Retrieve all sibling elements of this element (elements at the same DOM level).

        Args:
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all sibling elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of sibling WebElement objects that share the same
                parent as this element and match the tag filter criteria.

        Raises:
            ElementNotFound: If no sibling elements are found for this element
            and raise_exc is True.
        """
        logger.debug(f'Getting siblings: tag_filter={tag_filter}, raise_exc={raise_exc}')
        siblings = await self._get_family_elements(
            script=Scripts.GET_SIBLINGS_NODE, tag_filter=tag_filter
        )
        if not siblings and raise_exc:
            raise ElementNotFound(f'Sibling element not found for element: {self}')
        logger.debug(f'Siblings found: {len(siblings)}')
        return siblings

    async def take_screenshot(
        self,
        path: Optional[str | Path] = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Capture screenshot of this element only.

        Automatically scrolls element into view before capturing.

        Args:
            path: File path for screenshot (extension determines format).
            quality: Image quality 0-100 (default 100).
            as_base64: Return as base64 string instead of saving file.

        Returns:
            Base64 screenshot data if as_base64=True, None otherwise.

        Raises:
            InvalidFileExtension: If file extension not supported.
            MissingScreenshotPath: If path is None and as_base64 is False.
        """
        if not path and not as_base64:
            raise MissingScreenshotPath()

        if path and isinstance(path, str):
            output_extension = path.split('.')[-1]
        elif path and isinstance(path, Path):
            output_extension = path.suffix.lstrip('.')
        else:
            output_extension = ScreenshotFormat.JPEG

        # Normalize jpg to jpeg (CDP only accepts jpeg)
        if output_extension == 'jpg':
            output_extension = 'jpeg'

        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        file_format = ScreenshotFormat.get_value(output_extension)

        bounds = await self.get_bounds_using_js()
        clip = Viewport(
            x=bounds['x'],
            y=bounds['y'],
            width=bounds['width'],
            height=bounds['height'],
            scale=1,
        )
        logger.debug(
            f'Taking element screenshot: path={path}, quality={quality}, as_base64={as_base64}, '
            f'clip={{x: {clip["x"]}, y: {clip["y"]}, w: {clip["width"]}, h: {clip["height"]}}}'
        )

        screenshot: CaptureScreenshotResponse = await self._connection_handler.execute_command(
            PageCommands.capture_screenshot(format=file_format, clip=clip, quality=quality)
        )

        screenshot_data = screenshot['result']['data']

        if as_base64:
            logger.info('Element screenshot captured and returned as base64')
            return screenshot_data

        if path:
            image_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(str(path), 'wb') as file:
                await file.write(image_bytes)
            logger.info(f'Element screenshot saved: {path}')

        return None

    async def scroll_into_view(self):
        """Scroll element into visible viewport."""
        command = DomCommands.scroll_into_view_if_needed(object_id=self._object_id)
        logger.info(f'Scrolling element into view: object_id={self._object_id}')
        await self._execute_command(command)

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        timeout: int = 0,
    ):
        """Wait for element to meet specified conditions.

        Raises:
            ValueError: If neither ``is_visible`` nor ``is_interactable`` is True.
            WaitElementTimeout: If the condition is not met within ``timeout``.
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
            f'Waiting for element: visible={is_visible}, '
            f'interactable={is_interactable}, timeout={timeout}s'
        )
        loop = asyncio.get_event_loop()
        start_time = loop.time()
        while True:
            results = await asyncio.gather(*(check() for check in checks))
            if all(results):
                logger.info(f'Element condition satisfied: {condition_msg}')
                return

            if timeout and loop.time() - start_time > timeout:
                logger.error(f'Timeout waiting for element to become {condition_msg}')
                raise WaitElementTimeout(f'Timed out waiting for element to become {condition_msg}')

            await asyncio.sleep(0.5)

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
        if await self._is_option_element():
            return await self._click_option_tag()

        await self.scroll_into_view()

        if not await self.is_visible():
            raise ElementNotVisible()

        logger.info(f'Clicking element via JS: object_id={self._object_id}')
        result = await self.execute_script(Scripts.CLICK, return_by_value=True)
        clicked = result['result']['result']['value']
        if not clicked:
            raise ElementNotInteractable()

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0.1,
        humanize: bool = True,
    ):
        """
        Click element using simulated mouse events.

        Args:
            x_offset: Horizontal offset from element center.
            y_offset: Vertical offset from element center.
            hold_time: Duration to hold mouse button down (used when humanize=False).
            humanize: When True and a Mouse instance is available, uses humanized
                Bezier curve movement from the current tracked position to the
                element center before clicking. When False, dispatches raw CDP
                mousePressed/mouseReleased events directly.

        Raises:
            ElementNotVisible: If element is not visible.

        Note:
            For <option> elements, delegates to specialized JavaScript approach.
            Element is automatically scrolled into view.
        """
        if await self._is_option_element():
            return await self._click_option_tag()

        if not await self.is_visible():
            raise ElementNotVisible()

        await self.scroll_into_view()

        try:
            element_bounds = await self.bounds
            position_to_click = self._calculate_center(element_bounds)
            position_to_click = (
                position_to_click[0] + x_offset,
                position_to_click[1] + y_offset,
            )
        except KeyError:
            element_bounds_js = await self.get_bounds_using_js()
            position_to_click = (
                element_bounds_js['x'] + element_bounds_js['width'] / 2 + x_offset,
                element_bounds_js['y'] + element_bounds_js['height'] / 2 + y_offset,
            )

        if humanize and self._mouse is not None:
            logger.info(
                f'Clicking element (humanized): x={position_to_click[0]}, y={position_to_click[1]}'
            )
            await self._mouse.click(position_to_click[0], position_to_click[1])
            return

        logger.info(
            f'Clicking element: x={position_to_click[0]}, '
            f'y={position_to_click[1]}, hold={hold_time}s'
        )
        press_command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_PRESSED,
            x=int(position_to_click[0]),
            y=int(position_to_click[1]),
            button=MouseButton.LEFT,
            click_count=1,
        )
        release_command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_RELEASED,
            x=int(position_to_click[0]),
            y=int(position_to_click[1]),
            button=MouseButton.LEFT,
            click_count=1,
        )
        await self._execute_command(press_command)
        await asyncio.sleep(hold_time)
        await self._execute_command(release_command)

    async def clear(self):
        """
        Clear the current value of the element.

        Supports standard inputs, textareas, and contenteditable elements.
        Dispatches ``input`` and ``change`` events so frameworks detect the update.

        Raises:
            ElementNotInteractable: If the element does not accept text input.
        """
        logger.info('Clearing element value')
        result = await self.execute_script(Scripts.CLEAR_INPUT, return_by_value=True)
        success = result['result'].get('result', {}).get('value', False)
        if not success:
            logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        if self._attributes.get('tag_name', '').lower() in {'input', 'textarea'}:
            self._attributes['value'] = ''

    async def insert_text(self, text: str):
        """
        Insert text into element using JavaScript.

        Supports standard inputs, textareas, contenteditable elements, and rich text editors.
        Inserts text at cursor position or replaces selected text.

        Args:
            text: Text to insert.

        Raises:
            ElementNotInteractable: If element does not accept text input.

        Note:
            Uses JavaScript for maximum compatibility with all input types.
            Automatically handles input/textarea and contenteditable elements.
        """
        logger.info(f'Inserting text (length={len(text)})')
        result = await self.execute_script(
            Scripts.INSERT_TEXT, return_by_value=True, arguments=[CallArgument(value=text)]
        )
        logger.debug(f'Insert text result: {result}')
        success = result['result'].get('result', {}).get('value', False)

        if not success:
            logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        # Keep cached attributes coherent for common cases (e.g., input value)
        # This avoids forcing a DOM round-trip for simple assertions.
        if self._attributes.get('tag_name', '').lower() in {'input', 'textarea'}:
            # When inserting into an empty field, resulting value equals inserted text.
            # For complex cases (non-empty with caret), tests usually check non-empty.
            self._attributes['value'] = text

    async def set_input_files(self, files: str | Path | list[str | Path]):
        """
        Set file paths for file input element.

        Args:
            files: list of absolute file paths to existing files.

        Raises:
            ElementNotAFileInput: If element is not a file input.
        """
        if (
            self._attributes.get('tag_name', '').lower() != 'input'
            or self._attributes.get('type', '').lower() != 'file'
        ):
            raise ElementNotAFileInput()
        files_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
        logger.info(f'Setting input files: count={len(files_list)}')
        await self._execute_command(
            DomCommands.set_file_input_files(files=files_list, object_id=self._object_id)
        )

    async def type_text(
        self,
        text: str,
        humanize: bool = True,
        interval: Optional[float] = None,
    ):
        """
        Type text character by character.

        Args:
            text: Text to type into the element.
            humanize: When True (default), simulates human-like typing.
            interval: Deprecated. Use humanize=True instead.
        """
        logger.info(f'Typing text (length={len(text)}, humanize={humanize})')
        await self.click()
        keyboard = self._get_keyboard()
        await keyboard.type_text(text, humanize=humanize, interval=interval)

    async def key_down(self, key: Key, modifiers: Optional[KeyModifier] = None):
        """
        Send key down event.

        .. deprecated::
            This method is deprecated. Use ``tab.keyboard.down()`` instead.

        Note:
            Only sends key down without release. Pair with key_up() for complete keypress.
        """
        warnings.warn(
            'WebElement.key_down() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.down(key, modifiers)',
            DeprecationWarning,
            stacklevel=2,
        )
        key_name, code = key
        logger.info(f'Key down: key={key_name} code={code} modifiers={modifiers}')
        await self._execute_command(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_DOWN,
                key=key_name,
                windows_virtual_key_code=code,
                native_virtual_key_code=code,
                modifiers=modifiers,
            )
        )

    async def key_up(self, key: Key):
        """
        Send key up event (should follow corresponding key_down()).

        .. deprecated::
            This method is deprecated. Use ``tab.keyboard.up()`` instead.
        """
        warnings.warn(
            'WebElement.key_up() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.up(key)',
            DeprecationWarning,
            stacklevel=2,
        )
        key_name, code = key
        logger.info(f'Key up: key={key_name} code={code}')
        await self._execute_command(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_UP,
                key=key_name,
                windows_virtual_key_code=code,
                native_virtual_key_code=code,
            )
        )

    async def press_keyboard_key(
        self,
        key: Key,
        modifiers: Optional[KeyModifier] = None,
        interval: float = 0.1,
    ):
        """
        Press and release keyboard key with configurable timing.

        .. deprecated::
            This method is deprecated. Use ``tab.keyboard.press()`` instead.

        Better for special keys (Enter, Tab, etc.) than type_text().
        """
        warnings.warn(
            'WebElement.press_keyboard_key() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.press(key, modifiers, interval)',
            DeprecationWarning,
            stacklevel=2,
        )
        await self.key_down(key, modifiers)
        await asyncio.sleep(interval)
        await self.key_up(key)

    async def is_editable(self) -> bool:
        """
        Check if element can accept text input.

        Returns:
            True if element is editable (input, textarea, or contenteditable).
        """
        result = await self.execute_script(Scripts.IS_EDITABLE, return_by_value=True)
        is_editable = result['result']['result']['value']
        logger.debug(f'Element editable check: {is_editable}')
        return is_editable

    async def is_visible(self):
        """Check if element is visible using comprehensive JavaScript visibility test."""
        result = await self.execute_script(Scripts.ELEMENT_VISIBLE, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def is_on_top(self):
        """Check if element is topmost at its center point (not covered by overlays)."""
        result = await self.execute_script(Scripts.ELEMENT_ON_TOP, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def is_interactable(self):
        """Check if element is interactable based on visibility and position."""
        result = await self.execute_script(Scripts.ELEMENT_INTERACTIVE, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def execute_script(
        self,
        script: str,
        *,
        arguments: Optional[list[CallArgument]] = None,
        silent: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        throw_on_side_effect: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> CallFunctionOnResponse:
        """
        Execute JavaScript in element context.

        Args:
            script (str): JavaScript code to execute. Use 'this' to reference this element.
            arguments (Optional[list[CallArgument]]): Arguments to pass to the function
                (Runtime.callFunctionOn).
            silent (Optional[bool]): Whether to silence exceptions (Runtime.callFunctionOn).
            return_by_value (Optional[bool]): Whether to return the result by value instead of
                reference (Runtime.callFunctionOn).
            generate_preview (Optional[bool]): Whether to generate a preview for the result
                (Runtime.callFunctionOn).
            user_gesture (Optional[bool]): Whether to treat the call as initiated by user
                gesture (Runtime.callFunctionOn).
            await_promise (Optional[bool]): Whether to await promise result
                (Runtime.callFunctionOn).
            execution_context_id (Optional[int]): ID of the execution context to call the
                function in (Runtime.callFunctionOn).
            object_group (Optional[str]): Symbolic group name for the result
                (Runtime.callFunctionOn).
            throw_on_side_effect (Optional[bool]): Whether to throw if side effect cannot be
                ruled out (Runtime.callFunctionOn).
            unique_context_id (Optional[str]): Unique context ID for the function call
                (Runtime.callFunctionOn).
            serialization_options (Optional[SerializationOptions]): Serialization options for
                the result (Runtime.callFunctionOn).

        Returns:
            CallFunctionOnResponse: The result of the script execution.

        Examples:
            # Click the element
            await element.execute_script('this.click()')

            # Modify element style
            await element.execute_script('this.style.border = "2px solid red"')

            # Get element text
            result = await element.execute_script('return this.textContent', return_by_value=True)

            # Set element content
            await element.execute_script('this.textContent = "Hello World"')
        """
        if not is_script_already_function(script):
            script = f'function(){{ {script} }}'

        logger.debug(
            f'Executing script on element: return_by_value={return_by_value}, '
            f'length={len(script)}, args={len(arguments) if arguments else 0}'
        )
        command = RuntimeCommands.call_function_on(
            function_declaration=script,
            object_id=self._object_id,
            arguments=arguments,
            silent=silent,
            return_by_value=return_by_value,
            generate_preview=generate_preview,
            user_gesture=user_gesture,
            await_promise=await_promise,
            execution_context_id=execution_context_id,
            object_group=object_group,
            throw_on_side_effect=throw_on_side_effect,
            unique_context_id=unique_context_id,
            serialization_options=serialization_options,
        )
        return await self._execute_command(command)

    def __repr__(self):
        """String representation showing attributes and object ID."""
        attrs = ', '.join(f'{k}={v!r}' for k, v in self._attributes.items())
        return f'{self.__class__.__name__}({attrs})(object_id={self._object_id})'

    def _is_inside_iframe(self) -> bool:
        """Check if this element is inside an iframe context (not the iframe itself)."""
        return self._iframe_context is not None and not self.is_iframe

    async def _get_iframe_inner_html(self) -> str:
        """Get inner HTML of an iframe element."""
        iframe_context = await self.iframe_context
        if iframe_context is None:
            raise InvalidIFrame('Unable to resolve iframe context')
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate(
                expression='document.documentElement.outerHTML',
                context_id=iframe_context.execution_context_id,
                return_by_value=True,
            )
        )
        return response['result']['result'].get('value', '')

    def _apply_routing_from_context(self) -> None:
        """Apply routing attributes from iframe context."""
        if hasattr(self, '_routing_session_handler'):
            delattr(self, '_routing_session_handler')
        if hasattr(self, '_routing_session_id'):
            delattr(self, '_routing_session_id')

    async def _click_option_tag(self):
        """Specialized method for clicking <option> elements in dropdowns."""
        await self._execute_command(
            RuntimeCommands.call_function_on(
                object_id=self._object_id,
                function_declaration=Scripts.CLICK_OPTION_TAG,
                return_by_value=True,
            )
        )

    async def _get_family_elements(
        self, script: str, max_depth: int = 1, tag_filter: list[str] = []
    ) -> list[WebElement]:
        """
        Retrieve all family elements of this element (elements at the same DOM level).

        Args:
            script (str): CDP script to execute for retrieving family elements.
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all family elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of family WebElement objects that share the same
                parent as this element and match the tag filter criteria.
        """
        result = await self.execute_script(
            script.format(tag_filter=tag_filter, max_depth=max_depth)
        )
        if not self._has_object_id_key(result):
            return []

        array_object_id = result['result']['result']['objectId']

        get_properties_command = RuntimeCommands.get_properties(object_id=array_object_id)
        properties_response: GetPropertiesResponse = await self._execute_command(
            get_properties_command
        )

        family_elements: list[WebElement] = []
        for prop in properties_response['result']['result']:
            if not (prop['name'].isdigit() and 'objectId' in prop['value']):
                continue
            child_object_id = prop['value']['objectId']
            attributes = await self._get_object_attributes(object_id=child_object_id)
            family_elements.append(
                WebElement(
                    child_object_id,
                    self._connection_handler,
                    attributes_list=attributes,
                    mouse=self._mouse,
                )
            )

        logger.debug(f'Family elements found: {len(family_elements)}')
        return family_elements

    def _def_attributes(self, attributes_list: list[str]):
        """Process flat attribute list into dictionary (renames 'class' to 'class_name')."""
        for i in range(0, len(attributes_list), 2):
            key = attributes_list[i]
            key = key if key != 'class' else 'class_name'
            value = attributes_list[i + 1]
            self._attributes[key] = value
        logger.debug(f'Attributes defined: count={len(self._attributes)}')

    def _is_option_tag(self):
        """Check if element is an <option> tag."""
        return self._attributes.get('tag_name', '').lower() == 'option'

    async def _is_option_element(self) -> bool:
        """
        Robust check for <option> elements, falling back to JS when tag_name is missing.
        """
        tag = self._attributes.get('tag_name', '')
        if tag:
            return tag.lower() == 'option'

        # Heuristic from original selector/method
        selector = str(getattr(self, '_selector', '') or '')
        method_raw = getattr(self, '_search_method', '')
        method = str(getattr(method_raw, 'value', method_raw) or '').lower()
        if method == 'tag_name' and selector.lower() == 'option':
            return True
        if method == 'xpath' and 'option' in selector.lower():
            return True

        result = await self.execute_script(Scripts.IS_OPTION_TAG, return_by_value=True)
        is_option = result.get('result', {}).get('result', {}).get('value', False)
        if is_option and not self._attributes.get('tag_name'):
            self._attributes['tag_name'] = 'option'
        return bool(is_option)

    @staticmethod
    def _calculate_center(bounds: list) -> tuple:
        """Calculate center point from bounding box coordinates."""
        x_values = [bounds[i] for i in range(0, len(bounds), 2)]
        y_values = [bounds[i] for i in range(1, len(bounds), 2)]
        x_center = sum(x_values) / len(x_values)
        y_center = sum(y_values) / len(y_values)
        return x_center, y_center
