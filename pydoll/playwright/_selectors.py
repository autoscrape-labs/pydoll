"""Selector-string builders and escaping shared by Page, Frame and Locator.

Port of the helpers in ``playwright/_impl/_locator.py`` and ``_str_utils.py``.
The strings produced here are consumed by the injected engine.
"""

from __future__ import annotations

import json
import re
from typing import Pattern

TextMatch = str | Pattern[str]

_test_id_attribute_name = 'data-testid'


def test_id_attribute_name() -> str:
    return _test_id_attribute_name


def set_test_id_attribute_name(name: str) -> None:
    global _test_id_attribute_name
    _test_id_attribute_name = name


def escape_regex_flags(pattern: Pattern[str]) -> str:
    flags = ''
    if pattern.flags & re.IGNORECASE:
        flags += 'i'
    if pattern.flags & re.DOTALL:
        flags += 's'
    if pattern.flags & re.MULTILINE:
        flags += 'm'
    return flags


def escape_regex_for_selector(pattern: Pattern[str]) -> str:
    source = re.sub(r'(^|[^\\])(\\\\)*(["\'`])', r'\1\2\\\3', pattern.pattern).replace(
        '>>', '\\>\\>'
    )
    return f'/{source}/{escape_regex_flags(pattern)}'


def escape_for_text_selector(text: TextMatch, exact: bool | None = None) -> str:
    if isinstance(text, Pattern):
        return escape_regex_for_selector(text)
    return json.dumps(text, ensure_ascii=False) + ('s' if exact else 'i')


def escape_for_attribute_selector(value: TextMatch, exact: bool | None = None) -> str:
    if isinstance(value, Pattern):
        return escape_regex_for_selector(value)
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"' + ('s' if exact else 'i')


def bool_to_js(value: bool) -> str:
    return 'true' if value else 'false'


def get_by_test_id_selector(test_id: TextMatch) -> str:
    value = escape_for_attribute_selector(test_id, True)
    return f'internal:testid=[{_test_id_attribute_name}={value}]'


def get_by_attribute_text_selector(
    attr_name: str, text: TextMatch, exact: bool | None = None
) -> str:
    return f'internal:attr=[{attr_name}={escape_for_attribute_selector(text, exact=exact)}]'


def get_by_label_selector(text: TextMatch, exact: bool | None = None) -> str:
    return 'internal:label=' + escape_for_text_selector(text, exact=exact)


def get_by_alt_text_selector(text: TextMatch, exact: bool | None = None) -> str:
    return get_by_attribute_text_selector('alt', text, exact=exact)


def get_by_title_selector(text: TextMatch, exact: bool | None = None) -> str:
    return get_by_attribute_text_selector('title', text, exact=exact)


def get_by_placeholder_selector(text: TextMatch, exact: bool | None = None) -> str:
    return get_by_attribute_text_selector('placeholder', text, exact=exact)


def get_by_text_selector(text: TextMatch, exact: bool | None = None) -> str:
    return 'internal:text=' + escape_for_text_selector(text, exact=exact)


def get_by_role_selector(
    role: str,
    checked: bool | None = None,
    disabled: bool | None = None,
    expanded: bool | None = None,
    include_hidden: bool | None = None,
    level: int | None = None,
    name: TextMatch | None = None,
    pressed: bool | None = None,
    selected: bool | None = None,
    exact: bool | None = None,
) -> str:
    props: list[tuple[str, str]] = []
    if checked is not None:
        props.append(('checked', bool_to_js(checked)))
    if disabled is not None:
        props.append(('disabled', bool_to_js(disabled)))
    if selected is not None:
        props.append(('selected', bool_to_js(selected)))
    if expanded is not None:
        props.append(('expanded', bool_to_js(expanded)))
    if include_hidden is not None:
        props.append(('include-hidden', bool_to_js(include_hidden)))
    if level is not None:
        props.append(('level', str(level)))
    if name is not None:
        props.append(('name', escape_for_attribute_selector(name, exact=exact)))
    if pressed is not None:
        props.append(('pressed', bool_to_js(pressed)))
    props_str = ''.join(f'[{key}={value}]' for key, value in props)
    return f'internal:role={role}{props_str}'


def with_has_text(selector: str, has_text: TextMatch) -> str:
    return f'{selector} >> internal:has-text={escape_for_text_selector(has_text, exact=False)}'


def with_has_not_text(selector: str, has_not_text: TextMatch) -> str:
    return (
        f'{selector} >> internal:has-not-text={escape_for_text_selector(has_not_text, exact=False)}'
    )


def with_has(selector: str, inner_selector: str) -> str:
    return f'{selector} >> internal:has={json.dumps(inner_selector, ensure_ascii=False)}'


def with_has_not(selector: str, inner_selector: str) -> str:
    return f'{selector} >> internal:has-not={json.dumps(inner_selector, ensure_ascii=False)}'


def with_visible(selector: str, visible: bool) -> str:
    return f'{selector} >> visible={bool_to_js(visible)}'


ENTER_FRAME = 'internal:control=enter-frame'


def split_by_frame(selector: str) -> list[str]:
    """Split a selector at frame boundaries, honoring quotes like the engine parser."""
    chunks: list[str] = []
    parts = _split_top_level(selector)
    current: list[str] = []
    for part in parts:
        if part.strip() == ENTER_FRAME:
            chunks.append(' >> '.join(current))
            current = []
        else:
            current.append(part.strip())
    chunks.append(' >> '.join(current))
    return chunks


def _split_top_level(selector: str) -> list[str]:
    parts: list[str] = []
    index = 0
    start = 0
    quote: str | None = None
    while index < len(selector):
        char = selector[index]
        if char == '\\' and index + 1 < len(selector):
            index += 2
            continue
        if char == quote:
            quote = None
        elif quote is None and char in {'"', "'", '`'}:
            quote = char
        elif quote is None and char == '>' and selector[index + 1 : index + 2] == '>':
            parts.append(selector[start:index])
            index += 2
            start = index
            continue
        index += 1
    parts.append(selector[start:])
    return parts
