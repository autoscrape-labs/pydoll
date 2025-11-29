# Browser Domain

The Browser domain is the backbone of Pydoll's zero-webdriver architecture. This component provides a direct interface to browser instances through the Chrome DevTools Protocol (CDP), eliminating the need for traditional webdrivers while delivering superior performance and reliability.

```mermaid
graph LR
    A[Pydoll API] --> B[Browser Domain]
    B <--> C[Chrome DevTools Protocol]
    C <--> D[Browser Process]
    
    subgraph "Internal Components"
        B --> E[Connection Handler]
        B --> F[Process Manager]
        B --> G[Options Manager]
        B --> H[Proxy Manager]
        B --> I[Temp Directory Manager]
    end
```

## Technical Architecture

At its core, the Browser domain is implemented as an abstract base class (`Browser`) that establishes the fundamental contract for all browser implementations. Specific browser classes like `Chrome` and `Edge` extend this base class to provide browser-specific behavior while sharing the common architecture.

```python
# Abstract base class (simplified)
class Browser(ABC):
    def __init__(self, options_manager: BrowserOptionsManager, connection_port: Optional[int] = None):
        # Initialize components
        # ...
    
    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """Must be implemented by subclasses"""
        pass

    async def start(self, headless: bool = False) -> Tab:
        # Start browser process
        # Establish CDP connection
        # Return initial tab for interaction
        # ...

# Implementation for Chrome
class Chrome(Browser):
    def _get_default_binary_location(self) -> str:
        # Return path to Chrome binary
        # ...
```

The abstraction allows Pydoll to support multiple browsers through a unified interface, with each implementation handling browser-specific details such as executable discovery, command-line arguments, and protocol variations.

## Core Usage Patterns

The Browser domain follows a consistent pattern for initialization, tab management, and cleanup. Note that `start()` now returns a `Tab` instance directly:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def simple_browser_example():
    # Create and start a browser instance
    browser = Chrome()
    tab = await browser.start()  # Returns Tab directly
    
    try:
        # Navigate and interact with the tab
        await tab.go_to("https://example.com")
        
        # Perform operations with the tab
        title = await tab.execute_script("return document.title")
        print(f"Page title: {title}")
        
    finally:
        # Always ensure the browser is properly closed
        await browser.stop()

# Run the async example
asyncio.run(simple_browser_example())
```

!!! tip "Context Manager Usage"
    For cleaner resource management, use the context manager pattern:
    
    ```python
    async def context_manager_example():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to("https://example.com")
            # The browser is automatically closed when exiting the context
    
    asyncio.run(context_manager_example())
    ```

## Hierarchy of Browser Implementations

The Browser domain follows a clear inheritance hierarchy that promotes code reuse while allowing for browser-specific implementations:

```mermaid
classDiagram
    class Browser {
        <<Abstract>>
        +__init__(options_manager, connection_port)
        +start(headless) Tab
        +stop()
        +new_tab(url, browser_context_id) Tab
        +create_browser_context() str
        #_get_default_binary_location()*
    }
    
    class Chrome {
        +_get_default_binary_location()
    }
    
    class Edge {
        +_get_default_binary_location()
    }
    
    Browser <|-- Chrome : extends
    Browser <|-- Edge : extends
```

This architecture allows Pydoll to support multiple browser types through a unified interface. Each concrete implementation (Chrome, Edge) needs only to provide browser-specific details like executable discovery, while inheriting the robust core functionality from the base Browser class.

## Initialization Parameters

The Browser domain accepts two primary parameters during initialization, each controlling a different aspect of the browser's behavior:

### Options Manager Parameter

The `options_manager` parameter accepts an instance of `BrowserOptionsManager` that handles browser options initialization and configuration:

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.interfaces import BrowserOptionsManager

# The options manager is typically handled internally by browser implementations
browser = Chrome()  # Uses default ChromiumOptionsManager internally
```

The options manager is responsible for:
- Initializing browser options with appropriate defaults
- Adding required CDP arguments
- Managing browser-specific configuration

!!! info "Internal Implementation"
    Most users don't need to interact directly with the options manager, as browser implementations like `Chrome` provide their own specialized managers internally. However, advanced users can create custom options managers for specialized configurations.

### Connection Port Parameter

The `connection_port` parameter defines which port to use for the CDP WebSocket connection:

```python
# Specify exact port for connection
browser = Chrome(connection_port=9222)
```

This parameter serves two distinct purposes:

1. **For browser launching**: Specifies which port the browser should open for CDP communication
2. **For connection to existing browser**: Defines which port to connect to when using external browser instances

!!! warning "Port Availability"
    When not specified, Pydoll selects a random available port between 9223 and 9322. If your environment has firewall or network restrictions, you may need to explicitly set a port that's accessible.

## Internal Components

The Browser domain coordinates several specialized components to provide its functionality:

### Connection Handler

The ConnectionHandler establishes and maintains communication with the browser through the Chrome DevTools Protocol. It provides a layer of abstraction over the WebSocket connection, handling command execution, response processing, and event subscription.

This component is a fundamental part of Pydoll's architecture and will be explored in more detail in the dedicated Connection Domain section.

### Browser Process Manager

The BrowserProcessManager handles the browser process lifecycle:

```python
class BrowserProcessManager:
    def start_browser_process(self, binary, port, arguments):
        # Launch browser executable with proper arguments
        # Monitor process startup
        # ...
        
    def stop_process(self):
        # Terminate browser process
        # Cleanup resources
        # ...
```

This separation of concerns ensures that browser process management is decoupled from protocol communication, making the code more maintainable and testable.

### Temp Directory Manager

The TempDirectoryManager handles temporary directory creation and cleanup for browser user data:

```python
class TempDirectoryManager:
    def create_temp_dir(self):
        # Create temporary directory for browser user data
        # Return directory handle
        # ...
        
    def cleanup(self):
        # Remove temporary directories
        # Clean up resources
        # ...
```

This component ensures that temporary browser data is properly managed and cleaned up, preventing disk space issues during long-running automation sessions.

### Proxy Manager

The ProxyManager configures browser proxy settings:

```python
class ProxyManager:
    def __init__(self, options):
        # Parse proxy settings from options
        # ...
        
    def get_proxy_credentials(self):
        # Extract authentication details
        # Format proxy configuration
        # ...
```

This component is crucial for automated web scraping or testing scenarios that require proxy rotation or authentication.

## Lifecyle and Context Management

The Browser domain implements Python's asynchronous context management protocol (`__aenter__` and `__aexit__`) to provide automatic resource cleanup:

```python
async def scrape_data():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        # Work with tab...
        # Browser automatically closes when exiting the context
```

This pattern ensures that browser processes are properly terminated even if exceptions occur during automation, preventing resource leaks.


### Starting Browser and Getting Initial Tab

```python
browser = Chrome()
tab = await browser.start()  # Returns Tab instance
await tab.go_to("https://example.com")
```

### Creating Additional Tabs

```python
# Create additional tabs
tab2 = await browser.new_tab("https://github.com")
tab3 = await browser.new_tab()  # Empty tab

# Work with multiple tabs
await tab.go_to("https://example.com")
await tab2.go_to("https://github.com")
```

!!! tip "Multi-Tab Automation"
    You can work with multiple tabs simultaneously:
    
    ```python
    async def multi_tab_example():
        browser = Chrome()
        tab1 = await browser.start()
        
        # Create and work with multiple tabs
        await tab1.go_to("https://example.com")
        
        tab2 = await browser.new_tab("https://github.com")
        
        # Get information from both tabs
        title1 = await tab1.execute_script("return document.title")
        title2 = await tab2.execute_script("return document.title")
        
        print(f"Tab 1: {title1}")
        print(f"Tab 2: {title2}")
        
        await browser.stop()
    ```

## Browser Context Management

### Understanding Browser Contexts

Browser contexts are one of Pydoll's most powerful features for creating isolated browsing environments. Think of a browser context as a completely separate browser session within the same browser process - similar to opening an incognito window, but with programmatic control.

Each browser context maintains its own:

- **Cookies and session storage**: Completely isolated from other contexts
- **Local storage and IndexedDB**: Separate data stores per context
- **Cache**: Independent caching for each context
- **Permissions**: Context-specific permission grants
- **Network settings**: Including proxy configurations
- **Authentication state**: Login sessions are context-specific

```mermaid
graph TB
    A[Browser Process] --> B[Default Context]
    A --> C[Context 1]
    A --> D[Context 2]
    
    B --> B1[Tab 1]
    B --> B2[Tab 2]
    
    C --> C1[Tab 3]
    
    D --> D1[Tab 4]
    

```

