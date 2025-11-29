# 键盘控制

键盘 API 提供了在页面级别对键盘输入的完全控制，使您能够模拟真实的输入、执行快捷键和控制复杂的按键序列。与元素级键盘方法不同，键盘 API 在页面上全局操作，为您提供与任何焦点元素交互或触发页面级键盘操作的灵活性。

!!! info "集中式键盘接口"
    所有键盘操作均可通过 `tab.keyboard` 访问，为所有键盘交互提供统一的 API。

!!! warning "重要的 CDP 限制：浏览器 UI 快捷键无法使用"
    **已知问题**：通过 Chrome DevTools Protocol 注入的事件被标记为"不可信"，**不会**触发浏览器 UI 操作或创建用户手势。
    
    **不起作用的功能：**

    - 浏览器快捷键（Ctrl+T、Ctrl+W、Ctrl+N）
    - 开发者工具快捷键（F12、Ctrl+Shift+I）
    - 浏览器导航（Ctrl+Shift+T 重新打开标签）
    - 任何修改浏览器 UI 或窗口的快捷键
    
    **完美工作的功能：**

    - 页面级快捷键（Ctrl+A、Ctrl+C、Ctrl+V、Ctrl+F）
    - 文本选择和操作
    - 表单导航（Tab、Enter、方向键）
    - 输入字段交互
    - 自定义应用快捷键（在 Web 应用中）
    
    **技术原因**：CDP 事件不会创建浏览器安全所需的"用户手势"。参见 [chromium issue #615341](https://bugs.chromium.org/p/chromium/issues/detail?id=615341) 和 [CDP 文档](https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-dispatchKeyEvent)。
    
    对于浏览器级自动化，请直接使用 CDP 浏览器命令（如 `tab.close()`、`browser.new_tab()`），而不是键盘快捷键。

## 快速开始

键盘 API 提供三种主要方法:

```python
from pydoll.browser import Chrome
from pydoll.constants import Key

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')
    
    # 按下并释放一个键
    await tab.keyboard.press(Key.ENTER)
    
    # 执行快捷键组合
    await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # Ctrl+S
    
    # 手动控制
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    await tab.keyboard.up(Key.SHIFT)
```

## 核心方法

### Press: 完整的按键操作

`press()` 方法执行完整的按键周期（按下 → 等待 → 释放）:

```python
from pydoll.constants import Key

# 基本按键
await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# 带修饰键的按键
await tab.keyboard.press(Key.S, modifiers=2)  # Ctrl+S（手动修饰符）

# 自定义按住时长
await tab.keyboard.press(Key.SPACE, interval=0.5)  # 按住 500 毫秒
```

**参数:**

- `key`: 要按下的键（来自 `Key` 枚举）
- `modifiers` (可选): 修饰符标志（Alt=1, Ctrl=2, Meta=4, Shift=8）
- `interval` (可选): 按住键的时长（秒）（默认: 0.1）

### Down: 按下键而不释放

`down()` 方法按下键但不释放它，对于按住修饰键或创建按键序列很有用:

```python
from pydoll.constants import Key

# 按住 Shift 键的同时按其他键
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)  # 选择文本
await tab.keyboard.press(Key.ARROWRIGHT)  # 继续选择
await tab.keyboard.up(Key.SHIFT)

# 使用修饰符标志按下
await tab.keyboard.down(Key.A, modifiers=2)  # Ctrl+A（全选）
```

**参数:**

- `key`: 要按下的键
- `modifiers` (可选): 要应用的修饰符标志

### Up: 释放按键

`up()` 方法释放先前按下的键:

```python
from pydoll.constants import Key

# 手动按键序列
await tab.keyboard.down(Key.CONTROL)
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.T)  # Ctrl+Shift+T
await tab.keyboard.up(Key.SHIFT)
await tab.keyboard.up(Key.CONTROL)
```

**参数:**

- `key`: 要释放的键

!!! tip "何时使用每种方法"

    - **`press()`**: 单个按键操作（Enter、Tab、字母）
    - **`hotkey()`**: 键盘快捷键（Ctrl+C、Ctrl+Shift+T）
    - **`down()`/`up()`**: 复杂序列、按住修饰键、自定义时序

## 快捷键：轻松实现键盘快捷方式

`hotkey()` 方法自动检测修饰键并正确执行快捷键:

### 基本快捷键

```python
from pydoll.constants import Key

# 常用快捷键
await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # 复制
await tab.keyboard.hotkey(Key.CONTROL, Key.V)  # 粘贴
await tab.keyboard.hotkey(Key.CONTROL, Key.X)  # 剪切
await tab.keyboard.hotkey(Key.CONTROL, Key.Z)  # 撤销
await tab.keyboard.hotkey(Key.CONTROL, Key.Y)  # 重做
await tab.keyboard.hotkey(Key.CONTROL, Key.A)  # 全选
await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # 保存

```

### 三键组合

```python
from pydoll.constants import Key

# 文本编辑快捷键（这些有效！）
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # 向左选择单词
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWRIGHT)  # 向右选择单词
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.HOME)  # 选择到文档开头
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.END)  # 选择到文档末尾

# 应用特定快捷键（如果 Web 应用支持）
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.Z)  # 在许多应用中重做
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.S)  # 另存为（如果应用支持）
```

### 平台特定快捷键

```python
import sys
from pydoll.constants import Key

# 在 macOS 上使用 Meta（Command），在 Windows/Linux 上使用 Control
modifier = Key.META if sys.platform == 'darwin' else Key.CONTROL

await tab.keyboard.hotkey(modifier, Key.C)  # 复制（平台感知）
await tab.keyboard.hotkey(modifier, Key.V)  # 粘贴（平台感知）
```

### 快捷键工作原理

`hotkey()` 方法智能处理修饰键:

1. **检测修饰键**: 自动识别 Ctrl、Shift、Alt、Meta
2. **计算标志**: 使用按位或组合修饰键（Ctrl=2, Shift=8 → 10）
3. **正确应用**: 按下非修饰键时应用修饰符标志
4. **干净释放**: 按相反顺序释放键

```python
from pydoll.constants import Key

# hotkey(Key.CONTROL, Key.SHIFT, Key.T) 的幕后:
# 1. 检测: modifiers=[CONTROL, SHIFT], keys=[T]
# 2. 计算: modifier_value = 2 | 8 = 10
# 3. 执行: 按下 T，modifiers=10
# 4. 释放: 释放 T
```

!!! tip "修饰符值"
    手动使用 `modifiers` 参数时:

    - Alt = 1
    - Ctrl = 2
    - Meta/Command = 4
    - Shift = 8
    
    组合它们: Ctrl+Shift = 2 + 8 = 10

## 可用按键

`Key` 枚举提供全面的键盘覆盖:

### 字母键 (A-Z)

```python
from pydoll.constants import Key

# 所有字母 A 到 Z
await tab.keyboard.press(Key.A)
await tab.keyboard.press(Key.Z)
```

### 数字键

```python
from pydoll.constants import Key

# 顶部行数字 (0-9)
await tab.keyboard.press(Key.DIGIT0)
await tab.keyboard.press(Key.DIGIT9)

# 数字键盘数字
await tab.keyboard.press(Key.NUMPAD0)
await tab.keyboard.press(Key.NUMPAD9)
```

### 功能键

```python
from pydoll.constants import Key

# F1 到 F12
await tab.keyboard.press(Key.F1)
await tab.keyboard.press(Key.F12)
```

### 导航键

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ARROWUP)
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.ARROWLEFT)
await tab.keyboard.press(Key.ARROWRIGHT)
await tab.keyboard.press(Key.HOME)
await tab.keyboard.press(Key.END)
await tab.keyboard.press(Key.PAGEUP)
await tab.keyboard.press(Key.PAGEDOWN)
```

### 修饰键

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.CONTROL)
await tab.keyboard.press(Key.SHIFT)
await tab.keyboard.press(Key.ALT)
await tab.keyboard.press(Key.META)  # macOS 上的 Command，Windows 上的 Windows 键
```

