# 升级到 Pydoll 3

Pydoll 3 让同步 API 成为库的一等公民，并清理了围绕异步 API 长出来的那些接口。一个 Pydoll 2 脚本只需要三处机械性的修改，而 2.x 中已弃用的 API 则被移除了。驱动浏览器的方式没有任何变化。

**你将学到**

- [从哪里导入](#import-from-pydoll)
- [哪些属性变成了方法](#call-what-used-to-be-a-property)
- [哪些已弃用的 API 被移除](#removed-apis)

## 从 `pydoll` 导入 {#import-from-pydoll}

每个脚本都会用到的类现在从顶层包导出。同步 API 从 `pydoll.sync` 导出同样的名称，所以两种形式只差一行导入。

=== "Sync"

    ```python
    from pydoll.sync import Chrome, ChromiumOptions, Key
    ```

=== "Async"

    ```python
    from pydoll import Chrome, ChromiumOptions, Key
    ```

旧路径仍然可用（`pydoll.browser.chromium`、`pydoll.browser.options`、`pydoll.constants`），所以这项修改是可选的。顶层可用的名称有 `Chrome`、`Edge`、`ChromiumOptions`、`Tab`、`WebElement`、`ShadowRoot`、`Keyboard`、`Mouse`、`Scroll`、`Request`、`RequestHandle`、`Response`、`ResponseHandle`、`DownloadHandle`、`Key`、`ExtractionModel`、`Field`、`PageEvent`、`NetworkEvent` 和 `FetchEvent`。

## 把原来的属性改为方法调用 {#call-what-used-to-be-a-property}

Pydoll 2 把一些值暴露为需要 `await` 的属性。需要 `await` 的属性会让读者和 IDE 感到意外，也没有诚实的同步等价物，所以在 Pydoll 3 中它们全部变成了方法：

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

从不需要 `await` 的普通属性保持不变：`tab.keyboard`、`element.tag_name`、`element.is_enabled` 等。

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

## 已移除的 API {#removed-apis}

Pydoll 2 中所有会发出 `DeprecationWarning` 的接口都已移除。每一行列出了替代方案，它们在 2.x 中就已经可用。

| 已移除 | 改用 |
|--------|------|
| `tab.get_frame(element)` | iframe 的 `WebElement` 本身：在它上面调用 `find()` 和 `query()` 即可进入框架内部。参见 [Iframe](guides/iframes.md)。 |
| `tab.execute_script(script, element)` | `element.execute_script(script)` |
| `element.key_down()`、`element.key_up()`、`element.press_keyboard_key()` | `tab.keyboard.down()`、`tab.keyboard.up()`、`tab.keyboard.press()`。参见 [键盘](guides/keyboard.md)。 |
| `type_text(text, interval=...)` | `type_text(text, humanize=True)` |
| `browser.start(headless=True)` | 在创建浏览器之前设置 `options.headless = True` |
| `expect_and_bypass_cloudflare_captcha()` | `expect_cloudflare_turnstile()` |
| `enable_auto_solve_cloudflare_captcha()`、`disable_auto_solve_cloudflare_captcha()` | `enable_cloudflare_turnstile_handling()`、`disable_cloudflare_turnstile_handling()` |
| 这些方法上的 `custom_selector` 和 `time_before_click` | 删掉它们；Turnstile 组件会被自动定位 |
| `NotAnIFrame`、`IFrameNotFound` 异常 | 不再有任何地方抛出它们 |

`tab.expect_download()` 返回的下载句柄现在是公开的 `DownloadHandle` 类，可以从 `pydoll` 和 `pydoll.sync` 导入。

## 下一步

- [快速上手](getting-started.md)：第一个脚本，两种形式。
- [核心概念](guides/core-concepts.md#sync-and-async)：同步和异步 API 之间的关系。
- [从 Selenium 和 Playwright 迁移](migrating.md)：如果你来自其他工具。
