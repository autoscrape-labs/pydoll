"""Pure-logic tests for SelectorParser (CSS/XPath building and classification)."""

from __future__ import annotations

import pytest

from pydoll.constants import By
from pydoll.elements.utils.selector_parser import SelectorParser


@pytest.mark.parametrize(
    'expression, expected',
    [
        ('//div', By.XPATH),
        ('./span', By.XPATH),
        ('(/a)', By.XPATH),
        ('.button', By.CSS_SELECTOR),
        ('div.btn', By.CSS_SELECTOR),
        ('#id', By.CSS_SELECTOR),
    ],
)
def test_get_expression_type(expression, expected):
    assert SelectorParser.get_expression_type(expression) == expected


def test_build_xpath_single_criteria():
    assert SelectorParser.build_xpath(id='go') == '//*[@id="go"]'
    assert SelectorParser.build_xpath(name='q') == '//*[@name="q"]'
    assert SelectorParser.build_xpath(tag_name='div') == '//div'
    assert SelectorParser.build_xpath() == '//*'


def test_build_xpath_class_uses_normalized_contains():
    assert SelectorParser.build_xpath(class_name='btn') == (
        '//*[contains(concat(" ", normalize-space(@class), " "), " btn ")]'
    )


def test_build_xpath_text_uses_contains():
    assert SelectorParser.build_xpath(text='Hello') == '//*[contains(text(), "Hello")]'


def test_build_xpath_combines_conditions_with_and_under_tag():
    assert SelectorParser.build_xpath(tag_name='input', id='a', name='b') == (
        '//input[@id="a" and @name="b"]'
    )


def test_build_xpath_custom_attribute_converts_underscore_to_hyphen():
    assert SelectorParser.build_xpath(data_test='v') == '//*[@data-test="v"]'


def test_ensure_relative_xpath():
    assert SelectorParser.ensure_relative_xpath('//div') == './/div'
    assert SelectorParser.ensure_relative_xpath('.//div') == './/div'
    assert SelectorParser.ensure_relative_xpath('./x') == './x'


def test_parse_iframe_segments_xpath_without_iframe_is_single():
    assert SelectorParser.parse_iframe_segments_xpath('//div[@id="x"]') == [
        (By.XPATH, '//div[@id="x"]')
    ]


def test_parse_iframe_segments_xpath_splits_on_iframe():
    assert SelectorParser.parse_iframe_segments_xpath('//iframe//button') == [
        (By.XPATH, '//iframe'),
        (By.XPATH, '//button'),
    ]


def test_parse_iframe_segments_css_without_iframe_is_single():
    assert SelectorParser.parse_iframe_segments_css('div.btn') == [(By.CSS_SELECTOR, 'div.btn')]


def test_parse_iframe_segments_css_splits_on_iframe():
    assert SelectorParser.parse_iframe_segments_css('iframe button') == [
        (By.CSS_SELECTOR, 'iframe'),
        (By.CSS_SELECTOR, 'button'),
    ]


@pytest.mark.parametrize(
    'method, selector, fragment',
    [
        ('id', 'go', '#go'),
        ('class_name', 'btn', '.btn'),
        ('tag_name', 'div', 'div'),
        ('css_selector', '.x > a', '.x > a'),
        ('name', 'q', '@name='),
        ('xpath', '//a[@id="x"]', '@id='),
    ],
)
def test_build_text_expression_targets_each_selector_type(method, selector, fragment):
    result = SelectorParser.build_text_expression(selector, method)
    assert result is not None
    assert fragment in result


def test_parse_iframe_segments_xpath_splits_on_each_iframe():
    assert SelectorParser.parse_iframe_segments_xpath('//iframe//div//iframe//span') == [
        (By.XPATH, '//iframe'),
        (By.XPATH, '//div//iframe'),
        (By.XPATH, '//span'),
    ]


def test_parse_iframe_segments_xpath_trailing_iframe_is_not_a_split():
    assert SelectorParser.parse_iframe_segments_xpath('//div//iframe') == [
        (By.XPATH, '//div//iframe')
    ]


def test_parse_iframe_segments_xpath_without_steps_returns_single():
    assert SelectorParser.parse_iframe_segments_xpath('/') == [(By.XPATH, '/')]


@pytest.mark.parametrize(
    'expression, expected',
    [
        ('div iframe button', [(By.CSS_SELECTOR, 'div iframe'), (By.CSS_SELECTOR, 'button')]),
        ('iframe > button', [(By.CSS_SELECTOR, 'iframe'), (By.CSS_SELECTOR, 'button')]),
        ('iframe + span', [(By.CSS_SELECTOR, 'iframe'), (By.CSS_SELECTOR, 'span')]),
        ('iframe ~ p', [(By.CSS_SELECTOR, 'iframe'), (By.CSS_SELECTOR, 'p')]),
    ],
)
def test_parse_iframe_segments_css_splits_with_combinators(expression, expected):
    assert SelectorParser.parse_iframe_segments_css(expression) == expected


def test_parse_iframe_segments_css_trailing_iframe_is_not_a_split():
    assert SelectorParser.parse_iframe_segments_css('div iframe') == [(By.CSS_SELECTOR, 'div iframe')]


def test_parse_iframe_segments_css_blank_returns_single():
    assert SelectorParser.parse_iframe_segments_css('   ') == [(By.CSS_SELECTOR, '   ')]
