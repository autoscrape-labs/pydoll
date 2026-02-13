# HAR Network Recording

Capture all network activity during a browser session and export it as a standard HAR (HTTP Archive) 1.2 file. Perfect for debugging, performance analysis, and request replay.

!!! tip "Debug Like a Pro"
    HAR files are the industry standard for recording network traffic. You can import them directly into Chrome DevTools, Charles Proxy, or any HAR viewer for detailed analysis.

## Why Use HAR Recording?

| Use Case | Benefit |
|----------|---------|
| Debugging failed requests | See exact headers, timing, and response bodies |
| Performance analysis | Identify slow requests and bottlenecks |
| Request replay | Reproduce exact request sequences |
| API documentation | Capture real request/response pairs |
| Test fixtures | Record real traffic for test mocking |

## Quick Start

Record all network traffic during a page navigation:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def record_traffic():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as recording:
            await tab.go_to('https://example.com')

        # Save the recording as a HAR file
        recording.save('flow.har')
        print(f'Captured {len(recording.entries)} requests')

asyncio.run(record_traffic())
```

## Recording API

### `tab.request.record()`

Context manager that captures all network traffic on the tab.

```python
async with tab.request.record() as recording:
    # All network activity inside this block is captured
    await tab.go_to('https://example.com')
    await (await tab.find(id='search')).type_text('pydoll')
    await (await tab.find(type='submit')).click()
```

The `recording` object provides:

| Property/Method | Description |
|----------------|-------------|
| `recording.entries` | List of captured HAR entries |
| `recording.to_dict()` | Full HAR 1.2 dict (for custom processing) |
| `recording.save(path)` | Save as HAR JSON file |

### Saving Recordings

```python
# Save as HAR file (can be opened in Chrome DevTools)
recording.save('flow.har')

# Save to a nested directory (created automatically)
recording.save('recordings/session1/flow.har')

# Access the raw HAR dict for custom processing
har_dict = recording.to_dict()
print(har_dict['log']['version'])  # "1.2"
```

### Inspecting Entries

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

for entry in recording.entries:
    req = entry['request']
    resp = entry['response']
    print(f"{req['method']} {req['url']} -> {resp['status']}")
```

## Replaying Requests

Replay a previously recorded HAR file, executing each request sequentially through the browser:

```python
async def replay_traffic():
    async with Chrome() as browser:
        tab = await browser.start()

        # Navigate to set up session context
        await tab.go_to('https://example.com')

        # Replay all recorded requests
        responses = await tab.request.replay('flow.har')

        for resp in responses:
            print(f"Status: {resp.status_code}")

asyncio.run(replay_traffic())
```

### `tab.request.replay(path)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Path to the HAR file to replay |

**Returns:** `list[Response]` -- responses from each replayed request.

**Raises:** `HarReplayError` -- if the HAR file is invalid or unreadable.

## Advanced Usage

### Record and Replay Workflow

```python
async def record_and_replay():
    async with Chrome() as browser:
        tab = await browser.start()

        # Step 1: Record the original session
        async with tab.request.record() as recording:
            await tab.go_to('https://api.example.com')
            await tab.request.post(
                'https://api.example.com/data',
                json={'key': 'value'}
            )

        recording.save('api_session.har')

        # Step 2: Replay later
        responses = await tab.request.replay('api_session.har')
```

### Filtering Recorded Entries

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

# Filter only API calls
api_entries = [
    e for e in recording.entries
    if '/api/' in e['request']['url']
]

# Filter only failed requests
failed = [
    e for e in recording.entries
    if e['response']['status'] >= 400
]
```

### Custom HAR Processing

```python
har = recording.to_dict()

# Count requests by type
from collections import Counter
types = Counter(
    e.get('_resourceType', 'Other')
    for e in har['log']['entries']
)
print(types)  # Counter({'Document': 1, 'Script': 5, 'Stylesheet': 3, ...})
```

## HAR File Format

The exported HAR follows the [HAR 1.2 specification](http://www.softwareishard.com/blog/har-12-spec/). Each entry contains:

- **Request**: method, URL, headers, query parameters, POST data
- **Response**: status, headers, body content (text or base64-encoded)
- **Timings**: DNS, connect, SSL, send, wait (TTFB), receive
- **Metadata**: server IP, connection ID, resource type

!!! note "Response Bodies"
    Response bodies are captured automatically after each request completes. Binary content (images, fonts, etc.) is stored as base64-encoded strings.
