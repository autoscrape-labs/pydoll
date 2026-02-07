<p align="center">
    <img src="https://github.com/user-attachments/assets/219f2dbc-37ed-4aea-a289-ba39cdbb335d" alt="Pydoll Logo" /> <br>
</p>
<h1 align="center">Pydoll: Automate the Web, Naturally</h1>

<p align="center">
    <a href="https://github.com/autoscrape-labs/pydoll/stargazers"><img src="https://img.shields.io/github/stars/autoscrape-labs/pydoll?style=social"></a>
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll" >
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/>
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
    <img src="https://img.shields.io/badge/python-%3E%3D3.10-blue" alt="Python >= 3.10">
    <a href="https://deepwiki.com/autoscrape-labs/pydoll"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>


<p align="center">
  📖 <a href="https://autoscrape-labs.github.io/pydoll/">文档</a> •
  🚀 <a href="#-getting-started">快速上手</a> •
  ⚡ <a href="#-advanced-features">高级特性</a> •
  🤝 <a href="#-contributing">贡献</a> •
  💖 <a href="#-support-my-work">赞助我</a>
</p>

- [English](README.md)

设想以下场景：你需要实现浏览器任务的自动化操作——无论是测试Web应用程序、从网站采集数据，还是批量处理重复性流程。传统方法往往需要配置外部驱动程序、进行复杂的系统设置，还可能面临诸多兼容性问题。

**Pydoll的诞生就是解决这些问题!!!**

Pydoll 采用全新设计理念，从零构建，直接对接 Chrome DevTools Protocol（CDP），无需依赖外部驱动。 这种精简的实现方式，结合高度拟真的点击、导航及元素交互机制，使其行为与真实用户几乎毫无区别。

我们坚信，真正强大的自动化工具，不应让用户困于繁琐的配置学习，也不该让用户疲于应对反爬系统的风控。使用Pydoll，你只需专注核心业务逻辑——让自动化回归本质，而非纠缠于底层技术细节或防护机制。

<div>
  <h4>做一个好人，给我们一个星星 ⭐</h4> 
    没有星星，就没有Bug修复。开玩笑的（也许）
</div>

## 🌟 Pydoll 的核心优势

- **零 WebDriver 依赖**：彻底告别驱动兼容性烦恼
- **类人交互引擎**：能够通过行为验证码如 reCAPTCHA v3 或 Turnstile，取决于 IP 声誉和交互模式
- **异步高性能**：支持高速自动化与多任务并行处理
- **拟真交互体验**：完美复刻真实用户行为模式
- **极简部署**：安装即用，开箱即自动化

## 最新功能

### 类人页面滚动 —— 像真实用户一样滚动！

现在你可以控制页面滚动，支持平滑动画并自动等待完成：

```python
from pydoll.constants import ScrollPosition

# 带平滑动画向下滚动（等待完成）
await tab.scroll.by(ScrollPosition.DOWN, 500, smooth=True)

# 导航至特定位置
await tab.scroll.to_bottom(smooth=True)
await tab.scroll.to_top(smooth=True)

# 需要速度时的即时滚动
await tab.scroll.by(ScrollPosition.UP, 300, smooth=False)
```

不同于立即返回的 `execute_script("window.scrollBy(...)")`，滚动API使用CDP的`awaitPromise`等待浏览器的`scrollend`事件，确保后续操作仅在滚动完全完成后执行。非常适合截取屏幕截图、加载延迟内容或创建真实的阅读模式。

### 键盘 API —— 完全控制键盘输入

全新的 `KeyboardAPI` 为页面级别的所有键盘交互提供了简洁、集中的接口：

```python
from pydoll.constants import Key

# 按单个键
await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)

# 使用快捷键/组合键（最多3个键）
await tab.keyboard.hotkey(Key.CONTROL, Key.A)  # 全选（有效！）
await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # 复制（有效！）
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWRIGHT)  # 向右选择单词

# 复杂序列的手动控制
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)  # 按住 Shift 选择文本
await tab.keyboard.up(Key.SHIFT)
```

