"""Pure-logic tests for keyboard/scroll static helpers (no browser, no fakes)."""

from __future__ import annotations

import pytest

from pydoll.constants import Key, ScrollPosition
from pydoll.interactions.keyboard import Keyboard
from pydoll.interactions.scroll import Scroll


def test_split_modifiers_and_keys():
    modifiers, keys = Keyboard._split_modifiers_and_keys([Key.CONTROL, Key.A, Key.SHIFT, Key.B])
    assert modifiers == [Key.CONTROL, Key.SHIFT]
    assert keys == [Key.A, Key.B]


def test_calculate_modifier_value():
    assert Keyboard._calculate_modifier_value([]) is None
    assert Keyboard._calculate_modifier_value([Key.ALT]) == 1
    assert Keyboard._calculate_modifier_value([Key.CONTROL]) == 2
    assert Keyboard._calculate_modifier_value([Key.CONTROL, Key.SHIFT]) == 10


@pytest.mark.parametrize(
    'position, expected',
    [
        (ScrollPosition.UP, ('top', -100)),
        (ScrollPosition.DOWN, ('top', 100)),
        (ScrollPosition.LEFT, ('left', -100)),
        (ScrollPosition.RIGHT, ('left', 100)),
    ],
)
def test_get_axis_and_distance(position, expected):
    assert Scroll._get_axis_and_distance(position, 100) == expected


def test_get_behavior():
    assert Scroll._get_behavior(True) == 'smooth'
    assert Scroll._get_behavior(False) == 'auto'
