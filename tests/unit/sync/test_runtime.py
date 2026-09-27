"""Lifecycle guarantees of the sync runtime: no leaks, isolated handlers, restartable loop."""

from __future__ import annotations

import asyncio
import gc
import threading
import time
import weakref

import pytest

from pydoll.sync._runtime import EventLoopThread, Mapping, SyncBase, SyncError, run_sync


class Impl:
    def __init__(self, name: str) -> None:
        self.name = name


class Facade(SyncBase):
    pass


@pytest.fixture
def local_mapping() -> Mapping:
    mapping = Mapping()
    mapping.register(Impl, Facade)
    return mapping


def test_facade_identity_while_alive_and_no_retention_afterwards(local_mapping: Mapping) -> None:
    impl = Impl('a')
    first = local_mapping.from_impl(impl)
    assert local_mapping.from_impl(impl) is first
    ref = weakref.ref(first)
    del first
    gc.collect()
    assert ref() is None
    assert len(local_mapping._cache) == 0
    impl_ref = weakref.ref(impl)
    del impl
    gc.collect()
    assert impl_ref() is None


def test_cache_does_not_confuse_a_new_impl_with_a_dead_one(local_mapping: Mapping) -> None:
    facade = local_mapping.from_impl(Impl('a'))
    other = Impl('b')
    assert local_mapping.from_impl(other) is not facade
    assert local_mapping.from_impl(other)._impl is other


def test_handlers_run_on_their_own_threads_and_do_not_block_each_other(
    local_mapping: Mapping,
) -> None:
    order: list[str] = []
    started = threading.Event()

    def slow(value: str) -> str:
        started.set()
        time.sleep(0.4)
        order.append('slow')
        return value

    def fast(value: str) -> str:
        order.append('fast')
        return value

    wrapped_slow = local_mapping.wrap_handler(slow)
    wrapped_fast = local_mapping.wrap_handler(fast)
    slow_future = run_sync(_schedule(wrapped_slow, 'x'))
    started.wait(2)
    assert run_sync(wrapped_fast('y')) == 'y'
    assert order == ['fast']
    assert run_sync(slow_future) == 'x'
    assert order == ['fast', 'slow']


def test_same_handler_keeps_its_wrapper_and_order(local_mapping: Mapping) -> None:
    seen: list[int] = []

    def handler(value: int) -> None:
        time.sleep(0.01)
        seen.append(value)

    wrapper = local_mapping.wrap_handler(handler)
    assert local_mapping.wrap_handler(handler) is wrapper
    futures = [run_sync(_schedule(wrapper, index)) for index in range(5)]
    for future in futures:
        run_sync(future)
    assert seen == [0, 1, 2, 3, 4]


def test_shutdown_then_reuse_starts_a_fresh_loop() -> None:
    first = EventLoopThread.instance()
    assert run_sync(_value(1)) == 1
    first.shutdown()
    with pytest.raises(SyncError, match='shut down'):
        first.run(_value(2))
    second = EventLoopThread.instance()
    assert second is not first
    assert run_sync(_value(3)) == 3


def test_fork_hook_drops_the_singleton() -> None:
    before = EventLoopThread.instance()
    EventLoopThread._forget()
    after = EventLoopThread.instance()
    assert after is not before
    assert run_sync(_value(4)) == 4
    before.shutdown()


def test_calls_from_the_loop_thread_are_rejected() -> None:
    runtime = EventLoopThread.instance()
    outcome: list[BaseException] = []

    def misuse() -> None:
        try:
            runtime.run(_value(5))
        except SyncError as error:
            outcome.append(error)

    runtime.loop.call_soon_threadsafe(misuse)
    deadline = time.monotonic() + 2
    while not outcome and time.monotonic() < deadline:
        time.sleep(0.01)
    assert outcome


async def _value(value: int) -> int:
    return value


async def _schedule(wrapper, *args):
    """Call a wrapped handler from the loop thread, as pydoll's event dispatch does."""
    return wrapper(*args)


def test_run_accepts_futures_from_the_loop() -> None:
    async def make_future() -> asyncio.Future[str]:
        future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        future.set_result('done')
        return future

    assert run_sync(run_sync(make_future())) == 'done'