### Why Use Browser Contexts?

Browser contexts are essential for several automation scenarios:

1. **Multi-Account Testing**: Test different user accounts simultaneously without interference
2. **A/B Testing**: Compare different user experiences in parallel
3. **Geo-Location Testing**: Use different proxy settings per context
4. **Session Isolation**: Prevent cross-contamination between test scenarios
5. **Parallel Scraping**: Scrape multiple sites with different configurations

### Headless vs Headed: Windows and Best Practices

Browser contexts are a logical isolation layer. What you actually see is the page created inside a context:

- In headed mode (visible UI), creating the first page inside a new browser context will typically open a new OS window. The context is the isolated environment; the page is what renders in a tab or window.
- In headless mode (no visible UI), no windows appear. The isolation still exists logically in the background, keeping cookies, storage, cache and auth state fully separate per context.

Recommendations:

- Prefer using multiple contexts in headless environments (e.g., CI/CD) for cleaner isolation, faster startup, and lower resource usage compared to launching multiple browser processes.
- Use contexts to simulate multiple users or sessions in parallel without cross-contamination.

Why contexts are efficient:

- Creating a new browser context is significantly faster and lighter than starting a whole new browser instance. This makes test suites and scraping jobs more reliable and scalable.

### CDP Hierarchy and Context Window Semantics (Advanced)

To reason precisely about contexts, it's useful to map Pydoll concepts to CDP:

- Browser (process): single Chromium process running the DevTools endpoint.
- BrowserContext: isolated profile inside that process (cookies, storage, cache, permissions).
- Target/Page: an individual top-level page, popup, or background target that you control.

CDP and `browserContextId`:

- When creating a page via `Target.createTarget`, passing `browserContextId` tells the browser which isolated profile the new page should belong to. Without this ID, the target is created in the default context.
- The ID is essential for isolation — it binds the new target to the correct storage/auth/permission boundary.

Why the first page in a context opens a window (headed):

- In headed mode, a page needs a top-level native window to render. A freshly created context initially has no window associated with it — it exists only in memory.
- The first page created in that context implicitly materializes a window for that context. Subsequent pages can open as tabs within that window.

Implications for `new_window`/`newWindow` semantics:

- If you attempt to create a page with "tab-like" behavior (no new top-level window) in a context that has no existing window (first page), the browser may error because there is no host window to attach the tab to.
- Practically: treat the first page in a new context (headed) as requiring a top-level window. Afterwards, you can create additional pages as tabs.

Headless mode makes this distinction moot:

- With no visible UI, windows vs tabs are logical constructs only. Context isolation is enforced the same way, but nothing is rendered, so there is no requirement to bootstrap a native window for the first page.

### Context-specific Proxy: sanitize + auth via Fetch events

When creating a browser context with a private proxy (credentials embedded in the URL), Pydoll follows a two-step strategy to avoid leaking credentials and reliably authenticate:

1) Sanitize the proxy server in the CDP command

- If you pass `proxy_server='http://user:pass@host:port'`, only the credential-free URL is sent to CDP (`http://host:port`).
- Internally, Pydoll extracts and stores the credentials keyed by `browserContextId`.

2) Attach per-context auth handlers on first tab

- When you open a `Tab` inside that context, Pydoll enables Fetch events for that tab and registers two temporary listeners:
  - `Fetch.requestPaused`: continues normal requests.
  - `Fetch.authRequired`: automatically responds with the stored `user`/`pass`, then disables Fetch to avoid intercepting further requests.

Why this design?

- Prevents credential exposure in command logs and CDP parameters.
- Keeps the auth scope strictly limited to the context that requested the proxy.
- Works in both headed and headless modes (the auth flow is network-level, not UI-dependent).

Code flow highlights (simplified):

```python
# On context creation
context_id = await browser.create_browser_context(proxy_server='user:pwd@host:port')
# => sends Target.createBrowserContext with 'http://host:port'
# => stores {'context_id': ('user', 'pwd')} internally

# On first tab in that context
tab = await browser.new_tab(browser_context_id=context_id)
# => tab.enable_fetch_events(handle_auth=True)
# => tab.on('Fetch.requestPaused', continue_request)
# => tab.on('Fetch.authRequired', continue_with_auth(user, pwd))
```

### Creating and Managing Contexts

