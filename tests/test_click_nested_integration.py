"""Integration tests for click() on nested elements (shadow DOM, iframes)."""

import asyncio
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.elements.web_element import WebElement

TEST_PAGE = f'file://{(Path(__file__).parent / "pages" / "test_click_nested.html").absolute()}'


class TestClickRegularElement:
    """Baseline: click() on a normal page element."""

    @pytest.mark.asyncio
    async def test_click_regular_button(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            btn = await tab.find(id='regular-btn')
            counter = await tab.find(id='regular-btn-count')

            text_before = await counter.text
            assert text_before == '0'

            await btn.click()
            await asyncio.sleep(0.2)

            text_after = await counter.text
            assert text_after == '1'

    @pytest.mark.asyncio
    async def test_click_regular_button_multiple_times(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            btn = await tab.find(id='regular-btn')
            counter = await tab.find(id='regular-btn-count')

            for i in range(3):
                await btn.click()
                await asyncio.sleep(0.15)

            text = await counter.text
            assert text == '3'


class TestClickInShadowRoot:
    """click() on elements inside a shadow root."""

    @pytest.mark.asyncio
    async def test_click_button_in_shadow_root(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='shadow-host')
            shadow = await host.get_shadow_root()

            btn = await shadow.query('#shadow-btn')
            counter = await shadow.query('#shadow-btn-count')

            text_before = await counter.text
            assert text_before == '0'

            await btn.click()
            await asyncio.sleep(0.2)

            text_after = await counter.text
            assert text_after == '1'

    @pytest.mark.asyncio
    async def test_find_text_in_shadow_root(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            host = await tab.find(id='shadow-host')
            shadow = await host.get_shadow_root()

            text_el = await shadow.query('.shadow-text')
            assert isinstance(text_el, WebElement)
            text = await text_el.text
            assert text == 'Content inside shadow root'


class TestClickInNestedShadowRoots:
    """click() on elements inside nested shadow roots (outer open -> inner closed)."""

    @pytest.mark.asyncio
    async def test_click_button_in_nested_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            outer_host = await tab.find(id='nested-shadow-host')
            outer_shadow = await outer_host.get_shadow_root()

            inner_host = await outer_shadow.query('#inner-shadow-host')
            inner_shadow = await inner_host.get_shadow_root()

            btn = await inner_shadow.query('#deep-btn')
            counter = await inner_shadow.query('#deep-btn-count')

            text_before = await counter.text
            assert text_before == '0'

            await btn.click()
            await asyncio.sleep(0.2)

            text_after = await counter.text
            assert text_after == '1'

    @pytest.mark.asyncio
    async def test_find_text_in_nested_shadow(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(0.5)

            outer_host = await tab.find(id='nested-shadow-host')
            outer_shadow = await outer_host.get_shadow_root()

            outer_text = await outer_shadow.query('.outer-text')
            assert 'Outer shadow content' == await outer_text.text

            inner_host = await outer_shadow.query('#inner-shadow-host')
            inner_shadow = await inner_host.get_shadow_root()

            inner_text = await inner_shadow.query('.inner-text')
            assert 'Inner shadow content' == await inner_text.text


class TestClickInIframe:
    """click() on elements inside an iframe."""

    @pytest.mark.asyncio
    async def test_click_button_in_iframe(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(1)

            iframe = await tab.find(id='test-iframe')
            assert iframe.is_iframe

            btn = await iframe.find(id='iframe-btn')
            counter = await iframe.find(id='iframe-btn-count')

            text_before = await counter.text
            assert text_before == '0'

            await btn.click()
            await asyncio.sleep(0.3)

            text_after = await counter.text
            assert text_after == '1'


class TestClickInShadowRootInsideIframe:
    """click() on elements in a shadow root that lives inside an iframe."""

    @pytest.mark.asyncio
    async def test_click_shadow_button_inside_iframe(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(1)

            iframe = await tab.find(id='test-iframe')
            shadow_host = await iframe.find(id='shadow-host-in-iframe')
            shadow = await shadow_host.get_shadow_root()

            btn = await shadow.query('#shadow-btn-in-iframe')
            counter = await shadow.query('#shadow-btn-count')

            text_before = await counter.text
            assert text_before == '0'

            await btn.click()
            await asyncio.sleep(0.3)

            text_after = await counter.text
            assert text_after == '1'

    @pytest.mark.asyncio
    async def test_find_text_in_shadow_inside_iframe(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(TEST_PAGE)
            await asyncio.sleep(1)

            iframe = await tab.find(id='test-iframe')
            shadow_host = await iframe.find(id='shadow-host-in-iframe')
            shadow = await shadow_host.get_shadow_root()

            text_el = await shadow.query('.shadow-text')
            text = await text_el.text
            assert text == 'Shadow content inside iframe'
