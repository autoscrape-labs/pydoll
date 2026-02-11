"""
Selector parsing and building utilities for element finding.

Centralises all logic that inspects, builds, or transforms CSS and XPath
selector strings. This keeps the mixin layer focused on orchestration
(finding elements, managing timeouts, issuing CDP commands) while the
pure string-manipulation lives here.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from pydoll.constants import By, Scripts
from pydoll.utils import normalize_synthetic_xpath

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_IFRAME_XPATH_NODE_RE = re.compile(r'^(?:\w+::)?iframe(?:\[|$)', re.IGNORECASE)
_IFRAME_XPATH_GROUPED_RE = re.compile(r'\biframe\b', re.IGNORECASE)
_CSS_TAG_NAME_RE = re.compile(r'^([a-zA-Z][a-zA-Z0-9-]*)')
_XPATH_PREFIXES: list[tuple[str, int]] = [('.//', 3), ('//', 2), ('./', 2), ('/', 1)]

# Lookup tables for the nesting-depth tracker
_QUOTE_TRANSITIONS: dict[str, tuple[int, bool]] = {"'": (0, True), '"': (1, True)}
_DEPTH_TRANSITIONS: dict[str, tuple[int, int]] = {
    '[': (0, 1),
    ']': (0, -1),
    '(': (1, 1),
    ')': (1, -1),
}


class SelectorParser:
    """
    Stateless helper that parses, builds and classifies CSS / XPath selectors.

    Every method is a ``@staticmethod`` — the class is used purely as a
    namespace to keep the parsing surface area together. ``FindElementsMixin``
    delegates all selector string work here.
    """

    # ------------------------------------------------------------------
    # Expression type detection
    # ------------------------------------------------------------------

    @staticmethod
    def get_expression_type(expression: str) -> By:
        """
        Auto-detect selector type from expression syntax.

        Patterns:
        - XPath: starts with ``./``, ``/`` or ``(/``
        - Default: ``By.CSS_SELECTOR``
        """
        if expression.startswith(('./', '/', '(/')):
            return By.XPATH
        return By.CSS_SELECTOR

    # ------------------------------------------------------------------
    # XPath building from keyword criteria
    # ------------------------------------------------------------------

    @staticmethod
    def build_xpath(
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes: str,
    ) -> str:
        """
        Build XPath expression from multiple attribute criteria.

        Constructs complex XPath combining multiple conditions with ``and``
        operators. Handles class names correctly for space-separated class
        lists. Uses ``contains()`` for text matching (partial text support).

        Note:
            Attribute names with underscores are automatically converted to
            hyphens to match HTML attribute naming conventions
            (e.g. ``data_test`` -> ``data-test``).
        """
        xpath_conditions: list[str] = []
        base_xpath = f'//{tag_name}' if tag_name else '//*'
        if id:
            xpath_conditions.append(f'@id="{id}"')
        if class_name:
            xpath_conditions.append(
                f'contains(concat(" ", normalize-space(@class), " "), " {class_name} ")'
            )
        if name:
            xpath_conditions.append(f'@name="{name}"')
        if text:
            xpath_conditions.append(f'contains(text(), "{text}")')
        for attribute, value in attributes.items():
            html_attribute = attribute.replace('_', '-')
            xpath_conditions.append(f'@{html_attribute}="{value}"')

        xpath = (
            f'{base_xpath}[{" and ".join(xpath_conditions)}]' if xpath_conditions else base_xpath
        )
        logger.debug(f'build_xpath() -> {xpath}')
        return xpath

    # ------------------------------------------------------------------
    # XPath helpers
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_relative_xpath(xpath: str) -> str:
        """
        Ensure XPath is relative by prepending dot if needed.

        Converts absolute XPath to relative for context-based searches.
        """
        return f'.{xpath}' if not xpath.startswith('.') else xpath

    # ------------------------------------------------------------------
    # JS text-expression builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_text_expression(selector: str, method: str) -> Optional[str]:
        """
        Build JS expression using ``Scripts`` to extract ``textContent``
        based on selector type.
        """
        raw = str(selector)
        method_lc = (method or '').lower()

        if 'xpath' in method_lc:
            normalized_xpath = normalize_synthetic_xpath(raw)
            escaped_xpath = normalized_xpath.replace('"', '\\"')
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', escaped_xpath)

        if method_lc == 'name':
            escaped_name = raw.replace('"', '\\"')
            xpath = f'//*[@name="{escaped_name}"]'
            return Scripts.GET_TEXT_BY_XPATH.replace('{escaped_value}', xpath)

        escaped = raw.replace('\\', '\\\\').replace('"', '\\"')
        if method_lc == 'id':
            css = f'#{escaped}'
        elif method_lc == 'class_name':
            css = f'.{escaped}'
        elif method_lc == 'tag_name':
            css = escaped
        else:
            css = escaped
        return Scripts.GET_TEXT_BY_CSS.replace('{selector}', css)

    # ------------------------------------------------------------------
    # Iframe-crossing: XPath
    # ------------------------------------------------------------------

    @staticmethod
    def parse_iframe_segments_xpath(expression: str) -> list[tuple[By, str]]:
        """
        Split an XPath expression at iframe boundaries for cross-iframe
        traversal.

        Parses the XPath into steps separated by ``/`` or ``//``, respecting
        quoted strings, brackets and parentheses. Steps whose node test is
        ``iframe`` (case-insensitive) act as split points: everything up to
        and including the iframe step becomes one segment, and the remainder
        starts a new segment prefixed with ``//``.

        Args:
            expression: Raw XPath expression.

        Returns:
            List of ``(By.XPATH, segment)`` tuples.  A single-element list
            when no iframe crossing is detected.
        """
        xpath_steps = SelectorParser._tokenize_xpath_steps(expression)
        if not xpath_steps:
            return [(By.XPATH, expression)]

        iframe_split_indices: list[int] = [
            step_index
            for step_index, (_sep, step_text) in enumerate(xpath_steps)
            if SelectorParser._is_iframe_xpath_step(step_text) and step_index < len(xpath_steps) - 1
        ]

        if not iframe_split_indices:
            return [(By.XPATH, expression)]

        return SelectorParser._build_xpath_segments(xpath_steps, iframe_split_indices)

    # ------------------------------------------------------------------
    # Iframe-crossing: CSS
    # ------------------------------------------------------------------

    @staticmethod
    def parse_iframe_segments_css(expression: str) -> list[tuple[By, str]]:
        """
        Split a CSS selector at iframe boundaries for cross-iframe traversal.

        Tokenises the selector into compound selectors separated by
        combinators (space, ``>``, ``+``, ``~``), respecting quoted strings,
        brackets and parentheses. Compounds whose tag name is ``iframe``
        (case-insensitive) act as split points.

        Args:
            expression: Raw CSS selector.

        Returns:
            List of ``(By.CSS_SELECTOR, segment)`` tuples.  A single-element
            list when no iframe crossing is detected.
        """
        css_compounds = SelectorParser._tokenize_css_compounds(expression)
        if not css_compounds:
            return [(By.CSS_SELECTOR, expression)]

        iframe_split_indices: list[int] = [
            compound_index
            for compound_index, (compound_text, _comb) in enumerate(css_compounds)
            if SelectorParser._is_iframe_css_compound(compound_text)
            and compound_index < len(css_compounds) - 1
        ]

        if not iframe_split_indices:
            return [(By.CSS_SELECTOR, expression)]

        return SelectorParser._build_css_segments(css_compounds, iframe_split_indices)

    # ==================================================================
    # Private helpers
    # ==================================================================

    @staticmethod
    def _is_at_nesting_depth_zero(
        char: str,
        quote_state: list[bool],
        depth_state: list[int],
    ) -> bool:
        """
        Track quote/bracket/paren nesting and return whether char is at
        depth 0.  Mutates *quote_state* and *depth_state* in place.
        """
        if quote_state[0] or quote_state[1]:
            if quote_state[0]:
                quote_state[0] = char != "'"
            else:
                quote_state[1] = char != '"'
            return False

        if char in _QUOTE_TRANSITIONS:
            index, value = _QUOTE_TRANSITIONS[char]
            quote_state[index] = value
            return False

        if char in _DEPTH_TRANSITIONS:
            index, delta = _DEPTH_TRANSITIONS[char]
            depth_state[index] += delta
            return False

        return depth_state[0] == 0 and depth_state[1] == 0

    # -- XPath tokenizer -----------------------------------------------

    @staticmethod
    def _detect_xpath_leading_separator(expression: str) -> tuple[str, int]:
        """Return ``(separator, start_index)`` for the XPath prefix."""
        if expression.startswith('('):
            return '', 0
        for prefix, length in _XPATH_PREFIXES:
            if expression.startswith(prefix):
                return prefix, length
        return '', 0

    @staticmethod
    def _tokenize_xpath_steps(expression: str) -> list[tuple[str, str]]:
        """Tokenize XPath into ``(separator, step_text)`` pairs."""
        xpath_steps: list[tuple[str, str]] = []
        current_separator, token_start = SelectorParser._detect_xpath_leading_separator(expression)
        char_index = token_start
        quote_state = [False, False]
        depth_state = [0, 0]

        while char_index < len(expression):
            char = expression[char_index]
            at_depth_zero = SelectorParser._is_at_nesting_depth_zero(char, quote_state, depth_state)

            if at_depth_zero and char == '/':
                step_text = expression[token_start:char_index]
                if step_text:
                    xpath_steps.append((current_separator, step_text))
                is_double_slash = (
                    char_index + 1 < len(expression) and expression[char_index + 1] == '/'
                )
                current_separator = '//' if is_double_slash else '/'
                char_index += 2 if is_double_slash else 1
                token_start = char_index
                continue
            char_index += 1

        remaining_text = expression[token_start:]
        if remaining_text:
            xpath_steps.append((current_separator, remaining_text))

        return xpath_steps

    @staticmethod
    def _is_iframe_xpath_step(step_text: str) -> bool:
        """Return whether a single XPath step's node test is ``iframe``."""
        if step_text.startswith('('):
            return bool(_IFRAME_XPATH_GROUPED_RE.search(step_text))
        return bool(_IFRAME_XPATH_NODE_RE.match(step_text))

    @staticmethod
    def _build_xpath_segments(
        xpath_steps: list[tuple[str, str]],
        iframe_split_indices: list[int],
    ) -> list[tuple[By, str]]:
        """Reassemble XPath steps into segments split at iframe indices."""
        segments: list[tuple[By, str]] = []
        segment_start = 0

        for split_index in iframe_split_indices:
            segment_parts: list[str] = []
            for step_index in range(segment_start, split_index + 1):
                separator, step_text = xpath_steps[step_index]
                if step_index == segment_start and segment_start != 0:
                    segment_parts.append('//' + step_text)
                else:
                    segment_parts.append(separator + step_text)
            segments.append((By.XPATH, ''.join(segment_parts)))
            segment_start = split_index + 1

        if segment_start < len(xpath_steps):
            segment_parts = []
            for step_index in range(segment_start, len(xpath_steps)):
                separator, step_text = xpath_steps[step_index]
                if step_index == segment_start:
                    segment_parts.append('//' + step_text)
                else:
                    segment_parts.append(separator + step_text)
            segments.append((By.XPATH, ''.join(segment_parts)))

        return segments

    # -- CSS tokenizer --------------------------------------------------

    @staticmethod
    def _tokenize_css_compounds(expression: str) -> list[tuple[str, str | None]]:
        """Tokenize CSS selector into ``(compound_text, combinator_after)`` pairs."""
        css_compounds: list[tuple[str, str | None]] = []
        token_start = 0
        char_index = 0
        quote_state = [False, False]
        depth_state = [0, 0]

        while char_index < len(expression):
            char = expression[char_index]
            at_depth_zero = SelectorParser._is_at_nesting_depth_zero(char, quote_state, depth_state)

            if at_depth_zero and char in ' >+~':
                compound_text = expression[token_start:char_index]
                if not compound_text.strip():
                    char_index += 1
                    continue
                combinator, char_index = SelectorParser._consume_css_combinator(
                    expression, char_index
                )
                css_compounds.append((compound_text, combinator))
                token_start = char_index
                continue
            char_index += 1

        remaining_text = expression[token_start:].strip()
        if remaining_text:
            css_compounds.append((remaining_text, None))

        return css_compounds

    @staticmethod
    def _consume_css_combinator(expression: str, start: int) -> tuple[str, int]:
        """Consume a CSS combinator region and return ``(combinator, next_index)``."""
        char_index = start
        while char_index < len(expression) and expression[char_index] == ' ':
            char_index += 1
        if char_index < len(expression) and expression[char_index] in '>+~':
            combinator = expression[char_index]
            char_index += 1
            while char_index < len(expression) and expression[char_index] == ' ':
                char_index += 1
        else:
            combinator = ' '
        return combinator, char_index

    @staticmethod
    def _is_iframe_css_compound(compound_text: str) -> bool:
        """Return whether a CSS compound selector's tag name is ``iframe``."""
        stripped = compound_text.strip()
        if stripped and stripped[0] in '.#[:':
            return False
        match = _CSS_TAG_NAME_RE.match(stripped)
        if not match:
            return False
        return match.group(1).lower() == 'iframe'

    @staticmethod
    def _format_css_combinator(combinator: str) -> str:
        """Format a CSS combinator for human-readable output."""
        if combinator == ' ':
            return ' '
        return f' {combinator} '

    @staticmethod
    def _build_css_segments(
        css_compounds: list[tuple[str, str | None]],
        iframe_split_indices: list[int],
    ) -> list[tuple[By, str]]:
        """Reassemble CSS compounds into segments split at iframe indices."""
        segments: list[tuple[By, str]] = []
        segment_start = 0

        for split_index in iframe_split_indices:
            segment_parts: list[str] = []
            for compound_index in range(segment_start, split_index + 1):
                compound_text, _combinator = css_compounds[compound_index]
                if compound_index > segment_start:
                    previous_combinator = css_compounds[compound_index - 1][1] or ' '
                    segment_parts.append(SelectorParser._format_css_combinator(previous_combinator))
                segment_parts.append(compound_text)
            segments.append((By.CSS_SELECTOR, ''.join(segment_parts)))
            segment_start = split_index + 1

        if segment_start < len(css_compounds):
            segment_parts = []
            for compound_index in range(segment_start, len(css_compounds)):
                compound_text, _combinator = css_compounds[compound_index]
                if compound_index > segment_start:
                    previous_combinator = css_compounds[compound_index - 1][1] or ' '
                    segment_parts.append(SelectorParser._format_css_combinator(previous_combinator))
                segment_parts.append(compound_text)
            segments.append((By.CSS_SELECTOR, ''.join(segment_parts)))

        return segments
