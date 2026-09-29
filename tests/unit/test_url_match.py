"""The one URL matcher every wait and interception shares."""

from __future__ import annotations

import re

import pytest

from pydoll.utils import glob_to_regex_pattern, url_matcher


@pytest.mark.parametrize(
    ('glob', 'url', 'expected'),
    [
        ('**/api/*', 'https://shop.test/api/prices', True),
        ('**/api/*', 'https://shop.test/api/v1/prices', False),
        ('**/api/**', 'https://shop.test/api/v1/prices', True),
        ('*/checkout/*', 'https://shop.test/checkout/42', False),
        ('https://shop.test/checkout/*', 'https://shop.test/checkout/42', True),
        ('**/*.{png,jpg}', 'https://cdn.test/img/logo.png', True),
        ('**/*.{png,jpg}', 'https://cdn.test/img/logo.svg', False),
        ('https://shop.test/?q=a+b', 'https://shop.test/?q=a+b', True),
    ],
)
def test_glob_patterns(glob, url, expected):
    assert url_matcher(glob)(url) is expected


def test_regex_is_searched_anywhere_in_the_url():
    matches = url_matcher(re.compile(r'/checkout/\d+$'))
    assert matches('https://shop.test/app/checkout/42')
    assert not matches('https://shop.test/app/checkout/')


def test_callable_decides_by_itself():
    matches = url_matcher(lambda url: url.startswith('https://') and 'api' in url)
    assert matches('https://shop.test/api')
    assert not matches('http://shop.test/api')


def test_unsupported_pattern_type_is_rejected():
    with pytest.raises(TypeError):
        url_matcher(42)


def test_glob_translation_is_anchored_and_escapes_regex_characters():
    pattern = glob_to_regex_pattern('https://a.test/path?x=1')
    assert pattern.startswith('^') and pattern.endswith('$')
    assert re.match(pattern, 'https://a.test/path?x=1')
    assert not re.match(pattern, 'https://aXtest/path?x=1')
