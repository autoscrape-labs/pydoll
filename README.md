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

🎭 **Advanced Browser Fingerprint Spoofing** - Revolutionary fingerprint protection with one-click activation  
🔹 **Zero Webdrivers!** Say goodbye to webdriver compatibility nightmares  
🔹 **Native Captcha Bypass!** Smoothly handles Cloudflare Turnstile and reCAPTCHA v3*  
🔹 **Async Performance** for lightning-fast automation  
🔹 **Human-like Interactions** that mimic real user behavior  
🔹 **Powerful Event System** for reactive automations  
🔹 **Multi-browser Support** including Chrome and Edge

## Why Pydoll Exists

Picture this: you need to automate browser tasks. Maybe it's testing your web application, scraping data from websites, or automating repetitive processes. Traditionally, this meant dealing with external drivers, complex configurations, and a host of compatibility issues that seemed to appear out of nowhere.

But there's an even bigger challenge: **modern web protection and tracking systems**. Browser fingerprinting techniques, Cloudflare Turnstile captchas, reCAPTCHA v3, and sophisticated bot detection algorithms that can instantly identify and block traditional automation tools. Your perfectly written automation script fails not because of bugs, but because websites can track your unique browser fingerprint and detect automation patterns.

**Pydoll was born to change that.**

Built from the ground up with a different philosophy, Pydoll connects directly to the Chrome DevTools Protocol (CDP), eliminating the need for external drivers entirely. More importantly, it incorporates advanced browser fingerprint spoofing and intelligent captcha bypass capabilities that make your automations virtually indistinguishable from real human interactions.

We believe that powerful automation shouldn't require you to become a configuration expert or constantly battle with tracking and anti-bot systems. With Pydoll, you focus on what matters: your automation logic, not the underlying complexity or protection bypassing.

## What Makes Pydoll Special

- **🎭 Revolutionary Fingerprint Spoofing**: One-click activation generates realistic, randomized browser fingerprints that fool even sophisticated tracking systems. Covers all major fingerprinting techniques including WebGL, Canvas, Audio, Navigator properties, and more.

- **Intelligent Captcha Bypass**: Built-in automatic solving for Cloudflare Turnstile and reCAPTCHA v3 captchas without external services, API keys, or complex configurations. Your automations continue seamlessly even when encountering protection systems.

- **Truly Human Interactions**: Advanced algorithms simulate authentic human behavior patterns - from realistic timing between actions to natural mouse movements, scroll patterns, and typing rhythms that fool even sophisticated bot detection systems.

- **Genuine Simplicity**: We don't want you wasting time configuring drivers or dealing with compatibility issues. With Pydoll, you install and you're ready to automate, even on protected and tracking-enabled sites.

- **Native Async Performance**: Built from the ground up with `asyncio`, Pydoll doesn't just support asynchronous operations - it was designed for them, enabling concurrent processing of multiple protected sites.

- **Powerful Network Monitoring**: Intercept, modify, and analyze all network traffic with ease, giving you complete control over requests and responses - perfect for bypassing additional protection layers.

- **Event-Driven Architecture**: React to page events, network requests, and user interactions in real-time, enabling sophisticated automation flows that adapt to dynamic protection systems.

## Installation

### Install from PyPI

```bash
pip install pydoll-python
```

### Install from GitHub (Enhanced Version with Fingerprint Spoofing)

```bash
# Install the latest enhanced version with advanced fingerprint spoofing
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git

# Or install a specific version/branch
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git@main
```

That's it. No drivers to download, no complex configurations. Just install and start automating with advanced fingerprint protection.

## Browser Fingerprint Spoofing

### Overview

Pydoll's fingerprint spoofing feature provides a comprehensive browser fingerprint protection solution. By generating random but realistic browser fingerprints, it effectively prevents websites from tracking your browsing behavior through fingerprinting techniques.

### Key Features

