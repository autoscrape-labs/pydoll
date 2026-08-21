# Request interception

Interception lets you sit between the browser and the network. Every matching request pauses at your handler, where you decide to let it through (as-is or modified), block it, or answer it yourself with a mock response. Use it to drop images for speed, inject headers, or fake an API while you build against it.

This is the active counterpart to [Network monitoring](network-monitoring.md), which only observes traffic. Interception can change it.

<iframe src="/docs/resources/visuals/request-lifecycle.html" aria-label="What happens to an intercepted request under continue, block, or fulfill" style="width: 100%; height: 400px; border: 0;" loading="lazy"></iframe>

Try each button: `continue_request()` lets it reach the server, `fail_request()` drops it, and `fulfill_request()` answers from your handler without ever contacting the server.

## Enable interception

Interception runs on Chrome's Fetch domain. Enable it, register a handler for the paused-request event, and resolve every request the handler receives.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def on_request(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    print(f'paused: {url}')
    await tab.continue_request(request_id)   # let it through unchanged


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(on_request, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! warning "Resolve every paused request, exactly once"
    A paused request holds the page until you act on it. Each one must end in exactly one of `continue_request`, `fail_request`, or `fulfill_request`. Miss one and that request hangs until it times out; call two and you get an error. Wrap risky handler logic in `try`/`except` and continue the request in the `except` branch so a bug never freezes the page.

## Intercept only the requests you want

Interception adds a round-trip through your handler for every matching request, so narrow it down. Pass a `resource_type` to pause just one kind of request, and read `event['params']['resourceType']` in the handler to branch further.

```python
from pydoll.protocol.network.types import ResourceType

# pause only XHR/fetch calls, not documents, images, or styles
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
```

`ResourceType` covers `DOCUMENT`, `STYLESHEET`, `IMAGE`, `MEDIA`, `FONT`, `SCRIPT`, `XHR`, `FETCH`, and more; see the `ResourceType` enum in `pydoll.protocol.network.types` for the full set.

## Block requests

`fail_request` drops a request with an error reason. Blocking images and stylesheets is a common way to make scraping faster and lighter.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ErrorReason


async def block_heavy(tab, event):
    request_id = event['params']['requestId']
    resource_type = event['params']['resourceType']

    if resource_type in ('Image', 'Stylesheet', 'Font'):
        await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(block_heavy, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

Common `ErrorReason` values are `BLOCKED_BY_CLIENT` (looks like an ad blocker), `FAILED`, `ABORTED`, `TIMED_OUT`, and `CONNECTION_REFUSED`, useful for testing how a page handles network failures. The full list is the `ErrorReason` enum in `pydoll.protocol.network.types`.

## Modify a request

`continue_request` can rewrite the request before it goes out: change the URL, method, headers, or body. Headers are a list of `HeaderEntry` dicts (`{'name': ..., 'value': ...}`).

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ResourceType


async def add_header(tab, event):
    request_id = event['params']['requestId']
    headers = [
        {'name': 'X-Automated-By', 'value': 'pydoll'},
    ]
    await tab.continue_request(request_id, headers=headers)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(add_header, tab))

        await tab.go_to('https://httpbin.org/headers')  # echoes the headers it received
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "Headers you pass replace the request's headers"
    Supplying `headers` sets the full header list for that request, it does not merge with the browser's. Include the headers the request still needs, not only the one you are adding.

You can also change where a request goes by passing `url`, or replace `POST` data by passing `post_data`.

## Mock a response

`fulfill_request` answers a request yourself, so the server is never contacted. This is how you develop against an API that doesn't exist yet or force a specific payload. The `body` is base64-encoded.

```python
import asyncio
import base64
import json
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def mock_json(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']

    if url.endswith('/json'):
        payload = {'source': 'mocked by pydoll', 'items': [1, 2, 3]}
        body = base64.b64encode(json.dumps(payload).encode()).decode()
        await tab.fulfill_request(
            request_id,
            response_code=200,
            response_headers=[{'name': 'Content-Type', 'value': 'application/json'}],
            body=body,
        )
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(mock_json, tab))

        await tab.go_to('https://httpbin.org/json')  # normally returns a sample doc
        await tab.disable_fetch_events()

asyncio.run(main())
```

## Intercept the response, not just the request

By default requests pause before they are sent. Pass `request_stage=RequestStage.RESPONSE` to pause after the response arrives instead, so you can inspect or replace it. For a single request continued at the request stage, `intercept_response=True` pauses it again once its response is in.

```python
from pydoll.protocol.fetch.types import RequestStage

await tab.enable_fetch_events(request_stage=RequestStage.RESPONSE)
```

## Handle authentication challenges

With `handle_auth=True`, the browser raises an auth challenge you answer with `continue_with_auth`. This covers HTTP Basic/Digest auth (401) and proxy auth (407).

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def answer_auth(tab, event):
    request_id = event['params']['requestId']
    await tab.continue_with_auth(
        request_id,
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='passwd',
    )


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(handle_auth=True)
        await tab.on(FetchEvent.AUTH_REQUIRED, partial(answer_auth, tab))

        await tab.go_to('https://httpbin.org/basic-auth/user/passwd')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "Proxy auth is already automatic"
    You don't need this for a normal proxy. When you set proxy credentials in browser options, Pydoll answers the proxy challenge for you. Reach for manual `continue_with_auth` only for server auth or custom credential logic. See [Proxies](proxies.md).

## What's next

- [Network monitoring](network-monitoring.md): observe traffic without changing it.
- [Events](events.md): the event model that interception is built on.
- [Proxies](proxies.md): route traffic through a proxy, with authentication handled for you.
