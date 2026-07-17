"""Connection-layer tests against a real local WebSocket server.

These exercise the production ConnectionHandler over a real socket: commands,
concurrency, events, network logs, malformed frames, large frames, in-flight
failure and reconnection. There are no mocks and no private-method probing;
every assertion is on an observable result or state.
"""

from __future__ import annotations

import asyncio
from typing import Callable

import pytest

from pydoll.connection import ConnectionHandler
from pydoll.exceptions import CommandExecutionTimeout, WebSocketConnectionClosed


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
async def test_execute_command_returns_matching_response(cdp_server):
    cdp_server.set_result('Browser.getVersion', {'product': 'FakeChrome/1.0'})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        result = await handler.execute_command({'method': 'Browser.getVersion'})
    finally:
        await handler.close()

    assert result['result'] == {'product': 'FakeChrome/1.0'}
    assert 'Browser.getVersion' in [c['method'] for c in cdp_server.received_commands]


@pytest.mark.asyncio
async def test_concurrent_commands_get_unique_ids_and_all_resolve(cdp_server):
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        results = await asyncio.gather(
            *(handler.execute_command({'method': f'Domain.method{i}'}) for i in range(50))
        )
    finally:
        await handler.close()

    assert len(results) == 50
    ids = [c['id'] for c in cdp_server.received_commands]
    assert len(ids) == 50
    assert len(set(ids)) == 50


@pytest.mark.asyncio
async def test_event_callback_fires_on_pushed_event(cdp_server):
    received: list[dict] = []
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await handler.register_callback('Page.loadEventFired', received.append)
        await cdp_server.push_event('Page.loadEventFired', {'timestamp': 123})
        await _wait_until(lambda: len(received) == 1)
    finally:
        await handler.close()

    assert received[0]['method'] == 'Page.loadEventFired'
    assert received[0]['params'] == {'timestamp': 123}


@pytest.mark.asyncio
async def test_network_request_event_is_recorded_in_logs(cdp_server):
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Network.enable'})
        await cdp_server.push_event('Network.requestWillBeSent', {'requestId': 'req-1'})
        await _wait_until(lambda: len(handler.network_logs) == 1)
        logs = handler.network_logs
    finally:
        await handler.close()

    assert logs[0]['params']['requestId'] == 'req-1'


@pytest.mark.asyncio
async def test_receive_loop_survives_malformed_frame(cdp_server):
    cdp_server.set_result('Runtime.evaluate', {'value': 42})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Runtime.evaluate'})
        await cdp_server.send_raw('this is not valid json')
        result = await handler.execute_command({'method': 'Runtime.evaluate'})
    finally:
        await handler.close()

    assert result['result'] == {'value': 42}


@pytest.mark.asyncio
async def test_large_frame_is_received(cdp_server):
    big_payload = 'x' * (2 * 1024 * 1024)
    cdp_server.set_result('Page.captureScreenshot', {'data': big_payload})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        result = await handler.execute_command({'method': 'Page.captureScreenshot'})
    finally:
        await handler.close()

    assert result['result']['data'] == big_payload


@pytest.mark.asyncio
async def test_in_flight_command_fails_when_connection_drops(cdp_server):
    cdp_server.hang('Page.navigate')
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        pending = asyncio.create_task(handler.execute_command({'method': 'Page.navigate'}))
        await _wait_until(
            lambda: any(c['method'] == 'Page.navigate' for c in cdp_server.received_commands)
        )
        await cdp_server.drop_connections()
        with pytest.raises(WebSocketConnectionClosed):
            await pending
    finally:
        await handler.close()


@pytest.mark.asyncio
async def test_reconnects_on_next_command_after_drop(cdp_server):
    cdp_server.set_result('Page.enable', {})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await cdp_server.drop_connections()

        result = None
        for _ in range(10):
            try:
                result = await handler.execute_command({'method': 'Page.enable'})
                break
            except WebSocketConnectionClosed:
                await asyncio.sleep(0.05)
    finally:
        await handler.close()

    assert result is not None
    assert result['result'] == {}
    assert cdp_server.active_connections >= 1


