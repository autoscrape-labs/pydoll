# HAR 网络录制

捕获浏览器会话期间的所有网络活动，并导出为标准 HAR (HTTP Archive) 1.2 文件。非常适合调试、性能分析和请求重放。

!!! tip "像专家一样调试"
    HAR 文件是录制网络流量的行业标准。您可以将它们直接导入 Chrome DevTools、Charles Proxy 或任何 HAR 查看器进行详细分析。

## 为什么使用 HAR 录制？

| 使用场景 | 优势 |
|---------|------|
| 调试失败的请求 | 查看确切的 headers、时序和响应体 |
| 性能分析 | 识别慢速请求和瓶颈 |
| 请求重放 | 重现精确的请求序列 |
| API 文档 | 捕获真实的请求/响应对 |
| 测试固件 | 录制真实流量用于测试模拟 |

## 快速开始

录制页面导航期间的所有网络流量：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def record_traffic():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as recording:
            await tab.go_to('https://example.com')

        # 保存录制为 HAR 文件
        recording.save('flow.har')
        print(f'捕获了 {len(recording.entries)} 个请求')

asyncio.run(record_traffic())
```

## 录制 API

### `tab.request.record()`

上下文管理器，捕获标签页上的所有网络流量。

```python
async with tab.request.record() as recording:
    # 此块内的所有网络活动都会被捕获
    await tab.go_to('https://example.com')
    await (await tab.find(id='search')).type_text('pydoll')
    await (await tab.find(type='submit')).click()
```

`recording` 对象提供：

| 属性/方法 | 描述 |
|----------|------|
| `recording.entries` | 捕获的 HAR 条目列表 |
| `recording.to_dict()` | 完整的 HAR 1.2 字典（用于自定义处理） |
| `recording.save(path)` | 保存为 HAR JSON 文件 |

### 保存录制

```python
# 保存为 HAR 文件（可以在 Chrome DevTools 中打开）
recording.save('flow.har')

# 保存到嵌套目录（自动创建）
recording.save('recordings/session1/flow.har')

# 访问原始 HAR 字典进行自定义处理
har_dict = recording.to_dict()
print(har_dict['log']['version'])  # "1.2"
```

### 检查条目

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

for entry in recording.entries:
    req = entry['request']
    resp = entry['response']
    print(f"{req['method']} {req['url']} -> {resp['status']}")
```

## 重放请求

重放之前录制的 HAR 文件，通过浏览器按顺序执行每个请求：

```python
async def replay_traffic():
    async with Chrome() as browser:
        tab = await browser.start()

        # 导航以设置会话上下文
        await tab.go_to('https://example.com')

        # 重放所有录制的请求
        responses = await tab.request.replay('flow.har')

        for resp in responses:
            print(f"状态: {resp.status_code}")

asyncio.run(replay_traffic())
```

### `tab.request.replay(path)`

| 参数 | 类型 | 描述 |
|------|------|------|
| `path` | `str \| Path` | 要重放的 HAR 文件路径 |

**返回：** `list[Response]` -- 每个重放请求的响应。

**抛出：** `HarReplayError` -- 如果 HAR 文件无效或无法读取。

## 高级用法

### 录制和重放工作流

```python
async def record_and_replay():
    async with Chrome() as browser:
        tab = await browser.start()

        # 步骤 1：录制原始会话
        async with tab.request.record() as recording:
            await tab.go_to('https://api.example.com')
            await tab.request.post(
                'https://api.example.com/data',
                json={'key': 'value'}
            )

        recording.save('api_session.har')

        # 步骤 2：稍后重放
        responses = await tab.request.replay('api_session.har')
```

### 过滤录制的条目

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

# 仅过滤 API 调用
api_entries = [
    e for e in recording.entries
    if '/api/' in e['request']['url']
]

# 仅过滤失败的请求
failed = [
    e for e in recording.entries
    if e['response']['status'] >= 400
]
```

### 自定义 HAR 处理

```python
har = recording.to_dict()

# 按类型统计请求
from collections import Counter
types = Counter(
    e.get('_resourceType', 'Other')
    for e in har['log']['entries']
)
print(types)  # Counter({'Document': 1, 'Script': 5, 'Stylesheet': 3, ...})
```

## HAR 文件格式

导出的 HAR 遵循 [HAR 1.2 规范](http://www.softwareishard.com/blog/har-12-spec/)。每个条目包含：

- **Request**：方法、URL、headers、查询参数、POST 数据
- **Response**：状态、headers、响应体内容（文本或 base64 编码）
- **Timings**：DNS、连接、SSL、发送、等待（TTFB）、接收
- **Metadata**：服务器 IP、连接 ID、资源类型

!!! note "响应体"
    响应体在每个请求完成后自动捕获。二进制内容（图像、字体等）存储为 base64 编码的字符串。
