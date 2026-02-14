# HTTP/HTTPS SOCKS 代理

本文档深入探讨了 HTTP 和 HTTPS 代理，这是最常见但也是最 **受限** 的代理协议。尽管它们无处不在（几乎每个企业网络都在使用），但 HTTP 代理在安全性和架构上存在根本限制，使其不适用于许多对隐私至关重要的用例。

了解它们在协议层面的工作原理、其安全影响、标头操纵、缓存语义以及现代协议变体（HTTP/2, HTTP/3），对于明智的代理选择和有效的浏览器自动化至关重要。

!!! info "模块导航"
    - **[← 网络基础](./network-fundamentals.md)** - TCP/IP, UDP, OSI 模型
    - **[← 网络与安全概述](./index.md)** - 模块介绍
    - **[→ SOCKS 代理](./socks-proxies.md)** - 更安全的选择
    - **[→ 代理检测](./proxy-detection.md)** - 如何避免被检测
    
    有关实际配置，请参阅 **[代理配置](../../features/configuration/proxy.md)**。

!!! warning "安全限制"
    HTTP 代理在 **OSI 模型的第 7 层（应用层）** 运行。这个定位使其具有：
    
    - 对未加密 HTTP 流量（URL、标头、正文）的 **完全可见性**
    - **修改能力**（可以在传输过程中更改请求/响应）
    - **智能缓存**（理解 HTTP 语义）
    
    但这也意味着它们：
    
    - **可以读取、记录和修改** 所有未加密的 HTTP 流量
    - **无法代理非 HTTP 协议**（FTP, SSH, SMTP, 自定义协议）
    - **必须终止 TLS** 才能检查 HTTPS（破坏端到端加密）
    
    要获得真正的隐私，请使用 **SOCKS5** 或确保端到端 TLS 加密保持完整。

## 简介：第 7 层代理

HTTP 代理是 **应用层代理**，在 **OSI 模型的第 7 层** 运行。与 SOCKS 代理（第 5 层）盲目转发字节不同，HTTP 代理 **理解 HTTP 协议语义**。它们解析请求、解释标头、应用缓存逻辑，并能根据 HTTP 规则修改流量。

**历史背景：**

HTTP 代理出现于 20 世纪 90 年代中期，随着企业网络的发展，组织需要：

1.  **内容过滤** - 拦截不当网站
2.  **带宽优化** - 缓存频繁访问的资源
3.  **访问控制** - 强制执行使用策略
4.  **安全** - 检查流量中的恶意软件

HTTP/1.0 规范（RFC 1945, 1996）正式定义了代理行为，而 HTTP/1.1（RFC 2616, 1999, 后由 RFC 7230-7237 更新）对其进行了重大改进。这些 RFC 定义了代理应如何处理缓存、持久连接和转发语义。

**为什么应用层定位很重要：**

在第 7 层运行意味着 HTTP 代理：

- **能看到完整的 HTTP 请求** - 方法、URL、标头、正文（如果未加密）
- **能做出智能决策** - 基于 `Cache-Control` 进行缓存、重写 URL、压缩响应
- **会留下指纹** - 添加 `Via`、`X-Forwarded-For` 等标头，暴露代理的使用
- **特定于协议** - 只能代理 HTTP/HTTPS，不能代理其他协议

这种与 HTTP 的深度集既是它们的 **优势**（功能丰富），也是它们的 **弱点**（范围受限、隐私问题）。

## HTTP 代理操作：请求转发

HTTP 代理拦截来自客户端的 HTTP 请求，处理它们，然后将其转发到目标服务器。代理同时充当 **服务器**（对客户端而言）和 **客户端**（对目标服务器而言），维持两个独立的 TCP 连接。

### HTTP 代理请求流程

```mermaid
sequenceDiagram
    participant Client as 客户端浏览器
    participant Proxy as HTTP 代理
    participant Server as 目标服务器
    
    Note over Client: 客户端配置为使用代理<br/>(显式代理设置)
    
    Client->>Proxy: GET http://example.com/page HTTP/1.1<br/>Host: example.com<br/>User-Agent: Mozilla/5.0
    Note over Client,Proxy: TCP 连接 #1:<br/>客户端 ⟷ 代理
    
    Note over Proxy: 代理接收完整的 HTTP 请求<br/>解析方法、URL、标头、正文
    
    Note over Proxy: 代理处理：<br/>1. 验证身份<br/>2. 检查缓存 (如果是 GET)<br/>3. 应用访问控制<br/>4. 修改标头
    
    Proxy->>Proxy: 添加代理标头：<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100<br/>X-Real-IP: 192.168.1.100
    
    Proxy->>Server: GET /page HTTP/1.1<br/>Host: example.com<br/>Via: 1.1 proxy.example.com<br/>X-Forwarded-For: 192.168.1.100
    Note over Proxy,Server: TCP 连接 #2:<br/>代理 ⟷ 服务器
    
    Server->>Proxy: HTTP/1.1 200 OK<br/>Content-Type: text/html<br/>Cache-Control: max-age=3600<br/>[响应正文]
    
    Note over Proxy: 代理处理：<br/>1. 缓存响应 (如果可缓存)<br/>2. 过滤内容 (恶意软件、广告)<br/>3. 压缩 (如果 Accept-Encoding)<br/>4. 记录事务
    
    Proxy->>Client: HTTP/1.1 200 OK<br/>Content-Type: text/html<br/>Via: 1.1 proxy.example.com<br/>X-Cache: HIT<br/>[可能修改过的正文]
    
    Note over Client: 客户端看到响应<br/>可能包含代理标头
```

**详细分解：**

**1. 请求发起 (客户端 → 代理)**

客户端向代理发送一个 **完整的 HTTP 请求**，包含 **绝对 URI**（而不仅仅是路径）：

```http
GET http://example.com/page HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: text/html,application/xhtml+xml
Accept-Encoding: gzip, deflate
Connection: keep-alive
```

