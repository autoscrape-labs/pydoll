# 类人交互

成功自动化与易被识破的机器人之间的关键区别之一在于交互的逼真程度。Pydoll提供精密工具，使您的自动化操作几乎与人类行为无异。

!!! 警告 "未来增强功能"
    Pydoll正持续提升其类人交互能力。未来版本将包含：
    
    - **可变输入速度**：键盘敲击间隔内置随机化，免除手动调整需求
    - **真实键盘序列**：自动模拟输入错误、退格修正及动态停顿，实现极致逼真
    - **自动随机点击偏移**：可选参数实现元素内点击位置随机化，免除手动偏移计算
    - **鼠标移动模拟**：贝塞尔曲线生成真实光标轨迹
    - **鼠标位移事件**：自然的加速与减速模式
    - **悬停行为**：悬停时的真实延迟与移动效果
    - **时间变异性**：随机延迟避免可预测模式
    
    这些功能通过CDP与JavaScript技术实现极致逼真效果。

## 拟人化交互为何重要

现代网站采用精密的机器人检测技术：

- **事件时间分析**：识别超高速或精准定时操作
- **鼠标轨迹追踪**：识别直线移动或瞬移行为
- **键盘输入模式**：识别无单个按键操作的即时文本插入
- **点击位置**：检测始终精准落在元素中心的点击
- **操作序列**：识别用户行为中的非人类模式

Pydoll通过提供模拟真实用户行为的交互方法，助您规避检测。

## 真实点击模拟

### 基础点击：模拟鼠标事件

`click()`方法模拟真实的鼠标按下与释放事件，区别于基于JavaScript的点击方式：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def realistic_clicking():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com’)
        
        button = await tab.find(id=“submit-button”)
        
        # 基础真实点击
        await button.click()
        
        # 点击包含：
        # - 鼠标移动至元素
        # - 鼠标按下事件
        # - 可配置按压时长
        # - 鼠标释放事件

asyncio.run(realistic_clicking())
```

### 带位置偏移的点击

真实用户很少精确点击元素中心。使用偏移量改变点击位置：

!!! info “当前状态：手动偏移计算”
    目前每次交互需手动计算并随机化点击偏移量。未来版本将提供可选参数，支持在元素边界内自动随机化点击位置。

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def click_with_offset():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com/form’)
        
        submit_button = await tab.find(tag_name=“button”, type="submit")
        
        # 点击位置略偏离中心（更自然）
        await submit_button.click(
            x_offset=5,   # 中心右偏5像素
            y_offset=-3   # 中心上偏3像素
        )
        
        # 当前方案：每次点击手动调整偏移量以模拟人类行为
        for item in await tab.find(class_name=“clickable-item”, find_all=True):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            await item.click(x_offset=offset_x, y_offset=offset_y)
            await asyncio.sleep(random.uniform(0.5, 2.0))

asyncio.run(click_with_offset())
```

可调点击按压时长

通过调整鼠标按键按压时长模拟不同点击方式：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def variable_hold_time():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com’)
        
        button = await tab.find(class_name=“action-button”)
        
        # 快速点击（默认0.1秒）
        await button.click(hold_time=0.05)
        
        # 正常点击
        await button.click(hold_time=0.1)
        
        # 更慢、更刻意点击
        await button.click(hold_time=0.2)
        
        # 模拟用户犹豫
        await asyncio.sleep(0.8)
        await button.click(hold_time=0.15)

asyncio.run(variable_hold_time())
```

### 何时使用click()与click_using_js()

理解两者差异对规避检测至关重要：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def click_methods_comparison():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com’)
        
        button = await tab.find(id=“interactive-button”)
        
        # 方法1：click() - 模拟真实鼠标事件
        # ✅ 触发全部鼠标事件（按下、松开、点击）
        # ✅ 保持元素定位
        # ✅ 更逼真且更难被检测
        # ❌ 需元素可见且在视口内
        await button.click()
        
        # 方法二：click_using_js() - 使用 JavaScript 的 click()
        # ✅ 可作用于隐藏元素
        # ✅ 执行速度更快
        # ✅ 绕过视觉覆盖层
        # ❌ 可能被识别为自动化操作
        # ❌ 无法触发与真实用户相同的事件序列
        await button.click_using_js()

asyncio.run(click_methods_comparison())
```

