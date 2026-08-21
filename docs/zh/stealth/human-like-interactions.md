# 拟人化交互

检测系统关注的是你*如何*行动，而不只是你点击了什么。在元素正中心的瞬间点击、以完全固定的速率按键、光标沿直线跳动，这些都是行为破绽。传入 `humanize=True`，Pydoll 就会以真人的时序和动作来执行同样的操作：变化的打字节奏、曲线的光标路径，以及基于物理的滚动。

拟人化是按交互逐个选择启用的，所以你只在行为被监视的地方多花那几毫秒，而且它只是 stealth 的一层，并非全部。它塑造的是行为；它不会改变你的 [身份或网络 fingerprint](index.md)。

## 像人一样打字

给 `type_text()` 传入 `humanize=True`，Pydoll 就会改变按键之间的延迟，并偶尔加入被纠正的拼写错误（约 2%）。不加它时，打字会以固定的每字符 50ms 运行。

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('tester', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('secret-passphrase', humanize=True)

asyncio.run(main())
```

当某个字段的内容不需要看起来像是打出来的（比如隐藏的 token，或没人关注的值），`insert_text()` 会一次性设置整个字符串，不产生逐键事件。

> 🎞️ **交互式视觉占位** — 同一个单词的两条按键时间线：固定的 50ms 节奏，对比带有变化间隔和一次被纠正拼写错误的拟人化节奏。

## 像人一样点击

在 `click()` 上使用 `humanize=True`，会在按下之前让光标以拟人的时序沿曲线路径移动到元素。你还可以用 `x_offset`/`y_offset` 把点击位置从正中心偏移一些，并用 `hold_time` 改变按键被按住的时长。

```python
button = await tab.find(id='submit')

# 曲线接近，拟人的按压时序
await button.click(humanize=True)

# 落点略偏离中心，按住稍久一点
await button.click(x_offset=6, y_offset=-3, hold_time=0.12)
```

`click()` 会派发真实的鼠标事件（move、down、up、click），这正是页面从真实用户那里看到的。而 `click_using_js()` 调用的是元素的 JavaScript `click()`：它能作用于隐藏或被遮挡的元素，速度也更快，但它不触发任何鼠标事件，所以在行为被监视的地方优先使用 `click()`，把 `click_using_js()` 留给隐藏控件或对速度要求高的步骤。

## 像人一样移动鼠标

如果面对的是原始坐标而不是元素，可以用 `humanize=True` 驱动 `tab.mouse`。光标会沿贝塞尔曲线路径移动，时长遵循费茨定律（目标越远、越小，用时越长），带有钟形的速度曲线、轻微的抖动，以及偶尔会冲过头再修正回来的过冲。

```python
await tab.mouse.move(480, 260, humanize=True)
await tab.mouse.click(480, 260, humanize=True)
await tab.mouse.drag(120, 200, 480, 360, humanize=True)
```

完整的坐标 API 参见 [鼠标](../guides/mouse.md)，按键和快捷键参见 [键盘](../guides/keyboard.md)。

## 像人一样滚动

真实用户不会在页面上瞬移。`tab.scroll` 提供三种模式；`humanize=True` 会运行一个带有动量、摩擦、微停顿和过冲的物理模型，并在返回之前等待浏览器的 `scrollend` 事件，所以下一个操作只会在滚动结束之后才运行。

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

        await tab.scroll.by(ScrollPosition.DOWN, 600, humanize=True)
        await tab.scroll.to_bottom(humanize=True)
        await tab.scroll.to_top(humanize=True)

asyncio.run(main())
```

不加 `humanize` 时，`smooth=True`（默认值）会做一个可预测的 CSS 动画，而 `smooth=False` 则会瞬间跳转。若要在截图前把某个元素滚动到可见区域，请使用 `await element.scroll_into_view()`。

## 调整时序

拟人化的鼠标物理来自 `tab.mouse.timing` 上的一个 `MouseTimingConfig`：费茨定律常量、路径曲率、抖动、过冲和时长上限。只覆盖你在意的那些字段。[鼠标指南](../guides/mouse.md#tune-the-timing) 展示了这个配置，并对每个字段做了说明。

## 拟人化没有覆盖的部分

拟人化行为只应对一个检测层。无论你的光标看起来多么自然，网站仍然可以基于你的浏览器身份（User-Agent、WebGL、canvas）或网络路径（IP 信誉、TLS）来标记你。请把本页当作行为这一块，并与其余部分搭配使用：

!!! note "众多层中的一层"
    拟人化行为本身并不能让自动化无法被检测。请把它与一致的身份和干净的 IP 搭配起来。关于各层如何配合，参见 [Stealth 总览](index.md)。

## 下一步

- [Captcha 绕过](captcha-bypass.md)：在 Cloudflare Turnstile 出现时处理它。
- [Stealth 总览](index.md)：从行为到身份再到网络的完整图景。
- [键盘](../guides/keyboard.md) 和 [鼠标](../guides/mouse.md)：完整的输入 API。
- [行为指纹识别](../deep-dive/fingerprinting/behavioral-fingerprinting.md)：鼠标、键盘和时序是如何被分析的。
