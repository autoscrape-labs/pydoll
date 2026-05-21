import asyncio
import json
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import websockets
from websockets.protocol import State

from pydoll import exceptions
from pydoll.connection import ConnectionHandler


@pytest_asyncio.fixture
async def connection_handler():
    handler = ConnectionHandler(connection_port=9222)
    handler._ws_connection = AsyncMock()
    handler._ws_connection.state = State.OPEN
    handler._receive_task = MagicMock()
    handler._receive_task.done.return_value = False
    yield handler
    await handler._events_handler.stop()


@pytest_asyncio.fixture
async def connection_handler_closed():
    handler = ConnectionHandler(
        connection_port=9222,
        ws_address_resolver=AsyncMock(return_value='ws://localhost:9222'),
        ws_connector=AsyncMock(),
    )
    handler._ws_connection = AsyncMock()
    handler._ws_connection.state = State.CLOSED
    yield handler
    await handler._events_handler.stop()


@pytest_asyncio.fixture
async def connection_handler_with_page_id():
    handler = ConnectionHandler(
        page_id='ABCD',
        connection_port=9222,
        ws_address_resolver=AsyncMock(return_value='ws://localhost:9222'),
        ws_connector=AsyncMock(),
    )
    handler._ws_connection = AsyncMock()
    handler._ws_connection.state = State.CLOSED
    yield handler
    await handler._events_handler.stop()


@pytest.mark.asyncio
async def test_resolve_ws_address_priority_ws_address_over_port_and_page():
    handler = ConnectionHandler(
        connection_port=9333,
        page_id='SHOULD_NOT_BE_USED',
        ws_address='ws://host:9999/devtools/page/REAL',
        ws_address_resolver=AsyncMock(return_value='ws://host:9333/devtools/browser/ALT'),
        ws_connector=AsyncMock(),
    )
    # Should return the explicit ws_address regardless of others
    resolved = await handler._resolve_ws_address()
    assert resolved == 'ws://host:9999/devtools/page/REAL'


@pytest.mark.asyncio
async def test_ping_success(connection_handler):
    connection_handler._ws_connection.ping = AsyncMock()
    result = await connection_handler.ping()
    assert result is True


@pytest.mark.asyncio
async def test_ping_failure(connection_handler):
    connection_handler._ws_connection.ping = AsyncMock(
        side_effect=Exception('Ping failed')
    )
    result = await connection_handler.ping()
    assert result is False


@pytest.mark.asyncio
async def test_execute_command_success(connection_handler):
    command = {'id': 1, 'method': 'SomeMethod'}
    response = json.dumps({'id': 1, 'result': 'success'})

    connection_handler._ws_connection.send = AsyncMock()
    future = asyncio.Future()
    future.set_result(response)
    connection_handler._command_manager.create_command_future = MagicMock(
        return_value=future
    )
    result = await connection_handler.execute_command(command)
    assert result == {'id': 1, 'result': 'success'}


@pytest.mark.asyncio
async def test_execute_command_timeout(connection_handler):
    command = {'id': 2, 'method': 'TimeoutMethod'}

    connection_handler._ws_connection.send = AsyncMock()
    connection_handler._command_manager.create_command_future = MagicMock(
        return_value=asyncio.Future()
    )

    with pytest.raises(exceptions.CommandExecutionTimeout):
        await connection_handler.execute_command(command, timeout=0.1)


@pytest.mark.asyncio
async def test_execute_command_connection_closed_exception(connection_handler):
    connection_handler._ws_connection.send = AsyncMock(
        side_effect=websockets.ConnectionClosed(
            1000, 'Normal Closure', rcvd_then_sent=True
        )
    )
    connection_handler._ws_connection.close = AsyncMock()
    connection_handler._receive_task = AsyncMock(spec=asyncio.Task)
    connection_handler._receive_task.done = MagicMock(return_value=False)
    with pytest.raises(exceptions.WebSocketConnectionClosed):
        await connection_handler.execute_command({
            'id': 1,
            'method': 'SomeMethod',
        })


@pytest.mark.asyncio
async def test_register_callback(connection_handler):
    connection_handler._events_handler.register_callback = MagicMock(
        return_value=123
    )
    callback_id = await connection_handler.register_callback(
        'event', lambda x: x
    )
    assert callback_id == 123


@pytest.mark.asyncio
async def test_remove_callback(connection_handler):
    connection_handler._events_handler.remove_callback = MagicMock(
        return_value=True
    )
    result = await connection_handler.remove_callback(123)
    assert result is True


