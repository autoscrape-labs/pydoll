# 事件系统

Pydoll 的事件系统允许您实时监听和响应浏览器活动。这对于构建动态自动化、监控网络请求、检测页面更改和创建响应式工作流至关重要。

!!! info "提供深入探讨"
    本指南专注于实际使用。有关架构细节和内部实现，请参阅[事件架构深入探讨](../../deep-dive/event-architecture.md)。

## 前提条件

在使用事件之前，您需要启用相应的 CDP 域：

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    
    # 在监听事件之前启用域
    await tab.enable_page_events()     # 用于页面生命周期事件
    await tab.enable_network_events()  # 用于网络活动
    await tab.enable_dom_events()      # 用于 DOM 更改
```

!!! warning "不启用事件将不会触发"
    如果您注册了回调但忘记启用域，您的回调将永远不会被触发。始终先启用域！

## 基本事件监听

`on()` 方法注册事件监听器：

```python
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

async def handle_page_load(event: LoadEventFiredEvent):
    print(f"页面在 {event['params']['timestamp']} 加载完成")

# 注册回调
await tab.enable_page_events()
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_page_load)
```

### 事件结构

所有事件遵循相同的结构：

```python
{
    'method': 'Page.loadEventFired',  # 事件名称
    'params': {                        # 事件特定数据
        'timestamp': 123456.789
    }
}
```

通过 `event['params']` 访问事件数据：

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

async def handle_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    print(f"{method} {url}")
```

### 使用类型提示以获得更好的 IDE 支持

使用事件参数类型的类型提示来获取事件键的自动完成：

```python
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

# 使用类型提示 - IDE 知道所有可用的键！
async def handle_request(event: RequestWillBeSentEvent):
    # IDE 将自动完成 'params'、'request'、'url' 等
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    timestamp = event['params']['timestamp']
    print(f"{method} {url} 在 {timestamp}")

async def handle_load(event: LoadEventFiredEvent):
    # IDE 知道此事件在 params 中有 'timestamp'
    timestamp = event['params']['timestamp']
    print(f"页面在 {timestamp} 加载完成")

await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, handle_request)

await tab.enable_page_events()
await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_load)
```

!!! tip "事件参数的类型提示"
    所有事件类型都定义在 `pydoll.protocol.<domain>.events` 中。使用它们可以获得：
    
    - **自动完成**：IDE 建议 `event['params']` 中的可用键
    - **类型安全**：在运行代码之前捕获拼写错误
    - **文档**：查看每个事件提供的数据
    
    事件类型遵循模式：`<EventName>Event`（例如，`RequestWillBeSentEvent`、`ResponseReceivedEvent`）

## 常见事件域

### 页面事件

监控页面生命周期和对话框：

```python
from pydoll.protocol.page.events import PageEvent, JavascriptDialogOpeningEvent

await tab.enable_page_events()

# 页面已加载
await tab.on(PageEvent.LOAD_EVENT_FIRED, lambda e: print("页面已加载！"))

# DOM 就绪
await tab.on(PageEvent.DOM_CONTENT_EVENT_FIRED, lambda e: print("DOM 就绪！"))

# JavaScript 对话框
async def handle_dialog(event: JavascriptDialogOpeningEvent):
    message = event['params']['message']
    dialog_type = event['params']['type']
    print(f"对话框 ({dialog_type}): {message}")
    
    # 自动处理
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)

await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, handle_dialog)
```

### 网络事件

监控请求和响应：

```python
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

await tab.enable_network_events()

# 跟踪请求
async def log_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"→ {request['method']} {request['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# 跟踪响应
async def log_response(event: ResponseReceivedEvent):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")

await tab.on(NetworkEvent.RESPONSE_RECEIVED, log_response)

# 跟踪失败
async def log_failure(event: LoadingFailedEvent):
    url = event['params']['type']
    error = event['params']['errorText']
    print(f"[失败] {url} - {error}")

await tab.on(NetworkEvent.LOADING_FAILED, log_failure)
```

### DOM 事件

响应 DOM 更改：

