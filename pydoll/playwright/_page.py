"""Page: one tab, wrapping a pydoll Tab with Playwright's surface."""

from __future__ import annotations

import asyncio
import base64
import inspect
import json
import logging
import secrets
import weakref
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Sequence

from pydoll.browser.tab import Tab
from pydoll.commands import DomCommands, EmulationCommands, PageCommands, RuntimeCommands
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import PydollException
from pydoll.playwright._dialog import ConsoleMessage, Dialog, Download, FileChooser
from pydoll.playwright._element_handle import ElementHandle, JSHandle
from pydoll.playwright._errors import Error, TargetClosedError, translate
from pydoll.playwright._events import (
    Deadline,
    EventContextManager,
    EventEmitter,
    create_future,
    schedule,
)
from pydoll.playwright._frame import Frame
from pydoll.playwright._glob import URLMatch
from pydoll.playwright._input import Keyboard, Mouse, Touchscreen
from pydoll.playwright._locator import FrameLocator, Locator
from pydoll.playwright._navigation import NavigationTracker
from pydoll.playwright._network import (
    NetworkManager,
    Request,
    Response,
    RouteEntry,
    RouteHandler,
    Router,
    make_entry,
    wait_for_matching,
)
from pydoll.playwright._selectors import TextMatch
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.runtime.events import RuntimeEvent

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydoll.playwright._browser_context import BrowserContext

_EXPOSE_SOURCE = """
(() => {
  const name = %s;
  if (globalThis[name]) return;
  const pending = (globalThis.__pydoll_pending__ = globalThis.__pydoll_pending__ || new Map());
  let seq = 0;
  globalThis.__pydoll_deliver__ = globalThis.__pydoll_deliver__
    || ((bindingName, id, result, error) => {
    const entry = pending.get(bindingName + ':' + id);
    if (!entry) return;
    pending.delete(bindingName + ':' + id);
    error ? entry.reject(new Error(error)) : entry.resolve(result);
  });
  globalThis[name] = (...args) => {
    const id = ++seq;
    const promise = new Promise(
      (resolve, reject) => pending.set(name + ':' + id, { resolve, reject }));
    globalThis[name + '__binding__'](JSON.stringify({ id, args }));
    return promise;
  };
})();
"""


