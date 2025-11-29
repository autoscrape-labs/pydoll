# Browser-Level Fingerprinting

This document explores fingerprinting at the application layer (HTTP/2, JavaScript, Canvas, WebGL). While network-level fingerprinting identifies the **OS and network stack**, browser-level fingerprinting reveals the **specific browser, version, and configuration**.

!!! info "Module Navigation"
    - **[← Fingerprinting Overview](./index.md)** - Module introduction and philosophy
    - **[← Network Fingerprinting](./network-fingerprinting.md)** - Protocol-level fingerprinting
    - **[→ Evasion Techniques](./evasion-techniques.md)** - Practical countermeasures
    
    For practical browser configuration, see **[Browser Options](../../features/configuration/browser-options.md)** and **[Browser Preferences](../../features/configuration/browser-preferences.md)**.

!!! warning "Consistency is Key"
    Browser fingerprinting is **the primary detection layer** for most anti-bot systems. A single inconsistency (like a Chrome User-Agent with Firefox canvas artifacts) triggers immediate blocking.

## Browser-Level Fingerprinting

While network-level fingerprinting operates at the protocol level, browser-level fingerprinting exploits characteristics of the browser environment itself. This section covers modern techniques used to identify browsers, including HTTP/2 analysis, JavaScript APIs, rendering engines, and CDP-based evasion strategies.

## HTTP/2 Fingerprinting

HTTP/2's binary framing and multiplexing capabilities introduced new fingerprinting vectors. Companies like [Akamai](https://www.akamai.com/) pioneered HTTP/2 fingerprinting techniques to detect bots and automated tools.

### SETTINGS Frame Fingerprinting

The HTTP/2 `SETTINGS` frame sent during connection initialization reveals implementation-specific preferences. Different browsers send distinctly different settings.

**Chrome SETTINGS (as of v120+):**

```python
chrome_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_MAX_CONCURRENT_STREAMS': 1000,    # 0x3
    'SETTINGS_INITIAL_WINDOW_SIZE': 6291456,    # 0x4 (6MB)
    'SETTINGS_MAX_HEADER_LIST_SIZE': 262144,    # 0x6
}
```

**Firefox SETTINGS (as of v120+):**

```python
firefox_http2_settings = {
    'SETTINGS_HEADER_TABLE_SIZE': 65536,        # 0x1
    'SETTINGS_INITIAL_WINDOW_SIZE': 131072,     # 0x4 (128KB - much smaller!)
    'SETTINGS_MAX_FRAME_SIZE': 16384,           # 0x5 (16KB)
}
```

**Key differences:**

| Setting | Chrome | Firefox | Safari | curl | 
|---------|--------|---------|--------|------|
| **HEADER_TABLE_SIZE** | 65536 | 65536 | 4096 | 4096 |
| **MAX_CONCURRENT_STREAMS** | 1000 | 100 | 100 | 100 |
| **INITIAL_WINDOW_SIZE** | 6291456 | 131072 | 2097152 | 65535 |
| **MAX_FRAME_SIZE** | 16384 | 16384 | 16384 | 16384 |
| **MAX_HEADER_LIST_SIZE** | 262144 | (not set) | (not set) | (not set) |

!!! warning "HTTP/2 Settings Detection"
    Automated tools like `requests`, `httpx`, and even `curl` send **different** HTTP/2 settings than real browsers. This is one of the easiest ways to detect automation.

### WINDOW_UPDATE Frame Analysis

HTTP/2 uses `WINDOW_UPDATE` frames for flow control. The **size** and **timing** of these updates vary by implementation:

```python
# Connection-level window updates
http2_window_updates = {
    'Chrome': 15 * 1024 * 1024,      # 15MB
    'Firefox': 12 * 1024 * 1024,     # 12MB  
    'curl': 32 * 1024 * 1024,        # 32MB (suspicious!)
    'Python httpx': 65535,           # 64KB (default, suspicious!)
}
```

**Detection technique:**

```python
# Server-side HTTP/2 fingerprinting pseudocode
def fingerprint_http2_client(connection):
    """
    Analyze HTTP/2 characteristics to identify client.
    """
    fingerprint = {
        'settings': parse_settings_frame(connection),
        'window_update': get_initial_window_update(connection),
        'priority_tree': analyze_stream_priorities(connection),
        'header_order': get_pseudo_header_order(connection),
    }
    
    # Compare against known browser fingerprints
    if fingerprint['window_update'] > 20_000_000:
        return 'Likely curl or httpx (too large)'
    
    if 'MAX_CONCURRENT_STREAMS' not in fingerprint['settings']:
        return 'Likely Python/Go library (missing setting)'
    
    if fingerprint['settings']['INITIAL_WINDOW_SIZE'] == 6291456:
        return 'Likely Chrome/Chromium'
    
    return 'Unknown client'
```

