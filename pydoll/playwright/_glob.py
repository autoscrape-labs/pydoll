"""URL matching with Playwright's glob syntax, regular expressions or predicates."""

from __future__ import annotations

import re
from typing import Callable, Optional, Pattern, Union
from urllib.parse import urljoin

from pydoll.utils.url_match import glob_to_regex_pattern

URLMatch = Union[str, Pattern[str], Callable[[str], bool]]


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
