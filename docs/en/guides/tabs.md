# Tabs

A tab is the object you drive: navigation, element finding, and everything on a page happens through it. A browser can hold many tabs at once, and because Pydoll is async, you can drive them concurrently instead of one at a time.

## Open and close tabs

`browser.start()` gives you the first tab. `browser.new_tab()` opens more, and `tab.close()` closes one. The browser itself closes when the `async with` block ends, taking every tab with it.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

        # open another tab, already navigated
        docs = await browser.new_tab('https://en.wikipedia.org/wiki/Web_scraping')
        print(await docs.title)

        await docs.close()

asyncio.run(main())
```

Pass a URL to `new_tab(url)` and the tab navigates there before returning. Call `new_tab()` with no argument for a blank tab you navigate later.

## Scrape several pages at once

This is the payoff of the async design: give each page its own tab and run them through `asyncio.gather`, so their load times overlap instead of adding up. Reuse the tab from `start()` as the first worker rather than leaving it idle.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def title_of(tab, url):
    await tab.go_to(url)
    return await tab.title


async def main():
    urls = [
        'https://en.wikipedia.org/wiki/Async/await',
        'https://en.wikipedia.org/wiki/Coroutine',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    async with Chrome() as browser:
        first = await browser.start()
        tabs = [first] + [await browser.new_tab() for _ in urls[1:]]

        titles = await asyncio.gather(*(title_of(tab, url) for tab, url in zip(tabs, urls)))
        for title in titles:
            print(title)

asyncio.run(main())
```

The three pages load concurrently, so the run takes about as long as the slowest single page. See [Async Python in practice](../basics/async-python.md) for how `gather` works.

## List the open tabs

`browser.get_opened_tabs()` returns every open tab. The last item is the most recently opened.

```python
async with Chrome() as browser:
    await browser.start()
    await browser.new_tab('https://github.com')
    await browser.new_tab('https://news.ycombinator.com')

    tabs = await browser.get_opened_tabs()
    for tab in tabs:
        print(await tab.current_url)
```

## Handle a tab the page opened

When a click opens a tab (a link with `target="_blank"`), it shows up in `get_opened_tabs()`. Compare the list before and after the click, and the new tab is the last one.

```python
before = len(await browser.get_opened_tabs())

link = await tab.find(text='Open in new tab')
await link.click()

tabs = await browser.get_opened_tabs()
if len(tabs) > before:
    new_tab = tabs[-1]
    print(await new_tab.current_url)
```

## Bring a tab to the front

Automation drives background tabs fine, but some pages only run timers or animations while visible. `bring_to_front()` makes a tab the active one.

```python
await background_tab.bring_to_front()
```

## What's next

- [Browser contexts](browser-contexts.md): give tabs isolated cookies and sessions.
- [Cookies and sessions](cookies-and-sessions.md): carry a login across tabs.
- [Async Python in practice](../basics/async-python.md): the `gather` pattern behind concurrent tabs.
