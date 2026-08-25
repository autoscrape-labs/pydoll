# Events

Events let you react to what the browser does, as it happens: a page finishing loading, a request going out, a response coming back, a dialog opening. Instead of polling in a loop and guessing, you register a callback and Pydoll runs it the moment the event fires.

## Enable, then listen

Working with events is always the same three steps: enable the domain you care about, register a callback with `on()`, then let the events fire. A callback that is registered before its domain is enabled never runs, so enable first.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.page.events import PageEvent


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async def on_load(event):
            print('page finished loading')

        await tab.enable_page_events()
        await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(2)

asyncio.run(main())
```

`on(event_name, callback)` returns an integer id you can use later to remove the callback. The callback can be sync or async, and it receives one argument: the event.

<iframe scrolling="no" src="/docs/resources/visuals/events-flow.html" aria-label="Events firing on a page and your callbacks running" style="width: 100%; height: 395px; border: 0;" loading="lazy"></iframe>

Press Navigate: events fire on the page in order, and the callbacks you registered run as their event fires.

## Read the event data

Every event is a dict with a `method` name and a `params` payload. You read what you need out of `event['params']`:

```python
{
    'method': 'Page.loadEventFired',
    'params': {'timestamp': 123456.789},
}
```

Each event type is a `TypedDict` under `pydoll.protocol.<domain>.events`, so type-hinting a callback gives you autocomplete on the `params` keys:

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent


async def on_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")
```

The examples below assume a running `tab`, as set up in the first example.

## Watch network requests and responses

Enable the network domain to see every request go out and every response come back:

```python
from pydoll.protocol.network.events import NetworkEvent


async def on_request(event):
    print(f"→ {event['params']['request']['url']}")


async def on_response(event):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")


await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)

await tab.go_to('https://news.ycombinator.com')
```

To modify or block requests rather than just watch them, see [Request interception](request-interception.md).

## Run a listener once

Pass `temporary=True` and the callback removes itself after it fires the first time. This is what you want for one-off setup that should not repeat on every later load:

```python
from pydoll.protocol.page.events import PageEvent

await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load, temporary=True)

await tab.go_to('https://the-internet.herokuapp.com')  # fires once
await tab.refresh()                                      # does not fire again
```

## Wait for a specific event

Events pair naturally with `asyncio.Event` when you need to pause until something happens. Register a temporary listener that sets the flag, trigger the action, then await the flag:

```python
import asyncio

from pydoll.protocol.page.events import PageEvent


async def click_and_wait_for_navigation(tab):
    navigated = asyncio.Event()

    async def on_navigated(event):
        navigated.set()

    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)

    link = await tab.find(text='Form Authentication')
    await link.click()

    await navigated.wait()
    print('navigation finished')
```

## Use the tab inside a callback

`on()` only passes the event to your callback. To use the tab as well (for example, to read a response body), bind it with `functools.partial`:

```python
from functools import partial

from pydoll.protocol.network.events import NetworkEvent


async def capture_json(tab, event):
    url = event['params']['response']['url']
    if '/api/' not in url:
        return
    request_id = event['params']['requestId']
    body = await tab.get_network_response_body(request_id)
    print(f'{url}: {body[:80]}')


await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_json, tab))
```

Filter early, as above: return as soon as the event is not one you care about, so the expensive work only runs when it should.

## Handle JavaScript dialogs

Subscribe to dialog events to answer `alert`, `confirm`, and `prompt` boxes automatically instead of letting them block the page:

```python
from pydoll.protocol.page.events import PageEvent


async def on_dialog(event):
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)


await tab.enable_page_events()
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, on_dialog)
await tab.go_to('https://the-internet.herokuapp.com/javascript_alerts')
```

## Clean up when you are done

Keep listeners scoped to the work that needs them. Remove a single callback by its id, or clear them all, and disable a domain once you are finished with it:

```python
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# ... do the work that needs it ...

await tab.remove_callback(callback_id)   # remove one
await tab.clear_callbacks()              # or remove every callback on the tab
await tab.disable_network_events()       # stop the domain
```

Enable only the domains you use. DOM events in particular fire very often on dynamic pages, so subscribe to them only while you need them, and keep callbacks fast; offload heavy work to a separate task with `asyncio.create_task` so it does not hold up the next event.

## Event domains and key events

| Domain | Enable with | Reach for it to |
|---|---|---|
| Page | `enable_page_events()` | react to loads, navigation, and dialogs |
| Network | `enable_network_events()` | watch requests and responses |
| Fetch | `enable_fetch_events()` | intercept and modify requests |
| DOM | `enable_dom_events()` | react to DOM changes |
| Runtime | `enable_runtime_events()` | read console messages and exceptions |

Common event constants (each domain has more in `pydoll.protocol.<domain>.events`):

| Constant | Fires when |
|---|---|
| `PageEvent.LOAD_EVENT_FIRED` | the page finishes loading |
| `PageEvent.DOM_CONTENT_EVENT_FIRED` | the DOM is ready |
| `PageEvent.FRAME_NAVIGATED` | a navigation completes |
| `PageEvent.JAVASCRIPT_DIALOG_OPENING` | an alert, confirm, or prompt opens |
| `NetworkEvent.REQUEST_WILL_BE_SENT` | a request is about to go out |
| `NetworkEvent.RESPONSE_RECEIVED` | response headers arrive |
| `NetworkEvent.LOADING_FINISHED` | the response body is fully loaded |

## What's next

- [Network monitoring](network-monitoring.md): capture and analyze traffic with these events.
- [Request interception](request-interception.md): pause, modify, and block requests, not just observe them.
- [Retrying](retrying.md): retry flaky actions with the `@retry` decorator.
