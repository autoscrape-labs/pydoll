# 代理配置

代理对于专业的 Web 自动化至关重要，它可以帮助你绕过速率限制、访问地理限制内容并保持匿名性。Pydoll 提供原生代理支持，并具有自动身份验证处理功能。

!!! info "相关文档"
    - **[浏览器选项](browser-options.md)** - 命令行代理参数
    - **[请求拦截](../network/interception.md)** - 代理身份验证的内部工作原理
    - **[隐蔽自动化](../automation/human-interactions.md)** - 将代理与反检测结合使用
    - **[代理架构深入解析](../../deep-dive/proxy-architecture.md)** - 网络基础知识、协议、安全性和构建自己的代理

## 为什么使用代理？

代理为自动化提供了关键功能：

| 优势 | 描述 | 用例 |
|------|------|------|
| **IP 轮换** | 在多个 IP 之间分配请求 | 避免速率限制，大规模抓取 |
| **地理访问** | 访问区域锁定内容 | 测试地理定向功能，绕过限制 |
| **匿名性** | 隐藏真实 IP 地址 | 注重隐私的自动化，竞争对手分析 |
| **负载分配** | 将流量分散到多个端点 | 大容量抓取，压力测试 |
| **避免封禁** | 防止永久 IP 封禁 | 长期运行的自动化，激进抓取 |

!!! tip "何时使用代理"
    **始终使用代理：**
    
    - 生产环境 Web 抓取（>100 请求/小时）
    - 访问地理限制内容
    - 绕过速率限制或基于 IP 的封锁
    - 从不同地区进行测试
    - 保持匿名性
    
    **可以跳过代理：**
    
    - 本地开发和测试
    - 内部/企业自动化
    - 低容量自动化（<50 请求/天）
    - 抓取自己的基础设施时

## 代理类型

不同的代理协议适用于不同的目的：

| 类型 | 端口 | 身份验证 | 速度 | 安全性 | 用例 |
|------|------|---------|------|--------|------|
| **HTTP** | 80, 8080 | 可选 | 快速 | 低 | 基本 Web 抓取，非敏感数据 |
| **HTTPS** | 443, 8443 | 可选 | 快速 | 中等 | 安全 Web 抓取，加密流量 |
| **SOCKS5** | 1080, 1081 | 可选 | 中等 | 高 | 完整 TCP/UDP 支持，高级用例 |

### HTTP/HTTPS 代理

标准 Web 代理，适用于大多数自动化任务：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def http_proxy_example():
    options = ChromiumOptions()
    
    # HTTP proxy (unencrypted)
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    
    # Or HTTPS proxy (encrypted)
    # options.add_argument('--proxy-server=https://proxy.example.com:8443')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # All traffic goes through proxy
        await tab.go_to('https://httpbin.org/ip')
        
        # Verify proxy IP
        ip = await tab.execute_script('return document.body.textContent')
        print(f"Current IP: {ip}")

asyncio.run(http_proxy_example())
```

**优点：**

- 快速高效
- 在各种服务中广泛支持
- 易于配置

**缺点：**

- HTTP：无加密（流量对代理可见）
- 比 SOCKS5 更容易被检测

### SOCKS5 代理

支持完整 TCP/UDP 的高级代理：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def socks5_proxy_example():
    options = ChromiumOptions()
    
    # SOCKS5 proxy
    options.add_argument('--proxy-server=socks5://proxy.example.com:1080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://httpbin.org/ip')

asyncio.run(socks5_proxy_example())
```

**优点：**

- 协议无关（适用于任何 TCP/UDP 流量）
- 更适合高级用例（WebSockets、WebRTC）
- 更隐蔽（更难检测）

**缺点：**

- 比 HTTP/HTTPS 稍慢
- 在免费/廉价代理服务中不太常见

!!! info "SOCKS4 vs SOCKS5"
    推荐使用 **SOCKS5** 而不是 SOCKS4，因为它：
    
    - 支持身份验证（用户名/密码）
    - 处理 UDP 流量（用于 WebRTC、DNS 等）
    - 提供更好的错误处理
    
    除非你特别需要 SOCKS4（`socks4://`），否则使用 `socks5://`。

## 身份验证代理

Pydoll 自动处理代理身份验证，无需手动干预。

### 身份验证工作原理

