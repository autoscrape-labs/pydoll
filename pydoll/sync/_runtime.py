"""Runtime for the generated synchronous facades.

One asyncio loop runs in a daemon thread for the whole process. A facade method
schedules its coroutine on that loop and blocks until the result arrives.
Callbacks the user registers (event listeners, route handlers, exposed
functions) each run on their own single-worker thread, so they can call facade
methods themselves without deadlocking the loop, keep their event order, and
cannot delay the callbacks of another handler or browser.

The facades in ``pydoll.sync`` and ``pydoll.playwright.sync_api`` are generated
by ``scripts/generate_sync_api.py``; this module is the only hand-written part.
"""

from __future__ import annotations

import asyncio
import atexit
import concurrent.futures
import contextlib
import inspect
import logging
import os
import threading
import weakref
from typing import Any, Callable, Coroutine, Generic, TypeVar

T = TypeVar('T')

logger = logging.getLogger(__name__)


class SyncError(RuntimeError):
    """Raised when the sync API is used in a way its threading model cannot serve."""


class EventLoopThread:
    """A process-wide asyncio loop living in a daemon thread.

    The instance is created on first use and dropped by ``shutdown()`` or in
    the child of ``os.fork()`` (threads do not survive a fork), so the next
    call starts a fresh loop instead of waiting on a dead one.
    """

    _instance: EventLoopThread | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._closed = False
        self._thread = threading.Thread(
            target=self._run_forever, name='pydoll-sync-loop', daemon=True
        )
        self._executors: weakref.WeakSet[concurrent.futures.ThreadPoolExecutor] = weakref.WeakSet()
        self._thread.start()
        if not self._ready.wait(10):
            raise SyncError('The pydoll sync event loop did not start')

    @classmethod
    def instance(cls) -> EventLoopThread:
        """The shared loop thread, started on first use."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
                atexit.register(cls._instance.shutdown)
            return cls._instance

    @classmethod
    def _forget(cls) -> None:
        """Drop the singleton without touching its threads (fork child, shutdown)."""
        with cls._instance_lock:
            cls._instance = None

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def _run_forever(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.call_soon(self._ready.set)
        self._loop.run_forever()

    def run(
        self, awaitable: Coroutine[Any, Any, T] | asyncio.Future[T], timeout: float | None = None
    ) -> T:
        """Run a coroutine on the loop from another thread and wait for its result."""
        if self._closed:
            if inspect.iscoroutine(awaitable):
                awaitable.close()
            raise SyncError('This pydoll sync event loop was shut down')
        if threading.current_thread() is self._thread:
            if inspect.iscoroutine(awaitable):
                awaitable.close()
            raise SyncError(
                'The sync API cannot be called from inside an event loop callback. '
                'Register the callback through the sync API so it runs on the dispatch thread.'
            )
        if inspect.iscoroutine(awaitable):
            future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
            return future.result(timeout)
        return asyncio.run_coroutine_threadsafe(_await(awaitable), self._loop).result(timeout)

    def new_dispatcher(self) -> concurrent.futures.ThreadPoolExecutor:
        """A single-worker executor for one callback: ordered per handler, isolated between them."""
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix='pydoll-sync-callbacks'
        )
        self._executors.add(executor)
        return executor

    def dispatch(
        self,
        executor: concurrent.futures.ThreadPoolExecutor,
        function: Callable[..., Any],
        *args: Any,
    ) -> asyncio.Future[Any]:
        """Run a user callback on its executor; returns a loop future for its result.

        A failure inside the callback is logged with the callback's name, so it
        does not surface only as an unretrieved future when the implementation
        fires the callback without awaiting its result.
        """
        future = asyncio.wrap_future(executor.submit(function, *args), loop=self._loop)
        name = getattr(function, '__qualname__', repr(function))
        future.add_done_callback(lambda done: _log_callback_failure(done, name))
        return future

    def shutdown(self) -> None:
        """Cancel pending work, close the loop and stop the callback threads.

        The next use of the sync API starts a new instance.
        """
        if self._closed:
            return
        self._closed = True
        if type(self)._instance is self:
            self._forget()
        if not self._loop.is_closed():
            if self._thread.is_alive():
                asyncio.run_coroutine_threadsafe(self._drain(), self._loop)
                self._thread.join(5)
            if not self._thread.is_alive():
                self._loop.close()
        for executor in list(self._executors):
            executor.shutdown(wait=False)

    async def _drain(self) -> None:
        """Cancel every other task, let them finish, then stop the loop."""
        current = asyncio.current_task()
        pending = [task for task in asyncio.all_tasks() if task is not current]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        await self._loop.shutdown_asyncgens()
        self._loop.stop()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=EventLoopThread._forget)


def _log_callback_failure(future: asyncio.Future[object], name: str) -> None:
    if future.cancelled():
        return
    error = future.exception()
    if error is not None:
        logger.error('Sync callback %s raised', name, exc_info=error)


async def _await(awaitable: Any) -> Any:
    return await awaitable


def run_sync(awaitable: Any, timeout: float | None = None) -> Any:
    """Run an awaitable on the shared loop and block for its result."""
    return EventLoopThread.instance().run(awaitable, timeout)


class Mapping:
    """Convert implementation objects into facades and back."""

    def __init__(self) -> None:
        self._facades: dict[type, type[SyncBase]] = {}
        self._cache: weakref.WeakValueDictionary[int, SyncBase] = weakref.WeakValueDictionary()
        self._handlers: weakref.WeakValueDictionary[Any, Callable[..., Any]] = (
            weakref.WeakValueDictionary()
        )

    def register(self, impl_type: type, facade_type: type[SyncBase]) -> None:
        self._facades[impl_type] = facade_type

    def facade_for(self, value: Any) -> type[SyncBase] | None:
        for base in type(value).__mro__:
            facade = self._facades.get(base)
            if facade is not None:
                return facade
        return None

    def from_impl(self, value: Any) -> Any:
        """Wrap ``value`` (or its members) in facades where a facade is registered."""
        if isinstance(value, SyncBase):
            return value
        if inspect.iscoroutine(value) or isinstance(value, asyncio.Future):
            return self.from_impl(run_sync(value))
        facade = self.facade_for(value)
        if facade is not None:
            cached = self._cache.get(id(value))
            if cached is not None and cached._impl is value:
                return cached
            wrapped = facade._wrap(value)
            self._cache[id(value)] = wrapped
            return wrapped
        if isinstance(value, list):
            return [self.from_impl(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.from_impl(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return type(value)(self.from_impl(item) for item in value)
        if isinstance(value, dict):
            return {self.from_impl(key): self.from_impl(item) for key, item in value.items()}
        if hasattr(value, '__aenter__') and hasattr(value, '__aexit__'):
            return SyncContextManager(value, self)
        return value

    def to_impl(self, value: Any) -> Any:
        """Unwrap facades (or containers of them) into implementation objects."""
        if isinstance(value, SyncBase):
            return value._impl
        if isinstance(value, list):
            return [self.to_impl(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.to_impl(item) for item in value)
        if isinstance(value, (set, frozenset)):
            return type(value)(self.to_impl(item) for item in value)
        if isinstance(value, dict):
            return {self.to_impl(key): self.to_impl(item) for key, item in value.items()}
        return value

    def wrap_handler(self, handler: Any) -> Any:
        """Make a user callback run on the dispatch thread with facade arguments.

        The wrapper returns a loop future, so implementation code that awaits
        the callback's result (route handlers, exposed functions) waits for it,
        while fire-and-forget listeners are not blocked by it.

        The same handler maps to the same wrapper for as long as that wrapper
        is alive (the implementation holds it while the callback is
        registered), so ``remove_listener``/``unroute`` find the entry they
        registered. Once the implementation drops the wrapper, the cache entry,
        the handler reference and the wrapper's dispatch thread go with it.

        The wrapper carries the handler's name, docstring and signature (route
        dispatch reads the signature to decide whether to pass the request),
        but not a ``__wrapped__`` link.
        """
        if not callable(handler):
            return handler
        if inspect.iscoroutinefunction(handler):
            raise SyncError(
                'The sync API takes plain functions as callbacks, not async ones: '
                f'{getattr(handler, "__qualname__", handler)!r} is a coroutine function. '
                'Use the async API (pydoll) to register coroutine callbacks.'
            )
        runtime = EventLoopThread.instance()
        try:
            cached = self._handlers.get(handler)
        except TypeError:
            cached = None
        if cached is not None:
            return cached

        executor = runtime.new_dispatcher()

        def call(*args: Any) -> Any:
            return self.to_impl(handler(*[self.from_impl(arg) for arg in args]))

        def wrapper(*args: Any) -> asyncio.Future[Any]:
            return EventLoopThread.instance().dispatch(executor, call, *args)

        metadata: dict[str, object] = {
            attribute: getattr(handler, attribute, None)
            for attribute in ('__module__', '__name__', '__qualname__', '__doc__')
        }
        with contextlib.suppress(TypeError, ValueError):
            metadata['__signature__'] = inspect.signature(handler)
        for attribute, copied in metadata.items():
            if copied is not None:
                setattr(wrapper, attribute, copied)
                setattr(call, attribute, copied)
        weakref.finalize(wrapper, executor.shutdown, wait=False)
        try:
            self._handlers[handler] = wrapper
        except TypeError:
            pass
        return wrapper

    def wrap_predicate(self, predicate: Any) -> Any:
        """Make a predicate see facade arguments; it runs inline on the loop thread."""
        if not callable(predicate):
            return predicate

        def wrapper(*args: Any) -> Any:
            return predicate(*[self.from_impl(arg) for arg in args])

        return wrapper


mapping = Mapping()


class SyncBase:
    """Base of every generated facade: holds the implementation object."""

    def __init__(self, impl: Any) -> None:
        self._impl = impl
        mapping._cache[id(impl)] = self

    @classmethod
    def _wrap(cls, impl: Any) -> SyncBase:
        """Build a facade around ``impl`` without running the public constructor."""
        facade = cls.__new__(cls)
        facade._impl = impl
        return facade

    @property
    def impl(self) -> Any:
        """The underlying asynchronous object."""
        return self._impl

    def _run(self, awaitable: Any) -> Any:
        return run_sync(awaitable)

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            raise AttributeError(name)
        return mapping.from_impl(getattr(self._impl, name))

    def __repr__(self) -> str:
        return repr(self._impl)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SyncBase):
            return self._impl is other._impl
        return NotImplemented

    def __hash__(self) -> int:
        return id(self._impl)


class SyncContextManager(Generic[T]):
    """``with`` support for an asynchronous context manager."""

    def __init__(self, async_manager: Any, owner: Mapping) -> None:
        self._manager = async_manager
        self._mapping = owner

    def __enter__(self) -> T:
        return self._mapping.from_impl(run_sync(self._manager.__aenter__()))

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        return run_sync(self._manager.__aexit__(exc_type, exc, tb))
