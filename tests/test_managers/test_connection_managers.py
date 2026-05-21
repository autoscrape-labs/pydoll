import asyncio

import pytest

from pydoll import exceptions
from pydoll.connection.managers import CommandsManager, EventsManager
from pydoll.connection.managers.events_manager import MAX_NETWORK_LOGS


@pytest.fixture
def commands_manager():
    """Retorna uma instância fresca de CommandManager para os testes."""
    return CommandsManager()


@pytest.fixture
def events_manager():
    """Retorna uma instância fresca de EventsManager para os testes."""
    return EventsManager()


def test_create_command_future(commands_manager):
    test_command = {'method': 'TestMethod'}
    future_result = commands_manager.create_command_future(test_command)

    # Verifica se o ID foi atribuído corretamente
    assert test_command['id'] == 1, 'The first command ID should be 1'
    # Verifica se o future foi armazenado no dicionário de pendentes
    assert 1 in commands_manager._pending_commands
    assert commands_manager._pending_commands[1] is future_result

    # Cria um segundo comando e verifica o incremento do ID
    second_command = {'method': 'SecondMethod'}
    future_second = commands_manager.create_command_future(second_command)
    assert second_command['id'] == 2, 'The second command ID should be 2'
    assert 2 in commands_manager._pending_commands
    assert commands_manager._pending_commands[2] is future_second


def test_resolve_command(commands_manager):
    test_command = {'method': 'TestMethod'}
    future_result = commands_manager.create_command_future(test_command)
    result_payload = '{"result": "success"}'

    # O future não deve estar concluído antes da resolução
    assert not future_result.done(), (
        'The future should not be completed before resolution'
    )

    # Resolve o comando e verifica o resultado
    commands_manager.resolve_command(1, result_payload)
    assert future_result.done(), (
        'The future should be completed after resolution'
    )
    assert future_result.result() == result_payload, (
        'The future result does not match the expected result'
    )
    # O comando pendente deve ser removido
    assert 1 not in commands_manager._pending_commands


def test_resolve_unknown_command(commands_manager):
    test_command = {'method': 'TestMethod'}
    future_result = commands_manager.create_command_future(test_command)

    # Tenta resolver um ID inexistente; o future original deve permanecer pendente
    commands_manager.resolve_command(999, '{"result": "ignored"}')
    assert not future_result.done(), (
        'The future should not be completed after resolving an unknown command'
    )


def test_remove_pending_command(commands_manager):
    test_command = {'method': 'TestMethod'}
    _ = commands_manager.create_command_future(test_command)

    # Remove o comando pendente e verifica se ele foi removido
    commands_manager.remove_pending_command(1)
    assert 1 not in commands_manager._pending_commands, (
        'The pending command should be removed'
    )
    commands_manager.remove_pending_command(1)


def test_register_callback_success(events_manager):
    dummy_callback = lambda event: event
    callback_id = events_manager.register_callback('TestEvent', dummy_callback)

    assert callback_id == 1, 'The first callback ID should be 1'
    assert callback_id in events_manager._event_callbacks, (
        'The callback must be registered'
    )
    callback_info = events_manager._event_callbacks[callback_id]
    assert callback_info['temporary'] is False, (
        'The temporary flag should be False by default'
    )


def test_remove_existing_callback(events_manager):
    dummy_callback = lambda event: event
    callback_id = events_manager.register_callback('TestEvent', dummy_callback)
    removal_result = events_manager.remove_callback(callback_id)

    assert removal_result is True, (
        'The removal of a existing callback should be successful'
    )
    assert callback_id not in events_manager._event_callbacks, (
        'The callback should be removed'
    )


def test_remove_nonexistent_callback(events_manager):
    removal_result = events_manager.remove_callback(999)
    assert removal_result is False, (
        'The removal of a nonexistent callback should return False'
    )


def test_clear_callbacks(events_manager):
    dummy_callback = lambda event: event
    events_manager.register_callback('EventA', dummy_callback)
    events_manager.register_callback('EventB', dummy_callback)

    events_manager.clear_callbacks()
    assert len(events_manager._event_callbacks) == 0, (
        'All callbacks should be cleared'
    )


@pytest.mark.asyncio
async def test_process_event_updates_network_logs(events_manager):
    assert len(events_manager.network_logs) == 0
    network_event = {
        'method': 'Network.requestWillBeSent',
        'url': 'http://example.com',
    }

    await events_manager.process_event(network_event)

    assert network_event in events_manager.network_logs, (
        'The network event should be added to the logs'
    )


@pytest.mark.asyncio
async def test_process_event_triggers_callbacks(events_manager):
    callback_results = []

    def sync_callback(event):
        callback_results.append(('sync', event.get('value')))

    async def async_callback(event):
        callback_results.append(('async', event.get('value')))

    sync_callback_id = events_manager.register_callback(
        'MyCustomEvent', sync_callback, temporary=True
    )
    async_callback_id = events_manager.register_callback(
        'MyCustomEvent', async_callback, temporary=False
    )

    test_event = {'method': 'MyCustomEvent', 'value': 123}
    await events_manager.process_event(test_event)

    assert ('sync', 123) in callback_results, (
        'The synchronous callback was not triggered correctly'
    )
    assert ('async', 123) in callback_results, (
        'The asynchronous callback was not triggered correctly'
    )

    assert sync_callback_id not in events_manager._event_callbacks, (
        'The temporary callback should be removed after execution'
    )

    assert async_callback_id in events_manager._event_callbacks, (
        'The permanent callback should remain registered'
    )


