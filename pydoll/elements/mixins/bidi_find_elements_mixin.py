from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.constants import By
from pydoll.elements.mixins.find_elements_mixin import FindElementsMixin
from pydoll.exceptions import ElementNotFound
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browsing_context.types import (
    AccessibilityLocator,
    CssLocator,
    InnerTextLocator,
    Locator,
    XPathLocator,
)

if TYPE_CHECKING:
    from pydoll.elements.bidi.web_element import BiDiWebElement
    from pydoll.protocol.bidi.script.types import NodeRemoteValue

logger = logging.getLogger(__name__)


def create_bidi_web_element(*args, **kwargs):
    """Create BiDiWebElement instance avoiding circular imports."""
    from pydoll.elements.bidi.web_element import BiDiWebElement  # noqa: PLC0415

    return BiDiWebElement(*args, **kwargs)


class BidiFindElementsMixin(FindElementsMixin):
    """BiDi-specific implementation of element finding.

    Uses browsingContext.locateNodes for element location.
    Elements are referenced by sharedId for subsequent operations.
    """

    if TYPE_CHECKING:
        _connection_handler: BiDiConnectionHandler
        _context_id: str

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional[BiDiWebElement]:
        """Find first element matching selector using BiDi locateNodes."""
        locator = self._build_locator(by, value)
        start_nodes = self._get_start_nodes()

        response = await self._execute_command(
            BrowsingContextCommands.locate_nodes(
                context=self._context_id,
                locator=locator,
                max_node_count=1,
                start_nodes=start_nodes,
            )
        )
        nodes: list[NodeRemoteValue] = response['result']['nodes']
        if not nodes:
            if raise_exc:
                raise ElementNotFound()
            return None
        return self._create_element_from_node(nodes[0], by, value)

    async def _find_elements(
        self, by: By, value: str, raise_exc: bool = True
    ) -> list[BiDiWebElement]:
        """Find all elements matching selector using BiDi locateNodes."""
        locator = self._build_locator(by, value)
        start_nodes = self._get_start_nodes()

        response = await self._execute_command(
            BrowsingContextCommands.locate_nodes(
                context=self._context_id,
                locator=locator,
                start_nodes=start_nodes,
            )
        )
        nodes: list[NodeRemoteValue] = response['result']['nodes']
        if not nodes:
            if raise_exc:
                raise ElementNotFound()
            return []
        return [self._create_element_from_node(node, by, value) for node in nodes]

    async def _execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Execute a BiDi command."""
        return await self._connection_handler.execute_command(command, timeout)

    @staticmethod
    def _build_locator(by: By, value: str) -> Locator:
        """Convert By strategy + value to a BiDi Locator."""
        match by:
            case By.CSS_SELECTOR:
                return CssLocator(type='css', value=value)
            case By.XPATH:
                return XPathLocator(type='xpath', value=value)
            case By.ID:
                return CssLocator(type='css', value=f'#{value}')
            case By.CLASS_NAME:
                return CssLocator(type='css', value=f'.{value}')
            case By.TAG_NAME:
                return CssLocator(type='css', value=value)
            case By.NAME:
                return XPathLocator(type='xpath', value=f'//*[@name="{value}"]')
            case _:
                return CssLocator(type='css', value=value)

    def _get_start_nodes(self) -> Optional[list[dict]]:
        """Get start nodes for scoped search.

        Returns None for document-level search (Tab),
        or [SharedReference] for element-scoped search (BiDiWebElement).
        """
        shared_id = getattr(self, '_shared_id', None)
        if shared_id:
            return [{'sharedId': shared_id}]
        return None

    def _create_element_from_node(
        self, node: NodeRemoteValue, by: By, value: str
    ) -> BiDiWebElement:
        """Create a BiDiWebElement from a locateNodes result node."""
        node_props = node.get('value', {})
        attributes = node_props.get('attributes', {})
        tag_name = node_props.get('localName', '')

        return create_bidi_web_element(
            shared_id=node.get('sharedId', ''),
            context_id=self._context_id,
            connection=self._connection_handler,
            attributes=attributes,
            tag_name=tag_name,
            method=by,
            selector=value,
        )
