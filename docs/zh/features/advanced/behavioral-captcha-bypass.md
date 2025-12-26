# Cloudflare Turnstile 交互

Pydoll 通过执行真实的浏览器点击，为与 Cloudflare Turnstile 验证码交互提供原生支持。这**不是绕过或规避**。它只是自动化人类在验证码复选框上执行的相同点击操作。

!!! warning "此功能实际做什么"
    此功能使用标准浏览器交互**点击** Cloudflare Turnstile 验证码复选框。就这样。没有：
    
    - **没有**：魔法绕过或规避
    - **没有**：挑战解决（图像选择、拼图等）
    - **没有**：分数操纵或指纹欺骗
    - **有**：只是对验证码容器的真实点击
    
    **成功完全取决于您的环境**（IP 声誉、浏览器指纹、行为模式）。Pydoll 提供点击机制；您的环境决定点击是否被接受。

!!! info "什么是 Cloudflare Turnstile？"
    Cloudflare Turnstile 是一个现代验证码系统，它分析浏览器环境和行为信号来判断您是否是人类。它通常显示为用户必须点击的复选框。系统分析：
    
    - **IP 声誉**：您的 IP 地址是否被标记或可疑？
    - **浏览器指纹**：您的浏览器看起来合法吗？
    - **行为模式**：您的行为像人类吗？
    
    当信任分数足够高时，复选框点击被接受。当分数太低时，Turnstile 可能会显示挑战（Pydoll **无法解决**）或完全阻止您。对于图像或拼图挑战，可以考虑使用 **[CapSolver](https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc)**。

## 快速开始

### 上下文管理器（推荐）

上下文管理器等待验证码出现，点击它，并在继续之前等待解决：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def turnstile_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 上下文管理器自动处理验证码
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')
        
        # 此代码仅在验证码被点击后运行
        print("Turnstile 验证码交互完成！")
        
        # 继续您的自动化
        content = await tab.find(id='protected-content')
        print(await content.text)

asyncio.run(turnstile_example())
```

### 后台处理

在后台启用自动验证码点击：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def background_turnstile():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 在导航前启用自动点击
        await tab.enable_auto_solve_cloudflare_captcha()
        
        # 导航到受保护的站点
        await tab.go_to('https://site-with-turnstile.com')
        
        # 等待验证码在后台处理
        await asyncio.sleep(5)
        
        print("页面加载完成，后台处理验证码")
        
        # 不再需要时禁用
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(background_turnstile())
```

## 自定义验证码交互

### 自定义选择器

某些站点对验证码使用不同的类名或包装器：

```python
from pydoll.constants import By

async def custom_selector_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 如果默认选择器不起作用，使用自定义选择器
        custom_selector = (By.CLASS_NAME, 'custom-captcha-wrapper')
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=custom_selector
        ):
            await tab.go_to('https://site-with-custom-turnstile.com')
        
        print("自定义选择器使用成功！")

asyncio.run(custom_selector_example())
```

!!! tip "查找正确的选择器"
    要查找正确的选择器：
    
    1. 在 Chrome DevTools 中打开站点
    2. 检查验证码 iframe/容器
    3. 查找唯一的类名或 ID
    4. 使用 `custom_selector` 参数使用该选择器
    
    默认选择器是 `(By.CLASS_NAME, 'cf-turnstile')`，适用于大多数标准的 Cloudflare Turnstile 实现。

### 时间配置

验证码复选框并不总是立即出现。调整时间以匹配站点的行为：

```python
async def timing_configuration_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            time_before_click=3,      # 点击前等待 3 秒（默认：2）
            time_to_wait_captcha=10   # 等待最多 10 秒让验证码出现（默认：5）
        ):
            await tab.go_to('https://site-with-slow-turnstile.com')
        
        print("使用自定义时间完成验证码交互！")

asyncio.run(timing_configuration_example())
```

**参数参考：**

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `custom_selector` | `Optional[tuple[By, str]]` | `(By.CLASS_NAME, 'cf-turnstile')` | 验证码容器的 CSS 选择器 |
| `time_before_click` | `int` | `2` | 点击前等待的秒数（模拟人类思考时间） |
| `time_to_wait_captcha` | `int` | `5` | 等待验证码出现的最大秒数 |

