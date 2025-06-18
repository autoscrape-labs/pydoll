# 运行时命令

运行时命令提供 JavaScript 执行功能和运行时环境管理。

## 概述

运行时命令模块支持在浏览器上下文中执行 JavaScript 代码、检查对象以及控制运行时环境。

::: pydoll.commands.runtime_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

运行时命令用于 JavaScript 执行和运行时管理：

```python
from pydoll.commands.runtime_commands import evaluate, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Enable runtime events
connection = ConnectionHandler()
await enable(connection)

# Execute JavaScript
result = await evaluate(
    connection, 
    expression="document.title",
    return_by_value=True
)
print(result.value)  # Page title
```

## 主要功能

运行时命令模块提供以下功能：

### JavaScript 执行
- `evaluate()` - 执行 JavaScript 表达式
- `call_function_on()` - 调用对象上的函数
- `compile_script()` - 编译 JavaScript 以供复用
- `run_script()` - 运行已编译的脚本

### 对象管理
- `get_properties()` - 获取对象属性
- `release_object()` - 释放对象引用
- `release_object_group()` - 释放对象组

### 运行时控制
- `enable()` / `disable()` - 启用/禁用运行时事件
- `discard_console_entries()` - 清除控制台记录
- `set_custom_object_formatter_enabled()` - 启用自定义格式化程序

### 异常处理
- `set_async_call_stack_depth()` - 设置调用堆栈深度
- 异常捕获和报告
- 错误对象检查

## 高级用法

### 复杂的 JavaScript 执行

```python
# 执行带有错误处理的复杂 JavaScript
script = """
try {
    const elements = document.querySelectorAll('.item');
    return Array.from(elements).map(el => ({
        text: el.textContent,
        href: el.href
    }));
} catch (error) {
    return { error: error.message };
}
"""

result = await evaluate(
    connection,
    expression=script,
    return_by_value=True,
    await_promise=True
)
```

### 对象检查
```python
# Get detailed object properties
properties = await get_properties(
    connection,
    object_id=object_id,
    own_properties=True,
    accessor_properties_only=False
)

for prop in properties:
    print(f"{prop.name}: {prop.value}")
```

### 控制台集成
运行时命令与浏览器控制台集成：
- 控制台消息和错误
- 控制台 API 方法调用
- 自定义控制台格式化程序

!!! note "Performance Considerations"
    JavaScript execution through runtime commands can be slower than native browser execution. Use judiciously for complex operations. 