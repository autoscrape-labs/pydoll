# Browser Contexts

Browser Contexts are Pydoll's solution for creating completely isolated browsing environments within a single browser process. Think of them as separate "incognito windows" but with full programmatic control, each context maintains its own cookies, storage, cache, and authentication state.

## Quick Start

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_context_example():
    async with Chrome() as browser:
        # Start browser with initial tab in default context
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # Create isolated context
        context_id = await browser.create_browser_context()
        
        # New tab in isolated context
        isolated_tab = await browser.new_tab('https://example.com', browser_context_id=context_id)
        
        # Both tabs are completely isolated - different cookies, storage, etc.
        await initial_tab.execute_script("localStorage.setItem('user', 'Alice')")
        await isolated_tab.execute_script("localStorage.setItem('user', 'Bob')")
        
        # Verify isolation
        user_default = await initial_tab.execute_script("return localStorage.getItem('user')")
        user_isolated = await isolated_tab.execute_script("return localStorage.getItem('user')")
        
        print(f"Default context: {user_default}")  # Alice
        print(f"Isolated context: {user_isolated}")  # Bob

asyncio.run(basic_context_example())
```

## What Are Browser Contexts?

A browser context is an isolated browsing environment within a single browser process. Each context maintains completely separate:

| Component | Description | Isolation Level |
|-----------|-------------|-----------------|
| **Cookies** | HTTP cookies and session data | ✓ Fully isolated |
| **Local Storage** | `localStorage` and `sessionStorage` | ✓ Fully isolated |
| **IndexedDB** | Client-side database | ✓ Fully isolated |
| **Cache** | HTTP cache and resources | ✓ Fully isolated |
| **Permissions** | Geolocation, notifications, camera, etc. | ✓ Fully isolated |
| **Authentication** | Login sessions and auth tokens | ✓ Fully isolated |
| **Service Workers** | Background scripts | ✓ Fully isolated |

```mermaid
graph LR
    Browser[Browser Process] --> Default[Default Context]
    Browser --> Context1[Context 1]
    Browser --> Context2[Context 2]
    
    Default --> T1[Tab A]
    Default --> T2[Tab B]
    Context1 --> T3[Tab C]
    Context2 --> T4[Tab D]
```

## Why Use Browser Contexts?

### 1. Multi-Account Testing

Test different user accounts simultaneously without interference:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def perform_login(tab, email, password):
    """
    Helper function to navigate to the login page
    and submit account credentials.
    """
    print(f"Attempting login with: {email}...")
    await tab.go_to('https://app.example.com/login')

    # Find elements
    email_field = await tab.find(id='email')
    password_field = await tab.find(id='password')
    login_btn = await tab.find(id='login-btn')

    # Fill credentials and click
    await email_field.type_text(email)
    await password_field.type_text(password)
    await login_btn.click()

    # Wait for login to process
    await asyncio.sleep(2)
    print(f"Login successful for {email}.")


async def multi_account_test():
    """
    Main script to test simultaneous logins
    using isolated browser contexts.
    """
    accounts = [
        {"email": "user1@example.com", "password": "pass1"},
        {"email": "user2@example.com", "password": "pass2"},
        {"email": "admin@example.com", "password": "admin_pass"}
    ]

    # This list will store information for each active user session.
    user_sessions = []

    async with Chrome() as browser:
        first_account = accounts[0]
        initial_tab = await browser.start()
        await perform_login(initial_tab, first_account['email'], first_account['password'])
        user_sessions.append({
            "email": first_account['email'],
            "tab": initial_tab,
            "context_id": None  # 'None' represents the default browser context
        })

        # Iterate over the rest of the accounts
        for account in accounts[1:]:
            context_id = await browser.create_browser_context()
            new_tab = await browser.new_tab(browser_context_id=context_id)
            await perform_login(new_tab, account['email'], account['password'])

            # Add this new session info to the list
            user_sessions.append({
                "email": account['email'],
                "tab": new_tab,
                "context_id": context_id
            })

        print("\n--- Verifying all active sessions ---")
        for session in user_sessions:
            tab = session["tab"]
            email = session["email"]
            await tab.go_to('https://app.example.com/dashboard')
            username = await tab.find(class_name='username')
            username_text = await username.text
            print(f"[Account: {email}] -> Logged in as: {username_text}")
            await asyncio.sleep(0.5)

        print("\n--- Cleaning up contexts ---")
        for session in user_sessions:
            # Only close contexts we created (non-None)
            if session["context_id"] is not None:
                print(f"Closing context for: {session['email']}")
                await session["tab"].close()
                await browser.delete_browser_context(session["context_id"])
        
        # The default context (None) is closed automatically
        # by the 'async with Chrome() as browser'

asyncio.run(multi_account_test())
```

