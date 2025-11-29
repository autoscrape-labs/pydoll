# Fingerprint Evasion Techniques

This document provides **practical, actionable techniques** for evading fingerprinting using Pydoll's CDP integration, JavaScript overrides, and request interception. Everything described here has been tested and validated.

!!! info "Module Navigation"
    - **[← Fingerprinting Overview](./index.md)** - Module introduction and philosophy
    - **[← Network Fingerprinting](./network-fingerprinting.md)** - Protocol-level fingerprinting
    - **[← Browser Fingerprinting](./browser-fingerprinting.md)** - Application-layer fingerprinting
    - **[← Behavioral Fingerprinting](./behavioral-fingerprinting.md)** - Human behavior analysis
    
    For practical Pydoll usage, see **[Human-Like Interactions](../../features/automation/human-interactions.md)** and **[Behavioral Captcha Bypass](../../features/advanced/behavioral-captcha-bypass.md)**.

!!! warning "Theory → Practice"
    This is where everything you've learned about network and browser fingerprinting gets applied. Each technique includes **working code examples** ready to integrate with Pydoll.

## CDP-Based Fingerprint Evasion

The Chrome DevTools Protocol (CDP) provides powerful methods to modify browser behavior at a deep level, far beyond what JavaScript injection can achieve. This makes CDP-based automation (like Pydoll) **significantly more stealthy** than Selenium or Puppeteer.

### The User-Agent Mismatch Problem

One of the **most common** fingerprinting inconsistencies in automation is the mismatch between:

1. **HTTP `User-Agent` header** (sent with every request)
2. **`navigator.userAgent`** property (JavaScript-accessible)

**The problem:**

```python
# Bad approach: Setting User-Agent via command-line argument
options = ChromiumOptions()
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)...')

# Result:
# HTTP header: Mozilla/5.0 (Windows NT 10.0; Win64; x64)... (correct)
# navigator.userAgent: Chrome/120.0.0.0 (original value - wrong!)
# → MISMATCH DETECTED!
```

**Why this happens:**

- `--user-agent` flag only modifies **HTTP headers**
- `navigator.userAgent` is set **before** page load from internal Chromium values
- JavaScript cannot see HTTP headers directly, but servers can compare both values

**Detection technique (server-side):**

```python
def detect_user_agent_mismatch(request):
    """
    Server-side detection of User-Agent inconsistency.
    """
    # Get HTTP header
    http_user_agent = request.headers.get('User-Agent')
    
    # Execute JavaScript to get navigator.userAgent
    # (done via challenge/captcha page)
    navigator_user_agent = get_client_navigator_ua()
    
    if http_user_agent != navigator_user_agent:
        return 'AUTOMATION_DETECTED'  # Clear mismatch
    
    return 'OK'
```

### Solution: CDP Emulation Domain

The correct way to set User-Agent is via CDP's **Emulation.setUserAgentOverride** method, which modifies **both** the HTTP header and navigator properties. In Pydoll, you can execute CDP commands directly:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.commands import PageCommands


async def set_user_agent_correctly(tab, user_agent: str, platform: str = 'Win32'):
    """
    Set User-Agent properly using CDP Emulation domain.
    This ensures consistency between HTTP headers and navigator properties.
    
    Note: Pydoll doesn't expose Emulation commands directly yet, so we use
    execute_script to override navigator properties for now.
    """
    # Override navigator.userAgent via JavaScript
    override_script = f'''
        Object.defineProperty(Navigator.prototype, 'userAgent', {{
            get: () => '{user_agent}'
        }});
        Object.defineProperty(Navigator.prototype, 'platform', {{
            get: () => '{platform}'
        }});
    '''
    
    await tab.execute_script(override_script)


async def main():
    async with Chrome() as browser:
        # Set User-Agent via command-line argument (affects HTTP headers)
        options = browser.options
        custom_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={custom_ua}')
        
        tab = await browser.start()
        
        # Also override navigator.userAgent via JavaScript for consistency
        await set_user_agent_correctly(tab, custom_ua)
        
        # Navigate (User-Agent now consistent)
        await tab.go_to('https://example.com')
        
        # Verify consistency
        result = await tab.execute_script('return navigator.userAgent')
        nav_ua = result['result']['result']['value']
        print(f"navigator.userAgent: {nav_ua}")
        # Both match now!

