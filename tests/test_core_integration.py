"""Integration tests for core WebElement/Tab behaviors (non-iframe)."""

import asyncio
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.elements.web_element import WebElement


class TestCoreFindQuery:
    """Find and query basics on a simple page."""

    @pytest.mark.asyncio
    async def test_find_by_common_selectors(self, ci_chrome_options):
        test_file = Path(__file__).parent / 'pages' / 'test_core_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(0.5)

            # id
            heading = await tab.find(id='main-heading')
            assert heading is not None
            assert isinstance(heading, WebElement)
            assert heading.get_attribute('id') == 'main-heading'

            # class_name (first occurrence)
            first_item = await tab.find(class_name='item')
            assert first_item is not None
            assert 'item' in (first_item.get_attribute('class') or '')

            # name
            name_input = await tab.find(name='username')
            assert name_input is not None
            assert name_input.get_attribute('id') == 'text-input'

            # tag_name (first button)
            button = await tab.find(tag_name='button')
            assert button is not None
            assert button.get_attribute('id') == 'btn-1'

    @pytest.mark.asyncio
    async def test_query_css_and_xpath(self, ci_chrome_options):
        test_file = Path(__file__).parent / 'pages' / 'test_core_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(0.5)

            # CSS: list items
            items = await tab.query('.list-item', find_all=True)
            assert items is not None
            assert len(items) == 3

            # XPath absolute
            deep_span = await tab.query('//*[@id="deep-section"]//span[@id="deep-span"]')
            assert deep_span is not None
            text = await deep_span.text
            assert 'Deep nested element' in text

            # XPath relative from container
            container = await tab.find(id='deep-section')
            rel_span = await container.find(xpath='.//span[@id="deep-span"]')
            assert rel_span is not None
            text2 = await rel_span.text
            assert 'Deep nested element' in text2


class TestCoreClickAndInput:
    """Click and text insertion behaviors."""

    @pytest.mark.asyncio
    async def test_click_increments_counter(self, ci_chrome_options):
        test_file = Path(__file__).parent / 'pages' / 'test_core_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(0.5)

            button = await tab.find(id='btn-1')
            counter = await tab.find(id='btn-1-count')

            # before
            before_text = await counter.text
            assert before_text.strip() == '0'

            await button.click()
            await asyncio.sleep(0.2)
            after_text = await counter.text
            assert after_text.strip() == '1'

            await button.click()
            await asyncio.sleep(0.2)
            after_text2 = await counter.text
            assert after_text2.strip() == '2'

    @pytest.mark.asyncio
    async def test_insert_text_input_and_textarea(self, ci_chrome_options):
        test_file = Path(__file__).parent / 'pages' / 'test_core_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(0.5)

            # input
            input_el = await tab.find(id='text-input')
            await input_el.insert_text('Hello')
            await asyncio.sleep(0.1)
            assert 'Hello' in (input_el.get_attribute('value') or '')

            # textarea
            textarea = await tab.find(id='text-area')
            await textarea.insert_text('World')
            await asyncio.sleep(0.1)
            assert 'World' in (textarea.get_attribute('value') or '')

    @pytest.mark.asyncio
    async def test_select_option_click(self, ci_chrome_options):
        test_file = Path(__file__).parent / 'pages' / 'test_core_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(0.5)

            select_el = await tab.find(id='simple-select')
            assert select_el is not None

            # click on option 'beta'
            opt_beta = await select_el.find(xpath='.//option[@value="beta"]')
            await opt_beta.click()
            await asyncio.sleep(0.2)

            # verify using JS value read
            prop = await select_el.execute_script('return this.value', return_by_value=True)
            current_value = prop['result']['result']['value']
            assert current_value == 'beta'


