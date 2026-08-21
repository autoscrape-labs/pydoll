# Behavioral fingerprinting

Behavioral fingerprinting 分析的是用户如何与页面交互，而不是他们用什么工具。网络和浏览器 fingerprint 可以通过设置正确的值来伪造，但人类行为遵循难以令人信服地复制的生物力学模式。检测系统收集鼠标移动、按键时序、滚动行为和交互序列，然后用统计模型把人类和自动化区分开来。本页解释这些技术、它们背后的科学，以及 Pydoll 的拟人化如何应对每一项。

## 鼠标移动分析

鼠标移动是最强的行为指标之一，因为人类的运动控制遵循简单自动化无法重现的生物力学规律。检测系统收集 `mousemove` 事件（每个事件都带有 x、y 坐标和一个时间戳），并分析轨迹，寻找能把有机移动与程序化光标瞬移区分开来的特性。

### Fitts's Law

Fitts's Law 描述了将指针移动到目标所需的时间。Shannon 形式（MacKenzie, 1992）是使用最广泛的：

```
T = a + b * log2(D/W + 1)
```

`T` 是移动时间，`a` 是起始/反应常数，`b` 是输入设备固有的速度，`D` 是到目标的距离，`W` 是目标宽度。这个对数意味着距离翻倍会增加固定的时间量，而目标尺寸减半会增加同样的固定时间量。

它对检测的影响是直接的。人类到达又小又远的目标需要更长时间，而快速到达又大又近的目标。他们在起始时加速，在大约路径中点达到峰值速度，在到达时减速。一个无论距离和目标尺寸如何都以恒定时间移动的机器人，违反了 Fitts's Law，极易被检测到。检测系统会测量每次点击前的移动时间，根据距离和目标尺寸计算 Fitts's Law 所预测的时间，并标记那些远快于预测、或距离/尺寸与时间之间毫无相关性的移动。

### 轨迹形状

人手在两点之间的移动不是直线。Abend、Bizzi 和 Morasso（1982）表明，由于手臂的关节和肌肉，手的路径是弯曲的。Flash 和 Hogan（1985）表明，够取动作遵循最小急动度（minimum-jerk）轨迹，即在整个移动过程中使急动度（加速度的导数）的积分最小化。速度曲线呈钟形，用一个五次多项式描述：

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

其中 `t` 是从 0 到 1 归一化的时间，`x0`/`xf` 是起始和结束位置。这带来了从静止开始的平滑加速、路径中点附近的峰值速度，以及平滑减速回到静止。

检测系统分析曲率、速度和加速度，寻找四个破绽：

- **直线路径。** 每个采样点的曲率都为零，是最明显的机器人信号；人类的路径总是弯曲的，因为手臂围绕关节旋转。
- **恒定速度。** 人类呈现钟形的速度曲线。恒定速度表明是线性插值，这是大多数自动化工具的默认做法。
- **没有子移动（sub-movements）。** 长距离移动是由重叠的子移动构成的（Meyer et al., 1988），每个子移动都有自己的速度峰值。一次 500 像素的移动只有单个平滑峰值是可疑的；真实的移动会呈现 2 到 4 个峰值。
- **没有过冲。** 人类经常会过冲 5 到 15 像素然后修正回来。每次都精确落在目标上，从统计学上讲不太可能。

### 移动熵

这里的熵衡量的是路径有多不可预测。检测系统把轨迹拆分成若干段，测量每个点上的方向变化，并对这些变化的分布计算 Shannon 熵。直线的熵为零；随机游走的熵最大；人类移动介于两者之间，把意图与不自主的变异结合在一起。在一个会话中，许多移动都呈现低熵，是一个强烈的机器人信号，即使单个移动看起来是貌似合理地弯曲的。

### Pydoll 如何拟人化鼠标