asyncio.run(main())
```

!!! warning "Client Hints Consistency"
    When setting a custom User-Agent, you **must** also set consistent `userAgentMetadata` (Client Hints), otherwise modern Chromium will send **inconsistent** `Sec-CH-UA` headers!
    
    **Example inconsistency:**

    - User-Agent: "Chrome/120.0.0.0"
    - Sec-CH-UA: "Chrome/119" (wrong version!)
    - → Detection!

### Fingerprint Modification Techniques

While Pydoll doesn't expose all CDP Emulation commands directly, you can achieve similar results using JavaScript overrides and browser options:

#### 1. Timezone Override (via JavaScript)

```python
async def set_timezone(tab, timezone_id: str):
    """
    Override timezone via JavaScript.
    Example: 'America/New_York', 'Europe/London', 'Asia/Tokyo'
    
    Note: This overrides the JavaScript API but doesn't affect system-level
    timezone. Use --tz command-line argument for complete emulation.
    """
    script = f'''
        // Override Intl.DateTimeFormat
        const originalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const options = args[1] || {{}};
            options.timeZone = '{timezone_id}';
            return new originalDateTimeFormat(args[0], options);
        }};
        
        // Override Date.prototype.getTimezoneOffset
        const timezoneOffsets = {{
            'America/New_York': 300,
            'Europe/London': 0,
            'Asia/Tokyo': -540,
            'America/Los_Angeles': 480,
        }};
        Date.prototype.getTimezoneOffset = function() {{
            return timezoneOffsets['{timezone_id}'] || 0;
        }};
    '''
    await tab.execute_script(script)


# Usage
await set_timezone(tab, 'America/Los_Angeles')

# Verify
result = await tab.execute_script('return Intl.DateTimeFormat().resolvedOptions().timeZone')
tz = result['result']['result']['value']
print(f"Timezone: {tz}")  # America/Los_Angeles
```

#### 2. Locale Override (via Browser Options)

```python
# Set locale via command-line arguments
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.add_argument('--lang=pt-BR')
options.set_accept_languages('pt-BR,pt;q=0.9,en;q=0.8')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    
    # Verify
    result = await tab.execute_script('return navigator.language')
    locale = result['result']['result']['value']
    print(f"Locale: {locale}")  # pt-BR
```

#### 3. Geolocation Override (via JavaScript)

```python
async def set_geolocation(tab, latitude: float, longitude: float, accuracy: int = 1):
    """
    Override geolocation via JavaScript.
    """
    script = f'''
        navigator.geolocation.getCurrentPosition = function(success) {{
            const position = {{
                coords: {{
                    latitude: {latitude},
                    longitude: {longitude},
                    accuracy: {accuracy},
                    altitude: null,
                    altitudeAccuracy: null,
                    heading: null,
                    speed: null
                }},
                timestamp: Date.now()
            }};
            success(position);
        }};
    '''
    await tab.execute_script(script)


# Example: New York City
await set_geolocation(tab, 40.7128, -74.0060)
```

#### 4. Device Metrics (via Browser Options)

```python
# Mobile emulation via command-line arguments
options = ChromiumOptions()
options.add_argument('--window-size=393,852')
options.add_argument('--device-scale-factor=3')
options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

async with Chrome(options=options) as browser:
    tab = await browser.start()
    
    # Override additional mobile properties
    mobile_script = '''
        Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {
            get: () => 5
        });
        
        // Override screen properties
        Object.defineProperty(window.screen, 'width', { get: () => 393 });
        Object.defineProperty(window.screen, 'height', { get: () => 852 });
        Object.defineProperty(window.screen, 'availWidth', { get: () => 393 });
        Object.defineProperty(window.screen, 'availHeight', { get: () => 852 });
    '''
    await tab.execute_script(mobile_script)