- 🎭 **One-Click Activation** - Enable fingerprint spoofing with just one parameter
- 🔄 **Intelligent Generation** - Automatically generates random but realistic browser fingerprints
- 🛡️ **Comprehensive Protection** - Covers all major fingerprinting techniques (User-Agent, WebGL, Canvas, Audio, etc.)
- 💾 **Fingerprint Persistence** - Support for saving and reusing fingerprint configurations
- ⚙️ **Highly Customizable** - Support for customizing various browser attributes
- 🚀 **Auto-Injection** - Uses CDP to automatically inject scripts without manual operation

### Quick Start

#### Basic Usage

```python
import asyncio
from pydoll.fingerprint import Chrome

async def basic_fingerprint_example():
    # Enable fingerprint spoofing with just one parameter
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Use browser normally, fingerprint spoofing works automatically
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        
        # View generated fingerprint information
        summary = browser.get_fingerprint_summary()
        print("Current fingerprint:", summary)

asyncio.run(basic_fingerprint_example())
```

#### Custom Configuration

```python
from pydoll.fingerprint import Chrome, FingerprintConfig

async def custom_fingerprint_example():
    # Create custom fingerprint configuration
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",  # Force Windows
        min_screen_width=1920,   # Fixed screen resolution
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

asyncio.run(custom_fingerprint_example())
```

#### Edge Browser Support

```python
from pydoll.fingerprint import Edge

async def edge_fingerprint_example():
    # Edge browser also supports fingerprint spoofing
    async with Edge(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        await tab.go_to('https://browserleaks.com/javascript')

asyncio.run(edge_fingerprint_example())
```

### Advanced Fingerprint Features

#### Fingerprint Persistence

```python
async def persistence_example():
    # First session: generate and save fingerprint
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # Save current fingerprint
        if browser.fingerprint_manager:
            path = browser.fingerprint_manager.save_fingerprint("my_identity")
            print(f"Fingerprint saved to: {path}")
    
    # Second session: reuse saved fingerprint
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        if browser.fingerprint_manager:
            browser.fingerprint_manager.load_fingerprint("my_identity")
            print("Loaded saved fingerprint")
        
        tab = await browser.start()
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')

asyncio.run(persistence_example())
```

#### Fingerprint Management

```python
from pydoll.fingerprint import FingerprintManager, FingerprintConfig

# Use fingerprint manager directly
manager = FingerprintManager()

# Generate multiple different fingerprints
for i in range(3):
    fingerprint = manager.generate_new_fingerprint(force=True)
    manager.save_fingerprint(f"fingerprint_{i}")
    print(f"Fingerprint {i}: {fingerprint.user_agent}")

# View all saved fingerprints
saved_fingerprints = manager.list_saved_fingerprints()
print("Saved fingerprints:", saved_fingerprints)

# Delete fingerprint
manager.delete_fingerprint("fingerprint_0")
```

### Spoofed Fingerprinting Techniques

This module can spoof the following fingerprinting techniques:

#### 🔧 Navigator Properties
- User-Agent string
- Platform information (platform)
- Language settings (language, languages)
- Hardware concurrency (hardwareConcurrency)
- Device memory (deviceMemory)
- Cookie enabled status

#### 🖥️ Screen and Window Properties
- Screen resolution (screen.width/height)
- Available screen area (screen.availWidth/availHeight)
- Color depth (colorDepth, pixelDepth)
- Window inner dimensions (innerWidth/innerHeight)
- Window outer dimensions (outerWidth/outerHeight)

#### 🎨 WebGL Fingerprint
- WebGL vendor information (VENDOR)
- WebGL renderer information (RENDERER)
- WebGL version information
- Supported WebGL extensions list

#### 🖼️ Canvas Fingerprint
- Canvas drawing result spoofing
- Image data noise injection

#### 🔊 Audio Fingerprint
- AudioContext sample rate
- Audio context state
- Maximum number of channels

#### 🌍 Geography and Timezone
- Timezone settings
- Timezone offset
- Internationalization API (Intl)