**主要改进：**
- **集中化**：所有键盘操作通过 `tab.keyboard` 访问
- **智能修饰键检测**：快捷键自动检测并应用修饰键（Ctrl、Shift、Alt、Meta）
- **完整按键支持**：26个字母（A-Z）、10个数字（0-9）、所有功能键、数字键盘和特殊键
- **页面级快捷键**：适用于 Ctrl+C、Ctrl+V、Ctrl+A 等（由于 CDP 限制，浏览器 UI 快捷键不起作用）

> **⚠️ CDP 限制：** 浏览器 UI 快捷键（如 Ctrl+T 打开新标签，F12 打开开发者工具）通过 CDP 无法使用。请改用 Pydoll 的方法：`await browser.new_tab()`、`await tab.close()`。

### Retry 装饰器：生产级错误恢复

使用 `@retry` 装饰器将脆弱的脚本转变为强大的生产级爬虫。通过指数退避和自定义恢复策略，自动从网络故障、超时和临时错误中恢复：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, NetworkError

class ProductScraper:
    def __init__(self):
        self.tab = None
        self.retry_count = 0
    
    # 在每次重试前执行的恢复回调
    async def recover_from_failure(self):
        self.retry_count += 1
        print(f"尝试 {self.retry_count} 失败。恢复中...")
        
        # 刷新页面并恢复状态
        if self.tab:
            await self.tab.refresh()
            await asyncio.sleep(2)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, NetworkError],
        on_retry=recover_from_failure,  # 执行恢复逻辑
        delay=2.0,
        exponential_backoff=True
    )
    async def scrape_product(self, url: str):
        if not self.tab:
            browser = Chrome()
            self.tab = await browser.start()
        
        await self.tab.go_to(url)
        title = await self.tab.find(class_name='product-title', timeout=5)
        return await title.text
```

**强大功能：**
- **智能重试逻辑**：仅对您定义的特定异常重试
- **指数退避**：逐步增加等待时间（1秒 → 2秒 → 4秒 → 8秒）
- **恢复回调**：在重试之间执行自定义逻辑（刷新页面、切换代理、重启浏览器）
- **生产验证**：自信地处理真实世界爬虫的混乱情况

非常适合处理速率限制、网络不稳定、动态内容加载和验证码检测。将不可靠的爬虫转变为防弹自动化。

[**📖 完整文档**](https://pydoll.tech/docs/zh/features/advanced/decorators/)

### 通过 WebSocket 进行远程连接 —— 随时随地控制浏览器！

现在你可以使用浏览器的 WebSocket 地址直接连接到已运行的实例，并立即使用完整的 Pydoll API：

```python
from pydoll.browser.chromium import Chrome

chrome = Chrome()
tab = await chrome.connect('ws://YOUR_HOST:9222/devtools/browser/XXXX')

# 直接开干：导航、元素自动化、请求、事件…
await tab.go_to('https://example.com')
title = await tab.execute_script('return document.title')
print(title)
```

这让你可以轻松对接远程/CI 浏览器、容器或共享调试目标——无需本地启动，只需指向 WS 端点即可自动化。

### 像专业人士一样漫游 DOM：get_children_elements() 与 get_siblings_elements()

两个让复杂布局遍历更优雅的小助手：

```python
# 获取容器的直接子元素
container = await tab.find(id='cards')
cards = await container.get_children_elements(max_depth=1)

# 想更深入？这将返回子元素的子元素（以此类推）
elements = await container.get_children_elements(max_depth=2) 

# 在横向列表中无痛遍历兄弟元素
active = await tab.find(class_name='item--active')
siblings = await active.get_siblings_elements()

print(len(cards), len(siblings))
```

用更少样板代码表达更多意图，特别适合动态网格、列表与菜单的场景，让抓取/自动化逻辑更清晰、更可读。

### WebElement：状态等待与新的公共 API

- 新增 `wait_until(...)` 用于等待元素状态，使用更简单：

```python
# 等待元素变为可见，直到超时
await element.wait_until(is_visible=True, timeout=5)

