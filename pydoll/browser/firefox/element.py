from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from pydoll.browser.firefox.find_mixin import _FirefoxFindMixin
from pydoll.protocol.bidi import input as bidi_input
from pydoll.protocol.bidi import script

if TYPE_CHECKING:
    from pydoll.browser.firefox.shadow_root import FirefoxShadowRoot
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler

logger = logging.getLogger(__name__)

KEYS = {
    'ctrl': '\ue009',
    'shift': '\ue008',
    'alt': '\ue00a',
    'enter': '\ue006',
    'return': '\ue006',
    'backspace': '\ue003',
    'delete': '\ue017',
    'escape': '\ue00c',
    'esc': '\ue00c',
    'tab': '\ue004',
    'space': ' ',
    'up': '\ue013',
    'down': '\ue015',
    'left': '\ue012',
    'right': '\ue014',
    'home': '\ue011',
    'end': '\ue010',
    'pageup': '\ue00e',
    'pagedown': '\ue00f',
}


class FirefoxElement(_FirefoxFindMixin):
    """
    Represents a DOM element in a Firefox tab via WebDriver BiDi.

    Wraps a node reference returned by browsingContext.locateNodes and
    provides interaction methods (click, type, hover, etc.) using
    input.performActions with element origins.
    """

    def __init__(
        self,
        node: dict,
        context_id: str,
        connection_handler: BiDiConnectionHandler,
    ):
        """
        Initialize a FirefoxElement.

        Args:
            node: Raw node dict from browsingContext.locateNodes (must have 'sharedId').
            context_id: BiDi browsing context ID of the parent tab.
            connection_handler: Shared BiDi connection handler.
        """
        self._node = node
        self._context_id = context_id
        self._connection_handler = connection_handler
        self._shared_id: str = node.get('sharedId', '')
        logger.debug(f'FirefoxElement initialized: sharedId={self._shared_id}')

    @property
    def _find_start_nodes(self) -> list[dict]:
        """Scope ``find()`` / ``query()`` to within this element."""
        return [{'type': 'node', 'sharedId': self._shared_id}]

    @property
    def shared_id(self) -> str:
        """BiDi shared reference ID for this element."""
        return self._shared_id

    @property
    def node(self) -> dict:
        """Raw node dict returned by locateNodes."""
        return self._node

    async def click(self) -> None:
        """Click the center of the element."""
        logger.debug(f'Clicking element: sharedId={self._shared_id}')
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'pointer',
                        'id': 'mouse1',
                        'parameters': {'pointerType': 'mouse'},
                        'actions': [
                            {
                                'type': 'pointerMove',
                                'x': 0,
                                'y': 0,
                                'origin': {
                                    'type': 'element',
                                    'element': {'sharedId': self._shared_id},
                                },
                            },
                            {'type': 'pointerDown', 'button': 0},
                            {'type': 'pointerUp', 'button': 0},
                        ],
                    }
                ],
            )
        )

    async def hover(self) -> None:
        """Move the mouse over the element without clicking."""
        logger.debug(f'Hovering over element: sharedId={self._shared_id}')
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'pointer',
                        'id': 'mouse1',
                        'parameters': {'pointerType': 'mouse'},
                        'actions': [
                            {
                                'type': 'pointerMove',
                                'x': 0,
                                'y': 0,
                                'origin': {
                                    'type': 'element',
                                    'element': {'sharedId': self._shared_id},
                                },
                            },
                        ],
                    }
                ],
            )
        )

    async def type(self, text: str, clear_first: bool = True) -> None:
        """
        Click the element to focus it, then type text character by character.

        Args:
            text: Text to type into the element.
            clear_first: Select all existing content and delete it before typing.
        """
        await self.click()

        key_actions: list[dict] = []

        if clear_first:
            key_actions.extend([
                {'type': 'keyDown', 'value': KEYS['ctrl']},
                {'type': 'keyDown', 'value': 'a'},
                {'type': 'keyUp', 'value': 'a'},
                {'type': 'keyUp', 'value': KEYS['ctrl']},
                {'type': 'keyDown', 'value': KEYS['delete']},
                {'type': 'keyUp', 'value': KEYS['delete']},
            ])

        for char in text:
            key_actions.extend([
                {'type': 'keyDown', 'value': char},
                {'type': 'keyUp', 'value': char},
            ])

        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [{'type': 'key', 'id': 'keyboard1', 'actions': key_actions}],
            )
        )
        logger.debug(f'Typed {len(text)} chars into element: sharedId={self._shared_id}')

    async def press_key(self, key: str) -> None:
        """
        Press a single key while this element is focused.

        Args:
            key: Key name from KEYS dict (e.g. 'enter', 'tab', 'escape')
                 or a single character (e.g. 'a', '1').
        """
        value = KEYS.get(key.lower(), key)
        await self._connection_handler.execute_command(
            bidi_input.perform_actions(
                self._context_id,
                [
                    {
                        'type': 'key',
                        'id': 'keyboard1',
                        'actions': [
                            {'type': 'keyDown', 'value': value},
                            {'type': 'keyUp', 'value': value},
                        ],
                    }
                ],
            )
        )

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get the value of an HTML attribute (e.g. 'href', 'class')."""
        return await self._call_function(f'(el) => el.getAttribute("{name}")')

    async def get_property(self, name: str) -> Any:
        """Get the value of a DOM property (e.g. 'value', 'checked', 'disabled')."""
        return await self._call_function(f'(el) => el["{name}"]')

    @property
    async def text(self) -> str:
        """Visible text content of the element (innerText)."""
        return await self._call_function('(el) => el.innerText') or ''

    @property
    async def inner_html(self) -> str:
        """Inner HTML of the element."""
        return await self._call_function('(el) => el.innerHTML') or ''

    async def _call_function(self, function_declaration: str) -> Any:
        """Call a JS function with this element as the first argument."""
        response: dict = await self._connection_handler.execute_command(
            script.call_function(
                function_declaration=function_declaration,
                context=self._context_id,
                args=[{'sharedId': self._shared_id}],
            )
        )
        result = response.get('result', {})
        script_result = result.get('result', {})
        return script_result.get('value')

    async def get_shadow_root(self) -> FirefoxShadowRoot:
        """
        Return the shadow root attached to this element.

        Raises:
            ValueError: If the element has no shadow root (``el.shadowRoot`` is ``null``).
        """
        from pydoll.browser.firefox.shadow_root import FirefoxShadowRoot

        response: dict = await self._connection_handler.execute_command(
            script.call_function(
                function_declaration='(el) => el.shadowRoot',
                context=self._context_id,
                args=[{'sharedId': self._shared_id}],
            )
        )
        result = response.get('result', {}).get('result', {})
        shared_id = result.get('sharedId', '')
        if not shared_id:
            raise ValueError(f'Element {self._shared_id!r} has no shadow root')
        return FirefoxShadowRoot(shared_id, self._context_id, self._connection_handler)

    def __repr__(self) -> str:
        return f'FirefoxElement(sharedId={self._shared_id!r})'
