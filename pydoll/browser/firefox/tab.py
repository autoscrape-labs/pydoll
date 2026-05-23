from __future__ import annotations

import asyncio
import base64 as _b64
import logging
import shutil
from collections.abc import Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Optional, Union, overload

import aiofiles

from pydoll.browser.requests.bidi.request import BiDiRequest
from pydoll.commands.bidi.browser_commands import BrowserCommands
from pydoll.commands.bidi.browsing_context_commands import BrowsingContextCommands
from pydoll.commands.bidi.emulation_commands import EmulationCommands
from pydoll.commands.bidi.input_commands import InputCommands as BiDiInputCommands
from pydoll.commands.bidi.script_commands import ScriptCommands
from pydoll.commands.bidi.session_commands import SessionCommands
from pydoll.commands.bidi.storage_commands import StorageCommands
from pydoll.connection.bidi_connection_handler import BiDiConnectionHandler
from pydoll.elements.mixins.bidi_find_elements_mixin import BidiFindElementsMixin
from pydoll.exceptions import DownloadTimeout, ScriptExecutionError
from pydoll.interactions.keyboard import BiDiKeyboard
from pydoll.interactions.mouse import BiDiMouse
from pydoll.interactions.scroll import BiDiScroll
from pydoll.protocol.bidi.base import Command, T_CommandParams, T_CommandResult
from pydoll.protocol.bidi.browser.types import DownloadBehaviorAllowed
from pydoll.protocol.bidi.browsing_context.types import ImageFormat, ReadinessState
from pydoll.protocol.bidi.network.types import Cookie as BiDiCookie
from pydoll.protocol.bidi.network.types import SameSite, StringValue
from pydoll.protocol.bidi.script.types import ContextTarget, NodeRemoteValue, SharedReference
from pydoll.protocol.bidi.storage.types import BrowsingContextPartitionDescriptor, PartialCookie
from pydoll.protocol.events import BIDI_EVENT_MAP, Event
from pydoll.protocol.types import Cookie, CookieParam
from pydoll.utils import has_return_outside_function

