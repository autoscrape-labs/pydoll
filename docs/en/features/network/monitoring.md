# Network Monitoring

Network monitoring in Pydoll allows you to observe and analyze HTTP requests, responses, and other network activity during browser automation. This is essential for debugging, performance analysis, API testing, and understanding how web applications communicate with servers.

!!! info "Network vs Fetch Domain"
    **Network domain** is for passive monitoring (observing traffic). **Fetch domain** is for active interception (modifying requests/responses). This guide focuses on monitoring. For request interception, see the advanced documentation.

## Enabling Network Events

Before you can monitor network activity, you must enable the Network domain:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Enable network monitoring
        await tab.enable_network_events()
        
        # Now navigate
        await tab.go_to('https://api.github.com')
        
        # Don't forget to disable when done (optional but recommended)
        await tab.disable_network_events()

asyncio.run(main())
```

!!! warning "Enable Before Navigation"
    Always enable network events **before** navigating to capture all requests. Requests made before enabling won't be captured.

## Getting Network Logs

Pydoll automatically stores network logs when network events are enabled. You can retrieve them using `get_network_logs()`:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_requests():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navigate to a page
        await tab.go_to('https://httpbin.org/json')
        
        # Wait for page to fully load
        await asyncio.sleep(2)
        
        # Get all network logs
        logs = await tab.get_network_logs()
        
        print(f"Total requests captured: {len(logs)}")
        
        for log in logs:
            request = log['params']['request']
            print(f"→ {request['method']} {request['url']}")

asyncio.run(analyze_requests())
```

!!! note "Production-Ready Waiting"
    The examples above use `asyncio.sleep(2)` for simplicity. In production code, consider using more explicit waiting strategies:
    
    - Wait for specific elements to appear
    - Use the [Event System](../advanced/event-system.md) to detect when all resources have loaded
    - Implement network idle detection (see Real-Time Network Monitoring section)
    
    This ensures your automation waits exactly as long as needed, no more, no less.

### Filtering Network Logs

You can filter logs by URL pattern:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def filter_logs_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # Get all logs
        all_logs = await tab.get_network_logs()
        
        # Get logs for specific domain
        api_logs = await tab.get_network_logs(filter='api.example.com')
        
        # Get logs for specific endpoint
        user_logs = await tab.get_network_logs(filter='/api/users')

asyncio.run(filter_logs_example())
```

## Understanding Network Event Structure

Network logs contain detailed information about each request. Here's the structure:

### RequestWillBeSentEvent

This event is fired when a request is about to be sent:

```python
{
    'method': 'Network.requestWillBeSent',
    'params': {
        'requestId': 'unique-request-id',
        'loaderId': 'loader-id',
        'documentURL': 'https://example.com',
        'request': {
            'url': 'https://api.example.com/data',
            'method': 'GET',  # or 'POST', 'PUT', 'DELETE', etc.
            'headers': {
                'User-Agent': 'Chrome/...',
                'Accept': 'application/json',
                ...
            },
            'postData': '...',  # Only present for POST/PUT requests
            'initialPriority': 'High',
            'referrerPolicy': 'strict-origin-when-cross-origin'
        },
        'timestamp': 1234567890.123,
        'wallTime': 1234567890.123,
        'initiator': {
            'type': 'script',  # or 'parser', 'other'
            'stack': {...}  # Call stack if initiated from script
        },
        'type': 'XHR',  # Resource type: Document, Script, Image, XHR, etc.
        'frameId': 'frame-id',
        'hasUserGesture': False
    }
}
```

### Key Fields Reference

| Field | Location | Type | Description |
|-------|----------|------|-------------|
| `requestId` | `params.requestId` | `str` | Unique identifier for this request |
| `url` | `params.request.url` | `str` | Complete request URL |
| `method` | `params.request.method` | `str` | HTTP method (GET, POST, etc.) |
| `headers` | `params.request.headers` | `dict` | Request headers |
| `postData` | `params.request.postData` | `str` | Request body (POST/PUT) |
| `timestamp` | `params.timestamp` | `float` | Monotonic time when request started |
| `type` | `params.type` | `str` | Resource type (Document, XHR, Image, etc.) |
| `initiator` | `params.initiator` | `dict` | What triggered this request |

## Getting Response Bodies

To get the actual response content, use `get_network_response_body()`:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def fetch_api_response():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navigate to API endpoint
        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)
        
        # Get all requests
        logs = await tab.get_network_logs()
        
        for log in logs:
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            
            # Only get response for JSON endpoint
            if 'httpbin.org/json' in url:
                try:
                    # Get response body
                    response_body = await tab.get_network_response_body(request_id)
                    print(f"Response from {url}:")
                    print(response_body)
                except Exception as e:
                    print(f"Could not get response body: {e}")

asyncio.run(fetch_api_response())
```

