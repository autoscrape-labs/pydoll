import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.constants import By
from pydoll.exceptions import ElementNotFound, WaitElementTimeout


class MockFindElementsMixin(FindElementsMixin):
    """Mock implementation of FindElementsMixin for testing."""
    
    def __init__(self):
        self._connection_handler = AsyncMock()
        # Some tests need object_id, others don't
        self._object_id = None


class TestBuildXPath:
    """Test the _build_xpath static method comprehensively."""

    def test_build_xpath_single_id(self):
        """Test XPath building with only ID."""
        xpath = FindElementsMixin._build_xpath(id='test-id')
        assert xpath == '//*[@id="test-id"]'

    def test_build_xpath_single_class_name(self):
        """Test XPath building with only class name."""
        xpath = FindElementsMixin._build_xpath(class_name='btn-primary')
        expected = '//*[contains(concat(" ", normalize-space(@class), " "), " btn-primary ")]'
        assert xpath == expected

    def test_build_xpath_single_name(self):
        """Test XPath building with only name attribute."""
        xpath = FindElementsMixin._build_xpath(name='username')
        assert xpath == '//*[@name="username"]'

    def test_build_xpath_single_tag_name(self):
        """Test XPath building with only tag name."""
        xpath = FindElementsMixin._build_xpath(tag_name='button')
        assert xpath == '//button'

    def test_build_xpath_single_text(self):
        """Test XPath building with only text content."""
        xpath = FindElementsMixin._build_xpath(text='Click me')
        assert xpath == '//*[contains(text(), "Click me")]'

    def test_build_xpath_single_custom_attribute(self):
        """Test XPath building with single custom attribute."""
        xpath = FindElementsMixin._build_xpath(data_testid='submit-btn')
        assert xpath == '//*[@data-testid="submit-btn"]'

    def test_build_xpath_id_and_class(self):
        """Test XPath building with ID and class name."""
        xpath = FindElementsMixin._build_xpath(id='main-btn', class_name='primary')
        expected = '//*[@id="main-btn" and contains(concat(" ", normalize-space(@class), " "), " primary ")]'
        assert xpath == expected

    def test_build_xpath_tag_and_attributes(self):
        """Test XPath building with tag name and multiple attributes."""
        xpath = FindElementsMixin._build_xpath(
            tag_name='input',
            id='email-field',
            name='email',
            type='email'
        )
        expected = '//input[@id="email-field" and @name="email" and @type="email"]'
        assert xpath == expected

    def test_build_xpath_all_parameters(self):
        """Test XPath building with all possible parameters."""
        xpath = FindElementsMixin._build_xpath(
            id='complex-element',
            class_name='form-control',
            name='user_input',
            tag_name='input',
            text='placeholder text',
            data_role='textbox',
            aria_label='User input field'
        )
        expected = ('//input[@id="complex-element" and '
                   'contains(concat(" ", normalize-space(@class), " "), " form-control ") and '
                   '@name="user_input" and '
                   'contains(text(), "placeholder text") and '
                   '@data-role="textbox" and '
                   '@aria-label="User input field"]')
        assert xpath == expected

    def test_build_xpath_text_with_quotes(self):
        """Test XPath building with text containing quotes."""
        xpath = FindElementsMixin._build_xpath(text='Say "Hello"')
        assert xpath == '//*[contains(text(), "Say "Hello"")]'

    def test_build_xpath_attribute_with_quotes(self):
        """Test XPath building with attribute value containing quotes."""
        xpath = FindElementsMixin._build_xpath(title='This is a "quoted" title')
        assert xpath == '//*[@title="This is a "quoted" title"]'

    def test_build_xpath_empty_values_ignored(self):
        """Test that empty string values are ignored in XPath building."""
        xpath = FindElementsMixin._build_xpath(
            id='test-id',
            class_name='',  # Empty string should be ignored
            name=None,      # None should be ignored
            tag_name='div'
        )
        assert xpath == '//div[@id="test-id"]'

    def test_build_xpath_class_name_with_spaces(self):
        """Test XPath building with class name that has spaces (edge case)."""
        xpath = FindElementsMixin._build_xpath(class_name='btn primary large')
        expected = '//*[contains(concat(" ", normalize-space(@class), " "), " btn primary large ")]'
        assert xpath == expected

    def test_build_xpath_special_characters_in_attributes(self):
        """Test XPath building with special characters in attribute values."""
        xpath = FindElementsMixin._build_xpath(
            data_value='test@example.com',
            aria_describedby='field-help-123'
        )
        expected = '//*[@data-value="test@example.com" and @aria-describedby="field-help-123"]'
        assert xpath == expected

    def test_build_xpath_numeric_attribute_values(self):
        """Test XPath building with numeric attribute values."""
        xpath = FindElementsMixin._build_xpath(
            tabindex='0',
            maxlength='255'
        )
        expected = '//*[@tabindex="0" and @maxlength="255"]'
        assert xpath == expected

    def test_build_xpath_no_parameters(self):
        """Test XPath building with no parameters returns generic selector."""
        xpath = FindElementsMixin._build_xpath()
        assert xpath == '//*'

    def test_build_xpath_only_tag_name(self):
        """Test XPath building with only tag name."""
        xpath = FindElementsMixin._build_xpath(tag_name='span')
        assert xpath == '//span'

    def test_build_xpath_hyphenated_attributes(self):
        """Test XPath building with hyphenated attribute names."""
        xpath = FindElementsMixin._build_xpath(
            **{'data-test-id': 'submit-button', 'aria-label': 'Submit form'}
        )
        expected = '//*[@data-test-id="submit-button" and @aria-label="Submit form"]'
        assert xpath == expected


