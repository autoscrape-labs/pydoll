"""Unit tests for the humanized typing engine of Keyboard.

The contract under test is behavioural: no matter which typo the engine injects,
the self-correction must leave the *intended* text in the field. A FakeTextField
plays the role of the browser's focused input — it reconstructs the resulting
text from the CDP key events (a keyDown with text appends, a Backspace deletes) —
so the assertions look at the final text, not the sequence of keystrokes.

Each typo type is forced deterministically through the public ``TypoConfig``
weights (a single weight set to 1.0), while the external ``random`` source is
pinned so a typo is always attempted and delays collapse to zero.
"""

from __future__ import annotations

import pytest

from pydoll.interactions.keyboard import Keyboard, TypoConfig

RANDOM = 'pydoll.interactions.keyboard.random'


class FakeTextField:
    """Stand-in for a focused browser input that records typed text from key events."""

    def __init__(self):
        self.text = ''
        self.focus_calls = 0

    async def focus(self):
        self.focus_calls += 1

    async def _execute_command(self, command):
        params = command['params']
        if params.get('type') == 'keyDown':
            if params.get('key') == 'Backspace':
                self.text = self.text[:-1]
            elif params.get('text'):
                self.text += params['text']
        return {}


def _only(weight_name: str) -> TypoConfig:
    weights = {
        'adjacent_weight': 0.0,
        'transpose_weight': 0.0,
        'double_weight': 0.0,
        'skip_weight': 0.0,
        'missed_space_weight': 0.0,
    }
    weights[weight_name] = 1.0
    return TypoConfig(**weights)


@pytest.fixture
def field():
    return FakeTextField()


@pytest.fixture
def force_typos(monkeypatch):
    monkeypatch.setattr(f'{RANDOM}.random', lambda: 0.0)
    monkeypatch.setattr(f'{RANDOM}.uniform', lambda a, b: 0.0)


@pytest.mark.asyncio
async def test_humanized_typing_without_typos_reproduces_text(field, monkeypatch):
    monkeypatch.setattr(f'{RANDOM}.random', lambda: 0.99)
    monkeypatch.setattr(f'{RANDOM}.uniform', lambda a, b: 0.0)

    await Keyboard(field).type_text('hello world', humanize=True)

    assert field.text == 'hello world'
    assert field.focus_calls > 0


@pytest.mark.parametrize(
    ('weight_name', 'text'),
    [
        ('adjacent_weight', 'ab'),
        ('transpose_weight', 'ab'),
        ('double_weight', 'ab'),
        ('skip_weight', 'ab'),
        ('missed_space_weight', 'a b'),
    ],
)
@pytest.mark.asyncio
async def test_each_typo_type_self_corrects_to_intended_text(field, force_typos, weight_name, text):
    await Keyboard(field, typo_config=_only(weight_name)).type_text(text, humanize=True)
    assert field.text == text


@pytest.mark.asyncio
async def test_adjacent_typo_on_non_qwerty_char_still_yields_char(field, force_typos):
    await Keyboard(field, typo_config=_only('adjacent_weight')).type_text('1', humanize=True)
    assert field.text == '1'


@pytest.mark.asyncio
async def test_transpose_typo_without_alpha_neighbor_still_yields_text(field, force_typos):
    await Keyboard(field, typo_config=_only('transpose_weight')).type_text('a1', humanize=True)
    assert field.text == 'a1'


class RecordingField(FakeTextField):
    """Records key events in order so hold times can be read between them."""

    def __init__(self):
        super().__init__()
        self.trace: list[tuple[str, object]] = []

    async def _execute_command(self, command):
        params = command['params']
        self.trace.append((params.get('type'), params.get('key')))
        return await super()._execute_command(command)


@pytest.fixture
def recording_field():
    return RecordingField()


@pytest.mark.asyncio
async def test_default_typing_holds_each_key_before_releasing(recording_field, monkeypatch):
    """Keydown and keyup must not arrive back to back: humans hold a key for tens of ms."""
    sleeps: list[float] = []

    async def fake_sleep(delay):
        recording_field.trace.append(('sleep', delay))
        sleeps.append(delay)

    monkeypatch.setattr('pydoll.interactions.keyboard.asyncio.sleep', fake_sleep)
    keyboard = Keyboard(recording_field)
    await keyboard.type_text('ab')

    trace = recording_field.trace
    down = trace.index(('keyDown', 'a'))
    assert trace[down + 1] == ('sleep', Keyboard.DEFAULT_KEY_HOLD)
    assert trace[down + 2] == ('keyUp', 'a')
    assert recording_field.text == 'ab'


@pytest.mark.asyncio
async def test_humanized_typing_draws_the_hold_from_the_timing_config(recording_field, monkeypatch):
    draws: list[tuple[float, float]] = []

    def fake_uniform(a, b):
        draws.append((a, b))
        return b

    monkeypatch.setattr(f'{RANDOM}.random', lambda: 0.99)
    monkeypatch.setattr(f'{RANDOM}.uniform', fake_uniform)

    async def fake_sleep(delay):
        recording_field.trace.append(('sleep', delay))

    monkeypatch.setattr('pydoll.interactions.keyboard.asyncio.sleep', fake_sleep)
    keyboard = Keyboard(recording_field)
    timing = keyboard._timing
    await keyboard.type_text('a', humanize=True)

    trace = recording_field.trace
    down = trace.index(('keyDown', 'a'))
    assert trace[down + 1] == ('sleep', timing.key_hold_max)
    assert trace[down + 2] == ('keyUp', 'a')
    assert (timing.key_hold_min, timing.key_hold_max) in draws