!!! info "为什么时间很重要"
    - **`time_before_click`**：模拟人类反应时间。点击太快可能看起来可疑。
    - **`time_to_wait_captcha`**：某些站点异步加载验证码。如果验证码在此时间内没有出现，交互将被跳过。

## 其他验证码系统

### reCAPTCHA v3（隐形）

reCAPTCHA v3 是**完全隐形的**，**不需要交互**。只需正常导航：

```python
async def recaptcha_v3_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 不需要特殊处理 - 只需导航
        await tab.go_to('https://site-with-recaptcha-v3.com')
        
        # reCAPTCHA v3 在后台运行，分析您的行为
        await asyncio.sleep(3)
        
        # 继续提交表单
        submit_button = await tab.find(id='submit-btn')
        await submit_button.click()

asyncio.run(recaptcha_v3_example())
```

!!! note "reCAPTCHA v3 成功因素"
    由于 reCAPTCHA v3 完全是被动的（无需交互），成功取决于：
    
    - **IP 声誉**：使用声誉良好的住宅代理
    - **浏览器指纹**：配置真实的浏览器首选项
    - **行为模式**：在页面上花费时间，自然滚动，真实打字
    
    如果您的分数太低，某些站点可能会显示 reCAPTCHA v2 挑战（Pydoll **无法解决**）。

## 什么决定成功？

验证码交互的成功**完全取决于您的环境**，而不是 Pydoll。验证码系统分析：

### 1. IP 声誉（最关键）

| IP 类型 | 信任级别 | 预期行为 |
|---------|-------------|-------------------|
| **住宅 IP（干净）** | 高 | 通常无需挑战即被接受 |
| **移动 IP** | 高 | 通常无需挑战即被接受 |
| **数据中心 IP** | 低 | 经常被阻止或挑战 |
| **先前被阻止的 IP** | 非常低 | 几乎总是被阻止或挑战 |

!!! danger "IP 声誉就是一切"
    **没有工具可以克服糟糕的 IP 地址。** 如果您的 IP 被标记，无论您的浏览器看起来多么真实，您都会被阻止或挑战。
    
    使用声誉良好的住宅代理以获得最佳结果。

### 2. 浏览器指纹

配置您的浏览器使其看起来合法：

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def stealth_configuration():
    options = ChromiumOptions()
    
    # 隐蔽参数
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    # 真实的浏览器首选项
    current_time = int(time.time())
    options.browser_preferences = {
        'profile': {
            'last_engagement_time': str(current_time - (3 * 60 * 60)),  # 3 小时前
            'exited_cleanly': True,
            'exit_type': 'Normal',
        },
        'safebrowsing': {'enabled': True},
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')

asyncio.run(stealth_configuration())
```

### 3. 行为模式

验证码系统分析您如何与页面交互：

```python
async def realistic_behavior():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://site-with-turnstile.com')
        
        # 在验证码出现之前模拟人类行为
        await asyncio.sleep(2)  # 阅读页面内容
        await tab.execute_script('window.scrollBy(0, 300)')  # 滚动
        await asyncio.sleep(1)
        
        # 现在与验证码交互
        async with tab.expect_and_bypass_cloudflare_captcha():
            # 验证码交互在这里发生
            pass
        
        print("使用真实行为通过验证码！")

asyncio.run(realistic_behavior())
```

!!! tip "行为指纹识别"
    要深入了解行为模式如何影响验证码成功，请参阅**[行为指纹识别](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)**。本指南解释：
    
    - 鼠标移动模式和检测
    - 击键时间分析
    - 滚动行为物理学
    - 事件序列分析
    
    理解这些概念可以帮助您构建更真实的自动化，实现更高的成功率。

## 故障排除

### 验证码未被点击

**症状**：验证码出现但从未被点击，页面停留在挑战上。

**可能的原因：**

1. **选择器错误**：站点使用不同的元素类/ID
2. **时间太短**：Pydoll 尝试点击时验证码尚未加载
3. **元素不可见**：验证码被隐藏或以不同方式渲染

**解决方案：**

```python
async def troubleshooting_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 增加等待时间并使用自定义选择器
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'your-selector-here'),
            time_before_click=5,     # 点击前更长的延迟
            time_to_wait_captcha=15  # 更多时间查找验证码
        ):
            await tab.go_to('https://problematic-site.com')

