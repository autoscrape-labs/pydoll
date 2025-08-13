# API Reference

Welcome to the Pydoll API Reference! This section provides comprehensive documentation for all classes, methods, and functions available in the Pydoll library.

## Overview

Pydoll is organized into several key modules, each serving a specific purpose in browser automation:

### Browser Module
The browser module contains classes for managing browser instances and their lifecycle.

- **[Chrome](browser/chrome.md)** - Chrome browser automation
- **[Edge](browser/edge.md)** - Microsoft Edge browser automation  
- **[Options](browser/options.md)** - Browser configuration options
- **[Tab](browser/tab.md)** - Tab management and interaction
- **[Requests](browser/requests.md)** - HTTP requests within browser context
- **[Managers](browser/managers.md)** - Browser lifecycle managers

### Elements Module
The elements module provides classes for interacting with web page elements.

- **[WebElement](elements/web_element.md)** - Individual element interaction
- **[Mixins](elements/mixins.md)** - Reusable element functionality

### Connection Module
The connection module handles communication with the browser through the Chrome DevTools Protocol.

- **[Connection Handler](connection/connection.md)** - WebSocket connection management
- **[Managers](connection/managers.md)** - Connection lifecycle managers

### Commands Module
The commands module provides low-level Chrome DevTools Protocol command implementations.

- **[Commands Overview](commands/index.md)** - CDP command implementations by domain

### Protocol Module
The protocol module implements the Chrome DevTools Protocol commands and events.

- **[Base Types](protocol/base.md)** - Base types for Chrome DevTools Protocol
- **[Browser](protocol/browser.md)** - Browser domain commands and events
- **[DOM](protocol/dom.md)** - DOM domain commands and events
- **[Fetch](protocol/fetch.md)** - Fetch domain commands and events
- **[Input](protocol/input.md)** - Input domain commands and events
- **[Network](protocol/network.md)** - Network domain commands and events
- **[Page](protocol/page.md)** - Page domain commands and events
- **[Runtime](protocol/runtime.md)** - Runtime domain commands and events
- **[Storage](protocol/storage.md)** - Storage domain commands and events
- **[Target](protocol/target.md)** - Target domain commands and events

### Core Module
The core module contains fundamental utilities, constants, and exceptions.

- **[Constants](core/constants.md)** - Library constants and enums
- **[Exceptions](core/exceptions.md)** - Custom exception classes
- **[Utils](core/utils.md)** - Utility functions

## Quick Navigation

### Most Common Classes

| Class | Purpose | Module |
|-------|---------|--------|
| `Chrome` | Chrome browser automation | `pydoll.browser.chromium` |
| `Edge` | Edge browser automation | `pydoll.browser.chromium` |
| `Tab` | Tab interaction and control | `pydoll.browser.tab` |
| `WebElement` | Element interaction | `pydoll.elements.web_element` |
| `ChromiumOptions` | Browser configuration | `pydoll.browser.options` |

### Key Enums and Constants

| Name | Purpose | Module |
|------|---------|--------|
| `By` | Element selector strategies | `pydoll.constants` |
| `Key` | Keyboard key constants | `pydoll.constants` |
| `PermissionType` | Browser permission types | `pydoll.constants` |

### Common Exceptions

| Exception | When Raised | Module |
|-----------|-------------|--------|
| `ElementNotFound` | Element not found in DOM | `pydoll.exceptions` |
| `WaitElementTimeout` | Element wait timeout | `pydoll.exceptions` |
| `BrowserNotStarted` | Browser not started | `pydoll.exceptions` |

## Usage Patterns

### Basic Browser Automation

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://example.com")
    element = await tab.find(id="my-element")
    await element.click()
```

### Element Finding

```python
# Using the modern find() method
element = await tab.find(id="username")
element = await tab.find(tag_name="button", class_name="submit")

# Using CSS selectors or XPath
element = await tab.query("#username")
element = await tab.query("//button[@class='submit']")
```

### Event Handling

```python
await tab.enable_page_events()
await tab.on('Page.loadEventFired', handle_page_load)
```

## Type Hints

Pydoll is fully typed and provides comprehensive type hints for better IDE support and code safety. All public APIs include proper type annotations.

```python
from typing import Optional, List
from pydoll.elements.web_element import WebElement

# Methods return properly typed objects
element: Optional[WebElement] = await tab.find(id="test", raise_exc=False)
elements: List[WebElement] = await tab.find(class_name="item", find_all=True)
```

## Async/Await Support

All Pydoll operations are asynchronous and must be used with `async`/`await`:

```python
import asyncio

async def main():
    # All Pydoll operations are async
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to("https://example.com")
        
asyncio.run(main())
```

Browse the sections below to explore the complete API documentation for each module. 