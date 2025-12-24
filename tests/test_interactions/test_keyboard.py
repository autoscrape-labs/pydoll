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
        """Test KeyboardAPI is properly initialized with executor."""
        keyboard_api = KeyboardAPI(mock_tab)
        assert keyboard_api._executor == mock_tab


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

    def test_keyboard_api_stores_executor_reference(self, mock_tab):
        """Test that KeyboardAPI stores reference to executor."""
        keyboard_api = KeyboardAPI(mock_tab)
        assert keyboard_api._executor is mock_tab


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


class TestTimingConfig:
    """Test TimingConfig dataclass."""

    def test_default_values(self):
        """Test default timing configuration values."""
        from pydoll.interactions.keyboard import TimingConfig

        config = TimingConfig()

        assert config.keystroke_min == 0.03
        assert config.keystroke_max == 0.12
        assert config.punctuation_min == 0.08
        assert config.punctuation_max == 0.18
        assert config.thinking_probability == 0.02
        assert config.thinking_min == 0.3
        assert config.thinking_max == 0.7
        assert config.distraction_probability == 0.005
        assert config.distraction_min == 0.5
        assert config.distraction_max == 1.2
        assert config.mistake_realize_min == 0.1
        assert config.mistake_realize_max == 0.25
        assert config.after_correction_min == 0.03
        assert config.after_correction_max == 0.08
        assert config.double_press_min == 0.02
        assert config.double_press_max == 0.05
        assert config.hesitation_min == 0.15
        assert config.hesitation_max == 0.3

    def test_custom_values(self):
        """Test custom timing configuration values."""
        from pydoll.interactions.keyboard import TimingConfig

        config = TimingConfig(
            keystroke_min=0.05,
            keystroke_max=0.15,
            thinking_probability=0.1,
        )

        assert config.keystroke_min == 0.05
        assert config.keystroke_max == 0.15
        assert config.thinking_probability == 0.1

    def test_frozen_dataclass(self):
        """Test that config is immutable (frozen)."""
        from pydoll.interactions.keyboard import TimingConfig

        config = TimingConfig()

        with pytest.raises(AttributeError):
            config.keystroke_min = 1.0


class TestTypoConfig:
    """Test TypoConfig dataclass."""

    def test_default_values(self):
        """Test default typo configuration values."""
        from pydoll.interactions.keyboard import TypoConfig

        config = TypoConfig()

        assert config.adjacent_weight == 0.55
        assert config.transpose_weight == 0.20
        assert config.double_weight == 0.12
        assert config.skip_weight == 0.08
        assert config.missed_space_weight == 0.05

    def test_custom_values(self):
        """Test custom typo configuration values."""
        from pydoll.interactions.keyboard import TypoConfig

        config = TypoConfig(
            adjacent_weight=0.7,
            transpose_weight=0.1,
        )

        assert config.adjacent_weight == 0.7
        assert config.transpose_weight == 0.1

    def test_frozen_dataclass(self):
        """Test that config is immutable (frozen)."""
        from pydoll.interactions.keyboard import TypoConfig

        config = TypoConfig()

        with pytest.raises(AttributeError):
            config.adjacent_weight = 1.0


class TestTypoResult:
    """Test TypoResult dataclass."""

    def test_typo_result_creation(self):
        """Test creating TypoResult."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        result = TypoResult(typo_type=TypoType.ADJACENT, wrong_char='e')

        assert result.typo_type == TypoType.ADJACENT
        assert result.wrong_char == 'e'

    def test_typo_result_default_wrong_char(self):
        """Test TypoResult with default wrong_char."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        result = TypoResult(typo_type=TypoType.SKIP)

        assert result.typo_type == TypoType.SKIP
        assert result.wrong_char == ''


