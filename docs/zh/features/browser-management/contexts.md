# 浏览器上下文

浏览器上下文是Pydoll在单个浏览器进程内创建完全隔离的浏览环境的解决方案。可以将它们视为独立的"隐私窗口"，但具有完全的编程控制，每个上下文维护自己的Cookie、存储、缓存和认证状态。

## 快速入门

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_context_example():
    async with Chrome() as browser:
        # 在默认上下文中启动浏览器并创建初始标签页
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # 创建隔离的上下文
        context_id = await browser.create_browser_context()
        
        # 在隔离上下文中创建新标签页
        isolated_tab = await browser.new_tab('https://example.com', browser_context_id=context_id)
        
        # 两个标签页完全隔离 - 不同的Cookie、存储等
        await initial_tab.execute_script("localStorage.setItem('user', 'Alice')")
        await isolated_tab.execute_script("localStorage.setItem('user', 'Bob')")
        
        # 验证隔离
        user_default = await initial_tab.execute_script("return localStorage.getItem('user')")
        user_isolated = await isolated_tab.execute_script("return localStorage.getItem('user')")
        
        print(f"默认上下文: {user_default}")  # Alice
        print(f"隔离上下文: {user_isolated}")  # Bob

asyncio.run(basic_context_example())
```

## 什么是浏览器上下文？

浏览器上下文是单个浏览器进程内的隔离浏览环境。每个上下文维护完全独立的：

| 组件 | 描述 | 隔离级别 |
|-----------|-------------|-----------------|
| **Cookie** | HTTP Cookie和会话数据 | ✓ 完全隔离 |
| **本地存储** | `localStorage`和`sessionStorage` | ✓ 完全隔离 |
| **IndexedDB** | 客户端数据库 | ✓ 完全隔离 |
| **缓存** | HTTP缓存和资源 | ✓ 完全隔离 |
| **权限** | 地理位置、通知、摄像头等 | ✓ 完全隔离 |
| **认证** | 登录会话和认证令牌 | ✓ 完全隔离 |
| **Service Workers** | 后台脚本 | ✓ 完全隔离 |

```mermaid
graph LR
    Browser[浏览器进程] --> Default[默认上下文]
    Browser --> Context1[上下文1]
    Browser --> Context2[上下文2]
    
    Default --> T1[标签A]
    Default --> T2[标签B]
    Context1 --> T3[标签C]
    Context2 --> T4[标签D]
```

## 为什么使用浏览器上下文？

### 1. 多账户测试

同时测试不同的用户账户而不产生干扰：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def perform_login(tab, email, password):
    """
    辅助函数：导航到登录页面
    并提交账户凭据。
    """
    print(f"尝试使用以下账户登录：{email}...")
    await tab.go_to('https://app.example.com/login')

    # 查找元素
    email_field = await tab.find(id='email')
    password_field = await tab.find(id='password')
    login_btn = await tab.find(id='login-btn')

    # 填写凭据并点击
    await email_field.type_text(email)
    await password_field.type_text(password)
    await login_btn.click()

    # 等待登录处理
    await asyncio.sleep(2)
    print(f"{email} 登录成功。")


async def multi_account_test():
    """
    使用隔离的浏览器上下文
    测试同时登录的主脚本。
    """
    accounts = [
        {"email": "user1@example.com", "password": "pass1"},
        {"email": "user2@example.com", "password": "pass2"},
        {"email": "admin@example.com", "password": "admin_pass"}
    ]

    # 此列表将存储每个活动用户会话的信息
    user_sessions = []

    async with Chrome() as browser:
        first_account = accounts[0]
        initial_tab = await browser.start()
        await perform_login(initial_tab, first_account['email'], first_account['password'])
        user_sessions.append({
            "email": first_account['email'],
            "tab": initial_tab,
            "context_id": None  # 'None' 表示默认浏览器上下文
        })

        # 遍历其余账户
        for account in accounts[1:]:
            context_id = await browser.create_browser_context()
            new_tab = await browser.new_tab(browser_context_id=context_id)
            await perform_login(new_tab, account['email'], account['password'])

            # 将新会话信息添加到列表
            user_sessions.append({
                "email": account['email'],
                "tab": new_tab,
                "context_id": context_id
            })

        print("\n--- 验证所有活动会话 ---")
        for session in user_sessions:
            tab = session["tab"]
            email = session["email"]
            await tab.go_to('https://app.example.com/dashboard')
            username = await tab.find(class_name='username')
            username_text = await username.text
            print(f"[账户：{email}] -> 登录为：{username_text}")
            await asyncio.sleep(0.5)

        print("\n--- 清理上下文 ---")
        for session in user_sessions:
            # 仅关闭我们创建的上下文（非None）
            if session["context_id"] is not None:
                print(f"关闭上下文：{session['email']}")
                await session["tab"].close()
                await browser.delete_browser_context(session["context_id"])
        
        # 默认上下文（None）由
        # 'async with Chrome() as browser' 自动关闭

asyncio.run(multi_account_test())
```

