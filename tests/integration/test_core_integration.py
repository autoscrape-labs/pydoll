"""Integration tests for core WebElement/Tab behaviors (non-iframe)."""

from pathlib import Path

import pytest

from _waits import wait_for_element_text, wait_for_js, wait_for_js_value
from pydoll.browser.chromium import Chrome
from pydoll.elements.cdp.web_element import WebElement

PAGE = f'file://{(Path(__file__).parent / "pages" / "test_core_simple.html").absolute()}'


class TestCoreFindQuery:
    """Find and query basics on a simple page."""

    @pytest.mark.asyncio
    async def test_find_by_common_selectors(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            # id
            heading = await tab.find(id='main-heading', timeout=5)
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
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            # CSS: list items
            items = await tab.query('.list-item', find_all=True, timeout=5)
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
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            button = await tab.find(id='btn-1', timeout=5)
            counter = await tab.find(id='btn-1-count')
            assert (await counter.text).strip() == '0'

            await button.click()
            await wait_for_element_text(counter, '1')

            await button.click()
            await wait_for_element_text(counter, '2')

    @pytest.mark.asyncio
    async def test_insert_text_input_and_textarea(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            input_el = await tab.find(id='text-input', timeout=5)
            await input_el.insert_text('Hello')
            await wait_for_js_value(input_el, 'this.value', 'Hello')

            textarea = await tab.find(id='text-area')
            await textarea.insert_text('World')
            await wait_for_js_value(textarea, 'this.value', 'World')

    @pytest.mark.asyncio
    async def test_clear_input_and_textarea(self, ci_chrome_options):
        """Test clear() removes existing value from input and textarea."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            # -- input: insert text, clear, verify empty, insert again --
            input_el = await tab.find(id='text-input', timeout=5)
            await input_el.insert_text('old value')
            await wait_for_js_value(input_el, 'this.value', 'old value')

            await input_el.clear()
            await wait_for_js_value(input_el, 'this.value', '')

            await input_el.insert_text('new value')
            await wait_for_js_value(input_el, 'this.value', 'new value')

            # -- textarea: insert text, clear, verify empty --
            textarea = await tab.find(id='text-area')
            await textarea.insert_text('old message')
            await wait_for_js_value(textarea, 'this.value', 'old message')

            await textarea.clear()
            await wait_for_js_value(textarea, 'this.value', '')

    @pytest.mark.asyncio
    async def test_select_option_click(self, ci_chrome_options):
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            select_el = await tab.find(id='simple-select', timeout=5)
            assert select_el is not None

            # click on option 'beta'
            opt_beta = await select_el.find(xpath='.//option[@value="beta"]')
            await opt_beta.click()

            # verify using JS value read
            await wait_for_js_value(select_el, 'this.value', 'beta')


class TestCoreTypeText:
    """Integration tests for type_text (keyboard-based input)."""

    @pytest.mark.asyncio
    async def test_type_text_into_input(self, ci_chrome_options):
        """type_text should insert characters via keyboard events."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            input_el = await tab.find(id='text-input', timeout=5)
            await input_el.type_text('hello123')

            await wait_for_js_value(input_el, 'this.value', 'hello123')

    @pytest.mark.asyncio
    async def test_type_text_humanized_into_input(self, ci_chrome_options):
        """type_text with humanize=True should produce the same result."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            input_el = await tab.find(id='text-input', timeout=5)
            await input_el.type_text('Test!', humanize=True)

            # Humanized typing may introduce and self-correct typos; the final
            # value should still be the intended text.
            await wait_for_js_value(input_el, 'this.value', 'Test!')

    @pytest.mark.asyncio
    async def test_type_text_symbols_and_punctuation(self, ci_chrome_options):
        """type_text should handle symbols, digits, and punctuation."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            input_el = await tab.find(id='text-input', timeout=5)
            test_text = 'user@example.com'
            await input_el.type_text(test_text)

            await wait_for_js_value(input_el, 'this.value', test_text)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        'text,label',
        [
            ('abcdefghijklmnopqrstuvwxyz', 'lowercase'),
            ('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'uppercase'),
            ('0123456789', 'digits'),
            ('-=[];\',./', 'punctuation_unshifted'),
            ('!@#$%^&*()_+{}|:"<>?~', 'punctuation_shifted'),
        ],
    )
    async def test_type_text_all_character_groups(self, ci_chrome_options, text, label):
        """type_text should correctly type every mapped character group."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(PAGE)

            input_el = await tab.find(id='text-input', timeout=5)
            await input_el.type_text(text)

            await wait_for_js(
                input_el,
                'this.value',
                lambda value: value == text,
                message=f'Failed for {label}: {text!r}',
            )