if TYPE_CHECKING:
    from typing import Any, AsyncGenerator, Awaitable, Callable

    from pydoll.elements.bidi.shadow_root import BiDiShadowRoot

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
        self._mouse: BiDiMouse = BiDiMouse(self)
        self._keyboard: Optional[BiDiKeyboard] = None
        self._scroll: Optional[BiDiScroll] = None
        self._request: Optional[BiDiRequest] = None

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
    async def current_url(self) -> str:
        """Get the current page URL."""
        return str(await self._evaluate_js('location.href') or '')

    @property
    async def page_source(self) -> str:
        """Get the HTML source of the current page."""
        return str(await self._evaluate_js('document.documentElement.outerHTML') or '')

    @property
    async def title(self) -> str:
        """Get the current page title."""
        return str(await self._evaluate_js('document.title') or '')

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
                wait=ReadinessState.COMPLETE,
            ),
            timeout=timeout,
        )

    async def refresh(self, ignore_cache: bool = False):
        """Reload the current page."""
        await self._execute_command(
            BrowsingContextCommands.reload(
                context=self._context_id,
                ignore_cache=ignore_cache,
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
        path: Optional[Union[str, Path]] = None,
        quality: int = 100,
        beyond_viewport: bool = False,
        as_base64: bool = False,
    ) -> Optional[str]:
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
        data = response['result']['data']

        if as_base64:
            return data

        if path:
            async with aiofiles.open(str(path), 'wb') as f:
                await f.write(_b64.b64decode(data))

        return None

    async def print_to_pdf(
        self,
        path: Optional[Union[str, Path]] = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
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
        data = response['result']['data']

        if as_base64:
            return data

        if path:
            async with aiofiles.open(str(path), 'wb') as f:
                await f.write(_b64.b64decode(data))

        return None

    async def execute_script(self, script: str, *args: object) -> object:
        """Execute JavaScript in this tab and return its deserialized result.

        Args:
            script: JavaScript to run. With args, pass a function expression
                (e.g. ``(a, b) => a + b``) — the args are forwarded to it.
            *args: values forwarded to the script function.

        Returns:
            The script's return value as a Python object.

        Raises:
            ScriptExecutionError: If the script throws.
        """
        target = ContextTarget(context=self._context_id)
        if args:
            response = await self._execute_command(
                ScriptCommands.call_function(
                    function_declaration=script,
                    await_promise=True,
                    target=target,
                    arguments=[self._to_local_value(arg) for arg in args],
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
                )
            )
        result = response['result']
        if result['type'] == 'exception':
            raise ScriptExecutionError(result['exceptionDetails']['text'])
        return self._deserialize_remote_value(result['result'])

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

    async def get_cookies(self) -> list[Cookie]:
        """Get all cookies for this tab's context."""
        partition = BrowsingContextPartitionDescriptor(type='context', context=self._context_id)
        response = await self._execute_command(StorageCommands.get_cookies(partition=partition))
        return [self._to_generic_cookie(c) for c in response['result']['cookies']]

    @staticmethod
    def _to_generic_cookie(cookie: BiDiCookie) -> Cookie:
        """Convert a BiDi cookie to the protocol-agnostic Cookie type."""
        result = Cookie(
            name=cookie['name'],
            value=cookie['value'].get('value', ''),
            domain=cookie['domain'],
            path=cookie['path'],
            size=cookie['size'],
            httpOnly=cookie['httpOnly'],
            secure=cookie['secure'],
            sameSite=cookie['sameSite'],
        )
        if 'expiry' in cookie:
            result['expiry'] = cookie['expiry']
        return result

    async def set_cookies(self, cookies: list[CookieParam]):
        """Set cookies for this tab's context."""
        partition = BrowsingContextPartitionDescriptor(type='context', context=self._context_id)
        for cookie in cookies:
            bidi_cookie = PartialCookie(
                name=cookie['name'],
                value=StringValue(type='string', value=cookie['value']),
                domain=cookie['domain'],
            )
            if 'path' in cookie:
                bidi_cookie['path'] = cookie['path']
            if 'httpOnly' in cookie:
                bidi_cookie['httpOnly'] = cookie['httpOnly']
            if 'secure' in cookie:
                bidi_cookie['secure'] = cookie['secure']
            if 'expiry' in cookie:
                bidi_cookie['expiry'] = cookie['expiry']
            if 'sameSite' in cookie:
                bidi_cookie['sameSite'] = SameSite(cookie['sameSite'].lower())
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

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: Union[str, Path, list[Union[str, Path]]]
    ) -> AsyncGenerator[None, None]:
        """Automatically fill the next file chooser opened inside the block.

        Subscribes to input.fileDialogOpened; when a file dialog opens (e.g. a
        click on an ``<input type=file>``), sets the given files on the
        originating element via input.setFiles — the real, trusted upload path
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
        keep_file_at: Optional[Union[str, Path]] = None,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[_BiDiDownloadHandle, None]:
        """Capture a file download triggered inside the block (mirrors the CDP API).

        Routes downloads to a directory and yields a handle to await completion
        and read the file. BiDi reports the saved path directly on
        browsingContext.downloadEnd, so no progress polling is needed.

        Args:
            keep_file_at: Directory to persist the file. If None, a temporary
                directory is used and removed when the block exits.
            timeout: Max seconds to wait for the download to finish (default 60).

        Yields:
            _BiDiDownloadHandle: reads the downloaded file (bytes/base64) and its path.
        """
        download_timeout = 60.0 if timeout is None else float(timeout)

        cleanup_dir = False
        if keep_file_at is None:
            download_dir = mkdtemp(prefix='pydoll-download-')
            cleanup_dir = True
        else:
            download_dir = str(Path(keep_file_at))
            Path(download_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f'Expecting download (dir={download_dir}, timeout={download_timeout}s)')
        await self._execute_command(
            BrowserCommands.set_download_behavior(
                download_behavior=DownloadBehaviorAllowed(
                    type='allowed', destinationFolder=download_dir
                )
            )
        )

        loop = asyncio.get_event_loop()
        will_begin: asyncio.Future[bool] = loop.create_future()
        done: asyncio.Future[bool] = loop.create_future()
        state: dict[str, Optional[str]] = {
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
                f'Download will begin: url={state["url"]}, filename={state["suggestedFilename"]}'
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
            logger.info(f'Download completed: {file_path}')

        cb_will_begin = await self.on(Event.DOWNLOAD_STARTED, on_will_begin)
        cb_end = await self.on(Event.DOWNLOAD_COMPLETED, on_end)

        handle = _BiDiDownloadHandle(
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
        state: dict[str, Optional[str]],
        download_dir: str,
    ) -> None:
        for callback_id in callback_ids:
            await self.remove_callback(callback_id)
        await self._execute_command(
            BrowserCommands.set_download_behavior(download_behavior=None)
        )
        if cleanup_dir:
            file_path = state['filePath']
            if file_path:
                Path(file_path).unlink(missing_ok=True)
            shutil.rmtree(download_dir, ignore_errors=True)

    @property
    def network_logs(self) -> list:
        """Access captured network logs."""
        return self._connection_handler.network_logs

    async def find_shadow_roots(self, timeout: float = 0) -> list[BiDiShadowRoot]:
        """Find every shadow root in the page, open and closed (nested included).

        Serializes the document subtree with includeShadowTree='all' (which reaches
        closed roots, like CDP's pierce) and wraps each shadow root as a
        BiDiShadowRoot. Mirrors the CDP Tab.find_shadow_roots.

        Args:
            timeout: Seconds to poll for shadow roots to appear (0 = single scan).
        """
        from pydoll.elements.bidi.shadow_root import BiDiShadowRoot  # noqa: PLC0415

        start = asyncio.get_event_loop().time()
        while True:
            collected = await self._collect_shadow_roots()
            if collected or not timeout:
                return [
                    BiDiShadowRoot(
                        shadow_root_id=shared_id,
                        context_id=self._context_id,
                        connection=self._connection_handler,
                        mode=mode or 'open',
                        mouse=self._mouse,
                    )
                    for shared_id, mode in collected
                ]
            if asyncio.get_event_loop().time() - start > timeout:
                return []
            await asyncio.sleep(0.5)

    async def _collect_shadow_roots(self) -> list[tuple[str, Optional[str]]]:
        """Serialize the body subtree (including closed shadow trees) and collect roots."""
        response = await self._execute_command(
            BrowsingContextCommands.locate_nodes(
                context=self._context_id,
                locator={'type': 'css', 'value': 'body'},
                max_node_count=1,
                serialization_options={'includeShadowTree': 'all', 'maxDomDepth': None},
            )
        )
        nodes = response['result']['nodes']
        roots: list[tuple[str, Optional[str]]] = []
        if nodes:
            self._walk_shadow_roots(nodes[0], roots)
        return roots

    @staticmethod
    def _walk_shadow_roots(node: NodeRemoteValue, out: list[tuple[str, Optional[str]]]) -> None:
        """Recursively collect (sharedId, mode) of every shadow root in a serialized tree."""
        value = node.get('value')
        if value is None:
            return
        shadow = value.get('shadowRoot')
        if shadow:
            shadow_props = shadow.get('value')
            mode = shadow_props.get('mode') if shadow_props else None
            out.append((shadow.get('sharedId', ''), mode))
            BiDiTab._walk_shadow_roots(shadow, out)
        for child in value.get('children') or []:
            BiDiTab._walk_shadow_roots(child, out)

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


class _BiDiDownloadHandle:
    """Handle returned by BiDiTab.expect_download to access the downloaded file."""

    def __init__(
        self,
        state: dict[str, Optional[str]],
        will_begin_future: asyncio.Future[bool],
        done_future: asyncio.Future[bool],
        timeout: float,
    ) -> None:
        self._state = state
        self._will_begin_future = will_begin_future
        self._done_future = done_future
        self._timeout = timeout

    @property
    def file_path(self) -> Optional[str]:
        return self._state.get('filePath')

    async def wait_started(self, timeout: Optional[float] = None) -> None:
        await asyncio.wait_for(self._will_begin_future, timeout=timeout or self._timeout)

    async def wait_finished(self, timeout: Optional[float] = None) -> None:
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
