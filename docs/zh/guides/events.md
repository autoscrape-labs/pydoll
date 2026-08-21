# 事件

事件让你能够对浏览器的行为实时作出反应：一个页面加载完成、一个请求发出、一个响应返回、一个对话框打开。你不必在循环里轮询和猜测，而是注册一个 callback，事件一触发，Pydoll 就运行它。

## 先启用，再监听

处理事件始终是同样的三个步骤：启用你关心的域，用 `on()` 注册一个 callback，然后让事件触发。在其域被启用之前注册的 callback 永远不会运行，所以要先启用。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.page.events import PageEvent


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async def on_load(event):
            print('page finished loading')

        await tab.enable_page_events()
        await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(2)

asyncio.run(main())
```

`on(event_name, callback)` 返回一个整数 id，你之后可以用它来移除该 callback。callback 可以是同步或异步的，它接收一个参数：事件本身。

<iframe src="/docs/resources/visuals/events-flow.html" aria-label="Events firing on a page and your callbacks running" style="width: 100%; height: 395px; border: 0;" loading="lazy"></iframe>

按下 Navigate：事件在页面上按顺序触发，你注册的 callback 会随着各自的事件触发而运行。

## 读取事件数据

每个事件都是一个字典，带有一个 `method` 名称和一个 `params` 载荷。你从 `event['params']` 中读取你需要的内容：

```python
{
    'method': 'Page.loadEventFired',
    'params': {'timestamp': 123456.789},
}
```

每种事件类型在 `pydoll.protocol.<domain>.events` 下都是一个 `TypedDict`，所以为 callback 添加类型提示会让你在 `params` 的键上获得自动补全：

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent


async def on_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")
```

下面的示例都假定有一个运行中的 `tab`，就像第一个示例里设置的那样。

## 观察网络请求和响应

启用网络域，就能看到每一个请求发出、每一个响应返回：

```python
from pydoll.protocol.network.events import NetworkEvent


async def on_request(event):
    print(f"→ {event['params']['request']['url']}")


async def on_response(event):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")


await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)

await tab.go_to('https://news.ycombinator.com')
```

若要修改或阻止请求而不只是观察它们，参见[请求拦截](request-interception.md)。

## 让监听器只运行一次

传入 `temporary=True`，callback 在第一次触发后就会移除自身。对于那种不应在之后每次加载时都重复的一次性设置，这正是你想要的：

```python
from pydoll.protocol.page.events import PageEvent

await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load, temporary=True)

await tab.go_to('https://the-internet.herokuapp.com')  # 触发一次
await tab.refresh()                                      # 不会再次触发
```

## 等待某个特定事件

当你需要暂停直到某件事发生时，事件天然地与 `asyncio.Event` 搭配。注册一个设置标志的临时监听器，触发动作，然后等待该标志：

```python
import asyncio

from pydoll.protocol.page.events import PageEvent


async def click_and_wait_for_navigation(tab):
    navigated = asyncio.Event()

    async def on_navigated(event):
        navigated.set()

    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)

    link = await tab.find(text='Form Authentication')
    await link.click()

    await navigated.wait()
    print('navigation finished')
```

## 在 callback 内部使用 tab

`on()` 只把事件传给你的 callback。若要同时使用 tab（例如读取响应体），用 `functools.partial` 把它绑定进去：

```python
from functools import partial

from pydoll.protocol.network.events import NetworkEvent


async def capture_json(tab, event):
    url = event['params']['response']['url']
    if '/api/' not in url:
        return
    request_id = event['params']['requestId']
    body = await tab.get_network_response_body(request_id)
    print(f'{url}: {body[:80]}')


await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_json, tab))
```

像上面那样尽早过滤：一旦发现事件不是你关心的，就立即返回，这样昂贵的工作只在该做时才运行。

## 处理 JavaScript 对话框

订阅对话框事件，就能自动应答 `alert`、`confirm` 和 `prompt` 弹框，而不是让它们卡住页面：

```python
from pydoll.protocol.page.events import PageEvent


async def on_dialog(event):
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)


await tab.enable_page_events()
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, on_dialog)
await tab.go_to('https://the-internet.herokuapp.com/javascript_alerts')
```

## 用完之后清理

让监听器的作用范围只限于需要它们的那部分工作。用 id 移除单个 callback，或者全部清除，并在你用完某个域之后禁用它：

```python
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# ... 做需要它的那部分工作 ...

await tab.remove_callback(callback_id)   # 移除一个
await tab.clear_callbacks()              # 或移除该标签页上的每一个 callback
await tab.disable_network_events()       # 停止该域
```

只启用你用得到的域。DOM 事件尤其在动态页面上触发得非常频繁，所以只在你需要时才订阅它们，并让 callback 保持快速；用 `asyncio.create_task` 把繁重的工作卸载到单独的任务里，这样它就不会拖住下一个事件。

## 事件域与关键事件

| 域 | 启用方式 | 用它来 |
|---|---|---|
| Page | `enable_page_events()` | 对加载、导航和对话框作出反应 |
| Network | `enable_network_events()` | 观察请求和响应 |
| Fetch | `enable_fetch_events()` | 拦截并修改请求 |
| DOM | `enable_dom_events()` | 对 DOM 变化作出反应 |
| Runtime | `enable_runtime_events()` | 读取控制台消息和异常 |

常用的事件常量（每个域在 `pydoll.protocol.<domain>.events` 中都有更多）：

| 常量 | 触发时机 |
|---|---|
| `PageEvent.LOAD_EVENT_FIRED` | 页面加载完成 |
| `PageEvent.DOM_CONTENT_EVENT_FIRED` | DOM 就绪 |
| `PageEvent.FRAME_NAVIGATED` | 一次导航完成 |
| `PageEvent.JAVASCRIPT_DIALOG_OPENING` | 一个 alert、confirm 或 prompt 打开 |
| `NetworkEvent.REQUEST_WILL_BE_SENT` | 一个请求即将发出 |
| `NetworkEvent.RESPONSE_RECEIVED` | 响应头到达 |
| `NetworkEvent.LOADING_FINISHED` | 响应体完全加载完毕 |

## 下一步

- [网络监控](network-monitoring.md)：用这些事件捕获并分析流量。
- [请求拦截](request-interception.md)：暂停、修改和阻止请求，而不只是观察它们。
- [重试](retrying.md)：用 `@retry` 装饰器重试不稳定的动作。
