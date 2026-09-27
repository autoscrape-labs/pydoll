"""Frame: the main document of a page or one of its iframes.

A frame wraps a pydoll root that already knows how to route commands into
the right execution context: the ``Tab`` for the main frame, an iframe
``WebElement`` for child frames. Every selector resolution, evaluation and
action of Page, Locator and ElementHandle ends up here.
"""

from __future__ import annotations

import asyncio
import json
import weakref
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Sequence, TypeVar, cast

from pydoll.browser.tab import Tab
from pydoll.commands import DomCommands, PageCommands, RuntimeCommands
from pydoll.elements.web_element import WebElement
from pydoll.exceptions import PydollException
from pydoll.playwright._actions import Actions, Resolver
from pydoll.playwright._element_handle import ElementHandle, JSHandle, PrimitiveHandle
from pydoll.playwright._errors import Error, translate
from pydoll.playwright._events import Deadline
from pydoll.playwright._injected import engine_call, engine_source
from pydoll.playwright._locator import FilePayload, FrameLocator, Locator
from pydoll.playwright._remote_values import parse_remote_value
from pydoll.playwright._selectors import (
    TextMatch,
    get_by_alt_text_selector,
    get_by_label_selector,
    get_by_placeholder_selector,
    get_by_role_selector,
    get_by_test_id_selector,
    get_by_text_selector,
    get_by_title_selector,
    split_by_frame,
)
from pydoll.playwright._serialization import call_arguments, evaluate_source
from pydoll.protocol.runtime.types import CallArgument

if TYPE_CHECKING:
    from pydoll.playwright._network import Response
    from pydoll.playwright._page import Page

FrameRoot = Tab | WebElement
T = TypeVar('T')

_QUERY_ALL = engine_call('return engine.querySelectorAll(a0, this);')
_WRAP_NODE = 'function(node) { return node; }'
_THIS_NODE = 'function() { return this; }'
_QUERY_ONE_STRICT = engine_call(
    'const e = engine.querySelector(a0, this, true); return e ? [e] : [];'
)
_QUERY_VISIBLE = engine_call(
    'return engine.querySelectorAll(a0, this).filter(e => engine.isElementVisible(e));'
)
_QUERY_FRAME_OWNERS = engine_call(
    'return engine.querySelectorAll(a0, this)'
    '.filter(e => e.nodeName === "IFRAME" || e.nodeName === "FRAME");'
)


