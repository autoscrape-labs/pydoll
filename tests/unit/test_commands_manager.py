"""Unit tests for CommandsManager: id assignment and command future lifecycle."""

from __future__ import annotations

import pytest

from pydoll.connection.managers import CommandsManager


@pytest.mark.asyncio
async def test_assigns_unique_incrementing_ids():
    manager = CommandsManager()
    commands = [{'method': 'A'}, {'method': 'B'}, {'method': 'C'}]
    for command in commands:
        manager.create_command_future(command)
    assert [command['id'] for command in commands] == [1, 2, 3]


@pytest.mark.asyncio
async def test_resolve_sets_future_result():
    manager = CommandsManager()
    command = {'method': 'A'}
    future = manager.create_command_future(command)
    manager.resolve_command(command['id'], 'response-payload')
    assert future.done()
    assert future.result() == 'response-payload'


@pytest.mark.asyncio
async def test_resolve_unknown_id_is_noop():
    manager = CommandsManager()
    manager.resolve_command(999, 'ignored')


@pytest.mark.asyncio
async def test_resolve_after_cancel_does_not_raise():
    manager = CommandsManager()
    command = {'method': 'A'}
    future = manager.create_command_future(command)
    future.cancel()
    manager.resolve_command(command['id'], 'late')
    assert future.cancelled()


@pytest.mark.asyncio
async def test_remove_pending_command_prevents_resolution():
    manager = CommandsManager()
    command = {'method': 'A'}
    future = manager.create_command_future(command)
    manager.remove_pending_command(command['id'])
    manager.resolve_command(command['id'], 'late')
    assert not future.done()
    future.cancel()


@pytest.mark.asyncio
async def test_fail_all_pending_propagates_to_every_future():
    manager = CommandsManager()
    first = manager.create_command_future({'method': 'A'})
    second = manager.create_command_future({'method': 'B'})
    error = RuntimeError('connection lost')
    manager.fail_all_pending(error)
    assert first.exception() is error
    assert second.exception() is error


@pytest.mark.asyncio
async def test_fail_all_pending_clears_so_late_resolve_is_noop():
    manager = CommandsManager()
    command = {'method': 'A'}
    future = manager.create_command_future(command)
    error = RuntimeError('lost')
    manager.fail_all_pending(error)
    manager.resolve_command(command['id'], 'late')
    assert future.exception() is error


@pytest.mark.asyncio
async def test_fail_all_pending_on_empty_is_noop():
    manager = CommandsManager()
    manager.fail_all_pending(RuntimeError('nothing pending'))