### 特殊键

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.SPACE)
await tab.keyboard.press(Key.BACKSPACE)
await tab.keyboard.press(Key.DELETE)
await tab.keyboard.press(Key.ESCAPE)
await tab.keyboard.press(Key.INSERT)
```

## 实用示例

### 表单导航

```python
from pydoll.browser import Chrome
from pydoll.constants import Key

async def fill_form_with_keyboard():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/form')
        
        # 聚焦第一个字段并输入
        first_field = await tab.find(id='name')
        await first_field.click()
        await first_field.insert_text('张三')
        
        # 使用 Tab 键导航到下一个字段
        await tab.keyboard.press(Key.TAB)
        await tab.keyboard.press(Key.TAB)  # 跳过一个字段
        
        # 在当前焦点字段中输入
        second_field = await tab.find(id='email')
        await second_field.insert_text('zhangsan@example.com')
        
        # 使用 Enter 提交
        await tab.keyboard.press(Key.ENTER)
```

### 文本选择和操作

```python
from pydoll.constants import Key

async def select_and_replace_text():
    # 全选文本
    await tab.keyboard.hotkey(Key.CONTROL, Key.A)
    
    # 复制选中内容
    await tab.keyboard.hotkey(Key.CONTROL, Key.C)
    
    # 移动到末尾
    await tab.keyboard.press(Key.END)
    
    # 逐字选择
    await tab.keyboard.down(Key.CONTROL)
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.up(Key.SHIFT)
    await tab.keyboard.up(Key.CONTROL)
    
    # 删除选中内容
    await tab.keyboard.press(Key.DELETE)
