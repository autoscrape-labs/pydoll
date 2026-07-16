"""Real-Firefox (WebDriver BiDi) integration tests for the WebElement API.

Mirrors the applicable parts of
tests/cdp/integration/test_web_element_integration.py against a live Firefox:
finding, clicking (trusted + humanized), typing, option selection, traversal,
visibility, scrolling and screenshots — asserted by the observable effect on the
page (refactor-resistant). The shared fixture page is tests/pages/web_element.html.
"""

from __future__ import annotations

import pytest
import pytest_asyncio


@pytest_asyncio.fixture(loop_scope='module')
async def element_tab(tab, page_url):
    """A Firefox tab on the shared WebElement fixture page."""
    await tab.go_to(page_url('web_element.html'))
    return tab


async def _live(tab, expression: str):
    """Read a live JS value from the page (BiDi execute_script returns it directly)."""
    return await tab.execute_script(f'return {expression}')


@pytest.mark.asyncio(loop_scope='module')
async def test_find_returns_element_with_text(element_tab):
    title = await element_tab.find(id='title')
    assert (await title.text) == 'WebElement Test Page'


@pytest.mark.asyncio(loop_scope='module')
async def test_query_css_selector_finds_element(element_tab):
    button = await element_tab.query('#btn')
    assert button.id == 'btn'


@pytest.mark.asyncio(loop_scope='module')
async def test_find_all_returns_every_match(element_tab):
    kids = await element_tab.find(class_name='kid', find_all=True)
    assert len(kids) == 3


@pytest.mark.asyncio(loop_scope='module')
async def test_click_triggers_dom_side_effect(element_tab):
    await (await element_tab.find(id='btn')).click()
    assert (await (await element_tab.find(id='clicks')).text) == '1'


@pytest.mark.asyncio(loop_scope='module')
async def test_humanized_click_triggers_dom_side_effect(element_tab):
    await (await element_tab.find(id='btn')).click(humanize=True)
    assert (await (await element_tab.find(id='clicks')).text) == '1'


@pytest.mark.asyncio(loop_scope='module')
async def test_type_text_reflects_in_live_value(element_tab):
    field = await element_tab.find(id='text-input')
    await field.clear()
    await field.type_text('hello')
    assert await _live(element_tab, "document.getElementById('text-input').value") == 'hello'


@pytest.mark.asyncio(loop_scope='module')
async def test_clicking_option_selects_it(element_tab):
    await (await element_tab.find(id='opt-b')).click()
    assert await _live(element_tab, "document.getElementById('select').value") == 'b'


@pytest.mark.asyncio(loop_scope='module')
async def test_visibility_flags(element_tab):
    assert await (await element_tab.find(id='visible')).is_visible() is True
    assert await (await element_tab.find(id='hidden')).is_visible() is False


@pytest.mark.asyncio(loop_scope='module')
async def test_interactability_flags(element_tab):
    assert await (await element_tab.find(id='btn')).is_interactable() is True
    assert await (await element_tab.find(id='hidden')).is_interactable() is False


@pytest.mark.asyncio(loop_scope='module')
async def test_cached_attributes_value_and_tag(element_tab):
    field = await element_tab.find(id='text-input')
    assert field.tag_name == 'input'
    assert field.get_attribute('id') == 'text-input'
    assert field.value == 'initial'


@pytest.mark.asyncio(loop_scope='module')
async def test_traversal_parent_children_siblings(element_tab):
    first_child = await element_tab.find(id='c1')

    parent = await first_child.get_parent_element()
    assert parent.get_attribute('id') == 'parent'

    children = await parent.get_children_elements()
    assert {child.get_attribute('id') for child in children} == {'c1', 'c2', 'c3'}

    siblings = await first_child.get_siblings_elements()
    assert {sibling.get_attribute('id') for sibling in siblings} == {'c2', 'c3'}


@pytest.mark.asyncio(loop_scope='module')
async def test_scroll_into_view_brings_element_down(element_tab):
    assert await _live(element_tab, 'window.scrollY') == 0
    await (await element_tab.find(id='bottom-btn')).scroll_into_view()
    assert await _live(element_tab, 'window.scrollY') > 0


@pytest.mark.asyncio(loop_scope='module')
async def test_take_screenshot_returns_image_data(element_tab):
    button = await element_tab.find(id='btn')
    data = await button.take_screenshot(as_base64=True)
    assert isinstance(data, str)
    assert len(data) > 0
