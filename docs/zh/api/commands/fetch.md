# Fetch 命令

Fetch 命令使用 Fetch API 域提供高级网络请求处理和拦截功能。

## 概述

Fetch 命令模块支持复杂的网络请求管理，包括请求修改、响应拦截和身份验证处理。

::: pydoll.commands.fetch_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

Fetch 命令用于高级网络拦截和请求处理：

```python
from pydoll.commands.fetch_commands import enable, request_paused, continue_request
from pydoll.connection.connection_handler import ConnectionHandler

# Enable fetch domain
connection = ConnectionHandler()
await enable(connection, patterns=[{
    "urlPattern": "*",
    "requestStage": "Request"
}])

# Handle paused requests
async def handle_paused_request(request_id, request):
    # Modify request or continue as-is
    await continue_request(connection, request_id=request_id)
```

## 关键功能

fetch 命令模块提供以下功能：

### 请求拦截
- `enable()` - 激活fetch模式
- `disable()` - 关闭fetch模式
- `continue_request()` - 继续请求（放行）
- `fail_request()` - 返回特定错误请求

### 修改请求
- 修改请求headers
- 更改请求 URL
- 更改请求方法（GET、POST 等）
- 修改请求body

### 响应处理
- `fulfill_request()` - 提供自定义响应
- `get_response_body()` - 获取响应内容
- 修改响应头
- 响应状态码控制

### 身份验证
- `continue_with_auth()` - 处理身份验证挑战
- 基本身份验证支持
- 自定义身份验证流程

## 高级功能

### 基于模式的拦截

```python
# Intercept specific URL patterns
patterns = [
    {"urlPattern": "*/api/*", "requestStage": "Request"},
    {"urlPattern": "*.js", "requestStage": "Response"},
    {"urlPattern": "https://example.com/*", "requestStage": "Request"}
]

await enable(connection, patterns=patterns)
```

### 请求修改
```python
# Modify intercepted requests
async def modify_request(request_id, request):
    # Add authentication header
    headers = request.headers.copy()
    headers["Authorization"] = "Bearer token123"
    
    # Continue with modified headers
    await continue_request(
        connection,
        request_id=request_id,
        headers=headers
    )
```

### 响应模拟
```python
# Mock API responses
await fulfill_request(
    connection,
    request_id=request_id,
    response_code=200,
    response_headers=[
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Access-Control-Allow-Origin", "value": "*"}
    ],
    body='{"status": "success", "data": {"mocked": true}}'
)
```

### 身份验证处理
```python
# Handle authentication challenges
await continue_with_auth(
    connection,
    request_id=request_id,
    auth_challenge_response={
        "response": "ProvideCredentials",
        "username": "user",
        "password": "pass"
    }
)
```

## 请求阶段

Fetch 命令可以在不同阶段拦截请求：

| 阶段 | 描述 | 用例 |
|-------|-------------|-----------|
| 请求 | 请求发送前 | 修改标头、URL 和方法 |
| 响应 | 收到响应后 | 模拟响应，修改内容 |

## 错误处理

```python
# Fail requests with specific errors
await fail_request(
    connection,
    request_id=request_id,
    error_reason="ConnectionRefused"  # or "AccessDenied", "TimedOut", etc.
)
```

## 与网络命令集成

Fetch 命令与网络命令协同工作，但提供更精细的控制：

- **网络命令**：更广泛的网络监控和控制
- **Fetch 命令**：特定的请求/响应拦截和修改

!!! tip "Performance Considerations"
    Fetch interception can impact page loading performance. Use specific URL patterns and disable when not needed to minimize overhead. 