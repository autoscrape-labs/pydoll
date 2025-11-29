# 远程连接和混合自动化

Pydoll 允许您通过 WebSocket 连接到已运行的浏览器，实现远程控制和混合自动化场景。这非常适合 CI/CD 管道、容器化环境、调试会话以及将 Pydoll 与现有 CDP 工具集成。

!!! info "无需设置"
    与启动浏览器的传统自动化不同，远程连接让您控制已经运行的浏览器。不需要进程管理！

## 为什么使用远程连接？

远程连接解锁了强大的自动化场景：

| 用例 | 好处 |
|----------|---------|
| **CI/CD 管道** | 连接到浏览器容器而无需管理进程 |
| **Docker 环境** | 控制在单独容器中运行的浏览器 |
| **远程调试** | 自动化远程服务器或虚拟机上的浏览器 |
| **混合工具** | 将 Pydoll 与现有 CDP 基础设施集成 |
| **开发** | 连接到本地浏览器进行快速测试 |
| **多工具自动化** | 在不同工具之间共享浏览器会话 |

## 设置远程浏览器服务器

!!! tip "已经有远程浏览器服务？"
    如果您正在使用云浏览器服务（BrowserStack、Selenium Grid、LambdaTest 等）或已经有一个运行中的 Chrome 实例并带有 WebSocket URL，您可以**跳过整个部分**，直接跳转到[连接方法](#connection-methods)了解如何使用 Pydoll 连接。

在远程连接之前，您需要启动启用了调试并正确配置以接受外部连接的 Chrome。

### 基本服务器设置（Linux）

在服务器上启动带有远程调试的 Chrome：

```bash
# 基本设置 - 仅从 localhost 可访问
google-chrome \
  --remote-debugging-port=9222 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/tmp/chrome-profile

# 服务器设置 - 从其他机器可访问
google-chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --user-data-dir=/tmp/chrome-profile
```

!!! warning "安全关键"
    使用 `--remote-debugging-address=0.0.0.0` 使调试端口可从**任何网络接口**访问。这对于远程连接是必要的，但如果暴露到互联网，会造成重大安全风险。

### 推荐的服务器配置

```bash
# 生产就绪配置
google-chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --headless=new \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --disable-software-rasterizer \
  --disable-extensions \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-client-side-phishing-detection \
  --disable-popup-blocking \
  --disable-prompt-on-repost \
  --disable-sync \
  --metrics-recording-only \
  --no-first-run \
  --safebrowsing-disable-auto-update \
  --user-data-dir=/tmp/chrome-remote-$(date +%s)
```

**关键标志说明：**

| 标志 | 目的 |
|------|---------|
| `--remote-debugging-port=9222` | 在端口 9222 上启用 CDP |
| `--remote-debugging-address=0.0.0.0` | 允许外部连接（安全风险！） |
| `--headless=new` | 无 GUI 运行（服务器模式） |
| `--no-sandbox` | 在 Docker/容器中必需（安全权衡） |
| `--disable-dev-shm-usage` | 防止容器中的 /dev/shm 内存问题 |
| `--disable-gpu` | 无 GPU 加速（建议用于无头模式） |
| `--user-data-dir=/tmp/...` | 每个实例的隔离配置文件 |

!!! warning "关于 --no-sandbox 标志"
    `--no-sandbox` 标志禁用 Chrome 的安全沙箱，该沙箱将浏览器进程与系统隔离。由于内核能力限制，此标志在大多数 Docker/容器环境中是**必需的**，但它带来了安全影响：
    
    - **风险**：移除浏览器和系统之间的隔离
    - **何时使用**：Docker 容器、受限环境
    - **缓解措施**：确保容器级隔离（命名空间、cgroups）并避免以 root 身份运行
    
    仅在绝对必要时考虑使用 `--no-sandbox`，并在容器级别实施额外的安全层。

### Docker 设置

创建容器化的 Chrome 服务器：

!!! tip "使用预构建镜像"
    对于生产环境，考虑使用官方预构建镜像而不是自己构建：
    
    - **Selenium 镜像**：`selenium/standalone-chrome`（包含 WebDriver）
    - **Zenika Alpine Chrome**：`zenika/alpine-chrome`（轻量级，约 200MB）
    - **Browserless**：`browserless/chrome`（生产就绪，带监控）
    
    这些镜像定期更新、经过安全测试，并针对容器环境进行了优化。

**Dockerfile（自定义构建）：**
```dockerfile
FROM ubuntu:22.04

# 安装 Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 暴露调试端口
EXPOSE 9222

# 使用远程调试启动 Chrome
CMD ["google-chrome", \
     "--remote-debugging-port=9222", \
     "--remote-debugging-address=0.0.0.0", \
     "--headless=new", \
     "--no-sandbox", \
     "--disable-dev-shm-usage", \
     "--disable-gpu", \
     "--user-data-dir=/tmp/chrome-profile"]
```

**docker-compose.yml：**
```yaml
services:
  chrome-server:
    build: .
    ports:
      - "127.0.0.1:9222:9222"
    
    # 仅当您需要远程访问且已使用防火墙或代理保护端口时，取消注释下面的行。
    # - "9222:9222"

    shm_size: '2gb'  # 关键：Chrome 使用 /dev/shm 进行共享内存
                      # 默认的 Docker shm_size（64MB）不足
    restart: unless-stopped
    environment:
      - DISPLAY=:99
    networks:
      - automation-network
    # 可选：生产环境的资源限制
    # deploy:
    #   resources:
    #     limits:
    #       cpus: '2'
    #       memory: 4G

  automation-client:
    image: python:3.11
    depends_on:
      - chrome-server
    volumes:
      - ./:/app
    working_dir: /app
    command: python automation_script.py
    environment:
      - CHROME_WS=ws://chrome-server:9222/devtools/browser
    networks:
      - automation-network

networks:
  automation-network:
    driver: bridge
```

**用法：**
```bash
# 启动堆栈
docker-compose up -d

# 检查 Chrome 是否运行
curl http://localhost:9222/json/version

# 从自动化客户端连接（在 Docker 网络内）
# ws://chrome-server:9222/devtools/browser/...
```

### Systemd 服务（Linux 服务器）

创建持久的 Chrome 服务：

**/etc/systemd/system/chrome-remote.service：**
```ini
[Unit]
Description=Chrome Remote Debugging Server
After=network.target

[Service]
Type=simple
User=chrome-user
Group=chrome-user
Environment="DISPLAY=:99"
ExecStart=/usr/bin/google-chrome \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --headless=new \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --user-data-dir=/var/lib/chrome-remote
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**设置和管理：**
```bash
# 创建专用用户
sudo useradd -r -s /bin/false chrome-user
sudo mkdir -p /var/lib/chrome-remote
sudo chown chrome-user:chrome-user /var/lib/chrome-remote

# 安装并启用服务
sudo systemctl daemon-reload
sudo systemctl enable chrome-remote
sudo systemctl start chrome-remote

# 检查状态
sudo systemctl status chrome-remote

# 查看日志
sudo journalctl -u chrome-remote -f

# 重启服务
sudo systemctl restart chrome-remote
```

### 网络安全配置

#### 防火墙规则（iptables）

```bash
# 仅允许特定 IP 访问端口 9222
sudo iptables -A INPUT -p tcp --dport 9222 -s 192.168.1.100 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9222 -j DROP

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4
```

#### 防火墙规则（ufw）

```bash
# 默认拒绝对端口 9222 的所有访问
sudo ufw deny 9222

# 允许特定 IP
sudo ufw allow from 192.168.1.100 to any port 9222

# 允许特定子网
sudo ufw allow from 192.168.1.0/24 to any port 9222

# 启用防火墙
sudo ufw enable
```

#### Nginx 反向代理（带身份验证）

使用 HTTP 身份验证保护 Chrome 调试：

**/etc/nginx/sites-available/chrome-remote：**
```nginx
server {
    listen 80;
    server_name chrome.example.com;

    # 基本身份验证
    auth_basic "Chrome Remote Debugging";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:9222;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

**设置：**
```bash
# 创建密码文件
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 启用站点
sudo ln -s /etc/nginx/sites-available/chrome-remote /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 使用身份验证连接
# ws://admin:password@chrome.example.com/devtools/browser/...
```

### 从另一台计算机连接

配置服务器后，从客户端机器连接：

```python
import asyncio
import aiohttp
from pydoll.browser.chromium import Chrome

async def connect_to_remote_server():
    """连接到远程服务器上运行的 Chrome。"""
    # 服务器 IP 和端口
    server_ip = "192.168.1.100"
    server_port = 9222

    async with aiohttp.ClientSession() as session:
        # 查询服务器的可用目标
        url = f"http://{server_ip}:{server_port}/json/version"
        
        async with session.get(url) as response:
            data = await response.json()
            ws_url = data['webSocketDebuggerUrl']
            
            print(f"服务器信息:")
            print(f"  浏览器: {data.get('Browser')}")
            print(f"  协议: {data.get('Protocol-Version')}")
            print(f"  WebSocket: {ws_url}")
    
    # 2. 连接到浏览器
    chrome = Chrome()
    tab = await chrome.connect(ws_url)
    
    print(f"\n[成功] 已连接到远程 Chrome 服务器！")
    
    # 3. 正常使用
    await tab.go_to('https://example.com')
    title = await tab.execute_script('return document.title')
    print(f"页面标题: {title}")
    
    # 4. 清理
    await chrome.close()

asyncio.run(connect_to_remote_server())
```

### 测试服务器设置

```bash
# 1. 检查 Chrome 是否运行
ps aux | grep chrome

# 2. 检查端口是否在监听
netstat -tulpn | grep 9222
# 或
ss -tulpn | grep 9222

# 3. 测试本地访问
curl http://localhost:9222/json/version

# 4. 测试远程访问（从客户端机器）
curl http://SERVER_IP:9222/json/version

# 5. 检查 WebSocket URL
curl http://SERVER_IP:9222/json/version | jq -r '.webSocketDebuggerUrl'

# 6. 列出所有可用目标（标签页/页面）
curl http://SERVER_IP:9222/json/list
```

### 多实例设置

在不同端口上运行多个 Chrome 实例：

```bash
#!/bin/bash
# start-chrome-pool.sh

for port in 9222 9223 9224 9225; do
    google-chrome \
        --remote-debugging-port=$port \
        --remote-debugging-address=0.0.0.0 \
        --headless=new \
        --no-sandbox \
        --disable-dev-shm-usage \
        --user-data-dir=/tmp/chrome-$port &
    
    echo "在端口 $port 上启动了 Chrome"
done

echo "Chrome 池已就绪。端口: 9222-9225"
```

**使用池的 Python 客户端：**
```python
import asyncio
from pydoll.browser.chromium import Chrome
import aiohttp

async def connect_to_pool(server_ip: str, ports: list[int]):
    """连接到多个 Chrome 实例。"""
    tasks = []
    
    for port in ports:
        task = connect_to_instance(server_ip, port)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

async def connect_to_instance(server_ip: str, port: int):
    """连接到单个 Chrome 实例。"""
    # 获取 WebSocket URL
    async with aiohttp.ClientSession() as session:
        url = f"http://{server_ip}:{port}/json/version"
        async with session.get(url) as response:
            data = await response.json()
            ws_url = data['webSocketDebuggerUrl']
    
    # 连接
    chrome = Chrome()
    tab = await chrome.connect(ws_url)
    
    # 运行自动化
    await tab.go_to('https://example.com')
    title = await tab.execute_script('return document.title')
    
    print(f"端口 {port}: {title}")
    
    await chrome.close()
    return title

# 用法
asyncio.run(connect_to_pool('192.168.1.100', [9222, 9223, 9224, 9225]))
```

## 连接方法

Pydoll 提供两种远程连接方法，每种都适合不同的场景。

### 方法 1：浏览器级连接

使用 WebSocket 端点连接到运行中的浏览器并访问所有打开的标签页：

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def connect_to_remote_browser():
    chrome = Chrome()
    
    # 通过 WebSocket 连接到远程浏览器
    tab = await chrome.connect('ws://localhost:9222/devtools/browser/XXXX')
    
    # 返回的标签页是第一个可用的标签页
    print(f"已连接到标签页: {await tab.execute_script('return document.title')}")
    
    # 您也可以获取所有其他标签页
    all_tabs = await chrome.get_opened_tabs()
    print(f"可用的标签页总数: {len(all_tabs)}")
    
    # 正常使用标签页
    await tab.go_to('https://example.com')
    element = await tab.find(id='main-content')
    text = await element.text
    print(f"内容: {text}")
    
    # 清理
    await chrome.close()

asyncio.run(connect_to_remote_browser())
```

!!! tip "获取 WebSocket URL"
    启动启用了调试的 Chrome：
    ```bash
    # Linux/Mac
    google-chrome --remote-debugging-port=9222
    
    # Windows
    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    ```
    
    **对于本地连接**（同一台机器）：
    
    - 在浏览器中访问 `http://localhost:9222/json/version` 以在 `webSocketDebuggerUrl` 字段中获取 WebSocket URL
    - 或使用 `aiohttp` 以编程方式查询它，如上面的示例所示
    - 对于快速调试，您还可以在启动本地浏览器实例后检查 `browser._connection_port`
    
    **对于远程连接**（不同机器）：
    
    - 从客户端机器查询 `http://SERVER_IP:9222/json/version`
    - 使用响应中的 `webSocketDebuggerUrl`，如果需要，将 `localhost` 替换为实际服务器 IP

### 方法 2：直接元素控制（混合方法）

如果您已经有自己的 CDP 集成或低级工具，可以用 Pydoll 的高级 API 包装现有元素：

```python
import asyncio
import json
from pydoll.connection.connection_handler import ConnectionHandler
from pydoll.elements.web_element import WebElement

async def custom_cdp_integration():
    """将 Pydoll 与您的自定义 CDP 实现一起使用。"""
    # 您现有的 CDP 设置已找到一个元素
    page_ws = 'ws://localhost:9222/devtools/page/ABC123'
    
    # 您已使用 Runtime.evaluate 查找元素
    # 并获得了其 objectId
    element_object_id = '{\"injectedScriptId\":1,\"id\":1}'
    
    # 创建 Pydoll 连接
    connection = ConnectionHandler(ws_address=page_ws)
    
    # 包装元素
    button = WebElement(
        object_id=element_object_id,
        connection_handler=connection
    )
    
    # 使用 Pydoll 的高级方法
    await button.wait_until(is_visible=True, timeout=5)
    await button.wait_until(is_interactable=True)
    
    # 使用真实偏移点击
    await button.click(offset_x=5, offset_y=5)
    
    # 轻松获取计算的属性
    is_enabled = await button.is_enabled()
    bounds = await button.bounds
    
    print(f"按钮已点击！启用: {is_enabled}, 边界: {bounds}")
    
    # 清理
    await connection.close()

asyncio.run(custom_cdp_integration())
```

!!! tip "对象 ID 格式"
    `objectId` 是由 CDP 命令（如 `Runtime.evaluate` 或 `DOM.resolveNode`）返回的字符串。它通常是一个带有 `injectedScriptId` 和 `id` 等字段的 JSON 字符串。

!!! info "两全其美"
    这种混合方法让您利用现有的 CDP 基础设施，同时受益于 Pydoll 的人性化元素 API 来进行交互、等待和属性访问。

## 安全注意事项

!!! danger "生产环境"
    远程调试端口暴露了对浏览器的**完全控制**，包括：
    
    - 访问所有页面和数据
    - 执行任意 JavaScript 的能力
    - Cookie 和会话访问
    - 通过下载访问文件系统
    
    **未经适当的身份验证和网络安全，切勿将调试端口暴露到互联网！**

### 推荐的安全实践

| 实践 | 原因 | 如何做 |
|----------|-----|-----|
| **SSH 隧道** | 加密流量并进行身份验证 | `ssh -L 9222:localhost:9222 user@host` |
| **VPN** | 网络级安全 | 通过企业/私有 VPN 连接 |
| **防火墙规则** | 限制访问 | 仅允许特定 IP |
| **Docker 网络** | 容器隔离 | 使用私有 Docker 网络 |
| **不公开暴露** | 防止攻击 | 在生产环境中切勿绑定到 `0.0.0.0` |

## 进一步阅读

- **[事件系统](event-system.md)** - 监控远程浏览器事件
- **[网络监控](../network/monitoring.md)** - 跟踪远程浏览器中的请求
- **[浏览器选项](../configuration/browser-options.md)** - 在启动前配置本地浏览器

!!! tip "从本地开始，远程扩展"
    使用 `browser.start()` 在本地开发自动化以进行快速迭代，然后使用 `browser.connect()` 部署到生产 CI/CD 管道和容器化环境。