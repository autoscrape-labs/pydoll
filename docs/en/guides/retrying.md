# Retrying

Real pages are flaky: an element loads a beat late, a navigation drops, a request times out. The `@retry` decorator re-runs a function when it raises, so a transient failure becomes a second attempt instead of a crash, and your automation code stays free of retry plumbing.

## Retry a flaky function

Decorate an async function with `@retry` and list the exceptions worth retrying. If the function raises one of them, it runs again, up to `max_retries` more times.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, ConnectionFailed


@retry(max_retries=3, exceptions=[WaitElementTimeout, ConnectionFailed])
async def scrape_title(url):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        heading = await tab.find(id='firstHeading', timeout=5)
        return await heading.text


async def main():
    title = await scrape_title('https://en.wikipedia.org/wiki/Web_scraping')
    print(title)


asyncio.run(main())
```

`max_retries` counts the retries, not the total tries: `max_retries=3` runs the function once and then up to three more times, so four attempts at most.

## Retry only the failures you expect

`@retry` defaults to `exceptions=Exception`, which retries on everything, including bugs in your own code that a second run cannot fix (a typo, a wrong selector, a `KeyError`). Name the specific exceptions instead, so genuine bugs surface immediately while only recoverable failures are retried.

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, ConnectionFailed

@retry(max_retries=3, exceptions=[ElementNotFound, WaitElementTimeout, ConnectionFailed])
async def open_dashboard(tab):
    await tab.go_to('https://app.example.test/dashboard')
    return await tab.find(id='dashboard', timeout=10)
```

The exceptions worth retrying in browser automation are the transient ones. Common choices:

- `WaitElementTimeout`, `ElementNotFound`: the element wasn't there in time.
- `ElementNotVisible`, `ElementNotInteractable`, `ClickIntercepted`: the element existed but couldn't be used yet.
- `ConnectionFailed`, `NetworkError`, `PageLoadTimeout`: the page or connection failed.

## Wait between attempts

Retrying instantly rarely helps when the problem is a slow server. Pass `delay` (seconds) to wait between attempts:

```python
@retry(max_retries=3, exceptions=[ConnectionFailed], delay=2)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## Back off exponentially

For rate limits or an overloaded server, a constant delay still hammers it. Set `exponential_backoff=True` and each wait grows: with `delay=1`, the pauses are 2s, then 4s, then 8s, giving the server progressively more room to recover.

```python
@retry(
    max_retries=4,
    exceptions=[ConnectionFailed, PageLoadTimeout],
    delay=1,
    exponential_backoff=True,
)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

<iframe src="/docs/resources/visuals/retry-backoff.html" aria-label="Fixed delay vs exponential backoff retry timeline" style="width: 100%; height: 290px; border: 0;" loading="lazy"></iframe>

Run each mode: a fixed delay keeps the same gap between attempts, while exponential backoff doubles it (2s, 4s, 8s), spacing the retries further apart.

## Recover before the next attempt

`on_retry` runs an async function after each failed attempt, before the next one. Use it to put the page back into a good state, for example by refreshing after stale elements or a blocking modal.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout


class ProductScraper:
    def __init__(self, tab):
        self.tab = tab

    async def recover(self):
        await self.tab.refresh()
        await asyncio.sleep(1)

    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover,
        delay=1,
    )
    async def price(self):
        element = await self.tab.find(class_name='price', timeout=5)
        return await element.text
```

Two things to know about `on_retry`:

- It must be an async function, because the decorator awaits it.
- When the callback is a method, define it **above** the decorated method in the class body. Python evaluates `@retry(on_retry=recover)` while the class is being built, so the name has to exist already.

## Raise your own error when retries run out

By default, the last exception is re-raised once every attempt fails. Pass `exception_to_raise` to surface a clearer error to your caller instead:

```python
from pydoll.exceptions import ConnectionFailed


class SiteUnavailable(Exception):
    pass


@retry(
    max_retries=3,
    exceptions=[ConnectionFailed],
    exception_to_raise=SiteUnavailable('the site never responded'),
)
async def open_site(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## What's next

- [Events](events.md): react to page and network events instead of retrying blind.
- [Element finding](element-finding.md): the `timeout` on `find()` already waits for late elements, before any retry is needed.
- [Proxies](proxies.md): rotate the egress IP when failures come from rate limits or blocks.