```python
# Create isolated browser context
context_id = await browser.create_browser_context()

# Create tab in specific context
tab = await browser.new_tab("https://example.com", browser_context_id=context_id)

# Get all browser contexts
contexts = await browser.get_browser_contexts()
print(f"Active contexts: {contexts}")

# Delete context (closes all associated tabs)
await browser.delete_browser_context(context_id)
```

### Default vs Custom Contexts

Every browser starts with a **default context** that contains the initial tab returned by `browser.start()`. You can create additional contexts as needed:

```python
browser = Chrome()
default_tab = await browser.start()  # Uses default context

# Create custom context
custom_context_id = await browser.create_browser_context()
custom_tab = await browser.new_tab("https://example.com", browser_context_id=custom_context_id)

# Both tabs are completely isolated from each other
await default_tab.go_to("https://site1.com")
await custom_tab.go_to("https://site2.com")
```

### Practical Example: Multi-Account Testing

Here's a real-world example of testing multiple user accounts simultaneously:

```python
async def test_multiple_accounts():
    browser = Chrome()
    await browser.start()
    
    # Test data for different accounts
    accounts = [
        {"username": "user1@example.com", "password": "pass1"},
        {"username": "user2@example.com", "password": "pass2"},
        {"username": "admin@example.com", "password": "admin_pass"}
    ]
    
    contexts_and_tabs = []
    
    # Create isolated context for each account
    for i, account in enumerate(accounts):
        context_id = await browser.create_browser_context()
        tab = await browser.new_tab("https://app.example.com/login", browser_context_id=context_id)
        
        # Login with account credentials
        await tab.find(tag_name="input", name="username").type_text(account["username"])
        await tab.find(tag_name="input", name="password").type_text(account["password"])
        await tab.find(tag_name="button", type="submit").click()
        
        contexts_and_tabs.append((context_id, tab, account["username"]))
    
    # Now test different scenarios with each account simultaneously
    for context_id, tab, username in contexts_and_tabs:
        # Each tab maintains its own login session
        await tab.go_to("https://app.example.com/dashboard")
        user_info = await tab.find(class_name="user-info").text
        print(f"User {username} dashboard: {user_info}")
    
    # Cleanup: delete all contexts
    for context_id, _, _ in contexts_and_tabs:
        await browser.delete_browser_context(context_id)
    
    await browser.stop()
```

### Context-Specific Proxy Configuration

Each browser context can have its own proxy settings, making it perfect for geo-location testing or IP rotation:

```python
# Create context with specific proxy
context_id = await browser.create_browser_context(
    proxy_server="http://proxy.example.com:8080",
    proxy_bypass_list="localhost,127.0.0.1"
)

# All tabs in this context will use the specified proxy
tab = await browser.new_tab("https://example.com", browser_context_id=context_id)
```

### Advanced Context Management

#### Context Lifecycle Management

```python
async def manage_context_lifecycle():
    browser = Chrome()
    await browser.start()
    
    # Create multiple contexts for different purposes
    contexts = {}
    
    # Context for US region testing
    us_context = await browser.create_browser_context(
        proxy_server="http://us-proxy.example.com:8080"
    )
    contexts['us'] = us_context
    
    # Context for EU region testing  
    eu_context = await browser.create_browser_context(
        proxy_server="http://eu-proxy.example.com:8080"
    )
    contexts['eu'] = eu_context
    
    # Context for admin testing (no proxy)
    admin_context = await browser.create_browser_context()
    contexts['admin'] = admin_context
    
    try:
        # Use contexts for parallel testing
        us_tab = await browser.new_tab("https://api.example.com/geo", browser_context_id=contexts['us'])
        eu_tab = await browser.new_tab("https://api.example.com/geo", browser_context_id=contexts['eu'])
        admin_tab = await browser.new_tab("https://admin.example.com", browser_context_id=contexts['admin'])
        
        # Each tab will have different IP/location
        us_location = await us_tab.execute_script("return fetch('/api/location').then(r => r.json())")
        eu_location = await eu_tab.execute_script("return fetch('/api/location').then(r => r.json())")
        
        print(f"US Context Location: {us_location}")
        print(f"EU Context Location: {eu_location}")
        
    finally:
        # Clean up all contexts
        for region, context_id in contexts.items():
            await browser.delete_browser_context(context_id)
            print(f"Deleted {region} context")
        
        await browser.stop()
```

#### Context Storage Isolation

