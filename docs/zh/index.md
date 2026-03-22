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
- **结构化提取**: 定义 [Pydantic](https://docs.pydantic.dev/) 模型，调用 `tab.extract()`，获取类型化和验证过的数据。无需逐元素手动查询。
- **强类型安全**: 完备的类型系统为复杂自动化场景提供更优IDE支持和更好地预防运行时报错。


准备好开始了吗？以下内容将带您从安装配置、基础使用到高级功能，全面掌握 Pydoll 的最佳实践。

让我们以最优雅的方式，开启您的网页自动化之旅！🚀

## 快速入门

### 1. 有状态自动化与规避

当您需要导航、绕过挑战或与动态UI交互时，Pydoll的命令式API默认以人性化的时序处理一切。

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')

        # 查找元素并以人类般的时序进行交互
        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print("按钮未找到。")
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

### 2. 结构化数据提取

到达目标页面后，切换到声明式引擎。用模型定义您想要的数据，Pydoll会提取它——类型化、验证过、随时可用。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='引用文本')
    author: str = Field(selector='.author', description='作者')
    tags: list[str] = Field(selector='.tag', description='标签')
    year: int | None = Field(selector='.year', description='年份', default=None)

async def extract_quotes():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

        for q in quotes:
            print(f'{q.author}: {q.text}')  # 完全类型化，IDE自动补全
            print(q.tags)                    # list[str]，不是原始元素
            print(q.model_dump_json())       # 内置pydantic序列化

asyncio.run(extract_quotes())
```

模型支持CSS/XPath自动检测、HTML属性提取、自定义转换函数和嵌套模型。

??? note "嵌套模型、转换函数和属性提取"
    ```python
    from datetime import datetime
    from pydoll.extractor import ExtractionModel, Field

    def parse_date(raw: str) -> datetime:
        return datetime.strptime(raw.strip(), '%B %d, %Y')

    class Author(ExtractionModel):
        name: str = Field(selector='.author-title')
        born: datetime = Field(
            selector='.author-born-date',
            transform=parse_date,
        )

    class Article(ExtractionModel):
        title: str = Field(selector='h1')
        url: str = Field(selector='.source-link', attribute='href')
        author: Author = Field(selector='.author-card', description='嵌套模型')

    article = await tab.extract(Article, timeout=5)
    article.author.born.year  # int — 类型在整个链中保持一致
    ```

## 扩展示例：结合两种方式

实际的抓取任务通常结合两种方式：命令式自动化用于导航和绕过挑战，然后声明式提取用于收集结构化数据。

```python
import asyncio
from typing import Optional

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.extractor import ExtractionModel, Field


class GitHubRepo(ExtractionModel):
    name: str = Field(
        selector='[itemprop="name"] a',
        description='仓库名称',
    )
    description: Optional[str] = Field(
        selector='[itemprop="description"]',
        description='仓库描述',
        default=None,
    )
    language: Optional[str] = Field(
        selector='[itemprop="programmingLanguage"]',
        description='主要编程语言',
        default=None,
    )


async def main():
    options = ChromiumOptions()
    options.add_argument('--headless=new')

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        # 1. 导航和交互（命令式）
        await tab.go_to('https://github.com/autoscrape-labs')

        # 2. 提取结构化数据（声明式）
        repos = await tab.extract_all(
            GitHubRepo,
            scope='article.Box-row',
            timeout=10,
        )

        for repo in repos:
            print(f'{repo.name} ({repo.language}): {repo.description}')
            print(repo.model_dump_json())

if __name__ == "__main__":
    asyncio.run(main())
```

此示例演示了：

1. 为GitHub仓库数据定义类型化模型
2. 配置无头模式以实现无痕操作
3. 使用 `extract_all` 一次性收集多个仓库
4. 获取完全类型化的对象，支持IDE自动补全和pydantic序列化

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
websockets = "^14"
aiohttp = "^3.9.5"
aiofiles = "^25.1.0"
pydantic = "^2.0"
typing_extensions = "^4.14.0"
```

这种极简依赖策略带来五大核心优势：  

- **⚡闪电安装** - 无需解析复杂的依赖树
- **🧩 零冲突** - 与其他包发生版本冲突的概率极低
- **📦 轻量化** - 更低的磁盘空间占用
- **🔒 更好的安全** - 更小的攻击面和供应链漏洞
- **🔄 方便升级** - 方便维护已经无破坏性更新

更少的依赖项带来了： 更高的运行可靠性以及更强的性能表现。

## 顶级赞助商

<a href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
  <img src="../resources/images/banner-the-webscraping-club.png" alt="The Web Scraping Club" />
</a>

<sub>在 <b><a href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">The Web Scraping Club</a></b> 上阅读 Pydoll 的完整评测，这是排名第一的网页抓取专属通讯。</sub>

## 赞助商

赞助商的支持对于项目的持续发展至关重要。每一份合作都能帮助我们覆盖基础成本、推动新功能迭代，并保证项目长期维护与更新。非常感谢所有相信并支持 Pydoll 的伙伴！

<div class="sponsors-grid">
  <a href="https://www.thordata.com/?ls=github&lk=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <img src="../resources/images/Thordata-logo.png" alt="Thordata" />
  </a>
  <a href="https://www.testmuai.com/?utm_medium=sponsor&utm_source=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <img src="../resources/images/logo-lamda-test.svg" alt="LambdaTest" />
  </a>
  <a href="https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc" target="_blank" rel="noopener nofollow sponsored">
    <img src="../resources/images/capsolver-logo.png" alt="CapSolver" />
  </a>
</div>

<p>
  <a href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">成为赞助商</a>
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