### 2. Geo-Location Testing with Context-Specific Proxies

Each context can have its own proxy configuration:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def geo_location_testing():
    async with Chrome() as browser:
        # Start browser and use initial tab for first test (default context, no proxy)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://api.ipify.org')
        await asyncio.sleep(2)
        default_ip = await initial_tab.execute_script('return document.body.textContent')
        print(f"Default IP (no proxy): {default_ip}")
        
        # US context with US proxy
        us_context = await browser.create_browser_context(
            proxy_server='http://us-proxy.example.com:8080'
        )
        us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us_context)
        await asyncio.sleep(2)
        us_ip = await us_tab.execute_script('return document.body.textContent')
        print(f"US IP: {us_ip}")
        
        # EU context with EU proxy
        eu_context = await browser.create_browser_context(
            proxy_server='http://eu-proxy.example.com:8080'
        )
        eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu_context)
        await asyncio.sleep(2)
        eu_ip = await eu_tab.execute_script('return document.body.textContent')
        print(f"EU IP: {eu_ip}")
        
        # Cleanup (skip initial tab)
        await us_tab.close()
        await eu_tab.close()
        await browser.delete_browser_context(us_context)
        await browser.delete_browser_context(eu_context)

asyncio.run(geo_location_testing())
```

!!! tip "Proxy Authentication"
    Pydoll handles proxy authentication automatically for contexts. Just include credentials in the URL:
    ```python
    context_id = await browser.create_browser_context(
        proxy_server='http://username:password@proxy.example.com:8080'
    )
    ```
    The credentials are sanitized from CDP commands and only used when the browser challenges for auth.

### 3. A/B Testing

Compare different user experiences in parallel:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def ab_testing():
    async with Chrome() as browser:
        # Start browser with initial tab (Control group in default context)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        await initial_tab.execute_script("localStorage.setItem('experiment', 'control')")
        
        # Treatment group in isolated context
        context_b = await browser.create_browser_context()
        tab_b = await browser.new_tab('https://example.com', browser_context_id=context_b)
        await tab_b.execute_script("localStorage.setItem('experiment', 'treatment')")
        
        # Navigate both to the feature page
        await initial_tab.go_to('https://example.com/feature')
        await tab_b.go_to('https://example.com/feature')
        
        # Compare results
        result_a = await initial_tab.find(class_name='experiment-result')
        result_b = await tab_b.find(class_name='experiment-result')
        
        print(f"Control group result: {await result_a.text}")
        print(f"Treatment group result: {await result_b.text}")
        
        # Cleanup
        await tab_b.close()
        await browser.delete_browser_context(context_b)

asyncio.run(ab_testing())
```

### 4. Parallel Web Scraping

