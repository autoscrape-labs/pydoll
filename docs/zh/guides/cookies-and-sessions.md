# Cookies 与会话

一个已登录的会话就存在于浏览器的 cookies 里。读取它们、设置它们，或把它们保存到磁盘、在下次运行时再加载回来，这样你的自动化就只需登录一次，而不是每次都登录。

## 读取 cookies

`tab.get_cookies()` 返回该标签页所在浏览器上下文中的每一个 cookie，而不只是当前页面的：

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

每个 cookie 都是一个字典，包含 `name`、`value`、`domain`、`path`、`expires`、`secure`、`httpOnly`、`sameSite`，以及像 `size` 和 `session` 这样的几个只读字段。

## 设置 cookies

给 `tab.set_cookies()` 传入一个 cookie 字典的列表。只有 `name` 和 `value` 是必填的；其余都是可选的，会回退到合理的默认值（`domain` 为当前页面，`path` 为 `/`，`secure` 和 `httpOnly` 为 `False`）。

```python
await tab.set_cookies([
    {'name': 'theme', 'value': 'dark', 'domain': 'github.com'},
    {'name': 'session', 'value': 'abc123', 'domain': 'github.com', 'secure': True, 'httpOnly': True},
])
```

cookies 作用于整个浏览器上下文，所以该上下文中的每个标签页都能看到它们。如果站点在加载时会读取 cookies，就在导航之前设置它们。

## 清除 cookies

```python
await tab.delete_all_cookies()
```

这会清除该标签页所在的上下文。若要清除某个特定的上下文，使用带有其 id 的浏览器级方法：`await browser.delete_all_cookies(browser_context_id=ctx)`。

## 保存并恢复会话

登录一次，保存 cookies，然后在之后的运行中重新加载它们，从而完全跳过登录。本示例使用 [quotes.toscrape.com](https://quotes.toscrape.com/login)，它的登录接受任意凭据并设置一个会话 cookie。

第一次运行，登录并保存：

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

之后的运行，加载 cookies，你就已经登录了：

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

重新格式化这一步很重要：`get_cookies()` 返回完整的 `Cookie` 对象，其中带有 `set_cookies()` 不接受的只读字段（`size`、`session` 等），所以只把可设置的字段复制过去。

!!! warning "保存的 cookies 就是可用的凭据"
    一个保存下来的会话文件就等于对账号的访问权限。把它排除在版本控制之外，限制它的权限，并像对待密码一样对待它。从环境变量加载密钥，而不要硬编码。

会话一旦生效，[浏览器上下文的 HTTP 请求](http-requests.md)也会复用它，所以对站点 API 发起的 `tab.request.get(...)` 已经是完成认证的了。

## 按上下文隔离 cookies

cookies 归属于某个浏览器上下文。两个上下文有各自独立的 cookie 存储，这正是你并排运行两个账号而互不干扰的方式。用浏览器级方法在某个特定上下文中设置 cookies：

```python
ctx = await browser.create_browser_context()
tab2 = await browser.new_tab(browser_context_id=ctx)

await browser.set_cookies(
    [{'name': 'session', 'value': 'second-account', 'domain': 'quotes.toscrape.com'}],
    browser_context_id=ctx,
)
```

关于并行运行隔离会话，参见[浏览器上下文](browser-contexts.md)。

!!! note "无痕模式与 `get_cookies`"
    `browser.get_cookies()` 使用 CDP 的 `Storage` 域，它无法读取原生 `--incognito` 标志下的 cookies。`tab.get_cookies()` 使用 `Network` 域，在那种情况下也能工作，所以在无痕模式下优先使用标签页的方法。要做隔离，请使用浏览器上下文而不是 `--incognito`。

## CookieParam 字段

设置 cookie 时，这些是你可以传入的字段：

| 字段 | 类型 | 默认值 |
|---|---|---|
| `name` | str | 必填 |
| `value` | str | 必填 |
| `domain` | str | 当前页面的 domain |
| `path` | str | `/` |
| `secure` | bool | `False` |
| `httpOnly` | bool | `False` |
| `sameSite` | `'Strict'` / `'Lax'` / `'None'` | 浏览器默认值 |
| `expires` | float（Unix 时间戳） | 会话 cookie |

`CookieParam`（来自 `pydoll.protocol.network.types`）是一个 `TypedDict`，所以实际使用时你传入一个普通字典即可；这个类型只是额外提供 IDE 自动补全。

## 下一步

- [浏览器上下文](browser-contexts.md)：用于并行会话的隔离 cookie 存储。
- [浏览器上下文的 HTTP 请求](http-requests.md)：复用该会话的已认证 API 调用。
- [你的第一个自动化](../first-automation.md)：本指南所保存的那套登录流程。
