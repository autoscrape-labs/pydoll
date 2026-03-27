from __future__ import annotations

import asyncio
import base64
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Awaitable, Callable, Optional, overload

import aiofiles

from pydoll.browser.firefox.element import KEYS
from pydoll.browser.firefox.find_mixin import _FirefoxFindMixin
from pydoll.exceptions import NetworkEventsNotEnabled, NoDialogPresent
from pydoll.protocol.bidi import browsing_context, network, script, session, storage
from pydoll.protocol.bidi import input as bidi_input
from pydoll.protocol.bidi.browsing_context import BrowsingContextEvent
from pydoll.protocol.bidi.input import InputEvent
from pydoll.protocol.bidi.network import Header, InterceptPhase, NetworkEvent

if TYPE_CHECKING:
    from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
    from pydoll.protocol.bidi.storage import CookieParam

logger = logging.getLogger(__name__)


class FirefoxTab(_FirefoxFindMixin):
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
        self._network_events_enabled: bool = False
        self._network_logs: list[dict] = []
        self._network_logs_callback_id: Optional[int] = None
        self._current_dialog: Optional[dict] = None
        self._dialog_subscribed: bool = False
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
        response: dict = await self._connection_handler.execute_command(
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
        response: dict = await self._connection_handler.execute_command(
            script.evaluate(expression, self._context_id, await_promise)
        )
        result = response.get('result', {})
        script_result = result.get('result', {})
        return script_result.get('value')

    async def take_screenshot(
        self, path: Optional[str] = None, as_base64: bool = False
    ) -> Optional[bytes | str]:
        """
        Capture a screenshot of this tab.

        Args:
            path: If provided, save the screenshot to this file path.
            as_base64: If True, return the screenshot as a base64 string.

        Returns:
            PNG bytes, base64 string, or None (if path provided).
        """
        logger.debug(f'Taking screenshot: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.capture_screenshot(self._context_id)
        )
        data = response.get('result', {}).get('data', '')
        if as_base64:
            return data
        png_bytes = base64.b64decode(data)
        if path is not None:
            async with aiofiles.open(path, 'wb') as f:
                await f.write(png_bytes)
            return None
        return png_bytes

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

    async def get_cookies(self) -> list[dict]:
        """
        Get all cookies for this tab's browsing context.

        Returns:
            List of cookie dicts with keys: name, value, domain, path,
            httpOnly, secure, sameSite, expiry, etc.
        """
        logger.debug(f'Getting cookies: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            storage.get_cookies(self._context_id)
        )
        return response.get('result', {}).get('cookies', [])

    async def set_cookie(
        self,
        name: str,
        value: str,
        domain: str,
        path: str = '/',
        http_only: bool = False,
        secure: bool = False,
        same_site: Optional[str] = None,
        expiry: Optional[int] = None,
    ) -> None:
        """
        Set a cookie in this tab's browsing context.

        Args:
            name: Cookie name.
            value: Cookie value.
            domain: Cookie domain (e.g. 'example.com').
            path: Cookie path (default '/').
            http_only: Whether the cookie is HTTP-only.
            secure: Whether the cookie requires HTTPS.
            same_site: SameSite policy - 'strict', 'lax', or 'none'.
            expiry: Cookie expiry as a Unix timestamp.
        """
        logger.debug(f'Setting cookie {name!r}: context={self._context_id}')
        await self._connection_handler.execute_command(
            storage.set_cookie(
                self._context_id,
                name=name,
                value=value,
                domain=domain,
                path=path,
                http_only=http_only,
                secure=secure,
                same_site=same_site,
                expiry=expiry,
            )
        )

    async def set_cookies(self, cookies: list[CookieParam]) -> None:
        """
        Set multiple cookies in this tab's browsing context.

        Args:
            cookies: List of CookieParam dicts. Each must have ``name``,
                ``value`` and ``domain``; all other fields are optional.
        """
        logger.debug(f'Setting {len(cookies)} cookies: context={self._context_id}')
        for cookie in cookies:
            await self._connection_handler.execute_command(
                storage.set_cookie(
                    self._context_id,
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie['domain'],
                    path=cookie.get('path', '/'),
                    http_only=cookie.get('httpOnly', False),
                    secure=cookie.get('secure', False),
                    same_site=cookie.get('sameSite'),
                    expiry=cookie.get('expiry'),
                )
            )

    async def delete_cookies(
        self, name: Optional[str] = None, domain: Optional[str] = None
    ) -> None:
        """
        Delete cookies in this tab's browsing context.

        Args:
            name: If provided, only delete cookies with this name.
            domain: If provided, only delete cookies for this domain.
                    When neither is given, all cookies for the context are deleted.
        """
        cookie_filter = None
        if name is not None or domain is not None:
            cookie_filter = storage.CookieFilter()
            if name is not None:
                cookie_filter['name'] = name
            if domain is not None:
                cookie_filter['domain'] = domain

        logger.debug(
            f'Deleting cookies: context={self._context_id}, name={name!r}, domain={domain!r}'
        )
        await self._connection_handler.execute_command(
            storage.delete_cookies(self._context_id, filter=cookie_filter)
        )

    async def delete_all_cookies(self) -> None:
        """Delete all cookies for this tab's browsing context."""
        await self.delete_cookies()

    async def refresh(self, wait: str = 'complete') -> dict:
        """
        Reload the current page.

        Args:
            wait: Page load strategy - 'none', 'interactive', or 'complete'.

        Returns:
            Reload result dict with 'url' key.
        """
        logger.info(f'Refreshing context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.reload(self._context_id, wait)
        )
        return response.get('result', {})

    async def go_back(self) -> dict:
        """
        Navigate one step back in browser history.

        Returns:
            TraverseHistory result dict.
        """
        logger.info(f'Going back: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.traverse_history(self._context_id, delta=-1)
        )
        return response.get('result', {})

    async def go_forward(self) -> dict:
        """
        Navigate one step forward in browser history.

        Returns:
            TraverseHistory result dict.
        """
        logger.info(f'Going forward: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.traverse_history(self._context_id, delta=1)
        )
        return response.get('result', {})

    async def enable_network_events(self) -> None:
        """
        Subscribe to all BiDi network monitoring events for this tab.

        After calling this, use ``tab.on(NetworkEvent.BEFORE_REQUEST_SENT, cb)``
        etc. to receive events. No intercept is registered — requests flow
        through unblocked.
        """
        logger.info(f'Enabling network events: context={self._context_id}')
        await self._connection_handler.execute_command(
            session.subscribe(NetworkEvent.ALL_EVENTS, contexts=[self._context_id])
        )

        async def _log_event(event: dict) -> None:
            self._network_logs.append(event)

        self._network_logs_callback_id = await self._connection_handler.register_callback(
            NetworkEvent.BEFORE_REQUEST_SENT, _log_event, False
        )
        self._network_events_enabled = True

    async def disable_network_events(self) -> None:
        """Unsubscribe from all BiDi network monitoring events for this tab."""
        logger.info(f'Disabling network events: context={self._context_id}')
        await self._connection_handler.execute_command(
            session.unsubscribe(NetworkEvent.ALL_EVENTS, contexts=[self._context_id])
        )
        if self._network_logs_callback_id is not None:
            await self._connection_handler.remove_callback(self._network_logs_callback_id)
            self._network_logs_callback_id = None
        self._network_events_enabled = False

    async def add_intercept(
        self,
        phases: Optional[list[str]] = None,
        url_patterns: Optional[list[str]] = None,
    ) -> str:
        """
        Register a network intercept scoped to this tab.

        Every matching request will be **blocked** until the callback calls
        ``continue_request()``, ``fail_request()``, or ``provide_response()``.

        Args:
            phases: Intercept phases. Defaults to ``['beforeRequestSent']``.
                    Use ``InterceptPhase`` constants.
            url_patterns: Optional URL glob patterns (e.g. ``'*://api.example.com/*'``).
                          Omit to intercept all URLs.

        Returns:
            Intercept ID — pass to ``remove_intercept()`` to clean up.
        """
        if phases is None:
            phases = [InterceptPhase.BEFORE_REQUEST_SENT]
        logger.info(f'Adding intercept phases={phases}: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            network.add_intercept(
                phases=phases,
                contexts=[self._context_id],
                url_patterns=url_patterns,
            )
        )
        return response['result']['intercept']

    async def remove_intercept(self, intercept_id: str) -> None:
        """Remove a previously registered network intercept."""
        logger.debug(f'Removing intercept {intercept_id!r}')
        await self._connection_handler.execute_command(network.remove_intercept(intercept_id))

    async def continue_request(
        self,
        request_id: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[list[Header]] = None,
        body: Optional[str] = None,
    ) -> None:
        """
        Allow a blocked request to proceed, with optional modifications.

        Must be called from within a ``network.beforeRequestSent`` callback
        when ``isBlocked`` is ``True``.

        Args:
            request_id: ``event['params']['request']['request']``.
            url: Override the request URL.
            method: Override the HTTP method (e.g. ``'POST'``).
            headers: Override headers — list of ``{'name': ..., 'value': ...}`` dicts.
            body: Override the request body as a plain string.
        """
        await self._connection_handler.execute_command(
            network.continue_request(request_id, url=url, method=method, headers=headers, body=body)
        )

    async def fail_request(self, request_id: str) -> None:
        """
        Abort a blocked request with a network error.

        Args:
            request_id: ``event['params']['request']['request']``.
        """
        await self._connection_handler.execute_command(network.fail_request(request_id))

    async def provide_response(
        self,
        request_id: str,
        status_code: int = 200,
        headers: Optional[list[Header]] = None,
        body: Optional[str] = None,
        reason_phrase: Optional[str] = None,
    ) -> None:
        """
        Fulfill a blocked request with a synthetic response without hitting the server.

        Args:
            request_id: ``event['params']['request']['request']``.
            status_code: HTTP status code (default 200).
            headers: Response headers — list of ``{'name': ..., 'value': ...}`` dicts.
            body: Response body as a plain string.
            reason_phrase: HTTP reason phrase (e.g. ``'OK'``, ``'Not Found'``).
        """
        await self._connection_handler.execute_command(
            network.provide_response(
                request_id,
                status_code=status_code,
                headers=headers,
                body=body,
                reason_phrase=reason_phrase,
            )
        )

    async def continue_response(
        self,
        request_id: str,
        status_code: Optional[int] = None,
        headers: Optional[list[Header]] = None,
        reason_phrase: Optional[str] = None,
    ) -> None:
        """
        Allow a blocked response to proceed, with optional modifications.

        Must be called from within a ``network.responseStarted`` callback
        when ``isBlocked`` is ``True``.

        Args:
            request_id: ``event['params']['request']['request']``.
            status_code: Override the response status code.
            headers: Override response headers.
            reason_phrase: Override the HTTP reason phrase.
        """
        await self._connection_handler.execute_command(
            network.continue_response(
                request_id, status_code=status_code, headers=headers, reason_phrase=reason_phrase
            )
        )

    async def continue_with_auth(
        self,
        request_id: str,
        action: str = 'cancel',
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Respond to an auth challenge from a ``network.authRequired`` event.

        Args:
            request_id: ``event['params']['request']['request']``.
            action: ``'provideCredentials'``, ``'default'``, or ``'cancel'``.
            username: Username (required when action is ``'provideCredentials'``).
            password: Password (required when action is ``'provideCredentials'``).
        """
        await self._connection_handler.execute_command(
            network.continue_with_auth(
                request_id, action=action, username=username, password=password
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
        response: dict = await self._connection_handler.execute_command(browsing_context.create())
        context_id = response['result']['context']
        tab = FirefoxTab(context_id, self._connection_handler)
        if url:
            await tab.go_to(url)
        return tab

    async def close(self):
        """Close this tab's browsing context."""
        logger.info(f'Closing context: {self._context_id}')
        await self._connection_handler.execute_command(browsing_context.close(self._context_id))

    async def has_dialog(self) -> bool:
        """
        Check whether a dialog (alert, confirm, prompt) is currently open.

        Subscribes to userPromptOpened on first call.
        """
        if not self._dialog_subscribed:
            await self._connection_handler.execute_command(
                session.subscribe(
                    [BrowsingContextEvent.USER_PROMPT_OPENED], contexts=[self._context_id]
                )
            )

            async def _on_dialog(event: dict) -> None:
                self._current_dialog = event

            await self._connection_handler.register_callback(
                BrowsingContextEvent.USER_PROMPT_OPENED, _on_dialog, False
            )
            self._dialog_subscribed = True
        return bool(self._current_dialog)

    async def get_dialog_message(self) -> str:
        """
        Return the message text of the currently open dialog.

        Raises:
            NoDialogPresent: If no dialog is currently open.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        return self._current_dialog['params']['message']  # type: ignore[index]

    async def handle_dialog(self, accept: bool, prompt_text: Optional[str] = None) -> None:
        """
        Accept or dismiss the currently open dialog.

        Args:
            accept: True to accept, False to dismiss.
            prompt_text: Optional text for prompt dialogs.

        Raises:
            NoDialogPresent: If no dialog is currently open.
        """
        if not await self.has_dialog():
            raise NoDialogPresent()
        await self._connection_handler.execute_command(
            browsing_context.handle_user_prompt(self._context_id, accept, prompt_text)
        )
        self._current_dialog = None

    async def bring_to_front(self) -> None:
        """Activate/focus this tab."""
        logger.debug(f'Bringing to front: context={self._context_id}')
        await self._connection_handler.execute_command(browsing_context.activate(self._context_id))

    async def print_to_pdf(
        self,
        path: Optional[str] = None,
        landscape: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
        """
        Print the current page to PDF.

        Args:
            path: If provided, save the PDF to this file path.
            landscape: Whether to print in landscape orientation.
            print_background: Whether to print background graphics.
            scale: Scale factor (0.1–2.0).
            as_base64: If True, return the PDF as a base64 string.

        Returns:
            Base64 string if as_base64=True, None if path provided.

        Raises:
            ValueError: If neither path nor as_base64=True is specified.
        """
        logger.debug(f'Printing to PDF: context={self._context_id}')
        response: dict = await self._connection_handler.execute_command(
            browsing_context.print_page(self._context_id, landscape, print_background, scale)
        )
        data: str = response['result']['data']
        if as_base64:
            return data
        if path is not None:
            pdf_bytes = base64.b64decode(data)
            async with aiofiles.open(path, 'wb') as f:
                await f.write(pdf_bytes)
            return None
        raise ValueError('path is required when as_base64 is False')

    async def get_network_response_body(self, request_id: str) -> str:
        """
        Retrieve the response body for a completed network request.

        Args:
            request_id: The BiDi request ID from a network event.

        Returns:
            Response body as a string.

        Raises:
            NetworkEventsNotEnabled: If network events haven't been enabled.
        """
        if not self._network_events_enabled:
            raise NetworkEventsNotEnabled()
        response: dict = await self._connection_handler.execute_command(
            network.get_response_body(request_id)
        )
        return response['result']['body']

    async def clear_callbacks(self) -> None:
        """Remove all registered event callbacks."""
        await self._connection_handler.clear_callbacks()

    def get_network_logs(self, filter: Optional[str] = None) -> list[dict]:
        """
        Return captured network log events.

        Args:
            filter: Optional URL substring to filter events by.

        Returns:
            List of network event dicts.

        Raises:
            NetworkEventsNotEnabled: If network events haven't been enabled.
        """
        if not self._network_events_enabled:
            raise NetworkEventsNotEnabled()
        if filter is None:
            return list(self._network_logs)
        return [
            event
            for event in self._network_logs
            if filter in event.get('params', {}).get('request', {}).get('url', '')
        ]

    @asynccontextmanager
    async def expect_file_chooser(self, files: list[str]) -> AsyncIterator[None]:
        """
        Context manager that handles a file chooser dialog.

        Subscribe to ``input.fileDialogOpened`` before yielding, then set files
        automatically when the dialog opens.

        Args:
            files: List of absolute file paths to select.

        Example::

            async with tab.expect_file_chooser(['/tmp/file.txt']):
                await element.click()  # triggers file input dialog
        """
        await self._connection_handler.execute_command(
            session.subscribe([InputEvent.FILE_DIALOG_OPENED], contexts=[self._context_id])
        )

        async def _on_file_dialog(event: dict) -> None:
            element = event.get('params', {}).get('element', {})
            shared_id = element.get('sharedId', '')
            if shared_id:
                await self._connection_handler.execute_command(
                    bidi_input.set_files(self._context_id, shared_id, files)
                )

        callback_id = await self._connection_handler.register_callback(
            InputEvent.FILE_DIALOG_OPENED, _on_file_dialog, True
        )
        try:
            yield
        finally:
            await self._connection_handler.remove_callback(callback_id)

    def __repr__(self) -> str:
        return f'FirefoxTab(context_id={self._context_id!r})'
