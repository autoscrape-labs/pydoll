"""Integration tests for iframe functionality in WebElement.

These tests use real HTML files and Chrome browser to test iframe interactions,
element finding, and DOM manipulation within iframes.
"""

from pathlib import Path

import pytest

from _waits import wait_for_js, wait_for_js_value, wait_until
from pydoll.commands import RuntimeCommands
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import ElementNotFound, InvalidIFrame


class TestSimpleIframeIntegration:
    """Integration tests for simple iframe operations."""

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_id(self, tab):
        """Test finding an element inside an iframe by id."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)
        assert iframe_element is not None
        assert iframe_element.is_iframe

        iframe_context = await iframe_element.iframe_context()
        assert iframe_context is not None
        assert iframe_context.frame_id is not None
        assert iframe_context.execution_context_id is not None

        heading_in_iframe = await iframe_element.find(id='iframe-heading', timeout=5)
        assert heading_in_iframe is not None
        assert isinstance(heading_in_iframe, WebElement)

        text = await heading_in_iframe.text()
        assert 'Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_multiple_elements_in_iframe(self, tab):
        """Test finding multiple elements inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        links = await iframe_element.query('.iframe-link', find_all=True, timeout=5)
        assert len(links) == 3

        for i, link in enumerate(links, 1):
            link_id = link.get_attribute('id')
            assert link_id == f'iframe-link{i}'

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_css_selector(self, tab):
        """Test finding elements in iframe using CSS selectors."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        action_buttons = await iframe_element.query('.action-btn', find_all=True, timeout=5)
        assert len(action_buttons) >= 2

        inputs = await iframe_element.query('input[type="text"]', find_all=True)
        assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_find_element_in_iframe_by_xpath(self, tab):
        """Test finding elements in iframe using XPath."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        paragraph = await iframe_element.find(xpath='//p[@id="iframe-paragraph"]', timeout=5)
        assert paragraph is not None

        text = await paragraph.text()
        assert 'content inside the iframe' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_iframe_input(self, tab):
        """Test inserting text into an input field inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        input_element = await iframe_element.find(id='iframe-input', timeout=5)
        assert input_element is not None

        test_text = 'Test User Name'
        await input_element.insert_text(test_text)

        value = input_element.get_attribute('value')
        assert test_text in value

    @pytest.mark.asyncio
    async def test_insert_text_in_iframe_textarea(self, tab):
        """Test inserting text into a textarea inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        textarea = await iframe_element.find(id='iframe-textarea', timeout=5)
        assert textarea is not None

        new_message = 'This is a new test message'
        await textarea.insert_text(new_message)

        value = textarea.get_attribute('value')
        assert new_message in value

    @pytest.mark.asyncio
    async def test_click_button_in_iframe(self, tab):
        """Test clicking a button inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        button = await iframe_element.find(id='iframe-button1', timeout=5)
        assert button is not None

        await button.click()

    @pytest.mark.asyncio
    async def test_get_inner_html_of_iframe(self, tab):
        """Test getting inner HTML of an iframe element."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        inner_html = await iframe_element.inner_html()
        assert inner_html is not None
        assert len(inner_html) > 0
        assert 'iframe-heading' in inner_html
        assert 'Iframe Content' in inner_html

    @pytest.mark.asyncio
    async def test_get_inner_html_of_element_in_iframe(self, tab):
        """Test getting inner HTML of an element inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        container = await iframe_element.find(id='iframe-container', timeout=5)
        assert container is not None

        inner_html = await container.inner_html()
        assert inner_html is not None
        assert 'iframe-paragraph' in inner_html
        assert 'iframe-form' in inner_html

    @pytest.mark.asyncio
    async def test_get_children_elements_in_iframe(self, tab):
        """Test getting children elements of an element inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        list_element = await iframe_element.find(id='iframe-list', timeout=5)
        assert list_element is not None

        list_items = await list_element.get_children_elements(max_depth=2, tag_filter=['li'])
        assert len(list_items) == 3

    @pytest.mark.asyncio
    async def test_element_visibility_in_iframe(self, tab):
        """Test checking element visibility inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        visible_button = await iframe_element.find(id='iframe-button1', timeout=5)
        is_visible = await visible_button.is_visible()
        assert is_visible is True

        hidden_button = await iframe_element.find(id='iframe-button3')
        is_hidden = await hidden_button.is_visible()
        assert is_hidden is False


class TestNestedIframeIntegration:
    """Integration tests for nested iframe operations."""

    @pytest.mark.asyncio
    async def test_find_element_in_parent_iframe(self, tab):
        """Test finding an element in parent iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)
        assert parent_iframe is not None
        assert parent_iframe.is_iframe

        parent_heading = await parent_iframe.find(id='parent-iframe-heading', timeout=5)
        assert parent_heading is not None

        text = await parent_heading.text()
        assert 'Parent Iframe Content' in text

    @pytest.mark.asyncio
    async def test_find_nested_iframe_element(self, tab):
        """Test finding the nested iframe element inside parent iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)

        nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)
        assert nested_iframe is not None
        assert nested_iframe.is_iframe

    @pytest.mark.asyncio
    async def test_find_element_in_nested_iframe(self, tab):
        """Test finding an element in nested iframe (iframe within iframe)."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)

        nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)
        assert nested_iframe is not None

        nested_heading = await nested_iframe.find(id='nested-iframe-heading', timeout=5)
        assert nested_heading is not None

        text = await nested_heading.text()
        assert 'Nested Iframe Content' in text

    @pytest.mark.asyncio
    async def test_insert_text_in_nested_iframe(self, tab):
        """Test inserting text into input field in nested iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)
        nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

        nested_input = await nested_iframe.find(id='nested-input', timeout=5)
        assert nested_input is not None

        test_text = 'Nested Input Test'
        await nested_input.insert_text(test_text)

        value = nested_input.get_attribute('value')
        assert test_text in value

    @pytest.mark.asyncio
    async def test_find_multiple_elements_in_nested_iframe(self, tab):
        """Test finding multiple elements in nested iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)
        nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

        links = await nested_iframe.query('a', find_all=True, timeout=5)
        assert len(links) == 2

        link_ids = [link.get_attribute('id') for link in links]
        assert 'nested-link1' in link_ids
        assert 'nested-link2' in link_ids

    @pytest.mark.asyncio
    async def test_submit_form_in_nested_iframe(self, tab):
        """Test interacting with form elements in nested iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_nested.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        parent_iframe = await tab.find(id='parent-iframe', timeout=5)
        nested_iframe = await parent_iframe.find(id='nested-iframe', timeout=5)

        username_input = await nested_iframe.find(id='nested-form-input', timeout=5)
        await username_input.insert_text('testuser')

        password_input = await nested_iframe.find(id='nested-form-password')
        await password_input.insert_text('password123')

        assert 'testuser' in username_input.get_attribute('value')
        assert 'password123' in password_input.get_attribute('value')

        submit_button = await nested_iframe.find(id='nested-form-submit')
        await submit_button.click()


class TestIframeElementInteraction:
    """Integration tests for various element interactions within iframes."""

    @pytest.mark.asyncio
    async def test_select_option_in_iframe(self, tab):
        """Test selecting an option in a select element inside iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        select_element = await iframe_element.find(id='iframe-select', timeout=5)
        assert select_element is not None

        option2 = await select_element.find(xpath='.//option[@value="option2"]')
        await option2.click()
        await wait_for_js_value(select_element, 'this.value', 'option2')
        prop_val = await select_element.execute_script('return this.value', return_by_value=True)
        current_value = prop_val['result']['result']['value']
        assert current_value == 'option2'

        option3 = await select_element.find(xpath='.//option[@value="option3"]')
        await option3.click()
        await wait_for_js_value(select_element, 'this.value', 'option3')
        prop_val2 = await select_element.execute_script('return this.value', return_by_value=True)
        new_value = prop_val2['result']['result']['value']
        assert new_value == 'option3'

    @pytest.mark.asyncio
    async def test_get_attributes_from_iframe_elements(self, tab):
        """Test getting various attributes from elements in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        link = await iframe_element.find(id='iframe-link1', timeout=5)
        href = link.get_attribute('href')
        assert href is not None
        assert '#link1' in href

        link_class = link.get_attribute('class')
        assert 'iframe-link' in link_class

        input_elem = await iframe_element.find(id='iframe-input')
        input_type = input_elem.get_attribute('type')
        assert input_type == 'text'

        placeholder = input_elem.get_attribute('placeholder')
        assert 'name' in placeholder.lower()

    @pytest.mark.asyncio
    async def test_deep_nested_element_search_in_iframe(self, tab):
        """Test finding deeply nested elements inside iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        deep_span = await iframe_element.find(id='deep-span', timeout=5)
        assert deep_span is not None

        text = await deep_span.text()
        assert 'Deep nested element' in text

    @pytest.mark.asyncio
    async def test_wait_for_element_in_iframe(self, tab):
        """Test waiting for element to appear in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        element = await iframe_element.find(id='iframe-paragraph', timeout=5)
        assert element is not None

        text = await element.text()
        assert 'content inside the iframe' in text

    @pytest.mark.asyncio
    async def test_element_not_found_in_iframe(self, tab):
        """Test that ElementNotFound is raised for non-existent elements in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        with pytest.raises(ElementNotFound):
            await iframe_element.find(id='non-existent-element')

    @pytest.mark.asyncio
    async def test_clear_input_in_iframe(self, tab):
        """Test clearing input field in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        input_elem = await iframe_element.find(id='iframe-input', timeout=5)
        await input_elem.insert_text('Test text to clear')

        await input_elem.insert_text('')
        value = input_elem.get_attribute('value')
        assert value in ('', None)

    @pytest.mark.asyncio
    async def test_multiple_iframes_on_same_page(self, tab):
        """Test handling multiple iframes on the same page."""
        # Create a test page with multiple iframes
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        main_heading = await tab.find(id='main-heading', timeout=5)
        assert main_heading is not None
        main_text = await main_heading.text()
        assert 'Main Page' in main_text

        iframe_element = await tab.find(id='simple-iframe')
        iframe_heading = await iframe_element.find(id='iframe-heading', timeout=5)
        iframe_text = await iframe_heading.text()
        assert 'Iframe Content' in iframe_text

        assert main_text != iframe_text

    @pytest.mark.asyncio
    async def test_iframe_context_persistence(self, tab):
        """Test that iframe context persists across multiple operations."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        context1 = await iframe_element.iframe_context()
        assert context1 is not None

        element1 = await iframe_element.find(id='iframe-heading', timeout=5)
        await element1.text()

        context2 = await iframe_element.iframe_context()
        assert context2 is not None

        assert context1.frame_id == context2.frame_id
        assert context1.execution_context_id == context2.execution_context_id

    @pytest.mark.asyncio
    async def test_get_text_from_multiple_elements_in_iframe(self, tab):
        """Test getting text from multiple elements in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        list_items = await iframe_element.query('.list-item', find_all=True, timeout=5)
        assert len(list_items) == 3

        texts = []
        for item in list_items:
            text = await item.text()
            texts.append(text)

        assert 'Item 1' in texts[0]
        assert 'Item 2' in texts[1]
        assert 'Item 3' in texts[2]


class TestMultipleIframesSelection:
    """Integration tests for selecting the correct iframe when multiple iframes exist."""

    @pytest.mark.asyncio
    async def test_find_specific_iframe_by_id_among_multiple(self, tab):
        """Test finding a specific iframe by ID when multiple iframes exist on the page."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        all_iframes = await tab.find(tag_name='iframe', find_all=True, timeout=5)
        assert len(all_iframes) == 3, 'Should have 3 iframes on the page'

        login_iframe = await tab.find(id='login-iframe')
        assert login_iframe is not None
        assert login_iframe.is_iframe
        assert login_iframe.get_attribute('id') == 'login-iframe'

        iframe_context = await login_iframe.iframe_context()
        assert iframe_context is not None
        assert iframe_context.frame_id is not None

    @pytest.mark.asyncio
    async def test_find_elements_in_correct_iframe_among_multiple(self, tab):
        """Test that elements are found in the correct iframe when multiple exist."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        login_iframe = await tab.find(id='login-iframe', timeout=5)

        heading = await login_iframe.find(id='iframe-heading', timeout=5)
        assert heading is not None

        text = await heading.text()
        assert 'Iframe Content' in text

        buttons = await login_iframe.find(class_name='action-btn', find_all=True)
        assert len(buttons) >= 2

    @pytest.mark.asyncio
    async def test_different_iframes_have_different_contexts(self, tab):
        """Test that different iframes have distinct frame contexts even with same content."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        cookie_iframe = await tab.find(id='cookie-iframe', timeout=5)
        login_iframe = await tab.find(id='login-iframe')

        assert cookie_iframe.is_iframe
        assert login_iframe.is_iframe

        cookie_ctx = await cookie_iframe.iframe_context()
        login_ctx = await login_iframe.iframe_context()

        assert cookie_ctx.frame_id != login_ctx.frame_id

        cookie_heading = await cookie_iframe.find(id='iframe-heading')
        login_heading = await login_iframe.find(id='iframe-heading')

        assert cookie_heading is not None
        assert login_heading is not None

        assert cookie_heading._object_id != login_heading._object_id

    @pytest.mark.asyncio
    async def test_iframe_selection_by_data_attribute(self, tab):
        """Test selecting iframe by custom data attribute."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        login_iframe = await tab.find(xpath='//iframe[@data-purpose="login"]', timeout=5)
        assert login_iframe is not None
        assert login_iframe.get_attribute('id') == 'login-iframe'

        form = await login_iframe.find(id='iframe-form')
        assert form is not None

    @pytest.mark.asyncio
    async def test_iterate_over_multiple_iframes(self, tab):
        """Test iterating over multiple iframes and accessing each one's content."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        all_iframes = await tab.find(tag_name='iframe', find_all=True, timeout=5)
        assert len(all_iframes) == 3

        for iframe in all_iframes:
            assert iframe.is_iframe

            ctx = await iframe.iframe_context()
            assert ctx is not None
            assert ctx.frame_id is not None

            heading = await iframe.find(id='iframe-heading', raise_exc=False)
            if heading:
                text = await heading.text()
                assert len(text) > 0

    @pytest.mark.asyncio
    async def test_find_in_iframe_after_finding_in_another(self, tab):
        """Test finding elements in one iframe after finding in another."""
        test_file = Path(__file__).parent / 'pages' / 'test_multiple_iframes.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        cookie_iframe = await tab.find(id='cookie-iframe', timeout=5)
        cookie_heading = await cookie_iframe.find(id='iframe-heading', timeout=5)
        cookie_text = await cookie_heading.text()

        login_iframe = await tab.find(id='login-iframe')
        login_heading = await login_iframe.find(id='iframe-heading')
        login_text = await login_heading.text()

        assert 'Iframe Content' in cookie_text
        assert 'Iframe Content' in login_text

        analytics_iframe = await tab.find(id='analytics-iframe')
        analytics_heading = await analytics_iframe.find(id='iframe-heading')
        analytics_text = await analytics_heading.text()

        assert 'Iframe Content' in analytics_text


