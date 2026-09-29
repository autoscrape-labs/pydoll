"""Match URLs against a glob, a regular expression or a predicate.

Every pydoll method that takes a URL to wait for or to intercept accepts the
same three forms:

- a string with globs: ``*`` matches within one path segment, ``**`` matches
  across segments, ``{a,b}`` matches either alternative;
- a compiled ``re.Pattern``, searched anywhere in the URL;
- a callable that receives the URL and returns whether it matches.
"""

from __future__ import annotations

import re
from typing import Callable, Pattern

UrlPattern = str | Pattern[str] | Callable[[str], bool]

_ESCAPED_CHARS = {'$', '^', '+', '.', '*', '(', ')', '|', '\\', '?', '{', '}', '[', ']'}


def glob_to_regex_pattern(glob: str) -> str:
    """Translate a URL glob into a regular expression source anchored at both ends."""
    tokens = ['^']
    in_group = False
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == '\\' and i + 1 < len(glob):
            char = glob[i + 1]
            tokens.append('\\' + char if char in _ESCAPED_CHARS else char)
            i += 1
        elif c == '*':
            char_before = glob[i - 1] if i > 0 else None
            star_count = 1
            while i + 1 < len(glob) and glob[i + 1] == '*':
                star_count += 1
                i += 1
            if star_count > 1:
                char_after = glob[i + 1] if i + 1 < len(glob) else None
                if char_after == '/':
                    tokens.append('((.+/)|)' if char_before == '/' else '(.*/)')
                    i += 1
                else:
                    tokens.append('(.*)')
            else:
                tokens.append('([^/]*)')
        elif c == '{':
            in_group = True
            tokens.append('(')
        elif c == '}':
            in_group = False
            tokens.append(')')
        elif c == ',':
            tokens.append('|' if in_group else '\\,')
        else:
            tokens.append('\\' + c if c in _ESCAPED_CHARS else c)
        i += 1
    tokens.append('$')
    return ''.join(tokens)


def url_matcher(pattern: UrlPattern) -> Callable[[str], bool]:
    """Turn a glob, a regular expression or a predicate into a ``url -> bool`` function.

    Args:
        pattern: The glob string, compiled pattern or predicate to match with.

    Returns:
        A function that reports whether a URL matches.
    """
    if isinstance(pattern, str):
        regex = re.compile(glob_to_regex_pattern(pattern))
        return lambda url: regex.search(url) is not None
    if isinstance(pattern, Pattern):
        compiled = pattern
        return lambda url: compiled.search(url) is not None
    if callable(pattern):
        predicate = pattern
        return lambda url: bool(predicate(url))
    raise TypeError(
        f'A URL pattern must be a str, a re.Pattern or a callable, not {type(pattern)!r}'
    )
