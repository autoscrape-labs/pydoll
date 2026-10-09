# 等待

页面在加载之后还会变化：加载指示器消失，按钮变为可用，一次点击发出请求，提交表单触发导航。Pydoll 为这些时刻各提供一种等待，让你精确地等待所需的那件事，而不是靠睡眠碰运气。每种等待在超时后都会抛出 `WaitTimeout`（元素状态则抛出 `WaitElementTimeout`）。

## 等待元素状态

带 `timeout` 的 `find()` 等待元素出现。`wait_until()` 等待接下来发生的事：元素变为可见、隐藏、可用、可交互，或从页面中移除。设置一个或多个条件，调用会在全部条件成立时返回。

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            tab.find(tag_name='button').click()

            loading = tab.find(id='loading')
            loading.wait_until(is_hidden=True, timeout=10)

            print(tab.find(id='finish').text())

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            await (await tab.find(tag_name='button')).click()

            loading = await tab.find(id='loading')
            await loading.wait_until(is_hidden=True, timeout=10)

            print(await (await tab.find(id='finish')).text())

    asyncio.run(main())
    ```

可以设置的条件：

| 标志 | 成立条件 |
|------|----------|
| `is_visible` | 元素在屏幕上有盒子，且未被 CSS 隐藏。 |
| `is_hidden` | 与 `is_visible` 相反。 |
| `is_enabled` | 元素没有 `disabled` 属性。 |
| `is_interactable` | 元素可见、位于最上层，并且能接收点击。 |
| `is_detached` | 元素已从 DOM 中移除。 |

每个元素也能直接回答同样的问题：`is_visible()`、`is_interactable()`、`is_on_top()` 和 `is_detached()` 是方法，`is_enabled` 则是普通属性。

## 等待元素消失

当你从未持有该元素，或者新的 `find()` 会不断匹配到别的元素时，改在标签页上等待。`wait_for_absence()` 接受与 `find()` 相同的条件，在没有任何匹配时返回。

=== "Sync"

    ```python
    tab.find(text='开始').click()
    tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

=== "Async"

    ```python
    await (await tab.find(text='开始')).click()
    await tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

## 等待 URL

单页应用会在不加载页面的情况下改变 URL。`wait_for_url()` 轮询当前 URL 直到匹配，并返回匹配到的 URL。模式可以是 glob、编译好的正则表达式，或接收 URL 并返回 bool 的可调用对象。

=== "Sync"

    ```python
    import re

    tab.find(id='checkout').click()

    tab.wait_for_url('**/checkout/*', timeout=10)
    tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

=== "Async"

    ```python
    import re

    await (await tab.find(id='checkout')).click()

    await tab.wait_for_url('**/checkout/*', timeout=10)
    await tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    await tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

在 glob 中，`*` 匹配除 `/` 外的任意内容，`**` 匹配包括 `/` 在内的任意内容，`{a,b}` 匹配其中任一备选项。本指南中凡是接受 URL 模式的地方，这三种形式都适用。

## 等待 JavaScript 条件

`wait_for_script()` 在页面中反复求值一个表达式，直到它按 JavaScript 的规则为真，判断在页面一侧完成，因此 DOM 节点、函数或空对象都算找到，返回的 promise 会被等待。值是基本类型时返回该值，是对象时返回 `True`。脚本抛出错误时立即抛出 `ScriptEvaluationError`，`error_text` 携带 JavaScript 错误，而不是等到超时。用它等待 DOM 不显示的状态：应用设置的全局变量、某个 store 的就绪标志、一个计数。

=== "Sync"

    ```python
    tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