class TestIframeEdgeCases:
    """Integration tests for edge cases in iframe handling."""

    @pytest.mark.asyncio
    async def test_dynamic_content_in_iframe(self, tab):
        """Test finding dynamically added content in iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        iframe_context = await iframe_element.iframe_context()
        await tab.execute_script(
            """
            const div = document.createElement('div');
            div.id = 'dynamic-element';
            div.textContent = 'Dynamic Content';
            document.body.appendChild(div);
            """,
            context_id=iframe_context.execution_context_id,
        )

        dynamic_element = await iframe_element.find(id='dynamic-element', timeout=5)
        assert dynamic_element is not None

        text = await dynamic_element.text()
        assert 'Dynamic Content' in text

    @pytest.mark.asyncio
    async def test_iframe_reload_handling(self, tab):
        """Test that iframe context is properly handled after page reload."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)
        element_before = await iframe_element.find(id='iframe-heading', timeout=5)
        assert element_before is not None

        await tab.refresh()

        iframe_element_after = await tab.find(id='simple-iframe', timeout=5)
        element_after = await iframe_element_after.find(id='iframe-heading', timeout=5)
        assert element_after is not None

        text = await element_after.text()
        assert 'Iframe Content' in text


class TestIframeTypeText:
    """Integration tests for type_text inside iframes."""

    @pytest.mark.asyncio
    async def test_type_text_in_iframe_input(self, tab):
        """type_text should work inside an iframe input."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)
        input_el = await iframe_element.find(id='iframe-input', timeout=5)

        await input_el.type_text('hello')

        await wait_for_js_value(input_el, 'this.value', 'hello')
        prop = await input_el.execute_script('return this.value', return_by_value=True)
        assert prop['result']['result']['value'] == 'hello'

    @pytest.mark.asyncio
    async def test_type_text_humanized_in_iframe_input(self, tab):
        """type_text with humanize=True should work inside an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)
        input_el = await iframe_element.find(id='iframe-input', timeout=5)

        await input_el.type_text('Test', humanize=True)

        await wait_for_js(input_el, 'this.value', lambda value: len(value) >= 2)
        prop = await input_el.execute_script('return this.value', return_by_value=True)
        value = prop['result']['result']['value']
        assert len(value) >= 2

    @pytest.mark.asyncio
    async def test_type_text_email_in_iframe_input(self, tab):
        """type_text should handle symbols like @ and . inside iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)
        input_el = await iframe_element.find(id='iframe-email', timeout=5)

        test_text = 'user@test.com'
        await input_el.type_text(test_text)

        await wait_for_js_value(input_el, 'this.value', test_text)
        prop = await input_el.execute_script('return this.value', return_by_value=True)
        assert prop['result']['result']['value'] == test_text


class TestFrameElementIntegration:
    """Integration tests for <frame> elements (frameset pages)."""

    @pytest.mark.asyncio
    async def test_frame_element_is_iframe(self, tab):
        """Test that a <frame> element is recognized as an iframe."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        frame_element = await tab.find(id='left-frame', timeout=5)
        assert frame_element is not None
        assert frame_element.tag_name == 'frame'
        assert frame_element.is_iframe

    @pytest.mark.asyncio
    async def test_find_element_inside_frame(self, tab):
        """Test finding an element inside a <frame> element."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        frame_element = await tab.find(id='left-frame', timeout=5)
        heading = await frame_element.find(id='frame-heading', timeout=5)
        assert heading is not None

        text = await heading.text()
        assert 'Frame Content' in text

    @pytest.mark.asyncio
    async def test_frame_context_is_resolved(self, tab):
        """Test that iframe_context works for <frame> elements."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        frame_element = await tab.find(id='left-frame', timeout=5)
        ctx = await frame_element.iframe_context()
        assert ctx is not None
        assert ctx.frame_id is not None
        assert ctx.execution_context_id is not None

    @pytest.mark.asyncio
    async def test_inner_html_of_frame(self, tab):
        """Test that inner_html works for <frame> elements."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        frame_element = await tab.find(id='left-frame', timeout=5)
        html = await frame_element.inner_html()
        assert 'frame-heading' in html

    @pytest.mark.asyncio
    async def test_multiple_frames_in_frameset(self, tab):
        """Test interacting with multiple <frame> elements in a frameset."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        left_frame = await tab.find(id='left-frame', timeout=5)
        right_frame = await tab.find(id='right-frame', timeout=5)

        assert left_frame.is_iframe
        assert right_frame.is_iframe

        left_heading = await left_frame.find(id='frame-heading', timeout=5)
        left_text = await left_heading.text()
        assert 'Frame Content' in left_text

        right_heading = await right_frame.find(id='iframe-heading', timeout=5)
        right_text = await right_heading.text()
        assert 'Iframe Content' in right_text

    @pytest.mark.asyncio
    async def test_type_text_in_frame_input(self, tab):
        """Test typing text into an input inside a <frame> element."""
        test_file = Path(__file__).parent / 'pages' / 'test_frameset.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        frame_element = await tab.find(id='left-frame', timeout=5)
        input_el = await frame_element.find(id='frame-input', timeout=5)

        test_text = 'hello frame'
        await input_el.type_text(test_text)

        await wait_for_js_value(input_el, 'this.value', test_text)
        prop = await input_el.execute_script('return this.value', return_by_value=True)
        assert prop['result']['result']['value'] == test_text


