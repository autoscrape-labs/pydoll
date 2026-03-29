from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union, cast

from pydoll.commands import (
    DomCommands,
    RuntimeCommands,
)
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.constants import By, Scripts
from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.exceptions import ElementNotFound

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

logger = logging.getLogger(__name__)


def create_web_element(*args, **kwargs):
    """Create WebElement instance avoiding circular imports."""
    from pydoll.elements.cdp.web_element import WebElement  # noqa: PLC0415

    return WebElement(*args, **kwargs)


class CDPFindElementsMixin(FindElementsMixin):
    """CDP-specific implementation of element finding.

    Uses RuntimeCommands.evaluate/call_function_on for element location
    and DomCommands.describe_node for attribute extraction.
    """

    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional[WebElement]:
        """Find first element matching selector using CDP."""
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
                raise ElementNotFound()
            return None

        object_id = response_for_command['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
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

    async def _find_elements(
        self, by: By, value: str, raise_exc: bool = True
    ) -> list[WebElement]:
        """Find all elements matching selector using CDP."""
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

    async def _get_object_attributes(self, object_id: str) -> list[str]:
        """Get attributes of a DOM node."""
        node_description = await self._describe_node(object_id=object_id)
        if not node_description:
            return ['tag_name', '']
        attributes = node_description.get('attributes', [])
        tag_name = node_description.get('nodeName', '').lower()
        attributes.extend(['tag_name', tag_name])
        return attributes

    async def _describe_node(self, object_id: str = '') -> Node:
        """Get detailed DOM node information using CDP DOM.describeNode."""
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=object_id)
        )
        if 'error' in response:
            return {}
        return response.get('result', {}).get('node', {})

    def _apply_iframe_context_to_element(
        self, element: WebElement, iframe_context: IFrameContext | None
    ) -> None:
        """Propagate iframe context to the newly created element."""
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
        """Resolve handler and sessionId for the current context."""
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
        """Execute CDP command via resolved handler."""
        handler, session_id = self._resolve_routing()
        if session_id:
            command['sessionId'] = session_id
        return await handler.execute_command(command, timeout=60)

    def _get_find_element_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: Optional[int] = None,
    ):
        """Create CDP command for finding single element."""
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
        """Create CDP command for finding multiple elements."""
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
        """Create CDP command for XPath single element finding."""
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
        """Create CDP command for XPath multiple element finding."""
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
    def _has_object_id_key(response: Union[EvaluateResponse, CallFunctionOnResponse]) -> bool:
        """Check if response has objectId key."""
        return bool(response.get('result', {}).get('result', {}).get('objectId'))