### Stream Priority and Dependency

HTTP/2 allows clients to specify stream priorities and dependencies using `PRIORITY` frames. Browsers create sophisticated priority trees to optimize page loading.

**Chrome's priority tree (simplified):**

```
Stream 0 (connection)
├─ Stream 3 (HTML document) - weight: 256
├─ Stream 5 (CSS) - weight: 220, depends on Stream 3
├─ Stream 7 (JavaScript) - weight: 220, depends on Stream 3
├─ Stream 9 (Image) - weight: 110, depends on Stream 3
└─ Stream 11 (Font) - weight: 110, depends on Stream 3
```

**Python requests/httpx (no priorities):**

```
Stream 0 (connection)
└─ Stream 3 (request) - no priority, no dependencies
```

!!! danger "Priority Tree Mismatch"
    Automated HTTP clients rarely implement sophisticated priority trees. Missing or simplistic priorities are **strong indicators** of automation.

### Pseudo-Header Ordering

HTTP/2 replaces HTTP/1.1 request line with pseudo-headers (`:method`, `:path`, `:authority`, `:scheme`). The **order** of these headers varies:

```python
# Chrome/Edge order
chrome_order = [':method', ':path', ':authority', ':scheme']

# Firefox order  
firefox_order = [':method', ':path', ':authority', ':scheme']

# Safari order
safari_order = [':method', ':scheme', ':path', ':authority']

# curl/httpx order (often different)
automated_order = [':method', ':authority', ':scheme', ':path']
```

**Detection code:**

```python
def detect_pseudo_header_order(headers: list[tuple[str, str]]) -> str:
    """Detect client based on pseudo-header order."""
    pseudo_headers = [h[0] for h in headers if h[0].startswith(':')]
    order_str = ','.join(pseudo_headers)
    
    patterns = {
        ':method,:path,:authority,:scheme': 'Chrome/Edge/Firefox',
        ':method,:scheme,:path,:authority': 'Safari',
        ':method,:authority,:scheme,:path': 'Automated tool (curl/httpx)',
    }
    
    return patterns.get(order_str, 'Unknown')
```

### Analyzing HTTP/2 with Python

```python
from h2.connection import H2Connection
from h2.config import H2Configuration
from h2.events import SettingsAcknowledged, WindowUpdated
import socket
import ssl


class HTTP2Analyzer:
    """
    Analyze HTTP/2 connection characteristics.
    """
    
    def __init__(self, hostname: str, port: int = 443):
        self.hostname = hostname
        self.port = port
        self.settings = {}
        self.window_updates = []
    
    def analyze_server_http2(self) -> dict:
        """
        Connect to server and analyze its HTTP/2 implementation.
        """
        # Create socket
        sock = socket.create_connection((self.hostname, self.port))
        
        # Wrap with TLS
        context = ssl.create_default_context()
        context.set_alpn_protocols(['h2'])
        sock = context.wrap_socket(sock, server_hostname=self.hostname)
        
        # Create H2 connection
        config = H2Configuration(client_side=True)
        conn = H2Connection(config=config)
        conn.initiate_connection()
        
        # Send initial data
        sock.sendall(conn.data_to_send())
        
        # Receive server preface
        data = sock.recv(65535)
        events = conn.receive_data(data)
        
        # Analyze events
        for event in events:
            if isinstance(event, SettingsAcknowledged):
                # Server acknowledged our settings
                pass
            elif isinstance(event, WindowUpdated):
                self.window_updates.append({
                    'stream_id': event.stream_id,
                    'delta': event.delta,
                })
        
        # Extract server settings
        server_settings = conn.remote_settings
        
        sock.close()
        
        return {
            'settings': dict(server_settings),
            'window_updates': self.window_updates,
            'alpn_protocol': sock.selected_alpn_protocol(),
        }


# Usage
analyzer = HTTP2Analyzer('www.google.com')
result = analyzer.analyze_server_http2()
print(f"Server HTTP/2 Settings: {result['settings']}")
print(f"Window Updates: {result['window_updates']}")
```

