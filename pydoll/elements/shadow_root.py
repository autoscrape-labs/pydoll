from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydoll.commands import DomCommands
from pydoll.connection import ConnectionHandler
from pydoll.elements.mixins import FindElementsMixin
from pydoll.protocol.dom.types import ShadowRootType

if TYPE_CHECKING:
    from pydoll.elements.web_element import WebElement

logger = logging.getLogger(__name__)


class ShadowRoot(FindElementsMixin):
    """
    Shadow root wrapper for shadow DOM traversal.

    Provides element finding capabilities within shadow DOM boundaries
    using the same API as Tab and WebElement (find, query, find_or_wait_element).

    Usage:
        shadow_host = await tab.find(id='my-component')
        shadow_root = await shadow_host.get_shadow_root()
        button = await shadow_root.find(class_name='internal-button')
        await button.click()
    """

    def __init__(
        self,
        object_id: str,
        connection_handler: ConnectionHandler,
        mode: ShadowRootType = ShadowRootType.OPEN,
        host_element: WebElement | None = None,
    ):
        """
        Initialize shadow root wrapper.

        Args:
            object_id: CDP object ID for the shadow root node.
            connection_handler: Browser connection for CDP commands.
            mode: Shadow root mode (open, closed, or user-agent).
            host_element: Reference to the shadow host element.
        """
        self._object_id = object_id
        self._connection_handler = connection_handler
        self._mode = mode
        self._host_element = host_element
        logger.debug(
            f'ShadowRoot initialized: object_id={self._object_id}, mode={self._mode.value}'
        )

    @property
    def mode(self) -> ShadowRootType:
        """Shadow root mode (open, closed, or user-agent)."""
        return self._mode

    @property
    def host_element(self) -> WebElement | None:
        """Reference to the shadow host element, if available."""
        return self._host_element

    @property
    async def inner_html(self) -> str:
        """HTML content of the shadow root."""
        response = await self._execute_command(
            DomCommands.get_outer_html(object_id=self._object_id)
        )
        return response['result']['outerHTML']

    def __repr__(self) -> str:
        return f'ShadowRoot(mode={self._mode.value}, object_id={self._object_id})'

    def __str__(self) -> str:
        return f'ShadowRoot({self._mode.value})'