```

#### 5. Touch Events (via JavaScript)

```python
async def enable_touch_events(tab, max_touch_points: int = 5):
    """
    Override touch-related properties.
    """
    script = f'''
        Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {{
            get: () => {max_touch_points}
        }});
        
        // Add touch event support
        if (!window.TouchEvent) {{
            window.TouchEvent = class TouchEvent extends UIEvent {{}};
        }}
    '''
    await tab.execute_script(script)


# Verify
result = await tab.execute_script('return navigator.maxTouchPoints')
touch_points = result['result']['result']['value']
print(f"Max Touch Points: {touch_points}")  # 5
```

### Request Interception for Header Modification

Pydoll provides native support for request interception via the Fetch domain. This allows you to modify headers, block requests, or provide custom responses:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def setup_request_interception(tab):
    """
    Intercept all requests and modify headers using Pydoll's native methods.
    """
    # Enable Fetch domain for request interception
    await tab.enable_fetch_events()
    
    # Listen for request paused events
    async def handle_request(event):
        """Handle intercepted requests."""
        request_id = event['params']['requestId']
        request = event['params']['request']
        
        # Get current headers
        headers = request.get('headers', {})
        
        # Fix common inconsistencies
        if 'Accept-Encoding' in headers:
            # Ensure Brotli support
            if 'br' not in headers['Accept-Encoding']:
                headers['Accept-Encoding'] = 'gzip, deflate, br, zstd'
        
        # Remove automation markers
        headers.pop('X-Requested-With', None)
        
        # Convert headers to HeaderEntry format
        header_list = [{'name': k, 'value': v} for k, v in headers.items()]
        
        # Continue request with modified headers
        await tab.continue_request(
            request_id=request_id,
            headers=header_list
        )
    
    # Register event listener for request paused events
    await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Setup interception before navigation
        await setup_request_interception(tab)
        
        # All requests will now have modified headers
        await tab.go_to('https://example.com')

asyncio.run(main())
```

### Complete Fingerprint Evasion Example

Here's a comprehensive example combining all techniques using Pydoll's API:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


