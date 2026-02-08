from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional, Union, cast, overload

from pydoll.commands import (
    DomCommands,
    RuntimeCommands,
)
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import By, Scripts
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.utils import normalize_synthetic_xpath

if TYPE_CHECKING:
    from typing import Literal, Optional, Union

    from pydoll.elements.web_element import WebElement
    from pydoll.interactions.iframe import IFrameContext
    from pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse
    from pydoll.protocol.dom.methods import DescribeNodeResponse
    from pydoll.protocol.dom.types import Node
    from pydoll.protocol.runtime.methods import (
        CallFunctionOnParams,
        CallFunctionOnResponse,
        EvaluateParams,
        EvaluateResponse,
        GetPropertiesResponse,
    )


logger = logging.getLogger(__name__)


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

    _css_only: bool = False

    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler

    @staticmethod
    def _build_text_expression(selector: str, method: str) -> Optional[str]:
        """
        Build JS expression using Scripts to extract textContent based on selector type.
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
    ) -> WebElement: ...

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
    ) -> Optional[WebElement]: ...

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
    ) -> list[WebElement]: ...

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
    ) -> Optional[list[WebElement]]: ...

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
    ) -> Union[WebElement, list[WebElement], None]: ...

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
    ) -> Union[WebElement, list[WebElement], None]:
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
        return await self.find_or_wait_element(
            by, value, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
    ) -> WebElement: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
    ) -> Optional[WebElement]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
    ) -> list[WebElement]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
    ) -> Optional[list[WebElement]]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
    ) -> Union[WebElement, list[WebElement], None]: ...

    async def query(
        self, expression: str, timeout: int = 0, find_all: bool = False, raise_exc: bool = True
    ) -> Union[WebElement, list[WebElement], None]:
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
    ) -> Union[WebElement, list[WebElement], None]:
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
        logger.debug(
            f'find_or_wait_element(): by={by}, value={value}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}'
        )
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

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional[WebElement]:
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
        logger.debug(f'_find_element(): by={by}, value={value}, raise_exc={raise_exc}')
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context

        if iframe_context:
            command = self._get_find_element_command(
                by,
                value,
                object_id=iframe_context.document_object_id or '',
                execution_context_id=iframe_context.execution_context_id,
            )
        elif hasattr(self, '_object_id'):
            command = self._get_find_element_command(by, value, self._object_id)
        else:
            command = self._get_find_element_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not self._has_object_id_key(response_for_command):
            if raise_exc:
                logger.debug('Element not found and raise_exc=True')
                raise ElementNotFound()
            return None

        object_id = response_for_command['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
        logger.debug(f'_find_element() found object_id={object_id}')
        element = create_web_element(object_id, self._connection_handler, by, value, attributes)
        self._apply_iframe_context_to_element(
            element, iframe_context or getattr(self, '_iframe_context', None)
        )
        return element

    async def _find_elements(self, by: By, value: str, raise_exc: bool = True) -> list[WebElement]:
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
        logger.debug(f'_find_elements(): by={by}, value={value}, raise_exc={raise_exc}')
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context

        if iframe_context:
            command = self._get_find_elements_command(
                by,
                value,
                object_id=iframe_context.document_object_id or '',
                execution_context_id=iframe_context.execution_context_id,
            )
        elif hasattr(self, '_object_id'):
            command = self._get_find_elements_command(by, value, self._object_id)
        else:
            command = self._get_find_elements_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not response_for_command.get('result', {}).get('result', {}).get('objectId'):
            if raise_exc:
                logger.debug('No elements found and raise_exc=True')
                raise ElementNotFound()
            return []

        object_id = response_for_command['result']['result']['objectId']
        query_response: GetPropertiesResponse = await self._execute_command(
            RuntimeCommands.get_properties(object_id=object_id)
        )
        response: list[str] = []
        for query in query_response['result']['result']:
            if not (query['name'].isdigit() and 'objectId' in query['value']):
                continue
            response.append(query['value']['objectId'])

        inherited_context = iframe_context or getattr(self, '_iframe_context', None)
        elements = []
        for object_id in response:
            try:
                node_description = await self._describe_node(object_id=object_id)
            except KeyError:
                continue

            attributes = node_description.get('attributes', [])
            tag_name = node_description.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            child = create_web_element(object_id, self._connection_handler, by, value, attributes)
            self._apply_iframe_context_to_element(child, inherited_context)
            elements.append(child)
        logger.debug(f'_find_elements() returning {len(elements)} elements')
        return elements

    async def _get_object_attributes(self, object_id: str) -> list[str]:
        """
        Get attributes of a DOM node.
        """
        node_description = await self._describe_node(object_id=object_id)
        if not node_description:
            # If the node couldn't be described (e.g., object id doesn't reference a Node),
            # return minimal attributes to keep the flow stable.
            return ['tag_name', '']
        attributes = node_description.get('attributes', [])
        tag_name = node_description.get('nodeName', '').lower()
        attributes.extend(['tag_name', tag_name])
        return attributes

    def _get_by_and_value(
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
        logger.debug(
            f'_get_by_and_value(): id={id}, class_name={class_name}, name={name}, '
            f'tag_name={tag_name}, text={text}, attrs={attributes}'
        )
        xpath_raw = attributes.get('xpath')
        if isinstance(xpath_raw, str) and xpath_raw:
            logger.debug(f'Explicit XPath provided; using raw expression: {xpath_raw}')
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
            logger.debug(f'Simple selector resolved: by={by}, value={value}')
            return by, value

        xpath = self._build_xpath(id, class_name, name, tag_name, text, **attributes)
        logger.debug(f'Complex selector resolved to XPath: {xpath}')
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

        Note:
            Attribute names with underscores are automatically converted to hyphens
            to match HTML attribute naming conventions (e.g., data_test -> data-test).
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
            # Convert underscores to hyphens for HTML attribute names
            html_attribute = attribute.replace('_', '-')
            xpath_conditions.append(f'@{html_attribute}="{value}"')

        xpath = (
            f'{base_xpath}[{" and ".join(xpath_conditions)}]' if xpath_conditions else base_xpath
        )
        logger.debug(f'_build_xpath() -> {xpath}')
        return xpath

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """
        Auto-detect selector type from expression syntax.

        Patterns:
        - XPath: starts with ./, or /
        - Default: CSS_SELECTOR
        """
        if expression.startswith(('./', '/', '(/')):
            return By.XPATH

        return By.CSS_SELECTOR

    async def _describe_node(self, object_id: str = '') -> Node:
        """
        Get detailed DOM node information using CDP DOM.describeNode.

        Used internally to gather data for WebElement initialization.
        """
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=object_id)
        )
        if 'error' in response:
            # Return empty node structure when CDP reports that the objectId
            # doesn't reference a Node or any other describe error occurs.
            return {}
        return response.get('result', {}).get('node', {})

    def _apply_iframe_context_to_element(
        self, element: WebElement, iframe_context: IFrameContext | None
    ) -> None:
        """
        Propagate iframe context to the newly created element.
        - If the element is also an iframe, configure session routing.
        - Otherwise, inject the iframe's own context.
        """
        if not iframe_context:
            return
        if getattr(element, 'is_iframe', False):
            routing_handler = iframe_context.session_handler or self._connection_handler
            element._routing_session_handler = routing_handler
            element._routing_session_id = iframe_context.session_id
            element._routing_parent_frame_id = iframe_context.frame_id
            return
        element._iframe_context = iframe_context

    def _resolve_routing(self) -> tuple[ConnectionHandler, Optional[str]]:
        """
        Resolve handler and sessionId for the current context (iframe routed or default).
        """
        iframe_context = getattr(self, '_iframe_context', None)
        if iframe_context and getattr(iframe_context, 'session_handler', None):
            return iframe_context.session_handler, getattr(iframe_context, 'session_id', None)
        routing_handler = getattr(self, '_routing_session_handler', None)
        if routing_handler is not None:
            return routing_handler, getattr(self, '_routing_session_id', None)
        return self._connection_handler, None

    async def _execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse]
    ) -> T_CommandResponse:
        """Execute CDP command via resolved handler (10s timeout)."""
        handler, session_id = self._resolve_routing()
        if session_id:
            command['sessionId'] = session_id
        return await handler.execute_command(command, timeout=10)

    def _get_find_element_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: Optional[int] = None,
    ):
        """
        Create CDP command for finding single element.

        Handles special cases for different selector types and contexts:
        - CLASS_NAME/ID: converts to CSS selector
        - Relative searches: uses different scripts for context element
        - XPath: requires special handling
        - NAME: converts to XPath expression
        """
        escaped_value = value.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
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
            command = self._get_find_element_by_xpath_command(
                value, object_id=object_id, execution_context_id=execution_context_id
            )
        elif by == By.NAME:
            command = self._get_find_element_by_xpath_command(
                f'//*[@name="{escaped_value}"]',
                object_id=object_id,
                execution_context_id=execution_context_id,
            )
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR.replace('{selector}', selector),
                context_id=execution_context_id,
            )
        return command

    def _get_find_elements_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: Optional[int] = None,
    ):
        """
        Create CDP command for finding multiple elements.

        Similar to _get_find_element_command but for multiple element searches.
        Handles same special cases and selector type conversions.
        """
        escaped_value = value.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
        match by:
            case By.CLASS_NAME:
                selector = f'.{escaped_value}'
            case By.ID:
                selector = f'#{escaped_value}'
            case _:
                selector = escaped_value
        if object_id and not by == By.XPATH:
            script = Scripts.RELATIVE_QUERY_SELECTOR_ALL.replace('{selector}', selector)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        elif by == By.XPATH:
            command = self._get_find_elements_by_xpath_command(
                value, object_id=object_id, execution_context_id=execution_context_id
            )
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR_ALL.replace('{selector}', selector),
                context_id=execution_context_id,
            )
        return command

    def _get_find_element_by_xpath_command(
        self,
        xpath: str,
        object_id: str,
        execution_context_id: Optional[int] = None,
    ):
        """
        Create CDP command specifically for XPath single element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
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
            command = RuntimeCommands.evaluate(expression=script, context_id=execution_context_id)
        return command

    def _get_find_elements_by_xpath_command(
        self,
        xpath: str,
        object_id: str,
        execution_context_id: Optional[int] = None,
    ):
        """
        Create CDP command specifically for XPath multiple element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        escaped_value = xpath.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
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
            command = RuntimeCommands.evaluate(expression=script, context_id=execution_context_id)
        return command

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """
        Ensure XPath is relative by prepending dot if needed.

        Converts absolute XPath to relative for context-based searches.
        """
        return f'.{xpath}' if not xpath.startswith('.') else xpath

    @staticmethod
    def _has_object_id_key(response: Union[EvaluateResponse, CallFunctionOnResponse]) -> bool:
        """
        Check if response has objectId key.
        """
        return bool(response.get('result', {}).get('result', {}).get('objectId'))
