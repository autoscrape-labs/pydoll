# Browser Options (ChromiumOptions)

`ChromiumOptions` is your central configuration hub for customizing browser behavior. It controls everything from command-line arguments and binary location to page load states and content preferences.

!!! info "Related Documentation"
    - **[Browser Preferences](browser-preferences.md)** - Deep dive into Chromium's internal preference system
    - **[Browser Management](../browser-management/tabs.md)** - Working with browser instances and tabs
    - **[Contexts](../browser-management/contexts.md)** - Isolated browsing contexts

## Quick Start

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def main():
    # Create and configure options
    options = ChromiumOptions()
    
    # Basic configuration
    options.headless = True
    options.start_timeout = 15
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Add command-line arguments
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Helper methods for common settings
    options.block_notifications = True
    options.block_popups = True
    options.set_default_download_directory('/tmp/downloads')
    
    # Use the configured options
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')

asyncio.run(main())
```

## Core Properties

### Command-Line Arguments

Chromium supports hundreds of command-line switches that control browser behavior at the deepest level. Use `add_argument()` to pass flags directly to the browser process.

```python
options = ChromiumOptions()

# Add single argument
options.add_argument('--disable-blink-features=AutomationControlled')

# Add argument with value
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 ...')

# Remove argument if needed
options.remove_argument('--window-size=1920,1080')

# Get all arguments
all_args = options.arguments
```

!!! tip "Argument Format"
    - Arguments starting with `--` are flags: `--headless`, `--disable-gpu`
    - Arguments with `=` have values: `--window-size=1920,1080`
    - Some accept multiple values: `--disable-features=Feature1,Feature2`

**See [Command-Line Arguments Reference](#command-line-arguments-reference) below for comprehensive lists.**

### Binary Location

Specify a custom browser executable instead of using the system default:

```python
options = ChromiumOptions()

# Linux
options.binary_location = '/opt/google/chrome-beta/chrome'

# macOS
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'

# Windows
options.binary_location = r'C:\Program Files\Google\Chrome Beta\Application\chrome.exe'
```

!!! info "When to Set Binary Location"
    - Testing different Chrome versions (Stable, Beta, Canary)
    - Using Chromium instead of Chrome
    - Using portable browser installations
    - Running specific builds for debugging

### Start Timeout

Control how long Pydoll waits for the browser to start and respond:

```python
options = ChromiumOptions()
options.start_timeout = 20  # seconds (default: 10)
```

!!! warning "Timeout Considerations"
    - **Too low**: Browser may not fully initialize, causing startup failures
    - **Too high**: Hangs will block your automation for longer
    - **Recommended**: 10-15s for most cases, 20-30s for slow systems or heavy browser profiles

### Headless Mode

Run the browser without a visible UI:

```python
options = ChromiumOptions()
options.headless = True  # Automatically adds --headless argument

# Or manually
options.add_argument('--headless')
options.add_argument('--headless=new')  # New headless mode (Chrome 109+)
```

| Mode | Argument | Description |
|------|----------|-------------|
| **Headful** | (none) | Visible browser window (default) |
| **Classic Headless** | `--headless` | Legacy headless mode |
| **New Headless** | `--headless=new` | Modern headless (Chrome 109+, better compatibility) |

!!! tip "New Headless Mode"
    The `--headless=new` mode (Chrome 109+) provides better compatibility with modern web features and is harder to detect. Use it for production automation.

### Page Load State

Control when `tab.go_to()` considers a page "loaded":

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE  # or PageLoadState.COMPLETE
```

| State | When Navigation Completes | Use Case |
|-------|---------------------------|----------|
| `COMPLETE` (default) | `load` event fired, all resources loaded | Wait for images, fonts, scripts |
| `INTERACTIVE` | `DOMContentLoaded` fired, DOM ready | Faster navigation, interact with DOM immediately |

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

async def compare_load_states():
    # Complete mode - waits for everything
    options_complete = ChromiumOptions()
    options_complete.page_load_state = PageLoadState.COMPLETE
    
    async with Chrome(options=options_complete) as browser:
        tab = await browser.start()
        
        import time
        start = time.time()
        await tab.go_to('https://example.com')
        complete_time = time.time() - start
        print(f"COMPLETE mode: {complete_time:.2f}s")
    
    # Interactive mode - DOM ready is enough
    options_interactive = ChromiumOptions()
    options_interactive.page_load_state = PageLoadState.INTERACTIVE
    
    async with Chrome(options=options_interactive) as browser:
        tab = await browser.start()
        
        start = time.time()
        await tab.go_to('https://example.com')
        interactive_time = time.time() - start
        print(f"INTERACTIVE mode: {interactive_time:.2f}s")

