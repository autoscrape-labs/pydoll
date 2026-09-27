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
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.interactions.iframe import IFrameContext
from pydoll.interactions.mouse import Mouse, MouseTimingConfig
from pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotInteractable,
    ElementNotVisible,
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


def test_iframe_context_docstring_escapes_iframe_tag():
    docstring = WebElement.iframe_context.__doc__
    assert docstring is not None
    assert '``<iframe>``' in docstring


def test_attributes_returns_a_copy(make_element):
    element = make_element(attributes=['id', 'x'])
    snapshot = element.attributes
    snapshot['id'] = 'mutated'
    assert element.id == 'x'


@pytest.mark.asyncio
async def test_inner_html_returns_outer_html(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('DOM.getOuterHTML', {'outerHTML': '<div>hi</div>'})
    assert await element.inner_html() == '<div>hi</div>'
    assert fake_conn.last_command('DOM.getOuterHTML')['params']['objectId'] == 'el-1'


@pytest.mark.asyncio
async def test_bounds_returns_box_model_content(fake_conn, make_element):
    element = make_element()
    quad = [0, 0, 100, 0, 100, 50, 0, 50]
    fake_conn.set_response('DOM.getBoxModel', {'model': {'content': quad}})
    assert await element.bounds() == quad


@pytest.mark.asyncio
async def test_focus_sends_dom_focus_for_object(fake_conn, make_element):
    element = make_element()
    await element.focus()
    assert fake_conn.last_command('DOM.focus')['params']['objectId'] == 'el-1'


@pytest.mark.asyncio
async def test_click_dispatches_press_and_release_at_center(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    fake_conn.set_response(
        'DOM.getBoxModel', {'model': {'content': [0, 0, 100, 0, 100, 50, 0, 50]}}
    )

    await element.click(hold_time=0)

    dispatched = fake_conn.commands_for('Input.dispatchMouseEvent')
    pressed = [e for e in dispatched if e['params']['type'] == 'mousePressed']
    released = [e for e in dispatched if e['params']['type'] == 'mouseReleased']
    assert pressed and (pressed[0]['params']['x'], pressed[0]['params']['y']) == (50, 25)
    assert released and (released[0]['params']['x'], released[0]['params']['y']) == (50, 25)


@pytest.mark.asyncio
async def test_click_press_reads_like_a_real_mouse_button(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    fake_conn.set_response(
        'DOM.getBoxModel', {'model': {'content': [0, 0, 100, 0, 100, 50, 0, 50]}}
    )

    await element.click(hold_time=0)

    dispatched = fake_conn.commands_for('Input.dispatchMouseEvent')
    pressed = next(e['params'] for e in dispatched if e['params']['type'] == 'mousePressed')
    released = next(e['params'] for e in dispatched if e['params']['type'] == 'mouseReleased')
    assert pressed['buttons'] == 1
    assert pressed['force'] == 0.5
    assert 'buttons' not in released
    assert 'force' not in released


@pytest.mark.asyncio
async def test_click_raises_when_element_not_visible(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'button'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(ElementNotVisible):
        await element.click(hold_time=0)
    assert fake_conn.commands_for('Input.dispatchMouseEvent') == []


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
    # insert_text makes two Runtime.callFunctionOn calls:
    # 1. INSERT_TEXT script → returns True (success)
    # 2. read this.value → returns the actual DOM value
    call_count = 0

    async def patched_execute(command, timeout=60):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {'id': 1, 'result': {'result': {'type': 'boolean', 'value': True}}}
        return {'id': 2, 'result': {'result': {'type': 'string', 'value': 'hello'}}}

    fake_conn.execute_command = patched_execute
    await element.insert_text('hello')
    assert element.value == 'hello'


@pytest.mark.asyncio
async def test_insert_text_cache_falls_back_when_reread_fails(fake_conn, make_element):
    """When the re-read of this.value fails, the except block sets value = text."""
    element = make_element(attributes=['tag_name', 'input'])
    call_count = 0

    async def patched_execute(command, timeout=60):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {'id': 1, 'result': {'result': {'type': 'boolean', 'value': True}}}
        raise KeyError('result')

    fake_conn.execute_command = patched_execute
    await element.insert_text('fallback')
    assert element.value == 'fallback'


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


@pytest.mark.asyncio
async def test_scroll_into_view_asks_for_the_box_plus_a_margin(make_element, fake_conn):
    fake_conn.set_response(
        'Runtime.callFunctionOn',
        {'result': {'value': '{"x": 10, "y": 380, "width": 100, "height": 20}'}},
    )
    await make_element().scroll_into_view()
    rect = fake_conn.last_command('DOM.scrollIntoViewIfNeeded')['params']['rect']
    margin = WebElement._SCROLL_INTO_VIEW_MARGIN
    assert rect == {'x': -margin, 'y': -margin, 'width': 100 + 2 * margin, 'height': 20 + 2 * margin}


@pytest.mark.asyncio
async def test_scroll_into_view_falls_back_to_plain_scroll_without_a_box(make_element, fake_conn):
    await make_element().scroll_into_view()
    assert 'rect' not in fake_conn.last_command('DOM.scrollIntoViewIfNeeded')['params']


@pytest.mark.asyncio
async def test_is_detached_reads_is_connected_and_treats_a_lost_object_as_detached(
    fake_conn, make_element
):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    assert await element.is_detached() is False
    assert 'isConnected' in fake_conn.last_command('Runtime.callFunctionOn')['params']['functionDeclaration']
    fake_conn.set_failure('Runtime.callFunctionOn', -32000, 'Could not find object with given id')
    assert await element.is_detached() is True


@pytest.mark.asyncio
async def test_wait_until_hidden_detached_and_enabled(fake_conn, make_element):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    await element.wait_until(is_hidden=True, timeout=1)
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    await element.wait_until(is_detached=True, timeout=1)
    await element.wait_until(is_enabled=True, timeout=1)
    assert 'this.disabled' in fake_conn.last_command('Runtime.callFunctionOn')['params']['functionDeclaration']


@pytest.mark.asyncio
async def test_wait_until_with_no_timeout_checks_once_and_raises(fake_conn, make_element):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    before = len(fake_conn.commands_for('Runtime.callFunctionOn'))
    with pytest.raises(WaitElementTimeout):
        await element.wait_until(is_hidden=True, is_detached=True)
    assert len(fake_conn.commands_for('Runtime.callFunctionOn')) - before == 2


@pytest.mark.asyncio
async def test_wait_until_times_out_and_requires_a_condition(fake_conn, make_element):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    with pytest.raises(WaitElementTimeout):
        await element.wait_until(is_hidden=True, timeout=0.05)
    with pytest.raises(ValueError):
        await element.wait_until()


@pytest.mark.asyncio
async def test_hover_moves_the_mouse_to_the_element_center(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    fake_conn.set_response('DOM.getBoxModel', {'model': {'content': [10, 10, 30, 10, 30, 50, 10, 50]}})

    await element.hover(x_offset=2, y_offset=-3)

    assert fake_conn.commands_for('DOM.scrollIntoViewIfNeeded')
    moved = fake_conn.last_command('Input.dispatchMouseEvent')['params']
    assert moved['type'] == 'mouseMoved'
    assert (moved['x'], moved['y']) == (22, 27)


@pytest.mark.asyncio
async def test_hover_refuses_an_invisible_element(fake_conn, make_element):
    element = make_element()
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': False}})
    with pytest.raises(ElementNotVisible):
        await element.hover()


@pytest.mark.asyncio
async def test_double_click_sends_two_press_release_pairs_with_click_counts(fake_conn, make_element):
    element = make_element(attributes=['tag_name', 'div'])
    fake_conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    fake_conn.set_response('DOM.getBoxModel', {'model': {'content': [0, 0, 100, 0, 100, 50, 0, 50]}})

    await element.double_click()

    events = [e['params'] for e in fake_conn.commands_for('Input.dispatchMouseEvent')]
    assert [(e['type'], e['clickCount']) for e in events] == [
        ('mousePressed', 1),
        ('mouseReleased', 1),
        ('mousePressed', 2),
        ('mouseReleased', 2),
    ]
    assert all((e['x'], e['y']) == (50, 25) for e in events)
    assert events[0]['force'] == 0.5 and events[0]['buttons'] == 1


FAST_MOUSE = MouseTimingConfig(
    frame_interval=0.001,
    frame_interval_variance=0.0,
    min_duration=0.01,
    max_duration=0.02,
    micro_pause_probability=0.0,
    pre_click_pause_min=0.0,
    pre_click_pause_max=0.0,
    click_hold_min=0.0,
    click_hold_max=0.0,
    overshoot_probability=0.0,
)


def _visible_with_box(conn) -> None:
    conn.set_response('Runtime.callFunctionOn', {'result': {'value': True}})
    conn.set_response('DOM.getBoxModel', {'model': {'content': [10, 10, 30, 10, 30, 50, 10, 50]}})


@pytest.mark.asyncio
async def test_an_element_in_an_out_of_process_frame_gets_a_mouse_bound_to_the_frame_session(
    fake_conn,
):
    frame_conn = type(fake_conn)()
    _visible_with_box(frame_conn)
    tab_mouse = Mouse(fake_conn, timing=FAST_MOUSE)
    element = WebElement('el-1', fake_conn, attributes_list=['tag_name', 'div'], mouse=tab_mouse)
    element._iframe_context = IFrameContext(
        frame_id='child', session_handler=frame_conn, session_id='child-session'
    )

    await element.hover(humanize=True)

    frame_mouse = element._input_mouse()
    assert frame_mouse is not tab_mouse
    assert frame_mouse is element._iframe_context.mouse
    assert frame_mouse.timing is tab_mouse.timing
    moves = frame_conn.commands_for('Input.dispatchMouseEvent')
    assert len(moves) > 2
    assert {move['sessionId'] for move in moves} == {'child-session'}
    assert (moves[-1]['params']['x'], moves[-1]['params']['y']) == (20, 30)
    assert not fake_conn.commands_for('Input.dispatchMouseEvent')
    assert tab_mouse._position == (0.0, 0.0)


@pytest.mark.asyncio
async def test_an_element_in_a_same_process_frame_shares_the_tab_mouse(fake_conn):
    _visible_with_box(fake_conn)
    tab_mouse = Mouse(fake_conn, timing=FAST_MOUSE)
    element = WebElement('el-1', fake_conn, attributes_list=['tag_name', 'div'], mouse=tab_mouse)
    element._iframe_context = IFrameContext(frame_id='child', execution_context_id=7)

    assert element._input_mouse() is tab_mouse
    await element.hover(humanize=True)
    assert tab_mouse._position == (20, 30)
    assert element._iframe_context.mouse is None


def test_a_shadow_root_hands_the_host_mouse_to_its_elements(fake_conn):
    tab_mouse = Mouse(fake_conn, timing=FAST_MOUSE)
    host = WebElement('host', fake_conn, attributes_list=['tag_name', 'div'], mouse=tab_mouse)
    assert ShadowRoot('shadow', fake_conn, host_element=host)._mouse is tab_mouse
    assert ShadowRoot('shadow', fake_conn)._mouse is None