### 2. 使用上下文特定代理的地理位置测试

每个上下文可以拥有自己的代理配置：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def geo_location_testing():
    async with Chrome() as browser:
        # 启动浏览器并使用初始标签页进行第一个测试（默认上下文，无代理）
        initial_tab = await browser.start()
        await initial_tab.go_to('https://api.ipify.org')
        await asyncio.sleep(2)
        default_ip = await initial_tab.execute_script('return document.body.textContent')
        print(f"默认IP（无代理）：{default_ip}")
        
        # 带美国代理的美国上下文
        us_context = await browser.create_browser_context(
            proxy_server='http://us-proxy.example.com:8080'
        )
        us_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=us_context)
        await asyncio.sleep(2)
        us_ip = await us_tab.execute_script('return document.body.textContent')
        print(f"美国IP：{us_ip}")
        
        # 带欧盟代理的欧盟上下文
        eu_context = await browser.create_browser_context(
            proxy_server='http://eu-proxy.example.com:8080'
        )
        eu_tab = await browser.new_tab('https://api.ipify.org', browser_context_id=eu_context)
        await asyncio.sleep(2)
        eu_ip = await eu_tab.execute_script('return document.body.textContent')
        print(f"欧盟IP：{eu_ip}")
        
        # 清理（跳过初始标签页）
        await us_tab.close()
        await eu_tab.close()
        await browser.delete_browser_context(us_context)
        await browser.delete_browser_context(eu_context)

asyncio.run(geo_location_testing())
```

!!! tip "代理认证"
    Pydoll自动处理上下文的代理认证。只需在URL中包含凭据：
    ```python
    context_id = await browser.create_browser_context(
        proxy_server='http://username:password@proxy.example.com:8080'
    )
    ```
    凭据从CDP命令中清理，仅在浏览器要求认证时使用。

### 3. A/B测试

并行比较不同的用户体验：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def ab_testing():
    async with Chrome() as browser:
        # 启动浏览器并创建初始标签页（默认上下文中的对照组）
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        await initial_tab.execute_script("localStorage.setItem('experiment', 'control')")
        
        # 隔离上下文中的实验组
        context_b = await browser.create_browser_context()
        tab_b = await browser.new_tab('https://example.com', browser_context_id=context_b)
        await tab_b.execute_script("localStorage.setItem('experiment', 'treatment')")
        
        # 将两者导航到功能页面
        await initial_tab.go_to('https://example.com/feature')
        await tab_b.go_to('https://example.com/feature')
        
        # 比较结果
        result_a = await initial_tab.find(class_name='experiment-result')
        result_b = await tab_b.find(class_name='experiment-result')
        
        print(f"对照组结果：{await result_a.text}")
        print(f"实验组结果：{await result_b.text}")
        
        # 清理
        await tab_b.close()
        await browser.delete_browser_context(context_b)

asyncio.run(ab_testing())
```

### 4. 并行网页抓取