```python
async def demonstrate_storage_isolation():
    browser = Chrome()
    await browser.start()
    
    # Create two contexts
    context1 = await browser.create_browser_context()
    context2 = await browser.create_browser_context()
    
    # Create tabs in each context
    tab1 = await browser.new_tab("https://example.com", browser_context_id=context1)
    tab2 = await browser.new_tab("https://example.com", browser_context_id=context2)
    
    # Set different data in localStorage for each context
    await tab1.execute_script("localStorage.setItem('user', 'Alice')")
    await tab2.execute_script("localStorage.setItem('user', 'Bob')")
    
    # Verify isolation - each context has its own storage
    user1 = await tab1.execute_script("return localStorage.getItem('user')")
    user2 = await tab2.execute_script("return localStorage.getItem('user')")
    
    print(f"Context 1 user: {user1}")  # Alice
    print(f"Context 2 user: {user2}")  # Bob
    
    # Clean up
    await browser.delete_browser_context(context1)
    await browser.delete_browser_context(context2)
    await browser.stop()
```

## Target Management

Get information about all active targets (tabs, service workers, etc.) in the browser:

```python
# Get all targets
targets = await browser.get_targets()

# Filter for page targets only
pages = [t for t in targets if t.get('type') == 'page']

for page in pages:
    print(f"Target ID: {page['targetId']}")
    print(f"URL: {page['url']}")
    print(f"Title: {page.get('title', 'No title')}")
```

## Window Management

The Browser domain provides methods to control the browser window:

```python
# Get the current window ID
window_id = await browser.get_window_id()

# Set window bounds (position and size)
await browser.set_window_bounds({
    'left': 100,
    'top': 100,
    'width': 1024,
    'height': 768
})

# Maximize the window
await browser.set_window_maximized()

# Minimize the window
await browser.set_window_minimized()
```

!!! info "Window Management Use Cases"
    Window management is particularly useful for:
    - Setting precise window sizes for consistent screenshots
    - Positioning windows for multi-monitor setups
    - Creating user-friendly automation that's visible during development

## Cookie Management

The Browser domain provides methods for browser-wide cookie management:

```python
# Set cookies at the browser level
cookies_to_set = [
    {
        "name": "session_id",
        "value": "global_session_123",
        "domain": "example.com",
        "path": "/",
        "secure": True,
        "httpOnly": True
    }
]
await browser.set_cookies(cookies_to_set)

# Get all cookies from the browser
all_cookies = await browser.get_cookies()
print(f"Number of cookies: {len(all_cookies)}")

# Delete all cookies from the browser
await browser.delete_all_cookies()
```

### Context-Specific Cookie Management

```python
# Create browser context
context_id = await browser.create_browser_context()

# Set cookies for specific context
await browser.set_cookies(cookies_to_set, browser_context_id=context_id)

# Get cookies from specific context
context_cookies = await browser.get_cookies(browser_context_id=context_id)

# Delete cookies from specific context
await browser.delete_all_cookies(browser_context_id=context_id)
```

!!! tip "Browser vs Tab Cookie Management"
    - **Browser-level cookies** (using the methods above) apply to all tabs in the browser or specific context
    - **Tab-level cookies** (using `tab.set_cookies()`) apply only to that specific tab
    
    Choose the appropriate scope based on your automation needs.

## Download Management

Configure download behavior for the browser or specific contexts:

```python
# Set a custom download path
download_path = "/path/to/downloads"
await browser.set_download_path(download_path)

# Advanced download configuration
await browser.set_download_behavior(
    behavior=DownloadBehavior.ALLOW,
    download_path=download_path,
    events_enabled=True  # Enable download progress events
)

# Context-specific download configuration
context_id = await browser.create_browser_context()
await browser.set_download_behavior(
    behavior=DownloadBehavior.ALLOW,
    download_path="/path/to/context/downloads",
    browser_context_id=context_id
)
```

## Permission Management

Grant or reset browser permissions for automated testing:

```python
from pydoll.constants import PermissionType

# Grant permissions globally
await browser.grant_permissions([
    PermissionType.GEOLOCATION,
    PermissionType.NOTIFICATIONS,
    PermissionType.CAMERA
])

# Grant permissions for specific origin
await browser.grant_permissions(
    [PermissionType.GEOLOCATION],
    origin="https://example.com"
)

# Grant permissions for specific context
context_id = await browser.create_browser_context()
await browser.grant_permissions(
    [PermissionType.MICROPHONE],
    browser_context_id=context_id
)

# Reset all permissions to defaults
await browser.reset_permissions()
```

