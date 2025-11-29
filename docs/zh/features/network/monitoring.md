# 网络监控

Pydoll 中的网络监控允许您在浏览器自动化期间观察和分析 HTTP 请求、响应和其他网络活动。这对于调试、性能分析、API 测试和了解 Web 应用程序如何与服务器通信至关重要。

!!! info "Network 与 Fetch 域"
    **Network 域**用于被动监控（观察流量）。**Fetch 域**用于主动拦截（修改请求/响应）。本指南重点介绍监控。有关请求拦截，请参阅高级文档。

## 启用网络事件

在监控网络活动之前，您必须启用 Network 域：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 启用网络监控
        await tab.enable_network_events()
        
        # 现在导航
        await tab.go_to('https://api.github.com')
        
        # 完成后不要忘记禁用（可选但推荐）
        await tab.disable_network_events()

asyncio.run(main())
```

!!! warning "导航前启用"
    始终在导航**之前**启用网络事件以捕获所有请求。在启用之前发起的请求不会被捕获。

## 获取网络日志

启用网络事件后，Pydoll 会自动存储网络日志。您可以使用 `get_network_logs()` 检索它们：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_requests():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # 导航到页面
        await tab.go_to('https://httpbin.org/json')
        
        # 等待页面完全加载
        await asyncio.sleep(2)
        
        # 获取所有网络日志
        logs = await tab.get_network_logs()
        
        print(f"捕获的总请求数: {len(logs)}")
        
        for log in logs:
            request = log['params']['request']
            print(f"→ {request['method']} {request['url']}")

asyncio.run(analyze_requests())
```

!!! note "生产就绪的等待"
    上面的示例为简单起见使用 `asyncio.sleep(2)`。在生产代码中，请考虑使用更明确的等待策略：
    
    - 等待特定元素出现
    - 使用[事件系统](../advanced/event-system.md)来检测何时加载所有资源
    - 实现网络空闲检测（参见实时网络监控部分）
    
    这确保您的自动化等待的时间正好合适，不多不少。

### 过滤网络日志

您可以按 URL 模式过滤日志：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def filter_logs_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # 获取所有日志
        all_logs = await tab.get_network_logs()
        
        # 获取特定域的日志
        api_logs = await tab.get_network_logs(filter='api.example.com')
        
        # 获取特定端点的日志
        user_logs = await tab.get_network_logs(filter='/api/users')

asyncio.run(filter_logs_example())
```

## 理解网络事件结构

网络日志包含有关每个请求的详细信息。以下是结构：

### RequestWillBeSentEvent

此事件在即将发送请求时触发：

```python
{
    'method': 'Network.requestWillBeSent',
    'params': {
        'requestId': 'unique-request-id',
        'loaderId': 'loader-id',
        'documentURL': 'https://example.com',
        'request': {
            'url': 'https://api.example.com/data',
            'method': 'GET',  # 或 'POST'、'PUT'、'DELETE' 等
            'headers': {
                'User-Agent': 'Chrome/...',
                'Accept': 'application/json',
                ...
            },
            'postData': '...',  # 仅存在于 POST/PUT 请求
            'initialPriority': 'High',
            'referrerPolicy': 'strict-origin-when-cross-origin'
        },
        'timestamp': 1234567890.123,
        'wallTime': 1234567890.123,
        'initiator': {
            'type': 'script',  # 或 'parser'、'other'
            'stack': {...}  # 如果从脚本发起则有调用堆栈
        },
        'type': 'XHR',  # 资源类型：Document、Script、Image、XHR 等
        'frameId': 'frame-id',
        'hasUserGesture': False
    }
}
```

### 关键字段参考

| 字段 | 位置 | 类型 | 描述 |
|-------|----------|------|-------------|
| `requestId` | `params.requestId` | `str` | 此请求的唯一标识符 |
| `url` | `params.request.url` | `str` | 完整的请求 URL |
| `method` | `params.request.method` | `str` | HTTP 方法（GET、POST 等）|
| `headers` | `params.request.headers` | `dict` | 请求标头 |
| `postData` | `params.request.postData` | `str` | 请求体（POST/PUT）|
| `timestamp` | `params.timestamp` | `float` | 请求开始的单调时间 |
| `type` | `params.type` | `str` | 资源类型（Document、XHR、Image 等）|
| `initiator` | `params.initiator` | `dict` | 触发此请求的内容 |

## 获取响应体

要获取实际的响应内容，请使用 `get_network_response_body()`：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def fetch_api_response():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # 导航到 API 端点
        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)
        
        # 获取所有请求
        logs = await tab.get_network_logs()
        
        for log in logs:
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            
            # 仅获取 JSON 端点的响应
            if 'httpbin.org/json' in url:
                try:
                    # 获取响应体
                    response_body = await tab.get_network_response_body(request_id)
                    print(f"来自 {url} 的响应:")
                    print(response_body)
                except Exception as e:
                    print(f"无法获取响应体: {e}")

asyncio.run(fetch_api_response())
```