asyncio.run(compare_load_states())
```

!!! tip "When to Use INTERACTIVE"
    Use `INTERACTIVE` when:
    
    - You only need DOM access, not images/fonts
    - Scraping text content and structure
    - Speed is critical
    - The page has many slow-loading resources
    
    Stick with `COMPLETE` (default) when:
    
    - Taking screenshots (need images loaded)
    - Waiting for JavaScript-heavy apps to fully initialize
    - Testing page load performance

## Command-Line Arguments Reference

Chromium supports hundreds of command-line switches. Below are the most useful for automation, organized by category.

!!! info "Full Reference"
    Complete list of all Chromium switches: [Peter Beverloo's Chromium Command Line Switches](https://peter.sh/experiments/chromium-command-line-switches/)

### Performance & Resource Management

Optimize browser performance for faster automation:

```python
options = ChromiumOptions()

# Disable GPU acceleration (headless, Docker, CI/CD)
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')

# Reduce memory usage
options.add_argument('--disable-dev-shm-usage')  # Docker: overcome /dev/shm size limit
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')

# Disable unnecessary features
options.add_argument('--disable-sync')  # Google account sync
options.add_argument('--disable-translate')
options.add_argument('--disable-background-timer-throttling')
options.add_argument('--disable-backgrounding-occluded-windows')
options.add_argument('--disable-renderer-backgrounding')

# Network optimizations
options.add_argument('--disable-features=NetworkPrediction')
options.add_argument('--dns-prefetch-disable')

# Window and rendering
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--force-device-scale-factor=1')
```

| Argument | Effect | When to Use |
|----------|--------|-------------|
| `--disable-gpu` | No GPU acceleration | Headless, Docker, servers without GPU |
| `--disable-dev-shm-usage` | Use `/tmp` instead of `/dev/shm` | Docker containers with small shared memory |
| `--disable-extensions` | Don't load any extensions | Clean, fast browser for automation |
| `--window-size=W,H` | Set initial window dimensions | Screenshots, consistent viewport |
| `--force-device-scale-factor=1` | Disable high-DPI scaling | Consistent rendering across systems |

### Stealth & Fingerprinting

Make your automation harder to detect with these command-line arguments:

| Argument | Purpose | Example |
|----------|---------|---------|
| `--disable-blink-features=AutomationControlled` | Remove `navigator.webdriver` flag | Essential for stealth |
| `--user-agent=...` | Set realistic, common user agent | Match target region/device |
| `--use-gl=swiftshader` | Software WebGL renderer | Avoid unique GPU fingerprints |
| `--force-webrtc-ip-handling-policy=...` | Prevent WebRTC IP leaks | Use `disable_non_proxied_udp` |
| `--lang=en-US` | Set browser language | Match target locale |
| `--accept-lang=en-US,en;q=0.9` | Accept-Language header | Realistic language preferences |
| `--tz=America/New_York` | Set timezone | Match target region |
| `--no-first-run` | Skip first-run wizards | Cleaner automation |
| `--no-default-browser-check` | Skip default browser prompt | Avoid UI interruptions |
| `--disable-reading-from-canvas` | Canvas fingerprinting mitigation | Reduce uniqueness |
| `--disable-features=AudioServiceOutOfProcess` | Audio fingerprinting mitigation | Reduce uniqueness |

!!! warning "Detection Arms Race"
    No single technique guarantees undetectability. Combine multiple strategies:
    
    1. **Command-line arguments** (this table)
    2. **Browser preferences** - [Browser Preferences - Stealth & Fingerprinting](browser-preferences.md#stealth-fingerprinting)
    3. **Human-like interactions** - [Human-Like Interactions](../automation/human-interactions.md)
    4. **Good IP reputation** - Use residential proxies with clean history

### Security & Privacy

Control security features and privacy settings:

```python
options = ChromiumOptions()