#### 🔌 Plugin Information
- Browser plugin list
- Plugin detailed information

#### 🛡️ Automation Detection Protection
- Remove `navigator.webdriver` property
- Clear Selenium-related identifiers
- Hide WebDriver automation traces
- Override `toString` methods to hide modifications

### Configuration Options

#### FingerprintConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `browser_type` | str | "chrome" | Browser type ("chrome" or "edge") |
| `is_mobile` | bool | False | Whether to simulate mobile device |
| `preferred_os` | str | None | Preferred OS ("windows", "macos", "linux") |
| `preferred_languages` | List[str] | None | Preferred language list |
| `min_screen_width` | int | 1024 | Minimum screen width |
| `max_screen_width` | int | 2560 | Maximum screen width |
| `min_screen_height` | int | 768 | Minimum screen height |
| `max_screen_height` | int | 1440 | Maximum screen height |
| `enable_webgl_spoofing` | bool | True | Enable WebGL spoofing |
| `enable_canvas_spoofing` | bool | True | Enable Canvas spoofing |
| `enable_audio_spoofing` | bool | True | Enable Audio spoofing |
| `include_plugins` | bool | True | Include plugin information |
| `enable_webrtc_spoofing` | bool | True | Enable WebRTC spoofing |

### Testing Fingerprint Spoofing

Visit these websites to test fingerprint spoofing effectiveness:

1. **FingerprintJS**: https://fingerprintjs.github.io/fingerprintjs/
2. **AmIUnique**: https://amiunique.org/fp  
3. **BrowserLeaks**: https://browserleaks.com/javascript

If fingerprint spoofing is successful, visiting these sites with different browser instances should generate different fingerprint IDs.

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

🎭 **先进的浏览器指纹伪装** - 革命性的指纹保护，一键激活  
🔹 **零WebDriver依赖！** 告别WebDriver兼容性噩梦  
🔹 **原生验证码绕过！** 平滑处理Cloudflare Turnstile和reCAPTCHA v3*  
🔹 **异步性能** 实现闪电般快速的自动化  
🔹 **类人交互** 模拟真实用户行为  
🔹 **强大的事件系统** 用于响应式自动化  
🔹 **多浏览器支持** 包括Chrome和Edge

## 为什么存在Pydoll

想象一下：您需要自动化浏览器任务。也许是测试您的Web应用程序、从网站抓取数据或自动化重复流程。传统上，这意味着要处理外部驱动程序、复杂配置以及看似无处不在的兼容性问题。

但还有一个更大的挑战：**现代Web保护和跟踪系统**。浏览器指纹识别技术、Cloudflare Turnstile验证码、reCAPTCHA v3以及能够立即识别和阻止传统自动化工具的复杂机器人检测算法。您精心编写的自动化脚本失败不是因为错误，而是因为网站可以跟踪您独特的浏览器指纹并检测自动化模式。

**Pydoll就是为改变这种情况而生的。**

Pydoll采用不同的理念从头构建，直接连接到Chrome DevTools协议（CDP），完全消除了对外部驱动程序的需求。更重要的是，它融合了先进的浏览器指纹伪装和智能验证码绕过功能，使您的自动化几乎无法与真实的人类交互区分开来。

## Pydoll的特别之处

- **🎭 革命性指纹伪装**：一键激活生成真实的随机化浏览器指纹，欺骗甚至复杂的跟踪系统。涵盖所有主要指纹技术，包括WebGL、Canvas、音频、Navigator属性等。

- **智能验证码绕过**：内置自动解决Cloudflare Turnstile和reCAPTCHA v3验证码，无需外部服务、API密钥或复杂配置。

- **真正的人类交互**：先进算法模拟真实的人类行为模式。

- **真正的简单性**：我们不希望您浪费时间配置驱动程序或处理兼容性问题。

## 安装

### 从 PyPI 安装

```bash
pip install pydoll-python
```

