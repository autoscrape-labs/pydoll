# 页面命令

页面命令处理页面导航、生命周期事件和页面操作。

## 概述

页面命令模块提供页面间导航、管理页面生命周期、处理 JavaScript 执行以及控制页面行为的功能。

::: pydoll.commands.page_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

“Tab”类广泛使用页面命令进行导航和页面管理：

```python
from pydoll.commands.page_commands import navigate, reload, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Navigate to a URL
connection = ConnectionHandler()
await enable(connection)  # Enable page events
await navigate(connection, url="https://example.com")

# Reload the page
await reload(connection)
```

## 关键功能

页面命令模块提供以下函数：

### 导航
- `navigate()` - 访问URL
- `reload()` - 重新加载当前页面
- `go_back()` - 后退一步
- `go_forward()` - 前进一步
- `stop_loading()` - 停止页面加载

### 页面生命周期
- `enable()` / `disable()` - 启用/禁用页面事件
- `get_frame_tree()` - 获取页面框架结构
- `get_navigation_history()` - 获取导航历史记录

### 内容管理
- `get_resource_content()` - 获取页面资源内容
- `search_in_resource()` - 在页面资源内搜索
- `set_document_content()` - 设置页面 HTML 内容

### 截图和 PDF
- `capture_screenshot()` - 页面截图
- `print_to_pdf()` - 将页面保存为PDF
- `capture_snapshot()` - 页面快照

### JavaScript 执行
- `add_script_to_evaluate_on_new_document()` - 添加启动脚本(在网页加载前注入js)
- `remove_script_to_evaluate_on_new_document()` - 移除启动脚本

### 页面设置
- `set_lifecycle_events_enabled()` - 控制生命周期事件
- `set_ad_blocking_enabled()` - 启用/禁用广告拦截
- `set_bypass_csp()` - 绕过内容安全策略

## 高级功能
### 框架管理

```python
# Get all frames in the page
frame_tree = await get_frame_tree(connection)
for frame in frame_tree.child_frames:
    print(f"Frame: {frame.frame.url}")
```

### 资源拦截
```python
# Get resource content
content = await get_resource_content(
    connection, 
    frame_id=frame_id, 
    url="https://example.com/script.js"
)
```

### 页面事件
页面命令可与各种页面事件配合使用：
- `Page.loadEventFired` - 页面加载完成
- `Page.domContentEventFired` - DOM 内容已加载
- `Page.frameNavigated` - 框架访问结束
- `Page.frameStartedLoading` - 框架加载开始


!!! 小提示“Tab 类集成”
大多数页面操作都可以通过 `Tab` 类方法实现，例如 `tab.go_to()`、`tab.reload()` 和 `tab.screenshot()`，这些方法提供了更便捷的 API。