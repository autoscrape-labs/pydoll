"""Real-Chrome integration tests for humanized mouse, scroll and keyboard.

The humanized paths (bezier movement, momentum scrolling, realistic typing with
self-corrected typos) run actual physics with timing, so they are exercised
against a real browser and asserted by their observable effect on the page.
Deterministic dispatch is covered in tests/unit/test_interactions.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition
from pydoll.elements.cdp.web_element import WebElement

PAGE_URL = f'file://{(Path(__file__).parent / "pages" / "web_element.html").absolute()}'


async def _live(element_or_tab, expression: str):
    if isinstance(element_or_tab, WebElement):
        result = await element_or_tab.execute_script(
            f'return {expression}', return_by_value=True
        )
        return result['result']['result']['value']
    return await element_or_tab.execute_script(f'return {expression}')


@pytest_asyncio.fixture
async def page_tab(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        await tab.go_to(PAGE_URL)
        yield tab


@pytest.mark.asyncio
async def test_humanized_mouse_click_triggers_button(page_tab):
    button = await page_tab.find(id='btn')
    bounds = await button.get_bounds_using_js()
    center_x = bounds['x'] + bounds['width'] / 2
    center_y = bounds['y'] + bounds['height'] / 2

    await page_tab.mouse.click(center_x, center_y, humanize=True)

    counter = await page_tab.find(id='clicks')
    assert (await counter.text) == '1'


@pytest.mark.asyncio
async def test_humanized_scroll_moves_the_page_down(page_tab):
    assert await _live(page_tab, 'window.scrollY') == 0
    await page_tab.scroll.by(ScrollPosition.DOWN, 800, humanize=True)
    assert await _live(page_tab, 'window.scrollY') > 0


@pytest.mark.asyncio
async def test_humanized_typing_fills_the_input(page_tab):
    field = await page_tab.find(id='text-input')
    await field.clear()
    await field.type_text('hello', humanize=True)
    assert await _live(field, 'this.value') == 'hello'
