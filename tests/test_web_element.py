import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import json
import asyncio

from pydoll.exceptions import (
    ElementNotVisible,
    ElementNotInteractable,
    ElementNotFound,
    ElementNotAFileInput,
    WaitElementTimeout,
)
from pydoll.commands import (
    DomCommands,
    InputCommands,
    PageCommands,
    RuntimeCommands,
)
from pydoll.constants import (
    By,
    Key,
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
    ScreenshotFormat,
    Scripts,
)

from pydoll.elements.web_element import WebElement


@pytest_asyncio.fixture
async def mock_connection_handler():
    """Mock connection handler for WebElement tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        yield handler


@pytest.fixture
def web_element(mock_connection_handler):
    """Basic WebElement fixture with common attributes."""
    attributes_list = [
        'id', 'test-id',
        'class', 'test-class',
        'value', 'test-value',
        'tag_name', 'div',
        'type', 'text'
    ]
    return WebElement(
        object_id='test-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='#test',
        attributes_list=attributes_list,
    )


@pytest.fixture
def input_element(mock_connection_handler):
    """Input element fixture for form-related tests."""
    attributes_list = [
        'id', 'input-id',
        'tag_name', 'input',
        'type', 'text',
        'value', 'initial-value'
    ]
    return WebElement(
        object_id='input-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='input[type="text"]',
        attributes_list=attributes_list,
    )


@pytest.fixture
def file_input_element(mock_connection_handler):
    """File input element fixture for file upload tests."""
    attributes_list = [
        'id', 'file-input-id',
        'tag_name', 'input',
        'type', 'file'
    ]
    return WebElement(
        object_id='file-input-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='input[type="file"]',
        attributes_list=attributes_list,
    )


@pytest.fixture
def option_element(mock_connection_handler):
    """Option element fixture for dropdown tests."""
    attributes_list = [
        'tag_name', 'option',
        'value', 'option-value',
        'id', 'option-id'
    ]
    return WebElement(
        object_id='option-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='option[value="option-value"]',
        attributes_list=attributes_list,
    )


@pytest.fixture
def disabled_element(mock_connection_handler):
    """Disabled element fixture for testing enabled/disabled state."""
    attributes_list = [
        'id', 'disabled-id',
        'tag_name', 'button',
        'disabled', 'true'
    ]
    return WebElement(
        object_id='disabled-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='button:disabled',
        attributes_list=attributes_list,
    )


class TestWebElementInitialization:
    """Test WebElement initialization and basic properties."""

    def test_web_element_initialization(self, web_element):
        """Test basic WebElement initialization."""
        assert web_element._object_id == 'test-object-id'
        assert web_element._search_method == 'css'
        assert web_element._selector == '#test'
        assert web_element._attributes == {
            'id': 'test-id',
            'class_name': 'test-class',
            'value': 'test-value',
            'tag_name': 'div',
            'type': 'text'
        }

    def test_web_element_initialization_empty_attributes(self, mock_connection_handler):
        """Test WebElement initialization with empty attributes list."""
        element = WebElement(
            object_id='empty-id',
            connection_handler=mock_connection_handler,
            attributes_list=[]
        )
        assert element._attributes == {}
        assert element._search_method is None
        assert element._selector is None

    def test_web_element_initialization_odd_attributes(self, mock_connection_handler):
        """Test WebElement initialization with odd number of attributes (causes IndexError)."""
        attributes_list = ['id', 'test-id', 'class']  # Missing value for 'class'
        
        # This should raise IndexError because _def_attributes doesn't handle odd lists
        with pytest.raises(IndexError):
            WebElement(
                object_id='odd-id',
                connection_handler=mock_connection_handler,
                attributes_list=attributes_list
            )

    def test_class_attribute_renamed_to_class_name(self, mock_connection_handler):
        """Test that 'class' attribute is renamed to 'class_name'."""
        attributes_list = ['class', 'my-class', 'id', 'my-id']
        element = WebElement(
            object_id='class-test',
            connection_handler=mock_connection_handler,
            attributes_list=attributes_list
        )
        assert 'class' not in element._attributes
        assert element._attributes['class_name'] == 'my-class'
        assert element._attributes['id'] == 'my-id'


class TestWebElementProperties:
    """Test WebElement properties and getters."""

    def test_basic_properties(self, web_element):
        """Test basic property accessors."""
        assert web_element.value == 'test-value'
        assert web_element.class_name == 'test-class'
        assert web_element.id == 'test-id'
        assert web_element.tag_name == 'div'

    def test_is_enabled_property(self, web_element, disabled_element):
        """Test is_enabled property for enabled and disabled elements."""
        assert web_element.is_enabled is True
        assert disabled_element.is_enabled is False

    def test_properties_with_none_values(self, mock_connection_handler):
        """Test properties when attributes are not present."""
        element = WebElement(
            object_id='empty-element',
            connection_handler=mock_connection_handler,
            attributes_list=[]
        )
        assert element.value is None
        assert element.class_name is None
        assert element.id is None
        assert element.tag_name is None
        assert element.is_enabled is True  # No 'disabled' attribute means enabled

    @pytest.mark.asyncio
    async def test_text_property(self, web_element):
        """Test text property extraction from HTML."""
        test_html = '<div>Hello <span>World</span></div>'
        web_element._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': test_html}
        }

        text = await web_element.text
        assert text == 'HelloWorld'  # BeautifulSoup strips spaces between elements

    @pytest.mark.asyncio
    async def test_text_property_with_nested_elements(self, web_element):
        """Test text property with complex nested HTML."""
        test_html = '<div>Text <b>Bold</b> <i>Italic</i> More text</div>'
        web_element._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': test_html}
        }

        text = await web_element.text
        assert text == 'TextBoldItalicMore text'  # BeautifulSoup strips spaces between elements

    @pytest.mark.asyncio
    async def test_bounds_property(self, web_element):
        """Test bounds property returns correct coordinates."""
        expected_bounds = [0, 0, 100, 100, 100, 100, 0, 100]
        web_element._connection_handler.execute_command.return_value = {
            'result': {'model': {'content': expected_bounds}}
        }

        bounds = await web_element.bounds
        assert bounds == expected_bounds

    @pytest.mark.asyncio
    async def test_inner_html_property(self, web_element):
        """Test inner_html property returns outer HTML."""
        expected_html = '<div class="test">Content</div>'
        web_element._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': expected_html}
        }

        html = await web_element.inner_html
        assert html == expected_html


class TestWebElementMethods:
    """Test WebElement methods and interactions."""

    def test_get_attribute(self, web_element):
        """Test get_attribute method."""
        assert web_element.get_attribute('id') == 'test-id'
        assert web_element.get_attribute('class_name') == 'test-class'
        assert web_element.get_attribute('nonexistent') is None

    @pytest.mark.asyncio
    async def test_get_bounds_using_js(self, web_element):
        """Test JavaScript-based bounds calculation."""
        expected_bounds = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        web_element._connection_handler.execute_command.return_value = {
            'result': {'result': {'value': json.dumps(expected_bounds)}}
        }

        bounds = await web_element.get_bounds_using_js()
        assert bounds == expected_bounds

    @pytest.mark.asyncio
    async def test_scroll_into_view(self, web_element):
        """Test scroll_into_view method."""
        await web_element.scroll_into_view()
        web_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_text(self, input_element):
        """Test insert_text method."""
        test_text = 'Hello World'
        await input_element.insert_text(test_text)
        
        input_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_type_text(self, input_element):
        """Test type_text method with character-by-character typing."""
        test_text = 'Hi'
        input_element.click = AsyncMock()
        with patch('asyncio.sleep') as mock_sleep:
            await input_element.type_text(test_text, interval=0.05)

        # Should call execute_command for each character
        assert input_element._connection_handler.execute_command.call_count == len(test_text)
        assert input_element.click.call_count == 1
        
        # Verify sleep was called between characters
        assert mock_sleep.call_count == len(test_text)
        mock_sleep.assert_called_with(0.05)

    @pytest.mark.asyncio
    async def test_type_text_default_interval(self, input_element):
        """Test type_text with default interval."""
        test_text = 'A'
        input_element.click = AsyncMock()
        with patch('asyncio.sleep') as mock_sleep:
            await input_element.type_text(test_text)

        mock_sleep.assert_called_with(0.1)  # Default interval
        assert input_element.click.call_count == 1


class TestWebElementKeyboardInteraction:
    """Test keyboard interaction methods."""

    @pytest.mark.asyncio
    async def test_key_down(self, web_element):
        """Test key_down method."""
        key = Key.ENTER
        modifiers = KeyModifier.CTRL
        
        await web_element.key_down(key, modifiers)
        
        web_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_key_down_without_modifiers(self, web_element):
        """Test key_down without modifiers."""
        key = Key.TAB
        
        await web_element.key_down(key)
        
        web_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_key_up(self, web_element):
        """Test key_up method."""
        key = Key.ESCAPE
        
        await web_element.key_up(key)
        
        web_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_press_keyboard_key(self, web_element):
        """Test press_keyboard_key method (key down + up)."""
        key = Key.SPACE
        modifiers = KeyModifier.SHIFT
        
        with patch('asyncio.sleep') as mock_sleep:
            await web_element.press_keyboard_key(key, modifiers, interval=0.05)
        
        # Should call key_down and key_up
        assert web_element._connection_handler.execute_command.call_count == 2
        mock_sleep.assert_called_once_with(0.05)

    @pytest.mark.asyncio
    async def test_press_keyboard_key_default_interval(self, web_element):
        """Test press_keyboard_key with default interval."""
        key = Key.ENTER
        
        with patch('asyncio.sleep') as mock_sleep:
            await web_element.press_keyboard_key(key)
        
        mock_sleep.assert_called_once_with(0.1)


class TestWebElementClicking:
    """Test clicking methods and behaviors."""

    @pytest.mark.asyncio
    async def test_click_using_js_success(self, web_element):
        """Test successful JavaScript click."""
        # Mock element visibility and click success
        web_element._is_element_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': True}}}
        )
        
        await web_element.click_using_js()
        
        web_element.scroll_into_view.assert_called_once()
        web_element._is_element_visible.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_using_js_not_visible(self, web_element):
        """Test JavaScript click when element is not visible."""
        web_element._is_element_visible = AsyncMock(return_value=False)
        web_element.scroll_into_view = AsyncMock()

        with pytest.raises(ElementNotVisible):
            await web_element.click_using_js()

    @pytest.mark.asyncio
    async def test_click_using_js_not_interactable(self, web_element):
        """Test JavaScript click when element is not interactable."""
        web_element._is_element_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )

        with pytest.raises(ElementNotInteractable):
            await web_element.click_using_js()

    @pytest.mark.asyncio
    async def test_click_using_js_option_element(self, option_element):
        """Test JavaScript click on option element uses specialized method."""
        option_element._click_option_tag = AsyncMock()
        
        await option_element.click_using_js()
        
        option_element._click_option_tag.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_success(self, web_element):
        """Test successful mouse click."""
        bounds = [0, 0, 100, 0, 100, 100, 0, 100]  # Rectangle coordinates
        web_element._is_element_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'model': {'content': bounds}}},  # bounds
            None,  # mouse press
            None,  # mouse release
        ]
        
        with patch('asyncio.sleep') as mock_sleep:
            await web_element.click(x_offset=5, y_offset=10, hold_time=0.2)
        
        # Should call mouse press and release
        assert web_element._connection_handler.execute_command.call_count == 3
        mock_sleep.assert_called_once_with(0.2)

    @pytest.mark.asyncio
    async def test_click_not_visible(self, web_element):
        """Test click when element is not visible."""
        web_element._is_element_visible = AsyncMock(return_value=False)

        with pytest.raises(ElementNotVisible):
            await web_element.click()

    @pytest.mark.asyncio
    async def test_click_option_element(self, option_element):
        """Test click on option element uses specialized method."""
        option_element._click_option_tag = AsyncMock()
        
        await option_element.click()
        
        option_element._click_option_tag.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_bounds_fallback_to_js(self, web_element):
        """Test click falls back to JS bounds when CDP bounds fail."""
        web_element._is_element_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        
        # First call (bounds) raises KeyError, second call (JS bounds) succeeds
        js_bounds = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'model': {'invalid_key': []}}},  # bounds with KeyError
            {'result': {'result': {'value': json.dumps(js_bounds)}}},  # JS bounds
            None,  # mouse press
            None,  # mouse release
        ]
        
        await web_element.click()
        
        # Should call bounds, JS bounds, mouse press, and mouse release
        assert web_element._connection_handler.execute_command.call_count == 4

    @pytest.mark.asyncio
    async def test_click_option_tag_method(self, option_element):
        """Test _click_option_tag method."""
        await option_element._click_option_tag()
        
        # Should execute script with option value
        option_element._connection_handler.execute_command.assert_called_once()


class TestWebElementFileInput:
    """Test file input specific functionality."""

    @pytest.mark.asyncio
    async def test_set_input_files_success(self, file_input_element):
        """Test successful file input setting."""
        files = ['/path/to/file1.txt', '/path/to/file2.pdf']
        
        await file_input_element.set_input_files(files)
        
        file_input_element._connection_handler.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_input_files_not_file_input(self, web_element):
        """Test set_input_files on non-file input element."""
        files = ['/path/to/file.txt']
        
        with pytest.raises(ElementNotAFileInput):
            await web_element.set_input_files(files)

    @pytest.mark.asyncio
    async def test_set_input_files_input_but_wrong_type(self, input_element):
        """Test set_input_files on input element with wrong type."""
        files = ['/path/to/file.txt']
        
        with pytest.raises(ElementNotAFileInput):
            await input_element.set_input_files(files)


class TestWebElementScreenshot:
    """Test screenshot functionality."""

    @pytest.mark.asyncio
    async def test_take_screenshot_success(self, web_element, tmp_path):
        """Test successful element screenshot."""
        bounds = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
        
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': json.dumps(bounds)}}},  # get_bounds_using_js
            {'result': {'data': screenshot_data}},  # capture_screenshot
        ]
        
        screenshot_path = tmp_path / 'element.jpg'
        
        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        
        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            await web_element.take_screenshot(str(screenshot_path), quality=90)
        
        # Should call get_bounds_using_js and capture_screenshot
        assert web_element._connection_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_take_screenshot_default_quality(self, web_element, tmp_path):
        """Test screenshot with default quality."""
        bounds = {'x': 0, 'y': 0, 'width': 50, 'height': 50}
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': json.dumps(bounds)}}},
            {'result': {'data': screenshot_data}},
        ]
        
        screenshot_path = tmp_path / 'element_default.jpg'
        
        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        
        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            await web_element.take_screenshot(str(screenshot_path))
        
        # Should call get_bounds_using_js and capture_screenshot
        assert web_element._connection_handler.execute_command.call_count == 2


class TestWebElementVisibility:
    """Test element visibility and interaction checks."""

    @pytest.mark.asyncio
    async def test_is_element_visible_true(self, web_element):
        """Test _is_element_visible returns True."""
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': True}}}
        )
        
        result = await web_element._is_element_visible()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_element_visible_false(self, web_element):
        """Test _is_element_visible returns False."""
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )
        
        result = await web_element._is_element_visible()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_element_on_top_true(self, web_element):
        """Test _is_element_on_top returns True."""
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': True}}}
        )
        
        result = await web_element._is_element_on_top()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_element_on_top_false(self, web_element):
        """Test _is_element_on_top returns False."""
        web_element._execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )
        
        result = await web_element._is_element_on_top()
        assert result is False


class TestWebElementUtilityMethods:
    """Test utility and helper methods."""

    def test_calculate_center(self):
        """Test _calculate_center static method."""
        # Rectangle: (0,0), (100,0), (100,100), (0,100)
        bounds = [0, 0, 100, 0, 100, 100, 0, 100]
        x_center, y_center = WebElement._calculate_center(bounds)
        assert x_center == 50
        assert y_center == 50

    def test_calculate_center_irregular_shape(self):
        """Test _calculate_center with irregular coordinates."""
        # Triangle-like shape
        bounds = [0, 0, 50, 0, 25, 50]
        x_center, y_center = WebElement._calculate_center(bounds)
        assert x_center == 25  # (0 + 50 + 25) / 3
        assert y_center == pytest.approx(16.67, rel=1e-2)  # (0 + 0 + 50) / 3

    def test_is_option_tag_true(self, option_element):
        """Test _is_option_tag returns True for option elements."""
        assert option_element._is_option_tag() is True

    def test_is_option_tag_false(self, web_element):
        """Test _is_option_tag returns False for non-option elements."""
        assert web_element._is_option_tag() is False

    def test_def_attributes_empty_list(self, mock_connection_handler):
        """Test _def_attributes with empty list."""
        element = WebElement(
            object_id='test',
            connection_handler=mock_connection_handler,
            attributes_list=[]
        )
        assert element._attributes == {}

    def test_def_attributes_class_rename(self, mock_connection_handler):
        """Test _def_attributes renames 'class' to 'class_name'."""
        attributes_list = ['class', 'my-class', 'id', 'my-id']
        element = WebElement(
            object_id='test',
            connection_handler=mock_connection_handler,
            attributes_list=attributes_list
        )
        assert element._attributes == {'class_name': 'my-class', 'id': 'my-id'}

    @pytest.mark.asyncio
    async def test_execute_script(self, web_element):
        """Test _execute_script method."""
        script = 'return this.tagName;'
        expected_response = {'result': {'result': {'value': 'DIV'}}}
        web_element._connection_handler.execute_command.return_value = expected_response
        
        result = await web_element._execute_script(script, return_by_value=True)
        
        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration=script,
            return_by_value=True,
        )
        web_element._connection_handler.execute_command.assert_called_once_with(expected_command, timeout=60)

    def test_repr(self, web_element):
        """Test __repr__ method."""
        repr_str = repr(web_element)
        assert 'WebElement' in repr_str
        assert 'test-object-id' in repr_str
        assert 'id=\'test-id\'' in repr_str
        assert 'class_name=\'test-class\'' in repr_str


class TestWebElementFindMethods:
    """Test element finding methods from FindElementsMixin."""

    @pytest.mark.asyncio
    async def test_find_element_success(self, web_element):
        """Test successful element finding."""
        node_response = {'result': {'result': {'objectId': 'found-element-id'}}}
        describe_response = {
            'result': {
                'node': {'nodeName': 'BUTTON', 'attributes': ['class', 'btn']}
            }
        }
        
        web_element._connection_handler.execute_command.side_effect = [
            node_response,
            describe_response,
        ]
        
        element = await web_element.find(id='button-id')
        
        assert isinstance(element, WebElement)
        assert element._object_id == 'found-element-id'
        assert element._attributes['class_name'] == 'btn'

    @pytest.mark.asyncio
    async def test_find_element_not_found_with_exception(self, web_element):
        """Test element not found raises exception."""
        web_element._connection_handler.execute_command.return_value = {
            'result': {'result': {}}
        }
        
        with pytest.raises(ElementNotFound):
            await web_element.find(id='nonexistent')

    @pytest.mark.asyncio
    async def test_find_element_not_found_no_exception(self, web_element):
        """Test element not found returns None when raise_exc=False."""
        web_element._connection_handler.execute_command.return_value = {
            'result': {'result': {}}
        }
        
        result = await web_element.find(id='nonexistent', raise_exc=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_elements_success(self, web_element):
        """Test successful multiple elements finding."""
        find_response = {'result': {'result': {'objectId': 'parent-id'}}}
        properties_response = {
            'result': {
                'result': [
                    {'value': {'type': 'object', 'objectId': 'child-1'}},
                    {'value': {'type': 'object', 'objectId': 'child-2'}},
                ]
            }
        }
        describe_response = {
            'result': {
                'node': {'nodeName': 'LI', 'attributes': ['class', 'item']}
            }
        }
        
        web_element._connection_handler.execute_command.side_effect = [
            find_response,
            properties_response,
            describe_response,
            describe_response,
        ]
        
        elements = await web_element.find(class_name='item', find_all=True)
        
        assert len(elements) == 2
        assert all(isinstance(elem, WebElement) for elem in elements)
        assert elements[0]._object_id == 'child-1'
        assert elements[1]._object_id == 'child-2'

    @pytest.mark.asyncio
    async def test_find_with_timeout_success(self, web_element):
        """Test find with timeout succeeds on retry."""
        node_response = {'result': {'result': {'objectId': 'delayed-element'}}}
        describe_response = {
            'result': {
                'node': {'nodeName': 'DIV', 'attributes': []}
            }
        }
        
        # First call returns empty, second call succeeds
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'result': {}}},  # First attempt fails
            node_response,  # Second attempt succeeds
            describe_response,
        ]
        
        with patch('asyncio.sleep') as mock_sleep:
            element = await web_element.find(id='delayed', timeout=2)
        
        assert isinstance(element, WebElement)
        assert element._object_id == 'delayed-element'
        mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_find_with_timeout_failure(self, web_element):
        """Test find with timeout raises WaitElementTimeout."""
        web_element._connection_handler.execute_command.return_value = {
            'result': {'result': {}}
        }
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0, 1.5, 2.1]  # Simulate time progression
            
            with pytest.raises(WaitElementTimeout):
                await web_element.find(id='never-appears', timeout=2)

    @pytest.mark.asyncio
    async def test_query_css_selector(self, web_element):
        """Test query method with CSS selector."""
        node_response = {'result': {'result': {'objectId': 'queried-element'}}}
        describe_response = {
            'result': {
                'node': {'nodeName': 'A', 'attributes': ['href', 'http://example.com']}
            }
        }
        
        web_element._connection_handler.execute_command.side_effect = [
            node_response,
            describe_response,
        ]
        
        element = await web_element.query('a[href*="example"]')
        
        assert isinstance(element, WebElement)
        assert element._object_id == 'queried-element'

    @pytest.mark.asyncio
    async def test_query_xpath(self, web_element):
        """Test query method with XPath expression."""
        node_response = {'result': {'result': {'objectId': 'xpath-element'}}}
        describe_response = {
            'result': {
                'node': {'nodeName': 'SPAN', 'attributes': []}
            }
        }
        
        web_element._connection_handler.execute_command.side_effect = [
            node_response,
            describe_response,
        ]
        
        element = await web_element.query('//span[text()="Click me"]')
        
        assert isinstance(element, WebElement)
        assert element._object_id == 'xpath-element'

    def test_find_no_criteria_raises_error(self, web_element):
        """Test find with no search criteria raises ValueError."""
        with pytest.raises(ValueError, match='At least one of the following arguments must be provided'):
            asyncio.run(web_element.find())


class TestWebElementEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_bounds_property_with_connection_error(self, web_element):
        """Test bounds property when connection fails."""
        web_element._connection_handler.execute_command.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            await web_element.bounds

    @pytest.mark.asyncio
    async def test_text_property_with_malformed_html(self, web_element):
        """Test text property with malformed HTML."""
        malformed_html = '<div>Unclosed tag <span>content'
        web_element._connection_handler.execute_command.return_value = {
            'result': {'outerHTML': malformed_html}
        }
        
        # BeautifulSoup should handle malformed HTML gracefully
        text = await web_element.text
        assert 'Unclosed tag' in text
        assert 'content' in text

    @pytest.mark.asyncio
    async def test_click_with_zero_hold_time(self, web_element):
        """Test click with zero hold time."""
        bounds = [0, 0, 50, 0, 50, 50, 0, 50]
        web_element._is_element_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'model': {'content': bounds}}},
            None,  # mouse press
            None,  # mouse release
        ]
        
        with patch('asyncio.sleep') as mock_sleep:
            await web_element.click(hold_time=0)
        
        mock_sleep.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_type_text_empty_string(self, input_element):
        """Test type_text with empty string."""
        input_element.click = AsyncMock()
        await input_element.type_text('')

        # Should not call execute_command for empty string
        input_element._connection_handler.execute_command.assert_not_called()
        assert input_element.click.call_count == 1

    @pytest.mark.asyncio
    async def test_set_input_files_empty_list(self, file_input_element):
        """Test set_input_files with empty file list."""
        await file_input_element.set_input_files([])
        
        expected_command = DomCommands.set_file_input_files(
            files=[], 
            object_id='file-input-object-id'
        )
        file_input_element._connection_handler.execute_command.assert_called_once_with(expected_command, timeout=60)
