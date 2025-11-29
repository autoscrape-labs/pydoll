from __future__ import annotations

import asyncio
import json
import logging
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

import aiofiles

from pydoll.commands import (
    DomCommands,
    InputCommands,
    PageCommands,
    RuntimeCommands,
    TargetCommands,
)
from pydoll.connection import ConnectionHandler
from pydoll.constants import (
    Key,
    Scripts,
)
from pydoll.elements.mixins import FindElementsMixin
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    InvalidFileExtension,
    InvalidIFrame,
    MissingScreenshotPath,
    WaitElementTimeout,
)
from pydoll.protocol.dom.methods import GetFrameOwnerResponse
from pydoll.protocol.dom.types import Node
from pydoll.protocol.input.types import (
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
)
from pydoll.protocol.page.methods import CreateIsolatedWorldResponse, GetFrameTreeResponse
from pydoll.protocol.page.types import Frame, FrameTree, ScreenshotFormat, Viewport
from pydoll.protocol.runtime.methods import (
    CallFunctionOnResponse,
    EvaluateResponse,
    GetPropertiesResponse,
    SerializationOptions,
)
from pydoll.protocol.runtime.types import CallArgument
from pydoll.protocol.target.methods import AttachToTargetResponse, GetTargetsResponse
from pydoll.utils import (
    decode_base64_to_bytes,
    extract_text_from_html,
    is_script_already_function,
    normalize_synthetic_xpath,
)


@dataclass
class _IFrameContext:
    frame_id: str
    document_url: Optional[str] = None
    execution_context_id: Optional[int] = None
    document_object_id: Optional[str] = None
    session_handler: Optional[ConnectionHandler] = None
    session_id: Optional[str] = None


