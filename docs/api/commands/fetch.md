# Fetch Commands

Fetch commands provide advanced network request handling and interception capabilities using the Fetch API domain.

## Overview

The fetch commands module enables sophisticated network request management, including request modification, response interception, and authentication handling.

::: pydoll.commands.fetch_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

Fetch commands are used for advanced network interception and request handling:

```python
from pydoll.commands.fetch_commands import enable, request_paused, continue_request
from pydoll.connection.connection_handler import ConnectionHandler

# Enable fetch domain
connection = ConnectionHandler()
await enable(connection, patterns=[{
    "urlPattern": "*",
    "requestStage": "Request"
}])

# Handle paused requests
async def handle_paused_request(request_id, request):
    # Modify request or continue as-is
    await continue_request(connection, request_id=request_id)
```

## Key Functionality

The fetch commands module provides functions for:

### Request Interception
- `enable()` - Enable fetch domain with patterns
- `disable()` - Disable fetch domain
- `continue_request()` - Continue intercepted requests
- `fail_request()` - Fail requests with specific errors

### Request Modification
- Modify request headers
- Change request URLs
- Alter request methods (GET, POST, etc.)
- Modify request bodies

### Response Handling
- `fulfill_request()` - Provide custom responses
- `get_response_body()` - Get response content
- Response header modification
- Response status code control

### Authentication
- `continue_with_auth()` - Handle authentication challenges
- Basic authentication support
- Custom authentication flows

## Advanced Features

### Pattern-Based Interception
```python
# Intercept specific URL patterns
patterns = [
    {"urlPattern": "*/api/*", "requestStage": "Request"},
    {"urlPattern": "*.js", "requestStage": "Response"},
    {"urlPattern": "https://example.com/*", "requestStage": "Request"}
]

await enable(connection, patterns=patterns)
```

### Request Modification
```python
# Modify intercepted requests
async def modify_request(request_id, request):
    # Add authentication header
    headers = request.headers.copy()
    headers["Authorization"] = "Bearer token123"
    
    # Continue with modified headers
    await continue_request(
        connection,
        request_id=request_id,
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
    response_headers=[
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Access-Control-Allow-Origin", "value": "*"}
    ],
    body='{"status": "success", "data": {"mocked": true}}'
)
```

### Authentication Handling
```python
# Handle authentication challenges
await continue_with_auth(
    connection,
    request_id=request_id,
    auth_challenge_response={
        "response": "ProvideCredentials",
        "username": "user",
        "password": "pass"
    }
)
```

## Request Stages

Fetch commands can intercept requests at different stages:

| Stage | Description | Use Cases |
|-------|-------------|-----------|
| Request | Before request is sent | Modify headers, URL, method |
| Response | After response received | Mock responses, modify content |

## Error Handling

```python
# Fail requests with specific errors
await fail_request(
    connection,
    request_id=request_id,
    error_reason="ConnectionRefused"  # or "AccessDenied", "TimedOut", etc.
)
```

## Integration with Network Commands

Fetch commands work alongside network commands but provide more granular control:

- **Network Commands**: Broader network monitoring and control
- **Fetch Commands**: Specific request/response interception and modification

!!! tip "Performance Considerations"
    Fetch interception can impact page loading performance. Use specific URL patterns and disable when not needed to minimize overhead. 