"""Real-Firefox (WebDriver BiDi) integration tests for trusted mouse/scroll/keyboard.

The humanized BiDi input paths run through input.performActions (events report
isTrusted=true), asserted by their observable effect on the page — the BiDi
counterpart of tests/cdp/integration/test_interactions_integration.py. The shared
fixture page is tests/pages/web_element.html.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from pydoll.constants import ScrollPosition


@pytest_asyncio.fixture
async def page_tab(tab, page_url):
    """A Firefox tab on the shared WebElement fixture page."""
    await tab.go_to(page_url('web_element.html'))
    return tab


async def _live(tab, expression: str):
    return await tab.execute_script(f'return {expression}')


@pytest.mark.asyncio
async def test_humanized_mouse_click_triggers_button(page_tab):
    button = await page_tab.find(id='btn')
    bounds = await button.get_bounds_using_js()
    center_x = bounds['x'] + bounds['width'] / 2
    center_y = bounds['y'] + bounds['height'] / 2

    await page_tab.mouse.click(center_x, center_y, humanize=True)

    assert (await (await page_tab.find(id='clicks')).text) == '1'


@pytest.mark.asyncio
async def test_humanized_scroll_moves_the_page_down(page_tab):
    assert await _live(page_tab, 'window.scrollY') == 0
    await page_tab.scroll.by(ScrollPosition.DOWN, 800, humanize=True)
    assert await _live(page_tab, 'window.scrollY') > 0


@pytest.mark.asyncio
async def test_keyboard_dispatches_trusted_key_events(page_tab):
    field = await page_tab.find(id='key-input')
    await field.click()
    await page_tab.keyboard.type_text('ab')
    assert await _live(page_tab, "document.getElementById('key-log').textContent") == 'ab'