### 从 GitHub 安装（增强版本，带指纹伪装功能）

```bash
# 安装最新的增强版本，带有先进的指纹伪装功能
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git

# 或安装特定版本/分支
pip install git+https://github.com/3-Tokisaki-Kurumi/pydoll-enhance.git@main
```

就这样。无需下载驱动程序，无需复杂配置。只需安装即可开始使用先进指纹保护的自动化。

## 浏览器指纹伪装

### 概述

Pydoll的指纹伪装功能为您提供了一套完整的浏览器指纹防护解决方案。通过生成随机但真实的浏览器指纹，它能够有效防止网站通过指纹技术追踪您的浏览行为。

### 主要特性

- 🎭 **一键启用** - 只需设置一个参数即可启用指纹伪装
- 🔄 **智能生成** - 自动生成随机但真实的浏览器指纹
- 🛡️ **全面防护** - 覆盖所有主流指纹技术（User-Agent、WebGL、Canvas、音频等）
- 💾 **指纹持久化** - 支持保存和重用指纹配置
- ⚙️ **高度可定制** - 支持自定义各种浏览器属性
- 🚀 **自动注入** - 使用CDP自动注入脚本，无需手动操作

### 快速开始

#### 基础用法

```python
import asyncio
from pydoll.fingerprint import Chrome

async def basic_example():
    # 启用指纹伪装只需要设置一个参数
    async with Chrome(enable_fingerprint_spoofing=True) as browser:
        tab = await browser.start()
        
        # 正常使用浏览器，指纹伪装自动生效
        await tab.go_to('https://fingerprintjs.github.io/fingerprintjs/')
        
        # 查看生成的指纹信息
        summary = browser.get_fingerprint_summary()
        print("当前指纹:", summary)

asyncio.run(basic_example())
```

#### 自定义配置

```python
from pydoll.fingerprint import Chrome, FingerprintConfig

async def custom_example():
    # 创建自定义指纹配置
    config = FingerprintConfig(
        browser_type="chrome",
        preferred_os="windows",  # 强制使用Windows
        min_screen_width=1920,   # 固定屏幕分辨率
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

asyncio.run(custom_example())
```

### 伪装的指纹技术

本模块能够伪装以下指纹技术：

#### 🔧 Navigator 属性
- User-Agent 字符串
- 平台信息 (platform)
- 语言设置 (language, languages)
- 硬件并发数 (hardwareConcurrency)
- 设备内存 (deviceMemory)
- Cookie 启用状态

#### 🖥️ 屏幕和窗口属性
- 屏幕分辨率 (screen.width/height)
- 可用屏幕区域 (screen.availWidth/availHeight)
- 颜色深度 (colorDepth, pixelDepth)
- 窗口内部尺寸 (innerWidth/innerHeight)
- 窗口外部尺寸 (outerWidth/outerHeight)

#### 🎨 WebGL 指纹
- WebGL 供应商信息 (VENDOR)
- WebGL 渲染器信息 (RENDERER)
- WebGL 版本信息
- 支持的 WebGL 扩展列表

#### 🖼️ Canvas 指纹
- Canvas 绘制结果伪装
- 图像数据噪声注入

#### 🔊 音频指纹
- AudioContext 采样率
- 音频上下文状态
- 最大声道数

### 验证效果

访问以下网站测试指纹伪装效果：

1. **FingerprintJS**: https://fingerprintjs.github.io/fingerprintjs/
2. **AmIUnique**: https://amiunique.org/fp  
3. **BrowserLeaks**: https://browserleaks.com/javascript

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

# 运行自动化
asyncio.run(my_first_automation())
```

## 高级功能

### 智能验证码绕过

Pydoll最具革命性的功能之一是能够自动处理通常阻止自动化工具的现代验证码系统。

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

asyncio.run(advanced_captcha_bypass())
```

</div>

<p align="center">
  <b>Pydoll</b> — Making browser automation magical!
</p>
