# 行为 Fingerprinting

行为 fingerprinting 分析的是用户与 Web 应用的交互方式，而非他们使用的工具。虽然网络和浏览器指纹可以通过设置正确的值来伪造，但人类行为遵循生物力学模式，难以令人信服地复制。检测系统收集鼠标移动、击键时间、滚动行为和交互序列，然后使用统计模型来区分人类和自动化。

本文档涵盖检测技术、背后的科学原理，以及 Pydoll 的人性化功能如何应对各个检测向量。

!!! info "模块导航"
    - [网络 Fingerprinting](./network-fingerprinting.md)：TCP/IP、TLS、HTTP/2 协议 fingerprinting
    - [浏览器 Fingerprinting](./browser-fingerprinting.md)：Canvas、WebGL、navigator 属性
    - [规避技术](./evasion-techniques.md)：实用对策

## 鼠标移动分析

鼠标移动是最强大的行为指标之一，因为人类的运动控制遵循生物力学定律，简单的自动化无法复制。检测系统收集 `mousemove` 事件（每个事件包含 x、y 坐标和时间戳），并分析轨迹的属性，以区分有机移动和程序化光标瞬移。

### Fitts's Law

Fitts's Law 描述将指针移动到目标所需的时间。Shannon 公式（MacKenzie, 1992）是使用最广泛的版本，表述如下：

```
T = a + b * log2(D/W + 1)
```

其中 `T` 是移动时间，`a` 是代表反应/启动时间的常数，`b` 是代表输入设备固有速度的常数，`D` 是到目标的距离，`W` 是目标的宽度（大小）。对数关系意味着距离加倍会增加固定的时间量，而目标大小减半也会增加相同的固定时间量。

这对机器人检测具有重要意义。人类到达小而远的目标需要更长时间，而到达大而近的目标则很快。他们在移动开始时加速，大约在路径中点达到峰值速度，并在接近目标时减速。如果机器人无论距离和目标大小如何都以恒定时间移动光标，就违反了 Fitts's Law，很容易被检测到。

检测系统测量每次点击事件的移动时间，根据距离和目标大小计算预期时间，并标记那些明显快于 Fitts's Law 预测或在距离/大小与移动时间之间没有相关性的移动。

### 轨迹形状

两点之间的人类手部移动不是直线。Abend、Bizzi 和 Morasso（1982）的研究表明，由于手臂关节和肌肉的生物力学约束，手部路径通常是弯曲的。Flash 和 Hogan（1985）证明，人类到达运动遵循最小 jerk 轨迹，即轨迹在移动持续时间内最小化 jerk（加速度的导数）的积分。由此产生的速度曲线呈钟形，用五次（5 阶）多项式描述：

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

其中 `t` 是从 0 到 1 的归一化时间，`x0`/`xf` 是起始和终止位置。这会产生从静止开始的平滑加速、大约在路径中点的峰值速度，以及回到静止的平滑减速。

检测系统分析轨迹曲率、速度曲线和加速度模式。它们寻找的具体信号包括：

**直线检测。** 两点之间完全笔直的路径（每个采样点曲率为零）是最明显的机器人信号。由于手臂旋转关节的存在，人类路径总是有一定的曲率。

**恒定速度。** 人类表现出钟形速度曲线（加速、达到峰值、减速）。整个移动过程中恒定的速度表明是线性插值，这是大多数自动化工具的默认行为。

**缺少子移动。** 长距离移动由多个重叠的子移动组成（Meyer 等，1988），每个子移动都有自己的速度峰值。覆盖 500+ 像素但只有一个平滑速度峰值的移动是可疑的；该距离的真实移动通常会显示 2-4 个速度峰值。

**无 overshoot。** 人类经常会略微超过目标（5-15 像素），然后做一个小的校正回来。每次都精确命中目标的完美移动在统计上是不可能的。

### 移动熵

