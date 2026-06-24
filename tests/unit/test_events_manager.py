"""Unit tests for EventsManager: callbacks, special-event state, and the worker."""

from __future__ import annotations

import asyncio
from typing import Callable

import pytest

from pydoll.connection.managers import EventsManager


async def _wait_until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    """Poll an observable condition instead of sleeping a fixed amount."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError('condition not met within timeout')


@pytest.mark.asyncio
async def test_register_returns_incrementing_ids():
    manager = EventsManager()
    assert manager.register_callback('A', lambda event: None) == 1
    assert manager.register_callback('B', lambda event: None) == 2


@pytest.mark.asyncio
async def test_remove_callback_reports_whether_it_existed():
    manager = EventsManager()
    callback_id = manager.register_callback('A', lambda event: None)
    assert manager.remove_callback(callback_id) is True
    assert manager.remove_callback(callback_id) is False
    assert manager.remove_callback(999) is False


@pytest.mark.asyncio
async def test_clear_callbacks_removes_all():
    manager = EventsManager()
    callback_id = manager.register_callback('A', lambda event: None)
    manager.clear_callbacks()
    assert manager.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_process_event_triggers_sync_callback():
    manager = EventsManager()
    received = []
    manager.register_callback('Page.loadEventFired', received.append)
    event = {'method': 'Page.loadEventFired', 'params': {'frame': 'main'}}
    await manager.process_event(event)
    assert received == [event]


@pytest.mark.asyncio
async def test_process_event_awaits_async_callback():
    manager = EventsManager()
    received = []

    async def handler(event):
        received.append(event)

    manager.register_callback('X', handler)
    await manager.process_event({'method': 'X', 'params': {}})
    assert len(received) == 1


@pytest.mark.asyncio
async def test_temporary_callback_runs_once_then_is_removed():
    manager = EventsManager()
    received = []
    callback_id = manager.register_callback('X', received.append, temporary=True)
    await manager.process_event({'method': 'X', 'params': {}})
    await manager.process_event({'method': 'X', 'params': {}})
    assert len(received) == 1
    assert manager.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_callback_exception_does_not_stop_other_callbacks():
    manager = EventsManager()
    order = []

    def failing(event):
        order.append('failing')
        raise RuntimeError('boom')

    def healthy(event):
        order.append('healthy')

    manager.register_callback('X', failing)
    manager.register_callback('X', healthy)
    await manager.process_event({'method': 'X', 'params': {}})
    assert order == ['failing', 'healthy']


@pytest.mark.asyncio
async def test_event_without_method_is_discarded():
    manager = EventsManager()
    received = []
    manager.register_callback('X', received.append)
    await manager.process_event({})
    await manager.process_event({'params': {}})
    assert received == []


@pytest.mark.asyncio
async def test_network_request_event_appended_to_logs():
    manager = EventsManager()
    event = {'method': 'Network.requestWillBeSent', 'params': {'requestId': 'r1'}}
    await manager.process_event(event)
    assert list(manager.network_logs) == [event]


@pytest.mark.asyncio
async def test_dialog_state_tracks_open_and_close():
    manager = EventsManager()
    assert not manager.dialog
    opening = {'method': 'Page.javascriptDialogOpening', 'params': {'message': 'hi'}}
    await manager.process_event(opening)
    assert manager.dialog
    assert manager.dialog['params'] == {'message': 'hi'}
    await manager.process_event({'method': 'Page.javascriptDialogClosed'})
    assert not manager.dialog


@pytest.mark.asyncio
async def test_worker_processes_enqueued_events_in_order():
    manager = EventsManager()
    received = []
    manager.register_callback('E', received.append)
    manager.start()
    try:
        manager.enqueue_event({'method': 'E', 'params': {'n': 1}})
        manager.enqueue_event({'method': 'E', 'params': {'n': 2}})
        await _wait_until(lambda: len(received) == 2)
    finally:
        await manager.stop()
    assert [event['params']['n'] for event in received] == [1, 2]