**与直接请求的关键区别：** `GET` 行包含 **完整的 URL** (`http://example.com/page`)，而不仅仅是路径 (`/page`)。这告诉代理要将请求转发到哪里。仅靠 `Host` 标头是不够的，因为代理可能正在转发到多个域。

!!! tip "绝对 URI vs 相对 URI"
    **直接到服务器**：`GET /page HTTP/1.1`
    **通过代理**：`GET http://example.com/page HTTP/1.1`
    
    这个区别是代理知道目的地的方式。

**2. 代理处理 - 请求分析**

代理 **解析整个 HTTP 请求** 并做出决策：

```python
# 简化的代理处理逻辑
def process_request(request):
    # 1. 身份验证检查
    if not authenticate_user(request.headers.get('Proxy-Authorization')):
        return HTTP_407_PROXY_AUTH_REQUIRED
    
    # 2. 访问控制
    if is_blocked(request.url):
        return HTTP_403_FORBIDDEN
    
    # 3. 缓存检查 (针对 GET 请求)
    if request.method == 'GET':
        cached = check_cache(request.url)
        if cached and not_expired(cached):
            return cached  # 缓存命中 - 无需服务器请求
    
    # 4. 标头修改
    request.headers['Via'] = '1.1 proxy.example.com'
    request.headers['X-Forwarded-For'] = client_ip
    request.headers['X-Real-IP'] = client_ip
    
    # 5. 转发到服务器
    return forward_to_server(request)
```

**3. 请求转发 (代理 → 服务器)**

代理与目标服务器建立一个 **独立的 TCP 连接** 并转发请求。代理可能会修改标头：

**代理添加的标头：**

- `Via: 1.1 proxy.example.com` - 标识链中的代理 (RFC 7230)
- `X-Forwarded-For: 192.168.1.100` - 原始客户端 IP (事实标准)
- `X-Real-IP: 192.168.1.100` - 原始客户端 IP (备选标头)
- `X-Forwarded-Proto: http` - 原始协议 (http vs https)
- `X-Forwarded-Host: example.com` - 原始 `Host` 标头

!!! danger "通过代理标头泄露隐私"
    **这些标头会暴露您正在使用代理！** 检测系统会寻找：
    - 存在 `Via` 标头 → 确认使用代理
    - `X-Forwarded-For` 有多个 IP → 代理链
    - `X-Real-IP` 与连接 IP 不匹配 → 确认使用代理
    
    复杂的代理可以 **剥离这些标头**，但许多默认情况下不会。

**4. 服务器响应 (服务器 → 代理)**

服务器向代理响应：

```http
HTTP/1.1 200 OK
Date: Mon, 01 Jan 2024 12:00:00 GMT
Server: nginx/1.18.0
Content-Type: text/html; charset=UTF-8
Content-Length: 1234
Cache-Control: public, max-age=3600
ETag: "abc123"

<!DOCTYPE html>
<html>...
```

**5. 代理处理 - 响应处理**

代理可以对响应执行各种操作：

```python
def process_response(response, request):
    # 1. 缓存决策
    if should_cache(response):
        cache_entry = {
            'url': request.url,
            'response': response,
            'expires': now() + parse_cache_control(response.headers['Cache-Control'])
        }
        save_to_cache(cache_entry)
    
    # 2. 内容过滤
    if contains_malware(response.body):
        return HTTP_403_FORBIDDEN
    
    # 3. 压缩 (如果客户端支持)
    if 'gzip' in request.headers.get('Accept-Encoding', ''):
        response.body = gzip_compress(response.body)
        response.headers['Content-Encoding'] = 'gzip'
    
    # 4. 标头修改
    response.headers['Via'] = '1.1 proxy.example.com'
    response.headers['X-Cache'] = 'HIT' if from_cache else 'MISS'
    
    # 5. 日志记录
    log_transaction(request, response)
    
    return response
```

**6. 响应交付 (代理 → 客户端)**

代理将（可能修改过的）响应发送回客户端：

```http
HTTP/1.1 200 OK
Date: Mon, 01 Jan 2024 12:00:00 GMT
Content-Type: text/html; charset=UTF-8
Content-Encoding: gzip
Via: 1.1 proxy.example.com
X-Cache: HIT
Age: 120

[压缩后的响应正文]
```

### 关键能力与限制

**HTTP 代理能做什么：**

- **读取整个 HTTP 请求/响应**（如果未加密）
- **修改标头**（添加 `Via`、`X-Forwarded-For`，移除敏感标头）
- 基于 HTTP 语义（`Cache-Control`, `ETag`）**缓存响应**
- **压缩/解压** 内容（gzip, deflate, br）
- **过滤内容**（拦截 URL、扫描恶意软件、移除广告）
- **验证用户身份**（通过 `Proxy-Authorization` 标头）
- **记录所有流量**（访问的 URL、传输的数据、时间）
- **重写 URL**（重定向、规范化）
- **注入内容**（广告、跟踪脚本、警告）

**HTTP 代理不能做什么：**

- **代理非 HTTP 协议**（FTP, SSH, SMTP, WebSocket 升级, 自定义协议）
- **检查 HTTPS 内容** 而不进行 TLS 终止（破坏端到端加密）
- **隐藏您正在使用代理**（除非精心剥离了标头）
- **代理 UDP 流量**（WebRTC, DNS, QUIC）
- 在检查内容的同时 **保持端到端 TLS**（根本上不兼容）

