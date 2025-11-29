# Cookies & Sessions

Managing cookies and sessions effectively is crucial for realistic browser automation. Websites use cookies to track authentication, preferences, and user behavior, and they expect browsers to behave accordingly.

## Why Cookies Matter for Automation

Cookies are more than just stored data: they're a fingerprint of browser activity:

- **Authentication**: Session cookies maintain login state across requests
- **Tracking Prevention**: Anti-bot systems analyze cookie patterns
- **Realistic Behavior**: A browser without cookies looks suspicious
- **Session Persistence**: Reusing cookies can save time on repeated logins

!!! warning "The Cookie Paradox"
    - **Too clean**: A browser with no cookies or history appears bot-like
    - **Too stale**: Using the same session for weeks triggers security alerts
    - **Sweet spot**: Fresh cookies with occasional rotation and realistic activity patterns

## Quick Start

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_cookie_management():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Set a cookie (using a simple dict)
        cookies = [
            {
                'name': 'session_id',
                'value': 'abc123xyz',
                'domain': 'example.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            }
        ]
        await tab.set_cookies(cookies)
        
        # Get all cookies
        all_cookies = await browser.get_cookies()
        print(f"Total cookies: {len(all_cookies)}")
        
        # Delete all cookies
        await tab.delete_all_cookies()

asyncio.run(basic_cookie_management())
```

## Understanding Cookie Types

!!! info "TypedDict: Use Regular Dicts in Practice"
    Throughout this documentation, you'll see references to `CookieParam` and `Cookie`. These are **TypedDict** types, they're just regular Python dicts with type hints for IDE autocomplete and type checking.
    
    **In practice, you use regular dicts:**
    ```python
    # This is what you actually write:
    cookie = {'name': 'session', 'value': 'abc123', 'domain': 'example.com'}
    
    # The type annotation is just for your IDE:
    from pydoll.protocol.network.types import CookieParam
    cookie: CookieParam = {'name': 'session', 'value': 'abc123'}
    ```
    
    All examples below use plain dicts for simplicity.

### Cookie Structure

The `Cookie` type (retrieved from browser) contains full cookie information:

```python
{
    "name": str,           # Cookie name
    "value": str,          # Cookie value
    "domain": str,         # Domain where cookie is valid
    "path": str,           # Path where cookie is valid
    "expires": float,      # Unix timestamp (0 = session cookie)
    "size": int,           # Size in bytes
    "httpOnly": bool,      # Accessible only via HTTP (not JavaScript)
    "secure": bool,        # Sent only over HTTPS
    "session": bool,       # True if expires when browser closes
    "sameSite": str,       # "Strict", "Lax", or "None"
    "priority": str,       # "Low", "Medium", or "High"
    "sourceScheme": str,   # "Unset", "NonSecure", or "Secure"
    "sourcePort": int,     # Port where cookie was set
}
```

### CookieParam Structure

When **setting** cookies, use a dict (only `name` and `value` are required):

```python
# Simple cookie with just required fields
cookie = {
    'name': 'user_token',
    'value': 'token_value'
}

# Full cookie with all optional fields
cookie = {
    'name': 'user_token',       # Required
    'value': 'token_value',     # Required
    'domain': 'example.com',    # Optional: defaults to current page domain
    'path': '/',                # Optional: defaults to /
    'secure': True,             # Optional: HTTPS only
    'httpOnly': True,           # Optional: no JS access
    'sameSite': 'Lax',          # Optional: 'Strict', 'Lax', or 'None'
    'expires': 1735689600,      # Optional: Unix timestamp
    'priority': 'High',         # Optional: 'Low', 'Medium', or 'High'
}
```

!!! info "Optional Fields Default Behavior"
    When you omit optional fields:
    
    - `domain`: Uses the domain of the current page
    - `path`: Defaults to `/`
    - `secure`: Defaults to `False`
    - `httpOnly`: Defaults to `False`
    - `sameSite`: Browser's default (usually `Lax`)
    - `expires`: Session cookie (deleted when browser closes)

## Cookie Management Operations

### Setting Cookies

#### Set Multiple Cookies at Once

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def set_multiple_cookies():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        cookies = [
            {
                'name': 'session_id',
                'value': 'xyz789',
                'domain': 'example.com',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Strict'
            },
            {
                'name': 'preferences',
                'value': 'dark_mode=true',
                'domain': 'example.com',
                'path': '/settings'
            },
            {
                'name': 'analytics',
                'value': 'tracking_id_12345',
                'domain': 'example.com',
                'expires': 1735689600  # Expires on specific date
            }
        ]
        
        await tab.set_cookies(cookies)
        print(f"Set {len(cookies)} cookies")

asyncio.run(set_multiple_cookies())
```

#### Set Cookies in Specific Context

```python
# Set cookies in a specific browser context
context_id = await browser.create_browser_context()
await browser.set_cookies(cookies, browser_context_id=context_id)
```

!!! tip "Tab vs Browser Methods for Setting Cookies"
    - `tab.set_cookies(cookies)`: Sets cookies in the tab's browser context (convenient shortcut)
    - `browser.set_cookies(cookies, browser_context_id=...)`: Sets cookies with explicit context control
    
    Both methods add cookies to the **entire context**, not just the current page. The cookies will be available to all tabs in that context.

### Retrieving Cookies

#### Get All Cookies (Context-Wide)

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def get_cookies_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com')
        
        # Wait for page to set cookies
        await asyncio.sleep(2)
        
        # Option 1: Get cookies via tab (shortcut for current context)
        cookies = await tab.get_cookies()
        
        # Option 2: Get cookies via browser (explicit context control)
        # cookies = await browser.get_cookies()  # Same as tab.get_cookies() for default context
        
        print(f"Found {len(cookies)} cookies:")
        for cookie in cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
            print(f"    Domain: {cookie['domain']}, Secure: {cookie['secure']}")

asyncio.run(get_cookies_example())
```

!!! tip "Tab vs Browser Methods"
    - `tab.get_cookies()`: Returns cookies from the tab's browser context (convenient shortcut)
    - `browser.get_cookies()`: Returns cookies from the default context (or specify `browser_context_id`)
    
    Both methods return **all cookies** from the context, not just cookies for the current page domain.

#### Get Cookies from Specific Context

```python
# Get cookies from specific browser context
context_id = await browser.create_browser_context()
cookies = await browser.get_cookies(browser_context_id=context_id)
```

### Deleting Cookies

#### Delete All Cookies

```python
# Delete all cookies from current tab's context
await tab.delete_all_cookies()

# Delete all cookies from specific context
await browser.delete_all_cookies(browser_context_id=context_id)
```

!!! warning "Cookies Are Deleted Immediately"
    When you delete cookies, they're removed from the browser immediately. The website may not detect this until the next request or page reload.

## Practical Use Cases

### 1. Persistent Login Sessions

Reuse authentication cookies across script runs:

```python
import asyncio
import json
from pathlib import Path
from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('cookies.json')

async def save_cookies_after_login():
    """Log in and save cookies for future use."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/login')
        
        # Perform login (simplified)
        email = await tab.find(id='email')
        password = await tab.find(id='password')
        await email.type_text('user@example.com')
        await password.type_text('secret')
        
        login_btn = await tab.find(id='login')
        await login_btn.click()
        await asyncio.sleep(3)
        
        # Save cookies
        cookies = await browser.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"Saved {len(cookies)} cookies to {COOKIE_FILE}")

async def reuse_saved_cookies():
    """Load saved cookies to skip login."""
    if not COOKIE_FILE.exists():
        print("No saved cookies found. Run save_cookies_after_login() first.")
        return
    
    # Load cookies from file
    saved_cookies = json.loads(COOKIE_FILE.read_text())
    
    # Convert to simplified format (only required fields)
    # Note: get_cookies() returns detailed Cookie objects with read-only fields
    # (size, session, sourceScheme, etc.). set_cookies() expects CookieParam
    # format with only the settable fields.
    cookies_to_set = [
        {
            'name': c['name'],
            'value': c['value'],
            'domain': c['domain'],
            'path': c.get('path', '/'),
            'secure': c.get('secure', False),
            'httpOnly': c.get('httpOnly', False)
        }
        for c in saved_cookies
    ]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Set cookies before navigating
        await tab.set_cookies(cookies_to_set)
        print(f"Loaded {len(cookies_to_set)} cookies from file")
        
        # Navigate - should be logged in already
        await tab.go_to('https://example.com/dashboard')
        await asyncio.sleep(2)
        
        # Verify login
        try:
            username = await tab.find(class_name='username')
            print(f"Logged in as: {await username.text}")
        except Exception:
            print("Login failed - cookies may have expired")

# First run: log in and save cookies
# asyncio.run(save_cookies_after_login())

# Subsequent runs: reuse cookies
asyncio.run(reuse_saved_cookies())
```

!!! note "Cookie Reformatting Required"
    `get_cookies()` returns **detailed `Cookie` objects** with read-only attributes like `size`, `session`, `sourceScheme`, and `sourcePort`. When using `set_cookies()`, you must provide **`CookieParam` format** containing only the settable fields (`name`, `value`, `domain`, `path`, `secure`, `httpOnly`, `sameSite`, `expires`, `priority`).
    
    The reformatting step in the example above is **essential**. Passing raw `Cookie` objects to `set_cookies()` may cause errors or unexpected behavior.

!!! tip "Cookie Expiration"
    Always check if saved cookies have expired. Session cookies (`session=True`) expire when the browser closes, while persistent cookies have an `expires` timestamp you can validate.

### 2. Multi-Account Testing with Isolated Cookies

Each browser context maintains separate cookies:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_multiple_accounts():
    accounts = [
        {'email': 'user1@example.com', 'cookie_value': 'session_user1'},
        {'email': 'user2@example.com', 'cookie_value': 'session_user2'},
    ]
    
    async with Chrome() as browser:
        initial_tab = await browser.start()
        
        # First account in default context
        cookies_user1 = [{
            'name': 'session',
            'value': accounts[0]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await initial_tab.set_cookies(cookies_user1)
        await initial_tab.go_to('https://example.com/dashboard')
        
        # Second account in isolated context
        context2 = await browser.create_browser_context()
        tab2 = await browser.new_tab(browser_context_id=context2)
        
        cookies_user2 = [{
            'name': 'session',
            'value': accounts[1]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await browser.set_cookies(cookies_user2, browser_context_id=context2)
        await tab2.go_to('https://example.com/dashboard')
        
        # Both users are logged in simultaneously with different sessions
        print("User 1 and User 2 logged in with isolated cookies")
        
        await asyncio.sleep(5)
        
        # Cleanup
        await tab2.close()
        await browser.delete_browser_context(context2)

asyncio.run(test_multiple_accounts())
```

### 3. Cookie Rotation for Long-Running Scripts

Refresh cookies periodically to avoid detection:

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def scrape_with_cookie_rotation():
    urls = [f'https://example.com/page{i}' for i in range(100)]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Log in initially
        await tab.go_to('https://example.com/login')
        # ... perform login ...
        await asyncio.sleep(2)
        
        last_rotation = time.time()
        rotation_interval = 600  # Rotate every 10 minutes
        
        for url in urls:
            # Check if it's time to rotate cookies
            if time.time() - last_rotation > rotation_interval:
                print("Rotating session...")
                
                # Delete old cookies
                await tab.delete_all_cookies()
                
                # Re-login or load fresh cookies
                await tab.go_to('https://example.com/login')
                # ... perform login again ...
                
                last_rotation = time.time()
            
            # Scrape page
            await tab.go_to(url)
            await asyncio.sleep(2)
            # ... extract data ...

asyncio.run(scrape_with_cookie_rotation())
```

!!! tip "Rotation Frequency"
    The ideal rotation frequency depends on your use case:
    
    - **High-security sites**: Rotate every 5-15 minutes
    - **Normal sites**: Rotate every 30-60 minutes
    - **Low-risk scraping**: Rotate every few hours


## Cookie Attributes Reference

| Attribute | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | `str` | Cookie name | *Required* |
| `value` | `str` | Cookie value | *Required* |
| `domain` | `str` | Domain where cookie is valid | Current page domain |
| `path` | `str` | Path where cookie is valid | `/` |
| `secure` | `bool` | Send only over HTTPS | `False` |
| `httpOnly` | `bool` | Not accessible via JavaScript | `False` |
| `sameSite` | `CookieSameSite` | CSRF protection: `Strict`, `Lax`, `None` | Browser default (`Lax`) |
| `expires` | `float` | Unix timestamp (0 = session cookie) | `0` (session) |
| `priority` | `CookiePriority` | Cookie priority: `Low`, `Medium`, `High` | `Medium` |

### SameSite Values

```python
# Use string values directly in your cookie dict:

'sameSite': 'Strict'  # Cookie sent only for same-site requests
'sameSite': 'Lax'     # Cookie sent for top-level navigation (default)
'sameSite': 'None'    # Cookie sent for all requests (requires secure=True)

# Or use the enum for IDE autocomplete:
from pydoll.protocol.network.types import CookieSameSite

cookie = {
    'name': 'session',
    'value': 'xyz',
    'sameSite': CookieSameSite.STRICT  # IDE will autocomplete: STRICT, LAX, NONE
}
```

### Priority Values

```python
# Use string values directly:

'priority': 'Low'     # Low priority (deleted first when space is needed)
'priority': 'Medium'  # Medium priority (default)
'priority': 'High'    # High priority (deleted last)

# Or use the enum:
from pydoll.protocol.network.types import CookiePriority

cookie = {
    'name': 'session',
    'value': 'xyz',
    'priority': CookiePriority.HIGH  # IDE will autocomplete: LOW, MEDIUM, HIGH
}
```

## Common Patterns

### Context Manager for Temporary Cookies

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def temporary_cookies(browser, tab, cookies):
    """Set cookies, execute code, then restore original cookies."""
    # Save current cookies
    original_cookies = await browser.get_cookies()
    
    try:
        # Set temporary cookies
        await tab.delete_all_cookies()
        await tab.set_cookies(cookies)
        yield tab
    finally:
        # Restore original cookies
        await tab.delete_all_cookies()
        cookies_to_restore = [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c.get('path', '/')
            }
            for c in original_cookies
        ]
        await tab.set_cookies(cookies_to_restore)

# Usage
async with temporary_cookies(browser, tab, test_cookies):
    await tab.go_to('https://example.com')
    # ... perform actions with temporary cookies ...
# Original cookies restored automatically
```

!!! tip "Using Public APIs"
    This context manager accepts both `browser` and `tab` as parameters to use public APIs. Since `tab` doesn't expose its parent `browser` as a public property, passing it explicitly is the recommended approach for accessing browser-level methods.

### Cookie Fingerprint Comparison

```python
def cookie_fingerprint(cookies):
    """Generate a simple fingerprint of cookie state."""
    return {
        'count': len(cookies),
        'domains': set(c['domain'] for c in cookies),
        'names': sorted(c['name'] for c in cookies),
        'secure_count': sum(1 for c in cookies if c.get('secure')),
        'httponly_count': sum(1 for c in cookies if c.get('httpOnly')),
    }

# Compare cookie states
before = await browser.get_cookies()
await tab.go_to('https://example.com')
after = await browser.get_cookies()

print(f"Before: {cookie_fingerprint(before)}")
print(f"After: {cookie_fingerprint(after)}")
```

## Security Considerations

!!! danger "Never Hardcode Sensitive Cookies"
    Always load authentication cookies from secure storage (environment variables, encrypted files, secrets managers).
    
    ```python
    # ❌ Bad - hardcoded in code
    cookies = [{'name': 'session', 'value': 'abc123secret'}]
    
    # ✅ Good - loaded from environment
    import os
    cookies = [{
        'name': 'session',
        'value': os.getenv('SESSION_COOKIE'),
        'domain': os.getenv('COOKIE_DOMAIN')
    }]
    ```

!!! warning "Cookie Theft Protection"
    When saving cookies to disk:
    
    - Use encrypted storage (e.g., `cryptography` library)
    - Set restrictive file permissions
    - Never commit cookie files to version control
    - Rotate cookies regularly

## Best Practices Summary

1. **Start with realistic cookies** - Don't run automation with a completely clean browser
2. **Rotate sessions periodically** - Avoid using the same cookies for extended periods
3. **Respect cookie security attributes** - Use `secure`, `httpOnly`, `sameSite` appropriately
4. **Save and reuse authentication cookies** - Skip repetitive logins when appropriate
5. **Isolate contexts for multi-account testing** - Each context has independent cookies
6. **Monitor cookie evolution** - Real browsing accumulates cookies naturally
7. **Clean up expired cookies** - Remove invalid cookies before reuse
8. **Use secure storage** - Encrypt saved cookies, never hardcode secrets

## See Also

- **[Browser Contexts](contexts.md)** - Isolated cookie environments
- **[HTTP Requests](../network/http-requests.md)** - Browser-context requests inherit cookies automatically
- **[Human-Like Interactions](../automation/human-interactions.md)** - Combine cookies with realistic behavior
- **[API Reference: Storage Commands](/api/commands/storage_commands/)** - Full CDP cookie methods

Effective cookie management is the foundation of realistic browser automation. By balancing freshness with persistence and respecting security attributes, you can build automation that behaves like a real user while remaining efficient and maintainable.
