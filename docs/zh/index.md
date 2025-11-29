<p align="center">
    <img src="../resources/images/logo.png" alt="Pydoll Logo" /> <br><br>
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

欢迎来到 Pydoll 的世界～这是为 Python 量身打造的新一代浏览器自动化神器！

## 什么是Pydoll?

Pydoll采用全新的浏览器自动化技术——完全无需 WebDriver！与其他依赖外部驱动的解决方案不同，Pydoll 通过浏览器原生 DevTools 协议直接通信，提供零依赖的自动化体验，并自带原生异步高性能支持。

无论是数据采集、[Web应用测试](https://www.lambdatest.com/web-testing)，还是自动化重复任务，Pydoll 都能通过其直观的 API 和强大功能，让这些工作变得异常简单。  

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

## 简单的例子上手

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

此示例演示了如何导航到网站、等待元素出现并与之交互。您可以使用这样的模式来自动执行许多不同的 Web 任务。

??? note "或者使用不带上下文管理器的..."
    如果你不想要使用上下文管理器模式，你可以手动管理浏览器实例：
    
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

## 补充例子: 自定义浏览器配置

对于更高级的使用场景，Pydoll 允许您使用 `ChromiumOptions` 类自定义浏览器配置。此功能在您需要执行以下操作时非常有用：

- 在无头模式下运行（无可见浏览器窗口）
- 指定自定义浏览器可执行文件路径
- 配置代理、用户代理或其他浏览器设置
- 设置窗口尺寸或启动参数

以下示例展示了如何使用 Chrome 的自定义选项：

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


此扩展示例演示了：

1. 创建和配置浏览器选项
2. 设置自定义Chrome可执行程序路径
3. 启用无头模式以实现无痕操作
4. 设置其他浏览器命令行flags
5. 屏幕截图（在无头模式下尤其有用）

??? info "关于Chrome配置选项"
    The `options.add_argument()` 方法允许您传递任何 Chromium 命令行参数来自定义浏览器行为。有数百个可用选项可用于控制从网络到渲染行为的所有内容。

    常用Chrome配置选项
    
    ```python
    # 性能与行为选项
    options.add_argument('--headless=new')         # 以无头模式运行Chrome
    options.add_argument('--disable-gpu')          # 禁用GPU加速
    options.add_argument('--no-sandbox')           # 禁用沙盒模式（需谨慎使用）
    options.add_argument('--disable-dev-shm-usage') # 解决资源限制问题
    
    # 界面显示选项
    options.add_argument('--start-maximized')      # 以最大化窗口启动
    options.add_argument('--window-size=1920,1080') # 设置特定窗口尺寸
    options.add_argument('--hide-scrollbars')      # 隐藏滚动条
    
    # 网络选项
    options.add_argument('--proxy-server=socks5://127.0.0.1:9050') # 使用代理服务器
    options.add_argument('--disable-extensions')   # 禁用扩展程序
    options.add_argument('--disable-notifications') # 禁用通知
    
    # 隐私与安全
    options.add_argument('--incognito')            # 以隐身模式运行
    options.add_argument('--disable-infobars')     # 禁用信息栏
    ```
    
    完整参考指南
    
    如需获取所有可用的Chrome命令行参数完整列表，请参考以下资源：
    
    - [Chromium Command Line Switches](https://peter.sh/experiments/chromium-command-line-switches/) - Complete reference list
    - [Chrome Flags](chrome://flags) - Enter this in your Chrome browser address bar to see experimental features
    - [Chromium Source Code Flags](https://source.chromium.org/chromium/chromium/src/+/main:chrome/common/chrome_switches.cc) - Direct source code reference
    
    请注意某些选项在不同Chrome版本中可能有差异表现，建议在升级Chrome时测试您的配置。

通过这些配置，您可以在各种环境中运行 Pydoll，包括 CI/CD 流水线、无显示器的服务器或 Docker 容器。

继续阅读文档，探索 Pydoll 在处理验证码、处理多个标签页、与元素交互等方面的强大功能。

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

## 赞助商

赞助商的支持对于项目的持续发展至关重要。每一份合作都能帮助我们覆盖基础成本、推动新功能迭代，并保证项目长期维护与更新。非常感谢所有相信并支持 Pydoll 的伙伴！

<a href="https://www.lambdatest.com/?utm_source=pydoll&utm_medium=sponsor" target="_blank" rel="noopener nofollow sponsored">
  <img src="https://www.lambdatest.com/blue-logo.png" alt="LambdaTest" width="200" height="45" />
  
</a>

<p>
  <a href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener" style="display:inline-block;padding:6px 10px;border:1px solid #94a3b8;border-radius:6px;text-decoration:none;color:#e2e8f0;background:#0f172a;">成为赞助商</a>
</p>

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