```python
from pydoll.protocol.dom.events import DomEvent, AttributeModifiedEvent

await tab.enable_dom_events()

# 跟踪属性更改
async def on_attribute_change(event: AttributeModifiedEvent):
    node_id = event['params']['nodeId']
    attr_name = event['params']['name']
    attr_value = event['params']['value']
    print(f"节点 {node_id}: {attr_name}={attr_value}")

await tab.on(DomEvent.ATTRIBUTE_MODIFIED, on_attribute_change)

# 跟踪文档更新
await tab.on(DomEvent.DOCUMENT_UPDATED, lambda e: print("文档已更新！"))
```

## 临时回调

使用 `temporary=True` 进行一次性监听器：

```python
from pydoll.protocol.page.events import PageEvent

# 这只会触发一次，然后自动删除
await tab.on(
    PageEvent.LOAD_EVENT_FIRED,
    lambda e: print("首次加载！"),
    temporary=True
)

await tab.go_to("https://example.com")  # 触发回调
await tab.refresh()                      # 回调不会再次触发
```

!!! tip "非常适合一次性设置"
    临时回调非常适合只应发生一次的初始化任务。

## 在回调中访问 Tab

使用 `functools.partial` 将 tab 传递给您的回调：

```python
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def process_response(tab, event: ResponseReceivedEvent):
    # 现在我们可以使用 tab 对象！
    request_id = event['params']['requestId']
    
    # 获取响应体
    body = await tab.get_network_response_body(request_id)
    print(f"响应体: {body[:100]}...")

await tab.enable_network_events()
await tab.on(
    NetworkEvent.RESPONSE_RECEIVED,
    partial(process_response, tab)
)
```

!!! info "为什么使用 Partial？"
    事件系统只将事件数据传递给回调。`partial` 允许您绑定其他参数，如 tab 实例。

## 管理回调

### 删除回调

```python
from pydoll.protocol.page.events import PageEvent

# 保存回调 ID
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, my_callback)

# 稍后删除它
await tab.remove_callback(callback_id)
```

### 清除所有回调

```python
# 删除此 tab 的所有已注册回调
await tab.clear_callbacks()
```

## 实用示例

### 监控 API 调用

```python
import asyncio
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def monitor_api_calls(tab):
    collected_data = []
    
    # 类型提示帮助 IDE 自动完成事件键
    async def capture_api_response(tab, data_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # 仅过滤 API 调用
        if '/api/' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        data_list.append({
            'url': url,
            'body': body,
            'status': event['params']['response']['status']
        })
        print(f"捕获 API 调用: {url}")
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_api_response, tab, collected_data)
    )
    
    # 导航并收集
    await tab.go_to("https://example.com")
    await asyncio.sleep(3)  # 等待请求完成
    
    return collected_data
```

### 等待特定事件

```python
import asyncio
from pydoll.protocol.page.events import PageEvent, FrameNavigatedEvent

async def wait_for_navigation():
    navigation_done = asyncio.Event()
    
    async def on_navigated(event: FrameNavigatedEvent):
        navigation_done.set()
    
    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)
    
    # 触发导航
    button = await tab.find(id='next-page')
    await button.click()
    
    # 等待它完成
    await navigation_done.wait()
    print("导航完成！")
```

### 网络空闲检测

```python
import asyncio
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    LoadingFinishedEvent,
    LoadingFailedEvent
)

async def wait_for_network_idle(tab, timeout=5):
    in_flight = 0
    idle_event = asyncio.Event()
    last_activity = asyncio.get_event_loop().time()
    
    async def on_request(event: RequestWillBeSentEvent):
        nonlocal in_flight, last_activity
        in_flight += 1
        last_activity = asyncio.get_event_loop().time()
    
    async def on_finished(event: LoadingFinishedEvent | LoadingFailedEvent):
        nonlocal in_flight, last_activity
        in_flight -= 1
        last_activity = asyncio.get_event_loop().time()
        
        if in_flight == 0:
            idle_event.set()
    
    await tab.enable_network_events()
    req_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
    fin_id = await tab.on(NetworkEvent.LOADING_FINISHED, on_finished)
    fail_id = await tab.on(NetworkEvent.LOADING_FAILED, on_finished)
    
    try:
        await asyncio.wait_for(idle_event.wait(), timeout=timeout)
        print("网络空闲！")
    except asyncio.TimeoutError:
        print(f"{timeout}秒后网络仍然活跃")
    finally:
        # 清理
        await tab.remove_callback(req_id)
        await tab.remove_callback(fin_id)
        await tab.remove_callback(fail_id)
```

