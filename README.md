# pydoll 浏览器指纹伪装功能说明
#Pydoll Browser Fingerprint Disguise Function Description

在原有的pydoll库基础上提供内置伪装指纹功能
Provide built-in disguised fingerprint function on the basis of the original Pydoll library

## 自动伪装机制

pydoll的指纹伪装系统设计为"一键启用"模式：只需设置一个参数，系统会自动完成所有指纹伪装工作，无需用户进行额外配置或手动注入代码。

### 自动注入流程

1. **初始化阶段**：当您创建浏览器实例并设置`enable_fingerprint_spoofing=True`时，系统会自动生成一个随机指纹。

2. **启动参数注入**：浏览器启动前，指纹相关的命令行参数会自动添加到浏览器选项中。

3. **JavaScript自动注入**：浏览器启动后，系统会自动将JavaScript脚本注入到页面中，进一步修改浏览器的运行时属性。

4. **全程保护**：在整个浏览会话中，伪装机制会持续工作，保护您免受指纹识别技术的追踪。

所有这些步骤都在底层自动完成，用户只需确保启用该功能即可。

## 快速开始

### 简单三步使用指纹伪装功能

```python
# 1. 导入必要组件
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options

# 2. 创建浏览器选项
options = Options()

# 3. 创建浏览器实例并启用指纹伪装(重点是这个参数)
browser = Chrome(options=options, enable_fingerprint_spoofing=True)

# 正常使用浏览器...
await browser.start()
page = await browser.get_page()
await page.go_to("https://fingerprintjs.github.io/fingerprintjs/")
```

就是这么简单！系统会自动完成所有指纹伪装工作，无需其他额外步骤。

## 工作原理

### 1. 命令行级别保护

设置`enable_fingerprint_spoofing=True`后，以下参数会自动添加到浏览器启动命令中：

- 自定义User-Agent
- 语言设置
- 硬件并发数
- 视口大小
- 平台信息
- 禁用自动化检测特性

### 2. JavaScript级别保护

浏览器启动后，系统会自动注入JavaScript脚本，修改或覆盖以下浏览器特性：

- Navigator对象属性（userAgent, platform, languages等）
- Screen对象属性（width, height, colorDepth）
- WebGL参数和渲染信息
- Canvas绘图行为
- AudioContext音频处理
- 浏览器插件列表
- 自动化标识（如webdriver属性）

### 3. 每个会话唯一指纹

每次创建新的浏览器实例时，系统会生成一个全新的随机指纹。这确保了即使多次访问同一网站，也会被识别为不同的访问者。

## 验证指纹伪装效果

访问以下网站可以测试指纹伪装的效果：

1. FingerprintJS: https://fingerprintjs.github.io/fingerprintjs/
2. AmIUnique: https://amiunique.org/fp
3. BrowserLeaks: https://browserleaks.com/javascript

如果指纹伪装成功，每次使用不同浏览器实例访问这些网站时，应该会生成不同的指纹ID。

## 高级使用

虽然基本的自动注入已经足够应对大多数情况，但您也可以进行更高级的定制：

### 查看当前使用的指纹

```python
from pydoll.browser.fingerprint import FINGERPRINT_MANAGER

# 获取当前指纹
current_fingerprint = FINGERPRINT_MANAGER.current_fingerprint
print(f"当前使用的User Agent: {current_fingerprint['user_agent']}")
```

### 手动生成新指纹

```python
# 手动生成新的Chrome浏览器指纹
new_fingerprint = FINGERPRINT_MANAGER.generate_new_fingerprint('chrome')
```

### 定制浏览器参数

即使启用了指纹伪装，您仍然可以添加自己的命令行参数：

```python
options = Options()
options.add_argument("--disable-extensions")
options.add_argument("--incognito")

# 这些参数会与指纹伪装参数一起使用
browser = Chrome(options=options, enable_fingerprint_spoofing=True)
```

## 工作原理示意图

