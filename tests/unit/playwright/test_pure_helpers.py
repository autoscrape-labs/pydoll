"""Unit tests for the pure-Python helpers of the Playwright-compatible layer."""

from __future__ import annotations

import datetime
import math
import re

import pytest

from pydoll.playwright._glob import URLMatcher, glob_to_regex_pattern
from pydoll.playwright._keys import describe_key, modifier_bits, split_key_string
from pydoll.playwright._selectors import (
    escape_for_attribute_selector,
    escape_for_text_selector,
    get_by_role_selector,
    get_by_test_id_selector,
    get_by_text_selector,
    split_by_frame,
)
from pydoll.playwright._serialization import (
    HANDLE_KEY,
    call_arguments,
    evaluate_source,
    normalize_expression,
    parse_remote_value,
    serialize_argument,
)
from pydoll.protocol.input.types import KeyModifier


class TestGlob:
    @pytest.mark.parametrize(
        ('glob', 'url', 'expected'),
        [
            ('**/*.json', 'https://a.com/x/data.json', True),
            ('**/*.json', 'https://a.com/x/data.js', False),
            ('https://a.com/**', 'https://a.com/path/deep', True),
            ('https://a.com/*', 'https://a.com/path/deep', False),
            ('**/{a,b}.txt', 'http://x/b.txt', True),
            ('**/{a,b}.txt', 'http://x/c.txt', False),
            ('**/?', 'http://x/y', False),
        ],
    )
    def test_glob_patterns(self, glob, url, expected):
        assert bool(re.match(glob_to_regex_pattern(glob), url)) is expected

    def test_matcher_accepts_regex_and_callable(self):
        assert URLMatcher(re.compile(r'wiki')).matches('https://wikipedia.org')
        assert URLMatcher(lambda url: url.endswith('/x')).matches('http://h/x')
        assert not URLMatcher('http://h/x').matches('http://h/y')

    def test_relative_glob_uses_base_url(self):
        assert URLMatcher('/login', base_url='https://site.test').matches('https://site.test/login')


class TestSelectors:
    def test_text_and_attribute_escaping(self):
        assert escape_for_text_selector('a "q"') == '"a \\"q\\""i'
        assert escape_for_text_selector('x', exact=True) == '"x"s'
        assert escape_for_text_selector(re.compile('a/b', re.I)) == '/a/b/i'
        assert escape_for_attribute_selector('v"w', exact=True) == '"v\\"w"s'

    def test_builders(self):
        assert get_by_text_selector('Hi') == 'internal:text="Hi"i'
        assert get_by_test_id_selector('save') == 'internal:testid=[data-testid="save"s]'
        assert get_by_role_selector('button', name='Save', exact=True, pressed=True, level=None) == (
            'internal:role=button[name="Save"s][pressed=true]'
        )

    def test_split_by_frame_respects_quotes(self):
        chunks = split_by_frame('iframe >> internal:control=enter-frame >> text="a >> b" >> nth=0')
        assert chunks == ['iframe', 'text="a >> b" >> nth=0']
        assert split_by_frame('#a >> #b') == ['#a >> #b']


class TestKeys:
    def test_named_and_character_keys(self):
        enter = describe_key('Enter', False)
        assert (enter.key, enter.key_code, enter.text) == ('Enter', 13, '\r')
        a = describe_key('a', False)
        assert (a.key, a.code, a.key_code) == ('a', 'KeyA', 65)
        upper = describe_key('A', False)
        assert (upper.key, upper.shifted) == ('A', True)
        assert describe_key('KeyA', True).key == 'A'
        assert describe_key('Digit1', True).key == '!'
        assert describe_key('ArrowDown', False).key_code == 40

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match='Unknown key'):
            describe_key('NotAKey', False)

    def test_split_and_modifiers(self):
        assert split_key_string('Control+Shift+A') == ['Control', 'Shift', 'A']
        assert split_key_string('+') == ['+']
        assert modifier_bits(['Control', 'Shift']) == KeyModifier.CTRL | KeyModifier.SHIFT
        assert modifier_bits([]) is None


class TestSerialization:
    def test_normalize_expression_wraps_functions(self):
        assert normalize_expression(' function() { return 1 } ') == '(function() { return 1 })'
        assert normalize_expression('async function f() {}') == '(async function f() {})'
        assert normalize_expression('() => 1') == '() => 1'
        assert normalize_expression('document.title') == 'document.title'

    def test_special_values(self):
        tree, handles = serialize_argument({'n': math.nan, 'i': math.inf, 'z': -0.0, 'list': (1, 'a')})
        assert tree['n'] == {'__pydoll_value__': 'NaN'}
        assert tree['i'] == {'__pydoll_value__': 'Infinity'}
        assert tree['z'] == {'__pydoll_value__': '-0'}
        assert tree['list'] == [1, 'a']
        assert handles == []

    def test_dates_and_regex(self):
        tree, _ = serialize_argument([datetime.datetime(2024, 1, 2, tzinfo=datetime.timezone.utc), re.compile('a+', re.I)])
        assert tree[0] == {'__pydoll_date__': '2024-01-02T00:00:00Z'}
        assert tree[1] == {'__pydoll_regex__': ['a+', 'i']}

    def test_call_arguments_shape(self):
        arguments = call_arguments({'k': 1})
        assert arguments == [{'value': {'k': 1}}]
        assert HANDLE_KEY == '__pydoll_handle__'

    def test_evaluate_source_embeds_the_expression_without_eval(self):
        source = evaluate_source('() => 7 * 6')
        assert '() => 7 * 6' in source
        assert 'eval' not in source
        assert 'result = result(arg)' in source
        assert 'result = result(this, arg)' in evaluate_source('e => e', with_this=True)
        assert '(function() { return 1 })' in evaluate_source('function() { return 1 }')

    def test_circular_structure_rejected(self):
        loop: list = []
        loop.append(loop)
        with pytest.raises(ValueError, match='circular'):
            serialize_argument(loop)

    def test_parse_remote_value(self):
        assert parse_remote_value({'type': 'undefined'}) is None
        assert math.isnan(parse_remote_value({'unserializableValue': 'NaN'}))
        assert parse_remote_value({'unserializableValue': 'Infinity'}) == math.inf
        assert parse_remote_value({'type': 'string', 'value': 'x'}) == 'x'
