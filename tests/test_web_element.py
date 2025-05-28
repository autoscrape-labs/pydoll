import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from pydoll.exceptions import (
    ElementNotVisible,
    ElementNotInteractable,
    ElementNotFound,
)
from pydoll.protocol.commands import (
    DomCommands,
    InputCommands,
)

from pydoll.elements.web_element import WebElement


@pytest_asyncio.fixture
async def mock_connection_handler():
    with patch(
        'pydoll.connection.ConnectionHandler', autospec=True
    ) as mock:
        handler = mock.return_value
        handler.execute_command = AsyncMock()
        yield handler


@pytest.fixture
def web_element(mock_connection_handler):
    attributes_list = [
        'id',
        'test-id',
        'class',
        'test-class',
        'value',
        'test-value',
        'tag_name',
        'div',
    ]
    return WebElement(
        object_id='test-object-id',
        connection_handler=mock_connection_handler,
        method='css',
        selector='#test',
        attributes_list=attributes_list,
    )


@pytest.mark.asyncio
async def test_web_element_initialization(web_element):
    assert web_element._object_id == 'test-object-id'
    assert web_element._search_method == 'css'
    assert web_element._selector == '#test'
    assert web_element._attributes == {
        'id': 'test-id',
        'class_name': 'test-class',
        'value': 'test-value',
        'tag_name': 'div',
    }


def test_web_element_properties(web_element):
    assert web_element.value == 'test-value'
    assert web_element.class_name == 'test-class'
    assert web_element.id == 'test-id'
    assert web_element.is_enabled == True

    # Test disabled attribute
    disabled_element = WebElement(
        'test-id', MagicMock(), attributes_list=['disabled', 'true']
    )
    assert disabled_element.is_enabled == False


@pytest.mark.asyncio
async def test_bounds_property(web_element):
    expected_bounds = {'content': [0, 0, 100, 100]}
    web_element._connection_handler.execute_command.return_value = {
        'result': {'model': expected_bounds}
    }

    bounds = await web_element.bounds
    assert bounds == expected_bounds['content']
    web_element._connection_handler.execute_command.assert_called_once_with(
        DomCommands.box_model(object_id='test-object-id'), timeout=60
    )


@pytest.mark.asyncio
async def test_inner_html(web_element):
    expected_html = '<div>Test</div>'
    web_element._connection_handler.execute_command.return_value = {
        'result': {'outerHTML': expected_html}
    }

    html = await web_element.inner_html
    assert html == expected_html
    web_element._connection_handler.execute_command.assert_called_once_with(
        DomCommands.get_outer_html('test-object-id'), timeout=60
    )


@pytest.mark.asyncio
async def test_get_bounds_using_js(web_element):
    expected_bounds = {'x': 0, 'y': 0, 'width': 100, 'height': 100}
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {'value': json.dumps(expected_bounds)}}
    }

    bounds = await web_element.get_bounds_using_js()
    assert bounds == expected_bounds


@pytest.mark.asyncio
async def test_get_screenshot(web_element, tmp_path):
    bounds = {'x': 0, 'y': 0, 'width': 100, 'height': 100}
    web_element._connection_handler.execute_command.side_effect = [
        {'result': {'result': {'value': json.dumps(bounds)}}},
        {
            'result': {
                'data': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAgAB/edzE+oAAAAASUVORK5CYII='
            }
        },
    ]

    screenshot_path = tmp_path / 'element.png'
    with patch('aiofiles.open') as mock_open:
        mock_open.return_value.__aenter__.return_value.write = AsyncMock()
        await web_element.get_screenshot(str(screenshot_path))

    assert web_element._connection_handler.execute_command.call_count == 2


@pytest.mark.asyncio
async def test_get_element_text(web_element):
    test_html = '<div>Test Text</div>'
    web_element._connection_handler.execute_command.return_value = {
        'result': {'outerHTML': test_html}
    } 

    text = await web_element.get_element_text()
    assert text == 'Test Text'

@pytest.mark.asyncio
async def test_text_property(web_element):
    test_html = '<div>Hello World</div>'
    web_element._connection_handler.execute_command.return_value = {
        'result': {'outerHTML': test_html}
    }

    text = await web_element.text
    assert text == 'Hello World'



