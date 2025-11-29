# Event System

Pydoll's event system allows you to listen and react to browser activities in real-time. This is essential for building dynamic automation, monitoring network requests, detecting page changes, and creating reactive workflows.

!!! info "Deep Dive Available"
    This guide focuses on practical usage. For architectural details and internal implementation, see [Event Architecture Deep Dive](../../deep-dive/event-architecture.md).

## Prerequisites

Before working with events, you need to enable the corresponding CDP domain:

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    
    # Enable the domain before listening to events
    await tab.enable_page_events()     # For page lifecycle events
    await tab.enable_network_events()  # For network activity
    await tab.enable_dom_events()      # For DOM changes
```

!!! warning "Events Won't Fire Without Enabling"
    If you register a callback but forget to enable the domain, your callback will never be triggered. Always enable the domain first!

## Basic Event Listening

The `on()` method registers event listeners:

```python
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

async def handle_page_load(event: LoadEventFiredEvent):
    print(f"Page loaded at {event['params']['timestamp']}")

# Register the callback
await tab.enable_page_events()
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_page_load)
```

### Event Structure

All events follow the same structure:

```python
{
    'method': 'Page.loadEventFired',  # Event name
    'params': {                        # Event-specific data
        'timestamp': 123456.789
    }
}
```

Access event data through `event['params']`:

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

async def handle_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    print(f"{method} {url}")
```

### Using Type Hints for Better IDE Support

Use type hints with event parameter types to get autocomplete for event keys:

```python
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

# With type hints - IDE knows all available keys!
async def handle_request(event: RequestWillBeSentEvent):
    # IDE will autocomplete 'params', 'request', 'url', etc.
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    timestamp = event['params']['timestamp']
    print(f"{method} {url} at {timestamp}")

async def handle_load(event: LoadEventFiredEvent):
    # IDE knows this event has 'timestamp' in params
    timestamp = event['params']['timestamp']
    print(f"Page loaded at {timestamp}")

await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, handle_request)

await tab.enable_page_events()
await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_load)
```

!!! tip "Type Hints for Event Parameters"
    All event types are defined in `pydoll.protocol.<domain>.events`. Using them gives you:
    
    - **Autocomplete**: IDE suggests available keys in `event['params']`
    - **Type safety**: Catch typos before running code
    - **Documentation**: See what data each event provides
    
    Event types follow the pattern: `<EventName>Event` (e.g., `RequestWillBeSentEvent`, `ResponseReceivedEvent`)

## Common Event Domains

### Page Events

Monitor page lifecycle and dialogs:

```python
from pydoll.protocol.page.events import PageEvent, JavascriptDialogOpeningEvent

await tab.enable_page_events()

# Page loaded
await tab.on(PageEvent.LOAD_EVENT_FIRED, lambda e: print("Page loaded!"))

# DOM ready
await tab.on(PageEvent.DOM_CONTENT_EVENT_FIRED, lambda e: print("DOM ready!"))

# JavaScript dialog
async def handle_dialog(event: JavascriptDialogOpeningEvent):
    message = event['params']['message']
    dialog_type = event['params']['type']
    print(f"Dialog ({dialog_type}): {message}")
    
    # Handle it automatically
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)

await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, handle_dialog)
```

### Network Events

Monitor requests and responses:

```python
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

await tab.enable_network_events()

# Track requests
async def log_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"→ {request['method']} {request['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# Track responses
async def log_response(event: ResponseReceivedEvent):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")

await tab.on(NetworkEvent.RESPONSE_RECEIVED, log_response)

# Track failures
async def log_failure(event: LoadingFailedEvent):
    url = event['params']['type']
    error = event['params']['errorText']
    print(f"[FAILED] {url} - {error}")

await tab.on(NetworkEvent.LOADING_FAILED, log_failure)
```

### DOM Events

React to DOM changes:

```python
from pydoll.protocol.dom.events import DomEvent, AttributeModifiedEvent

await tab.enable_dom_events()

# Track attribute changes
async def on_attribute_change(event: AttributeModifiedEvent):
    node_id = event['params']['nodeId']
    attr_name = event['params']['name']
    attr_value = event['params']['value']
    print(f"Node {node_id}: {attr_name}={attr_value}")

await tab.on(DomEvent.ATTRIBUTE_MODIFIED, on_attribute_change)

# Track document updates
await tab.on(DomEvent.DOCUMENT_UPDATED, lambda e: print("Document updated!"))
```

## Temporary Callbacks

Use `temporary=True` for one-time listeners:

```python
from pydoll.protocol.page.events import PageEvent

# This will only fire once and then auto-remove
await tab.on(
    PageEvent.LOAD_EVENT_FIRED,
    lambda e: print("First load!"),
    temporary=True
)

await tab.go_to("https://example.com")  # Fires callback
await tab.refresh()                      # Callback won't fire again
```

!!! tip "Perfect for One-Time Setup"
    Temporary callbacks are ideal for initialization tasks that should only happen once.

## Accessing Tab in Callbacks

Use `functools.partial` to pass the tab to your callbacks:

```python
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def process_response(tab, event: ResponseReceivedEvent):
    # Now we can use the tab object!
    request_id = event['params']['requestId']
    
    # Get response body
    body = await tab.get_network_response_body(request_id)
    print(f"Response body: {body[:100]}...")

await tab.enable_network_events()
await tab.on(
    NetworkEvent.RESPONSE_RECEIVED,
    partial(process_response, tab)
)
```

!!! info "Why Use Partial?"
    The event system only passes the event data to callbacks. `partial` lets you bind additional parameters like the tab instance.

## Managing Callbacks

### Removing Callbacks

```python
from pydoll.protocol.page.events import PageEvent

# Save the callback ID
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, my_callback)

# Remove it later
await tab.remove_callback(callback_id)
```

### Clearing All Callbacks

```python
# Remove all registered callbacks for this tab
await tab.clear_callbacks()
```

## Practical Examples

### Monitor API Calls

```python
import asyncio
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def monitor_api_calls(tab):
    collected_data = []
    
    # Type hint helps IDE autocomplete event keys
    async def capture_api_response(tab, data_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # Filter only API calls
        if '/api/' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        data_list.append({
            'url': url,
            'body': body,
            'status': event['params']['response']['status']
        })
        print(f"Captured API call: {url}")
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_api_response, tab, collected_data)
    )
    
    # Navigate and collect
    await tab.go_to("https://example.com")
    await asyncio.sleep(3)  # Wait for requests to complete
    
    return collected_data
```

### Wait for Specific Event

```python
import asyncio
from pydoll.protocol.page.events import PageEvent, FrameNavigatedEvent

async def wait_for_navigation():
    navigation_done = asyncio.Event()
    
    async def on_navigated(event: FrameNavigatedEvent):
        navigation_done.set()
    
    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)
    
    # Trigger navigation
    button = await tab.find(id='next-page')
    await button.click()
    
    # Wait for it to complete
    await navigation_done.wait()
    print("Navigation completed!")
```

### Network Idle Detection

```python
import asyncio
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    LoadingFinishedEvent,
    LoadingFailedEvent
)

async def wait_for_network_idle(tab, timeout=5):
    in_flight = 0
    idle_event = asyncio.Event()
    last_activity = asyncio.get_event_loop().time()
    
    async def on_request(event: RequestWillBeSentEvent):
        nonlocal in_flight, last_activity
        in_flight += 1
        last_activity = asyncio.get_event_loop().time()
    
    async def on_finished(event: LoadingFinishedEvent | LoadingFailedEvent):
        nonlocal in_flight, last_activity
        in_flight -= 1
        last_activity = asyncio.get_event_loop().time()
        
        if in_flight == 0:
            idle_event.set()
    
    await tab.enable_network_events()
    req_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
    fin_id = await tab.on(NetworkEvent.LOADING_FINISHED, on_finished)
    fail_id = await tab.on(NetworkEvent.LOADING_FAILED, on_finished)
    
    try:
        await asyncio.wait_for(idle_event.wait(), timeout=timeout)
        print("Network is idle!")
    except asyncio.TimeoutError:
        print(f"Network still active after {timeout}s")
    finally:
        # Cleanup
        await tab.remove_callback(req_id)
        await tab.remove_callback(fin_id)
        await tab.remove_callback(fail_id)
```