@pytest.mark.asyncio
async def test_clear_callbacks(connection_handler):
    connection_handler._events_handler.clear_callbacks = MagicMock(
        return_value=None
    )
    result = await connection_handler.clear_callbacks()
    connection_handler._events_handler.clear_callbacks.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_close(connection_handler):
    connection_handler._ws_connection.close = AsyncMock()
    connection_handler.clear_callbacks = AsyncMock()

    await connection_handler.close()
    connection_handler.clear_callbacks.assert_awaited_once()
    connection_handler._ws_connection.close.assert_awaited_once()

    connection_handler._ws_connection.close.side_effect = websockets.ConnectionClosed(
        1000, 'Normal Closure', rcvd_then_sent=True
    )
    await connection_handler.close()


@pytest.mark.asyncio
async def test_execute_command_connection_closed(connection_handler_closed):
    mock_connector = AsyncMock(
        return_value=connection_handler_closed._ws_connection
    )
    connection_handler_closed._ws_connector = mock_connector

    command = {'id': 1, 'method': 'SomeMethod'}
    response = json.dumps({'id': 1, 'result': 'success'})

    connection_handler_closed._ws_connection.send = AsyncMock()
    future = asyncio.Future()
    future.set_result(response)
    connection_handler_closed._command_manager.create_command_future = (
        MagicMock(return_value=future)
    )
    result = await connection_handler_closed.execute_command(command)
    mock_connector.assert_awaited_once()  # Verifica se tentou reconectar
    connection_handler_closed._ws_connection.send.assert_awaited_once_with(
        json.dumps(command)
    )
    assert result == {'id': 1, 'result': 'success'}


@pytest.mark.asyncio
async def test__is_command_response_true(connection_handler):
    command = {'id': 1, 'method': 'SomeMethod'}
    result = connection_handler._is_command_response(command)
    assert result is True


@pytest.mark.asyncio
async def test__is_command_response_false(connection_handler):
    command = {'id': 'string', 'method': 'SomeMethod'}
    result = connection_handler._is_command_response(command)
    assert result is False


@pytest.mark.asyncio
async def test__resolve_ws_address_with_page_id(
    connection_handler_with_page_id,
):
    result = await connection_handler_with_page_id._resolve_ws_address()
    assert result == 'ws://localhost:9222/devtools/page/ABCD'


@pytest.mark.asyncio
async def test__incoming_messages(connection_handler):
    connection_handler._ws_connection.recv = AsyncMock(
        return_value='{"id": 1, "method": "SomeMethod"}'
    )

    try:
        async_generator = connection_handler._incoming_messages()
        result = await anext(async_generator)
    finally:
        await async_generator.aclose()

    assert result == '{"id": 1, "method": "SomeMethod"}'


@pytest.mark.asyncio
async def test__process_single_message(connection_handler):
    raw_message = '{"id": 1, "method": "SomeMethod"}'
    connection_handler._command_manager.resolve_command = MagicMock()
    connection_handler._process_single_message(raw_message)
    connection_handler._command_manager.resolve_command.assert_called_once_with(
        1, raw_message
    )


@pytest.mark.asyncio
async def test__process_single_message_invalid_command(connection_handler):
    raw_message = 'not a valid JSON'
    result = connection_handler._process_single_message(raw_message)
    assert result is None


@pytest.mark.asyncio
async def test__process_single_message_event_is_enqueued(connection_handler):
    event = {'method': 'SomeEvent'}
    connection_handler._events_handler.enqueue_event = MagicMock()
    connection_handler._process_single_message(json.dumps(event))
    connection_handler._events_handler.enqueue_event.assert_called_once_with(event)


@pytest.mark.asyncio
async def test__process_single_message_event_with_callback(connection_handler):
    event = {'method': 'SomeEvent'}
    callback = MagicMock(return_value=None)
    await connection_handler.register_callback('SomeEvent', callback)
    connection_handler._events_handler.start()
    connection_handler._process_single_message(json.dumps(event))
    await asyncio.wait_for(connection_handler._events_handler._event_queue.join(), 1)
    callback.assert_called_once_with(event)
    await connection_handler._events_handler.stop()


