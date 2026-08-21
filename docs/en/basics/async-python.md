# Async Python in practice

Every Pydoll call has `await` in front of it. If that keyword is new to you, this page is the one to read first. You don't need to master asyncio; you need just enough to be comfortable, and to see why Pydoll is built on it. Each example here runs on its own, so paste them into a file and watch what happens.

## Why every Pydoll call is awaited

Browser automation spends most of its time waiting: for a page to load, for an element to appear, for a network request to come back. Regular Python code sits idle during those waits. Async code doesn't: while one task waits, another can run.

That single idea is what makes Pydoll's headline features possible:

- Driving many tabs or browsers **at the same time** instead of one after another.
- Watching **network traffic** while your script keeps working.
- Running **callbacks** the moment a page event fires.

None of that needs threads. It all comes from `async` and `await`, so it is worth ten minutes to get the shape.

## The shape: `async def`, `await`, `asyncio.run`

Three pieces show up in every Pydoll script:

```python
import asyncio


async def main():          # 1. an async function, called a coroutine
    print('hello')
    await asyncio.sleep(1)  # 2. await pauses here for 1 second
    print('one second later')


asyncio.run(main())         # 3. asyncio.run starts it
```

- `async def` defines a **coroutine**: a function that can pause and resume.
- `await` is where it pauses. You can only use `await` inside an `async def`.
- `asyncio.run()` is the entry point that actually runs the coroutine. It is the one call that is *not* awaited, because it starts everything.

Calling `main()` on its own does nothing useful; it only creates a coroutine object. `asyncio.run(main())` is what makes it go.

## `await` means "wait here, but let other work run"

`await asyncio.sleep(1)` does not freeze your whole program for a second. It pauses *this* coroutine and hands control back, so anything else that is ready can run during that second. That handoff is the entire trick, and the next section shows why it matters.

## Doing things at the same time

Imagine two chores that are mostly waiting: boiling water and toasting bread, two minutes each.

Do them one after another and you wait for both in sequence:

```python
import asyncio
import time


async def boil_water():
    print('kettle on')
    await asyncio.sleep(2)
    print('water boiled')


async def toast_bread():
    print('bread in')
    await asyncio.sleep(2)
    print('toast ready')


async def main():
    start = time.perf_counter()
    await boil_water()
    await toast_bread()
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

Run it and you get about **4 seconds**, because you awaited one chore fully before starting the next.

Now start both, then wait for both together with `asyncio.gather`:

```python
async def main():
    start = time.perf_counter()
    await asyncio.gather(boil_water(), toast_bread())
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

This time it is about **2 seconds**. The two waits overlap. The kettle boils while the bread toasts.

<iframe src="../async-flow.html" aria-label="Sequential vs concurrent async, animated" style="width: 100%; height: 285px; border: 0;" loading="lazy"></iframe>

Run each mode and watch the timer: sequential finishes at 4.0s, concurrent at 2.0s, because the two waits overlap.

`asyncio.gather(*coroutines)` runs everything you pass it concurrently and returns their results in order once all are done.

## The same idea, with Pydoll

Swap the chores for real pages and nothing changes. Loading three pages one at a time waits three times over; loading them with `gather` overlaps the waits.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def title_of(browser, url):
    tab = await browser.new_tab(url)
    title = await tab.title
    await tab.close()
    return title


async def main():
    urls = [
        'https://en.wikipedia.org/wiki/Async/await',
        'https://en.wikipedia.org/wiki/Coroutine',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    async with Chrome() as browser:
        await browser.start()
        titles = await asyncio.gather(*(title_of(browser, url) for url in urls))
        for title in titles:
            print(title)


asyncio.run(main())
```

The three pages load concurrently, so the whole thing takes about as long as the slowest single page.

## Two errors you'll probably hit

These are the normal stumbles when async is new. They are quick to recognize once you've seen them.

**You forgot `await`.** Without it, you get the coroutine object instead of its result, and a warning:

```python
title = tab.title
print(title)   # <coroutine object ...>, and: RuntimeWarning: coroutine was never awaited
```

The fix is to add `await`: `title = await tab.title`.

**You called async code without starting the loop.** `await` only works inside an `async def`, and coroutines only run under `asyncio.run()` (or another running loop):

```python
main()   # nothing happens; this just creates a coroutine
```

The fix is `asyncio.run(main())`.

## Where async pays off in Pydoll

Once the shape is comfortable, these features are `gather` and callbacks at work:

- **Parallel automation:** drive many tabs or browsers at once with `gather`. See [Tabs](../guides/tabs.md).
- **Network interception:** watch and modify requests while your script keeps going. See [Network monitoring](../guides/network-monitoring.md).
- **Event callbacks:** run a function the moment a page or network event fires. See [Events](../guides/events.md).

## What's next

- [Installation](../getting-started.md): install Pydoll and run your first script.
- [Core concepts](../guides/core-concepts.md): how the browser and tab objects fit together.
- [Selectors: CSS and XPath](selectors.md): the other prerequisite, choosing and writing selectors.
