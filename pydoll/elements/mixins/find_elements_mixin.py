from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Generic, TypeVar, cast, overload

from pydoll.constants import By
from pydoll.elements.utils import SelectorParser
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.utils import PollInterval

if TYPE_CHECKING:
    from typing import Literal

    from pydoll.elements.protocols import WebElementProtocol


logger = logging.getLogger(__name__)

T_Element = TypeVar('T_Element', bound='WebElementProtocol')


class FindElementsMixin(Generic[T_Element]):
    """
    Mixin providing comprehensive element finding and waiting capabilities.

    Implements DOM element location using various selector strategies (CSS, XPath, etc.)
    with support for single/multiple element finding and configurable waiting.
    Classes using this mixin gain powerful element discovery without implementing
    complex location logic themselves.

    The mixin is protocol-agnostic: the search itself is delegated to
    ``_find_element`` / ``_find_elements``, implemented per protocol
    (``CDPFindElementsMixin`` for Chromium, ``BidiFindElementsMixin`` for Firefox).
    """

    _css_only: bool = False

    async def _find_element(self, by: By, value: str, raise_exc: bool = True) -> T_Element | None:
        """
        Find first element matching selector.

        Internal method performing the actual element search. Searches in the
        document context or relative to the current element (when used from an
        element). Implemented per protocol (CDP/BiDi).

        Args:
            by: Selector strategy (CSS_SELECTOR, XPATH, ID, etc.).
            value: Selector value to locate element.
            raise_exc: Whether to raise ElementNotFound if not found.

        Returns:
            Element instance or None if not found and raise_exc=False.

        Raises:
            ElementNotFound: If element not found and raise_exc=True.
        """
        raise NotImplementedError

    async def _find_elements(self, by: By, value: str, raise_exc: bool = True) -> list[T_Element]:
        """
        Find all elements matching selector.

        Internal method performing the actual multi-element search. Searches in
        the document context or relative to the current element (when used from
        an element). Implemented per protocol (CDP/BiDi).

        Args:
            by: Selector strategy (CSS_SELECTOR, XPATH, ID, etc.).
            value: Selector value to locate elements.
            raise_exc: Whether to raise ElementNotFound if none found.

        Returns:
            List of element instances (empty if none found and raise_exc=False).

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
        """
        raise NotImplementedError

    @staticmethod
    def _build_text_expression(selector: str, method: str) -> str | None:
        """
        Build JS expression using Scripts to extract textContent based on selector type.
        """
        return SelectorParser.build_text_expression(selector, method)

    @overload
    async def find(
        self,
        id: str | None = ...,
        class_name: str | None = ...,
        name: str | None = ...,
        tag_name: str | None = ...,
        text: str | None = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> T_Element: ...

    @overload
    async def find(
        self,
        id: str | None = ...,
        class_name: str | None = ...,
        name: str | None = ...,
        tag_name: str | None = ...,
        text: str | None = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> T_Element | None: ...

    @overload
    async def find(
        self,
        id: str | None = ...,
        class_name: str | None = ...,
        name: str | None = ...,
        tag_name: str | None = ...,
        text: str | None = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> list[T_Element]: ...

    @overload
    async def find(
        self,
        id: str | None = ...,
        class_name: str | None = ...,
        name: str | None = ...,
        tag_name: str | None = ...,
        text: str | None = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> list[T_Element] | None: ...

    @overload
    async def find(
        self,
        id: str | None = ...,
        class_name: str | None = ...,
        name: str | None = ...,
        tag_name: str | None = ...,
        text: str | None = ...,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
        **attributes,
    ) -> T_Element | list[T_Element] | None: ...

    async def find(
        self,
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        **attributes: dict[str, str],
    ) -> T_Element | list[T_Element] | None:
        """
        Find element(s) using combination of common HTML attributes.

        Flexible element location using standard attributes. Multiple attributes
        can be combined for specific selectors (builds XPath when multiple specified).

        Args:
            id: Element ID attribute value.
            class_name: CSS class name to match.
            name: Element name attribute value.
            tag_name: HTML tag name (e.g., "div", "input").
            text: Text content to match within element.
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.
            **attributes: Additional HTML attributes to match.

        Returns:
            Element, list of elements, or None based on find_all and raise_exc.

        Raises:
            ValueError: If no search criteria provided.
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called on a ShadowRoot (use query() with CSS instead).
        """
        if self._css_only:
            raise NotImplementedError(
                'find() is not supported on ShadowRoot. Use query() with a CSS selector instead.'
            )

        logger.debug(
            'find() called with id=%s, class_name=%s, name=%s, tag_name=%s, text=%s, '
            'timeout=%s, find_all=%s, raise_exc=%s, attrs=%s',
            id,
            class_name,
            name,
            tag_name,
            text,
            timeout,
            find_all,
            raise_exc,
            attributes,
        )
        if not any([id, class_name, name, tag_name, text, *attributes.keys()]):
            raise ValueError(
                'At least one of the following arguments must be provided: id, '
                'class_name, name, tag_name, text'
            )

        by_map = {
            'id': By.ID,
            'class_name': By.CLASS_NAME,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'xpath': By.XPATH,
        }
        by, value = self._get_by_and_value(
            by_map, id, class_name, name, tag_name, text, **attributes
        )
        logger.debug('find() resolved to by=%s value=%s', by, value)
        return await self._find_or_wait_element(
            by, value, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
    ) -> T_Element: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
    ) -> T_Element | None: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
    ) -> list[T_Element]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
    ) -> list[T_Element] | None: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
    ) -> T_Element | list[T_Element] | None: ...

    async def query(
        self, expression: str, timeout: int = 0, find_all: bool = False, raise_exc: bool = True
    ) -> T_Element | list[T_Element] | None:
        """
        Find element(s) using raw CSS selector or XPath expression.

        Direct access using CSS or XPath syntax. Selector type automatically
        determined based on expression pattern.

        Args:
            expression: Selector expression (CSS, XPath, ID with #, class with .).
            timeout: Maximum seconds to wait for elements to appear.
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.

        Returns:
            Element, list of elements, or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
            NotImplementedError: If called with XPath on a ShadowRoot.
        """
        if self._css_only and self._get_expression_type(expression) == By.XPATH:
            raise NotImplementedError(
                'XPath is not supported on ShadowRoot. Use a CSS selector instead.'
            )

        logger.debug(
            'query() called with expression=%s, timeout=%s, find_all=%s, raise_exc=%s',
            expression,
            timeout,
            find_all,
            raise_exc,
        )
        by = self._get_expression_type(expression)
        logger.debug('query() resolved to by=%s', by)
        return await self._find_or_wait_element(
            by=by, value=expression, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    async def _find_or_wait_element(
        self,
        by: By,
        value: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> T_Element | list[T_Element] | None:
        """
        Core element finding method with optional waiting capability.

        Searches for elements with flexible waiting. If a timeout is given, it
        polls with a short, growing pause until success or timeout. This is the
        engine behind ``find()`` and ``query()``; those two are the public way in.

        Args:
            by: Selector strategy (CSS_SELECTOR, XPATH, ID, etc.).
            value: Selector value to locate element(s).
            timeout: Maximum seconds to wait (0 = no waiting).
            find_all: If True, returns all matches; if False, first match only.
            raise_exc: Whether to raise exception if no elements found.

        Returns:
            Element, list of elements, or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found with timeout=0 and raise_exc=True.
            WaitElementTimeout: If elements not found within timeout and raise_exc=True.
        """
        logger.debug(
            '_find_or_wait_element(): by=%s, value=%s, timeout=%s, find_all=%s, raise_exc=%s',
            by,
            value,
            timeout,
            find_all,
            raise_exc,
        )

        if by == By.XPATH:
            segments = SelectorParser.parse_iframe_segments_xpath(value)
        elif by == By.CSS_SELECTOR:
            segments = SelectorParser.parse_iframe_segments_css(value)
        else:
            segments = [(by, value)]

        if len(segments) > 1:
            return await self._find_across_iframes(segments, timeout, find_all, raise_exc)

        find_method = self._find_element if not find_all else self._find_elements
        start_time = asyncio.get_running_loop().time()

        if not timeout:
            logger.debug('No timeout specified; performing single attempt')
            return await find_method(by, value, raise_exc=raise_exc)

        interval = PollInterval()
        while True:
            element = await find_method(by, value, raise_exc=False)
            if element:
                if isinstance(element, list):
                    logger.debug('Found %s elements within timeout window', len(element))
                else:
                    logger.debug('Found 1 element within timeout window')
                return element

            if asyncio.get_running_loop().time() - start_time > timeout:
                if raise_exc:
                    logger.error('Timeout while waiting for elements')
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'(by={by.value}, value={value!r})'
                    )
                return None

            await interval.wait()

    async def _find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        timeout: int,
        find_all: bool,
        raise_exc: bool,
    ) -> T_Element | list[T_Element] | None:
        """
        Retry loop for iframe-crossing element searches.

        Repeatedly calls :meth:`_attempt_find_across_iframes` until the target
        element is found or the *timeout* expires.

        Args:
            segments: Ordered ``(By, selector)`` pairs, one per iframe boundary
                plus a final selector for the target element(s).
            timeout: Maximum seconds to wait (0 = single attempt).
            find_all: If ``True``, the last segment uses ``_find_elements``.
            raise_exc: Whether to raise on failure.

        Returns:
            The found element(s), or ``None`` / ``[]`` on failure.

        Raises:
            ElementNotFound: If ``timeout=0``, nothing found, and ``raise_exc=True``.
            WaitElementTimeout: If timeout expires and ``raise_exc=True``.
        """
        start_time = asyncio.get_running_loop().time()
        selector_repr = ' -> '.join(seg for _, seg in segments)
        interval = PollInterval()

        while True:
            result = await self._attempt_find_across_iframes(segments, find_all)
            if result is not None and result != []:
                return result

            if not timeout:
                if raise_exc:
                    raise ElementNotFound(f'Element not found across iframes: {selector_repr}')
                return [] if find_all else None

            if asyncio.get_running_loop().time() - start_time > timeout:
                if raise_exc:
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'across iframes: {selector_repr}'
                    )
                return [] if find_all else None

            await interval.wait()

    async def _attempt_find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        find_all: bool,
    ) -> T_Element | list[T_Element] | None:
        """
        Single attempt to walk iframe segments and find the target element.

        For each intermediate segment, finds a single iframe element and uses it
        as the search context for the next segment. The last segment respects
        *find_all*.

        Args:
            segments: Ordered ``(By, selector)`` pairs.
            find_all: Whether the final segment should return all matches.

        Returns:
            Found element(s) or ``None`` / ``[]`` if any intermediate step fails.
        """
        current_context: FindElementsMixin[T_Element] = self
        for i, (by, selector) in enumerate(segments):
            is_last = i == len(segments) - 1
            if is_last:
                if find_all:
                    result = await current_context._find_elements(by, selector, raise_exc=False)
                    return result if result else []
                return await current_context._find_element(by, selector, raise_exc=False)

            element = await current_context._find_element(by, selector, raise_exc=False)
            if not element or not getattr(element, 'is_iframe', False):
                return None
            current_context = cast('FindElementsMixin[T_Element]', element)
        return None

    def _get_by_and_value(
        self,
        by_map: dict[str, By],
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        **attributes,
    ) -> tuple[By, str]:
        """
        Determine appropriate selector strategy and value from provided arguments.

        For single attribute: uses direct selector strategy.
        For multiple attributes: builds XPath expression.
        """
        logger.debug(
            '_get_by_and_value(): id=%s, class_name=%s, name=%s, tag_name=%s, text=%s, attrs=%s',
            id,
            class_name,
            name,
            tag_name,
            text,
            attributes,
        )
        xpath_raw = attributes.get('xpath')
        if isinstance(xpath_raw, str) and xpath_raw:
            logger.debug('Explicit XPath provided; using raw expression: %s', xpath_raw)
            return By.XPATH, xpath_raw

        simple_selectors = {
            'id': id,
            'class_name': class_name,
            'name': name,
            'tag_name': tag_name,
        }
        provided_selectors = {key: value for key, value in simple_selectors.items() if value}

        if len(provided_selectors) == 1 and not text and not attributes:
            key, value = next(iter(provided_selectors.items()))
            by = by_map[key]
            logger.debug('Simple selector resolved: by=%s, value=%s', by, value)
            return by, value

        xpath = self._build_xpath(id, class_name, name, tag_name, text, **attributes)
        logger.debug('Complex selector resolved to XPath: %s', xpath)
        return By.XPATH, xpath

    @staticmethod
    def _build_xpath(
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        **attributes: str,
    ) -> str:
        """
        Build XPath expression from multiple attribute criteria.

        Constructs complex XPath combining multiple conditions with 'and' operators.
        Handles class names correctly for space-separated class lists.
        Uses contains() for text matching (partial text support).

        Note:
            Attribute names with underscores are automatically converted to hyphens
            to match HTML attribute naming conventions (e.g., data_test -> data-test).
        """
        return SelectorParser.build_xpath(id, class_name, name, tag_name, text, **attributes)

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """
        Auto-detect selector type from expression syntax.

        Patterns:
        - XPath: starts with ./, or /
        - Default: CSS_SELECTOR
        """
        return SelectorParser.get_expression_type(expression)

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """
        Ensure XPath is relative by prepending dot if needed.

        Converts absolute XPath to relative for context-based searches.
        """
        return SelectorParser.ensure_relative_xpath(xpath)
