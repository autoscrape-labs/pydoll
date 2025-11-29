# Cloudflare Turnstile Interaction

Pydoll provides native support for interacting with Cloudflare Turnstile captchas by performing realistic browser clicks. This is **not a bypass or circumvention**. It simply automates the same click action a human would perform on the captcha checkbox.

!!! warning "What This Feature Actually Does"
    This feature **clicks** on the Cloudflare Turnstile captcha checkbox using standard browser interactions. That's it. There is no:
    
    - **NO**: Magic bypass or circumvention
    - **NO**: Challenge solving (image selection, puzzles, etc.)
    - **NO**: Score manipulation or fingerprint spoofing
    - **YES**: Just a realistic click on the captcha container
    
    **Success depends entirely on your environment** (IP reputation, browser fingerprint, behavior patterns). Pydoll provides the mechanism to click; your environment determines if the click is accepted.

!!! info "What Is Cloudflare Turnstile?"
    Cloudflare Turnstile is a modern captcha system that analyzes browser environment and behavioral signals to determine if you're human. It typically shows as a checkbox that users must click. The system analyzes:
    
    - **IP reputation**: Is your IP address flagged or suspicious?
    - **Browser fingerprint**: Does your browser look legitimate?
    - **Behavioral patterns**: Do you behave like a human?
    
    When trust score is high enough, the checkbox click is accepted. When it's too low, Turnstile may show a challenge (which Pydoll **cannot solve**) or block you entirely.

## Quick Start

### Context Manager (Recommended)

The context manager waits for the captcha to appear, clicks it, and waits for resolution before continuing:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def turnstile_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Context manager handles captcha automatically
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')
        
        # This code only runs after captcha is clicked
        print("Turnstile captcha interaction complete!")
        
        # Continue with your automation
        content = await tab.find(id='protected-content')
        print(await content.text)

asyncio.run(turnstile_example())
```

### Background Processing

Enable automatic captcha clicking in the background:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def background_turnstile():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Enable automatic clicking before navigating
        await tab.enable_auto_solve_cloudflare_captcha()
        
        # Navigate to protected site
        await tab.go_to('https://site-with-turnstile.com')
        
        # Wait for captcha to be processed in background
        await asyncio.sleep(5)
        
        print("Page loaded with background captcha handling")
        
        # Disable when no longer needed
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(background_turnstile())
```

## Customizing Captcha Interaction

### Custom Selector

Some sites use different class names or wrappers for the captcha:

```python
from pydoll.constants import By

async def custom_selector_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Use custom selector if default doesn't work
        custom_selector = (By.CLASS_NAME, 'custom-captcha-wrapper')
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=custom_selector
        ):
            await tab.go_to('https://site-with-custom-turnstile.com')
        
        print("Custom selector used successfully!")

asyncio.run(custom_selector_example())
```

!!! tip "Finding the Right Selector"
    To find the correct selector:
    
    1. Open the site in Chrome DevTools
    2. Inspect the captcha iframe/container
    3. Look for unique class names or IDs
    4. Use that selector with `custom_selector` parameter
    
    The default selector is `(By.CLASS_NAME, 'cf-turnstile')` which works for most standard Cloudflare Turnstile implementations.

### Timing Configuration

The captcha checkbox doesn't always appear immediately. Adjust timing to match the site's behavior:

```python
async def timing_configuration_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha(
            time_before_click=3,      # Wait 3 seconds before clicking (default: 2)
            time_to_wait_captcha=10   # Wait up to 10 seconds for captcha to appear (default: 5)
        ):
            await tab.go_to('https://site-with-slow-turnstile.com')
        
        print("Captcha interaction complete with custom timing!")

asyncio.run(timing_configuration_example())
```

**Parameter Reference:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `custom_selector` | `Optional[tuple[By, str]]` | `(By.CLASS_NAME, 'cf-turnstile')` | CSS selector for captcha container |
| `time_before_click` | `int` | `2` | Seconds to wait before clicking (simulates human thinking time) |
| `time_to_wait_captcha` | `int` | `5` | Maximum seconds to wait for captcha to appear |

