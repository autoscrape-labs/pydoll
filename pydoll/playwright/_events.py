"""A minimal event emitter plus the timeout helpers every object shares."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Awaitable, Callable, Generic, TypeAlias, TypeVar

from pydoll.playwright._errors import TimeoutError

T = TypeVar('T')
Listener: TypeAlias = Callable[..., Any]

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_MS = 30_000.0


def create_future(loop: asyncio.AbstractEventLoop) -> asyncio.Future[Any]:
    """A future bound to ``loop`` even when called from a thread without a running loop."""
    return loop.create_future()


def schedule(loop: asyncio.AbstractEventLoop, coroutine: Awaitable[Any]) -> None:
    """Run ``coroutine`` on ``loop`` from the loop thread or from any other thread."""
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    if running is loop:
        asyncio.ensure_future(coroutine)
    else:
        asyncio.run_coroutine_threadsafe(coroutine, loop)  # type: ignore[arg-type]


class EventEmitter:
    """Register listeners with ``on``/``once`` and dispatch with ``emit``."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[tuple[Listener, bool]]] = {}

    def on(self, event: str, listener: Listener) -> None:
        self._listeners.setdefault(event, []).append((listener, False))

    def once(self, event: str, listener: Listener) -> None:
        self._listeners.setdefault(event, []).append((listener, True))

    def remove_listener(self, event: str, listener: Listener) -> None:
        entries = self._listeners.get(event, [])
        self._listeners[event] = [entry for entry in entries if entry[0] is not listener]

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))

    def emit(self, event: str, *args: Any) -> None:
        entries = list(self._listeners.get(event, []))
        if not entries:
            return
        self._listeners[event] = [entry for entry in entries if not entry[1]]
        for listener, _ in entries:
            try:
                result = listener(*args)
                if inspect.isawaitable(result):
                    asyncio.ensure_future(_log_failure(result, event))
            except Exception:
                logger.exception(f'Listener for {event!r} raised')


async def _log_failure(awaitable: Awaitable[Any], event: str) -> None:
    try:
        await awaitable
    except Exception:
        logger.exception(f'Async listener for {event!r} raised')


class Deadline:
    """Track the time budget of one API call, in Playwright's millisecond units."""

    def __init__(self, timeout_ms: float | None) -> None:
        self.timeout_ms = timeout_ms
        self._start = time.monotonic()

    @property
    def elapsed_ms(self) -> float:
        return (time.monotonic() - self._start) * 1000

    def remaining_seconds(self) -> float | None:
        if self.timeout_ms is None or self.timeout_ms <= 0:
            return None
        return max(0.0, (self.timeout_ms - self.elapsed_ms) / 1000)

    def remaining_seconds_ms(self) -> float | None:
        remaining = self.remaining_seconds()
        return None if remaining is None else remaining * 1000

    def expired(self) -> bool:
        remaining = self.remaining_seconds()
        return remaining is not None and remaining <= 0

    def error(self, description: str, log: list[str] | None = None) -> TimeoutError:
        lines = [
            f'Timeout {int(self.timeout_ms or 0)}ms exceeded.',
            f'Call log:\n  - {description}',
        ]
        for entry in log or []:
            lines.append(f'  - {entry}')
        return TimeoutError('\n'.join(lines))


class EventInfo(Generic[T]):
    """Result placeholder returned by ``expect_*`` context managers."""

    def __init__(self, future: asyncio.Future[T]) -> None:
        self._future = future

    @property
    async def value(self) -> T:
        return await self._future

    def is_done(self) -> bool:
        return self._future.done()


class EventContextManager(Generic[T]):
    """``async with page.expect_event(...) as info`` support."""

    def __init__(self, future: asyncio.Future[T]) -> None:
        self._info = EventInfo(future)

    async def __aenter__(self) -> EventInfo[T]:
        return self._info

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc is not None:
            self._info._future.cancel()
            return
        await self._info._future


async def wait_for(
    predicate_future: asyncio.Future[T],
    deadline: Deadline,
    description: str,
) -> T:
    """Await a future within the deadline, translating expiry into TimeoutError."""
    remaining = deadline.remaining_seconds()
    try:
        if remaining is None:
            return await predicate_future
        return await asyncio.wait_for(predicate_future, timeout=remaining)
    except asyncio.TimeoutError:
        raise deadline.error(description) from None