!!! warning "响应体可用性"
    响应体仅适用于已完成的请求。此外，某些响应类型（如图像或重定向）可能没有可访问的响应体。

## 实际用例

### 1. API 测试和验证

监控 API 调用以验证是否正在进行正确的请求：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def validate_api_calls():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # 导航到您的应用
        await tab.go_to('https://your-app.com')
        
        # 触发某些进行 API 调用的操作
        button = await tab.find(id='load-data-button')
        await button.click()
        await asyncio.sleep(2)
        
        # 获取 API 日志
        api_logs = await tab.get_network_logs(filter='/api/')
        
        print(f"\n📊 API 调用摘要:")
        print(f"总 API 调用数: {len(api_logs)}")
        
        for log in api_logs:
            request = log['params']['request']
            method = request['method']
            url = request['url']
            
            # 检查是否存在正确的认证标头
            headers = request.get('headers', {})
            has_auth = 'Authorization' in headers or 'authorization' in headers
            
            print(f"\n{method} {url}")
            print(f"  ✓ 有授权: {has_auth}")
            
            # 如果适用，验证 POST 数据
            if method == 'POST' and 'postData' in request:
                print(f"  📤 正文: {request['postData'][:100]}...")

asyncio.run(validate_api_calls())
```

### 2. 性能分析

分析请求时序并识别慢速资源：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_performance():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # 存储时序数据
        timings = []
        
        for log in logs:
            params = log['params']
            request_id = params['requestId']
            url = params['request']['url']
            resource_type = params.get('type', 'Other')
            
            timings.append({
                'url': url,
                'type': resource_type,
                'timestamp': params['timestamp']
            })
        
        # 按时间戳排序
        timings.sort(key=lambda x: x['timestamp'])
        
        print("\n⏱️  请求时间线:")
        start_time = timings[0]['timestamp'] if timings else 0
        
        for timing in timings[:20]:  # 显示前 20 个
            elapsed = (timing['timestamp'] - start_time) * 1000  # 转换为毫秒
            print(f"{elapsed:7.0f}ms | {timing['type']:12} | {timing['url'][:80]}")

asyncio.run(analyze_performance())
```

### 3. 检测外部资源

查找您的页面连接到的所有外部域：

```python
import asyncio
from urllib.parse import urlparse
from collections import Counter
from pydoll.browser.chromium import Chrome

async def analyze_domains():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # 计算每个域的请求数
        domains = Counter()
        
        for log in logs:
            url = log['params']['request']['url']
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains[domain] += 1
            except:
                pass
        
        print("\n🌐 外部域:")
        for domain, count in domains.most_common(10):
            print(f"  {count:3} 个请求 | {domain}")

asyncio.run(analyze_domains())
```

### 4. 监控特定资源类型