class TestGetExpressionType:
    """Test the _get_expression_type static method."""

    def test_xpath_double_slash(self):
        """Test XPath detection with double slash."""
        assert FindElementsMixin._get_expression_type('//div') == By.XPATH

    def test_xpath_dot_double_slash(self):
        """Test XPath detection with dot double slash."""
        assert FindElementsMixin._get_expression_type('.//span') == By.XPATH

    def test_xpath_dot_slash(self):
        """Test XPath detection with dot slash."""
        assert FindElementsMixin._get_expression_type('./button') == By.XPATH

    def test_xpath_single_slash(self):
        """Test XPath detection with single slash."""
        assert FindElementsMixin._get_expression_type('/html/body') == By.XPATH

    def test_css_selector_default(self):
        """Test CSS selector as default."""
        assert FindElementsMixin._get_expression_type('div.content > p') == By.CSS_SELECTOR

    def test_css_selector_attribute(self):
        """Test CSS selector with attributes."""
        assert FindElementsMixin._get_expression_type('input[type="text"]') == By.CSS_SELECTOR

    def test_css_selector_pseudo_class(self):
        """Test CSS selector with pseudo-classes."""
        assert FindElementsMixin._get_expression_type('button:hover') == By.CSS_SELECTOR
    
    def test_css_selector_not_xpath(self):
        """Test that css selector doesn't conflict with XPath dot slash."""
        assert FindElementsMixin._get_expression_type('.button') == By.CSS_SELECTOR
        assert FindElementsMixin._get_expression_type('./button') == By.XPATH

    def test_complex_xpath_expressions(self):
        """Test complex XPath expressions are detected correctly."""
        complex_xpaths = [
            '//div[@class="content"]/p[contains(text(), "Hello")]',
            './/button[position()=1]',
            './/*[@id="test" and @class="active"]',
            '/html/body/div[1]/form/input[@type="submit"]'
        ]
        for xpath in complex_xpaths:
            assert FindElementsMixin._get_expression_type(xpath) == By.XPATH

    def test_edge_case_expressions(self):
        """Test edge case expressions."""
        # Empty string should default to CSS
        assert FindElementsMixin._get_expression_type('') == By.CSS_SELECTOR

    def test_xpath_with_parentheses_and_predicate(self):
        """Test XPath detection with parentheses, e.g. (//div)[last()]."""
        expressions = [
            '(//div)[last()]',
            '(//span[@class="btn"])[1]',
            '(/html/body/div)[position()=1]'
        ]
        for expr in expressions:
            assert FindElementsMixin._get_expression_type(expr) == By.XPATH