### Dynamic Content Scraping

```python
import asyncio
import json
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def scrape_infinite_scroll(tab, max_items=100):
    items = []
    
    async def capture_products(tab, items_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # Look for product API endpoint
        if '/products' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        try:
            data = json.loads(body)
            if 'items' in data:
                items_list.extend(data['items'])
                print(f"Collected {len(data['items'])} items (total: {len(items_list)})")
        except json.JSONDecodeError:
            pass
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_products, tab, items)
    )
    
    await tab.go_to("https://example.com/products")
    
    # Scroll to trigger infinite loading
    while len(items) < max_items:
        await tab.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
    
    return items[:max_items]
```

## Event Reference Tables

### Available Domains

| Domain | Enable Method | Common Use Cases |
|--------|--------------|------------------|
| Page | `enable_page_events()` | Page lifecycle, navigation, dialogs |
| Network | `enable_network_events()` | Request/response monitoring, API tracking |
| DOM | `enable_dom_events()` | DOM structure changes, attribute modifications |
| Fetch | `enable_fetch_events()` | Request interception and modification |
| Runtime | `enable_runtime_events()` | Console messages, JavaScript exceptions |

### Key Page Events

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| `LOAD_EVENT_FIRED` | Page load complete | Wait for full page load |
| `DOM_CONTENT_EVENT_FIRED` | DOM ready | Start DOM manipulation |
| `JAVASCRIPT_DIALOG_OPENING` | Alert/confirm/prompt | Auto-handle dialogs |
| `FRAME_NAVIGATED` | Navigation complete | Track SPA navigation |
| `FILE_CHOOSER_OPENED` | File input clicked | Automated file uploads |

### Key Network Events

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| `REQUEST_WILL_BE_SENT` | Before request sent | Log/modify outgoing requests |
| `RESPONSE_RECEIVED` | Response headers received | Capture API responses |
| `LOADING_FINISHED` | Response body loaded | Get full response data |
| `LOADING_FAILED` | Request failed | Track errors and retries |
| `WEB_SOCKET_CREATED` | WebSocket opened | Monitor real-time connections |

### Key DOM Events

| Event | When It Fires | Use Case |
|-------|---------------|----------|
| `DOCUMENT_UPDATED` | DOM rebuilt | Refresh element references |
| `ATTRIBUTE_MODIFIED` | Element attribute changed | Track dynamic attribute changes |
| `CHILD_NODE_INSERTED` | New element added | Detect dynamically added content |
| `CHILD_NODE_REMOVED` | Element removed | Detect removed content |

### Event Type Reference

All event types and their parameter structures are defined in the protocol modules:

| Domain | Import Path | Example Types |
|--------|-------------|---------------|
| Page | `pydoll.protocol.page.events` | `LoadEventFiredEvent`, `FrameNavigatedEvent`, `JavascriptDialogOpeningEvent` |
| Network | `pydoll.protocol.network.events` | `RequestWillBeSentEvent`, `ResponseReceivedEvent`, `LoadingFinishedEvent` |
| DOM | `pydoll.protocol.dom.events` | `DocumentUpdatedEvent`, `AttributeModifiedEvent`, `ChildNodeInsertedEvent` |
| Fetch | `pydoll.protocol.fetch.events` | `RequestPausedEvent`, `AuthRequiredEvent` |
| Runtime | `pydoll.protocol.runtime.events` | `ConsoleAPICalledEvent`, `ExceptionThrownEvent` |

Each event type is a `TypedDict` that defines the exact structure of the event, including all available keys in the `params` dictionary.

## Best Practices

