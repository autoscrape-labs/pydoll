from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence, cast

from pydoll.commands import (
    DomCommands,
    RuntimeCommands,
)
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import By, Scripts
from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.exceptions import (
    CommandFailed,
    ElementNotFound,
    ScriptException,
)

if TYPE_CHECKING:
    from pydoll.elements.cdp.web_element import WebElement
    from pydoll.interactions.iframe import IFrameContext
    from pydoll.protocol.cdp.base import Command, T_CommandParams, T_CommandResponse
    from pydoll.protocol.cdp.dom.methods import DescribeNodeResponse
    from pydoll.protocol.cdp.dom.types import Node
    from pydoll.protocol.cdp.runtime.methods import (
        CallFunctionOnParams,
        CallFunctionOnResponse,
        EvaluateParams,
        EvaluateResponse,
        GetPropertiesResponse,
    )
    from pydoll.protocol.cdp.runtime.types import CallArgument


logger = logging.getLogger(__name__)


def create_web_element(*args, **kwargs):
    """
    Create WebElement instance avoiding circular imports.

    Factory method that dynamically imports WebElement at runtime
    to prevent circular import dependencies.
    """
    from pydoll.elements.cdp.web_element import WebElement  # noqa: PLC0415

    return WebElement(*args, **kwargs)


