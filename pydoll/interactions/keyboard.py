from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional, cast

from pydoll.commands import InputCommands
from pydoll.constants import Key
from pydoll.protocol.input.types import KeyEventType, KeyModifier

if TYPE_CHECKING:
    from pydoll.browser.tab import Tab

logger = logging.getLogger(__name__)


class KeyboardAPI:
    """
    API for controlling keyboard input at page level.

    Provides methods for simulating keyboard input, key combinations,
    and realistic typing using CDP Input domain.
    """

    def __init__(self, tab: Tab):
        """
        Initialize the KeyboardAPI with a tab instance.

        Args:
            tab: Tab instance to execute keyboard commands on.
        """
        logger.debug(f'Initializing KeyboardAPI for tab: {tab}')
        self._tab = tab

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
        logger.info(f'Pressing key: {key} with modifiers: {modifiers} and interval: {interval}')
        await self.down(key, modifiers)
        await asyncio.sleep(interval)
        await self.up(key)

    async def down(self, key: Key, modifiers: Optional[KeyModifier] = None):
        """
        Press a key down (without releasing).

        Args:
            key: Key to press down (from Key enum).
            modifiers: Optional key modifiers (Alt=1, Ctrl=2, Meta=4, Shift=8).

        Example:
            await tab.keyboard.down(Key.SHIFT)
        """
        key_name, code = key
        logger.info(f'Pressing key down: {key_name} with modifiers: {modifiers}')
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_DOWN,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
            modifiers=modifiers,
        )
        await self._tab._execute_command(command)

    async def up(self, key: Key):
        """
        Release a key (key up event).

        Args:
            key: Key to release (from Key enum).

        Example:
            await tab.keyboard.up(Key.SHIFT)
        """
        logger.info(f'Pressing key up: {key}')
        key_name, code = key
        command = InputCommands.dispatch_key_event(
            type=KeyEventType.KEY_UP,
            key=key_name,
            windows_virtual_key_code=code,
            native_virtual_key_code=code,
        )
        await self._tab._execute_command(command)

    async def hotkey(self, key1: Key, key2: Key, key3: Optional[Key] = None):
        """
        Execute a key combination (hotkey) with up to 3 keys.

        Automatically detects modifier keys (Ctrl, Shift, Alt, Meta) and applies
        them correctly when pressing non-modifier keys.

        Args:
            key1: First key (usually a modifier like Ctrl, Shift, Alt).
            key2: Second key.
            key3: Optional third key.

        Example:
            await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # Ctrl+C
            await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.T)  # Ctrl+Shift+T
        """
        logger.info(f'Executing hotkey: {key1} {key2} {key3}')
        keys = [key1, key2]
        if key3 is not None:
            keys.append(key3)

        modifiers, non_modifiers = self._split_modifiers_and_keys(keys)
        modifier_value = self._calculate_modifier_value(modifiers)

        logger.debug(f'Modifiers: {modifiers} modifier_value: {modifier_value}')
        for key in non_modifiers:
            await self.down(key, modifiers=modifier_value)
            await asyncio.sleep(0.05)

        await asyncio.sleep(0.1)

        for key in reversed(non_modifiers):
            await self.up(key)
            await asyncio.sleep(0.05)

    @staticmethod
    def _split_modifiers_and_keys(keys: list[Key]) -> tuple[list[Key], list[Key]]:
        """
        Split keys into modifiers and non-modifiers.

        Args:
            keys: List of keys to split.

        Returns:
            Tuple of (modifiers, non_modifiers).
        """
        modifier_keys = {Key.CONTROL, Key.SHIFT, Key.ALT, Key.META}
        modifiers = [k for k in keys if k in modifier_keys]
        non_modifiers = [k for k in keys if k not in modifier_keys]
        logger.debug(f'Modifiers: {modifiers} Non-modifiers: {non_modifiers}')
        return modifiers, non_modifiers

    @staticmethod
    def _calculate_modifier_value(modifiers: list[Key]) -> Optional[KeyModifier]:
        """
        Calculate the KeyModifier value from a list of modifier keys.

        Args:
            modifiers: List of modifier keys.

        Returns:
            Combined KeyModifier value, or None if no modifiers.
        """
        logger.debug(f'Calculating modifier value for: {modifiers}')
        if not modifiers:
            return None

        modifier_map = {
            Key.ALT: 1,
            Key.CONTROL: 2,
            Key.META: 4,
            Key.SHIFT: 8,
        }

        value = 0
        for modifier in modifiers:
            value += modifier_map.get(modifier, 0)

        return cast(KeyModifier, value) if value > 0 else None
