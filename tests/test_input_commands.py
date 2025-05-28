from pydoll.protocol.commands import InputCommands
from pydoll.constants import Keys


def test_mouse_press():
    x, y = 100, 200
    expected_command = {
        'method': 'Input.dispatchMouseEvent',
        'params': {
            'type': 'mousePressed',
            'button': 'left',
            'x': x,
            'y': y,
            'clickCount': 1,
            'modifiers': 0,
        },
    }
    assert InputCommands.mouse_press(x, y) == expected_command


def test_mouse_release():
    x, y = 100, 200
    expected_command = {
        'method': 'Input.dispatchMouseEvent',
        'params': {
            'type': 'mouseReleased',
            'button': 'left',
            'x': x,
            'y': y,
            'clickCount': 1,
            'modifiers': 0,
        },
    }
    assert InputCommands.mouse_release(x, y) == expected_command


def test_key_press():
    char = 'a'
    expected_command = {
        'method': 'Input.dispatchKeyEvent',
        'params': {
            'type': 'char',
            'text': char,
        },
    }
    assert InputCommands.char_press(char) == expected_command


def test_paste_text():
    text = 'hello'
    expected_command = {
        'method': 'Input.insertText',
        'params': {
            'text': text,
        },
    }
    assert InputCommands.paste_text(text) == expected_command