!!! warning "HTTPS 的根本困境"
    HTTP 代理在处理 HTTPS 时面临一个无法解决的选择：
    
    **选项 A：盲隧道（CONNECT 方法）**
    - 代理无法读取/缓存/过滤 HTTPS 内容
    - 保持端到端加密
    - 代理只能看到目标 IP:端口，而不是 URL
    
    **选项 B：TLS 终止（MITM，中间人攻击）**
    - 代理解密 HTTPS，检查内容，然后重新加密
    - 破坏端到端加密
    - 需要在客户端上安装代理的 CA 证书
    - 可通过证书固定、CT 日志检测
    
    大多数企业代理选择选项 B（TLS 终止）以进行内容过滤。大多数注重隐私的代理选择选项 A（盲隧道）。

### HTTP CONNECT 方法：HTTPS 隧道

`CONNECT` 方法（在 RFC 7231 第 4.3.6 节中定义）解决了 HTTPS 问题：HTTP 代理如何转发它无法读取的加密流量？答案是：**成为一个盲目的 TCP 隧道**。

当客户端希望通过代理访问 HTTPS 站点时，它使用 `CONNECT` 请求代理建立一个到目标的 **原始 TCP 隧道**。隧道建立后，代理只是双向转发字节，而不解释它们。它变成了第 4 层（传输层）而不是第 7 层（应用层）。

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server
    
    Note over Client: 客户端想要访问 https://example.com
    
    Client->>Proxy: CONNECT example.com:443 HTTP/1.1<br/>Host: example.com:443<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    Note over Client,Proxy: HTTP 请求 (未加密)
    
    Note over Proxy: 代理验证凭据<br/>检查对 example.com:443 的访问控制
    
    Proxy->>Server: TCP SYN (三次握手)
    Server->>Proxy: TCP SYN-ACK
    Proxy->>Server: TCP ACK
    Note over Proxy,Server: TCP 连接建立
    
    Proxy->>Client: HTTP/1.1 200 Connection Established<br/><br/>(空行 = 隧道准备就绪)
    
    Note right of Proxy: 从此刻起，代理是一个<br/>透明的 TCP 中继 (第 4 层)
    
    Client->>Server: TLS ClientHello (加密握手)
    Note over Client,Server: TLS 1.3 握手
    Server->>Client: TLS ServerHello, 证书等
    
    Note over Proxy: 代理看到加密的字节，<br/>无法解密或检查
    
    Client->>Server: HTTP/2 GET /page<br/>(在 TLS 内部加密)
    Server->>Client: HTTP/2 200 OK<br/>(在 TLS 内部加密)
    
    Note over Proxy: 代理盲目转发<br/>所有加密数据
```

#### CONNECT 请求格式

```http
CONNECT example.com:443 HTTP/1.1
Host: example.com:443
Proxy-Authorization: Basic dXNlcjpwYXNz
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
```

**关键特征：**

1.  **方法**：`CONNECT` (不是 GET/POST)
2.  **请求-URI**：`host:port` (不是像 `/page` 这样的路径)
3.  **需要端口**：通常是 HTTPS 的 `443`，但任何端口都有效
4.  **身份验证**：如果代理需要，则使用 `Proxy-Authorization`
5.  **无请求体**：CONNECT 请求没有正文

#### CONNECT 响应格式

**成功（隧道已建立）：**

```http
HTTP/1.1 200 Connection Established
```

**就是这样！** 只有状态行和一个空行。空行之后，HTTP 对话结束，代理变成一个 **透明的 TCP 隧道**。

**失败响应：**

```http
HTTP/1.1 407 Proxy Authentication Required
Proxy-Authenticate: Basic realm="proxy"

HTTP/1.1 403 Forbidden
Content-Type: text/plain

Access to example.com:443 is blocked by policy.

HTTP/1.1 502 Bad Gateway
Content-Type: text/plain

Cannot establish connection to example.com:443
```

#### CONNECT 成功后会发生什么

一旦代理发送 `200 Connection Established`，它就 **不再是 HTTP 代理**，而是变成一个 **第 4 层的 TCP 中继**。客户端和服务器直接建立 TLS，代理盲目地转发字节：

```python
# 简化的代理隧道实现
def handle_connect(client_socket, target_host, target_port):
    # 1. 建立到目标的 TCP 连接
    server_socket = socket.create_connection((target_host, target_port))
    
    # 2. 向客户端发送 200
    client_socket.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
    
    # 3. 成为透明中继 (双向转发)
    while True:
        # 等待任意一方的数据
        readable, _, _ = select.select([client_socket, server_socket], [], [])
        
        for sock in readable:
            data = sock.recv(8192)
            if not data:
                # 连接关闭
                return
            
            # 将数据转发到另一方
            if sock is client_socket:
                server_socket.send(data)  # 客户端 → 服务器
            else:
                client_socket.send(data)  # 服务器 → 客户端
