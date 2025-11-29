"""Integration tests for iframe functionality in WebElement.

These tests use real HTML files and Chrome browser to test iframe interactions,
element finding, and DOM manipulation within iframes.
"""

import asyncio
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ElementNotFound, InvalidIFrame


class TestSimpleIframeIntegration:
    """Integration tests for simple iframe operations."""

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_id(self, ci_chrome_options):
        """Test finding an element inside an iframe by id."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)

            # Wait for iframe to load
            await asyncio.sleep(1)

            # Find the iframe element
            iframe_element = await tab.find(id='simple-iframe')
            assert iframe_element is not None
            assert iframe_element.is_iframe

            # Get iframe context
            iframe_context = await iframe_element.iframe_context
            assert iframe_context is not None
            assert iframe_context.frame_id is not None
            assert iframe_context.execution_context_id is not None

            # Find element inside iframe
            heading_in_iframe = await iframe_element.find(id='iframe-heading')
            assert heading_in_iframe is not None
            assert isinstance(heading_in_iframe, WebElement)

            # Verify the element text
            text = await heading_in_iframe.text
            assert 'Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_multiple_elements_in_iframe(self, ci_chrome_options):
        """Test finding multiple elements inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find all links inside iframe
            links = await iframe_element.query('.iframe-link', find_all=True)
            assert len(links) == 3

            # Verify each link
            for i, link in enumerate(links, 1):
                link_id = link.get_attribute('id')
                assert link_id == f'iframe-link{i}'

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_css_selector(self, ci_chrome_options):
        """Test finding elements in iframe using CSS selectors."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find by class
            action_buttons = await iframe_element.query('.action-btn', find_all=True)
            assert len(action_buttons) >= 2  # At least 2 visible buttons

            # Find by tag
            inputs = await iframe_element.query('input[type="text"]', find_all=True)
            assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_xpath(self, ci_chrome_options):
        """Test finding elements in iframe using XPath."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find by XPath
            paragraph = await iframe_element.find(xpath='//p[@id="iframe-paragraph"]')
            assert paragraph is not None

            text = await paragraph.text
            assert 'content inside the iframe' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_iframe_input(self, ci_chrome_options):
        """Test inserting text into an input field inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find input inside iframe
            input_element = await iframe_element.find(id='iframe-input')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find textarea inside iframe
            textarea = await iframe_element.find(id='iframe-textarea')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find button inside iframe
            button = await iframe_element.find(id='iframe-button1')
            assert button is not None

            # Click the button (should not raise exception)
            await button.click()
            await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_get_inner_html_of_iframe(self, ci_chrome_options):
        """Test getting inner HTML of an iframe element."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Get inner HTML of the iframe
            inner_html = await iframe_element.inner_html
            assert inner_html is not None
            assert len(inner_html) > 0
            assert 'iframe-heading' in inner_html
            assert 'Iframe Content' in inner_html

    @pytest.mark.asyncio
    async def test_get_inner_html_of_element_in_iframe(self, ci_chrome_options):
        """Test getting inner HTML of an element inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find container inside iframe
            container = await iframe_element.find(id='iframe-container')
            assert container is not None

            # Get inner HTML
            inner_html = await container.inner_html
            assert inner_html is not None
            assert 'iframe-paragraph' in inner_html
            assert 'iframe-form' in inner_html

    @pytest.mark.asyncio
    async def test_get_children_elements_in_iframe(self, ci_chrome_options):
        """Test getting children elements of an element inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find list inside iframe
            list_element = await iframe_element.find(id='iframe-list')
            assert list_element is not None

            # Get list items using tag filter to avoid relying on class attributes
            list_items = await list_element.get_children_elements(max_depth=2, tag_filter=['li'])
            assert len(list_items) == 3

    @pytest.mark.asyncio
    async def test_element_visibility_in_iframe(self, ci_chrome_options):
        """Test checking element visibility inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find visible button
            visible_button = await iframe_element.find(id='iframe-button1')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1.5)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe')
            assert parent_iframe is not None
            assert parent_iframe.is_iframe

            # Find element in parent iframe
            parent_heading = await parent_iframe.find(id='parent-iframe-heading')
            assert parent_heading is not None

            text = await parent_heading.text
            assert 'Parent Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_nested_iframe_element(self, ci_chrome_options):
        """Test finding the nested iframe element inside parent iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1.5)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe')

            # Find nested iframe inside parent iframe
            nested_iframe = await parent_iframe.find(id='nested-iframe')
            assert nested_iframe is not None
            assert nested_iframe.is_iframe

    @pytest.mark.asyncio
    async def test_find_element_in_nested_iframe(self, ci_chrome_options):
        """Test finding an element in nested iframe (iframe within iframe)."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(2)

            # Find parent iframe
            parent_iframe = await tab.find(id='parent-iframe')

            # Find nested iframe inside parent
            nested_iframe = await parent_iframe.find(id='nested-iframe')
            assert nested_iframe is not None

            # Find element in nested iframe
            nested_heading = await nested_iframe.find(id='nested-iframe-heading')
            assert nested_heading is not None

            text = await nested_heading.text
            assert 'Nested Iframe Content' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_nested_iframe(self, ci_chrome_options):
        """Test inserting text into input field in nested iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(2)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe')
            nested_iframe = await parent_iframe.find(id='nested-iframe')

            # Find input in nested iframe
            nested_input = await nested_iframe.find(id='nested-input')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(2)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe')
            nested_iframe = await parent_iframe.find(id='nested-iframe')

            # Find all links in nested iframe
            links = await nested_iframe.query('a', find_all=True)
            assert len(links) == 2

            # Verify link IDs
            link_ids = [link.get_attribute('id') for link in links]
            assert 'nested-link1' in link_ids
            assert 'nested-link2' in link_ids

    @pytest.mark.asyncio
    async def test_submit_form_in_nested_iframe(self, ci_chrome_options):
        """Test interacting with form elements in nested iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(2)

            # Navigate to nested iframe
            parent_iframe = await tab.find(id='parent-iframe')
            nested_iframe = await parent_iframe.find(id='nested-iframe')

            # Fill form fields
            username_input = await nested_iframe.find(id='nested-form-input')
            await username_input.insert_text('testuser')

            password_input = await nested_iframe.find(id='nested-form-password')
            await password_input.insert_text('password123')

            # Verify values
            assert 'testuser' in username_input.get_attribute('value')
            assert 'password123' in password_input.get_attribute('value')

            # Click submit button
            submit_button = await nested_iframe.find(id='nested-form-submit')
            await submit_button.click()
            await asyncio.sleep(0.5)


class TestIframeElementInteraction:
    """Integration tests for various element interactions within iframes."""

    @pytest.mark.asyncio
    async def test_select_option_in_iframe(self, ci_chrome_options):
        """Test selecting an option in a select element inside iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find select element
            select_element = await iframe_element.find(id='iframe-select')
            assert select_element is not None

            # Select option2 by clicking the option element
            option2 = await select_element.find(xpath='.//option[@value="option2"]')
            await option2.click()
            await asyncio.sleep(0.2)
            # Verify via property read (execute_script)
            prop_val = await select_element.execute_script('return this.value', return_by_value=True)
            current_value = prop_val['result']['result']['value']
            assert current_value == 'option2'

            # Select different option (option3) by clicking it
            option3 = await select_element.find(xpath='.//option[@value="option3"]')
            await option3.click()
            await asyncio.sleep(0.2)
            prop_val2 = await select_element.execute_script('return this.value', return_by_value=True)
            new_value = prop_val2['result']['result']['value']
            assert new_value == 'option3'

    @pytest.mark.asyncio
    async def test_get_attributes_from_iframe_elements(self, ci_chrome_options):
        """Test getting various attributes from elements in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Get link attributes
            link = await iframe_element.find(id='iframe-link1')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find deeply nested element
            deep_span = await iframe_element.find(id='deep-span')
            assert deep_span is not None

            text = await deep_span.text
            assert 'Deep nested element' in text


    @pytest.mark.asyncio
    async def test_wait_for_element_in_iframe(self, ci_chrome_options):
        """Test waiting for element to appear in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Try to find non-existent element
            with pytest.raises(ElementNotFound):
                await iframe_element.find(id='non-existent-element')

    @pytest.mark.asyncio
    async def test_clear_input_in_iframe(self, ci_chrome_options):
        """Test clearing input field in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Find input and add text
            input_elem = await iframe_element.find(id='iframe-input')
            await input_elem.insert_text('Test text to clear')
            await asyncio.sleep(0.3)

            await input_elem.insert_text('')
            await asyncio.sleep(0.3)
            value = input_elem.get_attribute('value')
            assert value in ('', None)

    @pytest.mark.asyncio
    async def test_multiple_iframes_on_same_page(self, ci_chrome_options):
        """Test handling multiple iframes on the same page."""
        # Create a test page with multiple iframes
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Find main content (not in iframe)
            main_heading = await tab.find(id='main-heading')
            assert main_heading is not None
            main_text = await main_heading.text
            assert 'Main Page' in main_text

            # Find content in iframe
            iframe_element = await tab.find(id='simple-iframe')
            iframe_heading = await iframe_element.find(id='iframe-heading')
            iframe_text = await iframe_heading.text
            assert 'Iframe Content' in iframe_text

            # Verify they are different
            assert main_text != iframe_text

    @pytest.mark.asyncio
    async def test_iframe_context_persistence(self, ci_chrome_options):
        """Test that iframe context persists across multiple operations."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Get context first time
            context1 = await iframe_element.iframe_context
            assert context1 is not None

            # Perform some operations
            element1 = await iframe_element.find(id='iframe-heading')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Get all list items
            list_items = await iframe_element.query('.list-item', find_all=True)
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
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Find all iframes
            all_iframes = await tab.find(tag_name='iframe', find_all=True)
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
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Get the login iframe specifically
            login_iframe = await tab.find(id='login-iframe')
            
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
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Get two different iframes
            cookie_iframe = await tab.find(id='cookie-iframe')
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
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Find iframe by data-purpose attribute using xpath
            login_iframe = await tab.find(xpath='//iframe[@data-purpose="login"]')
            assert login_iframe is not None
            assert login_iframe.get_attribute('id') == 'login-iframe'

            # Verify we can interact with it
            form = await login_iframe.find(id='iframe-form')
            assert form is not None

    @pytest.mark.asyncio
    async def test_iterate_over_multiple_iframes(self, ci_chrome_options):
        """Test iterating over multiple iframes and accessing each one's content."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Find all iframes
            all_iframes = await tab.find(tag_name='iframe', find_all=True)
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
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # First, find element in cookie iframe
            cookie_iframe = await tab.find(id='cookie-iframe')
            cookie_heading = await cookie_iframe.find(id='iframe-heading')
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
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            iframe_element = await tab.find(id='simple-iframe')

            # Add dynamic content via JavaScript
            iframe_context = await iframe_element.iframe_context
            await tab.execute_script(
                """
                const div = document.createElement('div');
                div.id = 'dynamic-element';
                div.textContent = 'Dynamic Content';
                document.body.appendChild(div);
                """,
                context_id=iframe_context.execution_context_id,
            )
            await asyncio.sleep(0.5)

            # Find dynamically added element
            dynamic_element = await iframe_element.find(id='dynamic-element')
            assert dynamic_element is not None

            text = await dynamic_element.text
            assert 'Dynamic Content' in text

    @pytest.mark.asyncio
    async def test_iframe_reload_handling(self, ci_chrome_options):
        """Test that iframe context is properly handled after page reload."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(file_url)
            await asyncio.sleep(1)

            # Find iframe and element
            iframe_element = await tab.find(id='simple-iframe')
            element_before = await iframe_element.find(id='iframe-heading')
            assert element_before is not None

            # Reload page
            await tab.refresh()
            await asyncio.sleep(1)

            # Find iframe again (new instance)
            iframe_element_after = await tab.find(id='simple-iframe')
            element_after = await iframe_element_after.find(id='iframe-heading')
            assert element_after is not None

            # Verify element is accessible
            text = await element_after.text
            assert 'Iframe Content' in text