@pytest.mark.asyncio
async def test__receive_events_flow(connection_handler):
    async def fake_incoming_messages():
        yield '{"id": 1, "method": "TestCommand"}'
        yield '{"method": "TestEvent"}'

    connection_handler._incoming_messages = fake_incoming_messages

    connection_handler._command_manager.resolve_command = MagicMock()
    connection_handler._events_handler.enqueue_event = MagicMock()

    await connection_handler._receive_events()

    connection_handler._command_manager.resolve_command.assert_called_once_with(
        1, '{"id": 1, "method": "TestCommand"}'
    )
    connection_handler._events_handler.enqueue_event.assert_called_once_with({
        'method': 'TestEvent'
    })


@pytest.mark.asyncio
async def test__receive_events_connection_closed(connection_handler):
    async def fake_incoming_messages_connection_closed():
        raise websockets.ConnectionClosed(
            1000, 'Normal Closure', rcvd_then_sent=True
        )
        yield  # Garante que seja um async generator

    connection_handler._incoming_messages = (
        fake_incoming_messages_connection_closed
    )
    await connection_handler._receive_events()


@pytest.mark.asyncio
async def test__receive_events_unexpected_exception_does_not_propagate(connection_handler):
    async def fake_incoming_messages_unexpected_error():
        raise ValueError('Unexpected error in async generator')
        yield  # Garante que seja um async generator

    connection_handler._incoming_messages = (
        fake_incoming_messages_unexpected_error
    )
    connection_handler._command_manager.fail_all_pending = MagicMock()
    connection_handler._events_handler.stop = AsyncMock()

    # A fatal loop error must NOT propagate out of the (never-awaited) receive task;
    # it must fail pending commands and stop the event worker instead.
    await connection_handler._receive_events()

    connection_handler._command_manager.fail_all_pending.assert_called_once()
    connection_handler._events_handler.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test__aenter__(connection_handler):
    result = await connection_handler.__aenter__()
    assert result is connection_handler


@pytest.mark.asyncio
async def test__aexit__(connection_handler):
    await connection_handler.register_callback('SomeEvent', MagicMock())
    connection_handler.clear_callbacks = AsyncMock()
    connection_handler._ws_connection.close = AsyncMock()
    await connection_handler.__aexit__(None, None, None)
    connection_handler.clear_callbacks.assert_awaited_once()
    connection_handler._ws_connection.close.assert_awaited_once()


def test__repr__(connection_handler):
    result = connection_handler.__repr__()
    assert result == 'ConnectionHandler(port=9222)'


def test__str__(connection_handler):
    result = connection_handler.__str__()
    assert result == 'ConnectionHandler(port=9222)'


@pytest.mark.asyncio
async def test_concurrent_send_does_not_raise(connection_handler):
    connection_handler._ws_connection.send = AsyncMock()

    futures = []
    for i in range(1, 6):
        response = json.dumps({'id': i, 'result': f'ok{i}'})
        future = asyncio.Future()
        future.set_result(response)
        futures.append(future)

    side_effects = iter(futures)
    connection_handler._command_manager.create_command_future = MagicMock(
        side_effect=lambda cmd: next(side_effects)
    )

    commands = [{'id': i, 'method': f'Method{i}'} for i in range(1, 6)]
    results = await asyncio.gather(
        *(connection_handler.execute_command(cmd) for cmd in commands)
    )

    assert len(results) == 5
    assert connection_handler._ws_connection.send.await_count == 5


@pytest.mark.asyncio
async def test_single_receiver_task_created(connection_handler_closed):
    mock_ws = AsyncMock()
    mock_ws.state = State.OPEN

    mock_connector = AsyncMock(return_value=mock_ws)
    connection_handler_closed._ws_connector = mock_connector

    await connection_handler_closed._ensure_active_connection()

    assert connection_handler_closed._receive_task is not None
    first_task = connection_handler_closed._receive_task

    mock_ws.state = State.OPEN
    connection_handler_closed._ws_connection = mock_ws
    await connection_handler_closed._ensure_active_connection()

    assert connection_handler_closed._receive_task is first_task
    first_task.cancel()
    with suppress(asyncio.CancelledError):
        await first_task


def _make_parked_ws():
    """A fake open WebSocket whose recv() blocks, so the receive loop parks."""
    ws = AsyncMock()
    ws.state = State.OPEN

    async def _blocking_recv():
        await asyncio.sleep(3600)

    ws.recv = _blocking_recv
    return ws


