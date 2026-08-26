# 重试

真实页面是不稳定的：元素晚了一拍才加载、一次导航中断、一个请求超时。`@retry` 装饰器会在函数抛出异常时重新运行它，于是一次瞬时故障就变成了第二次尝试，而不是一次崩溃，你的自动化代码也不必掺杂重试的样板逻辑。

## 重试一个不稳定的函数

用 `@retry` 装饰一个异步函数，并列出值得重试的异常。如果函数抛出其中之一，它就会再次运行，最多再运行 `max_retries` 次。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, ConnectionFailed


@retry(max_retries=3, exceptions=[WaitElementTimeout, ConnectionFailed])
async def scrape_title(url):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        heading = await tab.find(id='firstHeading', timeout=5)
        return await heading.text


async def main():
    title = await scrape_title('https://en.wikipedia.org/wiki/Web_scraping')
    print(title)


asyncio.run(main())
```

`max_retries` 计的是重试次数，而不是总尝试次数：`max_retries=3` 会运行函数一次，然后最多再运行三次，所以最多四次尝试。

## 只重试你预期到的失败

`@retry` 默认为 `exceptions=Exception`，它会对一切进行重试，包括你自己代码中的、第二次运行也修不好的 bug（一个拼写错误、一个写错的选择器、一个 `KeyError`）。改为指明具体的异常，这样真正的 bug 会立即暴露，而只有可恢复的失败才会被重试。

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, ConnectionFailed

@retry(max_retries=3, exceptions=[ElementNotFound, WaitElementTimeout, ConnectionFailed])
async def open_dashboard(tab):
    await tab.go_to('https://app.example.test/dashboard')
    return await tab.find(id='dashboard', timeout=10)
```

在浏览器自动化中值得重试的，是那些瞬时性的异常。常见选择：

- `WaitElementTimeout`、`ElementNotFound`：元素没能及时出现。
- `ElementNotVisible`、`ElementNotInteractable`、`ClickIntercepted`：元素存在，但还不能用。
- `ConnectionFailed`、`NetworkError`、`PageLoadTimeout`：页面或连接失败。

## 在两次尝试之间等待

当问题出在服务器慢时，立刻重试很少有用。传入 `delay`（秒）在两次尝试之间等待：

```python
@retry(max_retries=3, exceptions=[ConnectionFailed], delay=2)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## 指数退避

对于速率限制或过载的服务器，恒定的延迟仍然是在不停地锤它。设置 `exponential_backoff=True`，每次等待都会增长：当 `delay=1` 时，暂停依次为 2 秒、4 秒、8 秒，给服务器逐步更大的恢复余地。

```python
@retry(
    max_retries=4,
    exceptions=[ConnectionFailed, PageLoadTimeout],
    delay=1,
    exponential_backoff=True,
)
async def fetch(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

<iframe scrolling="no" src="/docs/resources/visuals/retry-backoff.html" aria-label="Fixed delay vs exponential backoff retry timeline" style="width: 100%; height: 290px; border: 0;" loading="lazy"></iframe>

运行每一种模式：固定延迟在每次尝试之间保持相同的间隔，而指数退避会把间隔翻倍（2 秒、4 秒、8 秒），让重试之间的间隔越拉越开。

## 在下一次尝试之前先恢复

`on_retry` 会在每次失败的尝试之后、下一次尝试之前运行一个异步函数。用它把页面恢复到一个良好的状态，例如在遇到失效元素或一个挡路的模态框后刷新页面。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout


class ProductScraper:
    def __init__(self, tab):
        self.tab = tab

    async def recover(self):
        await self.tab.refresh()
        await asyncio.sleep(1)

    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover,
        delay=1,
    )
    async def price(self):
        element = await self.tab.find(class_name='price', timeout=5)
        return await element.text
```

关于 `on_retry` 有两点需要知道：

- 它必须是一个异步函数，因为装饰器会 await 它。
- 当 callback 是一个方法时，把它定义在被装饰方法的**上方**、在类体中。Python 在类被构建时就会求值 `@retry(on_retry=recover)`，所以那个名字必须已经存在。

## 重试耗尽后抛出你自己的错误

默认情况下，当每次尝试都失败后，最后一个异常会被重新抛出。传入 `exception_to_raise`，可以给你的调用方呈现一个更清晰的错误：

```python
from pydoll.exceptions import ConnectionFailed


class SiteUnavailable(Exception):
    pass


@retry(
    max_retries=3,
    exceptions=[ConnectionFailed],
    exception_to_raise=SiteUnavailable('the site never responded'),
)
async def open_site(tab, url):
    await tab.go_to(url)
    return await tab.find(id='content', timeout=10)
```

## 下一步

- [事件](events.md)：对页面和网络事件作出反应，而不是盲目重试。
- [元素查找](element-finding.md)：`find()` 上的 `timeout` 已经会等待晚到的元素，无需任何重试。
- [Proxy](proxies.md)：当失败源自速率限制或封锁时，轮换出口 IP。
