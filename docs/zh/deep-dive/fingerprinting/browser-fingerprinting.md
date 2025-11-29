# 浏览器级指纹

本文探讨应用层（HTTP/2、JavaScript、Canvas、WebGL）的指纹。网络级指纹识别 **操作系统和网络堆栈**，而浏览器级指纹则揭示 **特定的浏览器、版本和配置**。

!!! info "模块导航"
    - **[← 指纹概述](./index.md)** - 模块介绍与理念
    - **[← 网络指纹](./network-fingerprinting.md)** - 协议级指纹
    - **[→ 规避技术](./evasion-techniques.md)** - 实用对策
    
    有关实用的浏览器配置，请参阅 **[浏览器选项](../../features/configuration/browser-options.md)** 和 **[浏览器偏好设置](../../features/configuration/browser-preferences.md)**。

!!! warning "一致性是关键"
    浏览器指纹是大多数反机器人系统的 **主要检测层**。一个单一的不一致（例如 Chrome User-Agent 带有 Firefox 的 canvas 伪影）就会触发立即阻止。

## 浏览器级指纹

网络级指纹在协议层运行，而浏览器级指纹则利用浏览器环境本身的特性。本节涵盖用于识别浏览器的现代技术，包括 HTTP/2 分析、JavaScript API、渲染引擎和基于 CDP 的规避策略。

## HTTP/2 指纹