Scrape multiple sites with different configurations:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def parallel_scraping():
    websites = [
        {'url': 'https://news.ycombinator.com', 'selector': '.storylink'},
        {'url': 'https://reddit.com/r/python', 'selector': '.title'},
        {'url': 'https://github.com/trending', 'selector': '.h3'},
    ]
    
    async with Chrome() as browser:
        # Start browser and get initial tab
        initial_tab = await browser.start()
        
        # Create contexts for remaining sites (first uses default context)
        contexts = [None] + [await browser.create_browser_context() for _ in websites[1:]]
        
        # Create tabs (reusing initial tab for first site)
        tabs = [initial_tab] + [
            await browser.new_tab(browser_context_id=ctx) for ctx in contexts[1:]
        ]
        
        async def scrape_site(tab, site, context_id):
            """Scrape a single site within the given tab and context."""
            try:
                await tab.go_to(site['url'])
                await asyncio.sleep(3)
                
                # Extract titles using CSS selector
                elements = await tab.query(site['selector'], find_all=True)
                titles = [await elem.text for elem in elements[:5]]
                
                return {'url': site['url'], 'titles': titles}
            finally:
                # Clean up context (skip default context for initial tab)
                if context_id is not None:
                    await tab.close()
                    await browser.delete_browser_context(context_id)
        
        # Scrape all sites concurrently
        results = await asyncio.gather(*[
            scrape_site(tab, site, ctx) for tab, site, ctx in zip(tabs, websites, contexts)
        ])
        
        # Display results
        for result in results:
            print(f"\n{result['url']}:")
            for i, title in enumerate(result['titles'], 1):
                print(f"  {i}. {title}")

asyncio.run(parallel_scraping())
```

## Understanding Context Performance

### Contexts Are Lightweight

!!! info "Performance Characteristics"
    Creating a browser context is **significantly faster and lighter** than launching a new browser process:
    
    - **Context creation**: ~50-100ms, minimal memory overhead
    - **New browser process**: ~2-5 seconds, 50-150 MB base memory
    
    For 10 isolated environments:

    - **10 contexts in 1 browser**: ~500ms startup, ~500 MB total
    - **10 separate browsers**: ~30 seconds startup, ~1-1.5 GB total

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def benchmark_contexts_vs_browsers():
    # Benchmark contexts
    start = time.time()
    async with Chrome() as browser:
        # Start browser (initial tab not used in this example)
        await browser.start()
        
        contexts = []
        for i in range(10):
            context_id = await browser.create_browser_context()
            contexts.append(context_id)
        
        print(f"10 contexts created in: {time.time() - start:.2f}s")
        
        # Cleanup
        for context_id in contexts:
            await browser.delete_browser_context(context_id)

asyncio.run(benchmark_contexts_vs_browsers())
```

### Headless vs Headed: The Window Behavior

!!! warning "Important: Context Windows in Headed Mode"
    When running in **headed mode** (visible browser UI), there's an important behavior to understand:
    
    **The first tab created in a new context will open a new OS window.**
    
    - This happens because the context needs a "host window" to render its first page
    - Subsequent tabs in that context can open as tabs within that window
    - This is a CDP/Chromium limitation, not a Pydoll design choice
    
    **In headless mode**, this doesn't matter—no windows are created, everything runs in the background.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def demonstrate_window_behavior():
    # Headed mode - will see windows
    options_headed = ChromiumOptions()
    options_headed.headless = False
    
    async with Chrome(options=options_headed) as browser:
        # Start browser with initial tab (opens first window in default context)
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # Create new context - first tab will open a NEW window
        context = await browser.create_browser_context()
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context)
        
        # Second tab in same context - opens as tab in existing window
        tab3 = await browser.new_tab('https://google.com', browser_context_id=context)
        
        await asyncio.sleep(10)  # Observe the windows
        
        await tab2.close()
        await tab3.close()
        await browser.delete_browser_context(context)

# Headless mode - no windows, contexts are invisible but still isolated
async def headless_contexts():
    options = ChromiumOptions()
    options.headless = True  # No visible windows
    
    async with Chrome(options=options) as browser:
        # Start browser with initial tab in default context
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com/page0')
        
        # Create 4 more contexts - no windows opened, all in background
        contexts = []
        for i in range(1, 5):
            context_id = await browser.create_browser_context()
            tab = await browser.new_tab(f'https://example.com/page{i}', browser_context_id=context_id)
            contexts.append((context_id, tab))
        
        print(f"Created {len(contexts) + 1} isolated contexts (1 default + {len(contexts)} custom, invisible)")
        
        # Cleanup
        for context_id, tab in contexts:
            await tab.close()
            await browser.delete_browser_context(context_id)

