from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.protocol.bidi.script.types import ContextTarget

if TYPE_CHECKING:
    from pydoll.elements.bidi.web_element import BiDiWebElement
    from pydoll.interactions.mouse import BiDiMouse

logger = logging.getLogger(__name__)


class BiDiShadowRoot(BidiFindElementsMixin):
    """Shadow root wrapper for Firefox/BiDi shadow DOM traversal.

    Searches are scoped to the shadow tree by passing the shadow root's sharedId
    as the locateNodes start node, which reaches both open and closed roots. Use
    query() with CSS selectors — XPath is not supported inside shadow roots
    (mirrors the CDP ShadowRoot).

    Usage:
        host = await tab.find(id='my-component')
        root = await host.get_shadow_root()
        button = await root.query('#internal-button')
    """

    _css_only = True

    def __init__(
        self,
        shadow_root_id: str,
        context_id: str,
        connection: BiDiConnectionHandler,
        mode: str = 'open',
        host_element: Optional[BiDiWebElement] = None,
        mouse: Optional[BiDiMouse] = None,
    ):
        self._shared_id = shadow_root_id
        self._context_id = context_id
        self._connection_handler = connection
        self._mode = mode
        self._host_element = host_element
        self._mouse = mouse

    @property
    def mode(self) -> str:
        """Shadow root mode ('open' or 'closed')."""
        return self._mode

    @property
    def host_element(self) -> Optional[BiDiWebElement]:
        """The shadow host element, if available."""
        return self._host_element

    @property
    async def inner_html(self) -> str:
        """HTML content of the shadow root."""
        response = await self._execute_command(
            ScriptCommands.call_function(
                function_declaration='(el) => el.innerHTML',
                await_promise=False,
                target=ContextTarget(context=self._context_id),
                arguments=[{'type': 'node', 'sharedId': self._shared_id}],
            )
        )
        result = response['result']
        if result['type'] != 'success':
            return ''
        return str(result['result'].get('value') or '')

    def __repr__(self) -> str:
        return f'BiDiShadowRoot(mode={self._mode!r}, shared_id={self._shared_id!r})'
