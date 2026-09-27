"""Lifecycle guarantees of the sync runtime: no leaks, isolated handlers, restartable loop."""

from __future__ import annotations

import asyncio
import gc
import inspect
import logging
import threading
import time
import weakref

import pytest

from pydoll.browser.options import ChromiumOptions
from pydoll.sync import Chrome, Tab
from pydoll.sync._runtime import EventLoopThread, Mapping, SyncBase, SyncError, mapping, run_sync


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


def _callback_threads() -> int:
    return sum(
        1 for thread in threading.enumerate() if thread.name.startswith('pydoll-sync-callbacks')
    )


def test_removed_callbacks_release_their_wrapper_and_dispatch_thread(fake_tab, fake_conn) -> None:
    tab = mapping.from_impl(fake_tab)
    assert isinstance(tab, Tab)
    gc.collect()
    threads_before = _callback_threads()
    handlers_before = len(mapping._handlers)

    callback_ids = [tab.on('Page.loadEventFired', lambda event: None) for _ in range(30)]
    wrappers = fake_conn.callbacks_for('Page.loadEventFired')
    assert len(wrappers) == 30
    assert len(mapping._handlers) == handlers_before + 30
    for wrapper in wrappers:
        run_sync(run_sync(_schedule(wrapper, {'method': 'Page.loadEventFired'})))
    assert _callback_threads() >= 30

    for callback_id in callback_ids:
        tab.remove_callback(callback_id)
    del wrapper, wrappers
    gc.collect()
    deadline = time.monotonic() + 5
    while _callback_threads() > threads_before and time.monotonic() < deadline:
        time.sleep(0.01)
    assert _callback_threads() <= threads_before
    assert len(mapping._handlers) == handlers_before


def test_wrapper_keeps_the_handler_name_without_pinning_it(local_mapping: Mapping) -> None:
    def named_handler(event: dict) -> None:
        """Handles events."""

    wrapper = local_mapping.wrap_handler(named_handler)
    assert wrapper.__name__ == 'named_handler'
    assert wrapper.__doc__ == 'Handles events.'
    assert list(inspect.signature(wrapper).parameters) == ['event']
    assert not hasattr(wrapper, '__wrapped__')
    ref = weakref.ref(wrapper)
    del wrapper
    gc.collect()
    assert ref() is None
    assert len(local_mapping._handlers) == 0


def test_async_handlers_are_rejected_instead_of_silently_ignored(local_mapping: Mapping) -> None:
    async def handler(event: dict) -> None:
        pass

    with pytest.raises(SyncError, match='coroutine function'):
        local_mapping.wrap_handler(handler)


def test_callback_failures_are_logged_with_the_handler_name(
    local_mapping: Mapping, caplog: pytest.LogCaptureFixture
) -> None:
    def explode(event: dict) -> None:
        raise ValueError('boom')

    wrapper = local_mapping.wrap_handler(explode)
    with caplog.at_level(logging.ERROR, logger='pydoll.sync._runtime'):
        future = run_sync(_schedule(wrapper, {}))
        with pytest.raises(ValueError, match='boom'):
            run_sync(future)
        deadline = time.monotonic() + 2
        while not caplog.records and time.monotonic() < deadline:
            time.sleep(0.01)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert 'explode' in record.getMessage()
    assert record.exc_info is not None and record.exc_info[0] is ValueError


def test_constructed_facade_is_the_one_its_context_manager_yields() -> None:
    browser = Chrome()
    assert mapping.from_impl(browser.impl) is browser
    assert browser.__enter__() is browser


def test_instance_attributes_are_assignable_through_the_facade() -> None:
    browser = Chrome()
    options = ChromiumOptions()
    browser.options = options
    assert browser.impl.options is options
    assert browser.options is options


def test_sets_and_dict_keys_are_converted_both_ways(local_mapping: Mapping) -> None:
    impl = Impl('a')
    facade = local_mapping.from_impl(impl)
    converted = local_mapping.from_impl({impl: frozenset({impl}), 'plain': {impl}})
    assert converted == {facade: frozenset({facade}), 'plain': {facade}}
    assert isinstance(converted[facade], frozenset)
    restored = local_mapping.to_impl(converted)
    assert restored == {impl: frozenset({impl}), 'plain': {impl}}
    assert next(iter(restored)) is impl


def test_shutdown_cancels_pending_tasks_and_closes_the_loop() -> None:
    runtime = EventLoopThread.instance()
    started = threading.Event()

    async def hang() -> None:
        started.set()
        await asyncio.sleep(60)

    pending = asyncio.run_coroutine_threadsafe(hang(), runtime.loop)
    assert started.wait(2)
    runtime.shutdown()
    assert pending.cancelled()
    assert runtime.loop.is_closed()
    assert not runtime._thread.is_alive()
    assert run_sync(_value(6)) == 6