class CDPFindElementsMixin(FindElementsMixin['WebElement']):
    """
    CDP-specific implementation of element finding.

    Uses ``Runtime.evaluate`` / ``Runtime.callFunctionOn`` for element location
    and ``DOM.describeNode`` for attribute extraction. Commands are routed through
    the session of the frame the object lives in (``_resolve_routing``), so an
    element inside an out-of-process iframe talks to that frame's target.

    Host classes (Tab, WebElement, ShadowRoot) provide ``_connection_handler``;
    elements additionally carry ``_object_id``, ``_mouse``, ``_iframe_context``
    and the ``_routing_session_*`` attributes read here through ``getattr``.
    """

    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler

    async def _find_element(self, by: By, value: str, raise_exc: bool = True) -> WebElement | None:
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
        logger.debug('_find_element(): by=%s, value=%s, raise_exc=%s', by, value, raise_exc)
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context()

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

        try:
            response_for_command: (
                EvaluateResponse | CallFunctionOnResponse
            ) = await self._execute_command(command)
        except CommandFailed as exc:
            self._not_found(raise_exc, f'Element search rejected by the browser: {exc}', exc)
            return None

        if not self._has_object_id_key(response_for_command):
            self._not_found(raise_exc, 'Element not found')
            return None

        object_id = response_for_command['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
        logger.debug('_find_element() found object_id=%s', object_id)
        element = create_web_element(
            object_id,
            self._connection_handler,
            by,
            value,
            attributes,
            mouse=getattr(self, '_mouse', None),
        )
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
        logger.debug('_find_elements(): by=%s, value=%s, raise_exc=%s', by, value, raise_exc)
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context()

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

        try:
            response_for_command: (
                EvaluateResponse | CallFunctionOnResponse
            ) = await self._execute_command(command)
        except CommandFailed as exc:
            self._not_found(raise_exc, f'Element search rejected by the browser: {exc}', exc)
            return []

        if not self._has_object_id_key(response_for_command):
            self._not_found(raise_exc, 'No elements found')
            return []

        object_id = response_for_command['result']['result']['objectId']
        try:
            object_ids = await self._collection_object_ids(object_id)
        except CommandFailed as exc:
            self._not_found(raise_exc, f'Element list vanished before it was read: {exc}', exc)
            return []

        inherited_context = iframe_context or getattr(self, '_iframe_context', None)
        elements = await self._wrap_elements(object_ids, by, value, inherited_context)
        logger.debug('_find_elements() returning %s elements', len(elements))
        return elements

    async def query_script(
        self,
        function_declaration: str,
        arguments: list[CallArgument] | None = None,
        execution_context_id: int | None = None,
    ) -> list[WebElement]:
        """
        Run a JavaScript function that returns elements and wrap them as WebElements.

        The function runs with the search root bound to ``this`` (``document`` on a
        Tab, the frame document on an iframe element, the element itself on a
        WebElement, the root on a ShadowRoot) in the same execution context and
        iframe routing that ``query()`` uses. It may return a single Element, a
        NodeList, an array of Elements, or ``null``.

        Args:
            function_declaration: JavaScript function source, e.g.
                ``function(tag) { return this.querySelectorAll(tag); }``.
            arguments: CDP call arguments passed positionally to the function.
            execution_context_id: Run in this execution context of the frame (for
                example an isolated world created with ``Page.createIsolatedWorld``)
                with ``this`` bound to that context's ``document``. Ignored when the
                root is a non-iframe element, whose object id already fixes the context.

        Returns:
            WebElements for every element the function returned, in return order.

        Raises:
            ScriptException: If the function throws or fails to compile.
            CommandFailed: If the browser rejects the command itself.
        """
        logger.debug('query_script(): length=%s', len(function_declaration))
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context()

        if execution_context_id is None and iframe_context:
            if not iframe_context.document_object_id:
                execution_context_id = iframe_context.execution_context_id
        element_root = hasattr(self, '_object_id') and not getattr(self, 'is_iframe', False)
        if execution_context_id is not None and not element_root:
            command = RuntimeCommands.call_function_on(
                function_declaration=(
                    f'function() {{ return ({function_declaration}).apply(document, arguments); }}'
                ),
                arguments=arguments,
                execution_context_id=execution_context_id,
                return_by_value=False,
            )
        else:
            if iframe_context:
                root_object_id = iframe_context.document_object_id or ''
            elif hasattr(self, '_object_id'):
                root_object_id = self._object_id
            else:
                root_object_id = await self._document_object_id()
            command = RuntimeCommands.call_function_on(
                function_declaration=function_declaration,
                object_id=root_object_id,
                arguments=arguments,
                return_by_value=False,
            )
        response: CallFunctionOnResponse = await self._execute_command(command)
        self._raise_script_exception(response)
        remote_object = response['result']['result']
        result_object_id = remote_object.get('objectId')
        if not result_object_id:
            return []

        if remote_object.get('subtype') == 'node':
            object_ids = [result_object_id]
        else:
            object_ids = await self._collection_object_ids(result_object_id)

        inherited_context = iframe_context or getattr(self, '_iframe_context', None)
        elements = await self._wrap_elements(object_ids, 'script', None, inherited_context)
        logger.debug('query_script() returning %s elements', len(elements))
        return elements

    async def _document_object_id(self) -> str:
        """Resolve the remote object id of ``document`` in the default context."""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate(expression='document', return_by_value=False)
        )
        return response['result']['result']['objectId']

    async def _collection_object_ids(self, object_id: str) -> list[str]:
        """Object ids of the indexed entries of an array-like remote object."""
        query_response: GetPropertiesResponse = await self._execute_command(
            RuntimeCommands.get_properties(object_id=object_id)
        )
        object_ids: list[str] = []
        for query in query_response.get('result', {}).get('result', []):
            if not (query['name'].isdigit() and 'objectId' in query['value']):
                continue
            object_ids.append(query['value']['objectId'])
        return object_ids

    async def _wrap_elements(
        self,
        object_ids: list[str],
        by: str | None,
        value: str | None,
        inherited_context: IFrameContext | None,
    ) -> list[WebElement]:
        """Describe each node and build the WebElements, propagating iframe context."""
        elements = []
        for object_id in object_ids:
            try:
                node_description = await self._describe_node(object_id=object_id)
            except KeyError:
                continue

            attributes = node_description.get('attributes', [])
            tag_name = node_description.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            child = create_web_element(
                object_id,
                self._connection_handler,
                by,
                value,
                attributes,
                mouse=getattr(self, '_mouse', None),
            )
            self._apply_iframe_context_to_element(child, inherited_context)
            elements.append(child)
        return elements

    @staticmethod
    def _raise_script_exception(response: CallFunctionOnResponse) -> None:
        """Surface a JavaScript exception thrown by a script as ScriptException."""
        details = response.get('result', {}).get('exceptionDetails')
        if not details:
            return
        exception = details.get('exception', {})
        message = exception.get('description') or details.get('text') or 'Script threw an exception'
        raise ScriptException(message)

    async def _get_object_attributes(self, object_id: str) -> list[str]:
        """
        Get attributes of a DOM node.

        When the node cannot be described (the object id does not reference a
        Node), minimal attributes are returned to keep the flow stable.
        """
        node_description = await self._describe_node(object_id=object_id)
        if not node_description:
            return ['tag_name', '']
        attributes = node_description.get('attributes', [])
        tag_name = node_description.get('nodeName', '').lower()
        attributes.extend(['tag_name', tag_name])
        return attributes

    async def _describe_node(self, object_id: str = '') -> Node:
        """
        Get detailed DOM node information using CDP DOM.describeNode.

        Used internally to gather data for WebElement initialization.
        """
        try:
            response: DescribeNodeResponse = await self._execute_command(
                DomCommands.describe_node(object_id=object_id)
            )
        except CommandFailed:
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

    def _resolve_routing(self) -> tuple[ConnectionHandler, str | None]:
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

    async def execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse], timeout: int = 60
    ) -> T_CommandResponse:
        """
        Send a raw CDP command through this object's session.

        The command is routed exactly like the object's own operations: a Tab
        sends it to the page session, a WebElement inside an out-of-process
        iframe sends it to that frame's session. Build commands with the
        factories in ``pydoll.commands`` or pass a plain ``{'method': ..., 'params': ...}``
        dict for methods pydoll does not wrap.

        Args:
            command: CDP command to send.
            timeout: Seconds to wait for the browser's answer.

        Returns:
            The browser's response, with the domain result under ``'result'``.

        Raises:
            CommandFailed: If the browser answers with an error.
            CommandExecutionTimeout: If no answer arrives within ``timeout``.
        """
        handler, session_id = self._resolve_routing()
        if session_id:
            command['sessionId'] = session_id
        return await handler.execute_command(command, timeout=timeout)

    async def _execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse]
    ) -> T_CommandResponse:
        """Execute CDP command via resolved handler (60s timeout)."""
        handler, session_id = self._resolve_routing()
        if session_id:
            command['sessionId'] = session_id
        return await handler.execute_command(command, timeout=60)

    async def _execute_commands(
        self, commands: Sequence[Command[T_CommandParams, T_CommandResponse]]
    ) -> list[T_CommandResponse]:
        """Send a batch of commands in order through the resolved handler."""
        handler, session_id = self._resolve_routing()
        if session_id:
            for command in commands:
                command['sessionId'] = session_id
        return await handler.execute_commands(commands, timeout=60)

    def _get_find_element_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: int | None = None,
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
        command: (
            Command[CallFunctionOnParams, CallFunctionOnResponse]
            | Command[EvaluateParams, EvaluateResponse]
        )
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
        execution_context_id: int | None = None,
    ):
        """
        Create CDP command for finding multiple elements.

        Similar to _get_find_element_command but for multiple element searches.
        Handles same special cases and selector type conversions.
        """
        escaped_value = value.replace('"', '\\"')
        command: (
            Command[CallFunctionOnParams, CallFunctionOnResponse]
            | Command[EvaluateParams, EvaluateResponse]
        )
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
        execution_context_id: int | None = None,
    ):
        """
        Create CDP command specifically for XPath single element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        command: (
            Command[CallFunctionOnParams, CallFunctionOnResponse]
            | Command[EvaluateParams, EvaluateResponse]
        )
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
        execution_context_id: int | None = None,
    ):
        """
        Create CDP command specifically for XPath multiple element finding.

        XPath requires special handling vs CSS selectors. Ensures relative
        XPath for context-based searches.
        """
        escaped_value = xpath.replace('"', '\\"')
        command: (
            Command[CallFunctionOnParams, CallFunctionOnResponse]
            | Command[EvaluateParams, EvaluateResponse]
        )
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
    def _not_found(raise_exc: bool, reason: str, cause: BaseException | None = None) -> None:
        """Log a failed search and raise ElementNotFound when the caller asked for it."""
        logger.debug(reason)
        if raise_exc:
            raise ElementNotFound() from cause

    @staticmethod
    def _has_object_id_key(response: EvaluateResponse | CallFunctionOnResponse) -> bool:
        """
        Check if response has objectId key.
        """
        return bool(response.get('result', {}).get('result', {}).get('objectId'))