## Event System Overview

The Browser domain provides methods to enable and monitor various types of events. These methods include `enable_fetch_events()` and the `on()` method for registering event callbacks.

### Request Interception

```python
# Enable request interception
await browser.enable_fetch_events(handle_auth_requests=True)

# Register event handler for intercepted requests
async def handle_request(event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    
    if 'analytics' in url:
        # Block analytics requests
        await browser.fail_request(request_id, NetworkErrorReason.BLOCKED_BY_CLIENT)
    else:
        # Continue other requests
        await browser.continue_request(request_id)

await browser.on('Fetch.requestPaused', handle_request)
```

### Custom Response Fulfillment

```python
async def fulfill_custom_response(event):
    request_id = event['params']['requestId']
    
    # Fulfill with custom response
    await browser.fulfill_request(
        request_id=request_id,
        response_code=200,
        response_headers=[{'name': 'Content-Type', 'value': 'application/json'}],
        response_body={'message': 'Custom response from Pydoll'}
    )

await browser.on('Fetch.requestPaused', fulfill_custom_response)
```

!!! warning "Browser vs Tab Event Scope"
    When enabling events at the Browser level (e.g., `browser.enable_fetch_events()`), they apply **globally** to all tabs in the browser. In contrast, enabling events at the Tab level (e.g., `tab.enable_fetch_events()`) affects only that specific tab.
    
    This distinction is important for performance and resource management. Enable events at the browser level when you need to monitor activity across all tabs, and at the tab level when you only care about a specific tab's events.

!!! info "Detailed Event System Documentation"
    The event system is a core component of Pydoll's architecture and will be covered in detail in a dedicated section. This will include event types, handling patterns, and advanced event-driven techniques.

## Proxy Configuration

Pydoll supports using proxies for browser connections. This is useful for web scraping, testing geo-specific content, or bypassing IP-based rate limits:

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Configure a proxy
options.add_argument('--proxy-server=http://proxy.example.com:8080')

# For proxies requiring authentication
browser = Chrome(options=options)
tab = await browser.start()

# Pydoll automatically handles proxy authentication challenges
await tab.go_to("https://example.com")
```

!!! tip "Private Proxy Authentication"
    Pydoll handles private proxy authentication automatically:
    
    1. When a proxy authentication challenge is detected, Pydoll intercepts it
    2. The proxy credentials are applied from the options
    3. The authentication is completed transparently
    4. Your automation continues without interruption
    
    This makes working with authenticated proxies much simpler compared to traditional browser automation.

## Parallel Execution

Pydoll provides built-in support for running multiple coroutines in parallel through the `run_in_parallel()` method. This feature is essential for maximizing performance in browser automation scenarios where multiple independent operations can be executed concurrently.

### Basic Usage

```python
from pydoll.browser.chromium import Chrome

async def main():
    browser = Chrome()
    tab = await browser.start()
    tab2 = await browser.new_tab()

    # Define multiple coroutines
    async def task1():
        await tab.go_to("https://example1.com")
        return await tab.execute_script("return document.title")
    
    async def task2():
        await tab2.go_to("https://example2.com")
        return await tab2.execute_script("return document.title")
    
    # Execute all tasks in parallel
    results = await browser.run_in_parallel(task1(), task2())
    print(results)  # ['Title 1', 'Title 2']
    
    await browser.stop()
```

### Concurrency Control with max_parallel_tasks

By default, Pydoll limits parallel execution to 2 concurrent tasks. You can configure this limit using the `max_parallel_tasks` option:

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

# Configure concurrency limit
options = ChromiumOptions()
options.max_parallel_tasks = 5  # Allow up to 5 concurrent tasks

browser = Chrome(options=options)
tab = await browser.start()

# Now up to 5 tasks will run concurrently
tasks = [fetch_data(i) for i in range(10)]
results = await browser.run_in_parallel(*tasks)
```

!!! warning "Concurrency Limit"
    The `max_parallel_tasks` must be greater than 0. Setting it too high may cause resource exhaustion or browser instability. A value between 2-10 is recommended for most use cases.

### Thread-Safe Execution