@pytest.mark.asyncio
async def test_trigger_callbacks_error_handling(events_manager, caplog):
    def faulty_callback(event):
        raise ValueError('Error in callback')

    faulty_callback_id = events_manager.register_callback(
        'ErrorEvent', faulty_callback, temporary=True
    )
    test_event = {'method': 'ErrorEvent'}

    await events_manager.process_event(test_event)
    assert faulty_callback_id not in events_manager._event_callbacks, (
        'The callback with error should be removed after execution'
    )
    error_logged = any(
        'Error in callback' in record.message for record in caplog.records
    )
    assert error_logged, 'The error in the callback should be logged'


# --- CommandsManager.fail_all_pending ---


def test_fail_all_pending_sets_exception_on_every_future(commands_manager):
    futures = [
        commands_manager.create_command_future({'method': f'M{i}'}) for i in range(3)
    ]

    commands_manager.fail_all_pending(exceptions.WebSocketConnectionClosed())

    assert commands_manager._pending_commands == {}
    for future in futures:
        assert future.done()
        with pytest.raises(exceptions.WebSocketConnectionClosed):
            future.result()


def test_fail_all_pending_skips_already_resolved(commands_manager):
    future = commands_manager.create_command_future({'method': 'M'})
    commands_manager.resolve_command(1, '{"ok": true}')

    # No pending futures remain; calling must be a no-op and must not raise.
    commands_manager.fail_all_pending(exceptions.WebSocketConnectionClosed())

    assert future.result() == '{"ok": true}'


def test_fail_all_pending_empty_is_noop(commands_manager):
    commands_manager.fail_all_pending(exceptions.WebSocketConnectionClosed())
    assert commands_manager._pending_commands == {}


def test_resolve_command_ignores_cancelled_future(commands_manager):
    future = commands_manager.create_command_future({'method': 'M'})
    future.cancel()

    # A late response arriving after the caller timed out (future cancelled)
    # must not raise InvalidStateError and must drop the pending entry.
    commands_manager.resolve_command(1, '{"ok": true}')

    assert 1 not in commands_manager._pending_commands


# --- EventsManager event worker (decoupled, ordered, leak-free) ---


@pytest.mark.asyncio
async def test_worker_processes_enqueued_events_in_order(events_manager):
    processed = []
    events_manager.register_callback('E', lambda e: processed.append(e['n']))

    events_manager.start()
    for n in range(5):
        events_manager.enqueue_event({'method': 'E', 'n': n})
    await asyncio.wait_for(events_manager._event_queue.join(), 1)
    await events_manager.stop()

    assert processed == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_worker_isolates_failures_and_keeps_processing(events_manager, caplog):
    processed = []

    def cb(event):
        if event['n'] == 1:
            raise ValueError('boom')
        processed.append(event['n'])

    events_manager.register_callback('E', cb)
    events_manager.start()
    for n in range(3):
        events_manager.enqueue_event({'method': 'E', 'n': n})
    await asyncio.wait_for(events_manager._event_queue.join(), 1)
    await events_manager.stop()

    assert processed == [0, 2]


@pytest.mark.asyncio
async def test_stop_cancels_worker_and_clears_queue(events_manager):
    events_manager.start()
    worker = events_manager._worker_task
    events_manager.enqueue_event({'method': 'E', 'n': 0})

    await events_manager.stop()

    assert worker.done()
    assert events_manager._worker_task is None
    assert events_manager._event_queue.empty()


@pytest.mark.asyncio
async def test_start_is_idempotent(events_manager):
    events_manager.start()
    first = events_manager._worker_task
    events_manager.start()
    assert events_manager._worker_task is first
    await events_manager.stop()


@pytest.mark.asyncio
async def test_stop_without_start_is_safe(events_manager):
    await events_manager.stop()
    assert events_manager._worker_task is None


# --- EventsManager.process_event robustness (malformed messages) ---


@pytest.mark.asyncio
async def test_process_event_without_method_is_ignored(events_manager):
    await events_manager.process_event({'params': {'foo': 'bar'}})
    assert len(events_manager.network_logs) == 0


@pytest.mark.asyncio
async def test_process_dialog_event_without_params_does_not_raise(events_manager):
    await events_manager.process_event({'method': 'Page.javascriptDialogOpening'})


# --- EventsManager.network_logs is bounded ---


@pytest.mark.asyncio
async def test_network_logs_are_bounded(events_manager):
    for i in range(MAX_NETWORK_LOGS + 50):
        events_manager._update_network_logs({'method': 'Network.requestWillBeSent', 'i': i})

    assert len(events_manager.network_logs) == MAX_NETWORK_LOGS
    assert events_manager.network_logs[0]['i'] == 50
    assert events_manager.network_logs[-1]['i'] == MAX_NETWORK_LOGS + 49