```
用户代码          →     pydoll指纹系统          →     浏览器实例
--------          -----------------------          ------------
enable_fingerprint_spoofing=True
                  ↓
                  1. 生成随机指纹
                  2. 添加命令行参数
                  3. 准备JS注入代码
                                                  ↓
                                                  浏览器启动
                  ↓
                  4. 自动注入JS
                                                  ↓
                                                  浏览器访问网站
                                                  (伪装指纹生效)
```

## 常见问题

### Q: 需要手动注入JavaScript代码吗？
A: 不需要。只要设置`enable_fingerprint_spoofing=True`，所有的JavaScript注入都会自动完成。

### Q: 每次生成的指纹都不同吗？
A: 是的，每次创建新的浏览器实例时都会生成不同的随机指纹。

### Q: 能否保证100%防止指纹识别？
A: 没有系统能保证100%防止所有指纹识别技术，但pydoll的指纹伪装系统覆盖了主流的指纹识别点，能有效对抗大多数常见的指纹识别方法。

### Q: 为什么有时候相同的指纹ID会出现？
A: 有些高级指纹识别技术可能会绕过常规的伪装方法。如果发现有相同的指纹ID，可以尝试额外注入更多定制化的JavaScript保护脚本。

## 结语

pydoll的指纹伪装系统设计为"开箱即用"，只要启用该功能，系统会自动完成所有复杂的指纹保护工作。这使得它非常易于使用，同时又提供了强大的指纹保护能力。 


<p align="center">
    <h1>🚀 Pydoll: Async Web Automation in Python!</h1>
</p>
<br>
<p align="center">
    <img src="https://github.com/user-attachments/assets/c4615101-d932-4e79-8a08-f50fbc686e3b" alt="Alt text" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll">
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/> 
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://tokei.rs/b1/github/thalissonvs/pydoll" alt="Total lines">
    <img src="https://tokei.rs/b1/github/thalissonvs/pydoll?category=files" alt="Files">
    <img src="https://tokei.rs/b1/github/thalissonvs/pydoll?category=comments" alt="Comments">
    <img src="https://img.shields.io/github/issues/thalissonvs/pydoll?label=Issues" alt="GitHub issues">
    <img src="https://img.shields.io/github/issues-closed/thalissonvs/pydoll?label=Closed issues" alt="GitHub closed issues">
    <img src="https://img.shields.io/github/issues/thalissonvs/pydoll/bug?label=Bugs&color=red" alt="GitHub bug issues">
    <img src="https://img.shields.io/github/issues/thalissonvs/pydoll/enhancement?label=Enhancements&color=purple" alt="GitHub enhancement issues">
</p>
<p align="center">
    <a href="https://trendshift.io/repositories/13125" target="_blank"><img src="https://trendshift.io/api/badge/repositories/13125" alt="thalissonvs%2Fpydoll | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center">
  <b>Pydoll</b> is revolutionizing browser automation! Unlike other solutions, it <b>eliminates the need for webdrivers</b>, 
  providing a smooth and reliable automation experience with native asynchronous performance.
</p>

<p align="center">
  <a href="#-installation">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-core-components">Core Components</a> •
  <a href="#-whats-new">What's New</a> •
  <a href="#-advanced-features">Advanced Features</a>
</p>

## ✨ Key Features

🔹 **Zero Webdrivers!** Say goodbye to webdriver compatibility nightmares  
🔹 **Native Captcha Bypass!** Smoothly handles Cloudflare Turnstile and reCAPTCHA v3*  
🔹 **Async Performance** for lightning-fast automation  
🔹 **Human-like Interactions** that mimic real user behavior  
🔹 **Powerful Event System** for reactive automations  
🔹 **Multi-browser Support** including Chrome and Edge



## 🔥 Installation

```bash
pip install pydoll-python
```

## ⚡ Quick Start

Get started with just a few lines of code:

```python
import asyncio
from pydoll.browser.chrome import Chrome
from pydoll.constants import By

async def main():
    async with Chrome() as browser:
        await browser.start()
        page = await browser.get_page()
        
        # Works with captcha-protected sites
        await page.go_to('https://example-with-cloudflare.com')
        button = await page.find_element(By.CSS_SELECTOR, 'button')
        await button.click()

asyncio.run(main())
```