!!! 提示 “最佳实践：优先使用鼠标事件”
    用户交互场景请使用`click()`以保持真实感。仅在后端操作、隐藏元素或追求速度且无需规避检测时使用`click_using_js()`。

## 逼真文本输入

### 带间隔的自然输入

`type_text()`方法通过发送单个按键模拟人工输入。`interval`参数会在每次按键间添加**固定延迟**。

!!! info “当前状态：需手动随机化”
    当前`interval`参数对所有字符采用**恒定延迟**。为实现最高逼真度，需手动随机化输入速度（如下文高级示例所示）。未来版本将内置随机化功能实现自动可变输入速度。

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def natural_typing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com/login’)
        
        username_field = await tab.find(id=“username”)
        password_field = await tab.find(id=“password”)
        
        # 固定间隔输入（当前实现）
        # 人类平均输入速度：每字符0.1-0.3秒
        await username_field.type_text(“john.doe@example.com”, interval=0.15)
        
        # 复杂密码采用慢速输入
        await password_field.type_text(“MyC0mpl3xP@ssw0rd!”, interval=0.12)

asyncio.run(natural_typing())
```

### 不可见字段的快速输入

对于无需真实模拟的字段（如隐藏字段或后端操作），使用`insert_text()`：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def fast_vs_realistic_input():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(‘https://example.com/form’)
        
        # 可见字段的真实输入
        username = await tab.find(id=“username”)
        await username.click()
        await username.type_text(“john_doe”, interval=0.12)
        
        # 隐藏/后台字段的快速插入
        hidden_field = await tab.find(id=“hidden-token”)
        await hidden_field.insert_text(“very-long-generated-token-12345678”)
        
        # 关键字段采用真实输入模拟
        comment = await tab.find(id=“comment-box”)
        await comment.click()
        await comment.type_text(“This looks like human input!”, interval=0.15)

asyncio.run(fast_vs_realistic_input())
```

!!! info “高级键盘控制”
    有关全面的键盘控制文档（包括特殊键、组合键、修饰键及完整键位参考表），请参阅**[键盘控制](keyboard-control.md)**。

## 逼真页面滚动

Pydoll提供专用滚动API，在继续执行前等待滚动完成，使您的自动化更加真实可靠。

### 基础方向滚动

使用`scroll.by()`方法精确控制页面任意方向的滚动：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def basic_scrolling():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/long-page')
        
        # 向下滚动500像素（平滑动画）
        await tab.scroll.by(ScrollPosition.DOWN, 500, smooth=True)
        
        # 向上滚动300像素
        await tab.scroll.by(ScrollPosition.UP, 300, smooth=True)
        
        # 向右滚动（适用于横向滚动页面）
        await tab.scroll.by(ScrollPosition.RIGHT, 200, smooth=True)
        
        # 向左滚动
        await tab.scroll.by(ScrollPosition.LEFT, 200, smooth=True)
        
        # 即时滚动（无动画）
        await tab.scroll.by(ScrollPosition.DOWN, 1000, smooth=False)

asyncio.run(basic_scrolling())
```

### 滚动至特定位置

快速导航至页面顶部或底部：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scroll_to_positions():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/article')
        
        # 阅读文章开头
        await asyncio.sleep(2.0)
        
        # 平滑滚动至底部
        await tab.scroll.to_bottom(smooth=True)
        
        # 在底部停顿
        await asyncio.sleep(1.5)
        
        # 返回顶部
        await tab.scroll.to_top(smooth=True)

asyncio.run(scroll_to_positions())
```

!!! tip "平滑 vs 即时"
    - **smooth=True**：使用浏览器平滑动画并等待`scrollend`事件
    - **smooth=False**：即时滚动，在逼真度非关键时实现最大速度

### 类人滚动模式