asyncio.run(troubleshooting_example())
```

### 验证码被点击但显示挑战

**症状**：复选框短暂显示勾号，然后呈现图像/拼图挑战。

**根本原因**：您的环境的信任分数太低。

**解决方案：**

- 使用声誉良好的住宅代理
- 配置真实的浏览器指纹
- 添加更真实的行为模式（滚动、鼠标移动、延迟）
- **注意**：Pydoll 无法自行解决挑战 — 如果您需要自动验证码解决，请考虑集成 **[CapSolver](https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc)**

### "访问被拒绝"或立即阻止

**症状**：站点立即显示"访问被拒绝"或阻止您而不显示验证码。

**根本原因**：**您的 IP 地址被标记。**

**解决方案：**

- 使用声誉良好的不同住宅代理
- 在请求之间轮换 IP
- 在 `https://www.cloudflare.com/cdn-cgi/trace` 测试您的 IP
- **注意**：再多的浏览器配置都无法修复被标记的 IP

### 在本地工作但在 Docker/CI 中失败

**症状**：验证码交互在您的机器上工作，但在 Docker/CI 环境中失败。

**根本原因**：验证码系统严格审查数据中心 IP。

**解决方案：**

1. **使用带有适当显示的无头模式**（用于完全渲染）：
   ```dockerfile
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \
       chromium \
       chromium-driver \
       xvfb \
       && rm -rf /var/lib/apt/lists/*
   
   ENV DISPLAY=:99
   
   CMD Xvfb :99 -screen 0 1920x1080x24 & python your_script.py
   ```

2. **即使在 CI/CD 中也使用住宅代理**：
   ```python
   options = ChromiumOptions()
   options.add_argument('--proxy-server=http://user:pass@residential-proxy.com:8080')
   ```

## 最佳实践

1. **使用住宅代理**：IP 声誉是最关键的因素
2. **配置隐蔽选项**：移除自动化指示器
3. **添加行为模式**：点击前滚动、等待、移动鼠标
4. **调整时间**：在尝试点击之前给验证码加载时间
5. **使用自定义选择器**：当默认选择器不起作用时
6. **优雅地处理失败**：当无法通过验证码时有备用逻辑
7. **测试您的环境**：在自动化前验证 IP 声誉和浏览器指纹

## 道德准则

!!! danger "服务条款和法律合规"
    即使技术上可行，与验证码交互也可能违反网站的服务条款。在自动化任何网站之前**始终检查并尊重服务条款**。
    
    此功能仅用于**合法的自动化目的**：
    
    **适当的用例：**
    - 对您自己的应用程序进行自动化测试
    - 监控您有权监控的服务
    - 具有适当授权的研究和安全分析
    
    **不适当的用例：**
    - 抓取您无权访问的内容
    - 规避付费墙或订阅系统
    - 拒绝服务攻击或激进抓取
    - 任何违反服务条款的活动

## 另请参阅

- **[浏览器选项](../configuration/browser-options.md)** - 隐蔽配置
- **[浏览器首选项](../configuration/browser-preferences.md)** - 高级指纹识别
- **[代理配置](../configuration/proxy.md)** - 设置代理
- **[行为指纹识别](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)** - 理解行为检测
- **[类人交互](../automation/human-interactions.md)** - 真实的行为模式

---

**记住**：Pydoll 提供点击验证码的机制，但您的环境（IP、指纹、行为）决定成功。这不是魔法解决方案，它是在正确的环境和适当配置下使用的工具。对于需要图像识别或拼图解决的挑战，可以考虑使用 **[CapSolver](https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc)** — 使用代码 **PYDOLL** 获得额外 6% 余额奖励。