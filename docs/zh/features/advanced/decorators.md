# Retry 装饰器

网页爬虫本质上是不可预测的。网络故障、页面加载缓慢、元素出现和消失、触发速率限制以及意外出现的验证码。`@retry` 装饰器提供了一个经过实战测试的强大解决方案，能够优雅地处理这些不可避免的故障。

## 为什么使用 Retry 装饰器？

在生产环境的爬虫中，故障不是例外——而是常态。与其让整个爬虫任务因为临时的网络故障或缺失的元素而崩溃，retry 装饰器允许您：

- **自动恢复** 临时性故障
- **实施复杂的重试策略** 使用指数退避
- **在重试前执行恢复逻辑** （刷新页面、切换代理、重启浏览器）
- **保持业务逻辑清晰** 不会被错误处理代码污染

## 快速开始

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, NetworkError

@retry(max_retries=3, exceptions=[WaitElementTimeout, NetworkError])
async def scrape_product_page(url: str):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        
        # 这可能因网络问题或加载缓慢而失败
        product_title = await tab.find(class_name='product-title', timeout=5)
        return await product_title.text

asyncio.run(scrape_product_page('https://example.com/product/123'))
```

如果 `scrape_product_page` 因 `WaitElementTimeout` 或 `NetworkError` 失败，它将自动重试最多 3 次才会放弃。

## 最佳实践：始终指定异常

!!! warning "关键最佳实践"
    **始终** 指定应该触发重试的异常。使用默认的 `exceptions=Exception` 会捕获 **所有** 异常，包括应该立即失败的代码错误。

**错误（捕获所有内容，包括错误）：**

```python
@retry(max_retries=3)  # 不要这样做
async def scrape_data():
    data = response['items'][0]  # 如果 'items' 不存在，重试无济于事！
    return data
```

**正确（仅对预期的失败重试）：**

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

@retry(
    max_retries=3,
    exceptions=[ElementNotFound, WaitElementTimeout, NetworkError]
)
async def scrape_data():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        return await tab.find(id='data-container', timeout=10)
```

通过指定异常，您可以确保：

- **逻辑错误快速失败** （拼写错误、错误的选择器、代码错误）
- **仅重试可恢复的错误** （网络问题、超时、缺失元素）
- **调试更容易** （您确切知道出了什么问题）

## 参数

### max_retries

放弃前的最大重试次数。

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=5, exceptions=[WaitElementTimeout])
async def fetch_data():
    # 总共将尝试 5 次
    pass
```

### exceptions

应该触发重试的异常类型。可以是单个异常或列表。

```python
from pydoll.exceptions import (
    ElementNotFound,
    WaitElementTimeout,
    NetworkError,
    ElementNotInteractable
)

# 单个异常
@retry(exceptions=[WaitElementTimeout])
async def example1():
    pass

# 多个异常
@retry(exceptions=[WaitElementTimeout, NetworkError, ElementNotFound, ElementNotInteractable])
async def example2():
    pass
```

!!! tip "常见爬虫异常"
    对于使用 Pydoll 进行网页爬虫，您通常会希望重试：

    - `WaitElementTimeout` - 等待元素出现超时
    - `ElementNotFound` - DOM 中不存在元素
    - `ElementNotVisible` - 元素存在但不可见
    - `ElementNotInteractable` - 元素无法接收交互
    - `NetworkError` - 网络连接问题
    - `ConnectionFailed` - 连接浏览器失败
    - `PageLoadTimeout` - 页面加载超时
    - `ClickIntercepted` - 点击被另一个元素拦截

### delay

重试尝试之间的等待时间（以秒为单位）。

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=3, exceptions=[WaitElementTimeout], delay=2.0)
async def scrape_with_delay():
    # 每次重试之间等待 2 秒
    pass
```

### exponential_backoff

当设置为 `True` 时，随着每次重试尝试，延迟会指数级增加。

```python
from pydoll.exceptions import NetworkError

@retry(
    max_retries=5,
    exceptions=[NetworkError],
    delay=1.0,
    exponential_backoff=True
)
async def scrape_with_backoff():
    # 尝试 1: 失败 → 等待 1 秒
    # 尝试 2: 失败 → 等待 2 秒
    # 尝试 3: 失败 → 等待 4 秒
    # 尝试 4: 失败 → 等待 8 秒
    # 尝试 5: 失败 → 抛出异常
    pass
```

**什么是指数退避？**

