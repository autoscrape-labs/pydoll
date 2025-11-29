import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from pydoll.interactions.keyboard import KeyboardAPI
from pydoll.constants import Key
from pydoll.protocol.input.types import KeyEventType


@pytest_asyncio.fixture
async def mock_tab():
    """Mock Tab instance for KeyboardAPI tests."""
    tab = MagicMock()
    tab._execute_command = AsyncMock()
    return tab


@pytest_asyncio.fixture
async def keyboard_api(mock_tab):
    """Create KeyboardAPI instance with mocked tab."""
    return KeyboardAPI(mock_tab)


class TestKeyboardAPIInitialization:
    """Test KeyboardAPI initialization."""

    def test_initialization(self, mock_tab):
        """Test KeyboardAPI is properly initialized with tab."""
        keyboard_api = KeyboardAPI(mock_tab)
        assert keyboard_api._tab == mock_tab


class TestKeyboardAPIDown:
    """Test keyboard.down() method."""

    @pytest.mark.asyncio
    async def test_key_down_without_modifiers(self, keyboard_api, mock_tab):
        """Test pressing key down without modifiers."""
        await keyboard_api.down(Key.A)

        # Verify execute_command was called
        assert mock_tab._execute_command.called
        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        # Verify the command structure
        assert command['method'] == 'Input.dispatchKeyEvent'
        assert command['params']['type'] == KeyEventType.KEY_DOWN
        assert command['params']['key'] == 'A'
        assert command['params']['windowsVirtualKeyCode'] == 65
        assert command['params']['nativeVirtualKeyCode'] == 65

    @pytest.mark.asyncio
    async def test_key_down_with_modifiers(self, keyboard_api, mock_tab):
        """Test pressing key down with modifiers."""
        await keyboard_api.down(Key.C, modifiers=2)  # Ctrl modifier

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['params']['type'] == KeyEventType.KEY_DOWN
        assert command['params']['key'] == 'C'
        assert command['params']['modifiers'] == 2

    @pytest.mark.asyncio
    async def test_key_down_enter(self, keyboard_api, mock_tab):
        """Test pressing Enter key down."""
        await keyboard_api.down(Key.ENTER)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['params']['key'] == 'Enter'
        assert command['params']['windowsVirtualKeyCode'] == 13


class TestKeyboardAPIUp:
    """Test keyboard.up() method."""

    @pytest.mark.asyncio
    async def test_key_up(self, keyboard_api, mock_tab):
        """Test releasing a key."""
        await keyboard_api.up(Key.A)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['method'] == 'Input.dispatchKeyEvent'
        assert command['params']['type'] == KeyEventType.KEY_UP
        assert command['params']['key'] == 'A'
        assert command['params']['windowsVirtualKeyCode'] == 65

    @pytest.mark.asyncio
    async def test_key_up_shift(self, keyboard_api, mock_tab):
        """Test releasing Shift key."""
        await keyboard_api.up(Key.SHIFT)

        call_args = mock_tab._execute_command.call_args
        command = call_args[0][0]

        assert command['params']['key'] == 'Shift'
        assert command['params']['windowsVirtualKeyCode'] == 16


class TestKeyboardAPIPress:
    """Test keyboard.press() method."""

    @pytest.mark.asyncio
    async def test_press_key(self, keyboard_api, mock_tab):
        """Test pressing and releasing a key."""
        await keyboard_api.press(Key.ENTER)

        # Should call execute_command twice (down + up)
        assert mock_tab._execute_command.call_count == 2

        # Verify first call is KEY_DOWN
        first_call = mock_tab._execute_command.call_args_list[0]
        assert first_call[0][0]['params']['type'] == KeyEventType.KEY_DOWN

        # Verify second call is KEY_UP
        second_call = mock_tab._execute_command.call_args_list[1]
        assert second_call[0][0]['params']['type'] == KeyEventType.KEY_UP

    @pytest.mark.asyncio
    async def test_press_with_modifiers(self, keyboard_api, mock_tab):
        """Test pressing key with modifiers."""
        await keyboard_api.press(Key.S, modifiers=2)  # Ctrl+S

        # Verify KEY_DOWN has modifiers
        first_call = mock_tab._execute_command.call_args_list[0]
        assert first_call[0][0]['params']['modifiers'] == 2

    @pytest.mark.asyncio
    async def test_press_with_custom_interval(self, keyboard_api, mock_tab):
        """Test pressing key with custom hold interval."""
        # Just verify it completes without error
        await keyboard_api.press(Key.TAB, interval=0.2)
        assert mock_tab._execute_command.call_count == 2


