import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, call

import pytest
import pytest_asyncio

from pydoll.browser.options import ChromiumOptions as Options
from pydoll.browser.chromium.chrome import Chrome
from pydoll.commands import DomCommands, RuntimeCommands
from pydoll.constants import Key
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    WaitElementTimeout,
)
from pydoll.protocol.input.types import KeyModifier
from pydoll.protocol.runtime.types import CallArgument


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
        'id',
        'test-id',
        'class',
        'test-class',
        'value',
        'test-value',
        'tag_name',
        'div',
        'type',
        'text',
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
        'id',
        'input-id',
        'tag_name',
        'input',
        'type',
        'text',
        'value',
        'initial-value',
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
    attributes_list = ['id', 'file-input-id', 'tag_name', 'input', 'type', 'file']
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
    attributes_list = ['tag_name', 'option', 'value', 'option-value', 'id', 'option-id']
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
    attributes_list = ['id', 'disabled-id', 'tag_name', 'button', 'disabled', 'true']
    return WebElement(
        object_id='disabled-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='button:disabled',
        attributes_list=attributes_list,
    )


@pytest.fixture
def iframe_element(mock_connection_handler):
    """Iframe element fixture for iframe-related tests."""
    attributes_list = ['id', 'iframe-id', 'tag_name', 'iframe']
    return WebElement(
        object_id='iframe-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='iframe#iframe-id',
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
            'type': 'text',
        }

    def test_web_element_initialization_empty_attributes(self, mock_connection_handler):
        """Test WebElement initialization with empty attributes list."""
        element = WebElement(
            object_id='empty-id', connection_handler=mock_connection_handler, attributes_list=[]
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
                attributes_list=attributes_list,
            )

    def test_class_attribute_renamed_to_class_name(self, mock_connection_handler):
        """Test that 'class' attribute is renamed to 'class_name'."""
        attributes_list = ['class', 'my-class', 'id', 'my-id']
        element = WebElement(
            object_id='class-test',
            connection_handler=mock_connection_handler,
            attributes_list=attributes_list,
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
            attributes_list=[],
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

    @pytest.mark.asyncio
    async def test_iframe_context_non_iframe_returns_none(self, web_element):
        """Non-iframe elements should not produce iframe context."""
        result = await web_element.iframe_context
        assert result is None
        web_element._connection_handler.execute_command.assert_not_awaited()


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

        # Should call execute_command for each character (KEY_DOWN + KEY_UP)
        assert input_element._connection_handler.execute_command.call_count == len(test_text) * 2
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

        mock_sleep.assert_called_with(0.05)  # Default interval
        assert input_element.click.call_count == 1


class TestWebElementIFrame:
    """Tests for iframe-specific WebElement behaviour."""

    @pytest.mark.asyncio
    async def test_iframe_context_initialization(self, iframe_element):
        """Iframe context should be created via CDP commands."""

        async def side_effect(command, timeout=60):
            method = command['method']
            if method == 'DOM.describeNode':
                return {
                    'result': {
                        'node': {
                            'frameId': 'frame-123',
                            'contentDocument': {
                                'frameId': 'frame-123',
                                'documentURL': 'https://example.com/frame.html',
                                'baseURL': 'https://example.com/frame.html',
                            },
                        }
                    }
                }
            if method == 'Page.createIsolatedWorld':
                return {'result': {'executionContextId': 42}}
            if method == 'Runtime.evaluate':
                return {
                    'result': {
                        'result': {
                            'type': 'object',
                            'objectId': 'document-object-id',
                        }
                    }
                }
            raise AssertionError(f'Unexpected method {method}')

        iframe_element._connection_handler.execute_command.side_effect = side_effect

        ctx = await iframe_element.iframe_context
        assert ctx is not None
        assert ctx.frame_id == 'frame-123'
        assert ctx.document_url == 'https://example.com/frame.html'
        assert ctx.execution_context_id == 42
        assert ctx.document_object_id == 'document-object-id'

        # Subsequent access should not trigger additional CDP calls
        iframe_element._connection_handler.execute_command.reset_mock()
        cached_ctx = await iframe_element.iframe_context
        assert cached_ctx is ctx
        iframe_element._connection_handler.execute_command.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_iframe_inner_html_uses_runtime_evaluate(self, iframe_element):
        """inner_html should read from iframe execution context."""
        async def side_effect(command, timeout=60):
            method = command['method']
            if method == 'DOM.describeNode':
                return {
                    'result': {
                        'node': {
                            'frameId': 'frame-123',
                            'contentDocument': {
                                'frameId': 'frame-123',
                                'documentURL': 'https://example.com/frame.html',
                                'baseURL': 'https://example.com/frame.html',
                            },
                        }
                    }
                }
            if method == 'Page.createIsolatedWorld':
                return {'result': {'executionContextId': 77}}
            if method == 'Runtime.evaluate':
                expression = command['params']['expression']
                if expression == 'document.documentElement':
                    return {
                        'result': {
                            'result': {
                                'type': 'object',
                                'objectId': 'document-object-id',
                            }
                        }
                    }
                if expression == 'document.documentElement.outerHTML':
                    assert command['params']['contextId'] == 77
                    return {
                        'result': {
                            'result': {
                                'type': 'string',
                                'value': '<html>iframe content</html>',
                            }
                        }
                    }
            raise AssertionError(f'Unexpected method {method}')

        iframe_element._connection_handler.execute_command.side_effect = side_effect

        html = await iframe_element.inner_html
        assert html == '<html>iframe content</html>'

        methods = [
            call.args[0]['method']
            for call in iframe_element._connection_handler.execute_command.await_args_list
        ]
        assert methods.count('DOM.describeNode') == 1
        assert methods.count('Page.createIsolatedWorld') == 1
        assert methods.count('Runtime.evaluate') == 2

    @pytest.mark.asyncio
    async def test_find_within_iframe_uses_document_context(self, iframe_element):
        """find() should query against the iframe's document element."""

        async def side_effect(command, timeout=60):
            method = command['method']
            if method == 'DOM.describeNode':
                object_id = command['params'].get('objectId')
                if object_id == 'iframe-object-id':
                    return {
                        'result': {
                            'node': {
                                'frameId': 'frame-123',
                                'contentDocument': {
                                    'frameId': 'frame-123',
                                    'documentURL': 'https://example.com/frame.html',
                                    'baseURL': 'https://example.com/frame.html',
                                },
                            }
                        }
                    }
                if object_id == 'element-object-id':
                    return {
                        'result': {
                            'node': {
                                'nodeName': 'DIV',
                                'attributes': ['id', 'child', 'data-test', 'value'],
                            }
                        }
                    }
                raise AssertionError('Unexpected objectId in describeNode')
            if method == 'Page.createIsolatedWorld':
                return {'result': {'executionContextId': 88}}
            if method == 'Runtime.evaluate':
                expression = command['params']['expression']
                if expression == 'document.documentElement':
                    return {
                        'result': {
                            'result': {
                                'type': 'object',
                                'objectId': 'document-object-id',
                            }
                        }
                    }
                raise AssertionError(f'Unexpected evaluate expression: {expression}')
            if method == 'Runtime.callFunctionOn':
                assert command['params']['objectId'] == 'document-object-id'
                return {
                    'result': {
                        'result': {
                            'type': 'object',
                            'objectId': 'element-object-id',
                        }
                    }
                }
            raise AssertionError(f'Unexpected method {method}')

        iframe_element._connection_handler.execute_command.side_effect = side_effect

        result = await iframe_element.find(tag_name='div')

        assert isinstance(result, WebElement)
        assert result._object_id == 'element-object-id'

        runtime_calls = [
            call.args[0]
            for call in iframe_element._connection_handler.execute_command.await_args_list
            if call.args[0]['method'] == 'Runtime.callFunctionOn'
        ]
        assert runtime_calls, 'Runtime.callFunctionOn should be used for iframe queries'
        assert runtime_calls[0]['params']['objectId'] == 'document-object-id'

    @pytest.mark.asyncio
    async def test_get_parent_element_success(self, web_element):
        """Test successful parent element retrieval."""
        script_response = {'result': {'result': {'objectId': 'parent-object-id'}}}
        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'DIV',
                    'attributes': ['id', 'parent-container', 'class', 'container'],
                }
            }
        }
        web_element._connection_handler.execute_command.side_effect = [
            script_response,  # Script execution
            describe_response,  # Describe node
        ]

        parent_element = await web_element.get_parent_element()

        assert isinstance(parent_element, WebElement)
        assert parent_element._object_id == 'parent-object-id'
        assert parent_element._attributes == {
            'id': 'parent-container',
            'class_name': 'container',
            'tag_name': 'div',
        }
        web_element._connection_handler.execute_command.assert_called()

    @pytest.mark.asyncio
    async def test_get_parent_element_not_found(self, web_element):
        """Test parent element not found raises ElementNotFound."""
        script_response = {'result': {'result': {}}}  # No objectId

        web_element._connection_handler.execute_command.return_value = script_response

        with pytest.raises(ElementNotFound, match='Parent element not found for element:'):
            await web_element.get_parent_element()

    @pytest.mark.asyncio
    async def test_get_parent_element_with_complex_attributes(self, web_element):
        """Test parent element with complex attribute list."""
        script_response = {'result': {'result': {'objectId': 'complex-parent-id'}}}

        describe_response = {
            'result': {
                'node': {
                    'nodeName': 'SECTION',
                    'attributes': [
                        'id',
                        'main-section',
                        'class',
                        'content-wrapper',
                        'data-testid',
                        'parent-element',
                        'aria-label',
                        'Main content area',
                    ],
                }
            }
        }

        web_element._connection_handler.execute_command.side_effect = [
            script_response,
            describe_response,
        ]

        parent_element = await web_element.get_parent_element()

        assert isinstance(parent_element, WebElement)
        assert parent_element._object_id == 'complex-parent-id'
        assert parent_element._attributes == {
            'id': 'main-section',
            'class_name': 'content-wrapper',
            'data-testid': 'parent-element',
            'aria-label': 'Main content area',
            'tag_name': 'section',
        }

    @pytest.mark.asyncio
    async def test_get_parent_element_root_element(self, web_element):
        """Test getting parent of root element (should return document body)."""
        script_response = {'result': {'result': {'objectId': 'body-object-id'}}}

        describe_response = {
            'result': {'node': {'nodeName': 'BODY', 'attributes': ['class', 'page-body']}}
        }

        web_element._connection_handler.execute_command.side_effect = [
            script_response,
            describe_response,
        ]

        parent_element = await web_element.get_parent_element()

        assert isinstance(parent_element, WebElement)
        assert parent_element._object_id == 'body-object-id'
        assert parent_element._attributes == {'class_name': 'page-body', 'tag_name': 'body'}


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
        web_element.is_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element.execute_script = AsyncMock(return_value={'result': {'result': {'value': True}}})

        await web_element.click_using_js()

        web_element.scroll_into_view.assert_called_once()
        web_element.is_visible.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_using_js_not_visible(self, web_element):
        """Test JavaScript click when element is not visible."""
        web_element.is_visible = AsyncMock(return_value=False)
        web_element.scroll_into_view = AsyncMock()

        with pytest.raises(ElementNotVisible):
            await web_element.click_using_js()

    @pytest.mark.asyncio
    async def test_click_using_js_not_interactable(self, web_element):
        """Test JavaScript click when element is not interactable."""
        web_element.is_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element.execute_script = AsyncMock(
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
        web_element.is_visible = AsyncMock(return_value=True)
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
        web_element.is_visible = AsyncMock(return_value=False)

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
        web_element.is_visible = AsyncMock(return_value=True)
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

    @pytest.mark.asyncio
    async def test_double_click_success(self, web_element):
        """Test successful mouse double click."""
        bounds = [0, 0, 100, 0, 100, 100, 0, 100]  # Rectangle coordinates
        web_element.is_visible = AsyncMock(return_value=True)
        web_element.scroll_into_view = AsyncMock()
        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'model': {'content': bounds}}},  # bounds
            None,  # mouse press
            None,  # mouse release
            None,  # mouse press second time
            None,  # mouse release second time
        ]

        with patch('asyncio.sleep') as mock_sleep:
            await web_element.double_click(x_offset=5, y_offset=10, hold_time=0.2, wait_time=0.3)

        # Should call mouse press and release
        assert web_element._connection_handler.execute_command.call_count == 5
        mock_sleep.assert_has_calls([
            call(0.2),
            call(0.3),
            call(0.2),
        ])

    @pytest.mark.asyncio
    async def test_double_click_not_visible(self, web_element):
        """Test double click when element is not visible."""
        web_element.is_visible = AsyncMock(return_value=False)

        with pytest.raises(ElementNotVisible):
            await web_element.double_click()

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

        screenshot_path = tmp_path / 'element.jpeg'

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

        screenshot_path = tmp_path / 'element_default.jpeg'

        # Mock aiofiles.open properly for async context manager
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()

        with patch('aiofiles.open') as mock_aiofiles_open:
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            await web_element.take_screenshot(str(screenshot_path))

        # Should call get_bounds_using_js and capture_screenshot
        assert web_element._connection_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_take_screenshot_as_base64(self, web_element):
        """Test screenshot returned as base64 string."""
        bounds = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        screenshot_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='

        web_element._connection_handler.execute_command.side_effect = [
            {'result': {'result': {'value': json.dumps(bounds)}}},  # get_bounds_using_js
            {'result': {'data': screenshot_data}},  # capture_screenshot
        ]

        # Take screenshot as base64
        result = await web_element.take_screenshot(as_base64=True)

        # Should return the base64 data
        assert result == screenshot_data
        # Should call get_bounds_using_js and capture_screenshot
        assert web_element._connection_handler.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_take_screenshot_missing_path_without_base64(self, web_element):
        """Test screenshot raises error when no path and as_base64=False."""
        from pydoll.exceptions import MissingScreenshotPath

        with pytest.raises(MissingScreenshotPath):
            await web_element.take_screenshot(as_base64=False)

    @pytest.mark.asyncio
    async def test_take_screenshot_jpg_alias(self, web_element, tmp_path):
        """Test that .jpg extension works as alias for .jpeg."""
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

        # Should work without raising InvalidFileExtension
        assert web_element._connection_handler.execute_command.call_count == 2


