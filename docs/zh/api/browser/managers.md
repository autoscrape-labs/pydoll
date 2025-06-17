# 浏览器管理器

管理器模块提供专门的类来管理浏览器生命周期和配置。

## 总览

Browser managers handle specific responsibilities in browser automation:

::: pydoll.browser.managers
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 管理器类

### 浏览器进程管理器
管理浏览器进程的生命周期，包括启动、停止和监控浏览器进程。

::: pydoll.browser.managers.browser_process_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### 浏览器选项管理器
处理浏览器配置选项和命令行参数。

::: pydoll.browser.managers.browser_options_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### 代理管理器
管理浏览器实例的代理配置和身份验证。

::: pydoll.browser.managers.proxy_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### 临时目录管理器
处理浏览器实例使用的临时目录的创建和清理。

::: pydoll.browser.managers.temp_dir_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## 用法
管理器通常由 Chrome 和 Edge 等浏览器类内部使用。它们提供可组合的模块化功能：

```python
from pydoll.browser.managers.proxy_manager import ProxyManager
from pydoll.browser.managers.temp_dir_manager import TempDirManager

# Managers are used internally by browser classes
# Direct usage is for advanced scenarios only
proxy_manager = ProxyManager()
temp_manager = TempDirManager()
```

!!! note "Internal Usage"
    These managers are primarily used internally by the browser classes. Direct usage is recommended only for advanced scenarios or when extending the library. 