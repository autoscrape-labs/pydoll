import asyncio
import json
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
    return handler


@pytest_asyncio.fixture
async def connection_handler_closed():
    handler = ConnectionHandler(
        connection_port=9222,
        ws_address_resolver=AsyncMock(return_value='ws://localhost:9222'),
        ws_connector=AsyncMock(),
    )
    handler._ws_connection = AsyncMock()
    handler._ws_connection.state = State.CLOSED
    return handler


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
    return handler


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
    async_generator = connection_handler._incoming_messages()
    result = await anext(async_generator)
    assert result == '{"id": 1, "method": "SomeMethod"}'


@pytest.mark.asyncio
async def test__process_single_message(connection_handler):
    raw_message = '{"id": 1, "method": "SomeMethod"}'
    connection_handler._command_manager.resolve_command = MagicMock()
    await connection_handler._process_single_message(raw_message)
    connection_handler._command_manager.resolve_command.assert_called_once_with(
        1, raw_message
    )


@pytest.mark.asyncio
async def test__process_single_message_invalid_command(connection_handler):
    raw_message = 'not a valid JSON'
    result = await connection_handler._process_single_message(raw_message)
    assert result is None


@pytest.mark.asyncio
async def test__process_single_message_event(connection_handler):
    event = {'method': 'SomeEvent'}
    connection_handler._events_handler.process_event = AsyncMock()
    await connection_handler._process_single_message(json.dumps(event))
    connection_handler._events_handler.process_event.assert_called_once_with(
        event
    )


@pytest.mark.asyncio
async def test__process_single_message_event_with_callback(connection_handler):
    event = {'method': 'SomeEvent'}
    callback = MagicMock(return_value=None)
    await connection_handler.register_callback('SomeEvent', callback)
    await connection_handler._process_single_message(json.dumps(event))
    callback.assert_called_once_with(event)


@pytest.mark.asyncio
async def test__receive_events_flow(connection_handler):
    async def fake_incoming_messages():
        yield '{"id": 1, "method": "TestCommand"}'
        yield '{"method": "TestEvent"}'

    connection_handler._incoming_messages = fake_incoming_messages

    connection_handler._handle_command_message = AsyncMock()
    connection_handler._handle_event_message = AsyncMock()

    await connection_handler._receive_events()

    connection_handler._handle_command_message.assert_awaited_once_with({
        'id': 1,
        'method': 'TestCommand',
    })
    connection_handler._handle_event_message.assert_awaited_once_with({
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
async def test__receive_events_unexpected_exception(connection_handler):
    async def fake_incoming_messages_unexpected_error():
        raise ValueError('Unexpected error in async generator')
        yield  # Garante que seja um async generator

    connection_handler._incoming_messages = (
        fake_incoming_messages_unexpected_error
    )

    with pytest.raises(
        ValueError, match='Unexpected error in async generator'
    ):
        await connection_handler._receive_events()


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
