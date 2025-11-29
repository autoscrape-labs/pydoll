# 浏览器上下文 HTTP 请求

发起自动继承浏览器会话状态、Cookie 和身份验证的 HTTP 请求。非常适合结合 UI 导航和 API 效率的混合自动化。

!!! tip "混合自动化的游戏规则改变者"
    曾经希望您可以发起自动获取所有浏览器 Cookie 和身份验证的 HTTP 请求吗？现在您可以了！`tab.request` 属性为您提供了一个漂亮的类似 `requests` 的接口，可以**直接在浏览器的 JavaScript 上下文中**执行 HTTP 调用。

## 为什么使用浏览器上下文请求？

传统自动化通常需要您手动提取 Cookie 和标头以进行 API 调用。浏览器上下文请求消除了这种麻烦：

| 传统方法 | 浏览器上下文请求 |
|---------------------|-------------------------|
| 手动提取 Cookie | Cookie 自动继承 |
| 管理会话令牌 | 会话状态保留 |
| 单独处理 CORS | 遵守 CORS 策略 |
| 同时使用两个 HTTP 客户端 | 一个统一的接口 |
| 同步身份验证状态 | 始终已认证 |

**非常适合：**

- 通过 UI 登录后抓取已认证的 API
- 混合工作流，混合浏览器交互和 API 调用
- 测试已认证的端点而无需管理令牌
- 绕过复杂的身份验证流程
- 使用单页应用程序（SPA）

## 快速入门

