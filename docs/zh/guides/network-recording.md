# HAR 网络录制

录制页面在一次会话中发起的每一个请求，并将其导出为 HAR 文件，也就是标准的 HTTP Archive 格式。HAR 文件会把每个请求和响应连同请求头、响应体和时序一起捕获下来，并可在 Chrome DevTools 或任意 HAR 查看器中打开。可用于调试、性能分析，或作为测试的固定数据（fixture）。

## 录制一次会话

把你想要捕获的浏览过程包裹在 `tab.request.record()` 中。页面在这个代码块内请求的一切都会被录制，块退出后 `capture` 对象即准备就绪。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as capture:
            await tab.go_to('https://news.ycombinator.com')

        print(f'captured {len(capture.entries)} requests')

asyncio.run(main())
```

## 保存录制内容

`capture.save()` 会写出一个 `.har` 文件。在 Chrome DevTools（Network 选项卡，import）或任意 HAR 查看器中打开它，即可直观地检查流量。缺失的目录会自动为你创建。

```python
capture.save('flow.har')
capture.save('recordings/session-1/flow.har')
```

## 在代码中检查条目

`capture.entries` 是一个 HAR 条目列表。每个条目都有一个可以直接读取的 `request` 和 `response`，这对于在测试中对流量做断言、或提取特定的调用非常方便。

```python
async with tab.request.record() as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')

for entry in capture.entries:
    request = entry['request']
    response = entry['response']
    print(f"{request['method']} {request['url']} -> {response['status']}")

# 只保留失败的 API 调用
failed_api = [
    entry for entry in capture.entries
    if '/api/' in entry['request']['url'] and entry['response']['status'] >= 400
]
```

## 只录制某些资源类型

录制每一张图片、字体和样式表会产生很大的文件。传入 `resource_types` 可以只保留你关心的种类，这是仅捕获页面 API 流量的常用做法。

```python
from pydoll.protocol.network.types import ResourceType

# 只保留 fetch/XHR 调用，跳过文档、图片和样式
async with tab.request.record(
    resource_types=[ResourceType.FETCH, ResourceType.XHR]
) as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')
```

常见的 `ResourceType` 值有 `DOCUMENT`、`STYLESHEET`、`SCRIPT`、`IMAGE`、`FONT`、`MEDIA`、`FETCH`、`XHR` 和 `WEB_SOCKET`。完整列表请参见 `pydoll.protocol.network.types` 中的 `ResourceType` 枚举。

## 获取原始的 HAR 字典

`capture.to_dict()` 返回完整的 HAR 1.2 结构，这样你就可以自己处理它，或把它交给另一个工具，而不必写文件。

```python
har = capture.to_dict()
print(har['log']['version'])  # '1.2'

from collections import Counter

by_type = Counter(entry.get('_resourceType', 'Other') for entry in har['log']['entries'])
print(by_type)  # Counter({'Script': 5, 'Stylesheet': 3, 'Document': 1, ...})
```

!!! note "响应体"
    响应体是在每个请求完成后捕获的。图片和字体这类二进制内容会按照 HAR 规范以 base64 编码存储。

## 下一步

- [网络监控](network-monitoring.md)：实时观察请求并读取响应，无需录制文件。
- [请求拦截](request-interception.md)：在请求发生时暂停、修改、阻止或伪造它们。
- [浏览器上下文的 HTTP 请求](http-requests.md)：通过页面自身的会话发起已认证的请求。