```

**代理能看到什么：**

- **目标主机名和端口** - 来自 CONNECT 请求
- **连接时间** - 何时建立，开放多久
- **数据量** - 每个方向传输的总字节数
- **连接关闭** - 任意一方终止时

**代理看不到什么：**

- **TLS 握手详情** - 已加密，但存在可观察的模式
- **HTTP 方法/URL** - 在 TLS 内部加密
- **请求/响应标头** - 在 TLS 内部加密
- **响应内容** - 在 TLS 内部加密
- **Cookie, 会话令牌** - 在 TLS 内部加密

!!! tip "TLS 握手指纹"
    虽然代理无法解密 TLS 握手，但它可以 **观察其结构**。`CONNECT` 之后的最初几个数据包揭示了：
    - TLS 版本 (1.2 vs 1.3)
    - ClientHello 大小和时序
    - 密码套件顺序 (通过数据包大小)
    - 使用的扩展 (通过数据包模式)
    
    这使得即使通过 CONNECT 隧道也能进行 **被动 TLS 指纹识别** (JA3)。详情请参阅 [网络指纹](../fingerprinting/network-fingerprinting.md)。

#### CONNECT vs 直接 HTTP 代理

| 方面 | HTTP (无 CONNECT) | HTTPS (CONNECT 隧道) |
|---|---|---|
| **代理可见性** | 完整的 HTTP 请求/响应 | 仅目标 host:port |
| **加密** | 否 (除非 TLS 终止) | 端到端 TLS (客户端 ⟷ 服务器) |
| **缓存** | 是, 基于 HTTP 语义 | 否 (加密内容) |
| **内容过滤** | 是 (可检查/拦截内容) | 否 (只能基于主机名拦截) |
| **标头修改** | 是 (可添加/删除标头) | 否 (加密标头) |
| **URL 可见性** | 完整 URL 可见 | 仅主机名可见 |
| **协议** | 仅 HTTP | 任何基于 TCP 的协议 (HTTPS, SSH, FTP-over-TLS) |

#### CONNECT 的安全影响

**对隐私 (好)：**

- **保持端到端 TLS** - 客户端直接验证服务器证书
- **不可能进行 MITM** (除非客户端信任代理的 CA)
- **证书固定有效** - 客户端看到真实的服务器证书

**对隐私 (坏)：**

- **泄露主机名** - 代理知道您访问了 `example.com:443`
- **可能进行计时分析** - 可观察到流量模式
- **TLS 指纹** - 对 ClientHello 的被动分析

**对企业安全 (坏)：**

- **无法检查内容** - 无法扫描恶意软件、数据丢失
- **对威胁视而不见** - 加密的 C2 流量、数据泄露不可见
- **绕过策略** - 用户可以隧道传输任意协议

**这就是为什么企业代理经常使用 TLS 终止 (MITM) 而不是 CONNECT 隧道的原因。**

#### CONNECT 用于非 HTTPS 协议

虽然 `CONNECT` 主要用于 HTTPS，但它可以隧道传输 **任何基于 TCP 的协议**：

```http
CONNECT mail.example.com:993 HTTP/1.1
Host: mail.example.com:993

[隧道建立，IMAPS 流量开始流动]
```

```http
CONNECT ssh.example.com:22 HTTP/1.1
Host: ssh.example.com:22

[隧道建立，SSH 流量开始流动]
```

这使得支持 `CONNECT` 的 HTTP 代理 **功能惊人地多样化**。它们可以代理 SSH、FTP-over-TLS、IMAPS、SMTPS 和其他加密协议，而不仅仅是 HTTPS。

!!! danger "CONNECT 滥用和限制"
    因为 `CONNECT` 能够隧道传输任意 TCP 连接，许多代理会：

    - **限制允许的端口** (通常只有 HTTPS 的 443)
    - **拦截可疑主机** (已知的恶意软件 C2、Tor 节点)
    - **记录所有 CONNECT 尝试** (用于安全审计)
    - **要求身份验证** (以跟踪用户)
    
    如果您尝试 `CONNECT example.com:22` (SSH)，许多企业代理将返回 `403 Forbidden`。

### HTTP 代理身份验证：访问控制

与 SOCKS 代理（支持在协议握手中进行身份验证）不同，HTTP 代理使用 **HTTP 身份验证标头** 来控制访问。这意味着身份验证是 **在应用层** 使用标准 HTTP 状态码和标头进行的。

身份验证流程遵循 **RFC 7235 (HTTP 身份验证)**，使用 `407 Proxy Authentication Required` 状态码（类似于服务器的 `401 Unauthorized`）和 `Proxy-Authorization` 请求标头（类似于 `Authorization`）。

#### 身份验证流程

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server
    
    Note over Client: 客户端尝试请求<br/>(尚无凭据)
    
    Client->>Proxy: GET http://example.com/ HTTP/1.1<br/>Host: example.com
    
    Note over Proxy: 代理要求身份验证
    
    Proxy->>Client: HTTP/1.1 407 Proxy Authentication Required<br/>Proxy-Authenticate: Basic realm="Corporate Proxy"<br/>Proxy-Authenticate: Digest realm="proxy", nonce="abc123"
    
    Note over Client: 客户端选择身份验证方法<br/>编码凭据<br/>(浏览器可能提示用户)
    
    Client->>Proxy: GET http://example.com/ HTTP/1.1<br/>Host: example.com<br/>Proxy-Authorization: Basic dXNlcjpwYXNz
    
    Note over Proxy: 验证凭据<br/>(检查用户名/密码)
    
    alt 身份验证成功
        Proxy->>Server: GET / HTTP/1.1<br/>Host: example.com<br/>(转发原始请求)
        Server->>Proxy: HTTP/1.1 200 OK<br/>[响应正文]
        Proxy->>Client: HTTP/1.1 200 OK<br/>[响应正文]
    else 身份验证失败
        Proxy->>Client: HTTP/1.1 407 Proxy Authentication Required<br/>(如果凭据无效，则为 403 Forbidden)
    end
```

#### 身份验证方案：详细比较

HTTP 支持多种身份验证方案，每种方案具有不同的安全特性：

| 方案 | RFC | 安全级别 | 机制 | 优点 | 缺点 |
|---|---|---|---|---|---|
| **Basic** | RFC 7617 | 低 | Base64 编码的 `username:password` | 简单, 通用支持 | **明文** (易于解码), 无重放保护 |
| **Digest** | RFC 7616 | 中 | 使用 MD5/SHA-256 的挑战-响应 | 防止明文传输, 重放保护 | 易受彩虹表攻击, 很少实现 |
| **NTLM** | 专有 (微软) | 中 | 挑战-响应 (NT 哈希) | Windows 集成, SSO | 专有, 复杂, 已知漏洞 |
| **Negotiate** | RFC 4559 | 高 | Kerberos/SPNEGO | 强加密, SSO, 相互身份验证 | 设置复杂, 依赖 Active Directory |
| **Bearer** | RFC 6750 | 高 (如果令牌安全) | OAuth 2.0 令牌 | API 友好, 可撤销令牌 | 令牌被盗 = 完全访问, 需要令牌基础设施 |

#### Basic 身份验证：最简单 (也最弱)

