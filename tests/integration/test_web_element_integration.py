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
from pydoll.elements.cdp.web_element import WebElement
from pydoll.exceptions import (
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    ShadowRootNotFound,
    WaitElementTimeout,
)

PAGE_URL = f'file://{(Path(__file__).parent / "pages" / "web_element.html").absolute()}'


async def _live(element_or_tab, expression: str):
    """Read a live JS value from an element or tab via execute_script."""
    if isinstance(element_or_tab, WebElement):
        result = await element_or_tab.execute_script(
            f'return {expression}', return_by_value=True
        )
        return result['result']['result']['value']
    return await element_or_tab.execute_script(f'return {expression}')


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


@pytest.mark.asyncio
async def test_get_shadow_root_returns_traversable_root(element_tab):
    host = await element_tab.find(id='shadow-host')
    shadow_root = await host.get_shadow_root()
    inner = await shadow_root.query('#shadow-btn')
    assert (await inner.text) == 'inside shadow'


@pytest.mark.asyncio
async def test_get_shadow_root_raises_when_absent(element_tab):
    plain = await element_tab.find(id='no-shadow')
    with pytest.raises(ShadowRootNotFound):
        await plain.get_shadow_root()


@pytest.mark.asyncio
async def test_get_shadow_root_with_timeout_waits_for_late_attachment(element_tab):
    host = await element_tab.find(id='shadow-host-late')
    shadow_root = await host.get_shadow_root(timeout=3)
    inner = await shadow_root.query('#late-shadow')
    assert (await inner.text) == 'late shadow content'


@pytest.mark.asyncio
async def test_get_shadow_root_with_timeout_raises_when_never_attached(element_tab):
    plain = await element_tab.find(id='no-shadow')
    with pytest.raises(WaitElementTimeout):
        await plain.get_shadow_root(timeout=1)


@pytest.mark.asyncio
async def test_get_parent_element_raises_for_root_element(element_tab):
    root = await element_tab.find(tag_name='html')
    with pytest.raises(ElementNotFound):
        await root.get_parent_element()


@pytest.mark.asyncio
async def test_humanized_click_triggers_dom_side_effect(element_tab):
    button = await element_tab.find(id='btn')
    await button.click(humanize=True)
    counter = await element_tab.find(id='clicks')
    assert (await counter.text) == '1'


@pytest.mark.asyncio
async def test_click_using_js_raises_when_element_not_interactable(element_tab):
    disabled_button = await element_tab.find(id='disabled-btn')
    assert await disabled_button.is_visible() is True
    with pytest.raises(ElementNotInteractable):
        await disabled_button.click_using_js()


@pytest.mark.asyncio
async def test_get_children_elements_raise_exc_when_empty(element_tab):
    empty = await element_tab.find(id='empty-parent')
    assert await empty.get_children_elements() == []
    with pytest.raises(ElementNotFound):
        await empty.get_children_elements(raise_exc=True)


@pytest.mark.asyncio
async def test_get_siblings_elements_raise_exc_when_alone(element_tab):
    only_child = await element_tab.find(id='only-child')
    assert await only_child.get_siblings_elements() == []
    with pytest.raises(ElementNotFound):
        await only_child.get_siblings_elements(raise_exc=True)


@pytest.mark.asyncio
async def test_take_screenshot_saves_file_to_disk(element_tab, tmp_path):
    title = await element_tab.find(id='title')
    destination = tmp_path / 'element.png'
    result = await title.take_screenshot(path=destination)
    assert result is None
    assert destination.exists()
    assert destination.stat().st_size > 100
    assert destination.read_bytes().startswith(b'\x89PNG')


@pytest.mark.asyncio
async def test_take_screenshot_normalizes_jpg_extension(element_tab, tmp_path):
    title = await element_tab.find(id='title')
    destination = tmp_path / 'element.jpg'
    await title.take_screenshot(path=str(destination))
    assert destination.exists()
    assert destination.read_bytes()[:3] == b'\xff\xd8\xff'


@pytest.mark.asyncio
async def test_wait_until_requires_a_condition(element_tab):
    title = await element_tab.find(id='title')
    with pytest.raises(ValueError):
        await title.wait_until(timeout=1)


@pytest.mark.asyncio
async def test_wait_until_interactable_times_out_on_hidden_element(element_tab):
    hidden = await element_tab.find(id='hidden')
    with pytest.raises(WaitElementTimeout):
        await hidden.wait_until(is_interactable=True, timeout=1)


@pytest.mark.asyncio
async def test_wait_until_interactable_returns_when_element_becomes_interactable(element_tab):
    await element_tab.execute_script(
        "var b = document.createElement('button');"
        "b.id = 'delayed-btn';"
        "b.textContent = 'soon';"
        "b.style.display = 'none';"
        "document.body.insertBefore(b, document.body.firstChild);"
        "setTimeout(function () { b.style.display = 'block'; }, 800);"
    )
    button = await element_tab.find(id='delayed-btn')
    await button.wait_until(is_visible=True, is_interactable=True, timeout=5)
    assert await button.is_interactable() is True


@pytest.mark.asyncio
async def test_click_using_js_selects_option(element_tab):
    option = await element_tab.find(id='opt-y')
    await option.click_using_js()
    value = await _live(element_tab, "document.getElementById('select-js').value")
    assert value == 'y'


@pytest.mark.asyncio
async def test_click_using_js_raises_when_element_not_visible(element_tab):
    hidden_button = await element_tab.find(id='hidden-btn')
    with pytest.raises(ElementNotVisible):
        await hidden_button.click_using_js()


@pytest.mark.asyncio
async def test_state_flags_false_after_context_invalidated(element_tab):
    button = await element_tab.find(id='btn')
    assert await button.is_visible() is True
    await element_tab.go_to('about:blank')
    assert await button.is_visible() is False
    assert await button.is_on_top() is False
    assert await button.is_interactable() is False


@pytest.mark.asyncio
async def test_iframe_context_is_none_for_non_iframe(element_tab):
    title = await element_tab.find(id='title')
    assert await title.iframe_context is None


@pytest.mark.asyncio
async def test_bounds_raises_key_error_for_element_without_box_model(element_tab):
    contents_only = await element_tab.find(id='contents-only')
    with pytest.raises(KeyError):
        await contents_only.bounds
