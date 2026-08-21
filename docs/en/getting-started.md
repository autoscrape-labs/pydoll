# Getting started

Pydoll automates the Chrome or Edge you already have installed, so setup is two steps: install the package, run a script. This page takes you from an empty folder to a working script that opens a real page and reads data from it.

**You will learn**

- [How to install Pydoll](#install-pydoll)
- [How to write and run your first script](#write-your-first-script)
- [How to run without a visible browser window](#run-headless)

## Install Pydoll

Pydoll requires Python 3.10 or newer, and Google Chrome or Microsoft Edge installed on your machine. You don't need to download a webdriver; Pydoll talks to the browser directly.

Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html), then install:

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

To try the latest development version instead, install from GitHub:

```bash
pip install git+https://github.com/autoscrape-labs/pydoll.git
```

## Write your first script

Create a file called `first_script.py`:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

asyncio.run(main())
```

Run it:

```bash
python first_script.py
```

A Chrome window opens, loads the page, and your terminal prints the first quote:

```
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
```

Three things happened there:

- `async with Chrome() as browser` launched your installed Chrome and guarantees it closes when the block ends, even if the script fails.
- `browser.start()` returned a [tab](api/browser/tab.md), the object you'll use for navigation, element finding, and everything else on the page.
- `tab.find(class_name='text')` waited for the element to appear and returned it. You don't need to add sleeps or write wait loops; `find()` retries until the element shows up or the timeout expires.

!!! note "New to async Python?"
    Every Pydoll call is `await`ed inside an `async def` function, and `asyncio.run(main())` starts it. That's all the asyncio you need for now; the rest of the docs follow this same shape.

## Run headless

On a server or in CI there is no display, so run the browser headless. Pass options when creating the browser:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--headless=new')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

asyncio.run(main())
```

The script behaves exactly the same; the window is invisible. `ChromiumOptions` accepts any Chromium command-line argument. See [Browser options](guides/browser-options.md) for the ones worth knowing.

!!! warning "Headless is detectable"
    Headless Chrome leaks more than a user agent string. It renders WebGL through a software rasterizer instead of your real GPU, exposes no PDF plugins, reports screen metrics with no taskbar gap, and is missing media devices. Anti-bot systems check all of these, so setting a user agent alone does not make a headless browser pass as headful, not by a wide margin. If you automate sites that fight bots, either run headful, or neutralize the headless signals with [Fingerprint injection](stealth/fingerprint-injection.md).

## What's next

- [Your first automation](first-automation.md): log in to a site, interact like a person, and extract typed data.
- [Staying undetected](stealth/index.md): the minimum setup to avoid the obvious bot signals.
- [Element finding](guides/element-finding.md): every way to locate elements with `find()` and `query()`.