HTTP/2 的二进制分帧和多路复用功能引入了新的指纹向量。像 [Akamai](https://www.akamai.com/) 这样的公司开创了 HTTP/2 指纹技术来检测机器人和自动化工具。

### SETTINGS 帧指纹

HTTP/2 `SETTINGS` 帧在连接初始化期间发送，揭示了特定于实现的偏好。不同的浏览器发送明显不同的设置。

**Chrome SETTINGS (v120+):**

```python
chrome_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_MAX_CONCURRENT_STREAMS': 1000,    # 0x3
    'SETTINGS_INITIAL_WINDOW_SIZE': 6291456,    # 0x4 (6MB)
    'SETTINGS_MAX_HEADER_LIST_SIZE': 262144,    # 0x6
}
```

**Firefox SETTINGS (v120+):**

```python
firefox_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_INITIAL_WINDOW_SIZE': 131072,     # 0x4 (128KB - 小得多!)
    'SETTINGS_MAX_FRAME_SIZE': 16384,           # 0x5 (16KB)
}
```

**主要区别：**

| 设置 | Chrome | Firefox | Safari | curl | 
|---|---|---|---|---|
| **HEADER_TABLE_SIZE** | 65536 | 65536 | 4096 | 4096 |
| **MAX_CONCURRENT_STREAMS** | 1000 | 100 | 100 | 100 |
| **INITIAL_WINDOW_SIZE** | 6291456 | 131072 | 2097152 | 65535 |
| **MAX_FRAME_SIZE** | 16384 | 16384 | 16384 | 16384 |
| **MAX_HEADER_LIST_SIZE** | 262144 | (未设置) | (未设置) | (未设置) |

!!! warning "HTTP/2 设置检测"
    像 `requests`、`httpx` 甚至 `curl` 这样的自动化工具发送的 HTTP/2 设置与真实浏览器 **不同**。这是检测自动化的最简单方法之一。

### WINDOW_UPDATE 帧分析

HTTP/2 使用 `WINDOW_UPDATE` 帧进行流量控制。这些更新的 **大小** 和 **时机** 因实现而异：

```python
# 连接级窗口更新
http2_window_updates = {
    'Chrome': 15 * 1024 * 1024,      # 15MB
    'Firefox': 12 * 1024 * 1024,     # 12MB  
    'curl': 32 * 1024 * 1024,        # 32MB (可疑!)
    'Python httpx': 65535,           # 64KB (默认, 可疑!)
}
```

**检测技术：**

```python
# 服务器端 HTTP/2 指纹伪代码
def fingerprint_http2_client(connection):
    """
    分析 HTTP/2 特性以识别客户端。
    """
    fingerprint = {
        'settings': parse_settings_frame(connection),
        'window_update': get_initial_window_update(connection),
        'priority_tree': analyze_stream_priorities(connection),
        'header_order': get_pseudo_header_order(connection),
    }
    
    # 与已知浏览器指纹进行比较
    if fingerprint['window_update'] > 20_000_000:
        return '可能是 curl 或 httpx (太大)'
    
    if 'MAX_CONCURRENT_STREAMS' not in fingerprint['settings']:
        return '可能是 Python/Go 库 (缺少设置)'
    
    if fingerprint['settings']['INITIAL_WINDOW_SIZE'] == 6291456:
        return '可能是 Chrome/Chromium'
    
    return '未知客户端'
```

### 流优先级和依赖关系

HTTP/2 允许客户端使用 `PRIORITY` 帧指定流优先级和依赖关系。浏览器创建复杂的优先级树来优化页面加载。

**Chrome 的优先级树 (简化):**

```
Stream 0 (connection)
├─ Stream 3 (HTML document) - weight: 256
├─ Stream 5 (CSS) - weight: 220, depends on Stream 3
├─ Stream 7 (JavaScript) - weight: 220, depends on Stream 3
├─ Stream 9 (Image) - weight: 110, depends on Stream 3
└─ Stream 11 (Font) - weight: 110, depends on Stream 3
```

**Python requests/httpx (无优先级):**

```
Stream 0 (connection)
└─ Stream 3 (request) - no priority, no dependencies
```

!!! danger "优先级树不匹配"
    自动化 HTTP 客户端很少实现复杂的优先级树。缺少或过于简单的优先级是自动化的 **强烈指标**。

### 伪标头顺序

HTTP/2 用伪标头（`:method`、`:path`、`:authority`、`:scheme`）替换了 HTTP/1.1 请求行。这些标头的 **顺序** 各不相同：

```python
# Chrome/Edge 顺序
chrome_order = [':method', ':path', ':authority', ':scheme']

# Firefox 顺序  
firefox_order = [':method', ':path', ':authority', ':scheme']

# Safari 顺序
safari_order = [':method', ':scheme', ':path', ':authority']

# curl/httpx 顺序 (通常不同)
automated_order = [':method', ':authority', ':scheme', ':path']
```

**检测代码：**

```python
def detect_pseudo_header_order(headers: list[tuple[str, str]]) -> str:
    """根据伪标头顺序检测客户端。"""
    pseudo_headers = [h[0] for h in headers if h[0].startswith(':')]
    order_str = ','.join(pseudo_headers)
    
    patterns = {
        ':method,:path,:authority,:scheme': 'Chrome/Edge/Firefox',
        ':method,:scheme,:path,:authority': 'Safari',
        ':method,:authority,:scheme,:path': '自动化工具 (curl/httpx)',
    }
    
    return patterns.get(order_str, 'Unknown')
```

### 使用 Python 分析 HTTP/2

```python
from h2.connection import H2Connection
from h2.config import H2Configuration
from h2.events import SettingsAcknowledged, WindowUpdated
import socket
import ssl


class HTTP2Analyzer:
    """
    分析 HTTP/2 连接特性。
    """
    
    def __init__(self, hostname: str, port: int = 443):
        self.hostname = hostname
        self.port = port
        self.settings = {}
        self.window_updates = []
    
    def analyze_server_http2(self) -> dict:
        """
        连接到服务器并分析其 HTTP/2 实现。
        """
        # 创建套接字
        sock = socket.create_connection((self.hostname, self.port))
        
        # 使用 TLS 包装
        context = ssl.create_default_context()
        context.set_alpn_protocols(['h2'])
        sock = context.wrap_socket(sock, server_hostname=self.hostname)
        
        # 创建 H2 连接
        config = H2Configuration(client_side=True)
        conn = H2Connection(config=config)
        conn.initiate_connection()
        
        # 发送初始数据
        sock.sendall(conn.data_to_send())
        
        # 接收服务器前言
        data = sock.recv(65535)
        events = conn.receive_data(data)
        
        # 分析事件
        for event in events:
            if isinstance(event, SettingsAcknowledged):
                # 服务器确认了我们的设置
                pass
            elif isinstance(event, WindowUpdated):
                self.window_updates.append({
                    'stream_id': event.stream_id,
                    'delta': event.delta,
                })
        
        # 提取服务器设置
        server_settings = conn.remote_settings
        
        sock.close()
        
        return {
            'settings': dict(server_settings),
            'window_updates': self.window_updates,
            'alpn_protocol': sock.selected_alpn_protocol(),
        }


# 用法
analyzer = HTTP2Analyzer('www.google.com')
result = analyzer.analyze_server_http2()
print(f"Server HTTP/2 Settings: {result['settings']}")
print(f"Window Updates: {result['window_updates']}")
```

!!! info "HTTP/2 指纹参考"
    - **[Understanding HTTP/2 Fingerprinting](https://www.trickster.dev/post/understanding-http2-fingerprinting/)** by Trickster Dev - HTTP/2 指纹综合指南
    - **[HTTP/2 Fingerprinting](https://lwthiker.com/networks/2022/06/17/http2-fingerprinting.html)** by lwthiker - HTTP/2 特性技术深潜
    - **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)** - 使用 HTTP/2 指纹的商业解决方案
    - **[Multilogin HTTP/2 Fingerprinting Guide](https://multilogin.com/glossary/http2-fingerprinting/)** - HTTP/2 检测的实用视角

## HTTP 标头一致性

除了 HTTP/2 特定的帧之外，标准 HTTP 标头也提供了丰富的指纹数据。关键在于多个特性之间的 **一致性**。

### User-Agent 标头分析

`User-Agent` 标头是最明显的指纹向量，但它也是最常被伪造的：

```python
# 典型 Chrome User-Agent
chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 典型 Firefox User-Agent
firefox_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'

# 可疑 User-Agent (版本过时)
suspicious_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36'
```

**伪造 User-Agent 的常见问题：**

1.  **版本过时**：在 2025 年声称是 Chrome 90
2.  **操作系统不匹配**：声称是 "Windows NT 10.0" 但发送 Linux 的 TTL 值
3.  **平台不一致**：声称是 "Windows" 但 `navigator.platform` 返回 "Linux"
4.  **缺少浏览器功能**：声称是 Chrome 120 但不支持 v110 中引入的功能

### Accept-Language 一致性

`Accept-Language` 标头应与浏览器/操作系统的语言设置匹配：

```python
# 不一致示例
inconsistencies = {
    # 标头说是英语, 但时区是 GMT+9 (日本)
    'accept_language': 'en-US,en;q=0.9',
    'timezone': 'Asia/Tokyo',  # 可疑!
    
    # 标头只有一种语言, 但 navigator.languages 有多种
    'header': 'en-US',
    'navigator_languages': ['en-US', 'en', 'pt-BR', 'pt', 'es'],  # 不匹配!
}
```

**正确配置：**

```python
import pytz
from datetime import datetime

def generate_consistent_accept_language(primary_lang: str, timezone_str: str) -> dict:
    """
    根据时区生成一致的语言标头。
    """
    # 语言-时区映射 (简化)
    tz_to_lang = {
        'America/New_York': 'en-US,en;q=0.9',
        'Europe/London': 'en-GB,en;q=0.9',
        'Asia/Tokyo': 'ja-JP,ja;q=0.9,en;q=0.8',
        'Europe/Berlin': 'de-DE,de;q=0.9,en;q=0.8',
        'America/Sao_Paulo': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    
    expected_lang = tz_to_lang.get(timezone_str, 'en-US,en;q=0.9')
    
    if primary_lang not in expected_lang:
        print(f"Warning: Language {primary_lang} inconsistent with timezone {timezone_str}")
    
    return {
        'accept_language_header': expected_lang,
        'navigator_languages': expected_lang.replace(';q=0.9', '').replace(';q=0.8', '').split(','),
        'timezone': timezone_str,
    }


# 示例
config = generate_consistent_accept_language('ja', 'Asia/Tokyo')
print(config)
# 输出:
# {
#     'accept_language_header': 'ja-JP,ja;q=0.9,en;q=0.8',
#     'navigator_languages': ['ja-JP', 'ja', 'en'],
#     'timezone': 'Asia/Tokyo'
# }
```

### Accept-Encoding 标头

现代浏览器支持特定的压缩算法：

```python
# Chrome/Edge (支持 Brotli)
chrome_encoding = 'gzip, deflate, br, zstd'

# Firefox  
firefox_encoding = 'gzip, deflate, br'

# 旧的/自动工具 (不支持 Brotli)
automated_encoding = 'gzip, deflate'  # 在 2024+ 年可疑
```

!!! warning "Brotli 支持检测"
    任何现代浏览器 (2024+) **必须** 支持 Brotli (`br`)。缺少 Brotli 表明是自动化工具或浏览器版本严重过时。

### Sec-CH-UA (客户端提示)

现代 Chromium 浏览器会发送 [客户端提示](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints) 标头：

```http
Sec-CH-UA: "Chromium";v="120", "Google Chrome";v="120", "Not:A-Brand";v="99"
Sec-CH-UA-Mobile: ?0
Sec-CH-UA-Platform: "Windows"
Sec-CH-UA-Platform-Version: "15.0.0"
Sec-CH-UA-Arch: "x86"
Sec-CH-UA-Bitness: "64"
Sec-CH-UA-Full-Version: "120.0.6099.130"
Sec-CH-UA-Model: ""
```

**一致性检查：**

```python
def validate_client_hints(headers: dict, navigator_props: dict) -> list[str]:
    """
    验证客户端提示与 navigator 属性的一致性。
    """
    issues = []
    
    # 提取 Sec-CH-UA
    sec_ch_ua = headers.get('sec-ch-ua', '')
    sec_ch_platform = headers.get('sec-ch-ua-platform', '').strip('"')
    sec_ch_mobile = headers.get('sec-ch-ua-mobile', '')
    
    # 检查平台一致性
    nav_platform = navigator_props.get('platform', '')
    if sec_ch_platform == 'Windows' and 'Win' not in nav_platform:
        issues.append(f"Platform mismatch: Sec-CH-UA says {sec_ch_platform}, navigator.platform says {nav_platform}")
    
    # 检查移动设备一致性
    nav_mobile = navigator_props.get('userAgentData', {}).get('mobile', False)
    if sec_ch_mobile == '?1' and not nav_mobile:
        issues.append("Mobile mismatch: Sec-CH-UA-Mobile says mobile, but navigator says desktop")
    
    # 检查品牌与 User-Agent 的一致性
    user_agent = headers.get('user-agent', '')
    if 'Chrome' in sec_ch_ua and 'Chrome' not in user_agent:
        issues.append("Brand mismatch: Sec-CH-UA mentions Chrome, but User-Agent doesn't")
    
    return issues


# 示例
headers = {
    'sec-ch-ua': '"Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

navigator = {
    'platform': 'Win32',
    'userAgentData': {'mobile': False},
}

issues = validate_client_hints(headers, navigator)
if issues:
    print("Inconsistencies detected:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Client Hints are consistent")
```

### 标头顺序指纹

HTTP 标头的 **顺序** 是特定于浏览器的，并且在伪造时经常被忽略：

```python
# Chrome 标头顺序 (典型)
chrome_header_order = [
    ':method',
    ':path',
    ':authority',
    ':scheme',
    'cache-control',
    'sec-ch-ua',
    'sec-ch-ua-mobile',
    'sec-ch-ua-platform',
    'upgrade-insecure-requests',
    'user-agent',
    'accept',
    'sec-fetch-site',
    'sec-fetch-mode',
    'sec-fetch-dest',
    'referer',
    'accept-encoding',
    'accept-language',
    'cookie',
]

# Firefox 标头顺序 (不同!)
firefox_header_order = [
    ':method',
    ':path',
    ':authority',
    ':scheme',
    'user-agent',
    'accept',
    'accept-language',
    'accept-encoding',
    'referer',
    'dnt',
    'connection',
    'upgrade-insecure-requests',
    'sec-fetch-dest',
    'sec-fetch-mode',
    'sec-fetch-site',
    'cookie',
]
```

**检测：**

```python
def fingerprint_by_header_order(request_headers: list[tuple[str, str]]) -> str:
    """
    根据标头顺序识别浏览器。
    """
    header_names = [h[0].lower() for h in request_headers]
    order_signature = ','.join(header_names[:10])  # 前 10 个标头
    
    # 已知浏览器签名
    signatures = {
        ':method,:path,:authority,:scheme,cache-control,sec-ch-ua': 'Chrome/Edge',
        ':method,:path,:authority,:scheme,user-agent,accept': 'Firefox',
        'host,connection,accept,user-agent,referer': 'Requests/httpx (可疑!)',
    }
    
    for sig, browser in signatures.items():
        if order_signature.startswith(sig):
            return browser
    
    return 'Unknown (possibly spoofed)'
```

!!! info "HTTP 标头指纹参考"
    - **[HTTP Fingerprinting](https://www.yeswehack.com/learn-bug-bounty/recon-series-http-fingerprinting)** by YesWeHack - HTTP 侦察指南
    - **[Client Hints (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints)** - Sec-CH-UA 标头官方文档
    - **[HTTP Header Order Fingerprinting](https://lwthiker.com/networks/2022/06/17/tls-fingerprinting.html)** - 标头排序技术讨论

## JavaScript 属性指纹

JavaScript 通过 `window` 和 `navigator` 对象提供了对浏览器和系统属性的广泛访问。这些属性是最常被用于指纹识别的属性。

### Navigator 对象属性

`navigator` 对象暴露了数十个揭示浏览器特征的属性：

```javascript
// 核心 navigator 属性
const fingerprint = {
    // User Agent
    userAgent: navigator.userAgent,
    appVersion: navigator.appVersion,
    platform: navigator.platform,
    
    // 语言
    language: navigator.language,
    languages: navigator.languages,
    
    // 硬件
    hardwareConcurrency: navigator.hardwareConcurrency,  // CPU 核心数
    deviceMemory: navigator.deviceMemory,  // RAM (GB, 近似值)
    
    // 功能
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    maxTouchPoints: navigator.maxTouchPoints,
    
    // 供应商
    vendor: navigator.vendor,
    vendorSub: navigator.vendorSub,
    
    // 产品
    product: navigator.product,
    productSub: navigator.productSub,
    
    // 操作系统 CPU (传统, 但仍可用)
    oscpu: navigator.oscpu,  // 仅 Firefox
};
```

**Chrome 特有属性：**

```javascript
// Chrome User Agent Data (Client Hints API)
if (navigator.userAgentData) {
    const uaData = {
        brands: navigator.userAgentData.brands,
        mobile: navigator.userAgentData.mobile,
        platform: navigator.userAgentData.platform,
    };
    
    // 请求高熵值 (需要权限)
    navigator.userAgentData.getHighEntropyValues([
        'architecture',
        'bitness',
        'model',
        'platformVersion',
        'uaFullVersion',
    ]).then(highEntropyValues => {
        console.log('High Entropy Values:', highEntropyValues);
        // {
        //     architecture: "x86",
        //     bitness: "64",
        //     model: "",
        //     platformVersion: "15.0.0",
        //     uaFullVersion: "120.0.6099.130"
        // }
    });
}
```

### 屏幕和窗口属性

显示特性具有高度辨识度：

```javascript
const screenFingerprint = {
    // 屏幕尺寸
    width: screen.width,
    height: screen.height,
    availWidth: screen.availWidth,
    availHeight: screen.availHeight,
    
    // 颜色深度
    colorDepth: screen.colorDepth,
    pixelDepth: screen.pixelDepth,
    
    // 设备像素比 (Retina 显示屏)
    devicePixelRatio: window.devicePixelRatio,
    
    // 窗口尺寸
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    outerWidth: window.outerWidth,
    outerHeight: window.outerHeight,
    
    // 屏幕方向
    orientation: {
        type: screen.orientation?.type,
        angle: screen.orientation?.angle,
    },
};
```

**检测虚拟化/无头环境：**

```python
def detect_headless_chrome(properties: dict) -> list[str]:
    """
    根据属性不一致性检测无头 Chrome。
    """
    issues = []
    
    # 无头 Chrome 的 outerWidth/Height = innerWidth/Height (没有 UI 边框)
    if properties['outerWidth'] == properties['innerWidth']:
        issues.append("outerWidth == innerWidth (对于有头浏览器可疑)")
    
    # 无头环境通常屏幕尺寸 == 窗口尺寸
    if properties['screen']['width'] == properties['innerWidth']:
        issues.append("Screen width == window width (可能是无头)")
    
    # 无头 Chrome 报告特定的 user agent
    if 'HeadlessChrome' in properties.get('userAgent', ''):
        issues.append("User-Agent explicitly says HeadlessChrome")
    
    # 真实浏览器中 navigator.webdriver 应为 undefined
    if properties.get('webdriver') == True:
        issues.append("navigator.webdriver is true (检测到自动化)")
    
    return issues
```

### 插件和 MIME 类型 (传统)

现代浏览器已弃用插件枚举，但它仍然是一个指纹向量：

```javascript
// 插件 (已弃用, 但仍暴露)
const plugins = [];
for (let i = 0; i < navigator.plugins.length; i++) {
    plugins.push({
        name: navigator.plugins[i].name,
        description: navigator.plugins[i].description,
        filename: navigator.plugins[i].filename,
    });
}

// MIME 类型 (已弃用)
const mimeTypes = [];
for (let i = 0; i < navigator.mimeTypes.length; i++) {
    mimeTypes.push({
        type: navigator.mimeTypes[i].type,
        description: navigator.mimeTypes[i].description,
        suffixes: navigator.mimeTypes[i].suffixes,
    });
}
```

!!! warning "插件枚举检测"
    **现代 Chrome/Firefox**：为 `navigator.plugins` 和 `navigator.mimeTypes` 返回空数组以防止指纹识别。
    
    **无头 Chrome**：即使存在插件，也经常返回 **空** 数组，从而暴露了自动化。
    
    **检测**：如果浏览器声称是 Chrome 但没有插件，这是可疑的。

### 时区和日期属性

时区信息出奇地具有揭示性：

```javascript
const timezoneFingerprint = {
    // 时区偏移 (分钟)
    timezoneOffset: new Date().getTimezoneOffset(),
    
    // IANA 时区名称 (例如, "America/New_York")
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    
    // 区域设置
    locale: Intl.DateTimeFormat().resolvedOptions().locale,
    
    // 日期格式化
    dateFormat: new Date().toLocaleDateString(),
    timeFormat: new Date().toLocaleTimeString(),
};
```

**一致性检查：**

```python
def validate_timezone_consistency(tz_offset: int, tz_name: str, accept_language: str) -> list[str]:
    """
    验证时区与语言/位置的一致性。
    """
    issues = []
    
    # 时区-语言预期映射
    tz_to_languages = {
        'America/New_York': ['en-US', 'en'],
        'Europe/London': ['en-GB', 'en'],
        'Asia/Tokyo': ['ja-JP', 'ja'],
        'Europe/Berlin': ['de-DE', 'de'],
    }
    
    expected_langs = tz_to_languages.get(tz_name, [])
    primary_lang = accept_language.split(',')[0].split(';')[0]
    
    if expected_langs and primary_lang not in expected_langs:
        issues.append(f"Timezone {tz_name} inconsistent with language {primary_lang}")
    
    # 时区偏移验证
    expected_offsets = {
        'America/New_York': -300,  # EST (分钟)
        'Europe/London': 0,        # GMT
        'Asia/Tokyo': -540,        # JST
    }
    
    expected_offset = expected_offsets.get(tz_name)
    if expected_offset and tz_offset != expected_offset:
        issues.append(f"Timezone offset {tz_offset} doesn't match {tz_name}")
    
    return issues
```

### 权限和电池 API

一些 API 需要用户许可，但仍可用于指纹识别：

```javascript
// 电池 API (如果可用)
if (navigator.getBattery) {
    navigator.getBattery().then(battery => {
        const batteryInfo = {
            charging: battery.charging,
            chargingTime: battery.chargingTime,
            dischargingTime: battery.dischargingTime,
            level: battery.level,
        };
        // 电池电量可用作熵
    });
}

// 权限
navigator.permissions.query({name: 'geolocation'}).then(result => {
    console.log('Geolocation permission:', result.state);
    // 'granted', 'denied', 'prompt'
});
```

!!! danger "navigator.webdriver 检测"
    `navigator.webdriver` 属性是 **最明显** 的自动化指标：
    
    ```javascript
    if (navigator.webdriver === true) {
        alert('Automation detected!');
    }
    ```
    
    **Selenium, Puppeteer, Playwright** 默认都将其设置为 `true`。CDP 自动化 (如 Pydoll) **不会** 设置此属性，使其更加隐蔽。

### Python 实现：收集浏览器属性

```python
async def collect_browser_fingerprint(tab) -> dict:
    """
    使用 Pydoll 收集全面的浏览器指纹。
    """
    fingerprint = await tab.execute_script(```
        () => {
            return {
                // Navigator
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                maxTouchPoints: navigator.maxTouchPoints,
                vendor: navigator.vendor,
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                webdriver: navigator.webdriver,
                
                // Screen
                screen: {
                    width: screen.width,
                    height: screen.height,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth,
                },
                
                // Window
                window: {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight,
                    devicePixelRatio: window.devicePixelRatio,
                },
                
                // Timezone
                timezone: {
                    offset: new Date().getTimezoneOffset(),
                    name: Intl.DateTimeFormat().resolvedOptions().timeZone,
                },
                
                // Plugins (legacy, but still checked)
                plugins: Array.from(navigator.plugins).map(p => ({
                    name: p.name,
                    description: p.description,
                })),
                
                // User Agent Data (Chrome)
                userAgentData: navigator.userAgentData ? {
                    brands: navigator.userAgentData.brands,
                    mobile: navigator.userAgentData.mobile,
                    platform: navigator.userAgentData.platform,
                } : null,
            };
        }
    ```)
    
    return fingerprint


# 用法示例
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        fingerprint = await collect_browser_fingerprint(tab)
        
        print("Browser Fingerprint:")
        print(f"  User-Agent: {fingerprint['userAgent']}")
        print(f"  Platform: {fingerprint['platform']}")
        print(f"  Languages: {fingerprint['languages']}")
        print(f"  Hardware Concurrency: {fingerprint['hardwareConcurrency']}")
        print(f"  Screen: {fingerprint['screen']['width']}x{fingerprint['screen']['height']}")
        print(f"  Timezone: {fingerprint['timezone']['name']}")
        print(f"  Webdriver: {fingerprint['webdriver']}")

asyncio.run(main())
```

!!! info "JavaScript 属性参考"
    - **[Fingerprint.com: Browser Fingerprinting Techniques](https://fingerprint.com/blog/browser-fingerprinting-techniques/)** - 所有指纹方法的综合指南
    - **[NordLayer: Browser Fingerprinting Guide](https://nordlayer.com/learn/browser-security/browser-fingerprinting/)** - 浏览器指纹如何工作
    - **[AIMultiple: Browser Fingerprinting Best Practices](https://research.aimultiple.com/browser-fingerprinting/)** - 指纹技术的技术分析
    - **[Bureau.id: Top 9 Fingerprinting Techniques](https://www.bureau.id/blog/browser-fingerprinting-techniques)** - 检测方法的详细分解

## Canvas 指纹

Canvas 指纹利用浏览器在 HTML5 `<canvas>` 元素上渲染图形时的细微差异。这些差异源于硬件 (GPU)、显卡驱动、操作系统和浏览器实现的差异。

### Canvas 指纹如何工作

该技术涉及：
1.  在 canvas 上绘制特定文本/形状
2.  使用 `toDataURL()` 或 `getImageData()` 提取像素数据
3.  对结果进行哈希以创建唯一指纹

**影响 canvas 渲染的因素：**
- **GPU 和驱动程序**：不同的 GPU 渲染抗锯齿的方式不同
- **操作系统**：字体渲染各不相同 (Windows 上的 ClearType, Linux 上的 FreeType)
- **浏览器引擎**：WebKit vs Blink vs Gecko 具有不同的渲染管线
- **图形库**：Skia (Chrome) vs Cairo (Firefox)

### Canvas 指纹技术

```javascript
function generateCanvasFingerprint() {
    // 创建 canvas
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    
    const ctx = canvas.getContext('2d');
    
    // 文本渲染 (最具辨识度)
    ctx.textBaseline = 'top';
    ctx.font = '14px "Arial"';
    ctx.textBaseline = 'alphabetic';
    
    // 添加颜色渐变 (暴露渲染差异)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    
    // 添加半透明颜色 (混合差异)
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
    
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
    
    // 提取 data URL
    const dataURL = canvas.toDataURL();
    
    // 生成哈希 (MD5, SHA-256 等)
    return hashString(dataURL);
}

// 演示用的简单哈希函数
function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // 转换为 32 位整数
    }
    return hash.toString(16);
}
```

**为什么使用特定的测试字符串？**

- **"Cwm fjordbank glyphs vext quiz"**：包含不寻常字符的 Pangram (全字母句)，以最大化字体渲染差异
- **表情符号 (😃)**：表情符号渲染在不同系统上差异显著
- **混合字体/大小**：增加熵

### Canvas 指纹唯一性

[USENIX](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery) 的研究表明：
- 两个随机用户拥有相同 canvas 指纹的几率为 **5.5%**
- 当与其他技术结合使用时，唯一性增加到 **99.24%**

### 检测 Canvas 指纹

网站会检测指纹修改尝试：

```javascript
// 检测 canvas 是否被阻止/修改
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;

HTMLCanvasElement.prototype.toDataURL = function() {
    // 检查指纹是否一致
    const result = originalToDataURL.apply(this, arguments);
    
    // 如果每次调用的结果都改变 → 检测到伪造指纹
    return result;
};

// 高级检测: 检查噪声注入
function detectCanvasNoise(canvas) {
    const ctx = canvas.getContext('2d');
    
    // 绘制已知图案
    ctx.fillStyle = '#ff0000';
    ctx.fillRect(0, 0, 10, 10);
    
    // 读回像素
    const imageData = ctx.getImageData(0, 0, 10, 10);
    const pixels = imageData.data;
    
    // 检查是否精确为红色 (255, 0, 0) 或者是否有噪声
    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] !== 255 || pixels[i + 1] !== 0 || pixels[i + 2] !== 0) {
            return true;  // 检测到噪声 = 指纹阻止
        }
    }
    
    return false;  // 干净的 canvas
}
```

### Python Pydoll 实现

```python
import hashlib
import asyncio
from pydoll.browser.chromium import Chrome


async def get_canvas_fingerprint(tab) -> str:
    """
    使用 Pydoll 生成 canvas 指纹。
    """
    fingerprint = await tab.execute_script(```
        () => {
            const canvas = document.createElement('canvas');
            canvas.width = 220;
            canvas.height = 30;
            
            const ctx = canvas.getContext('2d');
            
            // 文本渲染
            ctx.textBaseline = 'top';
            ctx.font = '14px "Arial"';
            ctx.textBaseline = 'alphabetic';
            
            // 色块
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            
            // 带表情符号的文本
            ctx.fillStyle = '#069';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
            
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
            
            // 返回 data URL
            return canvas.toDataURL();
        }
    ```)
    
    # 哈希 canvas 数据
    canvas_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
    
    return canvas_hash


async def compare_canvas_consistency(tab, iterations: int = 3) -> bool:
    """
    检查 canvas 指纹是否一致 (不是随机生成的)。
    """
    fingerprints = []
    
    for _ in range(iterations):
        fp = await get_canvas_fingerprint(tab)
        fingerprints.append(fp)
        await asyncio.sleep(0.1)
    
    # 所有指纹都应该相同
    is_consistent = len(set(fingerprints)) == 1
    
    if not is_consistent:
        print("Canvas fingerprint is inconsistent (possible fake)")
        print(f"  Unique values: {len(set(fingerprints))}")
    
    return is_consistent


# 用法
async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        canvas_fp = await get_canvas_fingerprint(tab)
        print(f"Canvas Fingerprint: {canvas_fp}")
        
        is_consistent = await compare_canvas_consistency(tab)
        print(f"Consistency check: {'PASS' if is_consistent else 'FAIL'}")

asyncio.run(main())
```

!!! warning "Canvas 指纹阻止检测"
    许多反指纹工具会向 canvas 数据中注入 **随机噪声** 以防止跟踪。然而，这会创建一个 **不一致的指纹**，每次请求都会改变，这本身是可检测的！
    
    **检测技术：**
    1.  多次请求 canvas 指纹
    2.  如果值不同 → 检测到噪声注入
    3.  标记为 "指纹阻止 = 可疑行为"

## WebGL 指纹

WebGL 指纹比 Canvas 更强大，因为它暴露了有关 **GPU、驱动程序和图形堆栈** 的详细信息。

### WebGL 渲染器信息

最具辨识度的 WebGL 数据来自 `WEBGL_debug_renderer_info` 扩展：

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) {
        return null;  // 不支持 WebGL
    }
    
    const fingerprint = {
        // 获取调试信息 (最具辨识度)
        debugInfo: (() => {
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            if (ext) {
                return {
                    vendor: gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),
                    renderer: gl.getParameter(ext.UNMASKED_RENDERER_WEBGL),
                };
            }
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER),
            };
        })(),
        
        // 支持的扩展
        extensions: gl.getSupportedExtensions(),
        
        // WebGL 参数
        parameters: {
            version: gl.getParameter(gl.VERSION),
            shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
            maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
            maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
            maxRenderbufferSize: gl.getParameter(gl.MAX_RENDERBUFFER_SIZE),
            maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
            maxVertexUniformVectors: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS),
            maxFragmentUniformVectors: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),
            maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
            aliasedLineWidthRange: gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE),
            aliasedPointSizeRange: gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE),
        },
        
        // 精度格式
        precisionFormats: {
            vertexShader: {
                highFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.HIGH_FLOAT),
                mediumFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.MEDIUM_FLOAT),
                lowFloat: getShaderPrecisionFormat(gl, gl.VERTEX_SHADER, gl.LOW_FLOAT),
            },
            fragmentShader: {
                highFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.HIGH_FLOAT),
                mediumFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.MEDIUM_FLOAT),
                lowFloat: getShaderPrecisionFormat(gl, gl.FRAGMENT_SHADER, gl.LOW_FLOAT),
            },
        },
    };
    
    return fingerprint;
}

