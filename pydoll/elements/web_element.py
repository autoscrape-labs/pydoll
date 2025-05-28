import asyncio
import json
from typing import Dict, List, Optional

import aiofiles
from bs4 import BeautifulSoup

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
from pydoll.utils import decode_base64_to_bytes


class WebElement(FindElementsMixin):  # noqa: PLR0904
    """
    Represents and interacts with DOM elements in the browser.

    The WebElement class provides comprehensive functionality for manipulating,
    inspecting, and interacting with DOM elements in web pages. It offers methods
    for common operations like clicking, typing, and element state inspection,
    along with more advanced capabilities like JavaScript execution in the element's
    context and element screenshots.

    This class implements the FindElementsMixin to allow finding child elements
    within the context of this element, enabling efficient DOM traversal.

    Key capabilities include:
    1. Element property access (text, bounds, HTML)
    2. User interactions (click, type, key presses)
    3. Element state inspection (visibility, attributes)
    4. Element screenshots
    5. JavaScript execution in element context
    6. File input handling

    The implementation uses Chrome DevTools Protocol commands to communicate
    directly with the browser, providing more reliable and powerful interactions
    than traditional WebDriver approaches.
    """

    def __init__(
        self,
        object_id: str,
        connection_handler: ConnectionHandler,
        method: Optional[str] = None,
        selector: Optional[str] = None,
        attributes_list: List[str] = [],
    ):
        """
        Initializes a new WebElement instance.

        Creates a wrapper for a DOM element identified by its CDP object ID,
        providing methods to interact with and inspect the element. The element's
        attributes are parsed from the attribute list provided by the browser.

        Args:
            object_id: Unique CDP object identifier for this DOM element.
                This ID is used in subsequent CDP commands targeting this element.
            connection_handler: Connection instance for communicating with the browser.
                Used to send commands and receive responses.
            method: Search method used to find this element (e.g., CSS_SELECTOR, XPATH).
                Stored for debugging and reference purposes.
            selector: The selector string used to find this element.
                Stored for debugging and reference purposes.
            attributes_list: Flat list of alternating attribute names and values
                from the browser. Processed into a dictionary during initialization.
        """
        self._object_id = object_id
        self._search_method = method
        self._selector = selector
        self._connection_handler = connection_handler
        self._attributes: Dict[str, str] = {}
        self._def_attributes(attributes_list)

    @property
    def value(self) -> Optional[str]:
        """
        Gets the value attribute of the element.

        Retrieves the current value of form elements like inputs, textareas,
        and select elements. For other elements, returns None or the value
        attribute if present.

        Returns:
            str or None: The element's value attribute if present, otherwise None.
        """
        return self._attributes.get('value')

    @property
    def class_name(self) -> Optional[str]:
        """
        Gets the CSS class name(s) of the element.

        Provides access to the element's class attribute, which may contain
        multiple space-separated class names in the original HTML.

        Returns:
            str or None: The element's class attribute if present, otherwise None.
        """
        return self._attributes.get('class_name')

    @property
    def id(self) -> Optional[str]:
        """
        Gets the ID attribute of the element.

        Retrieves the unique identifier assigned to the element in the HTML.

        Returns:
            str or None: The element's id attribute if present, otherwise None.
        """
        return self._attributes.get('id')

    @property
    def tag_name(self) -> Optional[str]:
        """
        Gets the HTML tag name of the element.

        Returns:
            str or None: The element's tag name if present, otherwise None.
        """
        return self._attributes.get('tag_name')

    @property
    def is_enabled(self) -> bool:
        """
        Determines if the element is enabled for interaction.

        Checks if the element is enabled by verifying the absence of the
        'disabled' attribute. This is primarily relevant for form controls
        like inputs, buttons, and select elements.

        Returns:
            bool: True if the element is enabled (not disabled),
                False if it has the 'disabled' attribute.
        """
        return bool('disabled' not in self._attributes.keys())

    @property
    async def text(self) -> str:
        """
        Gets the visible text content of the element.

        Retrieves the element's inner HTML and uses BeautifulSoup to extract
        the visible text content, stripping whitespace. This provides a clean
        representation of the text a user would see in the browser.

        Returns:
            str: The visible text content of the element.

        Note:
            This is an async property that requires awaiting.
        """
        outer_html = await self.inner_html
        soup = BeautifulSoup(outer_html, 'html.parser')
        return soup.get_text(strip=True)

    @property
    async def bounds(self) -> Quad:
        """
        Gets the precise bounding box coordinates of the element.

        Retrieves the element's content box coordinates using the CDP DOM.getBoxModel
        command. This provides exact positioning information useful for
        operations that need precise element geometry like screenshots and clicks.

        Returns:
            Quad: A list of eight coordinates representing the four corners
                of the element's content box, in the format:
                [x1, y1, x2, y2, x3, y3, x4, y4]

        Note:
            This is an async property that requires awaiting.
            The coordinates are in CSS pixels relative to the document origin.
        """
        command = DomCommands.get_box_model(object_id=self._object_id)
        response: GetBoxModelResponse = await self._execute_command(command)
        return response['result']['model']['content']

    @property
    async def inner_html(self) -> str:
        """
        Gets the HTML content of the element.

        Retrieves the element's outer HTML using the CDP DOM.getOuterHTML
        command. This includes the element itself and all its contents.

        Returns:
            str: The complete HTML representation of the element.

        Note:
            This is an async property that requires awaiting.
            Despite the name, this actually returns the outerHTML
            (including the element itself).
        """
        command = DomCommands.get_outer_html(object_id=self._object_id)
        response: GetOuterHTMLResponse = await self._execute_command(command)
        return response['result']['outerHTML']

    async def get_bounds_using_js(self) -> Dict[str, int]:
        """
        Gets the element's bounding rectangle using JavaScript.

        Executes JavaScript in the element's context to get its bounding
        client rectangle information using getBoundingClientRect(). This is
        an alternative to the bounds property that provides the data in a
        different format.

        Returns:
            Dict[str, int]: A dictionary containing the element's position and size:
                {
                    'x': Left position relative to viewport,
                    'y': Top position relative to viewport,
                    'width': Element width,
                    'height': Element height
                }

        Note:
            The coordinates are relative to the viewport, not the document.
            This method is sometimes more reliable than bounds for certain
            types of elements or in certain browser conditions.
        """
        response = await self._execute_script(Scripts.BOUNDS, return_by_value=True)
        return json.loads(response['result']['result']['value'])

    async def get_screenshot(self, path: str, quality: int = 100):
        """
        Captures a screenshot of just this element.

        Takes a screenshot of only this element by determining its position
        and dimensions, then using the CDP Page.captureScreenshot command
        with a clip region. The screenshot is saved to the specified path.

        Args:
            path: File path where the screenshot should be saved.
                The file extension determines the format.
            quality: Image quality from 0-100 for lossy formats like JPEG.
                Default is 100 (maximum quality).

        Note:
            This method automatically scrolls the element into view before
            taking the screenshot. The element must be visible in the viewport.
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
        Gets the value of a specific attribute on the element.

        Retrieves an attribute's value from the element's attribute dictionary,
        which is populated during element creation. This provides fast access
        to element attributes without additional browser communication.

        Args:
            name: The name of the attribute to retrieve.

        Returns:
            str or None: The value of the specified attribute if present,
                otherwise None.

        Note:
            This method only provides access to attributes available when
            the element was located. For dynamically changing attributes,
            consider using JavaScript execution.
        """
        return self._attributes.get(name)

    async def scroll_into_view(self):
        """
        Scrolls the element into the visible viewport.

        Uses the CDP DOM.scrollIntoViewIfNeeded command to ensure the element
        is visible in the browser viewport. This is automatically called by
        interaction methods like click(), but can be called explicitly if needed.

        Note:
            This command scrolls the minimum amount needed to make the element
            visible, which may mean the element is only partially in view
            (e.g., at the very bottom of the viewport).
        """
        command = DomCommands.scroll_into_view_if_needed(object_id=self._object_id)
        await self._execute_command(command)

    async def click_using_js(self):
        """
        Clicks the element using JavaScript click() method.

        Executes the native element.click() method via JavaScript in the element's
        context. This can be useful for clicking elements that are difficult to
        interact with using standard mouse events, such as elements with event
        listeners that intercept propagation.

        Raises:
            ElementNotVisible: If the element is not visible on the page.
            ElementNotInteractable: If the element couldn't be clicked
                (e.g., disabled or not in the DOM).

        Note:
            For <option> elements in <select> dropdowns, a specialized
            JavaScript approach is used to properly select the option.
            The element is automatically scrolled into view before clicking.
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
        Clicks the element using simulated mouse events.

        Simulates a real mouse interaction by calculating the element's center
        position (or a specified offset from center), then sending mouse press
        and release events at that location. This more closely mimics an actual
        user's mouse click than the JavaScript click() method.

        Args:
            x_offset: Horizontal pixel offset from the element's center.
                Positive values move right, negative values move left.
            y_offset: Vertical pixel offset from the element's center.
                Positive values move down, negative values move up.
            hold_time: Duration in seconds to hold the mouse button down
                between press and release events. Default is 0.1 seconds.

        Raises:
            ElementNotVisible: If the element is not visible on the page.

        Note:
            For <option> elements, this delegates to _click_option_tag() which
            uses a specialized JavaScript approach. The element is automatically
            scrolled into view before attempting to click.
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
            x=position_to_click[0],
            y=position_to_click[1],
            button=MouseButton.LEFT,
            click_count=1,
        )
        release_command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_RELEASED,
            x=position_to_click[0],
            y=position_to_click[1],
            button=MouseButton.LEFT,
            click_count=1,
        )
        await self._connection_handler.execute_command(press_command)
        await asyncio.sleep(hold_time)
        await self._connection_handler.execute_command(release_command)

    async def insert_text(self, text: str):
        """
        Inserts text into the element in a single operation.

        Uses the CDP Input.insertText command to directly insert the provided
        text into the focused element. This is faster than type_text() but
        doesn't simulate realistic typing behavior.

        Args:
            text: The text string to insert.

        Note:
            This method doesn't handle focus automatically - the element
            should already be focused (e.g., by clicking it first) for
            the text to be inserted in the right place.
        """
        await self._execute_command(InputCommands.insert_text(text))

    async def set_input_files(self, files: List[str]):
        """
        Sets file paths for a file input element.

        Uses the CDP DOM.setFileInputFiles command to programmatically set
        the selected files for a file input element, bypassing the need for
        native file selection dialogs.

        Args:
            files: List of absolute file paths to set as the input's value.
                These must be paths to files that exist on the system where
                the browser is running.

        Raises:
            ElementNotInteractable: If the element is not a file input element.
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
        Types text character by character with realistic timing.

        Simulates human typing by sending individual keypress events for each
        character with a configurable delay between keypresses. This more
        closely mimics real user typing than insert_text().

        Args:
            text: The text string to type.
            interval: Delay in seconds between each keypress.
                Default is 0.1 seconds (100ms).

        Note:
            This method is slower than insert_text() but provides more realistic
            typing behavior, which can be important for sites that have keystroke
            timing detection or that trigger events on individual keypresses.
        """
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
        Simulates pressing a keyboard key down.

        Sends a key down event for the specified key using the CDP Input.dispatchKeyEvent
        command. This can be used to simulate keyboard shortcuts by combining
        with modifiers or to hold down keys for extended periods.

        Args:
            key: Tuple of (key_name, key_code) representing the key to press.
                Constants are available in the Key enum.
            modifiers: Optional keyboard modifiers to apply (Shift, Ctrl, Alt, etc.).
                Constants are available in the KeyModifier enum.

        Note:
            This only sends the key down event without releasing the key.
            For complete keypresses, pair with key_up() or use press_keyboard_key().
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
        """
        Simulates releasing a keyboard key.

        Sends a key up event for the specified key using the CDP Input.dispatchKeyEvent
        command. This completes a keypress action started with key_down().

        Args:
            key: Tuple of (key_name, key_code) representing the key to release.
                Constants are available in the Key enum.

        Note:
            This should typically be called after a corresponding key_down()
            to complete the keypress action.
        """
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
        Simulates pressing and releasing a keyboard key.

        Combines key_down() and key_up() with a configurable delay to simulate
        a complete keypress action. This is useful for special keys like Enter,
        Tab, Escape, arrow keys, etc.

        Args:
            key: Tuple of (key_name, key_code) representing the key to press.
                Constants are available in the Key enum.
            modifiers: Optional keyboard modifiers to apply (Shift, Ctrl, Alt, etc.).
                Constants are available in the KeyModifier enum.
            interval: Delay in seconds between key down and key up events.
                Default is 0.1 seconds (100ms).

        Note:
            For typing text, prefer type_text() which is designed specifically
            for character input. This method is better for non-character keys.
        """
        await self.key_down(key, modifiers)
        await asyncio.sleep(interval)
        await self.key_up(key)

    async def _click_option_tag(self):
        """
        Specialized method to click <option> elements in <select> dropdowns.

        Uses JavaScript to properly select an option from a dropdown menu,
        since <option> elements can't be directly clicked with mouse events.

        Note:
            This is automatically called by click() and click_using_js()
            when clicking an option element.
        """
        script = Scripts.CLICK_OPTION_TAG.replace('{self.value}', self.value)
        await self._execute_command(RuntimeCommands.evaluate_script(script))

    async def _is_element_visible(self):
        """
        Determines if the element is visible in the viewport.

        Executes JavaScript to check if the element is visible by verifying:
        1. The element has a non-zero size
        2. The element has non-zero opacity
        3. The element has no hidden overflow
        4. The element and its ancestors have 'display' != 'none'
        5. The element and its ancestors have 'visibility' != 'hidden'

        Returns:
            bool: True if the element is visible, False otherwise.
        """
        result = await self._execute_script(Scripts.ELEMENT_VISIBLE, return_by_value=True)
        return result['result']['result']['value']

    async def _is_element_on_top(self):
        """
        Determines if the element is the topmost element at its center point.

        Executes JavaScript to check if the element is the topmost element
        at its center position using document.elementFromPoint(). This helps
        detect if the element is covered by other elements like overlays.

        Returns:
            bool: True if the element is the topmost element at its center,
                False if it's covered by another element.
        """
        result = await self._execute_script(Scripts.ELEMENT_ON_TOP, return_by_value=True)
        return result['result']['result']['value']

    async def _execute_script(self, script: str, return_by_value: bool = False):
        """
        Executes JavaScript in the context of this element.

        Uses the CDP Runtime.callFunctionOn command to execute JavaScript
        with this element as the 'this' context. This allows direct manipulation
        of the element using JavaScript.

        Args:
            script: JavaScript function to execute. The element will be available
                as 'this' within the script.
            return_by_value: If True, serializes the result value and returns it.
                If False, returns a remote object reference. Default is False.

        Returns:
            dict: The complete response from the browser, containing execution
                results and any returned values or object references.

        Note:
            This is a powerful but lower-level method. Most common operations
            are available through more convenient methods like click(),
            type_text(), etc.
        """
        return await self._execute_command(
            RuntimeCommands.call_function_on(
                object_id=self._object_id,
                function_declaration=script,
                return_by_value=return_by_value,
            )
        )

    def _def_attributes(self, attributes_list: List[str]):
        """
        Processes and stores element attributes from the browser.

        Converts a flat list of alternating attribute names and values into
        a dictionary for easier access. Handles special cases like renaming
        'class' to 'class_name' to avoid conflicts with Python keywords.

        Args:
            attributes_list: Flat list of alternating attribute names and values.
                Example: ['id', 'submit-button', 'class', 'btn primary', 'disabled', '']
        """
        for i in range(0, len(attributes_list), 2):
            key = attributes_list[i]
            key = key if key != 'class' else 'class_name'
            value = attributes_list[i + 1]
            self._attributes[key] = value

    def _is_option_tag(self):
        """
        Checks if this element is an <option> element.

        Determines if the element is an option in a select dropdown by
        checking its tag name.

        Returns:
            bool: True if the element is an <option> tag, False otherwise.
        """
        return self._attributes['tag_name'].lower() == 'option'

    @staticmethod  # TODO: move to utils
    def _calculate_center(bounds: list) -> tuple:
        """
        Calculates the center point coordinates of an element.

        Processes the coordinates from a bounding box (quad) to determine
        the element's center point, which is useful for positioning mouse
        events.

        Args:
            bounds: A list of 8 coordinates representing the 4 corners of
                the element's bounding box in the format [x1,y1,x2,y2,x3,y3,x4,y4].

        Returns:
            tuple: (x, y) coordinates of the element's center point.
        """
        x_values = [bounds[i] for i in range(0, len(bounds), 2)]
        y_values = [bounds[i] for i in range(1, len(bounds), 2)]
        x_center = sum(x_values) / len(x_values)
        y_center = sum(y_values) / len(y_values)
        return x_center, y_center

    def __repr__(self):
        """
        Creates a string representation of the WebElement.

        Generates a detailed representation including all attributes and the
        object ID, useful for debugging and logging.

        Returns:
            str: String representation of the WebElement showing its attributes
                and object ID.
        """
        attrs = ', '.join(f'{k}={v!r}' for k, v in self._attributes.items())
        return f'{self.__class__.__name__}({attrs})(object_id={self._object_id})'
