# DOM Commands

DOM commands provide comprehensive functionality for interacting with the Document Object Model of web pages.

## Overview

The DOM commands module is one of the most important modules in Pydoll, providing all the functionality needed to find, interact with, and manipulate HTML elements on web pages.

::: pydoll.commands.dom_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

DOM commands are used extensively by the `WebElement` class and element finding methods:

```python
from pydoll.commands.dom_commands import query_selector, get_attributes
from pydoll.connection.connection_handler import ConnectionHandler

# Find element and get its attributes
connection = ConnectionHandler()
node_id = await query_selector(connection, selector="#username")
attributes = await get_attributes(connection, node_id=node_id)
```

## Key Functionality

The DOM commands module provides functions for:

### Element Finding
- `query_selector()` - Find single element by CSS selector
- `query_selector_all()` - Find multiple elements by CSS selector
- `get_document()` - Get the document root node

### Element Interaction
- `click_element()` - Click on elements
- `focus_element()` - Focus elements
- `set_attribute_value()` - Set element attributes
- `get_attributes()` - Get element attributes

### Element Information
- `get_box_model()` - Get element positioning and dimensions
- `describe_node()` - Get detailed element information
- `get_outer_html()` - Get element HTML content

### DOM Manipulation
- `remove_node()` - Remove elements from DOM
- `set_node_value()` - Set element values
- `request_child_nodes()` - Get child elements

!!! tip "High-Level APIs"
    While these commands provide powerful low-level access, most users should use the higher-level `WebElement` class methods like `click()`, `type_text()`, and `get_attribute()` which use these commands internally. 