!!! warning "Response Body Availability"
    Response bodies are only available for requests that have completed. Also, some response types (like images or redirects) may not have accessible bodies.

## Practical Use Cases

### 1. API Testing and Validation

Monitor API calls to verify correct requests are being made:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def validate_api_calls():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navigate to your app
        await tab.go_to('https://your-app.com')
        
        # Trigger some action that makes API calls
        button = await tab.find(id='load-data-button')
        await button.click()
        await asyncio.sleep(2)
        
        # Get API logs
        api_logs = await tab.get_network_logs(filter='/api/')
        
        print(f"\n📊 API Calls Summary:")
        print(f"Total API calls: {len(api_logs)}")
        
        for log in api_logs:
            request = log['params']['request']
            method = request['method']
            url = request['url']
            
            # Check if correct auth header is present
            headers = request.get('headers', {})
            has_auth = 'Authorization' in headers or 'authorization' in headers
            
            print(f"\n{method} {url}")
            print(f"  ✓ Has Authorization: {has_auth}")
            
            # Validate POST data if applicable
            if method == 'POST' and 'postData' in request:
                print(f"  📤 Body: {request['postData'][:100]}...")

asyncio.run(validate_api_calls())
```

### 2. Performance Analysis

Analyze request timing and identify slow resources:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_performance():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # Store timing data
        timings = []
        
        for log in logs:
            params = log['params']
            request_id = params['requestId']
            url = params['request']['url']
            resource_type = params.get('type', 'Other')
            
            timings.append({
                'url': url,
                'type': resource_type,
                'timestamp': params['timestamp']
            })
        
        # Sort by timestamp
        timings.sort(key=lambda x: x['timestamp'])
        
        print("\n⏱️  Request Timeline:")
        start_time = timings[0]['timestamp'] if timings else 0
        
        for timing in timings[:20]:  # Show first 20
            elapsed = (timing['timestamp'] - start_time) * 1000  # Convert to ms
            print(f"{elapsed:7.0f}ms | {timing['type']:12} | {timing['url'][:80]}")

asyncio.run(analyze_performance())
```

### 3. Detecting External Resources

Find all external domains your page connects to:

```python
import asyncio
from urllib.parse import urlparse
from collections import Counter
from pydoll.browser.chromium import Chrome

async def analyze_domains():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # Count requests per domain
        domains = Counter()
        
        for log in logs:
            url = log['params']['request']['url']
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains[domain] += 1
            except:
                pass
        
        print("\n🌐 External Domains:")
        for domain, count in domains.most_common(10):
            print(f"  {count:3} requests | {domain}")

asyncio.run(analyze_domains())
```

### 4. Monitoring Specific Resource Types

Track specific types of resources like images or scripts:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def track_resource_types():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(3)
        
        logs = await tab.get_network_logs()
        
        # Group by resource type
        by_type = {}
        
        for log in logs:
            params = log['params']
            resource_type = params.get('type', 'Other')
            url = params['request']['url']
            
            if resource_type not in by_type:
                by_type[resource_type] = []
            
            by_type[resource_type].append(url)
        
        print("\n📦 Resources by Type:")
        for rtype in sorted(by_type.keys()):
            urls = by_type[rtype]
            print(f"\n{rtype}: {len(urls)} resource(s)")
            for url in urls[:3]:  # Show first 3
                print(f"  • {url}")
            if len(urls) > 3:
                print(f"  ... and {len(urls) - 3} more")