最简单的示例：通过 UI 登录，然后进行已认证的 API 调用：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def hybrid_automation():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 1. 通过 UI 正常登录
        await tab.go_to('https://example.com/login')
        await (await tab.find(id='username')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password123')
        await (await tab.find(id='login-btn')).click()
        
        # 登录后等待重定向
        await asyncio.sleep(2)
        
        # 2. 现在使用已认证的会话进行 API 调用！
        response = await tab.request.get('https://example.com/api/user/profile')
        user_data = response.json()
        
        print(f"登录为: {user_data['name']}")
        print(f"邮箱: {user_data['email']}")

asyncio.run(hybrid_automation())
```

!!! success "无需 Cookie 管理"
    注意我们没有提取或传递任何 Cookie？请求自动继承了浏览器的已认证会话！

## 常见用例

### 1. 抓取已认证的 API

使用 UI 登录，然后使用 API 提取数据：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scrape_user_data():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 通过 UI 登录（处理复杂的认证流程）
        await tab.go_to('https://app.example.com/login')
        await (await tab.find(id='email')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password')
        await (await tab.find(type='submit')).click()
        await asyncio.sleep(2)
        
        # 现在通过 API 提取数据（比抓取 UI 快得多）
        all_users = []
        for page in range(1, 6):
            response = await tab.request.get(
                f'https://app.example.com/api/users',
                params={'page': str(page), 'limit': '100'}
            )
            users = response.json()['users']
            all_users.extend(users)
            print(f"第 {page} 页: 获取了 {len(users)} 个用户")
        
        print(f"抓取的总用户数: {len(all_users)}")

asyncio.run(scrape_user_data())
```

### 2. 测试受保护的端点

测试 API 端点而无需管理身份验证令牌：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_api_endpoints():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 一次性认证
        await tab.go_to('https://api.example.com/login')
        # ... 执行登录 ...
        await asyncio.sleep(2)
        
        # 测试多个端点
        endpoints = [
            '/api/users/me',
            '/api/settings',
            '/api/notifications',
            '/api/dashboard/stats'
        ]
        
        for endpoint in endpoints:
            response = await tab.request.get(f'https://api.example.com{endpoint}')
            
            if response.ok:
                print(f"成功 {endpoint}: {response.status_code}")
            else:
                print(f"失败 {endpoint}: {response.status_code}")
                print(f"   错误: {response.text[:100]}")

asyncio.run(test_api_endpoints())
```

### 3. 通过 API 提交表单

通过直接向 API 发送来更快地填充表单：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def bulk_form_submission():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 首先登录
        await tab.go_to('https://crm.example.com/login')
        # ... 登录逻辑 ...
        await asyncio.sleep(2)
        
        # 通过 API 提交多个条目（比填写表单快得多）
        contacts = [
            {'name': 'John Doe', 'email': 'john@example.com', 'company': 'Acme Inc'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'company': 'Tech Corp'},
            {'name': 'Bob Wilson', 'email': 'bob@example.com', 'company': 'StartupXYZ'},
        ]
        
        for contact in contacts:
            response = await tab.request.post(
                'https://crm.example.com/api/contacts',
                json=contact
            )
            
            if response.ok:
                print(f"已添加: {contact['name']}")
            else:
                print(f"失败: {contact['name']} - {response.status_code}")

asyncio.run(bulk_form_submission())
```

### 4. 使用会话下载文件

下载需要身份验证的文件：

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def download_authenticated_file():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 认证
        await tab.go_to('https://portal.example.com/login')
        # ... 登录逻辑 ...
        await asyncio.sleep(2)
        
        # 下载需要身份验证的文件
        response = await tab.request.get(
            'https://portal.example.com/api/reports/monthly.pdf'
        )
        
        if response.ok:
            # 保存文件
            output_path = Path('/tmp/monthly_report.pdf')
            output_path.write_bytes(response.content)
            print(f"已下载: {output_path} ({len(response.content)} 字节)")
        else:
            print(f"下载失败: {response.status_code}")

asyncio.run(download_authenticated_file())
```

### 5. 使用自定义标头

向您的请求添加自定义标头：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def custom_headers_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 首先登录
        await tab.go_to('https://api.example.com/login')
        # ... 登录逻辑 ...
        
        # 使用自定义标头发起请求
        headers: list[HeaderEntry] = [
            {'name': 'X-API-Version', 'value': '2.0'},
            {'name': 'X-Request-ID', 'value': 'unique-id-123'},
            {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/data',
            headers=headers
        )
        
        print(f"状态: {response.status_code}")
        print(f"数据: {response.json()}")

asyncio.run(custom_headers_example())
```

### 6. 处理不同的响应类型

以多种格式访问响应数据：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def response_formats():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://api.example.com')
        
        # JSON 响应
        json_response = await tab.request.get('/api/users/1')
        user = json_response.json()
        print(f"JSON: {user}")
        
        # 文本响应
        text_response = await tab.request.get('/api/status')
        status_text = text_response.text
        print(f"文本: {status_text}")
        
        # 二进制响应（例如，图像）
        image_response = await tab.request.get('/api/avatar/1')
        image_bytes = image_response.content
        print(f"二进制: {len(image_bytes)} 字节")
        
        # 检查响应状态
        if json_response.ok:
            print("请求成功！")
        
        # 访问响应 URL（在重定向后很有用）
        print(f"最终 URL: {json_response.url}")

asyncio.run(response_formats())
```

## HTTP 方法

支持所有标准的 HTTP 方法：

### GET - 检索数据

```python
# 简单的 GET
response = await tab.request.get('https://api.example.com/users')

# 带查询参数的 GET
response = await tab.request.get(
    'https://api.example.com/search',
    params={'q': 'python', 'limit': '10'}
)
```

### POST - 创建资源

```python
# 使用 JSON 数据的 POST
response = await tab.request.post(
    'https://api.example.com/users',
    json={'name': 'John Doe', 'email': 'john@example.com'}
)

# 使用表单数据的 POST
response = await tab.request.post(
    'https://api.example.com/login',
    data={'username': 'john', 'password': 'secret'}
)
```

### PUT - 更新资源

```python
# 更新整个资源
response = await tab.request.put(
    'https://api.example.com/users/123',
    json={'name': 'Jane Doe', 'email': 'jane@example.com', 'role': 'admin'}
)
```

### PATCH - 部分更新

```python
# 更新特定字段
response = await tab.request.patch(
    'https://api.example.com/users/123',
    json={'email': 'newemail@example.com'}
)
```

### DELETE - 删除资源

```python
# 删除资源
response = await tab.request.delete('https://api.example.com/users/123')
```

### HEAD - 仅获取标头

```python
# 检查资源是否存在而不下载它
response = await tab.request.head('https://example.com/large-file.zip')
print(f"Content-Length: {response.headers}")
```

### OPTIONS - 检查功能

```python
# 检查允许的方法
response = await tab.request.options('https://api.example.com/users')
print(f"允许的方法: {response.headers}")
```

!!! info "这是如何工作的？"
    浏览器上下文请求使用 Fetch API 直接在浏览器的 JavaScript 上下文中执行 HTTP 调用，同时监控 CDP 网络事件以捕获全面的元数据（标头、Cookie、时序）。
    
    有关内部架构、事件监控和实现详细信息的详细说明，请参阅[浏览器请求架构](../../deep-dive/browser-requests-architecture.md)。

## 响应对象

`Response` 对象提供了类似于 `requests.Response` 的熟悉接口：

```python
response = await tab.request.get('https://api.example.com/users')

# 状态码
print(response.status_code)  # 200, 404, 500 等

# 检查是否成功（2xx 或 3xx）
if response.ok:
    print("成功！")

# 响应体
text_data = response.text      # 作为字符串
byte_data = response.content   # 作为字节
json_data = response.json()    # 解析的 JSON

# 标头
for header in response.headers:
    print(f"{header['name']}: {header['value']}")

# 请求标头（实际发送的内容）
for header in response.request_headers:
    print(f"{header['name']}: {header['value']}")

# 响应设置的 Cookie
for cookie in response.cookies:
    print(f"{cookie['name']} = {cookie['value']}")

# 最终 URL（在重定向后）
print(response.url)

# 为错误状态码引发异常
response.raise_for_status()  # 如果是 4xx 或 5xx 则引发 HTTPError
```

!!! note "重定向和 URL 跟踪"
    `response.url` 属性仅包含所有重定向后的**最终 URL**。如果您需要跟踪完整的重定向链（中间 URL、状态码、时序），请使用[网络监控](monitoring.md)详细观察所有请求。

## 标头和 Cookie

### 使用标头

标头表示为 `HeaderEntry` 对象：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def header_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 使用 HeaderEntry 类型以获得 IDE 自动完成和类型检查
        headers: list[HeaderEntry] = [
            {'name': 'Authorization', 'value': 'Bearer token-123'},
            {'name': 'X-Custom-Header', 'value': 'custom-value'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/protected',
            headers=headers
        )
        
        # 检查响应标头（也是 HeaderEntry 类型的字典）
        for header in response.headers:
            if header['name'] == 'Content-Type':
                print(f"Content-Type: {header['value']}")

asyncio.run(header_example())
```

!!! tip "标头的类型提示"
    `HeaderEntry` 是来自 `pydoll.protocol.fetch.types` 的 `TypedDict`。将其用作类型提示可为您提供：
    
    - **自动完成**：IDE 建议 `name` 和 `value` 键
    - **类型安全**：在运行前捕获拼写错误和缺失的键
    - **文档**：清晰的标头结构
    
    虽然您可以传递普通字典，但使用类型提示可以提高代码质量和 IDE 支持。

!!! tip "自定义标头行为"
    自定义标头与浏览器的自动标头（如 `User-Agent`、`Accept`、`Referer` 等）**一起**发送。
    
    如果您尝试设置标准浏览器标头（例如 `User-Agent`），行为取决于特定标头；有些可能会被覆盖，其他可能被忽略，有些可能会导致冲突。对于大多数用例，坚持使用自定义标头（例如 `X-API-Key`、`Authorization`）以避免意外行为。

### 理解 Cookie

Cookie 由浏览器自动管理：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def cookie_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 第一个请求设置 Cookie
        login_response = await tab.request.post(
            'https://api.example.com/login',
            json={'username': 'user', 'password': 'pass'}
        )
        
        # 检查服务器设置的 Cookie
        print("服务器设置的 Cookie：")
        for cookie in login_response.cookies:
            print(f"  {cookie['name']} = {cookie['value']}")
        
        # 后续请求自动包含 Cookie
        profile_response = await tab.request.get(
            'https://api.example.com/profile'
        )
        # 无需传递 Cookie - 浏览器会处理！
        
        print(f"配置文件数据: {profile_response.json()}")

asyncio.run(cookie_example())
```

## 与传统 Requests 的比较

| 功能 | `requests` 库 | 浏览器上下文请求 |
|---------|-------------------|-------------------------|
| **会话管理** | 手动 Cookie 处理 | 通过浏览器自动 |
| **身份验证** | 提取并传递令牌 | 从浏览器继承 |
| **CORS** | 不适用 | 浏览器执行策略 |
| **JavaScript** | 无法执行 | 完全访问浏览器上下文 |
| **Cookie Jar** | 单独的实例 | 浏览器的原生 Cookie 存储 |
| **标头** | 手动设置 | 浏览器自动添加标准标头 |
| **用例** | 服务器端脚本 | 浏览器自动化 |
| **设置** | 外部库 | 内置于 Pydoll |

## 另请参阅

- **[浏览器请求架构](../../deep-dive/browser-requests-architecture.md)** - 内部实现和架构
- **[网络监控](monitoring.md)** - 观察所有网络流量
- **[请求拦截](interception.md)** - 在发送前修改请求
- **[事件系统](../advanced/event-system.md)** - 对浏览器事件做出反应
- **[深入了解：网络功能](../../deep-dive/network-capabilities.md)** - 技术细节

浏览器上下文请求是混合自动化的游戏规则改变者。结合 UI 自动化的强大功能和直接 API 调用的速度，同时保持完美的会话连续性！
