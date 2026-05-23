"""Real-Firefox (WebDriver BiDi) integration tests for iframe traversal.

An iframe is searched like any WebElement: find the iframe, then ``.find()``
inside it descends into the iframe's child browsing context (resolved via
``contentWindow``). A cross-iframe selector (one expression spanning the
boundary) takes the same path through the shared segment walker.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from pydoll.browser import Firefox
from pydoll.browser.firefox.options import FirefoxOptions

PAGE = (
    'data:text/html,'
    '<iframe id="frame" srcdoc="'
    "<p id='inner'>hi</p><b class='item'>1</b><b class='item'>2</b>"
    '"></iframe>'
)


@pytest.fixture
def ci_firefox_options():
    options = FirefoxOptions()
    options.headless = True
    options.start_timeout = 60
    return options


@pytest_asyncio.fixture
async def tab(ci_firefox_options):
    async with Firefox(options=ci_firefox_options) as browser:
        yield await browser.start()


class TestIframeTraversal:
    @pytest.mark.asyncio
    async def test_find_inside_iframe_via_element(self, tab):
        await tab.go_to(PAGE)
        frame = await tab.find(id='frame')
        assert frame.is_iframe
        inner = await frame.find(id='inner', timeout=5)
        assert (await inner.text) == 'hi'

    @pytest.mark.asyncio
    async def test_find_all_inside_iframe(self, tab):
        await tab.go_to(PAGE)
        frame = await tab.find(id='frame')
        items = await frame.find(class_name='item', find_all=True, timeout=5)
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_cross_iframe_xpath_selector(self, tab):
        await tab.go_to(PAGE)
        inner = await tab.query("//iframe[@id='frame']//p[@id='inner']", timeout=5)
        assert (await inner.text) == 'hi'
