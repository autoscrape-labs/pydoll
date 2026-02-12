# 鼠标控制

鼠标API提供页面级别的完整鼠标输入控制，支持模拟逼真的光标移动、点击、双击和拖拽操作。默认情况下，所有鼠标操作使用人性化模拟：路径遵循自然贝塞尔曲线，配合菲茨定律时序、最小急动速度曲线、生理性手抖和过冲修正，使自动化操作几乎无法与人类行为区分。

!!! info "集中式鼠标接口"
    所有鼠标操作均通过`tab.mouse`访问，为所有鼠标交互提供简洁统一的API。

## 快速开始

```python
from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')

    # 移动光标到指定位置（默认人性化）
    await tab.mouse.move(500, 300)

    # 在指定位置点击（默认人性化）
    await tab.mouse.click(500, 300)

    # 右键点击
    await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

    # 双击
    await tab.mouse.double_click(500, 300)

    # 从一个位置拖拽到另一个位置
    await tab.mouse.drag(100, 200, 500, 400)
```

## 核心方法

### move: 移动光标

将鼠标光标移动到页面上的指定位置：

```python
# 人性化移动（默认，自然时序的曲线路径）
await tab.mouse.move(500, 300)

# 瞬时移动（单个CDP事件，无模拟）
await tab.mouse.move(500, 300, humanize=False)
```

**参数：**

- `x`：目标X坐标（CSS像素）
- `y`：目标Y坐标（CSS像素）
- `humanize`（仅关键字）：模拟人类般的曲线移动（默认：`True`）

### click: 在指定位置点击

移动到指定位置并执行鼠标点击：

```python
from pydoll.protocol.input.types import MouseButton

# 左键点击，包含人性化移动（默认）
await tab.mouse.click(500, 300)

# 右键点击
await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

# 通过click_count实现双击
await tab.mouse.click(500, 300, click_count=2)

# 瞬时点击，不使用人性化
await tab.mouse.click(500, 300, humanize=False)
```

**参数：**

- `x`：目标X坐标
- `y`：目标Y坐标
- `button`（仅关键字）：鼠标按钮，可选 `LEFT`、`RIGHT`、`MIDDLE`（默认：`LEFT`）
- `click_count`（仅关键字）：点击次数（默认：`1`）
- `humanize`（仅关键字）：模拟人类般的行为（默认：`True`）

### double_click: 在指定位置双击

等价于`click(x, y, click_count=2)`的便捷方法：

```python
await tab.mouse.double_click(500, 300)
await tab.mouse.double_click(500, 300, humanize=False)
```

### down / up: 底层按钮控制

独立按下或释放鼠标按钮：

```python
# 在当前位置按下左键
await tab.mouse.down()

# 释放左键
await tab.mouse.up()

# 右键
await tab.mouse.down(button=MouseButton.RIGHT)
await tab.mouse.up(button=MouseButton.RIGHT)
```

这些是底层原语，在当前光标位置操作，没有`humanize`参数。

### drag: 拖放

按住鼠标按钮从起点移动到终点：

```python
# 人性化拖拽（默认）
await tab.mouse.drag(100, 200, 500, 400)

# 瞬时拖拽，不使用人性化
await tab.mouse.drag(100, 200, 500, 400, humanize=False)
```

**参数：**

- `start_x`、`start_y`：起始坐标
- `end_x`、`end_y`：结束坐标
- `humanize`（仅关键字）：模拟人类般的拖拽（默认：`True`）

## 禁用人性化

所有鼠标方法默认使用`humanize=True`。要执行瞬时非人性化操作，传入`humanize=False`：

```python
# 瞬时移动，单个CDP mouseMoved事件
await tab.mouse.move(500, 300, humanize=False)

# 瞬时点击：移动+按下+释放，无模拟
await tab.mouse.click(500, 300, humanize=False)

# 瞬时拖拽，无曲线，无停顿
await tab.mouse.drag(100, 200, 500, 400, humanize=False)
```

这在速度至关重要且不需要规避检测时很有用，例如测试环境或内部工具。

## 人性化模式

启用`humanize=True`时（默认），鼠标模块应用多层逼真效果：

### 贝塞尔曲线路径

鼠标沿自然曲线轨迹移动，而非直线。控制点在起点→终点连线的垂直方向上随机偏移，采用非对称放置（移动初期曲率更大，模拟真实的弹道伸展）。

### 菲茨定律时序

移动持续时间遵循菲茨定律：`MT = a + b × log₂(D/W + 1)`。距离越远所需时间成比例增加，符合人类运动控制行为。

### 最小急动速度曲线

光标遵循钟形速度曲线，起始缓慢，中间加速到峰值速度，然后在末尾减速。这符合最平滑的人类运动轨迹。