# Sandbox (disable for Docker/CI only)
options.add_argument('--no-sandbox')  # SECURITY RISK - use only in controlled environments
options.add_argument('--disable-setuid-sandbox')

# HTTPS/SSL
options.add_argument('--ignore-certificate-errors')  # Ignore SSL errors
options.add_argument('--ignore-ssl-errors')
options.add_argument('--allow-insecure-localhost')

# Privacy
options.add_argument('--disable-features=Translate')
options.add_argument('--disable-sync')
options.add_argument('--incognito')  # Open in incognito mode

# Permissions auto-grant (for testing)
options.add_argument('--use-fake-ui-for-media-stream')  # Auto-grant camera/mic
options.add_argument('--use-fake-device-for-media-stream')  # Use fake devices
```

!!! danger "Sandbox Warnings"
    **`--no-sandbox` is a security risk!** Only use it when:
    
    - Running in Docker containers (sandbox conflicts with container isolation)
    - CI/CD environments with restricted permissions
    - You fully trust the content being loaded
    
    **Never** use `--no-sandbox` when:
    
    - Visiting untrusted websites
    - Running user-submitted code
    - In production environments with external input

| Argument | Effect | Security Impact |
|----------|--------|-----------------|
| `--no-sandbox` | Disable Chrome sandbox | **HIGH RISK** - Allows code execution |
| `--ignore-certificate-errors` | Skip SSL validation | **MEDIUM RISK** - MITM attacks possible |
| `--incognito` | Private browsing mode | Safer - no persistent state |

### Debugging & Development

Tools for debugging automation and development:

```python
options = ChromiumOptions()

# DevTools
options.add_argument('--auto-open-devtools-for-tabs')

# Logging
options.add_argument('--enable-logging')
options.add_argument('--v=1')  # Verbosity level (0-3)
options.add_argument('--log-level=0')  # 0=INFO, 1=WARNING, 2=ERROR

# Crash handling
options.add_argument('--disable-crash-reporter')
options.add_argument('--no-crash-upload')

# Enable experimental features
options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
options.add_argument('--enable-experimental-web-platform-features')

# JavaScript debugging
options.add_argument('--js-flags=--expose-gc')  # Expose garbage collector
```

!!! tip "Remote Debugging"
    Pydoll automatically manages the remote debugging port. To access Chrome DevTools:
    
    ```python
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Get the debugging port
        port = browser._connection_port
        print(f"DevTools available at: http://localhost:{port}")
        
        # Open this URL in your browser to access DevTools
    ```
    
    **Do not** use `--remote-debugging-port` argument - it will conflict with Pydoll's internal management!

### Display & Rendering

Control how the browser renders content:

```python
options = ChromiumOptions()

# Viewport and window
options.add_argument('--window-size=1920,1080')
options.add_argument('--window-position=0,0')
options.add_argument('--start-maximized')
options.add_argument('--start-fullscreen')

# High DPI displays
options.add_argument('--force-device-scale-factor=1')
options.add_argument('--high-dpi-support=1')

# Color and rendering
options.add_argument('--force-color-profile=srgb')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-accelerated-video-decode')

# Font rendering
options.add_argument('--font-render-hinting=none')
options.add_argument('--disable-font-subpixel-positioning')

# Animations
options.add_argument('--disable-animations')
options.add_argument('--wm-window-animations-disabled')
```

| Argument | Effect | Use Case |
|----------|--------|----------|
| `--window-size=W,H` | Set window dimensions | Screenshots, consistent viewport |
| `--start-maximized` | Open maximized window | UI testing, full-screen captures |
| `--force-device-scale-factor=1` | Disable DPI scaling | Consistent rendering across systems |
| `--disable-animations` | No CSS/UI animations | Faster testing, reduce flakiness |

### Proxy Configuration

Configure proxies for all network traffic:

```python
options = ChromiumOptions()

# HTTP/HTTPS proxy
options.add_argument('--proxy-server=http://proxy.example.com:8080')

# Authenticated proxy
options.add_argument('--proxy-server=http://user:pass@proxy.example.com:8080')

# SOCKS proxy
options.add_argument('--proxy-server=socks5://proxy.example.com:1080')

# Bypass proxy for specific hosts
options.add_argument('--proxy-bypass-list=localhost,127.0.0.1,*.local')

