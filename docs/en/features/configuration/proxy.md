# Proxy Configuration

Proxies are essential for professional web automation, enabling you to bypass rate limits, access geo-restricted content, and maintain anonymity. Pydoll provides native proxy support with automatic authentication handling.

!!! info "Related Documentation"
    - **[Browser Options](browser-options.md)** - Command-line proxy arguments
    - **[Request Interception](../network/interception.md)** - How proxy authentication works internally
    - **[Stealth Automation](../automation/human-interactions.md)** - Combine proxies with anti-detection
    - **[Proxy Architecture Deep Dive](../../deep-dive/proxy-architecture.md)** - Network fundamentals, protocols, security, and building your own proxy

## Why Use Proxies?

Proxies provide critical capabilities for automation:

| Benefit | Description | Use Case |
|---------|-------------|----------|
| **IP Rotation** | Distribute requests across multiple IPs | Avoid rate limits, scrape at scale |
| **Geographic Access** | Access region-locked content | Test geo-targeted features, bypass restrictions |
| **Anonymity** | Hide your real IP address | Privacy-focused automation, competitor analysis |
| **Load Distribution** | Spread traffic across multiple endpoints | High-volume scraping, stress testing |
| **Ban Avoidance** | Prevent permanent IP bans | Long-running automation, aggressive scraping |

!!! tip "When to Use Proxies"
    **Always use proxies for:**
    
    - Production web scraping (>100 requests/hour)
    - Accessing geo-restricted content
    - Bypassing rate limits or IP-based blocks
    - Testing from different regions
    - Maintaining anonymity
    
    **You may skip proxies for:**
    
    - Local development and testing
    - Internal/corporate automation
    - Low-volume automation (<50 requests/day)
    - When scraping your own infrastructure

## Proxy Types

Different proxy protocols serve different purposes:

| Type | Port | Authentication | Speed | Security | Use Case |
|------|------|----------------|-------|----------|----------|
| **HTTP** | 80, 8080 | Optional | Fast | Low | Basic web scraping, non-sensitive data |
| **HTTPS** | 443, 8443 | Optional | Fast | Medium | Secure web scraping, encrypted traffic |
| **SOCKS5** | 1080, 1081 | Optional | Medium | High | Full TCP/UDP support, advanced use cases |

### HTTP/HTTPS Proxies

Standard web proxies, ideal for most automation tasks:

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

**Pros:**

- Fast and efficient
- Wide support across services
- Easy to configure

**Cons:**

- HTTP: No encryption (traffic visible to proxy)
- Can be detected more easily than SOCKS5

### SOCKS5 Proxies

Advanced proxies with full TCP/UDP support:

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

**Pros:**

- Protocol-agnostic (works with any TCP/UDP traffic)
- Better for advanced use cases (WebSockets, WebRTC)
- More stealthy (harder to detect)

**Cons:**

- Slightly slower than HTTP/HTTPS
- Less common in free/cheap proxy services

!!! info "SOCKS4 vs SOCKS5"
    **SOCKS5** is recommended over SOCKS4 because it:
    
    - Supports authentication (username/password)
    - Handles UDP traffic (for WebRTC, DNS, etc.)
    - Provides better error handling
    
    Use `socks5://` unless you specifically need SOCKS4 (`socks4://`).

## Authenticated Proxies

Pydoll automatically handles proxy authentication without manual intervention.

### How Authentication Works

When you provide credentials in the proxy URL, Pydoll:

1. **Intercepts the authentication challenge** using the Fetch domain
2. **Automatically responds** with credentials
3. **Continues navigation** sea@mlessly

This happens transparently, you don't need to handle authentication manually!

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

!!! tip "Credential Format"
    Include credentials directly in the proxy URL:

    - HTTP: `http://username:password@host:port`
    - HTTPS: `https://username:password@host:port`
    - SOCKS5: `socks5://username:password@host:port`

    Pydoll automatically extracts and uses these credentials.