class TestIframeContextResolutionFailures:
    """Integration tests for iframe context resolution failure paths.

    These exercise the resolver's defensive branches with a real browser:
    when the <iframe> element handle becomes stale (removed from the DOM or
    its remote object released), context resolution must surface a clear
    ``InvalidIFrame`` instead of silently returning a broken context.
    """

    @pytest.mark.asyncio
    async def test_iframe_context_raises_after_iframe_removed_from_dom(self, tab):
        """Resolving context for an iframe removed from the DOM raises InvalidIFrame.

        After removal ``DOM.describeNode`` still returns the (now detached)
        node but with no ``frameId``; the owner lookup over the frame tree
        finds no matching frame, so the resolver cannot determine a frameId
        and raises.
        """
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        ctx_before = await iframe_element.iframe_context()
        assert ctx_before is not None
        assert ctx_before.frame_id is not None

        await tab.execute_script("document.getElementById('simple-iframe').remove();")

        async def context_resolution_fails() -> bool:
            try:
                await iframe_element.iframe_context()
                return False
            except InvalidIFrame:
                return True

        await wait_until(
            context_resolution_fails,
            timeout=5,
            message='iframe_context did not raise after removal',
        )

        with pytest.raises(InvalidIFrame):
            await iframe_element.iframe_context()

    @pytest.mark.asyncio
    async def test_iframe_context_raises_when_remote_object_released(self, tab):
        """Releasing the iframe's remote object makes context resolution raise.

        ``Runtime.releaseObject`` invalidates the element's ``objectId``; the
        subsequent ``DOM.describeNode`` returns an error, the resolver falls
        back to an empty node (no frameId, no backendNodeId) and ultimately
        raises ``InvalidIFrame``.
        """
        test_file = Path(__file__).parent / 'pages' / 'test_iframe_simple.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='simple-iframe', timeout=5)

        await tab._connection_handler.execute_command(
            RuntimeCommands.release_object(object_id=iframe_element._object_id)
        )

        with pytest.raises(InvalidIFrame):
            await iframe_element.iframe_context()

    @pytest.mark.asyncio
    async def test_no_src_iframe_resolves_about_blank_context(self, tab):
        """A srcless <iframe> (about:blank) still resolves a usable context.

        Its ``contentDocument.frameId`` is null, so resolution goes through the
        frame-owner lookup (matching the iframe's backendNodeId against the
        page frame tree) rather than the direct contentDocument path.
        """
        test_file = Path(__file__).parent / 'pages' / 'iframe_features.html'
        file_url = f'file://{test_file.absolute()}'

        await tab.go_to(file_url)

        iframe_element = await tab.find(id='frame-no-src', timeout=5)
        assert iframe_element.is_iframe

        ctx = await iframe_element.iframe_context()
        assert ctx is not None
        assert ctx.frame_id is not None
        assert ctx.execution_context_id is not None

        await tab.execute_script(
            """
            const marker = document.createElement('div');
            marker.id = 'about-blank-marker';
            marker.textContent = 'blank ok';
            document.body.appendChild(marker);
            """,
            context_id=ctx.execution_context_id,
        )
        marker = await iframe_element.find(id='about-blank-marker', timeout=5)
        assert 'blank ok' in await marker.text()
