# Remote connections

`browser.connect()` attaches Pydoll to a Chrome that is already running, instead of launching one. Use it to drive a browser you did not start: one in a container, on a remote host, or a long-lived instance shared between runs. You get the same `Tab` API as a browser you launched.

## Start Chrome with a debugging port

The target browser has to expose the Chrome DevTools Protocol. Start it with `--remote-debugging-port`:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-remote
```

That serves a small JSON API on the port. Ask it for the browser's WebSocket address:

```bash
curl http://localhost:9222/json/version
```

The `webSocketDebuggerUrl` field in the response (something like `ws://localhost:9222/devtools/browser/<id>`) is what you pass to Pydoll.

## Connect and drive the tab

Create a browser object, call `connect()` with the WebSocket address, and use the returned tab like any other:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    browser = Chrome()
    tab = await browser.connect('ws://localhost:9222/devtools/browser/<id>')

    print(await tab.title)

    await tab.go_to('https://news.ycombinator.com')
    headline = await tab.find(class_name='titleline')
    print(await headline.text)

    await browser.close()

asyncio.run(main())
```

`connect()` returns the first open tab. Reach the others with `await browser.get_opened_tabs()`, exactly as when you launch the browser yourself. See [Tabs](tabs.md).

!!! warning "Disconnect with `close()`, not `stop()`"
    You did not launch this browser, so do not terminate it. `await browser.close()` closes only Pydoll's WebSocket connection and leaves the browser running for whatever else uses it. `await browser.stop()` sends the browser a close command and kills the process, which is what you want for a browser you started, not one you attached to.

## Fetch the WebSocket address in code

You usually discover the address at runtime rather than hardcoding it. Query the JSON endpoint with any HTTP client:

```python
import asyncio

import aiohttp
from pydoll.browser.chromium import Chrome


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:9222/json/version') as resp:
            ws_address = (await resp.json())['webSocketDebuggerUrl']

    browser = Chrome()
    tab = await browser.connect(ws_address)
    print(await tab.title)
    await browser.close()

asyncio.run(main())
```

For a browser on another machine, replace `localhost` with the server's address and query `http://<host>:9222/json/version` from the client.

## Run Chrome in a container

In Docker, start Chrome headless with the debugging port bound and a large enough shared-memory segment (Chrome uses `/dev/shm`, and Docker's 64MB default is too small):

```bash
docker run -d --shm-size=2g -p 127.0.0.1:9222:9222 \
  zenika/alpine-chrome \
  --no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222
```

Then connect from the host with `browser.connect('ws://localhost:9222/devtools/browser/<id>')`. `--remote-debugging-address=0.0.0.0` lets connections in from outside the container; `--no-sandbox` is needed in most containers.

!!! warning "Never expose the debugging port to the internet"
    A reachable debugging port is full control of the browser: every page, cookie, and session, plus arbitrary JavaScript. Bind it to localhost (as `-p 127.0.0.1:9222:9222` does) and reach a remote one through an SSH tunnel (`ssh -L 9222:localhost:9222 user@host`) or a private network, never a public interface.

## Wrap an element from your own CDP tooling

If you already have a CDP integration and an element's `objectId`, wrap it in a Pydoll `WebElement` to use the high-level interaction API. Build a `ConnectionHandler` for the page's WebSocket and pass it in:

```python
from pydoll.connection import ConnectionHandler
from pydoll.elements.web_element import WebElement

connection = ConnectionHandler(ws_address='ws://localhost:9222/devtools/page/<id>')

button = WebElement(
    object_id='<objectId from your CDP call>',
    connection_handler=connection,
)

await button.wait_until(is_visible=True, timeout=5)
await button.click(x_offset=5, y_offset=5)

await connection.close()
```

The `objectId` is what CDP commands like `Runtime.evaluate` or `DOM.resolveNode` return for a node. This keeps your existing setup and borrows Pydoll's waits and interactions on top.

## What's next

- [Tabs](tabs.md): drive the tabs the remote browser already has open.
- [Browser options](browser-options.md): configure a browser you launch yourself instead of attaching to one.
- [Network monitoring](network-monitoring.md): watch traffic on the browser you connected to.