!!! warning "SOCKS5 Authentication Limitation"
    **Chrome does not support SOCKS5 authentication natively** ([Chromium Issue #40323993](https://issues.chromium.org/issues/40323993)). Credentials embedded in `socks5://user:pass@host:port` are silently ignored — Chrome only sends a "no authentication" greeting to the SOCKS5 proxy.

    This means Pydoll's automatic proxy auth (via `Fetch.authRequired`) **does not work for SOCKS5**, because Chrome never issues an HTTP 407 challenge for SOCKS5 connections.

    **Workaround — Local proxy forwarder:**

    Run a local SOCKS5 proxy (no auth) that forwards to the remote authenticated proxy. Pydoll provides a ready-to-use script for this:

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

    The forwarder handles the username/password handshake with the remote proxy while Chrome connects to localhost without authentication.

    For the full technical explanation of why this happens, see **[SOCKS5 Authentication Deep Dive](../../deep-dive/network/socks-proxies.md#socks5-authentication-and-chrome)**.

### Authentication Implementation Details

Pydoll uses Chrome's **Fetch domain** at the browser level to intercept and handle authentication challenges:

```python
# This is handled internally by Pydoll
# You don't need to write this code!

async def _handle_proxy_auth(event):
    """Pydoll's internal proxy authentication handler."""
    if event['params']['authChallenge']['source'] == 'Proxy':
        await browser.continue_request_with_auth(
            request_id=event['params']['requestId'],
            username='user',
            password='pass'
        )
```

!!! info "Under the Hood"
    For technical details on how Pydoll intercepts and handles proxy authentication, see:
    
    - **[Request Interception](../network/interception.md)** - Fetch domain and request handling
    - **[Event System](../advanced/event-system.md)** - Event-driven authentication

!!! warning "Fetch Domain Conflicts"
    When using **authenticated proxies** + **tab-level request interception**, be aware:
    
    - Pydoll enables Fetch at the **Browser level** for proxy auth
    - If you enable Fetch at the **Tab level**, they share the same domain
    - **Solution**: Call `tab.go_to()` once before enabling tab-level interception
    
    ```python
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # 1. First navigation triggers proxy auth (Browser-level Fetch)
        await tab.go_to('https://example.com')
        
        # 2. Then enable tab-level interception safely
        await tab.enable_fetch_events()
        await tab.on('Fetch.requestPaused', my_interceptor)
        
        # 3. Continue with your automation
        await tab.go_to('https://example.com/page2')
    ```
    
    See [Request Interception - Proxy + Interception](../network/interception.md#private-proxy-request-interception-fetch) for details.

## Proxy Bypass List

Exclude specific domains from using the proxy:

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

**Bypass list patterns:**

| Pattern | Matches | Example |
|---------|---------|---------|
| `localhost` | Localhost only | `http://localhost` |
| `127.0.0.1` | Loopback IP | `http://127.0.0.1` |
| `*.local` | All `.local` domains | `http://server.local` |
| `internal.company.com` | Specific domain | `http://internal.company.com` |
| `192.168.1.*` | IP range | `http://192.168.1.100` |

!!! tip "When to Use Bypass List"
    Bypass proxy for:
    
    - **Local development servers** (`localhost`, `127.0.0.1`)
    - **Internal company resources** (VPN, intranet)
    - **Testing environments** (`.local`, `.test` domains)
    - **High-bandwidth resources** (when proxy is slow)

## PAC (Proxy Auto-Config)

Use a PAC file for complex proxy routing rules:

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

!!! info "PAC File Use Cases"
    PAC files are useful for:
    
    - **Complex routing rules** (domain-based, IP-based)
    - **Proxy failover** (try multiple proxies)
    - **Load balancing** (distribute across proxy pool)
    - **Enterprise environments** (centralized proxy management)

## Rotating Proxies

Rotate through multiple proxies for better distribution:

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

!!! tip "Proxy Rotation Strategies"
    **Per-browser rotation** (above):

    - Each browser instance uses a different proxy
    - Best for isolation and avoiding session conflicts
    
    **Per-request rotation**:

    - More complex, requires request interception
    - See [Request Interception](../network/interception.md) for implementation

## Residential vs Datacenter Proxies

Understanding proxy types helps you choose the right service:

| Feature | Residential | Datacenter |
|---------|------------|------------|
| **IP Source** | Real residential ISPs | Data centers |
| **Legitimacy** | High (real users) | Low (known ranges) |
| **Detection Risk** | Very low | High |
| **Speed** | Medium (150-500ms) | Very fast (<50ms) |
| **Cost** | Expensive ($5-15/GB) | Cheap ($0.10-1/GB) |
| **Best For** | Anti-bot sites, e-commerce | APIs, internal tools |

### Residential Proxies

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

**When to use Residential:**

- Sites with strong anti-bot protection (Cloudflare, DataDome)
- E-commerce scraping (Amazon, eBay, etc.)
- Social media automation
- Financial services
- Any site that actively blocks datacenter IPs

### Datacenter Proxies

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

**When to use Datacenter:**

- Public APIs without rate limits
- Internal/corporate automation
- Sites without anti-bot measures
- High-volume, speed-critical scraping
- Development and testing

!!! warning "Proxy Quality Matters"
    **Bad proxies** cause more problems than they solve:
    
    - Slow response times (timeouts)
    - Connection failures (error rates)
    - Blacklisted IPs (immediate bans)
    - Leaked real IP (privacy breach)
    
    **Invest in quality proxies** from reputable providers. Free proxies are almost never worth it.

## Testing Your Proxy

Verify proxy configuration before running production automation:

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

## Further Reading

- **[Proxy Architecture Deep Dive](../../deep-dive/proxy-architecture.md)** - Network fundamentals, TCP/UDP, HTTP/2/3, SOCKS5 internals, security analysis, and building your own proxy server
- **[Browser Options](browser-options.md)** - Command-line arguments and configuration
- **[Request Interception](../network/interception.md)** - How proxy authentication works
- **[Browser Preferences](browser-preferences.md)** - Stealth and fingerprinting
- **[Contexts](../browser-management/contexts.md)** - Using different proxies per context

!!! tip "Start Simple"
    Begin with a simple proxy setup, test thoroughly, then add complexity (rotation, retry logic, monitoring) as needed. Quality proxies are more important than complex rotation strategies.
    
    For those interested in understanding proxies at a deeper level, the **[Proxy Architecture Deep Dive](../../deep-dive/proxy-architecture.md)** provides comprehensive coverage of network protocols, security considerations, and even guides you through building your own proxy server.