# Proxy auto-config (PAC) file
options.add_argument('--proxy-pac-url=http://proxy.example.com/proxy.pac')
```

!!! info "Proxy Authentication"
    For proxies requiring authentication, Pydoll automatically handles auth challenges when using the `--proxy-server` argument with credentials.
    
    See **[Request Interception](../network/interception.md)** for details on the Fetch domain interaction with proxies.

## Helper Methods

`ChromiumOptions` provides convenient methods for common configuration tasks:

### Download Management

```python
options = ChromiumOptions()

# Set download directory
options.set_default_download_directory('/home/user/downloads')

# Prompt for download location
options.prompt_for_download = True  # Ask user where to save
options.prompt_for_download = False  # Download silently (default)

# Allow multiple automatic downloads
options.allow_automatic_downloads = True  # Allow without prompt
options.allow_automatic_downloads = False  # Block or ask (default)
```

### Content Blocking

```python
options = ChromiumOptions()

# Block pop-ups
options.block_popups = True  # Block (default in most cases)
options.block_popups = False  # Allow

# Block notifications
options.block_notifications = True  # Block requests
options.block_notifications = False  # Allow sites to ask
```

### Privacy Controls

```python
options = ChromiumOptions()

# Password manager
options.password_manager_enabled = False  # Disable save password prompts
options.password_manager_enabled = True  # Enable (default)

# WebRTC leak protection (prevents real IP exposure through WebRTC)
options.webrtc_leak_protection = True  # Adds --force-webrtc-ip-handling-policy=disable_non_proxied_udp
options.webrtc_leak_protection = False  # Disable (default)
```

!!! tip "WebRTC Leak Protection"
    WebRTC can leak your real IP address even when using a proxy. Enable `webrtc_leak_protection` to block non-proxied UDP connections, preventing STUN requests from bypassing your proxy. This is **essential** when using proxies for anonymity. See **[Network Fundamentals - WebRTC](../../deep-dive/network/network-fundamentals.md#webrtc-and-ip-leakage)** for details.

### File Handling

```python
options = ChromiumOptions()

# PDF behavior
options.open_pdf_externally = True  # Download PDFs instead of viewing
options.open_pdf_externally = False  # View in browser (default)
```

### Internationalization

```python
options = ChromiumOptions()

# Accept languages (affects Content-Language header)
options.set_accept_languages('en-US,en;q=0.9,pt-BR;q=0.8')
```

## Complete Configuration Examples

### Fast Scraping Configuration

Optimized for speed and resource efficiency:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_fast_scraping_options() -> ChromiumOptions:
    """Ultra-fast configuration for web scraping."""
    options = ChromiumOptions()
    
    # Headless for speed
    options.headless = True
    
    # Faster page loads (DOM ready is enough for scraping)
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Disable unnecessary features
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    
    # Block content that slows down loading
    options.block_notifications = True
    options.block_popups = True
    
    # Disable images for even faster loading (if you don't need them)
    options.add_argument('--blink-settings=imagesEnabled=false')
    
    # Network optimizations
    options.add_argument('--disable-features=NetworkPrediction')
    options.add_argument('--dns-prefetch-disable')
    
    return options

async def fast_scraping_example():
    options = create_fast_scraping_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Blazingly fast navigation and scraping
        urls = ['https://example.com', 'https://example.org', 'https://example.net']
        
        for url in urls:
            await tab.go_to(url)
            title = await tab.execute_script('return document.title')
            print(f"{url}: {title}")

asyncio.run(fast_scraping_example())
```

### Full Stealth Configuration

For maximum undetectability, combine command-line arguments with browser preferences:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

def create_full_stealth_options() -> ChromiumOptions:
    """Complete stealth configuration combining arguments and preferences."""
    options = ChromiumOptions()
    
    # ===== Command-Line Arguments =====
    
    # Core stealth
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # User agent (use a recent, common one)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    
    # Language and locale
    options.add_argument('--lang=en-US')
    options.add_argument('--accept-lang=en-US,en;q=0.9')
    
    # WebGL (software renderer to avoid unique GPU signatures)
    options.add_argument('--use-gl=swiftshader')
    options.add_argument('--disable-features=WebGLDraftExtensions')
    
    # WebRTC IP leak prevention
    options.webrtc_leak_protection = True

    # Permissions and first-run
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    
    # Window size (common resolution)
    options.add_argument('--window-size=1920,1080')
    
    # ===== Browser Preferences =====
    # For comprehensive browser preferences configuration, see:
    # https://pydoll.tech/docs/features/configuration/browser-preferences/#stealth-fingerprinting
    
    return options

