# Browser-Context HTTP Requests

Make HTTP requests that automatically inherit your browser's session state, cookies, and authentication. Perfect for hybrid automation combining UI navigation with API efficiency.

!!! tip "Game Changer for Hybrid Automation"
    Ever wished you could make HTTP requests that automatically get all your browser's cookies and authentication? Now you can! The `tab.request` property gives you a beautiful `requests`-like interface that executes HTTP calls **directly in the browser's JavaScript context**.

## Why Use Browser-Context Requests?

Traditional automation often requires you to extract cookies and headers manually to make API calls. Browser-context requests eliminate this hassle:

| Traditional Approach | Browser-Context Requests |
|---------------------|-------------------------|
| Extract cookies manually | Cookies inherited automatically |
| Manage session tokens | Session state preserved |
| Handle CORS separately | CORS policies respected |
| Juggle two HTTP clients | One unified interface |
| Sync authentication state | Always authenticated |

**Perfect for:**

- Scraping authenticated APIs after login via UI
- Hybrid workflows mixing browser interaction and API calls
- Testing authenticated endpoints without token management
- Bypassing complex authentication flows
- Working with single-page applications (SPAs)

## Quick Start

The simplest example: +login via UI, then make authenticated API calls:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def hybrid_automation():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 1. Login normally through the UI
        await tab.go_to('https://example.com/login')
        await (await tab.find(id='username')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password123')
        await (await tab.find(id='login-btn')).click()
        
        # Wait for redirect after login
        await asyncio.sleep(2)
        
        # 2. Now make API calls with the authenticated session!
        response = await tab.request.get('https://example.com/api/user/profile')
        user_data = response.json()
        
        print(f"Logged in as: {user_data['name']}")
        print(f"Email: {user_data['email']}")

asyncio.run(hybrid_automation())
```

!!! success "No Cookie Management Required"
    Notice how we didn't extract or pass any cookies? The request automatically inherited the browser's authenticated session!

## Common Use Cases

### 1. Scraping Authenticated APIs

Use the UI to login, then hammer APIs for data extraction:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scrape_user_data():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Login via UI (handles complex auth flows)
        await tab.go_to('https://app.example.com/login')
        await (await tab.find(id='email')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password')
        await (await tab.find(type='submit')).click()
        await asyncio.sleep(2)
        
        # Now extract data via API (much faster than scraping UI)
        all_users = []
        for page in range(1, 6):
            response = await tab.request.get(
                f'https://app.example.com/api/users',
                params={'page': str(page), 'limit': '100'}
            )
            users = response.json()['users']
            all_users.extend(users)
            print(f"Page {page}: fetched {len(users)} users")
        
        print(f"Total users scraped: {len(all_users)}")

asyncio.run(scrape_user_data())
```

### 2. Testing Protected Endpoints

Test API endpoints without managing authentication tokens:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_api_endpoints():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Authenticate once
        await tab.go_to('https://api.example.com/login')
        # ... perform login ...
        await asyncio.sleep(2)
        
        # Test multiple endpoints
        endpoints = [
            '/api/users/me',
            '/api/settings',
            '/api/notifications',
            '/api/dashboard/stats'
        ]
        
        for endpoint in endpoints:
            response = await tab.request.get(f'https://api.example.com{endpoint}')
            
            if response.ok:
                print(f"Success {endpoint}: {response.status_code}")
            else:
                print(f"Failed {endpoint}: {response.status_code}")
                print(f"   Error: {response.text[:100]}")

asyncio.run(test_api_endpoints())
```

### 3. Submitting Forms via API

Fill forms faster by posting directly to the API:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def bulk_form_submission():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Login first
        await tab.go_to('https://crm.example.com/login')
        # ... login logic ...
        await asyncio.sleep(2)
        
        # Submit multiple entries via API (much faster than filling forms)
        contacts = [
            {'name': 'John Doe', 'email': 'john@example.com', 'company': 'Acme Inc'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'company': 'Tech Corp'},
            {'name': 'Bob Wilson', 'email': 'bob@example.com', 'company': 'StartupXYZ'},
        ]
        
        for contact in contacts:
            response = await tab.request.post(
                'https://crm.example.com/api/contacts',
                json=contact
            )
            
            if response.ok:
                print(f"Added: {contact['name']}")
            else:
                print(f"Failed: {contact['name']} - {response.status_code}")

asyncio.run(bulk_form_submission())
```

### 4. Downloading Files with Session

Download files that require authentication:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def download_authenticated_file():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Authenticate
        await tab.go_to('https://portal.example.com/login')
        # ... login logic ...
        await asyncio.sleep(2)
        
        # Download file that requires authentication
        response = await tab.request.get(
            'https://portal.example.com/api/reports/monthly.pdf'
        )
        
        if response.ok:
            # Save the file
            output_path = Path('/tmp/monthly_report.pdf')
            output_path.write_bytes(response.content)
            print(f"Downloaded: {output_path} ({len(response.content)} bytes)")
        else:
            print(f"Download failed: {response.status_code}")

asyncio.run(download_authenticated_file())
```

### 5. Working with Custom Headers

Add custom headers to your requests:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def custom_headers_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Login first
        await tab.go_to('https://api.example.com/login')
        # ... login logic ...
        
        # Make request with custom headers
        headers: list[HeaderEntry] = [
            {'name': 'X-API-Version', 'value': '2.0'},
            {'name': 'X-Request-ID', 'value': 'unique-id-123'},
            {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/data',
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json()}")

asyncio.run(custom_headers_example())
```

### 6. Handling Different Response Types

Access response data in multiple formats:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def response_formats():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://api.example.com')
        
        # JSON response
        json_response = await tab.request.get('/api/users/1')
        user = json_response.json()
        print(f"JSON: {user}")
        
        # Text response
        text_response = await tab.request.get('/api/status')
        status_text = text_response.text
        print(f"Text: {status_text}")
        
        # Binary response (e.g., image)
        image_response = await tab.request.get('/api/avatar/1')
        image_bytes = image_response.content
        print(f"Binary: {len(image_bytes)} bytes")
        
        # Check response status
        if json_response.ok:
            print("Request successful!")
        
        # Access response URL (useful after redirects)
        print(f"Final URL: {json_response.url}")

asyncio.run(response_formats())
```

## HTTP Methods

All standard HTTP methods are supported:

### GET - Retrieve Data

```python
# Simple GET
response = await tab.request.get('https://api.example.com/users')

# GET with query parameters
response = await tab.request.get(
    'https://api.example.com/search',
    params={'q': 'python', 'limit': '10'}
)
```

### POST - Create Resources

```python
# POST with JSON data
response = await tab.request.post(
    'https://api.example.com/users',
    json={'name': 'John Doe', 'email': 'john@example.com'}
)

# POST with form data
response = await tab.request.post(
    'https://api.example.com/login',
    data={'username': 'john', 'password': 'secret'}
)
```

### PUT - Update Resources

```python
# Update entire resource
response = await tab.request.put(
    'https://api.example.com/users/123',
    json={'name': 'Jane Doe', 'email': 'jane@example.com', 'role': 'admin'}
)
```

### PATCH - Partial Updates

```python
# Update specific fields
response = await tab.request.patch(
    'https://api.example.com/users/123',
    json={'email': 'newemail@example.com'}
)
```

### DELETE - Remove Resources

```python
# Delete a resource
response = await tab.request.delete('https://api.example.com/users/123')
```

### HEAD - Get Headers Only

```python
# Check if resource exists without downloading it
response = await tab.request.head('https://example.com/large-file.zip')
print(f"Content-Length: {response.headers}")
```

### OPTIONS - Check Capabilities

```python
# Check allowed methods
response = await tab.request.options('https://api.example.com/users')
print(f"Allowed methods: {response.headers}")
```

!!! info "How Does This Work?"
    Browser-context requests execute HTTP calls directly in the browser's JavaScript context using the Fetch API, while monitoring CDP network events to capture comprehensive metadata (headers, cookies, timing).
    
    For a detailed explanation of the internal architecture, event monitoring, and implementation details, see [Browser Requests Architecture](../../deep-dive/browser-requests-architecture.md).

## Response Object

The `Response` object provides a familiar interface similar to `requests.Response`:

```python
response = await tab.request.get('https://api.example.com/users')

# Status code
print(response.status_code)  # 200, 404, 500, etc.

# Check if successful (2xx or 3xx)
if response.ok:
    print("Success!")

# Response body
text_data = response.text      # As string
byte_data = response.content   # As bytes
json_data = response.json()    # Parsed JSON

# Headers
for header in response.headers:
    print(f"{header['name']}: {header['value']}")

# Request headers (what was actually sent)
for header in response.request_headers:
    print(f"{header['name']}: {header['value']}")

# Cookies set by the response
for cookie in response.cookies:
    print(f"{cookie['name']} = {cookie['value']}")

# Final URL (after redirects)
print(response.url)

# Raise exception for error status codes
response.raise_for_status()  # Raises HTTPError if 4xx or 5xx
```

!!! note "Redirects and URL Tracking"
    The `response.url` property contains only the **final URL** after all redirects. If you need to track the complete redirect chain (intermediate URLs, status codes, timing), use [Network Monitoring](monitoring.md) to observe all requests in detail.

## Headers and Cookies

### Working with Headers

Headers are represented as `HeaderEntry` objects:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def header_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Using HeaderEntry type for IDE autocomplete and type checking
        headers: list[HeaderEntry] = [
            {'name': 'Authorization', 'value': 'Bearer token-123'},
            {'name': 'X-Custom-Header', 'value': 'custom-value'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/protected',
            headers=headers
        )
        
        # Inspect response headers (also HeaderEntry typed dicts)
        for header in response.headers:
            if header['name'] == 'Content-Type':
                print(f"Content-Type: {header['value']}")

asyncio.run(header_example())
```

!!! tip "Type Hints for Headers"
    `HeaderEntry` is a `TypedDict` from `pydoll.protocol.fetch.types`. Using it as a type hint gives you:
    
    - **Autocomplete**: IDE suggests `name` and `value` keys
    - **Type safety**: Catch typos and missing keys before running
    - **Documentation**: Clear structure for headers
    
    While you can pass plain dictionaries, using the type hint improves code quality and IDE support.

!!! tip "Custom Headers Behavior"
    Custom headers are sent **alongside** the browser's automatic headers (like `User-Agent`, `Accept`, `Referer`, etc.). 
    
    If you try to set a standard browser header (e.g., `User-Agent`), the behavior depends on the specific header; some may be overridden, others ignored, and some may cause conflicts. For most use cases, stick to custom headers (e.g., `X-API-Key`, `Authorization`) to avoid unexpected behavior.

### Understanding Cookies

Cookies are automatically managed by the browser:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def cookie_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # First request sets cookies
        login_response = await tab.request.post(
            'https://api.example.com/login',
            json={'username': 'user', 'password': 'pass'}
        )
        
        # Check cookies set by server
        print("Cookies set by server:")
        for cookie in login_response.cookies:
            print(f"  {cookie['name']} = {cookie['value']}")
        
        # Subsequent requests automatically include cookies
        profile_response = await tab.request.get(
            'https://api.example.com/profile'
        )
        # No need to pass cookies - browser handles it!
        
        print(f"Profile data: {profile_response.json()}")

asyncio.run(cookie_example())
```

## Comparison with Traditional Requests

| Feature | `requests` Library | Browser-Context Requests |
|---------|-------------------|-------------------------|
| **Session Management** | Manual cookie handling | Automatic via browser |
| **Authentication** | Extract and pass tokens | Inherited from browser |
| **CORS** | Not applicable | Browser enforces policies |
| **JavaScript** | Cannot execute | Full access to browser context |
| **Cookie Jar** | Separate instance | Browser's native cookie store |
| **Headers** | Manually set | Browser auto-adds standard headers |
| **Use Case** | Server-side scripts | Browser automation |
| **Setup** | External library | Built into Pydoll |

## See Also

- **[Browser Requests Architecture](../../deep-dive/browser-requests-architecture.md)** - Internal implementation and architecture
- **[Network Monitoring](monitoring.md)** - Observe all network traffic
- **[Request Interception](interception.md)** - Modify requests before they're sent
- **[Event System](../advanced/event-system.md)** - React to browser events
- **[Deep Dive: Network Capabilities](../../deep-dive/network-capabilities.md)** - Technical details

Browser-context requests are a game-changer for hybrid automation. Combine the power of UI automation with the speed of direct API calls, all while maintaining perfect session continuity!
