"""Integration tests for iframe functionality in WebElement.

These tests use real HTML files and Chrome browser to test iframe interactions,
element finding, and DOM manipulation within iframes.
"""

from pathlib import Path

import pytest

from _waits import wait_for_js, wait_for_js_value, wait_until
from pydoll.browser.chromium import Chrome
from pydoll.commands import RuntimeCommands
from pydoll.elements.cdp.web_element import WebElement
from pydoll.exceptions import ElementNotFound, InvalidIFrame


class TestSimpleIframeIntegration:
    """Integration tests for simple iframe operations."""

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_id(self, ci_chrome_options):
        """Test finding an element inside an iframe by id."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find the iframe element
            iframe_element = await tab.find(id='simple-iframe', timeout=5)
            assert iframe_element is not None
            assert iframe_element.is_iframe

            # Get iframe context
            iframe_context = await iframe_element.iframe_context
            assert iframe_context is not None
            assert iframe_context.frame_id is not None
            assert iframe_context.execution_context_id is not None

            # Find element inside iframe
            heading_in_iframe = await iframe_element.find(id='iframe-heading', timeout=5)
            assert heading_in_iframe is not None
            assert isinstance(heading_in_iframe, WebElement)

            # Verify the element text
            text = await heading_in_iframe.text
            assert 'Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_multiple_elements_in_iframe(self, ci_chrome_options):
        """Test finding multiple elements inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find all links inside iframe
            links = await iframe_element.query('.iframe-link', find_all=True, timeout=5)
            assert len(links) == 3

            # Verify each link
            for i, link in enumerate(links, 1):
                link_id = link.get_attribute('id')
                assert link_id == f'iframe-link{i}'

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_css_selector(self, ci_chrome_options):
        """Test finding elements in iframe using CSS selectors."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find by class
            action_buttons = await iframe_element.query('.action-btn', find_all=True, timeout=5)
            assert len(action_buttons) >= 2  # At least 2 visible buttons

            # Find by tag
            inputs = await iframe_element.query('input[type="text"]', find_all=True)
            assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_xpath(self, ci_chrome_options):
        """Test finding elements in iframe using XPath."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find by XPath
            paragraph = await iframe_element.find(xpath='//p[@id="iframe-paragraph"]', timeout=5)
            assert paragraph is not None

            text = await paragraph.text
            assert 'content inside the iframe' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_iframe_input(self, ci_chrome_options):
        """Test inserting text into an input field inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find input inside iframe
            input_element = await iframe_element.find(id='iframe-input', timeout=5)
            assert input_element is not None

            # Insert text
            test_text = 'Test User Name'
            await input_element.insert_text(test_text)

            # Verify text was inserted
            value = input_element.get_attribute('value')
            assert test_text in value

    @pytest.mark.asyncio
    async def test_insert_text_in_iframe_textarea(self, ci_chrome_options):
        """Test inserting text into a textarea inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find textarea inside iframe
            textarea = await iframe_element.find(id='iframe-textarea', timeout=5)
            assert textarea is not None

            # Insert new text (textarea initially empty)
            new_message = 'This is a new test message'
            await textarea.insert_text(new_message)

            # Verify text was inserted
            value = textarea.get_attribute('value')
            assert new_message in value

    @pytest.mark.asyncio
    async def test_click_button_in_iframe(self, ci_chrome_options):
        """Test clicking a button inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find button inside iframe
            button = await iframe_element.find(id='iframe-button1', timeout=5)
            assert button is not None

            # Click the button (should not raise exception)
            await button.click()

    @pytest.mark.asyncio
    async def test_get_inner_html_of_iframe(self, ci_chrome_options):
        """Test getting inner HTML of an iframe element."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Get inner HTML of the iframe
            inner_html = await iframe_element.inner_html
            assert inner_html is not None
            assert len(inner_html) > 0
            assert 'iframe-heading' in inner_html
            assert 'Iframe Content' in inner_html

    @pytest.mark.asyncio
    async def test_get_inner_html_of_element_in_iframe(self, ci_chrome_options):
        """Test getting inner HTML of an element inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find container inside iframe
            container = await iframe_element.find(id='iframe-container', timeout=5)
            assert container is not None

            # Get inner HTML
            inner_html = await container.inner_html
            assert inner_html is not None
            assert 'iframe-paragraph' in inner_html
            assert 'iframe-form' in inner_html

    @pytest.mark.asyncio
    async def test_get_children_elements_in_iframe(self, ci_chrome_options):
        """Test getting children elements of an element inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find list inside iframe
            list_element = await iframe_element.find(id='iframe-list', timeout=5)
            assert list_element is not None

            # Get list items using tag filter to avoid relying on class attributes
            list_items = await list_element.get_children_elements(max_depth=2, tag_filter=['li'])
            assert len(list_items) == 3

    @pytest.mark.asyncio
    async def test_element_visibility_in_iframe(self, ci_chrome_options):
        """Test checking element visibility inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find visible button
            visible_button = await iframe_element.find(id='iframe-button1', timeout=5)
            is_visible = await visible_button.is_visible()
            assert is_visible is True

            # Find hidden button
            hidden_button = await iframe_element.find(id='iframe-button3')
            is_hidden = await hidden_button.is_visible()
            assert is_hidden is False


class TestNestedIframeIntegration:
    """Integration tests for nested iframe operations."""

    @pytest.mark.asyncio
    async def test_find_element_in_parent_iframe(self, ci_chrome_options):
        """Test finding an element in parent iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)
            assert parent_iframe is not None
            assert parent_iframe.is_iframe

            # Find element in parent iframe
            parent_heading = await parent_iframe.find(id='parent-iframe-heading', timeout=5)
            assert parent_heading is not None

            text = await parent_heading.text
            assert 'Parent Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_nested_iframe_element(self, ci_chrome_options):
        """Test finding the nested iframe element inside parent iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)

            # Find nested iframe inside parent iframe
            nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)
            assert nested_iframe is not None
            assert nested_iframe.is_iframe

    @pytest.mark.asyncio
    async def test_find_element_in_nested_iframe(self, ci_chrome_options):
        """Test finding an element in nested iframe (iframe within iframe)."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)

            # Find nested iframe inside parent
            nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)
            assert nested_iframe is not None

            # Find element in nested iframe
            nested_heading = await nested_iframe.find(id='nested-iframe-heading', timeout=5)
            assert nested_heading is not None

            text = await nested_heading.text
            assert 'Nested Iframe Content' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_nested_iframe(self, ci_chrome_options):
        """Test inserting text into input field in nested iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)
            nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

            # Find input in nested iframe
            nested_input = await nested_iframe.find(id='nested-input', timeout=5)
            assert nested_input is not None

            # Insert text
            test_text = 'Nested Input Test'
            await nested_input.insert_text(test_text)

            # Verify
            value = nested_input.get_attribute('value')
            assert test_text in value

    @pytest.mark.asyncio
    async def test_find_multiple_elements_in_nested_iframe(self, ci_chrome_options):
        """Test finding multiple elements in nested iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)
            nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

            # Find all links in nested iframe
            links = await nested_iframe.query('a', find_all=True, timeout=5)
            assert len(links) == 2

            # Verify link IDs
            link_ids = [link.get_attribute('id') for link in links]
            assert 'nested-link1' in link_ids
            assert 'nested-link2' in link_ids

    @pytest.mark.asyncio
    async def test_submit_form_in_nested_iframe(self, ci_chrome_options):
        """Test interacting with form elements in nested iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe', timeout=5)
            nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

            # Fill form fields
            username_input = await nested_iframe.find(id='nested-form-input', timeout=5)
            await username_input.insert_text('testuser')

            password_input = await nested_iframe.find(id='nested-form-password')
            await password_input.insert_text('password123')

            # Verify values
            assert 'testuser' in username_input.get_attribute('value')
            assert 'password123' in password_input.get_attribute('value')

            # Click submit button
            submit_button = await nested_iframe.find(id='nested-form-submit')
            await submit_button.click()


class TestIframeElementInteraction:
    """Integration tests for various element interactions within iframes."""

    @pytest.mark.asyncio
    async def test_select_option_in_iframe(self, ci_chrome_options):
        """Test selecting an option in a select element inside iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find select element
            select_element = await iframe_element.find(id='iframe-select', timeout=5)
            assert select_element is not None

            # Select option2 by clicking the option element
            option2 = await select_element.find(xpath='.//option[@value="option2"]')
            await option2.click()
            # Verify via property read (execute_script)
            await wait_for_js_value(select_element, 'this.value', 'option2')
            prop_val = await select_element.execute_script('return this.value', return_by_value=True)
            current_value = prop_val['result']['result']['value']
            assert current_value == 'option2'

            # Select different option (option3) by clicking it
            option3 = await select_element.find(xpath='.//option[@value="option3"]')
            await option3.click()
            await wait_for_js_value(select_element, 'this.value', 'option3')
            prop_val2 = await select_element.execute_script('return this.value', return_by_value=True)
            new_value = prop_val2['result']['result']['value']
            assert new_value == 'option3'

    @pytest.mark.asyncio
    async def test_get_attributes_from_iframe_elements(self, ci_chrome_options):
        """Test getting various attributes from elements in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Get link attributes
            link = await iframe_element.find(id='iframe-link1', timeout=5)
            href = link.get_attribute('href')
            assert href is not None
            assert '#link1' in href

            link_class = link.get_attribute('class')
            assert 'iframe-link' in link_class

            # Get input attributes
            input_elem = await iframe_element.find(id='iframe-input')
            input_type = input_elem.get_attribute('type')
            assert input_type == 'text'

            placeholder = input_elem.get_attribute('placeholder')
            assert 'name' in placeholder.lower()

    @pytest.mark.asyncio
    async def test_deep_nested_element_search_in_iframe(self, ci_chrome_options):
        """Test finding deeply nested elements inside iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find deeply nested element
            deep_span = await iframe_element.find(id='deep-span', timeout=5)
            assert deep_span is not None

            text = await deep_span.text
            assert 'Deep nested element' in text


    @pytest.mark.asyncio
    async def test_wait_for_element_in_iframe(self, ci_chrome_options):
        """Test waiting for element to appear in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Wait for element (should already exist)
            element = await iframe_element.find(
                id='iframe-paragraph', timeout=5
            )
            assert element is not None

            text = await element.text
            assert 'content inside the iframe' in text

    @pytest.mark.asyncio
    async def test_element_not_found_in_iframe(self, ci_chrome_options):
        """Test that ElementNotFound is raised for non-existent elements in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Try to find non-existent element
            with pytest.raises(ElementNotFound):
                await iframe_element.find(id='non-existent-element')

    @pytest.mark.asyncio
    async def test_clear_input_in_iframe(self, ci_chrome_options):
        """Test clearing input field in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Find input and add text
            input_elem = await iframe_element.find(id='iframe-input', timeout=5)
            await input_elem.insert_text('Test text to clear')

            await input_elem.insert_text('')
            value = input_elem.get_attribute('value')
            assert value in ('', None)

    @pytest.mark.asyncio
    async def test_multiple_iframes_on_same_page(self, ci_chrome_options):
        """Test handling multiple iframes on the same page."""
        # Create a test page with multiple iframes
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find main content (not in iframe)
            main_heading = await tab.find(id='main-heading', timeout=5)
            assert main_heading is not None
            main_text = await main_heading.text
            assert 'Main Page' in main_text

            # Find content in iframe
            iframe_element = await tab.find(id='simple-iframe')
            iframe_heading = await iframe_element.find(id='iframe-heading', timeout=5)
            iframe_text = await iframe_heading.text
            assert 'Iframe Content' in iframe_text

            # Verify they are different
            assert main_text != iframe_text

    @pytest.mark.asyncio
    async def test_iframe_context_persistence(self, ci_chrome_options):
        """Test that iframe context persists across multiple operations."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Get context first time
            context1 = await iframe_element.iframe_context
            assert context1 is not None

            # Perform some operations
            element1 = await iframe_element.find(id='iframe-heading', timeout=5)
            await element1.text

            # Get context again
            context2 = await iframe_element.iframe_context
            assert context2 is not None

            # Verify contexts are consistent
            assert context1.frame_id == context2.frame_id
            assert context1.execution_context_id == context2.execution_context_id

    @pytest.mark.asyncio
    async def test_get_text_from_multiple_elements_in_iframe(self, ci_chrome_options):
        """Test getting text from multiple elements in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Get all list items
            list_items = await iframe_element.query('.list-item', find_all=True, timeout=5)
            assert len(list_items) == 3

            # Get text from each
            texts = []
            for item in list_items:
                text = await item.text
                texts.append(text)

            # Verify texts
            assert 'Item 1' in texts[0]
            assert 'Item 2' in texts[1]
            assert 'Item 3' in texts[2]


class TestMultipleIframesSelection:
    """Integration tests for selecting the correct iframe when multiple iframes exist."""

    @pytest.mark.asyncio
    async def test_find_specific_iframe_by_id_among_multiple(self, ci_chrome_options):
        """Test finding a specific iframe by ID when multiple iframes exist on the page."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find all iframes
            all_iframes = await tab.find(tag_name='iframe', find_all=True, timeout=5)
            assert len(all_iframes) == 3, "Should have 3 iframes on the page"

            # Find specific iframe by ID
            login_iframe = await tab.find(id='login-iframe')
            assert login_iframe is not None
            assert login_iframe.is_iframe
            assert login_iframe.get_attribute('id') == 'login-iframe'

            # Verify we can access content in the correct iframe
            iframe_context = await login_iframe.iframe_context
            assert iframe_context is not None
            assert iframe_context.frame_id is not None

    @pytest.mark.asyncio
    async def test_find_elements_in_correct_iframe_among_multiple(self, ci_chrome_options):
        """Test that elements are found in the correct iframe when multiple exist."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Get the login iframe specifically
            login_iframe = await tab.find(id='login-iframe', timeout=5)

            # Find elements inside the login iframe
            heading = await login_iframe.find(id='iframe-heading', timeout=5)
            assert heading is not None

            text = await heading.text
            assert 'Iframe Content' in text

            # Verify we can find multiple elements
            buttons = await login_iframe.find(class_name='action-btn', find_all=True)
            assert len(buttons) >= 2

    @pytest.mark.asyncio
    async def test_different_iframes_have_different_contexts(self, ci_chrome_options):
        """Test that different iframes have distinct frame contexts even with same content."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Get two different iframes
            cookie_iframe = await tab.find(id='cookie-iframe', timeout=5)
            login_iframe = await tab.find(id='login-iframe')

            # Both should be iframes
            assert cookie_iframe.is_iframe
            assert login_iframe.is_iframe

            # Get their contexts
            cookie_ctx = await cookie_iframe.iframe_context
            login_ctx = await login_iframe.iframe_context

            # Frame IDs should be different (distinct iframe contexts)
            assert cookie_ctx.frame_id != login_ctx.frame_id

            # Both should be able to find elements in their respective content
            cookie_heading = await cookie_iframe.find(id='iframe-heading')
            login_heading = await login_iframe.find(id='iframe-heading')

            assert cookie_heading is not None
            assert login_heading is not None

            # The element object IDs should be different (different DOM instances)
            assert cookie_heading._object_id != login_heading._object_id

    @pytest.mark.asyncio
    async def test_iframe_selection_by_data_attribute(self, ci_chrome_options):
        """Test selecting iframe by custom data attribute."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find iframe by data-purpose attribute using xpath
            login_iframe = await tab.find(xpath='//iframe[@data-purpose="login"]', timeout=5)
            assert login_iframe is not None
            assert login_iframe.get_attribute('id') == 'login-iframe'

            # Verify we can interact with it
            form = await login_iframe.find(id='iframe-form')
            assert form is not None

    @pytest.mark.asyncio
    async def test_iterate_over_multiple_iframes(self, ci_chrome_options):
        """Test iterating over multiple iframes and accessing each one's content."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find all iframes
            all_iframes = await tab.find(tag_name='iframe', find_all=True, timeout=5)
            assert len(all_iframes) == 3

            # Each iframe should have accessible content
            for iframe in all_iframes:
                assert iframe.is_iframe

                # Get context for each iframe
                ctx = await iframe.iframe_context
                assert ctx is not None
                assert ctx.frame_id is not None

                # Each should have an iframe-heading
                heading = await iframe.find(id='iframe-heading', raise_exc=False)
                # At least the content iframes should have the heading
                if heading:
                    text = await heading.text
                    assert len(text) > 0

    @pytest.mark.asyncio
    async def test_find_in_iframe_after_finding_in_another(self, ci_chrome_options):
        """Test finding elements in one iframe after finding in another."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # First, find element in cookie iframe
            cookie_iframe = await tab.find(id='cookie-iframe', timeout=5)
            cookie_heading = await cookie_iframe.find(id='iframe-heading', timeout=5)
            cookie_text = await cookie_heading.text

            # Then, find element in login iframe
            login_iframe = await tab.find(id='login-iframe')
            login_heading = await login_iframe.find(id='iframe-heading')
            login_text = await login_heading.text

            # Both should work independently
            assert 'Iframe Content' in cookie_text
            assert 'Iframe Content' in login_text

            # Now find in analytics iframe
            analytics_iframe = await tab.find(id='analytics-iframe')
            analytics_heading = await analytics_iframe.find(id='iframe-heading')
            analytics_text = await analytics_heading.text

            assert 'Iframe Content' in analytics_text


class TestIframeEdgeCases:
    """Integration tests for edge cases in iframe handling."""

    @pytest.mark.asyncio
    async def test_dynamic_content_in_iframe(self, ci_chrome_options):
        """Test finding dynamically added content in iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Add dynamic content via JavaScript
            iframe_context = await iframe_element.iframe_context
            await tab.execute_protocol_command(
                RuntimeCommands.evaluate(
                    expression="""
                const div = document.createElement('div');
                div.id = 'dynamic-element';
                div.textContent = 'Dynamic Content';
                document.body.appendChild(div);
                """,
                    context_id=iframe_context.execution_context_id,
                )
            )

            # Find dynamically added element
            dynamic_element = await iframe_element.find(id='dynamic-element', timeout=5)
            assert dynamic_element is not None

            text = await dynamic_element.text
            assert 'Dynamic Content' in text

    @pytest.mark.asyncio
    async def test_iframe_reload_handling(self, ci_chrome_options):
        """Test that iframe context is properly handled after page reload."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Find iframe and element
            iframe_element = await tab.find(id='simple-iframe', timeout=5)
            element_before = await iframe_element.find(id='iframe-heading', timeout=5)
            assert element_before is not None

            # Reload page
            await tab.refresh()

            # Find iframe again (new instance)
            iframe_element_after = await tab.find(id='simple-iframe', timeout=5)
            element_after = await iframe_element_after.find(id='iframe-heading', timeout=5)
            assert element_after is not None

            # Verify element is accessible
            text = await element_after.text
            assert 'Iframe Content' in text


class TestIframeTypeText:
    """Integration tests for type_text inside iframes."""

    @pytest.mark.asyncio
    async def test_type_text_in_iframe_input(self, ci_chrome_options):
        """type_text should work inside an iframe input."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)
            input_el = await iframe_element.find(id='iframe-input', timeout=5)

            await input_el.type_text('hello')

            await wait_for_js_value(input_el, 'this.value', 'hello')
            prop = await input_el.execute_script(
                'return this.value', return_by_value=True
            )
            assert prop['result']['result']['value'] == 'hello'

    @pytest.mark.asyncio
    async def test_type_text_humanized_in_iframe_input(self, ci_chrome_options):
        """type_text with humanize=True should work inside an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)
            input_el = await iframe_element.find(id='iframe-input', timeout=5)

            await input_el.type_text('Test', humanize=True)

            # Humanized typing may introduce and correct typos,
            # but the final value should be non-empty.
            await wait_for_js(
                input_el, 'this.value', lambda value: len(value) >= 2
            )
            prop = await input_el.execute_script(
                'return this.value', return_by_value=True
            )
            value = prop['result']['result']['value']
            assert len(value) >= 2

    @pytest.mark.asyncio
    async def test_type_text_email_in_iframe_input(self, ci_chrome_options):
        """type_text should handle symbols like @ and . inside iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)
            input_el = await iframe_element.find(id='iframe-email', timeout=5)

            test_text = 'user@test.com'
            await input_el.type_text(test_text)

            await wait_for_js_value(input_el, 'this.value', test_text)
            prop = await input_el.execute_script(
                'return this.value', return_by_value=True
            )
            assert prop['result']['result']['value'] == test_text