在这个语境中，熵衡量鼠标路径的不可预测性。检测系统将轨迹分成段，测量每个点的方向变化，并计算方向变化分布上的 Shannon 熵。直线的熵为零（每段指向相同方向）。随机游走的熵最大。人类移动具有中等到高的熵，反映了有意方向和非自主变异性的结合。

在一个会话中多次鼠标移动都表现出低熵是一个强烈的机器人信号，即使个别移动具有合理的曲率。

### Pydoll 的鼠标 humanize 功能

Pydoll 通过点击操作上的 `humanize=True` 参数实现了全面的鼠标人性化。启用后，鼠标模块会生成针对上述每个检测向量的移动：

路径遵循带有随机控制点的三次 Bezier 曲线，产生自然曲率而非直线。沿路径的速度遵循最小 jerk 曲线（`10t^3 - 15t^4 + 6t^5`），产生 Fitts's Law 预测的钟形速度曲线。移动持续时间使用 Fitts's Law 和可配置常数（默认 `a=0.070`，`b=0.150`）计算。

通过向光标位置添加高斯噪声来模拟生理震颤，振幅与速度成反比（当手移动缓慢时震颤更明显，这与真实生理学一致）。overshoot 以 70% 的概率发生，超过目标总距离的 3-12%，然后进行校正移动。微停顿（15-40ms）以 3% 的概率在移动过程中发生，模拟短暂的犹豫。

```python
# 基本的 humanize 点击
await element.click(humanize=True)

# 也可以直接使用 Mouse 类获得更多控制
from pydoll.interactions.mouse import Mouse

mouse = Mouse(connection_handler)
await mouse.click(500, 300, humanize=True)
```

!!! note "Pydoll 目前未实现的功能"
    Pydoll 的鼠标人性化目前不会对非常长的距离建模子移动（路径是单个 Bezier 段）。对于大多数 Web 交互（距离在 500 像素以内），这已经足够了。极长的移动（全屏对角线穿越）可能会受益于未来的多段支持。

## 击键动态

击键动态分析键盘输入的时间模式。该技术可以追溯到 1850 年代的电报操作员，他们可以通过各自的莫尔斯电码"拳头"（特征性时间模式）来识别彼此。现代系统通过 `keydown` 和 `keyup` 事件以毫秒精度测量时间。

### 时间特征

两个基本测量是停留时间（单个按键 `keydown` 和 `keyup` 之间的持续时间，人类通常为 50-200ms）和飞行时间（释放一个键到按下下一个键之间的持续时间，通常为 80-400ms）。连续按键对的停留时间和飞行时间的组合称为二元组（digraph）延迟。

二元组延迟并不均匀。它们取决于键入的特定按键对（bigram），因为打字是一种运动技能，常见序列存储为程序记忆。关键的生物力学因素包括：

**双手交替。** 用双手交替输入的 bigram（如 "th"，在 QWERTY 键盘上 "t" 是左手，"h" 是右手）通常比同一只手输入的 bigram（如 "de"，两个键都在左手）更快。交替手可以在第一只手完成击键时就开始移动。

**手指距离。** 主行到主行的过渡最快。到达顶行或底行会增加与手指必须移动的物理距离成比例的时间。

**手指独立性。** 同一只手上的无名指和小指组合比食指和中指组合更慢，因为无名指和小指共享肌腱，独立运动控制能力较弱。

**频率效应。** 经常输入的 bigram（如英语中的 "th"、"er"、"in"）由于运动记忆而执行更快，与其物理布局无关。

### 检测信号

检测系统寻找几种将人类打字与自动化区分开的信号：

**零或恒定停留时间。** 许多自动化工具在 `keydown` 和 `keyup` 事件之间以零或接近零的延迟（低于 5ms）发送。真实的按键具有可测量的停留时间。所有按键的停留时间恒定同样可疑。

