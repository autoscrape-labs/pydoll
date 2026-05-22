from __future__ import annotations

import asyncio
import base64 as _b64
import logging
from typing import TYPE_CHECKING, Optional, overload

import aiofiles

from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.commands.bidi.session_commands import SessionCommands
from pydoll.commands.bidi.storage_commands import StorageCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.events import BIDI_EVENT_MAP, Event
from pydoll.protocol.types import Cookie, CookieParam

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class BiDiTab(BidiFindElementsMixin):
    """Firefox tab automation via WebDriver BiDi protocol.

    Unlike CDP where each tab has its own WebSocket connection,
    BiDi uses a single shared connection — tabs are identified
    by their browsing context ID.
    """

    def __init__(
        self,
        context_id: str,
        connection: BiDiConnectionHandler,
    ):
        self._context_id = context_id
        self._connection_handler = connection

    @property
    async def current_url(self) -> str:
        """Get the current page URL."""
        result = await self._evaluate_js('location.href')
        return result.get('value', '')

    @property
    async def page_source(self) -> str:
        """Get the HTML source of the current page."""
        result = await self._evaluate_js('document.documentElement.outerHTML')
        return result.get('value', '')

    @property
    async def title(self) -> str:
        """Get the current page title."""
        result = await self._evaluate_js('document.title')
        return result.get('value', '')

    async def go_to(self, url: str, timeout: int = 300):
        """Navigate to a URL.

        Args:
            url: URL to navigate to.
            timeout: Maximum seconds to wait for navigation.
        """
        await self._execute_command(
            BrowsingContextCommands.navigate(
                context=self._context_id,
                url=url,
                wait='complete',
            ),
            timeout=timeout,
        )

    async def refresh(self, ignore_cache: bool = False):
        """Reload the current page."""
        await self._execute_command(
            BrowsingContextCommands.reload(
                context=self._context_id,
                ignore_cache=ignore_cache,
                wait='complete',
            )
        )

    async def close(self):
        """Close this tab."""
        await self._execute_command(
            BrowsingContextCommands.close(context=self._context_id)
        )

    async def bring_to_front(self):
        """Activate and focus this tab."""
        await self._execute_command(
            BrowsingContextCommands.activate(context=self._context_id)
        )

    async def take_screenshot(
        self,
        path: Optional[str] = None,
        as_base64: bool = False,
    ) -> Optional[str]:
        """Capture a screenshot.

        Args:
            path: File path to save the screenshot.
            as_base64: Return base64-encoded data instead of saving.

        Returns:
            Base64 string if as_base64=True, None otherwise.
        """
        response = await self._execute_command(
            BrowsingContextCommands.capture_screenshot(
                context=self._context_id,
            )
        )
        data = response['result']['data']

        if as_base64:
            return data

        if path:
            async with aiofiles.open(path, 'wb') as f:
                await f.write(_b64.b64decode(data))

        return None

    async def print_to_pdf(
        self,
        path: Optional[str] = None,
        landscape: bool = False,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
        """Print the page as PDF.

        Args:
            path: File path to save the PDF.
            landscape: Use landscape orientation.
            scale: Scale factor (0.1 to 2.0).
            as_base64: Return base64-encoded data instead of saving.

        Returns:
            Base64 string if as_base64=True, None otherwise.
        """
        orientation = 'landscape' if landscape else 'portrait'
        response = await self._execute_command(
            BrowsingContextCommands.print(
                context=self._context_id,
                orientation=orientation,
                scale=scale,
            )
        )
        data = response['result']['data']

        if as_base64:
            return data

        if path:
            async with aiofiles.open(path, 'wb') as f:
                await f.write(_b64.b64decode(data))

        return None

    async def execute_script(self, script: str, *args, **kwargs):
        """Execute JavaScript in this tab's context.

        Args:
            script: JavaScript expression to evaluate.

        Returns:
            The deserialized result of the script evaluation.
        """
        response = await self._execute_command(
            ScriptCommands.evaluate(
                expression=script,
                target={'context': self._context_id},
                await_promise=True,
            )
        )
        result = response['result']
        if result.get('type') == 'exception':
            raise RuntimeError(result['exceptionDetails']['text'])
        remote_value = result.get('result', {})
        return self._deserialize_remote_value(remote_value)

    async def get_cookies(self) -> list[Cookie]:
        """Get all cookies for this tab's context."""
        partition = {
            'type': 'context',
            'context': self._context_id,
        }
        response = await self._execute_command(
            StorageCommands.get_cookies(partition=partition)
        )
        bidi_cookies = response['result']['cookies']
        return [
            Cookie(
                name=c['name'],
                value=c['value'].get('value', '') if isinstance(c['value'], dict) else c['value'],
                domain=c['domain'],
                path=c['path'],
                size=c.get('size', 0),
                httpOnly=c['httpOnly'],
                secure=c['secure'],
                sameSite=c['sameSite'],
                **({'expiry': c['expiry']} if 'expiry' in c else {}),
            )
            for c in bidi_cookies
        ]

    async def set_cookies(self, cookies: list[CookieParam]):
        """Set cookies for this tab's context."""
        partition = {
            'type': 'context',
            'context': self._context_id,
        }
        for cookie in cookies:
            bidi_cookie = {
                'name': cookie['name'],
                'value': {'type': 'string', 'value': cookie['value']},
                'domain': cookie['domain'],
            }
            for key in ('path', 'httpOnly', 'secure', 'expiry'):
                if key in cookie:
                    bidi_cookie[key] = cookie[key]
            if 'sameSite' in cookie:
                bidi_cookie['sameSite'] = cookie['sameSite'].lower()
            await self._execute_command(
                StorageCommands.set_cookie(cookie=bidi_cookie, partition=partition)
            )

    async def delete_all_cookies(self):
        """Delete all cookies for this tab's context."""
        partition = {
            'type': 'context',
            'context': self._context_id,
        }
        await self._execute_command(
            StorageCommands.delete_cookies(partition=partition)
        )

    async def has_dialog(self) -> bool:
        """Check if a dialog is currently open."""
        return bool(self._connection_handler.dialog)

    async def get_dialog_message(self) -> str:
        """Get the message of the currently open dialog."""
        dialog = self._connection_handler.dialog
        if not dialog:
            return ''
        return dialog.get('params', {}).get('message', '')

    async def handle_dialog(
        self,
        accept: bool = True,
        prompt_text: Optional[str] = None,
    ):
        """Handle a dialog (alert/confirm/prompt).

        Args:
            accept: Accept or dismiss the dialog.
            prompt_text: Text to enter for prompt dialogs.
        """
        await self._execute_command(
            BrowsingContextCommands.handle_user_prompt(
                context=self._context_id,
                accept=accept,
                user_text=prompt_text,
            )
        )

    @property
    def network_logs(self) -> list:
        """Access captured network logs."""
        return self._connection_handler.network_logs

    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Any],
        temporary: bool = False,
    ) -> int: ...

    @overload
    async def on(
        self,
        event_name: str,
        callback: Callable[[Any], Awaitable[Any]],
        temporary: bool = False,
    ) -> int: ...

    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """Register event listener on this tab.

        Args:
            event_name: Event enum or native BiDi event name.
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.
        """
        native_event = event_name
        if isinstance(event_name, Event):
            native_event = BIDI_EVENT_MAP.get(event_name, event_name)

        await self._execute_command(
            SessionCommands.subscribe(
                events=[native_event],
                contexts=[self._context_id],
            )
        )

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        return await self._connection_handler.register_callback(
            native_event, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """Remove registered event callback."""
        await self._connection_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """Remove all registered event callbacks."""
        await self._connection_handler.clear_callbacks()

    async def execute_protocol_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Send a raw WebDriver BiDi command and return its typed result.

        Escape hatch for BiDi features not covered by the portable API. Build the
        command with the ``pydoll.commands.bidi.*`` builders.
        """
        return await self._execute_command(command, timeout)

    async def _execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Execute a BiDi command."""
        return await self._connection_handler.execute_command(command, timeout)

    async def _evaluate_js(self, expression: str) -> dict:
        """Evaluate a JavaScript expression and return the result value."""
        response = await self._execute_command(
            ScriptCommands.evaluate(
                expression=expression,
                target={'context': self._context_id},
                await_promise=False,
            )
        )
        result = response['result']
        if result.get('type') == 'success':
            return result.get('result', {})
        return {}

    @staticmethod
    def _deserialize_remote_value(remote_value: dict):
        """Convert a BiDi RemoteValue to a Python value."""
        value_type = remote_value.get('type')

        if value_type in ('undefined', 'null'):
            return None
        if value_type in ('string', 'boolean'):
            return remote_value.get('value')
        if value_type == 'number':
            val = remote_value.get('value')
            if val == 'NaN':
                return float('nan')
            if val == '-0':
                return -0.0
            if val == 'Infinity':
                return float('inf')
            if val == '-Infinity':
                return float('-inf')
            return val
        if value_type == 'bigint':
            return int(remote_value.get('value', '0'))
        if value_type == 'array':
            items = remote_value.get('value', [])
            return [BiDiTab._deserialize_remote_value(item) for item in items]
        if value_type in ('object', 'map'):
            pairs = remote_value.get('value', [])
            return {
                (k if isinstance(k, str) else BiDiTab._deserialize_remote_value(k)):
                BiDiTab._deserialize_remote_value(v)
                for k, v in pairs
            }
        if value_type == 'set':
            items = remote_value.get('value', [])
            return [BiDiTab._deserialize_remote_value(item) for item in items]
        if value_type == 'date':
            return remote_value.get('value')
        if value_type == 'regexp':
            val = remote_value.get('value', {})
            return f'/{val.get("pattern", "")}/{val.get("flags", "")}'
        if value_type == 'node':
            return remote_value
        return remote_value.get('value', remote_value)