@pytest.mark.asyncio
async def test_temporary_callback_fires_only_once(cdp_server):
    fired: list[dict] = []
    markers: list[dict] = []
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await handler.register_callback('Custom.event', fired.append, temporary=True)
        await handler.register_callback('Custom.marker', markers.append)
        await cdp_server.push_event('Custom.event', {'n': 1})
        await cdp_server.push_event('Custom.event', {'n': 2})
        await cdp_server.push_event('Custom.marker')
        await _wait_until(lambda: len(markers) == 1)
    finally:
        await handler.close()

    assert len(fired) == 1
    assert fired[0]['params'] == {'n': 1}


@pytest.mark.asyncio
async def test_removed_callback_stops_firing(cdp_server):
    fired: list[dict] = []
    markers: list[dict] = []
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        callback_id = await handler.register_callback('Custom.event', fired.append)
        await handler.register_callback('Custom.marker', markers.append)
        await handler.remove_callback(callback_id)
        await cdp_server.push_event('Custom.event')
        await cdp_server.push_event('Custom.marker')
        await _wait_until(lambda: len(markers) == 1)
    finally:
        await handler.close()

    assert fired == []


# --- Edge cases: what happens when the CDP peer closes the connection? ---


@pytest.mark.asyncio
async def test_command_times_out_when_server_never_responds(cdp_server):
    """A command whose response never arrives raises CommandExecutionTimeout."""
    cdp_server.hang('Page.navigate')
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        with pytest.raises(CommandExecutionTimeout):
            await handler.execute_command({'method': 'Page.navigate'}, timeout=0.3)
    finally:
        await handler.close()


@pytest.mark.asyncio
async def test_all_in_flight_commands_fail_when_connection_drops(cdp_server):
    """Every pending command is failed (not left hanging) when the peer disconnects."""
    cdp_server.hang('Page.navigate')
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        pending = [
            asyncio.create_task(handler.execute_command({'method': 'Page.navigate'}))
            for _ in range(20)
        ]
        await _wait_until(lambda: len(cdp_server.commands_for('Page.navigate')) == 20)
        await cdp_server.drop_connections()
        results = await asyncio.gather(*pending, return_exceptions=True)
    finally:
        await handler.close()

    assert len(results) == 20
    assert all(isinstance(result, WebSocketConnectionClosed) for result in results)


@pytest.mark.asyncio
async def test_command_after_server_shutdown_raises_without_hanging(cdp_server):
    """If the peer is gone entirely, the next command errors quickly instead of hanging."""
    cdp_server.set_result('Page.enable', {})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await cdp_server.stop()
        with pytest.raises((OSError, WebSocketConnectionClosed)):
            await asyncio.wait_for(
                handler.execute_command({'method': 'Page.enable'}), timeout=5
            )
    finally:
        await handler.close()


@pytest.mark.asyncio
async def test_reconnect_after_drop_opens_a_fresh_connection(cdp_server):
    """After a drop, the handler transparently opens a brand-new socket."""
    cdp_server.set_result('Page.enable', {})
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await _wait_until(lambda: cdp_server.total_connections == 1)
        await cdp_server.drop_connections()

        for _ in range(10):
            try:
                await handler.execute_command({'method': 'Page.enable'})
                break
            except WebSocketConnectionClosed:
                await asyncio.sleep(0.05)
    finally:
        await handler.close()

    assert cdp_server.total_connections >= 2


@pytest.mark.asyncio
async def test_close_fails_a_pending_command(cdp_server):
    """Closing the handler while a command is in flight fails it instead of hanging."""
    cdp_server.hang('Page.navigate')
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    pending = asyncio.create_task(handler.execute_command({'method': 'Page.navigate'}))
    await _wait_until(lambda: cdp_server.commands_for('Page.navigate'))

    await handler.close()

    with pytest.raises(WebSocketConnectionClosed):
        await pending