# 等待元素变为可交互（可见、位于顶层并可接收事件）
await element.wait_until(is_interactable=True, timeout=10)
```

- 以下 `WebElement` 方法现已公开：
  - `is_visible()`
    - 判断元素是否具有可见区域、未被 CSS 隐藏，并在需要时滚动进入视口。适用于交互前的快速校验。
  - `is_interactable()`
    - “可点击”状态：综合可见性、启用状态与指针事件命中等条件，适合构建更稳健的交互流程。
  - `is_on_top()`
    - 检查元素在点击位置是否为顶部命中目标，避免被覆盖导致点击失效。
  - `execute_script(script: str, return_by_value: bool = False)`
    - 在元素上下文中执行 JavaScript（this 指向该元素），便于细粒度调整与快速检查。

```python
# 使用 JS 高亮元素
await element.execute_script("this.style.outline='2px solid #22d3ee'")

# 校验状态
visible = await element.is_visible()
interactable = await element.is_interactable()
on_top = await element.is_on_top()
```

以上新增能力能显著简化“等待+验证”场景，降低自动化过程中的不稳定性，使用例更可预测。

### 浏览器上下文 HTTP 请求 - 混合自动化的游戏规则改变者！
你是否曾经希望能够发出自动继承浏览器所有会话状态的 HTTP 请求？**现在你可以了！**<br>
`tab.request` 属性为你提供了一个美观的 `requests` 风格接口，可在浏览器的 JavaScript 上下文中直接执行 HTTP 调用。这意味着每个请求都会自动获得 cookies、身份验证标头、CORS 策略和会话状态，就像浏览器本身发出请求一样。

**混合自动化的完美选择：**
```python
# 使用 PyDoll 正常导航到网站并登录
await tab.go_to('https://example.com/login')
await (await tab.find(id='username')).type_text('user@example.com')
await (await tab.find(id='password')).type_text('password')
await (await tab.find(id='login-btn')).click()

# 现在发出继承已登录会话的 API 调用！
response = await tab.request.get('https://example.com/api/user/profile')
user_data = response.json()

# 在保持身份验证的同时 POST 数据
response = await tab.request.post(
    'https://example.com/api/settings', 
    json={'theme': 'dark', 'notifications': True}
)

# 以不同格式访问响应内容
raw_data = response.content
text_data = response.text
json_data = response.json()

# 检查设置的 cookies
for cookie in response.cookies:
    print(f"Cookie: {cookie['name']} = {cookie['value']}")

# 向你的请求添加自定义标头
headers = [
    {'name': 'X-Custom-Header', 'value': 'my-value'},
    {'name': 'X-API-Version', 'value': '2.0'}
]

await tab.request.get('https://api.example.com/data', headers=headers)

```

**为什么这很棒：**
- **无需会话切换** - 请求自动继承浏览器 cookies
- **CORS 无缝工作** - 请求遵循浏览器安全策略  
- **现代 SPA 的完美选择** - 无缝混合 UI 自动化与 API 调用
- **身份验证变得简单** - 通过 UI 登录一次，然后调用 API
- **混合工作流** - 为每个步骤使用最佳工具（UI 或 API）

这为需要浏览器交互和 API 效率的自动化场景开启了令人难以置信的可能性！

### 使用自定义首选项完全控制浏览器！(感谢 [@LucasAlvws](https://github.com/LucasAlvws))
想要完全自定义 Chrome 的行为？**现在你可以控制一切！**<br>
新的 `browser_preferences` 系统让你可以访问数百个之前无法通过编程方式更改的内部 Chrome 设置。我们说的是远超命令行标志的深度浏览器自定义！

**可能性是无限的：**
```python
options = ChromiumOptions()

# 创建完美的自动化环境
options.browser_preferences = {
    'download': {
        'default_directory': '/tmp/downloads',
        'prompt_for_download': False,
        'directory_upgrade': True,
        'extensions_to_open': ''  # 不自动打开任何下载
    },
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,        # 阻止所有通知
            'geolocation': 2,         # 阻止位置请求
            'media_stream_camera': 2, # 阻止摄像头访问
            'media_stream_mic': 2,    # 阻止麦克风访问
            'popups': 1               # 允许弹窗（对自动化有用）
        },
        'password_manager_enabled': False,  # 禁用密码提示
        'exit_type': 'Normal'              # 始终正常退出
    },
    'intl': {
        'accept_languages': 'zh-CN,zh,en-US,en',
        'charset_default': 'UTF-8'
    },
    'browser': {
        'check_default_browser': False,    # 不询问默认浏览器
        'show_update_promotion_infobar': False
    }
}

