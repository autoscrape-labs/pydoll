# Cookie 与会话管理

有效管理 Cookie 和会话对于真实的浏览器自动化至关重要。网站使用 Cookie 来跟踪身份验证、偏好设置和用户行为，并期望浏览器能相应地表现。

## 为什么 Cookie 对自动化很重要

Cookie 不仅仅是存储的数据：它们是浏览器活动的指纹：

- **身份验证**：会话 Cookie 在请求之间维护登录状态
- **跟踪防护**：反机器人系统分析 Cookie 模式
- **真实行为**：没有 Cookie 的浏览器看起来很可疑
- **会话持久性**：重用 Cookie 可以节省重复登录的时间

!!! warning "Cookie 悖论"
    - **太干净**：没有 Cookie 或历史记录的浏览器看起来像机器人
    - **太陈旧**：使用相同的会话数周会触发安全警报
    - **最佳点**：新鲜的 Cookie 配合偶尔的轮换和真实的活动模式

## 快速入门

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_cookie_management():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # 设置 Cookie（使用简单的字典）
        cookies = [
            {
                'name': 'session_id',
                'value': 'abc123xyz',
                'domain': 'example.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            }
        ]
        await tab.set_cookies(cookies)
        
        # 获取所有 Cookie
        all_cookies = await browser.get_cookies()
        print(f"总 Cookie 数: {len(all_cookies)}")
        
        # 删除所有 Cookie
        await tab.delete_all_cookies()

asyncio.run(basic_cookie_management())
```

## 理解 Cookie 类型

!!! info "TypedDict：实践中使用常规字典"
    在本文档中，您会看到对 `CookieParam` 和 `Cookie` 的引用。这些是 **TypedDict** 类型，它们只是带有类型提示的常规 Python 字典，用于 IDE 自动完成和类型检查。
    
    **实际上，您使用常规字典：**
    ```python
    # 这是您实际编写的：
    cookie = {'name': 'session', 'value': 'abc123', 'domain': 'example.com'}
    
    # 类型注释只是为了您的 IDE：
    from pydoll.protocol.network.types import CookieParam
    cookie: CookieParam = {'name': 'session', 'value': 'abc123'}
    ```
    
    下面的所有示例为简单起见都使用普通字典。

### Cookie 结构

`Cookie` 类型（从浏览器检索）包含完整的 Cookie 信息：

```python
{
    "name": str,           # Cookie 名称
    "value": str,          # Cookie 值
    "domain": str,         # Cookie 有效的域
    "path": str,           # Cookie 有效的路径
    "expires": float,      # Unix 时间戳（0 = 会话 Cookie）
    "size": int,           # 大小（字节）
    "httpOnly": bool,      # 仅通过 HTTP 访问（不是 JavaScript）
    "secure": bool,        # 仅通过 HTTPS 发送
    "session": bool,       # 如果浏览器关闭时过期则为 True
    "sameSite": str,       # "Strict"、"Lax" 或 "None"
    "priority": str,       # "Low"、"Medium" 或 "High"
    "sourceScheme": str,   # "Unset"、"NonSecure" 或 "Secure"
    "sourcePort": int,     # 设置 Cookie 的端口
}
```

### CookieParam 结构

当**设置** Cookie 时，使用字典（只有 `name` 和 `value` 是必需的）：

```python
# 仅包含必需字段的简单 Cookie
cookie = {
    'name': 'user_token',
    'value': 'token_value'
}

# 包含所有可选字段的完整 Cookie
cookie = {
    'name': 'user_token',       # 必需
    'value': 'token_value',     # 必需
    'domain': 'example.com',    # 可选：默认为当前页面域
    'path': '/',                # 可选：默认为 /
    'secure': True,             # 可选：仅 HTTPS
    'httpOnly': True,           # 可选：无 JS 访问
    'sameSite': 'Lax',          # 可选：'Strict'、'Lax' 或 'None'
    'expires': 1735689600,      # 可选：Unix 时间戳
    'priority': 'High',         # 可选：'Low'、'Medium' 或 'High'
}
```

!!! info "可选字段默认行为"
    当您省略可选字段时：
    
    - `domain`：使用当前页面的域
    - `path`：默认为 `/`
    - `secure`：默认为 `False`
    - `httpOnly`：默认为 `False`
    - `sameSite`：浏览器的默认值（通常为 `Lax`）
    - `expires`：会话 Cookie（浏览器关闭时删除）

## Cookie 管理操作

### 设置 Cookie

#### 一次设置多个 Cookie

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def set_multiple_cookies():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        cookies = [
            {
                'name': 'session_id',
                'value': 'xyz789',
                'domain': 'example.com',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Strict'
            },
            {
                'name': 'preferences',
                'value': 'dark_mode=true',
                'domain': 'example.com',
                'path': '/settings'
            },
            {
                'name': 'analytics',
                'value': 'tracking_id_12345',
                'domain': 'example.com',
                'expires': 1735689600  # 在特定日期过期
            }
        ]
        
        await tab.set_cookies(cookies)
        print(f"设置了 {len(cookies)} 个 Cookie")

asyncio.run(set_multiple_cookies())
```

#### 在特定上下文中设置 Cookie

```python
# 在特定浏览器上下文中设置 Cookie
context_id = await browser.create_browser_context()
await browser.set_cookies(cookies, browser_context_id=context_id)
```

!!! tip "标签页与浏览器方法设置 Cookie"
    - `tab.set_cookies(cookies)`：在标签页的浏览器上下文中设置 Cookie（便捷快捷方式）
    - `browser.set_cookies(cookies, browser_context_id=...)`：使用显式上下文控制设置 Cookie
    
    两种方法都将 Cookie 添加到**整个上下文**，而不仅仅是当前页面。Cookie 将可用于该上下文中的所有标签页。

### 检索 Cookie

#### 获取所有 Cookie（上下文范围）

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def get_cookies_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com')
        
        # 等待页面设置 Cookie
        await asyncio.sleep(2)
        
        # 选项 1：通过标签页获取 Cookie（当前上下文的快捷方式）
        cookies = await tab.get_cookies()
        
        # 选项 2：通过浏览器获取 Cookie（显式上下文控制）
        # cookies = await browser.get_cookies()  # 对于默认上下文与 tab.get_cookies() 相同
        
        print(f"找到 {len(cookies)} 个 Cookie：")
        for cookie in cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
            print(f"    域: {cookie['domain']}, 安全: {cookie['secure']}")

asyncio.run(get_cookies_example())
```

!!! tip "标签页与浏览器方法"
    - `tab.get_cookies()`：从标签页的浏览器上下文返回 Cookie（便捷快捷方式）
    - `browser.get_cookies()`：从默认上下文返回 Cookie（或指定 `browser_context_id`）
    
    两种方法都返回上下文中的**所有 Cookie**，而不仅仅是当前页面域的 Cookie。

!!! warning "隐身模式限制"
    `browser.get_cookies()` 在原生隐身模式（`--incognito` 标志）下**不起作用**。这是 Chrome DevTools Protocol 的限制，`Storage.getCookies` 无法在原生隐身模式下访问 Cookie。
    
    **解决方法：** 改用 `tab.get_cookies()`，它使用 `Network.getCookies` 并在隐身模式下正常工作。

#### 从特定上下文获取 Cookie

```python
# 从特定浏览器上下文获取 Cookie
context_id = await browser.create_browser_context()
cookies = await browser.get_cookies(browser_context_id=context_id)
```

### 删除 Cookie

#### 删除所有 Cookie

```python
# 从当前标签页的上下文删除所有 Cookie
await tab.delete_all_cookies()

# 从特定上下文删除所有 Cookie
await browser.delete_all_cookies(browser_context_id=context_id)
```

!!! warning "Cookie 立即删除"
    当您删除 Cookie 时，它们会立即从浏览器中移除。网站可能直到下一次请求或页面重新加载才会检测到这一点。

## 实际用例

### 1. 持久登录会话

跨脚本运行重用身份验证 Cookie：

```python
import asyncio
import json
from pathlib import Path
from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('cookies.json')

async def save_cookies_after_login():
    """登录并保存 Cookie 供将来使用。"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/login')
        
        # 执行登录（简化）
        email = await tab.find(id='email')
        password = await tab.find(id='password')
        await email.type_text('user@example.com')
        await password.type_text('secret')
        
        login_btn = await tab.find(id='login')
        await login_btn.click()
        await asyncio.sleep(3)
        
        # 保存 Cookie
        cookies = await browser.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"已将 {len(cookies)} 个 Cookie 保存到 {COOKIE_FILE}")

async def reuse_saved_cookies():
    """加载保存的 Cookie 以跳过登录。"""
    if not COOKIE_FILE.exists():
        print("未找到保存的 Cookie。请先运行 save_cookies_after_login()。")
        return
    
    # 从文件加载 Cookie
    saved_cookies = json.loads(COOKIE_FILE.read_text())
    
    # 转换为简化格式（仅必需字段）
    # 注意：get_cookies() 返回详细的 Cookie 对象，带有只读字段
    # （size、session、sourceScheme 等）。set_cookies() 期望 CookieParam
    # 格式，仅包含可设置的字段。
    cookies_to_set = [
        {
            'name': c['name'],
            'value': c['value'],
            'domain': c['domain'],
            'path': c.get('path', '/'),
            'secure': c.get('secure', False),
            'httpOnly': c.get('httpOnly', False)
        }
        for c in saved_cookies
    ]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 在导航之前设置 Cookie
        await tab.set_cookies(cookies_to_set)
        print(f"从文件加载了 {len(cookies_to_set)} 个 Cookie")
        
        # 导航 - 应该已经登录
        await tab.go_to('https://example.com/dashboard')
        await asyncio.sleep(2)
        
        # 验证登录
        try:
            username = await tab.find(class_name='username')
            print(f"登录为: {await username.text}")
        except Exception:
            print("登录失败 - Cookie 可能已过期")

# 首次运行：登录并保存 Cookie
# asyncio.run(save_cookies_after_login())

# 后续运行：重用 Cookie
asyncio.run(reuse_saved_cookies())
```

!!! note "需要重新格式化 Cookie"
    `get_cookies()` 返回**详细的 `Cookie` 对象**，带有只读属性如 `size`、`session`、`sourceScheme` 和 `sourcePort`。使用 `set_cookies()` 时，您必须提供 **`CookieParam` 格式**，仅包含可设置的字段（`name`、`value`、`domain`、`path`、`secure`、`httpOnly`、`sameSite`、`expires`、`priority`）。
    
    上面示例中的重新格式化步骤是**必不可少的**。将原始 `Cookie` 对象传递给 `set_cookies()` 可能会导致错误或意外行为。

!!! tip "Cookie 过期"
    始终检查保存的 Cookie 是否已过期。会话 Cookie（`session=True`）在浏览器关闭时过期，而持久性 Cookie 有一个您可以验证的 `expires` 时间戳。

### 2. 使用隔离 Cookie 进行多账户测试

每个浏览器上下文维护单独的 Cookie：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_multiple_accounts():
    accounts = [
        {'email': 'user1@example.com', 'cookie_value': 'session_user1'},
        {'email': 'user2@example.com', 'cookie_value': 'session_user2'},
    ]
    
    async with Chrome() as browser:
        initial_tab = await browser.start()
        
        # 默认上下文中的第一个账户
        cookies_user1 = [{
            'name': 'session',
            'value': accounts[0]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await initial_tab.set_cookies(cookies_user1)
        await initial_tab.go_to('https://example.com/dashboard')
        
        # 隔离上下文中的第二个账户
        context2 = await browser.create_browser_context()
        tab2 = await browser.new_tab(browser_context_id=context2)
        
        cookies_user2 = [{
            'name': 'session',
            'value': accounts[1]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await browser.set_cookies(cookies_user2, browser_context_id=context2)
        await tab2.go_to('https://example.com/dashboard')
        
        # 两个用户使用不同的会话同时登录
        print("用户 1 和用户 2 使用隔离的 Cookie 登录")
        
        await asyncio.sleep(5)
        
        # 清理
        await tab2.close()
        await browser.delete_browser_context(context2)

asyncio.run(test_multiple_accounts())
```

### 3. 长时间运行脚本的 Cookie 轮换

定期刷新 Cookie 以避免检测：

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def scrape_with_cookie_rotation():
    urls = [f'https://example.com/page{i}' for i in range(100)]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 最初登录
        await tab.go_to('https://example.com/login')
        # ... 执行登录 ...
        await asyncio.sleep(2)
        
        last_rotation = time.time()
        rotation_interval = 600  # 每 10 分钟轮换一次
        
        for url in urls:
            # 检查是否是轮换 Cookie 的时候
            if time.time() - last_rotation > rotation_interval:
                print("轮换会话...")
                
                # 删除旧 Cookie
                await tab.delete_all_cookies()
                
                # 重新登录或加载新 Cookie
                await tab.go_to('https://example.com/login')
                # ... 再次执行登录 ...
                
                last_rotation = time.time()
            
            # 抓取页面
            await tab.go_to(url)
            await asyncio.sleep(2)
            # ... 提取数据 ...

asyncio.run(scrape_with_cookie_rotation())
```

!!! tip "轮换频率"
    理想的轮换频率取决于您的用例：
    
    - **高安全性网站**：每 5-15 分钟轮换一次
    - **普通网站**：每 30-60 分钟轮换一次
    - **低风险抓取**：每几小时轮换一次


## Cookie 属性参考

| 属性 | 类型 | 描述 | 默认值 |
|-----------|------|-------------|---------|
| `name` | `str` | Cookie 名称 | *必需* |
| `value` | `str` | Cookie 值 | *必需* |
| `domain` | `str` | Cookie 有效的域 | 当前页面域 |
| `path` | `str` | Cookie 有效的路径 | `/` |
| `secure` | `bool` | 仅通过 HTTPS 发送 | `False` |
| `httpOnly` | `bool` | 无法通过 JavaScript 访问 | `False` |
| `sameSite` | `CookieSameSite` | CSRF 保护：`Strict`、`Lax`、`None` | 浏览器默认（`Lax`）|
| `expires` | `float` | Unix 时间戳（0 = 会话 Cookie）| `0`（会话）|
| `priority` | `CookiePriority` | Cookie 优先级：`Low`、`Medium`、`High` | `Medium` |

### SameSite 值

```python
# 在您的 Cookie 字典中直接使用字符串值：

'sameSite': 'Strict'  # 仅为同站点请求发送 Cookie
'sameSite': 'Lax'     # 为顶级导航发送 Cookie（默认）
'sameSite': 'None'    # 为所有请求发送 Cookie（需要 secure=True）

# 或使用枚举获得 IDE 自动完成：
from pydoll.protocol.network.types import CookieSameSite

cookie = {
    'name': 'session',
    'value': 'xyz',
    'sameSite': CookieSameSite.STRICT  # IDE 将自动完成：STRICT、LAX、NONE
}
```

### Priority 值

```python
# 直接使用字符串值：

'priority': 'Low'     # 低优先级（需要空间时首先删除）
'priority': 'Medium'  # 中优先级（默认）
'priority': 'High'    # 高优先级（最后删除）

# 或使用枚举：
from pydoll.protocol.network.types import CookiePriority

cookie = {
    'name': 'session',
    'value': 'xyz',
    'priority': CookiePriority.HIGH  # IDE 将自动完成：LOW、MEDIUM、HIGH
}
```

## 常见模式

### 临时 Cookie 的上下文管理器

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def temporary_cookies(browser, tab, cookies):
    """设置 Cookie，执行代码，然后恢复原始 Cookie。"""
    # 保存当前 Cookie
    original_cookies = await browser.get_cookies()
    
    try:
        # 设置临时 Cookie
        await tab.delete_all_cookies()
        await tab.set_cookies(cookies)
        yield tab
    finally:
        # 恢复原始 Cookie
        await tab.delete_all_cookies()
        cookies_to_restore = [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c.get('path', '/')
            }
            for c in original_cookies
        ]
        await tab.set_cookies(cookies_to_restore)

# 使用
async with temporary_cookies(browser, tab, test_cookies):
    await tab.go_to('https://example.com')
    # ... 使用临时 Cookie 执行操作 ...
# 原始 Cookie 自动恢复
```

!!! tip "使用公共 API"
    此上下文管理器接受 `browser` 和 `tab` 作为参数以使用公共 API。由于 `tab` 不将其父 `browser` 作为公共属性公开，因此显式传递它是访问浏览器级方法的推荐方法。

### Cookie 指纹比较

```python
def cookie_fingerprint(cookies):
    """生成 Cookie 状态的简单指纹。"""
    return {
        'count': len(cookies),
        'domains': set(c['domain'] for c in cookies),
        'names': sorted(c['name'] for c in cookies),
        'secure_count': sum(1 for c in cookies if c.get('secure')),
        'httponly_count': sum(1 for c in cookies if c.get('httpOnly')),
    }

# 比较 Cookie 状态
before = await browser.get_cookies()
await tab.go_to('https://example.com')
after = await browser.get_cookies()

print(f"之前: {cookie_fingerprint(before)}")
print(f"之后: {cookie_fingerprint(after)}")
```

## 安全注意事项

!!! danger "切勿硬编码敏感 Cookie"
    始终从安全存储（环境变量、加密文件、密钥管理器）加载身份验证 Cookie。
    
    ```python
    # ❌ 不好 - 在代码中硬编码
    cookies = [{'name': 'session', 'value': 'abc123secret'}]
    
    # ✅ 好 - 从环境加载
    import os
    cookies = [{
        'name': 'session',
        'value': os.getenv('SESSION_COOKIE'),
        'domain': os.getenv('COOKIE_DOMAIN')
    }]
    ```

!!! warning "Cookie 盗窃保护"
    将 Cookie 保存到磁盘时：
    
    - 使用加密存储（例如，`cryptography` 库）
    - 设置限制性文件权限
    - 切勿将 Cookie 文件提交到版本控制
    - 定期轮换 Cookie

## 最佳实践总结

1. **从真实 Cookie 开始** - 不要在完全干净的浏览器中运行自动化
2. **定期轮换会话** - 避免长时间使用相同的 Cookie
3. **尊重 Cookie 安全属性** - 适当使用 `secure`、`httpOnly`、`sameSite`
4. **保存和重用身份验证 Cookie** - 适当时跳过重复登录
5. **隔离多账户测试的上下文** - 每个上下文都有独立的 Cookie
6. **监控 Cookie 演变** - 真实浏览自然会积累 Cookie
7. **清理过期的 Cookie** - 重用前删除无效 Cookie
8. **使用安全存储** - 加密保存的 Cookie，切勿硬编码密钥

## 另请参阅

- **[浏览器上下文](contexts.md)** - 隔离的 Cookie 环境
- **[HTTP 请求](../network/http-requests.md)** - 浏览器上下文请求自动继承 Cookie
- **[类人交互](../automation/human-interactions.md)** - 将 Cookie 与真实行为结合
- **[API 参考：存储命令](/api/commands/storage_commands/)** - 完整的 CDP Cookie 方法

有效的 Cookie 管理是真实浏览器自动化的基础。通过平衡新鲜度与持久性并尊重安全属性，您可以构建表现得像真实用户一样的自动化，同时保持高效和可维护性。