class Page(EventEmitter):
    """A single tab of a browser context."""

    def __init__(self, context: BrowserContext, tab: Tab, opener: Page | None = None) -> None:
        super().__init__()
        self._context = context
        self._tab = tab
        self._opener = opener
        self._closed = False
        self._url = ''
        self._main_frame = Frame(self, tab)
        self._main_frame_id_cache: str | None = None
        self._frames_by_id: dict[str, Frame] = {}
        self._element_frames: weakref.WeakKeyDictionary[WebElement, Frame] = (
            weakref.WeakKeyDictionary()
        )
        self._navigation = NavigationTracker(self)
        self._network = NetworkManager(self)
        self._router = Router(self)
        self._routes: list[RouteEntry] = []
        self._keyboard = Keyboard(self)
        self._mouse = Mouse(self)
        self._touchscreen = Touchscreen(self)
        self._default_timeout: float | None = None
        self._default_navigation_timeout: float | None = None
        self._viewport: dict[str, int] | None = None
        self._user_gesture = bool(context._options.get('user_gesture_on_evaluate', False))
        self._world_name = f'w{secrets.token_hex(4)}'
        self._fetch_enabled = False
        self._fetch_handles_auth = False
        self._runtime_enabled = False
        self._file_chooser_enabled = False
        self._bindings: dict[str, tuple[Callable[..., Any], bool]] = {}
        self._downloads: dict[str, Download] = {}
        self._callback_ids: list[int] = []
        self._workers: list[Any] = []
        self._loop = asyncio.get_running_loop()
        self._close_future: asyncio.Future[None] = self._loop.create_future()

    def __repr__(self) -> str:
        return f'<Page url={self._url!r}>'

    # ------------------------------------------------------------ setup

    async def _initialize(self) -> None:
        await self._tab.enable_page_events()
        await self._send(PageCommands.set_lifecycle_events_enabled(True))
        await self._tab.enable_network_events()
        await self._main_frame_id()
        await self._listen(
            PageEvent.LIFECYCLE_EVENT, lambda e: self._navigation.on_lifecycle(e['params'])
        )
        await self._listen(
            PageEvent.FRAME_NAVIGATED, lambda e: self._navigation.on_frame_navigated(e['params'])
        )
        await self._listen(
            PageEvent.NAVIGATED_WITHIN_DOCUMENT,
            lambda e: self._navigation.on_navigated_within_document(e['params']),
        )
        await self._listen(PageEvent.FRAME_ATTACHED, self._on_frame_attached)
        await self._listen(PageEvent.FRAME_DETACHED, self._on_frame_detached)
        await self._listen(PageEvent.JAVASCRIPT_DIALOG_OPENING, self._on_dialog)
        await self._listen(PageEvent.DOWNLOAD_WILL_BEGIN, self._on_download_will_begin)
        await self._listen(PageEvent.DOWNLOAD_PROGRESS, self._on_download_progress)
        await self._listen(PageEvent.FILE_CHOOSER_OPENED, self._on_file_chooser)
        await self._listen(
            NetworkEvent.REQUEST_WILL_BE_SENT,
            lambda e: self._network.on_request_will_be_sent(e['params']),
        )
        await self._listen(
            NetworkEvent.RESPONSE_RECEIVED,
            lambda e: self._network.on_response_received(e['params']),
        )
        await self._listen(
            NetworkEvent.LOADING_FINISHED, lambda e: self._network.on_loading_finished(e['params'])
        )
        await self._listen(
            NetworkEvent.LOADING_FAILED, lambda e: self._network.on_loading_failed(e['params'])
        )
        await self._listen('Inspector.targetCrashed', lambda e: self.emit('crash', self))
        await self._context._apply_to_page(self)

    async def _listen(self, event: Any, callback: Callable[[dict[str, Any]], Any]) -> None:
        callback_id = await self._tab.on(event, callback)
        self._callback_ids.append(callback_id)

    async def _main_frame_id(self) -> str:
        if self._main_frame_id_cache is None:
            response = await self._send(PageCommands.get_frame_tree())
            frame = response['result']['frameTree']['frame']
            self._main_frame_id_cache = frame['id']
            self._main_frame._frame_id = frame['id']
            self._url = frame.get('url', '')
            self._navigation._state(frame['id']).url = self._url
            self._navigation._state(frame['id']).loader_id = frame.get('loaderId', '')
        return self._main_frame_id_cache

    async def _send(self, command: Any) -> Any:
        try:
            return await self._tab.execute_command(command)
        except PydollException as error:
            raise translate(error) from error

    def _timeout(self, timeout: float | None) -> float:
        if timeout is not None:
            return timeout
        if self._default_timeout is not None:
            return self._default_timeout
        return self._context._default_timeout_value()

    def _navigation_timeout(self, timeout: float | None) -> float:
        if timeout is not None:
            return timeout
        if self._default_navigation_timeout is not None:
            return self._default_navigation_timeout
        if self._default_timeout is not None:
            return self._default_timeout
        return self._context._default_navigation_timeout_value()

    # ------------------------------------------------------------ frames

    def _frame_for_id(self, frame_id: str) -> Frame:
        if frame_id == self._main_frame_id_cache or not frame_id:
            return self._main_frame
        frame = self._frames_by_id.get(frame_id)
        if frame is None:
            frame = Frame(self, self._tab, parent=self._main_frame)
            frame._frame_id = frame_id
            frame._url = self._navigation._state(frame_id).url
            self._frames_by_id[frame_id] = frame
            asyncio.ensure_future(self._resolve_frame(frame_id))
        return frame

    async def _canonical_frame(self, candidate: Frame) -> Frame:
        """Reuse the Frame already known for ``candidate``'s id, adopting its fresh root."""
        frame_id = await candidate._frame_id_value()
        if frame_id == self._main_frame_id_cache:
            return self._main_frame
        existing = self._frames_by_id.get(frame_id)
        if existing is None:
            self._frames_by_id[frame_id] = candidate
            return candidate
        existing._root = candidate._root
        existing._parent = candidate._parent
        if candidate._name:
            existing._name = candidate._name
        return existing

    def _child_frames_of(self, parent: Frame) -> list[Frame]:
        return [
            frame
            for frame in self._frames_by_id.values()
            if frame._parent is parent and not frame._detached
        ]

    def _on_frame_attached(self, event: dict[str, Any]) -> None:
        params = event['params']
        self._frame_for_id(params['frameId'])
        self._navigation.on_frame_attached(params)

    def _on_frame_detached(self, event: dict[str, Any]) -> None:
        params = event['params']
        frame = self._frames_by_id.pop(params['frameId'], None)
        if frame is not None:
            frame._detached = True
        self._navigation.on_frame_detached(params)

    async def _resolve_frame(self, frame_id: str) -> None:
        try:
            owner = await self._send(DomCommands.get_frame_owner(frame_id=frame_id))
            backend_node_id = owner['result'].get('backendNodeId')
            if backend_node_id is None:
                return
            resolved = await self._send(DomCommands.resolve_node(backend_node_id=backend_node_id))
            element = await self._main_frame._element_from_object_id(
                resolved['result']['object']['objectId']
            )
            frame = self._frames_by_id.get(frame_id)
            if frame is None:
                return
            frame._root = element
            frame._name = element.get_attribute('name') or ''
            parent_id = owner['result'].get('parentId')
            if parent_id:
                frame._parent = self._frame_for_id(parent_id)
        except Error:
            return

    @property
    def main_frame(self) -> Frame:
        return self._main_frame

    @property
    def frames(self) -> list[Frame]:
        return [
            self._main_frame,
            *[frame for frame in self._frames_by_id.values() if not frame._detached],
        ]

    def frame(self, name: str | None = None, url: URLMatch | None = None) -> Frame | None:
        from pydoll.playwright._glob import URLMatcher  # noqa: PLC0415

        matcher = URLMatcher(url, self._context._base_url) if url is not None else None
        for frame in self.frames:
            if name is not None and frame.name == name:
                return frame
            if matcher is not None and matcher.matches(frame.url):
                return frame
        return None

    # ------------------------------------------------------------ identity

    @property
    def context(self) -> BrowserContext:
        return self._context

    @property
    def url(self) -> str:
        return self._url

    @property
    def keyboard(self) -> Keyboard:
        return self._keyboard

    @property
    def mouse(self) -> Mouse:
        return self._mouse

    @property
    def touchscreen(self) -> Touchscreen:
        return self._touchscreen

    @property
    def viewport_size(self) -> dict[str, int] | None:
        return dict(self._viewport) if self._viewport else None

    @property
    def workers(self) -> list[Any]:
        return list(self._workers)

    @property
    def video(self) -> None:
        return None

    @property
    def request(self) -> Any:
        raise Error('page.request (APIRequestContext) is not supported by pydoll.playwright')

    @property
    def clock(self) -> Any:
        raise Error('page.clock is not supported by pydoll.playwright')

    @property
    def tab(self) -> Tab:
        """The underlying pydoll Tab, for code that mixes both APIs."""
        return self._tab

    def is_closed(self) -> bool:
        return self._closed

    async def opener(self) -> Page | None:
        return self._opener

    def set_default_timeout(self, timeout: float) -> None:
        self._default_timeout = timeout

    def set_default_navigation_timeout(self, timeout: float) -> None:
        self._default_navigation_timeout = timeout

    # ------------------------------------------------------------ events

    def on(self, event: str, listener: Callable[..., Any]) -> None:  # type: ignore[override]
        super().on(event, listener)
        self._ensure_event_source(event)

    def once(self, event: str, listener: Callable[..., Any]) -> None:  # type: ignore[override]
        super().once(event, listener)
        self._ensure_event_source(event)

    def _ensure_event_source(self, event: str) -> None:
        if event in {'console', 'pageerror'}:
            schedule(self._loop, self._enable_runtime())
        elif event == 'filechooser':
            schedule(self._loop, self._enable_file_chooser())

    async def _enable_runtime(self) -> None:
        if self._runtime_enabled or self._closed:
            return
        self._runtime_enabled = True
        await self._tab.enable_runtime_events()
        await self._listen(RuntimeEvent.CONSOLE_API_CALLED, self._on_console)
        await self._listen(RuntimeEvent.EXCEPTION_THROWN, self._on_exception)
        await self._listen(RuntimeEvent.BINDING_CALLED, self._on_binding_called)

    async def _enable_file_chooser(self) -> None:
        if self._file_chooser_enabled or self._closed:
            return
        self._file_chooser_enabled = True
        await self._tab.enable_intercept_file_chooser_dialog()

    def _on_console(self, event: dict[str, Any]) -> None:
        self.emit('console', ConsoleMessage(self, event['params']))

    def _on_exception(self, event: dict[str, Any]) -> None:
        details = event['params'].get('exceptionDetails', {})
        exception = details.get('exception', {})
        message = exception.get('description') or details.get('text') or 'Uncaught error'
        error = Error(message)
        error._name = exception.get('className')
        self.emit('pageerror', error)

    def _on_dialog(self, event: dict[str, Any]) -> None:
        dialog = Dialog(self, event['params'])
        if self.listener_count('dialog') == 0:
            asyncio.ensure_future(
                dialog.accept() if dialog.type == 'beforeunload' else dialog.dismiss()
            )
            return
        self.emit('dialog', dialog)

    def _on_download_will_begin(self, event: dict[str, Any]) -> None:
        params = event['params']
        download = Download(self, params, self._context._downloads_dir)
        self._downloads[params['guid']] = download
        self.emit('download', download)

    def _on_download_progress(self, event: dict[str, Any]) -> None:
        params = event['params']
        download = self._downloads.get(params.get('guid', ''))
        if download is not None:
            download._on_progress(params)

    def _on_file_chooser(self, event: dict[str, Any]) -> None:
        params = event['params']

        async def deliver() -> None:
            resolved = await self._send(
                DomCommands.resolve_node(backend_node_id=params['backendNodeId'])
            )
            element = await self._main_frame._element_from_object_id(
                resolved['result']['object']['objectId']
            )
            self.emit(
                'filechooser',
                FileChooser(
                    self,
                    ElementHandle(self._main_frame, element),
                    params.get('mode') == 'selectMultiple',
                ),
            )

        asyncio.ensure_future(deliver())

    def _on_binding_called(self, event: dict[str, Any]) -> None:
        params = event['params']
        name = params.get('name', '')
        if not name.endswith('__binding__'):
            return
        binding = self._bindings.get(name[: -len('__binding__')])
        if binding is None:
            return
        payload = json.loads(params.get('payload', '{}'))
        asyncio.ensure_future(
            self._run_binding(
                name[: -len('__binding__')], binding, payload, params.get('executionContextId')
            )
        )

    async def _run_binding(
        self,
        name: str,
        binding: tuple[Callable[..., Any], bool],
        payload: dict[str, Any],
        context_id: int | None,
    ) -> None:
        callback, with_source = binding
        result: Any = None
        error: str | None = None
        try:
            args = payload.get('args', [])
            if with_source:
                result = callback(
                    {'context': self._context, 'page': self, 'frame': self._main_frame}, *args
                )
            else:
                result = callback(*args)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            error = str(exc)
        await self._send(
            RuntimeCommands.evaluate(
                expression=(
                    f'globalThis.__pydoll_deliver__({json.dumps(name)}, {payload.get("id")}, '
                    f'{json.dumps(result)}, {json.dumps(error)})'
                ),
                context_id=context_id,
            )
        )

    def _on_target_closed(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._context._pages = [page for page in self._context._pages if page is not self]
        if not self._close_future.done():
            self._close_future.set_result(None)
        self.emit('close', self)

    async def wait_for_event(
        self,
        event: str,
        predicate: Callable[[Any], Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        async with self.expect_event(event, predicate=predicate, timeout=timeout) as info:
            pass
        return await info.value

    def expect_event(
        self,
        event: str,
        predicate: Callable[[Any], Any] | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[Any]:
        deadline = Deadline(self._timeout(timeout))
        future = create_future(self._loop)

        def listener(*args: Any) -> None:
            if future.done():
                return
            value = args[0] if args else None
            try:
                if predicate is not None and not predicate(value):
                    return
            except Exception as error:
                future.set_exception(error)
                return
            future.set_result(value)

        self.on(event, listener)

        async def guard() -> None:
            remaining = deadline.remaining_seconds()
            try:
                await asyncio.wait_for(
                    asyncio.shield(future), timeout=remaining
                ) if remaining is not None else await asyncio.shield(future)
            except asyncio.TimeoutError:
                if not future.done():
                    future.set_exception(deadline.error(f'waiting for event "{event}"'))
            except Exception:
                pass
            finally:
                self.remove_listener(event, listener)

        schedule(self._loop, guard())
        return EventContextManager(future)

    def expect_console_message(
        self,
        predicate: Callable[[ConsoleMessage], bool] | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[ConsoleMessage]:
        return self.expect_event('console', predicate=predicate, timeout=timeout)

    def expect_download(
        self,
        predicate: Callable[[Download], bool] | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[Download]:
        return self.expect_event('download', predicate=predicate, timeout=timeout)

    def expect_file_chooser(
        self,
        predicate: Callable[[FileChooser], bool] | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[FileChooser]:
        return self.expect_event('filechooser', predicate=predicate, timeout=timeout)

    def expect_popup(
        self, predicate: Callable[[Page], bool] | None = None, timeout: float | None = None
    ) -> EventContextManager[Page]:
        return self.expect_event('popup', predicate=predicate, timeout=timeout)

    def expect_worker(
        self, predicate: Any = None, timeout: float | None = None
    ) -> EventContextManager[Any]:
        return self.expect_event('worker', predicate=predicate, timeout=timeout)

    def expect_websocket(
        self, predicate: Any = None, timeout: float | None = None
    ) -> EventContextManager[Any]:
        return self.expect_event('websocket', predicate=predicate, timeout=timeout)

    def expect_request(
        self,
        url_or_predicate: URLMatch | Callable[[Request], Any],
        timeout: float | None = None,
    ) -> EventContextManager[Request]:
        return self._expect_network('request', url_or_predicate, timeout)

    def expect_request_finished(
        self, predicate: Callable[[Request], Any] | None = None, timeout: float | None = None
    ) -> EventContextManager[Request]:
        return self.expect_event('requestfinished', predicate=predicate, timeout=timeout)

    def expect_response(
        self,
        url_or_predicate: URLMatch | Callable[[Response], Any],
        timeout: float | None = None,
    ) -> EventContextManager[Response]:
        return self._expect_network('response', url_or_predicate, timeout)

    def _expect_network(
        self, event: str, matcher: Any, timeout: float | None
    ) -> EventContextManager[Any]:
        deadline = Deadline(self._timeout(timeout))
        future = create_future(self._loop)

        async def waiter() -> None:
            try:
                future.set_result(await wait_for_matching(self, event, matcher, deadline))
            except Exception as error:
                if not future.done():
                    future.set_exception(error)

        schedule(self._loop, waiter())
        return EventContextManager(future)

    def expect_navigation(
        self,
        url: URLMatch | None = None,
        wait_until: str | None = None,
        timeout: float | None = None,
    ) -> EventContextManager[Response | None]:
        return self._main_frame.expect_navigation(url=url, wait_until=wait_until, timeout=timeout)

    # ------------------------------------------------------------ navigation

    async def goto(
        self,
        url: str,
        timeout: float | None = None,
        wait_until: str | None = None,
        referer: str | None = None,
    ) -> Response | None:
        if self._context._base_url and not _is_absolute(url):
            from urllib.parse import urljoin  # noqa: PLC0415

            url = urljoin(self._context._base_url, url)
        return await self._main_frame.goto(
            url, timeout=timeout, wait_until=wait_until, referer=referer
        )

    async def reload(
        self, timeout: float | None = None, wait_until: str | None = None
    ) -> Response | None:
        async with self.expect_navigation(wait_until=wait_until, timeout=timeout) as info:
            await self._send(PageCommands.reload())
        return await info.value

    async def go_back(
        self, timeout: float | None = None, wait_until: str | None = None
    ) -> Response | None:
        return await self._history(-1, timeout, wait_until)

    async def go_forward(
        self, timeout: float | None = None, wait_until: str | None = None
    ) -> Response | None:
        return await self._history(1, timeout, wait_until)

    async def _history(
        self, delta: int, timeout: float | None, wait_until: str | None
    ) -> Response | None:
        history = (await self._send(PageCommands.get_navigation_history()))['result']
        index = history['currentIndex'] + delta
        entries = history['entries']
        if index < 0 or index >= len(entries):
            return None
        async with self.expect_navigation(wait_until=wait_until, timeout=timeout) as info:
            await self._send(PageCommands.navigate_to_history_entry(entry_id=entries[index]['id']))
        return await info.value

    async def wait_for_load_state(
        self, state: str | None = None, timeout: float | None = None
    ) -> None:
        await self._main_frame.wait_for_load_state(state, timeout=timeout)

    async def wait_for_url(
        self, url: URLMatch, wait_until: str | None = None, timeout: float | None = None
    ) -> None:
        await self._main_frame.wait_for_url(url, wait_until=wait_until, timeout=timeout)

    async def wait_for_timeout(self, timeout: float) -> None:
        await asyncio.sleep(timeout / 1000)

    async def wait_for_function(
        self, expression: str, arg: Any = None, timeout: float | None = None, polling: Any = None
    ) -> JSHandle:
        return await self._main_frame.wait_for_function(
            expression, arg, timeout=timeout, polling=polling
        )

    async def wait_for_selector(
        self,
        selector: str,
        timeout: float | None = None,
        state: str = 'visible',
        strict: bool | None = None,
    ) -> ElementHandle | None:
        return await self._main_frame.wait_for_selector(
            selector, timeout=timeout, state=state, strict=strict
        )

    # ------------------------------------------------------------ content

    async def content(self) -> str:
        return await self._main_frame.content()

    async def set_content(
        self, html: str, timeout: float | None = None, wait_until: str | None = None
    ) -> None:
        await self._main_frame.set_content(html, timeout=timeout, wait_until=wait_until)

    async def title(self) -> str:
        return await self._main_frame.title()

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return await self._main_frame.evaluate(expression, arg)

    async def evaluate_handle(self, expression: str, arg: Any = None) -> JSHandle:
        return await self._main_frame.evaluate_handle(expression, arg)

    async def query_selector(
        self, selector: str, strict: bool | None = None
    ) -> ElementHandle | None:
        return await self._main_frame.query_selector(selector, strict=strict)

    async def query_selector_all(self, selector: str) -> list[ElementHandle]:
        return await self._main_frame.query_selector_all(selector)

    async def eval_on_selector(
        self, selector: str, expression: str, arg: Any = None, strict: bool | None = None
    ) -> Any:
        return await self._main_frame.eval_on_selector(selector, expression, arg, strict=strict)

    async def eval_on_selector_all(self, selector: str, expression: str, arg: Any = None) -> Any:
        return await self._main_frame.eval_on_selector_all(selector, expression, arg)

    async def add_script_tag(self, **kwargs: Any) -> ElementHandle:
        return await self._main_frame.add_script_tag(**kwargs)

    async def add_style_tag(self, **kwargs: Any) -> ElementHandle:
        return await self._main_frame.add_style_tag(**kwargs)

    async def add_init_script(
        self, script: str | None = None, path: str | Path | None = None
    ) -> None:
        source = script if script is not None else Path(str(path)).read_text(encoding='utf-8')
        await self._send(PageCommands.add_script_to_evaluate_on_new_document(source=source))

    async def expose_function(self, name: str, callback: Callable[..., Any]) -> None:
        await self._expose(name, callback, False)

    async def expose_binding(
        self, name: str, callback: Callable[..., Any], handle: bool | None = None
    ) -> None:
        await self._expose(name, callback, True)

    async def _expose(self, name: str, callback: Callable[..., Any], with_source: bool) -> None:
        if name in self._bindings:
            raise Error(f'Function "{name}" has been already registered')
        self._bindings[name] = (callback, with_source)
        await self._enable_runtime()
        await self._send(RuntimeCommands.add_binding(name=f'{name}__binding__'))
        source = _EXPOSE_SOURCE % json.dumps(name)
        await self._send(PageCommands.add_script_to_evaluate_on_new_document(source=source))
        await self._send(RuntimeCommands.evaluate(expression=source))

    async def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        await self._send({
            'method': 'Network.setExtraHTTPHeaders',
            'params': {'headers': dict(headers)},
        })  # type: ignore[arg-type]

    async def set_viewport_size(self, viewport_size: dict[str, int]) -> None:
        """Emulate a viewport, keeping ``screen`` at least as large as the viewport.

        A viewport wider than the screen is a contradiction no real device
        produces, so the screen size follows the context's ``screen`` option or
        a common desktop size that contains the viewport.
        """
        self._viewport = dict(viewport_size)
        width = int(viewport_size['width'])
        height = int(viewport_size['height'])
        screen = self._context._screen or {
            'width': max(width, _DEFAULT_SCREEN['width']),
            'height': max(height, _DEFAULT_SCREEN['height']),
        }
        await self._send(
            EmulationCommands.set_device_metrics_override(
                width=width,
                height=height,
                device_scale_factor=self._context._device_scale_factor,
                mobile=self._context._is_mobile,
                screen_width=max(int(screen['width']), width),
                screen_height=max(int(screen['height']), height),
            )
        )

    async def emulate_media(
        self,
        media: str | None = None,
        color_scheme: str | None = None,
        reduced_motion: str | None = None,
        forced_colors: str | None = None,
        contrast: str | None = None,
    ) -> None:
        features = []
        for name, value in (
            ('prefers-color-scheme', color_scheme),
            ('prefers-reduced-motion', reduced_motion),
            ('forced-colors', forced_colors),
            ('prefers-contrast', contrast),
        ):
            if value is not None and value != 'null':
                features.append({'name': name, 'value': value})
        await self._send(EmulationCommands.set_emulated_media(media=media or '', features=features))  # type: ignore[arg-type]

    async def bring_to_front(self) -> None:
        await self._tab.bring_to_front()

    async def request_gc(self) -> None:
        await self._send({'method': 'HeapProfiler.collectGarbage', 'params': {}})  # type: ignore[arg-type]

    async def pause(self) -> None:
        return None

    # ------------------------------------------------------------ routes

    async def route(self, url: URLMatch, handler: RouteHandler, times: int | None = None) -> None:
        self._routes.append(make_entry(url, handler, times, self._context._base_url))
        await self._enable_fetch()

    async def unroute(self, url: URLMatch, handler: RouteHandler | None = None) -> None:
        self._routes = [
            entry
            for entry in self._routes
            if not (entry.matcher._match == url and (handler is None or entry.handler is handler))
        ]

    async def unroute_all(self, behavior: str | None = None) -> None:
        self._routes = []

    async def _enable_fetch(self, handle_auth: bool = False) -> None:
        if self._fetch_enabled:
            if handle_auth and not self._fetch_handles_auth:
                self._fetch_handles_auth = True
                await self._tab.enable_fetch_events(handle_auth=True)
            return
        self._fetch_enabled = True
        self._fetch_handles_auth = handle_auth
        await self._listen(
            FetchEvent.REQUEST_PAUSED,
            lambda e: asyncio.ensure_future(self._router.dispatch(e['params'])),
        )
        await self._tab.enable_fetch_events(handle_auth=handle_auth)

    async def _enable_http_credentials(self, credentials: dict[str, str]) -> None:
        """Answer HTTP authentication challenges with the context credentials.

        Credentials travel only in reply to a challenge, and only when the
        challenge comes from the origin they were given for (any origin when
        none was set), the way Playwright and real browsers behave.
        """
        origin = credentials.get('origin')

        async def on_auth_required(event: dict[str, Any]) -> None:
            params = event['params']
            challenge = params.get('authChallenge', {})
            allowed = origin is None or challenge.get('origin', '').rstrip('/') == origin.rstrip(
                '/'
            )
            response = (
                AuthChallengeResponseType.PROVIDE_CREDENTIALS
                if allowed
                else AuthChallengeResponseType.DEFAULT
            )
            try:
                await self._tab.continue_with_auth(
                    params['requestId'],
                    response,
                    proxy_username=credentials['username'] if allowed else None,
                    proxy_password=credentials['password'] if allowed else None,
                )
            except PydollException:
                logger.debug('Could not answer the auth challenge', exc_info=True)

        await self._listen(FetchEvent.AUTH_REQUIRED, on_auth_required)
        await self._enable_fetch(handle_auth=True)

    # ------------------------------------------------------------ media

    async def screenshot(
        self,
        timeout: float | None = None,
        type: str | None = None,
        path: str | Path | None = None,
        quality: int | None = None,
        omit_background: bool | None = None,
        full_page: bool | None = None,
        clip: dict[str, float] | None = None,
        animations: str | None = None,
        caret: str | None = None,
        scale: str | None = None,
        mask: Sequence[Locator] | None = None,
        mask_color: str | None = None,
        style: str | None = None,
    ) -> bytes:
        image_type = type or (
            'jpeg' if str(path or '').lower().endswith(('.jpg', '.jpeg')) else 'png'
        )
        capture_clip = dict(clip) if clip else None
        if full_page and capture_clip is None:
            metrics = (await self._send(PageCommands.get_layout_metrics()))['result']
            size = metrics.get('cssContentSize') or metrics.get('contentSize')
            capture_clip = {'x': 0, 'y': 0, 'width': size['width'], 'height': size['height']}
        if capture_clip is not None:
            capture_clip.setdefault('scale', 1)
        return await self._capture_screenshot(
            type=image_type,
            quality=quality,
            clip=capture_clip,
            omit_background=omit_background,
            path=path,
            capture_beyond_viewport=bool(full_page or clip),
        )

    async def _capture_screenshot(
        self,
        *,
        type: str,
        quality: int | None,
        clip: dict[str, float] | None,
        omit_background: bool | None,
        path: str | Path | None,
        capture_beyond_viewport: bool,
    ) -> bytes:
        if omit_background:
            await self._send({
                'method': 'Emulation.setDefaultBackgroundColorOverride',
                'params': {'color': {'r': 0, 'g': 0, 'b': 0, 'a': 0}},
            })  # type: ignore[arg-type]
        try:
            response = await self._send(
                PageCommands.capture_screenshot(
                    format=type,  # type: ignore[arg-type]
                    quality=quality if type == 'jpeg' else None,
                    clip=clip,  # type: ignore[arg-type]
                    capture_beyond_viewport=capture_beyond_viewport or None,
                )
            )
        finally:
            if omit_background:
                await self._send({
                    'method': 'Emulation.setDefaultBackgroundColorOverride',
                    'params': {},
                })  # type: ignore[arg-type]
        data = base64.b64decode(response['result']['data'])
        if path is not None:
            Path(path).write_bytes(data)
        return data

    async def pdf(
        self,
        scale: float | None = None,
        display_header_footer: bool | None = None,
        header_template: str | None = None,
        footer_template: str | None = None,
        print_background: bool | None = None,
        landscape: bool | None = None,
        page_ranges: str | None = None,
        format: str | None = None,  # noqa: A002
        width: str | float | None = None,
        height: str | float | None = None,
        prefer_css_page_size: bool | None = None,
        margin: dict[str, str | float] | None = None,
        path: str | Path | None = None,
        outline: bool | None = None,
        tagged: bool | None = None,
    ) -> bytes:
        paper = _PAPER_FORMATS.get((format or 'letter').lower(), _PAPER_FORMATS['letter'])
        margins = margin or {}
        response = await self._send(
            PageCommands.print_to_pdf(
                landscape=landscape,
                display_header_footer=display_header_footer,
                print_background=print_background,
                scale=scale,
                paper_width=_inches(width) if width is not None else paper[0],
                paper_height=_inches(height) if height is not None else paper[1],
                margin_top=_inches(margins.get('top', 0)),
                margin_bottom=_inches(margins.get('bottom', 0)),
                margin_left=_inches(margins.get('left', 0)),
                margin_right=_inches(margins.get('right', 0)),
                page_ranges=page_ranges,
                header_template=header_template,
                footer_template=footer_template,
                prefer_css_page_size=prefer_css_page_size,
            )
        )
        data = base64.b64decode(response['result']['data'])
        if path is not None:
            Path(path).write_bytes(data)
        return data

    # ------------------------------------------------------------ lifecycle

    async def close(self, run_before_unload: bool | None = None, reason: str | None = None) -> None:
        if self._closed:
            return
        try:
            await self._tab.close()
        except PydollException:
            pass
        self._on_target_closed()

    async def _dispose(self) -> None:
        self._on_target_closed()

    # ------------------------------------------------------------ locators

    def locator(self, selector: str, **kwargs: Any) -> Locator:
        return self._main_frame.locator(selector, **kwargs)

    def get_by_alt_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self._main_frame.get_by_alt_text(text, exact=exact)

    def get_by_label(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self._main_frame.get_by_label(text, exact=exact)

    def get_by_placeholder(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self._main_frame.get_by_placeholder(text, exact=exact)

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return self._main_frame.get_by_role(role, **kwargs)

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return self._main_frame.get_by_test_id(test_id)

    def get_by_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self._main_frame.get_by_text(text, exact=exact)

    def get_by_title(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self._main_frame.get_by_title(text, exact=exact)

    def frame_locator(self, selector: str) -> FrameLocator:
        return self._main_frame.frame_locator(selector)

    # ------------------------------------------------------------ selector shortcuts

    async def click(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.click(selector, **kwargs)

    async def dblclick(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.dblclick(selector, **kwargs)

    async def tap(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.tap(selector, **kwargs)

    async def hover(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.hover(selector, **kwargs)

    async def fill(self, selector: str, value: str, **kwargs: Any) -> None:
        await self._main_frame.fill(selector, value, **kwargs)

    async def focus(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.focus(selector, **kwargs)

    async def type(self, selector: str, text: str, **kwargs: Any) -> None:
        await self._main_frame.type(selector, text, **kwargs)

    async def press(self, selector: str, key: str, **kwargs: Any) -> None:
        await self._main_frame.press(selector, key, **kwargs)

    async def check(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.check(selector, **kwargs)

    async def uncheck(self, selector: str, **kwargs: Any) -> None:
        await self._main_frame.uncheck(selector, **kwargs)

    async def set_checked(self, selector: str, checked: bool, **kwargs: Any) -> None:
        await self._main_frame.set_checked(selector, checked, **kwargs)

    async def select_option(self, selector: str, value: Any = None, **kwargs: Any) -> list[str]:
        return await self._main_frame.select_option(selector, value, **kwargs)

    async def set_input_files(self, selector: str, files: Any, **kwargs: Any) -> None:
        await self._main_frame.set_input_files(selector, files, **kwargs)

    async def dispatch_event(
        self, selector: str, type: str, event_init: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        await self._main_frame.dispatch_event(selector, type, event_init, **kwargs)

    async def drag_and_drop(self, source: str, target: str, **kwargs: Any) -> None:
        await self._main_frame.drag_and_drop(source, target, **kwargs)

    async def get_attribute(self, selector: str, name: str, **kwargs: Any) -> str | None:
        return await self._main_frame.get_attribute(selector, name, **kwargs)

    async def text_content(self, selector: str, **kwargs: Any) -> str | None:
        return await self._main_frame.text_content(selector, **kwargs)

    async def inner_text(self, selector: str, **kwargs: Any) -> str:
        return await self._main_frame.inner_text(selector, **kwargs)

    async def inner_html(self, selector: str, **kwargs: Any) -> str:
        return await self._main_frame.inner_html(selector, **kwargs)

    async def input_value(self, selector: str, **kwargs: Any) -> str:
        return await self._main_frame.input_value(selector, **kwargs)

    async def is_checked(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_checked(selector, **kwargs)

    async def is_disabled(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_disabled(selector, **kwargs)

    async def is_editable(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_editable(selector, **kwargs)

    async def is_enabled(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_enabled(selector, **kwargs)

    async def is_hidden(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_hidden(selector, **kwargs)

    async def is_visible(self, selector: str, **kwargs: Any) -> bool:
        return await self._main_frame.is_visible(selector, **kwargs)


_DEFAULT_SCREEN = {'width': 1920, 'height': 1080}

_PAPER_FORMATS = {
    'letter': (8.5, 11),
    'legal': (8.5, 14),
    'tabloid': (11, 17),
    'ledger': (17, 11),
    'a0': (33.1, 46.8),
    'a1': (23.4, 33.1),
    'a2': (16.54, 23.4),
    'a3': (11.7, 16.54),
    'a4': (8.27, 11.7),
    'a5': (5.83, 8.27),
    'a6': (4.13, 5.83),
}

_UNITS = {'px': 1 / 96, 'in': 1, 'cm': 0.393701, 'mm': 0.0393701}


def _inches(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value) / 96
    text = str(value).strip().lower()
    for unit, factor in _UNITS.items():
        if text.endswith(unit):
            return float(text[: -len(unit)]) * factor
    return float(text) / 96


def _is_absolute(url: str) -> bool:
    import re  # noqa: PLC0415

    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*:', url))


__all__ = ['Page', 'WebElement', 'Awaitable', 'TargetClosedError']
