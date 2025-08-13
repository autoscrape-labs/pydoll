# 输入命令

输入命令处理鼠标和键盘交互，提供真人仿真的输入模拟。

## 概述

输入命令模块提供模拟用户输入的功能，包括鼠标移动、点击、键盘输入和按键操作。

::: pydoll.commands.input_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## 用法

输入命令由元素交互方法使用，可直接用于高级输入场景：

```python
from pydoll.commands.input_commands import dispatch_mouse_event, dispatch_key_event
from pydoll.connection.connection_handler import ConnectionHandler

# Simulate mouse click
connection = ConnectionHandler()
await dispatch_mouse_event(
    connection, 
    type="mousePressed", 
    x=100, 
    y=200, 
    button="left"
)

# Simulate keyboard typing
await dispatch_key_event(
    connection,
    type="keyDown",
    key="Enter"
)
```

## 主要功能

输入命令模块提供以下函数：

### 鼠标事件
- `dispatch_mouse_event()` - 鼠标点击、移动和滚轮事件
- 鼠标按键状态（左键、右键、中键）
- 基于坐标的定位
- 拖放操作


### 键盘事件
- `dispatch_key_event()` - 键盘按下和释放事件
- `insert_text()` - 直接插入文本
- 特殊键处理（Enter、Tab、箭头键等）
- 修饰键（Ctrl、Alt、Shift）


### 触摸事件
- 触摸屏模拟
- 多点触控手势
- 触摸坐标和压力控制

## 仿真行为

输入命令支持仿真行为模式：

- 平滑的鼠标移动曲线
- 真实的打字速度和模式
- 操作之间随机的微延迟
- 压力感应触摸事件

!!! tip "Element Methods"
    For most use cases, use the higher-level element methods like `element.click()` and `element.type_text()` which provide a more convenient API and handle common scenarios automatically. 