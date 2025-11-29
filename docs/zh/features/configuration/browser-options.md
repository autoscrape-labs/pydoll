# 浏览器选项 (ChromiumOptions)

`ChromiumOptions` 是自定义浏览器行为的中央配置中心。它控制从命令行参数和二进制文件位置到页面加载状态和内容偏好的所有内容。

!!! info "相关文档"
    - **[浏览器偏好设置](browser-preferences.md)** - 深入了解 Chromium 的内部偏好系统
    - **[浏览器管理](../browser-management/tabs.md)** - 使用浏览器实例和标签页
    - **[上下文](../browser-management/contexts.md)** - 隔离的浏览上下文

## 快速入门

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def main():
    # 创建并配置选项
    options = ChromiumOptions()
    
    # 基本配置
    options.headless = True
    options.start_timeout = 15
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # 添加命令行参数
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # 常见设置的辅助方法
    options.block_notifications = True
    options.block_popups = True
    options.set_default_download_directory('/tmp/downloads')
    
    # 使用配置的选项
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(main())
```

## 核心属性

### 命令行参数

Chromium 支持数百个控制浏览器行为的命令行开关。使用 `add_argument()` 直接将标志传递给浏览器进程。

```python
options = ChromiumOptions()

# 添加单个参数
options.add_argument('--disable-blink-features=AutomationControlled')

# 添加带值的参数
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 ...')

# 如需要可删除参数
options.remove_argument('--window-size=1920,1080')

# 获取所有参数
all_args = options.arguments
```

!!! tip "参数格式"
    - 以 `--` 开头的参数是标志：`--headless`、`--disable-gpu`
    - 带 `=` 的参数有值：`--window-size=1920,1080`
    - 有些接受多个值：`--disable-features=Feature1,Feature2`

**请参阅下面的[命令行参数参考](#命令行参数参考)获取完整列表。**

### 二进制文件位置

指定自定义浏览器可执行文件而不是使用系统默认值：

```python
options = ChromiumOptions()

# Linux
options.binary_location = '/opt/google/chrome-beta/chrome'

# macOS
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

# Windows
options.binary_location = r'C:\Program Files\Google\Chrome Beta\Application\chrome.exe'
```

!!! info "何时设置二进制位置"
    - 测试不同的 Chrome 版本（Stable、Beta、Canary）
    - 使用 Chromium 而不是 Chrome
    - 使用便携式浏览器安装
    - 运行特定构建进行调试

### 启动超时

控制 Pydoll 等待浏览器启动和响应的时间：

```python
options = ChromiumOptions()
options.start_timeout = 20  # 秒（默认：10）
```

!!! warning "超时注意事项"
    - **太低**：浏览器可能无法完全初始化，导致启动失败
    - **太高**：挂起会阻塞您的自动化更长时间
    - **推荐**：大多数情况下 10-15 秒，慢速系统或大型浏览器配置文件 20-30 秒

### 无头模式

在没有可见 UI 的情况下运行浏览器：

```python
options = ChromiumOptions()
options.headless = True  # 自动添加 --headless 参数

# 或手动
options.add_argument('--headless')
options.add_argument('--headless=new')  # 新的无头模式（Chrome 109+）
```

| 模式 | 参数 | 描述 |
|------|----------|-------------|
| **有头** | (无) | 可见的浏览器窗口（默认）|
| **经典无头** | `--headless` | 旧版无头模式 |
| **新无头** | `--headless=new` | 现代无头（Chrome 109+，更好的兼容性）|

!!! tip "新无头模式"
    `--headless=new` 模式（Chrome 109+）提供更好的现代 Web 功能兼容性，更难检测。在生产自动化中使用它。

### 页面加载状态

控制 `tab.go_to()` 何时认为页面"已加载"：

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE  # 或 PageLoadState.COMPLETE
```