**格式：**
```http
Proxy-Authorization: Basic base64(username:password)
```

**示例：**
```python
# 用户名: "user", 密码: "pass"
credentials = "user:pass"
encoded = base64.b64encode(credentials.encode()).decode()
# 结果: "dXNlcjpwYXNz"

# 在 HTTP 标头中:
Proxy-Authorization: Basic dXNlcjpwYXNz
```

**安全问题：**

1.  **Base64 不是加密** - 解码非常简单：
    ```python
    >>> import base64
    >>> base64.b64decode('dXNlcjpwYXNz').decode()
    'user:pass'  # 凭据暴露！
    ```

2.  **在日志中可见** - 代理日志通常包含标头，泄露凭据

3.  **可重放** - 任何拦截到标头的人都可以无限期地重用它

4.  **无完整性保护** - 可以在传输过程中被修改

!!! danger "在未加密连接上使用 Basic Auth"
    通过 HTTP (而不是 HTTPS) 发送 `Proxy-Authorization: Basic` 是 **极其不安全的**：

    - 凭据以明文传输 (base64 不是加密！)
    - 对任何网络观察者可见 (ISP、WiFi 嗅探者、MITM 攻击者)
    - 被中间代理和服务器记录
    
    **始终通过 TLS/HTTPS 使用 Basic Auth**，或使用更安全的方案，如 Digest 或 Negotiate。

**何时使用 Basic：**

- 代理连接通过 TLS 加密 (HTTPS 到代理)
- 快速测试/开发 (绝不用于生产！)
- 没有其他选择的旧系统

#### Digest 身份验证：挑战-响应

**格式：**
```http
# 服务器挑战
Proxy-Authenticate: Digest realm="proxy",
                          qop="auth",
                          nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                          opaque="5ccc069c403ebaf9f0171e9517f40e41"

# 客户端响应
Proxy-Authorization: Digest username="user",
                            realm="proxy",
                            nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                            uri="http://example.com/",
                            qop=auth,
                            nc=00000001,
                            cnonce="0a4f113b",
                            response="6629fae49393a05397450978507c4ef1",
                            opaque="5ccc069c403ebaf9f0171e9517f40e41"
```

**工作原理：**

1.  **代理发送挑战** 带有随机 `nonce` (一次性数字)
2.  **客户端计算哈希**：
    ```python
    HA1 = MD5(username + ":" + realm + ":" + password)
    HA2 = MD5(method + ":" + uri)
    response = MD5(HA1 + ":" + nonce + ":" + nc + ":" + cnonce + ":" + qop + ":" + HA2)
    ```
3.  **代理通过计算相同的哈希并比较** 来验证

**相比 Basic 的安全改进：**
- 密码永不传输 (只有哈希)
- 重放保护 (`nonce` 每次挑战都会改变)
- 完整性保护 (哈希包含方法和 URI)

**遗留问题：**
- MD5 在密码学上很弱 (彩虹表攻击)
- 没有加密 (如果不使用 TLS，内容仍然可见)
- 正确实现起来很复杂

!!! tip "使用 SHA-256 的 Digest"
    RFC 7616 (2015) 更新了 Digest，以支持 SHA-256 代替 MD5，解决了加密弱点。然而，支持仍然有限。许多代理只实现 MD5。

#### NTLM：Windows 集成身份验证

NTLM (NT LAN Manager) 是微软专有的挑战-响应协议，常用于 Windows 企业环境。

**身份验证流程：**

1.  **Type 1 (协商)**：客户端宣布能力
2.  **Type 2 (挑战)**：服务器发送 8 字节挑战
3.  **Type 3 (认证)**：客户端发送 NT 哈希响应

**示例 (简化)：**
```http
# 步骤 1: 协商
Proxy-Authorization: NTLM TlRMTVNTUAABAAAAB4IIogAAAAAAAAAAAAAAAAAAAAAFASgKAAAADw==

# 步骤 2: 挑战
Proxy-Authenticate: NTLM TlRMTVNTUAACAAAADAAMADgAAAAFgooCBqqVKFrKPCMAAAAAAAAAAAAAAAAAAP8=

# 步骤 3: 认证
Proxy-Authorization: NTLM TlRMTVNTUAADAAAAGAAYAEgAAAAYABgAYAAAAAwADAB4AAAACAAIAIQAAAAAAAAAAAAAABVCSUCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==
```

**优点：**

- 无缝的 Windows 集成 (与 Active Directory 的 SSO)
- 不传输密码
- 支持域身份验证

**缺点：**

- 专有 (逆向工程，未标准化)
- 已知的加密弱点 (NTLMv1 已被破解, NTLMv2 易受攻击)
- 协议复杂 (多次往返)
- 绑定连接 (在 HTTP/2 多路复用下会中断)

!!! warning "NTLM 安全问题"
    NTLM 有已知的漏洞：
    - **哈希传递攻击**：窃取的哈希可以在不知道密码的情况下进行身份验证
    - **中继攻击**：攻击者将身份验证中继到另一台服务器
    - **弱加密**：NTLMv1 使用 DES (已破解), NTLMv2 使用 MD5 (弱)
    
    微软建议在新部署中使用 **Kerberos** (通过 Negotiate) 代替 NTLM。

#### Negotiate (Kerberos)：企业 SSO

**Negotiate** (RFC 4559) 使用 SPNEGO (简单且受保护的 GSSAPI 协商机制) 在 Kerberos 和 NTLM 之间进行选择，优先使用 Kerberos。

**Kerberos 流程：**

1.  客户端从密钥分发中心 (KDC) 请求 **票据授予票据 (TGT)**
2.  客户端为代理服务请求 **服务票据**
3.  客户端向代理出示服务票据
4.  代理使用 KDC 验证票据