function getShaderPrecisionFormat(gl, shaderType, precisionType) {
    const format = gl.getShaderPrecisionFormat(shaderType, precisionType);
    return {
        rangeMin: format.rangeMin,
        rangeMax: format.rangeMax,
        precision: format.precision,
    };
}
```

**示例输出：**

```json
{
    "debugInfo": {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)"
    },
    "extensions": [
        "ANGLE_instanced_arrays",
        "EXT_blend_minmax",
        "EXT_color_buffer_half_float",
        "EXT_disjoint_timer_query",
        "EXT_float_blend",
        "EXT_frag_depth",
        "EXT_shader_texture_lod",
        "EXT_texture_compression_bptc",
        "EXT_texture_filter_anisotropic",
        "WEBKIT_EXT_texture_filter_anisotropic",
        "EXT_sRGB",
        "OES_element_index_uint",
        "OES_fbo_render_mipmap",
        "OES_standard_derivatives",
        "OES_texture_float",
        "OES_texture_float_linear",
        "OES_texture_half_float",
        "OES_texture_half_float_linear",
        "OES_vertex_array_object",
        "WEBGL_color_buffer_float",
        "WEBGL_compressed_texture_s3tc",
        "WEBGL_compressed_texture_s3tc_srgb",
        "WEBGL_debug_renderer_info",
        "WEBGL_debug_shaders",
        "WEBGL_depth_texture",
        "WEBGL_draw_buffers",
        "WEBGL_lose_context",
        "WEBGL_multi_draw"
    ],
    "parameters": {
        "version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
        "shadingLanguageVersion": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
        "maxTextureSize": 16384,
        "maxViewportDims": [32767, 32767],
        "maxRenderbufferSize": 16384
    }
}
```

### WebGL 渲染指纹

除了元数据，WebGL 还可以渲染 3D 场景并分析像素输出：

```javascript
function getWebGLRenderFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    
    const gl = canvas.getContext('webgl');
    
    // 顶点着色器
    const vertexShaderSource = `
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
    `;
    
    // 带渐变的片段着色器
    const fragmentShaderSource = `
        precision mediump float;
        void main() {
            gl_FragColor = vec4(gl_FragCoord.x/256.0, gl_FragCoord.y/128.0, 0.5, 1.0);
        }
    `;
    
    // 编译着色器
    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);
    
    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);
    
    // 链接程序
    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    gl.useProgram(program);
    
    // 绘制三角形
    const vertices = new Float32Array([-1, -1, 1, -1, 0, 1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
    
    const position = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
    
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    
    // 提取渲染图像
    return canvas.toDataURL();
}
```

### Python Pydoll 实现

```python
async def get_webgl_fingerprint(tab) -> dict:
    """
    收集 WebGL 指纹数据。
    """
    fingerprint = await tab.execute_script(```
        () => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return null;
            }
            
            // 获取调试信息
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const vendor = debugInfo ? 
                gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 
                gl.getParameter(gl.VENDOR);
            const renderer = debugInfo ? 
                gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 
                gl.getParameter(gl.RENDERER);
            
            return {
                vendor: vendor,
                renderer: renderer,
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                extensions: gl.getSupportedExtensions(),
                maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
            };
        }
    ```)
    
    return fingerprint


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        webgl_fp = await get_webgl_fingerprint(tab)
        
        if webgl_fp:
            print("WebGL Fingerprint:")
            print(f"  Vendor: {webgl_fp['vendor']}")
            print(f"  Renderer: {webgl_fp['renderer']}")
            print(f"  Version: {webgl_fp['version']}")
            print(f"  Extensions: {len(webgl_fp['extensions'])} available")
        else:
            print("WebGL not available")

asyncio.run(main())
```

!!! danger "WebGL 指纹阻止"
    一些隐私工具试图通过以下方式阻止 WebGL 指纹：
    
    1.  **禁用 WEBGL_debug_renderer_info 扩展**
    2.  **返回通用的 "SwiftShader" 渲染器** (软件渲染)
    3.  **伪造 GPU 供应商/渲染器字符串**
    
    然而，**缺少或通用的 WebGL 数据是可疑的**，因为：
    - 97% 的浏览器支持 WebGL
    - 通用渲染器存在性能影响 (可通过计时检测)
    - 缺少常见扩展会暴露阻止行为

!!! info "Canvas & WebGL 指纹参考"
    - **[USENIX: Pixel Perfect Browser Fingerprinting](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery)** - 关于 canvas 指纹的原始学术研究 (2012)
    - **[Fingerprint.com: Canvas Fingerprinting](https://fingerprint.com/blog/canvas-fingerprinting/)** - 现代 canvas 指纹技术
    - **[BrowserLeaks WebGL Report](https://browserleaks.com/webgl)** - 测试你的 WebGL 指纹
    - **[Chromium WebGL Implementation](https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/modules/webgl/)** - Chromium 中 WebGL 的源代码