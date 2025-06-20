<p align="center">
    <img src="https://github.com/user-attachments/assets/219f2dbc-37ed-4aea-a289-ba39cdbb335d" alt="Pydoll Logo" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll" >
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/>
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
    <a href="https://deepwiki.com/autoscrape-labs/pydoll"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<p align="center">
  <a href="https://autoscrape-labs.github.io/pydoll/">Documentation</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#advanced-features">Advanced Features</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#support-my-work">Support</a> •
  <a href="#license">License</a>
</p>


## Key Features

- **Zero Webdrivers!** Say goodbye to webdriver compatibility nightmares  
- **Native Captcha Bypass!** Smoothly handles Cloudflare Turnstile and reCAPTCHA v3*  
- **Async Performance** for lightning-fast automation  
- **Human-like Interactions** that mimic real user behavior  
- **Powerful Event System** for reactive automations  
- **Multi-browser Support** including Chrome and Edge

## Why Pydoll Exists

Picture this: you need to automate browser tasks. Maybe it's testing your web application, scraping data from websites, or automating repetitive processes. Traditionally, this meant dealing with external drivers, complex configurations, and a host of compatibility issues that seemed to appear out of nowhere.

But there's another challenge that's even more frustrating: **modern web protection systems**. Cloudflare Turnstile captchas, reCAPTCHA v3, and sophisticated bot detection algorithms that can instantly identify and block traditional automation tools. Your perfectly written automation script fails not because of bugs, but because websites can tell it's not human.

**Pydoll was born to change that.**

Built from the ground up with a different philosophy, Pydoll connects directly to the Chrome DevTools Protocol (CDP), eliminating the need for external drivers entirely. More importantly, it incorporates advanced human behavior simulation and intelligent captcha bypass capabilities that make your automations virtually indistinguishable from real human interactions.

We believe that powerful automation shouldn't require you to become a configuration expert or constantly battle with anti-bot systems. With Pydoll, you focus on what matters: your automation logic, not the underlying complexity or protection bypassing.

## What Makes Pydoll Special

- **Intelligent Captcha Bypass**: Built-in automatic solving for Cloudflare Turnstile and reCAPTCHA v3 captchas without external services, API keys, or complex configurations. Your automations continue seamlessly even when encountering protection systems.

- **Truly Human Interactions**: Advanced algorithms simulate authentic human behavior patterns - from realistic timing between actions to natural mouse movements, scroll patterns, and typing rhythms that fool even sophisticated bot detection systems.

- **Genuine Simplicity**: We don't want you wasting time configuring drivers or dealing with compatibility issues. With Pydoll, you install and you're ready to automate, even on protected sites.

- **Native Async Performance**: Built from the ground up with `asyncio`, Pydoll doesn't just support asynchronous operations - it was designed for them, enabling concurrent processing of multiple protected sites.

- **Powerful Network Monitoring**: Intercept, modify, and analyze all network traffic with ease, giving you complete control over requests and responses - perfect for bypassing additional protection layers.

- **Event-Driven Architecture**: React to page events, network requests, and user interactions in real-time, enabling sophisticated automation flows that adapt to dynamic protection systems.

- **Intuitive Element Finding**: Modern `find()` and `query()` methods that make sense and work as you'd expect, even with dynamically loaded content from protection systems.

- **Robust Type Safety**: Comprehensive type system for better IDE support and error prevention in complex automation scenarios.

## Installation

```bash
pip install pydoll-python
```

That's it. No drivers to download, no complex configurations. Just install and start automating.

## Getting Started

### Your First Automation

Let's start with something simple. The code below opens a browser, navigates to a website, and interacts with elements:

```python
import asyncio
from pydoll.browser import Chrome

async def my_first_automation():
    # Create a browser instance
    async with Chrome() as browser:
        # Start the browser and get a tab
        tab = await browser.start()
        
        # Navigate to a website
        await tab.go_to('https://example.com')
        
        # Find elements intuitively
        button = await tab.find(tag_name='button', class_name='submit')
        await button.click()
        
        # Or use CSS selectors/XPath directly
        link = await tab.query('a[href*="contact"]')
        await link.click()

# Run the automation
asyncio.run(my_first_automation())
```

### Custom Configuration

Sometimes you need more control. Pydoll offers flexible configuration options:

```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

async def custom_automation():
    # Configure browser options
    options = ChromiumOptions()
    options.add_argument('--proxy-server=username:password@ip:port')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-web-security')
    options.binary_location = '/path/to/your/browser'

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        
        # Your automation code here
        await tab.go_to('https://example.com')
        
        # The browser is now using your custom settings

asyncio.run(custom_automation())
```

## Advanced Features

### Intelligent Captcha Bypass

One of Pydoll's most revolutionary features is its ability to automatically handle modern captcha systems that typically block automation tools. This isn't just about solving captchas - it's about making your automations completely transparent to protection systems.

**Supported Captcha Types:**
- **Cloudflare Turnstile** - The modern replacement for reCAPTCHA
- **reCAPTCHA v3** - Google's invisible captcha system
- **Custom implementations** - Extensible framework for new captcha types