在 `humanize=True` 时，Pydoll 生成的移动会回应上面每一个破绽。路径遵循一条控制点随机化的三次 Bezier 曲线，因此它会弯曲而不是走直线。沿路径的速度遵循最小急动度曲线（`10t^3 - 15t^4 + 6t^5`），给出 Fitts's Law 所预测的钟形曲线，而持续时间正是根据 Fitts's Law 本身计算得出的。生理性震颤被作为与速度成反比缩放的位置噪声加入（当光标缓慢移动时更明显，与真实生理相符），过冲以设定的概率发生并随后修正，偶尔的微停顿模拟短暂的犹豫。

```python
await element.click(humanize=True)
await tab.mouse.click(500, 300, humanize=True)   # 坐标形式
```

时序模型可以通过赋值给 `tab.mouse.timing` 的 `MouseTimingConfig` 进行配置。实用指南请参见 [Human-like interactions](../../stealth/human-like-interactions.md)。

!!! note "它没有建模的部分"
    Pydoll 的鼠标路径是单条 Bezier 曲线段；它不会把很长的移动拆分成多个子移动。对于典型的网页交互（大约 500 像素以内）这已经够了。全屏对角线穿越才是子移动会起作用的场景。

## 按键动态

按键动态分析的是键盘输入的时序。这个想法很古老：1850 年代的电报操作员通过彼此的莫尔斯"手法"（一种特征性的时序模式）来相互识别。现代系统通过 `keydown` 和 `keyup` 事件以毫秒级精度测量同样的东西。

### 时序特征

两个基本测量量是驻留时间（dwell time，从一个键的 `keydown` 到 `keyup`，通常为 50 到 200ms）和飞行时间（flight time，从松开一个键到按下下一个键，通常为 80 到 400ms）。连续键对的驻留和飞行是一个双字母组延迟（digraph latency），它并不均匀，因为打字是一种运动技能，常见序列存在于程序性记忆中：

- **双手交替。** 用交替的双手打出的二连字（bigram，比如 QWERTY 上的 "th"）比同一只手的（比如 "de"）更快，因为第二只手在第一只手还没打完时就开始移动了。
- **手指移动。** 主键行到主键行的转换最快；够到上排或下排的成本与距离成正比。
- **手指独立性。** 无名指和小指的组合比食指和中指慢，因为这些手指共享肌腱，独立活动的能力较弱。
- **频率。** 经常打的二连字（"th"、"er"、"in"）借助运动记忆跑得更快，与键盘布局无关。

### 检测信号

- **驻留时间为零或恒定。** 许多工具以近乎零的延迟派发 `keydown` 和 `keyup`；真实的按键有可测量、可变化的驻留时间。
- **飞行时间统一。** 按键之间固定的间隔会产生完美规律的时序，极易检测。人类的飞行时间随二连字、疲劳和负荷而变化。
- **没有打字错误。** 在 50 多个字符中完全没有退格是不寻常的；人类的出错率大约在 1% 到 5%。
- **超人的速度。** 持续打字超过 150 WPM 是除了顶尖打字员之外无人能及的，因此任何更快的都会被标记。

### Pydoll 如何拟人化打字

在 `type_text(humanize=True)` 时，按键延迟是从一个分布中抽取的，而不是固定间隔。标点会获得额外的延迟，模拟打字者在句子结构处的停顿；偶尔的思考停顿和更罕见的分心停顿模拟思考或被打断的瞬间。真实的打字错误以每字符大约 2% 的概率发生，分为五种错误类型，按现实世界的频率加权（相邻键、换位、双击、漏字符、漏空格），每个错误后都跟着一个自然的修正序列。

```python
await element.type_text('Hello, world!', humanize=True)
```

关于如何调整它，请参见 [Human-like interactions](../../stealth/human-like-interactions.md)。

!!! note "它没有建模的部分"
    Pydoll 使用的是可变的随机延迟，而不是感知二连字的时序，也不建模逐键的驻留时间或双手交替的差异。对于填表和搜索查询这已经够了。要躲避认证级别的按键生物特征，则需要一个定制的时序模型。