# 或使用便捷的辅助方法
options.set_default_download_directory('/tmp/downloads')
options.set_accept_languages('zh-CN,zh,en-US,en')  
options.prompt_for_download = False
```

**实际应用的强大示例：**
- **静默下载** - 无提示、无对话框，只有自动化下载
- **阻止所有干扰** - 通知、弹窗、摄像头请求，应有尽有
- **CI/CD 的完美选择** - 禁用更新检查、默认浏览器提示、崩溃报告
- **多区域测试** - 即时更改语言、时区和区域设置
- **安全加固** - 锁定权限并禁用不必要的功能
- **高级指纹控制** - 修改浏览器安装日期、参与历史和行为模式

**用于隐蔽自动化的指纹自定义：**
```python
import time

# 模拟一个已经存在几个月的浏览器
fake_engagement_time = int(time.time()) - (7 * 24 * 60 * 60)  # 7天前

options.browser_preferences = {
    'settings': {
        'touchpad': {
            'natural_scroll': True,
        }
    },
    'profile': {
        'last_engagement_time': fake_engagement_time,
        'exit_type': 'Normal',
        'exited_cleanly': True
    },
    'newtab_page_location_override': 'https://www.google.com',
    'session': {
        'restore_on_startup': 1,  # 恢复上次会话
        'startup_urls': ['https://www.google.com']
    }
}
```

这种控制级别以前只有 Chrome 扩展开发者才能使用 - 现在它在你的自动化工具包中！

查看[文档](https://pydoll.tech/docs/zh/features/#custom-browser-preferences/)了解更多详情。

### 新的 `get_parent_element()` 方法
检索任何 WebElement 的父元素，使导航 DOM 结构更加容易：
```python
element = await tab.find(id='button')
parent = await element.get_parent_element()
```

### 新的 start_timeout 选项 (感谢 [@j0j1j2](https://github.com/j0j1j2))
添加到 ChromiumOptions 来控制浏览器启动可以花费多长时间。在较慢的机器或 CI 环境中很有用。

```python
options = ChromiumOptions()
options.start_timeout = 20  # 等待 20 秒
```

### 新的 expect_download() 上下文管理器 —— 稳健、优雅的文件下载！
还在为不稳定的下载流程、丢失的文件或混乱的事件监听而头疼吗？`tab.expect_download()` 来了：一种可靠、简洁的下载方式。

- 自动配置浏览器下载行为
- 支持自定义下载目录或临时目录（自动清理！）
- 内置超时等待，防止任务卡住
- 提供便捷句柄：读取字节/BASE64，获取 `file_path`

一个“开箱即用”的小示例：

```python
import asyncio
from pathlib import Path
from pydoll.browser import Chrome

async def download_report():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/reports')

        target_dir = Path('/tmp/my-downloads')
        async with tab.expect_download(keep_file_at=target_dir, timeout=10) as dl:
            # 触发页面上的下载（按钮/链接等）
            await (await tab.find(text='Download latest report')).click()

            # 等待完成并读取内容
            data = await dl.read_bytes()
            print(f"已下载 {len(data)} 字节，保存至: {dl.file_path}")

asyncio.run(download_report())
```

想要“零成本清理”？不传 `keep_file_at` 即可——我们会创建临时目录，并在上下文退出后自动清理。对测试场景非常友好。

## 📦 安装

```bash
pip install pydoll-python
```

就这么简单！安装即用，马上开始自动化

## 🚀 快速上手

### 你的第一个自动化任务

让我们从一个实际例子开始：一个自动执行谷歌搜索并点击第一个结果的自动化流程。通过这个示例，你可以了解该库的工作原理，以及如何开始将日常任务自动化。

```python
import asyncio

from pydoll.browser import Chrome
from pydoll.constants import Key

async def google_search(query: str):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.insert_text(query)
        await tab.keyboard.press(Key.ENTER)
        await (await tab.find(
            tag_name='h3',
            text='autoscrape-labs/pydoll',
            timeout=10,
        )).click()
        await tab.find(id='repository-container-header', timeout=10)