asyncio.run(headless_contexts())
```

!!! tip "Best Practice: Use Headless for Contexts"
    For maximum efficiency with multiple contexts:
    
    - **Development/Debugging**: Use headed mode to see what's happening
    - **Production/CI/CD**: Use headless mode for faster, lighter execution
    - **Multiple contexts**: Strongly prefer headless to avoid window management complexity

## Context Management

### Creating Contexts

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def create_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # Create basic context
        context_id = await browser.create_browser_context()
        print(f"Created context: {context_id}")
        
        # Create context with proxy
        proxied_context = await browser.create_browser_context(
            proxy_server='http://proxy.example.com:8080',
            proxy_bypass_list='localhost,127.0.0.1'
        )
        print(f"Created proxied context: {proxied_context}")
        
        # Create context with authenticated proxy
        auth_context = await browser.create_browser_context(
            proxy_server='http://user:pass@proxy.example.com:8080'
        )
        print(f"Created auth context: {auth_context}")

asyncio.run(create_context_example())
```

### Listing Contexts

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def list_contexts():
    async with Chrome() as browser:
        await browser.start()
        
        # Get all contexts (includes default)
        contexts = await browser.get_browser_contexts()
        print(f"Initial contexts: {len(contexts)}")  # Usually 1 (default)
        
        # Create additional contexts
        context1 = await browser.create_browser_context()
        context2 = await browser.create_browser_context()
        
        # List again
        contexts = await browser.get_browser_contexts()
        print(f"After creating 2 new contexts: {len(contexts)}")  # 3 total
        
        for i, context_id in enumerate(contexts):
            print(f"  Context {i+1}: {context_id}")
        
        # Cleanup
        await browser.delete_browser_context(context1)
        await browser.delete_browser_context(context2)

asyncio.run(list_contexts())
```

### Deleting Contexts

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def delete_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # Create context with tabs
        context_id = await browser.create_browser_context()
        tab1 = await browser.new_tab('https://example.com', browser_context_id=context_id)
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context_id)
        
        print(f"Created context {context_id} with 2 tabs")
        
        # Deleting context closes all its tabs automatically
        await browser.delete_browser_context(context_id)
        print("Context deleted (all tabs closed automatically)")

asyncio.run(delete_context_example())
```

!!! warning "Deleting Contexts Closes All Tabs"
    When you delete a browser context, **all tabs belonging to that context are automatically closed**. This is an efficient way to clean up multiple tabs at once, but make sure you've saved any important data first.

## Default Context

Every browser starts with a **default context** that contains the initial tab:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def default_context_example():
    async with Chrome() as browser:
        # Initial tab is in the default context
        initial_tab = await browser.start()
        
        # Create tab without specifying context - uses default
        default_tab = await browser.new_tab('https://example.com')
        
        # Create custom context
        custom_context = await browser.create_browser_context()
        custom_tab = await browser.new_tab('https://github.com', browser_context_id=custom_context)
        
        # Default and custom contexts are isolated
        await default_tab.execute_script("localStorage.setItem('type', 'default')")
        await custom_tab.execute_script("localStorage.setItem('type', 'custom')")
        
        # Verify isolation
        default_type = await default_tab.execute_script("return localStorage.getItem('type')")
        custom_type = await custom_tab.execute_script("return localStorage.getItem('type')")
        
        print(f"Default context: {default_type}")  # 'default'
        print(f"Custom context: {custom_type}")    # 'custom'
        
        # Cleanup custom context
        await browser.delete_browser_context(custom_context)

asyncio.run(default_context_example())
```

!!! info "You Cannot Delete the Default Context"
    The default browser context is permanent and cannot be deleted. It exists for the entire browser session. Only custom contexts created with `create_browser_context()` can be deleted.

## Advanced Patterns

### Context Pool for Reusable Isolation

```python
import asyncio
from pydoll.browser.chromium import Chrome