Need to configure your browser? Easy!

```python
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options

options = Options()
# Add a proxy
options.add_argument('--proxy-server=username:password@ip:port')
# Custom browser location
options.binary_location = '/path/to/your/browser'

async with Chrome(options=options) as browser:
    await browser.start()
    # Your code here
```

## 🎉 What's New

Version 1.4.0 comes packed with amazing new features:

### 🛡️ Automatic Cloudflare Turnstile Captcha Handling

Seamlessly bypass Cloudflare Turnstile captchas with two powerful approaches:

#### Approach 1: Context Manager (Synchronous with main execution)

This approach waits for the captcha to be handled before continuing execution:

```python
import asyncio
from pydoll.browser import Chrome

async def example_with_context_manager():
    browser = Chrome()
    await browser.start()
    page = await browser.get_page()
    
    print("Using context manager approach...")
    # The context manager will wait for the captcha to be processed
    # before exiting and continuing execution
    async with page.expect_and_bypass_cloudflare_captcha(time_to_wait_captcha=5):
        await page.go_to('https://2captcha.com/demo/cloudflare-turnstile')
        print("Page loaded, waiting for captcha to be handled...")
    
    # This code will only run after the captcha has been handled
    print("Captcha handling completed, now we can continue...")
    # Your post-captcha logic here
    await asyncio.sleep(3)
    await browser.stop()

if __name__ == '__main__':
    asyncio.run(example_with_context_manager())
```

#### Approach 2: Enable/Disable (Background processing)

This approach handles captchas in the background without blocking execution:

```python
import asyncio
from pydoll.browser import Chrome

async def example_with_enable_disable():
    browser = Chrome()
    await browser.start()
    page = await browser.get_page()
    
    print("Using enable/disable approach...")
    # Enable automatic captcha solving before navigating
    await page.enable_auto_solve_cloudflare_captcha(time_to_wait_captcha=5)
    
    # Navigate to the page - captcha will be handled automatically in the background
    await page.go_to('https://2captcha.com/demo/cloudflare-turnstile')
    print("Page loaded, captcha will be handled in the background...")
    
    # Continue with other operations immediately
    # Consider adding some delay to give time for captcha to be solved
    await asyncio.sleep(5)
    
    # Disable auto-solving when no longer needed
    await page.disable_auto_solve_cloudflare_captcha()
    print("Auto-solving disabled")
    
    await browser.stop()

if __name__ == '__main__':
    asyncio.run(example_with_enable_disable())
```

### Which approach should you choose?

Not sure which method to use? Let's simplify:

#### Approach 1: Context Manager (Like a traffic light)

```python
async with page.expect_and_bypass_cloudflare_captcha():
    await page.go_to('https://protected-site.com')
    # All code inside waits for the captcha to be solved
```

**How it works:** 
- The code pauses at the end of the context manager until the captcha is resolved
- Ensures any code after the `async with` block only executes after the captcha is handled

**When to use it:**
- When you need to be certain the captcha is solved before continuing
- In sequential operations where the next steps depend on successful login
- In situations where timing is crucial (like purchasing tickets, logging in, etc.)
- When you prefer simpler, straightforward code

**Practical example:** Logging into a protected site
```python
async with page.expect_and_bypass_cloudflare_captcha():
    await page.go_to('https://site-with-captcha.com/login')
    # Here the context manager waits for the captcha to be resolved
    
# Now we can safely log in
await page.find_element(By.ID, 'username').type_keys('user123')
await page.find_element(By.ID, 'password').type_keys('password123')
await page.find_element(By.ID, 'login-button').click()
```

#### Approach 2: Enable/Disable (Like a background assistant)

```python
callback_id = await page.enable_auto_solve_cloudflare_captcha()
# Code continues immediately, solving captcha in the background
```

**How it works:**
- It's like having an assistant working in the background while you do other things
- Doesn't block your main code - continues executing immediately
- The captcha will be handled automatically when it appears, without pausing your script
- You need to manage timing yourself (by adding delays if necessary)

