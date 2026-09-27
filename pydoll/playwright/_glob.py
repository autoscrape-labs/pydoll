"""URL matching with Playwright's glob syntax, regular expressions or predicates."""

from __future__ import annotations

import re
from typing import Callable, Optional, Pattern, Union
from urllib.parse import urljoin

URLMatch = Union[str, Pattern[str], Callable[[str], bool]]

_ESCAPED_CHARS = {'$', '^', '+', '.', '*', '(', ')', '|', '\\', '?', '{', '}', '[', ']'}


def glob_to_regex_pattern(glob: str) -> str:
    """Translate a Playwright URL glob into a regular expression source."""
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


class URLMatcher:
    """Match URLs the way Playwright's ``url`` options do."""

    def __init__(self, match: URLMatch, base_url: Optional[str] = None) -> None:
        self._match = match
        self._regex: Optional[Pattern[str]] = None
        if isinstance(match, str):
            glob = match
            if (
                base_url
                and not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', glob)
                and not glob.startswith('*')
            ):
                glob = urljoin(base_url, glob)
            self._regex = re.compile(glob_to_regex_pattern(glob))
        elif isinstance(match, Pattern):
            self._regex = match

    def matches(self, url: str) -> bool:
        if callable(self._match):
            return bool(self._match(url))
        if self._regex is None:
            return False
        return self._regex.search(url) is not None