!!! info "Why Timing Matters"
    - **`time_before_click`**: Simulates human reaction time. Clicking too fast can look suspicious.
    - **`time_to_wait_captcha`**: Some sites load the captcha asynchronously. If the captcha doesn't appear within this time, the interaction is skipped.

## Other Captcha Systems

### reCAPTCHA v3 (Invisible)

reCAPTCHA v3 is **completely invisible** and requires **no interaction**. Just navigate normally:

```python
async def recaptcha_v3_example():
    options = ChromiumOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # No special handling needed - just navigate
        await tab.go_to('https://site-with-recaptcha-v3.com')
        
        # reCAPTCHA v3 runs in background, analyzing your behavior
        await asyncio.sleep(3)
        
        # Continue with form submission
        submit_button = await tab.find(id='submit-btn')
        await submit_button.click()

asyncio.run(recaptcha_v3_example())
```

!!! note "reCAPTCHA v3 Success Factors"
    Since reCAPTCHA v3 is entirely passive (no interaction), success depends on:
    
    - **IP reputation**: Use residential proxies with good reputation
    - **Browser fingerprint**: Configure realistic browser preferences
    - **Behavioral patterns**: Spend time on page, scroll naturally, type realistically
    
    If your score is too low, some sites may show a reCAPTCHA v2 challenge (which Pydoll **cannot solve**).

## What Determines Success?

The success of captcha interaction depends **entirely on your environment**, not on Pydoll. The captcha system analyzes:

### 1. IP Reputation (Most Critical)

| IP Type | Trust Level | Expected Behavior |
|---------|-------------|-------------------|
| **Residential IP (clean)** | High | Generally accepted without challenges |
| **Mobile IP** | High | Generally accepted without challenges |
| **Datacenter IP** | Low | Often blocked or challenged |
| **Previously blocked IP** | Very Low | Almost always blocked or challenged |

!!! danger "IP Reputation is Everything"
    **No tool can overcome a bad IP address.** If your IP is flagged, you will be blocked or challenged regardless of how realistic your browser looks.
    
    Use residential proxies with good reputation for best results.

### 2. Browser Fingerprint

Configure your browser to look legitimate:

```python
import time
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

async def stealth_configuration():
    options = ChromiumOptions()
    
    # Stealth arguments
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    
    # Realistic browser preferences
    current_time = int(time.time())
    options.browser_preferences = {
        'profile': {
            'last_engagement_time': str(current_time - (3 * 60 * 60)),  # 3 hours ago
            'exited_cleanly': True,
            'exit_type': 'Normal',
        },
        'safebrowsing': {'enabled': True},
    }
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-turnstile.com')

asyncio.run(stealth_configuration())
```

### 3. Behavioral Patterns

Captcha systems analyze how you interact with the page:

```python
async def realistic_behavior():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://site-with-turnstile.com')
        
        # Simulate human behavior before captcha appears
        await asyncio.sleep(2)  # Read page content
        await tab.execute_script('window.scrollBy(0, 300)')  # Scroll
        await asyncio.sleep(1)
        
        # Now interact with captcha
        async with tab.expect_and_bypass_cloudflare_captcha():
            # The captcha interaction happens here
            pass
        
        print("Captcha passed with realistic behavior!")

asyncio.run(realistic_behavior())
```

!!! tip "Behavioral Fingerprinting"
    For in-depth understanding of how behavioral patterns affect captcha success, see **[Behavioral Fingerprinting](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)**. This guide explains:
    
    - Mouse movement patterns and detection
    - Keystroke timing analysis
    - Scroll behavior physics
    - Event sequence analysis
    
    Understanding these concepts can help you build more realistic automation that achieves higher success rates.

## Troubleshooting

### Captcha Not Being Clicked

**Symptoms**: Captcha appears but is never clicked, page stays on challenge.

**Possible Causes:**