The `run_in_parallel()` method is designed to be thread-safe and handles different event loop scenarios:

1. **Same Event Loop**: If called from the same event loop where the browser was started, coroutines execute directly
2. **Different Event Loop**: Uses `asyncio.run_coroutine_threadsafe()` to safely execute across loops
3. **Semaphore Initialization**: Thread-safe double-checked locking pattern prevents race conditions

```python
import threading
import asyncio
from pydoll.browser.chromium import Chrome

def run_in_thread(browser):
    # This can be called from a different thread
    async def worker():
        async def task():
            # Your async work here
            return "result"
        
        result = await browser.run_in_parallel(task())
        print(result)
    
    asyncio.run(worker())

async def main():
    browser = Chrome()
    await browser.start()
    
    # Execute from different thread
    thread = threading.Thread(target=run_in_thread, args=(browser,))
    thread.start()
    thread.join()
    
    await browser.stop()
```

### Error Handling

The method includes comprehensive error handling:

```python
from pydoll.exceptions import RunInParallelError

try:
    results = await browser.run_in_parallel(task1(), task2())
except RunInParallelError as e:
    # Handles execution failures:
    # - Timeout after 60 seconds
    # - Cancelled execution
    # - Browser loop not running
    print(f"Parallel execution failed: {e}")
except RuntimeError as e:
    # Browser loop not initialized (start() not called)
    print(f"Browser not ready: {e}")
```

!!! info "Timeout Behavior"
    By default, `run_in_parallel()` has a 60-second timeout. If any coroutine takes longer, a `RunInParallelError` is raised. Design your tasks to complete within this timeframe or break them into smaller chunks.

### Practical Example: Multi-Tab Data Scraping

```python
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def scrape_multiple_pages():
    options = ChromiumOptions()
    options.max_parallel_tasks = 4  # 4 concurrent operations
    
    browser = Chrome(options=options)
    await browser.start()
    
    # Create multiple tabs
    tabs = [await browser.new_tab() for _ in range(4)]
    
    # Define scraping tasks
    async def scrape_page(tab, url):
        await tab.go_to(url)
        title = await tab.execute_script("return document.title")
        content = await tab.execute_script("return document.body.innerText")
        return {"url": url, "title": title, "content": content}
    
    urls = [
        "https://example1.com",
        "https://example2.com", 
        "https://example3.com",
        "https://example4.com"
    ]
    
    # Scrape all pages in parallel
    tasks = [scrape_page(tab, url) for tab, url in zip(tabs, urls)]
    results = await browser.run_in_parallel(*tasks)
    
    for result in results:
        print(f"Scraped {result['url']}: {result['title']}")
    
    await browser.stop()
```

### How It Works Internally

The `run_in_parallel()` method uses `asyncio.gather()` with semaphore-based concurrency control:

1. **Semaphore Creation**: A semaphore is lazily initialized based on `max_parallel_tasks`
2. **Coroutine Wrapping**: Each coroutine is wrapped with `_limited_coroutine()` to respect the semaphore
3. **Gather Execution**: `asyncio.gather()` runs all wrapped coroutines concurrently
4. **Result Collection**: Results are returned in the same order as input coroutines

```python
# Simplified internal implementation
async def _limited_coroutine(self, coroutine):
    if self.options.max_parallel_tasks and self._semaphore:
        async with self._semaphore:
            return await coroutine
    return await coroutine

async def run_in_parallel(self, *coroutines):
    wrapped = [self._limited_coroutine(coro) for coro in coroutines]
    return await asyncio.gather(*wrapped, return_exceptions=False)
```

!!! tip "Best Practices"
    - Use `run_in_parallel()` for I/O-bound operations like network requests or page navigation
    - Set `max_parallel_tasks` based on your system resources and target website's rate limits
    - Handle exceptions in individual tasks or use `return_exceptions=True` for fault tolerance
    - Ensure the browser is started before calling this method (check `_loop` is initialized)

## Conclusion

The Browser domain serves as the foundation of Pydoll's architecture, providing a powerful interface to browser instances through the Chrome DevTools Protocol. By understanding its capabilities and patterns, you can create sophisticated browser automation that's more reliable and efficient than traditional webdriver-based approaches.

The combination of a clean abstraction layer, comprehensive event system, tab-based architecture, parallel execution capabilities, and direct control over the browser process enables advanced automation scenarios while maintaining a simple and intuitive API.
