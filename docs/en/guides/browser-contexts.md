# Browser contexts

A browser context is an isolated session inside one browser process: its own cookies, storage, and cache, like a separate incognito profile. Use contexts to run several logins or identities at once in a single browser, without one leaking into another.

## Create a context and open a tab in it

`create_browser_context()` returns a context id. Pass it to `new_tab()` and that tab lives in the isolated context.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        await browser.start()

        context_id = await browser.create_browser_context()
        tab = await browser.new_tab('https://github.com', browser_context_id=context_id)

        print(await tab.title)

        await browser.delete_browser_context(context_id)

asyncio.run(main())
```

The tab you get from `browser.start()` lives in the permanent **default context**. Any tab you open without a `browser_context_id` joins it too.

## Contexts are isolated

Storage set in one context is invisible to another. Here two tabs write the same key and read back different values:

```python
await tab_a.go_to('https://the-internet.herokuapp.com')
await tab_b.go_to('https://the-internet.herokuapp.com')

await tab_a.execute_script("localStorage.setItem('user', 'Alice')")
await tab_b.execute_script("localStorage.setItem('user', 'Bob')")

a = await tab_a.execute_script("return localStorage.getItem('user')", return_by_value=True)
b = await tab_b.execute_script("return localStorage.getItem('user')", return_by_value=True)
print(a['result']['result']['value'])  # Alice
print(b['result']['result']['value'])  # Bob
```

Cookies, `localStorage`, `sessionStorage`, IndexedDB, cache, and permissions are all separate per context, so a login in one context does not sign you in anywhere else.

```mermaid
graph LR
    Browser[Browser process] --> Default[Default context]
    Browser --> C1[Context 1]
    Browser --> C2[Context 2]
    Default --> T1[Tab A]
    C1 --> T2[Tab B]
    C2 --> T3[Tab C]
```

<iframe scrolling="no" src="/docs/resources/visuals/contexts-isolation.html" aria-label="Two browser contexts, each with its own cookie jar, showing that a cookie set in one does not appear in the other" style="width: 100%; height: 325px; border: 0;" loading="lazy"></iframe>

Log in on each context: the cookie lands only in that context's jar. Nothing crosses over, which is what makes contexts good for running separate sessions in one browser.

## Run several sessions side by side

Give each account its own context and they stay logged in independently. Because the waits overlap, `asyncio.gather` runs them at once.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def open_session(browser, label):
    context_id = await browser.create_browser_context()
    tab = await browser.new_tab('https://the-internet.herokuapp.com', browser_context_id=context_id)
    await tab.execute_script(f"localStorage.setItem('account', '{label}')")
    return context_id, tab, label


async def main():
    async with Chrome() as browser:
        await browser.start()

        sessions = await asyncio.gather(
            open_session(browser, 'account-1'),
            open_session(browser, 'account-2'),
            open_session(browser, 'account-3'),
        )

        for context_id, tab, label in sessions:
            result = await tab.execute_script(
                "return localStorage.getItem('account')", return_by_value=True
            )
            active = result['result']['result']['value']
            print(f'{label}: {active}')
            await browser.delete_browser_context(context_id)

asyncio.run(main())
```

## Give a context its own cookies

The browser-level cookie methods take a `browser_context_id`, so you can seed or read a context's cookies without navigating a tab. Cookies set on one context never appear on another.

```python
from pydoll.protocol.network.types import CookieParam

context_id = await browser.create_browser_context()

await browser.set_cookies(
    [CookieParam(name='session', value='abc123', domain='httpbin.org')],
    browser_context_id=context_id,
)

in_context = await browser.get_cookies(browser_context_id=context_id)
in_default = await browser.get_cookies()   # does not include the cookie above
```

See [Cookies and sessions](cookies-and-sessions.md) for reading, writing, and clearing cookies in depth.

## Route a context through its own proxy

Pass `proxy_server` when you create the context and every request from its tabs goes through that proxy. This is how you run different geographies at the same time.

```python
us = await browser.create_browser_context(proxy_server='http://us-proxy.example:8080')
eu = await browser.create_browser_context(proxy_server='http://eu-proxy.example:8080')

us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us)
eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu)
```

Credentials in the proxy URL (`http://user:pass@host:port`) are handled for you: they are stripped from CDP commands and supplied only when the proxy challenges for auth. See [Proxies](proxies.md) for the full picture, and [Fingerprint injection](../stealth/fingerprint-injection.md) for keeping one identity per context.

## Clean up

`delete_browser_context()` removes a context and closes every tab in it, which is a quick way to tear down a whole session at once.

```python
await browser.delete_browser_context(context_id)
```

!!! warning "Deleting a context closes its tabs"
    Every tab in the context is closed when you delete it, so read anything you still need first. The default context is permanent and cannot be deleted; it closes when the browser stops.

## What's next

- [Tabs](tabs.md): manage several tabs within a context.
- [Cookies and sessions](cookies-and-sessions.md): seed and inspect a context's cookies.
- [Proxies](proxies.md): route contexts through different proxies, with authentication.