class TestKeyboardTypeText:
    """Test keyboard.type_text() method."""

    @pytest.mark.asyncio
    async def test_type_text_basic(self, keyboard_api, mock_tab):
        """Test basic text typing."""
        await keyboard_api.type_text("ab")

        # Should call execute_command for each character (KEY_DOWN + KEY_UP)
        assert mock_tab._execute_command.call_count == 4

        # Verify characters are typed (checking KEY_DOWN events)
        # Call 0: 'a' KEY_DOWN
        first_call = mock_tab._execute_command.call_args_list[0]
        assert first_call[0][0]['params']['text'] == 'a'
        assert first_call[0][0]['params']['type'] == KeyEventType.KEY_DOWN

        # Call 1: 'a' KEY_UP
        second_call = mock_tab._execute_command.call_args_list[1]
        assert second_call[0][0]['params']['type'] == KeyEventType.KEY_UP

        # Call 2: 'b' KEY_DOWN
        third_call = mock_tab._execute_command.call_args_list[2]
        assert third_call[0][0]['params']['text'] == 'b'
        assert third_call[0][0]['params']['type'] == KeyEventType.KEY_DOWN

    @pytest.mark.asyncio
    async def test_type_text_with_humanize_calls_humanized_method(self, mock_tab):
        """Test that humanize=True calls _type_text_humanized."""
        from pydoll.interactions.keyboard import Keyboard

        keyboard = Keyboard(mock_tab)
        keyboard._type_text_humanized = AsyncMock()

        await keyboard.type_text("test", humanize=True)

        keyboard._type_text_humanized.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_type_text_interval_deprecated_warning(self, keyboard_api):
        """Test that interval parameter shows deprecation warning."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await keyboard_api.type_text("a", interval=0.1)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "interval" in str(w[0].message)

    @pytest.mark.asyncio
    async def test_type_char(self, keyboard_api, mock_tab):
        """Test _type_char sends KEY_DOWN and KEY_UP events."""
        await keyboard_api._type_char("x")

        # Should call execute_command twice (down + up)
        assert mock_tab._execute_command.call_count == 2

        # Verify KEY_DOWN
        first_call = mock_tab._execute_command.call_args_list[0]
        command_down = first_call[0][0]
        assert command_down['method'] == 'Input.dispatchKeyEvent'
        assert command_down['params']['type'] == KeyEventType.KEY_DOWN
        assert command_down['params']['text'] == 'x'

        # Verify KEY_UP
        second_call = mock_tab._execute_command.call_args_list[1]
        command_up = second_call[0][0]
        assert command_up['method'] == 'Input.dispatchKeyEvent'
        assert command_up['params']['type'] == KeyEventType.KEY_UP

    @pytest.mark.asyncio
    async def test_type_backspace(self, keyboard_api, mock_tab):
        """Test _type_backspace sends backspace keys."""
        await keyboard_api._type_backspace()

        # Should call down + up for backspace
        assert mock_tab._execute_command.call_count == 2

        first_call = mock_tab._execute_command.call_args_list[0]
        assert first_call[0][0]['params']['key'] == 'Backspace'
        assert first_call[0][0]['params']['type'] == KeyEventType.KEY_DOWN

        second_call = mock_tab._execute_command.call_args_list[1]
        assert second_call[0][0]['params']['type'] == KeyEventType.KEY_UP


class TestKeyboardTypoGeneration:
    """Test typo generation methods."""

    def test_should_make_typo_returns_boolean(self):
        """Test _should_make_typo returns a boolean."""
        from pydoll.interactions.keyboard import Keyboard

        result = Keyboard._should_make_typo()
        assert isinstance(result, bool)

    def test_select_typo_type_returns_valid_type(self, keyboard_api):
        """Test _select_typo_type returns valid TypoType."""
        from pydoll.constants import TypoType

        valid_types = {
            TypoType.ADJACENT,
            TypoType.TRANSPOSE,
            TypoType.DOUBLE,
            TypoType.SKIP,
            TypoType.MISSED_SPACE,
        }

        for _ in range(10):
            result = keyboard_api._select_typo_type()
            assert result in valid_types

    def test_create_adjacent_typo_returns_adjacent_type(self):
        """Test _create_adjacent_typo returns ADJACENT type for valid char."""
        from pydoll.interactions.keyboard import Keyboard
        from pydoll.constants import TypoType

        result = Keyboard._create_adjacent_typo('a')

        # 'a' has neighbors, so should return ADJACENT
        assert result.typo_type == TypoType.ADJACENT
        assert result.wrong_char != ''

    def test_create_adjacent_typo_fallback_for_unknown_char(self):
        """Test _create_adjacent_typo falls back for unknown chars."""
        from pydoll.interactions.keyboard import Keyboard
        from pydoll.constants import TypoType

        # Using a character not in QWERTY_NEIGHBORS
        result = Keyboard._create_adjacent_typo('@')

        # Should fall back to DOUBLE
        assert result.typo_type == TypoType.DOUBLE
        assert result.wrong_char == '@'

    def test_create_adjacent_typo_preserves_case(self):
        """Test _create_adjacent_typo preserves character case."""
        from pydoll.interactions.keyboard import Keyboard

        # Uppercase should return uppercase neighbor
        result_upper = Keyboard._create_adjacent_typo('A')
        if result_upper.wrong_char:
            assert result_upper.wrong_char.isupper()

        # Lowercase should return lowercase neighbor
        result_lower = Keyboard._create_adjacent_typo('a')
        if result_lower.wrong_char:
            assert result_lower.wrong_char.islower()

    def test_create_transpose_typo(self, keyboard_api):
        """Test _create_transpose_typo returns TRANSPOSE type."""
        from pydoll.constants import TypoType

        result = keyboard_api._create_transpose_typo('a', 'b')

        assert result.typo_type == TypoType.TRANSPOSE
        assert result.wrong_char == 'b'

    def test_create_transpose_typo_fallback_no_next_char(self, keyboard_api):
        """Test _create_transpose_typo falls back when no next char."""
        from pydoll.constants import TypoType

        result = keyboard_api._create_transpose_typo('a', None)

        # Should fall back to ADJACENT
        assert result.typo_type == TypoType.ADJACENT

    def test_create_missed_space_typo(self, keyboard_api):
        """Test _create_missed_space_typo returns MISSED_SPACE type."""
        from pydoll.constants import TypoType

        result = keyboard_api._create_missed_space_typo(' ')

        assert result.typo_type == TypoType.MISSED_SPACE

    def test_create_missed_space_typo_fallback_non_space(self, keyboard_api):
        """Test _create_missed_space_typo falls back for non-space."""
        from pydoll.constants import TypoType

        result = keyboard_api._create_missed_space_typo('a')

        # Should fall back to ADJACENT
        assert result.typo_type == TypoType.ADJACENT

    def test_generate_typo_returns_typo_result(self, keyboard_api):
        """Test _generate_typo returns TypoResult."""
        from pydoll.interactions.keyboard import TypoResult

        result = keyboard_api._generate_typo('a', 'b')

        assert isinstance(result, TypoResult)

    def test_create_typo_with_all_types(self, keyboard_api):
        """Test _create_typo handles all TypoType values."""
        from pydoll.constants import TypoType
        from pydoll.interactions.keyboard import TypoResult

        for typo_type in TypoType:
            result = keyboard_api._create_typo(typo_type, 'a', 'b')
            assert isinstance(result, TypoResult)


class TestKeyboardTypoHandling:
    """Test typo handling methods."""

    @pytest.mark.asyncio
    async def test_do_adjacent_typo(self, keyboard_api, mock_tab):
        """Test _do_adjacent_typo types wrong char, backspaces, then correct."""
        await keyboard_api._do_adjacent_typo('a', 's')

        # Should type: 's' (wrong), backspace, 'a' (correct)
        # That's at least 3 key events (char, down, up, char)
        assert mock_tab._execute_command.call_count >= 3

    @pytest.mark.asyncio
    async def test_do_transpose_typo(self, keyboard_api, mock_tab):
        """Test _do_transpose_typo types chars in wrong order then fixes."""
        await keyboard_api._do_transpose_typo('a', 'b')

        # Should type: 'b', 'a', backspace×2, 'a', 'b'
        # Multiple key events expected
        assert mock_tab._execute_command.call_count >= 4

    @pytest.mark.asyncio
    async def test_do_double_typo(self, keyboard_api, mock_tab):
        """Test _do_double_typo types char twice then backspaces."""
        await keyboard_api._do_double_typo('a')

        # Should type: 'a', 'a', backspace
        assert mock_tab._execute_command.call_count >= 3

    @pytest.mark.asyncio
    async def test_do_skip_typo(self, keyboard_api, mock_tab):
        """Test _do_skip_typo hesitates then types normally."""
        await keyboard_api._do_skip_typo('a')

        # Should just type 'a' (KEY_DOWN + KEY_UP)
        assert mock_tab._execute_command.call_count == 2
        
        # Verify KEY_DOWN
        first_call = mock_tab._execute_command.call_args_list[0]
        assert first_call[0][0]['params']['text'] == 'a'
        assert first_call[0][0]['params']['type'] == KeyEventType.KEY_DOWN

    @pytest.mark.asyncio
    async def test_do_missed_space_typo(self, keyboard_api, mock_tab):
        """Test _do_missed_space_typo misses space, fixes, types both."""
        await keyboard_api._do_missed_space_typo(' ', 'w')

        # Should type: 'w', backspace, ' ', 'w'
        assert mock_tab._execute_command.call_count >= 4

    @pytest.mark.asyncio
    async def test_handle_typo_adjacent(self, keyboard_api, mock_tab):
        """Test _handle_typo with ADJACENT type."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        typo = TypoResult(typo_type=TypoType.ADJACENT, wrong_char='s')
        result = await keyboard_api._handle_typo('a', 'b', typo)

        assert result is False  # Should not skip next
        assert mock_tab._execute_command.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_typo_transpose_skips_next(self, keyboard_api, mock_tab):
        """Test _handle_typo with TRANSPOSE type returns True."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        typo = TypoResult(typo_type=TypoType.TRANSPOSE, wrong_char='b')
        result = await keyboard_api._handle_typo('a', 'b', typo)

        assert result is True  # Should skip next

    @pytest.mark.asyncio
    async def test_handle_typo_double(self, keyboard_api, mock_tab):
        """Test _handle_typo with DOUBLE type."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        typo = TypoResult(typo_type=TypoType.DOUBLE, wrong_char='a')
        result = await keyboard_api._handle_typo('a', 'b', typo)

        assert result is False

    @pytest.mark.asyncio
    async def test_handle_typo_skip(self, keyboard_api, mock_tab):
        """Test _handle_typo with SKIP type."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        typo = TypoResult(typo_type=TypoType.SKIP)
        result = await keyboard_api._handle_typo('a', 'b', typo)

        assert result is False

    @pytest.mark.asyncio
    async def test_handle_typo_missed_space_skips_next(self, keyboard_api, mock_tab):
        """Test _handle_typo with MISSED_SPACE type returns True."""
        from pydoll.interactions.keyboard import TypoResult
        from pydoll.constants import TypoType

        typo = TypoResult(typo_type=TypoType.MISSED_SPACE)
        result = await keyboard_api._handle_typo(' ', 'w', typo)

        assert result is True  # Should skip next


class TestKeyboardRealisticDelay:
    """Test realistic delay application."""

    @pytest.mark.asyncio
    async def test_apply_realistic_delay_basic(self, keyboard_api):
        """Test _apply_realistic_delay doesn't raise."""
        # Just ensure it completes without error
        await keyboard_api._apply_realistic_delay('a')

    @pytest.mark.asyncio
    async def test_apply_realistic_delay_with_punctuation(self, keyboard_api):
        """Test _apply_realistic_delay adds extra delay for punctuation."""
        # Just ensure it completes without error for punctuation
        for char in ' .,!?;:\n':
            await keyboard_api._apply_realistic_delay(char)

    def test_pause_chars_constant(self):
        """Test PAUSE_CHARS is properly defined."""
        from pydoll.interactions.keyboard import Keyboard

        assert ' ' in Keyboard.PAUSE_CHARS
        assert '.' in Keyboard.PAUSE_CHARS
        assert ',' in Keyboard.PAUSE_CHARS
        assert '!' in Keyboard.PAUSE_CHARS
        assert '?' in Keyboard.PAUSE_CHARS
        assert ';' in Keyboard.PAUSE_CHARS
        assert ':' in Keyboard.PAUSE_CHARS
        assert '\n' in Keyboard.PAUSE_CHARS