| 状态 | 导航完成时 | 用例 |
|-------|---------------------------|----------|
| `COMPLETE`（默认）| 触发 `load` 事件，所有资源已加载 | 等待图像、字体、脚本 |
| `INTERACTIVE` | 触发 `DOMContentLoaded`，DOM 就绪 | 更快的导航，立即与 DOM 交互 |

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def compare_load_states():
    # 完整模式 - 等待所有内容
    options_complete = ChromiumOptions()
    options_complete.page_load_state = PageLoadState.COMPLETE
    
    async with Chrome(options=options_complete) as browser:
        tab = await browser.start()
        
        import time
        start = time.time()
        await tab.go_to('https://example.com')
        complete_time = time.time() - start
        print(f"COMPLETE 模式: {complete_time:.2f}s")
    
    # 交互模式 - DOM 就绪就足够了
    options_interactive = ChromiumOptions()
    options_interactive.page_load_state = PageLoadState.INTERACTIVE
    
    async with Chrome(options=options_interactive) as browser:
        tab = await browser.start()
        
        start = time.time()
        await tab.go_to('https://example.com')
        interactive_time = time.time() - start
        print(f"INTERACTIVE 模式: {interactive_time:.2f}s")

asyncio.run(compare_load_states())
```

!!! tip "何时使用 INTERACTIVE"
    在以下情况使用 `INTERACTIVE`：
    
    - 只需要访问 DOM，不需要图像/字体
    - 抓取文本内容和结构
    - 速度至关重要
    - 页面有许多加载缓慢的资源
    
    在以下情况坚持使用 `COMPLETE`（默认）：
    
    - 截图（需要加载图像）
    - 等待 JavaScript 重型应用完全初始化
    - 测试页面加载性能

## 命令行参数参考

Chromium 支持数百个命令行开关。以下是自动化最有用的参数，按类别组织。

!!! info "完整参考"
    所有 Chromium 开关的完整列表：[Peter Beverloo 的 Chromium 命令行开关](https://peter.sh/experiments/chromium-command-line-switches/)

### 性能和资源管理

优化浏览器性能以加快自动化：

```python
options = ChromiumOptions()

# 禁用 GPU 加速（无头、Docker、CI/CD）
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

# 减少内存使用
options.add_argument('--disable-dev-shm-usage')  # Docker：克服 /dev/shm 大小限制
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')

# 禁用不必要的功能
options.add_argument('--disable-sync')  # Google 账户同步
options.add_argument('--disable-translate')
options.add_argument('--disable-background-timer-throttling')
options.add_argument('--disable-backgrounding-occluded-windows')
options.add_argument('--disable-renderer-backgrounding')

# 网络优化
options.add_argument('--disable-features=NetworkPrediction')
options.add_argument('--dns-prefetch-disable')

# 窗口和渲染
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--force-device-scale-factor=1')
```

| 参数 | 效果 | 何时使用 |
|----------|--------|-------------|
| `--disable-gpu` | 无 GPU 加速 | 无头、Docker、没有 GPU 的服务器 |
| `--disable-dev-shm-usage` | 使用 `/tmp` 而不是 `/dev/shm` | 共享内存小的 Docker 容器 |
| `--disable-extensions` | 不加载任何扩展 | 用于自动化的干净、快速的浏览器 |
| `--window-size=W,H` | 设置初始窗口尺寸 | 截图、一致的视口 |
| `--force-device-scale-factor=1` | 禁用高 DPI 缩放 | 跨系统一致渲染 |

### 隐蔽和指纹识别

使用这些命令行参数使您的自动化更难被检测：

| 参数 | 目的 | 示例 |
|----------|---------|---------|
| `--disable-blink-features=AutomationControlled` | 删除 `navigator.webdriver` 标志 | 隐蔽性必不可少 |
| `--user-agent=...` | 设置真实、常见的用户代理 | 匹配目标区域/设备 |
| `--use-gl=swiftshader` | 软件 WebGL 渲染器 | 避免独特的 GPU 指纹 |
| `--force-webrtc-ip-handling-policy=...` | 防止 WebRTC IP 泄露 | 使用 `disable_non_proxied_udp` |
| `--lang=en-US` | 设置浏览器语言 | 匹配目标区域 |
| `--accept-lang=en-US,en;q=0.9` | Accept-Language 标头 | 真实的语言偏好 |
| `--tz=America/New_York` | 设置时区 | 匹配目标区域 |
| `--no-first-run` | 跳过首次运行向导 | 更干净的自动化 |
| `--no-default-browser-check` | 跳过默认浏览器提示 | 避免 UI 中断 |
| `--disable-reading-from-canvas` | Canvas 指纹识别缓解 | 减少独特性 |
| `--disable-features=AudioServiceOutOfProcess` | 音频指纹识别缓解 | 减少独特性 |

!!! warning "检测军备竞赛"
    没有单一技术能保证不可检测性。结合多种策略：
    
    1. **命令行参数**（此表）
    2. **浏览器偏好设置** - [浏览器偏好设置 - 隐蔽和指纹识别](browser-preferences.md#stealth-fingerprinting)
    3. **类人交互** - [类人交互](../automation/human-interactions.md)
    4. **良好的 IP 声誉** - 使用历史干净的住宅代理

### 安全和隐私

控制安全功能和隐私设置：

```python
options = ChromiumOptions()