async def stealth_automation_example():
    options = create_full_stealth_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Test on bot detection sites
        await tab.go_to('https://bot.sannysoft.com')
        await asyncio.sleep(5)
        
        # Your automation here...

asyncio.run(stealth_automation_example())
```

!!! warning "User-Agent Consistency is Critical"
    Setting `--user-agent` only changes the **HTTP header**, but detection systems also check `navigator.userAgent`, `navigator.platform`, `navigator.vendor`, and other JavaScript properties. **Inconsistencies between these values are a strong bot indicator.**
    
    For example, if your HTTP User-Agent says "Windows" but `navigator.platform` says "Linux", you'll be flagged immediately.
    
    **Solution**: You must also override JavaScript properties via CDP to maintain consistency. See **[Browser Fingerprinting - User-Agent Consistency](../../deep-dive/fingerprinting/browser-fingerprinting.md#user-agent-consistency)** for detailed explanation and implementation using `Page.addScriptToEvaluateOnNewDocument`.
    
    This is why comprehensive stealth requires both command-line arguments AND browser preferences configuration.

!!! tip "Complete Stealth Strategy"
    Command-line arguments are only part of the solution. For maximum stealth:
    
    1. **Use arguments above** (navigator.webdriver, WebGL, WebRTC)
    2. **Configure browser preferences** - See [Browser Preferences - Stealth & Fingerprinting](browser-preferences.md#stealth-fingerprinting)
    3. **Human-like interactions** - See [Human-Like Interactions](../automation/human-interactions.md)
    4. **Good proxy/IP reputation** - Use residential proxies

### Docker/CI Configuration

For containerized environments:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.constants import PageLoadState

def create_docker_options() -> ChromiumOptions:
    """Configuration for Docker containers and CI/CD."""
    options = ChromiumOptions()
    
    # Required for Docker
    options.headless = True
    options.add_argument('--no-sandbox')  # Sandbox conflicts with container isolation
    options.add_argument('--disable-dev-shm-usage')  # Overcome /dev/shm size limit
    
    # Stability
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    
    # Memory optimization
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    
    # Faster page loads for CI
    options.page_load_state = PageLoadState.INTERACTIVE
    
    # Increase timeout for slow CI runners
    options.start_timeout = 20
    
    # Crash handling
    options.add_argument('--disable-crash-reporter')
    
    return options

async def ci_testing_example():
    options = create_docker_options()
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Run your tests...
        await tab.go_to('https://example.com')
        assert await tab.execute_script('return document.title') == 'Example Domain'

asyncio.run(ci_testing_example())
```

## Troubleshooting

### Browser Won't Start

```python
# Increase timeout
options.start_timeout = 30

# Check binary location
options.binary_location = '/path/to/chrome'

# Docker/CI issues
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

### Slow Performance

```python
# Disable GPU if not needed
options.add_argument('--disable-gpu')

# Disable images
options.add_argument('--blink-settings=imagesEnabled=false')

# Use INTERACTIVE load state
options.page_load_state = PageLoadState.INTERACTIVE

# Disable unnecessary features
options.add_argument('--disable-extensions')
options.add_argument('--disable-background-networking')
```

### Memory Issues in Docker

```python
# Essential for Docker
options.add_argument('--disable-dev-shm-usage')

# Reduce memory footprint
options.add_argument('--disable-extensions')
options.add_argument('--disable-gpu')
options.add_argument('--single-process')  # Last resort (can be unstable)
```

## Further Reading

- **[Browser Preferences](browser-preferences.md)** - Chromium's internal preference system
- **[Stealth Automation](../automation/human-interactions.md)** - Human-like interactions
- **[Contexts](../browser-management/contexts.md)** - Isolated browsing contexts
- **[Network Interception](../network/interception.md)** - Request/response manipulation

!!! tip "Experimentation is Key"
    Browser configuration is highly dependent on your specific use case. Start with the examples here, then adjust based on your needs. Use `browser._connection_port` to access DevTools and inspect what's happening inside the browser.
