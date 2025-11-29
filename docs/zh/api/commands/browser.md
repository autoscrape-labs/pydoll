# 浏览器命令

浏览器命令提供对浏览器实例及其配置的底层控制。

## 概述

浏览器命令模块处理浏览器级别的操作，例如版本信息、目标管理和浏览器范围的设置。

::: pydoll.commands.browser_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

浏览器命令通常由浏览器类在内部使用，用于管理浏览器实例：

```python
from pydoll.commands.browser_commands import get_version
from pydoll.connection.connection_handler import ConnectionHandler

# Get browser version information
connection = ConnectionHandler()
version_info = await get_version(connection)
```

## 可用命令

浏览器命令模块提供以下功能：

- 获取浏览器版本和用户代理信息
- 管理浏览器目标（标签页、窗口）
- 控制浏览器范围的设置和权限
- 处理浏览器生命周期事件

!!! note "Internal Usage"
    These commands are primarily used internally by the `Chrome` and `Edge` browser classes. Direct usage is recommended only for advanced scenarios. 