指数退避是一种重试策略，尝试之间的等待时间呈指数级增长。与其每秒对服务器发起请求，不如逐渐给服务器更多恢复时间：

- **尝试 1**：等待 `delay` 秒（例如 1 秒）
- **尝试 2**：等待 `delay * 2` 秒（例如 2 秒）
- **尝试 3**：等待 `delay * 4` 秒（例如 4 秒）
- **尝试 4**：等待 `delay * 8` 秒（例如 8 秒）

这在以下情况下特别有用：

- 处理 **速率限制** （给服务器时间重置）
- 处理 **临时服务器过载** （不要让情况变得更糟）
- 等待 **加载缓慢的动态内容**
- 避免 **被检测为机器人** （看起来自然的重试模式）

### on_retry

在每次失败尝试后、下次重试前执行的回调函数。必须是 **async 函数**。

```python
from pydoll.exceptions import WaitElementTimeout

@retry(
    max_retries=3,
    exceptions=[WaitElementTimeout],
    on_retry=my_recovery_function
)
async def scrape_data():
    pass
```

回调可以是：

- **独立的 async 函数**
- **类方法** （自动接收 `self`）

## on_retry 回调：您的恢复机制

`on_retry` 回调是真正神奇的地方。这是您在下次重试尝试之前 **恢复应用程序状态** 的机会。

### 独立函数

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

async def log_retry():
    print("重试尝试失败，下次尝试前等待...")
    await asyncio.sleep(1)

@retry(max_retries=3, exceptions=[WaitElementTimeout], on_retry=log_retry)
async def scrape_page():
    # 您的爬虫逻辑
    pass
```

### 类方法

在类内部使用装饰器时，回调可以是类方法。它将自动接收 `self` 作为第一个参数。

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

class DataCollector:
    def __init__(self):
        self.retry_count = 0
    
    # 重要：在装饰方法之前定义回调
    async def log_retry(self):
        self.retry_count += 1
        print(f"尝试 {self.retry_count} 失败，正在重试...")
        await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[WaitElementTimeout],
        on_retry=log_retry  # 不需要 'self.' 前缀
    )
    async def fetch_data(self):
        # 您的爬取逻辑
        pass
```

!!! warning "方法定义顺序很重要"
    使用类方法的 `on_retry` 时，**必须在类定义中的装饰方法之前定义回调方法**。Python 在应用装饰器时需要知道回调。

    **错误（会失败）：**

    ```python
    class Scraper:
        @retry(on_retry=handle_retry)  # handle_retry 还不存在！
        async def scrape(self):
            pass
        
        async def handle_retry(self):  # 定义太晚
            pass
    ```

    **正确：**

    ```python
    class Scraper:
        async def handle_retry(self):  # 首先定义
            pass
        
        @retry(on_retry=handle_retry)  # 现在存在
        async def scrape(self):
            pass
    ```

## 实际应用案例

### 1. 页面刷新和状态恢复

**这是 `on_retry` 最强大的用法**：通过刷新页面并恢复应用程序状态来从故障中恢复。此示例演示了为什么 retry 装饰器对生产爬虫如此有价值。

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.constants import Key
import asyncio

class DataScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.current_page = 1
    
    async def recover_from_failure(self):
        """刷新页面并在重试前恢复状态"""
        print(f"恢复中... 刷新第 {self.current_page} 页")
        
        if self.tab:
            # 刷新页面以从陈旧元素或错误状态中恢复
            await self.tab.refresh()
            await asyncio.sleep(2)  # 等待页面加载
            
            # 恢复状态：导航回正确页面
            if self.current_page > 1:
                page_input = await self.tab.find(id='page-number')
                await page_input.insert_text(str(self.current_page))
                await self.tab.keyboard.press(Key.ENTER)
                await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover_from_failure,
        delay=1.0
    )
    async def scrape_page_data(self):
        """从当前页面抓取数据"""
        if not self.browser:
            self.browser = Chrome()
            self.tab = await self.browser.start()
            await self.tab.go_to('https://example.com/data')
        
        # 导航到特定页面
        page_input = await self.tab.find(id='page-number')
        await page_input.insert_text(str(self.current_page))
        await self.tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(1)
        
        # 抓取数据（如果元素变陈旧可能会失败）
        items = await self.tab.find(class_name='data-item', find_all=True)
        return [await item.text for item in items]
    
    async def scrape_multiple_pages(self, start_page: int, end_page: int):
        """抓取多个页面，失败时自动重试"""
        results = []
        for page_num in range(start_page, end_page + 1):
            self.current_page = page_num
            data = await self.scrape_page_data()
            results.extend(data)
        return results

