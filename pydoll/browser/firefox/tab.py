from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, overload

from pydoll.browser.firefox.element import KEYS, FirefoxElement
from pydoll.protocol.bidi import browsing_context, script, session
from pydoll.protocol.bidi import input as bidi_input

if TYPE_CHECKING:
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler

logger = logging.getLogger(__name__)


class FirefoxTab:
    """
    Represents a Firefox browser tab using WebDriver BiDi protocol.

    Wraps a BiDi browsing context ID and provides high-level methods
    mirroring the Chromium Tab API.
    """

    def __init__(self, context_id: str, connection_handler: BiDiConnectionHandler):
        """
        Initialize a FirefoxTab.

        Args:
            context_id: BiDi browsing context ID for this tab.
            connection_handler: Shared BiDi connection handler.
        """
        self._context_id = context_id
        self._connection_handler = connection_handler
        logger.debug(f'FirefoxTab initialized: context_id={context_id}')

    @property
    def context_id(self) -> str:
        """BiDi browsing context ID for this tab."""
        return self._context_id

    async def go_to(self, url: str, wait: str = 'complete') -> dict:
        """
        Navigate to a URL and wait for the page to load.

        Args:
            url: URL to navigate to.
            wait: Page load strategy - 'none', 'interactive', or 'complete'.

        Returns:
            Navigation result dict with 'url' key.
        """
        logger.info(f'Navigating to {url} (context={self._context_id})')
        response = await self._connection_handler.execute_command(
            browsing_context.navigate(self._context_id, url, wait)
        )
        return response['result']

    async def evaluate(self, expression: str, await_promise: bool = True) -> Any:
        """
        Evaluate a JavaScript expression in this tab's context.

        Args:
            expression: JavaScript expression to evaluate.
            await_promise: Whether to await the result if it's a Promise.

        Returns:
            The JavaScript result value.
        """
        logger.debug(f'Evaluating expression in context={self._context_id}')
        response = await self._connection_handler.execute_command(
            script.evaluate(expression, self._context_id, await_promise)
        )
        result = response.get('result', {})
        script_result = result.get('result', {})
        return script_result.get('value')

    async def find(
        self,
        selector: str,
        selector_type: str = 'css',
        max_node_count: Optional[int] = None,
    ) -> list[FirefoxElement]:
        """
        Find elements in this tab using a CSS or XPath selector.

        Args:
            selector: CSS selector or XPath expression.
            selector_type: Locator type - 'css' or 'xpath'.
            max_node_count: Maximum number of nodes to return.

        Returns:
            List of FirefoxElement instances ready for interaction.
        """
        locator = {'type': selector_type, 'value': selector}
        logger.debug(
            f'Finding nodes: selector={selector!r}, type={selector_type}, '
            f'context={self._context_id}'
        )
        response = await self._connection_handler.execute_command(
            browsing_context.locate_nodes(self._context_id, locator, max_node_count)
        )
        nodes = response.get('result', {}).get('nodes', [])
        return [FirefoxElement(node, self._context_id, self._connection_handler) for node in nodes]

    async def take_screenshot(self) -> bytes:
        """
        Capture a screenshot of this tab.

        Returns:
            PNG screenshot as bytes.
        """
        logger.debug(f'Taking screenshot: context={self._context_id}')
        response = await self._connection_handler.execute_command(
            browsing_context.capture_screenshot(self._context_id)
        )
        data = response.get('result', {}).get('data', '')
        return base64.b64decode(data)

    @property
    async def current_url(self) -> Optional[str]:
        """Get the current URL of this tab."""
        return await self.evaluate('window.location.href')

    @property
    async def page_source(self) -> Optional[str]:
        """Get the full HTML source of the current page."""
        return await self.evaluate('document.documentElement.outerHTML')

    @property
    async def title(self) -> Optional[str]:
        """Get the current page title."""
        return await self.evaluate('document.title')

    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Awaitable[Any]],
        temporary: bool = False,
    ) -> int: ...
    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """
        Subscribe to a BiDi event and register a callback.

        Args:
            event_name: BiDi event name (e.g., 'browsingContext.load').
            callback: Function to call when the event fires (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for later removal.
        """
        import asyncio

        await self._connection_handler.execute_command(
            session.subscribe([event_name], contexts=[self._context_id])
        )

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        callback_id = await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )
        logger.debug(f'Registered callback: event={event_name}, id={callback_id}')
        return callback_id

    async def press_key(self, key: str) -> None:
        """
        Press a key in the current tab context (no specific element targeted).

        Args:
            key: Key name (e.g. 'enter', 'escape', 'tab') or a single character.
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

    async def remove_callback(self, callback_id: int) -> bool:
        """Remove a registered event callback by ID."""
        return await self._connection_handler.remove_callback(callback_id)

    async def new_tab(self, url: str = '') -> FirefoxTab:
        """
        Open a new browser tab.

        Args:
            url: URL to navigate to after opening (stays on about:blank if empty).

        Returns:
            New FirefoxTab instance.
        """
        logger.info('Creating new tab')
        response = await self._connection_handler.execute_command(browsing_context.create())
        context_id = response['result']['context']
        tab = FirefoxTab(context_id, self._connection_handler)
        if url:
            await tab.go_to(url)
        return tab

    async def close(self):
        """Close this tab's browsing context."""
        logger.info(f'Closing context: {self._context_id}')
        await self._connection_handler.execute_command(browsing_context.close(self._context_id))

    def __repr__(self) -> str:
        return f'FirefoxTab(context_id={self._context_id!r})'
