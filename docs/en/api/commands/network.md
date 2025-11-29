# Network Commands

Network commands provide comprehensive control over network requests, responses, and browser networking behavior.

## Overview

The network commands module enables request interception, response modification, cookie management, and network monitoring capabilities.

::: pydoll.commands.network_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Network commands are used for advanced scenarios like request interception and network monitoring:

```python
from pydoll.commands.network_commands import enable, set_request_interception
from pydoll.connection.connection_handler import ConnectionHandler

# Enable network monitoring
connection = ConnectionHandler()
await enable(connection)

# Enable request interception
await set_request_interception(connection, patterns=[{"urlPattern": "*"}])
```

## Key Functionality

The network commands module provides functions for:

### Request Management
- `enable()` / `disable()` - Enable/disable network monitoring
- `set_request_interception()` - Intercept and modify requests
- `continue_intercepted_request()` - Continue or modify intercepted requests
- `get_request_post_data()` - Get request body data

### Response Handling
- `get_response_body()` - Get response content
- `fulfill_request()` - Provide custom responses
- `fail_request()` - Simulate network failures

### Cookie Management
- `get_cookies()` - Get browser cookies
- `set_cookies()` - Set browser cookies
- `delete_cookies()` - Delete specific cookies
- `clear_browser_cookies()` - Clear all cookies

### Cache Control
- `clear_browser_cache()` - Clear browser cache
- `set_cache_disabled()` - Disable browser cache
- `get_response_body_for_interception()` - Get cached responses

### Security & Headers
- `set_user_agent_override()` - Override user agent
- `set_extra_http_headers()` - Add custom headers
- `emulate_network_conditions()` - Simulate network conditions

## Advanced Use Cases

### Request Interception
```python
# Intercept and modify requests
await set_request_interception(connection, patterns=[
    {"urlPattern": "*/api/*", "requestStage": "Request"}
])

# Handle intercepted request
async def handle_request(request):
    if "api/login" in request.url:
        # Modify request headers
        headers = request.headers.copy()
        headers["Authorization"] = "Bearer token"
        await continue_intercepted_request(
            connection, 
            request_id=request.request_id,
            headers=headers
        )
```

### Response Mocking
```python
# Mock API responses
await fulfill_request(
    connection,
    request_id=request_id,
    response_code=200,
    response_headers={"Content-Type": "application/json"},
    body='{"status": "success"}'
)
```

!!! warning "Performance Impact"
    Network interception can impact page loading performance. Use selectively and disable when not needed. 