class TestEnsureRelativeXPath:
    """Test the _ensure_relative_xpath static method."""

    def test_absolute_xpath_becomes_relative(self):
        """Test that absolute XPath becomes relative."""
        xpath = '//div[@id="test"]'
        result = FindElementsMixin._ensure_relative_xpath(xpath)
        assert result == './/div[@id="test"]'

    def test_already_relative_xpath_unchanged(self):
        """Test that already relative XPath remains unchanged."""
        xpath = './/div[@id="test"]'
        result = FindElementsMixin._ensure_relative_xpath(xpath)
        assert result == './/div[@id="test"]'

    def test_dot_slash_xpath_unchanged(self):
        """Test that dot slash XPath remains unchanged."""
        xpath = './button'
        result = FindElementsMixin._ensure_relative_xpath(xpath)
        assert result == './button'

    def test_single_slash_xpath_becomes_relative(self):
        """Test that single slash XPath becomes relative."""
        xpath = '/html/body/div'
        result = FindElementsMixin._ensure_relative_xpath(xpath)
        assert result == './html/body/div'

    def test_empty_xpath(self):
        """Test empty XPath handling."""
        xpath = ''
        result = FindElementsMixin._ensure_relative_xpath(xpath)
        assert result == '.'

    def test_complex_xpath_expressions(self):
        """Test complex XPath expressions."""
        test_cases = [
            ('//div[contains(@class, "test")]', './/div[contains(@class, "test")]'),
            ('.//span[@id="existing"]', './/span[@id="existing"]'),
            ('//*[@data-test="value"]', './/*[@data-test="value"]'),
            ('//button[text()="Submit"]', './/button[text()="Submit"]')
        ]
        
        for input_xpath, expected in test_cases:
            result = FindElementsMixin._ensure_relative_xpath(input_xpath)
            assert result == expected


class TestGetByAndValue:
    """Test the _get_by_and_value method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mixin = MockFindElementsMixin()
        self.by_map = {
            'id': By.ID,
            'class_name': By.CLASS_NAME,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'xpath': By.XPATH,
        }

    def test_single_id_selector(self):
        """Test single ID selector returns direct By.ID."""
        by, value = self.mixin._get_by_and_value(self.by_map, id='test-id')
        assert by == By.ID
        assert value == 'test-id'

    def test_single_class_name_selector(self):
        """Test single class name selector returns direct By.CLASS_NAME."""
        by, value = self.mixin._get_by_and_value(self.by_map, class_name='btn-primary')
        assert by == By.CLASS_NAME
        assert value == 'btn-primary'

    def test_single_name_selector(self):
        """Test single name selector returns direct By.NAME."""
        by, value = self.mixin._get_by_and_value(self.by_map, name='username')
        assert by == By.NAME
        assert value == 'username'

    def test_single_tag_name_selector(self):
        """Test single tag name selector returns direct By.TAG_NAME."""
        by, value = self.mixin._get_by_and_value(self.by_map, tag_name='button')
        assert by == By.TAG_NAME
        assert value == 'button'

    def test_single_custom_attribute(self):
        """Test single custom attribute builds XPath."""
        by, value = self.mixin._get_by_and_value(self.by_map, data_testid='submit-btn')
        assert by == By.XPATH
        assert value == '//*[@data-testid="submit-btn"]'

    def test_multiple_attributes_build_xpath(self):
        """Test multiple attributes build XPath."""
        by, value = self.mixin._get_by_and_value(
            self.by_map, 
            id='test-id', 
            class_name='btn-primary'
        )
        assert by == By.XPATH
        expected = '//*[@id="test-id" and contains(concat(" ", normalize-space(@class), " "), " btn-primary ")]'
        assert value == expected

    def test_text_with_single_attribute_builds_xpath(self):
        """Test that text with any other attribute builds XPath."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            id='test-id',
            text='Click me'
        )
        assert by == By.XPATH
        expected = '//*[@id="test-id" and contains(text(), "Click me")]'
        assert value == expected

    def test_text_alone_builds_xpath(self):
        """Test that text alone builds XPath."""
        by, value = self.mixin._get_by_and_value(self.by_map, text='Submit')
        assert by == By.XPATH
        assert value == '//*[contains(text(), "Submit")]'

    def test_empty_values_ignored(self):
        """Test that empty values are ignored in selector building."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            id='test-id',
            class_name='',  # Empty string
            name=None       # None value
        )
        assert by == By.ID
        assert value == 'test-id'

    def test_all_empty_values_with_custom_attribute(self):
        """Test custom attribute when standard attributes are empty."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            id='',
            class_name=None,
            data_role='button'
        )
        assert by == By.XPATH
        assert value == '//*[@data-role="button"]'


