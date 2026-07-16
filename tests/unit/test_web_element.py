"""Pure-logic and translate-only WebElement tests against a FakeConnection.

Cached-attribute properties and the coordinate math are pure; the command
methods (inner_html, bounds, click, clear, insert_text, focus, execute_script)
run through the in-memory FakeConnection, asserting the command emitted and the
resulting state. Real DOM behaviour (visibility, layout, traversal, screenshots)
is covered by the real-Chrome integration suite.
"""

from __future__ import annotations

import pytest

from pydoll.constants import By
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotInteractable,
    InvalidFileExtension,
    MissingScreenshotPath,
    WaitElementTimeout,
)


@pytest.fixture
def make_element(fake_conn):
    def _make(object_id: str = 'el-1', attributes=None) -> WebElement:
        return WebElement(
            object_id=object_id,
            connection_handler=fake_conn,
            attributes_list=attributes or [],
        )

    return _make


def test_attribute_properties_read_from_cache(make_element):
    element = make_element(
        attributes=['id', 'go', 'class', 'btn primary', 'value', 'Go', 'tag_name', 'button']
    )
    assert element.id == 'go'
    assert element.class_name == 'btn primary'
    assert element.value == 'Go'
    assert element.tag_name == 'button'


def test_get_attribute_maps_class_and_handles_missing(make_element):
    element = make_element(attributes=['class', 'card', 'id', 'x'])
    assert element.get_attribute('class') == 'card'
    assert element.get_attribute('id') == 'x'
    assert element.get_attribute('data-missing') is None


def test_is_enabled_reflects_disabled_attribute(make_element):
    assert make_element(attributes=['tag_name', 'input']).is_enabled is True
    assert make_element(attributes=['tag_name', 'input', 'disabled', '']).is_enabled is False


def test_is_iframe_reflects_tag_name(make_element):
    assert make_element(attributes=['tag_name', 'iframe']).is_iframe is True
    assert make_element(attributes=['tag_name', 'div']).is_iframe is False


def test_attributes_returns_a_copy(make_element):
    element = make_element(attributes=['id', 'x'])
    snapshot = element.attributes
    snapshot['id'] = 'mutated'
    assert element.id == 'x'