**均匀飞行时间。** 设置固定的击键间隔（如 `type_text("hello", interval=0.1)`）会产生完全规律的时间，非常容易被检测。人类的飞行时间因 bigram、疲劳和认知负荷而变化。

**无打字错误。** 在较长的文本输入（50+ 个字符）中，完全没有退格键或删除键的按下是不寻常的。人类的错误率大约为 1-5%，取决于打字熟练度和文本复杂度。

**超人速度。** 持续超过 150 WPM 的打字速度超出了除精英竞技打字员以外所有人的能力。比这更快发送字符的自动化工具会立即被标记。

### Pydoll 的键盘 humanize 功能

Pydoll 的 `type_text(humanize=True)` 通过可配置参数应对每个检测向量：

击键延迟从均匀分布中抽取（默认 30-120ms），而不是固定间隔。标点字符（`.!?;:,`）接收额外延迟（80-180ms），模拟打字者考虑句子结构时的停顿。思考停顿（300-700ms）以 2% 的概率发生，模拟短暂的思考时刻。分心停顿（500-1200ms）以 0.5% 的概率发生，模拟打字者看向别处或被短暂打断。

逼真的打字错误以大约每字符 2% 的概率发生，包含五种按其真实世界频率加权的不同错误类型：相邻键错误（55%，按下 QWERTY 键盘上的相邻键）、换位（20%，交换两个连续字符）、重复按键（12%，连续按两次键）、跳过字符（8%，在正确输入前犹豫）和遗漏空格（5%，忘记单词之间的空格）。每种错误类型包含逼真的恢复序列（停顿、退格、校正）和适当的时间。

```python
# Humanize 打字
await element.type_text("Hello, world!", humanize=True)

# 使用自定义时间配置
from pydoll.interactions.keyboard import Keyboard, TimingConfig, TypoConfig

config = TimingConfig(
    keystroke_min=0.04,
    keystroke_max=0.15,
    thinking_probability=0.03,
)
keyboard = Keyboard(connection_handler, timing_config=config)
await keyboard.type_text("Custom timing example", humanize=True)
```

!!! note "Pydoll 目前未实现的功能"
    Pydoll 的键盘人性化使用均匀随机延迟，而非基于 bigram 的时间。它不会建模每个按键的停留时间变化或双手交替速度差异。对于大多数自动化场景（表单填写、搜索查询），均匀变化足以通过行为检测。需要认证级别击键生物识别规避的应用需要自定义时间模型。

## 滚动行为分析

滚动 fingerprinting 分析用户如何在页面内容中进行垂直（和水平）导航。人类滚动和自动滚动之间的区别非常明显：程序化的 `window.scrollTo()` 调用产生即时的离散跳跃，而通过鼠标滚轮、触控板或触摸屏进行的人类滚动则产生一连串带有惯性和减速效果的小增量事件。

### 物理滚动特征

鼠标滚轮滚动产生带有一致 delta 值的离散 `wheel` 事件（通常每个凹槽 100 或 120 像素，取决于操作系统和浏览器）。事件以不规则的间隔到达，反映用户转动滚轮的速度。触控板滚动产生许多小事件，delta 值递减，模拟物理惯性。触摸滚动类似于触控板，但初始 delta 更大，减速尾部更长。

检测系统分析 delta 分布、事件间时间和减速曲线。`scrollTo(0, 5000)` 调用产生单次跳跃且没有中间事件，这与人类滚动产生的数百个增量事件根本不同。

### 检测信号

**即时滚动。** 使用 `window.scrollTo()` 或 `window.scrollBy()` 配合大值会产生零中间滚动事件。监听 `scroll` 事件的检测系统会看到滚动位置在单帧内发生变化。

**均匀 delta。** 程序化滚动模拟以恒定 delta 值发送 wheel 事件（例如始终 100 像素），缺少人类滚动中的自然变化，人类滚动的 delta 值由于手指压力不一致会波动 10-30%。