跟踪特定类型的资源，如图像或脚本：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def track_resource_types():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(3)
        
        logs = await tab.get_network_logs()
        
        # 按资源类型分组
        by_type = {}
        
        for log in logs:
            params = log['params']
            resource_type = params.get('type', 'Other')
            url = params['request']['url']
            
            if resource_type not in by_type:
                by_type[resource_type] = []
            
            by_type[resource_type].append(url)
        
        print("\n📦 按类型分类的资源:")
        for rtype in sorted(by_type.keys()):
            urls = by_type[rtype]
            print(f"\n{rtype}: {len(urls)} 个资源")
            for url in urls[:3]:  # 显示前 3 个
                print(f"  • {url}")
            if len(urls) > 3:
                print(f"  ... 还有 {len(urls) - 3} 个")

asyncio.run(track_resource_types())
```

## 实时网络监控

对于实时监控，使用事件回调而不是轮询 `get_network_logs()`：

!!! info "理解事件"
    实时监控使用 Pydoll 的事件系统来响应发生的网络活动。要深入了解事件的工作原理，请参阅 **[事件系统](../advanced/event-system.md)**。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

async def real_time_monitoring():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 统计
        stats = {
            'requests': 0,
            'responses': 0,
            'failed': 0
        }
        
        # 请求回调
        async def on_request(event: RequestWillBeSentEvent):
            stats['requests'] += 1
            url = event['params']['request']['url']
            method = event['params']['request']['method']
            print(f"→ {method:6} | {url}")
        
        # 响应回调
        async def on_response(event: ResponseReceivedEvent):
            stats['responses'] += 1
            response = event['params']['response']
            status = response['status']
            url = response['url']
            
            # 按状态着色
            if 200 <= status < 300:
                color = '\033[92m'  # 绿色
            elif 300 <= status < 400:
                color = '\033[93m'  # 黄色
            else:
                color = '\033[91m'  # 红色
            reset = '\033[0m'
            
            print(f"← {color}{status}{reset} | {url}")
        
        # 失败回调
        async def on_failed(event: LoadingFailedEvent):
            stats['failed'] += 1
            error = event['params']['errorText']
            print(f"✗ 失败: {error}")
        
        # 启用并注册回调
        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)
        
        # 导航
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        print(f"\n📊 摘要:")
        print(f"  请求: {stats['requests']}")
        print(f"  响应: {stats['responses']}")
        print(f"  失败: {stats['failed']}")

asyncio.run(real_time_monitoring())
```

## 资源类型参考

Pydoll 捕获以下资源类型：

| 类型 | 描述 | 示例 |
|------|-------------|----------|
| `Document` | 主 HTML 文档 | 页面加载、iframe 源 |
| `Stylesheet` | CSS 文件 | 外部 .css、内联样式 |
| `Image` | 图像资源 | .jpg、.png、.gif、.webp、.svg |
| `Media` | 音频/视频文件 | .mp4、.webm、.mp3、.ogg |
| `Font` | Web 字体 | .woff、.woff2、.ttf、.otf |
| `Script` | JavaScript 文件 | .js 文件、内联脚本 |
| `TextTrack` | 字幕文件 | .vtt、.srt |
| `XHR` | XMLHttpRequest | AJAX 请求、旧版 API 调用 |
| `Fetch` | Fetch API 请求 | 现代 API 调用 |
| `EventSource` | 服务器发送事件 | 实时流 |
| `WebSocket` | WebSocket 连接 | 双向通信 |
| `Manifest` | Web 应用清单 | PWA 配置 |
| `Other` | 其他资源类型 | 杂项 |

## 高级：提取响应时序