class TestKeyboardWithCustomConfig:
    """Test Keyboard with custom configurations."""

    def test_keyboard_with_custom_timing(self, mock_tab):
        """Test Keyboard accepts custom timing configuration."""
        from pydoll.interactions.keyboard import Keyboard, TimingConfig

        custom_timing = TimingConfig(
            keystroke_min=0.1,
            keystroke_max=0.2,
        )

        keyboard = Keyboard(mock_tab, timing=custom_timing)

        assert keyboard._timing == custom_timing
        assert keyboard._timing.keystroke_min == 0.1

    def test_keyboard_with_custom_typo_config(self, mock_tab):
        """Test Keyboard accepts custom typo configuration."""
        from pydoll.interactions.keyboard import Keyboard, TypoConfig

        custom_typo = TypoConfig(
            adjacent_weight=0.9,
            transpose_weight=0.1,
        )

        keyboard = Keyboard(mock_tab, typo_config=custom_typo)

        assert keyboard._typo_config == custom_typo
        assert keyboard._typo_config.adjacent_weight == 0.9

    def test_keyboard_uses_default_configs(self, mock_tab):
        """Test Keyboard uses default configs if none provided."""
        from pydoll.interactions.keyboard import Keyboard

        keyboard = Keyboard(mock_tab)

        assert keyboard._timing.keystroke_min == 0.03
        assert keyboard._typo_config.adjacent_weight == 0.55


