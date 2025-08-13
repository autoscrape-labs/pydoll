# Target Commands

Target commands manage browser targets including tabs, windows, and other browsing contexts.

## Overview

The target commands module provides functionality for creating, managing, and controlling browser targets such as tabs, popup windows, and service workers.

::: pydoll.commands.target_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Target commands are used internally by browser classes to manage tabs and windows:

```python
from pydoll.commands.target_commands import get_targets, create_target, close_target
from pydoll.connection.connection_handler import ConnectionHandler

# Get all browser targets
connection = ConnectionHandler()
targets = await get_targets(connection)

# Create a new tab
new_target = await create_target(connection, url="https://example.com")

# Close a target
await close_target(connection, target_id=new_target.target_id)
```

## Key Functionality

The target commands module provides functions for:

### Target Management
- `get_targets()` - List all browser targets
- `create_target()` - Create new tabs or windows
- `close_target()` - Close specific targets
- `activate_target()` - Bring target to foreground

### Target Information
- `get_target_info()` - Get detailed target information
- Target types: page, background_page, service_worker, browser
- Target states: attached, detached, crashed

### Session Management
- `attach_to_target()` - Attach to target for control
- `detach_from_target()` - Detach from target
- `send_message_to_target()` - Send commands to targets

### Browser Context
- `create_browser_context()` - Create isolated browser context
- `dispose_browser_context()` - Remove browser context
- `get_browser_contexts()` - List browser contexts

## Target Types

Different types of targets can be managed:

### Page Targets
```python
# Create a new tab
page_target = await create_target(
    connection,
    url="https://example.com",
    width=1920,
    height=1080,
    browser_context_id=None  # Default context
)
```

### Popup Windows
```python
# Create a popup window
popup_target = await create_target(
    connection,
    url="https://popup.example.com",
    width=800,
    height=600,
    new_window=True
)
```

### Incognito Contexts
```python
# Create incognito browser context
incognito_context = await create_browser_context(connection)

# Create tab in incognito context
incognito_tab = await create_target(
    connection,
    url="https://private.example.com",
    browser_context_id=incognito_context.browser_context_id
)
```

## Advanced Features

### Target Events
Target commands work with various target events:
- `Target.targetCreated` - New target created
- `Target.targetDestroyed` - Target closed
- `Target.targetInfoChanged` - Target information updated
- `Target.targetCrashed` - Target crashed

### Multi-Target Coordination
```python
# Manage multiple tabs
targets = await get_targets(connection)
page_targets = [t for t in targets if t.type == "page"]

for target in page_targets:
    # Perform operations on each tab
    await activate_target(connection, target_id=target.target_id)
    # ... do work in this tab
```

### Target Isolation
```python
# Create isolated browser context for testing
test_context = await create_browser_context(connection)

# All targets in this context are isolated
test_tab1 = await create_target(
    connection, 
    url="https://test1.com",
    browser_context_id=test_context.browser_context_id
)

test_tab2 = await create_target(
    connection,
    url="https://test2.com", 
    browser_context_id=test_context.browser_context_id
)
```

!!! note "Browser Integration"
    Target commands are primarily used internally by the `Chrome` and `Edge` browser classes. The high-level browser APIs provide more convenient methods for tab management. 