```python
import asyncio
from pydoll.browser import Chrome

async def advanced_captcha_bypass():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Method 1: Context manager (waits for captcha completion)
        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://site-with-cloudflare.com')
            print("Cloudflare Turnstile automatically solved!")
            
            # Continue with your automation - captcha is handled
            await tab.find(id='username').type_text('user@example.com')
            await tab.find(id='password').type_text('password123')
            await tab.find(tag_name='button', text='Login').click()
        
        # Method 2: Background processing (non-blocking)
        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://another-protected-site.com')
        # Captcha solved automatically in background while code continues
        
        # Method 3: Custom captcha selector for specific implementations
        await tab.enable_auto_solve_cloudflare_captcha(
            custom_selector=(By.CLASS_NAME, 'custom-captcha-widget'),
            time_before_click=3,  # Wait 3 seconds before solving
            time_to_wait_captcha=10  # Timeout after 10 seconds
        )
        
        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(advanced_captcha_bypass())
```

### Advanced Element Finding

Pydoll offers multiple intuitive ways to find elements. No matter how you prefer to work, we have an approach that makes sense for you:

```python
import asyncio
from pydoll.browser import Chrome

async def element_finding_examples():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Find by attributes (most intuitive)
        submit_btn = await tab.find(
            tag_name='button',
            class_name='btn-primary',
            text='Submit'
        )
        
        # Find by ID
        username_field = await tab.find(id='username')
        
        # Find multiple elements
        all_links = await tab.find(tag_name='a', find_all=True)
        
        # CSS selectors and XPath
        nav_menu = await tab.query('nav.main-menu')
        specific_item = await tab.query('//div[@data-testid="item-123"]')
        
        # With timeout and error handling
        delayed_element = await tab.find(
            class_name='dynamic-content',
            timeout=10,
            raise_exc=False  # Returns None if not found
        )
        
        # Advanced: Custom attributes
        custom_element = await tab.find(
            data_testid='submit-button',
            aria_label='Submit form'
        )

asyncio.run(element_finding_examples())
```

### Concurrent Automation

One of the great advantages of Pydoll's asynchronous design is the ability to process multiple tasks simultaneously:

```python
import asyncio
from pydoll.browser import Chrome

async def scrape_page(url):
    """Extract data from a single page"""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to(url)
        
        title = await tab.execute_script('return document.title')
        links = await tab.find(tag_name='a', find_all=True)
        
        return {
            'url': url,
            'title': title,
            'link_count': len(links)
        }

async def concurrent_scraping():
    urls = [
        'https://example1.com',
        'https://example2.com',
        'https://example3.com'
    ]
    
    # Process all URLs simultaneously
    tasks = [scrape_page(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(f"{result['url']}: {result['title']} ({result['link_count']} links)")

asyncio.run(concurrent_scraping())
```

### Event-Driven Automation

React to page events and user interactions in real-time. This enables more sophisticated and responsive automations:

```python
import asyncio
from pydoll.browser import Chrome
from pydoll.protocol.page.events import PageEvent

async def event_driven_automation():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Enable page events
        await tab.enable_page_events()
        
        # React to page load
        async def on_page_load(event):
            print("Page loaded! Starting automation...")
            # Perform actions after page loads
            search_box = await tab.find(id='search-box')
            await search_box.type_text('automation')
        
        # React to navigation
        async def on_navigation(event):
            url = event['params']['url']
            print(f"Navigated to: {url}")
        
        await tab.on(PageEvent.LOAD_EVENT_FIRED, on_page_load)
        await tab.on(PageEvent.FRAME_NAVIGATED, on_navigation)
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)  # Let events process

asyncio.run(event_driven_automation())
```

### Working with iFrames

Pydoll provides seamless iframe interaction through the `get_frame()` method. This is especially useful for dealing with embedded content:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def iframe_interaction():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')
        
        # Find the iframe element
        iframe_element = await tab.query('.hcaptcha-iframe', timeout=10)
        
        # Get a Tab instance for the iframe content
        frame = await tab.get_frame(iframe_element)
        
        # Now interact with elements inside the iframe
        submit_button = await frame.find(tag_name='button', class_name='submit')
        await submit_button.click()
        
        # You can use all Tab methods on the frame
        form_input = await frame.find(id='captcha-input')
        await form_input.type_text('verification-code')
        
        # Find elements by various methods
        links = await frame.find(tag_name='a', find_all=True)
        specific_element = await frame.query('#specific-id')

asyncio.run(iframe_interaction())
```

## Documentation

For comprehensive documentation, detailed examples, and deep dives into Pydoll's features, visit our [official documentation site](https://autoscrape-labs.github.io/pydoll/).

The documentation includes:
- **Getting Started Guide** - Step-by-step tutorials
- **API Reference** - Complete method documentation  
- **Advanced Techniques** - Network interception, event handling, performance optimization
- **Troubleshooting** - Common issues and solutions
- **Best Practices** - Patterns for reliable automation

## Contributing

We'd love your help making Pydoll even better! Check out our [contribution guidelines](CONTRIBUTING.md) to get started. Whether it's fixing bugs, adding features, or improving documentation - all contributions are welcome!

Please make sure to:
- Write tests for new features or bug fixes
- Follow coding style and conventions
- Use conventional commits for pull requests
- Run lint and test checks before submitting

## Support My Work

If you find my projects helpful, consider [sponsoring me on GitHub](https://github.com/sponsors/thalissonvs).  
You'll get access to exclusive perks like prioritized support, custom features, and more!

Can't sponsor right now? No problem — you can still help a lot by:
- Starring the repo
- Sharing it on social media
- Writing blog posts or tutorials
- Giving feedback or reporting issues

Every bit of support makes a difference — thank you!

## License

Pydoll is licensed under the [MIT License](LICENSE).

<p align="center">
  <b>Pydoll</b> — Making browser automation magical!
</p>