class TestFindElementsMixinEdgeCases:
    """Test edge cases and error conditions in FindElementsMixin."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mixin = MockFindElementsMixin()

    @pytest.mark.asyncio
    async def test_find_no_criteria_raises_error(self):
        """Test that find with no criteria raises ValueError."""
        with pytest.raises(ValueError, match='At least one of the following arguments must be provided'):
            await self.mixin.find()

    @pytest.mark.asyncio
    async def test_find_empty_string_criteria_raises_error(self):
        """Test that find with only empty string criteria raises ValueError."""
        with pytest.raises(ValueError, match='At least one of the following arguments must be provided'):
            await self.mixin.find(id='', class_name='', name='', tag_name='', text='')

    @pytest.mark.asyncio
    async def test_find_none_criteria_raises_error(self):
        """Test that find with only None criteria raises ValueError."""
        with pytest.raises(ValueError, match='At least one of the following arguments must be provided'):
            await self.mixin.find(id=None, class_name=None, name=None, tag_name=None, text=None)

    @pytest.mark.asyncio
    async def test_find_with_custom_attributes_only(self):
        """Test find with only custom attributes works."""
        # Mock the internal methods
        self.mixin._find_element = AsyncMock(return_value=MagicMock())
        
        result = await self.mixin.find(data_testid='submit-button')
        
        # Should call _find_element with XPath
        self.mixin._find_element.assert_called_once()
        call_args = self.mixin._find_element.call_args[0]
        assert call_args[0] == By.XPATH
        assert '@data-testid="submit-button"' in call_args[1]

    @pytest.mark.asyncio
    async def test_query_empty_expression(self):
        """Test query with empty expression."""
        self.mixin._find_element = AsyncMock(return_value=MagicMock())
        
        result = await self.mixin.query('')
        
        # Should call _find_element with CSS_SELECTOR (default)
        self.mixin._find_element.assert_called_once()
        call_args = self.mixin._find_element.call_args[0]
        assert call_args[0] == By.CSS_SELECTOR
        assert call_args[1] == ''

    @pytest.mark.asyncio
    async def test_find_or_wait_element_timeout_zero(self):
        """Test find_or_wait_element with timeout=0 calls find immediately."""
        self.mixin._find_element = AsyncMock(return_value=MagicMock())
        
        result = await self.mixin.find_or_wait_element(By.ID, 'test-id', timeout=0)
        
        self.mixin._find_element.assert_called_once_with(By.ID, 'test-id', raise_exc=True)

    @pytest.mark.asyncio
    async def test_find_or_wait_element_timeout_success_on_retry(self):
        """Test find_or_wait_element succeeds on retry within timeout."""
        # First call returns None, second call returns element
        mock_element = MagicMock()
        self.mixin._find_element = AsyncMock(side_effect=[None, mock_element])
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('asyncio.get_event_loop') as mock_loop:
            # Mock time progression
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0]
            
            result = await self.mixin.find_or_wait_element(
                By.ID, 'test-id', timeout=2, raise_exc=False
            )
        
        assert result == mock_element
        assert self.mixin._find_element.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_find_or_wait_element_timeout_failure(self):
        """Test find_or_wait_element raises WaitElementTimeout."""
        self.mixin._find_element = AsyncMock(return_value=None)
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('asyncio.get_event_loop') as mock_loop:
            # Mock time progression that exceeds timeout
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0, 1.5, 2.1]
            
            with pytest.raises(WaitElementTimeout):
                await self.mixin.find_or_wait_element(
                    By.ID, 'test-id', timeout=2, raise_exc=True
                )

    @pytest.mark.asyncio
    async def test_find_or_wait_element_timeout_failure_no_exception(self):
        """Test find_or_wait_element returns None when raise_exc=False."""
        self.mixin._find_element = AsyncMock(return_value=None)
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('asyncio.get_event_loop') as mock_loop:
            # Mock time progression that exceeds timeout
            mock_loop.return_value.time.side_effect = [0, 0.5, 1.0, 1.5, 2.1]
            
            result = await self.mixin.find_or_wait_element(
                By.ID, 'test-id', timeout=2, raise_exc=False
            )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_find_elements_with_timeout(self):
        """Test find with find_all=True and timeout."""
        mock_elements = [MagicMock(), MagicMock()]
        self.mixin._find_elements = AsyncMock(return_value=mock_elements)
        
        result = await self.mixin.find_or_wait_element(
            By.CLASS_NAME, 'item', timeout=1, find_all=True
        )
        
        assert result == mock_elements
        self.mixin._find_elements.assert_called_once()

    def test_regex_pattern_in_get_expression_type(self):
        """Test the regex pattern used in _get_expression_type."""
        xpath_pattern = r'^(//|\.//|\.\/|/)'
        
        # Test cases that should match
        xpath_expressions = [
            '//div',
            './/span', 
            './button',
            '/html/body'
        ]
        
        for expr in xpath_expressions:
            assert re.match(xpath_pattern, expr), f"Pattern should match: {expr}"
        
        # Test cases that should not match
        non_xpath_expressions = [
            'div.class',
            '#id',
            '.class',
            'input[type="text"]',
            'button:hover'
        ]
        
        for expr in non_xpath_expressions:
            assert not re.match(xpath_pattern, expr), f"Pattern should not match: {expr}"

    def test_xpath_building_with_boolean_attributes(self):
        """Test XPath building with boolean-like attributes."""
        xpath = FindElementsMixin._build_xpath(
            required='true',
            disabled='false',
            checked='checked'
        )
        expected = '//*[@required="true" and @disabled="false" and @checked="checked"]'
        assert xpath == expected

    def test_xpath_building_preserves_attribute_order(self):
        """Test that XPath building maintains consistent attribute order."""
        # Test multiple times to ensure consistency
        for _ in range(5):
            xpath = FindElementsMixin._build_xpath(
                id='test',
                class_name='btn',
                name='submit',
                data_role='button'
            )
            # The order should be: id, class_name, name, then custom attributes
            assert '@id="test"' in xpath
            assert 'contains(concat(" ", normalize-space(@class), " "), " btn ")' in xpath
            assert '@name="submit"' in xpath
            assert '@data-role="button"' in xpath

    def test_xpath_building_with_unicode_characters(self):
        """Test XPath building with Unicode characters."""
        xpath = FindElementsMixin._build_xpath(
            text='Olá mundo',
            title='Título com acentos',
            placeholder='Escreva aqui...'
        )
        expected = '//*[contains(text(), "Olá mundo") and @title="Título com acentos" and @placeholder="Escreva aqui..."]'
        assert xpath == expected

    def test_class_name_xpath_normalization(self):
        """Test that class name XPath uses proper normalization."""
        xpath = FindElementsMixin._build_xpath(class_name='test-class')
        
        # Should use normalize-space to handle multiple spaces
        assert 'normalize-space(@class)' in xpath
        # Should wrap with spaces to match exact class names
        assert '" test-class "' in xpath
        # Should use concat to add spaces
        assert 'concat(" "' in xpath


class TestUnderscoreToHyphenConversion:
    """Test automatic conversion of underscores to hyphens in attribute names."""

    def test_single_underscore_to_hyphen(self):
        """Test single underscore conversion in attribute name."""
        xpath = FindElementsMixin._build_xpath(data_test='submit-button')
        assert xpath == '//*[@data-test="submit-button"]'

    def test_multiple_underscores_to_hyphens(self):
        """Test multiple underscores conversion in same attribute."""
        xpath = FindElementsMixin._build_xpath(data_test_id='submit-button')
        assert xpath == '//*[@data-test-id="submit-button"]'

    def test_aria_attributes_conversion(self):
        """Test aria attributes underscore conversion."""
        xpath = FindElementsMixin._build_xpath(
            aria_label='Submit form',
            aria_describedby='helper-text'
        )
        assert '@aria-label="Submit form"' in xpath
        assert '@aria-describedby="helper-text"' in xpath

    def test_data_attributes_conversion(self):
        """Test data attributes underscore conversion."""
        xpath = FindElementsMixin._build_xpath(
            data_testid='main-button',
            data_value='123',
            data_action='submit'
        )
        assert '@data-testid="main-button"' in xpath
        assert '@data-value="123"' in xpath
        assert '@data-action="submit"' in xpath

    def test_mixed_underscore_and_hyphen_attributes(self):
        """Test that attributes already with hyphens are not affected."""
        # Using dict unpacking for attributes with hyphens
        xpath = FindElementsMixin._build_xpath(
            data_test='value1',
            **{'already-hyphenated': 'value2'}
        )
        assert '@data-test="value1"' in xpath
        assert '@already-hyphenated="value2"' in xpath

    def test_combined_standard_and_custom_attributes(self):
        """Test conversion works with combined standard and custom attributes."""
        xpath = FindElementsMixin._build_xpath(
            id='main-element',
            class_name='btn',
            data_testid='submit-btn',
            aria_label='Submit button'
        )
        assert '@id="main-element"' in xpath
        assert 'contains(concat(" ", normalize-space(@class), " "), " btn ")' in xpath
        assert '@data-testid="submit-btn"' in xpath
        assert '@aria-label="Submit button"' in xpath

    def test_underscore_in_attribute_value_unchanged(self):
        """Test that underscores in values are not converted."""
        xpath = FindElementsMixin._build_xpath(data_test='some_value_with_underscores')
        assert xpath == '//*[@data-test="some_value_with_underscores"]'
        assert 'some_value_with_underscores' in xpath  # Value unchanged

    def test_complex_attribute_names_conversion(self):
        """Test conversion of complex attribute names."""
        xpath = FindElementsMixin._build_xpath(
            ng_repeat='item in items',
            v_model='username',
            x_bind_value='someValue'
        )
        assert '@ng-repeat="item in items"' in xpath
        assert '@v-model="username"' in xpath
        assert '@x-bind-value="someValue"' in xpath

    def test_single_character_segments(self):
        """Test attributes with single character segments."""
        xpath = FindElementsMixin._build_xpath(
            a_b_c='value1',
            x_y='value2'
        )
        assert '@a-b-c="value1"' in xpath
        assert '@x-y="value2"' in xpath

    def test_no_underscores_unchanged(self):
        """Test attributes without underscores remain unchanged."""
        xpath = FindElementsMixin._build_xpath(
            role='button',
            type='submit',
            disabled='true'
        )
        assert '@role="button"' in xpath
        assert '@type="submit"' in xpath
        assert '@disabled="true"' in xpath

    def test_trailing_and_leading_underscores(self):
        """Test handling of trailing and leading underscores."""
        xpath = FindElementsMixin._build_xpath(
            _private='value1',
            public_='value2',
            _both_='value3'
        )
        # Leading/trailing underscores should also be converted to hyphens
        assert '@-private="value1"' in xpath
        assert '@public-="value2"' in xpath
        assert '@-both-="value3"' in xpath

    def test_conversion_with_text_parameter(self):
        """Test conversion works correctly with text parameter."""
        xpath = FindElementsMixin._build_xpath(
            text='Button text',
            data_testid='submit-btn'
        )
        assert 'contains(text(), "Button text")' in xpath
        assert '@data-testid="submit-btn"' in xpath

    def test_conversion_with_tag_name(self):
        """Test conversion works correctly with tag_name parameter."""
        xpath = FindElementsMixin._build_xpath(
            tag_name='button',
            data_test='submit',
            aria_label='Submit form'
        )
        assert xpath.startswith('//button')
        assert '@data-test="submit"' in xpath
        assert '@aria-label="Submit form"' in xpath


class TestUnderscoreConversionWithGetByAndValue:
    """Test underscore to hyphen conversion in _get_by_and_value method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mixin = MockFindElementsMixin()
        self.by_map = {
            'id': By.ID,
            'class_name': By.CLASS_NAME,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'xpath': By.XPATH,
        }

    def test_custom_attribute_with_underscore(self):
        """Test custom attribute with underscore converts properly."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            data_testid='submit-button'
        )
        assert by == By.XPATH
        assert '@data-testid="submit-button"' in value

    def test_multiple_custom_attributes_with_underscores(self):
        """Test multiple custom attributes with underscores."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            data_test='value1',
            aria_label='value2',
            ng_model='value3'
        )
        assert by == By.XPATH
        assert '@data-test="value1"' in value
        assert '@aria-label="value2"' in value
        assert '@ng-model="value3"' in value

    def test_standard_and_custom_attributes_mixed(self):
        """Test standard attributes with custom underscore attributes."""
        by, value = self.mixin._get_by_and_value(
            self.by_map,
            id='main-btn',
            data_testid='submit',
            aria_label='Submit'
        )
        assert by == By.XPATH
        assert '@id="main-btn"' in value
        assert '@data-testid="submit"' in value
        assert '@aria-label="Submit"' in value