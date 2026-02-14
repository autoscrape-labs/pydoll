# Retry Decorator

Web scraping is inherently unpredictable. Networks fail, pages load slowly, elements appear and disappear, rate limits kick in, and CAPTCHAs show up unexpectedly. The `@retry` decorator provides a robust, battle-tested solution for handling these inevitable failures gracefully.

## Why Use the Retry Decorator?

In production scraping, failures aren't exceptions, they're the norm. Instead of letting your entire scraping job crash because of a temporary network hiccup or a missing element, the retry decorator allows you to:

- **Recover automatically** from transient failures
- **Implement sophisticated retry strategies** with exponential backoff
- **Execute recovery logic** before retrying (refresh page, switch proxy, restart browser)
- **Keep your business logic clean** without polluting it with error handling code

## Quick Start

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout, NetworkError

@retry(max_retries=3, exceptions=[WaitElementTimeout, NetworkError])
async def scrape_product_page(url: str):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        
        # This might fail due to network issues or slow loading
        product_title = await tab.find(class_name='product-title', timeout=5)
        return await product_title.text

asyncio.run(scrape_product_page('https://example.com/product/123'))
```

If `scrape_product_page` fails with a `WaitElementTimeout` or `NetworkError`, it will automatically retry up to 3 times before giving up.

## Best Practice: Always Specify Exceptions

!!! warning "Critical Best Practice"
    **ALWAYS** specify which exceptions should trigger a retry. Using the default `exceptions=Exception` will catch **everything**, including bugs in your code that should fail immediately.

**Bad (catches everything, including bugs):**

```python
@retry(max_retries=3)  # DON'T DO THIS
async def scrape_data():
    data = response['items'][0]  # If 'items' doesn't exist, retries won't help!
    return data
```

**Good (only retries on expected failures):**

```python
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

@retry(
    max_retries=3,
    exceptions=[ElementNotFound, WaitElementTimeout, NetworkError]
)
async def scrape_data():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        return await tab.find(id='data-container', timeout=10)
```

By specifying exceptions, you ensure that:

- **Logic errors fail fast** (typos, wrong selectors, code bugs)
- **Only recoverable errors are retried** (network issues, timeouts, missing elements)
- **Debugging is easier** (you know exactly what went wrong)

## Parameters

### max_retries

Maximum number of retry attempts before giving up.

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=5, exceptions=[WaitElementTimeout])
async def fetch_data():
    # Will try up to 5 times total
    pass
```

### exceptions

Exception types that should trigger a retry. Can be a single exception or a list.

```python
from pydoll.exceptions import (
    ElementNotFound,
    WaitElementTimeout,
    NetworkError,
    ElementNotInteractable
)

# Single exception
@retry(exceptions=[WaitElementTimeout])
async def example1():
    pass

# Multiple exceptions
@retry(exceptions=[WaitElementTimeout, NetworkError, ElementNotFound, ElementNotInteractable])
async def example2():
    pass
```

!!! tip "Common Scraping Exceptions"
    For web scraping with Pydoll, you'll typically want to retry on:

    - `WaitElementTimeout` - Timeout waiting for element to appear
    - `ElementNotFound` - Element doesn't exist in DOM
    - `ElementNotVisible` - Element exists but is not visible
    - `ElementNotInteractable` - Element cannot receive interaction
    - `NetworkError` - Network connectivity issues
    - `ConnectionFailed` - Failed to connect to browser
    - `PageLoadTimeout` - Page load timed out
    - `ClickIntercepted` - Click was intercepted by another element

### delay

Time to wait between retry attempts (in seconds).

```python
from pydoll.exceptions import WaitElementTimeout

@retry(max_retries=3, exceptions=[WaitElementTimeout], delay=2.0)
async def scrape_with_delay():
    # Waits 2 seconds between each retry
    pass
```

### exponential_backoff

When `True`, increases the delay exponentially with each retry attempt.

```python
from pydoll.exceptions import NetworkError

@retry(
    max_retries=5,
    exceptions=[NetworkError],
    delay=1.0,
    exponential_backoff=True
)
async def scrape_with_backoff():
    # Attempt 1: fails → wait 1 second
    # Attempt 2: fails → wait 2 seconds
    # Attempt 3: fails → wait 4 seconds
    # Attempt 4: fails → wait 8 seconds
    # Attempt 5: fails → raise exception
    pass
```

**What is Exponential Backoff?**

Exponential backoff is a retry strategy where the wait time between attempts increases exponentially. Instead of hammering a server with requests every second, you give it progressively more time to recover:

- **Attempt 1**: Wait `delay` seconds (e.g., 1s)
- **Attempt 2**: Wait `delay * 2` seconds (e.g., 2s)
- **Attempt 3**: Wait `delay * 4` seconds (e.g., 4s)
- **Attempt 4**: Wait `delay * 8` seconds (e.g., 8s)

This is especially useful when:

- Dealing with **rate limits** (give the server time to reset)
- Handling **temporary server overload** (don't make it worse)
- Waiting for **slow-loading dynamic content**
- Avoiding **detection as a bot** (natural-looking retry patterns)

### on_retry

A callback function executed after each failed attempt, before the next retry. Must be an **async function**.

```python
from pydoll.exceptions import WaitElementTimeout

@retry(
    max_retries=3,
    exceptions=[WaitElementTimeout],
    on_retry=my_recovery_function
)
async def scrape_data():
    pass
```

The callback can be:

- **A standalone async function**
- **A class method** (receives `self` automatically)

## The on_retry Callback: Your Recovery Mechanism

The `on_retry` callback is where the real magic happens. This is your opportunity to **restore the application state** before the next retry attempt.

### Standalone Function

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

async def log_retry():
    print("Retry attempt failed, waiting before next attempt...")
    await asyncio.sleep(1)

@retry(max_retries=3, exceptions=[WaitElementTimeout], on_retry=log_retry)
async def scrape_page():
    # Your scraping logic
    pass
```

### Class Method

When using the decorator inside a class, the callback can be a class method. It will automatically receive `self` as the first argument.

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import WaitElementTimeout

class DataCollector:
    def __init__(self):
        self.retry_count = 0
    
    # IMPORTANT: Define callback BEFORE the decorated method
    async def log_retry(self):
        self.retry_count += 1
        print(f"Attempt {self.retry_count} failed, retrying...")
        await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[WaitElementTimeout],
        on_retry=log_retry  # No 'self.' prefix needed
    )
    async def fetch_data(self):
        # Your scraping logic here
        pass
```

!!! warning "Method Definition Order Matters"
    When using `on_retry` with class methods, **you must define the callback method BEFORE the decorated method** in your class definition. Python needs to know about the callback when the decorator is applied.

    **Wrong (will fail):**

    ```python
    class Scraper:
        @retry(on_retry=handle_retry)  # handle_retry doesn't exist yet!
        async def scrape(self):
            pass
        
        async def handle_retry(self):  # Defined too late
            pass
    ```

    **Correct:**

    ```python
    class Scraper:
        async def handle_retry(self):  # Defined first
            pass
        
        @retry(on_retry=handle_retry)  # Now it exists
        async def scrape(self):
            pass
    ```

## Real-World Use Cases

### 1. Page Refresh and State Recovery

**This is the most powerful use of `on_retry`**: recovering from failures by refreshing the page and restoring your application state. This example demonstrates why the retry decorator is so valuable for production scraping.

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout
from pydoll.constants import Key
import asyncio

class DataScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.current_page = 1
    
    async def recover_from_failure(self):
        """Refresh page and restore state before retry"""
        print(f"Recovering... refreshing page {self.current_page}")
        
        if self.tab:
            # Refresh the page to recover from stale elements or bad state
            await self.tab.refresh()
            await asyncio.sleep(2)  # Wait for page to load
            
            # Restore state: navigate back to the correct page
            if self.current_page > 1:
                page_input = await self.tab.find(id='page-number')
                await page_input.insert_text(str(self.current_page))
                await self.tab.keyboard.press(Key.ENTER)
                await asyncio.sleep(1)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout],
        on_retry=recover_from_failure,
        delay=1.0
    )
    async def scrape_page_data(self):
        """Scrape data from the current page"""
        if not self.browser:
            self.browser = Chrome()
            self.tab = await self.browser.start()
            await self.tab.go_to('https://example.com/data')
        
        # Navigate to specific page
        page_input = await self.tab.find(id='page-number')
        await page_input.insert_text(str(self.current_page))
        await self.tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(1)
        
        # Scrape data (might fail if elements become stale)
        items = await self.tab.find(class_name='data-item', find_all=True)
        return [await item.text for item in items]
    
    async def scrape_multiple_pages(self, start_page: int, end_page: int):
        """Scrape multiple pages with automatic retry on failures"""
        results = []
        for page_num in range(start_page, end_page + 1):
            self.current_page = page_num
            data = await self.scrape_page_data()
            results.extend(data)
        return results

