# HAR network recording

Record every request a page makes during a session and export it as a HAR file, the standard HTTP Archive format. A HAR file captures each request and response with headers, bodies, and timings, and opens in Chrome DevTools or any HAR viewer. Use it for debugging, performance analysis, or as a fixture for tests.

## Record a session

Wrap the browsing you want to capture in `tab.request.record()`. Everything the page requests inside the block is recorded, and the `capture` object is ready once the block exits.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as capture:
            await tab.go_to('https://news.ycombinator.com')

        print(f'captured {len(capture.entries)} requests')

asyncio.run(main())
```

## Save the recording

`capture.save()` writes a `.har` file. Open it in Chrome DevTools (Network tab, import) or any HAR viewer to inspect the traffic visually. Missing directories are created for you.

```python
capture.save('flow.har')
capture.save('recordings/session-1/flow.har')
```

## Inspect entries in code

`capture.entries` is a list of HAR entries. Each entry has a `request` and a `response` you can read directly, which is handy for asserting on traffic in a test or pulling out specific calls.

```python
async with tab.request.record() as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')

for entry in capture.entries:
    request = entry['request']
    response = entry['response']
    print(f"{request['method']} {request['url']} -> {response['status']}")

# keep only the API calls that failed
failed_api = [
    entry for entry in capture.entries
    if '/api/' in entry['request']['url'] and entry['response']['status'] >= 400
]
```

## Record only some resource types

Recording every image, font, and stylesheet produces a large file. Pass `resource_types` to keep only the kinds you care about, which is the usual way to capture just a page's API traffic.

```python
from pydoll.protocol.network.types import ResourceType

# only the fetch/XHR calls, skipping documents, images, and styles
async with tab.request.record(
    resource_types=[ResourceType.FETCH, ResourceType.XHR]
) as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')
```

The common `ResourceType` values are `DOCUMENT`, `STYLESHEET`, `SCRIPT`, `IMAGE`, `FONT`, `MEDIA`, `FETCH`, `XHR`, and `WEB_SOCKET`. See the `ResourceType` enum in `pydoll.protocol.network.types` for the full list.

## Get the raw HAR dict

`capture.to_dict()` returns the full HAR 1.2 structure, so you can process it yourself or hand it to another tool instead of writing a file.

```python
har = capture.to_dict()
print(har['log']['version'])  # '1.2'

from collections import Counter

by_type = Counter(entry.get('_resourceType', 'Other') for entry in har['log']['entries'])
print(by_type)  # Counter({'Script': 5, 'Stylesheet': 3, 'Document': 1, ...})
```

!!! note "Response bodies"
    Response bodies are captured after each request finishes. Binary content such as images and fonts is stored base64-encoded, following the HAR spec.

## What's next

- [Network monitoring](network-monitoring.md): watch requests and read responses live, without recording a file.
- [Request interception](request-interception.md): pause, modify, block, or mock requests as they happen.
- [Browser-context HTTP requests](http-requests.md): make authenticated requests through the page's own session.