**示例：**
```http
Proxy-Authorization: Negotiate YIIFyQYGKwYBBQUCoIIFvTCCBbmgMDAuBgkqhkiC9xIBAgIGCSqGSIb3EgECAgYKKwYBBAGCNwICHgYKKwYBBAGCNwICCqKCBYMEggV/...
```

**优点：**
- **最强的安全性**：AES 加密, 相互身份验证
- **真正的 SSO**：域用户无需输入密码
- **票据过期**：有时间限制的身份验证
- **审计**：集中的 KDC 日志记录

**缺点：**
- **设置复杂**：需要 Active Directory 基础设施
- **跨平台支持有限**：在 Windows 上最好, macOS/Linux 支持有限
- **时间同步**：需要准确的时钟 (Kerberos 票据对时间敏感)

!!! info "浏览器自动化中的 Kerberos"
    Pydoll (以及大多数无头浏览器) 对 **Kerberos 的支持有限**，因为：
    - 需要操作系统级别的集成 (票据缓存, keytab)
    - 需要加入域的机器
    - 以编程方式配置很复杂
    
    对于 Kerberos 环境中的自动化测试，请考虑使用具有 Basic/Digest 身份验证的 **服务帐户** 代替。

#### 实用 Pydoll 配置

**Basic 身份验证：**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--proxy-server=http://myuser:mypass@proxy.example.com:8080')
# Pydoll 会自动处理 Basic/Digest 等身份验证质询

async with Chrome(options=options) as browser:
    tab = await browser.start()
    await tab.go_to('http://example.com')
```

**通过 Fetch 域进行身份验证 (高级)：**

Pydoll 使用 Chrome 的 **Fetch 域** 来自动处理浏览器支持的任何方案 (Basic, Digest, NTLM, Negotiate) 的代理身份验证：

```python
# Pydoll 内部实现 (简化)
async def handle_auth_required(self, event):
    # 浏览器检测到 407 Proxy Authentication Required
    auth_challenge_id = event['requestId']
    
    # 响应凭据
    await self._execute_command('Fetch.continueWithAuth', {
        'requestId': auth_challenge_id,
        'authChallengeResponse': {
            'response': 'ProvideCredentials',
            'username': self.proxy_username,
            'password': self.proxy_password
        }
    })
```

这种方法适用于 **所有身份验证方案**，而 Pydoll 无需实现特定于协议的逻辑。Chrome 会在内部处理 Digest/NTLM/Negotiate。

!!! tip "身份验证最佳实践"
    - **使用 TLS 加密的代理连接** (HTTPS 代理或 SSH 隧道)
    - API 代理 **首选 Bearer 令牌** (可撤销, 有时限)
    - 如果 TLS 不可用，**使用 Digest** 而不是 Basic
    - 定期 **轮换凭据**
    - **监控身份验证失败** (可能表明凭据被盗)
    
    - **切勿通过 HTTP (未加密连接) 使用 Basic auth**
    - **不要硬编码凭据** (使用环境变量)
    - **不要在代理之间重用凭据**
    - **不要记录 Proxy-Authorization 标头**

## 现代 HTTP 协议与代理

传统的 HTTP/1.1 代理已广为人知，但现代协议引入了新的考量。

### HTTP/2 代理

HTTP/2 引入了多路复用，这从根本上改变了代理处理连接的方式：

**关键差异：**

| 特性 | HTTP/1.1 | HTTP/2 |
|---|---|---|
| **连接** | 每个连接一个请求 (或顺序) | 单个连接上的多个请求 |
| **多路复用** | 否 (队头阻塞) | 是 (并发流) |
| **标头压缩** | 无 | HPACK 压缩 |
| **服务器推送** | 不支持 | 服务器可以推送资源 |
| **代理复杂性** | 简单的请求/响应转发 | 必须管理流优先级 |

**对代理的影响：**

```python
# HTTP/1.1 代理：简单的一对一映射
client_conn_1 → proxy → server_conn_1  # 请求 A
client_conn_2 → proxy → server_conn_2  # 请求 B

# HTTP/2 代理：复杂的流管理
client_conn (流 1,3,5) → proxy → server_conn (流 2,4,6)
#     ↓ 必须维护流 ID 和优先级
```

**性能影响：**

- **积极**：减少连接开销, 更好的带宽利用率
- **消极**：代理必须解析二进制分帧, 管理流状态
- **泄露风险**：流 ID 和优先级可以对客户端行为进行指纹识别

!!! info "HTTP/2 代理检测"
    HTTP/2 多路复用使得在多个用户共享代理时更难将请求与客户端关联，但流元数据（窗口大小、优先级设置）仍可对单个客户端进行指纹识别。

### HTTP/3 (QUIC) 代理

HTTP/3 运行在 QUIC (基于 UDP) 而不是 TCP 之上，带来了新的挑战：

**QUIC 特性：**

| 方面 | TCP + TLS | QUIC (UDP) |
|---|---|---|
| **传输** | TCP (面向连接) | UDP (无连接) |
| **握手** | 单独的 TCP + TLS (2 RTT) | 组合 (0-1 RTT) |
| **队头阻塞** | 是 (TCP 级别) | 否 (仅流级别) |
| **连接迁移** | 不支持 | 支持 (IP 更改后仍可存活) |
| **代理兼容性** | 极好 | 有限 (需要 UDP 支持) |

**对代理的影响：**

1.  **UDP 要求**：传统的 HTTP 代理 (仅 TCP) 无法处理 HTTP/3
2.  **连接迁移**：QUIC 连接可以在 IP 更改后存活，使代理会话管理复杂化
3.  **加密传输**：QUIC 几乎加密了所有内容，包括连接元数据
4.  **CONNECT-UDP**：需要新方法 (RFC 9298) 来代理 QUIC

```python
# 传统代理链
客户端 --TCP--> HTTP 代理 --TCP--> 服务器

# HTTP/3 代理链 (需要 CONNECT-UDP)
客户端 --UDP/QUIC--> 代理 --UDP/QUIC--> 服务器
       (或)