```

### 下拉菜单和选择导航

```python
from pydoll.constants import Key

async def navigate_dropdown():
    # 打开下拉菜单
    select = await tab.find(tag_name='select')
    await select.click()
    
    # 使用箭头键导航选项
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.press(Key.ARROWDOWN)
    
    # 使用 Enter 选择
    await tab.keyboard.press(Key.ENTER)
    
    # 或使用 Escape 取消
    await tab.keyboard.press(Key.ESCAPE)
```

### 复杂按键序列

```python
from pydoll.constants import Key
import asyncio

async def complex_editing():
    # 选择行
    await tab.keyboard.press(Key.HOME)  # 移动到开头
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.END)  # 选择到末尾
    await tab.keyboard.up(Key.SHIFT)
    
    # 剪切
    await tab.keyboard.hotkey(Key.CONTROL, Key.X)
    
    # 向下移动并粘贴
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.hotkey(Key.CONTROL, Key.V)
    
    # 如果需要，撤销
    await tab.keyboard.hotkey(Key.CONTROL, Key.Z)
```

## 最佳实践

### 1. 添加延迟以提高可靠性

```python
from pydoll.constants import Key
import asyncio

# 好: 等待 UI 更新
await tab.keyboard.hotkey(Key.CONTROL, Key.F)  # 打开查找
await asyncio.sleep(0.2)  # 等待对话框
await tab.keyboard.press(Key.ESCAPE)  # 关闭它

# 差: 没有延迟，可能不起作用
await tab.keyboard.hotkey(Key.CONTROL, Key.F)
await tab.keyboard.press(Key.ESCAPE)  # 可能太快了
```

### 2. 输入前聚焦元素

```python
from pydoll.constants import Key

# 好: 确保元素已聚焦
input_field = await tab.find(id='search')
await input_field.click()  # 聚焦它
await input_field.insert_text('query')

# 差: 键盘输入进入错误元素
await tab.keyboard.press(Key.A)  # 这会去哪里？
```

### 3. 使用平台感知快捷键

```python
import sys
from pydoll.constants import Key

# 好: 平台感知
cmd_key = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(cmd_key, Key.C)

# 差: 硬编码（在 macOS 上不起作用）
await tab.keyboard.hotkey(Key.CONTROL, Key.C)
```

### 4. 清理长序列

```python
from pydoll.constants import Key

# 好: 确保修饰键被释放
try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    # ... 更多操作
finally:
    await tab.keyboard.up(Key.SHIFT)  # 始终释放

