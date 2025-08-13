# Runtime Commands

Runtime commands provide JavaScript execution capabilities and runtime environment management.

## Overview

The runtime commands module enables JavaScript code execution, object inspection, and runtime environment control within browser contexts.

::: pydoll.commands.runtime_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Runtime commands are used for JavaScript execution and runtime management:

```python
from pydoll.commands.runtime_commands import evaluate, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Enable runtime events
connection = ConnectionHandler()
await enable(connection)

# Execute JavaScript
result = await evaluate(
    connection, 
    expression="document.title",
    return_by_value=True
)
print(result.value)  # Page title
```

## Key Functionality

The runtime commands module provides functions for:

### JavaScript Execution
- `evaluate()` - Execute JavaScript expressions
- `call_function_on()` - Call functions on objects
- `compile_script()` - Compile JavaScript for reuse
- `run_script()` - Run compiled scripts

### Object Management
- `get_properties()` - Get object properties
- `release_object()` - Release object references
- `release_object_group()` - Release object groups

### Runtime Control
- `enable()` / `disable()` - Enable/disable runtime events
- `discard_console_entries()` - Clear console entries
- `set_custom_object_formatter_enabled()` - Enable custom formatters

### Exception Handling
- `set_async_call_stack_depth()` - Set call stack depth
- Exception capture and reporting
- Error object inspection

## Advanced Usage

### Complex JavaScript Execution
```python
# Execute complex JavaScript with error handling
script = """
try {
    const elements = document.querySelectorAll('.item');
    return Array.from(elements).map(el => ({
        text: el.textContent,
        href: el.href
    }));
} catch (error) {
    return { error: error.message };
}
"""

result = await evaluate(
    connection,
    expression=script,
    return_by_value=True,
    await_promise=True
)
```

### Object Inspection
```python
# Get detailed object properties
properties = await get_properties(
    connection,
    object_id=object_id,
    own_properties=True,
    accessor_properties_only=False
)

for prop in properties:
    print(f"{prop.name}: {prop.value}")
```

### Console Integration
Runtime commands integrate with browser console:
- Console messages and errors
- Console API method calls
- Custom console formatters

!!! note "Performance Considerations"
    JavaScript execution through runtime commands can be slower than native browser execution. Use judiciously for complex operations. 