网络事件包括详细的时序信息：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def analyze_timing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # 自定义回调以捕获时序
        timing_data = []
        
        async def on_response(event: ResponseReceivedEvent):
            response = event['params']['response']
            timing = response.get('timing')
            
            if timing:
                # 计算不同阶段
                dns_time = timing.get('dnsEnd', 0) - timing.get('dnsStart', 0)
                connect_time = timing.get('connectEnd', 0) - timing.get('connectStart', 0)
                ssl_time = timing.get('sslEnd', 0) - timing.get('sslStart', 0)
                send_time = timing.get('sendEnd', 0) - timing.get('sendStart', 0)
                wait_time = timing.get('receiveHeadersStart', 0) - timing.get('sendEnd', 0)
                receive_time = timing.get('receiveHeadersEnd', 0) - timing.get('receiveHeadersStart', 0)
                
                timing_data.append({
                    'url': response['url'][:50],
                    'dns': dns_time if dns_time > 0 else 0,
                    'connect': connect_time if connect_time > 0 else 0,
                    'ssl': ssl_time if ssl_time > 0 else 0,
                    'send': send_time,
                    'wait': wait_time,
                    'receive': receive_time,
                    'total': receive_time + wait_time + send_time
                })
        
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.go_to('https://github.com')
        await asyncio.sleep(5)
        
        # 打印时序分解
        print("\n⏱️  请求时序分解（毫秒）:")
        print(f"{'URL':<50} | {'DNS':>6} | {'连接':>8} | {'SSL':>6} | {'发送':>6} | {'等待':>6} | {'接收':>8} | {'总计':>7}")
        print("-" * 120)
        
        for data in sorted(timing_data, key=lambda x: x['total'], reverse=True)[:10]:
            print(f"{data['url']:<50} | {data['dns']:6.1f} | {data['connect']:8.1f} | {data['ssl']:6.1f} | "
                  f"{data['send']:6.1f} | {data['wait']:6.1f} | {data['receive']:8.1f} | {data['total']:7.1f}")

asyncio.run(analyze_timing())
```

## 时序字段说明

| 阶段 | 字段 | 描述 |
|-------|--------|-------------|
| **DNS** | `dnsStart` → `dnsEnd` | DNS 查找时间 |
| **连接** | `connectStart` → `connectEnd` | TCP 连接建立 |
| **SSL** | `sslStart` → `sslEnd` | SSL/TLS 握手 |
| **发送** | `sendStart` → `sendEnd` | 发送请求的时间 |
| **等待** | `sendEnd` → `receiveHeadersStart` | 等待服务器响应（TTFB）|
| **接收** | `receiveHeadersStart` → `receiveHeadersEnd` | 接收响应标头的时间 |

!!! tip "首字节时间（TTFB）"
    TTFB 是"等待"阶段 - 发送请求和接收响应的第一个字节之间的时间。这对于性能分析至关重要。

## 最佳实践

### 1. 仅在需要时启用网络事件

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_enable():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # ✅ 好：导航前启用，之后禁用
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        logs = await tab.get_network_logs()
        await tab.disable_network_events()
        
        # ❌ 不好：在整个会话期间保持启用
        # await tab.enable_network_events()
        # ... 长时间的自动化会话 ...
```

### 2. 过滤日志以减少内存使用

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_filter():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # ✅ 好：过滤特定请求
        api_logs = await tab.get_network_logs(filter='/api/')
        
        # ❌ 不好：当您只需要特定日志时获取所有日志
        all_logs = await tab.get_network_logs()
        filtered = [log for log in all_logs if '/api/' in log['params']['request']['url']]
```

### 3. 安全地处理缺失字段

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_safe_access():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        logs = await tab.get_network_logs()
        
        # ✅ 好：使用 .get() 安全访问
        for log in logs:
            params = log.get('params', {})
            request = params.get('request', {})
            url = request.get('url', 'Unknown')
            post_data = request.get('postData')  # 可能为 None
            
            if post_data:
                print(f"POST 数据: {post_data}")
        
        # ❌ 不好：直接访问可能引发 KeyError
        # url = log['params']['request']['url']
        # post_data = log['params']['request']['postData']  # 可能不存在！
```

### 4. 对实时需求使用事件回调

```python
import asyncio
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

# ✅ 好：使用回调进行实时监控
async def on_request(event: RequestWillBeSentEvent):
    print(f"新请求: {event['params']['request']['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# ❌ 不好：重复轮询日志（效率低）
while True:
    logs = await tab.get_network_logs()
    # 处理日志...
    await asyncio.sleep(0.5)  # 浪费！
```

## 另请参阅

- **[CDP Network 域](../../deep-dive/network-capabilities.md)** - 深入了解网络功能
- **[事件系统](../advanced/event-system.md)** - 了解 Pydoll 的事件架构
- **[请求拦截](interception.md)** - 修改请求和响应