@pytest.mark.asyncio
async def test_inner_html_returns_outer_html(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('DOM.getOuterHTML', {'outerHTML': '<div>hi</div>'})
    assert await element.inner_html == '<div>hi</div>'
    assert fake_conn.last_command('DOM.getOuterHTML')['params']['objectId'] == 'el-1'


@pytest.mark.asyncio
async def test_bounds_returns_box_model_content(fake_conn, make_element):
    element = make_element()
    quad = [0, 0, 100, 0, 100, 50, 0, 50]
    fake_conn.set_response('DOM.getBoxModel', {'model': {'content': quad}})
    assert await element.bounds == quad


@pytest.mark.asyncio
async def test_focus_sends_dom_focus_for_object(fake_conn, make_element):
    element = make_element()
    await element.focus()
    assert fake_conn.last_command('DOM.focus')['params']['objectId'] == 'el-1'


@pytest.mark.asyncio
async def test_click_dispatches_press_and_release_at_center(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    fake_conn.set_response('DOM.getBoxModel', {'model': {'content': [0, 0, 100, 0, 100, 50, 0, 50]}})

    await element.click(hold_time=0)

    dispatched = fake_conn.commands_for('Input.dispatchMouseEvent')
    pressed = [e for e in dispatched if e['params']['type'] == 'mousePressed']
    released = [e for e in dispatched if e['params']['type'] == 'mouseReleased']
    assert pressed and (pressed[0]['params']['x'], pressed[0]['params']['y']) == (50, 25)
    assert released and (released[0]['params']['x'], released[0]['params']['y']) == (50, 25)


@pytest.mark.asyncio
async def test_click_raises_when_element_not_visible(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(WaitElementTimeout):
        await element.click(hold_time=0)
    assert fake_conn.commands_for('Input.dispatchMouseEvent') == []


@pytest.mark.asyncio
async def test_click_using_js_raises_when_element_not_visible(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(WaitElementTimeout):
        await element.click_using_js()


@pytest.mark.asyncio
async def test_click_negative_timeout_raises(make_element):
    element = make_element(attributes=['tag_name', 'button'])
    with pytest.raises(ValueError, match='timeout must be greater than or equal to 0'):
        await element.click(timeout=-1)


@pytest.mark.asyncio
async def test_click_using_js_negative_timeout_raises(make_element):
    element = make_element(attributes=['tag_name', 'button'])
    with pytest.raises(ValueError, match='timeout must be greater than or equal to 0'):
        await element.click_using_js(timeout=-1)


@pytest.mark.asyncio
async def test_clear_updates_cached_value(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'input', 'value', 'old'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    await element.clear()
    assert element.value == ''


@pytest.mark.asyncio
async def test_clear_raises_when_element_rejects_input(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(ElementNotInteractable):
        await element.clear()


@pytest.mark.asyncio
async def test_insert_text_updates_cached_value(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'input'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    await element.insert_text('hello')
    assert element.value == 'hello'


@pytest.mark.asyncio
async def test_insert_text_raises_when_element_rejects_input(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(ElementNotInteractable):
        await element.insert_text('hello')


@pytest.mark.asyncio
async def test_execute_script_wraps_script_and_targets_object(fake_conn, make_element):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': 'hi'}})
    await element.execute_script('return this.textContent', return_by_value=True)
    sent = fake_conn.last_command('Runtime.callFunctionOn')
    assert sent['params']['functionDeclaration'] == 'function(){ return this.textContent }'
    assert sent['params']['objectId'] == 'el-1'


@pytest.mark.asyncio
async def test_set_input_files_rejects_non_file_input(make_element):
    text_input = make_element(attributes=['tag_name', 'input', 'type', 'text'])
    with pytest.raises(ElementNotAFileInput):
        await text_input.set_input_files('/tmp/file.txt')


@pytest.mark.asyncio
async def test_take_screenshot_without_path_or_base64_raises(make_element):
    element = make_element()
    with pytest.raises(MissingScreenshotPath):
        await element.take_screenshot()


@pytest.mark.asyncio
async def test_take_screenshot_with_invalid_extension_raises(make_element):
    element = make_element()
    with pytest.raises(InvalidFileExtension):
        await element.take_screenshot(path='shot.xyz')


def test_is_option_tag_reads_cached_tag_name(make_element):
    assert make_element(attributes=['tag_name', 'option'])._is_option_tag() is True
    assert make_element(attributes=['tag_name', 'div'])._is_option_tag() is False
    assert make_element()._is_option_tag() is False


@pytest.mark.asyncio
async def test_is_option_element_uses_cached_tag_name(make_element):
    option = make_element(attributes=['tag_name', 'option'])
    button = make_element(attributes=['tag_name', 'button'])
    assert await option._is_option_element() is True
    assert await button._is_option_element() is False


@pytest.mark.asyncio
async def test_is_option_element_infers_from_tag_name_selector(fake_conn):
    element = WebElement(
        object_id='el-1',
        connection_handler=fake_conn,
        method=By.TAG_NAME,
        selector='option',
    )
    assert await element._is_option_element() is True
    assert fake_conn.commands_for('Runtime.callFunctionOn') == []


@pytest.mark.asyncio
async def test_is_option_element_infers_from_xpath_selector(fake_conn):
    element = WebElement(
        object_id='el-1',
        connection_handler=fake_conn,
        method=By.XPATH,
        selector='//select/option[2]',
    )
    assert await element._is_option_element() is True
    assert fake_conn.commands_for('Runtime.callFunctionOn') == []


@pytest.mark.asyncio
async def test_is_option_element_falls_back_to_js_and_caches_tag(fake_conn):
    element = WebElement(
        object_id='el-1',
        connection_handler=fake_conn,
        method=By.CSS_SELECTOR,
        selector='#some-option',
    )
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    assert await element._is_option_element() is True
    assert element.tag_name == 'option'


@pytest.mark.asyncio
async def test_is_option_element_js_fallback_returns_false(fake_conn):
    element = WebElement(
        object_id='el-1',
        connection_handler=fake_conn,
        method=By.CSS_SELECTOR,
        selector='#not-an-option',
    )
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    assert await element._is_option_element() is False
    assert element.tag_name is None


@pytest.mark.asyncio
async def test_get_children_returns_empty_when_script_yields_no_object(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': None}})
    assert await element.get_children_elements() == []


@pytest.mark.asyncio
async def test_click_falls_back_to_js_bounds_when_box_model_missing(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response(
        'Runtime.callFunctionOn',
        {'result': {'value': '{"x": 10, "y": 20, "width": 40, "height": 30}'}},
    )
    fake_conn.set_response('DOM.getBoxModel', {})

    await element.click(hold_time=0)

    dispatched = fake_conn.commands_for('Input.dispatchMouseEvent')
    pressed = [event for event in dispatched if event['params']['type'] == 'mousePressed']
    assert pressed
    assert (pressed[0]['params']['x'], pressed[0]['params']['y']) == (30, 35)
