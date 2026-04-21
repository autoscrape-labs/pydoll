from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydoll.commands import DomCommands
from pydoll.connection import ConnectionHandler
from pydoll.constants import Scripts
from pydoll.elements.mixins import FindElementsMixin
from pydoll.exceptions import ElementNotFound
from pydoll.protocol.dom.types import ShadowRootType

if TYPE_CHECKING:
    from pydoll.elements.web_element import WebElement
    from pydoll.protocol.dom.methods import GetOuterHTMLResponse

logger = logging.getLogger(__name__)


class ShadowRoot(FindElementsMixin):
    """
    Shadow root wrapper for shadow DOM traversal.

    Provides element finding capabilities within shadow DOM boundaries
    using query() with CSS selectors. Use query() instead of find() —
    find() and XPath are not supported inside shadow roots.

    Usage:
        shadow_host = await tab.find(id='my-component')
        shadow_root = await shadow_host.get_shadow_root()
        button = await shadow_root.query('#internal-button')
        await button.click()
    """

    _css_only = True

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

        # Inherit iframe/routing context from host element if present
        if host_element:
            self._iframe_context = getattr(host_element, '_iframe_context', None)
            self._routing_session_handler = getattr(host_element, '_routing_session_handler', None)
            self._routing_session_id = getattr(host_element, '_routing_session_id', None)
            self._routing_parent_frame_id = getattr(host_element, '_routing_parent_frame_id', None)

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
        command: GetOuterHTMLResponse = await self._execute_command(
            DomCommands.get_outer_html(object_id=self._object_id)
        )
        return command['result']['outerHTML']

    async def get_children_elements(
        self, max_depth: int = 1, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """
        Retrieve all direct and nested child elements within this shadow root.

        Args:
            max_depth (int, optional): Maximum depth to traverse when finding children.
                Defaults to 1 for direct children only.
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all child elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of child WebElement objects found within the shadow root.

        Raises:
            ElementNotFound: If no child elements are found and raise_exc is True.
        """
        logger.debug(
            f'Getting shadow children: max_depth={max_depth}, '
            f'tag_filter={tag_filter}, raise_exc={raise_exc}'
        )
        children = await self._get_family_elements(
            script=Scripts.GET_CHILDREN_NODE, max_depth=max_depth, tag_filter=tag_filter
        )
        if not children and raise_exc:
            raise ElementNotFound(f'Child element not found for shadow root: {self}')
        logger.debug(f'Shadow children found: {len(children)}')
        return children

    async def get_siblings_elements(
        self, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """
        Retrieve all sibling elements of the shadow root (at the same DOM level).

        Note: Siblings of a shadow root are technically sibling elements of its host.

        Args:
            tag_filter (list[str], optional): List of HTML tag names to filter results.
                If empty, returns all sibling elements regardless of tag. Defaults to [].

        Returns:
            list[WebElement]: List of sibling WebElement objects matching criteria.
        """
        logger.debug(f'Getting shadow siblings: tag_filter={tag_filter}, raise_exc={raise_exc}')
        if not self._host_element:
            logger.warning(
                'get_siblings_elements called on ShadowRoot without host_element'
            )
            return []

        siblings = await self._host_element.get_siblings_elements(
            tag_filter=tag_filter, raise_exc=raise_exc
        )
        logger.debug(f'Shadow siblings (via host) found: {len(siblings)}')
        return siblings

    def __repr__(self) -> str:
        return f'ShadowRoot(mode={self._mode.value}, object_id={self._object_id})'

    def __str__(self) -> str:
        return f'ShadowRoot({self._mode.value})'
