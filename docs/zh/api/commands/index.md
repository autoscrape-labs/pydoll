# 命令概述

命令模块提供了与Chrome DevTools协议(CDP)域交互的高级接口。每个命令模块对应一个特定的CDP域，并提供执行各种浏览器操作的方法。

## 可用命令模块

### 浏览器命令
- **模块**: `browser_commands.py`
- **用途**: 浏览器级别操作和窗口管理
- **文档**: [浏览器命令](browser.md)

### DOM命令
- **模块**: `dom_commands.py`
- **用途**: DOM树操作和元素操作
- **文档**: [DOM命令](dom.md)

### 输入命令
- **模块**: `input_commands.py`
- **用途**: 输入事件模拟(键盘、鼠标、触摸)
- **文档**: [输入命令](input.md)

### 网络命令
- **模块**: `network_commands.py`
- **用途**: 网络监控和请求拦截
- **文档**: [网络命令](network.md)

### 页面命令
- **模块**: `page_commands.py`
- **用途**: 页面生命周期管理和导航
- **文档**: [页面命令](page.md)

### 运行时命令
- **模块**: `runtime_commands.py`
- **用途**: JavaScript执行和运行时管理
- **文档**: [运行时命令](runtime.md)

### 存储命令
- **模块**: `storage_commands.py`
- **用途**: 浏览器存储访问(cookies、本地存储等)
- **文档**: [存储命令](storage.md)

### 目标命令
- **模块**: `target_commands.py`
- **用途**: 目标管理和标签页操作
- **文档**: [目标命令](target.md)

### 获取命令
- **模块**: `fetch_commands.py`
- **用途**: 网络请求拦截和修改
- **文档**: [获取命令](fetch.md)

## 使用模式

命令通常通过浏览器或标签页实例访问：

```python
from pydoll.browser.chromium import Chrome

# 初始化浏览器
browser = Chrome()
await browser.start()

# 获取活动标签页
tab = await browser.get_active_tab()

# 通过标签页使用命令
await tab.navigate("https://example.com")
element = await tab.find(id="button")
await element.click()
```

## 命令结构

每个命令模块遵循一致的模式：
- **静态方法**: 用于直接命令执行
- **类型提示**: 使用协议类型的完整类型安全
- **错误处理**: 对CDP错误的正确异常处理
- **文档**: 包含示例的全面文档字符串 