class TestWebElementVisibility:
    """Test element visibility and interaction checks."""

    @pytest.mark.asyncio
    async def test_is_element_visible_true(self, web_element):
        """Test _is_element_visible returns True."""
        web_element.execute_script = AsyncMock(return_value={'result': {'result': {'value': True}}})

        result = await web_element.is_visible()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_element_visible_false(self, web_element):
        """Test _is_element_visible returns False."""
        web_element.execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )

        result = await web_element.is_visible()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_element_on_top_true(self, web_element):
        """Test _is_element_on_top returns True."""
        web_element.execute_script = AsyncMock(return_value={'result': {'result': {'value': True}}})

        result = await web_element.is_on_top()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_element_on_top_false(self, web_element):
        """Test _is_element_on_top returns False."""
        web_element.execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )

        result = await web_element.is_on_top()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_element_interactable_true(self, web_element):
        """Test _is_element_interactable returns True."""
        web_element.execute_script = AsyncMock(return_value={'result': {'result': {'value': True}}})

        result = await web_element.is_interactable()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_element_interactable_false(self, web_element):
        """Test _is_element_interactable returns False."""
        web_element.execute_script = AsyncMock(
            return_value={'result': {'result': {'value': False}}}
        )

        result = await web_element.is_interactable()
        assert result is False


