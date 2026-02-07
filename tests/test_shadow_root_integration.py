"""Integration tests for Shadow DOM support (open, closed, nested)."""

import asyncio
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.elements.shadow_root import ShadowRoot
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ShadowRootNotFound
from pydoll.protocol.dom.types import ShadowRootType

TEST_PAGE = f'file://{(Path(__file__).parent / "pages" / "shadow_dom_test.html").absolute()}'


class TestOpenShadowRoot:
    """Tests for open shadow root access and element finding."""

    @pytest.mark.asyncio
    async def test_get_shadow_root_open(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='open-host')
            shadow = await host.get_shadow_root()

            assert isinstance(shadow, ShadowRoot)
            assert shadow.mode == ShadowRootType.OPEN
            assert shadow.host_element is host

    @pytest.mark.asyncio
    async def test_find_elements_in_open_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='open-host')
            shadow = await host.get_shadow_root()

            text_el = await shadow.find(class_name='open-text')
            assert isinstance(text_el, WebElement)
            text = await text_el.text
            assert text == 'Open shadow content'

            btn = await shadow.find(id='open-btn')
            assert btn is not None

    @pytest.mark.asyncio
    async def test_query_in_open_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='open-host')
            shadow = await host.get_shadow_root()

            input_el = await shadow.query('input[type="email"]')
            assert input_el is not None

    @pytest.mark.asyncio
    async def test_find_all_in_open_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='open-host')
            shadow = await host.get_shadow_root()

            buttons = await shadow.find(class_name='shadow-btn', find_all=True)
            assert len(buttons) == 1

    @pytest.mark.asyncio
    async def test_inner_html_open(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='open-host')
            shadow = await host.get_shadow_root()

            html = await shadow.inner_html
            assert 'Open shadow content' in html


class TestClosedShadowRoot:
    """Tests for closed shadow root access via CDP bypass."""

    @pytest.mark.asyncio
    async def test_get_shadow_root_closed(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='closed-host')
            shadow = await host.get_shadow_root()

            assert isinstance(shadow, ShadowRoot)
            assert shadow.mode == ShadowRootType.CLOSED

    @pytest.mark.asyncio
    async def test_find_elements_in_closed_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='closed-host')
            shadow = await host.get_shadow_root()

            text_el = await shadow.find(class_name='closed-text')
            assert isinstance(text_el, WebElement)
            text = await text_el.text
            assert text == 'Closed shadow content'

    @pytest.mark.asyncio
    async def test_query_in_closed_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='closed-host')
            shadow = await host.get_shadow_root()

            btn = await shadow.find(id='closed-btn')
            assert btn is not None

            input_el = await shadow.query('input[type="password"]')
            assert input_el is not None

    @pytest.mark.asyncio
    async def test_inner_html_closed(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='closed-host')
            shadow = await host.get_shadow_root()

            html = await shadow.inner_html
            assert 'Closed shadow content' in html


class TestNestedShadowRoots:
    """Tests for nested shadow roots (open -> closed)."""

    @pytest.mark.asyncio
    async def test_nested_open_then_closed(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            nested_host = await tab.find(id='nested-host')
            outer_shadow = await nested_host.get_shadow_root()
            assert outer_shadow.mode == ShadowRootType.OPEN

            outer_text = await outer_shadow.find(class_name='outer-text')
            text = await outer_text.text
            assert text == 'Outer shadow'

            inner_host = await outer_shadow.find(id='inner-host')
            inner_shadow = await inner_host.get_shadow_root()
            assert inner_shadow.mode == ShadowRootType.CLOSED

            inner_text = await inner_shadow.find(class_name='inner-text')
            text = await inner_text.text
            assert text == 'Inner closed shadow'

            deep_btn = await inner_shadow.find(id='deep-btn')
            assert deep_btn is not None


class TestShadowRootNotPresent:
    """Tests for elements without shadow roots."""

    @pytest.mark.asyncio
    async def test_no_shadow_root_raises(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            h1 = await tab.find(tag_name='h1')
            with pytest.raises(ShadowRootNotFound):
                await h1.get_shadow_root()