# 沙箱（仅在 Docker/CI 中禁用）
options.add_argument('--no-sandbox')  # 安全风险 - 仅在受控环境中使用
options.add_argument('--disable-setuid-sandbox')

# HTTPS/SSL
options.add_argument('--ignore-certificate-errors')  # 忽略 SSL 错误
options.add_argument('--ignore-ssl-errors')
options.add_argument('--allow-insecure-localhost')

# 隐私
options.add_argument('--disable-features=Translate')
options.add_argument('--disable-sync')
options.add_argument('--incognito')  # 在隐身模式下打开

# 权限自动授予（用于测试）
options.add_argument('--use-fake-ui-for-media-stream')  # 自动授予摄像头/麦克风
options.add_argument('--use-fake-device-for-media-stream')  # 使用假设备
```

!!! danger "沙箱警告"
    **`--no-sandbox` 是安全风险！** 仅在以下情况使用：
    
    - 在 Docker 容器中运行（沙箱与容器隔离冲突）
    - 具有受限权限的 CI/CD 环境
    - 您完全信任正在加载的内容
    
    **永远不要**在以下情况使用 `--no-sandbox`：
    
    - 访问不受信任的网站
    - 运行用户提交的代码
    - 在具有外部输入的生产环境中

| 参数 | 效果 | 安全影响 |
|----------|--------|-----------------|
| `--no-sandbox` | 禁用 Chrome 沙箱 | **高风险** - 允许代码执行 |
| `--ignore-certificate-errors` | 跳过 SSL 验证 | **中等风险** - 可能发生 MITM 攻击 |
| `--incognito` | 隐私浏览模式 | 更安全 - 没有持久状态 |

### 调试和开发

用于调试自动化和开发的工具：

```python
options = ChromiumOptions()

# DevTools
options.add_argument('--auto-open-devtools-for-tabs')

# 日志记录
options.add_argument('--enable-logging')
options.add_argument('--v=1')  # 详细级别（0-3）
options.add_argument('--log-level=0')  # 0=INFO, 1=WARNING, 2=ERROR

# 崩溃处理
options.add_argument('--disable-crash-reporter')
options.add_argument('--no-crash-upload')

# 启用实验性功能
options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
options.add_argument('--enable-experimental-web-platform-features')

# JavaScript 调试
options.add_argument('--js-flags=--expose-gc')  # 公开垃圾收集器
```

!!! tip "远程调试"
    Pydoll 自动管理远程调试端口。要访问 Chrome DevTools：
    
    ```python
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 获取调试端口
        port = browser._connection_port
        print(f"DevTools 可用于: http://localhost:{port}")
        
        # 在浏览器中打开此 URL 以访问 DevTools
    ```
    
    **不要**使用 `--remote-debugging-port` 参数 - 它会与 Pydoll 的内部管理冲突！

### 显示和渲染

控制浏览器如何渲染内容：

```python
options = ChromiumOptions()

# 视口和窗口
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--start-maximized')
options.add_argument('--start-fullscreen')

# 高 DPI 显示器
options.add_argument('--force-device-scale-factor=1')
options.add_argument('--high-dpi-support=1')

# 颜色和渲染
options.add_argument('--force-color-profile=srgb')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-accelerated-video-decode')

# 字体渲染
options.add_argument('--font-render-hinting=none')
options.add_argument('--disable-font-subpixel-positioning')

# 动画
options.add_argument('--disable-animations')
options.add_argument('--wm-window-animations-disabled')
```

| 参数 | 效果 | 用例 |
|----------|--------|----------|
| `--window-size=W,H` | 设置窗口尺寸 | 截图、一致的视口 |
| `--start-maximized` | 打开最大化窗口 | UI 测试、全屏捕获 |
| `--force-device-scale-factor=1` | 禁用 DPI 缩放 | 跨系统一致渲染 |
| `--disable-animations` | 无 CSS/UI 动画 | 更快的测试、减少不稳定 |

### 代理配置

为所有网络流量配置代理：

```python
options = ChromiumOptions()

