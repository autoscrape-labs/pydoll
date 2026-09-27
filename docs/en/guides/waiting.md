# Waiting

Pages change after they load: a spinner goes away, a button becomes enabled, a click fires a request, a form submit navigates. Pydoll gives you a wait for each of those moments, so you wait for the exact thing you need instead of sleeping and hoping. Every wait raises `WaitTimeout` (or `WaitElementTimeout` for element states) when the time runs out.

## Wait for an element state

`find()` with a `timeout` waits for an element to exist. `wait_until()` waits for what happens next: the element becoming visible, hidden, enabled, interactable, or removed from the page. Set one or more conditions and the call returns when all of them hold.

=== "Sync"

    ```python
    from pydoll import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            tab.find(tag_name='button').click()

            loading = tab.find(id='loading')
            loading.wait_until(is_hidden=True, timeout=10)

            print(tab.find(id='finish').text())

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            await (await tab.find(tag_name='button')).click()

            loading = await tab.find(id='loading')
            await loading.wait_until(is_hidden=True, timeout=10)

            print(await (await tab.find(id='finish')).text())

    asyncio.run(main())
    ```

The conditions you can set:

| Flag | Holds when |
|------|-----------|
| `is_visible` | The element has a box on screen and is not hidden by CSS. |
| `is_hidden` | The opposite of `is_visible`. |
| `is_enabled` | The element has no `disabled` attribute. |
| `is_interactable` | The element is visible, on top, and can receive a click. |
| `is_detached` | The element was removed from the DOM. |

Each element also answers the same questions directly: `is_visible()`, `is_enabled()`, `is_interactable()`, `is_on_top()` and `is_detached()`.

## Wait for an element to disappear

When you never held the element, or a fresh `find()` would keep re-matching, wait on the tab instead. `wait_for_absence()` takes the same criteria as `find()` and returns once nothing matches.

=== "Sync"

    ```python
    tab.find(text='Start').click()
    tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

=== "Async"

    ```python
    await (await tab.find(text='Start')).click()
    await tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

## Wait for a URL

Single-page apps change the URL without a page load. `wait_for_url()` polls the current URL until it matches and returns the URL that matched. The pattern can be a glob, a compiled regular expression, or a callable that takes the URL and returns a bool.

=== "Sync"

    ```python
    import re

    tab.find(id='checkout').click()

    tab.wait_for_url('**/checkout/*', timeout=10)
    tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

=== "Async"

    ```python
    import re

    await (await tab.find(id='checkout')).click()

    await tab.wait_for_url('**/checkout/*', timeout=10)
    await tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    await tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

In a glob, `*` matches anything except `/`, `**` matches anything including `/`, and `{a,b}` matches either alternative. The same three pattern forms work everywhere a URL pattern is accepted in this guide.

## Wait for a JavaScript condition

`wait_for_script()` evaluates an expression in the page until it returns a truthy value, and returns that value. Use it for state the DOM does not show: a global set by the app, a store's ready flag, a count.

=== "Sync"

    ```python
    tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

=== "Async"

    ```python
    await tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = await tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

## Wait for the network to go quiet

`wait_for_network_idle()` returns once no request has been in flight for `idle_time` seconds. Call it right after the action that starts the requests, because only requests started after the call are counted.

=== "Sync"

    ```python
    tab.find(id='load-more').click()
    tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = tab.find(class_name='card', find_all=True)
    ```

=== "Async"

    ```python
    await (await tab.find(id='load-more')).click()
    await tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = await tab.find(class_name='card', find_all=True)
    ```

!!! note "Pages that never go quiet"
    Analytics beacons and long polling keep some pages busy forever. There, wait for the element or response you need instead of the whole network.

## Capture the response a click triggers

The data you want is often in the JSON the page fetches, not in the DOM. `expect_response()` is a context manager: enter it, do the action inside the block, and when the block exits the handle holds the first matching response, body included.

=== "Sync"

    ```python
    with tab.expect_response('**/api/prices*') as response:
        tab.find(id='refresh').click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

=== "Async"

    ```python
    async with tab.expect_response('**/api/prices*') as response:
        await (await tab.find(id='refresh')).click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

The handle exposes `url`, `status`, `ok` (true for a 2xx status), `headers`, `mime_type` and `request_id`, plus `body()` as bytes, `text()` and `json()`. Reading a field inside the block, before anything arrived, raises `WaitTimeout`. If the browser failed the load after the headers came in, `status` and `headers` are still set and `body()` raises `WaitTimeout`.

`expect_request()` works the same way for the outgoing side, and its handle exposes `url`, `method`, `headers`, `post_data` and `resource_type`.

=== "Sync"

    ```python
    with tab.expect_request('**/api/search') as request:
        tab.find(id='search').click()

    print(request.method, request.post_data)
    ```

=== "Async"

    ```python
    async with tab.expect_request('**/api/search') as request:
        await (await tab.find(id='search')).click()

    print(request.method, request.post_data)
    ```

Both managers turn network events on for the block if they were off, and turn them back off afterwards. You don't manage `enable_network_events()` yourself.

## Wait for a navigation you cause

`go_to()` already waits for the page to load. When a click or a form submit is what navigates, wrap it in `expect_navigation()`: the block exits once the main frame has moved (to a URL matching `url`, when given) and reached the load state configured in `options.page_load_state`.

=== "Sync"

    ```python
    with tab.expect_navigation(url='**/dashboard'):
        tab.find(id='login').click()

    print(tab.current_url())
    ```

=== "Async"

    ```python
    async with tab.expect_navigation(url='**/dashboard'):
        await (await tab.find(id='login')).click()

    print(await tab.current_url())
    ```

## Register before you act

The three `expect_*` managers start listening when you enter the block, and the action goes inside it. Doing the action first and then waiting would miss a response that arrived in between, which is exactly the fast case you want to handle.

=== "Sync"

    ```python
    # the listener is already in place when the click fires
    with tab.expect_response('**/api/data') as response:
        tab.find(id='fetch').click()
    ```

=== "Async"

    ```python
    # the listener is already in place when the click fires
    async with tab.expect_response('**/api/data') as response:
        await (await tab.find(id='fetch')).click()
    ```

## Complete example: read an API instead of the DOM

=== "Sync"

    ```python
    from pydoll import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://quotes.toscrape.com/scroll')

            with tab.expect_response('**/api/quotes?page=2') as response:
                tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            tab.wait_for_network_idle(idle_time=0.5)

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com/scroll')

            async with tab.expect_response('**/api/quotes?page=2') as response:
                await tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            await tab.wait_for_network_idle(idle_time=0.5)

    asyncio.run(main())
    ```

## What's next

- [Element finding](element-finding.md): `find()` with a timeout, the wait that comes before all of these.
- [Network monitoring](network-monitoring.md): watch every request on the page, not only the one you expect.
- [Events](events.md): react to page and network events as they happen.
- [Retrying](retrying.md): re-run a whole step when a wait times out.