@pytest.mark.asyncio
async def test_close_is_idempotent(cdp_server):
    """Closing twice is safe and does not raise."""
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    await handler.execute_command({'method': 'Page.enable'})
    await handler.close()
    await handler.close()


@pytest.mark.asyncio
async def test_event_callback_exception_does_not_stop_later_events(cdp_server):
    """A raising event callback is isolated; subsequent events are still delivered."""
    markers: list[dict] = []

    async def boom(_event):
        raise RuntimeError('callback boom')

    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await handler.register_callback('Custom.boom', boom)
        await handler.register_callback('Custom.marker', markers.append)
        await cdp_server.push_event('Custom.boom')
        await cdp_server.push_event('Custom.marker')
        await _wait_until(lambda: len(markers) == 1)
    finally:
        await handler.close()

    assert len(markers) == 1


# --- Edge cases: what happens when the handler is bombarded with commands? ---


@pytest.mark.asyncio
async def test_high_concurrency_commands_all_resolve_with_unique_ids(cdp_server):
    """300 commands fired at once all resolve and each carries a unique id."""
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        results = await asyncio.gather(
            *(handler.execute_command({'method': f'Domain.method{i}'}) for i in range(300))
        )
    finally:
        await handler.close()

    assert len(results) == 300
    ids = [command['id'] for command in cdp_server.received_commands]
    assert len(ids) == 300
    assert len(set(ids)) == 300


@pytest.mark.asyncio
async def test_command_bombardment_does_not_drop_concurrent_events(cdp_server):
    """A flood of commands does not starve the event stream; all events arrive."""
    events: list[dict] = []
    handler = ConnectionHandler(ws_address=cdp_server.ws_address)
    try:
        await handler.execute_command({'method': 'Page.enable'})
        await handler.register_callback('Stream.tick', events.append)

        async def flood_commands():
            await asyncio.gather(
                *(handler.execute_command({'method': f'Domain.m{i}'}) for i in range(100))
            )

        async def flood_events():
            for n in range(25):
                await cdp_server.push_event('Stream.tick', {'n': n})

        await asyncio.gather(flood_commands(), flood_events())
        await _wait_until(lambda: len(events) == 25, timeout=5.0)
    finally:
        await handler.close()

    assert len(events) == 25


@pytest.mark.asyncio
async def test_resolves_page_level_address_from_port_and_page_id(cdp_server):
    """A handler given a port + page_id connects via the page-level devtools path."""
    cdp_server.set_result('Page.enable', {})
    handler = ConnectionHandler(connection_port=cdp_server.port, page_id='abc')
    try:
        result = await handler.execute_command({'method': 'Page.enable'})
        assert result['result'] == {}
        assert cdp_server.total_connections >= 1
    finally:
        await handler.close()


@pytest.mark.asyncio
async def test_context_manager_runs_commands_and_has_repr(cdp_server):
    """The async context manager yields a usable handler and closes it on exit."""
    cdp_server.set_result('Browser.getVersion', {'ok': True})
    async with ConnectionHandler(ws_address=cdp_server.ws_address) as handler:
        result = await handler.execute_command({'method': 'Browser.getVersion'})
        assert result['result'] == {'ok': True}
        assert 'ConnectionHandler' in repr(handler)
        assert 'ConnectionHandler' in str(handler)


@pytest.mark.asyncio
async def test_resolves_page_level_address_from_explicit_host_port_and_page_id(cdp_server):
    """A handler given a host + port + page_id + use_secure resolves and connects via the page-level devtools path."""
    cdp_server.set_result('Page.enable', {})
    handler = ConnectionHandler(
        connection_host='localhost',
        connection_port=cdp_server.port,
        page_id='abc',
        use_secure=False,
    )
    try:
        result = await handler.execute_command({'method': 'Page.enable'})
        assert result['result'] == {}
        assert cdp_server.total_connections >= 1
    finally:
        await handler.close()
