<p align="center">
    <img src="https://github.com/user-attachments/assets/219f2dbc-37ed-4aea-a289-ba39cdbb335d" alt="Pydoll Logo" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll">
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/> 
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
    <a href="https://deepwiki.com/autoscrape-labs/pydoll"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<p align="center">
  <!-- Language Switch | 语言切换 -->
  <strong>🌍 Language:</strong> 
  <a href="#english">English</a> • 
  <a href="#中文">中文</a>
</p>

<p align="center">
  <a href="https://autoscrape-labs.github.io/pydoll/">Documentation</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#browser-fingerprint-spoofing">Fingerprint Spoofing</a> •
  <a href="#advanced-features">Advanced Features</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#support-my-work">Support</a> •
  <a href="#license">License</a>
</p>

---

<div id="english">

## Key Features

🎭 **Advanced Browser Fingerprint Spoofing** - Revolutionary one-click fingerprint protection system  
🔹 **Zero Webdrivers!** Say goodbye to webdriver compatibility nightmares  
🔹 **Native Captcha Bypass!** Smoothly handles Cloudflare Turnstile and reCAPTCHA v3*  
🔹 **Async Performance** for lightning-fast automation  
🔹 **Human-like Interactions** that mimic real user behavior  
🔹 **Powerful Event System** for reactive automations  
🔹 **Multi-browser Support** including Chrome and Edge

## Why Pydoll Exists

Picture this: you need to automate browser tasks. Maybe it's testing your web application, scraping data from websites, or automating repetitive processes. Traditionally, this meant dealing with external drivers, complex configurations, and a host of compatibility issues that seemed to appear out of nowhere.

But there's another challenge that's even more frustrating: **modern web protection systems**. Browser fingerprinting techniques, Cloudflare Turnstile captchas, reCAPTCHA v3, and sophisticated bot detection algorithms that can instantly identify and block traditional automation tools. Your perfectly written automation script fails not because of bugs, but because websites can track your unique browser fingerprint and tell it's not human.

**Pydoll was born to change that.**

Built from the ground up with a different philosophy, Pydoll connects directly to the Chrome DevTools Protocol (CDP), eliminating the need for external drivers entirely. More importantly, it incorporates advanced browser fingerprint spoofing and intelligent captcha bypass capabilities that make your automations virtually indistinguishable from real human interactions.

We believe that powerful automation shouldn't require you to become a configuration expert or constantly battle with anti-bot systems. With Pydoll, you focus on what matters: your automation logic, not the underlying complexity or protection bypassing.

## What Makes Pydoll Special

- **🎭 Revolutionary Fingerprint Spoofing**: One-click activation generates realistic, randomized browser fingerprints that fool even sophisticated tracking systems. Covers all major fingerprinting techniques including WebGL, Canvas, Audio, Navigator properties, and more.

- **Intelligent Captcha Bypass**: Built-in automatic solving for Cloudflare Turnstile and reCAPTCHA v3 captchas without external services, API keys, or complex configurations. Your automations continue seamlessly even when encountering protection systems.

- **Truly Human Interactions**: Advanced algorithms simulate authentic human behavior patterns - from realistic timing between actions to natural mouse movements, scroll patterns, and typing rhythms that fool even sophisticated bot detection systems.

- **Genuine Simplicity**: We don't want you wasting time configuring drivers or dealing with compatibility issues. With Pydoll, you install and you're ready to automate, even on protected sites.

- **Native Async Performance**: Built from the ground up with `asyncio`, Pydoll doesn't just support asynchronous operations - it was designed for them, enabling concurrent processing of multiple protected sites.

- **Powerful Network Monitoring**: Intercept, modify, and analyze all network traffic with ease, giving you complete control over requests and responses - perfect for bypassing additional protection layers.

- **Event-Driven Architecture**: React to page events, network requests, and user interactions in real-time, enabling sophisticated automation flows that adapt to dynamic protection systems.

- **Intuitive Element Finding**: Modern `find()` and `query()` methods that make sense and work as you'd expected, even with dynamically loaded content from protection systems.

- **Robust Type Safety**: Comprehensive type system for better IDE support and error prevention in complex automation scenarios.

## Installation

### Install from PyPI (Standard Version)

```bash
pip install pydoll-python
```

### Install from GitHub (Enhanced Version with Fingerprint Spoofing)

