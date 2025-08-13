# 浏览器请求

请求模块在浏览器上下文中提供 HTTP 请求功能，支持继承浏览器会话状态、cookies 和身份验证的无缝 API 调用。

## 概述

浏览器请求模块为在浏览器 JavaScript 上下文中直接进行 HTTP 调用提供了类似 `requests` 的接口。这种方法相比传统 HTTP 库提供了几个优势：

- **会话继承**: 自动处理 cookie、身份验证和 CORS
- **浏览器上下文**: 请求在与页面相同的安全上下文中执行
- **无需会话管理**: 消除在自动化和 API 调用之间传输 cookies 和令牌的需要
- **SPA 兼容性**: 完美适配具有复杂身份验证流程的单页应用

## Request 类

在浏览器上下文中进行 HTTP 请求的主要接口。

::: pydoll.browser.requests.request.Request
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## Response 类

表示 HTTP 请求的响应，提供类似于 `requests` 库的熟悉接口。

::: pydoll.browser.requests.response.Response
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## 使用示例

### 基本 HTTP 方法

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://api.example.com")
    
    # GET 请求
    response = await tab.request.get("/users/123")
    user_data = await response.json()
    
    # POST 请求
    response = await tab.request.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # 带 headers 的 PUT 请求
    response = await tab.request.put("/users/123", 
        json={"name": "Jane Doe"},
        headers={"Authorization": "Bearer token123"}
    )
```

### 响应处理

```python
# 检查响应状态
if response.ok:
    print(f"成功: {response.status_code}")
else:
    print(f"错误: {response.status_code}")
    response.raise_for_status()  # 对 4xx/5xx 抛出 HTTPError

# 访问响应数据
text_data = response.text
json_data = await response.json()
raw_bytes = response.content

# 检查 headers 和 cookies
print("响应 headers:", response.headers)
print("请求 headers:", response.request_headers)
for cookie in response.cookies:
    print(f"Cookie: {cookie.name}={cookie.value}")
```

### 高级功能

```python
# 带自定义 headers 和参数的请求
response = await tab.request.get("/search", 
    params={"q": "python", "limit": 10},
    headers={
        "User-Agent": "Custom Bot 1.0",
        "Accept": "application/json"
    }
)

# 文件上传模拟
response = await tab.request.post("/upload",
    data={"description": "Test file"},
    files={"file": ("test.txt", "file content", "text/plain")}
)

# 表单数据提交
response = await tab.request.post("/login",
    data={"username": "user", "password": "pass"}
)
```

## 与 Tab 的集成

请求功能通过 `tab.request` 属性访问，该属性为每个 tab 提供一个单例 `Request` 实例：

```python
# 每个 tab 都有自己的 request 实例
tab1 = await browser.get_tab(0)
tab2 = await browser.new_tab()

# 这些是独立的 Request 实例
request1 = tab1.request  # 绑定到 tab1 的 Request
request2 = tab2.request  # 绑定到 tab2 的 Request

# 请求继承 tab 的上下文
await tab1.go_to("https://site1.com")
await tab2.go_to("https://site2.com")

# 这些请求将具有不同的 cookie/会话上下文
response1 = await tab1.request.get("/api/data")  # 使用 site1.com 的 cookies
response2 = await tab2.request.get("/api/data")  # 使用 site2.com 的 cookies
```

!!! tip "混合自动化"
    该模块对于需要结合 UI 交互和 API 调用的混合自动化场景特别强大。例如，通过 UI 登录，然后使用已认证的会话进行 API 调用，无需手动处理 cookies 或令牌。