asyncio.run(google_search('pydoll site:github.com'))
```

无需任何配置，只需一个简单脚本，我们就能完成一次完整的谷歌搜索！
好了，现在让我们看看如何从网页中提取数据，依然沿用之前的示例。

假设在以下代码中，我们已经进入了 Pydoll 项目页面。我们需要提取以下信息：

- 项目描述
- 星标数量
- Fork 数量
- Issue 数量
- Pull Request 数量
如果想要获取项目描述，我们将使用 XPath 查询。你可以查阅相关文档，学习如何构建自己的查询语句。

```python
description = await (await tab.query(
    '//h2[contains(text(), "About")]/following-sibling::p',
    timeout=10,
)).text
```

下面让我们来理解这条查询语句的作用：

1. `//h2[contains(text(), "About")]` - 选择第一个包含"About"的 `<h2>` 标签
2. `/following-sibling::p` - 选择第一个在`<h2>` 标签之后的`<p>`标签

然后你可以获取到剩下的数据：

```python
number_of_stars = await (await tab.find(
    id='repo-stars-counter-star'
)).text

number_of_forks = await (await tab.find(
    id='repo-network-counter'
)).text
number_of_issues = await (await tab.find(
    id='issues-repo-tab-count',
)).text
number_of_pull_requests = await (await tab.find(
    id='pull-requests-repo-tab-count',
)).text

data = {
    'description': description,
    'number_of_stars': number_of_stars,
    'number_of_forks': number_of_forks,
    'number_of_issues': number_of_issues,
    'number_of_pull_requests': number_of_pull_requests,
}
print(data)

```

下图展示了本次自动化任务的执行速度与结果。
（为演示需要，浏览器界面未显示。）

![google_seach](./docs/images/google-search-example.gif)


短短5秒内，我们就成功提取了所需数据！  
这就是使用Pydoll进行自动化所能达到的速度。

### 更多复杂的例子

接下来我们来看一个你可能经常遇到的场景：类似Cloudflare的验证码防护。  
Pydoll提供了相应的处理方法，但需要说明的是，正如前文所述，其有效性会受到多种因素影响。  
下面的代码展示了一个完整的Cloudflare验证码处理示例。

```python
import asyncio

from pydoll.browser import Chrome
from pydoll.constants import By

async def cloudflare_example():
    async with Chrome() as browser:
        tab = await browser.start()
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://2captcha.com/demo/cloudflare-turnstile')
        print('Captcha handled, continuing...')
        await asyncio.sleep(5)  # just to see the result :)

asyncio.run(cloudflare_example())

```

执行结果如下：

![cloudflare_example](./docs/images/cloudflare-example.gif)


仅需数行代码，我们就成功攻克了最棘手的验证码防护之一。
而这仅仅是Pydoll所提供的众多强大功能之一。但这还远不是全部！


### 自定义配置

有时我们需要对浏览器进行更精细的控制。Pydoll提供了灵活的配置方式来实现这一点。下面我们来看具体示例：


```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions as Options

async def custom_automation():
    # Configure browser options
    options = Options()
    options.add_argument('--proxy-server=username:password@ip:port')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = '/path/to/your/browser'
    options.start_timeout = 20

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        # Your automation code here
        await tab.go_to('https://example.com')
        # The browser is now using your custom settings

asyncio.run(custom_automation())
```

本示例中，我们配置浏览器使用代理服务器，并设置窗口分辨率为1920x1080。此外，还指定了Chrome二进制文件的自定义路径——适用于您的安装位置与常规默认路径不同的情况。

## ⚡ 高级功能

Pydoll提供了一系列高级特性满足高端玩家的需求。


### 高级元素定位

我们提供多种页面元素定位方式。无论您偏好那种方法，都能找到适合您的解决方案：