class TestKeyboardProcessCharWithTypo:
    """Test _process_char_with_typo method."""

    @pytest.mark.asyncio
    async def test_process_char_no_typo(self, mock_tab):
        """Test _process_char_with_typo when no typo occurs."""
        from pydoll.interactions.keyboard import Keyboard
        from unittest.mock import patch

        keyboard = Keyboard(mock_tab)

        # Patch _should_make_typo to always return False
        with patch.object(keyboard, '_should_make_typo', return_value=False):
            result = await keyboard._process_char_with_typo('a', 'b')

        assert result is False  # Should not skip next
        assert mock_tab._execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_process_char_with_typo(self, mock_tab):
        """Test _process_char_with_typo when typo occurs."""
        from pydoll.interactions.keyboard import Keyboard, TypoResult
        from pydoll.constants import TypoType
        from unittest.mock import patch

        keyboard = Keyboard(mock_tab)

        # Patch _should_make_typo to always return True
        # And _generate_typo to return a SKIP typo (simplest case)
        with patch.object(keyboard, '_should_make_typo', return_value=True):
            with patch.object(
                keyboard,
                '_generate_typo',
                return_value=TypoResult(typo_type=TypoType.SKIP),
            ):
                result = await keyboard._process_char_with_typo('a', 'b')

        assert result is False  # SKIP doesn't skip next


class TestKeyboardAPIBackwardCompatibility:
    """Test backward compatibility alias."""

    def test_keyboard_api_alias(self):
        """Test KeyboardAPI is an alias for Keyboard."""
        from pydoll.interactions.keyboard import Keyboard, KeyboardAPI

        assert KeyboardAPI is Keyboard