1. **Wrong selector**: Site uses different element class/ID
2. **Timing too short**: Captcha hasn't loaded yet when Pydoll tries to click
3. **Element not visible**: Captcha is hidden or rendered differently

**Solutions:**

```python
async def troubleshooting_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Increase wait times and use custom selector
        async with tab.expect_and_bypass_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'your-selector-here'),
            time_before_click=5,     # Longer delay before clicking
            time_to_wait_captcha=15  # More time to find captcha
        ):
            await tab.go_to('https://problematic-site.com')

asyncio.run(troubleshooting_example())
```

### Captcha Clicked but Shows Challenge

**Symptoms**: Checkbox shows checkmark briefly, then presents an image/puzzle challenge.

**Root Cause**: Your environment's trust score is too low.

**Solutions:**

- Use residential proxies with good reputation
- Configure realistic browser fingerprint
- Add more realistic behavioral patterns (scrolling, mouse movement, delays)
- **Note**: Pydoll cannot solve the challenge itself

### "Access Denied" or Immediate Block

**Symptoms**: Site immediately shows "Access Denied" or blocks you without showing captcha.

**Root Cause**: **Your IP address is flagged.**

**Solutions:**

- Use different residential proxy with good reputation
- Rotate IPs between requests
- Test your IP at `https://www.cloudflare.com/cdn-cgi/trace`
- **Note**: No amount of browser configuration will fix a flagged IP

### Works Locally but Fails in Docker/CI

**Symptoms**: Captcha interaction works on your machine but fails in Docker/CI environments.

**Root Cause**: Datacenter IPs are heavily scrutinized by captcha systems.

**Solutions:**

1. **Use headless mode with proper display** (for full rendering):
   ```dockerfile
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \
       chromium \
       chromium-driver \
       xvfb \
       && rm -rf /var/lib/apt/lists/*
   
   ENV DISPLAY=:99
   
   CMD Xvfb :99 -screen 0 1920x1080x24 & python your_script.py
   ```

2. **Use residential proxy** even in CI/CD:
   ```python
   options = ChromiumOptions()
   options.add_argument('--proxy-server=http://user:pass@residential-proxy.com:8080')
   ```

## Best Practices

1. **Use residential proxies**: IP reputation is the most critical factor
2. **Configure stealth options**: Remove automation indicators
3. **Add behavioral patterns**: Scroll, wait, move mouse before clicking
4. **Adjust timing**: Give captcha time to load before attempting click
5. **Use custom selectors**: When default selector doesn't work
6. **Handle failures gracefully**: Have fallback logic when captcha cannot be passed
7. **Test your environment**: Verify IP reputation and browser fingerprint before automation

## Ethical Guidelines

!!! danger "Terms of Service and Legal Compliance"
    Interacting with captchas may violate a website's Terms of Service even if technically possible. **Always check and respect ToS** before automating any website.
    
    This feature is provided for **legitimate automation purposes only**:
    
    **Appropriate use cases:**
    - Automated testing of your own applications
    - Monitoring services you have permission to monitor
    - Research and security analysis with proper authorization
    
    **Inappropriate use cases:**
    - Scraping content you don't have permission to access
    - Circumventing paywalls or subscription systems
    - Denial-of-service attacks or aggressive scraping
    - Any activity that violates Terms of Service

## See Also

- **[Browser Options](../configuration/browser-options.md)** - Stealth configuration
- **[Browser Preferences](../configuration/browser-preferences.md)** - Advanced fingerprinting
- **[Proxy Configuration](../configuration/proxy.md)** - Setting up proxies
- **[Behavioral Fingerprinting](../../deep-dive/fingerprinting/behavioral-fingerprinting.md)** - Understanding behavioral detection
- **[Human-Like Interactions](../automation/human-interactions.md)** - Realistic behavior patterns

---

**Remember**: Pydoll provides the mechanism to click on captchas, but your environment (IP, fingerprint, behavior) determines success. This is not a magic solution, it's a tool that works when used in the right environment with proper configuration.
