# 浏览器上下文

浏览器上下文是一个浏览器进程内相互隔离的会话：它有自己的 cookies、存储和缓存，就像一个独立的隐身配置文件。用上下文可以在单个浏览器里同时运行多个登录或身份，彼此互不泄露。

## 创建上下文并在其中打开标签页

`create_browser_context()` 返回一个上下文 id。把它传给 `new_tab()`，那个标签页就活在这个隔离的上下文里。

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

你从 `browser.start()` 得到的标签页活在永久的 **默认上下文** 里。任何不带 `browser_context_id` 打开的标签页也会加入它。

## 上下文之间相互隔离

在一个上下文里设置的存储，对另一个是不可见的。这里两个标签页写入同一个键，读回来的却是不同的值：

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

cookies、`localStorage`、`sessionStorage`、IndexedDB、缓存和权限在每个上下文里都是各自独立的，所以在一个上下文里登录，并不会让你在别处也登录。

```mermaid
graph LR
    Browser[浏览器进程] --> Default[默认上下文]
    Browser --> C1[上下文 1]
    Browser --> C2[上下文 2]
    Default --> T1[标签页 A]
    C1 --> T2[标签页 B]
    C2 --> T3[标签页 C]
```

<iframe scrolling="no" src="/docs/resources/visuals/contexts-isolation.html" aria-label="Two browser contexts, each with its own cookie jar, showing that a cookie set in one does not appear in the other" style="width: 100%; height: 325px; border: 0;" loading="lazy"></iframe>

在每个上下文里各自登录：cookie 只会落在那个上下文的 jar 里。什么都不会互相越界，这正是上下文适合在一个浏览器里运行多个独立会话的原因。

## 多个会话并排运行

给每个账号各自的上下文，它们就能各自独立地保持登录。由于这些等待彼此重叠，`asyncio.gather` 会让它们同时进行。

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

## 给上下文配上自己的 cookies

浏览器级别的 cookie 方法接受 `browser_context_id`，所以你无需导航某个标签页就能给上下文注入或读取 cookies。在一个上下文里设置的 cookies 永远不会出现在另一个上下文里。

```python
from pydoll.protocol.network.types import CookieParam

context_id = await browser.create_browser_context()

await browser.set_cookies(
    [CookieParam(name='session', value='abc123', domain='httpbin.org')],
    browser_context_id=context_id,
)

in_context = await browser.get_cookies(browser_context_id=context_id)
in_default = await browser.get_cookies()   # 不包含上面那个 cookie
```

深入了解 cookies 的读取、写入和清除，请看 [Cookies 与会话](cookies-and-sessions.md)。

## 让上下文经过自己的 proxy

在创建上下文时传入 `proxy_server`，它的标签页发出的每个请求都会经过那个 proxy。这就是你同时运行不同地理位置的方式。

```python
us = await browser.create_browser_context(proxy_server='http://us-proxy.example:8080')
eu = await browser.create_browser_context(proxy_server='http://eu-proxy.example:8080')

us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us)
eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu)
```

proxy URL 中的凭据（`http://user:pass@host:port`）会替你处理好：它们会从 CDP 命令中剥离，仅在 proxy 发起认证质询时才提供。完整图景请看 [Proxy](proxies.md)，为每个上下文保持一份身份请看 [Fingerprint 注入](../stealth/fingerprint-injection.md)。

## 清理

`delete_browser_context()` 会移除一个上下文并关闭其中的每个标签页，这是一次性拆除整个会话的快捷方式。

```python
await browser.delete_browser_context(context_id)
```

!!! warning "删除上下文会关闭它的标签页"
    删除上下文时，其中的每个标签页都会被关闭，所以要先读取你还需要的东西。默认上下文是永久的、无法删除；它会在浏览器停止时关闭。

## 下一步

- [标签页](tabs.md)：在一个上下文内管理多个标签页。
- [Cookies 与会话](cookies-and-sessions.md)：注入并检查上下文的 cookies。
- [Proxy](proxies.md)：让不同的上下文经过不同的 proxy，并处理认证。