### 生理性手抖

每帧添加小幅高斯噪声（σ ≈ 1像素），模拟手部震颤。颤抖幅度与速度成反比，光标缓慢或悬停时颤抖更多，快速弹道运动时颤抖减少。

### 过冲与修正

对于快速长距离移动（约70%概率），光标会超过目标3–12%的距离，然后做一个小的修正子运动回到目标。这符合真实人类运动控制数据。

### 点击前停顿

人性化点击包含点击前停顿（50–200毫秒），模拟按下按钮前的自然稳定时间。

## 自动人性化元素点击

当您使用`element.click()`时，鼠标API会自动使用，从当前光标位置到元素中心产生逼真的贝塞尔曲线运动后再点击。这意味着每次`element.click()`调用都会产生自然的鼠标移动，使元素点击与人类行为无法区分。

```python
# 人性化点击（默认）：贝塞尔曲线运动+点击
button = await tab.find(id='submit')
await button.click()

# 带中心偏移
await button.click(x_offset=10, y_offset=5)

# 禁用人性化：原始CDP按下/释放，无光标移动
await button.click(humanize=False)
```

位置追踪在元素点击之间保持。点击元素A，然后点击元素B，会产生从A到B的自然曲线路径。

## 自定义时序配置

所有人性化参数均可通过`MouseTimingConfig`配置：

```python
from pydoll.interactions.mouse import Mouse, MouseTimingConfig

config = MouseTimingConfig(
    fitts_a=0.070,              # 菲茨定律截距（秒）
    fitts_b=0.150,              # 菲茨定律斜率（秒/比特）
    frame_interval=0.012,       # mouseMoved事件间的基础间隔
    curvature_min=0.10,         # 最小路径曲率（距离的分数）
    curvature_max=0.30,         # 最大路径曲率
    tremor_amplitude=1.0,       # 颤抖sigma值（像素）
    overshoot_probability=0.70, # 快速移动时过冲的概率
    min_duration=0.08,          # 最小移动持续时间
    max_duration=2.5,           # 最大移动持续时间
)

# 与Tab一起使用
tab._mouse = Mouse(tab, timing=config)
```

查看`MouseTimingConfig`数据类了解所有可用参数。

## 位置追踪

鼠标API在操作之间追踪光标位置：

```python
# 初始位置为(0, 0)
await tab.mouse.move(100, 200)
# 位置现在是(100, 200)

await tab.mouse.click(300, 400)
# 位置现在是(300, 400)

# 底层方法使用追踪的位置
await tab.mouse.down()   # 在(300, 400)按下
await tab.mouse.up()     # 在(300, 400)释放
```

!!! note "位置状态"
    鼠标位置在内部追踪。`WebElement.click()`在可用时自动使用`tab.mouse`，因此位置追踪在元素点击之间保持一致。

## 调试模式

启用调试模式以在页面上可视化鼠标移动。激活后，彩色点将绘制在透明覆盖画布上：

- **蓝色点**：移动过程中的光标路径
- **红色点**：点击位置

```python
# 通过构造函数启用
from pydoll.interactions.mouse import Mouse
tab._mouse = Mouse(tab, debug=True)

# 或通过属性在运行时切换
tab.mouse.debug = True

# 现在所有移动都会绘制彩色点
await tab.mouse.click(500, 300)

# 完成后禁用
tab.mouse.debug = False
```

这对于调整时序参数和验证路径是否自然很有用。

## 实用示例

### 以逼真移动点击按钮

```python
async def click_button_naturally(tab):
    button = await tab.find(id='submit')
    bounds = await button.get_bounds_using_js()
    center_x = bounds['x'] + bounds['width'] / 2
    center_y = bounds['y'] + bounds['height'] / 2

    await tab.mouse.click(center_x, center_y)
```

### 拖动滑块

```python
async def drag_slider(tab):
    slider = await tab.find(css_selector='.slider-handle')
    bounds = await slider.get_bounds_using_js()

    start_x = bounds['x'] + bounds['width'] / 2
    start_y = bounds['y'] + bounds['height'] / 2
    end_x = start_x + 200  # 向右拖拽200像素

    await tab.mouse.drag(start_x, start_y, end_x, start_y)
```

### 悬停在元素上

```python
async def hover_menu(tab):
    menu = await tab.find(css_selector='.dropdown-trigger')
    bounds = await menu.get_bounds_using_js()

    await tab.mouse.move(
        bounds['x'] + bounds['width'] / 2,
        bounds['y'] + bounds['height'] / 2,
    )
    # 菜单现在应通过CSS :hover可见
```

## 了解更多

- **[类人交互](human-interactions.md)**：所有人性化交互的概述
- **[键盘控制](keyboard-control.md)**：逼真的键盘模拟