# 用法
async def main():
    scraper = DataScraper()
    try:
        # 抓取第 1-10 页，失败时自动恢复
        all_data = await scraper.scrape_multiple_pages(1, 10)
        print(f"已抓取 {len(all_data)} 个项目")
    finally:
        if scraper.browser:
            await scraper.browser.stop()
```

**这为什么强大：**

- `recover_from_failure()` 真正**恢复状态**：刷新并导航回来
- `scrape_page_data()` 方法保持简洁，只专注于爬取逻辑
- 如果元素变陈旧或消失，重试机制会自动处理恢复
- 浏览器通过 `self.browser` 和 `self.tab` 在重试之间保持

### 2. 模态对话框恢复

有时模态框或遮罩层会意外出现并阻止自动化。关闭它并重试。

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class ModalAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def close_modals(self):
        """在重试前关闭任何阻挡的模态框"""
        print("检查阻挡的模态框...")
        
        # 尝试查找并关闭常见模态框
        modal_close = await self.tab.find(
            class_name='modal-close',
            timeout=2,
            raise_exc=False
        )
        if modal_close:
            print("找到模态框，关闭中...")
            await modal_close.click()
            await asyncio.sleep(0.5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=close_modals,
        delay=0.5
    )
    async def click_button(self, button_id: str):
        button = await self.tab.find(id=button_id)
        await button.click()
```

### 3. 浏览器重启和代理轮换

对于大型爬虫任务，失败后可能需要完全重启浏览器并切换代理。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.decorators import retry
from pydoll.exceptions import NetworkError, PageLoadTimeout

class RobustScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.proxy_list = [
            'proxy1.example.com:8080',
            'proxy2.example.com:8080',
            'proxy3.example.com:8080',
        ]
        self.current_proxy_index = 0
    
    async def restart_with_new_proxy(self):
        """使用不同代理重启浏览器"""
        print("使用新代理重启浏览器...")
        
        # 关闭当前浏览器
        if self.browser:
            await self.browser.stop()
            await asyncio.sleep(2)
        
        # 轮换到下一个代理
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        proxy = self.proxy_list[self.current_proxy_index]
        
        print(f"使用代理: {proxy}")
        
        # 使用新代理启动新浏览器
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server={proxy}')
        
        self.browser = Chrome(options=options)
        self.tab = await self.browser.start()
    
    @retry(
        max_retries=3,
        exceptions=[NetworkError, PageLoadTimeout],
        on_retry=restart_with_new_proxy,
        delay=5.0,
        exponential_backoff=True
    )
    async def scrape_protected_site(self, url: str):
        if not self.browser:
            await self.restart_with_new_proxy()
        
        await self.tab.go_to(url)
        await asyncio.sleep(3)
        
        # 您的爬虫逻辑
        content = await self.tab.find(id='content')
        return await content.text
```

### 4. 网络空闲检测与重试

等待所有网络活动完成，如果页面从未稳定则使用重试逻辑。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import TimeoutException

class NetworkAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def reload_page(self):
        """如果网络从未稳定则重新加载页面"""
        print("页面未稳定，重新加载...")
        if self.tab:
            await self.tab.refresh()
            await asyncio.sleep(2)
    
    @retry(
        max_retries=2,
        exceptions=[TimeoutException],
        on_retry=reload_page,
        delay=3.0
    )
    async def wait_for_page_ready(self):
        """等待所有网络请求完成"""
        await self.tab.enable_network_events()
        
        # 等待网络空闲（2 秒内无请求）
        idle_time = 0
        max_wait = 10
        
        while idle_time < max_wait:
            # 检查是否有正在进行的请求
            # （实现取决于您的事件跟踪）
            await asyncio.sleep(0.5)
            idle_time += 0.5
        
        if idle_time >= max_wait:
            raise TimeoutException("网络从未稳定")
```

### 5. 验证码检测和恢复