@pytest.mark.asyncio
async def test_scroll_into_view(web_element):
    await web_element.scroll_into_view()
    web_element._connection_handler.execute_command.assert_called_once_with(
        DomCommands.scroll_into_view(object_id='test-object-id'), timeout=60
    )


@pytest.mark.asyncio
async def test_click_using_js_not_visible(web_element):
    web_element._execute_script = AsyncMock(
        return_value={'result': {'result': {'value': False}}}
    )

    with pytest.raises(ElementNotVisible):
        await web_element.click_using_js()


@pytest.mark.asyncio
async def test_click_using_js_not_interactable(web_element):
    web_element._execute_script = AsyncMock(
        side_effect=[
            {'result': {'result': {'value': True}}},  # _is_element_visible
            {'result': {'result': {'value': False}}},  # click result
        ]
    )
    web_element.scroll_into_view = AsyncMock()

    with pytest.raises(ElementNotInteractable):
        await web_element.click_using_js()


@pytest.mark.asyncio
async def test_click_using_js_option_tag(web_element):
    option_element = WebElement(
        'test-id',
        web_element._connection_handler,
        method='css',
        selector='#test',
        attributes_list=[
            'id',
            'test-id',
            'value',
            'test-value',
            'tag_name',
            'option',
        ],
    )
    option_element._execute_script = AsyncMock(
        return_value={'result': {'result': {'value': False}}}
    )

    await option_element.click_using_js()

    web_element._connection_handler.execute_command.assert_called_once()


@pytest.mark.asyncio
async def test_click(web_element):
    bounds = [0, 0, 100, 100, 100, 100, 0, 100]
    web_element._connection_handler.execute_command.side_effect = [
        {'result': {'result': {'value': True}}},  # _is_element_visible
        {'result': {'result': {'value': True}}},  # scroll_into_view
        {'result': {'model': {'content': bounds}}},  # self.bounds
        None,  # mouse_press
        None,  # mouse_release
    ]
    await web_element.click()
    assert web_element._connection_handler.execute_command.call_count == 5


@pytest.mark.asyncio
async def test_click_element_not_visible(web_element):
    web_element._is_element_visible = AsyncMock(return_value=False)
    with pytest.raises(ElementNotVisible):
        await web_element.click()


@pytest.mark.asyncio
async def test_click_bounds_key_error(web_element):
    web_element._connection_handler.execute_command.side_effect = [
        {'result': {'result': {'value': True}}},  # _is_element_visible
        {'result': {'result': {'value': True}}},  # scroll_into_view
        {'result': {'model': {'invalid_key': [10]}}},  # self.bounds
        {
            'result': {
                'result': {
                    'value': '{"x": 0, "y": 0, "width": 100, "height": 100}'
                }
            }
        },  # bounds_using_js
        None,  # mouse_press
        None,  # mouse_release
    ]

    await web_element.click()
    assert web_element._connection_handler.execute_command.call_count == 6


@pytest.mark.asyncio
async def test_click_option_tag(web_element):
    option_element = WebElement(
        'test-id',
        web_element._connection_handler,
        attributes_list=['tag_name', 'option', 'value', 'test-value'],
    )

    await option_element.click()
    web_element._connection_handler.execute_command.assert_called_once()


@pytest.mark.asyncio
async def test__is_element_on_top(web_element):
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {'value': True}}
    }

    result = await web_element._is_element_on_top()
    assert result is True

    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {'value': False}}
    }

    result = await web_element._is_element_on_top()
    assert result is False


@pytest.mark.asyncio
async def test_type_text(web_element):
    test_text = 'Hi'
    with patch('asyncio.sleep') as mock_sleep:
        await web_element.type_text(test_text)

    assert web_element._connection_handler.execute_command.call_count == len(
        test_text
    )
    web_element._connection_handler.execute_command.assert_any_call(
        InputCommands.char_press('H'), timeout=60
    )
    web_element._connection_handler.execute_command.assert_any_call(
        InputCommands.char_press('i'), timeout=60
    )


def test_calculate_center():
    bounds = [0, 0, 100, 0, 100, 100, 0, 100]  # Rectangle corners
    x_center, y_center = WebElement._calculate_center(bounds)
    assert x_center == 50
    assert y_center == 50