!!! info "未来增强：内置真实滚动"
    目前需手动实现随机滚动模式。未来版本将提供`realistic=True`参数，自动添加滚动距离、速度及停顿的自然变化，模拟人类阅读行为。

模拟自然阅读与导航行为：

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def human_like_scrolling():
    """模拟阅读文章时的自然滚动模式。"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/article')
        
        # 用户从顶部开始阅读
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # 阅读时逐步滚动
        for _ in range(random.randint(5, 8)):
            # 变化滚动距离（模拟阅读速度）
            scroll_distance = random.randint(300, 600)
            await tab.scroll.by(
                ScrollPosition.DOWN, 
                scroll_distance, 
                smooth=True
            )
            
            # 停顿"阅读"内容
            await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # 快速滚动查看末尾
        await tab.scroll.to_bottom(smooth=True)
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # 滚回顶部重读某处
        await tab.scroll.to_top(smooth=True)

asyncio.run(human_like_scrolling())
```

### 将元素滚动至可见区

使用`scroll_into_view()`确保元素在截取页面屏幕截图前可见：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scroll_for_screenshots():
    """截取页面屏幕截图前将元素滚动至可见区。"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/product')
        
        # 截取完整页面屏幕截图前滚动至价格部分
        pricing_section = await tab.find(id="pricing")
        await pricing_section.scroll_into_view()
        await tab.take_screenshot(path="page_with_pricing.png")
        
        # 截图前滚动至评论区
        reviews = await tab.find(class_name="reviews")
        await reviews.scroll_into_view()
        await tab.take_screenshot(path="page_with_reviews.png")
        
        # 滚动至页脚以捕获完整页面状态
        footer = await tab.find(tag_name="footer")
        await footer.scroll_into_view()
        await tab.take_screenshot(path="page_with_footer.png")
        
        # 注意：click()已自动滚动，因此无需：
        # await button.scroll_into_view()  # 多余！
        # await button.click()  # 此操作已将按钮滚动至可见区

asyncio.run(scroll_for_screenshots())
```

### 处理无限滚动内容

实现滚动模式加载延迟加载的内容：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def infinite_scroll_loading():
    """在无限滚动页面上加载内容。"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/feed')
        
        items_loaded = 0
        max_scrolls = 10
        
        for scroll_num in range(max_scrolls):
            # 滚动至底部触发加载
            await tab.scroll.to_bottom(smooth=True)
            
            # 等待内容加载
            await asyncio.sleep(random.uniform(2.0, 3.0))
            
            # 检查是否加载新项目
            items = await tab.find(class_name="feed-item", find_all=True)
            new_count = len(items)
            
            if new_count == items_loaded:
                print("无更多内容可加载")
                break
            
            items_loaded = new_count
            print(f"滚动 {scroll_num + 1}：已加载 {items_loaded} 项")
            
            # 小幅向上滚动（人类行为）
            if random.random() > 0.7:
                await tab.scroll.by(ScrollPosition.UP, 200, smooth=True)
                await asyncio.sleep(random.uniform(0.5, 1.0))

asyncio.run(infinite_scroll_loading())
```

!!! success "自动等待完成"
    不同于立即返回的`execute_script("window.scrollBy(...)")`，`scroll` API使用CDP的`awaitPromise`参数等待浏览器的`scrollend`事件。这确保后续操作仅在滚动完全完成后执行。

## 组合技术实现最高逼真度

### 完整表单填写示例

以下综合示例融合了所有类人交互技术。**这展示了当前手动实现最高逼真度的方案**——未来版本将自动化处理大部分随机化操作：


