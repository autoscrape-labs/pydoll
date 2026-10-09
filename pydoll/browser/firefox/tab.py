from __future__ import annotations

import asyncio
import base64 as _b64
import contextlib
import json
import logging
import shutil
from collections.abc import Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, TypeVar, cast, overload
from urllib.parse import urlparse

import aiofiles

from pydoll.browser.firefox.fingerprint_applier import BiDiFingerprintApplier
from pydoll.browser.requests.bidi.request import BiDiRequest
from pydoll.commands.bidi.browser_commands import BrowserCommands
from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.emulation_commands import EmulationCommands
from pydoll.commands.bidi.input_commands import InputCommands as BiDiInputCommands
from pydoll.commands.bidi.network_commands import NetworkCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.commands.bidi.session_commands import SessionCommands
from pydoll.commands.bidi.storage_commands import StorageCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.exceptions import (
    CommandFailed,
    DownloadTimeout,
    NetworkEventsNotEnabled,
    NoDialogPresent,
    ScriptEvaluationError,
    WaitElementTimeout,
    WaitTimeout,
)
from pydoll.extractor.engine import ExtractionEngine
from pydoll.interactions.keyboard import BiDiKeyboard
from pydoll.interactions.mouse import BiDiMouse
from pydoll.interactions.scroll import BiDiScroll
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browser.types import DownloadBehaviorAllowed
from pydoll.protocol.bidi.browsing_context.types import ImageFormat, Info, ReadinessState
from pydoll.protocol.bidi.network.types import Cookie as BiDiCookie
from pydoll.protocol.bidi.network.types import DataType, SameSite, StringValue
from pydoll.protocol.bidi.script.types import (
    ContextTarget,
    EvaluateResultSuccess,
    NodeRemoteValue,
    SerializationOptions,
    SharedReference,
)
from pydoll.protocol.bidi.storage.types import BrowsingContextPartitionDescriptor, PartialCookie
from pydoll.protocol.cdp.network.types import Cookie, CookieParam, CookieSameSite
from pydoll.protocol.events import BIDI_EVENT_MAP, Event
from pydoll.utils import PollInterval, UrlPattern, has_return_outside_function, url_matcher

if TYPE_CHECKING:
    from typing import AsyncGenerator, Awaitable, Callable

    from pydoll.elements.bidi.shadow_root import BiDiShadowRoot
    from pydoll.elements.bidi.web_element import BiDiWebElement
    from pydoll.extractor.model import ExtractionModel
    from pydoll.protocol.fingerprint.types import FingerprintConfig

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ExtractionModel')

_MAX_COLLECTED_BYTES = 50_000_000
_SUCCESS_STATUSES = range(200, 300)
_BODILESS_STATUSES = frozenset({204, 205, 304})
_FALSY_NUMBERS = frozenset({0, 'NaN', '-0'})

_BIDI_TO_CDP_SAME_SITE: dict[str, CookieSameSite] = {
    SameSite.STRICT.value: CookieSameSite.STRICT,
    SameSite.LAX.value: CookieSameSite.LAX,
    SameSite.NONE.value: CookieSameSite.NONE,
}


