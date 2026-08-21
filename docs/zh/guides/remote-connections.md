# 远程连接

`browser.connect()` 会把 Pydoll 接入一个已经在运行的 Chrome，而不是启动一个新的。当你要驱动一个不是自己启动的浏览器时用它：容器里的、远程主机上的，或是在多次运行之间共享的长期实例。你得到的 `Tab` API 与你自己启动的浏览器完全一样。

## 用调试端口启动 Chrome

目标浏览器必须暴露 Chrome DevTools Protocol。用 `--remote-debugging-port` 启动它：

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-remote
```

这会在该端口上提供一个小型 JSON API。向它询问浏览器的 WebSocket 地址：

```bash
curl http://localhost:9222/json/version
```

响应中的 `webSocketDebuggerUrl` 字段（形如 `ws://localhost:9222/devtools/browser/<id>`）就是你要传给 Pydoll 的东西。

## 连接并操作标签页

创建一个 browser 对象，用 WebSocket 地址调用 `connect()`，然后像操作其他标签页一样使用返回的那个：

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    browser = Chrome()
    tab = await browser.connect('ws://localhost:9222/devtools/browser/<id>')

    print(await tab.title)

    await tab.go_to('https://news.ycombinator.com')
    headline = await tab.find(class_name='titleline')
    print(await headline.text)

    await browser.close()

asyncio.run(main())
```

`connect()` 返回第一个打开的标签页。用 `await browser.get_opened_tabs()` 访问其他标签页，方式和你自己启动浏览器时完全一样。请看 [标签页](tabs.md)。

!!! warning "用 `close()` 断开连接，而不是 `stop()`"
    这个浏览器不是你启动的，所以不要终止它。`await browser.close()` 只会关闭 Pydoll 的 WebSocket 连接，让浏览器继续为其他用途运行。`await browser.stop()` 会向浏览器发送关闭命令并杀掉进程，这适用于你自己启动的浏览器，而不是你接入的那个。

## 在代码里获取 WebSocket 地址

你通常在运行时发现该地址，而不是把它写死。用任意 HTTP 客户端查询这个 JSON 端点：

```python
import asyncio

import aiohttp
from pydoll.browser.chromium import Chrome


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:9222/json/version') as resp:
            ws_address = (await resp.json())['webSocketDebuggerUrl']

    browser = Chrome()
    tab = await browser.connect(ws_address)
    print(await tab.title)
    await browser.close()

asyncio.run(main())
```

对于另一台机器上的浏览器，把 `localhost` 替换成该服务器的地址，并从客户端查询 `http://<host>:9222/json/version`。

## 在容器中运行 Chrome

在 Docker 里，以 headless 启动 Chrome，绑定调试端口，并给一个足够大的共享内存段（Chrome 使用 `/dev/shm`，而 Docker 默认的 64MB 太小）：

```bash
docker run -d --shm-size=2g -p 127.0.0.1:9222:9222 \
  zenika/alpine-chrome \
  --no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222
```

然后从宿主机用 `browser.connect('ws://localhost:9222/devtools/browser/<id>')` 连接。`--remote-debugging-address=0.0.0.0` 允许来自容器外部的连接进入；`--no-sandbox` 在大多数容器里都是必需的。

!!! warning "绝不要把调试端口暴露到公网"
    一个可达的调试端口就等于对浏览器的完全控制权：每一个页面、cookie 和会话，外加任意 JavaScript。把它绑定到 localhost（就像 `-p 127.0.0.1:9222:9222` 那样），并通过 SSH 隧道（`ssh -L 9222:localhost:9222 user@host`）或私有网络访问远程端口，绝不要用公共接口。

## 用你自己的 CDP 工具包裹一个元素

如果你已经有了一套 CDP 集成，以及某个元素的 `objectId`，可以把它包进一个 Pydoll 的 `WebElement`，从而使用高层交互 API。为该页面的 WebSocket 构建一个 `ConnectionHandler`，然后传进去：

```python
from pydoll.connection import ConnectionHandler
from pydoll.elements.web_element import WebElement

connection = ConnectionHandler(ws_address='ws://localhost:9222/devtools/page/<id>')

button = WebElement(
    object_id='<objectId from your CDP call>',
    connection_handler=connection,
)

await button.wait_until(is_visible=True, timeout=5)
await button.click(x_offset=5, y_offset=5)

await connection.close()
```

`objectId` 就是 `Runtime.evaluate` 或 `DOM.resolveNode` 这类 CDP 命令为某个节点返回的东西。这样既能保留你现有的搭建，又能在其上借用 Pydoll 的等待与交互。

## 下一步

- [标签页](tabs.md)：操作远程浏览器已经打开的标签页。
- [浏览器选项](browser-options.md)：配置一个你自己启动的浏览器，而不是接入现成的。
- [网络监控](network-monitoring.md)：观察你所连接浏览器上的流量。
