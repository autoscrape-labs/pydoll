from __future__ import annotations

import asyncio
import logging
import random
import warnings
from dataclasses import dataclass
from typing import Any, Optional, Protocol, cast

from pydoll.commands import InputCommands
from pydoll.constants import DEFAULT_TYPO_PROBABILITY, QWERTY_NEIGHBORS, Key, TypoType
from pydoll.protocol.input.types import KeyEventType, KeyModifier

logger = logging.getLogger(__name__)


class CommandExecutor(Protocol):
    """Protocol for objects that can execute CDP commands."""

    async def _execute_command(self, command: Any) -> Any: ...


@dataclass(frozen=True)
class TypoResult:
    """Result of a typo generation."""

    typo_type: TypoType
    wrong_char: str = ''


@dataclass(frozen=True)
class TimingConfig:
    """Configuration for realistic typing timing."""

    keystroke_min: float = 0.03
    keystroke_max: float = 0.12
    punctuation_min: float = 0.08
    punctuation_max: float = 0.18
    thinking_probability: float = 0.02
    thinking_min: float = 0.3
    thinking_max: float = 0.7
    distraction_probability: float = 0.005
    distraction_min: float = 0.5
    distraction_max: float = 1.2
    mistake_realize_min: float = 0.1
    mistake_realize_max: float = 0.25
    after_correction_min: float = 0.03
    after_correction_max: float = 0.08
    double_press_min: float = 0.02
    double_press_max: float = 0.05
    hesitation_min: float = 0.15
    hesitation_max: float = 0.3


@dataclass(frozen=True)
class TypoConfig:
    """Configuration for typo generation weights."""

    adjacent_weight: float = 0.55
    transpose_weight: float = 0.20
    double_weight: float = 0.12
    skip_weight: float = 0.08
    missed_space_weight: float = 0.05


