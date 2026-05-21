"""Real-Chrome integration tests for the WebElement DOM-facing API.

These drive an actual browser against a fixture page to exercise the behaviour
that depends on a live DOM and layout: clicking, typing, traversal, visibility
and interactability, scrolling, screenshots, option selection, file inputs and
keyboard dispatch. Pure logic and command-shape glue live in the unit suite
(tests/unit/test_web_element.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key
from pydoll.elements.web_element import WebElement

PAGE_URL = f'file://{(Path(__file__).parent / "pages" / "web_element.html").absolute()}'


async def _live(element_or_tab, expression: str):
    """Read a live JS value from an element or tab via execute_script."""
    result = await element_or_tab.execute_script(f'return {expression}', return_by_value=True)
    return result['result']['result']['value']


@pytest_asyncio.fixture
async def element_tab(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.go_to(PAGE_URL)
        yield tab


@pytest.mark.asyncio
async def test_click_triggers_dom_side_effect(element_tab):
    button = await element_tab.find(id='btn')
    await button.click()
    counter = await element_tab.find(id='clicks')
    assert (await counter.text) == '1'


@pytest.mark.asyncio
async def test_click_using_js_triggers_handler(element_tab):
    button = await element_tab.find(id='js-btn')
    await button.click_using_js()
    result = await element_tab.find(id='js-clicks')
    assert (await result.text) == 'clicked'


@pytest.mark.asyncio
async def test_type_text_reflects_in_live_value(element_tab):
    field = await element_tab.find(id='text-input')
    await field.clear()
    await field.type_text('hello')
    assert await _live(field, 'this.value') == 'hello'


@pytest.mark.asyncio
async def test_insert_text_and_clear_update_value(element_tab):
    field = await element_tab.find(id='text-input')
    await field.clear()
    await field.insert_text('world')
    assert field.value == 'world'
    assert await _live(field, 'this.value') == 'world'

    await field.clear()
    assert field.value == ''
    assert await _live(field, 'this.value') == ''


@pytest.mark.xfail(
    reason='insert_text caches the inserted text as the whole value; on a non-empty '
    'field the real DOM value is the existing text plus the insertion, so the '
    'cached element.value diverges from the DOM',
    strict=False,
)
@pytest.mark.asyncio
async def test_insert_text_cached_value_matches_dom_on_nonempty_field(element_tab):
    field = await element_tab.find(id='text-input')
    await field.insert_text('world')
    assert field.value == await _live(field, 'this.value')


@pytest.mark.asyncio
async def test_traversal_parent_children_siblings(element_tab):
    first_child = await element_tab.find(id='c1')

    parent = await first_child.get_parent_element()
    assert parent.get_attribute('id') == 'parent'

    children = await parent.get_children_elements()
    assert {child.get_attribute('id') for child in children} == {'c1', 'c2', 'c3'}

    siblings = await first_child.get_siblings_elements()
    assert {sibling.get_attribute('id') for sibling in siblings} == {'c2', 'c3'}


@pytest.mark.asyncio
async def test_visibility_and_state_flags(element_tab):
    visible = await element_tab.find(id='visible')
    hidden = await element_tab.find(id='hidden')
    assert await visible.is_visible() is True
    assert await hidden.is_visible() is False
    assert await visible.is_on_top() is True

    enabled_field = await element_tab.find(id='text-input')
    disabled_field = await element_tab.find(id='disabled-input')
    assert enabled_field.is_enabled is True
    assert disabled_field.is_enabled is False

    title = await element_tab.find(id='title')
    assert await enabled_field.is_editable() is True
    assert await title.is_editable() is False

    button = await element_tab.find(id='btn')
    assert await button.is_interactable() is True


@pytest.mark.asyncio
async def test_scroll_into_view_brings_element_down(element_tab):
    bottom = await element_tab.find(id='bottom-btn')
    assert await _live(element_tab, 'window.scrollY') == 0
    await bottom.scroll_into_view()
    assert await _live(element_tab, 'window.scrollY') > 0
    await bottom.wait_until(is_visible=True, timeout=2)


@pytest.mark.asyncio
async def test_take_screenshot_returns_image_bytes(element_tab):
    import base64

    title = await element_tab.find(id='title')
    data = await title.take_screenshot(as_base64=True)
    assert data
    assert len(base64.b64decode(data)) > 100


@pytest.mark.asyncio
async def test_clicking_option_selects_it(element_tab):
    option = await element_tab.find(id='opt-b')
    await option.click()
    selected = await element_tab.find(id='select-value')
    assert (await selected.text) == 'b'


@pytest.mark.asyncio
async def test_set_input_files_attaches_file(element_tab):
    file_input = await element_tab.find(id='file-input')
    await file_input.set_input_files(str(Path(__file__)))
    assert await _live(file_input, 'this.files.length') == 1


@pytest.mark.asyncio
async def test_press_keyboard_key_dispatches_to_focused_element(element_tab):
    key_input = await element_tab.find(id='key-input')
    await key_input.click()
    with pytest.warns(DeprecationWarning):
        await key_input.press_keyboard_key(Key.ENTER)
    assert 'Enter' in await _live(element_tab, "document.getElementById('key-log').textContent")


@pytest.mark.asyncio
async def test_text_inner_html_and_bounds(element_tab):
    title = await element_tab.find(id='title')
    assert (await title.text) == 'WebElement Test Page'
    assert '<h1' in (await title.inner_html)

    bounds = await title.get_bounds_using_js()
    assert bounds['width'] > 0
    assert bounds['height'] > 0
    assert isinstance(await title.bounds, list)
