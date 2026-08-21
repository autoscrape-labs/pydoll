# 浏览器上下文的 HTTP 请求

`tab.request` 从浏览器内部发起 HTTP 调用，因此这些请求会自动带上页面的 cookies、会话和身份认证。只需通过界面登录一次，就能直接调用站点的 API：无需复制 cookies，也不用再维护一个与浏览器保持同步的第二个 HTTP 客户端。

## 发起第一个请求

`tab.request` 提供了一个类似 `requests` 的接口。用一个 URL 调用 `get()`，然后读取响应：

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

        print(response.status_code)   # 200
        print(response.json()['title'])

asyncio.run(main())
```

该调用通过浏览器自身的 `fetch` 执行，所以浏览器已经携带的一切（cookies、活跃的会话）都会随之带上。

## 登录后调用 API

浏览器上下文请求在登录之后最有用。像用户一样通过页面登录，然后用你刚刚建立的会话去调用站点的 API。你不需要提取 token 或复制 cookie，请求本身就已经完成了认证。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        # 1. 通过界面登录（这是你自己的、已认证的应用）
        await tab.go_to('https://yourapp.com/login')
        await (await tab.find(id='username')).type_text('tester', humanize=True)
        await (await tab.find(id='password')).type_text('secret', humanize=True)
        await (await tab.find(tag_name='button', type='submit')).click()

        # 2. 用已登录的会话调用 API
        response = await tab.request.get('https://yourapp.com/api/profile')
        print(response.json())

asyncio.run(main())
```

!!! note "无需处理 cookie"
    上面的代码没有复制任何 cookies，也没有传递 token。由于请求运行在浏览器上下文中，它使用的正是页面刚刚认证过的那个会话。

## 用 POST 发送数据

传入 `json=` 来发送一个 JSON 请求体（`Content-Type` 会自动为你设置好）：

```python
response = await tab.request.post(
    'https://jsonplaceholder.typicode.com/posts',
    json={'title': 'Automating the web', 'body': 'with pydoll', 'userId': 1},
)
print(response.status_code)          # 201
print(response.json()['id'])
```

若要改为发送表单编码的字段，请传入 `data=`。`data` 和 `json` 互斥：

```python
response = await tab.request.post(
    'https://httpbin.org/post',
    data={'username': 'tester', 'remember': 'true'},
)
print(response.json()['form'])       # {'username': 'tester', 'remember': 'true'}
```

当你需要发送原始请求体时，`data` 也接受 `str` 或 `bytes`。

## 添加请求头

请求头是一个 `HeaderEntry` 列表（一个带有 `name` 和 `value` 的类型化字典）。它们是叠加在浏览器自动请求头之上的，而不是替换：

```python
from pydoll.protocol.fetch.types import HeaderEntry

headers: list[HeaderEntry] = [
    {'name': 'X-API-Version', 'value': '2'},
    {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
]

response = await tab.request.get('https://httpbin.org/headers', headers=headers)
print(response.json()['headers'])
```

!!! tip "只添加自定义请求头"
    像 `X-API-Key` 或 `Authorization` 这样的自定义请求头会与浏览器自身的请求头一起发送。试图覆盖标准请求头（`User-Agent`、`Referer`）行为并不一致，所以把这些交给浏览器，只设置你自己的请求头。

## 读取响应

`Response` 对象与 `requests` 库保持一致。`text`、`content`、`status_code`、`ok`、`headers`、`cookies` 和 `url` 是属性；`json()` 和 `raise_for_status()` 是方法：

```python
response = await tab.request.get('https://jsonplaceholder.typicode.com/posts/1')

response.status_code     # 200
response.ok              # 2xx 和 3xx 为 True

response.text            # 以 str 形式返回的响应体
response.content         # 以 bytes 形式返回的响应体
response.json()          # 解析后的 JSON（dict 或 list）

response.url             # 经过所有重定向后的最终 URL

for header in response.headers:
    print(header['name'], header['value'])

for cookie in response.cookies:
    print(cookie['name'], cookie['value'])

response.raise_for_status()   # 遇到 4xx 或 5xx 状态时抛出异常
```

`response.url` 只保存最终的 URL。若要跟踪完整的重定向链，请用[网络监控](network-monitoring.md)来观察这些请求。

## 其他 HTTP 方法

`get` 和 `post` 涵盖了大部分工作；其余的动词在你需要时也都有，形式相同：

```python
await tab.request.put('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'edited'})
await tab.request.patch('https://jsonplaceholder.typicode.com/posts/1', json={'title': 'tweaked'})
await tab.request.delete('https://jsonplaceholder.typicode.com/posts/1')
await tab.request.head('https://httpbin.org/get')
await tab.request.options('https://httpbin.org/get')
```

若要在一次调用中完全控制动词和每一个选项，请使用 `tab.request.request(method, url, params=..., data=..., json=..., headers=...)`。

## 下一步

- [Cookies 与会话](cookies-and-sessions.md)：管理你的请求所继承的会话。
- [网络监控](network-monitoring.md)：观察页面发起的每一个请求，包括重定向。
- [请求拦截](request-interception.md)：在请求发送前更改或阻止它们。