客户端 --TCP/CONNECT-UDP--> 代理 --UDP/QUIC--> 服务器
```

!!! warning "HTTP/3 代理支持"
    大多数传统代理 (包括许多商业服务) 不支持 HTTP/3。当代理不支持 QUIC 时，浏览器通常会回退到 HTTP/2 或 HTTP/1.1。
    
    这种回退可能是一个 **隐私问题**：如果您期望 HTTP/3 的加密元数据，但回退到 HTTP/1.1，则可能会通过代理泄露更多信息。

### 协议协商和降级攻击

```mermaid
sequenceDiagram
    participant Client
    participant Proxy
    participant Server
    
    Client->>Proxy: 通过 QUIC 发送 HTTP/3 请求
    Note over Proxy: 代理不支持 UDP/QUIC
    Proxy->>Client: 连接失败
    
    Client->>Proxy: 回退到 TCP 上的 HTTP/2
    Note over Proxy: 代理支持 HTTP/2
    Proxy->>Server: 转发为 HTTP/1.1
    Note over Proxy: 服务器元数据对代理可见
    
    Server->>Proxy: HTTP/1.1 响应
    Proxy->>Client: 升级为 HTTP/2 响应
```

**安全注意事项：**

- **降级攻击**：攻击者强制回退到不太安全的协议
- **元数据泄露**：HTTP/1.1 暴露了 HTTP/3 会加密的标头
- **性能下降**：降级中失去多路复用的好处

!!! tip "现代协议最佳实践"
    - 使用 HTTP/2 和 HTTP/3 测试您的代理，以了解回退行为
    - 监控意外的协议降级 (可能表示 MITM)
    - 如果使用现代 Web 应用，请考虑支持 QUIC 的代理
    - 请注意 HTTP/3 的采用因地区和 CDN 而异

## 总结和关键要点

HTTP 和 HTTPS 代理是 **最常见** 但也是最 **受限** 的代理协议。了解它们的架构、功能和根本的安全限制，对于在浏览器自动化中做出明智决策至关重要。

### 涵盖的核心概念

**1. 第 7 层操作：**

- HTTP 代理在 **应用层** 运行，使其对 HTTP 流量具有完全可见性
- 可以读取/修改 URL、标头、Cookie、请求正文 (对于未加密的 HTTP)
- 特定于协议：**仅适用于 HTTP/HTTPS**，不适用于 FTP/SSH/SMTP/自定义协议

**2. CONNECT 方法：**

- 通过 CONNECT 进行的 **HTTPS 隧道** 将代理转变为 **盲目的 TCP 中继**
- 发送 `200 Connection Established` 后，代理变为第 4 层 (无法检查加密流量)
- 在客户端和服务器之间保持 **端到端 TLS**
- 向代理泄露 **主机名和端口**，但不泄露 URL 或内容

**3. 请求/响应代理：**

- HTTP 代理在请求中使用 **绝对 URI** (`GET http://example.com/page`)
- 维护 **两个 TCP 连接**：客户端↔代理 和 代理↔服务器
- 可以添加标头 (`Via`, `X-Forwarded-For`, `X-Real-IP`) 暴露代理的使用
- 支持基于 HTTP 语义 (`Cache-Control`, `ETag`) 的 **缓存**

**4. 身份验证：**

- 使用 HTTP 状态码 **407** 和 `Proxy-Authorization` 标头
- **Basic**：简单但不安全 (base64 编码, 未加密)
- **Digest**：使用哈希的挑战-响应 (更好, 但 MD5 弱)
- **NTLM**：Windows 集成 (复杂, 专有)
- **Negotiate/Kerberos**：最强 (企业 SSO, Active Directory)

**5. 现代协议：**

- **HTTP/2**：多路复用、二进制分帧、HPACK 压缩
- **HTTP/3/QUIC**：基于 UDP、0-RTT、连接迁移
- 大多数代理 **不支持 HTTP/3** (需要 UDP 中继支持)
- 如果代理缺少 QUIC 支持，浏览器会 **回退** 到 HTTP/2 或 HTTP/1.1

### 安全影响

**优势：**

- **成熟的协议**，广泛支持
- **智能缓存** 减少带宽和延迟
- **内容过滤** 支持恶意软件扫描、广告拦截
- **CONNECT 隧道** 保持 HTTPS 的端到端 TLS

**弱点：**

- **可以读取所有未加密的 HTTP 流量**（URL、标头、正文）
- **添加识别标头** (`Via`, `X-Forwarded-For`) 暴露代理使用
- **无法代理非 HTTP 协议** (FTP, SSH, 自定义)
- **不支持 UDP** (WebRTC 泄露真实 IP)
- **用于检查的 TLS 终止** 破坏端到端加密

### 何时使用 HTTP 代理

**好的用例：**

- 需要内容过滤和监控的 **企业网络**
- 用于带宽优化的 **缓存代理**
- 隐蔽性不重要的 **简单网页抓取**
- 仅支持 HTTP 代理的 **旧系统**
- **基于 URL 的访问控制** (拦截特定域)

**坏的用例：**

- **对隐私要求严格的自动化** (请改用 SOCKS5)
- **非 HTTP 协议** (FTP, SSH, 自定义 → 使用 SOCKS5)
- **WebRTC 应用** (不支持 UDP → 使用 SOCKS5 或 VPN)
- **证书固定** 环境 (CONNECT 会破坏 MITM)
- **隐形自动化** (标头泄露代理使用)

### HTTP 代理 vs SOCKS5：快速决策矩阵