**When to use it:**
- When you're navigating across multiple pages and want continuous protection
- In scripts that perform many independent tasks in parallel
- For "exploratory" navigation where exact timing isn't crucial
- In long-running automation scenarios where you want to leave the handler "turned on"

**Practical example:** Continuous navigation across multiple pages
```python
# Activate protection for the entire session
await page.enable_auto_solve_cloudflare_captcha()

# Navigate through multiple pages with background protection
await page.go_to('https://site1.com')
await page.go_to('https://site2.com')
await page.go_to('https://site3.com')

# Optionally disable when no longer needed
await page.disable_auto_solve_cloudflare_captcha()
```

⚠️ **Tip for the Enable/Disable approach:** Consider adding small delays before interacting with critical elements, to give time for the captcha to be solved in the background:

```python
# Enable background solving
await page.enable_auto_solve_cloudflare_captcha()

# Navigate to protected page
await page.go_to('https://protected-site.com')

# Small delay to give time for the captcha to be solved in the background
await asyncio.sleep(3)

# Now interact with the page
await page.find_element(By.ID, 'important-button').click()
```

### Understanding Cloudflare Bypass Parameters

Both captcha bypass methods accept several parameters that let you customize how the captcha detection and solving works:

| Parameter | Description | Default | When to Change |
|-----------|-------------|---------|---------------|
| `custom_selector` | Custom CSS selector to locate the captcha element | `(By.CLASS_NAME, 'cf-turnstile')` | When the captcha has a non-standard HTML structure or class name |
| `time_before_click` | Time to wait (in seconds) before clicking the captcha element | `2` | When the captcha element isn't immediately interactive or requires time to load properly |
| `time_to_wait_captcha` | Maximum time (in seconds) to wait for the captcha element to be found | `5` | When pages load slowly or when captcha widgets take longer to appear |

**Example with custom parameters:**

```python
# For sites with slow-loading captchas or non-standard elements
async with page.expect_and_bypass_cloudflare_captcha(
    custom_selector=(By.ID, 'custom-captcha-id'),
    time_before_click=3.5,  # Wait longer before clicking
    time_to_wait_captcha=10  # Allow more time for the captcha to appear
):
    await page.go_to('https://site-with-slow-captcha.com')
```

**When to adjust `time_before_click`:**
- The captcha widget is complex and takes time to initialize
- You notice the click happens too early and fails to register
- The page is loading slowly due to network conditions
- JavaScript on the page needs time to fully initialize the widget

**When to adjust `time_to_wait_captcha`:**
- The page takes longer to load completely 
- The captcha appears after an initial loading delay
- You're experiencing timeout errors with the default value
- When working with slower connections or complex pages

### 🔌 Connect to Existing Browser

Connect to an already running Chrome/Edge instance without launching a new browser process:

```python
import asyncio
from pydoll.browser import Chrome

async def main():
    # Connect to Chrome already running on port 1234
    browser = Chrome(connection_port=1234)
    page = await browser.connect()
    
    # Control the browser as usual
    await page.go_to('https://google.com')
    
    # No need to call browser.stop() as we didn't start this instance

asyncio.run(main())
```

This is perfect for:
- Debugging scripts without restarting the browser
- Connecting to remote debugging sessions
- Working with custom browser configurations
- Integrating with existing browser instances


### 🔤 Advanced Keyboard Control

