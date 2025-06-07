"""
Tests for InputCommands class.

This module contains comprehensive tests for all InputCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.input_commands import InputCommands
from pydoll.constants import (
    DragEventType,
    GestureSourceType,
    KeyEventType,
    KeyLocation,
    KeyModifier,
    MouseButton,
    MouseEventType,
    PointerType,
    TouchEventType,
)
from pydoll.protocol.input.methods import InputMethod


def test_cancel_dragging():
    """Test cancel_dragging method generates correct command."""
    expected_command = {
        'method': InputMethod.CANCEL_DRAGGING,
    }
    result = InputCommands.cancel_dragging()
    assert result['method'] == expected_command['method']
    assert 'params' not in result


def test_dispatch_key_event_minimal():
    """Test dispatch_key_event with minimal parameters."""
    expected_command = {
        'method': InputMethod.DISPATCH_KEY_EVENT,
        'params': {
            'type': KeyEventType.KEY_DOWN,
        },
    }
    result = InputCommands.dispatch_key_event(type=KeyEventType.KEY_DOWN)
    assert result['method'] == expected_command['method']
    assert result['params']['type'] == expected_command['params']['type']


def test_dispatch_key_event_with_modifiers():
    """Test dispatch_key_event with modifiers."""
    result = InputCommands.dispatch_key_event(
        type=KeyEventType.KEY_DOWN,
        modifiers=KeyModifier.CTRL | KeyModifier.SHIFT,
        text='A',
    )
    assert result['method'] == InputMethod.DISPATCH_KEY_EVENT
    assert result['params']['type'] == KeyEventType.KEY_DOWN
    assert result['params']['modifiers'] == KeyModifier.CTRL | KeyModifier.SHIFT
    assert result['params']['text'] == 'A'


def test_dispatch_key_event_with_all_params():
    """Test dispatch_key_event with all parameters."""
    result = InputCommands.dispatch_key_event(
        type=KeyEventType.CHAR,
        modifiers=KeyModifier.ALT,
        timestamp=123.456,
        text='a',
        unmodified_text='A',
        key_identifier='U+0041',
        code='KeyA',
        key='a',
        windows_virtual_key_code=65,
        native_virtual_key_code=65,
        auto_repeat=True,
        is_keypad=False,
        is_system_key=False,
        location=KeyLocation.LEFT,
        commands=['selectAll'],
    )
    assert result['method'] == InputMethod.DISPATCH_KEY_EVENT
    assert result['params']['type'] == KeyEventType.CHAR
    assert result['params']['modifiers'] == KeyModifier.ALT
    assert result['params']['timestamp'] == 123.456
    assert result['params']['text'] == 'a'
    assert result['params']['unmodifiedText'] == 'A'
    assert result['params']['keyIdentifier'] == 'U+0041'
    assert result['params']['code'] == 'KeyA'
    assert result['params']['key'] == 'a'
    assert result['params']['windowsVirtualKeyCode'] == 65
    assert result['params']['nativeVirtualKeyCode'] == 65
    assert result['params']['autoRepeat'] is True
    assert result['params']['isKeypad'] is False
    assert result['params']['isSystemKey'] is False
    assert result['params']['location'] == KeyLocation.LEFT
    assert result['params']['commands'] == ['selectAll']


def test_dispatch_mouse_event_minimal():
    """Test dispatch_mouse_event with minimal parameters."""
    result = InputCommands.dispatch_mouse_event(
        type=MouseEventType.MOUSE_PRESSED,
        x=100,
        y=200,
    )
    assert result['method'] == InputMethod.DISPATCH_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_PRESSED
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200


def test_dispatch_mouse_event_with_button():
    """Test dispatch_mouse_event with button parameter."""
    result = InputCommands.dispatch_mouse_event(
        type=MouseEventType.MOUSE_PRESSED,
        x=100,
        y=200,
        button=MouseButton.LEFT,
        click_count=1,
    )
    assert result['method'] == InputMethod.DISPATCH_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_PRESSED
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
    assert result['params']['button'] == MouseButton.LEFT
    assert result['params']['clickCount'] == 1


def test_dispatch_mouse_event_with_all_params():
    """Test dispatch_mouse_event with all parameters."""
    result = InputCommands.dispatch_mouse_event(
        type=MouseEventType.MOUSE_MOVED,
        x=150,
        y=250,
        modifiers=KeyModifier.CTRL,
        timestamp=789.123,
        button=MouseButton.RIGHT,
        click_count=2,
        force=0.5,
        tangential_pressure=0.3,
        tilt_x=15.0,
        tilt_y=20.0,
        twist=45,
        delta_x=10.0,
        delta_y=15.0,
        pointer_type=PointerType.PEN,
    )
    assert result['method'] == InputMethod.DISPATCH_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_MOVED
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['modifiers'] == KeyModifier.CTRL
    assert result['params']['timestamp'] == 789.123
    assert result['params']['button'] == MouseButton.RIGHT
    assert result['params']['clickCount'] == 2
    assert result['params']['force'] == 0.5
    assert result['params']['tangentialPressure'] == 0.3
    assert result['params']['tiltX'] == 15.0
    assert result['params']['tiltY'] == 20.0
    assert result['params']['twist'] == 45
    assert result['params']['deltaX'] == 10.0
    assert result['params']['deltaY'] == 15.0
    assert result['params']['pointerType'] == PointerType.PEN


def test_dispatch_touch_event_minimal():
    """Test dispatch_touch_event with minimal parameters."""
    result = InputCommands.dispatch_touch_event(
        type=TouchEventType.TOUCH_START,
    )
    assert result['method'] == InputMethod.DISPATCH_TOUCH_EVENT
    assert result['params']['type'] == TouchEventType.TOUCH_START


def test_dispatch_touch_event_with_touch_points():
    """Test dispatch_touch_event with touch points."""
    touch_points = [
        {
            'x': 100,
            'y': 200,
            'radiusX': 10,
            'radiusY': 10,
            'rotationAngle': 0,
            'force': 1.0,
        }
    ]
    result = InputCommands.dispatch_touch_event(
        type=TouchEventType.TOUCH_START,
        touch_points=touch_points,
        modifiers=KeyModifier.SHIFT,
        timestamp=456.789,
    )
    assert result['method'] == InputMethod.DISPATCH_TOUCH_EVENT
    assert result['params']['type'] == TouchEventType.TOUCH_START
    assert result['params']['touchPoints'] == touch_points
    assert result['params']['modifiers'] == KeyModifier.SHIFT
    assert result['params']['timestamp'] == 456.789


def test_set_ignore_input_events():
    """Test set_ignore_input_events"""
    result = InputCommands.set_ignore_input_events(enabled=True)
    assert result['method'] == InputMethod.SET_IGNORE_INPUT_EVENTS
    assert result['params']['enabled'] is True


def test_dispatch_drag_event_minimal():
    """Test dispatch_drag_event with minimal parameters."""
    result = InputCommands.dispatch_drag_event(
        type=DragEventType.DRAG_ENTER,
        x=100,
        y=200,
    )
    assert result['method'] == InputMethod.DISPATCH_DRAG_EVENT
    assert result['params']['type'] == DragEventType.DRAG_ENTER
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200


def test_dispatch_drag_event_with_data():
    """Test dispatch_drag_event with drag data."""
    drag_data = {
        'items': [
            {
                'mimeType': 'text/plain',
                'data': 'Hello World',
            }
        ],
        'dragOperationsMask': 1,
    }
    result = InputCommands.dispatch_drag_event(
        type=DragEventType.DROP,
        x=150,
        y=250,
        data=drag_data,
        modifiers=KeyModifier.ALT,
    )
    assert result['method'] == InputMethod.DISPATCH_DRAG_EVENT
    assert result['params']['type'] == DragEventType.DROP
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['data'] == drag_data
    assert result['params']['modifiers'] == KeyModifier.ALT


def test_emulate_touch_from_mouse_event_minimal():
    """Test emulate_touch_from_mouse_event with minimal parameters."""
    result = InputCommands.emulate_touch_from_mouse_event(
        type=MouseEventType.MOUSE_PRESSED,
        x=100,
        y=200,
        button=MouseButton.LEFT,
    )
    assert result['method'] == InputMethod.EMULATE_TOUCH_FROM_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_PRESSED
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
    assert result['params']['button'] == MouseButton.LEFT


def test_emulate_touch_from_mouse_event_with_all_params():
    """Test emulate_touch_from_mouse_event with all parameters."""
    result = InputCommands.emulate_touch_from_mouse_event(
        type=MouseEventType.MOUSE_MOVED,
        x=150,
        y=250,
        button=MouseButton.RIGHT,
        timestamp=123.456,
        delta_x=10.0,
        delta_y=15.0,
        modifiers=KeyModifier.CTRL | KeyModifier.SHIFT,
        click_count=2,
    )
    assert result['method'] == InputMethod.EMULATE_TOUCH_FROM_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_MOVED
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['button'] == MouseButton.RIGHT
    assert result['params']['timestamp'] == 123.456
    assert result['params']['deltaX'] == 10.0
    assert result['params']['deltaY'] == 15.0
    assert result['params']['modifiers'] == KeyModifier.CTRL | KeyModifier.SHIFT
    assert result['params']['clickCount'] == 2


def test_ime_set_composition():
    """Test ime_set_composition method."""
    result = InputCommands.ime_set_composition(
        text='Hello',
        selection_start=0,
        selection_end=5,
    )
    assert result['method'] == InputMethod.IME_SET_COMPOSITION
    assert result['params']['text'] == 'Hello'
    assert result['params']['selectionStart'] == 0
    assert result['params']['selectionEnd'] == 5


def test_ime_set_composition_with_replacement():
    """Test ime_set_composition with replacement parameters."""
    result = InputCommands.ime_set_composition(
        text='World',
        selection_start=0,
        selection_end=5,
        replacement_start=0,
        replacement_end=5,
    )
    assert result['method'] == InputMethod.IME_SET_COMPOSITION
    assert result['params']['text'] == 'World'
    assert result['params']['selectionStart'] == 0
    assert result['params']['selectionEnd'] == 5
    assert result['params']['replacementStart'] == 0
    assert result['params']['replacementEnd'] == 5


def test_insert_text():
    """Test insert_text method."""
    result = InputCommands.insert_text(text='Hello World')
    assert result['method'] == InputMethod.INSERT_TEXT
    assert result['params']['text'] == 'Hello World'


def test_set_intercept_drags_enabled():
    """Test set_intercept_drags with enabled=True."""
    result = InputCommands.set_intercept_drags(enabled=True)
    assert result['method'] == InputMethod.SET_INTERCEPT_DRAGS
    assert result['params']['enabled'] is True


def test_set_intercept_drags_disabled():
    """Test set_intercept_drags with enabled=False."""
    result = InputCommands.set_intercept_drags(enabled=False)
    assert result['method'] == InputMethod.SET_INTERCEPT_DRAGS
    assert result['params']['enabled'] is False


def test_synthesize_pinch_gesture_minimal():
    """Test synthesize_pinch_gesture with minimal parameters."""
    result = InputCommands.synthesize_pinch_gesture(
        x=100,
        y=200,
        scale_factor=2.0,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_PINCH_GESTURE
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
    assert result['params']['scaleFactor'] == 2.0


def test_synthesize_pinch_gesture_with_all_params():
    """Test synthesize_pinch_gesture with all parameters."""
    result = InputCommands.synthesize_pinch_gesture(
        x=150,
        y=250,
        scale_factor=1.5,
        relative_speed=100,
        gesture_source_type=GestureSourceType.TOUCH,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_PINCH_GESTURE
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['scaleFactor'] == 1.5
    assert result['params']['relativeSpeed'] == 100
    assert result['params']['gestureSourceType'] == GestureSourceType.TOUCH


def test_synthesize_scroll_gesture_minimal():
    """Test synthesize_scroll_gesture with minimal parameters."""
    result = InputCommands.synthesize_scroll_gesture(
        x=100,
        y=200,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_SCROLL_GESTURE
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200


def test_synthesize_scroll_gesture_with_distance():
    """Test synthesize_scroll_gesture with distance parameters."""
    result = InputCommands.synthesize_scroll_gesture(
        x=100,
        y=200,
        x_distance=50.0,
        y_distance=100.0,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_SCROLL_GESTURE
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
    assert result['params']['xDistance'] == 50.0
    assert result['params']['yDistance'] == 100.0


def test_synthesize_scroll_gesture_with_all_params():
    """Test synthesize_scroll_gesture with all parameters."""
    result = InputCommands.synthesize_scroll_gesture(
        x=150,
        y=250,
        x_distance=75.0,
        y_distance=125.0,
        x_overscroll=10.0,
        y_overscroll=15.0,
        prevent_fling=True,
        speed=500,
        gesture_source_type=GestureSourceType.MOUSE,
        repeat_count=3,
        repeat_delay_ms=100,
        interaction_marker_name='scroll_test',
    )
    assert result['method'] == InputMethod.SYNTHESIZE_SCROLL_GESTURE
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['xDistance'] == 75.0
    assert result['params']['yDistance'] == 125.0
    assert result['params']['xOverscroll'] == 10.0
    assert result['params']['yOverscroll'] == 15.0
    assert result['params']['preventFling'] is True
    assert result['params']['speed'] == 500
    assert result['params']['gestureSourceType'] == GestureSourceType.MOUSE
    assert result['params']['repeatCount'] == 3
    assert result['params']['repeatDelayMs'] == 100
    assert result['params']['interactionMarkerName'] == 'scroll_test'


def test_synthesize_tap_gesture_minimal():
    """Test synthesize_tap_gesture with minimal parameters."""
    result = InputCommands.synthesize_tap_gesture(
        x=100,
        y=200,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_TAP_GESTURE
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200


def test_synthesize_tap_gesture_with_all_params():
    """Test synthesize_tap_gesture with all parameters."""
    result = InputCommands.synthesize_tap_gesture(
        x=150,
        y=250,
        duration=500,
        tap_count=2,
        gesture_source_type=GestureSourceType.TOUCH,
    )
    assert result['method'] == InputMethod.SYNTHESIZE_TAP_GESTURE
    assert result['params']['x'] == 150
    assert result['params']['y'] == 250
    assert result['params']['duration'] == 500
    assert result['params']['tapCount'] == 2
    assert result['params']['gestureSourceType'] == GestureSourceType.TOUCH


def test_mouse_wheel_event():
    """Test mouse wheel event dispatch."""
    result = InputCommands.dispatch_mouse_event(
        type=MouseEventType.MOUSE_WHEEL,
        x=100,
        y=200,
        delta_x=10.0,
        delta_y=-20.0,
    )
    assert result['method'] == InputMethod.DISPATCH_MOUSE_EVENT
    assert result['params']['type'] == MouseEventType.MOUSE_WHEEL
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
    assert result['params']['deltaX'] == 10.0
    assert result['params']['deltaY'] == -20.0


def test_key_event_with_location():
    """Test key event with location parameter."""
    result = InputCommands.dispatch_key_event(
        type=KeyEventType.KEY_DOWN,
        key='Shift',
        location=KeyLocation.LEFT,
    )
    assert result['method'] == InputMethod.DISPATCH_KEY_EVENT
    assert result['params']['type'] == KeyEventType.KEY_DOWN
    assert result['params']['key'] == 'Shift'
    assert result['params']['location'] == KeyLocation.LEFT


def test_touch_event_multiple_points():
    """Test touch event with multiple touch points."""
    touch_points = [
        {
            'x': 100,
            'y': 200,
            'radiusX': 10,
            'radiusY': 10,
            'rotationAngle': 0,
            'force': 1.0,
        },
        {
            'x': 300,
            'y': 400,
            'radiusX': 15,
            'radiusY': 15,
            'rotationAngle': 45,
            'force': 0.8,
        },
    ]
    result = InputCommands.dispatch_touch_event(
        type=TouchEventType.TOUCH_MOVE,
        touch_points=touch_points,
    )
    assert result['method'] == InputMethod.DISPATCH_TOUCH_EVENT
    assert result['params']['type'] == TouchEventType.TOUCH_MOVE
    assert result['params']['touchPoints'] == touch_points
    assert len(result['params']['touchPoints']) == 2


def test_drag_event_cancel():
    """Test drag cancel event."""
    result = InputCommands.dispatch_drag_event(
        type=DragEventType.DRAG_CANCEL,
        x=100,
        y=200,
    )
    assert result['method'] == InputMethod.DISPATCH_DRAG_EVENT
    assert result['params']['type'] == DragEventType.DRAG_CANCEL
    assert result['params']['x'] == 100
    assert result['params']['y'] == 200