class FingerprintEvader:
    """
    Comprehensive fingerprint evasion using browser options and JavaScript.
    """
    
    def __init__(self, profile: dict):
        """
        Initialize with target profile (OS, location, device, etc.)
        """
        self.profile = profile
        self.options = ChromiumOptions()
        self._configure_browser_options()
    
    def _configure_browser_options(self):
        """Configure browser launch options based on profile."""
        # 1. User-Agent
        self.options.add_argument(f'--user-agent={self.profile["userAgent"]}')
        
        # 2. Language and locale
        self.options.add_argument(f'--lang={self.profile["locale"]}')
        self.options.set_accept_languages(self.profile["acceptLanguage"])
        
        # 3. Window size (screen dimensions)
        screen = self.profile['screen']
        self.options.add_argument(f'--window-size={screen["width"]},{screen["height"]}')
        
        # 4. Device scale factor (for high-DPI displays)
        if screen.get('deviceScaleFactor', 1.0) != 1.0:
            self.options.add_argument(f'--device-scale-factor={screen["deviceScaleFactor"]}')
    
    async def apply_to_tab(self, tab):
        """
        Apply JavaScript overrides to tab after launch.
        """
        script = f'''
            // Override User-Agent (for consistency)
            Object.defineProperty(Navigator.prototype, 'userAgent', {{
                get: () => '{self.profile["userAgent"]}'
            }});
            
            // Override platform
            Object.defineProperty(Navigator.prototype, 'platform', {{
                get: () => '{self.profile["platform"]}'
            }});
            
            // Override hardware concurrency
            Object.defineProperty(Navigator.prototype, 'hardwareConcurrency', {{
                get: () => {self.profile.get('hardwareConcurrency', 8)}
            }});
            
            // Override device memory
            Object.defineProperty(Navigator.prototype, 'deviceMemory', {{
                get: () => {self.profile.get('deviceMemory', 8)}
            }});
            
            // Override languages
            Object.defineProperty(Navigator.prototype, 'languages', {{
                get: () => {self.profile['languages']}
            }});
            
            // Override vendor
            Object.defineProperty(Navigator.prototype, 'vendor', {{
                get: () => '{self.profile.get('vendor', 'Google Inc.')}'
            }});
            
            // Override max touch points (for mobile)
            Object.defineProperty(Navigator.prototype, 'maxTouchPoints', {{
                get: () => {self.profile.get('maxTouchPoints', 0)}
            }});
        '''
        
        await tab.execute_script(script)
        
        # Apply geolocation if provided
        if 'geolocation' in self.profile:
            await self._override_geolocation(tab)
        
        # Apply timezone if provided
        if 'timezone' in self.profile:
            await self._override_timezone(tab)
    
    async def _override_geolocation(self, tab):
        """Override geolocation API."""
        geo = self.profile['geolocation']
        script = f'''
            navigator.geolocation.getCurrentPosition = function(success) {{
                const position = {{
                    coords: {{
                        latitude: {geo['latitude']},
                        longitude: {geo['longitude']},
                        accuracy: 1,
                        altitude: null,
                        altitudeAccuracy: null,
                        heading: null,
                        speed: null
                    }},
                    timestamp: Date.now()
                }};
                success(position);
            }};
        '''
        await tab.execute_script(script)
    
    async def _override_timezone(self, tab):
        """Override timezone-related functions."""
        timezone = self.profile['timezone']
        # Map of timezone to offset in minutes
        offsets = {
            'America/New_York': 300,
            'Europe/London': 0,
            'Asia/Tokyo': -540,
            'America/Los_Angeles': 480,
        }
        offset = offsets.get(timezone, 0)
        
        script = f'''
            // Override Intl.DateTimeFormat
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...args) {{
                const options = args[1] || {{}};
                options.timeZone = '{timezone}';
                return new originalDateTimeFormat(args[0], options);
            }};
            
            // Override Date.prototype.getTimezoneOffset
            Date.prototype.getTimezoneOffset = function() {{
                return {offset};
            }};
        '''
        await tab.execute_script(script)


# Usage example
async def main():
    # Define target profile
    profile = {
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'platform': 'Win32',
        'acceptLanguage': 'en-US,en;q=0.9',
        'languages': ['en-US', 'en'],
        'timezone': 'America/New_York',
        'locale': 'en-US',
        'geolocation': {
            'latitude': 40.7128,
            'longitude': -74.0060
        },
        'screen': {
            'width': 1920,
            'height': 1080,
            'deviceScaleFactor': 1.0
        },
        'hardwareConcurrency': 8,
        'deviceMemory': 8,
        'vendor': 'Google Inc.',
        'maxTouchPoints': 0,  # Desktop
    }
    
    # Create evader with profile
    evader = FingerprintEvader(profile)
    
    # Launch browser with configured options
    async with Chrome(options=evader.options) as browser:
        tab = await browser.start()
        
        # Apply JavaScript overrides
        await evader.apply_to_tab(tab)
        
        # Navigate with consistent fingerprint
        await tab.go_to('https://example.com')
        
        # Verify fingerprint
        result = await tab.execute_script('''
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                maxTouchPoints: navigator.maxTouchPoints,
            };
        ''')
        
        fingerprint = result['result']['result']['value']
        
        print("Applied Fingerprint:")
        for key, value in fingerprint.items():
            print(f"  {key}: {value}")