```python
import asyncio
import random
from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

async def human_like_form_filling():
    “”‘以最大真实感填写表单以规避检测’“”
    async with Chrome() as browser:
        tab = await browser.start()
        await 标签页.go_to(‘https://example.com/registration’)
        
        # 等待片刻（模拟用户阅读页面）
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # 以随机打字速度填写名字
        名字 = await 标签页.find(id=“first-name”)
        await first_name.click(
            x_offset=random.randint(-5, 5),
            y_offset=random.randint(-5, 5)
        )
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # 手动逐字符输入并随机延迟
        # （未来版本将实现自动化）
        name_text = “John”
        for char in name_text:
            await first_name.type_text(char, interval=0)
            await asyncio.sleep(random.uniform(0.08, 0.22))
        
        # 跳转至下一个字段
        await asyncio.sleep(random.uniform(0.3, 0.8))
        await first_name.press_keyboard_key(Key.TAB)
        
        # 填写姓氏
        await asyncio.sleep(random.uniform(0.2, 0.5))
        last_name = await tab.find(id=“last-name”)
        await last_name.type_text(“Doe”, interval=random.uniform(0.1, 0.18))
        
        # 跳转至邮箱字段
        await asyncio.sleep(random.uniform(0.4, 1.0))
        await last_name.press_keyboard_key(Key.TAB)
        
        # 填充邮箱时加入真实停顿
        await asyncio.sleep(random.uniform(0.2, 0.5))
        email = await tab.find(id=“email”)
        
        email_text = “john.doe@example.com”
        for i, char in enumerate(email_text):
            await email.type_text(char, interval=0)
            # 在@和.符号处延长停顿（自然）
            if char in [‘@’, ‘.’]:
                await asyncio.sleep(random.uniform(0.2, 0.4))
            else:
                await asyncio.sleep(random.uniform(0.08, 0.2))
        
        # 模拟用户检查输入内容
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # 带偏移量的条款同意复选框
        terms_checkbox = await tab.find(id=“accept-terms”)
        await terms_checkbox.click(
            x_offset=random.randint(-3, 3),
            y_offset=random.randint(-3, 3),
            hold_time=random.uniform(0.08, 0.15)
        )
        
        # 提交前暂停（用户审核表单）
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # 模拟真实参数点击提交按钮
        submit_button = await tab.find(tag_name=“button”, type="submit")
        await submit_button.click(
            x_offset=random.randint(-8, 8),
            y_offset=random.randint(-5, 5),
            hold_time=random.uniform(0.1, 0.2)
        )
        
        print(“表单已按人类行为提交”)

asyncio.run(human_like_form_filling())
```

## 规避检测的最佳实践

!!! 提示 “当前需手动随机化”
    以下最佳实践代表**Pydoll的当前状态**，您必须手动实现随机化。虽然这需要更多代码，但能让您精细控制行为。未来版本将自动实现这些模式，同时保持同等逼真度。

### 1. 始终添加随机延迟

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

# 错误示例：可预测的操作时序
await element1.click()
await element2.click()
await element3.click()

# 良好：可变时序（当前必需）
await element1.click()
await asyncio.sleep(random.uniform(0.5, 1.5))
await element2.click()
await asyncio.sleep(random.uniform(0.8, 2.0))
await element3.click()
```

### 2. 变化点击位置

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

# 错误示例：始终点击中心位置
for button in buttons:
    await button.click()

# 正确示例：随机变化点击位置（当前需手动设置）
for button in buttons:
    await button.click(
        x_offset=random.randint(-10, 10),
        y_offset=random.randint(-10, 10)
    )
```

