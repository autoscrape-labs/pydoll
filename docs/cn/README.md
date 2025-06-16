<p align="center">
    <img src="https://github.com/user-attachments/assets/219f2dbc-37ed-4aea-a289-ba39cdbb335d" alt="Pydoll Logo" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll" >
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/>
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
    <a href="https://deepwiki.com/autoscrape-labs/pydoll"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<p align="center">
  <a href="https://autoscrape-labs.github.io/pydoll/">Documentation</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#advanced-features">Advanced Features</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#support-my-work">Support</a> •
  <a href="#license">License</a>
</p>


## 核心特性  

🔹 **无需Webdriver!** 从此告别webdriver兼容性地狱   
🔹 **绕过本地验证码!** 平滑处理Cloudflare Turnstile和reCAPTCHA v3验证码  
🔹 **异步性能加持** 闪电般快速的自动化操作  
🔹 **模拟真人交互** 模拟真实用户行为  
🔹 **强大的事件系统** 为了响应式自动化  
🔹 **多浏览器支持** 支持Chrome以及Edge

## 为什么选择Pydoll

想象一下场景: 你正在尝试写一个浏览器自动化任务，比如测试你的网站，从网站抓取数据，或者自动化一些重复性任务。通常来说，这需要解决外部驱动，复杂的配置，和一些无缘无故的兼容性问题。  
不仅如此,目前还有一个更重要的问题: **现在网站反爬保护系统**  例如: Cloudflare Turnstile 验证码, reCAPTCHA v3以及一些检测出传统自动化工具的机器人检测算法,你完美地写了一个没有bug的自动化脚本,但是这些网站却判定你是机器人.  

**Pydoll的诞生就是为了解决此类问题!**

Pydoll从头开始构建，Pydoll可以直接通过Chrome DevTools Protocol (CDP协议)链接到浏览器，完全消除了传统自动化框架需要外部驱动的问题（例如selenuim）。更重要地是，它可以更先进地模拟真人行为操作以及拥有更智能的验证码绕过能力使你的自动化任务和真人行为一样几乎无法区分。  

我们相信强大的自动化框架不应该需要复杂配置并且可以更方便地绕过反爬系统。在Pydoll的加持下，你只需要专注于业务逻辑而并不是复杂的底层设计以及绕过反爬系统。  

## 特点

- **智能验证码绕过**: 内置Cloudflare Turnstile与reCAPTCHA v3验证码的自动破解能力，无需依赖外部服务、API密钥或复杂配置。即使遭遇防护系统，您的自动化流程仍可畅行无阻。

- **模拟真人交互**: 通过先进算法模拟真实人类行为特征——通过随机操作间隔，到鼠标移动轨迹、页面滚动模式乃至输入速度，皆可骗过最严苛的反爬虫系统。

- **极简哲学**: 无需浪费太多时间在配置驱动或解决兼容问题上。Pydoll开箱即用。

- **原生异步性能**: 基于`asyncio`库深度设计, Pydoll不仅支持异步操作——更为高并发而生，可同时进行多个受防护站点的数据采集。

- **强大的网络监控**: 轻松实现请求拦截、流量篡改与响应分析，完整掌控网络通信链路，轻松突破层层防护体系。

- **事件驱动架构**: 实时响应页面事件、网络请求与用户交互，构建能动态适应防护系统的智能自动化流。

- **直观的元素定位**: 使用符合人类直觉的定位方法 `find()` 和 `query()` ，面对动态加载的防护内容，定位依然精准。

- **强类型安全**: 完备的类型系统为复杂自动化场景提供更优IDE支持和更好地预防运行时报错。

## 安装

```bash
pip install pydoll-python
```

无需额外的驱动下载，无需复杂的配置，开箱即用。  

## 开始开始

### 开始第一个自动化应用

这是一个简单的例子，主要包括打开一个浏览器，访问网站以及和网页元素交互：

```python
import asyncio
from pydoll.browser import Chrome

async def my_first_automation():
    # 创建浏览器实例
    async with Chrome() as browser:
        # 启动浏览器并获取一个标签
        tab = await browser.start()
        
        # 访问网站
        await tab.go_to('https://example.com')
        
        # 直观地查找元素
        button = await tab.find(tag_name='button', class_name='submit')
        await button.click()
        
        # 或者直接使用CSS selectors/XPath表达式
        link = await tab.query('a[href*="contact"]')
        await link.click()

# 运行自动化程序
asyncio.run(my_first_automation())
```

### 定制配置

Pydoll提供了灵活的配置选项

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def custom_automation():
    # 配置浏览器命令行参数
    options = ChromiumOptions()
    options.add_argument('--proxy-server=username:password@ip:port')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-web-security')
    options.binary_location = '/path/to/your/browser'

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Your automation code here
        await tab.go_to('https://example.com')
        
        # The browser is now using your custom settings

asyncio.run(custom_automation())
```

## 进阶特性  

### 智能验证码绕过  

Pydoll最具代表性的功能之一，是能自动处理现代验证码系统——这些系统通常会检测拦截自动化工具。这不仅仅是绕过验证码，更是让您的自动化操作在防护系统面前完全隐形。  

**Supported Captcha Types:**
- **Cloudflare Turnstile** - reCAPTCHA 的现代替代方案
- **reCAPTCHA v3** - 谷歌的无感验证系统
- **自定义实现** - 可扩展框架，适配新型验证码

```python
import asyncio
from pydoll.browser import Chrome