### 1. Always Enable Domains First

```python
from pydoll.protocol.network.events import NetworkEvent

# Good
await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)

# Bad: callback will never fire
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)
await tab.enable_network_events()
```

### 2. Clean Up When Done

```python
from pydoll.protocol.network.events import NetworkEvent

# Enable for specific task
await tab.enable_network_events()
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# Do your work...
await tab.go_to("https://example.com")

# Clean up
await tab.remove_callback(callback_id)
await tab.disable_network_events()
```

### 3. Use Early Filtering

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

# Good: filter early
async def handle_api_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    if '/api/' not in url:
        return  # Exit early
    
    # Process only API requests
    process_request(event)

# Bad: processes everything
async def handle_all_requests(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    process_request(event)
    if '/api/' in url:
        do_extra_work(event)
```

### 4. Handle Errors Gracefully

```python
from pydoll.protocol.network.events import ResponseReceivedEvent

async def safe_callback(event: ResponseReceivedEvent):
    try:
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        process_body(body)
    except KeyError:
        # Event might not have requestId
        pass
    except Exception as e:
        print(f"Error in callback: {e}")
        # Continue without breaking event loop
```

## Performance Considerations

!!! warning "High-Frequency Events"
    DOM events can fire **very frequently** on dynamic pages. Use filtering and debouncing to avoid performance issues.

### Event Volume by Domain

| Domain | Event Frequency | Performance Impact |
|--------|----------------|-------------------|
| Page | Low | Minimal |
| Network | Moderate-High | Moderate |
| DOM | Very High | High |
| Fetch | Moderate | Moderate |

### Optimization Tips

1. **Enable only what you need**: Don't enable all domains at once
2. **Use temporary callbacks**: Auto-cleanup when possible
3. **Filter early**: Check conditions before expensive operations
4. **Disable when done**: Free up resources
5. **Avoid heavy processing**: Keep callbacks fast, offload work to separate tasks

```python
import asyncio
from pydoll.protocol.network.events import ResponseReceivedEvent

# Good: fast callback, offload heavy work
async def handle_response(event: ResponseReceivedEvent):
    if should_process(event):
        asyncio.create_task(heavy_processing(event))  # Don't block

# Bad: blocks event loop
async def handle_response(event: ResponseReceivedEvent):
    await heavy_processing(event)  # Blocks other events
```

## Common Patterns

### Context Manager for Events

```python
from contextlib import asynccontextmanager
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

@asynccontextmanager
async def monitor_requests(tab):
    """Context manager to monitor requests during a block."""
    requests = []
    
    async def capture(event: RequestWillBeSentEvent):
        requests.append(event['params']['request'])
    
    await tab.enable_network_events()
    cb_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, capture)
    
    try:
        yield requests
    finally:
        await tab.remove_callback(cb_id)
        await tab.disable_network_events()

# Usage
async with monitor_requests(tab) as requests:
    await tab.go_to("https://example.com")
    # All requests are captured

print(f"Captured {len(requests)} requests")
```

### Conditional Event Registration

```python
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.dom.events import DomEvent

async def setup_monitoring(tab, track_network=False, track_dom=False):
    """Enable only specified monitoring."""
    callbacks = []
    
    if track_network:
        await tab.enable_network_events()
        cb = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)
        callbacks.append(('network', cb))
    
    if track_dom:
        await tab.enable_dom_events()
        cb = await tab.on(DomEvent.ATTRIBUTE_MODIFIED, log_dom_change)
        callbacks.append(('dom', cb))
    
    return callbacks
```

## Further Reading

- **[Event Architecture Deep Dive](../../deep-dive/event-architecture.md)** - Internal implementation and WebSocket communication
- **[Network Monitoring](../network/monitoring.md)** - Advanced network analysis techniques
- **[Reactive Automation](reactive-automation.md)** - Building event-driven workflows

!!! tip "Start Simple"
    Begin with Page events to understand the basics, then move to Network and DOM events as needed. The event system is powerful but can be overwhelming at first.