asyncio.run(track_resource_types())
```

## Real-Time Network Monitoring

For real-time monitoring, use event callbacks instead of polling `get_network_logs()`:

!!! info "Understanding Events"
    Real-time monitoring uses Pydoll's event system to react to network activity as it happens. For a deep dive into how events work, see **[Event System](../advanced/event-system.md)**.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

async def real_time_monitoring():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Statistics
        stats = {
            'requests': 0,
            'responses': 0,
            'failed': 0
        }
        
        # Request callback
        async def on_request(event: RequestWillBeSentEvent):
            stats['requests'] += 1
            url = event['params']['request']['url']
            method = event['params']['request']['method']
            print(f"→ {method:6} | {url}")
        
        # Response callback
        async def on_response(event: ResponseReceivedEvent):
            stats['responses'] += 1
            response = event['params']['response']
            status = response['status']
            url = response['url']
            
            # Color code by status
            if 200 <= status < 300:
                color = '\033[92m'  # Green
            elif 300 <= status < 400:
                color = '\033[93m'  # Yellow
            else:
                color = '\033[91m'  # Red
            reset = '\033[0m'
            
            print(f"← {color}{status}{reset} | {url}")
        
        # Failed callback
        async def on_failed(event: LoadingFailedEvent):
            stats['failed'] += 1
            error = event['params']['errorText']
            print(f"✗ FAILED: {error}")
        
        # Enable and register callbacks
        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)
        
        # Navigate
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        print(f"\n📊 Summary:")
        print(f"  Requests: {stats['requests']}")
        print(f"  Responses: {stats['responses']}")
        print(f"  Failed: {stats['failed']}")

asyncio.run(real_time_monitoring())
```

## Resource Types Reference

Pydoll captures the following resource types:

| Type | Description | Examples |
|------|-------------|----------|
| `Document` | Main HTML documents | Page loads, iframe sources |
| `Stylesheet` | CSS files | External .css, inline styles |
| `Image` | Image resources | .jpg, .png, .gif, .webp, .svg |
| `Media` | Audio/video files | .mp4, .webm, .mp3, .ogg |
| `Font` | Web fonts | .woff, .woff2, .ttf, .otf |
| `Script` | JavaScript files | .js files, inline scripts |
| `TextTrack` | Subtitle files | .vtt, .srt |
| `XHR` | XMLHttpRequest | AJAX requests, legacy API calls |
| `Fetch` | Fetch API requests | Modern API calls |
| `EventSource` | Server-Sent Events | Real-time streams |
| `WebSocket` | WebSocket connections | Bidirectional communication |
| `Manifest` | Web app manifests | PWA configuration |
| `Other` | Other resource types | Miscellaneous |

## Advanced: Extracting Response Timing