!!! info "HTTP/2 Fingerprinting References"
    - **[Understanding HTTP/2 Fingerprinting](https://www.trickster.dev/post/understanding-http2-fingerprinting/)** by Trickster Dev - Comprehensive guide on HTTP/2 fingerprinting
    - **[HTTP/2 Fingerprinting](https://lwthiker.com/networks/2022/06/17/http2-fingerprinting.html)** by lwthiker - Technical deep-dive into HTTP/2 characteristics
    - **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)** - Commercial solution using HTTP/2 fingerprinting
    - **[Multilogin HTTP/2 Fingerprinting Guide](https://multilogin.com/glossary/http2-fingerprinting/)** - Practical perspective on HTTP/2 detection

## HTTP Headers Consistency

Beyond HTTP/2-specific frames, standard HTTP headers provide rich fingerprinting data. The key is **consistency** across multiple characteristics.

### User-Agent Header Analysis

The `User-Agent` header is the most obvious fingerprinting vector, but it's also the most commonly spoofed:

```python
# Typical Chrome User-Agent
chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Typical Firefox User-Agent
firefox_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'

# Suspicious User-Agent (outdated version)
suspicious_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.0.0 Safari/537.36'
```

**Common issues with spoofed User-Agents:**

1. **Outdated version**: Claims Chrome 90 in 2025
2. **OS mismatch**: Claims "Windows NT 10.0" but sends Linux TTL values
3. **Platform inconsistency**: Claims "Windows" but `navigator.platform` returns "Linux"
4. **Missing browser features**: Claims Chrome 120 but doesn't support features introduced in v110

### Accept-Language Consistency

The `Accept-Language` header should match browser/OS language settings:

```python
# Inconsistency examples
inconsistencies = {
    # Header says English, but timezone is GMT+9 (Japan)
    'accept_language': 'en-US,en;q=0.9',
    'timezone': 'Asia/Tokyo',  # Suspicious!
    
    # Header has single language, but navigator.languages has many
    'header': 'en-US',
    'navigator_languages': ['en-US', 'en', 'pt-BR', 'pt', 'es'],  # Mismatch!
}
```

**Proper configuration:**

```python
import pytz
from datetime import datetime

def generate_consistent_accept_language(primary_lang: str, timezone_str: str) -> dict:
    """
    Generate consistent language headers based on timezone.
    """
    # Language-timezone mappings (simplified)
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


# Example
config = generate_consistent_accept_language('ja', 'Asia/Tokyo')
print(config)
# Output:
# {
#     'accept_language_header': 'ja-JP,ja;q=0.9,en;q=0.8',
#     'navigator_languages': ['ja-JP', 'ja', 'en'],
#     'timezone': 'Asia/Tokyo'
# }
```

### Accept-Encoding Header

Modern browsers support specific compression algorithms:

```python
# Chrome/Edge (Brotli support)
chrome_encoding = 'gzip, deflate, br, zstd'

# Firefox  
firefox_encoding = 'gzip, deflate, br'

# Old/Automated tools (no Brotli)
automated_encoding = 'gzip, deflate'  # Suspicious in 2024+
```

!!! warning "Brotli Support Detection"
    Any modern browser (2024+) **must** support Brotli (`br`). Missing Brotli indicates an automated tool or heavily outdated browser.

### Sec-CH-UA (Client Hints)

Modern Chromium browsers send [Client Hints](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints) headers:

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

**Consistency checks:**

```python
def validate_client_hints(headers: dict, navigator_props: dict) -> list[str]:
    """
    Validate Client Hints consistency with navigator properties.
    """
    issues = []
    
    # Extract Sec-CH-UA
    sec_ch_ua = headers.get('sec-ch-ua', '')
    sec_ch_platform = headers.get('sec-ch-ua-platform', '').strip('"')
    sec_ch_mobile = headers.get('sec-ch-ua-mobile', '')
    
    # Check platform consistency
    nav_platform = navigator_props.get('platform', '')
    if sec_ch_platform == 'Windows' and 'Win' not in nav_platform:
        issues.append(f"Platform mismatch: Sec-CH-UA says {sec_ch_platform}, navigator.platform says {nav_platform}")
    
    # Check mobile consistency
    nav_mobile = navigator_props.get('userAgentData', {}).get('mobile', False)
    if sec_ch_mobile == '?1' and not nav_mobile:
        issues.append("Mobile mismatch: Sec-CH-UA-Mobile says mobile, but navigator says desktop")
    
    # Check brand consistency with User-Agent
    user_agent = headers.get('user-agent', '')
    if 'Chrome' in sec_ch_ua and 'Chrome' not in user_agent:
        issues.append("Brand mismatch: Sec-CH-UA mentions Chrome, but User-Agent doesn't")
    
    return issues


# Example
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

### Header Order Fingerprinting

The **order** of HTTP headers is browser-specific and often overlooked when spoofing:

```python
# Chrome header order (typical)
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

# Firefox header order (different!)
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

**Detection:**

```python
def fingerprint_by_header_order(request_headers: list[tuple[str, str]]) -> str:
    """
    Identify browser based on header order.
    """
    header_names = [h[0].lower() for h in request_headers]
    order_signature = ','.join(header_names[:10])  # First 10 headers
    
    # Known browser signatures
    signatures = {
        ':method,:path,:authority,:scheme,cache-control,sec-ch-ua': 'Chrome/Edge',
        ':method,:path,:authority,:scheme,user-agent,accept': 'Firefox',
        'host,connection,accept,user-agent,referer': 'Requests/httpx (suspicious!)',
    }
    
    for sig, browser in signatures.items():
        if order_signature.startswith(sig):
            return browser
    
    return 'Unknown (possibly spoofed)'
```

!!! info "HTTP Header Fingerprinting References"
    - **[HTTP Fingerprinting](https://www.yeswehack.com/learn-bug-bounty/recon-series-http-fingerprinting)** by YesWeHack - Guide to HTTP-based reconnaissance
    - **[Client Hints (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Client_hints)** - Official documentation on Sec-CH-UA headers
    - **[HTTP Header Order Fingerprinting](https://lwthiker.com/networks/2022/06/17/tls-fingerprinting.html)** - Discussion of header ordering techniques

## JavaScript Properties Fingerprinting

JavaScript provides extensive access to browser and system properties via the `window` and `navigator` objects. These properties are the most commonly fingerprinted attributes.

### Navigator Object Properties

The `navigator` object exposes dozens of properties that reveal browser characteristics:

```javascript
// Core navigator properties
const fingerprint = {
    // User Agent
    userAgent: navigator.userAgent,
    appVersion: navigator.appVersion,
    platform: navigator.platform,
    
    // Language
    language: navigator.language,
    languages: navigator.languages,
    
    // Hardware
    hardwareConcurrency: navigator.hardwareConcurrency,  // CPU cores
    deviceMemory: navigator.deviceMemory,  // RAM in GB (approximation)
    
    // Features
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
    maxTouchPoints: navigator.maxTouchPoints,
    
    // Vendor
    vendor: navigator.vendor,
    vendorSub: navigator.vendorSub,
    
    // Product
    product: navigator.product,
    productSub: navigator.productSub,
    
    // OS CPU (legacy, but still available)
    oscpu: navigator.oscpu,  // Firefox only
};
```

**Chrome-specific properties:**

```javascript
// Chrome User Agent Data (Client Hints API)
if (navigator.userAgentData) {
    const uaData = {
        brands: navigator.userAgentData.brands,
        mobile: navigator.userAgentData.mobile,
        platform: navigator.userAgentData.platform,
    };
    
    // Request high entropy values (requires permission)
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

### Screen and Window Properties

Display characteristics are highly distinctive:

```javascript
const screenFingerprint = {
    // Screen dimensions
    width: screen.width,
    height: screen.height,
    availWidth: screen.availWidth,
    availHeight: screen.availHeight,
    
    // Color depth
    colorDepth: screen.colorDepth,
    pixelDepth: screen.pixelDepth,
    
    // Device pixel ratio (Retina displays)
    devicePixelRatio: window.devicePixelRatio,
    
    // Window dimensions
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    outerWidth: window.outerWidth,
    outerHeight: window.outerHeight,
    
    // Screen orientation
    orientation: {
        type: screen.orientation?.type,
        angle: screen.orientation?.angle,
    },
};
```

**Detection of virtualized/headless environments:**

```python
def detect_headless_chrome(properties: dict) -> list[str]:
    """
    Detect headless Chrome based on property inconsistencies.
    """
    issues = []
    
    # Headless Chrome has outerWidth/Height = innerWidth/Height (no UI chrome)
    if properties['outerWidth'] == properties['innerWidth']:
        issues.append("outerWidth == innerWidth (suspicious for headed browser)")
    
    # Headless often has screen dimensions == window dimensions
    if properties['screen']['width'] == properties['innerWidth']:
        issues.append("Screen width == window width (possibly headless)")
    
    # Headless Chrome reports specific user agent
    if 'HeadlessChrome' in properties.get('userAgent', ''):
        issues.append("User-Agent explicitly says HeadlessChrome")
    
    # navigator.webdriver should be undefined in real browsers
    if properties.get('webdriver') == True:
        issues.append("navigator.webdriver is true (automation detected)")
    
    return issues
```

### Plugins and MIME Types (Legacy)

Modern browsers have deprecated plugin enumeration, but it's still a fingerprinting vector:

```javascript
// Plugins (deprecated, but still exposed)
const plugins = [];
for (let i = 0; i < navigator.plugins.length; i++) {
    plugins.push({
        name: navigator.plugins[i].name,
        description: navigator.plugins[i].description,
        filename: navigator.plugins[i].filename,
    });
}

// MIME types (deprecated)
const mimeTypes = [];
for (let i = 0; i < navigator.mimeTypes.length; i++) {
    mimeTypes.push({
        type: navigator.mimeTypes[i].type,
        description: navigator.mimeTypes[i].description,
        suffixes: navigator.mimeTypes[i].suffixes,
    });
}
```

!!! warning "Plugin Enumeration Detection"
    **Modern Chrome/Firefox**: Return empty arrays for `navigator.plugins` and `navigator.mimeTypes` to prevent fingerprinting.
    
    **Headless Chrome**: Often returns **empty** arrays even when plugins exist, revealing automation.
    
    **Detection**: If browser claims to be Chrome but has no plugins, it's suspicious.

### Timezone and Date Properties

Timezone information is surprisingly revealing:

```javascript
const timezoneFingerprint = {
    // Timezone offset in minutes
    timezoneOffset: new Date().getTimezoneOffset(),
    
    // IANA timezone name (e.g., "America/New_York")
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    
    // Locale
    locale: Intl.DateTimeFormat().resolvedOptions().locale,
    
    // Date formatting
    dateFormat: new Date().toLocaleDateString(),
    timeFormat: new Date().toLocaleTimeString(),
};
```

**Consistency check:**

```python
def validate_timezone_consistency(tz_offset: int, tz_name: str, accept_language: str) -> list[str]:
    """
    Validate timezone consistency with language/location.
    """
    issues = []
    
    # Timezone-language expected mappings
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
    
    # Timezone offset validation
    expected_offsets = {
        'America/New_York': -300,  # EST (minutes)
        'Europe/London': 0,        # GMT
        'Asia/Tokyo': -540,        # JST
    }
    
    expected_offset = expected_offsets.get(tz_name)
    if expected_offset and tz_offset != expected_offset:
        issues.append(f"Timezone offset {tz_offset} doesn't match {tz_name}")
    
    return issues
```

### Permissions and Battery API

Some APIs require user permission but can still fingerprint:

```javascript
// Battery API (if available)
if (navigator.getBattery) {
    navigator.getBattery().then(battery => {
        const batteryInfo = {
            charging: battery.charging,
            chargingTime: battery.chargingTime,
            dischargingTime: battery.dischargingTime,
            level: battery.level,
        };
        // Battery level can be used as entropy
    });
}

// Permissions
navigator.permissions.query({name: 'geolocation'}).then(result => {
    console.log('Geolocation permission:', result.state);
    // 'granted', 'denied', 'prompt'
});
```

!!! danger "navigator.webdriver Detection"
    The `navigator.webdriver` property is **the most obvious** automation indicator:
    
    ```javascript
    if (navigator.webdriver === true) {
        alert('Automation detected!');
    }
    ```
    
    **Selenium, Puppeteer, Playwright** all set this to `true` by default. CDP automation (like Pydoll) does **not** set this property, making it more stealthy.

### Python Implementation: Collecting Browser Properties

```python
async def collect_browser_fingerprint(tab) -> dict:
    """
    Collect comprehensive browser fingerprint using Pydoll.
    """
    fingerprint = await tab.execute_script('''
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
    ''')
    
    return fingerprint


# Usage example
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

!!! info "JavaScript Properties References"
    - **[Fingerprint.com: Browser Fingerprinting Techniques](https://fingerprint.com/blog/browser-fingerprinting-techniques/)** - Comprehensive guide to all fingerprinting methods
    - **[NordLayer: Browser Fingerprinting Guide](https://nordlayer.com/learn/browser-security/browser-fingerprinting/)** - How browser fingerprinting works
    - **[AIMultiple: Browser Fingerprinting Best Practices](https://research.aimultiple.com/browser-fingerprinting/)** - Technical analysis of fingerprinting techniques
    - **[Bureau.id: Top 9 Fingerprinting Techniques](https://www.bureau.id/blog/browser-fingerprinting-techniques)** - Detailed breakdown of detection methods

## Canvas Fingerprinting

Canvas fingerprinting exploits subtle differences in how browsers render graphics on the HTML5 `<canvas>` element. These differences arise from variations in hardware (GPU), graphics drivers, operating systems, and browser implementations.

### How Canvas Fingerprinting Works

The technique involves:
1. Drawing specific text/shapes on a canvas
2. Extracting the pixel data with `toDataURL()` or `getImageData()`
3. Hashing the result to create a unique fingerprint

**Factors affecting canvas rendering:**
- **GPU and drivers**: Different GPUs render anti-aliasing differently
- **Operating System**: Font rendering varies (ClearType on Windows, FreeType on Linux)
- **Browser engine**: WebKit vs Blink vs Gecko have different rendering pipelines
- **Graphics libraries**: Skia (Chrome) vs Cairo (Firefox)

### Canvas Fingerprinting Technique

```javascript
function generateCanvasFingerprint() {
    // Create canvas
    const canvas = document.createElement('canvas');
    canvas.width = 220;
    canvas.height = 30;
    
    const ctx = canvas.getContext('2d');
    
    // Text rendering (most distinctive)
    ctx.textBaseline = 'top';
    ctx.font = '14px "Arial"';
    ctx.textBaseline = 'alphabetic';
    
    // Add color gradients (exposes rendering differences)
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    
    // Add semi-transparent color (blending differences)
    ctx.fillStyle = '#069';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
    
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
    
    // Extract data URL
    const dataURL = canvas.toDataURL();
    
    // Generate hash (MD5, SHA-256, etc.)
    return hashString(dataURL);
}

// Simpler hash function for demo
function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(16);
}
```

**Why the specific test string?**

- **"Cwm fjordbank glyphs vext quiz"**: Pangram with unusual characters to maximize font rendering variations
- **Emoji (😃)**: Emoji rendering varies significantly across systems
- **Mixed fonts/sizes**: Increases entropy

### Canvas Fingerprint Uniqueness

Research by [USENIX](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery) shows:

- **5.5% chance** of two random users having the same canvas fingerprint
- When combined with other techniques, uniqueness increases to **99.24%**

### Detecting Canvas Fingerprinting

Websites detect fingerprint modification attempts:

```javascript
// Detect if canvas is being blocked/modified
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;

HTMLCanvasElement.prototype.toDataURL = function() {
    // Check if fingerprint is consistent
    const result = originalToDataURL.apply(this, arguments);
    
    // If result changes on every call → fake fingerprint detected
    return result;
};

// Advanced detection: Check for noise injection
function detectCanvasNoise(canvas) {
    const ctx = canvas.getContext('2d');
    
    // Draw known pattern
    ctx.fillStyle = '#ff0000';
    ctx.fillRect(0, 0, 10, 10);
    
    // Read back pixels
    const imageData = ctx.getImageData(0, 0, 10, 10);
    const pixels = imageData.data;
    
    // Check if exactly red (255, 0, 0) or if there's noise
    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] !== 255 || pixels[i + 1] !== 0 || pixels[i + 2] !== 0) {
            return true;  // Noise detected = fingerprint blocking
        }
    }
    
    return false;  // Clean canvas
}
```

### Python Implementation with Pydoll

```python
import hashlib
import asyncio
from pydoll.browser.chromium import Chrome


async def get_canvas_fingerprint(tab) -> str:
    """
    Generate canvas fingerprint using Pydoll.
    """
    fingerprint = await tab.execute_script('''
        () => {
            const canvas = document.createElement('canvas');
            canvas.width = 220;
            canvas.height = 30;
            
            const ctx = canvas.getContext('2d');
            
            // Text rendering
            ctx.textBaseline = 'top';
            ctx.font = '14px "Arial"';
            ctx.textBaseline = 'alphabetic';
            
            // Color blocks
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            
            // Text with emoji
            ctx.fillStyle = '#069';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 2, 15);
            
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Cwm fjordbank glyphs vext quiz, 😃', 4, 17);
            
            // Return data URL
            return canvas.toDataURL();
        }
    ''')
    
    # Hash the canvas data
    canvas_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
    
    return canvas_hash


async def compare_canvas_consistency(tab, iterations: int = 3) -> bool:
    """
    Check if canvas fingerprint is consistent (not randomly generated).
    """
    fingerprints = []
    
    for _ in range(iterations):
        fp = await get_canvas_fingerprint(tab)
        fingerprints.append(fp)
        await asyncio.sleep(0.1)
    
    # All fingerprints should be identical
    is_consistent = len(set(fingerprints)) == 1
    
    if not is_consistent:
        print("Canvas fingerprint is inconsistent (possible fake)")
        print(f"  Unique values: {len(set(fingerprints))}")
    
    return is_consistent


# Usage
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

!!! warning "Canvas Fingerprint Blocking Detection"
    Many anti-fingerprinting tools inject **random noise** into canvas data to prevent tracking. However, this creates an **inconsistent fingerprint** that changes on every request, which is itself detectable!
    
    **Detection technique:**

    1. Request canvas fingerprint multiple times
    2. If values differ → noise injection detected
    3. Flag as "fingerprint blocking = suspicious behavior"

## WebGL Fingerprinting

WebGL fingerprinting is more powerful than Canvas because it exposes detailed information about the **GPU, drivers, and graphics stack**.

### WebGL Renderer Information

The most distinctive WebGL data comes from the `WEBGL_debug_renderer_info` extension:

```javascript
function getWebGLFingerprint() {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) {
        return null;  // WebGL not supported
    }
    
    const fingerprint = {
        // Get debug info (most distinctive)
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
        
        // Supported extensions
        extensions: gl.getSupportedExtensions(),
        
        // WebGL parameters
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
        
        // Precision formats
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

**Example output:**

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

###WebGL Rendering Fingerprint

Beyond metadata, WebGL can render a 3D scene and analyze pixel output:

```javascript
function getWebGLRenderFingerprint() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    
    const gl = canvas.getContext('webgl');
    
    // Vertex shader
    const vertexShaderSource = `
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
    `;
    
    // Fragment shader with gradient
    const fragmentShaderSource = `
        precision mediump float;
        void main() {
            gl_FragColor = vec4(gl_FragCoord.x/256.0, gl_FragCoord.y/128.0, 0.5, 1.0);
        }
    `;
    
    // Compile shaders
    const vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertexShaderSource);
    gl.compileShader(vertexShader);
    
    const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragmentShaderSource);
    gl.compileShader(fragmentShader);
    
    // Link program
    const program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    gl.useProgram(program);
    
    // Draw triangle
    const vertices = new Float32Array([-1, -1, 1, -1, 0, 1]);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
    
    const position = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(position);
    gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
    
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    
    // Extract rendered image
    return canvas.toDataURL();
}
```

### Python Implementation with Pydoll

```python
async def get_webgl_fingerprint(tab) -> dict:
    """
    Collect WebGL fingerprint data.
    """
    fingerprint = await tab.execute_script('''
        () => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return null;
            }
            
            // Get debug info
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
    ''')
    
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

!!! danger "WebGL Fingerprint Blocking"
    Some privacy tools attempt to block WebGL fingerprinting by:
    
    1. **Disabling WEBGL_debug_renderer_info extension**
    2. **Returning generic "SwiftShader" renderer** (software rendering)
    3. **Spoofing GPU vendor/renderer strings**
    
    However, **missing or generic WebGL data is suspicious** because:
    - 97% of browsers support WebGL
    - Generic renderers have performance implications (detectable via timing)
    - Absence of common extensions reveals blocking

!!! info "Canvas & WebGL Fingerprinting References"
    - **[USENIX: Pixel Perfect Browser Fingerprinting](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery)** - Original academic research on canvas fingerprinting (2012)
    - **[Fingerprint.com: Canvas Fingerprinting](https://fingerprint.com/blog/canvas-fingerprinting/)** - Modern canvas fingerprinting techniques
    - **[BrowserLeaks WebGL Report](https://browserleaks.com/webgl)** - Test your WebGL fingerprint
    - **[Chromium WebGL Implementation](https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/modules/webgl/)** - Source code for WebGL in Chromium