class Frame:
    """A document inside a page: the main frame or an ``<iframe>``."""

    def __init__(self, page: Page, root: FrameRoot, parent: Frame | None = None) -> None:
        self._page = page
        self._root = root
        self._parent = parent
        self._actions = Actions(self)
        self._document_object_id: str | None = None
        self._world_id: int | None = None
        self._engine_id: str | None = None
        self._main_ids: weakref.WeakKeyDictionary[WebElement, str] = weakref.WeakKeyDictionary()
        self._frame_id: str | None = None
        self._url = ''
        self._name = ''
        self._detached = False

    def __repr__(self) -> str:
        return f'<Frame name={self._name!r} url={self.url!r}>'

    @property
    def page(self) -> Page:
        return self._page

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        if self._parent is None:
            return self._page._url
        if self._frame_id:
            tracked = self._page._navigation.url_of(self._frame_id)
            if tracked:
                return tracked
        return self._url

    @property
    def parent_frame(self) -> Frame | None:
        return self._parent

    @property
    def child_frames(self) -> list[Frame]:
        return self._page._child_frames_of(self)

    def is_detached(self) -> bool:
        return self._detached

    async def frame_element(self) -> ElementHandle:
        if self._parent is None or not isinstance(self._root, WebElement):
            raise Error('Main frame has no owner element')
        return ElementHandle(self._parent, self._root)

    async def _frame_id_value(self) -> str:
        if self._frame_id:
            return self._frame_id
        if isinstance(self._root, Tab):
            self._frame_id = await self._page._main_frame_id()
        else:
            context = await self._root.iframe_context()
            if context is None:
                raise Error('Element is not an iframe')
            self._frame_id = context.frame_id
            self._url = context.document_url or self._url
        return self._frame_id

    async def _send(self, command: Any) -> Any:
        try:
            return await self._root.execute_command(command)
        except PydollException as error:
            raise translate(error) from error

    async def _send_for_element(self, element: WebElement, command: Any) -> Any:
        try:
            return await element.execute_command(command)
        except PydollException as error:
            raise translate(error) from error

    def _child_frame(self, iframe: WebElement) -> Frame:
        frame = Frame(self._page, iframe, parent=self)
        frame._name = iframe.get_attribute('name') or ''
        frame._url = iframe.get_attribute('src') or ''
        return frame

    async def _canonical(self) -> Frame:
        """The page's single Frame object for this frame id, adopting this root."""
        return await self._page._canonical_frame(self)

    def _owner(self, element: WebElement) -> Frame:
        """The frame whose isolated world produced ``element`` (this frame by default)."""
        return self._page._element_frames.get(element, self)

    def _reset_world(self) -> None:
        """Forget the isolated world and every handle bound to it (after navigation)."""
        self._document_object_id = None
        self._world_id = None
        self._engine_id = None
        self._main_ids.clear()

    async def _world(self) -> int:
        """Execution context id of this frame's isolated world, created on demand."""
        if self._world_id is None:
            frame_id = await self._frame_id_value()
            response = await self._send(
                PageCommands.create_isolated_world(
                    frame_id=frame_id,
                    world_name=self._page._world_name,
                    grant_universal_access=True,
                )
            )
            self._world_id = int(response['result']['executionContextId'])
        return self._world_id

    async def _engine_handle(self) -> str:
        """Object id of the engine object, evaluated once per isolated world."""
        if self._engine_id is None:
            world = await self._world()
            response = await self._send(
                RuntimeCommands.evaluate(
                    expression=engine_source(), context_id=world, return_by_value=False
                )
            )
            self._raise_exception(cast('dict[str, Any]', response))
            self._engine_id = response['result']['result']['objectId']
        return self._engine_id

    async def _with_world(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Run ``operation`` and retry once with a fresh world if the old one is gone."""
        try:
            return await operation()
        except Error as error:
            if not _is_stale_context(error):
                raise
            self._reset_world()
            return await operation()

    async def _document_id(self) -> str:
        """Object id of ``document`` in the main world, for user evaluations."""
        if self._document_object_id:
            return self._document_object_id
        if isinstance(self._root, Tab):
            response = await self._send(
                RuntimeCommands.evaluate(expression='document', return_by_value=False)
            )
        else:
            context = await self._root.iframe_context()
            if context is None:
                raise Error('Element is not an iframe')
            if context.document_object_id:
                self._document_object_id = context.document_object_id
                return self._document_object_id
            response = await self._send(
                RuntimeCommands.evaluate(
                    expression='document',
                    return_by_value=False,
                    context_id=context.execution_context_id,
                )
            )
        self._document_object_id = response['result']['result']['objectId']
        return self._document_object_id

    @staticmethod
    def _raise_exception(response: dict[str, Any]) -> None:
        details = response.get('result', {}).get('exceptionDetails')
        if not details:
            return
        exception = details.get('exception', {})
        message = exception.get('description') or details.get('text') or 'Evaluation failed'
        raise Error(message)

    async def _call(
        self,
        function_declaration: str,
        arguments: Sequence[CallArgument],
        *,
        object_id: str | None = None,
        by_value: bool = True,
        await_promise: bool = False,
        user_gesture: bool = False,
    ) -> Any:
        """Call a function in the main world on ``document`` or on ``object_id``."""
        for attempt in range(2):
            target = object_id or await self._document_id()
            try:
                response = await self._send(
                    RuntimeCommands.call_function_on(
                        function_declaration=function_declaration,
                        object_id=target,
                        arguments=list(arguments),
                        return_by_value=by_value,
                        await_promise=await_promise,
                        user_gesture=user_gesture,
                    )
                )
                break
            except Error as error:
                if object_id is not None or attempt or not _is_stale_context(error):
                    raise
                self._document_object_id = None
        self._raise_exception(cast('dict[str, Any]', response))
        remote = cast('dict[str, Any]', response['result']['result'])
        return parse_remote_value(remote) if by_value else remote

    async def _call_on_element(
        self,
        element: WebElement,
        function_declaration: str,
        arguments: Sequence[CallArgument],
        *,
        by_value: bool = True,
        await_promise: bool = False,
        user_gesture: bool = False,
    ) -> Any:
        """Call a function with ``this`` bound to the element, in the element's world."""
        try:
            response = await element.execute_script(
                function_declaration,
                arguments=list(arguments),
                return_by_value=by_value,
                await_promise=await_promise,
                user_gesture=user_gesture,
            )
        except PydollException as error:
            raise translate(error) from error
        self._raise_exception(cast('dict[str, Any]', response))
        remote = cast('dict[str, Any]', response['result']['result'])
        return parse_remote_value(remote) if by_value else remote

    async def _engine(self, body: str, args: Sequence[Any], *, await_promise: bool = False) -> Any:
        """Run an engine body with ``this`` bound to the isolated world's document."""

        async def operation() -> Any:
            world = await self._world()
            engine = await self._engine_handle()
            arguments: list[CallArgument] = [{'objectId': engine}]
            arguments.extend({'value': arg} for arg in args)
            response = await self._send(
                RuntimeCommands.call_function_on(
                    function_declaration=(
                        'function() { return ('
                        + engine_call(body)
                        + ').apply(document, arguments); }'
                    ),
                    execution_context_id=world,
                    arguments=arguments,
                    return_by_value=True,
                    await_promise=await_promise,
                )
            )
            self._raise_exception(cast('dict[str, Any]', response))
            return parse_remote_value(cast('dict[str, Any]', response['result']['result']))

        return await self._with_world(operation)

    async def _engine_on_element(
        self,
        element: WebElement,
        body: str,
        args: Sequence[Any],
        *,
        await_promise: bool = False,
        extra_arguments: Sequence[CallArgument] | None = None,
    ) -> Any:
        """Run an engine body with ``this`` bound to an element of the isolated world."""

        home = self._owner(element)
        if home is not self:
            return await home._engine_on_element(
                element, body, args, await_promise=await_promise, extra_arguments=extra_arguments
            )

        async def operation() -> Any:
            engine = await self._engine_handle()
            arguments: list[CallArgument] = [{'objectId': engine}]
            arguments.extend({'value': arg} for arg in args)
            arguments.extend(extra_arguments or [])
            return await self._call_on_element(
                element, engine_call(body), arguments, await_promise=await_promise
            )

        return await self._with_world(operation)

    async def _query_script(
        self, root: WebElement | None, script: str, selector: str
    ) -> list[WebElement]:
        """Resolve a selector in the isolated world and wrap the matches as WebElements."""

        async def operation() -> list[WebElement]:
            engine = await self._engine_handle()
            arguments: list[CallArgument] = [{'objectId': engine}, {'value': selector}]
            try:
                if root is not None:
                    elements = await root.query_script(script, arguments=arguments)
                else:
                    elements = await self._root.query_script(
                        script, arguments=arguments, execution_context_id=await self._world()
                    )
            except PydollException as error:
                raise translate(error) from error
            for element in elements:
                self._page._element_frames[element] = self
            return elements

        return await self._with_world(operation)

    async def _backend_node_id(self, object_id: str) -> int:
        response = await self._send(DomCommands.describe_node(object_id=object_id))
        return int(response['result']['node']['backendNodeId'])

    async def _element_from_object_id(self, object_id: str) -> WebElement:
        """Wrap a node from any world as a WebElement living in the isolated world."""
        backend_node_id = await self._backend_node_id(object_id)
        world = await self._world()
        resolved = await self._send(
            DomCommands.resolve_node(backend_node_id=backend_node_id, execution_context_id=world)
        )
        isolated_id = resolved['result']['object']['objectId']
        try:
            elements = await self._root.query_script(
                _WRAP_NODE, arguments=[{'objectId': isolated_id}], execution_context_id=world
            )
        except PydollException as error:
            raise translate(error) from error
        if not elements:
            raise Error('Object is not an element')
        self._page._element_frames[elements[0]] = self
        return elements[0]

    async def _main_world_object_id(self, element: WebElement) -> str:
        """Main-world object id of an isolated-world element, for user evaluations."""
        home = self._owner(element)
        if home is not self:
            return await home._main_world_object_id(element)
        cached = self._main_ids.get(element)
        if cached is not None:
            return cached
        remote = await self._call_on_element(element, _THIS_NODE, [], by_value=False)
        backend_node_id = await self._backend_node_id(remote['objectId'])
        resolved = await self._send(DomCommands.resolve_node(backend_node_id=backend_node_id))
        object_id = resolved['result']['object']['objectId']
        self._main_ids[element] = object_id
        return object_id

    def _handle_from_remote_object(self, remote: dict[str, Any]) -> JSHandle:
        object_id = remote.get('objectId')
        if not object_id:
            return PrimitiveHandle(self, parse_remote_value(remote))
        return JSHandle(
            self, object_id, remote.get('description') or remote.get('className') or 'JSHandle'
        )

    async def _element_from_remote(self, remote: dict[str, Any]) -> ElementHandle:
        element = await self._element_from_object_id(remote['objectId'])
        handle = ElementHandle(self, element)
        handle._object_id = remote['objectId']
        self._main_ids[element] = remote['objectId']
        return handle

    async def _handle_or_element(self, remote: dict[str, Any]) -> JSHandle:
        if remote.get('subtype') == 'node' and remote.get('objectId'):
            return await self._element_from_remote(remote)
        if 'objectId' not in remote:
            return PrimitiveHandle(self, parse_remote_value(remote))
        return self._handle_from_remote_object(remote)

    async def _query_all(self, selector: str, root: WebElement | None = None) -> list[WebElement]:
        chunks = split_by_frame(selector)
        frames: list[Frame] = [self]
        roots: list[WebElement | None] = [root]
        for chunk in chunks[:-1]:
            next_frames: list[Frame] = []
            for frame, frame_root in zip(frames, roots):
                owners = await frame._query_script(frame_root, _QUERY_FRAME_OWNERS, chunk)
                for home in owners:
                    next_frames.append(await frame._child_frame(home)._canonical())
            frames = next_frames
            roots = [None] * len(frames)
            if not frames:
                return []
        result: list[WebElement] = []
        for frame, frame_root in zip(frames, roots):
            result.extend(await frame._query_script(frame_root, _QUERY_ALL, chunks[-1]))
        return result

    async def _query_one(
        self, selector: str, strict: bool, root: WebElement | None = None
    ) -> WebElement | None:
        if not strict:
            elements = await self._query_all(selector, root=root)
            return elements[0] if elements else None
        chunks = split_by_frame(selector)
        if len(chunks) == 1:
            elements = await self._query_script(root, _QUERY_ONE_STRICT, selector)
            return elements[0] if elements else None
        elements = await self._query_all(selector, root=root)
        if len(elements) > 1:
            raise Error(f'strict mode violation: {selector} resolved to {len(elements)} elements')
        return elements[0] if elements else None

    async def _query_visible(self, selector: str, root: WebElement | None) -> list[WebElement]:
        chunks = split_by_frame(selector)
        if len(chunks) == 1:
            return await self._query_script(root, _QUERY_VISIBLE, selector)
        elements = await self._query_all(selector, root=root)
        visible = []
        for element in elements:
            if await self._engine_on_element(element, 'return engine.isElementVisible(this);', []):
                visible.append(element)
        return visible

    async def wait_for_selector(
        self,
        selector: str,
        timeout: float | None = None,
        state: str = 'visible',
        strict: bool | None = None,
        root: WebElement | None = None,
    ) -> ElementHandle | None:
        if state not in {'attached', 'detached', 'visible', 'hidden'}:
            raise Error(f'state: expected one of (attached|detached|visible|hidden), got {state!r}')
        deadline = Deadline(self._page._timeout(timeout))
        description = f'locator({json.dumps(selector)}) to be {state}'
        while True:
            if state in {'visible', 'hidden'}:
                candidates = await self._query_visible(selector, root)
            else:
                candidates = await self._query_all(selector, root=root)
            if strict and len(candidates) > 1:
                raise Error(
                    f'strict mode violation: {selector} resolved to {len(candidates)} elements'
                )
            if state in {'attached', 'visible'}:
                if candidates:
                    return ElementHandle(self, candidates[0])
            elif not candidates:
                return None
            if deadline.expired():
                raise deadline.error(f'waiting for {description}')
            await asyncio.sleep(0.1)

    async def _evaluate(
        self,
        expression: str,
        arg: Any = None,
        *,
        this_object_id: str | None = None,
        by_value: bool = True,
    ) -> Any:
        source = evaluate_source(expression, with_this=bool(this_object_id), by_value=by_value)
        for handle in _handles_in(arg):
            if isinstance(handle, ElementHandle):
                await handle._ensure_object_id()
        result = await self._call(
            source,
            call_arguments(arg),
            object_id=this_object_id,
            by_value=by_value,
            await_promise=True,
            user_gesture=self._page._user_gesture,
        )
        if by_value:
            return result
        return await self._handle_or_element(result)

    async def _evaluate_on_element(
        self, element: WebElement, expression: str, arg: Any, by_value: bool
    ) -> Any:
        for handle in _handles_in(arg):
            if isinstance(handle, ElementHandle):
                await handle._ensure_object_id()
        result = await self._call(
            evaluate_source(expression, with_this=True, by_value=by_value),
            call_arguments(arg),
            object_id=await self._main_world_object_id(element),
            by_value=by_value,
            await_promise=True,
            user_gesture=self._page._user_gesture,
        )
        if by_value:
            return result
        return await self._handle_or_element(result)

    async def _evaluate_on_elements(
        self, elements: Sequence[WebElement], expression: str, arg: Any = None
    ) -> Any:
        object_ids: list[str] = []
        for element in elements:
            object_ids.append(await self._main_world_object_id(element))
        for handle in _handles_in(arg):
            if isinstance(handle, ElementHandle):
                await handle._ensure_object_id()
        arguments = call_arguments(arg)
        handle_count = len(arguments) - 1
        arguments.extend({'objectId': object_id} for object_id in object_ids)
        source = (
            'function(tree, ...rest) {\n'
            f'  const handles = rest.slice(0, {handle_count});\n'
            f'  const elements = rest.slice({handle_count});\n'
            f'  const evaluate = {evaluate_source(expression, all_elements=True)};\n'
            '  return evaluate.call(this, tree, ...handles);\n'
            '}'
        )
        return await self._call(
            source, arguments, await_promise=True, user_gesture=self._page._user_gesture
        )

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return await self._evaluate(expression, arg, by_value=True)

    async def evaluate_handle(self, expression: str, arg: Any = None) -> JSHandle:
        return await self._evaluate(expression, arg, by_value=False)

    async def _wait_for_function(
        self,
        expression: str,
        arg: Any = None,
        timeout: float | None = None,
        polling: Any = None,
        element: WebElement | None = None,
    ) -> JSHandle:
        deadline = Deadline(self._page._timeout(timeout))
        interval = (polling / 1000) if isinstance(polling, (int, float)) else 0.1
        while True:
            if element is not None:
                result = await self._evaluate_on_element(element, expression, arg, by_value=False)
            else:
                result = await self._evaluate(expression, arg, by_value=False)
            truthy = await result.json_value() if isinstance(result, JSHandle) else result
            if truthy:
                return result
            if isinstance(result, JSHandle):
                await result.dispose()
            if deadline.expired():
                raise deadline.error('waiting for function to return a truthy value')
            await asyncio.sleep(interval)

    async def wait_for_function(
        self, expression: str, arg: Any = None, timeout: float | None = None, polling: Any = None
    ) -> JSHandle:
        return await self._wait_for_function(expression, arg, timeout=timeout, polling=polling)

    async def wait_for_timeout(self, timeout: float) -> None:
        await asyncio.sleep(timeout / 1000)

    async def content(self) -> str:
        return await self._call(
            'function() {'
            ' let content = document.doctype'
            '   ? new XMLSerializer().serializeToString(document.doctype) : "";'
            ' return content'
            '   + (document.documentElement ? document.documentElement.outerHTML : ""); }',
            [],
        )

    async def set_content(
        self, html: str, timeout: float | None = None, wait_until: str | None = None
    ) -> None:
        frame_id = await self._frame_id_value()
        self._document_object_id = None
        await self._send(PageCommands.set_document_content(frame_id=frame_id, html=html))
        await self.wait_for_load_state(wait_until or 'load', timeout=timeout)

    async def title(self) -> str:
        return await self._call('function() { return document.title; }', [])

    async def query_selector(
        self, selector: str, strict: bool | None = None
    ) -> ElementHandle | None:
        element = await self._query_one(selector, strict=bool(strict))
        return ElementHandle(self, element) if element else None

    async def query_selector_all(self, selector: str) -> list[ElementHandle]:
        return [ElementHandle(self, element) for element in await self._query_all(selector)]

    async def eval_on_selector(
        self, selector: str, expression: str, arg: Any = None, strict: bool | None = None
    ) -> Any:
        element = await self._query_one(selector, strict=bool(strict))
        if element is None:
            raise Error(f'Failed to find element matching selector "{selector}"')
        return await self._evaluate_on_element(element, expression, arg, by_value=True)

    async def eval_on_selector_all(self, selector: str, expression: str, arg: Any = None) -> Any:
        return await self._evaluate_on_elements(await self._query_all(selector), expression, arg)

    async def add_script_tag(
        self,
        url: str | None = None,
        path: str | Path | None = None,
        content: str | None = None,
        type: str | None = None,
    ) -> ElementHandle:
        if path is not None:
            content = Path(path).read_text(encoding='utf-8')
        remote = await self._call(
            'function(url, content, type) {'
            ' return new Promise((resolve, reject) => {'
            '   const script = document.createElement("script");'
            '   if (type) script.type = type;'
            '   if (url) { script.src = url; script.onload = () => resolve(script);'
            '     script.onerror = () => reject(new Error("Could not load script: " + url)); }'
            '   else { script.textContent = content; }'
            '   (document.head || document.documentElement).appendChild(script);'
            '   if (!url) resolve(script);'
            ' }); }',
            [{'value': url}, {'value': content}, {'value': type}],
            by_value=False,
            await_promise=True,
        )
        return await self._element_from_remote(remote)

    async def add_style_tag(
        self,
        url: str | None = None,
        path: str | Path | None = None,
        content: str | None = None,
    ) -> ElementHandle:
        if path is not None:
            content = Path(path).read_text(encoding='utf-8')
        remote = await self._call(
            'function(url, content) {'
            ' return new Promise((resolve, reject) => {'
            '   if (url) { const link = document.createElement("link");'
            '     link.rel = "stylesheet"; link.href = url;'
            '     link.onload = () => resolve(link);'
            '     link.onerror = () => reject(new Error("Could not load stylesheet: " + url));'
            '     (document.head || document.documentElement).appendChild(link); return; }'
            '   const style = document.createElement("style"); style.textContent = content;'
            '   (document.head || document.documentElement).appendChild(style); resolve(style);'
            ' }); }',
            [{'value': url}, {'value': content}],
            by_value=False,
            await_promise=True,
        )
        return await self._element_from_remote(remote)

    async def goto(
        self,
        url: str,
        timeout: float | None = None,
        wait_until: str | None = None,
        referer: str | None = None,
    ) -> Response | None:
        frame_id = await self._frame_id_value()
        self._document_object_id = None
        return await self._page._navigation.navigate(
            url, frame_id, timeout=timeout, wait_until=wait_until, referer=referer
        )

    async def wait_for_load_state(
        self, state: str | None = None, timeout: float | None = None
    ) -> None:
        frame_id = await self._frame_id_value()
        await self._page._navigation.wait_for_load_state(
            self, frame_id, state or 'load', timeout=timeout
        )

    async def wait_for_url(
        self, url: Any, wait_until: str | None = None, timeout: float | None = None
    ) -> None:
        frame_id = await self._frame_id_value()
        await self._page._navigation.wait_for_url(
            self, frame_id, url, wait_until=wait_until, timeout=timeout
        )

    def expect_navigation(
        self, url: Any = None, wait_until: str | None = None, timeout: float | None = None
    ) -> Any:
        return self._page._navigation.expect_navigation(
            self, url=url, wait_until=wait_until, timeout=timeout
        )

    def locator(
        self,
        selector: str,
        has_text: TextMatch | None = None,
        has_not_text: TextMatch | None = None,
        has: Locator | None = None,
        has_not: Locator | None = None,
    ) -> Locator:
        return Locator(
            self, selector, has_text=has_text, has_not_text=has_not_text, has=has, has_not=has_not
        )

    def get_by_alt_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_alt_text_selector(text, exact=exact))

    def get_by_label(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_label_selector(text, exact=exact))

    def get_by_placeholder(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_placeholder_selector(text, exact=exact))

    def get_by_role(self, role: str, **kwargs: Any) -> Locator:
        return self.locator(get_by_role_selector(role, **kwargs))

    def get_by_test_id(self, test_id: TextMatch) -> Locator:
        return self.locator(get_by_test_id_selector(test_id, self._page._test_id_attribute))

    def get_by_text(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_text_selector(text, exact=exact))

    def get_by_title(self, text: TextMatch, exact: bool | None = None) -> Locator:
        return self.locator(get_by_title_selector(text, exact=exact))

    def frame_locator(self, selector: str) -> FrameLocator:
        return FrameLocator(self, selector)

    def _shortcut(self, selector: str, strict: bool | None) -> Any:
        async def find() -> WebElement | None:
            return await self._query_one(selector, strict=bool(strict))

        return Resolver(find, f'locator({json.dumps(selector)})')

    async def click(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.click(self._shortcut(selector, strict), **kwargs)

    async def dblclick(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.dblclick(self._shortcut(selector, strict), **kwargs)

    async def tap(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.tap(self._shortcut(selector, strict), **kwargs)

    async def hover(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.hover(self._shortcut(selector, strict), **kwargs)

    async def fill(
        self, selector: str, value: str, strict: bool | None = None, **kwargs: Any
    ) -> None:
        await self._actions.fill(self._shortcut(selector, strict), value, **kwargs)

    async def focus(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> None:
        await self._actions.focus(self._shortcut(selector, strict), timeout=timeout)

    async def type(
        self, selector: str, text: str, strict: bool | None = None, **kwargs: Any
    ) -> None:
        await self._actions.type(self._shortcut(selector, strict), text, **kwargs)

    async def press(
        self, selector: str, key: str, strict: bool | None = None, **kwargs: Any
    ) -> None:
        await self._actions.press(self._shortcut(selector, strict), key, **kwargs)

    async def check(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.set_checked(self._shortcut(selector, strict), True, **kwargs)

    async def uncheck(self, selector: str, strict: bool | None = None, **kwargs: Any) -> None:
        await self._actions.set_checked(self._shortcut(selector, strict), False, **kwargs)

    async def set_checked(
        self, selector: str, checked: bool, strict: bool | None = None, **kwargs: Any
    ) -> None:
        await self._actions.set_checked(self._shortcut(selector, strict), checked, **kwargs)

    async def select_option(
        self, selector: str, value: Any = None, strict: bool | None = None, **kwargs: Any
    ) -> list[str]:
        return await self._actions.select_option(
            self._shortcut(selector, strict), value=value, **kwargs
        )

    async def set_input_files(
        self,
        selector: str,
        files: str | Path | FilePayload | Sequence[Any],
        strict: bool | None = None,
        **kwargs: Any,
    ) -> None:
        await self._actions.set_input_files(self._shortcut(selector, strict), files, **kwargs)

    async def dispatch_event(
        self,
        selector: str,
        type: str,
        event_init: dict[str, Any] | None = None,
        strict: bool | None = None,
        **kwargs: Any,
    ) -> None:
        await self._actions.dispatch_event(
            self._shortcut(selector, strict), type, event_init, **kwargs
        )

    async def drag_and_drop(
        self, source: str, target: str, strict: bool | None = None, **kwargs: Any
    ) -> None:
        await self._actions.drag_to(
            self._shortcut(source, strict), self._shortcut(target, strict), **kwargs
        )

    async def get_attribute(
        self,
        selector: str,
        name: str,
        strict: bool | None = None,
        timeout: float | None = None,
    ) -> str | None:
        return await self._actions.get_attribute(
            self._shortcut(selector, strict), name, timeout=timeout
        )

    async def text_content(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> str | None:
        return await self._actions.text_content(self._shortcut(selector, strict), timeout=timeout)

    async def inner_text(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> str:
        return await self._actions.inner_text(self._shortcut(selector, strict), timeout=timeout)

    async def inner_html(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> str:
        return await self._actions.inner_html(self._shortcut(selector, strict), timeout=timeout)

    async def input_value(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> str:
        return await self._actions.input_value(self._shortcut(selector, strict), timeout=timeout)

    async def is_checked(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'checked', timeout=timeout
        )

    async def is_disabled(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'disabled', timeout=timeout
        )

    async def is_editable(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'editable', timeout=timeout
        )

    async def is_enabled(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'enabled', timeout=timeout
        )

    async def is_hidden(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'hidden', timeout=timeout
        )

    async def is_visible(
        self, selector: str, strict: bool | None = None, timeout: float | None = None
    ) -> bool:
        return await self._actions.element_state(
            self._shortcut(selector, strict), 'visible', timeout=timeout
        )


def _is_stale_context(error: Error) -> bool:
    text = str(error)
    return (
        'Cannot find context with specified id' in text or 'Execution context was destroyed' in text
    )


def _handles_in(value: Any) -> list[JSHandle]:
    found: list[JSHandle] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, JSHandle):
            found.append(item)
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, (list, tuple, set)):
            stack.extend(item)
    return found
