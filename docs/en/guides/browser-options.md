# Browser options

`ChromiumOptions` is the object you configure before launching the browser. It holds the command-line flags, the browser binary to run, timeouts, and a handful of convenience settings. You build one, pass it to `Chrome` or `Edge`, and start.

## Configure and launch

Create a `ChromiumOptions`, set what you need, and hand it to the browser:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.headless = True
    options.add_argument('--window-size=1920,1080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

asyncio.run(main())
```

The same options object works for Edge; import `Edge` instead of `Chrome`.

## Add command-line flags

Chromium takes hundreds of command-line switches. Use `add_argument()` to pass any of them, `remove_argument()` to take one back, and `arguments` to read the current list.

```python
options = ChromiumOptions()

options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')

options.remove_argument('--start-maximized')
print(options.arguments)
```

The full switch list is Peter Beverloo's [Chromium command-line switches](https://peter.sh/experiments/chromium-command-line-switches/). A few that come up often: `--window-size=W,H` for a fixed viewport, `--disable-gpu` on machines without a GPU, and the Docker pair below.

!!! note "Do not set the debugging port yourself"
    Pydoll manages `--remote-debugging-port` internally. Passing your own `--remote-debugging-port` conflicts with it.

## Run headless

Set `headless` to run without a visible window, which is what you want on a server or in CI:

```python
options = ChromiumOptions()
options.headless = True   # adds the --headless flag
```

!!! warning "Headless is detectable"
    Headless Chrome leaks more than a flag: it renders WebGL through a software rasterizer, exposes no PDF plugins, and reports different screen metrics. Anti-bot systems check all of these. Setting a user agent does not hide it. If you automate sites that fight bots, either run headful or neutralize the headless signals with [Fingerprint injection](../stealth/fingerprint-injection.md).

## Use a different browser build

Point `binary_location` at any Chromium build (Beta, Canary, Chromium, Brave) instead of the system default:

```python
options = ChromiumOptions()
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
```

## Wait longer for startup

`start_timeout` is how many seconds Pydoll waits for the browser to come up before giving up. Raise it on slow machines or heavy profiles:

```python
options = ChromiumOptions()
options.start_timeout = 20   # seconds, default 10
```

## Choose when navigation finishes

`page_load_state` decides when `tab.go_to()` returns. `COMPLETE` (the default) waits for every resource; `INTERACTIVE` returns as soon as the DOM is ready, which is faster when you only read text or markup.

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE
```

The three states are `PageLoadState.COMPLETE`, `PageLoadState.INTERACTIVE`, and `PageLoadState.LOADING`.

## Set the download folder and languages

Two helpers cover the most common preferences without touching the raw preference dict:

```python
options = ChromiumOptions()
options.set_default_download_directory('/home/user/downloads')
options.set_accept_languages('en-US,en;q=0.9')
```

For anything deeper in Chromium's preferences, see [Browser preferences](browser-preferences.md).

## Quiet the browser

A set of boolean properties toggle the interruptions that get in the way of automation:

```python
options = ChromiumOptions()
options.block_popups = True
options.block_notifications = True
options.password_manager_enabled = False
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True   # download PDFs instead of opening the viewer
```

## Protect against WebRTC IP leaks

WebRTC can reveal your real IP even behind a proxy. `webrtc_leak_protection` adds the flag that blocks non-proxied UDP:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
```

Reach for this when you route traffic through a [proxy](proxies.md).

## Run in Docker or CI

Containers need two flags: `--no-sandbox` (the sandbox clashes with container isolation) and `--disable-dev-shm-usage` (containers often have a tiny `/dev/shm`).

```python
options = ChromiumOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

!!! warning "`--no-sandbox` lowers Chrome's security"
    Only use it in a controlled environment (a container, a CI runner) where you trust the pages you load. Do not use it when visiting untrusted sites.

## What's next

- [Browser preferences](browser-preferences.md): the deeper Chromium preference dictionary.
- [Proxies](proxies.md): route the browser's traffic through a proxy.
- [Fingerprint injection](../stealth/fingerprint-injection.md): make headless pass as headful, and keep the browser identity consistent.