当你在代理 URL 中提供凭据时，Pydoll 会：

1. **拦截身份验证挑战** 使用 Fetch 域
2. **自动响应** 提供凭据
3. **继续导航** 无缝衔接

这一切都是透明的，你无需手动处理身份验证！

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def authenticated_proxy_example():
    options = ChromiumOptions()
    
    # Proxy with authentication (username:password)
    options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Authentication handled automatically!
        await tab.go_to('https://example.com')
        print("Connected through authenticated proxy")

asyncio.run(authenticated_proxy_example())
```

!!! tip "凭据格式"
    直接在代理 URL 中包含凭据：

    - HTTP: `http://username:password@host:port`
    - HTTPS: `https://username:password@host:port`
    - SOCKS5: `socks5://username:password@host:port`

    Pydoll 会自动提取并使用这些凭据。

!!! warning "SOCKS5 身份验证限制"
    **Chrome 不原生支持 SOCKS5 身份验证**（[Chromium Issue #40323993](https://issues.chromium.org/issues/40323993)）。嵌入在 `socks5://user:pass@host:port` 中的凭据会被静默忽略 — Chrome 只会向 SOCKS5 代理发送"无需身份验证"的问候。

    这意味着 Pydoll 的自动代理身份验证（通过 `Fetch.authRequired`）**对 SOCKS5 不起作用**，因为 Chrome 从不会为 SOCKS5 连接发出 HTTP 407 质询。

    **解决方案 — 本地代理转发器：**

    运行一个本地 SOCKS5 代理（无需身份验证），将流量转发到远程的身份验证代理。Pydoll 提供了一个即用脚本：

    ```python
    import asyncio
    from pydoll.utils import SOCKS5Forwarder
    from pydoll.browser.chromium import Chrome
    from pydoll.browser.options import ChromiumOptions

    async def main():
        forwarder = SOCKS5Forwarder(
            remote_host='proxy.example.com',
            remote_port=1080,
            username='myuser',
            password='mypass',
            local_port=1081,
        )
        async with forwarder:
            options = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')

            async with Chrome(options=options) as browser:
                tab = await browser.start()
                await tab.go_to('https://httpbin.org/ip')

    asyncio.run(main())
    ```

    转发器负责与远程代理进行用户名/密码握手，而 Chrome 无需身份验证即可连接到本地主机。

    有关此问题的完整技术解释，请参阅 **[SOCKS5 身份验证深入解析](../../deep-dive/network/socks-proxies.md#socks5-身份验证与-chrome)**。

### 身份验证实现细节

Pydoll 在浏览器级别使用 Chrome 的 **Fetch 域** 来拦截和处理身份验证挑战：

```python
# 这是 Pydoll 内部处理的
# 你不需要编写这段代码！

async def _handle_proxy_auth(event):
    """Pydoll 的内部代理身份验证处理器。"""
    if event['params']['authChallenge']['source'] == 'Proxy':
        await browser.continue_request_with_auth(
            request_id=event['params']['requestId'],
            username='user',
            password='pass'
        )
```

!!! info "底层原理"
    有关 Pydoll 如何拦截和处理代理身份验证的技术细节，请参阅：
    
    - **[请求拦截](../network/interception.md)** - Fetch 域和请求处理
    - **[事件系统](../advanced/event-system.md)** - 事件驱动的身份验证

!!! warning "Fetch 域冲突"
    当使用**身份验证代理** + **标签页级别请求拦截**时，请注意：
    
    - Pydoll 在**浏览器级别**启用 Fetch 以进行代理身份验证
    - 如果在**标签页级别**启用 Fetch，它们共享同一个域
    - **解决方案**：在启用标签页级别拦截之前调用一次 `tab.go_to()`
    
    ```python
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 1. 首次导航触发代理身份验证（浏览器级别 Fetch）
        await tab.go_to('https://example.com')
        
        # 2. 然后安全地启用标签页级别拦截
        await tab.enable_fetch_events()
        await tab.on('Fetch.requestPaused', my_interceptor)
        
        # 3. 继续自动化
        await tab.go_to('https://example.com/page2')
    ```
    
    详细信息请参阅 [请求拦截 - 代理 + 拦截](../network/interception.md#private-proxy-request-interception-fetch)。

## 代理绕过列表

从使用代理中排除特定域：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def proxy_bypass_example():
    options = ChromiumOptions()
    
    # Use proxy for most traffic
    options.add_argument('--proxy-server=http://proxy.example.com:8080')
    
    # But bypass proxy for these domains
    options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local,internal.company.com')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Uses proxy
        await tab.go_to('https://external-site.com')
        
        # Bypasses proxy (direct connection)
        await tab.go_to('http://localhost:8000')
        await tab.go_to('http://internal.company.com')

asyncio.run(proxy_bypass_example())
```

**绕过列表模式：**

| 模式 | 匹配 | 示例 |
|------|------|------|
| `localhost` | 仅本地主机 | `http://localhost` |
| `127.0.0.1` | 回环 IP | `http://127.0.0.1` |
| `*.local` | 所有 `.local` 域 | `http://server.local` |
| `internal.company.com` | 特定域 | `http://internal.company.com` |
| `192.168.1.*` | IP 范围 | `http://192.168.1.100` |

!!! tip "何时使用绕过列表"
    为以下情况绕过代理：
    
    - **本地开发服务器**（`localhost`、`127.0.0.1`）
    - **公司内部资源**（VPN、内网）
    - **测试环境**（`.local`、`.test` 域）
    - **高带宽资源**（当代理较慢时）

## PAC（代理自动配置）

使用 PAC 文件实现复杂的代理路由规则：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def pac_proxy_example():
    options = ChromiumOptions()
    
    # Load PAC file from URL
    options.add_argument('--proxy-pac-url=http://proxy.example.com/proxy.pac')
    
    # Or use local PAC file
    # options.add_argument('--proxy-pac-url=file:///path/to/proxy.pac')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(pac_proxy_example())
```

**Example PAC file:**

```javascript
function FindProxyForURL(url, host) {
    // Direct connection for local addresses
    if (isInNet(host, "192.168.0.0", "255.255.0.0") ||
        isInNet(host, "127.0.0.0", "255.0.0.0")) {
        return "DIRECT";
    }
    
    // Use specific proxy for certain domains
    if (dnsDomainIs(host, ".example.com")) {
        return "PROXY proxy1.example.com:8080";
    }
    
    // Default proxy for everything else
    return "PROXY proxy2.example.com:8080";
}
```

!!! info "PAC 文件用例"
    PAC 文件适用于：
    
    - **复杂路由规则**（基于域名、基于 IP）
    - **代理故障转移**（尝试多个代理）
    - **负载均衡**（在代理池中分配）
    - **企业环境**（集中式代理管理）

## 轮换代理

轮换使用多个代理以实现更好的分配：

```python
import asyncio
from itertools import cycle
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def rotating_proxy_example():
    # List of proxies
    proxies = [
        'http://user:pass@proxy1.example.com:8080',
        'http://user:pass@proxy2.example.com:8080',
        'http://user:pass@proxy3.example.com:8080',
    ]
    
    # Cycle through proxies
    proxy_pool = cycle(proxies)
    
    # Scrape multiple URLs with different proxies
    urls = [
        'https://example.com/page1',
        'https://example.com/page2',
        'https://example.com/page3',
    ]
    
    for url in urls:
        # Get next proxy
        proxy = next(proxy_pool)
        
        # Configure options with this proxy
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server={proxy}')
        
        # Use proxy for this browser instance
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            await tab.go_to(url)
            
            title = await tab.execute_script('return document.title')
            print(f"[{proxy.split('@')[1]}] {url}: {title}")

asyncio.run(rotating_proxy_example())
```

!!! tip "代理轮换策略"
    **每个浏览器轮换**（如上）：

    - 每个浏览器实例使用不同的代理
    - 最适合隔离和避免会话冲突
    
    **每个请求轮换**：

    - 更复杂，需要请求拦截
    - 实现方式请参阅 [请求拦截](../network/interception.md)

## 住宅代理 vs 数据中心代理

理解代理类型有助于你选择正确的服务：

| 特性 | 住宅代理 | 数据中心代理 |
|------|---------|-------------|
| **IP 来源** | 真实住宅 ISP | 数据中心 |
| **合法性** | 高（真实用户） | 低（已知范围） |
| **检测风险** | 非常低 | 高 |
| **速度** | 中等（150-500ms） | 非常快（<50ms） |
| **成本** | 昂贵（$5-15/GB） | 便宜（$0.10-1/GB） |
| **最适合** | 反机器人网站、电商 | API、内部工具 |

### 住宅代理

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def residential_proxy_example():
    """Use residential proxy for anti-bot sites."""
    options = ChromiumOptions()
    
    # Residential proxy with high trust score
    options.add_argument('--proxy-server=http://user:pass@residential.proxy.com:8080')
    
    # Combine with stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Access protected site
        await tab.go_to('https://protected-site.com')
        print("Successfully accessed through residential proxy")

asyncio.run(residential_proxy_example())
```

**何时使用住宅代理：**

- 具有强大反机器人保护的网站（Cloudflare、DataDome）
- 电商抓取（Amazon、eBay 等）
- 社交媒体自动化
- 金融服务
- 任何主动封锁数据中心 IP 的网站

### 数据中心代理

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def datacenter_proxy_example():
    """Use fast datacenter proxy for APIs and unprotected sites."""
    options = ChromiumOptions()
    
    # Fast datacenter proxy
    options.add_argument('--proxy-server=http://user:pass@datacenter.proxy.com:8080')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Fast API scraping
        await tab.go_to('https://api.example.com/data')

asyncio.run(datacenter_proxy_example())
```

**何时使用数据中心代理：**

- 无速率限制的公共 API
- 内部/企业自动化
- 没有反机器人措施的网站
- 大容量、速度关键的抓取
- 开发和测试

!!! warning "代理质量很重要"
    **劣质代理**带来的问题比解决的问题更多：
    
    - 响应时间慢（超时）
    - 连接失败（错误率高）
    - IP 被列入黑名单（立即封禁）
    - 真实 IP 泄露（隐私泄露）
    
    **投资高质量代理**，选择信誉良好的提供商。免费代理几乎从不值得使用。

## 测试你的代理

在运行生产环境自动化之前验证代理配置：

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def test_proxy():
    """Test proxy connection and configuration."""
    proxy_url = 'http://user:pass@proxy.example.com:8080'
    
    options = ChromiumOptions()
    options.add_argument(f'--proxy-server={proxy_url}')
    
    try:
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            
            # Test 1: Connection
            print("Testing proxy connection...")
            await tab.go_to('https://httpbin.org/ip', timeout=10)
            
            # Test 2: IP verification
            print("Verifying proxy IP...")
            ip_response = await tab.execute_script('return document.body.textContent')
            print(f"[OK] Proxy IP: {ip_response}")
            
            # Test 3: Geographic location (if available)
            await tab.go_to('https://ipapi.co/json/')
            geo_data = await tab.execute_script('return document.body.textContent')
            print(f"[OK] Geographic data: {geo_data}")
            
            # Test 4: Speed test
            import time
            start = time.time()
            await tab.go_to('https://example.com')
            load_time = time.time() - start
            print(f"[OK] Load time: {load_time:.2f}s")
            
            if load_time > 5:
                print("[WARNING] Slow proxy response time")
            
            print("\n[SUCCESS] All proxy tests passed!")
            
    except asyncio.TimeoutError:
        print("[ERROR] Proxy connection timeout")
    except Exception as e:
        print(f"[ERROR] Proxy test failed: {e}")

asyncio.run(test_proxy())
```

## 延伸阅读

- **[代理架构深入解析](../../deep-dive/proxy-architecture.md)** - 网络基础知识、TCP/UDP、HTTP/2/3、SOCKS5 内部原理、安全分析以及构建自己的代理服务器
- **[浏览器选项](browser-options.md)** - 命令行参数和配置
- **[请求拦截](../network/interception.md)** - 代理身份验证工作原理
- **[浏览器首选项](browser-preferences.md)** - 隐蔽性和指纹识别
- **[上下文](../browser-management/contexts.md)** - 每个上下文使用不同的代理

!!! tip "从简单开始"
    从简单的代理设置开始，彻底测试，然后根据需要添加复杂性（轮换、重试逻辑、监控）。高质量的代理比复杂的轮换策略更重要。
    
    对于那些有兴趣深入了解代理的人，**[代理架构深入解析](../../deep-dive/proxy-architecture.md)** 提供了网络协议、安全注意事项的全面介绍，甚至指导你构建自己的代理服务器。
