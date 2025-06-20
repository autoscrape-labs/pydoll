import asyncio
import json
from typing import Optional

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
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
    ScreenshotFormat,
    Scripts,
)
from pydoll.elements.mixins import FindElementsMixin
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotInteractable,
    ElementNotVisible,
)
from pydoll.protocol.dom.responses import (
    GetBoxModelResponse,
    GetOuterHTMLResponse,
)
from pydoll.protocol.dom.types import Quad
from pydoll.protocol.page.responses import CaptureScreenshotResponse
from pydoll.protocol.page.types import Viewport
from pydoll.utils import (
    decode_base64_to_bytes,
    extract_text_from_html,
)


class WebElement(FindElementsMixin):  # noqa: PLR0904
    """
    DOM element wrapper for browser automation.

    Provides comprehensive functionality for element interaction, inspection,
    and manipulation using Chrome DevTools Protocol commands.
    """

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
    def is_enabled(self) -> bool:
        """Whether element is enabled (not disabled)."""
        return bool('disabled' not in self._attributes.keys())

    @property
    async def text(self) -> str:
        """Visible text content of the element."""
        outer_html = await self.inner_html
        return extract_text_from_html(outer_html, strip=True)

    @property
    async def bounds(self) -> Quad:
        """
        Element's bounding box coordinates.

        Returns coordinates in CSS pixels relative to document origin.
        """
        command = DomCommands.get_box_model(object_id=self._object_id)
        response: GetBoxModelResponse = await self._execute_command(command)
        return response['result']['model']['content']

    @property
    async def inner_html(self) -> str:
        """Element's HTML content (actually returns outerHTML)."""
        command = DomCommands.get_outer_html(object_id=self._object_id)
        response: GetOuterHTMLResponse = await self._execute_command(command)
        return response['result']['outerHTML']

    async def get_bounds_using_js(self) -> dict[str, int]:
        """
        Get element bounds using JavaScript getBoundingClientRect().

        Returns coordinates relative to viewport (alternative to bounds property).
        """
        response = await self._execute_script(Scripts.BOUNDS, return_by_value=True)
        return json.loads(response['result']['result']['value'])

    async def take_screenshot(self, path: str, quality: int = 100):
        """
        Capture screenshot of this element only.

        Automatically scrolls element into view before capturing.
        """
        bounds = await self.get_bounds_using_js()
        clip = Viewport(
            x=bounds['x'],
            y=bounds['y'],
            width=bounds['width'],
            height=bounds['height'],
            scale=1,
        )
        screenshot: CaptureScreenshotResponse = await self._connection_handler.execute_command(
            PageCommands.capture_screenshot(
                format=ScreenshotFormat.JPEG, clip=clip, quality=quality
            )
        )
        async with aiofiles.open(path, 'wb') as file:
            image_bytes = decode_base64_to_bytes(screenshot['result']['data'])
            await file.write(image_bytes)

    def get_attribute(self, name: str) -> Optional[str]:
        """
        Get element attribute value.

        Note:
            Only provides attributes available when element was located.
            For dynamic attributes, consider using JavaScript execution.
        """
        return self._attributes.get(name)

    async def scroll_into_view(self):
        """Scroll element into visible viewport."""
        command = DomCommands.scroll_into_view_if_needed(object_id=self._object_id)
        await self._execute_command(command)

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

        if not await self._is_element_visible():
            raise ElementNotVisible()

        result = await self._execute_script(Scripts.CLICK, return_by_value=True)
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
        if self._is_option_tag():
            return await self._click_option_tag()

        if not await self._is_element_visible():
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
        Insert text in single operation (faster but less realistic than typing).

        Note:
            Element should already be focused for text to be inserted correctly.
        """
        await self._execute_command(InputCommands.insert_text(text))

    async def set_input_files(self, files: list[str]):
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
        await self._execute_command(
            DomCommands.set_file_input_files(files=files, object_id=self._object_id)
        )

    async def type_text(self, text: str, interval: float = 0.1):
        """
        Type text character by character with realistic timing.

        More realistic than insert_text() but slower.
        """
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

        Note:
            Only sends key down without release. Pair with key_up() for complete keypress.
        """
        key_name, code = key
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
        """Send key up event (should follow corresponding key_down())."""
        key_name, code = key
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

        Better for special keys (Enter, Tab, etc.) than type_text().
        """
        await self.key_down(key, modifiers)
        await asyncio.sleep(interval)
        await self.key_up(key)

    async def _click_option_tag(self):
        """Specialized method for clicking <option> elements in dropdowns."""
        script = Scripts.CLICK_OPTION_TAG.replace('{self.value}', self.value)
        await self._execute_command(RuntimeCommands.evaluate(script))

    async def _is_element_visible(self):
        """Check if element is visible using comprehensive JavaScript visibility test."""
        result = await self._execute_script(Scripts.ELEMENT_VISIBLE, return_by_value=True)
        return result['result']['result']['value']

    async def _is_element_on_top(self):
        """Check if element is topmost at its center point (not covered by overlays)."""
        result = await self._execute_script(Scripts.ELEMENT_ON_TOP, return_by_value=True)
        return result['result']['result']['value']

    async def _execute_script(self, script: str, return_by_value: bool = False):
        """
        Execute JavaScript in element context.

        Element is available as 'this' within the script.
        """
        return await self._execute_command(
            RuntimeCommands.call_function_on(
                object_id=self._object_id,
                function_declaration=script,
                return_by_value=return_by_value,
            )
        )

    def _def_attributes(self, attributes_list: list[str]):
        """Process flat attribute list into dictionary (renames 'class' to 'class_name')."""
        for i in range(0, len(attributes_list), 2):
            key = attributes_list[i]
            key = key if key != 'class' else 'class_name'
            value = attributes_list[i + 1]
            self._attributes[key] = value

    def _is_option_tag(self):
        """Check if element is an <option> tag."""
        return self._attributes['tag_name'].lower() == 'option'

    @staticmethod  # TODO: move to utils
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