class TestWebElementWaitUntil:
    """Test wait_until method."""

    @pytest.mark.asyncio
    async def test_wait_until_visible_success(self, web_element):
        """Test wait_until succeeds when element becomes visible."""
        web_element.is_visible = AsyncMock(side_effect=[False, True])

        with patch('asyncio.sleep') as mock_sleep, patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 0.5]

            await web_element.wait_until(is_visible=True, timeout=2)

        assert web_element.is_visible.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_wait_until_visible_timeout(self, web_element):
        """Test wait_until raises WaitElementTimeout when visibility not met."""
        web_element.is_visible = AsyncMock(return_value=False)

        with patch('asyncio.sleep') as mock_sleep, patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0, 1.5, 2.1]

            with pytest.raises(WaitElementTimeout, match='element to become visible'):
                await web_element.wait_until(is_visible=True, timeout=2)

        assert mock_sleep.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_until_interactable_success(self, web_element):
        """Test wait_until succeeds when element becomes interactable."""
        web_element.is_interactable = AsyncMock(return_value=True)

        await web_element.wait_until(is_interactable=True, timeout=1)

        web_element.is_interactable.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_until_interactable_timeout(self, web_element):
        """Test wait_until raises WaitElementTimeout when not interactable."""
        web_element.is_interactable = AsyncMock(return_value=False)

        with patch('asyncio.sleep') as mock_sleep, patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.1]

            with pytest.raises(WaitElementTimeout, match='element to become interactable'):
                await web_element.wait_until(is_interactable=True, timeout=1)

        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_wait_until_visible_and_interactable(self, web_element):
        """Test wait_until requires both conditions when both are True."""
        web_element.is_visible = AsyncMock(side_effect=[False, True])
        web_element.is_interactable = AsyncMock(side_effect=[False, True])

        with patch('asyncio.sleep') as mock_sleep, patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0]

            await web_element.wait_until(is_visible=True, is_interactable=True, timeout=2)

        assert web_element.is_visible.call_count == 2
        assert web_element.is_interactable.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_wait_until_no_conditions(self, web_element):
        """Test wait_until raises ValueError when no condition specified."""
        with pytest.raises(ValueError):
            await web_element.wait_until()


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
            object_id='test', connection_handler=mock_connection_handler, attributes_list=[]
        )
        assert element._attributes == {}

    def test_def_attributes_class_rename(self, mock_connection_handler):
        """Test _def_attributes renames 'class' to 'class_name'."""
        attributes_list = ['class', 'my-class', 'id', 'my-id']
        element = WebElement(
            object_id='test',
            connection_handler=mock_connection_handler,
            attributes_list=attributes_list,
        )
        assert element._attributes == {'class_name': 'my-class', 'id': 'my-id'}

    @pytest.mark.asyncio
    async def test_execute_script_basic(self, web_element):
        """Test execute_script basic functionality with return value."""
        script = 'return this.tagName;'
        expected_response = {'result': {'result': {'value': 'DIV'}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script, return_by_value=True)

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function(){ return this.tagName; }',
            return_by_value=True,
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

class TestBuildTextExpression:
    """Unit tests for FindElementsMixin._build_text_expression."""

    def test_build_text_expression_with_xpath(self):
        from pydoll.elements.mixins import FindElementsMixin
        expr = FindElementsMixin._build_text_expression('//p[@id="x"]', 'xpath')
        assert isinstance(expr, str)
        assert 'XPathResult.FIRST_ORDERED_NODE_TYPE' in expr
        assert '@id' in expr
        assert 'p' in expr

    def test_build_text_expression_with_name(self):
        from pydoll.elements.mixins import FindElementsMixin
        expr = FindElementsMixin._build_text_expression('fieldName', 'name')
        assert isinstance(expr, str)
        assert '//*[@name="fieldName"]' in expr

    def test_build_text_expression_with_id_css(self):
        from pydoll.elements.mixins import FindElementsMixin
        expr = FindElementsMixin._build_text_expression('main', 'id')
        assert 'document.querySelector' in expr
        assert '#main' in expr

    def test_build_text_expression_with_class_css(self):
        from pydoll.elements.mixins import FindElementsMixin
        expr = FindElementsMixin._build_text_expression('item', 'class_name')
        assert 'document.querySelector' in expr
        assert '.item' in expr

    def test_build_text_expression_with_tag_css(self):
        from pydoll.elements.mixins import FindElementsMixin
        expr = FindElementsMixin._build_text_expression('button', 'tag_name')
        assert 'document.querySelector' in expr
        assert 'button' in expr

class TestIsOptionElementHeuristics:
    """Unit tests for heuristics inside WebElement._is_option_element."""

    @pytest.mark.asyncio
    async def test_is_option_element_by_tag_attribute(self, option_element):
        assert await option_element._is_option_element() is True

    @pytest.mark.asyncio
    async def test_is_option_element_by_method_and_selector_tag_name(self, mock_connection_handler):
        dummy = WebElement('dummy', mock_connection_handler, method='tag_name', selector='option', attributes_list=[])
        assert await dummy._is_option_element() is True

    @pytest.mark.asyncio
    async def test_is_option_element_by_xpath_selector_contains_option(self, mock_connection_handler):
        dummy = WebElement('dummy', mock_connection_handler, method='xpath', selector='//OPTION[@value=\"x\"]', attributes_list=[])
        assert await dummy._is_option_element() is True
    @pytest.mark.asyncio
    async def test_execute_script_with_this_syntax(self, web_element):
        """Test execute_script method with 'this' syntax."""
        script = 'this.style.border = "2px solid red"'
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script)

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function(){ this.style.border = "2px solid red" }',
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

    @pytest.mark.asyncio
    async def test_execute_script_already_function(self, web_element):
        """Test execute_script when script is already a function."""
        script = 'function() { this.style.border = "2px solid red"; }'
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script)

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function() { this.style.border = "2px solid red"; }',
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

    @pytest.mark.asyncio
    async def test_execute_script_with_parameters(self, web_element):
        """Test execute_script with additional parameters."""
        script = 'this.value = "test"'
        expected_response = {'result': {'result': {'value': 'test'}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(
            script, 
            return_by_value=True,
            user_gesture=True
        )

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function(){ this.value = "test" }',
            return_by_value=True,
            user_gesture=True,
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

    @pytest.mark.asyncio
    async def test_execute_script_arrow_function(self, web_element):
        """Test execute_script with arrow function syntax."""
        script = '() => { this.style.color = "red"; }'
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script)

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='() => { this.style.color = "red"; }',
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

    @pytest.mark.asyncio
    async def test_execute_script_multiline(self, web_element):
        """Test execute_script with multiline script."""
        script = '''
            this.style.padding = "10px";
            this.style.margin = "5px";
            this.style.borderRadius = "8px";
        '''
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script)

        assert result == expected_response
        web_element._connection_handler.execute_command.assert_called_once()
        call_args = web_element._connection_handler.execute_command.call_args[0][0]
        
        assert call_args['method'].value == 'Runtime.callFunctionOn'
        assert call_args['params']['objectId'] == 'test-object-id'
        
        func_decl = call_args['params']['functionDeclaration']
        assert 'function(){' in func_decl
        assert 'this.style.padding = "10px"' in func_decl
        assert 'this.style.margin = "5px"' in func_decl
        assert 'this.style.borderRadius = "8px"' in func_decl

    @pytest.mark.asyncio
    async def test_execute_script_with_arguments(self, web_element):
        """Test execute_script with custom arguments."""
        script = 'this.value = arguments[0];'
        arguments = [CallArgument(value="test_value")]
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(script, arguments=arguments)

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function(){ this.value = arguments[0]; }',
            arguments=arguments,
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

    @pytest.mark.asyncio
    async def test_execute_script_all_parameters(self, web_element):
        """Test execute_script with all optional parameters."""
        script = 'this.click()'
        expected_response = {'result': {'result': {'value': None}}}
        web_element._connection_handler.execute_command.return_value = expected_response

        result = await web_element.execute_script(
            script,
            silent=True,
            return_by_value=True,
            generate_preview=True,
            user_gesture=True,
            await_promise=True,
            execution_context_id=123,
            object_group="test_group",
            throw_on_side_effect=True,
            unique_context_id="unique_123"
        )

        assert result == expected_response
        expected_command = RuntimeCommands.call_function_on(
            object_id='test-object-id',
            function_declaration='function(){ this.click() }',
            silent=True,
            return_by_value=True,
            generate_preview=True,
            user_gesture=True,
            await_promise=True,
            execution_context_id=123,
            object_group="test_group",
            throw_on_side_effect=True,
            unique_context_id="unique_123",
        )
        web_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )

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
            'result': {'node': {'nodeName': 'BUTTON', 'attributes': ['class', 'btn']}}
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
        web_element._connection_handler.execute_command.return_value = {'result': {'result': {}}}

        with pytest.raises(ElementNotFound):
            await web_element.find(id='nonexistent')

    @pytest.mark.asyncio
    async def test_find_element_not_found_no_exception(self, web_element):
        """Test element not found returns None when raise_exc=False."""
        web_element._connection_handler.execute_command.return_value = {'result': {'result': {}}}

        result = await web_element.find(id='nonexistent', raise_exc=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_elements_success(self, web_element):
        """Test successful multiple elements finding."""
        find_response = {'result': {'result': {'objectId': 'parent-id'}}}
        properties_response = {
            'result': {
                'result': [
                    {'name': '0', 'value': {'type': 'object', 'objectId': 'child-1'}},
                    {'name': '1', 'value': {'type': 'object', 'objectId': 'child-2'}},
                ]
            }
        }
        describe_response = {
            'result': {'node': {'nodeName': 'LI', 'attributes': ['class', 'item']}}
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
        describe_response = {'result': {'node': {'nodeName': 'DIV', 'attributes': []}}}

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
        web_element._connection_handler.execute_command.return_value = {'result': {'result': {}}}

        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.side_effect = [
                0,
                0.5,
                1.0,
                1.5,
                2.1,
            ]  # Simulate time progression

            with pytest.raises(WaitElementTimeout):
                await web_element.find(id='never-appears', timeout=2)

    @pytest.mark.asyncio
    async def test_query_css_selector(self, web_element):
        """Test query method with CSS selector."""
        node_response = {'result': {'result': {'objectId': 'queried-element'}}}
        describe_response = {
            'result': {'node': {'nodeName': 'A', 'attributes': ['href', 'http://example.com']}}
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
        describe_response = {'result': {'node': {'nodeName': 'SPAN', 'attributes': []}}}

        web_element._connection_handler.execute_command.side_effect = [
            node_response,
            describe_response,
        ]

        element = await web_element.query('//span[text()="Click me"]')

        assert isinstance(element, WebElement)
        assert element._object_id == 'xpath-element'

    def test_find_no_criteria_raises_error(self, web_element):
        """Test find with no search criteria raises ValueError."""
        with pytest.raises(
            ValueError, match='At least one of the following arguments must be provided'
        ):
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
        web_element.is_visible = AsyncMock(return_value=True)
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
            files=[], object_id='file-input-object-id'
        )
        file_input_element._connection_handler.execute_command.assert_called_once_with(
            expected_command, timeout=60
        )


class TestWebElementGetChildren:
    """Integration tests for WebElement get_children_elements method using real HTML."""

    @pytest.mark.asyncio
    async def test_get_children_elements_basic(self, ci_chrome_options):
        """Test get_children_elements with basic depth using real HTML."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find the parent element
            parent_element = await tab.find(id='parent-element')

            # Test get_children_elements with depth 3
            nodes = await parent_element.get_children_elements(3)

            # Verify results - should get all direct children and nested children up to depth 3
            assert len(nodes) > 0
            assert all(isinstance(node, WebElement) for node in nodes)

            # Check that we have the expected direct children
            child_ids = []
            for node in nodes:
                node_id = node.get_attribute('id')
                if node_id:
                    child_ids.append(node_id)

            # Should include direct children
            expected_direct_children = [
                'child1',
                'child2',
                'child3',
                'link1',
                'link2',
                'nested-parent',
            ]
            for expected_id in expected_direct_children:
                assert (
                    expected_id in child_ids
                ), f"Expected child {expected_id} not found in {child_ids}"

            # Should also include nested children (depth 3)
            expected_nested_children = ['nested-child1', 'nested-child2', 'nested-link']
            for expected_id in expected_nested_children:
                assert (
                    expected_id in child_ids
                ), f"Expected nested child {expected_id} not found in {child_ids}"

    @pytest.mark.asyncio
    async def test_get_children_elements_with_tag_filter(self, ci_chrome_options):
        """Test get_children_elements with tag filter using real HTML."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find the parent element
            parent_element = await tab.find(id='parent-element')

            # Test get_children_elements with tag filter for 'a' tags
            nodes_filter = await parent_element.get_children_elements(4, ['a'])

            # Verify results - should only get anchor tags
            assert len(nodes_filter) > 0
            assert all(isinstance(node, WebElement) for node in nodes_filter)

            # Check that all returned elements are anchor tags
            for node in nodes_filter:
                tag_name = node.get_attribute('tag_name')
                assert tag_name.lower() == 'a', f"Expected 'a' tag, got '{tag_name}'"

            # Check that we have the expected anchor elements
            link_ids = []
            for node in nodes_filter:
                node_id = node.get_attribute('id')
                if node_id:
                    link_ids.append(node_id)

            # Should include both direct and nested anchor tags
            expected_links = ['link1', 'link2', 'nested-link']
            for expected_id in expected_links:
                assert (
                    expected_id in link_ids
                ), f"Expected link {expected_id} not found in {link_ids}"

    @pytest.mark.asyncio
    async def test_get_children_elements_depth_limit(self, ci_chrome_options):
        """Test get_children_elements with depth limit."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find the parent element
            parent_element = await tab.find(id='parent-element')

            # Test with depth 1 - should only get direct children
            nodes_depth_1 = await parent_element.get_children_elements(1)

            # Get IDs of elements found with depth 1
            depth_1_ids = []
            for node in nodes_depth_1:
                node_id = node.get_attribute('id')
                if node_id:
                    depth_1_ids.append(node_id)

            # Should include direct children but not nested ones
            expected_direct = ['child1', 'child2', 'child3', 'link1', 'link2', 'nested-parent']
            for expected_id in expected_direct:
                assert expected_id in depth_1_ids, f"Expected direct child {expected_id} not found"

            # Should NOT include nested children with depth 1
            unexpected_nested = ['nested-child1', 'nested-child2', 'nested-link']
            for unexpected_id in unexpected_nested:
                assert (
                    unexpected_id not in depth_1_ids
                ), f"Unexpected nested child {unexpected_id} found with depth 1"

    @pytest.mark.asyncio
    async def test_get_children_elements_empty_result(self, ci_chrome_options):
        """Test get_children_elements on element with no children."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find a leaf element (no children)
            leaf_element = await tab.find(id='child1')

            # Test get_children_elements on element with no children
            nodes = await leaf_element.get_children_elements(2)

            # Should return empty list
            assert isinstance(nodes, list)
            assert len(nodes) == 0

    @pytest.mark.asyncio
    async def test_get_children_elements_element_not_found_exception(self):
        """Test get_children_elements raises ElementNotFound when script fails."""
        # Create a mock element that will fail the script execution
        mock_connection_handler = AsyncMock()

        # Mock script result without objectId (simulates script failure)
        mock_connection_handler.execute_command.return_value = {
            'result': {'result': {}}  # No objectId key
        }

        # Create a WebElement with the mock connection
        element = WebElement(
            object_id='test-element-id',
            connection_handler=mock_connection_handler,
            attributes_list=['id', 'test-element', 'tag_name', 'div'],
        )

        # Should raise ElementNotFound when script returns no objectId
        with pytest.raises(ElementNotFound):
            await element.get_children_elements(1, raise_exc=True)

    @pytest.mark.asyncio
    async def test_get_siblings_elements_basic(self, ci_chrome_options):
        """Test get_siblings_elements with basic functionality using real HTML."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find one of the child elements to get its siblings
            child_element = await tab.find(id='child2')

            # Test get_siblings_elements
            siblings = await child_element.get_siblings_elements()

            # Verify results - should get all sibling elements
            assert len(siblings) > 0
            assert all(isinstance(sibling, WebElement) for sibling in siblings)

            # Check that we have the expected siblings
            sibling_ids = []
            for sibling in siblings:
                sibling_id = sibling.get_attribute('id')
                if sibling_id:
                    sibling_ids.append(sibling_id)

            # Should include all siblings of child2 (child1, child3, link1, link2, nested-parent)
            # but NOT child2 itself
            expected_siblings = ['child1', 'child3', 'link1', 'link2', 'nested-parent']
            for expected_id in expected_siblings:
                assert (
                    expected_id in sibling_ids
                ), f"Expected sibling {expected_id} not found in {sibling_ids}"

            # Should NOT include the element itself
            assert 'child2' not in sibling_ids, "Element should not include itself in siblings"

    @pytest.mark.asyncio
    async def test_get_siblings_elements_with_tag_filter(self, ci_chrome_options):
        """Test get_siblings_elements with tag filter."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find one of the child elements to get its siblings
            child_element = await tab.find(id='child1')

            # Test get_siblings_elements with tag filter for 'a' tags only
            siblings_filter = await child_element.get_siblings_elements(tag_filter=['a'])

            # Get IDs of filtered siblings
            sibling_ids = []
            for sibling in siblings_filter:
                sibling_id = sibling.get_attribute('id')
                if sibling_id:
                    sibling_ids.append(sibling_id)

            # Should include only anchor tag siblings
            expected_links = ['link1', 'link2']
            for expected_id in expected_links:
                assert (
                    expected_id in sibling_ids
                ), f"Expected link sibling {expected_id} not found in {sibling_ids}"

            # Should NOT include non-anchor siblings
            unexpected_siblings = ['child2', 'child3', 'nested-parent']
            for unexpected_id in unexpected_siblings:
                assert (
                    unexpected_id not in sibling_ids
                ), f"Unexpected non-anchor sibling {unexpected_id} found with tag filter"

    @pytest.mark.asyncio
    async def test_get_siblings_elements_empty_result(self, ci_chrome_options):
        """Test get_siblings_elements on element with no siblings."""

        # Get the path to our test HTML file
        test_file = Path(__file__).parent / 'pages' / 'test_children.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find the parent element which should have no siblings at its level
            parent_element = await tab.find(id='parent-element')

            # Test get_siblings_elements on element with no siblings
            siblings = await parent_element.get_siblings_elements()

            # Should return list with only the other parent element as sibling
            assert isinstance(siblings, list)
            # Should have at least one sibling (another-parent)
            sibling_ids = []
            for sibling in siblings:
                sibling_id = sibling.get_attribute('id')
                if sibling_id:
                    sibling_ids.append(sibling_id)

            # Should include the other parent element
            assert 'another-parent' in sibling_ids

    @pytest.mark.asyncio
    async def test_get_siblings_elements_element_not_found_exception(self):
        """Test get_siblings_elements raises ElementNotFound when script fails."""
        # Create a mock element that will fail the script execution
        mock_connection_handler = AsyncMock()

        # Mock script result without objectId (simulates script failure)
        mock_connection_handler.execute_command.return_value = {
            'result': {'result': {}}  # No objectId key
        }

        # Create a WebElement with the mock connection
        element = WebElement(
            object_id='test-element-id',
            connection_handler=mock_connection_handler,
            attributes_list=['id', 'test-element', 'tag_name', 'div'],
        )

        # Should raise ElementNotFound when script returns no objectId
        with pytest.raises(ElementNotFound):
            await element.get_siblings_elements(raise_exc=True)


"""
Tests for WebElement iframe edge cases and uncovered code paths.

This test suite focuses on covering edge cases in iframe resolution and context handling,
including:
- inner_html edge cases for iframes and iframe context elements
- Frame tree traversal and owner resolution
- OOPIF resolution scenarios
- Isolated world creation failures
- Document object resolution failures
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from pydoll.elements.web_element import WebElement
from pydoll.interactions.iframe import IFrameContext
from pydoll.connection import ConnectionHandler
from pydoll.exceptions import InvalidIFrame


@pytest_asyncio.fixture
async def mock_connection_handler():
    """Mock connection handler for WebElement tests."""
    with patch('pydoll.connection.ConnectionHandler', autospec=True) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        handler._connection_port = 9222
        yield handler


@pytest.fixture
def iframe_element(mock_connection_handler):
    """Iframe element fixture for iframe-related tests."""
    attributes_list = ['id', 'test-iframe', 'tag_name', 'iframe']
    return WebElement(
        object_id='iframe-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='iframe#test-iframe',
        attributes_list=attributes_list,
    )


@pytest.fixture
def element_in_iframe(mock_connection_handler):
    """Element inside an iframe (has _iframe_context set)."""
    attributes_list = ['id', 'button-in-iframe', 'tag_name', 'button']
    element = WebElement(
        object_id='button-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='button',
        attributes_list=attributes_list,
    )
    # Set iframe context to simulate element inside iframe
    element._iframe_context = IFrameContext(
        frame_id='frame-123',
        document_url='https://example.com/iframe.html',
        execution_context_id=42,
        document_object_id='doc-obj-id',
    )
    return element


class TestInnerHtmlEdgeCases:
    """Test inner_html property edge cases for iframe scenarios."""

    @pytest.mark.asyncio
    async def test_inner_html_iframe_element_with_context(self, iframe_element):
        """Test inner_html on iframe element uses Runtime.evaluate in iframe context."""

        async def side_effect(command, timeout=60):
            method = command['method']
            if method == 'DOM.describeNode':
                return {
                    'result': {
                        'node': {
                            # Simula um iframe de mesma origem já com frameId
                            # resolvido; não precisamos de backendNodeId aqui,
                            # pois não queremos acionar a resolução OOPIF.
                            'frameId': 'parent-frame',
                            'contentDocument': {
                                'frameId': 'iframe-123',
                                'documentURL': 'https://example.com/frame.html',
                            },
                        }
                    }
                }
            if method == 'Page.createIsolatedWorld':
                return {'result': {'executionContextId': 77}}
            if method == 'Runtime.evaluate':
                expression = command['params']['expression']
                if expression == 'document.documentElement':
                    return {
                        'result': {
                            'result': {
                                'type': 'object',
                                'objectId': 'doc-element-id',
                            }
                        }
                    }
                if expression == 'document.documentElement.outerHTML':
                    return {
                        'result': {
                            'result': {
                                'type': 'string',
                                'value': '<html><body>Iframe content</body></html>',
                            }
                        }
                    }
            raise AssertionError(f'Unexpected method {method}')

        iframe_element._connection_handler.execute_command.side_effect = side_effect

        # Get inner HTML of iframe element
        html = await iframe_element.inner_html

        # Should return iframe's document HTML
        assert html == '<html><body>Iframe content</body></html>'

        # Verify Runtime.evaluate was called with correct context
        evaluate_calls = [
            call
            for call in iframe_element._connection_handler.execute_command.await_args_list
            if call.args[0]['method'] == 'Runtime.evaluate'
        ]
        # Should have two calls: one for document.documentElement, one for outerHTML
        assert len(evaluate_calls) == 2
        outer_html_call = evaluate_calls[1]
        assert (
            outer_html_call.args[0]['params']['expression']
            == 'document.documentElement.outerHTML'
        )
        assert outer_html_call.args[0]['params']['contextId'] == 77

    @pytest.mark.asyncio
    async def test_inner_html_element_in_iframe_uses_call_function_on(self, element_in_iframe):
        """Test inner_html on element inside iframe uses Runtime.callFunctionOn."""
        element_in_iframe._connection_handler.execute_command.return_value = {
            'result': {
                'result': {
                    'type': 'string',
                    'value': '<button id="button-in-iframe">Click me</button>',
                }
            }
        }

        html = await element_in_iframe.inner_html

        # Should use callFunctionOn with this.outerHTML
        assert html == '<button id="button-in-iframe">Click me</button>'
        element_in_iframe._connection_handler.execute_command.assert_called_once()
        call_args = element_in_iframe._connection_handler.execute_command.call_args[0][0]
        assert call_args['method'] == 'Runtime.callFunctionOn'
        assert call_args['params']['objectId'] == 'button-object-id'
        assert 'this.outerHTML' in call_args['params']['functionDeclaration']

    @pytest.mark.asyncio
    async def test_inner_html_element_in_iframe_empty_response(self, element_in_iframe):
        """Test inner_html on element inside iframe when response is empty."""
        element_in_iframe._connection_handler.execute_command.return_value = {
            'result': {}  # Empty result
        }

        html = await element_in_iframe.inner_html

        # Should return empty string when result is missing
        assert html == ''

    @pytest.mark.asyncio
    async def test_inner_html_regular_element_fallback(self, mock_connection_handler):
        """Test inner_html falls back to DOM.getOuterHTML for regular elements."""
        attributes_list = ['id', 'regular-div', 'tag_name', 'div']
        element = WebElement(
            object_id='div-object-id',
            connection_handler=mock_connection_handler,
            attributes_list=attributes_list,
        )
        mock_connection_handler.execute_command.return_value = {
            'result': {'outerHTML': '<div id="regular-div">Content</div>'}
        }

        html = await element.inner_html

        # Should use DOM.getOuterHTML for regular elements
        assert html == '<div id="regular-div">Content</div>'
        call_args = mock_connection_handler.execute_command.call_args[0][0]
        assert call_args['method'] == 'DOM.getOuterHTML'