Full keyboard simulation thanks to [@cleitonleonel](https://github.com/cleitonleonel):

```python
import asyncio
from pydoll.browser.chrome import Chrome
from pydoll.browser.options import Options
from pydoll.common.keys import Keys
from pydoll.constants import By

async def main():
    async with Chrome() as browser:
        await browser.start()
        page = await browser.get_page()
        await page.go_to('https://example.com')
        
        input_field = await page.find_element(By.CSS_SELECTOR, 'input')
        await input_field.click()
        
        # Realistic typing with customizable speed
        await input_field.type_keys("hello@example.com", interval=0.2)
        
        # Special key combinations
        await input_field.key_down(Keys.SHIFT)
        await input_field.send_keys("UPPERCASE")
        await input_field.key_up(Keys.SHIFT)
        
        # Navigation keys
        await input_field.send_keys(Keys.ENTER)
        await input_field.send_keys(Keys.PAGEDOWN)

asyncio.run(main())
```

### 📁 File Upload Support

[@yie1d](https://github.com/yie1d) brings seamless file uploads:

```python
# For input elements
file_input = await page.find_element(By.XPATH, '//input[@type="file"]')
await file_input.set_input_files('path/to/file.pdf')  # Single file
await file_input.set_input_files(['file1.pdf', 'file2.jpg'])  # Multiple files

# For other elements using the file chooser
async with page.expect_file_chooser(files='path/to/file.pdf'):
    upload_button = await page.find_element(By.ID, 'upload-button')
    await upload_button.click()
```

### 🌐 Microsoft Edge Support

Now with Edge browser support thanks to [@Harris-H](https://github.com/Harris-H):

```python
import asyncio
from pydoll.browser import Edge
from pydoll.browser.options import EdgeOptions

async def main():
    options = EdgeOptions()
    # options.add_argument('--headless')
    
    async with Edge(options=options) as browser:
        await browser.start()
        page = await browser.get_page()
        await page.go_to('https://example.com')

asyncio.run(main())
```

## 🎯 Core Components

Pydoll offers three main interfaces for browser automation:

### Browser Interface

The Browser interface provides global control over the entire browser instance:

```python
async def browser_demo():
    async with Chrome() as browser:
        await browser.start()
        
        # Create multiple pages
        pages = [await browser.get_page() for _ in range(3)]
        
        # Control the browser window
        await browser.set_window_maximized()
        
        # Manage cookies globally
        await browser.set_cookies([{
            'name': 'session',
            'value': '12345',
            'domain': 'example.com'
        }])
```

#### Key Browser Methods

| Method | Description | Example |
|--------|-------------|---------|
| `async start()` | 🔥 Launch your browser and prepare for automation | `await browser.start()` |
| `async stop()` | 👋 Close the browser gracefully when finished | `await browser.stop()` |
| `async get_page()` | ✨ Get an existing page or create a new one | `page = await browser.get_page()` |
| `async new_page(url='')` | 🆕 Create a new page in the browser | `page_id = await browser.new_page()` |
| `async get_page_by_id(page_id)` | 🔍 Find and control a specific page by ID | `page = await browser.get_page_by_id(id)` |
| `async get_targets()` | 🎯 List all open pages in the browser | `targets = await browser.get_targets()` |
| `async set_window_bounds(bounds)` | 📐 Size and position the browser window | `await browser.set_window_bounds({'width': 1024})` |
| `async set_window_maximized()` | 💪 Maximize the browser window | `await browser.set_window_maximized()` |
| `async get_cookies()` | 🍪 Get all browser cookies | `cookies = await browser.get_cookies()` |
| `async set_cookies(cookies)` | 🧁 Set custom cookies for authentication | `await browser.set_cookies([{...}])` |
| `async delete_all_cookies()` | 🧹 Clear all cookies for a fresh state | `await browser.delete_all_cookies()` |
| `async set_download_path(path)` | 📂 Configure where downloaded files are saved | `await browser.set_download_path('/downloads')` |
| `async connect()` | 🔌 Connect to an existing browser instance | `page = await browser.connect()` |

### Tab Switching & Management

Want to switch between tabs or pages? It's super easy! First, get all your targets:

```python
targets = await browser.get_targets()
```

You'll get something like this:

```python
[
    {
        'targetId': 'F4729A95E0E4F9456BB6A853643518AF', 
        'type': 'page', 
        'title': 'New Tab', 
        'url': 'chrome://newtab/', 
        'attached': False, 
        'canAccessOpener': False, 
        'browserContextId': 'C76015D1F1C690B7BC295E1D81C8935F'
    }, 
    {
        'targetId': '1C44D55BEEE43F44C52D69D8FC5C3685', 
        'type': 'iframe', 
        'title': 'chrome-untrusted://new-tab-page/one-google-bar?paramsencoded=', 
        'url': 'chrome-untrusted://new-tab-page/one-google-bar?paramsencoded=', 
        'attached': False, 
        'canAccessOpener': False, 
        'browserContextId': 'C76015D1F1C690B7BC295E1D81C8935F'
    }
]
```

Then just pick the page you want:

```python
target = next(target for target in targets if target['title'] == 'New Tab')
```

And switch to it:

```python
new_tab_page = await browser.get_page_by_id(target['targetId'])
```

Now you can control this page as if it were the only one open! Switch between tabs effortlessly by keeping references to each page.

### Page Interface

The Page interface lets you control individual browser tabs and interact with web content:

```python
async def page_demo():
    page = await browser.get_page()
    
    # Navigation
    await page.go_to('https://example.com')
    await page.refresh()
    
    # Get page info
    url = await page.current_url
    html = await page.page_source
    
    # Screenshots and PDF
    await page.get_screenshot('screenshot.png')
    await page.print_to_pdf('page.pdf')
    
    # Execute JavaScript
    title = await page.execute_script('return document.title')
```

#### Key Page Methods

| Method | Description | Example |
|--------|-------------|---------|
| `async go_to(url, timeout=300)` | 🚀 Navigate to a URL with loading detection | `await page.go_to('https://example.com')` |
| `async refresh()` | 🔄 Reload the current page | `await page.refresh()` |
| `async close()` | 🚪 Close the current tab | `await page.close()` |
| `async current_url` | 🧭 Get the current page URL | `url = await page.current_url` |
| `async page_source` | 📝 Get the page's HTML content | `html = await page.page_source` |
| `async get_screenshot(path)` | 📸 Save a screenshot of the page | `await page.get_screenshot('shot.png')` |
| `async print_to_pdf(path)` | 📄 Convert the page to a PDF document | `await page.print_to_pdf('page.pdf')` |
| `async has_dialog()` | 🔔 Check if a dialog is present | `if await page.has_dialog():` |
| `async accept_dialog()` | 👍 Dismiss alert and confirmation dialogs | `await page.accept_dialog()` |
| `async execute_script(script, element)` | ⚡ Run JavaScript code on the page | `await page.execute_script('alert("Hi!")')` |
| `async get_network_logs(matches=[])` | 🕸️ Monitor network requests | `logs = await page.get_network_logs()` |
| `async find_element(by, value)` | 🔎 Find an element on the page | `el = await page.find_element(By.ID, 'btn')` |
| `async find_elements(by, value)` | 🔍 Find multiple elements matching a selector | `items = await page.find_elements(By.CSS, 'li')` |
| `async wait_element(by, value, timeout=10)` | ⏳ Wait for an element to appear | `await page.wait_element(By.ID, 'loaded', 5)` |
| `async expect_and_bypass_cloudflare_captcha(custom_selector=None, time_before_click=2, time_to_wait_captcha=5)` | 🛡️ Context manager that waits for captcha to be solved | `async with page.expect_and_bypass_cloudflare_captcha():` |
| `async enable_auto_solve_cloudflare_captcha(custom_selector=None, time_before_click=2, time_to_wait_captcha=5)` | 🤖 Enable automatic Cloudflare captcha solving | `await page.enable_auto_solve_cloudflare_captcha()` |
| `async disable_auto_solve_cloudflare_captcha()` | 🔌 Disable automatic Cloudflare captcha solving | `await page.disable_auto_solve_cloudflare_captcha()` |

### WebElement Interface

The WebElement interface provides methods to interact with DOM elements:

```python
async def element_demo():
    # Find elements
    button = await page.find_element(By.CSS_SELECTOR, 'button.submit')
    input_field = await page.find_element(By.ID, 'username')
    
    # Get properties
    button_text = await button.get_element_text()
    is_button_enabled = button.is_enabled
    input_value = input_field.value
    
    # Interact with elements
    await button.scroll_into_view()
    await input_field.type_keys("user123")
    await button.click()
```

#### Key WebElement Methods

| Method | Description | Example |
|--------|-------------|---------|
| `value` | 💬 Get the value of an input element | `value = input_field.value` |
| `class_name` | 🎨 Get the element's CSS classes | `classes = element.class_name` |
| `id` | 🏷️ Get the element's ID attribute | `id = element.id` |
| `is_enabled` | ✅ Check if the element is enabled | `if button.is_enabled:` |
| `async bounds` | 📏 Get the element's position and size | `coords = await element.bounds` |
| `async inner_html` | 🧩 Get the element's inner HTML content | `html = await element.inner_html` |
| `async get_element_text()` | 📜 Get the element's text content | `text = await element.get_element_text()` |
| `get_attribute(name)` | 📊 Get any attribute from the element | `href = link.get_attribute('href')` |
| `async scroll_into_view()` | 👁️ Scroll the element into viewport | `await element.scroll_into_view()` |
| `async click(x_offset=0, y_offset=0)` | 👆 Click the element with optional offsets | `await button.click()` |
| `async click_using_js()` | 🔮 Click using JavaScript for hidden elements | `await overlay_button.click_using_js()` |
| `async send_keys(text)` | ⌨️ Send text to input fields | `await input.send_keys("text")` |
| `async type_keys(text, interval=0.1)` | 👨‍💻 Type text with realistic timing | `await input.type_keys("hello", 0.2)` |
| `async get_screenshot(path)` | 📷 Take a screenshot of the element | `await error.get_screenshot('error.png')` |
| `async set_input_files(files)` | 📤 Upload files with file inputs | `await input.set_input_files('file.pdf')` |

## 🚀 Advanced Features

### Event System

Pydoll's powerful event system lets you react to browser events in real-time:

```python
from pydoll.events.page import PageEvents
from pydoll.events.network import NetworkEvents
from functools import partial

# Page navigation events
async def on_page_loaded(event):
    print(f"🌐 Page loaded: {event['params'].get('url')}")

await page.enable_page_events()
await page.on(PageEvents.PAGE_LOADED, on_page_loaded)

# Network request monitoring
async def on_request(page, event):
    url = event['params']['request']['url']
    print(f"🔄 Request to: {url}")

await page.enable_network_events()
await page.on(NetworkEvents.REQUEST_WILL_BE_SENT, partial(on_request, page))

# DOM change monitoring
from pydoll.events.dom import DomEvents
await page.enable_dom_events()
await page.on(DomEvents.DOCUMENT_UPDATED, lambda e: print("DOM updated!"))
```

### Request Interception

Pydoll gives you the power to intercept and modify network requests before they're sent! This allows you to customize headers or modify request data on the fly.

#### Basic Request Modification

The request interception system lets you monitor and modify requests before they're sent:

```python
from pydoll.events.fetch import FetchEvents
from pydoll.commands.fetch import FetchCommands
from functools import partial

async def request_interceptor(page, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    
    print(f"🔎 Intercepted request to: {url}")
    
    # Continue the request normally
    await page._execute_command(
        FetchCommands.continue_request(
            request_id=request_id
        )
    )

# Enable interception and register your handler
await page.enable_fetch_events()
await page.on(FetchEvents.REQUEST_PAUSED, partial(request_interceptor, page))
```

#### Adding Custom Headers

Inject authentication or tracking headers into specific requests:

```python
async def auth_header_interceptor(page, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    
    # Only add auth headers to API requests
    if '/api/' in url:
        # Get the original headers
        original_headers = event['params']['request'].get('headers', {})
        
        # Add your custom headers
        custom_headers = {
            **original_headers,
            'Authorization': 'Bearer your-token-123',
            'X-Custom-Track': 'pydoll-automation'
        }
        
        await page._execute_command(
            FetchCommands.continue_request(
                request_id=request_id,
                headers=custom_headers
            )
        )
    else:
        # Continue normally for non-API requests
        await page._execute_command(
            FetchCommands.continue_request(
                request_id=request_id
            )
        )

await page.enable_fetch_events()
await page.on(FetchEvents.REQUEST_PAUSED, partial(auth_header_interceptor, page))
```

#### Modifying Request Body

Change POST data before it's sent:

```python
async def modify_request_body(page, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    method = event['params']['request'].get('method', '')
    
    # Only modify POST requests to specific endpoints
    if method == 'POST' and 'submit-form' in url:
        # Get original request body if it exists
        original_body = event['params']['request'].get('postData', '{}')
        
        # In a real scenario, you'd parse and modify the body
        # For this example, we're just replacing it
        new_body = '{"modified": true, "data": "enhanced-by-pydoll"}'
        
        print(f"✏️ Modifying POST request to: {url}")
        await page._execute_command(
            FetchCommands.continue_request(
                request_id=request_id,
                post_data=new_body
            )
        )
    else:
        # Continue normally for other requests
        await page._execute_command(
            FetchCommands.continue_request(
                request_id=request_id
            )
        )

await page.enable_fetch_events()
await page.on(FetchEvents.REQUEST_PAUSED, partial(modify_request_body, page))
```

### Filtering Request Types

You can focus on specific types of requests to intercept:

```python
# Just intercept XHR requests
await page.enable_fetch_events(resource_type='xhr')

# Or focus on document requests
await page.enable_fetch_events(resource_type='document')

# Or maybe just images
await page.enable_fetch_events(resource_type='image')
```

Available resource types include: `document`, `stylesheet`, `image`, `media`, `font`, `script`, `texttrack`, `xhr`, `fetch`, `eventsource`, `websocket`, `manifest`, `other`.

### Concurrent Automation

Process multiple pages simultaneously for maximum efficiency:

```python
async def process_page(url):
    page = await browser.get_page()
    await page.go_to(url)
    # Do your scraping or automation here
    return await page.get_element_text()

# Process multiple URLs concurrently
urls = ['https://example1.com', 'https://example2.com', 'https://example3.com']
results = await asyncio.gather(*(process_page(url) for url in urls))
```

## 💡 Best Practices

Maximize your Pydoll experience with these tips:

✅ **Embrace async patterns** throughout your code for best performance  
✅ **Use specific selectors** (IDs, unique attributes) for reliable element finding  
✅ **Implement proper error handling** with try/except blocks around critical operations  
✅ **Leverage the event system** instead of polling for state changes  
✅ **Properly close resources** with async context managers  
✅ **Wait for elements** instead of fixed sleep delays  
✅ **Use realistic interactions** like `type_keys()` to avoid detection  

## 🤝 Contributing

We'd love your help making Pydoll even better! Check out our [contribution guidelines](CONTRIBUTING.md) to get started. Whether it's fixing bugs, adding features, or improving documentation - all contributions are welcome!

Please make sure to:
- Write tests for new features or bug fixes
- Follow coding style and conventions
- Use conventional commits for pull requests
- Run lint and test checks before submitting

## 🔮 Coming Soon

Get ready for these upcoming features in Pydoll:

🔹 **Proxy Rotation** - Seamless IP switching for extended scraping sessions  
🔹 **Shadow DOM Access** - Navigate and interact with Shadow Root elements  

Stay tuned and star the repository to get updates when these features are released!

## 📞 Professional Support

Need specialized help with your automation projects? I offer professional services for those who need:

- 🔧 **Custom Integration** - Integrate Pydoll into your existing systems
- 🚀 **Performance Optimization** - Make your automation scripts faster and more reliable
- 🛡️ **Bypass Solutions** - Help with complex captcha or anti-bot challenges
- 🎓 **Training & Consultation** - Learn advanced techniques and best practices
- 💼 **Enterprise Support** - Priority assistance for business-critical applications

### Contact:
- Telegram: [@thalissonvs](https://t.me/thalissonvs)
- LinkedIn: [Thalison Fernandes](https://www.linkedin.com/in/thalison-fernandes/)

## 📄 License

Pydoll is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <b>Pydoll</b> — Making browser automation magical! ✨
</p>