For the enhanced version with advanced browser fingerprint spoofing capabilities:

```bash
# Install the latest enhanced version with fingerprint spoofing
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git

# Or install a specific version/branch
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git@main
```

That's it. No drivers to download, no complex configurations. Just install and start automating with advanced protection bypassing.

## Browser Fingerprint Spoofing

### Overview

The enhanced version of Pydoll includes revolutionary browser fingerprint spoofing capabilities. This feature provides comprehensive protection against browser fingerprinting techniques used by websites to track and identify automated scripts.

### Key Features

- 🎭 **One-Click Activation** - Enable complete fingerprint protection with a single parameter
- 🔄 **Intelligent Generation** - Automatically generates random but realistic browser fingerprints
- 🛡️ **Comprehensive Protection** - Covers all major fingerprinting vectors
- 💾 **Fingerprint Persistence** - Save and reuse fingerprint configurations
- ⚙️ **Highly Customizable** - Fine-tune fingerprint characteristics
- 🚀 **Seamless Integration** - Works transparently with existing code

### Quick Start with Fingerprint Spoofing

```python
import asyncio
from pydoll.fingerprint import Chrome

async def fingerprint_protected_automation():
    # Enable fingerprint spoofing with one parameter
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Your automation runs with a completely spoofed fingerprint
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        
        # Check the generated fingerprint
        summary = browser.get_fingerprint_summary()
        print("Current fingerprint:", summary)

asyncio.run(fingerprint_protected_automation())
```

### Advanced Fingerprint Configuration

```python
from pydoll.fingerprint import Chrome, FingerprintConfig

async def custom_fingerprint_automation():
    # Create custom fingerprint configuration
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",
        min_screen_width=1920,
        max_screen_width=1920,
        min_screen_height=1080,
        max_screen_height=1080,
        enable_webgl_spoofing=True,
        enable_canvas_spoofing=True,
        enable_audio_spoofing=True,
    )
    
    async with Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    ) as browser:
        tab = await browser.start()
        await tab.go_to('https://amiunique.org/fp')

asyncio.run(custom_fingerprint_automation())
```

### Fingerprint Protection Techniques

This enhanced version spoofs the following fingerprinting techniques:

#### 🔧 Navigator Properties
- User-Agent strings with realistic browser versions
- Platform information (Windows, macOS, Linux)
- Language settings and preferences
- Hardware concurrency and device memory
- Browser plugins and their details

#### 🖥️ Screen and Display Properties
- Screen resolution and available dimensions
- Color depth and pixel density
- Window inner/outer dimensions
- Device pixel ratio

#### 🎨 WebGL Fingerprinting
- WebGL vendor and renderer information
- Supported WebGL extensions
- WebGL parameter values
- Graphics card information spoofing

#### 🖼️ Canvas Fingerprinting
- Canvas rendering result manipulation
- Image data noise injection
- Text rendering variations

#### 🔊 Audio Fingerprinting
- AudioContext sample rate spoofing
- Audio processing characteristics
- Sound synthesis variations

#### 🛡️ Anti-Detection Features
- Removes `navigator.webdriver` property
- Hides automation-related objects
- Spoofs `toString` method results
- Bypasses common detection scripts

### Testing Your Fingerprint Protection

Visit these websites to verify your fingerprint spoofing is working:

1. **FingerprintJS Demo**: https://fingerprintjs.github.io/fingerprintjs/
2. **AmIUnique**: https://amiunique.org/fp
3. **BrowserLeaks**: https://browserleaks.com/javascript

Each browser session should generate a unique, realistic fingerprint.

## Getting Started

### Your First Automation

Let's start with something simple. The code below opens a browser, navigates to a website, and interacts with elements:

```python
import asyncio
from pydoll.browser import Chrome

async def my_first_automation():
    # Create a browser instance
    async with Chrome() as browser:
        # Start the browser and get a tab
        tab = await browser.start()
        
        # Navigate to a website
        await tab.go_to('https://example.com')
        
        # Find elements intuitively
        button = await tab.find(tag_name='button', class_name='submit')
        await button.click()
        
        # Or use CSS selectors/XPath directly
        link = await tab.query('a[href*="contact"]')
        await link.click()

# Run the automation
asyncio.run(my_first_automation())
```

### Custom Configuration

Sometimes you need more control. Pydoll offers flexible configuration options:

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def custom_automation():
    # Configure browser options
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