# Usage
async def main():
    scraper = DataScraper()
    try:
        # Scrape pages 1-10 with automatic recovery on failures
        all_data = await scraper.scrape_multiple_pages(1, 10)
        print(f"Scraped {len(all_data)} items")
    finally:
        if scraper.browser:
            await scraper.browser.stop()
```

**What makes this powerful:**

- `recover_from_failure()` actually **restores the state** by refreshing and navigating back
- The `scrape_page_data()` method stays clean, focused only on scraping logic
- If elements become stale or disappear, the retry mechanism handles recovery automatically
- The browser persists across retries via `self.browser` and `self.tab`

### 2. Modal Dialog Recovery

Sometimes a modal or overlay appears unexpectedly and blocks your automation. Close it and retry.

```python
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class ModalAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def close_modals(self):
        """Close any blocking modals before retry"""
        print("Checking for blocking modals...")
        
        # Try to find and close common modals
        modal_close = await self.tab.find(
            class_name='modal-close',
            timeout=2,
            raise_exc=False
        )
        if modal_close:
            print("Found modal, closing it...")
            await modal_close.click()
            await asyncio.sleep(0.5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=close_modals,
        delay=0.5
    )
    async def click_button(self, button_id: str):
        button = await self.tab.find(id=button_id)
        await button.click()
```

### 3. Browser Restart and Proxy Rotation

For heavy scraping jobs, you might need to completely restart the browser and switch proxies after failures.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.decorators import retry
from pydoll.exceptions import NetworkError, PageLoadTimeout

class RobustScraper:
    def __init__(self):
        self.browser = None
        self.tab = None
        self.proxy_list = [
            'proxy1.example.com:8080',
            'proxy2.example.com:8080',
            'proxy3.example.com:8080',
        ]
        self.current_proxy_index = 0
    
    async def restart_with_new_proxy(self):
        """Restart browser with a different proxy"""
        print("Restarting browser with new proxy...")
        
        # Close current browser
        if self.browser:
            await self.browser.stop()
            await asyncio.sleep(2)
        
        # Rotate to next proxy
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        proxy = self.proxy_list[self.current_proxy_index]
        
        print(f"Using proxy: {proxy}")
        
        # Start new browser with new proxy
        options = ChromiumOptions()
        options.add_argument(f'--proxy-server={proxy}')
        
        self.browser = Chrome(options=options)
        self.tab = await self.browser.start()
    
    @retry(
        max_retries=3,
        exceptions=[NetworkError, PageLoadTimeout],
        on_retry=restart_with_new_proxy,
        delay=5.0,
        exponential_backoff=True
    )
    async def scrape_protected_site(self, url: str):
        if not self.browser:
            await self.restart_with_new_proxy()
        
        await self.tab.go_to(url)
        await asyncio.sleep(3)
        
        # Your scraping logic here
        content = await self.tab.find(id='content')
        return await content.text
```

### 4. Network Idle Detection with Retry

Wait for all network activity to complete, with retry logic if the page never stabilizes.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import TimeoutException

class NetworkAwareScraper:
    def __init__(self):
        self.tab = None
    
    async def reload_page(self):
        """Reload page if network never stabilized"""
        print("Page didn't stabilize, reloading...")
        if self.tab:
            await self.tab.refresh()
            await asyncio.sleep(2)
    
    @retry(
        max_retries=2,
        exceptions=[TimeoutException],
        on_retry=reload_page,
        delay=3.0
    )
    async def wait_for_page_ready(self):
        """Wait for all network requests to complete"""
        await self.tab.enable_network_events()
        
        # Wait for network idle (no requests for 2 seconds)
        idle_time = 0
        max_wait = 10
        
        while idle_time < max_wait:
            # Check if any requests are in flight
            # (Implementation depends on your event tracking)
            await asyncio.sleep(0.5)
            idle_time += 0.5
        
        if idle_time >= max_wait:
            raise TimeoutException("Network never stabilized")
```

### 5. CAPTCHA Detection and Recovery

Detect when a CAPTCHA appears and take appropriate action.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound

class CaptchaScraper:
    def __init__(self):
        self.tab = None
        self.captcha_count = 0
    
    async def handle_captcha(self):
        """Handle CAPTCHA by waiting or switching strategy"""
        self.captcha_count += 1
        print(f"CAPTCHA detected (count: {self.captcha_count})")
        
        if self.captcha_count > 2:
            print("Too many CAPTCHAs, might need to change strategy...")
            # Could switch to a different approach here
        
        # Wait longer between attempts
        await asyncio.sleep(30)
        
        # Refresh the page
        await self.tab.refresh()
        await asyncio.sleep(5)
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound],
        on_retry=handle_captcha,
        delay=10.0,
        exponential_backoff=True
    )
    async def scrape_protected_content(self, url: str):
        if not self.tab:
            browser = Chrome()
            self.tab = await browser.start()
        
        await self.tab.go_to(url)
        
        # Check for CAPTCHA
        captcha = await self.tab.find(
            class_name='g-recaptcha',
            timeout=2,
            raise_exc=False
        )
        
        if captcha:
            raise ElementNotFound("CAPTCHA detected")
        
        # Normal scraping logic
        content = await self.tab.find(class_name='article-content')
        return await content.text
```

