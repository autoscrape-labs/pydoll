# Browser Requests

The requests module provides HTTP request capabilities within the browser context, enabling seamless API calls that inherit the browser's session state, cookies, and authentication.

## Overview

The browser requests module offers a `requests`-like interface for making HTTP calls directly within the browser's JavaScript context. This approach provides several advantages over traditional HTTP libraries:

- **Session inheritance**: Automatic cookie, authentication, and CORS handling
- **Browser context**: Requests execute in the same security context as the page
- **No session juggling**: Eliminate the need to transfer cookies and tokens between automation and API calls
- **SPA compatibility**: Perfect for Single Page Applications with complex authentication flows

## Request Class

The main interface for making HTTP requests within the browser context.

::: pydoll.browser.requests.request.Request
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## Response Class

Represents the response from HTTP requests, providing a familiar interface similar to the `requests` library.

::: pydoll.browser.requests.response.Response
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## Usage Examples

### Basic HTTP Methods

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://api.example.com")
    
    # GET request
    response = await tab.request.get("/users/123")
    user_data = await response.json()
    
    # POST request
    response = await tab.request.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # PUT request with headers
    response = await tab.request.put("/users/123", 
        json={"name": "Jane Doe"},
        headers={"Authorization": "Bearer token123"}
    )
```

### Response Handling

```python
# Check response status
if response.ok:
    print(f"Success: {response.status_code}")
else:
    print(f"Error: {response.status_code}")
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx

# Access response data
text_data = response.text
json_data = await response.json()
raw_bytes = response.content

# Inspect headers and cookies
print("Response headers:", response.headers)
print("Request headers:", response.request_headers)
for cookie in response.cookies:
    print(f"Cookie: {cookie.name}={cookie.value}")
```

### Advanced Features

```python
# Request with custom headers and parameters
response = await tab.request.get("/search", 
    params={"q": "python", "limit": 10},
    headers={
        "User-Agent": "Custom Bot 1.0",
        "Accept": "application/json"
    }
)

# File upload simulation
response = await tab.request.post("/upload",
    data={"description": "Test file"},
    files={"file": ("test.txt", "file content", "text/plain")}
)

# Form data submission
response = await tab.request.post("/login",
    data={"username": "user", "password": "pass"}
)
```

## Integration with Tab

The request functionality is accessed through the `tab.request` property, which provides a singleton `Request` instance for each tab:

```python
# Each tab has its own request instance
tab1 = await browser.get_tab(0)
tab2 = await browser.new_tab()

# These are separate Request instances
request1 = tab1.request  # Request bound to tab1
request2 = tab2.request  # Request bound to tab2

# Requests inherit the tab's context
await tab1.go_to("https://site1.com")
await tab2.go_to("https://site2.com")

# These requests will have different cookie/session contexts
response1 = await tab1.request.get("/api/data")  # Uses site1.com cookies
response2 = await tab2.request.get("/api/data")  # Uses site2.com cookies
```

!!! tip "Hybrid Automation"
    This module is particularly powerful for hybrid automation scenarios where you need to combine UI interactions with API calls. For example, log in through the UI, then use the authenticated session for API calls without manually handling cookies or tokens.