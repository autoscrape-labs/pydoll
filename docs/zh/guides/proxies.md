# Proxy

让浏览器的流量经过 proxy，可以更换你的出口 IP、把请求分散到多个地址，或从另一个地区访问某个站点。你用一个启动参数就能设置 proxy，而 Pydoll 会替你处理 proxy 认证。

<iframe scrolling="no" src="/docs/resources/visuals/proxy-routing.html" aria-label="A request routed direct versus through a proxy, changing the IP the target sees" style="width: 100%; height: 300px; border: 0;" loading="lazy"></iframe>

## 设置 proxy

给 `ChromiumOptions` 传入 `--proxy-server`，浏览器发出的每个请求都会经过它。HTTP、HTTPS 和 SOCKS5 的 URL 都可以：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--proxy-server=http://proxy.example.com:8080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        response = await tab.request.get('https://httpbin.org/ip')
        print(response.json())   # {'origin': '<the proxy IP>'}

asyncio.run(main())
```

`tab.request.get` 在浏览器上下文中运行，所以它会经过与页面相同的 proxy。请看 [HTTP 请求](http-requests.md)。

## 使用带认证的 proxy

大多数付费 proxy 需要用户名和密码。把凭据放进 proxy URL，Pydoll 会替你应答认证质询，这样导航就能正常工作：

```python
options = ChromiumOptions()
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')
```

你不用写任何认证代码。在底层，Pydoll 会在浏览器级别启用 Chrome 的 Fetch 域；当 proxy 返回 407 质询时，Chrome 会暂停该请求，Pydoll 则用你 URL 里的凭据来应答。基于公开 API 构建的等价处理器长这样：

```python
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def on_auth_required(event):
    await tab.continue_with_auth(
        request_id=event['params']['requestId'],
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='pass',
    )
```

!!! warning "Chrome 不支持 SOCKS5 认证"
    Chrome 会忽略 `socks5://user:pass@host:port` URL 中的凭据（[Chromium issue 40323993](https://issues.chromium.org/issues/40323993)）：它既不发送这些凭据，也不会发出 Pydoll 本可应答的 407 质询。请运行一个替你处理凭据的本地无认证 SOCKS5 转发器，并让 Chrome 指向它：

    ```python
    import asyncio

    from pydoll.utils import SOCKS5Forwarder
    from pydoll.browser.chromium import Chrome
    from pydoll.browser.options import ChromiumOptions


    async def main():
        forwarder = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='myuser',
            password='mypass',
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())
    ```

    Chrome 无需认证即可连接到 `127.0.0.1`；转发器则与远程 proxy 完成用户名/密码握手。

## 为每个上下文使用不同的 proxy

一个 [浏览器上下文](browser-contexts.md) 可以携带自己的 proxy，所以一次浏览器运行可以让不同的标签页走不同的 proxy。在创建上下文时传入 `proxy_server`：

```python
async with Chrome() as browser:
    await browser.start()

    us_ctx = await browser.create_browser_context(proxy_server='http://user:pass@us.proxy.com:8080')
    de_ctx = await browser.create_browser_context(proxy_server='http://user:pass@de.proxy.com:8080')

    us_tab = await browser.new_tab(browser_context_id=us_ctx)
    de_tab = await browser.new_tab(browser_context_id=de_ctx)

    print((await us_tab.request.get('https://httpbin.org/ip')).json())
    print((await de_tab.request.get('https://httpbin.org/ip')).json())
```

## 对某些主机跳过 proxy

用 `--proxy-bypass-list` 让某些主机走直连，这对本地开发服务器和内部资源很方便：

```python
options.add_argument('--proxy-server=http://proxy.example.com:8080')
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')
```

## 核实你的出口 IP

在长时间运行之前，确认流量确实是经由 proxy 出去的：

```python
async with Chrome(options=options) as browser:
    tab = await browser.start()
    ip = (await tab.request.get('https://httpbin.org/ip')).json()['origin']
    print(f'Egress IP: {ip}')
```

!!! note "proxy 只是众多检测信号之一"
    更换 IP 并不能让自动化不被检测，而选错 IP 只会让情况更糟。反机器人系统会权衡 IP 声誉（住宅地址看起来比数据中心网段合法得多），并把 IP 所在国家与浏览器的时区和语言交叉比对。让 proxy 的地理位置与你其余的配置相匹配，是构成一份自洽 fingerprint 的一部分，详见 [Fingerprint 注入](../stealth/fingerprint-injection.md)。

## 下一步

- [浏览器上下文](browser-contexts.md)：隔离会话，并给每个会话配上自己的 proxy。
- [Fingerprint 注入](../stealth/fingerprint-injection.md)：让 IP 的地理位置与浏览器身份的其余部分相匹配。
- [HTTP 请求](http-requests.md)：通过同一个 proxy 和会话调用 API。
- [网络与 proxy（深入）](../deep-dive/network/index.md)：proxy 如何工作，以及它们是如何被检测的。