# HTTP/HTTPS 代理
options.add_argument('--proxy-server=http://proxy.example.com:8080')

# 认证代理
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

# SOCKS 代理
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

# 为特定主机绕过代理
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')

# 代理自动配置（PAC）文件
options.add_argument('--proxy-pac-url=http://proxy.example.com/proxy.pac')
```

!!! info "代理身份验证"
    对于需要身份验证的代理，当使用带凭据的 `--proxy-server` 参数时，Pydoll 会自动处理身份验证挑战。
    
    请参阅 **[请求拦截](../network/interception.md)** 了解 Fetch 域与代理的交互详情。

## 辅助方法

`ChromiumOptions` 为常见配置任务提供便捷方法：

### 下载管理

```python
options = ChromiumOptions()

# 设置下载目录
options.set_default_download_directory('/home/user/downloads')

# 提示下载位置
options.prompt_for_download = True  # 询问用户保存位置
options.prompt_for_download = False  # 静默下载（默认）

# 允许多个自动下载
options.allow_automatic_downloads = True  # 无需提示即允许
options.allow_automatic_downloads = False  # 阻止或询问（默认）
```

### 内容阻止

```python
options = ChromiumOptions()

# 阻止弹出窗口
options.block_popups = True  # 阻止（在大多数情况下为默认）
options.block_popups = False  # 允许

# 阻止通知
options.block_notifications = True  # 阻止请求
options.block_notifications = False  # 允许网站询问
```

### 隐私控制

```python
options = ChromiumOptions()

# 密码管理器
options.password_manager_enabled = False  # 禁用保存密码提示
options.password_manager_enabled = True  # 启用（默认）
```

### 文件处理

```python
options = ChromiumOptions()

# PDF 行为
options.open_pdf_externally = True  # 下载 PDF 而不是查看
options.open_pdf_externally = False  # 在浏览器中查看（默认）
```

### 国际化

```python
options = ChromiumOptions()

# 接受语言（影响 Content-Language 标头）
options.set_accept_languages('en-US,en;q=0.9,pt-BR;q=0.8')
```

## 完整配置示例

### 快速抓取配置

针对速度和资源效率进行优化：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_fast_scraping_options() -> ChromiumOptions:
    """用于 Web 抓取的超快配置。"""
    options = ChromiumOptions()
    
    # 无头模式以提高速度
    options.headless = True
    
    # 更快的页面加载（DOM 就绪足以进行抓取）
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # 禁用不必要的功能
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    
    # 阻止减慢加载速度的内容
    options.block_notifications = True
    options.block_popups = True
    
    # 禁用图像以实现更快的加载（如果不需要）
    options.add_argument('--blink-settings=imagesEnabled=false')
    
    # 网络优化
    options.add_argument('--disable-features=NetworkPrediction')
    options.add_argument('--dns-prefetch-disable')
    
    return options

async def fast_scraping_example():
    options = create_fast_scraping_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 极快的导航和抓取
        urls = ['https://example.com', 'https://example.org', 'https://example.net']
        
        for url in urls:
            await tab.go_to(url)
            title = await tab.execute_script('return document.title')
            print(f"{url}: {title}")

asyncio.run(fast_scraping_example())
```

### 完整隐蔽配置

为了最大的不可检测性，将命令行参数与浏览器偏好设置相结合：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_full_stealth_options() -> ChromiumOptions:
    """结合参数和偏好设置的完整隐蔽配置。"""
    options = ChromiumOptions()
    
    # ===== 命令行参数 =====
    
    # 核心隐蔽
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # 用户代理（使用最新的、常见的）
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    
    # 语言和区域
    options.add_argument('--lang=en-US')
    options.add_argument('--accept-lang=en-US,en;q=0.9')
    
    # WebGL（软件渲染器以避免独特的 GPU 签名）
    options.add_argument('--use-gl=swiftshader')
    options.add_argument('--disable-features=WebGLDraftExtensions')
    
    # WebRTC IP 泄露防护
    options.add_argument('--force-webrtc-ip-handling-policy=disable_non_proxied_udp')
    
    # 权限和首次运行
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    
    # 窗口大小（常见分辨率）
    options.add_argument('--window-size=1920,1080')
    
    # ===== 浏览器偏好设置 =====
    # 有关全面的浏览器偏好设置配置，请参阅：
    # https://pydoll.tech/docs/features/configuration/browser-preferences/#stealth-fingerprinting
    
    return options

