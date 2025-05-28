import asyncio
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, TypeVar, Union

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
    Creates a WebElement instance while avoiding circular imports.

    This function serves as a factory method to instantiate WebElement objects
    by dynamically importing the WebElement class at runtime. This approach
    prevents circular import dependencies between modules.

    Args:
        *args: Positional arguments to pass to the WebElement constructor.
        **kwargs: Keyword arguments to pass to the WebElement constructor.

    Returns:
        WebElement: A new instance of the WebElement class.
    """
    from pydoll.elements.web_element import WebElement  # noqa: PLC0415

    return WebElement(*args, **kwargs)


class FindElementsMixin:
    """
    A mixin class that provides element finding and waiting capabilities.

    This mixin implements comprehensive DOM element location functionality using
    various selector strategies (CSS, XPath, etc.) and provides methods for
    finding single elements, multiple elements, and waiting for elements to
    appear in the DOM.

    Classes that incorporate this mixin gain powerful element discovery capabilities
    without having to implement the complex logic of element location themselves.
    The mixin handles the communication with the browser through CDP commands and
    transforms the browser's responses into WebElement instances.

    Primary functionality includes:
    1. Finding individual elements by various selectors
    2. Finding collections of elements matching a selector
    3. Waiting for elements to appear with configurable timeouts
    4. Support for relative searches within a parent element's context
    """

    async def find(  # noqa: PLR0913, PLR0917
        self,
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        raise_exc: bool = True,
        find_all: bool = False,
        timeout: int = 0,
        **attributes,
    ):
        """
        Finds element(s) using a combination of common HTML attributes.

        Provides a flexible way to locate elements using standard attributes
        like id, class, name, tag, or text content. Multiple attributes can be
        combined to create more specific selectors. Under the hood, this builds
        an XPath expression when multiple attributes are specified.

        Args:
            id: Element ID attribute value to match.
            class_name: CSS class name to match.
            name: Element name attribute value to match.
            tag_name: HTML tag name to match (e.g., "div", "input").
            text: Text content to match within the element.
            raise_exc: Whether to raise an exception if no elements are found.
                Default is True.
            find_all: If True, returns all matching elements; if False, returns
                only the first match. Default is False.
            timeout: Maximum seconds to wait for matching elements to appear.
                Default is 0 (no waiting).
            **attributes: Additional HTML attributes to match (e.g., href="example.com").

        Returns:
            WebElement or List[WebElement] or None: Found element(s) or None if
            no elements are found and raise_exc is False.

        Raises:
            ValueError: If no search criteria are provided.
            ElementNotFound: If no elements are found and raise_exc is True.
            WaitElementTimeout: If timeout is specified and no elements appear
                within that time period.
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
    ):
        """
        Finds element(s) using a raw CSS selector or XPath expression.

        Provides direct access to find elements using CSS or XPath syntax without
        having to explicitly specify the selector type. The selector type is
        automatically determined based on the expression pattern.

        Args:
            expression: The selector expression to use. Can be CSS (e.g., "div.content"),
                XPath (e.g., "//div[@class='content']"), ID (e.g., "#myId"), or
                class name (e.g., ".myClass").
            find_all: If True, returns all matching elements; if False, returns
                only the first match. Default is False.
            timeout: Maximum seconds to wait for matching elements to appear.
                Default is 0 (no waiting).
            raise_exc: Whether to raise an exception if no elements are found.
                Default is True.

        Returns:
            WebElement or List[WebElement] or None: Found element(s) or None if
            no elements are found and raise_exc is False.

        Raises:
            ElementNotFound: If no elements are found and raise_exc is True.
            WaitElementTimeout: If timeout is specified and no elements appear
                within that time period.
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
    ):
        """
        Finds element(s) and optionally waits for them to appear in the DOM.

        Searches for elements matching the provided selector with flexible waiting
        capability. If timeout is specified, repeatedly attempts to find the element(s)
        with short delays between attempts until success or timeout.

        This method forms the core of the element finding system and is used by the
        higher-level find() and query() methods.

        Args:
            by: The selector strategy to use (CSS_SELECTOR, XPATH, ID, etc.).
                Constants are available in the By enum.
            value: The selector value to locate the element(s) (e.g., "div.content").
            timeout: Maximum time in seconds to wait for the element(s) to appear.
                Default is 0 (no waiting, immediate result).
            find_all: If True, returns all matching elements as a list;
                if False, returns only the first matching element.
                Default is False.
            raise_exc: Whether to raise an exception if no elements are found.
                If False, returns None (or empty list if find_all=True) instead.
                Default is True.

        Returns:
            Union[WebElement, List[WebElement], None]:
                - When find_all=False: A WebElement instance or None if not found
                  and raise_exc=False
                - When find_all=True: A list of WebElement instances (possibly empty)
                  or None if not found and raise_exc=False

        Raises:
            ElementNotFound: If no elements are found with timeout=0 and raise_exc=True
            WaitElementTimeout: If elements aren't found within the specified timeout
                and raise_exc=True
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
        Finds the first element matching the specified selector.

        Internal method that performs the actual element search operation.
        Although primarily intended for internal use, this method can be called
        directly when fine-grained control over the element search process is needed.

        Locates a single element in the DOM using the provided selector strategy
        and value. The search is performed either in the context of the entire
        document or relative to the current element (when used from a WebElement).

        Args:
            by: The selector strategy to use (CSS_SELECTOR, XPATH, ID, etc.).
                Constants are available in the By enum.
            value: The selector value to locate the element (e.g., "div.content").
            raise_exc: Whether to raise an ElementNotFound exception if the
                element is not found. If False, returns None instead.
                Default is True.

        Returns:
            WebElement or None: A WebElement instance representing the found element,
                or None if the element is not found and raise_exc is False.

        Raises:
            ElementNotFound: If the element is not found and raise_exc is True.
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
    ) -> List['WebElement']:
        """
        Finds all elements matching the specified selector.

        Internal method that performs the actual multi-element search operation.
        Although primarily intended for internal use, this method can be called
        directly when fine-grained control over the element search process is needed.

        Locates multiple elements in the DOM using the provided selector strategy
        and value. The search is performed either in the context of the entire
        document or relative to the current element (when used from a WebElement).

        Args:
            by: The selector strategy to use (CSS_SELECTOR, XPATH, ID, etc.).
                Constants are available in the By enum.
            value: The selector value to locate the elements (e.g., "div.item").
            raise_exc: Whether to raise an ElementNotFound exception if no
                elements are found. If False, returns an empty list instead.
                Default is True.

        Returns:
            list[WebElement]: A list of WebElement instances representing all
                found elements. Returns an empty list if no elements are found
                and raise_exc is False.

        Raises:
            ElementNotFound: If no elements are found and raise_exc is True.
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
        by_map: Dict[str, By],
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes,
    ) -> Tuple[By, str]:
        """
        Determines the appropriate selector strategy and value based on the provided arguments.

        This method checks the provided arguments against the by_map dictionary
        to determine the correct selector strategy and value.

        Args:
            by_map: A dictionary mapping selector types to their corresponding By enum values.
            *args: Variable-length argument list containing selector values.

        Returns:
            tuple[By, str]: A tuple containing the appropriate selector strategy (By enum)
                and the selector value.

        Raises:
            ValueError: If no valid selector strategy is found in the by_map.
        """
        simple_selectors = {
            'id': id,
            'class_name': class_name,
            'name': name,
            'tag_name': tag_name,
            **attributes,
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
        Builds an XPath expression from multiple attribute criteria.

        Constructs a complex XPath selector that combines multiple attribute conditions
        using 'and' operators. This is used when searching by multiple attributes
        simultaneously.

        Args:
            id: Element ID attribute to match.
            class_name: CSS class name to match (handles space-separated class lists correctly).
            name: Element name attribute to match.
            tag_name: HTML tag name to match. If not provided, matches any element (*).
            text: Text content to match (using contains() for partial matching).
            **attributes: Additional HTML attributes to match with exact equality.

        Returns:
            str: A complete XPath expression that matches elements satisfying all the
                specified conditions.
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

        return f'{base_xpath}[{" and ".join(xpath_conditions)}]'

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """
        Automatically determines the selector type based on the expression syntax.

        Analyzes the provided expression to detect whether it's an XPath, CSS selector,
        ID selector, or class selector based on common syntax patterns.

        Args:
            expression: The selector expression to analyze.

        Returns:
            By: The appropriate selector strategy enum value (By.XPATH, By.CSS_SELECTOR,
                By.ID, or By.CLASS_NAME).
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
        Retrieves detailed information about a DOM node.

        Uses the CDP DOM.describeNode command to get comprehensive information
        about a node, including its attributes, properties, and DOM structure.
        This method is used internally to gather the data needed to properly
        initialize WebElement instances.

        Args:
            object_id: The CDP object ID of the node to describe.
                If empty, describes the document node. Default is an empty string.

        Returns:
            dict: A dictionary containing the node's complete description,
                including attributes, node type, tag name, and other properties.
        """
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=object_id)
        )
        return response['result']['node']

    async def _execute_command(self, command: Command[T]) -> T:
        """
        Executes a Chrome DevTools Protocol command.

        Sends a command to the browser via the connection handler and returns
        the response. This is an internal method used by other methods in this
        class to communicate with the browser.

        Args:
            command: The CDP command to execute, properly structured according
                to the protocol specification.

        Returns:
            T: The response from the browser after executing the command,
                with the type specified by the command's type parameter.
        """
        return await self._connection_handler.execute_command(command, timeout=60)  # type: ignore

    def _get_find_element_command(self, by: By, value: str, object_id: str = ''):
        """
        Creates the appropriate CDP command for finding a single element.

        Constructs a command object based on the selector type and context
        (global document or relative to another element). Handles special cases
        for different selector types like CLASS_NAME, ID, and XPATH.

        Args:
            by: The selector strategy to use (CSS_SELECTOR, XPATH, ID, etc.).
            value: The selector value to locate the element.
            object_id: The CDP object ID of the context element for relative searches.
                If empty, the search is performed in the global document context.
                Default is an empty string.

        Returns:
            Command: A properly structured CDP command object ready to be executed.
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
                object_id,
                script,
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
        Creates the appropriate CDP command for finding multiple elements.

        Constructs a command object based on the selector type and context
        (global document or relative to another element). Handles special cases
        for different selector types like CLASS_NAME, ID, and XPATH.

        Args:
            by: The selector strategy to use (CSS_SELECTOR, XPATH, ID, etc.).
            value: The selector value to locate the elements.
            object_id: The CDP object ID of the context element for relative searches.
                If empty, the search is performed in the global document context.
                Default is an empty string.

        Returns:
            Command: A properly structured CDP command object ready to be executed.
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
                object_id,
                script,
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
        Creates a CDP command specifically for finding an element by XPath.

        XPath selectors require special handling compared to CSS selectors.
        This method constructs the appropriate command based on whether the
        search is global or relative to another element.

        Args:
            xpath: The XPath expression to locate the element.
            object_id: The CDP object ID of the context element for relative searches.
                If empty, the search is performed in the global document context.

        Returns:
            Command: A properly structured CDP command object for XPath element finding.
        """
        escaped_value = xpath.replace('"', '\\"')
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                object_id,
                script,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script)
        return command

    def _get_find_elements_by_xpath_command(self, xpath: str, object_id: str):
        """
        Creates a CDP command specifically for finding multiple elements by XPath.

        XPath selectors require special handling compared to CSS selectors.
        This method constructs the appropriate command based on whether the
        search is global or relative to another element.

        Args:
            xpath: The XPath expression to locate the elements.
            object_id: The CDP object ID of the context element for relative searches.
                If empty, the search is performed in the global document context.

        Returns:
            Command: A properly structured CDP command object for XPath multiple element finding.
        """
        escaped_value = xpath.replace('"', '\\"')
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                object_id,
                script,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script)
        return command

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """
        Ensures an XPath expression is properly formatted for relative searches.

        Prepends a dot (.) to the XPath expression if it doesn't already start
        with one, making it a relative XPath that searches from the context node
        rather than from the document root.

        Args:
            xpath: The original XPath expression.

        Returns:
            str: The XPath expression modified to be relative if needed.
        """
        return f'.{xpath}' if not xpath.startswith('.') else xpath
