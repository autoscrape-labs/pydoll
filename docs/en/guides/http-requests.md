# Browser-context HTTP requests

`tab.request` sends HTTP calls from inside the browser, so they carry the page's cookies, session, and authentication automatically. Log in once through the UI, then call the site's API directly: no cookies to copy, no second HTTP client to keep in sync with the browser.

## Make your first request

`tab.request` gives you a `requests`-like interface. Call `get()` with a URL and read the response:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

        print(response.status_code)   # 200
        print(response.json()['title'])

asyncio.run(main())
```

The call runs through the browser's own `fetch`, so anything the browser already carries (cookies, an active session) rides along with it.

## Call an API after logging in

Browser-context requests are most useful after a login. Sign in through the page as a user would, then hit the site's API with the session you just established. You don't extract a token or copy a cookie jar; the request is already authenticated.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        # 1. Log in through the UI (this is your own authenticated app)
        await tab.go_to('https://yourapp.com/login')
        await (await tab.find(id='username')).type_text('tester', humanize=True)
        await (await tab.find(id='password')).type_text('secret', humanize=True)
        await (await tab.find(tag_name='button', type='submit')).click()

        # 2. Call the API with the logged-in session
        response = await tab.request.get('https://yourapp.com/api/profile')
        print(response.json())

asyncio.run(main())
```

!!! note "No cookie handling"
    Nothing above copies cookies or passes a token. Because the request runs in the browser context, it uses the same session the page just authenticated.

## Send data with POST

Pass `json=` to send a JSON body (the `Content-Type` is set for you):

```python
response = await tab.request.post(
    'https://jsonplaceholder.typicode.com/posts',
    json={'title': 'Automating the web', 'body': 'with pydoll', 'userId': 1},
)
print(response.status_code)          # 201
print(response.json()['id'])
```

Pass `data=` to send form-encoded fields instead. `data` and `json` are mutually exclusive:

```python
response = await tab.request.post(
    'https://httpbin.org/post',
    data={'username': 'tester', 'remember': 'true'},
)
print(response.json()['form'])       # {'username': 'tester', 'remember': 'true'}
```

`data` also accepts a `str` or `bytes` when you need to send a raw body.

## Add request headers

Headers are a list of `HeaderEntry` (a typed dict with `name` and `value`). They are added on top of the browser's automatic headers, not replacements:

```python
from pydoll.protocol.fetch.types import HeaderEntry

headers: list[HeaderEntry] = [
    {'name': 'X-API-Version', 'value': '2'},
    {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
]

response = await tab.request.get('https://httpbin.org/headers', headers=headers)
print(response.json()['headers'])
```

!!! tip "Stick to custom headers"
    Custom headers like `X-API-Key` or `Authorization` are sent alongside the browser's own headers. Trying to override a standard header (`User-Agent`, `Referer`) behaves inconsistently, so leave those to the browser and set only your own.

## Read the response

The `Response` object mirrors the `requests` library. `text`, `content`, `status_code`, `ok`, `headers`, `cookies`, and `url` are properties; `json()` and `raise_for_status()` are methods:

```python
response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

response.status_code     # 200
response.ok              # True for 2xx and 3xx

response.text            # body as str
response.content         # body as bytes
response.json()          # parsed JSON (dict or list)

response.url             # final URL after any redirects

for header in response.headers:
    print(header['name'], header['value'])

for cookie in response.cookies:
    print(cookie['name'], cookie['value'])

response.raise_for_status()   # raises on a 4xx or 5xx status
```

`response.url` holds only the final URL. To follow the full redirect chain, watch the requests with [Network monitoring](network-monitoring.md).

## Other HTTP methods

`get` and `post` cover most work; the rest of the verbs are there when you need them, with the same shape:

```python
await tab.request.put('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'edited'})
await tab.request.patch('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'tweaked'})
await tab.request.delete('https://jsonplaceholder.typicode.com/posts/1')
await tab.request.head('https://httpbin.org/get')
await tab.request.options('https://httpbin.org/get')
```

For full control over the verb and every option in one call, use `tab.request.request(method, url, params=..., data=..., json=..., headers=...)`.

## What's next

- [Cookies and sessions](cookies-and-sessions.md): manage the session your requests inherit.
- [Network monitoring](network-monitoring.md): watch every request the page makes, including redirects.
- [Request interception](request-interception.md): change or block requests before they are sent.
