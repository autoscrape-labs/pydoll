"""Navigation and load-state tracking driven by Page lifecycle events."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydoll.commands import PageCommands
from pydoll.playwright._errors import Error
from pydoll.playwright._events import Deadline, EventContextManager, create_future, schedule
from pydoll.playwright._glob import URLMatcher

if TYPE_CHECKING:
    from pydoll.playwright._frame import Frame
    from pydoll.playwright._network import Response
    from pydoll.playwright._page import Page

_LIFECYCLE_NAMES = {
    'commit': 'commit',
    'domcontentloaded': 'DOMContentLoaded',
    'load': 'load',
    'networkidle': 'networkIdle',
}


@dataclass
class FrameState:
    loader_id: str = ''
    url: str = ''
    reached: set[str] = field(default_factory=set)
    same_document_navigations: int = 0


class NavigationTracker:
    """Keeps the lifecycle state of every frame of a page and awaits transitions."""

    def __init__(self, page: Page) -> None:
        self._page = page
        self._frames: dict[str, FrameState] = {}
        self._changed = asyncio.Event()

    def _state(self, frame_id: str) -> FrameState:
        return self._frames.setdefault(frame_id, FrameState())

    def url_of(self, frame_id: str) -> str:
        state = self._frames.get(frame_id)
        return state.url if state else ''

    def _notify(self) -> None:
        self._changed.set()
        self._changed = asyncio.Event()

    def on_lifecycle(self, params: dict[str, Any]) -> None:
        state = self._state(params['frameId'])
        name = params['name']
        loader_id = params.get('loaderId', '')
        if name == 'init':
            state.loader_id = loader_id
            state.reached = set()
            self._page._frame_for_id(params['frameId'])._reset_world()
        elif loader_id and loader_id != state.loader_id:
            state.loader_id = loader_id
            state.reached = set()
        state.reached.add(name)
        self._notify()
        if params['frameId'] == self._page._main_frame_id_cache:
            if name == 'load':
                self._page.emit('load', self._page)
            elif name == 'DOMContentLoaded':
                self._page.emit('domcontentloaded', self._page)

    def on_frame_navigated(self, params: dict[str, Any]) -> None:
        frame = params['frame']
        state = self._state(frame['id'])
        state.url = frame.get('url', '')
        if frame.get('loaderId') and frame['loaderId'] != state.loader_id:
            state.loader_id = frame['loaderId']
            state.reached = {'commit'}
        self._page._frame_for_id(frame['id'])._reset_world()
        if frame['id'] == self._page._main_frame_id_cache:
            self._page._url = state.url
        self._notify()
        self._page.emit('framenavigated', self._page._frame_for_id(frame['id']))

    def on_navigated_within_document(self, params: dict[str, Any]) -> None:
        state = self._state(params['frameId'])
        state.url = params.get('url', state.url)
        state.same_document_navigations += 1
        if params['frameId'] == self._page._main_frame_id_cache:
            self._page._url = state.url
        self._notify()
        self._page.emit('framenavigated', self._page._frame_for_id(params['frameId']))

    def on_frame_attached(self, params: dict[str, Any]) -> None:
        self._page.emit('frameattached', self._page._frame_for_id(params['frameId']))

    def on_frame_detached(self, params: dict[str, Any]) -> None:
        frame_id = params['frameId']
        self._frames.pop(frame_id, None)
        self._page.emit('framedetached', self._page._frame_for_id(frame_id))

    def _reached(self, frame_id: str, state_name: str, loader_id: str | None) -> bool:
        state = self._frames.get(frame_id)
        if state is None:
            return False
        if loader_id and state.loader_id != loader_id:
            return False
        return _LIFECYCLE_NAMES[state_name] in state.reached

    async def _wait_reached(
        self, frame_id: str, state_name: str, loader_id: str | None, deadline: Deadline, log: str
    ) -> None:
        while not self._reached(frame_id, state_name, loader_id):
            if loader_id:
                failure = self._page._network.navigation_failure(loader_id)
                if failure:
                    raise Error(f'{failure} at {self.url_of(frame_id) or "navigation"}')
            remaining = deadline.remaining_seconds()
            if remaining is not None and remaining <= 0:
                raise deadline.error(log)
            waiter = self._changed.wait()
            try:
                await asyncio.wait_for(waiter, timeout=remaining)
            except asyncio.TimeoutError:
                raise deadline.error(log) from None

    async def navigate(
        self,
        url: str,
        frame_id: str,
        *,
        timeout: float | None,
        wait_until: str | None,
        referer: str | None,
    ) -> Response | None:
        state_name = _validate_state(wait_until)
        deadline = Deadline(self._page._navigation_timeout(timeout))
        response = await self._page._send(
            PageCommands.navigate(url=url, referrer=referer, frame_id=frame_id)
        )
        result = response['result']
        error_text = result.get('errorText')
        if error_text:
            raise Error(f'{error_text} at {url}')
        loader_id = result.get('loaderId')
        target_frame_id = result.get('frameId', frame_id)
        if not loader_id:
            await self._wait_same_document(target_frame_id, deadline, url)
            return None
        await self._wait_reached(
            target_frame_id,
            state_name,
            loader_id,
            deadline,
            f'navigating to "{url}", waiting until "{state_name}"',
        )
        return await self._page._network.navigation_response(loader_id, deadline)

    async def _wait_same_document(self, frame_id: str, deadline: Deadline, url: str) -> None:
        state = self._state(frame_id)
        seen = state.same_document_navigations
        while state.same_document_navigations == seen and state.url != url:
            remaining = deadline.remaining_seconds()
            if remaining is not None and remaining <= 0:
                raise deadline.error(f'navigating to "{url}"')
            try:
                await asyncio.wait_for(self._changed.wait(), timeout=remaining)
            except asyncio.TimeoutError:
                raise deadline.error(f'navigating to "{url}"') from None

    async def wait_for_load_state(
        self, frame: Frame, frame_id: str, state_name: str, timeout: float | None
    ) -> None:
        state_name = _validate_state(state_name)
        if state_name == 'commit':
            return
        deadline = Deadline(self._page._navigation_timeout(timeout))
        if frame_id not in self._frames or not self._frames[frame_id].reached:
            ready = await frame._call('function() { return document.readyState; }', [])
            if ready == 'complete' and state_name in {'load', 'domcontentloaded'}:
                return
            if ready == 'interactive' and state_name == 'domcontentloaded':
                return
            if (
                state_name == 'networkidle'
                and ready == 'complete'
                and self._page._network.is_idle()
            ):
                return
        await self._wait_reached(
            frame_id, state_name, None, deadline, f'waiting for load state "{state_name}"'
        )

    async def wait_for_url(
        self,
        frame: Frame,
        frame_id: str,
        url: Any,
        *,
        wait_until: str | None,
        timeout: float | None,
    ) -> None:
        matcher = URLMatcher(url, self._page.context._base_url)
        deadline = Deadline(self._page._navigation_timeout(timeout))
        while not matcher.matches(frame.url):
            remaining = deadline.remaining_seconds()
            if remaining is not None and remaining <= 0:
                raise deadline.error(
                    f'waiting for navigation to "{url}" until "{wait_until or "load"}"'
                )
            try:
                await asyncio.wait_for(self._changed.wait(), timeout=remaining)
            except asyncio.TimeoutError:
                raise deadline.error(
                    f'waiting for navigation to "{url}" until "{wait_until or "load"}"'
                ) from None
        await self.wait_for_load_state(
            frame, frame_id, wait_until or 'load', timeout=deadline.remaining_seconds_ms()
        )

    def expect_navigation(
        self, frame: Frame, *, url: Any, wait_until: str | None, timeout: float | None
    ) -> EventContextManager[Response | None]:
        future: asyncio.Future[Response | None] = create_future(self._page._loop)

        async def waiter() -> None:
            try:
                frame_id = await frame._frame_id_value()
                deadline = Deadline(self._page._navigation_timeout(timeout))
                matcher = URLMatcher(url, self._page.context._base_url) if url is not None else None
                state = self._state(frame_id)
                start_loader = state.loader_id
                start_same_document = state.same_document_navigations
                while True:
                    current = self._frames.get(frame_id, state)
                    navigated = (
                        current.loader_id != start_loader
                        or current.same_document_navigations != start_same_document
                    )
                    if navigated and (matcher is None or matcher.matches(frame.url)):
                        break
                    remaining = deadline.remaining_seconds()
                    if remaining is not None and remaining <= 0:
                        raise deadline.error('waiting for navigation')
                    try:
                        await asyncio.wait_for(self._changed.wait(), timeout=remaining)
                    except asyncio.TimeoutError:
                        raise deadline.error('waiting for navigation') from None
                await self.wait_for_load_state(
                    frame, frame_id, wait_until or 'load', timeout=deadline.remaining_seconds_ms()
                )
                loader_id = self._frames[frame_id].loader_id
                response = (
                    await self._page._network.navigation_response(loader_id, deadline)
                    if loader_id
                    else None
                )
                if not future.done():
                    future.set_result(response)
            except Exception as error:
                if not future.done():
                    future.set_exception(error)

        schedule(self._page._loop, waiter())
        return EventContextManager(future)


def _validate_state(state: str | None) -> str:
    name = state or 'load'
    if name not in _LIFECYCLE_NAMES:
        raise Error(
            f'state: expected one of (load|domcontentloaded|networkidle|commit), got {name!r}'
        )
    return name