## Advanced Patterns

### Combining Multiple Recovery Strategies

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, WaitElementTimeout, NetworkError

class AdvancedScraper:
    def __init__(self):
        self.tab = None
        self.attempt = 0
        self.strategies = [
            self.strategy_refresh,
            self.strategy_clear_cache,
            self.strategy_restart_browser,
        ]
    
    async def strategy_refresh(self):
        """Strategy 1: Simple refresh"""
        print("Strategy 1: Refreshing page")
        await self.tab.refresh()
        await asyncio.sleep(2)
    
    async def strategy_clear_cache(self):
        """Strategy 2: Clear cache and refresh"""
        print("Strategy 2: Clearing cache")
        await self.tab.execute_command('Network.clearBrowserCache')
        await self.tab.refresh()
        await asyncio.sleep(3)
    
    async def strategy_restart_browser(self):
        """Strategy 3: Full browser restart"""
        print("Strategy 3: Restarting browser")
        if self.tab:
            await self.tab._browser.stop()
        
        browser = Chrome()
        self.tab = await browser.start()
    
    async def adaptive_recovery(self):
        """Try different recovery strategies based on attempt number"""
        strategy_index = min(self.attempt, len(self.strategies) - 1)
        strategy = self.strategies[strategy_index]
        
        print(f"Attempt {self.attempt + 1}: Using {strategy.__name__}")
        await strategy()
        
        self.attempt += 1
    
    @retry(
        max_retries=3,
        exceptions=[ElementNotFound, WaitElementTimeout, NetworkError],
        on_retry=adaptive_recovery,
        delay=2.0
    )
    async def scrape_with_adaptive_retry(self, url: str):
        await self.tab.go_to(url)
        return await self.tab.find(id='target-content')
```

### Custom Exception for Specific Failure

```python
import asyncio
from pydoll.decorators import retry
from pydoll.exceptions import PydollException

class RateLimitError(PydollException):
    """Raised when rate limit is detected"""
    message = "API rate limit exceeded"

class APIScraper:
    async def wait_for_rate_limit_reset(self):
        """Wait longer when rate limited"""
        print("Rate limit detected, waiting 60 seconds...")
        await asyncio.sleep(60)
    
    @retry(
        max_retries=5,
        exceptions=[RateLimitError],
        on_retry=wait_for_rate_limit_reset,
        delay=10.0,
        exponential_backoff=True
    )
    async def fetch_api_data(self, endpoint: str):
        response = await self.tab.request.get(endpoint)
        
        if response.status == 429:  # Too Many Requests
            raise RateLimitError("API rate limit exceeded")
        
        return response.json()
```

## Best Practices Summary

1. **Always specify exceptions explicitly** - Never use the default `exceptions=Exception`
2. **Use exponential backoff for external services** - Give servers time to recover
3. **Keep retry counts reasonable** - Usually 3-5 attempts is enough
4. **Log retry attempts** - Use `on_retry` to log what's happening
5. **Define callbacks before decorated methods** - Order matters in class definitions
6. **Make callbacks async** - The decorator requires async callbacks
7. **Restore state in callbacks** - Use `on_retry` to navigate back to where you were
8. **Consider the cost of retries** - Each retry consumes time and resources
9. **Combine with other error handling** - Retries don't replace try/except blocks
10. **Test your retry logic** - Ensure recovery callbacks actually work

## Learn More

- **[Exception Handling](../core-concepts.md#error-handling)** - Understanding Pydoll exceptions
- **[Network Events](../network/monitoring.md)** - Track and handle network failures
- **[Browser Options](../configuration/browser-options.md)** - Configure proxies and other settings
- **[Event System](event-system.md)** - Build reactive retry strategies

The retry decorator is a powerful tool that turns fragile scraping scripts into production-ready applications. By combining it with thoughtful recovery strategies, you can build scrapers that gracefully handle the chaos of the real web.

