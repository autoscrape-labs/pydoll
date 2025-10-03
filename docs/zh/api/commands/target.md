# Target命令

Target命令管理浏览器目标，包括标签页、窗口和其他浏览上下文。

## 概述

Target命令模块提供创建、管理和控制浏览器目标（例如标签页、弹出窗口和服务工作线程）的功能。

::: pydoll.commands.target_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

Target命令由浏览器类内部使用，用于管理标签页和窗口：

```python
from pydoll.commands.target_commands import get_targets, create_target, close_target
from pydoll.connection.connection_handler import ConnectionHandler

# Get all browser targets
connection = ConnectionHandler()
targets = await get_targets(connection)

# Create a new tab
new_target = await create_target(connection, url="https://example.com")

# Close a target
await close_target(connection, target_id=new_target.target_id)
```

## 主要功能

Target命令模块提供以下功能：


### Target管理
- `get_targets()` - 列出所有浏览器Target
- `create_target()` - 创建新的标签页或窗口
- `close_target()` - 关闭特定Target
- `activate_target()` - 将Target置于前台

### Target 信息
- `get_target_info()` - 获取详细的Target信息
- Target类型：页面、background_page、service_worker、浏览器
- Target状态：已连接、已分离、崩溃

### Session 管理
- `attach_to_target()` - 附加到Target进行控制
- `detach_from_target()` - 分离Target
- `send_message_to_target()` - 向Target发送命令

### 浏览器上下文
- `create_browser_context()` - 创建独立的浏览器上下文
- `dispose_browser_context()` - 移除浏览器上下文
- `get_browser_contexts()` - 列出浏览器上下文

## 目标类型

可以管理不同类型的目标：

### 页面 Targets
```python
# Create a new tab
page_target = await create_target(
    connection,
    url="https://example.com",
    width=1920,
    height=1080,
    browser_context_id=None  # Default context
)
```

### 弹窗
```python
# Create a popup window
popup_target = await create_target(
    connection,
    url="https://popup.example.com",
    width=800,
    height=600,
    new_window=True
)
```

### 无痕上下文
```python
# Create incognito browser context
incognito_context = await create_browser_context(connection)

# Create tab in incognito context
incognito_tab = await create_target(
    connection,
    url="https://private.example.com",
    browser_context_id=incognito_context.browser_context_id
)
```

!!! info "Headless 与 Headed：上下文如何呈现"
    浏览器上下文是逻辑上的隔离环境。在 Headed 模式下，在新的上下文中创建的第一个页面通常会打开一个新的系统窗口。 在 Headless 模式下不会显示窗口——隔离依然存在于后台（cookies、storage、缓存与认证状态仍按上下文分离）。在 CI/Headless 环境中优先使用上下文以获得更高性能与更干净的隔离。

## 高级特性

### 目标事件
Target命令可与各种Target事件配合使用：
- `Target.targetCreated` - 新Target创建
- `Target.targetDestroyed` - Target关闭
- `Target.targetInfoChanged` - Target信息更新
- `Target.targetCrashed` - Target崩溃

### 多Target协调

```python
# Manage multiple tabs
targets = await get_targets(connection)
page_targets = [t for t in targets if t.type == "page"]

for target in page_targets:
    # Perform operations on each tab
    await activate_target(connection, target_id=target.target_id)
    # ... do work in this tab
```

### Target 隔离
```python
# Create isolated browser context for testing
test_context = await create_browser_context(connection)

# All targets in this context are isolated
test_tab1 = await create_target(
    connection, 
    url="https://test1.com",
    browser_context_id=test_context.browser_context_id
)

test_tab2 = await create_target(
    connection,
    url="https://test2.com", 
    browser_context_id=test_context.browser_context_id
)
```

!!! note "Browser Integration"
    Target commands are primarily used internally by the `Chrome` and `Edge` browser classes. The high-level browser APIs provide more convenient methods for tab management. 