检测验证码何时出现并采取适当行动。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class CaptchaScraper:
    def __init__(self):
        self.tab = None
        self.captcha_count = 0
    
    async def handle_captcha(self):
        """通过等待或切换策略处理验证码"""
        self.captcha_count += 1
        print(f"检测到验证码（计数：{self.captcha_count}）")
        
        if self.captcha_count > 2:
            print("验证码过多，可能需要更改策略...")
            # 可以在这里切换到不同的方法
        
        # 尝试之间等待更长时间
        await asyncio.sleep(30)
        
        # 刷新页面
        await self.tab.refresh()
        await asyncio.sleep(5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=handle_captcha,
        delay=10.0,
        exponential_backoff=True
    )
    async def scrape_protected_content(self, url: str):
        if not self.tab:
            browser = Chrome()
            self.tab = await browser.start()
        
        await self.tab.go_to(url)
        
        # 检查验证码
        captcha = await self.tab.find(
            class_name='g-recaptcha',
            timeout=2,
            raise_exc=False
        )
        
        if captcha:
            raise ElementNotFound("检测到验证码")
        
        # 正常爬虫逻辑
        content = await self.tab.find(class_name='article-content')
        return await content.text
```

## 高级模式

### 组合多种恢复策略

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

class AdvancedScraper:
    def __init__(self):
        self.tab = None
        self.attempt = 0
        self.strategies = [
            self.strategy_refresh,
            self.strategy_clear_cache,
            self.strategy_restart_browser,
        ]
    
    async def strategy_refresh(self):
        """策略 1：简单刷新"""
        print("策略 1：刷新页面")
        await self.tab.refresh()
        await asyncio.sleep(2)
    
    async def strategy_clear_cache(self):
        """策略 2：清除缓存并刷新"""
        print("策略 2：清除缓存")
        await self.tab.execute_command('Network.clearBrowserCache')
        await self.tab.refresh()
        await asyncio.sleep(3)
    
    async def strategy_restart_browser(self):
        """策略 3：完全重启浏览器"""
        print("策略 3：重启浏览器")
        if self.tab:
            await self.tab._browser.stop()
        
        browser = Chrome()
        self.tab = await browser.start()
    
    async def adaptive_recovery(self):
        """根据尝试次数尝试不同的恢复策略"""
        strategy_index = min(self.attempt, len(self.strategies) - 1)
        strategy = self.strategies[strategy_index]
        
        print(f"尝试 {self.attempt + 1}：使用 {strategy.__name__}")
        await strategy()
        
        self.attempt += 1
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout, NetworkError],
        on_retry=adaptive_recovery,
        delay=2.0
    )
    async def scrape_with_adaptive_retry(self, url: str):
        await self.tab.go_to(url)
        return await self.tab.find(id='target-content')
```

### 特定失败的自定义异常

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import PydollException

class RateLimitError(PydollException):
    """检测到速率限制时引发"""
    message = "API 速率限制已超出"

class APIScraper:
    async def wait_for_rate_limit_reset(self):
        """被速率限制时等待更长时间"""
        print("检测到速率限制，等待 60 秒...")
        await asyncio.sleep(60)
    
    @retry(
        max_retries=5,
        exceptions=[RateLimitError],
        on_retry=wait_for_rate_limit_reset,
        delay=10.0,
        exponential_backoff=True
    )
    async def fetch_api_data(self, endpoint: str):
        response = await self.tab.request.get(endpoint)
        
        if response.status == 429:  # 请求过多
            raise RateLimitError("API 速率限制已超出")
        
        return response.json()
```

## 最佳实践总结

1. **始终明确指定异常** - 永不使用默认的 `exceptions=Exception`
2. **对外部服务使用指数退避** - 给服务器恢复时间
3. **保持合理的重试次数** - 通常 3-5 次尝试就足够了
4. **记录重试尝试** - 使用 `on_retry` 记录发生的事情
5. **在装饰方法之前定义回调** - 类定义中的顺序很重要
6. **使回调异步** - 装饰器需要异步回调
7. **在回调中恢复状态** - 使用 `on_retry` 导航回原位置
8. **考虑重试的成本** - 每次重试都会消耗时间和资源
9. **与其他错误处理结合** - 重试不能替代 try/except 块
10. **测试您的重试逻辑** - 确保恢复回调实际有效

## 了解更多

- **[异常处理](../core-concepts.md#error-handling)** - 理解 Pydoll 异常
- **[网络事件](../network/monitoring.md)** - 跟踪和处理网络故障
- **[浏览器选项](../configuration/browser-options.md)** - 配置代理和其他设置
- **[事件系统](event-system.md)** - 构建响应式重试策略

retry 装饰器是一个强大的工具，可以将脆弱的爬虫脚本转变为生产就绪的应用程序。通过将其与周到的恢复策略相结合，您可以构建能够优雅地处理真实网络混乱情况的爬虫。

