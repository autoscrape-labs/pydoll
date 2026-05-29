from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pydoll.elements.firefox_element import FirefoxElement, KEYS


@pytest.fixture
def mock_connection():
    conn = MagicMock()
    conn.execute_command = AsyncMock(return_value={'result': {}})
    return conn


@pytest.fixture
def element(mock_connection):
    node = {'sharedId': 'shared-abc'}
    return FirefoxElement(node, context_id='ctx-1', connection_handler=mock_connection)


# ---------------------------------------------------------------------------
# key_down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_key_down_single_key_sends_keydown_action(element, mock_connection):
    # Arrange / Act
    await element.key_down('a')

    # Assert
    mock_connection.execute_command.assert_called_once()
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [{'type': 'keyDown', 'value': 'a'}]


@pytest.mark.asyncio
async def test_key_down_with_modifier_sends_modifier_first(element, mock_connection):
    # Arrange / Act
    await element.key_down('a', 'ctrl')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyDown', 'value': KEYS['ctrl']},
        {'type': 'keyDown', 'value': 'a'},
    ]


@pytest.mark.asyncio
async def test_key_down_with_multiple_modifiers(element, mock_connection):
    # Arrange / Act
    await element.key_down('a', 'ctrl', 'shift')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyDown', 'value': KEYS['ctrl']},
        {'type': 'keyDown', 'value': KEYS['shift']},
        {'type': 'keyDown', 'value': 'a'},
    ]


@pytest.mark.asyncio
async def test_key_down_resolves_key_name_from_keys_dict(element, mock_connection):
    # Arrange / Act
    await element.key_down('enter')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [{'type': 'keyDown', 'value': KEYS['enter']}]


# ---------------------------------------------------------------------------
# key_up
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_key_up_single_key_sends_keyup_action(element, mock_connection):
    # Arrange / Act
    await element.key_up('a')

    # Assert
    mock_connection.execute_command.assert_called_once()
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [{'type': 'keyUp', 'value': 'a'}]


@pytest.mark.asyncio
async def test_key_up_with_modifier_releases_key_then_modifier(element, mock_connection):
    # Arrange / Act
    await element.key_up('a', 'ctrl')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyUp', 'value': 'a'},
        {'type': 'keyUp', 'value': KEYS['ctrl']},
    ]


@pytest.mark.asyncio
async def test_key_up_with_multiple_modifiers_releases_in_reverse(element, mock_connection):
    # Arrange / Act
    await element.key_up('a', 'ctrl', 'shift')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyUp', 'value': 'a'},
        {'type': 'keyUp', 'value': KEYS['shift']},
        {'type': 'keyUp', 'value': KEYS['ctrl']},
    ]


# ---------------------------------------------------------------------------
# hotkey
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hotkey_ctrl_a_sends_down_then_up_in_reverse(element, mock_connection):
    # Arrange / Act
    await element.hotkey('ctrl', 'a')

    # Assert
    mock_connection.execute_command.assert_called_once()
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyDown', 'value': KEYS['ctrl']},
        {'type': 'keyDown', 'value': 'a'},
        {'type': 'keyUp', 'value': 'a'},
        {'type': 'keyUp', 'value': KEYS['ctrl']},
    ]


@pytest.mark.asyncio
async def test_hotkey_ctrl_shift_s(element, mock_connection):
    # Arrange / Act
    await element.hotkey('ctrl', 'shift', 's')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    actions = command['params']['actions'][0]['actions']
    assert actions == [
        {'type': 'keyDown', 'value': KEYS['ctrl']},
        {'type': 'keyDown', 'value': KEYS['shift']},
        {'type': 'keyDown', 'value': 's'},
        {'type': 'keyUp', 'value': 's'},
        {'type': 'keyUp', 'value': KEYS['shift']},
        {'type': 'keyUp', 'value': KEYS['ctrl']},
    ]


@pytest.mark.asyncio
async def test_hotkey_uses_correct_bidi_method(element, mock_connection):
    # Arrange / Act
    await element.hotkey('ctrl', 'c')

    # Assert
    command = mock_connection.execute_command.call_args[0][0]
    assert command['method'] == 'input.performActions'
    assert command['params']['context'] == 'ctx-1'


@pytest.mark.asyncio
async def test_hotkey_raises_when_no_keys_given(element):
    with pytest.raises(ValueError, match='at least one key'):
        await element.hotkey()
