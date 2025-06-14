# Input Commands

Input commands handle mouse and keyboard interactions, providing human-like input simulation.

## Overview

The input commands module provides functionality for simulating user input including mouse movements, clicks, keyboard typing, and key presses.

::: pydoll.commands.input_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Input commands are used by element interaction methods and can be used directly for advanced input scenarios:

```python
from pydoll.commands.input_commands import dispatch_mouse_event, dispatch_key_event
from pydoll.connection.connection_handler import ConnectionHandler

# Simulate mouse click
connection = ConnectionHandler()
await dispatch_mouse_event(
    connection, 
    type="mousePressed", 
    x=100, 
    y=200, 
    button="left"
)

# Simulate keyboard typing
await dispatch_key_event(
    connection,
    type="keyDown",
    key="Enter"
)
```

## Key Functionality

The input commands module provides functions for:

### Mouse Events
- `dispatch_mouse_event()` - Mouse clicks, movements, and wheel events
- Mouse button states (left, right, middle)
- Coordinate-based positioning
- Drag and drop operations

### Keyboard Events
- `dispatch_key_event()` - Key press and release events
- `insert_text()` - Direct text insertion
- Special key handling (Enter, Tab, Arrow keys, etc.)
- Modifier keys (Ctrl, Alt, Shift)

### Touch Events
- Touch screen simulation
- Multi-touch gestures
- Touch coordinates and pressure

## Human-like Behavior

The input commands support human-like behavior patterns:

- Natural mouse movement curves
- Realistic typing speeds and patterns
- Random micro-delays between actions
- Pressure-sensitive touch events

!!! tip "Element Methods"
    For most use cases, use the higher-level element methods like `element.click()` and `element.type_text()` which provide a more convenient API and handle common scenarios automatically. 