asyncio.run(main())
```

!!! tip "Fingerprint Consistency is Key"
    The most important aspect of fingerprint evasion is **consistency across all layers**:
    
    1. **HTTP headers** (User-Agent, Accept-Language, Sec-CH-UA)
    2. **Navigator properties** (userAgent, platform, languages)
    3. **System properties** (timezone, locale, screen resolution)
    4. **Network fingerprint** (TLS, HTTP/2 settings)
    
    A single inconsistency can reveal automation!

!!! info "CDP Emulation References"
    - **[Chrome DevTools Protocol: Emulation Domain](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/)** - Official CDP Emulation documentation
    - **[Chrome DevTools Protocol: Fetch Domain](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/)** - Request interception documentation
    - **[Chromium Emulation Source](https://source.chromium.org/chromium/chromium/src/+/main:third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc)** - Emulation implementation in Chromium
    - **[Pydoll CDP Guide](./cdp.md)** - Using CDP with Pydoll

## Behavioral Evasion Strategies

Given Pydoll's CDP-based architecture, behavioral fingerprinting requires careful attention to human-like interaction patterns. For theoretical background on behavioral detection, see [Behavioral Fingerprinting](./behavioral-fingerprinting.md).

### Current State: Manual Randomization Required

As documented in [Human-Like Interactions](../../features/automation/human-interactions.md), Pydoll **currently requires manual implementation** of behavioral realism:

- **Mouse movements**: Must be implemented with Bezier curves and randomization
- **Typing**: Requires character-by-character input with variable intervals
- **Scrolling**: Needs manual JavaScript with momentum simulation
- **Event sequences**: Must ensure proper ordering (mousemove → mousedown → mouseup → click)

### Future Improvements

Future versions of Pydoll will include automated behavioral realism:

```python
# Future API (not yet implemented)
await element.click(
    realistic=True,              # Automatic Bezier curve movement
    offset='random',             # Random offset within bounds
    thinking_time=(1.0, 3.0)     # Random delay before action
)

await input_field.type_text(
    "human-like text",
    realistic=True,              # Variable typing speed with bigram timing
    error_rate=0.05              # 5% chance of typo + backspace
)

await tab.scroll_to(
    target_y=1000,
    realistic=True,              # Momentum + inertia simulation
    speed='medium'               # Human-like scroll speed
)
```

### Practical Implementation Now

Until automation is built-in, follow these practices:

#### 1. Mouse Movement Before Clicks

```python
# Bad: Instant click without movement
await element.click()  # Teleports cursor and clicks center

# Good: Realistic movement first
# (Manual implementation required)
await move_mouse_realistically(element)
await asyncio.sleep(random.uniform(0.1, 0.3))
await element.click(x_offset=random.randint(-10, 10))
```

#### 2. Variable Typing Speed

```python
# Bad: Constant interval
await input.type_text("text", interval=0.1)  # Robotic timing

# Good: Variable intervals per character
for char in "text":
    await input.type_text(char, interval=0)
    await asyncio.sleep(random.uniform(0.08, 0.22))
```

#### 3. Thinking Time

```python
# Bad: Instant action after page load
await tab.go_to('https://example.com')
await button.click()  # Too fast!

# Good: Natural delay for reading/scanning
await tab.go_to('https://example.com')
await asyncio.sleep(random.uniform(2.0, 5.0))  # Read page
await random_mouse_movement()  # Scan with cursor
await button.click()  # Then act
```

#### 4. Scrolling with Momentum

```python
# Bad: Instant scroll
await tab.execute_script("window.scrollTo(0, 1000)")

# Good: Gradual scroll with deceleration
scroll_events = simulate_human_scroll(target=1000)
for delta, delay in scroll_events:
    await tab.execute_script(f"window.scrollBy(0, {delta})")
    await asyncio.sleep(delay)