async def stealth_automation_example():
    options = create_full_stealth_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 在机器人检测网站上测试
        await tab.go_to('https://bot.sannysoft.com')
        await asyncio.sleep(5)
        
        # 您的自动化在这里...

asyncio.run(stealth_automation_example())
```

!!! warning "用户代理一致性至关重要"
    设置 `--user-agent` 只会更改 **HTTP 标头**，但检测系统还会检查 `navigator.userAgent`、`navigator.platform`、`navigator.vendor` 和其他 JavaScript 属性。**这些值之间的不一致是强烈的机器人指标。**
    
    例如，如果您的 HTTP User-Agent 说"Windows"但 `navigator.platform` 说"Linux"，您将立即被标记。
    
    **解决方案**：您还必须通过 CDP 覆盖 JavaScript 属性以保持一致性。请参阅 **[浏览器指纹识别 - 用户代理一致性](../../deep-dive/fingerprinting/browser-fingerprinting.md#user-agent-consistency)** 获取详细说明和使用 `Page.addScriptToEvaluateOnNewDocument` 的实现。
    
    这就是为什么全面的隐蔽需要命令行参数**和**浏览器偏好设置配置。

!!! tip "完整隐蔽策略"
    命令行参数只是解决方案的一部分。为了最大的隐蔽性：
    
    1. **使用上述参数**（navigator.webdriver、WebGL、WebRTC）
    2. **配置浏览器偏好设置** - 请参阅[浏览器偏好设置 - 隐蔽和指纹识别](browser-preferences.md#stealth-fingerprinting)
    3. **类人交互** - 请参阅[类人交互](../automation/human-interactions.md)
    4. **良好的代理/IP 声誉** - 使用住宅代理

### Docker/CI 配置

用于容器化环境：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_docker_options() -> ChromiumOptions:
    """用于 Docker 容器和 CI/CD 的配置。"""
    options = ChromiumOptions()
    
    # Docker 所需
    options.headless = True
    options.add_argument('--no-sandbox')  # 沙箱与容器隔离冲突
    options.add_argument('--disable-dev-shm-usage')  # 克服 /dev/shm 大小限制
    
    # 稳定性
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    
    # 内存优化
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    
    # 为 CI 更快的页面加载
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # 为慢速 CI 运行器增加超时
    options.start_timeout = 20
    
    # 崩溃处理
    options.add_argument('--disable-crash-reporter')
    
    return options

async def ci_testing_example():
    options = create_docker_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 运行您的测试...
        await tab.go_to('https://example.com')
        assert await tab.execute_script('return document.title') == 'Example Domain'

asyncio.run(ci_testing_example())
```

## 故障排除

### 浏览器无法启动

```python
# 增加超时
options.start_timeout = 30

# 检查二进制位置
options.binary_location = '/path/to/chrome'

# Docker/CI 问题
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

### 性能慢

```python
# 如果不需要则禁用 GPU
options.add_argument('--disable-gpu')

# 禁用图像
options.add_argument('--blink-settings=imagesEnabled=false')

# 使用 INTERACTIVE 加载状态
options.page_load_state = PageLoadState.INTERACTIVE

# 禁用不必要的功能
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')
```

### Docker 中的内存问题

```python
# Docker 必需
options.add_argument('--disable-dev-shm-usage')

# 减少内存占用
options.add_argument('--disable-extensions')
options.add_argument('--disable-gpu')
options.add_argument('--single-process')  # 最后手段（可能不稳定）
```

## 进一步阅读

- **[浏览器偏好设置](browser-preferences.md)** - Chromium 的内部偏好系统
- **[隐蔽自动化](../automation/human-interactions.md)** - 类人交互
- **[上下文](../browser-management/contexts.md)** - 隔离的浏览上下文
- **[网络拦截](../network/interception.md)** - 请求/响应操作

!!! tip "实验是关键"
    浏览器配置高度依赖于您的具体用例。从这里的示例开始，然后根据您的需求进行调整。使用 `browser._connection_port` 访问 DevTools 并检查浏览器内部发生的情况。
