# 鼠标

Pydoll 用两种方式驱动鼠标：通过你找到的元素，这是大多数情况下你需要的方式；或者在需要精确位置时，直接使用页面坐标。两者都支持 `humanize=True`，它让光标沿着一条带弧度、有人类节奏的路径移动，而不是瞬移到目标。

<iframe src="/docs/resources/visuals/mouse-humanize.html" aria-label="Humanized curved cursor path versus an instant robotic jump" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## 点击一个元素

常见情形是点击你已经用 `find()` 或 `query()` 定位到的元素。在它上面调用 `click()`；你不用计算坐标，而且元素会先被滚动到可见区域。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/add_remove_elements/')

        add_button = await tab.find(text='Add Element')
        await add_button.click()

        # 这次点击添加了一个 Delete 按钮
        delete = await tab.find(class_name='added-manually')
        print('Added:', await delete.text)

asyncio.run(main())
```

`click()` 接受几个选项：

```python
# 点击相对元素中心偏移的一个点（像素）
await element.click(x_offset=10, y_offset=5)

# 释放前把按钮多按住一会儿（秒）
await element.click(hold_time=0.3)

# 拟人化：光标沿弧线移动到元素，然后点击
await element.click(humanize=True)
```

!!! note "元素点击 vs 原始坐标"
    优先使用 `element.click()`。它会替你找出元素的位置，并且能挺过布局变动。只有在没有元素可作为目标时，比如在 `<canvas>` 内部点击或按像素拖动一个手柄，才求助下面的坐标 API。

## 坐标鼠标 API

`tab.mouse` 在明确的坐标处点击、移动和拖动，坐标以 CSS 像素为单位，从页面左上角算起。你通常从元素的边界得到这些坐标（参见[拖动滑块](#drag-a-slider)）。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/')

        await tab.mouse.move(500, 300)                        # 移动光标
        await tab.mouse.click(500, 300)                       # 左键点击
        await tab.mouse.click(500, 300, button=MouseButton.RIGHT)  # 右键点击
        await tab.mouse.double_click(500, 300)               # 双击
        await tab.mouse.drag(100, 200, 500, 400)             # 按下、移动、释放

asyncio.run(main())
```

`MouseButton`（来自 `pydoll.protocol.input.types`）有 `LEFT`、`MIDDLE` 和 `RIGHT`。`click()` 还接受 `click_count`（传 `2` 表示双击），而且每个方法都接受仅限关键字的 `humanize`。

要分别按下和释放，`down()` 和 `up()` 在当前光标位置操作：

```python
await tab.mouse.move(300, 400)
await tab.mouse.down(button=MouseButton.LEFT)
await tab.mouse.move(600, 400)     # 手动拖动
await tab.mouse.up(button=MouseButton.LEFT)
```

`tab.mouse` 会跨调用追踪光标位置，因此 `down()`/`up()` 作用在上一次 `move()` 或 `click()` 留下的位置。

## 像人一样移动

默认情况下，一次移动或点击会径直跳到目标，这是一种行为上的破绽。传入 `humanize=True`，Pydoll 就让光标沿着一条带弧度、有人类节奏的路径移动（符合 Fitts 定律的耗时、钟形的速度曲线、细微的抖动，以及偶尔的过冲加修正）：

```python
await tab.mouse.move(500, 300, humanize=True)
await tab.mouse.click(500, 300, humanize=True)
await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

> 🎞️ **GIF 占位** — 光标沿着一条带弧度、逐渐减速的拟人化路径移动，并带一点过冲，旁边是一条直线跳跃作对比。

拟人化的元素点击同理。由于位置是被追踪的，先点击元素 A 再点击元素 B，会从一个描出一条自然的弧线到另一个：

```python
# 瞬时：光标径直跳到每个目标
await (await tab.find(id='first')).click()
await (await tab.find(id='second')).click()

# 拟人化：光标从一个目标自然地弧线过渡到下一个
await (await tab.find(id='first')).click(humanize=True)
await (await tab.find(id='second')).click(humanize=True)
```

关于完整的时间模型以及拟人化在什么时候重要，参见[拟人化交互](../stealth/human-like-interactions.md)。

### 调节时间参数 {#tune-the-timing}

拟人化的物理参数可通过 `MouseTimingConfig` 配置。给 `tab.mouse.timing` 赋一个新的配置：

```python
from pydoll.interactions.mouse import MouseTimingConfig

tab.mouse.timing = MouseTimingConfig(
    fitts_a=0.070,               # 基础移动时间（秒）
    fitts_b=0.150,               # 每一比特难度所增加的时间
    curvature_min=0.10,          # 最小路径弧度（占距离的比例）
    curvature_max=0.30,          # 最大路径弧度
    tremor_amplitude=1.0,        # 手部抖动的 sigma，单位像素
    overshoot_probability=0.70,  # 快速长距离移动时发生过冲的概率
    max_duration=2.5,            # 单次移动的时长上限（秒）
)
```

每个字段都有默认值，所以只需覆盖你需要的。完整列表见 `pydoll/interactions/mouse.py` 中的 `MouseTimingConfig` 数据类。

## 调节时观察光标

设置 `tab.mouse.debug = True`，Pydoll 会在一个透明覆盖层上绘制光标路径：蓝点勾勒移动，红点标记点击。用它检查拟人化路径看起来是否自然，然后关掉。

```python
tab.mouse.debug = True
await tab.mouse.click(500, 300, humanize=True)
tab.mouse.debug = False
```

## 实用示例

### 拖动滑块 {#drag-a-slider}

从手柄的边界读取它的位置，然后从那里开始拖动：

```python
slider = await tab.query('.slider-handle')
bounds = await slider.get_bounds_using_js()   # {'x', 'y', 'width', 'height'}，视口像素

start_x = bounds['x'] + bounds['width'] / 2
start_y = bounds['y'] + bounds['height'] / 2

await tab.mouse.drag(start_x, start_y, start_x + 200, start_y, humanize=True)
```

> 🎞️ **GIF 占位** — 滑块手柄沿着一条拟人化路径向右被拖动 200 像素。

### 悬停在菜单上

把光标移到一个元素上以触发它的 CSS `:hover` 状态，而不点击：

```python
trigger = await tab.query('.dropdown-trigger')
bounds = await trigger.get_bounds_using_js()

await tab.mouse.move(
    bounds['x'] + bounds['width'] / 2,
    bounds['y'] + bounds['height'] / 2,
    humanize=True,
)
```

> 🎞️ **GIF 占位** — 光标移到菜单触发器上，其下拉菜单在悬停时展开。

## 下一步

- [键盘](keyboard.md)：输入文本、按键，采用同样的拟人化时间。
- [拟人化交互](../stealth/human-like-interactions.md)：`humanize=True` 背后的时间模型，以及何时使用它。
- [查找元素](element-finding.md)：定位你要点击和拖动的元素。