## Advanced Features

### Intelligent Captcha Bypass

One of Pydoll's most revolutionary features is its ability to automatically handle modern captcha systems that typically block automation tools. This isn't just about solving captchas - it's about making your automations completely transparent to protection systems.

**Supported Captcha Types:**
- **Cloudflare Turnstile** - The modern replacement for reCAPTCHA
- **reCAPTCHA v3** - Google's invisible captcha system
- **Custom implementations** - Extensible framework for new captcha types

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

**Why This Matters:**
- **No External Dependencies**: No need for captcha solving services or API keys
- **Cost Effective**: Eliminate monthly captcha solving service fees
- **Reliable**: Works consistently without depending on third-party availability
- **Fast**: Instant solving without network delays to external services
- **Seamless Integration**: Captcha bypass happens transparently in your automation flow

### Advanced Element Finding

Pydoll offers multiple intuitive ways to find elements. No matter how you prefer to work, we have an approach that makes sense for you:

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

### Concurrent Automation

One of the great advantages of Pydoll's asynchronous design is the ability to process multiple tasks simultaneously:

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

### Event-Driven Automation

React to page events and user interactions in real-time. This enables more sophisticated and responsive automations:

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

### Working with iFrames

Pydoll provides seamless iframe interaction through the `get_frame()` method. This is especially useful for dealing with embedded content:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def iframe_interaction():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')
        
        # Find the iframe element
        iframe_element = await tab.query('.hcaptcha-iframe', timeout=10)
        
        # Get a Tab instance for the iframe content
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

## Documentation

For comprehensive documentation, detailed examples, and deep dives into Pydoll's features, visit our [official documentation site](https://autoscrape-labs.github.io/pydoll/).

The documentation includes:
- **Getting Started Guide** - Step-by-step tutorials
- **API Reference** - Complete method documentation  
- **Advanced Techniques** - Network interception, event handling, performance optimization
- **Troubleshooting** - Common issues and solutions
- **Best Practices** - Patterns for reliable automation

## Contributing

We'd love your help making Pydoll even better! Check out our [contribution guidelines](CONTRIBUTING.md) to get started. Whether it's fixing bugs, adding features, or improving documentation - all contributions are welcome!

Please make sure to:
- Write tests for new features or bug fixes
- Follow coding style and conventions
- Use conventional commits for pull requests
- Run lint and test checks before submitting

## Support My Work

