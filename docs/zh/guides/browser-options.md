# 浏览器选项

`ChromiumOptions` 是你在启动浏览器之前配置的对象。它保存命令行 flag、要运行的浏览器二进制文件、超时设置，以及一小组便捷设置。你构建一个这样的对象，把它传给 `Chrome` 或 `Edge`，然后启动。

## 配置并启动

创建一个 `ChromiumOptions`，设置你需要的项，然后把它交给浏览器：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.headless = True
    options.add_argument('--window-size=1920,1080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

asyncio.run(main())
```

同一个 options 对象也适用于 Edge；把 `Chrome` 换成导入 `Edge` 即可。

## 添加命令行 flag

Chromium 接受数百个命令行开关。用 `add_argument()` 传入其中任何一个，用 `remove_argument()` 撤回某个，用 `arguments` 读取当前列表。

```python
options = ChromiumOptions()

options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')

options.remove_argument('--start-maximized')
print(options.arguments)
```

完整的开关列表见 Peter Beverloo 的 [Chromium 命令行开关](https://peter.sh/experiments/chromium-command-line-switches/)。几个经常用到的：`--window-size=W,H` 用于固定视口，`--disable-gpu` 用于没有 GPU 的机器，以及下面的 Docker 组合。

!!! note "不要自己设置调试端口"
    Pydoll 在内部管理 `--remote-debugging-port`。传入你自己的 `--remote-debugging-port` 会与它冲突。

## 以 headless 运行

设置 `headless` 可以在没有可见窗口的情况下运行，这正是你在服务器或 CI 上想要的：

```python
options = ChromiumOptions()
options.headless = True   # 添加 --headless flag
```

!!! warning "headless 是可被检测的"
    headless Chrome 泄露的不止一个 flag：它通过软件光栅器渲染 WebGL、不暴露任何 PDF 插件，还会报告不同的屏幕指标。反机器人系统会检查所有这些。设置 User-Agent 并不能把它藏起来。如果你要自动化那些会对抗机器人的站点，要么以有头模式运行，要么用 [Fingerprint 注入](../stealth/fingerprint-injection.md) 中和这些 headless 信号。

## 使用不同的浏览器构建

把 `binary_location` 指向任意 Chromium 构建（Beta、Canary、Chromium、Brave），而不是系统默认的那个：

```python
options = ChromiumOptions()
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
```

## 为启动预留更长等待时间

`start_timeout` 是 Pydoll 在放弃之前等待浏览器启动的秒数。在慢机器或重型配置文件上把它调高：

```python
options = ChromiumOptions()
options.start_timeout = 20   # 秒，默认 10
```

## 选择导航何时算完成

`page_load_state` 决定 `tab.go_to()` 何时返回。`COMPLETE`（默认）会等待每个资源；`INTERACTIVE` 会在 DOM 就绪后立即返回，当你只读取文本或标记时这样更快。

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE
```

三种状态是 `PageLoadState.COMPLETE`、`PageLoadState.INTERACTIVE` 和 `PageLoadState.LOADING`。

## 设置下载文件夹和语言

两个辅助方法覆盖了最常见的偏好设置，无需触碰原始的偏好设置字典：

```python
options = ChromiumOptions()
options.set_default_download_directory('/home/user/downloads')
options.set_accept_languages('en-US,en;q=0.9')
```

要设置 Chromium 偏好设置中更深的项，请看 [浏览器偏好设置](browser-preferences.md)。

## 让浏览器安静下来

一组布尔属性可以关掉那些妨碍自动化的打扰：

```python
options = ChromiumOptions()
options.block_popups = True
options.block_notifications = True
options.password_manager_enabled = False
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True   # 下载 PDF 而不是打开查看器
```

## 防范 WebRTC IP 泄露

即便在 proxy 后面，WebRTC 也可能暴露你的真实 IP。`webrtc_leak_protection` 会添加那个阻止非 proxy UDP 的 flag：

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
```

当你通过 [proxy](proxies.md) 路由流量时，可以用上它。

## 在 Docker 或 CI 中运行

容器需要两个 flag：`--no-sandbox`（沙箱会与容器隔离冲突）和 `--disable-dev-shm-usage`（容器的 `/dev/shm` 往往很小）。

```python
options = ChromiumOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

!!! warning "`--no-sandbox` 会降低 Chrome 的安全性"
    只在受控环境中使用它（容器、CI runner），并且你信任所加载的页面。在访问不受信任的站点时不要使用它。

## 下一步

- [浏览器偏好设置](browser-preferences.md)：更深层的 Chromium 偏好设置字典。
- [Proxy](proxies.md)：让浏览器的流量经过 proxy。
- [Fingerprint 注入](../stealth/fingerprint-injection.md)：让 headless 表现得像有头，并保持浏览器身份一致。
