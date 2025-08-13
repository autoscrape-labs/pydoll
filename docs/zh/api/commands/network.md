# 网络命令

网络命令提供对网络请求、响应和浏览器网络行为的全面控制。

## 概述

网络命令模块支持请求拦截、响应修改、Cookie 管理和网络监控功能。

::: pydoll.commands.network_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

网络命令用于请求拦截和网络监控等高级场景：

```python
from pydoll.commands.network_commands import enable, set_request_interception
from pydoll.connection.connection_handler import ConnectionHandler

# Enable network monitoring
connection = ConnectionHandler()
await enable(connection)

# Enable request interception
await set_request_interception(connection, patterns=[{"urlPattern": "*"}])
```

## 主要功能

网络命令模块提供以下功能：


### 请求管理
- `enable()` / `disable()` - 启用/禁用网络监控
- `set_request_interception()` - 拦截并修改请求
- `continue_intercepted_request()` - 继续或修改拦截的请求
- `get_request_post_data()` - 获取请求体数据


### 响应处理
- `get_response_body()` - 获取响应内容
- `fulfill_request()` - 提供自定义响应
- `fail_request()` - 模拟网络异常

### Cookie 管理
- `get_cookies()` - 获取浏览器 Cookie
- `set_cookies()` - 设置浏览器 Cookie
- `delete_cookies()` - 删除指定 Cookie
- `clear_browser_cookies()` - 清除所有 Cookie

### 缓存控制
- `clear_browser_cache()` - 清除浏览器缓存
- `set_cache_disabled()` - 禁用浏览器缓存
- `get_response_body_for_interception()` - 获取缓存的响应

### 安全和标头
- `set_user_agent_override()` - 覆盖用户代理
- `set_extra_http_headers()` - 添加自定义标头
- `emulate_network_conditions()` - 模拟网络连接状况

## 高级用例

### 请求拦截

```python
# 拦截修改请求
await set_request_interception(connection, patterns=[
    {"urlPattern": "*/api/*", "requestStage": "Request"}
])

# 拦截请求处理
async def handle_request(request):
    if "api/login" in request.url:
        # 修改请求头
        headers = request.headers.copy()
        headers["Authorization"] = "Bearer token"
        await continue_intercepted_request(
            connection, 
            request_id=request.request_id,
            headers=headers
        )
```

### 响应模拟
```python
# 模拟 API 响应
await fulfill_request(
    connection,
    request_id=request_id,
    response_code=200,
    response_headers={"Content-Type": "application/json"},
    body='{"status": "success"}'
)
```

!!! warning "Performance Impact"
    Network interception can impact page loading performance. Use selectively and disable when not needed. 