### 3. 模拟自然用户行为

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def natural_user_simulation(tab):
    # 用户到达页面
    await tab.go_to(‘https://example.com’)
    
    # 用户阅读页面内容（1-3秒）
    await asyncio.sleep(random.uniform(1.0, 3.0))
    
    # 用户向下滚动查看更多内容
    await tab.scroll.by(ScrollPosition.DOWN, 300, smooth=True)
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # 用户找到并点击按钮
    button = await tab.find(class_name=“cta-button”)
    await button.click(
        x_offset=random.randint(-5, 5),
        y_offset=random.randint(-5, 5)
    )
    
    # 用户等待内容加载
    await asyncio.sleep(random.uniform(0.8, 1.5))
```

### 4. 组合多种技术

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def advanced_stealth_automation():
    “”‘组合多种技术实现最大隐蔽性’“”
    async with Chrome() as browser:
    tab = await browser.start()
        
        # 模拟人类等待页面加载
        await tab.go_to(‘https://example.com/sensitive-page’)
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # 模拟真实滚动（当前手动实现）
        # 未来版本将提供带惯性效果的专用滚动方法
        for _ in range(random.randint(2, 4)):
            scroll_amount = random.randint(200, 500)
            await tab.execute_script(f“window.scrollBy(0, {scroll_amount})”)
            await asyncio.sleep(random.uniform(0.8, 2.0))
        
        # 超时查找元素（模拟用户搜索）
        target = await tab.find(
            class_name="target-element",
            timeout=random.randint(3, 7)
        )
        
        # 模拟真实点击参数
        await target.click(
            x_offset=random.randint(-12, 12),
            y_offset=random.randint(-8, 8),
            hold_time=random.uniform(0.09, 0.18)
        )
        
        # 人类反应时间
        await asyncio.sleep(random.uniform(0.5, 1.2))

asyncio.run(advanced_stealth_automation())
```

## 性能与逼真度权衡

有时需要在速度与逼真度之间找到平衡：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def balanced_automation():
    """根据场景选择适当的逼真度级别"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/scraping-target')
        
        # 阶段1：初始交互（高逼真度）
        # 此时检测系统最为活跃
        login_button = await tab.find(text="Login")
        await asyncio.sleep(random.uniform(1.0, 2.0))
        await login_button.click(
            x_offset=random.randint(-5, 5),
            y_offset=random.randint(-5, 5)
        )
        
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        username = await tab.find(id="username")
        await username.type_text("user@example.com", interval=0.12)
        
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        password = await tab.find(id="password")
        await password.type_text("password123", interval=0.10)
        
        submit = await tab.find(type="submit")
        await asyncio.sleep(random.uniform(0.8, 1.5))
        await submit.click()
        
        # 阶段2：已认证数据提取（低逼真度，高速度）
        # 成功认证后受审查较少
        await asyncio.sleep(2)
        
        # 快速浏览页面
        items = await tab.find(class_name="data-item", find_all=True)
        
        for item in items:
            # 无偏移量快速点击
            await item.click_using_js()
            await asyncio.sleep(0.3)  # 最小延迟
            
            # 提取数据
            title = await tab.find(class_name="title")
            data = await title.text
            
            # 快速导航
            await tab.execute_script("window.history.back()")
            await asyncio.sleep(0.5)

asyncio.run(balanced_automation())
```

## 监控与调整

测试自动化操作的逼真度：

```python
import asyncio
import random
import time
from pydoll.browser.chromium import Chrome

async def test_interaction_timing():
    """记录时序以确保逼真的行为模式"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/test-page')
        
        # 测量并记录交互时序
        elements = await tab.find(class_name="clickable", find_all=True)
        
        timings = []
        last_time = time.time()
        
        for i, element in enumerate(elements):
            await element.click(
                x_offset=random.randint(-8, 8),
                y_offset=random.randint(-8, 8)
            )
            
            current_time = time.time()
            elapsed = current_time - last_time
            timings.append(elapsed)
            
            print(f"点击 {i+1}: 距上次操作 {elapsed:.3f}秒")
            last_time = current_time
            
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # 分析时序分布
        avg_time = sum(timings) / len(timings)
        print(f"\n操作间平均时间: {avg_time:.3f}秒")
        print(f"最小值: {min(timings):.3f}秒, 最大值: {max(timings):.3f}秒")
        
        # 良好：可变时序且平均时间逼真（1-2秒）
        # 不佳：恒定时序或速度不真实（<0.1秒）

asyncio.run(test_interaction_timing())
```

## 了解更多

有关元素交互方法的更多信息：

- **[元素查找](../element-finding.md)**：定位需要交互的元素
- **[WebElement域](../../deep-dive/architecture/webelement-domain.md)**：深入了解WebElement功能
- **[文件操作](file-operations.md)**：上传文件和处理下载

掌握类人交互技术，您的自动化将更可靠、更难检测，并更贴近真实用户行为。