```python
import asyncio
from pydoll.browser import Chrome

async def element_finding_examples():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

        # Find by attributes (most intuitive)
        submit_btn = await tab.find(
            tag_name='button',
            class_name='btn-primary',
            text='Submit'
        )
        # Find by ID
        username_field = await tab.find(id='username')
        # Find multiple elements
        all_links = await tab.find(tag_name='a', find_all=True)
        # CSS selectors and XPath
        nav_menu = await tab.query('nav.main-menu')
        specific_item = await tab.query('//div[@data-testid="item-123"]')
        # With timeout and error handling
        delayed_element = await tab.find(
            class_name='dynamic-content',
            timeout=10,
            raise_exc=False  # Returns None if not found
        )
        # Advanced: Custom attributes
        custom_element = await tab.find(
            data_testid='submit-button',
            aria_label='Submit form'
        )

asyncio.run(element_finding_examples())
```

find 方法更为友好。我们可以通过常见属性（如 id、tag_name、class_name 等）进行元素查找，甚至支持自定义属性（例如 data-testid）。

如果这些基础方式仍不能满足需求，还可使用 query 方法，通过 CSS 选择器、XPath 查询语句等多种方式进行元素定位。Pydoll 会自动识别当前使用的查询类型。

### 并发自动化

Pydoll 的一大优势在于其基于异步实现的多任务并行处理能力。我们可以同时自动化操作多个浏览器标签页！下面来看具体示例：

```python
import asyncio
from pydoll.browser import Chrome

async def scrape_page(url, tab):
    await tab.go_to(url)
    title = await tab.execute_script('return document.title')
    links = await tab.find(tag_name='a', find_all=True)
    return {
        'url': url,
        'title': title,
        'link_count': len(links)
    }

async def concurrent_scraping():
    browser = Chrome()
    tab_google = await browser.start()
    tab_duckduckgo = await browser.new_tab()
    tasks = [
        scrape_page('https://google.com/', tab_google),
        scrape_page('https://duckduckgo.com/', tab_duckduckgo)
    ]
    results = await asyncio.gather(*tasks)
    print(results)
    await browser.stop()

asyncio.run(concurrent_scraping())
```

下方展示令人惊叹的执行速度：

![concurrent_example](./docs/images/concurrent-example.gif)


这个例子,我们成功实现了同时对两个页面的数据提取.
还有更多强大功能！响应式自动化的事件系统、请求拦截与修改等等。赶快查阅文档!

## 🔧 快速问题排查

**找不到浏览器？**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.binary_location = '/path/to/your/chrome'
browser = Chrome(options=options)
```

**浏览器在 FailedToStartBrowser 错误后启动？**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.start_timeout = 20  # 默认是 10 秒

browser = Chrome(options=options)
```

**需要代理？**
```python
options.add_argument('--proxy-server=your-proxy:port')
```

**在 Docker 中运行？**
```python
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

## 📚 文档

Pydoll 的完整文档、详细示例以及对所有功能的深入探讨可以通过以下链接访问： [官方文档](https://autoscrape-labs.github.io/pydoll/).

文档包含以下部分:
- **快速上手指南** - 分步教程
- **API 参考** - 完整的方法文档
- **高级技巧** - 网络拦截、事件处理、性能优化

>此 README 的中文版本在[这里](README_zh.md)。

## 🤝 贡献

我们很乐意看到您的帮助让 Pydoll 变得更好！查看我们的[贡献指南](CONTRIBUTING.md)开始贡献。无论是修复错误、添加功能还是改进文档 - 所有贡献都受欢迎！

请确保：
- 为新功能或错误修复编写测试
- 遵循代码风格和约定
- 对拉取请求使用约定式提交
- 在提交前运行 lint 检查和测试

## 💖 支持我的工作

如果您发现 Pydoll 有用，请考虑[在 GitHub 上支持我](https://github.com/sponsors/thalissonvs)。  
您将获得独家优惠，如优先支持、自定义功能等等！

现在无法赞助？没问题，您仍然可以通过以下方式提供很大帮助：
- 为仓库加星
- 在社交媒体上分享
- 撰写文章或教程
- 提供反馈或报告问题

每一点支持都很重要/

## 💬 传播消息

如果 Pydoll 为您节省了时间、心理健康或者拯救了一个键盘免于被砸，请给它一个 ⭐，分享它，或者告诉您奇怪的开发者朋友。

## 📄 许可证

Pydoll 在 [MIT 许可证](LICENSE) 下获得许可。

<p align="center">
  <b>Pydoll</b> — 让浏览器自动化变得神奇！
</p>
