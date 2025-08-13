# Commands Overview

The Commands module provides high-level interfaces for interacting with Chrome DevTools Protocol (CDP) domains. Each command module corresponds to a specific CDP domain and provides methods to execute various browser operations.

## Available Command Modules

### Browser Commands
- **Module**: `browser_commands.py`
- **Purpose**: Browser-level operations and window management
- **Documentation**: [Browser Commands](browser.md)

### DOM Commands
- **Module**: `dom_commands.py`
- **Purpose**: DOM tree manipulation and element operations
- **Documentation**: [DOM Commands](dom.md)

### Input Commands
- **Module**: `input_commands.py`
- **Purpose**: Input event simulation (keyboard, mouse, touch)
- **Documentation**: [Input Commands](input.md)

### Network Commands
- **Module**: `network_commands.py`
- **Purpose**: Network monitoring and request interception
- **Documentation**: [Network Commands](network.md)

### Page Commands
- **Module**: `page_commands.py`
- **Purpose**: Page lifecycle management and navigation
- **Documentation**: [Page Commands](page.md)

### Runtime Commands
- **Module**: `runtime_commands.py`
- **Purpose**: JavaScript execution and runtime management
- **Documentation**: [Runtime Commands](runtime.md)

### Storage Commands
- **Module**: `storage_commands.py`
- **Purpose**: Browser storage access (cookies, local storage, etc.)
- **Documentation**: [Storage Commands](storage.md)

### Target Commands
- **Module**: `target_commands.py`
- **Purpose**: Target management and tab operations
- **Documentation**: [Target Commands](target.md)

### Fetch Commands
- **Module**: `fetch_commands.py`
- **Purpose**: Network request interception and modification
- **Documentation**: [Fetch Commands](fetch.md)

## Usage Pattern

Commands are typically accessed through the browser or tab instances:

```python
from pydoll.browser.chromium import Chrome

# Initialize browser
browser = Chrome()
await browser.start()

# Get active tab
tab = await browser.get_active_tab()

# Use commands through the tab
await tab.navigate("https://example.com")
element = await tab.find(id="button")
await element.click()
```

## Command Structure

Each command module follows a consistent pattern:
- **Static methods**: For direct command execution
- **Type hints**: Full type safety with protocol types
- **Error handling**: Proper exception handling for CDP errors
- **Documentation**: Comprehensive docstrings with examples 