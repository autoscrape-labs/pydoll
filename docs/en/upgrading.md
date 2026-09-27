# Upgrading to Pydoll 3

Pydoll 3 makes the synchronous API a first-class part of the library and cleans up the surface that grew around the async one. A Pydoll 2 script needs three mechanical changes, and the APIs that were already deprecated in 2.x are gone. Nothing about how the browser is driven changed.

**You will learn**

- [Where to import from](#import-from-pydoll)
- [Which properties became methods](#call-what-used-to-be-a-property)
- [Which deprecated APIs were removed](#removed-apis)

## Import from `pydoll` {#import-from-pydoll}

The classes you use in every script are exported from the top-level package. The sync API exports the same names from `pydoll.sync`, so the two forms differ by one import line.

=== "Sync"

    ```python
    from pydoll.sync import Chrome, ChromiumOptions, Key
    ```

=== "Async"

    ```python
    from pydoll import Chrome, ChromiumOptions, Key
    ```

The old paths still work (`pydoll.browser.chromium`, `pydoll.browser.options`, `pydoll.constants`), so this change is optional. The names available at the top level are `Chrome`, `Edge`, `ChromiumOptions`, `Tab`, `WebElement`, `ShadowRoot`, `Keyboard`, `Mouse`, `Scroll`, `Request`, `Response`, `DownloadHandle`, `Key`, `ExtractionModel`, `Field`, `PageEvent`, `NetworkEvent` and `FetchEvent`.

## Call what used to be a property {#call-what-used-to-be-a-property}

Pydoll 2 exposed a few values as properties that had to be awaited. A property that needs `await` surprises readers and IDEs, and it had no honest synchronous equivalent, so in Pydoll 3 every one of them is a method:

| Pydoll 2 | Pydoll 3 |
|----------|----------|
| `await tab.title` | `await tab.title()` |
| `await tab.current_url` | `await tab.current_url()` |
| `await tab.page_source` | `await tab.page_source()` |
| `await element.text` | `await element.text()` |
| `await element.inner_html` | `await element.inner_html()` |
| `await element.bounds` | `await element.bounds()` |
| `await element.iframe_context` | `await element.iframe_context()` |
| `await shadow_root.inner_html` | `await shadow_root.inner_html()` |

Plain properties that never needed `await` are unchanged: `tab.keyboard`, `element.tag_name`, `element.is_enabled` and the rest.

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    with Chrome() as browser:
        tab = browser.start()
        tab.go_to('https://quotes.toscrape.com')
        print(tab.title())
        print(tab.find(class_name='text').text())
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com')
            print(await tab.title())
            print(await (await tab.find(class_name='text')).text())

    asyncio.run(main())
    ```

## Removed APIs {#removed-apis}

Everything that raised a `DeprecationWarning` in Pydoll 2 is removed. Each row lists the replacement, which already worked in 2.x.

| Removed | Use instead |
|---------|-------------|
| `tab.get_frame(element)` | The iframe `WebElement` itself: `find()` and `query()` on it reach inside the frame. See [Iframes](guides/iframes.md). |
| `tab.execute_script(script, element)` | `element.execute_script(script)` |
| `element.key_down()`, `element.key_up()`, `element.press_keyboard_key()` | `tab.keyboard.down()`, `tab.keyboard.up()`, `tab.keyboard.press()`. See [Keyboard](guides/keyboard.md). |
| `type_text(text, interval=...)` | `type_text(text, humanize=True)` |
| `browser.start(headless=True)` | `options.headless = True` before creating the browser |
| `expect_and_bypass_cloudflare_captcha()` | `expect_cloudflare_turnstile()` |
| `enable_auto_solve_cloudflare_captcha()`, `disable_auto_solve_cloudflare_captcha()` | `enable_cloudflare_turnstile_handling()`, `disable_cloudflare_turnstile_handling()` |
| `custom_selector` and `time_before_click` on those methods | Drop them; the Turnstile widget is located automatically |
| `NotAnIFrame`, `IFrameNotFound` exceptions | No longer raised by anything |

The download handle returned by `tab.expect_download()` is now the public `DownloadHandle` class, importable from `pydoll` and `pydoll.sync`.

## What's next

- [Getting started](getting-started.md): the first script, in both forms.
- [Core concepts](guides/core-concepts.md#sync-and-async): how the sync and async APIs relate.
- [Migrating from Selenium and Playwright](migrating.md): if you are coming from another tool.
