<p align="center">
    <img src="./images/E2ECED-cinza-azulado.png" alt="Pydoll Logo" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll">
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/> 
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
</p>


# 欢迎使用Pydoll

嗨，开发者大大！欢迎来到 Pydoll 的世界～这是为 Python 量身打造的新一代浏览器自动化神器！受够了 WebDriver 的折磨？想要丝滑又稳如老狗的自动化体验？您可算找对地方啦！

## 什么是Pydoll?

Pydoll采用全新的浏览器自动化技术——完全无需 WebDriver！与其他依赖外部驱动的解决方案不同，Pydoll 通过浏览器原生 DevTools 协议直接通信，提供零依赖的自动化体验，并自带原生异步高性能支持。

无论是数据采集、Web应用测试，还是自动化重复任务，Pydoll 都能通过其直观的 API 和强大功能，让这些工作变得异常简单。  

## 安装

创建并激活一个 [虚拟环境](https://docs.python.org/3/tutorial/venv.html)，然后安装Pydoll:

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

你可以直接在GitHub上找到最新的开发版本:

```bash
$ pip install git+https://github.com/autoscrape-labs/pydoll.git
```

## 为何选择Pydoll?

- **智能验证码绕过**: 内置Cloudflare Turnstile与reCAPTCHA v3验证码的自动破解能力，无需依赖外部服务、API密钥或复杂配置。即使遭遇防护系统，您的自动化流程仍可畅行无阻。
- **模拟真人交互**: 通过先进算法模拟真实人类行为特征——通过随机操作间隔，到鼠标移动轨迹、页面滚动模式乃至输入速度，皆可骗过最严苛的反爬虫系统。
- **极简哲学**: 无需浪费太多时间在配置驱动或解决兼容问题上。Pydoll开箱即用。
- **原生异步性能**: 基于`asyncio`库深度设计, Pydoll不仅支持异步操作——更为高并发而生，可同时进行多个受防护站点的数据采集。
- **强大的网络监控**: 轻松实现请求拦截、流量篡改与响应分析，完整掌控网络通信链路，轻松突破层层防护体系。
- **事件驱动架构**: 实时响应页面事件、网络请求与用户交互，构建能动态适应防护系统的智能自动化流。
- **直观的元素定位**: 使用符合人类直觉的定位方法 `find()` 和 `query()` ，面对动态加载的防护内容，定位依然精准。
- **强类型安全**: 完备的类型系统为复杂自动化场景提供更优IDE支持和更好地预防运行时报错。


准备好开始了吗？以下内容将带您从安装配置、基础使用到高级功能，全面掌握 Pydoll 的最佳实践。

让我们以最优雅的方式，开启您的网页自动化之旅！🚀

## 简单的例子快速上手

让我们从一个实际案例开始。以下脚本将打开 Pydoll 的 GitHub 仓库并star：  

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')
        
        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print("Ops! The button was not found.")
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

This example demonstrates how to navigate to a website, wait for an element to appear, and interact with it. You can adapt this pattern to automate many different web tasks.

??? note "Or use without context manager..."
    If you prefer not to use the context manager pattern, you can manually manage the browser instance:
    
    ```python
    import asyncio
    from pydoll.browser.chromium import Chrome
    
    async def main():
        browser = Chrome()
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')
        
        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print("Ops! The button was not found.")
            return

        await star_button.click()
        await asyncio.sleep(3)
        await browser.stop()
    
    asyncio.run(main())
    ```
    
    Note that when not using the context manager, you'll need to explicitly call `browser.stop()` to release resources.

## Extended Example: Custom Browser Configuration

For more advanced usage scenarios, Pydoll allows you to customize your browser configuration using the `ChromiumOptions` class. This is useful when you need to:

- Run in headless mode (no visible browser window)
- Specify a custom browser executable path
- Configure proxies, user agents, or other browser settings
- Set window dimensions or startup arguments

Here's an example showing how to use custom options for Chrome:

```python hl_lines="8-12 30-32 34-38"
import asyncio
import os
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def main():
    options = ChromiumOptions()
    options.binary_location = '/usr/bin/google-chrome-stable'
    options.add_argument('--headless=new')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')
        
        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print("Ops! The button was not found.")
            return

        await star_button.click()
        await asyncio.sleep(3)

        screenshot_path = os.path.join(os.getcwd(), 'pydoll_repo.png')
        await tab.take_screenshot(path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")

        base64_screenshot = await tab.take_screenshot(as_base64=True)

        repo_description_element = await tab.find(
            class_name='f4.my-3'
        )
        repo_description = await repo_description_element.text
        print(f"Repository description: {repo_description}")

if __name__ == "__main__":
    asyncio.run(main())
```

This extended example demonstrates:

1. Creating and configuring browser options
2. Setting a custom Chrome binary path
3. Enabling headless mode for invisible operation
4. Setting additional browser flags
5. Taking screenshots (especially useful in headless mode)

??? info "About Chromium Options"
    The `options.add_argument()` method allows you to pass any Chromium command-line argument to customize browser behavior. There are hundreds of available options to control everything from networking to rendering behavior.
    
    Common Chrome Options
    
    ```python
    # Performance & Behavior Options
    options.add_argument('--headless=new')         # Run Chrome in headless mode
    options.add_argument('--disable-gpu')          # Disable GPU hardware acceleration
    options.add_argument('--no-sandbox')           # Disable sandbox (use with caution)
    options.add_argument('--disable-dev-shm-usage') # Overcome limited resource issues
    
    # Appearance Options
    options.add_argument('--start-maximized')      # Start with maximized window
    options.add_argument('--window-size=1920,1080') # Set specific window size
    options.add_argument('--hide-scrollbars')      # Hide scrollbars
    
    # Network Options
    options.add_argument('--proxy-server=socks5://127.0.0.1:9050') # Use proxy
    options.add_argument('--disable-extensions')   # Disable extensions
    options.add_argument('--disable-notifications') # Disable notifications
    
    # Privacy & Security
    options.add_argument('--incognito')            # Run in incognito mode
    options.add_argument('--disable-infobars')     # Disable infobars
    ```
    
    Complete Reference Guides
    
    For a comprehensive list of all available Chrome command-line arguments, refer to these resources:
    
    - [Chromium Command Line Switches](https://peter.sh/experiments/chromium-command-line-switches/) - Complete reference list
    - [Chrome Flags](chrome://flags) - Enter this in your Chrome browser address bar to see experimental features
    - [Chromium Source Code Flags](https://source.chromium.org/chromium/chromium/src/+/main:chrome/common/chrome_switches.cc) - Direct source code reference
    
    Remember that some options may behave differently across Chrome versions, so it's a good practice to test your configuration when upgrading Chrome.

With these configurations, you can run Pydoll in various environments, including CI/CD pipelines, servers without displays, or Docker containers.

Continue reading the documentation to explore Pydoll's powerful features for handling captchas, working with multiple tabs, interacting with elements, and more.

## 极简依赖

Pydoll 的优势之一是其轻量级的占用空间。与其他需要大量依赖项的浏览器自动化工具不同，Pydoll 在保留了强大的功能的同时力求精简。  

### 核心依赖

Pydoll仅依赖少量的核心库：  

```
python = "^3.10"
websockets = "^13.1"
aiohttp = "^3.9.5"
aiofiles = "^23.2.1"
bs4 = "^0.0.2"
```

这种极简依赖策略带来五大核心优势：  

- **⚡闪电安装** - 无需解析复杂的依赖树
- **🧩 零冲突** - 与其他包发生版本冲突的概率极低
- **📦 轻量化** - 更低的磁盘空间占用
- **🔒 更好的安全** - 更小的攻击面和供应链漏洞
- **🔄 方便升级** - 方便维护已经无破坏性更新

更少的依赖项带来了： 更高的运行可靠性以及更强的性能表现。

## 许可证

Pydoll 遵循 MIT 许可证（完整文本见 LICENSE 文件），主要授权条款包括：  

1. 权利授予  
   - 永久、全球范围、免版税的使用权  
   - 允许修改创作衍生作品  
   - 可再授权给第三方  

2. 唯一责任限制  
   - 所有修改件必须保留原版权声明  
   - 不提供任何明示或默示担保  

??? info "View Full MIT License Text"
    ```
    MIT License
    
    Copyright (c) 2023 Pydoll Contributors
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    ```