使用不同配置抓取多个网站：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def parallel_scraping():
    websites = [
        {'url': 'https://news.ycombinator.com', 'selector': '.storylink'},
        {'url': 'https://reddit.com/r/python', 'selector': '.title'},
        {'url': 'https://github.com/trending', 'selector': '.h3'},
    ]
    
    async with Chrome() as browser:
        # 启动浏览器并获取初始标签页
        initial_tab = await browser.start()
        
        # 为其余网站创建上下文（第一个使用默认上下文）
        contexts = [None] + [await browser.create_browser_context() for _ in websites[1:]]
        
        # 创建标签页（为第一个网站重用初始标签页）
        tabs = [initial_tab] + [
            await browser.new_tab(browser_context_id=ctx) for ctx in contexts[1:]
        ]
        
        async def scrape_site(tab, site, context_id):
            """在给定的标签页和上下文内抓取单个网站"""
            try:
                await tab.go_to(site['url'])
                await asyncio.sleep(3)
                
                # 使用CSS选择器提取标题
                elements = await tab.query(site['selector'], find_all=True)
                titles = [await elem.text for elem in elements[:5]]
                
                return {'url': site['url'], 'titles': titles}
            finally:
                # 清理上下文（跳过初始标签页的默认上下文）
                if context_id is not None:
                    await tab.close()
                    await browser.delete_browser_context(context_id)
        
        # 并发抓取所有网站
        results = await asyncio.gather(*[
            scrape_site(tab, site, ctx) for tab, site, ctx in zip(tabs, websites, contexts)
        ])
        
        # 显示结果
        for result in results:
            print(f"\n{result['url']}:")
            for i, title in enumerate(result['titles'], 1):
                print(f"  {i}. {title}")

asyncio.run(parallel_scraping())
```

## 理解上下文性能

### 上下文是轻量级的

!!! info "性能特征"
    创建浏览器上下文**显著快于且更轻量**于启动新的浏览器进程：
    
    - **上下文创建**：约50-100毫秒，内存开销最小
    - **新浏览器进程**：约2-5秒，基础内存50-150 MB
    
    对于10个隔离环境：

    - **1个浏览器中的10个上下文**：约500毫秒启动，总计约500 MB
    - **10个独立浏览器**：约30秒启动，总计约1-1.5 GB

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def benchmark_contexts_vs_browsers():
    # Benchmark contexts
    start = time.time()
    async with Chrome() as browser:
        # 启动浏览器（此示例中未使用初始标签页）
        await browser.start()
        
        contexts = []
        for i in range(10):
            context_id = await browser.create_browser_context()
            contexts.append(context_id)
        
        print(f"创建10个上下文耗时：{time.time() - start:.2f}秒")
        
        # 清理
        for context_id in contexts:
            await browser.delete_browser_context(context_id)

asyncio.run(benchmark_contexts_vs_browsers())
```

### 无头模式 vs 有头模式：窗口行为

!!! warning "重要：有头模式中的上下文窗口"
    在**有头模式**（可见的浏览器UI）下运行时，有一个重要的行为需要理解：
    
    **在新上下文中创建的第一个标签页将打开一个新的操作系统窗口。**
    
    - 这是因为上下文需要一个"宿主窗口"来渲染其第一个页面
    - 该上下文中的后续标签页可以作为该窗口内的标签页打开
    - 这是CDP/Chromium的限制，而非Pydoll的设计选择
    
    **在无头模式下**，这不重要——不会创建窗口，一切都在后台运行。

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def demonstrate_window_behavior():
    # 有头模式 - 将看到窗口
    options_headed = ChromiumOptions()
    options_headed.headless = False
    
    async with Chrome(options=options_headed) as browser:
        # 启动浏览器并创建初始标签页（在默认上下文中打开第一个窗口）
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com')
        
        # 创建新上下文 - 第一个标签页将打开一个新窗口
        context = await browser.create_browser_context()
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context)
        
        # 同一上下文中的第二个标签页 - 在现有窗口中作为标签页打开
        tab3 = await browser.new_tab('https://google.com', browser_context_id=context)
        
        await asyncio.sleep(10)  # 观察窗口
        
        await tab2.close()
        await tab3.close()
        await browser.delete_browser_context(context)

# 无头模式 - 无窗口，上下文不可见但仍然隔离
async def headless_contexts():
    options = ChromiumOptions()
    options.headless = True  # 无可见窗口
    
    async with Chrome(options=options) as browser:
        # 在默认上下文中启动浏览器并创建初始标签页
        initial_tab = await browser.start()
        await initial_tab.go_to('https://example.com/page0')
        
        # 再创建4个上下文 - 未打开窗口，全部在后台
        contexts = []
        for i in range(1, 5):
            context_id = await browser.create_browser_context()
            tab = await browser.new_tab(f'https://example.com/page{i}', browser_context_id=context_id)
            contexts.append((context_id, tab))
        
        print(f"创建了{len(contexts) + 1}个隔离上下文（1个默认 + {len(contexts)}个自定义，不可见）")
        
        # 清理
        for context_id, tab in contexts:
            await tab.close()
            await browser.delete_browser_context(context_id)