def test_get_attribute(web_element):
    assert web_element.get_attribute('id') == 'test-id'
    assert web_element.get_attribute('class_name') == 'test-class'
    assert web_element.get_attribute('nonexistent') is None


@pytest.mark.asyncio
async def test_wait_element_success(web_element):
    mock_element = MagicMock()
    web_element.find_element = AsyncMock(
        side_effect=[None, None, mock_element]
    )

    result = await web_element.wait_element('css', '#test-selector')
    assert result == mock_element
    assert web_element.find_element.call_count == 3


@pytest.mark.asyncio
async def test_wait_element_timeout(web_element):
    web_element.find_element = AsyncMock(return_value=None)

    with pytest.raises(TimeoutError):
        await web_element.wait_element('css', '#test-selector', timeout=1)


@pytest.mark.asyncio
async def test_wait_element_no_exception(web_element):
    web_element.find_element = AsyncMock(return_value=None)

    result = await web_element.wait_element(
        'css', '#test-selector', timeout=1, raise_exc=False
    )
    assert result is None


@pytest.mark.asyncio
async def test_find_element_success(web_element):
    node_response = {'result': {'result': {'objectId': 'test-object-id'}}}

    describe_response = {
        'result': {
            'node': {'nodeName': 'DIV', 'attributes': ['class', 'test-class']}
        }
    }

    web_element._connection_handler.execute_command.side_effect = [
        node_response,
        describe_response,
    ]

    element = await web_element.find_element('css', '.test-selector')

    assert isinstance(element, WebElement)
    assert element._object_id == 'test-object-id'
    assert element._search_method == 'css'
    assert element._selector == '.test-selector'
    assert 'test-class' in element._attributes.values()


@pytest.mark.asyncio
async def test_find_element_not_found(web_element):
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {}}
    }

    with pytest.raises(ElementNotFound):
        await web_element.find_element('css', '.non-existent')


@pytest.mark.asyncio
async def test_find_element_no_exception(web_element):
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {}}
    }

    result = await web_element.find_element(
        'css', '.non-existent', raise_exc=False
    )
    assert result is None


@pytest.mark.asyncio
async def test_find_elements_success(web_element):
    find_elements_response = {
        'result': {'result': {'objectId': 'parent-object-id'}}
    }

    properties_response = {
        'result': {
            'result': [
                {'value': {'type': 'object', 'objectId': 'child-1'}},
                {'value': {'type': 'object', 'objectId': 'child-2'}},
            ]
        }
    }

    node_description = {
        'result': {
            'node': {'nodeName': 'DIV', 'attributes': ['class', 'test-class']}
        }
    }

    web_element._connection_handler.execute_command.side_effect = [
        find_elements_response,
        properties_response,
        node_description,
        node_description,
    ]

    elements = await web_element.find_elements('css', '.test-selector')

    assert len(elements) == 2
    assert all(isinstance(elem, WebElement) for elem in elements)
    assert elements[0]._object_id == 'child-1'
    assert elements[1]._object_id == 'child-2'


@pytest.mark.asyncio
async def test_find_elements_not_found(web_element):
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {}}
    }

    with pytest.raises(ElementNotFound):
        await web_element.find_elements('css', '.non-existent')


@pytest.mark.asyncio
async def test_find_elements_no_exception(web_element):
    web_element._connection_handler.execute_command.return_value = {
        'result': {'result': {}}
    }

    result = await web_element.find_elements(
        'css', '.non-existent', raise_exc=False
    )
    assert result == []


@pytest.mark.asyncio
async def test_describe_node(web_element):
    expected_node = {'nodeName': 'DIV', 'attributes': ['class', 'test-class']}

    web_element._connection_handler.execute_command.return_value = {
        'result': {'node': expected_node}
    }

    result = await web_element._describe_node('test-object-id')
    assert result == expected_node
    web_element._connection_handler.execute_command.assert_called_once_with(
        DomCommands.describe_node(object_id='test-object-id'), timeout=60
    )


@pytest.mark.asyncio
async def test_execute_command(web_element):
    expected_response = {'result': 'test'}
    web_element._connection_handler.execute_command.return_value = (
        expected_response
    )

    test_command = {'method': 'test', 'params': {}}
    result = await web_element._execute_command(test_command)

    assert result == expected_response
    web_element._connection_handler.execute_command.assert_called_once_with(
        test_command, timeout=60
    )
