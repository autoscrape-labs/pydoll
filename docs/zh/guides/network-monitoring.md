# 网络监控

Pydoll 让你可以观察页面发起的每一个请求、读取响应体、检查状态和时序，而这一切都来自浏览器本身。无需搭建 proxy，也不用安装证书；你只要启用网络域，流量就会送到你面前。

本指南讲的是观察流量。若要更改、阻止或伪造请求，请参阅[请求拦截](request-interception.md)。

## 实时观察请求

在导航之前启用网络事件，然后注册一个 callback。页面每发起一个请求，Pydoll 就会调用它。

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_request(tab, event):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, partial(on_request, tab))

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

要在导航**之前**启用该域；在启用之前发起的请求不会被捕获。

<iframe scrolling="no" src="/docs/resources/visuals/request-waterfall.html" aria-label="A request waterfall showing each request's start and duration as the page loads" style="width: 100%; height: 375px; border: 0;" loading="lazy"></iframe>

按下 Load：每个请求都显示为一根条形，其位置由它何时开始决定、宽度由它耗时多久决定，这正是网络事件在触发时所报告的内容。

## 读取响应体

响应体并不在事件里；一旦响应到达，你需要通过请求 id 去获取它。先匹配你关心的那个请求，然后调用 `get_network_response_body`。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)

        for log in await tab.get_network_logs():
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            if url.endswith('/json'):
                body = await tab.get_network_response_body(request_id)
                print(body)

asyncio.run(main())
```

!!! note "响应体仅在响应到达后才存在"
    响应体在请求完成后才可用。重定向和某些资源类型（例如图片）可能没有可读的响应体，所以当你遍历大量请求时，把这个调用包在 `try`/`except` 里。

## 导航之后获取日志

如果你不需要实时 callback，可以让 Pydoll 收集这些请求，之后再用 `get_network_logs` 读取。传入 `filter` 可以只保留包含某个子串的 URL。

```python
await tab.go_to('https://github.com')
await asyncio.sleep(3)

all_requests = await tab.get_network_logs()
api_requests = await tab.get_network_logs(filter='api.github.com')

print(f'{len(all_requests)} requests, {len(api_requests)} to the API')

for log in api_requests:
    print(log['params']['request']['url'])
```

## 对响应和失败作出反应

订阅响应可以检查状态码，订阅失败可以捕捉那些从未完成的请求。响应的 URL 和状态位于 `event['params']['response']` 之下；失败的原因在 `event['params']['errorText']` 中。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_response(event):
    response = event['params']['response']
    print(f"{response['status']} {response['url']}")


async def on_failed(event):
    print(f"failed: {event['params']['errorText']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

## 仅在需要时启用

在繁忙的页面上，网络事件会增加开销，所以只在自动化中真正需要它的那段代码前后启用，用完之后再禁用：

```python
await tab.enable_network_events()
await tab.go_to('https://github.com')
await asyncio.sleep(3)
logs = await tab.get_network_logs()
await tab.disable_network_events()
```

## 下一步

- [请求拦截](request-interception.md)：更改、阻止或应答请求，而不只是观察它们。
- [事件](events.md)：网络事件背后通用的启用、订阅与 callback 模型。
- [浏览器上下文的 HTTP 请求](http-requests.md)：直接从页面的会话中调用 API。
