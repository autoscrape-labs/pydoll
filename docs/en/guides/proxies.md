# Proxies

Route the browser's traffic through a proxy to change your egress IP, spread requests across addresses, or reach a site from another region. You set a proxy with one launch argument, and Pydoll handles proxy authentication for you.

<iframe src="../proxy-routing.html" aria-label="A request routed direct versus through a proxy, changing the IP the target sees" style="width: 100%; height: 300px; border: 0;" loading="lazy"></iframe>

## Set a proxy

Pass `--proxy-server` to `ChromiumOptions` and every request the browser makes goes through it. HTTP, HTTPS, and SOCKS5 URLs all work:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        response = await tab.request.get('https://httpbin.org/ip')
        print(response.json())   # {'origin': '<the proxy IP>'}

asyncio.run(main())
```

`tab.request.get` runs in the browser context, so it goes through the same proxy as the page. See [HTTP requests](http-requests.md).

## Use an authenticated proxy

Most paid proxies require a username and password. Put the credentials in the proxy URL and Pydoll answers the authentication challenge for you, so navigation works:

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')
```

You don't write any auth code. Under the hood Pydoll enables Chrome's Fetch domain at the browser level; when the proxy returns a 407 challenge, Chrome pauses the request and Pydoll replies with the credentials from your URL. The equivalent handler built on the public API looks like this:

```python
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def on_auth_required(event):
    await tab.continue_with_auth(
        request_id=event['params']['requestId'],
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='pass',
    )
```

!!! warning "SOCKS5 authentication is not supported by Chrome"
    Chrome ignores credentials in a `socks5://user:pass@host:port` URL ([Chromium issue 40323993](https://issues.chromium.org/issues/40323993)): it never sends them and never issues the 407 challenge Pydoll would answer. Run a local unauthenticated SOCKS5 forwarder that handles the credentials for you, and point Chrome at it:

    ```python
    import asyncio

    from pydoll.utils import SOCKS5Forwarder
    from pydoll.browser.chromium import Chrome
    from pydoll.browser.options import ChromiumOptions


    async def main():
        forwarder = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='myuser',
            password='mypass',
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())
    ```

    Chrome connects to `127.0.0.1` with no auth; the forwarder does the username/password handshake with the remote proxy.

## Use a different proxy per context

A [browser context](browser-contexts.md) can carry its own proxy, so one browser run can send different tabs through different proxies. Pass `proxy_server` when you create the context:

```python
async with Chrome() as browser:
    await browser.start()

    us_ctx = await browser.create_browser_context(proxy_server='http://user:pass@us.proxy.com:8080')
    de_ctx = await browser.create_browser_context(proxy_server='http://user:pass@de.proxy.com:8080')

    us_tab = await browser.new_tab(browser_context_id=us_ctx)
    de_tab = await browser.new_tab(browser_context_id=de_ctx)

    print((await us_tab.request.get('https://httpbin.org/ip')).json())
    print((await de_tab.request.get('https://httpbin.org/ip')).json())
```

## Skip the proxy for some hosts

Use `--proxy-bypass-list` to send certain hosts direct, which is handy for local development servers and internal resources:

```python
options.add_argument('--proxy-server=http://proxy.example.com:8080')
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')
```

## Verify your egress IP

Before a long run, confirm the traffic actually leaves through the proxy:

```python
async with Chrome(options=options) as browser:
    tab = await browser.start()
    ip = (await tab.request.get('https://httpbin.org/ip')).json()['origin']
    print(f'Egress IP: {ip}')
```

!!! note "The proxy is only one detection signal"
    Changing your IP does not make automation undetectable, and the wrong IP makes things worse. Anti-bot systems weigh IP reputation (residential addresses look far more legitimate than datacenter ranges) and cross-check the IP's country against the browser's timezone and languages. Matching the proxy's geography to the rest of your setup is part of a coherent fingerprint, covered in [Fingerprint injection](../stealth/fingerprint-injection.md).

## What's next

- [Browser contexts](browser-contexts.md): isolate sessions and give each its own proxy.
- [Fingerprint injection](../stealth/fingerprint-injection.md): match the IP's geography to the rest of the browser identity.
- [HTTP requests](http-requests.md): call APIs through the same proxy and session.
- [Network and proxies (deep dive)](../deep-dive/network/index.md): how proxies work and how they get detected.