asyncio.run(headless_contexts())
```

!!! tip "最佳实践：对上下文使用无头模式"
    为了在多个上下文中实现最大效率：
    
    - **开发/调试**：使用有头模式查看发生的情况
    - **生产/CI/CD**：使用无头模式以获得更快、更轻量的执行
    - **多个上下文**：强烈建议使用无头模式以避免窗口管理的复杂性

## 上下文管理

### 创建上下文

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def create_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # 创建基本上下文
        context_id = await browser.create_browser_context()
        print(f"已创建上下文：{context_id}")
        
        # 创建带代理的上下文
        proxied_context = await browser.create_browser_context(
            proxy_server='http://proxy.example.com:8080',
            proxy_bypass_list='localhost,127.0.0.1'
        )
        print(f"已创建代理上下文：{proxied_context}")
        
        # 创建带认证代理的上下文
        auth_context = await browser.create_browser_context(
            proxy_server='http://user:pass@proxy.example.com:8080'
        )
        print(f"已创建认证上下文：{auth_context}")

asyncio.run(create_context_example())
```

### 列出上下文

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def list_contexts():
    async with Chrome() as browser:
        await browser.start()
        
        # 获取所有上下文（包括默认上下文）
        contexts = await browser.get_browser_contexts()
        print(f"初始上下文：{len(contexts)}")  # 通常为1（默认）
        
        # 创建额外的上下文
        context1 = await browser.create_browser_context()
        context2 = await browser.create_browser_context()
        
        # 再次列出
        contexts = await browser.get_browser_contexts()
        print(f"创建2个新上下文后：{len(contexts)}")  # 总计3个
        
        for i, context_id in enumerate(contexts):
            print(f"  上下文 {i+1}：{context_id}")
        
        # 清理
        await browser.delete_browser_context(context1)
        await browser.delete_browser_context(context2)

asyncio.run(list_contexts())
```

### 删除上下文

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def delete_context_example():
    async with Chrome() as browser:
        await browser.start()
        
        # 创建带标签页的上下文
        context_id = await browser.create_browser_context()
        tab1 = await browser.new_tab('https://example.com', browser_context_id=context_id)
        tab2 = await browser.new_tab('https://github.com', browser_context_id=context_id)
        
        print(f"已创建上下文 {context_id}，包含2个标签页")
        
        # 删除上下文会自动关闭其所有标签页
        await browser.delete_browser_context(context_id)
        print("上下文已删除（所有标签页自动关闭）")

asyncio.run(delete_context_example())
```

!!! warning "删除上下文会关闭所有标签页"
    删除浏览器上下文时，**属于该上下文的所有标签页会自动关闭**。这是一次清理多个标签页的高效方法，但请确保您已保存了任何重要数据。

## 默认上下文

每个浏览器都以包含初始标签页的**默认上下文**开始：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def default_context_example():
    async with Chrome() as browser:
        # 初始标签页位于默认上下文中
        initial_tab = await browser.start()
        
        # 创建标签页而不指定上下文 - 使用默认上下文
        default_tab = await browser.new_tab('https://example.com')
        
        # 创建自定义上下文
        custom_context = await browser.create_browser_context()
        custom_tab = await browser.new_tab('https://github.com', browser_context_id=custom_context)
        
        # 默认上下文和自定义上下文是隔离的
        await default_tab.execute_script("localStorage.setItem('type', 'default')")
        await custom_tab.execute_script("localStorage.setItem('type', 'custom')")
        
        # 验证隔离
        default_type = await default_tab.execute_script("return localStorage.getItem('type')")
        custom_type = await custom_tab.execute_script("return localStorage.getItem('type')")
        
        print(f"默认上下文：{default_type}")  # 'default'
        print(f"自定义上下文：{custom_type}")    # 'custom'
        
        # 清理自定义上下文
        await browser.delete_browser_context(custom_context)

asyncio.run(default_context_example())
```

!!! info "您无法删除默认上下文"
    默认浏览器上下文是永久性的，无法删除。它在整个浏览器会话期间存在。只有使用`create_browser_context()`创建的自定义上下文可以被删除。

## 高级模式

### 用于可重用隔离的上下文池

```python
import asyncio
from pydoll.browser.chromium import Chrome