class BiDiTab(BidiFindElementsMixin):
    """Firefox tab automation via WebDriver BiDi protocol.

    Unlike CDP where each tab has its own WebSocket connection,
    BiDi uses a single shared connection; tabs are identified
    by their browsing context ID.
    """

    def __init__(
        self,
        context_id: str,
        connection: BiDiConnectionHandler,
    ):
        self._context_id = context_id
        self._connection_handler = connection
        self._mouse: BiDiMouse = BiDiMouse(self)
        self._keyboard: BiDiKeyboard | None = None
        self._scroll: BiDiScroll | None = None
        self._request: BiDiRequest | None = None
        self._extraction_engine: ExtractionEngine | None = None
        self._network_introspection_enabled = False
        self._response_collector_id: str | None = None
        self._fingerprint_applier: BiDiFingerprintApplier | None = None

    @property
    def mouse(self) -> BiDiMouse:
        """Mouse controller for this tab (real, trusted pointer input).

        Shared with every element found through this tab so the cursor position
        is preserved across interactions (humanized moves start where the last
        one ended).
        """
        return self._mouse

    @property
    def keyboard(self) -> BiDiKeyboard:
        """Keyboard controller for this tab (real, trusted key input)."""
        if self._keyboard is None:
            self._keyboard = BiDiKeyboard(self)
        return self._keyboard

    @property
    def scroll(self) -> BiDiScroll:
        """Scroll controller for this tab (humanized wheel via performActions)."""
        if self._scroll is None:
            self._scroll = BiDiScroll(self)
        return self._scroll

    @property
    def request(self) -> BiDiRequest:
        """HTTP client that runs in this tab's fetch context (cookies/session reused)."""
        if self._request is None:
            self._request = BiDiRequest(self)
        return self._request

    @property
    def _extractor(self) -> ExtractionEngine:
        """Lazy-initialized extraction engine."""
        if self._extraction_engine is None:
            self._extraction_engine = ExtractionEngine(self)
        return self._extraction_engine

    async def extract(
        self,
        model: type[T],
        *,
        scope: str | None = None,
        timeout: int = 0,
    ) -> T:
        """Extract structured data from the page into a typed model.

        Args:
            model: ExtractionModel subclass defining the extraction schema.
            scope: Optional CSS/XPath selector to limit the extraction region.
            timeout: Seconds to wait for elements (0 = no wait).

        Returns:
            Populated model instance with extracted data.

        Raises:
            FieldExtractionFailed: If a required field cannot be extracted.
        """
        return await self._extractor.extract(model, scope=scope, timeout=timeout)

    async def extract_all(
        self,
        model: type[T],
        *,
        scope: str,
        timeout: int = 0,
        limit: int | None = None,
    ) -> list[T]:
        """Extract multiple items from repeated containers on the page.

        Each element matching the scope selector generates one model instance,
        with fields resolved relative to that container.

        Args:
            model: ExtractionModel subclass defining the extraction schema.
            scope: CSS/XPath selector for the repeated container (required).
            timeout: Seconds to wait for elements (0 = no wait).
            limit: Maximum number of items to extract (None = all).

        Returns:
            List of populated model instances.
        """
        return await self._extractor.extract_all(model, scope=scope, timeout=timeout, limit=limit)

    async def get_network_logs(self, filter: str | None = None) -> list[dict]:
        """Return captured network request logs for this tab.

        Enables network introspection on first use (subscribes to
        network.beforeRequestSent and starts a response data collector), so call
        this before the traffic you want to capture. Returns the raw BiDi
        beforeRequestSent events for this browsing context.

        Args:
            filter: If set, only logs whose request URL contains this substring.
        """
        await self._ensure_network_introspection()
        logs = [
            log
            for log in self._connection_handler.network_logs
            if log.get('params', {}).get('context') == self._context_id
        ]
        if filter:
            logs = [
                log for log in logs if filter in log['params'].get('request', {}).get('url', '')
            ]
        return logs

    async def get_network_response_body(self, request_id: str) -> str:
        """Return the response body for a captured request id, decoded to text.

        BiDi retrieves bodies from a data collector, so network introspection must
        have been enabled (via get_network_logs) before the response arrived.

        Args:
            request_id: The request id from a network log (params.request.request).

        Raises:
            NetworkEventsNotEnabled: If network introspection was never enabled.
        """
        if not self._network_introspection_enabled or not self._response_collector_id:
            raise NetworkEventsNotEnabled(
                'Network events must be enabled to get response body '
                '(call get_network_logs() before the request)'
            )
        body, is_base64 = await self._collected_body(request_id, self._response_collector_id)
        if is_base64:
            return _b64.b64decode(body).decode('utf-8', 'replace')
        return body

    async def _collected_body(self, request_id: str, collector_id: str) -> tuple[str, bool]:
        """Read a collected response body; the flag says whether it is base64."""
        data = await self._execute_command(
            NetworkCommands.get_data(
                data_type=DataType.RESPONSE,
                request=request_id,
                collector=collector_id,
            )
        )
        bytes_value = data['result']['bytes']
        value = bytes_value.get('value', '')
        if not isinstance(value, str):
            return '', False
        return value, bytes_value.get('type') == 'base64'

    async def _ensure_network_introspection(self) -> None:
        """Subscribe to request/response events and start a response collector (once).

        The responseCompleted subscription is required for the data collector to
        finalize response bodies; without it network.getData blocks.
        """
        if self._network_introspection_enabled:
            return
        await self._execute_command(
            SessionCommands.subscribe(
                events=['network.beforeRequestSent', 'network.responseCompleted'],
                contexts=[self._context_id],
            )
        )
        self._response_collector_id = await self._add_response_collector()
        self._network_introspection_enabled = True

    async def _add_response_collector(self) -> str:
        """Start a BiDi data collector for response bodies and return its id."""
        response = await self._execute_command(
            NetworkCommands.add_data_collector(
                data_types=[DataType.RESPONSE], max_encoded_data_size=_MAX_COLLECTED_BYTES
            )
        )
        return response['result']['collector']

    async def current_url(self) -> str:
        """Get the current page URL."""
        return str(await self._evaluate_js('location.href') or '')

    async def page_source(self) -> str:
        """Get the HTML source of the current page."""
        return str(await self._evaluate_js('document.documentElement.outerHTML') or '')

    async def title(self) -> str:
        """Get the current page title."""
        return str(await self._evaluate_js('document.title') or '')

    async def go_to(self, url: str, timeout: int = 300):
        """Navigate to a URL.

        Args:
            url: URL to navigate to.
            timeout: Maximum seconds to wait for navigation.
        """
        logger.info('Navigating to URL: %s (timeout=%ss)', url, timeout)
        await self._execute_command(
            BrowsingContextCommands.navigate(
                context=self._context_id,
                url=url,
                wait=ReadinessState.COMPLETE,
            ),
            timeout=timeout,
        )

    async def refresh(self, ignore_cache: bool = False):
        """Reload the current page.

        Args:
            ignore_cache: Ask for a cache-bypassing reload. Firefox has not
                implemented the BiDi ``ignoreCache`` argument and rejects the
                command when it is sent, so it is only sent when True.

        Raises:
            CommandFailed: If ``ignore_cache`` is True on a Firefox that rejects it.
        """
        await self._execute_command(
            BrowsingContextCommands.reload(
                context=self._context_id,
                ignore_cache=True if ignore_cache else None,
                wait=ReadinessState.COMPLETE,
            )
        )

    async def useragent_override(self, user_agent: str) -> None:
        """Override the User-Agent string for this tab at runtime.

        Uses emulation.setUserAgentOverride scoped to this browsing context.
        """
        await self._execute_command(
            EmulationCommands.set_user_agent_override(
                user_agent=user_agent, contexts=[self._context_id]
            )
        )

    async def apply_fingerprint(self, fingerprint: FingerprintConfig) -> None:
        """Apply a browser fingerprint profile to this tab.

        Delegates to a per-tab :class:`BiDiFingerprintApplier` (created once and
        reused), which overrides the identity signals Firefox exposes through the
        BiDi ``emulation`` module natively and installs the JavaScript overrides as
        a preload script scoped to this browsing context. Call before navigating
        for full effect: the preload script runs ahead of page scripts on every
        navigation, while the current document only receives the JS layer.

        Sections Firefox cannot honour are skipped rather than faked:
        ``hardware.device_memory``, ``network_connection`` and ``client_hints``
        (the APIs do not exist in Gecko), ``media_features`` and ``permissions``
        (no per-tab BiDi command; use ``Firefox.grant_permissions``), and the
        identity inside Web Workers (BiDi preload scripts reach window realms
        only). See :class:`BiDiFingerprintApplier` for the native/JS split.

        Args:
            fingerprint: Fingerprint configuration. Only specified fields are
                overridden; unspecified fields keep real browser values.
        """
        if self._fingerprint_applier is None:
            self._fingerprint_applier = BiDiFingerprintApplier(self)
        await self._fingerprint_applier.apply(fingerprint)

    async def close(self):
        """Close this tab."""
        await self._execute_command(BrowsingContextCommands.close(context=self._context_id))

    async def bring_to_front(self):
        """Activate and focus this tab."""
        await self._execute_command(BrowsingContextCommands.activate(context=self._context_id))

    async def take_screenshot(
        self,
        path: str | Path | None = None,
        quality: int = 100,
        beyond_viewport: bool = False,
        as_base64: bool = False,
    ) -> str | None:
        """Capture a screenshot.

        Args:
            path: File path to save the screenshot (extension picks the format).
            quality: JPEG quality 0-100 (only applied when saving as .jpg/.jpeg).
            beyond_viewport: Capture the full page instead of just the viewport.
            as_base64: Return base64-encoded data instead of saving.

        Returns:
            Base64 string if as_base64=True, None otherwise.
        """
        extension = Path(path).suffix.lstrip('.').lower() if path is not None else ''
        if extension in {'jpg', 'jpeg'}:
            image_format: ImageFormat = {'type': 'image/jpeg', 'quality': quality / 100}
        else:
            image_format = {'type': 'image/png'}

        response = await self._execute_command(
            BrowsingContextCommands.capture_screenshot(
                context=self._context_id,
                origin='document' if beyond_viewport else 'viewport',
                format=image_format,
            )
        )
        return await self._deliver_binary(response['result']['data'], path, as_base64)

    async def print_to_pdf(
        self,
        path: str | Path | None = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> str | None:
        """Print the page as PDF.

        Args:
            path: File path to save the PDF.
            landscape: Use landscape orientation.
            display_header_footer: Accepted for CDP parity; WebDriver BiDi has no
                header/footer toggle, so it is ignored.
            print_background: Include background graphics.
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
                background=print_background,
            )
        )
        return await self._deliver_binary(response['result']['data'], path, as_base64)

    @staticmethod
    async def _deliver_binary(data: str, path: str | Path | None, as_base64: bool) -> str | None:
        """Return base64 data or write its decoded bytes to ``path``."""
        if as_base64:
            return data
        if path:
            async with aiofiles.open(str(path), 'wb') as f:
                await f.write(_b64.b64decode(data))
        return None

    async def evaluate(self, script: str, *args: object) -> object:
        """Evaluate JavaScript in this tab and return its deserialized result.

        Args:
            script: JavaScript to run. With args, pass a function expression
                (e.g. ``(a, b) => a + b``); the args are forwarded to it.
            *args: values forwarded to the script function.

        Returns:
            The script's return value as a Python object.

        Raises:
            ScriptEvaluationError: If the script throws or its promise rejects.
        """
        result = await self._evaluate_result(script, *args)
        return self._deserialize_remote_value(result['result'])

    async def _evaluate_result(
        self,
        script: str,
        *args: object,
        serialization_options: SerializationOptions | None = None,
    ) -> EvaluateResultSuccess:
        """Run ``script`` and return the BiDi EvaluateResultSuccess payload.

        ``script`` is an expression, a script with ``return``, or (with ``args``)
        a function expression the args are forwarded to.
        """
        target = ContextTarget(context=self._context_id)
        if args:
            response = await self._execute_command(
                ScriptCommands.call_function(
                    function_declaration=script,
                    await_promise=True,
                    target=target,
                    arguments=[self._to_local_value(arg) for arg in args],
                    serialization_options=serialization_options,
                )
            )
        else:
            expression = script
            if has_return_outside_function(script):
                expression = f'(function() {{ {script} }})()'
            response = await self._execute_command(
                ScriptCommands.evaluate(
                    expression=expression,
                    target=target,
                    await_promise=True,
                    serialization_options=serialization_options,
                )
            )
        result = response['result']
        if result['type'] == 'exception':
            raise ScriptEvaluationError(_exception_text(result['exceptionDetails']))
        return result

    @staticmethod
    def _to_local_value(value: object) -> dict:
        """Convert a Python value to a BiDi LocalValue for script arguments."""
        if value is None:
            return {'type': 'null'}
        if isinstance(value, bool):
            return {'type': 'boolean', 'value': value}
        if isinstance(value, (int, float)):
            return {'type': 'number', 'value': value}
        if isinstance(value, str):
            return {'type': 'string', 'value': value}
        if isinstance(value, (list, tuple)):
            return {'type': 'array', 'value': [BiDiTab._to_local_value(item) for item in value]}
        if isinstance(value, dict):
            return {
                'type': 'object',
                'value': [[key, BiDiTab._to_local_value(item)] for key, item in value.items()],
            }
        raise TypeError(f'Cannot serialize {type(value).__name__} as a BiDi script argument')

    async def wait_for_url(self, url: UrlPattern, timeout: float = 30) -> str:
        """Wait until the tab's URL matches a pattern and return it.

        Covers full navigations and in-page changes (``pushState``) alike,
        because it reads the live URL instead of listening to one event.

        Args:
            url: A glob (``'*/checkout/*'``), a compiled regular expression,
                or a callable that receives the URL and returns True to match.
            timeout: Maximum seconds to wait.

        Returns:
            The URL that matched.

        Raises:
            WaitTimeout: If no matching URL is seen within ``timeout``.
        """
        matches = url_matcher(url)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        interval = PollInterval()
        while True:
            current = await self.current_url()
            if matches(current):
                return current
            if loop.time() >= deadline:
                raise WaitTimeout(
                    f'Timed out after {timeout}s waiting for the URL to match {url!r}'
                )
            await interval.wait()

    async def wait_for_script(self, script: str, timeout: float = 30) -> Any:
        """Wait until a JavaScript expression evaluates to a truthy value and return it.

        Truthiness is JavaScript's, judged on the serialized result: a node, a
        function, an object (even ``{}`` or ``[]``) and a non-empty string or
        non-zero number are truthy; ``undefined``, ``null``, ``false``, ``0``,
        ``NaN``, ``-0``, ``0n`` and ``''`` are falsy. A promise is awaited and
        its settled value is judged.

        Args:
            script: An expression such as ``'window.app && window.app.ready'``,
                or a script with a ``return``.
            timeout: Maximum seconds to wait.

        Returns:
            The value itself when it is a primitive (string, number, ``True``),
            ``True`` for any object, node or function.

        Raises:
            WaitTimeout: If the script stays falsy for ``timeout`` seconds.
            ScriptEvaluationError: As soon as the script throws or its promise
                rejects, with the JavaScript error text.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        interval = PollInterval()
        while True:
            result = await self._evaluate_result(
                script, serialization_options=SerializationOptions(maxObjectDepth=0)
            )
            remote = result['result']
            if _remote_value_is_truthy(remote):
                value = self._deserialize_remote_value(remote)
                return value if isinstance(value, (str, int, float, bool)) else True
            if loop.time() >= deadline:
                raise WaitTimeout(f'Timed out after {timeout}s waiting for script: {script!r}')
            await interval.wait()

    async def wait_for_absence(
        self,
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        timeout: float = 30,
        **attributes: str,
    ) -> None:
        """Wait until no element matches the criteria, the same criteria ``find()`` takes.

        Use it for the thing that has to go away before you continue: a
        loading overlay, a "saving" badge, a modal that closes on its own.

        Args:
            id, class_name, name, tag_name, text, **attributes: Criteria, as in ``find()``.
            timeout: Maximum seconds to wait.

        Raises:
            WaitTimeout: If a matching element is still present after ``timeout``.
        """
        criteria: dict[str, str] = {
            key: value
            for key, value in {
                'id': id,
                'class_name': class_name,
                'name': name,
                'tag_name': tag_name,
                'text': text,
            }.items()
            if value is not None
        }
        criteria.update(attributes)
        finder = cast('Callable[..., Awaitable[BiDiWebElement | None]]', self.find)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        interval = PollInterval()
        while True:
            element = await finder(timeout=0, raise_exc=False, **criteria)
            if element is None:
                return
            if loop.time() >= deadline:
                raise WaitTimeout(f'Timed out after {timeout}s waiting for an element to disappear')
            await interval.wait()

    async def wait_for_network_idle(self, idle_time: float = 0.5, timeout: float = 30) -> None:
        """Wait until the page has had no network requests in flight for ``idle_time`` seconds.

        Requests are counted from the moment this method is called, so call
        it right after the action that starts them (a navigation, a click that
        loads data). A request that never finishes keeps the page busy until
        ``timeout``.

        Args:
            idle_time: Seconds without any request in flight that count as idle.
            timeout: Maximum seconds to wait.

        Raises:
            WaitTimeout: If the network is never idle for ``idle_time`` within ``timeout``.
        """
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        in_flight: set[str] = set()
        quiet_since = loop.time()

        def started(event: dict) -> None:
            nonlocal quiet_since
            in_flight.add(_event_request_id(event))
            quiet_since = loop.time()

        def finished(event: dict) -> None:
            nonlocal quiet_since
            in_flight.discard(_event_request_id(event))
            if not in_flight:
                quiet_since = loop.time()

        callback_ids = [
            await self.on(Event.REQUEST_SENT, started),
            await self.on(Event.RESPONSE_COMPLETED, finished),
            await self.on(Event.FETCH_ERROR, finished),
        ]
        try:
            while True:
                if not in_flight and loop.time() - quiet_since >= idle_time:
                    return
                if loop.time() >= deadline:
                    raise WaitTimeout(
                        f'Timed out after {timeout}s waiting for the network to be idle '
                        f'({len(in_flight)} requests in flight)'
                    )
                await asyncio.sleep(min(0.05, idle_time))
        finally:
            await self._remove_callbacks(callback_ids)

    @asynccontextmanager
    async def expect_navigation(
        self, url: UrlPattern | None = None, timeout: float = 30
    ) -> AsyncGenerator[None, None]:
        """Wait for a navigation started inside the block, and for the new page to load.

        Register before acting, act inside the block, and the block only
        exits once this browsing context has loaded a document (whose URL
        matches ``url``, when given).

        Args:
            url: Optional glob, regular expression or callable the new URL must match.
            timeout: Maximum seconds to wait after the block.

        Raises:
            WaitTimeout: If the navigation or the load does not happen in time.
        """
        matches = url_matcher(url) if url is not None else None
        loop = asyncio.get_running_loop()
        loaded: asyncio.Future[str] = loop.create_future()

        def on_load(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id or loaded.done():
                return
            new_url = params.get('url', '')
            if matches is None or matches(new_url):
                loaded.set_result(new_url)

        callback_id = await self.on(Event.PAGE_LOADED, on_load)
        try:
            yield
            try:
                await asyncio.wait_for(loaded, timeout)
            except asyncio.TimeoutError:
                raise WaitTimeout(f'Timed out after {timeout}s waiting for a navigation')
        finally:
            await self._remove_callbacks([callback_id])

    @asynccontextmanager
    async def expect_request(
        self, url: UrlPattern, timeout: float = 30
    ) -> AsyncGenerator[BiDiRequestHandle, None]:
        """Capture the first request whose URL matches, sent during the block.

        The handle is empty inside the block and filled when the block exits,
        which is when the wait happens.

        Args:
            url: A glob, a compiled regular expression, or a callable on the URL.
            timeout: Maximum seconds to wait after the block for the request.

        Yields:
            BiDiRequestHandle: URL, method and headers of the request.

        Raises:
            WaitTimeout: If no matching request is sent within ``timeout``.
        """
        matches = url_matcher(url)
        loop = asyncio.get_running_loop()
        seen: asyncio.Future[dict] = loop.create_future()

        def on_request(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id or seen.done():
                return
            if matches(params['request']['url']):
                seen.set_result(params)

        callback_id = await self.on(Event.REQUEST_SENT, on_request)
        handle = BiDiRequestHandle()
        try:
            yield handle
            try:
                params = await asyncio.wait_for(seen, timeout)
            except asyncio.TimeoutError:
                raise WaitTimeout(f'Timed out after {timeout}s waiting for a request to {url!r}')
            handle._fill(params)
        finally:
            await self._remove_callbacks([callback_id])

    @asynccontextmanager
    async def expect_response(
        self, url: UrlPattern, timeout: float = 30
    ) -> AsyncGenerator[BiDiResponseHandle, None]:
        """Capture the first response whose URL matches, received during the block.

        The block exits once the response has completed and its body has been
        read from a BiDi data collector, so ``response.json()`` is ready right
        after the block. A 204, 205 or 304 response has no body by definition,
        so it completes with an empty body.

        Args:
            url: A glob, a compiled regular expression, or a callable on the URL.
            timeout: Maximum seconds to wait after the block for the response.

        Yields:
            BiDiResponseHandle: status, headers and body of the response.

        Raises:
            WaitTimeout: If no matching response completes within ``timeout``.
        """
        matches = url_matcher(url)
        loop = asyncio.get_running_loop()
        completed: asyncio.Future[tuple[dict, bool]] = loop.create_future()

        def on_completed(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id or completed.done():
                return
            if matches(params['response']['url']):
                completed.set_result((params, True))

        def on_failed(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id or completed.done():
                return
            if matches(params['request']['url']):
                completed.set_result((params, False))

        collector_id = await self._add_response_collector()
        callback_ids = [
            await self.on(Event.RESPONSE_COMPLETED, on_completed),
            await self.on(Event.FETCH_ERROR, on_failed),
        ]
        handle = BiDiResponseHandle()
        try:
            yield handle
            try:
                params, succeeded = await asyncio.wait_for(completed, timeout)
            except asyncio.TimeoutError:
                raise WaitTimeout(f'Timed out after {timeout}s waiting for a response from {url!r}')
            body = await self._response_body(params, collector_id) if succeeded else None
            handle._fill(params, body)
        finally:
            await self._remove_callbacks(callback_ids)
            with contextlib.suppress(Exception):
                await self._execute_command(
                    NetworkCommands.remove_data_collector(collector=collector_id)
                )

    async def _response_body(self, params: dict, collector_id: str) -> bytes:
        """The collected body of a completed response (empty for bodiless statuses)."""
        status = int(params['response'].get('status', 0))
        try:
            body, is_base64 = await self._collected_body(_event_request_id(params), collector_id)
        except CommandFailed:
            if status in _BODILESS_STATUSES:
                return b''
            raise
        return _b64.b64decode(body) if is_base64 else body.encode('utf-8')

    async def _remove_callbacks(self, callback_ids: list[int]) -> None:
        """Remove listeners registered by a wait, tolerating a closed connection."""
        for callback_id in callback_ids:
            with contextlib.suppress(Exception):
                await self.remove_callback(callback_id)

    async def get_cookies(self) -> list[Cookie]:
        """Get all cookies for this tab's context, in the CDP ``Cookie`` shape."""
        partition = BrowsingContextPartitionDescriptor(type='context', context=self._context_id)
        response = await self._execute_command(StorageCommands.get_cookies(partition=partition))
        return [self._to_cdp_cookie(c) for c in response['result']['cookies']]

    @staticmethod
    def _to_cdp_cookie(cookie: BiDiCookie) -> Cookie:
        """Convert a BiDi cookie to the CDP ``Cookie`` shape the portable API returns.

        BiDi carries no ``session``/``sourcePort``: ``session`` is derived from the
        absence of ``expiry`` and ``sourcePort`` is -1 (CDP's "unspecified").
        """
        expiry = cookie.get('expiry')
        result = Cookie(
            name=cookie['name'],
            value=str(cookie['value'].get('value', '')),
            domain=cookie['domain'],
            path=cookie['path'],
            expires=float(expiry) if expiry is not None else -1,
            size=cookie['size'],
            httpOnly=cookie['httpOnly'],
            secure=cookie['secure'],
            session=expiry is None,
            sourcePort=-1,
        )
        same_site = _BIDI_TO_CDP_SAME_SITE.get(str(cookie.get('sameSite', '')))
        if same_site is not None:
            result['sameSite'] = same_site
        return result

    @staticmethod
    def _to_bidi_cookie(cookie: CookieParam) -> PartialCookie:
        """Convert a CDP ``CookieParam`` to the BiDi PartialCookie storage.setCookie takes.

        Raises:
            ValueError: If neither ``domain`` nor a ``url`` to derive it from is given
                (BiDi requires the domain).
        """
        domain = cookie.get('domain') or urlparse(cookie.get('url', '')).hostname
        if not domain:
            raise ValueError('BiDi cookies need a domain (or a url to derive it from)')
        bidi_cookie = PartialCookie(
            name=cookie['name'],
            value=StringValue(type='string', value=cookie['value']),
            domain=domain,
        )
        if 'path' in cookie:
            bidi_cookie['path'] = cookie['path']
        if 'httpOnly' in cookie:
            bidi_cookie['httpOnly'] = cookie['httpOnly']
        if 'secure' in cookie:
            bidi_cookie['secure'] = cookie['secure']
        if 'expires' in cookie:
            bidi_cookie['expiry'] = int(cookie['expires'])
        if 'sameSite' in cookie:
            bidi_cookie['sameSite'] = SameSite(str(cookie['sameSite']).lower())
        return bidi_cookie

    async def set_cookies(self, cookies: list[CookieParam]):
        """Set cookies for this tab's context (CDP ``CookieParam`` shape)."""
        partition = BrowsingContextPartitionDescriptor(type='context', context=self._context_id)
        for cookie in cookies:
            await self._execute_command(
                StorageCommands.set_cookie(cookie=self._to_bidi_cookie(cookie), partition=partition)
            )

    async def delete_all_cookies(self):
        """Delete all cookies for this tab's context."""
        partition = BrowsingContextPartitionDescriptor(type='context', context=self._context_id)
        await self._execute_command(StorageCommands.delete_cookies(partition=partition))

    async def has_dialog(self) -> bool:
        """Check if a dialog is currently open."""
        return bool(self._connection_handler.dialog)

    async def get_dialog_message(self) -> str:
        """Get the message of the currently open dialog.

        Raises:
            NoDialogPresent: If no dialog is currently displayed.
        """
        dialog = self._connection_handler.dialog
        if not dialog:
            raise NoDialogPresent()
        return dialog.get('params', {}).get('message', '')

    async def handle_dialog(
        self,
        accept: bool = True,
        prompt_text: str | None = None,
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

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: str | Path | list[str | Path]
    ) -> AsyncGenerator[None, None]:
        """Automatically fill the next file chooser opened inside the block.

        Subscribes to input.fileDialogOpened; when a file dialog opens (e.g. a
        click on an ``<input type=file>``), sets the given files on the
        originating element via input.setFiles, the real, trusted upload path
        (mirrors the CDP expect_file_chooser).

        Args:
            files: File path(s) to upload.
        """
        file_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]

        async def event_handler(event: dict) -> None:
            element = event.get('params', {}).get('element')
            if element is None:
                logger.warning('File dialog opened without an element reference; cannot set files')
                return
            await self._execute_command(
                BiDiInputCommands.set_files(
                    context=self._context_id,
                    element=SharedReference(sharedId=element['sharedId']),
                    files=file_list,
                )
            )

        callback_id = await self.on(Event.FILE_CHOOSER_OPENED, event_handler)
        try:
            yield
        finally:
            await self.remove_callback(callback_id)

    @asynccontextmanager
    async def expect_download(
        self,
        keep_file_at: str | Path | None = None,
        timeout: float | None = None,
    ) -> AsyncGenerator[BiDiDownloadHandle, None]:
        """Capture a file download triggered inside the block (mirrors the CDP API).

        Routes downloads to a directory and yields a handle to await completion
        and read the file. BiDi reports the saved path directly on
        browsingContext.downloadEnd, so no progress polling is needed.

        Args:
            keep_file_at: Directory to persist the file. If None, a temporary
                directory is used and removed when the block exits.
            timeout: Max seconds to wait for the download to finish (default 60).

        Yields:
            BiDiDownloadHandle: reads the downloaded file (bytes/base64) and its path.
        """
        download_timeout = 60.0 if timeout is None else float(timeout)

        cleanup_dir = False
        if keep_file_at is None:
            download_dir = mkdtemp(prefix='pydoll-download-')
            cleanup_dir = True
        else:
            download_dir = str(Path(keep_file_at))
            Path(download_dir).mkdir(parents=True, exist_ok=True)

        logger.info('Expecting download (dir=%s, timeout=%ss)', download_dir, download_timeout)
        await self._execute_command(
            BrowserCommands.set_download_behavior(
                download_behavior=DownloadBehaviorAllowed(
                    type='allowed', destinationFolder=download_dir
                )
            )
        )

        loop = asyncio.get_running_loop()
        will_begin: asyncio.Future[bool] = loop.create_future()
        done: asyncio.Future[bool] = loop.create_future()
        state: dict[str, str | None] = {
            'url': None,
            'suggestedFilename': None,
            'filePath': None,
        }

        async def on_will_begin(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id:
                return
            state['url'] = params.get('url')
            state['suggestedFilename'] = params.get('suggestedFilename')
            if not will_begin.done():
                will_begin.set_result(True)
            logger.info(
                'Download will begin: url=%s, filename=%s', state['url'], state['suggestedFilename']
            )

        async def on_end(event: dict) -> None:
            params = event['params']
            if params.get('context') != self._context_id or params.get('status') != 'complete':
                return
            file_path = params.get('filepath')
            suggested = state.get('suggestedFilename')
            if not file_path and suggested:
                file_path = str(Path(download_dir) / suggested)
            state['filePath'] = file_path
            if not done.done():
                done.set_result(True)
            logger.info('Download completed: %s', file_path)

        cb_will_begin = await self.on(Event.DOWNLOAD_STARTED, on_will_begin)
        cb_end = await self.on(Event.DOWNLOAD_COMPLETED, on_end)

        handle = BiDiDownloadHandle(
            state=state,
            will_begin_future=will_begin,
            done_future=done,
            timeout=download_timeout,
        )

        try:
            yield handle
            try:
                await asyncio.wait_for(done, timeout=download_timeout)
            except asyncio.TimeoutError as exc:
                raise DownloadTimeout() from exc
        finally:
            await self._cleanup_download_context(
                [cb_will_begin, cb_end], cleanup_dir, state, download_dir
            )

    async def _cleanup_download_context(
        self,
        callback_ids: list[int],
        cleanup_dir: bool,
        state: dict[str, str | None],
        download_dir: str,
    ) -> None:
        for callback_id in callback_ids:
            await self.remove_callback(callback_id)
        await self._execute_command(BrowserCommands.set_download_behavior(download_behavior=None))
        if cleanup_dir:
            file_path = state['filePath']
            if file_path:
                Path(file_path).unlink(missing_ok=True)
            shutil.rmtree(download_dir, ignore_errors=True)

    @property
    def network_logs(self) -> list:
        """Access captured network logs."""
        return self._connection_handler.network_logs

    async def find_shadow_roots(
        self, deep: bool = False, timeout: float = 0
    ) -> list[BiDiShadowRoot]:
        """Find every shadow root in the page, open and closed (nested included).

        Serializes the document subtree with includeShadowTree='all' (which reaches
        closed roots, like CDP's pierce) and wraps each shadow root as a
        BiDiShadowRoot. Mirrors the CDP Tab.find_shadow_roots.

        Args:
            deep: If True, also walks the child browsing contexts (iframes, cross-origin
                included) and returns their shadow roots, each bound to its own context.
            timeout: Maximum seconds to wait for shadow roots to appear. When > 0,
                polls (starting every 20 ms and backing off to 250 ms) until at
                least one shadow root is found or the timeout expires.

        Raises:
            WaitElementTimeout: If timeout > 0 and no shadow roots are found in time.
        """
        from pydoll.elements.bidi.shadow_root import BiDiShadowRoot  # noqa: PLC0415

        loop = asyncio.get_running_loop()
        start = loop.time()
        interval = PollInterval()
        while True:
            collected = await self._collect_shadow_roots(deep)
            if collected or not timeout:
                return [
                    BiDiShadowRoot(
                        shadow_root_id=shared_id,
                        context_id=context_id,
                        connection=self._connection_handler,
                        mode=mode or 'open',
                        mouse=self._mouse,
                    )
                    for context_id, shared_id, mode in collected
                ]
            if loop.time() - start > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow roots in page'
                )
            await interval.wait()

    async def _collect_shadow_roots(self, deep: bool) -> list[tuple[str, str, str | None]]:
        """Collect (context, sharedId, mode) of every shadow root in this context.

        With ``deep`` the child browsing contexts are walked too.
        """
        contexts = [self._context_id]
        if deep:
            contexts.extend(await self._descendant_contexts())
        roots: list[tuple[str, str, str | None]] = []
        for context_id in contexts:
            response = await self._execute_command(
                BrowsingContextCommands.locate_nodes(
                    context=context_id,
                    locator={'type': 'css', 'value': 'body'},
                    max_node_count=1,
                    serialization_options={'includeShadowTree': 'all', 'maxDomDepth': None},
                )
            )
            nodes = response['result']['nodes']
            if nodes:
                self._walk_shadow_roots(context_id, nodes[0], roots)
        return roots

    async def _descendant_contexts(self) -> list[str]:
        """Ids of every browsing context nested under this one (iframes, any depth).

        Firefox refuses to describe a privileged page (``about:home`` and friends)
        without system access; such a page has no content frames, so that answer
        is an empty list.
        """
        try:
            response = await self._execute_command(
                BrowsingContextCommands.get_tree(root=self._context_id)
            )
        except CommandFailed:
            return []
        descendants: list[str] = []

        def walk(info: Info) -> None:
            for child in info.get('children') or []:
                descendants.append(child['context'])
                walk(child)

        for info in response['result'].get('contexts', []):
            walk(info)
        return descendants

    @staticmethod
    def _walk_shadow_roots(
        context_id: str, node: NodeRemoteValue, out: list[tuple[str, str, str | None]]
    ) -> None:
        """Recursively collect the shadow roots in a serialized node tree."""
        value = node.get('value')
        if value is None:
            return
        shadow = value.get('shadowRoot')
        if shadow:
            shadow_props = shadow.get('value')
            mode = shadow_props.get('mode') if shadow_props else None
            out.append((context_id, shadow.get('sharedId', ''), mode))
            BiDiTab._walk_shadow_roots(context_id, shadow, out)
        for child in value.get('children') or []:
            BiDiTab._walk_shadow_roots(context_id, child, out)

    @overload
    async def on(
        self,
        event_name: Event | str,
        callback: Callable[[Any], Any],
        temporary: bool = False,
    ) -> int: ...

    @overload
    async def on(
        self,
        event_name: Event | str,
        callback: Callable[[Any], Awaitable[Any]],
        temporary: bool = False,
    ) -> int: ...

    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """Register event listener on this tab.

        Subscribes this browsing context (and, per the BiDi spec, its frames) to
        the event and registers the callback; portable ``Event`` members are
        translated to their BiDi names.

        Args:
            event_name: Event enum or native BiDi event name.
            callback: Function called on event (sync or async).
            temporary: Remove after first invocation.

        Returns:
            Callback ID for removal.

        Raises:
            CommandFailed: On a privileged page (``about:home`` and friends), which
                Firefox refuses to subscribe without system access.
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

    async def execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        """Send a raw WebDriver BiDi command and return its typed result.

        Escape hatch for BiDi features not covered by the portable API. Build the
        command with the ``pydoll.commands.bidi.*`` builders.

        Raises:
            CommandFailed: If Firefox answers the command with an error.
        """
        return await self._connection_handler.execute_command(command, timeout)

    async def _execute_command(
        self,
        command: Command[T_CommandParams, T_CommandResult],
        timeout: int = 60,
    ) -> T_CommandResult:
        return await self.execute_command(command, timeout)

    async def _evaluate_js(self, expression: str) -> object:
        """Evaluate a JavaScript expression and return its deserialized value."""
        response = await self._execute_command(
            ScriptCommands.evaluate(
                expression=expression,
                target=ContextTarget(context=self._context_id),
                await_promise=False,
            )
        )
        result = response['result']
        if result['type'] == 'success':
            return self._deserialize_remote_value(result['result'])
        return None

    @staticmethod
    def _deserialize_remote_value(  # noqa: PLR0911, PLR0912
        remote_value: Mapping[str, object],
    ) -> object:
        """Convert a BiDi RemoteValue to a Python value."""
        value_type = remote_value.get('type')
        value = remote_value.get('value')

        if value_type in {'undefined', 'null'}:
            return None
        if value_type in {'string', 'boolean'}:
            return value
        if value_type == 'number':
            if value == 'NaN':
                return float('nan')
            if value == '-0':
                return -0.0
            if value == 'Infinity':
                return float('inf')
            if value == '-Infinity':
                return float('-inf')
            return value
        if value_type == 'bigint':
            return int(value) if isinstance(value, (str, int)) else 0
        if value_type in {'array', 'set'}:
            return [
                BiDiTab._deserialize_remote_value(item)
                for item in (value if isinstance(value, list) else [])
                if isinstance(item, Mapping)
            ]
        if value_type in {'object', 'map'}:
            return BiDiTab._deserialize_remote_pairs(value)
        if value_type == 'date':
            return value
        if value_type == 'regexp':
            pattern = value.get('pattern', '') if isinstance(value, Mapping) else ''
            flags = value.get('flags', '') if isinstance(value, Mapping) else ''
            return f'/{pattern}/{flags}'
        if value_type == 'node':
            return remote_value
        return value if 'value' in remote_value else remote_value

    @staticmethod
    def _deserialize_remote_pairs(value: object) -> dict[object, object]:
        """Deserialize a BiDi object/map value (a list of ``[key, value]`` pairs)."""
        result: dict[object, object] = {}
        if not isinstance(value, list):
            return result
        key_value_size = 2
        for pair in value:
            if not isinstance(pair, (list, tuple)) or len(pair) != key_value_size:
                continue
            raw_key, raw_value = pair
            key = (
                raw_key
                if isinstance(raw_key, str)
                else BiDiTab._deserialize_remote_value(raw_key)
                if isinstance(raw_key, Mapping)
                else raw_key
            )
            result[key] = (
                BiDiTab._deserialize_remote_value(raw_value)
                if isinstance(raw_value, Mapping)
                else raw_value
            )
        return result


def _exception_text(details: Mapping[str, Any]) -> str:
    """The error text of a BiDi ExceptionDetails (``ReferenceError: x is not defined``)."""
    text = details.get('text')
    if text:
        return str(text).split('\n', 1)[0]
    exception = details.get('exception') or {}
    return str(exception.get('value', 'Uncaught'))


def _remote_value_is_truthy(remote: Mapping[str, object]) -> bool:
    """JavaScript truthiness of a serialized BiDi RemoteValue.

    Primitives carry ``value`` (numbers may travel as the strings ``'NaN'``,
    ``'-0'`` and the infinities); anything else (object, array, node, function,
    symbol, date, regexp) is truthy.
    """
    value_type = remote.get('type')
    value = remote.get('value')
    if value_type in {'undefined', 'null'}:
        return False
    if value_type in {'boolean', 'string'}:
        return bool(value)
    if value_type == 'number':
        return value not in _FALSY_NUMBERS
    if value_type == 'bigint':
        return value not in {'0', 0}
    return True


def _event_request_id(params_or_event: Mapping[str, Any]) -> str:
    """The request id of a BiDi network event (or of its ``params``)."""
    params = params_or_event.get('params', params_or_event)
    return str(params.get('request', {}).get('request', ''))


def _headers_to_dict(headers: list[dict]) -> dict[str, str]:
    """Flatten a BiDi header list (unwrapping each BytesValue) into a dict."""
    result: dict[str, str] = {}
    for header in headers:
        value = header.get('value')
        if isinstance(value, dict):
            value = value.get('value', '')
        result[header.get('name', '')] = str(value) if value is not None else ''
    return result


class BiDiDownloadHandle:
    """Handle returned by BiDiTab.expect_download to access the downloaded file."""

    def __init__(
        self,
        state: dict[str, str | None],
        will_begin_future: asyncio.Future[bool],
        done_future: asyncio.Future[bool],
        timeout: float,
    ) -> None:
        self._state = state
        self._will_begin_future = will_begin_future
        self._done_future = done_future
        self._timeout = timeout

    @property
    def file_path(self) -> str | None:
        return self._state.get('filePath')

    async def wait_started(self, timeout: float | None = None) -> None:
        await asyncio.wait_for(self._will_begin_future, timeout=timeout or self._timeout)

    async def wait_finished(self, timeout: float | None = None) -> None:
        await asyncio.wait_for(self._done_future, timeout=timeout or self._timeout)

    async def read_bytes(self) -> bytes:
        await self.wait_finished()
        file_path = self.file_path
        if not file_path:
            raise FileNotFoundError('Download file path not available')
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()

    async def read_base64(self) -> str:
        data = await self.read_bytes()
        return _b64.b64encode(data).decode('ascii')


class BiDiRequestHandle:
    """What ``BiDiTab.expect_request()`` captured: filled when its block exits."""

    def __init__(self) -> None:
        self._params: dict | None = None

    def _fill(self, params: dict) -> None:
        self._params = params

    @property
    def _request(self) -> dict:
        if self._params is None:
            raise WaitTimeout('The request has not been captured yet; read it after the block')
        return self._params['request']

    @property
    def request_id(self) -> str:
        """BiDi request id, usable with ``tab.get_network_response_body()``."""
        return self._request['request']

    @property
    def url(self) -> str:
        return self._request['url']

    @property
    def method(self) -> str:
        return self._request['method']

    @property
    def headers(self) -> dict[str, str]:
        return _headers_to_dict(self._request.get('headers', []))

    @property
    def post_data(self) -> str | None:
        """Always None: WebDriver BiDi does not expose request bodies."""
        self._request
        return None

    @property
    def resource_type(self) -> str | None:
        """The request destination (``document``, ``script``, ``image``, ...) or initiator type."""
        request = self._request
        return request.get('destination') or request.get('initiatorType') or None


class BiDiResponseHandle:
    """What ``BiDiTab.expect_response()`` captured: filled, body included, when its block exits."""

    def __init__(self) -> None:
        self._params: dict | None = None
        self._body: bytes | None = None

    def _fill(self, params: dict, body: bytes | None) -> None:
        self._params = params
        self._body = body

    @property
    def _response(self) -> dict:
        if self._params is None:
            raise WaitTimeout('The response has not been captured yet; read it after the block')
        return self._params.get('response') or {}

    @property
    def request_id(self) -> str:
        if self._params is None:
            raise WaitTimeout('The response has not been captured yet; read it after the block')
        return _event_request_id(self._params)

    @property
    def url(self) -> str:
        return self._response.get('url', '')

    @property
    def status(self) -> int:
        return int(self._response.get('status', 0))

    @property
    def ok(self) -> bool:
        """True for a 2xx status."""
        return self.status in _SUCCESS_STATUSES

    @property
    def headers(self) -> dict[str, str]:
        return _headers_to_dict(self._response.get('headers', []))

    @property
    def mime_type(self) -> str:
        return self._response.get('mimeType', '')

    def body(self) -> bytes:
        """The raw body, empty for a 204, 205 or 304.

        Raises when loading failed, so there was no body to read.
        """
        if self._body is None:
            self._response
            raise WaitTimeout('The response body was not received (the request failed)')
        return self._body

    def text(self, encoding: str = 'utf-8') -> str:
        return self.body().decode(encoding, errors='replace')

    def json(self) -> Any:
        return json.loads(self.text())
