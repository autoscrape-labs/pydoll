# 键盘

通过 `tab.keyboard` 驱动键盘输入：往字段里打字、按下 Enter 和 Tab 之类的特殊键，以及运行 Ctrl+A 这样的快捷键。当一个表单需要键盘导航，或者某个 web 应用会响应点击无法触发的组合键时，就该用它。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://www.wikipedia.org')

        search = await tab.find(id='searchInput')
        await search.type_text('web scraping', humanize=True)

        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(2)
        print(await tab.current_url)

asyncio.run(main())
```

## 往字段里打字

要逐字符地往获得焦点的元素里打字，在元素上使用 `type_text`。传入 `humanize=True` 可获得可变的节奏并偶尔修正打错的字；不传则用固定、更快的节奏。

```python
field = await tab.find(id='searchInput')
await field.type_text('search query', humanize=True)
```

在下面输入你自己的文本，两种方式都跑一遍。带 `humanize=True` 时节奏会变化、偶尔打错的字会被修正，所以每次运行都不一样；不带时，每个间隔都是固定的 50 毫秒。

<iframe src="/docs/resources/visuals/keyboard-humanize.html" aria-label="Interactive humanized typing: type text and watch it typed with human rhythm and corrected typos" style="width: 100%; height: 350px; border: 0;" loading="lazy"></iframe>

如果你只需要文本出现、并不关心逐键事件，`insert_text` 会把整个字符串一次性粘贴进去：

```python
await field.insert_text('search query')   # 瞬时，无按键事件
```

!!! note "`tab.keyboard` 在焦点已经所在处打字"
    在元素上调用的 `type_text` 和 `insert_text` 会替你把该元素设为焦点，因此文本会落在正确的位置。而更底层的 `tab.keyboard` 方法（见下文）不会：它们把按键发送到页面当前获得焦点的任何地方。通过 `tab.keyboard` 打字前，先让字段获得焦点（点击它就会使其获得焦点）。

## 按下一个键

`press()` 执行一次完整的按键（按下、短暂保持、抬起）。用它来按那些触发行为而非输入文本的键：Enter 提交、Tab 在字段间移动、Escape 关闭。

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# 方向键和导航键
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.END)
```

`press(key, interval=0.1)` 会在释放前把键保持 `interval` 秒；把它调大可模拟更长的按住。

## 运行键盘快捷键

`hotkey()` 按下一个组合并以正确的顺序释放，因此你不用自己计算修饰键的位掩码。把修饰键放在前面。

```python
from pydoll.constants import Key

await tab.keyboard.hotkey(Key.CONTROL, Key.A)   # 全选
await tab.keyboard.hotkey(Key.CONTROL, Key.C)   # 复制
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # 向左选中一个词
```

macOS 用 Command（Meta），而 Windows 和 Linux 用 Control，所以要根据平台挑选修饰键：

```python
import sys
from pydoll.constants import Key

mod = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(mod, Key.C)
```

## 给单个键施加修饰键

`press()` 和 `down()` 接受一个来自 `KeyModifier` 枚举的 `modifiers` 参数：

```python
from pydoll.protocol.input.types import KeyModifier

await tab.keyboard.press(Key.S, modifiers=KeyModifier.CTRL)   # Ctrl+S
```

成员有 `KeyModifier.ALT`、`.CTRL`、`.META` 和 `.SHIFT`。`hotkey()` 已经替你施加了修饰键，因此只有当你手动按下或按住单个键时才需要用到 `modifiers`。

## 按住并释放键

对于修饰键要跨多次按键保持按下的序列，自己驱动 `down()` 和 `up()`。在 `finally` 块中释放，这样序列中途出错也不会留下卡住的键。

```python
from pydoll.constants import Key

try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)   # 扩展选区
    await tab.keyboard.press(Key.ARROWRIGHT)
finally:
    await tab.keyboard.up(Key.SHIFT)
```

## 浏览器 UI 快捷键不起作用

通过 DevTools 协议发送的按键被标记为不可信，因此它们绝不会触发 Chrome 自身的 UI。打开标签页、DevTools 或地址栏的快捷键是无效的。文档内部的页面级快捷键则正常工作。

!!! warning "用浏览器命令，而不是 UI 快捷键"
    Ctrl+T、Ctrl+W、F12 和 Ctrl+L 都不会有任何效果。改为通过浏览器的 API 来驱动它：`await browser.new_tab()`、`await tab.close()`、`await tab.go_to(url)`、`await tab.refresh()`。作用于页面内容的快捷键（Ctrl+A、Ctrl+C、Tab、Enter、方向键）会如预期般工作。

## 按键参考

`Key`（`from pydoll.constants import Key`）覆盖了整个键盘：

| 类别 | 成员 |
|----------|---------|
| 字母 | `Key.A` 到 `Key.Z` |
| 数字 | `Key.DIGIT0` 到 `Key.DIGIT9`，`Key.NUMPAD0` 到 `Key.NUMPAD9` |
| 功能键 | `Key.F1` 到 `Key.F12` |
| 导航 | `ARROWUP`、`ARROWDOWN`、`ARROWLEFT`、`ARROWRIGHT`、`HOME`、`END`、`PAGEUP`、`PAGEDOWN` |
| 修饰键 | `CONTROL`、`SHIFT`、`ALT`、`META` |
| 编辑 | `ENTER`、`TAB`、`SPACE`、`BACKSPACE`、`DELETE`、`ESCAPE`、`INSERT` |

## 下一步

- [鼠标](mouse.md)：点击、移动和拖动，带拟人化时间。
- [查找元素](element-finding.md)：定位你要往里打字的字段。
- [拟人化交互](../stealth/human-like-interactions.md)：`humanize=True` 在内部做了什么。
