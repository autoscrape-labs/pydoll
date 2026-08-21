# 快速开始

Pydoll 自动化你已经安装好的 Chrome 或 Edge，所以配置只有两步：安装包，运行脚本。本页带你从一个空文件夹出发，到一个可运行的脚本，它会打开一个真实页面并从中读取数据。

**你将学到**

- [如何安装 Pydoll](#install-pydoll)
- [如何编写并运行你的第一个脚本](#write-your-first-script)
- [如何在没有可见浏览器窗口的情况下运行](#run-headless)

## 安装 Pydoll {#install-pydoll}

Pydoll 需要 Python 3.10 或更新版本，以及机器上安装的 Google Chrome 或 Microsoft Edge。你无需下载 webdriver；Pydoll 直接与浏览器通信。

创建并激活一个 [虚拟环境](https://docs.python.org/3/tutorial/venv.html)，然后安装：

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

如果想改为尝试最新的开发版本，从 GitHub 安装：

```bash
pip install git+https://github.com/autoscrape-labs/pydoll.git
```

## 编写你的第一个脚本 {#write-your-first-script}

创建一个名为 `first_script.py` 的文件：

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

asyncio.run(main())
```

运行它：

```bash
python first_script.py
```

一个 Chrome 窗口打开，加载页面，你的终端打印出第一条名言：

```
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
```

这里发生了三件事：

- `async with Chrome() as browser` 启动了你已安装的 Chrome，并保证在代码块结束时关闭它，即使脚本失败也是如此。
- `browser.start()` 返回了一个 [tab](api/browser/tab.md)，你将用这个对象来完成导航、元素查找以及页面上的其他一切操作。
- `tab.find(class_name='text')` 等待元素出现并返回它。你无需添加 sleep 或编写等待循环；`find()` 会重试直到元素出现或超时到期。

!!! note "第一次接触异步 Python？"
    每个 Pydoll 调用都在 `async def` 函数内部被 `await`，并由 `asyncio.run(main())` 启动。目前你需要的 asyncio 就这些；文档的其余部分都遵循同样的结构。

## 无头运行 {#run-headless}

在服务器上或在 CI 中没有显示器，因此要以 headless 方式运行浏览器。在创建浏览器时传入选项：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.add_argument('--headless=new')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        first_quote = await tab.find(class_name='text')
        print(await first_quote.text)

asyncio.run(main())
```

脚本行为完全相同；只是窗口不可见。`ChromiumOptions` 接受任意 Chromium 命令行参数。值得了解的参数见 [浏览器选项](guides/browser-options.md)。

!!! warning "headless 是可被检测的"
    headless Chrome 泄露的不只是一个 user agent 字符串。它通过软件光栅化器而非你真实的 GPU 来渲染 WebGL，不暴露任何 PDF 插件，报告的屏幕度量没有任务栏留出的间隙，还缺少媒体设备。反机器人系统会检查所有这些，因此仅仅设置一个 user agent 并不能让 headless 浏览器伪装成 headful，差得很远。如果你自动化那些与机器人对抗的站点，要么以 headful 方式运行，要么用 [Fingerprint 注入](stealth/fingerprint-injection.md) 中和这些 headless 信号。

## 下一步

- [你的第一个自动化](first-automation.md)：登录一个站点，像真人一样交互，并提取类型化数据。
- [保持不被检测](stealth/index.md)：避开明显机器人信号的最小配置。
- [元素查找](guides/element-finding.md)：用 `find()` 和 `query()` 定位元素的每一种方式。