If you find my projects helpful, consider [sponsoring me on GitHub](https://github.com/sponsors/thalissonvs).  
You'll get access to exclusive perks like prioritized support, custom features, and more!

Can't sponsor right now? No problem — you can still help a lot by:
- Starring the repo
- Sharing it on social media
- Writing blog posts or tutorials
- Giving feedback or reporting issues

Every bit of support makes a difference — thank you!

## License

Pydoll is licensed under the [MIT License](LICENSE).

</div>

---

<div id="中文">

## 主要特性

🎭 **先进的浏览器指纹伪装** - 革命性的一键指纹保护系统  
🔹 **零WebDriver依赖！** 告别WebDriver兼容性噩梦  
🔹 **原生验证码绕过！** 平滑处理Cloudflare Turnstile和reCAPTCHA v3*  
🔹 **异步性能** 实现闪电般快速的自动化  
🔹 **类人交互** 模拟真实用户行为  
🔹 **强大的事件系统** 用于响应式自动化  
🔹 **多浏览器支持** 包括Chrome和Edge

## 为什么存在Pydoll

想象一下：您需要自动化浏览器任务。也许是测试您的Web应用程序、从网站抓取数据或自动化重复流程。传统上，这意味着要处理外部驱动程序、复杂配置以及看似无处不在的兼容性问题。

但还有一个更大的挑战：**现代Web保护系统**。浏览器指纹识别技术、Cloudflare Turnstile验证码、reCAPTCHA v3以及能够立即识别和阻止传统自动化工具的复杂机器人检测算法。您精心编写的自动化脚本失败不是因为错误，而是因为网站可以跟踪您独特的浏览器指纹并识别出这不是人类。

**Pydoll就是为改变这种情况而生的。**

Pydoll采用不同的理念从头构建，直接连接到Chrome DevTools协议（CDP），完全消除了对外部驱动程序的需求。更重要的是，它融合了先进的浏览器指纹伪装和智能验证码绕过功能，使您的自动化几乎无法与真实的人类交互区分开来。

## Pydoll的特别之处

- **🎭 革命性指纹伪装**：一键激活生成真实的随机化浏览器指纹，欺骗甚至复杂的跟踪系统。涵盖所有主要指纹技术，包括WebGL、Canvas、音频、Navigator属性等。

- **智能验证码绕过**：内置自动解决Cloudflare Turnstile和reCAPTCHA v3验证码，无需外部服务、API密钥或复杂配置。

- **真正的人类交互**：先进算法模拟真实的人类行为模式。

- **真正的简单性**：我们不希望您浪费时间配置驱动程序或处理兼容性问题。

- **原生异步性能**：从头开始使用`asyncio`构建。

- **强大的网络监控**：轻松拦截、修改和分析所有网络流量。

- **事件驱动架构**：实时响应页面事件、网络请求和用户交互。

- **直观的元素查找**：现代化的`find()`和`query()`方法。

- **强大的类型安全**：全面的类型系统，提供更好的IDE支持。

## 安装

### 从 PyPI 安装（标准版本）

```bash
pip install pydoll-python
```

### 从 GitHub 安装（增强版本，带指纹伪装功能）

对于带有先进浏览器指纹伪装功能的增强版本：

```bash
# 安装最新的增强版本，带有指纹伪装功能
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git

# 或安装特定版本/分支
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git@main
```

就这样。无需下载驱动程序，无需复杂配置。只需安装即可开始使用先进的保护绕过功能的自动化。

## 浏览器指纹伪装

### 概述

Pydoll的增强版本包含革命性的浏览器指纹伪装功能。此功能为网站用于跟踪和识别自动化脚本的浏览器指纹技术提供全面保护。

### 主要特性

- 🎭 **一键启用** - 用单个参数启用完整的指纹保护
- 🔄 **智能生成** - 自动生成随机但真实的浏览器指纹
- 🛡️ **全面防护** - 覆盖所有主要指纹向量
- 💾 **指纹持久化** - 保存和重用指纹配置
- ⚙️ **高度可定制** - 微调指纹特征
- 🚀 **无缝集成** - 与现有代码透明地工作

### 指纹伪装快速开始

```python
import asyncio
from pydoll.fingerprint import Chrome

async def fingerprint_protected_automation():
    # 用一个参数启用指纹伪装
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # 您的自动化以完全伪装的指纹运行
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        
        # 检查生成的指纹
        summary = browser.get_fingerprint_summary()
        print("当前指纹:", summary)

asyncio.run(fingerprint_protected_automation())
```

### 高级指纹配置

```python
from pydoll.fingerprint import Chrome, FingerprintConfig

async def custom_fingerprint_automation():
    # 创建自定义指纹配置
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",
        min_screen_width=1920,
        max_screen_width=1920,
        min_screen_height=1080,
        max_screen_height=1080,
        enable_webgl_spoofing=True,
        enable_canvas_spoofing=True,
        enable_audio_spoofing=True,
    )
    
    async with Chrome(
        enable_fingerprint_spoofing=True,
        fingerprint_config=config
    ) as browser:
        tab = await browser.start()
        await tab.go_to('https://amiunique.org/fp')

asyncio.run(custom_fingerprint_automation())
```

### 指纹保护技术

此增强版本伪装以下指纹技术：

#### 🔧 Navigator 属性
- 具有真实浏览器版本的User-Agent字符串
- 平台信息（Windows、macOS、Linux）
- 语言设置和偏好
- 硬件并发和设备内存
- 浏览器插件及其详细信息

#### 🖥️ 屏幕和显示属性
- 屏幕分辨率和可用尺寸
- 颜色深度和像素密度
- 窗口内部/外部尺寸
- 设备像素比

#### 🎨 WebGL 指纹
- WebGL供应商和渲染器信息
- 支持的WebGL扩展
- WebGL参数值
- 显卡信息伪装

#### 🖼️ Canvas 指纹
- Canvas渲染结果操作
- 图像数据噪声注入
- 文本渲染变化

#### 🔊 音频指纹
- AudioContext采样率伪装
- 音频处理特征
- 声音合成变化

#### 🛡️ 反检测功能
- 移除`navigator.webdriver`属性
- 隐藏自动化相关对象
- 伪装`toString`方法结果
- 绕过常见检测脚本

### 测试您的指纹保护

访问这些网站验证您的指纹伪装是否工作：

1. **FingerprintJS演示**: https://fingerprintjs.github.io/fingerprintjs/
2. **AmIUnique**: https://amiunique.org/fp
3. **BrowserLeaks**: https://browserleaks.com/javascript

每个浏览器会话都应生成唯一、真实的指纹。

## 快速开始

### 您的第一个自动化

让我们从简单的开始。下面的代码打开浏览器，导航到网站并与元素交互：

```python
import asyncio
from pydoll.browser import Chrome

async def my_first_automation():
    # 创建浏览器实例
    async with Chrome() as browser:
        # 启动浏览器并获取标签页
        tab = await browser.start()
        
        # 导航到网站
        await tab.go_to('https://example.com')
        
        # 直观地查找元素
        button = await tab.find(tag_name='button', class_name='submit')
        await button.click()
        
        # 或直接使用CSS选择器/XPath
        link = await tab.query('a[href*="contact"]')
        await link.click()

# 运行自动化
asyncio.run(my_first_automation())
```

### 自定义配置

有时您需要更多控制。Pydoll提供灵活的配置选项：

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def custom_automation():
    # 配置浏览器选项
    options = ChromiumOptions()
    options.add_argument('--proxy-server=username:password@ip:port')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-web-security')
    options.binary_location = '/path/to/your/browser'

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 您的自动化代码在这里
        await tab.go_to('https://example.com')
        
        # 浏览器现在使用您的自定义设置

asyncio.run(custom_automation())
```

## 高级功能

### 智能验证码绕过

Pydoll最具革命性的功能之一是能够自动处理通常阻止自动化工具的现代验证码系统。这不仅仅是解决验证码 - 而是让您的自动化对保护系统完全透明。

**支持的验证码类型：**
- **Cloudflare Turnstile** - reCAPTCHA的现代替代品
- **reCAPTCHA v3** - Google的隐形验证码系统
- **自定义实现** - 新验证码类型的可扩展框架

```python
import asyncio
from pydoll.browser import Chrome

async def advanced_captcha_bypass():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 方法1：上下文管理器（等待验证码完成）
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-cloudflare.com')
            print("Cloudflare Turnstile 自动解决！")
            
            # 继续您的自动化 - 验证码已处理
            await tab.find(id='username').type_text('user@example.com')
            await tab.find(id='password').type_text('password123')
            await tab.find(tag_name='button', text='Login').click()
        
        # 方法2：后台处理（非阻塞）
        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://another-protected-site.com')
        # 验证码在后台自动解决，代码继续执行
        
        # 方法3：特定实现的自定义验证码选择器
        await tab.enable_auto_solve_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'custom-captcha-widget'),
            time_before_click=3,  # 解决前等待3秒
            time_to_wait_captcha=10  # 10秒后超时
        )
        
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(advanced_captcha_bypass())
```

**为什么这很重要：**
- **无外部依赖**：无需验证码解决服务或API密钥
- **成本效益**：消除月度验证码解决服务费用
- **可靠**：无需依赖第三方可用性即可一致工作
- **快速**：即时解决，无需到外部服务的网络延迟
- **无缝集成**：验证码绕过在您的自动化流程中透明进行

### 高级元素查找

Pydoll提供多种直观的方式来查找元素。无论您喜欢如何工作，我们都有适合您的方法：

```python
import asyncio
from pydoll.browser import Chrome

async def element_finding_examples():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 按属性查找（最直观）
        submit_btn = await tab.find(
            tag_name='button',
            class_name='btn-primary',
            text='Submit'
        )
        
        # 按ID查找
        username_field = await tab.find(id='username')
        
        # 查找多个元素
        all_links = await tab.find(tag_name='a', find_all=True)
        
        # CSS选择器和XPath
        nav_menu = await tab.query('nav.main-menu')
        specific_item = await tab.query('//div[@data-testid="item-123"]')
        
        # 带超时和错误处理
        delayed_element = await tab.find(
            class_name='dynamic-content',
            timeout=10,
            raise_exc=False  # 如果未找到则返回None
        )
        
        # 高级：自定义属性
        custom_element = await tab.find(
            data_testid='submit-button',
            aria_label='Submit form'
        )

asyncio.run(element_finding_examples())
```

</div>

<p align="center">
  <b>Pydoll</b> — Making browser automation magical!
</p>
