import asyncio
import re
from typing import TYPE_CHECKING, Optional, TypeVar, Union

from pydoll.commands import (
    DomCommands,
    RuntimeCommands,
)
from pydoll.constants import By, Scripts
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.protocol.base import Command
from pydoll.protocol.dom.responses import DescribeNodeResponse
from pydoll.protocol.dom.types import Node
from pydoll.protocol.runtime.responses import (
    CallFunctionOnResponse,
    EvaluateResponse,
    GetPropertiesResponse,
)

if TYPE_CHECKING:
    from pydoll.elements.web_element import WebElement

T = TypeVar('T')


def create_web_element(*args, **kwargs):
    """
    Create WebElement instance avoiding circular imports.

    Factory method that dynamically imports WebElement at runtime
    to prevent circular import dependencies.
    """
    from pydoll.elements.web_element import WebElement  # noqa: PLC0415

    return WebElement(*args, **kwargs)


class FindElementsMixin:
    """
    Mixin providing comprehensive element finding and waiting capabilities.

    Implements DOM element location using various selector strategies (CSS, XPath, etc.)
    with support for single/multiple element finding and configurable waiting.
    Classes using this mixin gain powerful element discovery without implementing
    complex location logic themselves.
    """

    async def find(  # noqa: PLR0913, PLR0917
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
    ) -> Union['WebElement', list['WebElement'], None]:
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
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ValueError: If no search criteria provided.
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
        """
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
        return await self.find_or_wait_element(
            by, value, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    async def query(
        self, expression: str, timeout: int = 0, find_all: bool = False, raise_exc: bool = True
    ) -> Union['WebElement', list['WebElement'], None]:
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
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
            WaitElementTimeout: If timeout specified and no elements appear in time.
        """
        by = self._get_expression_type(expression)
        return await self.find_or_wait_element(
            by=by, value=expression, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    async def find_or_wait_element(
        self,
        by: By,
        value: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> Union['WebElement', list['WebElement'], None]:
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
            WebElement, list[WebElement], or None based on find_all and raise_exc.

        Raises:
            ElementNotFound: If no elements found with timeout=0 and raise_exc=True.
            WaitElementTimeout: If elements not found within timeout and raise_exc=True.
        """
        find_method = self._find_element if not find_all else self._find_elements
        start_time = asyncio.get_event_loop().time()

        if not timeout:
            return await find_method(by, value, raise_exc=raise_exc)

        while True:
            element = await find_method(by, value, raise_exc=False)
            if element:
                return element

            if asyncio.get_event_loop().time() - start_time > timeout:
                if raise_exc:
                    raise WaitElementTimeout()
                return None

            await asyncio.sleep(0.5)

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional['WebElement']:
        """
        Find first element matching selector.

        Internal method performing actual element search. Can be called directly
        for fine-grained control. Searches in document context or relative to
        current element (when used from WebElement).

        Args:
            by: Selector strategy (CSS_SELECTOR, XPATH, ID, etc.).
            value: Selector value to locate element.
            raise_exc: Whether to raise ElementNotFound if not found.

        Returns:
            WebElement instance or None if not found and raise_exc=False.

        Raises:
            ElementNotFound: If element not found and raise_exc=True.
        """
        if hasattr(self, '_object_id'):
            command = self._get_find_element_command(by, value, self._object_id)
        else:
            command = self._get_find_element_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not response_for_command.get('result', {}).get('result', {}).get('objectId'):
            if raise_exc:
                raise ElementNotFound()
            return None

        object_id = response_for_command['result']['result']['objectId']
        node_description = await self._describe_node(object_id=object_id)
        attributes = node_description.get('attributes', [])

        tag_name = node_description.get('nodeName', '').lower()
        attributes.extend(['tag_name', tag_name])

        return create_web_element(object_id, self._connection_handler, by, value, attributes)  # type: ignore

    async def _find_elements(
        self, by: By, value: str, raise_exc: bool = True
    ) -> list['WebElement']:
        """
        Find all elements matching selector.

        Internal method performing actual multi-element search. Can be called directly
        for fine-grained control. Searches in document context or relative to
        current element (when used from WebElement).

        Args:
            by: Selector strategy (CSS_SELECTOR, XPATH, ID, etc.).
            value: Selector value to locate elements.
            raise_exc: Whether to raise ElementNotFound if none found.

        Returns:
            list of WebElement instances (empty if none found and raise_exc=False).

        Raises:
            ElementNotFound: If no elements found and raise_exc=True.
        """
        if hasattr(self, '_object_id'):
            command = self._get_find_elements_command(by, value, self._object_id)
        else:
            command = self._get_find_elements_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not response_for_command.get('result', {}).get('result', {}).get('objectId'):
            if raise_exc:
                raise ElementNotFound()
            return []

        object_id = response_for_command['result']['result']['objectId']
        query_response: GetPropertiesResponse = await self._execute_command(
            RuntimeCommands.get_properties(object_id=object_id)
        )
        response = []
        for query in query_response['result']['result']:
            query_value = query.get('value', {})
            if query_value and query_value['type'] == 'object':
                response.append(query_value['objectId'])

        elements = []
        for object_id in response:
            try:
                node_description = await self._describe_node(object_id=object_id)
            except KeyError:
                continue

            attributes = node_description.get('attributes', [])
            tag_name = node_description.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            elements.append(
                create_web_element(object_id, self._connection_handler, by, value, attributes)  # type: ignore
            )
        return elements

    def _get_by_and_value(  # noqa: PLR0913, PLR0917
        self,
        by_map: dict[str, By],
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes,
    ) -> tuple[By, str]:
        """
        Determine appropriate selector strategy and value from provided arguments.

        For single attribute: uses direct selector strategy.
        For multiple attributes: builds XPath expression.
        """
        simple_selectors = {
            'id': id,
            'class_name': class_name,
            'name': name,
            'tag_name': tag_name,
        }
        provided_selectors = {key: value for key, value in simple_selectors.items() if value}

        if len(provided_selectors) == 1 and not text:
            key, value = next(iter(provided_selectors.items()))
            by = by_map[key]
            return by, value

        xpath = self._build_xpath(id, class_name, name, tag_name, text, **attributes)
        return By.XPATH, xpath

    @staticmethod
    def _build_xpath(
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes,
    ) -> str:
        """
        Build XPath expression from multiple attribute criteria.

        Constructs complex XPath combining multiple conditions with 'and' operators.
        Handles class names correctly for space-separated class lists.
        Uses contains() for text matching (partial text support).
        """
        xpath_conditions = []
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
            xpath_conditions.append(f'@{attribute}="{value}"')

        return f'{base_xpath}[{" and ".join(xpath_conditions)}]' if xpath_conditions else base_xpath

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """
        Auto-detect selector type from expression syntax.

        Patterns:
        - XPath: starts with //, .// , ./, or /
        - ID: starts with #
        - Class: starts with . (but not ./)
        - Default: CSS_SELECTOR
        """
        xpath_pattern = r'^(//|\.//|\.\/|/)'
        if re.match(xpath_pattern, expression):
            return By.XPATH
        if expression.startswith('#'):
            return By.ID
        if expression.startswith('.') and not expression.startswith('./'):
            return By.CLASS_NAME

        return By.CSS_SELECTOR

    async def _describe_node(self, object_id: str = '') -> Node:
        """
        Get detailed DOM node information using CDP DOM.describeNode.

        Used internally to gather data for WebElement initialization.
        """
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=object_id)
        )
        return response['result']['node']

    async def _execute_command(self, command: Command[T]) -> T:
        """Execute CDP command via connection handler (60s timeout)."""
        return await self._connection_handler.execute_command(command, timeout=60)  # type: ignore

    def _get_find_element_command(self, by: By, value: str, object_id: str = ''):
        """
        Create CDP command for finding single element.

        Handles special cases for different selector types and contexts:
        - CLASS_NAME/ID: converts to CSS selector
        - Relative searches: uses different scripts for context element
        - XPath: requires special handling
        - NAME: converts to XPath expression
        """
        escaped_value = value.replace('"', '\\"')
        match by:
            case By.CLASS_NAME:
                selector = f'.{escaped_value}'
            case By.ID:
                selector = f'#{escaped_value}'
            case _:
                selector = escaped_value
        if object_id and not by == By.XPATH:
            script = Scripts.RELATIVE_QUERY_SELECTOR.replace('{selector}', selector)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        elif by == By.XPATH:
            command = self._get_find_element_by_xpath_command(value, object_id)
        elif by == By.NAME:
            command = self._get_find_element_by_xpath_command(
                f'//*[@name="{escaped_value}"]', object_id
            )
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR.replace('{selector}', selector)
            )
        return command

    def _get_find_elements_command(self, by: By, value: str, object_id: str = ''):
        """
        Create CDP command for finding multiple elements.

        Similar to _get_find_element_command but for multiple element searches.
        Handles same special cases and selector type conversions.
        """
        escaped_value = value.replace('"', '\\"')
        match by:
            case By.CLASS_NAME:
                selector = f'.{escaped_value}'
            case By.ID:
                selector = f'#{escaped_value}'
            case _:
                selector = escaped_value
        if object_id and not by == By.XPATH:
            script = Scripts.RELATIVE_QUERY_SELECTOR_ALL.replace('{selector}', escaped_value)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        elif by == By.XPATH:
            command = self._get_find_elements_by_xpath_command(value, object_id)
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR_ALL.replace('{selector}', selector)
            )
        return command

    def _get_find_element_by_xpath_command(self, xpath: str, object_id: str):
        """
        Create CDP command specifically for XPath single element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        escaped_value = xpath.replace('"', '\\"')
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script)
        return command

    def _get_find_elements_by_xpath_command(self, xpath: str, object_id: str):
        """
        Create CDP command specifically for XPath multiple element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        escaped_value = xpath.replace('"', '\\"')
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script)
        return command

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """
        Ensure XPath is relative by prepending dot if needed.

        Converts absolute XPath to relative for context-based searches.
        """
        return f'.{xpath}' if not xpath.startswith('.') else xpath