```

!!! warning "Behavioral Detection is ML-Powered"
    Modern anti-bot systems use machine learning trained on billions of interactions. They don't use simple rules—they detect **statistical patterns**. Focus on:
    
    1. **Variability**: No two actions should be identical
    2. **Context**: Actions must follow natural sequences
    3. **Timing**: Realistic intervals based on human biomechanics
    4. **Consistency**: Don't mix bot-like and human-like patterns

## Best Practices for Fingerprint Evasion

Based on all the techniques covered in this guide, here are the essential best practices for successful fingerprint evasion in web automation:

### 1. Start with Real Browser Profiles

Don't invent fingerprints from scratch. Capture real browser profiles and use them:

```python
# Capture a real fingerprint from your own browser
# Visit https://browserleaks.com/ and collect all data
REAL_PROFILES = {
    'windows_chrome': {
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'platform': 'Win32',
        'hardwareConcurrency': 8,
        'deviceMemory': 8,
        'canvas_hash': 'captured_from_real_browser',
        # ... all other properties
    }
}
```

### 2. Maintain Consistency Across All Layers

**Check these consistency points:**

- User-Agent matches navigator.userAgent
- Platform matches User-Agent OS
- Language matches timezone/geolocation
- Screen resolution is realistic for claimed device
- Hardware specs match claimed platform (CPU cores, RAM)
- Canvas/WebGL fingerprints are stable (not randomized)
- Timezone matches Accept-Language header
- Client Hints match User-Agent

### 3. Use Browser Preferences for Stealth

Leverage Pydoll's browser preferences (see [Browser Preferences](../features/configuration/browser-preferences.md)):

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.browser_preferences = {
    # Simulate usage history
    'profile': {
        'created_by_version': '120.0.6099.130',
        'creation_time': str(time.time() - (90 * 24 * 60 * 60)),  # 90 days old
        'exit_type': 'Normal',
    },
    
    # Realistic content settings
    'profile.default_content_setting_values': {
        'cookies': 1,
        'images': 1,
        'javascript': 1,
        'notifications': 2,  # Ask (realistic)
    },
    
    # WebRTC IP handling (prevent leaks)
    'webrtc': {
        'ip_handling_policy': 'disable_non_proxied_udp',
    },
}
```

### 4. Rotate Fingerprints Wisely

**Don't** change fingerprints too frequently on the same site:

```python
# Bad: New fingerprint every request
for url in urls:
    fingerprint = generate_random_fingerprint()  # Suspicious!
    apply_fingerprint(tab, fingerprint)
    await tab.go_to(url)

# Good: Consistent fingerprint per session
fingerprint = select_fingerprint_for_target(target_site)
apply_fingerprint(tab, fingerprint)

for url in urls:
    await tab.go_to(url)  # Same fingerprint
```

### 5. Test Your Fingerprint

Use these tools to verify your fingerprint before deploying:

| Tool | URL | Tests |
|------|-----|-------|
| **BrowserLeaks** | https://browserleaks.com/ | Comprehensive: Canvas, WebGL, Fonts, IP, WebRTC |
| **AmIUnique** | https://amiunique.org/ | Fingerprint uniqueness analysis |
| **CreepJS** | https://abrahamjuliot.github.io/creepjs/ | Advanced lie detection |
| **Fingerprint.com Demo** | https://fingerprint.com/demo/ | Commercial-grade detection |
| **PixelScan** | https://pixelscan.net/ | Bot detection analysis |
| **IPLeak** | https://ipleak.net/ | WebRTC, DNS, IP leaks |

**Verification script:**

```python
async def verify_fingerprint(tab):
    """
    Verify fingerprint consistency before actual use.
    """
    tests = []
    
    # Test 1: User-Agent consistency
    nav_ua = await tab.execute_script('return navigator.userAgent')
    print(f"User-Agent: {nav_ua[:50]}...")
    
    # Test 2: Timezone/Language consistency
    tz = await tab.execute_script('return Intl.DateTimeFormat().resolvedOptions().timeZone')
    lang = await tab.execute_script('return navigator.language')
    print(f"Timezone: {tz}, Language: {lang}")
    
    # Test 3: WebDriver detection
    webdriver = await tab.execute_script('return navigator.webdriver')
    if webdriver:
        print("navigator.webdriver is true! (DETECTED)")
        tests.append(False)
    else:
        print("navigator.webdriver is undefined (OK)")
        tests.append(True)
    
    # Test 4: Canvas consistency
    canvas1 = await get_canvas_fingerprint(tab)
    await asyncio.sleep(0.5)
    canvas2 = await get_canvas_fingerprint(tab)
    if canvas1 == canvas2:
        print("Canvas fingerprint is consistent (OK)")
        tests.append(True)
    else:
        print("Canvas fingerprint is inconsistent, noise detected (DETECTED)")
        tests.append(False)
    
    # Test 5: Plugins
    plugins = await tab.execute_script('return navigator.plugins.length')
    print(f"Plugins: {plugins}")
    
    return all(tests)
```