@pytest.mark.asyncio
async def test_is_connection_healthy_requires_live_receive_task(connection_handler):
    connection_handler._ws_connection.state = State.OPEN

    connection_handler._receive_task = MagicMock()
    connection_handler._receive_task.done.return_value = False
    assert connection_handler._is_connection_healthy() is True

    connection_handler._receive_task.done.return_value = True
    assert connection_handler._is_connection_healthy() is False

    connection_handler._receive_task = None
    assert connection_handler._is_connection_healthy() is False


@pytest.mark.asyncio
async def test_dead_receive_task_triggers_reconnect(connection_handler):
    dead_task = MagicMock()
    dead_task.done.return_value = True
    connection_handler._receive_task = dead_task
    connection_handler._establish_new_connection = AsyncMock()

    await connection_handler._ensure_active_connection()

    connection_handler._establish_new_connection.assert_awaited_once()


@pytest.mark.asyncio
async def test_healthy_connection_is_not_reestablished(connection_handler):
    connection_handler._establish_new_connection = AsyncMock()

    await connection_handler._ensure_active_connection()

    connection_handler._establish_new_connection.assert_not_awaited()


@pytest.mark.asyncio
async def test_concurrent_ensure_active_connects_only_once(connection_handler_closed):
    connect_calls = 0

    async def slow_connect(address, **kwargs):
        nonlocal connect_calls
        connect_calls += 1
        await asyncio.sleep(0.01)
        return _make_parked_ws()

    connection_handler_closed._ws_connector = slow_connect

    await asyncio.gather(
        *(connection_handler_closed._ensure_active_connection() for _ in range(10))
    )

    assert connect_calls == 1
    await connection_handler_closed.close()


@pytest.mark.asyncio
async def test_handle_connection_loss_fails_pending_commands(connection_handler):
    f1 = connection_handler._command_manager.create_command_future({'method': 'A'})
    f2 = connection_handler._command_manager.create_command_future({'method': 'B'})

    await connection_handler._handle_connection_loss()

    assert f1.done() and f2.done()
    for future in (f1, f2):
        with pytest.raises(exceptions.WebSocketConnectionClosed):
            future.result()


@pytest.mark.asyncio
async def test_receive_loop_skips_unparseable_message(connection_handler):
    resolved = []

    async def fake_incoming():
        yield 'not valid json'
        yield '{"id": 1, "result": {}}'

    connection_handler._incoming_messages = fake_incoming
    connection_handler._command_manager.resolve_command = MagicMock(
        side_effect=lambda cmd_id, raw: resolved.append(cmd_id)
    )

    await connection_handler._receive_events()

    assert resolved == [1]


@pytest.mark.asyncio
async def test_receive_loop_survives_processing_error(connection_handler):
    seen = []

    def resolve(cmd_id, raw):
        seen.append(cmd_id)
        if cmd_id == 1:
            raise RuntimeError('processing blew up')

    connection_handler._command_manager.resolve_command = resolve

    async def fake_incoming():
        yield '{"id": 1, "result": {}}'
        yield '{"id": 2, "result": {}}'

    connection_handler._incoming_messages = fake_incoming

    await connection_handler._receive_events()

    assert seen == [1, 2]


@pytest.mark.asyncio
async def test_establish_uses_unbounded_max_size_and_starts_worker(connection_handler_closed):
    captured = {}

    async def connector(address, **kwargs):
        captured.update(kwargs)
        return _make_parked_ws()

    connection_handler_closed._ws_connector = connector

    await connection_handler_closed._establish_new_connection()

    assert captured.get('max_size') is None
    worker = connection_handler_closed._events_handler._worker_task
    assert worker is not None and not worker.done()

    await connection_handler_closed.close()
    assert connection_handler_closed._events_handler._worker_task is None


@pytest.mark.asyncio
async def test_receive_loop_exit_stops_event_worker(connection_handler):
    connection_handler._events_handler.start()
    worker = connection_handler._events_handler._worker_task

    async def fake_incoming():
        raise websockets.ConnectionClosed(1006, 'gone', rcvd_then_sent=True)
        yield

    connection_handler._incoming_messages = fake_incoming

    await connection_handler._receive_events()

    assert worker.done()
    assert connection_handler._events_handler._worker_task is None


@pytest.mark.asyncio
async def test_command_ids_unique_under_concurrent_calls(connection_handler):
    assigned_ids = []
    for _ in range(100):
        cmd = {'method': 'Test'}
        connection_handler._command_manager.create_command_future(cmd)
        assigned_ids.append(cmd['id'])

    assert len(assigned_ids) == 100
    assert len(set(assigned_ids)) == 100
