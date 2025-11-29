# Browser Managers

The managers module provides specialized classes for managing different aspects of browser lifecycle and configuration.

## Overview

Browser managers handle specific responsibilities in browser automation:

::: pydoll.browser.managers
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Manager Classes

### Browser Process Manager
Manages the browser process lifecycle, including starting, stopping, and monitoring browser processes.

::: pydoll.browser.managers.browser_process_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Browser Options Manager
Handles browser configuration options and command-line arguments.

::: pydoll.browser.managers.browser_options_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Proxy Manager
Manages proxy configuration and authentication for browser instances.

::: pydoll.browser.managers.proxy_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Temporary Directory Manager
Handles creation and cleanup of temporary directories used by browser instances.

::: pydoll.browser.managers.temp_dir_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Usage

Managers are typically used internally by browser classes like `Chrome` and `Edge`. They provide modular functionality that can be composed together:

```python
from pydoll.browser.managers.proxy_manager import ProxyManager
from pydoll.browser.managers.temp_dir_manager import TempDirManager

# Managers are used internally by browser classes
# Direct usage is for advanced scenarios only
proxy_manager = ProxyManager()
temp_manager = TempDirManager()
```

!!! note "Internal Usage"
    These managers are primarily used internally by the browser classes. Direct usage is recommended only for advanced scenarios or when extending the library. 