class TestKeyboardAPIHotkey:
    """Test keyboard.hotkey() method."""

    @pytest.mark.asyncio
    async def test_hotkey_ctrl_c(self, keyboard_api, mock_tab):
        """Test Ctrl+C hotkey."""
        await keyboard_api.hotkey(Key.CONTROL, Key.C)

        # Should call execute_command twice (C down + up)
        assert mock_tab._execute_command.call_count == 2

        # Verify KEY_DOWN for C with Ctrl modifier
        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['type'] == KeyEventType.KEY_DOWN
        assert command['params']['key'] == 'C'
        assert command['params']['modifiers'] == 2  # Ctrl = 2

        # Verify KEY_UP for C
        second_call = mock_tab._execute_command.call_args_list[1]
        command = second_call[0][0]
        assert command['params']['type'] == KeyEventType.KEY_UP
        assert command['params']['key'] == 'C'

    @pytest.mark.asyncio
    async def test_hotkey_ctrl_shift_t(self, keyboard_api, mock_tab):
        """Test Ctrl+Shift+T hotkey (3 keys)."""
        await keyboard_api.hotkey(Key.CONTROL, Key.SHIFT, Key.T)

        # Should call execute_command twice (T down + up)
        assert mock_tab._execute_command.call_count == 2

        # Verify KEY_DOWN for T with Ctrl+Shift modifiers
        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == 'T'
        assert command['params']['modifiers'] == 10  # Ctrl(2) + Shift(8) = 10

        # Verify KEY_UP for T
        second_call = mock_tab._execute_command.call_args_list[1]
        command = second_call[0][0]
        assert command['params']['type'] == KeyEventType.KEY_UP

    @pytest.mark.asyncio
    async def test_hotkey_alt_f4(self, keyboard_api, mock_tab):
        """Test Alt+F4 hotkey."""
        await keyboard_api.hotkey(Key.ALT, Key.F4)

        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == 'F4'
        assert command['params']['modifiers'] == 1  # Alt = 1

    @pytest.mark.asyncio
    async def test_hotkey_shift_a(self, keyboard_api, mock_tab):
        """Test Shift+A hotkey (uppercase A)."""
        await keyboard_api.hotkey(Key.SHIFT, Key.A)

        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == 'A'
        assert command['params']['modifiers'] == 8  # Shift = 8


class TestKeyboardAPISplitModifiers:
    """Test _split_modifiers_and_keys static method."""

    def test_split_single_modifier_and_key(self):
        """Test splitting Ctrl+C."""
        keys = [Key.CONTROL, Key.C]
        modifiers, non_modifiers = KeyboardAPI._split_modifiers_and_keys(keys)

        assert modifiers == [Key.CONTROL]
        assert non_modifiers == [Key.C]

    def test_split_multiple_modifiers_and_key(self):
        """Test splitting Ctrl+Shift+T."""
        keys = [Key.CONTROL, Key.SHIFT, Key.T]
        modifiers, non_modifiers = KeyboardAPI._split_modifiers_and_keys(keys)

        assert set(modifiers) == {Key.CONTROL, Key.SHIFT}
        assert non_modifiers == [Key.T]

    def test_split_no_modifiers(self):
        """Test splitting when no modifiers present."""
        keys = [Key.A, Key.B]
        modifiers, non_modifiers = KeyboardAPI._split_modifiers_and_keys(keys)

        assert modifiers == []
        assert set(non_modifiers) == {Key.A, Key.B}

    def test_split_only_modifiers(self):
        """Test splitting when only modifiers present."""
        keys = [Key.CONTROL, Key.SHIFT]
        modifiers, non_modifiers = KeyboardAPI._split_modifiers_and_keys(keys)

        assert set(modifiers) == {Key.CONTROL, Key.SHIFT}
        assert non_modifiers == []