if TYPE_CHECKING:
    from pydoll.protocol.dom.methods import (
        GetBoxModelResponse,
        GetOuterHTMLResponse,
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
    ):
        """
        Initialize WebElement wrapper.

        Args:
            object_id: Unique CDP object identifier for this DOM element.
            connection_handler: Connection instance for browser communication.
            method: Search method used to find this element (for debugging).
            selector: Selector string used to find this element (for debugging).
            attributes_list: Flat list of alternating attribute names and values.
        """
        self._object_id = object_id
        self._search_method = method
        self._selector = selector
        self._connection_handler = connection_handler
        self._attributes: dict[str, str] = {}
        self._def_attributes(attributes_list)
        self._iframe_context: Optional[_IFrameContext] = None
        logger.debug(
            f'WebElement initialized: object_id={self._object_id}, '
            f'method={self._search_method}, selector={self._selector}, '
            f'attributes={len(self._attributes)}'
        )

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
        text_in_iframe = await self._text_via_iframe_context()
        if text_in_iframe is not None:
            logger.debug(f'Extracted text length (iframe ctx): {len(text_in_iframe)}')
            return text_in_iframe

        outer_html = await self.inner_html
        text_value = extract_text_from_html(outer_html, strip=True)
        logger.debug(f'Extracted text length: {len(text_value)}')
        return text_value

    async def _text_via_iframe_context(self) -> Optional[str]:
        """
        Resolve textContent for elements inside an iframe by executing on the element itself.
        """
        iframe_ctx = getattr(self, '_iframe_context', None)
        if iframe_ctx is None or self.is_iframe:
            return None
        # Execute directly against this element to avoid selector ambiguity
        response_cf: CallFunctionOnResponse = await self.execute_script(
            'return (this.textContent || "").trim()', return_by_value=True
        )
        return response_cf.get('result', {}).get('result', {}).get('value', '') or ''

    @staticmethod
    def _build_text_expression(selector: str, method: str) -> Optional[str]:
        """
        Build JS expression using Scripts to extract textContent based on selector type.
        """
        raw = str(selector)
        method_lc = (method or '').lower()

        if 'xpath' in method_lc:
            normalized_xpath = normalize_synthetic_xpath(raw)
            escaped_xpath = normalized_xpath.replace('"', '\\"')
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', escaped_xpath)

        if method_lc == 'name':
            escaped_name = raw.replace('"', '\\"')
            xpath = f'//*[@name="{escaped_name}"]'
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', xpath)

        escaped = raw.replace('\\', '\\\\').replace('"', '\\"')
        if method_lc == 'id':
            css = f'#{escaped}'
        elif method_lc == 'class_name':
            css = f'.{escaped}'
        elif method_lc == 'tag_name':
            css = escaped
        else:
            css = escaped
        return Scripts.GET_TEXT_BY_CSS.replace('{selector}', css)

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
            iframe_context = await self.iframe_context
            if iframe_context is None:
                raise InvalidIFrame('Unable to resolve iframe context')
            response_evaluate: EvaluateResponse = await self._execute_command(
                RuntimeCommands.evaluate(
                    expression='document.documentElement.outerHTML',
                    context_id=iframe_context.execution_context_id,
                    return_by_value=True,
                )
            )
            return response_evaluate['result']['result'].get('value', '')

        iframe_ctx = getattr(self, '_iframe_context', None)
        if iframe_ctx is not None:
            response_cf: CallFunctionOnResponse = await self._execute_command(
                RuntimeCommands.call_function_on(
                    function_declaration='function(){ return this.outerHTML }',
                    object_id=self._object_id,
                    return_by_value=True,
                )
            )
            return response_cf.get('result', {}).get('result', {}).get('value', '')

        command = DomCommands.get_outer_html(object_id=self._object_id)
        response_get_outer_html: GetOuterHTMLResponse = await self._execute_command(command)
        return response_get_outer_html['result']['outerHTML']

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
        return WebElement(object_id, self._connection_handler, attributes_list=attributes)

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
    ):
        """
        Click element using simulated mouse events.

        Args:
            x_offset: Horizontal offset from element center.
            y_offset: Vertical offset from element center.
            hold_time: Duration to hold mouse button down.

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
                element_bounds_js['x'] + element_bounds_js['width'] / 2,
                element_bounds_js['y'] + element_bounds_js['height'] / 2,
            )
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
        await self._connection_handler.execute_command(press_command)
        await asyncio.sleep(hold_time)
        await self._connection_handler.execute_command(release_command)

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

    async def type_text(self, text: str, interval: float = 0.1):
        """
        Type text character by character with realistic timing.

        More realistic than insert_text() but slower.
        """
        logger.info(f'Typing text (length={len(text)}, interval={interval}s)')
        await self.click()
        for char in text:
            await self._execute_command(
                InputCommands.dispatch_key_event(
                    type=KeyEventType.CHAR,
                    text=char,
                )
            )
            await asyncio.sleep(interval)

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

    async def _click_option_tag(self):
        """Specialized method for clicking <option> elements in dropdowns."""
        await self._execute_command(
            RuntimeCommands.call_function_on(
                object_id=self._object_id,
                function_declaration=Scripts.CLICK_OPTION_TAG,
                return_by_value=True,
            )
        )

    @property
    async def iframe_context(self) -> Optional[_IFrameContext]:
        """
        Return the resolved iframe context for this element when it is an <iframe>.

        The context includes: frame_id, document_url, execution_context_id,
        document_object_id and, for OOPIF targets, the session_id and
        session_handler used for routing commands. The first call resolves and
        caches the context. Non-iframe elements return None.

        Returns:
            _IFrameContext | None: Cached iframe context or None for non-iframes.
        """
        if not self.is_iframe:
            return None

        if self._iframe_context:
            return self._iframe_context

        await self._ensure_iframe_context()
        return self._iframe_context

    @staticmethod
    async def _get_frame_tree_for(
        handler: ConnectionHandler, session_id: Optional[str]
    ) -> FrameTree:
        """
        Get the Page frame tree for the given connection/target.

        Args:
            handler (ConnectionHandler): Connection to execute the command on.
            session_id (str | None): Target session id (flattened mode). When
                provided, the command is routed to that target.

        Returns:
            FrameTree: Frame tree returned by Page.getFrameTree.
        """
        command = PageCommands.get_frame_tree()
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameTreeResponse = await handler.execute_command(command)
        return response['result']['frameTree']

    @staticmethod
    def _walk_frames(tree: FrameTree) -> Iterable[Frame]:
        """
        Recursively traverse a FrameTree and collect all frame descriptors.

        Args:
            tree (FrameTree): Root frame tree node.

        Returns:
            Iterable[Frame]: Sequence of frame dictionaries (root first).
        """
        if not tree:
            return []
        frames: list[Frame] = [tree['frame']]
        for child_frame in tree.get('childFrames', []) or []:
            frames.extend(WebElement._walk_frames(child_frame))
        return [frame_node for frame_node in frames if frame_node]

    @staticmethod
    async def _owner_backend_for(
        handler: ConnectionHandler, session_id: Optional[str], frame_id: str
    ) -> Optional[int]:
        """
        Get the backendNodeId of the DOM element that owns the given frame.

        Args:
            handler (ConnectionHandler): Connection used to execute the command.
            session_id (str | None): Optional session id to route to the target.
            frame_id (str): Frame id to query.

        Returns:
            int | None: backendNodeId of the owner iframe element, or None.
        """
        command = DomCommands.get_frame_owner(frame_id=frame_id)
        if session_id:
            command['sessionId'] = session_id
        response: GetFrameOwnerResponse = await handler.execute_command(command)
        return response.get('result', {}).get('backendNodeId')

    async def _find_frame_by_owner(
        self, handler: ConnectionHandler, session_id: Optional[str], backend_node_id: int
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Find a frame by matching the owner backend_node_id of the <iframe> element.

        Args:
            handler (ConnectionHandler): Connection used to query Page/DOM.
            session_id (str | None): Optional session id used for routing.
            backend_node_id (int): Backend node id of the iframe element.

        Returns:
            tuple[str | None, str | None]: (frame_id, frame_url) or (None, None).
        """
        frame_tree = await self._get_frame_tree_for(handler, session_id)
        for frame_node in WebElement._walk_frames(frame_tree):
            candidate_frame_id = frame_node.get('id', '')
            if not candidate_frame_id:
                continue
            owner_backend_id = await self._owner_backend_for(
                handler, session_id, candidate_frame_id
            )
            if owner_backend_id == backend_node_id:
                return candidate_frame_id, frame_node.get('url')
        return None, None

    @staticmethod
    def _find_child_by_parent(tree: FrameTree, parent_id: str) -> Optional[str]:
        """
        Find the id of a child frame whose parentId equals the given one.

        Args:
            tree (FrameTree): Root frame tree node.
            parent_id (str): Parent frame id to match.

        Returns:
            str | None: Child frame id or None if not found.
        """
        if not tree:
            return None
        for child in tree.get('childFrames', []) or []:
            cframe = child.get('frame', {})
            if cframe.get('parentId') == parent_id:
                return cframe.get('id')
            found = WebElement._find_child_by_parent(child, parent_id)
            if found:
                return found
        return None

    async def _resolve_oopif_by_parent(
        self,
        parent_frame_id: str,
        backend_node_id: Optional[int],
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """
        Resolve an out-of-process iframe (OOPIF) using the given parent frame id.

        Strategy:
        - Try to attach to a direct child target whose parentFrameId matches.
        - Otherwise attach to targets and either:
          - find a child frame with matching parentId, or
          - match the root frame whose owner equals backend_node_id.

        Args:
            parent_frame_id (str): Parent frame id the iframe belongs to.
            backend_node_id (int | None): Backend node id of the iframe element.

        Returns:
            tuple[ConnectionHandler | None, str | None, str | None, str | None]:
                (session_handler, session_id, frame_id, document_url).
        """
        browser_handler = ConnectionHandler(
            connection_port=self._connection_handler._connection_port
        )
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )
        target_infos = targets_response.get('result', {}).get('targetInfos', [])

        direct_children = [
            target_info
            for target_info in target_infos
            if target_info.get('type') in {'iframe', 'page'}
            and target_info.get('parentFrameId') == parent_frame_id
        ]

        is_single_child = len(direct_children) == 1
        for child_target in direct_children:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=child_target['targetId'], flatten=True)
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue

            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            if is_single_child and root_frame_id and backend_node_id is None:
                return (
                    browser_handler,
                    attached_session_id,
                    root_frame_id,
                    root_frame.get('url'),
                )

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    self._connection_handler, None, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

        for target_info in target_infos:
            if target_info.get('type') not in {'iframe', 'page'}:
                continue
            attach_response = await browser_handler.execute_command(
                TargetCommands.attach_to_target(
                    target_id=target_info.get('targetId', ''), flatten=True
                )
            )
            attached_session_id = attach_response.get('result', {}).get('sessionId')
            if not attached_session_id:
                continue
            frame_tree = await self._get_frame_tree_for(browser_handler, attached_session_id)
            root_frame = (frame_tree or {}).get('frame', {})
            root_frame_id = root_frame.get('id', '')

            if root_frame_id and backend_node_id is not None:
                owner_backend_id = await self._owner_backend_for(
                    self._connection_handler, None, root_frame_id
                )
                if owner_backend_id == backend_node_id:
                    return (
                        browser_handler,
                        attached_session_id,
                        root_frame_id,
                        root_frame.get('url'),
                    )

            child_frame_id = WebElement._find_child_by_parent(frame_tree, parent_frame_id)
            if child_frame_id:
                return browser_handler, attached_session_id, child_frame_id, None

        return None, None, None, None

    @staticmethod
    def _extract_frame_metadata(
        node_info: Node,
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
        """
        Extract iframe-related metadata from a DOM.describeNode Node.task

        Args:
            node_info (Node): DOM node information of the iframe element.

        Returns:
            tuple[str | None, str | None, str | None, int | None]:
                (frame_id, document_url, parent_frame_id, backend_node_id).
        """
        content_document = node_info.get('contentDocument') or {}
        parent_frame_id = node_info.get('frameId')
        backend_node_id = node_info.get('backendNodeId')
        frame_id = content_document.get('frameId')
        document_url = (
            content_document.get('documentURL')
            or content_document.get('baseURL')
            or node_info.get('documentURL')
            or node_info.get('baseURL')
        )
        return frame_id, document_url, parent_frame_id, backend_node_id

    def _get_base_session(self) -> tuple[ConnectionHandler, Optional[str]]:
        """
        Return the default handler and session id for routing commands.

        Prefers a routing handler/session inherited from a parent iframe, otherwise
        falls back to this element's connection handler.

        Returns:
            tuple[ConnectionHandler, str | None]: (handler, session_id).
        """
        handler = getattr(self, '_routing_session_handler', None) or self._connection_handler
        session_id = getattr(self, '_routing_session_id', None)
        return handler, session_id

    async def _resolve_frame_by_owner(
        self,
        base_handler: ConnectionHandler,
        base_session_id: Optional[str],
        backend_node_id: int,
        current_document_url: Optional[str],
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve a frame id and URL by matching the owner backend_node_id.

        Args:
            base_handler (ConnectionHandler): Connection used to query Page/DOM.
            base_session_id (str | None): Optional session id for routing.
            backend_node_id (int): Backend node id of the iframe element.
            current_document_url (str | None): Current best-known document URL.

        Returns:
            tuple[str | None, str | None]: (frame_id, document_url) or (None, url).
        """
        owner_frame_id, owner_url = await self._find_frame_by_owner(
            base_handler, base_session_id, backend_node_id
        )
        if not owner_frame_id:
            return None, current_document_url
        return owner_frame_id, owner_url or current_document_url

    async def _resolve_oopif_if_needed(
        self,
        current_frame_id: Optional[str],
        parent_frame_id: Optional[str],
        backend_node_id: Optional[int],
        current_document_url: Optional[str],
    ) -> tuple[Optional[ConnectionHandler], Optional[str], Optional[str], Optional[str]]:
        """
        Resolve OOPIF and routing when needed.

        For cross-origin iframes (OOPIFs), commands must be routed to the OOPIF's
        target using a sessionId. For same-origin iframes, use the frame_id directly.

        Args:
            current_frame_id (str | None): Already known frame id, if any.
            parent_frame_id (str | None): Parent frame id used to search children.
            backend_node_id (int | None): Backend node id of the iframe element.
            current_document_url (str | None): Current best-known document URL.

        Returns:
            tuple[ConnectionHandler | None, str | None, str | None, str | None]:
                (session_handler, session_id, frame_id, document_url).
        """
        if not parent_frame_id or (current_frame_id and backend_node_id is None):
            return None, None, current_frame_id, current_document_url

        (
            session_handler,
            session_id,
            resolved_frame_id,
            resolved_url,
        ) = await self._resolve_oopif_by_parent(parent_frame_id, backend_node_id)

        if session_handler and session_id and resolved_url:
            return (
                session_handler,
                session_id,
                resolved_frame_id or current_frame_id,
                resolved_url or current_document_url,
            )

        return (
            None,
            None,
            current_frame_id or resolved_frame_id,
            current_document_url or resolved_url,
        )

    def _init_iframe_context(
        self,
        frame_id: str,
        document_url: Optional[str],
        session_handler: Optional[ConnectionHandler],
        session_id: Optional[str],
    ) -> None:
        """
        Initialize and cache iframe context on this element.

        Args:
            frame_id (str): Resolved frame id of the iframe document.
            document_url (str | None): Resolved document URL of the iframe.
            session_handler (ConnectionHandler | None): OOPIF target handler, if any.
            session_id (str | None): OOPIF target session id, if any.
        """
        self._iframe_context = _IFrameContext(frame_id=frame_id, document_url=document_url)
        if hasattr(self, '_routing_session_handler'):
            delattr(self, '_routing_session_handler')
        if hasattr(self, '_routing_session_id'):
            delattr(self, '_routing_session_id')
        if session_handler and session_id:
            self._iframe_context.session_handler = session_handler
            self._iframe_context.session_id = session_id

    @staticmethod
    async def _create_isolated_world_for_frame(
        frame_id: str,
        handler: ConnectionHandler,
        session_id: Optional[str],
    ) -> int:
        """
        Create an isolated world (Page.createIsolatedWorld) for the given frame.

        Args:
            frame_id (str): Target frame id to create the isolated world in.
            handler (ConnectionHandler): Connection used to execute the command.
            session_id (str | None): Optional session id to route the command.

        Returns:
            int: Execution context id for the created isolated world.

        Raises:
            InvalidIFrame: If the isolated world could not be created.
        """
        create_command = PageCommands.create_isolated_world(
            frame_id=frame_id,
            world_name=f'pydoll::iframe::{frame_id}',
            grant_universal_access=True,
        )
        if session_id:
            create_command['sessionId'] = session_id
        create_response: CreateIsolatedWorldResponse = await handler.execute_command(create_command)
        execution_context_id = create_response.get('result', {}).get('executionContextId')
        if not execution_context_id:
            raise InvalidIFrame('Unable to create isolated world for iframe')
        return execution_context_id

    async def _set_iframe_document_object_id(self, execution_context_id: int) -> None:
        """
        Evaluate document.documentElement in the iframe context and cache its object id.

        Args:
            execution_context_id (int): Execution context id for the iframe document.

        Raises:
            InvalidIFrame: If the document object id cannot be obtained.
        """
        evaluate_command = RuntimeCommands.evaluate(
            expression='document.documentElement',
            context_id=execution_context_id,
        )
        if self._iframe_context and self._iframe_context.session_id:
            evaluate_command['sessionId'] = self._iframe_context.session_id
        evaluate_response: EvaluateResponse = await (
            (self._iframe_context.session_handler if self._iframe_context else None)
            or self._connection_handler
        ).execute_command(evaluate_command)
        result_object = evaluate_response.get('result', {}).get('result', {})
        document_object_id = result_object.get('objectId')
        if not document_object_id:
            raise InvalidIFrame('Unable to obtain document reference for iframe')
        if self._iframe_context:
            self._iframe_context.document_object_id = document_object_id

    async def _ensure_iframe_context(self) -> None:
        """
        Initialize and cache context information for iframe elements.

        Populates frame id, document URL, execution context and document object id.
        """
        node_info = await self._describe_node(object_id=self._object_id)
        base_handler, base_session_id = self._get_base_session()
        frame_id, document_url, parent_frame_id, backend_node_id = self._extract_frame_metadata(
            node_info
        )

        if not frame_id and backend_node_id is not None:
            frame_id, document_url = await self._resolve_frame_by_owner(
                base_handler, base_session_id, backend_node_id, document_url
            )

        (
            session_handler,
            session_id,
            frame_id,
            document_url,
        ) = await self._resolve_oopif_if_needed(
            frame_id, parent_frame_id, backend_node_id, document_url
        )

        if not frame_id:
            raise InvalidIFrame('Unable to resolve frameId for the iframe element')

        self._init_iframe_context(frame_id, document_url, session_handler, session_id)

        effective_handler = session_handler or base_handler
        effective_session_id = session_id or base_session_id
        execution_context_id = await self._create_isolated_world_for_frame(
            frame_id, effective_handler, effective_session_id
        )
        if self._iframe_context:
            self._iframe_context.execution_context_id = execution_context_id

        await self._set_iframe_document_object_id(execution_context_id)

    async def is_visible(self):
        """Check if element is visible using comprehensive JavaScript visibility test."""
        result = await self.execute_script(Scripts.ELEMENT_VISIBLE, return_by_value=True)
        return bool(result['result']['result']['value'])

    async def is_on_top(self):
        """Check if element is topmost at its center point (not covered by overlays)."""
        result = await self.execute_script(Scripts.ELEMENT_ON_TOP, return_by_value=True)
        return result['result']['result']['value']

    async def is_interactable(self):
        """Check if element is interactable based on visibility and position."""
        result = await self.execute_script(Scripts.ELEMENT_INTERACTIVE, return_by_value=True)
        return result['result']['result']['value']

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
                WebElement(child_object_id, self._connection_handler, attributes_list=attributes)
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

    def __repr__(self):
        """String representation showing attributes and object ID."""
        attrs = ', '.join(f'{k}={v!r}' for k, v in self._attributes.items())
        return f'{self.__class__.__name__}({attrs})(object_id={self._object_id})'