## 滚动行为

滚动 fingerprinting 分析的是用户如何在页面内容中移动。程序化的 `window.scrollTo()` 是一次瞬间的、离散的跳转，而人类的滚动（滚轮、触控板或触摸）是一连串带有惯性和减速的小增量事件。

鼠标滚轮以不规则的间隔产生离散的 `wheel` 事件，其 delta 一致（通常每格 100 或 120 像素）。触控板产生许多 delta 递减的小事件来模拟惯性。触摸类似，但初始 delta 更大，减速尾部更长。检测系统读取 delta 分布、事件间时序和减速曲线，寻找：

- **瞬间滚动。** 带有大数值的 `scrollTo`/`scrollBy` 在单帧内改变滚动位置，没有中间事件。
- **统一的 delta。** 恒定的 delta 值缺少真实滚动那 10% 到 30% 的变化。
- **没有减速。** 人类的滚动，尤其是在触控板上，会在手指抬起后继续移动，速度呈指数递减。突然停止的自动化没有尾部。
- **没有方向变化。** 人类会过度滚动然后修正，或停下来阅读。单方向恒速滚动是可疑的。

Pydoll 的拟人化滚动回应了这些：它遵循 Bezier 缓动曲线以实现自然的加速和减速，为 delta 添加逐帧抖动，插入偶尔的微停顿，有时过冲并修正，并把长距离拆分成多个"轻拂"手势而不是一次连续的移动。

```python
from pydoll.constants import ScrollPosition

await tab.scroll.by(ScrollPosition.DOWN, 800, humanize=True)
```

## 其他行为信号

除了鼠标、键盘和滚动之外，一些系统还会关注另外几个信号。

**焦点和可见性。** Page Visibility API（`document.visibilityState`）和焦点事件揭示了用户是否正在主动查看页面。一个真实的会话会有标签页切换、最小化和空闲时段；一个连续数小时保持焦点、没有一次 blur 的脚本是异常的。

**空闲模式。** 真实用户会停下来阅读和思考。一个每个动作都在前一个动作后 100 到 500ms 内跟进、没有更长间隔的会话，在统计上与人类浏览截然不同，后者 2 到 30 秒的空闲是正常的。

**事件序列完整性。** 一次真实的点击会按顺序产生 `pointerdown`、`mousedown`、`pointerup`、`mouseup`、`click`，并且前面有接近目标的移动事件。那些派发一个没有前置移动的裸 `click` 的工具是可检测的。Pydoll 通过 CDP 使用 Chrome 自己的输入模拟来派发输入，因此它生成的完整事件链与真实输入相同。

## 机器学习检测

现代反机器人系统（DataDome、Akamai Bot Manager、Cloudflare Bot Management、HUMAN Security）不依赖阈值规则。它们在数百万个真实会话和已知机器人会话上训练模型，学习一次性跨 50 多个特征把它们区分开：速度与曲率的联合分布、打字速度与错误率之间的相关性、滚动深度与阅读时间之间的关系、会话的整体节奏。一次通过了每一项单独检查、但特征之间存在微妙错误相关性的运行，仍然可能被标记。

实际的后果是，行为的真实感必须在各种交互类型之间保持一致，而不仅仅是一次一个看起来合理。Pydoll 的 `humanize=True` 在鼠标、键盘和滚动之间提供了一个一致的拟人化层，但更高层次的合理性仍然由你负责：在页面加载之间加入阅读延迟，改变多页面工作流的节奏，并包含自然的空闲时段。

## 相关内容

- [Network fingerprinting](network-fingerprinting.md)：协议层（TCP/IP、TLS、HTTP/2）。
- [Browser fingerprinting](browser-fingerprinting.md)：canvas、WebGL、字体和 navigator。
- [Human-like interactions](../../stealth/human-like-interactions.md)：`humanize=True` 的实用指南。

## 参考文献

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
