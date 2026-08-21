# 请求拦截

拦截让你置身于浏览器和网络之间。每一个匹配的请求都会在你的处理函数处暂停，由你决定是放行（原样或经过修改）、阻止它，还是用一个模拟响应自己来应答。可以用它来丢弃图片以提速、注入请求头，或在开发时伪造一个还不存在的 API。

这是[网络监控](network-monitoring.md)的主动版本，后者只观察流量，而拦截可以改变它。

<iframe src="/docs/resources/visuals/request-lifecycle.html" aria-label="What happens to an intercepted request under continue, block, or fulfill" style="width: 100%; height: 400px; border: 0;" loading="lazy"></iframe>

试试每个按钮：`continue_request()` 让请求到达服务器，`fail_request()` 丢弃它，`fulfill_request()` 由你的处理函数应答，完全不联系服务器。

## 启用拦截

拦截运行在 Chrome 的 Fetch 域上。启用它，为暂停请求事件注册一个处理函数，并对处理函数收到的每一个请求作出处置。

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def on_request(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    print(f'paused: {url}')
    await tab.continue_request(request_id)   # 原样放行


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(on_request, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! warning "对每个暂停的请求恰好处置一次"
    一个暂停的请求会一直挂住页面，直到你对它作出处置。每个请求都必须以 `continue_request`、`fail_request` 或 `fulfill_request` 三者之一结束，且恰好一次。漏掉一个，该请求就会挂起直到超时；调用两次，则会报错。把有风险的处理逻辑包在 `try`/`except` 里，并在 `except` 分支中继续该请求，这样一个 bug 就永远不会冻结页面。

## 只拦截你想要的请求

拦截会为每一个匹配的请求增加一次经过你处理函数的往返，所以要把范围收窄。传入 `resource_type` 可以只暂停一种请求，在处理函数中读取 `event['params']['resourceType']` 可进一步分支。

```python
from pydoll.protocol.network.types import ResourceType

# 只暂停 XHR/fetch 调用，不暂停文档、图片或样式
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
```

`ResourceType` 涵盖 `DOCUMENT`、`STYLESHEET`、`IMAGE`、`MEDIA`、`FONT`、`SCRIPT`、`XHR`、`FETCH` 等；完整集合请参见 `pydoll.protocol.network.types` 中的 `ResourceType` 枚举。

## 阻止请求

`fail_request` 会以一个错误原因丢弃请求。阻止图片和样式表是让抓取更快、更轻量的常见做法。

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ErrorReason


async def block_heavy(tab, event):
    request_id = event['params']['requestId']
    resource_type = event['params']['resourceType']

    if resource_type in ('Image', 'Stylesheet', 'Font'):
        await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(block_heavy, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

常见的 `ErrorReason` 值有 `BLOCKED_BY_CLIENT`（看起来像广告拦截器）、`FAILED`、`ABORTED`、`TIMED_OUT` 和 `CONNECTION_REFUSED`，可用于测试页面如何应对网络故障。完整列表是 `pydoll.protocol.network.types` 中的 `ErrorReason` 枚举。

## 修改请求

`continue_request` 可以在请求发出之前重写它：更改 URL、方法、请求头或请求体。请求头是一个 `HeaderEntry` 字典的列表（`{'name': ..., 'value': ...}`）。

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ResourceType


async def add_header(tab, event):
    request_id = event['params']['requestId']
    headers = [
        {'name': 'X-Automated-By', 'value': 'pydoll'},
    ]
    await tab.continue_request(request_id, headers=headers)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(add_header, tab))

        await tab.go_to('https://httpbin.org/headers')  # 回显它收到的请求头
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "你传入的请求头会替换掉原请求的请求头"
    提供 `headers` 会为该请求设置完整的请求头列表，它不会与浏览器的请求头合并。要把该请求仍然需要的请求头都包含进去，而不只是你正在添加的那一个。

你也可以通过传入 `url` 来改变请求的去向，或通过传入 `post_data` 来替换 `POST` 数据。

## 模拟响应

`fulfill_request` 由你自己来应答一个请求，因此永远不会联系服务器。这正是你在一个尚不存在的 API 上做开发、或强制返回某个特定载荷的方式。`body` 是 base64 编码的。

```python
import asyncio
import base64
import json
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def mock_json(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']

    if url.endswith('/json'):
        payload = {'source': 'mocked by pydoll', 'items': [1, 2, 3]}
        body = base64.b64encode(json.dumps(payload).encode()).decode()
        await tab.fulfill_request(
            request_id,
            response_code=200,
            response_headers=[{'name': 'Content-Type', 'value': 'application/json'}],
            body=body,
        )
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(mock_json, tab))

        await tab.go_to('https://httpbin.org/json')  # 正常情况下会返回一份示例文档
        await tab.disable_fetch_events()

asyncio.run(main())
```

## 拦截响应，而不只是请求

默认情况下，请求会在发送前暂停。传入 `request_stage=RequestStage.RESPONSE` 可以改为在响应到达后暂停，这样你就能检查或替换它。对于某个在请求阶段被继续的单个请求，`intercept_response=True` 会在它的响应到来后再次将其暂停。

```python
from pydoll.protocol.fetch.types import RequestStage

await tab.enable_fetch_events(request_stage=RequestStage.RESPONSE)
```

## 处理认证质询

设置 `handle_auth=True` 后，浏览器会抛出一个认证质询，你用 `continue_with_auth` 来应答。这涵盖了 HTTP Basic/Digest 认证（401）和 proxy 认证（407）。

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def answer_auth(tab, event):
    request_id = event['params']['requestId']
    await tab.continue_with_auth(
        request_id,
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='passwd',
    )


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(handle_auth=True)
        await tab.on(FetchEvent.AUTH_REQUIRED, partial(answer_auth, tab))

        await tab.go_to('https://httpbin.org/basic-auth/user/passwd')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "proxy 认证已经是自动的"
    对于普通的 proxy 你并不需要这个。当你在浏览器选项中设置了 proxy 凭据时，Pydoll 会替你应答 proxy 质询。只有在处理服务器认证或自定义凭据逻辑时，才需要手动使用 `continue_with_auth`。参见 [Proxy](proxies.md)。

## 下一步

- [网络监控](network-monitoring.md)：在不改变流量的前提下观察它。
- [事件](events.md)：拦截所构建于其上的事件模型。
- [Proxy](proxies.md)：将流量路由经过 proxy，认证会自动为你处理。
