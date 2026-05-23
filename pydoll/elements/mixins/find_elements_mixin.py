from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union, overload

from pydoll.constants import By
from pydoll.elements.utils import SelectorParser
from pydoll.exceptions import ElementNotFound, WaitElementTimeout

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
    """

    _css_only: bool = False

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional[T_Element]:
        """Locate the first matching element. Implemented per protocol (CDP/BiDi)."""
        raise NotImplementedError

    async def _find_elements(
        self, by: By, value: str, raise_exc: bool = True
    ) -> list[T_Element]:
        """Locate all matching elements. Implemented per protocol (CDP/BiDi)."""
        raise NotImplementedError

    @staticmethod
    def _build_text_expression(selector: str, method: str) -> Optional[str]:
        """Build JS expression for text extraction based on selector type."""
        return SelectorParser.build_text_expression(selector, method)

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> T_Element: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> Optional[T_Element]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> list[T_Element]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> Optional[list[T_Element]]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
        **attributes,
    ) -> Union[T_Element, list[T_Element], None]: ...

    async def find(
        self,
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        **attributes: dict[str, str],
    ) -> Union[T_Element, list[T_Element], None]:
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
            f'find() called with id={id}, class_name={class_name}, name={name}, '
            f'tag_name={tag_name}, text={text}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}, attrs={attributes}'
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
        logger.debug(f'find() resolved to by={by} value={value}')
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
    ) -> Optional[T_Element]: ...

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
    ) -> Optional[list[T_Element]]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
    ) -> Union[T_Element, list[T_Element], None]: ...

    async def query(
        self, expression: str, timeout: int = 0, find_all: bool = False, raise_exc: bool = True
    ) -> Union[T_Element, list[T_Element], None]:
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
            f'query() called with expression={expression}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}'
        )
        by = self._get_expression_type(expression)
        logger.debug(f'query() resolved to by={by}')
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
    ) -> Union[T_Element, list[T_Element], None]:
        """
        Core element finding method with optional waiting capability.

        Searches for elements with flexible waiting. If timeout specified,
        repeatedly attempts to find elements with 0.5s delays until success or timeout.
        Used by higher-level find() and query() methods.

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
            f'_find_or_wait_element(): by={by}, value={value}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}'
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
        start_time = asyncio.get_event_loop().time()

        if not timeout:
            logger.debug('No timeout specified; performing single attempt')
            return await find_method(by, value, raise_exc=raise_exc)

        while True:
            element = await find_method(by, value, raise_exc=False)
            if element:
                if isinstance(element, list):
                    logger.debug(f'Found {len(element)} elements within timeout window')
                else:
                    logger.debug('Found 1 element within timeout window')
                return element

            if asyncio.get_event_loop().time() - start_time > timeout:
                if raise_exc:
                    logger.error('Timeout while waiting for elements')
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'(by={by.value}, value={value!r})'
                    )
                return None

            await asyncio.sleep(0.5)

    async def _find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        timeout: int,
        find_all: bool,
        raise_exc: bool,
    ) -> Union[T_Element, list[T_Element], None]:
        """
        Retry loop for iframe-crossing element searches.

        Repeatedly calls :meth:`_attempt_find_across_iframes` until the target
        element is found or the *timeout* expires.

        Args:
            segments: Ordered ``(By, selector)`` pairs — one per iframe boundary
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
        start_time = asyncio.get_event_loop().time()
        selector_repr = ' -> '.join(seg for _, seg in segments)

        while True:
            result = await self._attempt_find_across_iframes(segments, find_all)
            if result is not None and result != []:
                return result

            if not timeout:
                if raise_exc:
                    raise ElementNotFound(f'Element not found across iframes: {selector_repr}')
                return [] if find_all else None

            if asyncio.get_event_loop().time() - start_time > timeout:
                if raise_exc:
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'across iframes: {selector_repr}'
                    )
                return [] if find_all else None

            await asyncio.sleep(0.5)

    async def _attempt_find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        find_all: bool,
    ) -> Union[T_Element, list[T_Element], None]:
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
        current_context: FindElementsMixin = self
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
            current_context = element
        return None

    @staticmethod
    def _get_by_and_value(
        by_map: dict[str, By],
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes,
    ) -> tuple[By, str]:
        """Determine selector strategy and value from provided arguments."""
        xpath_raw = attributes.get('xpath')
        if isinstance(xpath_raw, str) and xpath_raw:
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
            return by, value

        xpath = SelectorParser.build_xpath(id, class_name, name, tag_name, text, **attributes)
        return By.XPATH, xpath

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """Auto-detect selector type (CSS vs XPath) from expression syntax."""
        return SelectorParser.get_expression_type(expression)

    @staticmethod
    def _build_xpath(
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes: str,
    ) -> str:
        """Build XPath expression from multiple attribute criteria."""
        return SelectorParser.build_xpath(id, class_name, name, tag_name, text, **attributes)

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """Ensure XPath is relative by prepending dot if needed."""
        return SelectorParser.ensure_relative_xpath(xpath)