=== "Async"

    ```python
    await tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = await tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

## 等待网络安静下来

`wait_for_network_idle()` 在连续 `idle_time` 秒没有任何请求进行中时返回。请在启动请求的动作之后立刻调用它，因为只有调用之后发起的请求才会被计入。

=== "Sync"

    ```python
    tab.find(id='load-more').click()
    tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = tab.find(class_name='card', find_all=True)
    ```

=== "Async"

    ```python
    await (await tab.find(id='load-more')).click()
    await tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = await tab.find(class_name='card', find_all=True)
    ```

!!! note "永不安静的页面"
    分析信标和长轮询会让一些页面永远忙碌。在这类页面上，等待你需要的元素或响应，而不是整个网络。

## 捕获点击触发的响应

你想要的数据往往在页面获取的 JSON 里，而不在 DOM 中。`expect_response()` 是一个上下文管理器：进入它，在块内执行动作，块退出时句柄就持有第一个匹配的响应，包括响应体。

=== "Sync"

    ```python
    with tab.expect_response('**/api/prices*') as response:
        tab.find(id='refresh').click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

=== "Async"

    ```python
    async with tab.expect_response('**/api/prices*') as response:
        await (await tab.find(id='refresh')).click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

句柄暴露 `url`、`status`、`ok`（2xx 状态为真）、`headers`、`mime_type` 和 `request_id`，以及返回字节的 `body()`、`text()` 和 `json()`。在块内、任何东西到达之前读取字段会抛出 `WaitTimeout`。如果浏览器在收到头部之后加载失败，`status` 和 `headers` 仍然有值，而 `body()` 抛出 `WaitTimeout`。

`expect_request()` 对发出的那一侧以同样方式工作，其句柄暴露 `url`、`method`、`headers`、`post_data` 和 `resource_type`。

=== "Sync"

    ```python
    with tab.expect_request('**/api/search') as request:
        tab.find(id='search').click()

    print(request.method, request.post_data)
    ```

=== "Async"

    ```python
    async with tab.expect_request('**/api/search') as request:
        await (await tab.find(id='search')).click()

    print(request.method, request.post_data)
    ```

两个管理器在块内会按需打开网络事件，之后再关闭。你不需要自己管理 `enable_network_events()`。

## 等待你引发的导航

`go_to()` 本身就会等待页面加载。当导航是由点击或表单提交引发时，把它包在 `expect_navigation()` 里：块在主框架完成跳转（给出 `url` 时须匹配它）并达到 `options.page_load_state` 配置的加载状态后退出。

=== "Sync"

    ```python
    with tab.expect_navigation(url='**/dashboard'):
        tab.find(id='login').click()

    print(tab.current_url())
    ```

=== "Async"

    ```python
    async with tab.expect_navigation(url='**/dashboard'):
        await (await tab.find(id='login')).click()

    print(await tab.current_url())
    ```

## 先注册，再行动

三个 `expect_*` 管理器在你进入块时开始监听，动作放在块内。先做动作再等待，会错过在这中间到达的响应，而这恰恰是你要处理的快速情况。

=== "Sync"

    ```python
    # 点击触发时监听器已经就位
    with tab.expect_response('**/api/data') as response:
        tab.find(id='fetch').click()
    ```

=== "Async"

    ```python
    # 点击触发时监听器已经就位
    async with tab.expect_response('**/api/data') as response:
        await (await tab.find(id='fetch')).click()
    ```

## 完整示例：读取 API 而不是 DOM

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://quotes.toscrape.com/scroll')
            # 页面加载时会自己请求第 1 页；先等它到达，再去要第 2 页
            tab.find(class_name='quote', timeout=10)

            with tab.expect_response('**/api/quotes?page=2') as response:
                tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            tab.wait_for_network_idle(idle_time=0.5)

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com/scroll')
            # 页面加载时会自己请求第 1 页；先等它到达，再去要第 2 页
            await tab.find(class_name='quote', timeout=10)

            async with tab.expect_response('**/api/quotes?page=2') as response:
                await tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            await tab.wait_for_network_idle(idle_time=0.5)

    asyncio.run(main())
    ```

## 下一步

- [元素查找](element-finding.md)：带超时的 `find()`，在这一切之前的那个等待。
- [网络监控](network-monitoring.md)：观察页面上的每个请求，而不只是你期待的那一个。
- [事件](events.md)：在页面和网络事件发生时做出响应。
- [重试](retrying.md)：当等待超时时重新执行整个步骤。