class TestFrameElementIntegration:
    """Integration tests for <frame> elements (frameset pages)."""

    @pytest.mark.asyncio
    async def test_frame_element_is_iframe(self, ci_chrome_options):
        """Test that a <frame> element is recognized as an iframe."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            frame_element = await tab.find(id='left-frame', timeout=5)
            assert frame_element is not None
            assert frame_element.tag_name == 'frame'
            assert frame_element.is_iframe

    @pytest.mark.asyncio
    async def test_find_element_inside_frame(self, ci_chrome_options):
        """Test finding an element inside a <frame> element."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            frame_element = await tab.find(id='left-frame', timeout=5)
            heading = await frame_element.find(id='frame-heading', timeout=5)
            assert heading is not None

            text = await heading.text
            assert 'Frame Content' in text

    @pytest.mark.asyncio
    async def test_frame_context_is_resolved(self, ci_chrome_options):
        """Test that iframe_context works for <frame> elements."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            frame_element = await tab.find(id='left-frame', timeout=5)
            ctx = await frame_element.iframe_context
            assert ctx is not None
            assert ctx.frame_id is not None
            assert ctx.execution_context_id is not None

    @pytest.mark.asyncio
    async def test_inner_html_of_frame(self, ci_chrome_options):
        """Test that inner_html works for <frame> elements."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            frame_element = await tab.find(id='left-frame', timeout=5)
            html = await frame_element.inner_html
            assert 'frame-heading' in html

    @pytest.mark.asyncio
    async def test_multiple_frames_in_frameset(self, ci_chrome_options):
        """Test interacting with multiple <frame> elements in a frameset."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            left_frame = await tab.find(id='left-frame', timeout=5)
            right_frame = await tab.find(id='right-frame', timeout=5)

            assert left_frame.is_iframe
            assert right_frame.is_iframe

            # Left frame has frame-specific content
            left_heading = await left_frame.find(id='frame-heading', timeout=5)
            left_text = await left_heading.text
            assert 'Frame Content' in left_text

            # Right frame has iframe content (reuses test_iframe_content.html)
            right_heading = await right_frame.find(id='iframe-heading', timeout=5)
            right_text = await right_heading.text
            assert 'Iframe Content' in right_text

    @pytest.mark.asyncio
    async def test_type_text_in_frame_input(self, ci_chrome_options):
        """Test typing text into an input inside a <frame> element."""
        test_file = Path(__file__).parents[2] / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            frame_element = await tab.find(id='left-frame', timeout=5)
            input_el = await frame_element.find(id='frame-input', timeout=5)

            test_text = 'hello frame'
            await input_el.type_text(test_text)

            await wait_for_js_value(input_el, 'this.value', test_text)
            prop = await input_el.execute_script(
                'return this.value', return_by_value=True
            )
            assert prop['result']['result']['value'] == test_text


class TestIframeContextResolutionFailures:
    """Integration tests for iframe context resolution failure paths.

    These exercise the resolver's defensive branches with a real browser:
    when the <iframe> element handle becomes stale (removed from the DOM or
    its remote object released), context resolution must surface a clear
    ``InvalidIFrame`` instead of silently returning a broken context.
    """

    @pytest.mark.asyncio
    async def test_iframe_context_raises_after_iframe_removed_from_dom(
        self, ci_chrome_options
    ):
        """Resolving context for an iframe removed from the DOM raises InvalidIFrame.

        After removal ``DOM.describeNode`` still returns the (now detached)
        node but with no ``frameId``; the owner lookup over the frame tree
        finds no matching frame, so the resolver cannot determine a frameId
        and raises.
        """
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            # Sanity check: context resolves while the iframe is in the DOM.
            ctx_before = await iframe_element.iframe_context
            assert ctx_before is not None
            assert ctx_before.frame_id is not None

            # Remove the iframe from the DOM (round-trips, so the mutation is
            # committed before resolution is attempted again).
            await tab.execute_script(
                "document.getElementById('simple-iframe').remove();"
            )

            async def context_resolution_fails() -> bool:
                try:
                    await iframe_element.iframe_context
                    return False
                except InvalidIFrame:
                    return True

            await wait_until(
                context_resolution_fails,
                timeout=5,
                message='iframe_context did not raise after removal',
            )

            with pytest.raises(InvalidIFrame):
                await iframe_element.iframe_context

    @pytest.mark.asyncio
    async def test_iframe_context_raises_when_remote_object_released(
        self, ci_chrome_options
    ):
        """Releasing the iframe's remote object makes context resolution raise.

        ``Runtime.releaseObject`` invalidates the element's ``objectId``; the
        subsequent ``DOM.describeNode`` returns an error, the resolver falls
        back to an empty node (no frameId, no backendNodeId) and ultimately
        raises ``InvalidIFrame``.
        """
        test_file = Path(__file__).parents[2] / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='simple-iframe', timeout=5)

            await tab._connection_handler.execute_command(
                RuntimeCommands.release_object(object_id=iframe_element._object_id)
            )

            with pytest.raises(InvalidIFrame):
                await iframe_element.iframe_context

    @pytest.mark.asyncio
    async def test_no_src_iframe_resolves_about_blank_context(self, ci_chrome_options):
        """A srcless <iframe> (about:blank) still resolves a usable context.

        Its ``contentDocument.frameId`` is null, so resolution goes through the
        frame-owner lookup (matching the iframe's backendNodeId against the
        page frame tree) rather than the direct contentDocument path.
        """
        test_file = Path(__file__).parents[2] / 'pages' / 'iframe_features.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            iframe_element = await tab.find(id='frame-no-src', timeout=5)
            assert iframe_element.is_iframe

            ctx = await iframe_element.iframe_context
            assert ctx is not None
            assert ctx.frame_id is not None
            assert ctx.execution_context_id is not None

            # The resolved frame is the empty about:blank document; we can
            # create elements in it via the resolved execution context.
            await tab.execute_protocol_command(
                RuntimeCommands.evaluate(
                    expression="""
                const marker = document.createElement('div');
                marker.id = 'about-blank-marker';
                marker.textContent = 'blank ok';
                document.body.appendChild(marker);
                """,
                    context_id=ctx.execution_context_id,
                )
            )
            marker = await iframe_element.find(id='about-blank-marker', timeout=5)
            assert 'blank ok' in await marker.text
