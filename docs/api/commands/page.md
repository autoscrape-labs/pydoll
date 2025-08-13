# Page Commands

Page commands handle page navigation, lifecycle events, and page-level operations.

## Overview

The page commands module provides functionality for navigating between pages, managing page lifecycle, handling JavaScript execution, and controlling page behavior.

::: pydoll.commands.page_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Page commands are used extensively by the `Tab` class for navigation and page management:

```python
from pydoll.commands.page_commands import navigate, reload, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Navigate to a URL
connection = ConnectionHandler()
await enable(connection)  # Enable page events
await navigate(connection, url="https://example.com")

# Reload the page
await reload(connection)
```

## Key Functionality

The page commands module provides functions for:

### Navigation
- `navigate()` - Navigate to URLs
- `reload()` - Reload current page
- `go_back()` - Navigate back in history
- `go_forward()` - Navigate forward in history
- `stop_loading()` - Stop page loading

### Page Lifecycle
- `enable()` / `disable()` - Enable/disable page events
- `get_frame_tree()` - Get page frame structure
- `get_navigation_history()` - Get navigation history

### Content Management
- `get_resource_content()` - Get page resource content
- `search_in_resource()` - Search within page resources
- `set_document_content()` - Set page HTML content

### Screenshots & PDF
- `capture_screenshot()` - Take page screenshots
- `print_to_pdf()` - Generate PDF from page
- `capture_snapshot()` - Capture page snapshots

### JavaScript Execution
- `add_script_to_evaluate_on_new_document()` - Add startup scripts
- `remove_script_to_evaluate_on_new_document()` - Remove startup scripts

### Page Settings
- `set_lifecycle_events_enabled()` - Control lifecycle events
- `set_ad_blocking_enabled()` - Enable/disable ad blocking
- `set_bypass_csp()` - Bypass Content Security Policy

## Advanced Features

### Frame Management
```python
# Get all frames in the page
frame_tree = await get_frame_tree(connection)
for frame in frame_tree.child_frames:
    print(f"Frame: {frame.frame.url}")
```

### Resource Interception
```python
# Get resource content
content = await get_resource_content(
    connection, 
    frame_id=frame_id, 
    url="https://example.com/script.js"
)
```

### Page Events
The page commands work with various page events:
- `Page.loadEventFired` - Page load completed
- `Page.domContentEventFired` - DOM content loaded
- `Page.frameNavigated` - Frame navigation
- `Page.frameStartedLoading` - Frame loading started

!!! tip "Tab Class Integration"
    Most page operations are available through the `Tab` class methods like `tab.go_to()`, `tab.reload()`, and `tab.screenshot()` which provide a more convenient API. 