class TestKeyboardAPICalculateModifier:
    """Test _calculate_modifier_value static method."""

    def test_calculate_single_modifier_ctrl(self):
        """Test calculating Ctrl modifier value."""
        modifiers = [Key.CONTROL]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 2

    def test_calculate_single_modifier_shift(self):
        """Test calculating Shift modifier value."""
        modifiers = [Key.SHIFT]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 8

    def test_calculate_single_modifier_alt(self):
        """Test calculating Alt modifier value."""
        modifiers = [Key.ALT]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 1

    def test_calculate_single_modifier_meta(self):
        """Test calculating Meta modifier value."""
        modifiers = [Key.META]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 4

    def test_calculate_ctrl_shift(self):
        """Test calculating Ctrl+Shift modifier value."""
        modifiers = [Key.CONTROL, Key.SHIFT]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 10  # 2 + 8

    def test_calculate_ctrl_alt(self):
        """Test calculating Ctrl+Alt modifier value."""
        modifiers = [Key.CONTROL, Key.ALT]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 3  # 2 + 1

    def test_calculate_all_modifiers(self):
        """Test calculating all modifiers together."""
        modifiers = [Key.CONTROL, Key.SHIFT, Key.ALT, Key.META]
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value == 15  # 2 + 8 + 1 + 4

    def test_calculate_no_modifiers(self):
        """Test calculating with no modifiers."""
        modifiers = []
        value = KeyboardAPI._calculate_modifier_value(modifiers)
        assert value is None


class TestKeyboardAPIIntegrationWithTab:
    """Test KeyboardAPI integration with Tab class."""

    @pytest.mark.asyncio
    async def test_keyboard_api_uses_tab_execute_command(self, mock_tab):
        """Test that KeyboardAPI uses tab's _execute_command."""
        keyboard_api = KeyboardAPI(mock_tab)
        await keyboard_api.down(Key.A)

        # Verify tab's _execute_command was called
        assert mock_tab._execute_command.called

    def test_keyboard_api_stores_tab_reference(self, mock_tab):
        """Test that KeyboardAPI stores reference to tab."""
        keyboard_api = KeyboardAPI(mock_tab)
        assert keyboard_api._tab is mock_tab


class TestKeyboardAPIEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_press_numpad_key(self, keyboard_api, mock_tab):
        """Test pressing numpad keys."""
        await keyboard_api.press(Key.NUMPAD5)

        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == 'Numpad5'
        assert command['params']['windowsVirtualKeyCode'] == 101

    @pytest.mark.asyncio
    async def test_press_function_key(self, keyboard_api, mock_tab):
        """Test pressing function keys."""
        await keyboard_api.press(Key.F12)

        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == 'F12'
        assert command['params']['windowsVirtualKeyCode'] == 123

    @pytest.mark.asyncio
    async def test_hotkey_with_digit(self, keyboard_api, mock_tab):
        """Test hotkey with digit keys."""
        await keyboard_api.hotkey(Key.CONTROL, Key.DIGIT1)

        first_call = mock_tab._execute_command.call_args_list[0]
        command = first_call[0][0]
        assert command['params']['key'] == '1'
        assert command['params']['modifiers'] == 2

    @pytest.mark.asyncio
    async def test_sequential_key_presses(self, keyboard_api, mock_tab):
        """Test multiple sequential key presses."""
        await keyboard_api.press(Key.A)
        await keyboard_api.press(Key.B)
        await keyboard_api.press(Key.C)

        # Should be called 6 times (3 keys × 2 events each)
        assert mock_tab._execute_command.call_count == 6

        # Verify sequence: A down, A up, B down, B up, C down, C up
        calls = mock_tab._execute_command.call_args_list
        assert calls[0][0][0]['params']['key'] == 'A'
        assert calls[0][0][0]['params']['type'] == KeyEventType.KEY_DOWN
        assert calls[1][0][0]['params']['key'] == 'A'
        assert calls[1][0][0]['params']['type'] == KeyEventType.KEY_UP
        assert calls[2][0][0]['params']['key'] == 'B'
        assert calls[4][0][0]['params']['key'] == 'C'