class ContextPool:
    def __init__(self, browser, size=5):
        self.browser = browser
        self.size = size
        self.contexts = []
        self.in_use = set()
    
    async def initialize(self):
        """Create pool of contexts"""
        for _ in range(self.size):
            context_id = await self.browser.create_browser_context()
            self.contexts.append(context_id)
        print(f"Context pool initialized with {self.size} contexts")
    
    async def acquire(self):
        """Get available context from pool"""
        for context_id in self.contexts:
            if context_id not in self.in_use:
                self.in_use.add(context_id)
                return context_id
        raise Exception("No available contexts in pool")
    
    def release(self, context_id):
        """Return context to pool"""
        self.in_use.discard(context_id)
    
    async def cleanup(self):
        """Delete all contexts in pool"""
        for context_id in self.contexts:
            await self.browser.delete_browser_context(context_id)

async def use_context_pool():
    async with Chrome() as browser:
        await browser.start()
        
        # Create pool
        pool = ContextPool(browser, size=3)
        await pool.initialize()
        
        # Use contexts from pool
        async def scrape_with_pool(url):
            context_id = await pool.acquire()
            try:
                tab = await browser.new_tab(url, browser_context_id=context_id)
                await asyncio.sleep(2)
                title = await tab.execute_script('return document.title')
                await tab.close()
                return title
            finally:
                pool.release(context_id)
        
        # Scrape multiple URLs using the pool
        urls = [f'https://example.com/page{i}' for i in range(10)]
        results = await asyncio.gather(*[scrape_with_pool(url) for url in urls])
        
        for i, title in enumerate(results):
            print(f"{urls[i]}: {title}")
        
        # Cleanup
        await pool.cleanup()

asyncio.run(use_context_pool())
```

### Per-Context Configuration Manager

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def context_config_manager():
    async with Chrome() as browser:
        await browser.start()
        
        # Define configurations for different scenarios
        configs = {
            'us_user': {
                'proxy': 'http://us-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            'eu_user': {
                'proxy': 'http://eu-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64)'
            },
            'mobile_user': {
                'proxy': None,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
            }
        }
        
        contexts = {}
        
        # Create context for each configuration
        for name, config in configs.items():
            if config['proxy']:
                context_id = await browser.create_browser_context(
                    proxy_server=config['proxy']
                )
            else:
                context_id = await browser.create_browser_context()
            
            # Create tab and set user agent
            tab = await browser.new_tab(browser_context_id=context_id)
            # Note: User agent would be set via CDP or options, simplified here
            
            contexts[name] = {'context_id': context_id, 'tab': tab}
        
        # Use different contexts for different scenarios
        for name, data in contexts.items():
            tab = data['tab']
            await tab.go_to('https://httpbin.org/headers')
            await asyncio.sleep(2)
            print(f"\n{name} configuration active")
        
        # Cleanup
        for data in contexts.values():
            await data['tab'].close()
            await browser.delete_browser_context(data['context_id'])

asyncio.run(context_config_manager())
```

## Best Practices

1. **Use headless mode for multiple contexts** to avoid window management complexity
2. **Always delete contexts when done** to prevent memory leaks
3. **Group related operations in the same context** for better organization
4. **Prefer contexts over multiple browser processes** for better performance
5. **Use context pools** for scenarios requiring many short-lived isolated environments
6. **Close tabs before deleting contexts** for cleaner cleanup (though not strictly required)

## See Also

- **[Multi-Tab Management](tabs.md)** - Managing multiple tabs within contexts
- **[Deep Dive: Browser Domain](../../deep-dive/browser-domain.md)** - Architectural details on contexts
- **[Network: HTTP Requests](../network/http-requests.md)** - Browser-context requests inherit context state
- **[Core Concepts](../core-concepts.md)** - Understanding Pydoll's architecture

Browser Contexts are one of Pydoll's most powerful features for creating sophisticated automation workflows. By understanding how they work—especially the window behavior in headed mode and their lightweight nature—you can build efficient, scalable automation that handles complex multi-environment scenarios with ease.