class Keyboard:
    """
    Keyboard input controller for Tab and WebElement.

    Provides methods for:
    - Tab: Public keyboard simulation (press, down, up, hotkey)
    - WebElement: Private text typing with optional humanization
    """

    PAUSE_CHARS = frozenset(' .,!?;:\n')

    def __init__(
        self,
        executor: CommandExecutor,
        timing: Optional[TimingConfig] = None,
        typo_config: Optional[TypoConfig] = None,
    ):
        """
        Initialize keyboard controller.

        Args:
            executor: Object with _execute_command method (Tab or WebElement).
            timing: Optional custom timing configuration.
            typo_config: Optional custom typo weights configuration.
        """
        self._executor = executor
        self._timing = timing or TimingConfig()
        self._typo_config = typo_config or TypoConfig()

    async def press(
        self,
        key: Key,
        modifiers: Optional[KeyModifier] = None,
        interval: float = 0.1,
    ):
        """
        Press and release a key (down + wait + up).

        Args:
            key: Key to press (from Key enum).
            modifiers: Optional key modifiers (Alt=1, Ctrl=2, Meta=4, Shift=8).
            interval: Time to hold the key down in seconds.

        Example:
            await tab.keyboard.press(Key.ENTER)
            await tab.keyboard.press(Key.A, modifiers=KeyModifier.CTRL)
        """
        logger.info(f'Pressing key: {key} with modifiers: {modifiers}')
        await self.down(key, modifiers)
        await asyncio.sleep(interval)
        await self.up(key)

    async def down(self, key: Key, modifiers: Optional[KeyModifier] = None):
        """
        Press a key down (without releasing).

        Args:
            key: Key to press down (from Key enum).
            modifiers: Optional key modifiers.
        """
        key_name, code = key
        logger.debug(f'Key down: {key_name}')
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_DOWN,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
            modifiers=modifiers,
        )
        await self._executor._execute_command(command)

    async def up(self, key: Key):
        """
        Release a key (key up event).

        Args:
            key: Key to release (from Key enum).
        """
        key_name, code = key
        logger.debug(f'Key up: {key_name}')
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_UP,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
        )
        await self._executor._execute_command(command)

    async def hotkey(self, key1: Key, key2: Key, key3: Optional[Key] = None):
        """
        Execute a key combination (hotkey) with up to 3 keys.

        Args:
            key1: First key (usually a modifier like Ctrl, Shift, Alt).
            key2: Second key.
            key3: Optional third key.

        Example:
            await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # Ctrl+C
        """
        logger.info(f'Hotkey: {key1} + {key2}' + (f' + {key3}' if key3 else ''))
        keys = [key1, key2]
        if key3 is not None:
            keys.append(key3)

        modifiers, non_modifiers = self._split_modifiers_and_keys(keys)
        modifier_value = self._calculate_modifier_value(modifiers)

        for key in non_modifiers:
            await self.down(key, modifiers=modifier_value)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.1)

        for key in reversed(non_modifiers):
            await self.up(key)
            await asyncio.sleep(0.05)

    async def type_text(
        self,
        text: str,
        humanize: bool = False,
        interval: Optional[float] = None,
    ):
        """
        Type text character by character.

        Args:
            text: Text to type.
            humanize: When True, simulates human-like typing with
                variable delays and occasional typos (~2%).
            interval: Deprecated. Use humanize=True instead.

        Example:
            await tab.keyboard.type_text("Hello World", humanize=True)
            await tab.keyboard.type_text("Hello World")
        """
        if interval is not None:
            warnings.warn(
                'The "interval" parameter is deprecated and will be removed '
                'in a future version. Use "humanize=True" for realistic typing.',
                DeprecationWarning,
                stacklevel=2,
            )

        if humanize:
            await self._type_text_humanized(text)
            return

        for current_char in text:
            await self._type_char(current_char)
            await asyncio.sleep(0.05)

    async def _type_text_humanized(self, text: str):
        """Type text with realistic human-like behavior."""
        char_index = 0
        while char_index < len(text):
            current_char = text[char_index]
            next_char = text[char_index + 1] if char_index + 1 < len(text) else None

            should_skip_next = await self._process_char_with_typo(current_char, next_char)

            if should_skip_next:
                char_index += 1

            await self._apply_realistic_delay(current_char)
            char_index += 1

    async def _type_char(self, char: str):
        """Type a single character."""
        command_down = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_DOWN,
            text=char,
            unmodified_text=char,
        )
        await self._executor._execute_command(command_down)

        command_up = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_UP,
        )
        await self._executor._execute_command(command_up)

    async def _type_backspace(self):
        """Send backspace keypress."""
        await self.down(Key.BACKSPACE)
        await self.up(Key.BACKSPACE)

    async def _process_char_with_typo(
        self,
        current_char: str,
        next_char: Optional[str],
    ) -> bool:
        """Process character, potentially with typo. Returns True if next should be skipped."""
        if not self._should_make_typo():
            await self._type_char(current_char)
            return False

        typo = self._generate_typo(current_char, next_char)
        return await self._handle_typo(current_char, next_char, typo)

    async def _handle_typo(
        self,
        current_char: str,
        next_char: Optional[str],
        typo: TypoResult,
    ) -> bool:
        """Handle typo. Returns True if next char should be skipped."""
        if typo.typo_type == TypoType.ADJACENT:
            await self._do_adjacent_typo(current_char, typo.wrong_char)
            return False

        if typo.typo_type == TypoType.TRANSPOSE and next_char:
            await self._do_transpose_typo(current_char, next_char)
            return True

        if typo.typo_type == TypoType.DOUBLE:
            await self._do_double_typo(current_char)
            return False

        if typo.typo_type == TypoType.SKIP:
            await self._do_skip_typo(current_char)
            return False

        if typo.typo_type == TypoType.MISSED_SPACE and current_char == ' ' and next_char:
            await self._do_missed_space_typo(current_char, next_char)
            return True

        await self._type_char(current_char)
        return False

    async def _do_adjacent_typo(self, correct_char: str, wrong_char: str):
        """Type wrong adjacent key, pause, backspace, correct."""
        timing = self._timing
        await self._type_char(wrong_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(correct_char)

    async def _do_transpose_typo(self, current_char: str, next_char: str):
        """Type chars in wrong order, then fix."""
        timing = self._timing
        await self._type_char(next_char)
        await asyncio.sleep(random.uniform(timing.keystroke_min, timing.keystroke_max))
        await self._type_char(current_char)

        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )

        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.keystroke_min, timing.keystroke_max))
        await self._type_char(next_char)

    async def _do_double_typo(self, current_char: str):
        """Type character twice, then backspace."""
        timing = self._timing
        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.double_press_min, timing.double_press_max))
        await self._type_char(current_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()

    async def _do_skip_typo(self, current_char: str):
        """Hesitate, then type normally."""
        timing = self._timing
        await asyncio.sleep(random.uniform(timing.hesitation_min, timing.hesitation_max))
        await self._type_char(current_char)

    async def _do_missed_space_typo(self, space_char: str, next_char: str):
        """Miss space, type next char, realize, go back and fix."""
        timing = self._timing
        await self._type_char(next_char)
        await asyncio.sleep(random.uniform(timing.mistake_realize_min, timing.mistake_realize_max))
        await self._type_backspace()
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(space_char)
        await asyncio.sleep(
            random.uniform(timing.after_correction_min, timing.after_correction_max)
        )
        await self._type_char(next_char)

    async def _apply_realistic_delay(self, typed_char: str):
        """Apply realistic delay after typing a character."""
        timing = self._timing
        delay = random.uniform(timing.keystroke_min, timing.keystroke_max)

        if typed_char in self.PAUSE_CHARS:
            delay += random.uniform(timing.punctuation_min, timing.punctuation_max)

        if random.random() < timing.thinking_probability:
            delay += random.uniform(timing.thinking_min, timing.thinking_max)

        if random.random() < timing.distraction_probability:
            delay += random.uniform(timing.distraction_min, timing.distraction_max)

        await asyncio.sleep(delay)

    @staticmethod
    def _should_make_typo() -> bool:
        """Determine if a typo should occur."""
        return random.random() < DEFAULT_TYPO_PROBABILITY

    def _generate_typo(self, current_char: str, next_char: Optional[str]) -> TypoResult:
        """Generate a realistic typo based on QWERTY layout."""
        typo_type = self._select_typo_type()
        return self._create_typo(typo_type, current_char, next_char)

    def _select_typo_type(self) -> TypoType:
        """Select typo type based on weights."""
        config = self._typo_config
        typo_types = [
            TypoType.ADJACENT,
            TypoType.TRANSPOSE,
            TypoType.DOUBLE,
            TypoType.SKIP,
            TypoType.MISSED_SPACE,
        ]
        typo_weights = [
            config.adjacent_weight,
            config.transpose_weight,
            config.double_weight,
            config.skip_weight,
            config.missed_space_weight,
        ]
        return random.choices(typo_types, weights=typo_weights, k=1)[0]

    def _create_typo(
        self,
        typo_type: TypoType,
        current_char: str,
        next_char: Optional[str],
    ) -> TypoResult:
        """Create typo result based on type."""
        typo_handlers = {
            TypoType.ADJACENT: lambda: self._create_adjacent_typo(current_char),
            TypoType.TRANSPOSE: lambda: self._create_transpose_typo(current_char, next_char),
            TypoType.MISSED_SPACE: lambda: self._create_missed_space_typo(current_char),
            TypoType.DOUBLE: lambda: TypoResult(typo_type=TypoType.DOUBLE, wrong_char=current_char),
            TypoType.SKIP: lambda: TypoResult(typo_type=TypoType.SKIP),
        }
        handler = typo_handlers.get(typo_type, typo_handlers[TypoType.SKIP])
        return handler()

    def _create_transpose_typo(self, current_char: str, next_char: Optional[str]) -> TypoResult:
        """Create transpose typo, falling back to adjacent if not possible."""
        if next_char and next_char.isalpha():
            return TypoResult(typo_type=TypoType.TRANSPOSE, wrong_char=next_char)
        return self._create_adjacent_typo(current_char)

    def _create_missed_space_typo(self, current_char: str) -> TypoResult:
        """Create missed space typo, falling back to adjacent if not a space."""
        if current_char == ' ':
            return TypoResult(typo_type=TypoType.MISSED_SPACE)
        return self._create_adjacent_typo(current_char)

    @staticmethod
    def _create_adjacent_typo(original_char: str) -> TypoResult:
        """Create adjacent key typo."""
        lowercase_char = original_char.lower()

        if lowercase_char not in QWERTY_NEIGHBORS:
            return TypoResult(typo_type=TypoType.DOUBLE, wrong_char=original_char)

        adjacent_char = random.choice(QWERTY_NEIGHBORS[lowercase_char])

        if original_char.isupper():
            adjacent_char = adjacent_char.upper()

        return TypoResult(typo_type=TypoType.ADJACENT, wrong_char=adjacent_char)

    @staticmethod
    def _split_modifiers_and_keys(keys: list[Key]) -> tuple[list[Key], list[Key]]:
        """Split keys into modifiers and non-modifiers."""
        modifier_keys = {Key.CONTROL, Key.SHIFT, Key.ALT, Key.META}
        modifiers = [key for key in keys if key in modifier_keys]
        non_modifiers = [key for key in keys if key not in modifier_keys]
        return modifiers, non_modifiers

    @staticmethod
    def _calculate_modifier_value(modifiers: list[Key]) -> Optional[KeyModifier]:
        """Calculate KeyModifier value from modifier keys."""
        if not modifiers:
            return None

        modifier_map = {
            Key.ALT: 1,
            Key.CONTROL: 2,
            Key.META: 4,
            Key.SHIFT: 8,
        }

        value = sum(modifier_map.get(mod, 0) for mod in modifiers)
        return cast(KeyModifier, value) if value > 0 else None


KeyboardAPI = Keyboard