class ContextPool:
    def __init__(self, browser, size=5):
        self.browser = browser
        self.size = size
        self.contexts = []
        self.in_use = set()
    
    async def initialize(self):
        """创建上下文池"""
        for _ in range(self.size):
            context_id = await self.browser.create_browser_context()
            self.contexts.append(context_id)
        print(f"上下文池已初始化，包含 {self.size} 个上下文")
    
    async def acquire(self):
        """从池中获取可用上下文"""
        for context_id in self.contexts:
            if context_id not in self.in_use:
                self.in_use.add(context_id)
                return context_id
        raise Exception("池中没有可用的上下文")
    
    def release(self, context_id):
        """将上下文返回到池"""
        self.in_use.discard(context_id)
    
    async def cleanup(self):
        """删除池中的所有上下文"""
        for context_id in self.contexts:
            await self.browser.delete_browser_context(context_id)

async def use_context_pool():
    async with Chrome() as browser:
        await browser.start()
        
        # 创建池
        pool = ContextPool(browser, size=3)
        await pool.initialize()
        
        # 从池中使用上下文
        async def scrape_with_pool(url):
            context_id = await pool.acquire()
            try:
                tab = await browser.new_tab(url, browser_context_id=context_id)
                await asyncio.sleep(2)
                title = await tab.execute_script('return document.title')
                await tab.close()
                return title
            finally:
                pool.release(context_id)
        
        # 使用池抓取多个URL
        urls = [f'https://example.com/page{i}' for i in range(10)]
        results = await asyncio.gather(*[scrape_with_pool(url) for url in urls])
        
        for i, title in enumerate(results):
            print(f"{urls[i]}: {title}")
        
        # 清理
        await pool.cleanup()

asyncio.run(use_context_pool())
```

### 每个上下文的配置管理器

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def context_config_manager():
    async with Chrome() as browser:
        await browser.start()
        
        # 为不同场景定义配置
        configs = {
            'us_user': {
                'proxy': 'http://us-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            },
            'eu_user': {
                'proxy': 'http://eu-proxy.example.com:8080',
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64)'
            },
            'mobile_user': {
                'proxy': None,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
            }
        }
        
        contexts = {}
        
        # 为每个配置创建上下文
        for name, config in configs.items():
            if config['proxy']:
                context_id = await browser.create_browser_context(
                    proxy_server=config['proxy']
                )
            else:
                context_id = await browser.create_browser_context()
            
            # 创建标签页并设置用户代理
            tab = await browser.new_tab(browser_context_id=context_id)
            # 注意：用户代理将通过CDP或选项设置，此处简化
            
            contexts[name] = {'context_id': context_id, 'tab': tab}
        
        # 为不同场景使用不同上下文
        for name, data in contexts.items():
            tab = data['tab']
            await tab.go_to('https://httpbin.org/headers')
            await asyncio.sleep(2)
            print(f"\n{name} 配置已激活")
        
        # 清理
        for data in contexts.values():
            await data['tab'].close()
            await browser.delete_browser_context(data['context_id'])

asyncio.run(context_config_manager())
```

## 最佳实践

1. **对多个上下文使用无头模式**以避免窗口管理的复杂性
2. **使用完毕后始终删除上下文**以防止内存泄漏
3. **将相关操作分组在同一上下文中**以获得更好的组织
4. **优先使用上下文而非多个浏览器进程**以获得更好的性能
5. **使用上下文池**用于需要许多短期隔离环境的场景
6. **在删除上下文前关闭标签页**以获得更干净的清理（虽然不是严格要求）

## 另请参阅

- **[多标签管理](tabs.md)** - 管理上下文中的多个标签页
- **[深入探讨：Browser域](../../deep-dive/architecture/browser-domain.md)** - 上下文的架构细节
- **[网络：HTTP请求](../network/http-requests.md)** - 浏览器上下文请求继承上下文状态
- **[核心概念](../core-concepts.md)** - 理解Pydoll的架构

浏览器上下文是Pydoll创建复杂自动化工作流的最强大功能之一。通过理解它们的工作方式——特别是有头模式下的窗口行为及其轻量级特性——您可以构建高效、可扩展的自动化，轻松处理复杂的多环境场景。

