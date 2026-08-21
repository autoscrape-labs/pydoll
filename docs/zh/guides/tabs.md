# 标签页

标签页是你所驱动的对象：导航、查找元素以及页面上的一切都通过它进行。一个浏览器可以同时持有许多标签页，而由于 Pydoll 是异步的，你可以并发地驱动它们，而不必一次只处理一个。

## 打开和关闭标签页

`browser.start()` 给你第一个标签页。`browser.new_tab()` 打开更多，`tab.close()` 关闭一个。`async with` 块结束时浏览器本身会关闭，连同它的每一个标签页。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

        # 打开另一个标签页，已经导航好了
        docs = await browser.new_tab('https://en.wikipedia.org/wiki/Web_scraping')
        print(await docs.title)

        await docs.close()

asyncio.run(main())
```

给 `new_tab(url)` 传一个 URL，标签页会在返回之前导航到那里。不带参数调用 `new_tab()` 则得到一个空白标签页，稍后再导航。

## 一次抓取多个页面

这就是异步设计的回报：给每个页面一个自己的标签页，用 `asyncio.gather` 把它们跑起来，这样它们的加载时间会重叠，而不是叠加。把 `start()` 得到的标签页复用为第一个工作单元，而不是让它闲置。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def title_of(tab, url):
    await tab.go_to(url)
    return await tab.title


async def main():
    urls = [
        'https://en.wikipedia.org/wiki/Async/await',
        'https://en.wikipedia.org/wiki/Coroutine',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    async with Chrome() as browser:
        first = await browser.start()
        tabs = [first] + [await browser.new_tab() for _ in urls[1:]]

        titles = await asyncio.gather(*(title_of(tab, url) for tab, url in zip(tabs, urls)))
        for title in titles:
            print(title)

asyncio.run(main())
```

这三个页面并发加载，所以整个运行耗时大约等于最慢的那个单页。关于 `gather` 如何工作，参见[实战中的异步 Python](../basics/async-python.md)。

## 列出打开的标签页

`browser.get_opened_tabs()` 返回每一个打开的标签页。最后一项是最近打开的。

```python
async with Chrome() as browser:
    await browser.start()
    await browser.new_tab('https://github.com')
    await browser.new_tab('https://news.ycombinator.com')

    tabs = await browser.get_opened_tabs()
    for tab in tabs:
        print(await tab.current_url)
```

## 处理页面打开的标签页

当一次点击打开了一个标签页（带 `target="_blank"` 的链接），它会出现在 `get_opened_tabs()` 中。比较点击前后的列表，新的标签页就是最后一个。

```python
before = len(await browser.get_opened_tabs())

link = await tab.find(text='Open in new tab')
await link.click()

tabs = await browser.get_opened_tabs()
if len(tabs) > before:
    new_tab = tabs[-1]
    print(await new_tab.current_url)
```

## 把标签页带到前台

自动化驱动后台标签页没问题，但有些页面只在可见时才运行定时器或动画。`bring_to_front()` 把一个标签页设为活动的那个。

```python
await background_tab.bring_to_front()
```

## 下一步

- [浏览器上下文](browser-contexts.md)：给标签页隔离的 cookies 和会话。
- [Cookies 和会话](cookies-and-sessions.md)：把登录状态带到多个标签页。
- [实战中的异步 Python](../basics/async-python.md)：并发标签页背后的 `gather` 模式。
