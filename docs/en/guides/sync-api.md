# Synchronous API

## Introduction

`pydoll.sync` is Pydoll without `async` and `await`. Every class mirrors its asynchronous counterpart method for method: `Chrome`, `Tab`, `WebElement`, `ShadowRoot`, `Keyboard`, `Mouse`, `Scroll`, `Request` and `Response`. Use it in scripts, notebooks and codebases that don't run an event loop of their own. You don't write a wrapper or manage a loop; each call blocks until the browser answers.

**You will learn**

- [How to drive a browser without asyncio](#drive-a-browser)
- [How events and callbacks behave](#react-to-events)
- [How the sync API is built and what it costs](#how-it-works)

## Drive a browser

Import from `pydoll.sync` instead of `pydoll.browser.chromium`, drop `async`/`await`, and use `with` instead of `async with`:

```python
from pydoll.sync import Chrome

with Chrome() as browser:
    tab = browser.start()
    tab.go_to('https://quotes.toscrape.com/login')

    tab.find(id='username').type_text('tester')
    tab.find(id='password').type_text('secret')
    tab.find(tag_name='input', type='submit').click()

    logout = tab.find(text='Logout', timeout=5)
    print(logout.text)
    print(tab.title)
```

Properties that are awaited in the async API (`tab.title`, `element.text`) are plain properties here. Context managers such as `tab.expect_download()` become `with` blocks:

```python
with tab.expect_download(keep_file_at='downloads') as download:
    tab.find(text='Export').click()
print(download.file_path)
```

Options, constants and exceptions are shared with the async API, so `ChromiumOptions`, `Key` and `ElementNotFound` come from the same modules as before.

## React to events

Callbacks work the same way as in the async API. A callback runs on a dedicated dispatch thread, so it can call any sync method itself:

```python
from pydoll.protocol.page.events import PageEvent

def on_load(event):
    print('loaded:', tab.title)

tab.enable_page_events()
tab.on(PageEvent.LOAD_EVENT_FIRED, on_load)
tab.go_to('https://example.com')
```

Callbacks run one at a time, in the order the events arrived. A callback that blocks for a long time delays the ones behind it, not the browser.

## How it works

The sync API is generated code. `scripts/generate_sync_api.py` reads every asynchronous class, and for each method emits a synchronous one with the same signature, docstring and type annotations. The generated facades live in `pydoll/sync/_generated.py`; a unit test fails when they drift from the async source, so the two APIs cannot disagree.

At runtime, one asyncio loop runs in a daemon thread for the whole process. A facade method schedules its coroutine on that loop and waits for the result. That is the same design Playwright uses for its own sync API, with threads in place of greenlets, and it has one practical consequence: the sync API works inside Jupyter and inside applications that already run their own event loop, because Pydoll's loop is separate.

To reach the asynchronous object behind a facade, read its `impl` attribute.

## What's next

- [Async Python in practice](../basics/async-python.md): when the async API is the better fit.
- [Events](events.md): everything you can subscribe to.
