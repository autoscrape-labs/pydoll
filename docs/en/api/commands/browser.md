# Browser Commands

Browser commands provide low-level control over browser instances and their configuration.

## Overview

The browser commands module handles browser-level operations such as version information, target management, and browser-wide settings.

::: pydoll.commands.browser_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Browser commands are typically used internally by browser classes to manage browser instances:

```python
from pydoll.commands.browser_commands import get_version
from pydoll.connection.connection_handler import ConnectionHandler

# Get browser version information
connection = ConnectionHandler()
version_info = await get_version(connection)
```

## Available Commands

The browser commands module provides functions for:

- Getting browser version and user agent information
- Managing browser targets (tabs, windows)
- Controlling browser-wide settings and permissions
- Handling browser lifecycle events

!!! note "Internal Usage"
    These commands are primarily used internally by the `Chrome` and `Edge` browser classes. Direct usage is recommended only for advanced scenarios. 