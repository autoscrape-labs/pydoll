"""Command-shaping tests for the Emulation screen commands.

These builders translate a Python call into the CDP command dict; the tests
assert the method name and that only the provided parameters are emitted.
"""

from __future__ import annotations

from pydoll.commands.emulation_commands import EmulationCommands
from pydoll.protocol.emulation.methods import EmulationMethod


def test_get_screen_infos_shape():
    command = EmulationCommands.get_screen_infos()
    assert command['method'] == EmulationMethod.GET_SCREEN_INFOS
    assert 'params' not in command


def test_update_screen_full():
    command = EmulationCommands.update_screen(
        '1',
        width=2880,
        height=1800,
        device_pixel_ratio=2.0,
        color_depth=30,
        work_area_insets={'top': 50, 'bottom': 30},
        is_internal=True,
    )
    assert command['method'] == EmulationMethod.UPDATE_SCREEN
    assert command['params'] == {
        'screenId': '1',
        'width': 2880,
        'height': 1800,
        'devicePixelRatio': 2.0,
        'colorDepth': 30,
        'workAreaInsets': {'top': 50, 'bottom': 30},
        'isInternal': True,
    }


def test_update_screen_omits_unset_params():
    command = EmulationCommands.update_screen('1', width=1920)
    assert command['params'] == {'screenId': '1', 'width': 1920}


def test_update_screen_requires_only_screen_id():
    command = EmulationCommands.update_screen('2')
    assert command['params'] == {'screenId': '2'}
