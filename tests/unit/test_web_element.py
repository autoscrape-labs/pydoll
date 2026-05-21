"""Pure-logic and translate-only WebElement tests against a FakeConnection.

Cached-attribute properties and the coordinate math are pure; the command
methods (inner_html, bounds, click, clear, insert_text, focus, execute_script)
run through the in-memory FakeConnection, asserting the command emitted and the
resulting state. Real DOM behaviour (visibility, layout, traversal, screenshots)
is covered by the real-Chrome integration suite.
"""

from __future__ import annotations

import pytest

from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ElementNotInteractable


@pytest.fixture
def make_element(fake_conn):
    def _make(object_id: str = 'el-1', attributes=None) -> WebElement:
        return WebElement(
            object_id=object_id,
            connection_handler=fake_conn,
            attributes_list=attributes or [],
        )

    return _make



def test_calculate_center_averages_quad_corners():
    assert WebElement._calculate_center([0, 0, 100, 0, 100, 50, 0, 50]) == (50.0, 25.0)


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
    assert [event['params']['type'] for event in dispatched] == ['mousePressed', 'mouseReleased']
    assert all(event['params']['x'] == 50 and event['params']['y'] == 25 for event in dispatched)


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
