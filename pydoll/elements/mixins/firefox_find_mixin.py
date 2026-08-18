from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional, Union

from pydoll.constants import By
from pydoll.elements.utils import SelectorParser
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.protocol.bidi import browsing_context

if TYPE_CHECKING:
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
    from pydoll.elements.firefox_element import FirefoxElement

logger = logging.getLogger(__name__)


def create_firefox_element(*args, **kwargs) -> FirefoxElement:
    """
    Create FirefoxElement instance avoiding circular imports.

    Factory function that dynamically imports FirefoxElement at runtime
    to prevent circular import dependencies.
    """
    from pydoll.elements.firefox_element import FirefoxElement  # noqa: PLC0415

    return FirefoxElement(*args, **kwargs)


class FirefoxFindMixin:
    """
    Mixin providing Chrome-like element finding via BiDi browsingContext.locateNodes.

    Host classes must expose:
      - ``_context_id: str``
      - ``_connection_handler: BiDiConnectionHandler``

    Optionally override ``_find_start_nodes`` to scope the search inside a
    specific node (element or shadow root).
    """

    if TYPE_CHECKING:
        _context_id: str
        _connection_handler: BiDiConnectionHandler

    @property
    def _find_start_nodes(self) -> Optional[list[dict]]:
        """Node references passed as ``startNodes`` to ``locateNodes``. ``None`` = full document."""
        return None

    async def find(
        self,
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        accessibility_name: Optional[str] = None,
        accessibility_role: Optional[str] = None,
        timeout: float = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        **attributes: str,
    ) -> Union[FirefoxElement, list[FirefoxElement], None]:
        """
        Find element(s) using keyword criteria, mirroring the Chrome Tab API.

        Locator selection priority:
        - ``accessibility_name`` / ``accessibility_role`` → BiDi ``AccessibilityLocator``
        - ``text`` alone (no other structural criteria) → BiDi ``InnerTextLocator``
        - everything else → CSS selector (or XPath when ``text`` is combined with
          structural criteria such as ``tag_name``, ``id``, etc.)

        Args:
            id: Element ``id`` attribute.
            class_name: CSS class name.
            name: Element ``name`` attribute.
            tag_name: HTML tag name (e.g. ``'button'``).
            text: Partial inner-text to match.
            accessibility_name: Accessible name (ARIA label / visible text).
            accessibility_role: ARIA role (e.g. ``'button'``, ``'link'``).
            timeout: Seconds to wait for the element to appear (0 = one attempt).
            find_all: Return all matches when ``True``; first match only when ``False``.
            raise_exc: Raise ``ElementNotFound`` / ``WaitElementTimeout`` on failure.
            **attributes: Extra HTML attributes; underscores are converted to hyphens.

        Returns:
            ``FirefoxElement``, ``list[FirefoxElement]``, or ``None``.

        Raises:
            ValueError: If no search criteria are provided.
            ElementNotFound: If element not found and ``raise_exc=True`` with no timeout.
            WaitElementTimeout: If element not found within ``timeout`` and ``raise_exc=True``.
        """
        if not any([
            id, class_name, name, tag_name, text,
            accessibility_name, accessibility_role,
            *attributes.keys(),
        ]):
            raise ValueError(
                'At least one of id, class_name, name, tag_name, text, '
                'accessibility_name, accessibility_role, '
                'or an extra attribute must be provided.'
            )
        locator = self._build_locator(
            id, class_name, name, tag_name, text,
            accessibility_name, accessibility_role,
            **attributes,
        )
        return await self._locate(locator, timeout, find_all, raise_exc)

    async def query(
        self,
        selector: str,
        timeout: float = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        max_node_count: Optional[int] = None,
    ) -> Union[FirefoxElement, list[FirefoxElement], None]:
        """
        Find element(s) using a raw CSS selector or XPath expression.

        Selector type is auto-detected: XPath if the expression starts with
        ``/``, ``./``, or ``//``; CSS otherwise.

        Args:
            selector: CSS selector or XPath expression.
            timeout: Seconds to wait (0 = one attempt).
            find_all: Return all matches when ``True``.
            raise_exc: Raise on failure when ``True``.

        Returns:
            ``FirefoxElement``, ``list[FirefoxElement]``, or ``None``.
        """
        if SelectorParser.get_expression_type(selector) == By.XPATH:
            locator = {'type': 'xpath', 'value': selector}
        else:
            locator = {'type': 'css', 'value': selector}
        return await self._locate(locator, timeout, find_all, raise_exc, max_node_count)

    @staticmethod
    def _build_locator(
        id: Optional[str],
        class_name: Optional[str],
        name: Optional[str],
        tag_name: Optional[str],
        text: Optional[str],
        accessibility_name: Optional[str] = None,
        accessibility_role: Optional[str] = None,
        **attributes: str,
    ) -> dict:
        """
        Build a BiDi locator dict from keyword criteria.

        Priority:
        1. Accessibility criteria → ``AccessibilityLocator``
        2. Text only (no structural criteria) → ``InnerTextLocator``
        3. Text + structural criteria → XPath (CSS cannot match text content)
        4. Structural criteria only → CSS selector

        CSS selector shape: ``{tag}{#id}{.class}{[name="…"]}{[attr="…"]…}``

        Examples::

            tag_name="a", class_name="link"         →  CSS  ``a.link``
            tag_name="input", name="email"           →  CSS  ``input[name="email"]``
            text="Sign in"                           →  InnerTextLocator (BiDi native)
            accessibility_role="button"              →  AccessibilityLocator (BiDi native)
            tag_name="span", text="hello"            →  XPath (combined)
        """
        # 1. Accessibility locator (BiDi native)
        if accessibility_name or accessibility_role:
            value: dict = {}
            if accessibility_name:
                value['name'] = accessibility_name
            if accessibility_role:
                value['role'] = accessibility_role
            return {'type': 'accessibility', 'value': value}

        structural_criteria = any([id, class_name, name, tag_name, *attributes.keys()])

        # 2. Text-only → InnerTextLocator (BiDi native, more accurate than XPath)
        if text and not structural_criteria:
            return {
                'type': 'innerText',
                'value': text,
                'matchType': 'partial',
                'ignoreCase': False,
            }

        # 3. Text + structural criteria → XPath (CSS cannot filter by text)
        if text and structural_criteria:
            xpath = SelectorParser.build_xpath(id, class_name, name, tag_name, text, **attributes)
            return {'type': 'xpath', 'value': xpath}

        # 4. Structural criteria only → CSS
        parts: list[str] = []
        if tag_name:
            parts.append(tag_name)
        if id:
            parts.append(f'#{id}')
        if class_name:
            parts.append(f'.{class_name}')
        if name:
            parts.append(f'[name="{name}"]')
        for attr, attr_value in attributes.items():
            html_attr = attr.replace('_', '-')
            parts.append(f'[{html_attr}="{attr_value}"]')

        return {'type': 'css', 'value': ''.join(parts)}

    async def _locate(
        self,
        locator: dict,
        timeout: float,
        find_all: bool,
        raise_exc: bool,
        max_node_count: Optional[int] = None,
    ) -> Union[FirefoxElement, list[FirefoxElement], None]:
        """Execute ``locateNodes`` with optional retry, return ``FirefoxElement(s)``."""
        start_nodes = self._find_start_nodes
        deadline = asyncio.get_event_loop().time() + timeout if timeout else None

        while True:
            response: dict = await self._connection_handler.execute_command(
                browsing_context.locate_nodes(
                    self._context_id,
                    locator,
                    max_node_count=max_node_count,
                    start_nodes=start_nodes,
                )
            )
            nodes = response.get('result', {}).get('nodes', [])

            if nodes:
                elements = [
                    create_firefox_element(node, self._context_id, self._connection_handler)
                    for node in nodes
                ]
                return elements if find_all else elements[0]

            # Nothing found — decide whether to retry, fail, or return None
            if deadline is None:
                if raise_exc:
                    raise ElementNotFound(f'Element not found: {locator}')
                return [] if find_all else None

            if asyncio.get_event_loop().time() >= deadline:
                if raise_exc:
                    raise WaitElementTimeout(f'Timed out waiting for element: {locator}')
                return [] if find_all else None

            await asyncio.sleep(0.5)
