# 异步 Python 实战

每一次 Pydoll 调用前面都带着 `await`。如果这个关键字对你还很陌生，那这一页就是你应该先读的内容。你不需要精通 asyncio，只需要理解到足以运用自如的程度，并明白 Pydoll 为什么构建在它之上。这里的每个示例都能独立运行，把它们粘贴到文件里，看看会发生什么。

## 为什么每次 Pydoll 调用都要 await

浏览器自动化的大部分时间都花在等待上：等页面加载、等元素出现、等网络请求返回。普通的 Python 代码在这些等待期间只能干等着。异步代码则不然：当一个任务在等待时，另一个任务可以继续运行。

正是这个想法让 Pydoll 的这些能力成为可能：

- **同时**驱动多个标签页或浏览器，而不是一个接一个地来。
- 在脚本继续工作的同时监视**网络流量**。
- 在页面事件触发的那一刻运行**回调**。

这些都不需要 thread。它们全都来自 `async` 和 `await`，所以花十分钟摸清它的样子是值得的。

## 结构：`async def`、`await`、`asyncio.run`

每个 Pydoll 脚本里都会出现三样东西：

```python
import asyncio


async def main():          # 1. 一个异步函数，称为 coroutine
    print('hello')
    await asyncio.sleep(1)  # 2. await 在这里暂停 1 秒
    print('one second later')


asyncio.run(main())         # 3. asyncio.run 把它启动起来
```

- `async def` 定义了一个 **coroutine**：一个可以暂停和恢复的函数。
- `await` 是它暂停的地方。你只能在 `async def` 内部使用 `await`。
- `asyncio.run()` 是真正运行这个 coroutine 的入口。它是唯一一个*不*被 await 的调用，因为是它启动了一切。

单独调用 `main()` 没有任何实际作用，它只会创建一个 coroutine 对象。真正让它跑起来的是 `asyncio.run(main())`。

## `await` 的意思是“在这里等，但让别的工作继续跑”

`await asyncio.sleep(1)` 不会把你的整个程序冻结一秒。它暂停的是*当前这个* coroutine，并把控制权交还出去，这样在这一秒内任何已经就绪的任务都能运行。正是这次交接让并发成为可能，下一节会说明它为什么重要。

## 同时做多件事

设想两件大部分时间都在等待的家务：烧水和烤面包，各需要两分钟。

一个接一个地做，你就得依次等完两件：

```python
import asyncio
import time


async def boil_water():
    print('kettle on')
    await asyncio.sleep(2)
    print('water boiled')


async def toast_bread():
    print('bread in')
    await asyncio.sleep(2)
    print('toast ready')


async def main():
    start = time.perf_counter()
    await boil_water()
    await toast_bread()
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

运行它，大约需要 **4 秒**，因为你在开始下一件家务之前完整地等完了前一件。

现在用 `asyncio.gather` 把两件都启动起来，然后一起等它们完成：

```python
async def main():
    start = time.perf_counter()
    await asyncio.gather(boil_water(), toast_bread())
    print(f'done in {time.perf_counter() - start:.1f}s')


asyncio.run(main())
```

这一次大约只需 **2 秒**。两段等待重叠了。水烧开的同时面包也在烤。

<iframe scrolling="no" src="/docs/resources/visuals/async-flow.html" aria-label="Sequential vs concurrent async, animated" style="width: 100%; height: 285px; border: 0;" loading="lazy"></iframe>

分别运行这两种模式，盯着计时器看：顺序执行在 4.0s 结束，并发执行在 2.0s 结束，因为两段等待重叠了。

`asyncio.gather(*coroutines)` 会并发地运行你传给它的所有内容，并在全部完成后按顺序返回它们的结果。

## 同样的思路，用 Pydoll 来做

把家务换成真实的页面，什么都不用变。一次加载三个页面，你要等三遍；用 `gather` 加载它们，则会让等待重叠。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def title_of(browser, url):
    tab = await browser.new_tab(url)
    title = await tab.title
    await tab.close()
    return title


async def main():
    urls = [
        'https://en.wikipedia.org/wiki/Async/await',
        'https://en.wikipedia.org/wiki/Coroutine',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    async with Chrome() as browser:
        await browser.start()
        titles = await asyncio.gather(*(title_of(browser, url) for url in urls))
        for title in titles:
            print(title)


asyncio.run(main())
```

三个页面并发加载，所以整个过程大约只需要最慢那一个页面所花的时间。

## 你多半会遇到的两个错误

这些是刚接触异步时常见的绊脚石。一旦见过一次，就很容易认出来。

**你忘了写 `await`。** 没有它，你拿到的是 coroutine 对象而不是它的结果，还会附带一条警告：

```python
title = tab.title
print(title)   # <coroutine object ...>, and: RuntimeWarning: coroutine was never awaited
```

修复方法是加上 `await`：`title = await tab.title`。

**你调用了异步代码，却没有启动事件循环。** `await` 只在 `async def` 内部有效，而 coroutine 只有在 `asyncio.run()`（或另一个正在运行的循环）下才会运行：

```python
main()   # nothing happens; this just creates a coroutine
```

修复方法是 `asyncio.run(main())`。

## 异步在 Pydoll 中的价值所在

一旦对这个结构运用自如，这些能力其实就是 `gather` 和回调在发挥作用：

- **并行自动化：** 用 `gather` 同时驱动多个标签页或浏览器。参见 [Tabs](../guides/tabs.md)。
- **网络拦截：** 在脚本继续运行的同时监视并修改请求。参见 [Network monitoring](../guides/network-monitoring.md)。
- **事件回调：** 在页面或网络事件触发的那一刻运行一个函数。参见 [Events](../guides/events.md)。

## 下一步

- [Installation](../getting-started.md)：安装 Pydoll 并运行你的第一个脚本。
- [Core concepts](../guides/core-concepts.md)：浏览器对象和标签页对象是如何配合的。
- [Selectors: CSS and XPath](selectors.md)：另一项前置知识，如何挑选和编写 selector。