| 需求 | HTTP 代理 | SOCKS5 |
|---|---|---|
| **内容过滤** | **是** | **否** |
| **基于 URL 拦截** | **是** | **否** (仅 IP:port) |
| **缓存** | **是** | **否** |
| **UDP 支持** | **否** | **是** (SOCKS5) |
| **协议灵活性** | **仅 HTTP** | **任何 TCP/UDP** |
| **隐私** | **低** (可见 HTTP) | **高** (盲目转发) |
| **隐蔽性** | **低** (标头泄露) | **高** (透明) |
| **DNS 隐私** | **客户端解析** | **远程解析** |
| **复杂性** | **简单** | **中等** |

**一般建议：**
- **企业/公司**：HTTP 代理 (内容控制, 缓存)
- **隐私/自动化**：SOCKS5 (隐蔽, 协议灵活性)
- **最高安全性**：SOCKS5 over SSH 隧道或 VPN

## 进一步阅读和后续步骤

### 相关文档

**本模块内：**
- **[SOCKS 代理](./socks-proxies.md)** - 协议无关、更安全的 HTTP 代理替代方案
- **[网络基础](./network-fundamentals.md)** - TCP/IP, UDP, WebRTC 理解
- **[代理检测](./proxy-detection.md)** - 如何检测代理以及如何避免
- **[构建代理服务器](./build-proxy.md)** - 从头开始实现 HTTP 和 SOCKS5 代理

**实际用法：**
- **[代理配置 (功能)](../../features/configuration/proxy.md)** - 如何在 Pydoll 中配置代理
- **[浏览器选项](../../features/configuration/browser-options.md)** - 与代理使用相关的浏览器标志

**深度探讨：**
- **[网络指纹](../fingerprinting/network-fingerprinting.md)** - TCP/IP 特征如何通过代理泄露
- **[浏览器指纹](../fingerprinting/browser-fingerprinting.md)** - 尽管有代理，仍进行应用层检测

### 外部参考

**RFC (官方规范)：**

- **RFC 7230-7237** - HTTP/1.1 规范套件 (2014)
  - RFC 7230: 消息语法和路由 (定义代理行为)
  - RFC 7231: 语义和内容 (定义 CONNECT 方法)
  - RFC 7235: 身份验证 (定义 407 和 Proxy-Authorization)
- **RFC 7617** - Basic 身份验证 (2015)
- **RFC 7616** - Digest 身份验证 (2015)
- **RFC 4559** - Negotiate 身份验证 (2006)
- **RFC 7540** - HTTP/2 (2015)
- **RFC 9000** - QUIC 传输协议 (2021)
- **RFC 9114** - HTTP/3 (2022)
- **RFC 9298** - 在 HTTP 中代理 UDP (CONNECT-UDP, 2022)

**标准机构：**

- **IETF (互联网工程任务组)**: https://www.ietf.org/
- **W3C (万维网联盟)**: https://www.w3.org/

**技术资源：**

- **MDN Web Docs - 代理服务器和隧道**: https://developer.mozilla.org/en-US/docs/Web/HTTP/Proxy_servers_and_tunneling
- **Chrome DevTools Protocol - Network 域**: https://chromedevtools.github.io/devtools-protocol/tot/Network/
- **Chrome DevTools Protocol - Fetch 域**: https://chromedevtools.github.io/devtools-protocol/tot/Fetch/

**安全研究：**

- **HTTP/2 Rapid Reset 攻击 (CVE-2023-44487)**：HTTP/2 多路复用漏洞示例
- **NTLM 中继攻击**：微软关于 NTLM 漏洞的安全通告
- **TLS 拦截研究**：关于企业代理 MITM 实践的研究

### 实用测试工具

**代理测试：**

- **curl**: 支持代理的命令行 HTTP 客户端
  ```bash
  curl -x http://proxy:8080 -U user:pass http://example.com
  ```
- **Burp Suite**: 用于安全测试的拦截式 HTTP 代理
- **mitmproxy**: 用于分析的交互式 HTTP/HTTPS 代理

**网络分析：**

- **Wireshark**: 用于观察 HTTP 代理流量的数据包分析器
- **tcpdump**: 命令行数据包捕获
- **Chrome DevTools**: 网络选项卡显示代理标头 (Via, X-Forwarded-For)

**代理检测测试：**

- **https://browserleaks.com/ip**: 显示您的 IP 和代理标头
- **https://whoer.net/**: 全面的代理检测测试
- **https://ipleak.net/**: 测试 DNS 泄露、WebRTC 泄露

### 高级主题 (超出本文档范围)

**代理链：**

- 按顺序使用多个代理以增加匿名性
- 性能和延迟的影响
- Tor 网络作为极端示例

**透明代理：**

- 操作系统级代理配置 (无应用感知)
- WPAD (Web 代理自动发现协议)
- PAC (代理自动配置) 文件

**反向代理：**

- 代表服务器 (而非客户端) 行事的代理
- 负载均衡, CDN, 缓存
- Nginx, HAProxy, Cloudflare 作为示例

**TLS 拦截：**

- 带有自定义 CA 证书的企业代理 MITM
- 证书透明度日志检测拦截
- 证书固定作为对策

---

## 最后的思考

HTTP 代理是一把 **双刃剑**：在内容控制和缓存方面功能强大，但由于其应用层定位，从根本上 **与强隐私不兼容**。

对于需要隐蔽性和灵活性的 **浏览器自动化**，**SOCKS5 几乎总是更好的选择**。仅在以下情况下才应使用 HTTP 代理：

- 您控制代理 (企业环境)
- 您需要 HTTP 特定的功能 (缓存, URL 过滤)
- SOCKS5 不可用

了解 HTTP 代理架构（其功能、限制和安全模型）使您能够 **做出明智的决策**，而不是盲目地复制代理配置。

**后续步骤：**

1. 阅读 **[SOCKS 代理](./socks-proxies.md)** 了解更优越的替代方案
2. 学习 **[代理检测](./proxy-detection.md)** 技术以避免泄露代理使用
3. 使用 **[代理配置](../../features/configuration/proxy.md)** 在 Pydoll 中配置代理

---