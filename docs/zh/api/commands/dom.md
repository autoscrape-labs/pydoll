# DOM命令

DOM 命令模块提供了与网页文档对象模型交互的全面功能。

## 概述

DOM 命令模块是 Pydoll 中最重要的模块之一，它提供了查找、交互和操作网页上的 HTML 元素所需的所有功能。

::: pydoll.commands.dom_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Usage

DOM commands are used extensively by the `WebElement` class and element finding methods:

## 用法

`WebElement` 类和元素查找方法广泛使用DOM 命令：

```python
from pydoll.commands.dom_commands import query_selector, get_attributes
from pydoll.connection.connection_handler import ConnectionHandler

# Find element and get its attributes
connection = ConnectionHandler()
node_id = await query_selector(connection, selector="#username")
attributes = await get_attributes(connection, node_id=node_id)
```

## 主要功能

DOM 命令模块提供以下功能：

### 元素定位
- `query_selector()` - 通过CSS选择器进行元素定位
- `query_selector_all()` - 通过CSS选择器进行元素定位（查找多个元素）
- `get_document()` - 获取document的根节点

### 元素交互
- `click_element()` - 点击元素
- `focus_element()` - 焦点置于元素
- `set_attribute_value()` - 设置元素属性
- `get_attributes()` - 获取元素属性

### 元素信息
- `get_box_model()` - 获取元素位置和尺寸
- `describe_node()` - 获取元素详细信息
- `get_outer_html()` - 获取元素的HTML内容

### DOM 操作
- `remove_node()` - 从DOM节点中删除元素
- `set_node_value()` - 设置元素值
- `request_child_nodes()` - 获取子元素

!!! tip "High-Level APIs"
    While these commands provide powerful low-level access, most users should use the higher-level `WebElement` class methods like `click()`, `type_text()`, and `get_attribute()` which use these commands internally. 