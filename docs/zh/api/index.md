# API 参考

这里是Pydoll API 参考！本节提供 Pydoll 库中所有类、方法和函数的详尽文档。

## 概述

Pydoll 几个关键模块组成，每个模块在浏览器自动化中都有特定的用途：

### 浏览器模块
浏览器模块可以管理浏览器实例和生命周期。

- **[Chrome](browser/chrome.md)** - Chrome 浏览器自动化
- **[Edge](browser/edge.md)** - Microsoft Edge 浏览器自动化  
- **[Options](browser/options.md)** - 浏览器配置选项  
- **[Tab](browser/tab.md)** - 页面标签和交互  
- **[Managers](browser/managers.md)** - 浏览器生命周期管理器  

### 元素模块
元素模块提供与网页元素交互的功能。

- **[WebElement](elements/web_element.md)** - 网页元素交互
- **[Mixins](elements/mixins.md)** - 可复用的元素交互功能

### 连接模块
连接模块通过 Chrome DevTools 协议处理与浏览器的通信。

- **[Connection Handler](connection/connection.md)** - WebSocket连接管理器
- **[Managers](connection/managers.md)** - 连接生命周期管理器

### 命令模块
命令模块提供低级 Chrome DevTools 协议命令实现。

- **[Commands Overview](commands/index.md)** - CDP command implementations by domain

### 协议模块
协议模块实现了 Chrome DevTools 协议命令和事件。

- **[Commands](protocol/commands.md)** - CDP 命令封装
- **[Events](protocol/events.md)** - CDP 事件处理

### 核心模块
核心模块包含基础程序、常量和异常。

- **[Constants](core/constants.md)** - 库常量和枚举
- **[Exceptions](core/exceptions.md)** - 自定义异常类
- **[Utils](core/utils.md)** - 实用功能

## 快捷导航

### 常用类

| 类                 | 功能           | 模块                            |
|-------------------|--------------|-------------------------------|
| `Chrome`          | Chrome浏览器自动化 | `pydoll.browser.chromium`     |
| `Edge`            | Edge浏览器自动化   | `pydoll.browser.chromium`     |
| `Tab`             | 标签页交互和控制     | `pydoll.browser.tab`          |
| `WebElement`      | 元素交互         | `pydoll.elements.web_element` |
| `ChromiumOptions` | 浏览器配置        | `pydoll.browser.options`      |

### 关键枚举和常量

| 名称               | 功能 | 模块 |
|------------------|---------|--------|
| `By`             | 元素选择器策略 | `pydoll.constants` |
| `Key`            | 键盘按键常量 | `pydoll.constants` |
| `PermissionType` | 浏览器权限类型 | `pydoll.constants` |

### 常见异常类型

| 异常                   | 原因        | 模块                  |
|----------------------|-----------|---------------------|
| `ElementNotFound`    | 元素在DOM未找到 | `pydoll.exceptions` |
| `WaitElementTimeout` | 元素等待超时    | `pydoll.exceptions` |
| `BrowserNotStarted`  | 浏览器未开启    | `pydoll.exceptions` |

## 使用模式

### 基本浏览器自动化

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://example.com")
    element = await tab.find(id="my-element")
    await element.click()
```

### 元素定位

```python
# Using the modern find() method
element = await tab.find(id="username")
element = await tab.find(tag_name="button", class_name="submit")

# Using CSS selectors or XPath
element = await tab.query("#username")
element = await tab.query("//button[@class='submit']")
```

### 事件处理

```python
await tab.enable_page_events()
await tab.on('Page.loadEventFired', handle_page_load)
```

## 类型提示

Pydoll 具有完整的类型支持，并提供全面的类型提示，以提供更好的 IDE 支持和代码安全性。所有公共 API 均包含正确的类型注释。

```python
from typing import Optional, List
from pydoll.elements.web_element import WebElement

# Methods return properly typed objects
element: Optional[WebElement] = await tab.find(id="test", raise_exc=False)
elements: List[WebElement] = await tab.find(class_name="item", find_all=True)
```

## Async/Await 支持

所有 Pydoll 操作都是异步的，必须与 `async`/`await` 一起使用：

```python
import asyncio

async def main():
    # All Pydoll operations are async
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to("https://example.com")
        
asyncio.run(main())
```

浏览以下部分以了解每个模块的完整 API 文档。