### 6. Combine with Behavioral Realism

Fingerprint evasion alone is not enough. Combine with:

- **Human-like interactions** (see [Human Interactions](../features/automation/human-interactions.md))
- **Natural timing** (random delays, realistic page interaction time)
- **Behavioral captcha handling** (see [Behavioral Captcha Bypass](../features/advanced/behavioral-captcha-bypass.md))
- **Realistic cookies** (see [Cookies & Sessions](../features/browser-management/cookies-sessions.md))

### 7. Monitor for Detection

Implement logging to detect when your automation is flagged:

```python
async def monitor_detection_signals(tab):
    """
    Monitor for signs of detection.
    """
    signals = await tab.execute_script('''
        () => {
            return {
                // Check for known detection scripts
                fpjs: typeof window.Fingerprint !== 'undefined',
                datadome: typeof window.DD_RUM !== 'undefined',
                perimeter_x: typeof window._pxAppId !== 'undefined',
                cloudflare: document.querySelector('script[src*="challenges.cloudflare.com"]') !== null,
                
                // Check for challenge pages
                is_captcha: document.title.includes('Captcha') || 
                           document.title.includes('Challenge') ||
                           document.body.innerText.includes('verification'),
            };
        }
    ''')
    
    if any(signals.values()):
        print("Detection signals found:")
        for key, value in signals.items():
            if value:
                print(f"  - {key}: detected")
```

### 8. Use Proxies Correctly

Network-level fingerprinting requires proper proxy usage:

- **Match proxy location** with timezone/language
- **Use residential proxies** for high-value targets
- **Rotate proxies** but maintain fingerprint consistency per proxy
- **Test for WebRTC leaks** (see [Proxy Configuration](../features/configuration/proxy.md))

## Common Mistakes to Avoid

### Mistake 1: Randomizing Everything

```python
# Bad: Random fingerprint that doesn't make sense
fingerprint = {
    'userAgent': 'Chrome 120 on Windows',
    'platform': 'Linux x86_64',  # Mismatch!
    'hardwareConcurrency': random.randint(1, 32),  # Too random
    'deviceMemory': random.choice([0.5, 128]),  # Unrealistic values
}
```

**Why it fails**: Real browsers have **consistent, realistic** configurations. Random values create impossible combinations.

### Mistake 2: Ignoring Client Hints

```python
# Bad: Setting User-Agent without Client Hints
await tab.send_cdp_command('Emulation.setUserAgentOverride', {
    'userAgent': 'Chrome/120...',
    # Missing userAgentMetadata!
})
# Result: Sec-CH-UA headers will be inconsistent
```

### Mistake 3: Canvas Noise Injection

```python
# Bad: Adding random noise to canvas
def add_canvas_noise(ctx):
    # Randomize pixel values
    imageData = ctx.getImageData(0, 0, 100, 100)
    for i in range(len(imageData.data)):
        imageData.data[i] += random.randint(-5, 5)  # Noise injection
    ctx.putImageData(imageData, 0, 0)
```

**Why it fails**: Noise makes fingerprint **inconsistent**, which is itself detectable. Sites can request fingerprint multiple times and detect variations.

### Mistake 4: Outdated User-Agents

```python
# Bad: Using old browser version
userAgent = 'Mozilla/5.0 ... Chrome/90.0.0.0'  # 2 years old!
```

**Why it fails**: Old versions missing modern features are easily detected. Use versions from the last 3-6 months.

### Mistake 5: Headless Mode Detection

```python
# Bad: Using headless without proper configuration
options = ChromiumOptions()
options.headless = True  # Detectable via window dimensions
```

**Fix**: Use `--headless=new` with realistic window size:

```python
options = ChromiumOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
```

## Conclusion

Browser and network fingerprinting is a sophisticated cat-and-mouse game between automation developers and anti-bot systems. Success requires understanding fingerprinting at **multiple layers**:

**Network Level:**
- TCP/IP characteristics (TTL, window size, options)
- TLS handshake patterns (JA3, cipher suites, GREASE)
- HTTP/2 settings and stream priorities

**Browser Level:**
- HTTP headers consistency
- JavaScript API properties (navigator, screen, etc.)
- Canvas and WebGL rendering
- CDP-based evasion techniques

**Behavioral Level:**
- Mouse movement patterns and physics (Fitts's Law, Bezier curves)
- Keystroke dynamics and typing rhythm (bigrams, dwell/flight time)
- Scroll momentum and inertia
- Event sequences and timing analysis

**Key Takeaways:**

1. **Consistency is paramount** - A single mismatch can reveal automation
2. **Use real profiles** - Don't invent fingerprints from scratch
3. **CDP is powerful** - Leverage Emulation domain for deep modifications
4. **Test thoroughly** - Use fingerprinting test sites before deployment
5. **Combine layers** - Network + Browser + Behavioral evasion
6. **Stay updated** - Detection techniques evolve; keep fingerprints current

**Pydoll's Advantages:**

- **No `navigator.webdriver`** (unlike Selenium/Puppeteer)
- **Direct CDP access** for deep browser control
- **Request interception** via Fetch domain
- **Browser preferences** for realistic history/settings
- **Async architecture** for natural timing patterns

With the techniques in this guide, you can create **highly stealthy** browser automation that mimics real user behavior at every level.

!!! tip "Keep Learning"
    Fingerprinting is an active research area. Stay updated by:
    
    - Following security conferences (USENIX, Black Hat, DEF CON)
    - Monitoring anti-bot vendors (Akamai, Cloudflare, DataDome)
    - Testing your fingerprints regularly on detection sites
    - Reading Chromium source code for new fingerprinting vectors

## Further Reading

### Comprehensive Guides

- **[Pydoll Core Concepts](../features/core-concepts.md)** - Understanding Pydoll's architecture
- **[Chrome DevTools Protocol](./cdp.md)** - Deep dive into CDP usage
- **[Network Fingerprinting](./network-fingerprinting.md)** - Protocol-level identification techniques
- **[Browser Fingerprinting](./browser-fingerprinting.md)** - Application-layer detection methods
- **[Behavioral Fingerprinting](./behavioral-fingerprinting.md)** - Human behavior analysis and detection
- **[Browser Options](../features/configuration/browser-options.md)** - Command-line arguments for stealth
- **[Browser Preferences](../features/configuration/browser-preferences.md)** - Internal settings for realism
- **[Proxy Configuration](../features/configuration/proxy.md)** - Network-level anonymization
- **[Proxy Architecture](./proxy-architecture.md)** - Network fundamentals and detection
- **[Human Interactions](../features/automation/human-interactions.md)** - Behavioral realism
- **[Behavioral Captcha Bypass](../features/advanced/behavioral-captcha-bypass.md)** - Handling modern challenges

### External Resources

- **[Chromium Source Code](https://source.chromium.org/chromium/chromium/src)** - Official Chromium codebase
- **[Chrome DevTools Protocol Viewer](https://chromedevtools.github.io/devtools-protocol/)** - Interactive CDP documentation
- **[W3C Web Standards](https://www.w3.org/standards/)** - Official web specifications
- **[IETF RFCs](https://www.ietf.org/rfc/)** - Network protocol standards

### Academic Papers

- **[Mowery, Shacham: "Pixel Perfect" (USENIX 2012)](https://www.usenix.org/conference/usenixsecurity12/technical-sessions/presentation/mowery)** - Foundational canvas fingerprinting research
- **[Eckersley: "How Unique Is Your Browser?" (EFF 2010)](https://panopticlick.eff.org/static/browser-uniqueness.pdf)** - Early browser fingerprinting study
- **[Nikiforakis et al.: "Cookieless Monster" (IEEE 2013)](https://securitee.org/files/cookieless_sp2013.pdf)** - Advanced fingerprinting techniques