async def advanced_captcha_bypass():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Method 1: Context manager (waits for captcha completion)
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-cloudflare.com')
            print("Cloudflare Turnstile automatically solved!")
            
            # Continue with your automation - captcha is handled
            await tab.find(id='username').type_text('user@example.com')
            await tab.find(id='password').type_text('password123')
            await tab.find(tag_name='button', text='Login').click()
        
        # Method 2: Background processing (non-blocking)
        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://another-protected-site.com')
        # Captcha solved automatically in background while code continues
        
        # Method 3: Custom captcha selector for specific implementations
        await tab.enable_auto_solve_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'custom-captcha-widget'),
            time_before_click=3,  # Wait 3 seconds before solving
            time_to_wait_captcha=10  # Timeout after 10 seconds
        )
        
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(advanced_captcha_bypass())
```

### 高级元素定位

Pydoll 提供多种直观的元素定位方式，无论您的使用习惯如何，总有一种方案适合您：  

```python
import asyncio
from pydoll.browser import Chrome

async def element_finding_examples():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 属性匹配
        submit_btn = await tab.find(
            tag_name='button',
            class_name='btn-primary',
            text='Submit'
        )
        
        # id匹配
        username_field = await tab.find(id='username')
        
        # 多个元素匹配
        all_links = await tab.find(tag_name='a', find_all=True)
        
        # CSS selectors 和 XPath表达式
        nav_menu = await tab.query('nav.main-menu')
        specific_item = await tab.query('//div[@data-testid="item-123"]')
        
        # 超时和错误处理
        delayed_element = await tab.find(
            class_name='dynamic-content',
            timeout=10,
            raise_exc=False  # Returns None if not found
        )
        
        # 自定义属性字段匹配
        custom_element = await tab.find(
            data_testid='submit-button',
            aria_label='Submit form'
        )

asyncio.run(element_finding_examples())
```

### 并行自动化  

由于Pydoll是基于异步设计的，能够更好地同时处理多个任务：  

```python
import asyncio
from pydoll.browser import Chrome

async def scrape_page(url):
    """Extract data from a single page"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        
        title = await tab.execute_script('return document.title')
        links = await tab.find(tag_name='a', find_all=True)
        
        return {
            'url': url,
            'title': title,
            'link_count': len(links)
        }

async def concurrent_scraping():
    urls = [
        'https://example1.com',
        'https://example2.com',
        'https://example3.com'
    ]
    
    # Process all URLs simultaneously
    tasks = [scrape_page(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(f"{result['url']}: {result['title']} ({result['link_count']} links)")

asyncio.run(concurrent_scraping())
```

### 事件驱动的自动化

Pydoll 支持实时响应页面事件与用户交互，从而实现更智能、响应更迅捷的自动化流程：  

```python
import asyncio
from pydoll.browser import Chrome
from pydoll.protocol.page.events import PageEvent

async def event_driven_automation():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Enable page events
        await tab.enable_page_events()
        
        # React to page load
        async def on_page_load(event):
            print("Page loaded! Starting automation...")
            # Perform actions after page loads
            search_box = await tab.find(id='search-box')
            await search_box.type_text('automation')
        
        # React to navigation
        async def on_navigation(event):
            url = event['params']['url']
            print(f"Navigated to: {url}")
        
        await tab.on(PageEvent.LOAD_EVENT_FIRED, on_page_load)
        await tab.on(PageEvent.FRAME_NAVIGATED, on_navigation)
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)  # Let events process

asyncio.run(event_driven_automation())
```

### 处理 iframe 内容

Pydoll 通过`get_frame()`方法提供无缝的 iframe 交互能力，尤其适用于处理嵌入式内容：  

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def iframe_interaction():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')
        
        # 查找iframe元素
        iframe_element = await tab.query('.hcaptcha-iframe', timeout=10)
        
        # 从iframe中获取一个tab实例
        frame = await tab.get_frame(iframe_element)
        
        # Now interact with elements inside the iframe
        submit_button = await frame.find(tag_name='button', class_name='submit')
        await submit_button.click()
        
        # You can use all Tab methods on the frame
        form_input = await frame.find(id='captcha-input')
        await form_input.type_text('verification-code')
        
        # Find elements by various methods
        links = await frame.find(tag_name='a', find_all=True)
        specific_element = await frame.query('#specific-id')

asyncio.run(iframe_interaction())
```

## 文档

如需完整文档、详细示例以及想要深入了解Pydoll的特性,请访问[官方文档](https://autoscrape-labs.github.io/pydoll/)

文档包含以下内容：
- **入门指南** - 手把手教学教程
- **API参考** - 完整的方法文档说明  
- **高级技巧** - 网络请求拦截、事件处理、性能优化
- **故障排查** - 常见问题及解决方案
- **最佳实践** - 构建稳定自动化流程的推荐方案

## 贡献

诚邀您携手，共铸 Pydoll 更佳体验！请参阅[贡献指南](CONTRIBUTING.md)开启协作。无论修复疏漏、添砖新能，抑或完善文档——所有热忱，皆为至宝！

请务必遵循以下规范：  
- 为新功能或 Bug 修复编写测试
- 遵守代码风格与项目规范  
- 提交 Pull Request 时使用约定式提交（Conventional Commits）  
- 提交前运行代码检查（Lint）和测试  

## 赞助我们

如果你觉得本项目对你有帮助，可以考虑[赞助我们](https://github.com/sponsors/thalissonvs).  
您将获取独家优先支持,定制需求以及更多的福利!

现在不能赞助?无妨,你可以通过以下方式支持我们:
- ⭐ Star 本项目
- 📢 社交平台分享
- ✍️ 撰写教程或博文
- 🐛 反馈建议或提交issues

点滴相助，铭记于心——诚谢！  

## 许可

Pydoll是在 [MIT License](LICENSE) 许可下许可的开源软件。  

<p align="center">
  <b>Pydoll</b> — Making browser automation magical!
</p>