**无减速。** 人类滚动，尤其是在触控板上，有一个惯性阶段，在用户抬起手指后滚动继续，速度呈指数递减。突然停止的自动滚动缺少这个减速尾部。

**缺少方向变化。** 人类经常过度滚动然后略微回滚，或在页面中途暂停阅读内容。以恒定速度沿一个方向移动而没有暂停或反转的自动滚动是可疑的。

### Pydoll 的滚动 humanize 功能

Pydoll 的滚动模块通过 `scroll.by(position, distance, humanize=True)` 实现人性化滚动：

滚动遵循三次 Bezier 缓动曲线（默认控制点 `0.645, 0.045, 0.355, 1.0`），产生自然的加速和减速。每帧 ±3 像素的 jitter 为 delta 值添加变化。微停顿（20-50ms）以 5% 的概率发生，模拟短暂的阅读停顿。overshoot 以 15% 的概率发生，滚过目标 2-8% 然后校正回来。对于长距离，滚动被分解为多个"轻弹"手势（每次 100-1200 像素），模拟真实用户通过重复滑动而非单次连续动作来滚动长页面的方式。

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)

# Humanize 向下滚动 800 像素
await scroll.by(ScrollPosition.Y, 800, humanize=True)

# 滚动到顶部/底部使用多次类人轻弹
await scroll.to_bottom(humanize=True)
```

## 其他检测向量

除了鼠标、键盘和滚动分析之外，复杂的检测系统还监控其他几种行为信号。

### 焦点和可见性

Page Visibility API（`document.visibilityState`）和焦点事件（`window.onfocus`、`window.onblur`）揭示用户是否在主动查看页面。真实用户的会话包括标签页切换、窗口最小化和不活动期。一个连续保持焦点数小时而没有一个 blur 事件的自动化脚本在行为上是异常的。同样，`document.hasFocus()` 在较长时间内持续返回 `true` 也是不寻常的。

### 空闲模式

真实用户有自然的空闲期：阅读内容、在行动前思考、被分心。检测系统测量交互之间空闲时间的分布。如果一个会话中每个动作都在前一个动作的 100-500ms 内发生，没有更长的停顿，这种模式在统计上与人类浏览有明显区别——人类浏览中动作之间 2-30 秒的空闲期是正常的。

### 事件序列完整性

浏览器为用户交互生成特定的事件序列。一次鼠标点击产生 `pointerdown`、`mousedown`、`pointerup`、`mouseup`、`click`，按此顺序，之前还有 `pointermove`/`mousemove` 事件显示光标正在接近点击目标。发送裸 `click` 事件而没有前置移动和指针事件的自动化工具可以通过事件序列分析被检测到。

Pydoll 基于 CDP 的事件发送生成完整的事件序列，因为它使用 Chrome 的输入模拟，产生与真实用户输入相同的事件链。

## 机器学习检测

现代反机器人系统（DataDome、Akamai Bot Manager、Cloudflare Bot Management、PerimeterX/HUMAN Security）不使用简单的阈值规则。它们在数百万真实用户会话和数百万已知机器人会话上训练机器学习模型，学习基于 50+ 个特征同时区分人类和自动化。

这些模型捕获难以列举为单独规则的统计属性：移动速度和曲率的联合分布、打字速度和错误率之间的相关性、滚动深度和阅读时间之间的关系，以及浏览会话的整体"节奏"。一个通过每项单独检查但在特征之间存在微妙错误相关性的系统，仍然可以被训练良好的模型标记。

实际意义在于，行为规避必须在所有交互类型之间保持一致，而不仅仅是单独看起来合理。Pydoll 的 `humanize=True` 参数提供了跨鼠标、键盘和滚动交互的连贯人性化层，但开发者仍然需要负责更高层面的行为合理性：在页面加载之间添加阅读延迟、变化多页工作流的节奏，以及包含自然的空闲期。

## 参考文献

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
