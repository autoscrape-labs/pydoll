# Cookies and sessions

A logged-in session lives in the browser's cookies. Read them, set them, or save them to disk and load them back on the next run, so your automation logs in once instead of every time.

## Read the cookies

`tab.get_cookies()` returns every cookie in the tab's browser context, not just the current page's:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com')

        cookies = await tab.get_cookies()
        print(f'{len(cookies)} cookies')
        for cookie in cookies:
            print(f"  {cookie['name']} = {cookie['value'][:16]}...")

asyncio.run(main())
```

Each cookie is a dict with `name`, `value`, `domain`, `path`, `expires`, `secure`, `httpOnly`, `sameSite`, and a few read-only fields like `size` and `session`.

## Set cookies

Pass a list of cookie dicts to `tab.set_cookies()`. Only `name` and `value` are required; the rest are optional and fall back to sensible defaults (`domain` is the current page, `path` is `/`, `secure` and `httpOnly` are `False`).

```python
await tab.set_cookies([
    {'name': 'theme', 'value': 'dark', 'domain': 'github.com'},
    {'name': 'session', 'value': 'abc123', 'domain': 'github.com', 'secure': True, 'httpOnly': True},
])
```

Cookies apply to the whole browser context, so every tab in that context sees them. Set them before you navigate if the site reads them on load.

## Clear cookies

```python
await tab.delete_all_cookies()
```

This clears the tab's context. To clear a specific context, use the browser-level method with its id: `await browser.delete_all_cookies(browser_context_id=ctx)`.

## Save and restore a session

Log in once, save the cookies, then reload them on later runs to skip the login entirely. This example uses [quotes.toscrape.com](https://quotes.toscrape.com/login), whose login accepts any credentials and sets a session cookie.

First run, log in and save:

```python
import asyncio
import json
from pathlib import Path

from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('session.json')


async def login_and_save():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        await (await tab.find(id='username')).type_text('tester', humanize=True)
        await (await tab.find(id='password')).type_text('secret', humanize=True)
        await (await tab.find(tag_name='input', type='submit')).click()

        cookies = await tab.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies))
        print(f'Saved {len(cookies)} cookies')

asyncio.run(login_and_save())
```

Later runs, load the cookies and you are already logged in:

```python
import asyncio
import json
from pathlib import Path

from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('session.json')


async def restore_and_use():
    saved = json.loads(COOKIE_FILE.read_text())
    cookies = [
        {'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/')}
        for c in saved
    ]

    async with Chrome() as browser:
        tab = await browser.start()
        await tab.set_cookies(cookies)

        await tab.go_to('https://quotes.toscrape.com')
        logout = await tab.find(text='Logout', timeout=5, raise_exc=False)
        print('Session restored.' if logout else 'Session expired, log in again.')

asyncio.run(restore_and_use())
```

The reformatting step matters: `get_cookies()` returns full `Cookie` objects with read-only fields (`size`, `session`, and others) that `set_cookies()` does not accept, so copy across just the settable fields.

!!! warning "Saved cookies are live credentials"
    A saved session file grants access to the account. Keep it out of version control, restrict its permissions, and treat it like a password. Load secrets from the environment rather than hardcoding them.

Once the session is active, [browser-context HTTP requests](http-requests.md) reuse it too, so `tab.request.get(...)` to the site's API is already authenticated.

## Isolate cookies per context

Cookies belong to a browser context. Two contexts have separate cookie jars, which is how you run two accounts side by side without one clobbering the other. Set cookies in a specific context with the browser-level method:

```python
ctx = await browser.create_browser_context()
tab2 = await browser.new_tab(browser_context_id=ctx)

await browser.set_cookies(
    [{'name': 'session', 'value': 'second-account', 'domain': 'quotes.toscrape.com'}],
    browser_context_id=ctx,
)
```

See [Browser contexts](browser-contexts.md) for running isolated sessions in parallel.

!!! note "Incognito and `get_cookies`"
    `browser.get_cookies()` uses the CDP `Storage` domain, which cannot read cookies under the native `--incognito` flag. `tab.get_cookies()` uses the `Network` domain and works there, so prefer the tab method in incognito. For isolation, use a browser context instead of `--incognito`.

## CookieParam fields

When setting a cookie, these are the fields you can pass:

| Field | Type | Default |
|---|---|---|
| `name` | str | required |
| `value` | str | required |
| `domain` | str | current page domain |
| `path` | str | `/` |
| `secure` | bool | `False` |
| `httpOnly` | bool | `False` |
| `sameSite` | `'Strict'` / `'Lax'` / `'None'` | browser default |
| `expires` | float (Unix timestamp) | session cookie |

`CookieParam` (from `pydoll.protocol.network.types`) is a `TypedDict`, so in practice you pass a plain dict; the type only adds IDE autocomplete.

## What's next

- [Browser contexts](browser-contexts.md): isolated cookie jars for parallel sessions.
- [Browser-context HTTP requests](http-requests.md): authenticated API calls that reuse the session.
- [Your first automation](../first-automation.md): the login flow this guide saves.