### 动态内容抓取

```python
import asyncio
import json
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def scrape_infinite_scroll(tab, max_items=100):
    items = []
    
    async def capture_products(tab, items_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # 查找产品 API 端点
        if '/products' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        try:
            data = json.loads(body)
            if 'items' in data:
                items_list.extend(data['items'])
                print(f"收集了 {len(data['items'])} 个项目（总计: {len(items_list)}）")
        except json.JSONDecodeError:
            pass
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_products, tab, items)
    )
    
    await tab.go_to("https://example.com/products")
    
    # 滚动以触发无限加载
    while len(items) < max_items:
        await tab.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
    
    return items[:max_items]
```

## 事件参考表

### 可用域

| 域 | 启用方法 | 常见用例 |
|--------|--------------|------------------|
| Page | `enable_page_events()` | 页面生命周期、导航、对话框 |
| Network | `enable_network_events()` | 请求/响应监控、API 跟踪 |
| DOM | `enable_dom_events()` | DOM 结构更改、属性修改 |
| Fetch | `enable_fetch_events()` | 请求拦截和修改 |
| Runtime | `enable_runtime_events()` | 控制台消息、JavaScript 异常 |

### 关键页面事件

| 事件 | 何时触发 | 用例 |
|-------|---------------|----------|
| `LOAD_EVENT_FIRED` | 页面加载完成 | 等待完整页面加载 |
| `DOM_CONTENT_EVENT_FIRED` | DOM 就绪 | 开始 DOM 操作 |
| `JAVASCRIPT_DIALOG_OPENING` | Alert/confirm/prompt | 自动处理对话框 |
| `FRAME_NAVIGATED` | 导航完成 | 跟踪 SPA 导航 |
| `FILE_CHOOSER_OPENED` | 文件输入被点击 | 自动化文件上传 |

### 关键网络事件

| 事件 | 何时触发 | 用例 |
|-------|---------------|----------|
| `REQUEST_WILL_BE_SENT` | 请求发送前 | 记录/修改传出请求 |
| `RESPONSE_RECEIVED` | 接收响应头 | 捕获 API 响应 |
| `LOADING_FINISHED` | 响应体加载完成 | 获取完整响应数据 |
| `LOADING_FAILED` | 请求失败 | 跟踪错误和重试 |
| `WEB_SOCKET_CREATED` | WebSocket 打开 | 监控实时连接 |

### 关键 DOM 事件

| 事件 | 何时触发 | 用例 |
|-------|---------------|----------|
| `DOCUMENT_UPDATED` | DOM 重建 | 刷新元素引用 |
| `ATTRIBUTE_MODIFIED` | 元素属性更改 | 跟踪动态属性更改 |
| `CHILD_NODE_INSERTED` | 添加新元素 | 检测动态添加的内容 |
| `CHILD_NODE_REMOVED` | 删除元素 | 检测删除的内容 |

### 事件类型参考

所有事件类型及其参数结构都定义在协议模块中：

| 域 | 导入路径 | 示例类型 |
|--------|-------------|---------------|
| Page | `pydoll.protocol.page.events` | `LoadEventFiredEvent`、`FrameNavigatedEvent`、`JavascriptDialogOpeningEvent` |
| Network | `pydoll.protocol.network.events` | `RequestWillBeSentEvent`、`ResponseReceivedEvent`、`LoadingFinishedEvent` |
| DOM | `pydoll.protocol.dom.events` | `DocumentUpdatedEvent`、`AttributeModifiedEvent`、`ChildNodeInsertedEvent` |
| Fetch | `pydoll.protocol.fetch.events` | `RequestPausedEvent`、`AuthRequiredEvent` |
| Runtime | `pydoll.protocol.runtime.events` | `ConsoleAPICalledEvent`、`ExceptionThrownEvent` |

每个事件类型都是一个 `TypedDict`，定义了事件的确切结构，包括 `params` 字典中的所有可用键。

