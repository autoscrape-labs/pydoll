# Network monitoring

Pydoll lets you watch every request a page makes, read response bodies, and inspect status and timing, all from the browser itself. There is no proxy to set up and no certificate to install; you enable the network domain and the traffic comes to you.

This guide is about observing traffic. To change, block, or fake requests, see [Request interception](request-interception.md).

## Watch requests as they happen

Enable network events before you navigate, then register a callback. Pydoll calls it for every request the page starts.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_request(tab, event):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, partial(on_request, tab))

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

Enable the domain **before** navigating; requests made before it is enabled are not captured.

<iframe src="../request-waterfall.html" aria-label="A request waterfall showing each request's start and duration as the page loads" style="width: 100%; height: 375px; border: 0;" loading="lazy"></iframe>

Press Load: each request appears as a bar placed by when it starts and how wide by how long it takes, which is what the network events report as they fire.

## Read a response body

The response body is not in the event; you fetch it by request id once the response has arrived. Match the request you care about, then call `get_network_response_body`.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)

        for log in await tab.get_network_logs():
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            if url.endswith('/json'):
                body = await tab.get_network_response_body(request_id)
                print(body)

asyncio.run(main())
```

!!! note "Bodies exist only after the response arrives"
    A body is available once the request has completed. Redirects and some resource types (images, for instance) may have no readable body, so wrap the call in a `try`/`except` when you loop over many requests.

## Get the logs after navigating

If you don't need real-time callbacks, let Pydoll collect the requests and read them afterward with `get_network_logs`. Pass `filter` to keep only URLs containing a substring.

```python
await tab.go_to('https://github.com')
await asyncio.sleep(3)

all_requests = await tab.get_network_logs()
api_requests = await tab.get_network_logs(filter='api.github.com')

print(f'{len(all_requests)} requests, {len(api_requests)} to the API')

for log in api_requests:
    print(log['params']['request']['url'])
```

## React to responses and failures

Subscribe to responses to check status codes, and to failures to catch requests that never completed. The response URL and status live under `event['params']['response']`; a failure's reason is in `event['params']['errorText']`.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_response(event):
    response = event['params']['response']
    print(f"{response['status']} {response['url']}")


async def on_failed(event):
    print(f"failed: {event['params']['errorText']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

## Enable only while you need it

Network events add overhead on busy pages, so enable them around the part of your automation that needs them and disable them afterward:

```python
await tab.enable_network_events()
await tab.go_to('https://github.com')
await asyncio.sleep(3)
logs = await tab.get_network_logs()
await tab.disable_network_events()
```

## What's next

- [Request interception](request-interception.md): change, block, or fulfill requests instead of only watching them.
- [Events](events.md): the general enable, subscribe, and callback model behind network events.
- [Browser-context HTTP requests](http-requests.md): call APIs directly from the page's session.