Network events include detailed timing information:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def analyze_timing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Custom callback to capture timing
        timing_data = []
        
        async def on_response(event: ResponseReceivedEvent):
            response = event['params']['response']
            timing = response.get('timing')
            
            if timing:
                # Calculate different phases
                dns_time = timing.get('dnsEnd', 0) - timing.get('dnsStart', 0)
                connect_time = timing.get('connectEnd', 0) - timing.get('connectStart', 0)
                ssl_time = timing.get('sslEnd', 0) - timing.get('sslStart', 0)
                send_time = timing.get('sendEnd', 0) - timing.get('sendStart', 0)
                wait_time = timing.get('receiveHeadersStart', 0) - timing.get('sendEnd', 0)
                receive_time = timing.get('receiveHeadersEnd', 0) - timing.get('receiveHeadersStart', 0)
                
                timing_data.append({
                    'url': response['url'][:50],
                    'dns': dns_time if dns_time > 0 else 0,
                    'connect': connect_time if connect_time > 0 else 0,
                    'ssl': ssl_time if ssl_time > 0 else 0,
                    'send': send_time,
                    'wait': wait_time,
                    'receive': receive_time,
                    'total': receive_time + wait_time + send_time
                })
        
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.go_to('https://github.com')
        await asyncio.sleep(5)
        
        # Print timing breakdown
        print("\n⏱️  Request Timing Breakdown (ms):")
        print(f"{'URL':<50} | {'DNS':>6} | {'Connect':>8} | {'SSL':>6} | {'Send':>6} | {'Wait':>6} | {'Receive':>8} | {'Total':>7}")
        print("-" * 120)
        
        for data in sorted(timing_data, key=lambda x: x['total'], reverse=True)[:10]:
            print(f"{data['url']:<50} | {data['dns']:6.1f} | {data['connect']:8.1f} | {data['ssl']:6.1f} | "
                  f"{data['send']:6.1f} | {data['wait']:6.1f} | {data['receive']:8.1f} | {data['total']:7.1f}")

asyncio.run(analyze_timing())
```

## Timing Fields Explanation

| Phase | Fields | Description |
|-------|--------|-------------|
| **DNS** | `dnsStart` → `dnsEnd` | DNS lookup time |
| **Connect** | `connectStart` → `connectEnd` | TCP connection establishment |
| **SSL** | `sslStart` → `sslEnd` | SSL/TLS handshake |
| **Send** | `sendStart` → `sendEnd` | Time to send request |
| **Wait** | `sendEnd` → `receiveHeadersStart` | Waiting for server response (TTFB) |
| **Receive** | `receiveHeadersStart` → `receiveHeadersEnd` | Time to receive response headers |

!!! tip "Time to First Byte (TTFB)"
    TTFB is the "Wait" phase - the time between sending the request and receiving the first byte of the response. This is crucial for performance analysis.

## Best Practices

### 1. Enable Network Events Only When Needed

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_enable():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # ✅ Good: Enable before navigation, disable after
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        logs = await tab.get_network_logs()
        await tab.disable_network_events()
        
        # ❌ Bad: Leaving it enabled throughout entire session
        # await tab.enable_network_events()
        # ... long automation session ...
```

### 2. Filter Logs to Reduce Memory Usage

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_filter():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # ✅ Good: Filter for specific requests
        api_logs = await tab.get_network_logs(filter='/api/')
        
        # ❌ Bad: Getting all logs when you only need specific ones
        all_logs = await tab.get_network_logs()
        filtered = [log for log in all_logs if '/api/' in log['params']['request']['url']]
```

### 3. Handle Missing Fields Safely

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_safe_access():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        logs = await tab.get_network_logs()
        
        # ✅ Good: Safe access with .get()
        for log in logs:
            params = log.get('params', {})
            request = params.get('request', {})
            url = request.get('url', 'Unknown')
            post_data = request.get('postData')  # May be None
            
            if post_data:
                print(f"POST data: {post_data}")
        
        # ❌ Bad: Direct access can raise KeyError
        # url = log['params']['request']['url']
        # post_data = log['params']['request']['postData']  # May not exist!
```

### 4. Use Event Callbacks for Real-Time Needs

```python
import asyncio
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

# ✅ Good: Real-time monitoring with callbacks
async def on_request(event: RequestWillBeSentEvent):
    print(f"New request: {event['params']['request']['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# ❌ Bad: Polling logs repeatedly (inefficient)
while True:
    logs = await tab.get_network_logs()
    # Process logs...
    await asyncio.sleep(0.5)  # Wasteful!
```

## See Also

- **[CDP Network Domain](../../deep-dive/network-capabilities.md)** - Deep dive into network capabilities
- **[Event System](../advanced/event-system.md)** - Understanding Pydoll's event architecture
- **[Request Interception](interception.md)** - Modifying requests and responses