## 最佳实践

### 1. 始终先启用域

```python
from pydoll.protocol.network.events import NetworkEvent

# 好
await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)

# 坏：回调永远不会触发
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)
await tab.enable_network_events()
```

### 2. 完成后清理

```python
from pydoll.protocol.network.events import NetworkEvent

# 为特定任务启用
await tab.enable_network_events()
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# 执行您的工作...
await tab.go_to("https://example.com")

# 清理
await tab.remove_callback(callback_id)
await tab.disable_network_events()
```

### 3. 使用早期过滤

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

# 好：早期过滤
async def handle_api_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    if '/api/' not in url:
        return  # 提前退出
    
    # 仅处理 API 请求
    process_request(event)

# 坏：处理所有内容
async def handle_all_requests(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    process_request(event)
    if '/api/' in url:
        do_extra_work(event)
```

### 4. 优雅地处理错误

```python
from pydoll.protocol.network.events import ResponseReceivedEvent

async def safe_callback(event: ResponseReceivedEvent):
    try:
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        process_body(body)
    except KeyError:
        # 事件可能没有 requestId
        pass
    except Exception as e:
        print(f"回调中的错误: {e}")
        # 继续而不中断事件循环
```

## 性能注意事项

!!! warning "高频事件"
    DOM 事件在动态页面上可能**非常频繁地**触发。使用过滤和防抖动以避免性能问题。

### 按域划分的事件量

| 域 | 事件频率 | 性能影响 |
|--------|----------------|-------------------|
| Page | 低 | 最小 |
| Network | 中-高 | 中等 |
| DOM | 非常高 | 高 |
| Fetch | 中等 | 中等 |

### 优化技巧

1. **仅启用您需要的**：不要一次启用所有域
2. **使用临时回调**：尽可能自动清理
3. **早期过滤**：在昂贵的操作之前检查条件
4. **完成后禁用**：释放资源
5. **避免繁重的处理**：保持回调快速，将工作卸载到单独的任务

```python
import asyncio
from pydoll.protocol.network.events import ResponseReceivedEvent

# 好：快速回调，卸载繁重的工作
async def handle_response(event: ResponseReceivedEvent):
    if should_process(event):
        asyncio.create_task(heavy_processing(event))  # 不阻塞

# 坏：阻塞事件循环
async def handle_response(event: ResponseReceivedEvent):
    await heavy_processing(event)  # 阻塞其他事件
```

## 常见模式

### 事件的上下文管理器

```python
from contextlib import asynccontextmanager
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

@asynccontextmanager
async def monitor_requests(tab):
    """在块期间监控请求的上下文管理器。"""
    requests = []
    
    async def capture(event: RequestWillBeSentEvent):
        requests.append(event['params']['request'])
    
    await tab.enable_network_events()
    cb_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, capture)
    
    try:
        yield requests
    finally:
        await tab.remove_callback(cb_id)
        await tab.disable_network_events()

# 用法
async with monitor_requests(tab) as requests:
    await tab.go_to("https://example.com")
    # 捕获所有请求

print(f"捕获了 {len(requests)} 个请求")
```

### 条件事件注册

```python
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.dom.events import DomEvent

async def setup_monitoring(tab, track_network=False, track_dom=False):
    """仅启用指定的监控。"""
    callbacks = []
    
    if track_network:
        await tab.enable_network_events()
        cb = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)
        callbacks.append(('network', cb))
    
    if track_dom:
        await tab.enable_dom_events()
        cb = await tab.on(DomEvent.ATTRIBUTE_MODIFIED, log_dom_change)
        callbacks.append(('dom', cb))
    
    return callbacks
```

## 进一步阅读

- **[事件架构深入探讨](../../deep-dive/event-architecture.md)** - 内部实现和 WebSocket 通信
- **[网络监控](../network/monitoring.md)** - 高级网络分析技术
- **[响应式自动化](reactive-automation.md)** - 构建事件驱动的工作流

!!! tip "从简单开始"
    从 Page 事件开始了解基础知识，然后根据需要转向 Network 和 DOM 事件。事件系统很强大，但一开始可能会让人不知所措。