# 差: 错误时修饰键保持按下
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)
# 这里出错会让 Shift 保持按下！
```

## 按键参考表

### 常用页面级快捷键（这些有效！）

| 操作 | Windows/Linux | macOS | 备注 |
|------|--------------|-------|------|
| 复制 | Ctrl+C | Cmd+C | 有效 |
| 粘贴 | Ctrl+V | Cmd+V | 有效 |
| 剪切 | Ctrl+X | Cmd+X | 有效 |
| 撤销 | Ctrl+Z | Cmd+Z | 有效 |
| 重做 | Ctrl+Y | Cmd+Y | 有效 |
| 全选 | Ctrl+A | Cmd+A | 有效 |
| 查找 | Ctrl+F | Cmd+F | 仅当 Web 应用实现时 |
| 保存 | Ctrl+S | Cmd+S | 仅当 Web 应用实现时 |
| 刷新 | F5 或 Ctrl+R | Cmd+R | 改用 `await tab.refresh()` |

### 浏览器快捷键（通过 CDP 无法使用）

| 操作 | 快捷键 | 改用 |
|------|--------|------|
| 新标签 | Ctrl+T | `await browser.new_tab()` |
| 关闭标签 | Ctrl+W | `await tab.close()` |
| 重新打开标签 | Ctrl+Shift+T | 手动跟踪标签 |
| 开发者工具 | F12, Ctrl+Shift+I | 已经可以通过 CDP 访问！ |
| 地址栏 | Ctrl+L | `await tab.go_to(url)` |

### 所有可用按键

| 类别 | 按键 |
|------|------|
| **字母** | `Key.A` 到 `Key.Z` (26 个键) |
| **数字** | `Key.DIGIT0` 到 `Key.DIGIT9` (10 个键) |
| **数字键盘** | `Key.NUMPAD0` 到 `Key.NUMPAD9`, `NUMPADMULTIPLY`, `NUMPADADD`, `NUMPADSUBTRACT`, `NUMPADDECIMAL`, `NUMPADDIVIDE` |
| **功能键** | `Key.F1` 到 `Key.F12` (12 个键) |
| **导航** | `ARROWUP`, `ARROWDOWN`, `ARROWLEFT`, `ARROWRIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN` |
| **修饰键** | `CONTROL`, `SHIFT`, `ALT`, `META` |
| **特殊键** | `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`, `ESCAPE`, `INSERT` |
| **锁定键** | `CAPSLOCK`, `NUMLOCK`, `SCROLLLOCK` |
| **符号** | `SEMICOLON`, `EQUALSIGN`, `COMMA`, `MINUS`, `PERIOD`, `SLASH`, `GRAVEACCENT`, `BRACKETLEFT`, `BACKSLASH`, `BRACKETRIGHT`, `QUOTE` |

### 修饰符标志值

| 修饰符 | 值 | 二进制 | 用法 |
|--------|---|--------|------|
| Alt | 1 | 0001 | `modifiers=1` |
| Ctrl | 2 | 0010 | `modifiers=2` |
| Meta | 4 | 0100 | `modifiers=4` |
| Shift | 8 | 1000 | `modifiers=8` |
| Ctrl+Shift | 10 | 1010 | `modifiers=10` |
| Ctrl+Alt | 3 | 0011 | `modifiers=3` |
| Ctrl+Shift+Alt | 11 | 1011 | `modifiers=11` |

## 从 WebElement 方法迁移

先前在 `WebElement` 上的键盘方法已弃用。以下是如何迁移:

### 旧 vs 新

```python
from pydoll.constants import Key

# 旧（已弃用）
element = await tab.find(id='input')
await element.key_down(Key.A, modifiers=2)
await element.key_up(Key.A)
await element.press_keyboard_key(Key.ENTER)

# 新（推荐）
await tab.keyboard.down(Key.A, modifiers=2)
await tab.keyboard.up(Key.A)
await tab.keyboard.press(Key.ENTER)
```

!!! warning "弃用通知"
    以下 `WebElement` 方法已弃用:

    - `key_down()` → 使用 `tab.keyboard.down()`
    - `key_up()` → 使用 `tab.keyboard.up()`
    - `press_keyboard_key()` → 使用 `tab.keyboard.press()`
    
    这些方法仍然可以工作以保持向后兼容性，但会显示弃用警告。

### 为什么要迁移？

- **集中化**: 所有键盘操作在一个地方
- **更清晰的 API**: 所有键盘操作的一致接口
- **更强大**: 快捷键支持，智能修饰符检测
- **更好的类型支持**: 完整的 IDE 自动完成支持

## 了解更多

有关其他自动化功能:

- **[人性化交互](human-interactions.md)**: 真实的点击、滚动和鼠标移动
- **[表单处理](form-handling.md)**: 完整的表单自动化工作流程
- **[文件操作](file-operations.md)**: 文件上传自动化

键盘 API 消除了键盘自动化的复杂性，为从简单按键到复杂快捷键和序列的所有内容提供了干净、可靠的方法。
