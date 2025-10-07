<p align="center">
    <img src="https://github.com/user-attachments/assets/219f2dbc-37ed-4aea-a289-ba39cdbb335d" alt="Pydoll Logo" /> <br>
</p>
<h1 align="center">Pydoll: scraping, the easier way</h1>

<p align="center">
    <a href="https://github.com/autoscrape-labs/pydoll/stargazers"><img src="https://img.shields.io/github/stars/autoscrape-labs/pydoll?style=social"></a>
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll" >
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/>
    </a>
    <img src="https://github.com/autoscrape-labs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/autoscrape-labs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/autoscrape-labs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
    <img src="https://img.shields.io/badge/python-%3E%3D3.10-blue" alt="Python >= 3.10">
    <a href="https://deepwiki.com/autoscrape-labs/pydoll"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>


<p align="center">
  📖 <a href="https://pydoll.tech/">Documentation</a> •
  🚀 <a href="#-getting-started">Getting Started</a> •
  ⚡ <a href="#-advanced-features">Advanced Features</a> •
  🤝 <a href="#-contributing">Contributing</a> •
  💖 <a href="#-support-my-work">Support My Work</a>
</p>

Imagine the following scenario: you need to automate tasks in your browser. Maybe it's testing a web application, collecting data from a site, or even automating repetitive processes. Normally this involves using external drivers, complex configurations, and many compatibility issues.

**Pydoll was born to solve these problems.**

Built from scratch with a different philosophy, Pydoll connects directly to the Chrome DevTools Protocol (CDP), eliminating the need for external drivers. This clean implementation along with realistic ways of clicking, navigating and interacting with elements makes it practically indistinguishable from a real user.

We believe that powerful automation shouldn't require you to become an expert in configuration or constantly fight with bot protection systems. With Pydoll, you can focus on what really matters: your automation logic, not the underlying complexity or protection systems.

<div>
  <h4>Be a good human. Give it a star ⭐</h4> 
    No stars, no bugs fixed. Just kidding (maybe)
</div>

## 🌟 What makes Pydoll special?

- **Zero Webdrivers**: Say goodbye to webdriver compatibility issues
- **Human-like Interaction Engine**: Capable of passing behavioral CAPTCHAs like reCAPTCHA v3 or Turnstile, depending on IP reputation and interaction patterns
- **Asynchronous Performance**: For high-speed automation and multiple simultaneous tasks
- **Humanized Interactions**: Mimic real user behavior
- **Simplicity**: With Pydoll, you install and you're ready to automate.

## 📦 Installation

```bash
pip install pydoll-python
```

And that's it! Just install and start automating.


## ⭐ Sponsors
The support from sponsors is essential to keep the project alive, evolving, and accessible to the entire community. Each partnership helps cover costs, drive new features, and ensure ongoing development.
We are truly grateful to everyone who believes in and supports the project!

<br>
<p style="font-size:21px; color:black;">Browser testing via 
    <a href="https://www.lambdatest.com/?utm_source=pydoll&utm_medium=sponsor" target="_blank">
        <img src="https://www.lambdatest.com/blue-logo.png" style="vertical-align: middle;" width="250" height="45" />
    </a>
</p>
<br>

## 🚀 Getting Started

### Your first automation

Let's start with a real example: an automation that performs a Google search and clicks on the first result. With this example, we can see how the library works and how you can start automating your tasks.

```python
import asyncio

from pydoll.browser import Chrome
from pydoll.constants import Key

async def google_search(query: str):
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://www.google.com')
        search_box = await tab.find(tag_name='textarea', name='q')
        await search_box.insert_text(query)
        await search_box.press_keyboard_key(Key.ENTER)
        await (await tab.find(
            tag_name='h3',
            text='autoscrape-labs/pydoll',
            timeout=10,
        )).click()
        await tab.find(id='repository-container-header', timeout=10)

asyncio.run(google_search('pydoll python'))
```

Without configurations, just a simple script, we can do a complete Google search!
Okay, now let's see how we can extract data from a page, using the same previous example.
Let's consider in the code below that we're already on the Pydoll page. We want to extract the following information:

- Project description
- Number of stars
- Number of forks
- Number of issues
- Number of pull requests

Let's get started! To get the project description, we'll use xpath queries. You can check the documentation on how to build your own queries.

```python
description = await (await tab.query(
    '//h2[contains(text(), "About")]/following-sibling::p',
    timeout=10,
)).text
```

And that's it! Let's understand what this query does:

1. `//h2[contains(text(), "About")]` - Selects the first `<h2>` that contains "About"
2. `/following-sibling::p` - Selects the first `<p>` that comes after the `<h2>`

Now let's get the rest of the data:

```python
number_of_stars = await (await tab.find(
    id='repo-stars-counter-star'
)).text

number_of_forks = await (await tab.find(
    id='repo-network-counter'
)).text
number_of_issues = await (await tab.find(
    id='issues-repo-tab-count',
)).text
number_of_pull_requests = await (await tab.find(
    id='pull-requests-repo-tab-count',
)).text

data = {
    'description': description,
    'number_of_stars': number_of_stars,
    'number_of_forks': number_of_forks,
    'number_of_issues': number_of_issues,
    'number_of_pull_requests': number_of_pull_requests,
}
print(data)

```

We managed to extract all the necessary data!

### Custom Configurations

Sometimes we need more control over the browser. Pydoll offers a flexible way to do this. Let's see the example below:


```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions as Options

async def custom_automation():
    # Configure browser options
    options = Options()
    options.add_argument('--proxy-server=username:password@ip:port')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = '/path/to/your/browser'
    options.start_timeout = 20

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        # Your automation code here
        await tab.go_to('https://example.com')
        # The browser is now using your custom settings

asyncio.run(custom_automation())
```

In this example, we're configuring the browser to use a proxy and a 1920x1080 window, in addition to a custom path for the Chrome binary, in case your installation location is different from the common defaults.


## ⚡ Advanced Features

Pydoll offers a series of advanced features to please even the most
demanding users.


### Advanced Element Search

We have several ways to find elements on the page. No matter how you prefer, we have a way that makes sense for you:

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

The `find` method is more user-friendly. We can search by common attributes like id, tag_name, class_name, etc., up to custom attributes (e.g. `data-testid`).

If that's not enough, we can use the `query` method to search for elements using CSS selectors, XPath queries, etc. Pydoll automatically takes care of identifying what type of query we're using.


### Browser-context HTTP requests - game changer for hybrid automation!
Ever wished you could make HTTP requests that automatically inherit all your browser's session state? **Now you can!**<br>
The `tab.request` property gives you a beautiful `requests`-like interface that executes HTTP calls directly in the browser's JavaScript context. This means every request automatically gets cookies, authentication headers, CORS policies, and session state, just as if the browser made the request itself.

**Perfect for Hybrid Automation:**
```python
# Navigate to a site and login normally with PyDoll
await tab.go_to('https://example.com/login')
await (await tab.find(id='username')).type_text('user@example.com')
await (await tab.find(id='password')).type_text('password')
await (await tab.find(id='login-btn')).click()

# Now make API calls that inherit the logged-in session!
response = await tab.request.get('https://example.com/api/user/profile')
user_data = response.json()

# POST data while staying authenticated
response = await tab.request.post(
    'https://example.com/api/settings', 
    json={'theme': 'dark', 'notifications': True}
)

# Access response content in different formats
raw_data = response.content
text_data = response.text
json_data = response.json()

# Check cookies that were set
for cookie in response.cookies:
    print(f"Cookie: {cookie['name']} = {cookie['value']}")

# Add custom headers to your requests
headers = [
    {'name': 'X-Custom-Header', 'value': 'my-value'},
    {'name': 'X-API-Version', 'value': '2.0'}
]

await tab.request.get('https://api.example.com/data', headers=headers)

```

**Why this is great:**
- **No more session juggling** - Requests inherit browser cookies automatically
- **CORS just works** - Requests respect browser security policies  
- **Perfect for modern SPAs** - Seamlessly mix UI automation with API calls
- **Authentication made easy** - Login once via UI, then hammer APIs
- **Hybrid workflows** - Use the best tool for each step (UI or API)

This opens up incredible possibilities for automation scenarios where you need both browser interaction AND API efficiency!

### New expect_download() context manager — robust file downloads made easy!
Tired of fighting with flaky download flows, missing files, or racy event listeners? Meet `tab.expect_download()`, a delightful, reliable way to handle file downloads.

- Automatically sets the browser’s download behavior
- Works with your own directory or a temporary folder (auto-cleaned!)
- Waits for completion with a timeout (so your tests don’t hang)
- Gives you a handy handle to read bytes/base64 or check `file_path`

Tiny example that just works:

```python
import asyncio
from pathlib import Path
from pydoll.browser import Chrome

async def download_report():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/reports')

        target_dir = Path('/tmp/my-downloads')
        async with tab.expect_download(keep_file_at=target_dir, timeout=10) as download:
            # Trigger the download in the page (button/link/etc.)
            await (await tab.find(text='Download latest report')).click()
            # Wait until finished and read the content
            data = await download.read_bytes()
            print(f"Downloaded {len(data)} bytes to: {download.file_path}")

asyncio.run(download_report())
```

Want zero-hassle cleanup? Omit `keep_file_at` and we’ll create a temp folder and remove it automatically after the context exits. Perfect for tests.

### Total browser control with custom preferences! (thanks to [@LucasAlvws](https://github.com/LucasAlvws))
Want to completely customize how Chrome behaves? **Now you can control EVERYTHING!**<br>
The new `browser_preferences` system gives you access to hundreds of internal Chrome settings that were previously impossible to change programmatically. We're talking about deep browser customization that goes way beyond command-line flags!

**The possibilities are endless:**
```python
options = ChromiumOptions()

# Create the perfect automation environment
options.browser_preferences = {
    'download': {
        'default_directory': '/tmp/downloads',
        'prompt_for_download': False,
        'directory_upgrade': True,
        'extensions_to_open': ''  # Don't auto-open any downloads
    },
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,        # Block all notifications
            'geolocation': 2,         # Block location requests
            'media_stream_camera': 2, # Block camera access
            'media_stream_mic': 2,    # Block microphone access
            'popups': 1               # Allow popups (useful for automation)
        },
        'password_manager_enabled': False,  # Disable password prompts
        'exit_type': 'Normal'              # Always exit cleanly
    },
    'intl': {
        'accept_languages': 'en-US,en',
        'charset_default': 'UTF-8'
    },
    'browser': {
        'check_default_browser': False,    # Don't ask about default browser
        'show_update_promotion_infobar': False
    }
}

# Or use the convenient helper methods
options.set_default_download_directory('/tmp/downloads')
options.set_accept_languages('en-US,en,pt-BR')  
options.prompt_for_download = False
```

**Real-world power examples:**
- **Silent downloads** - No prompts, no dialogs, just automated downloads
- **Block ALL distractions** - Notifications, popups, camera requests, you name it
- **Perfect for CI/CD** - Disable update checks, default browser prompts, crash reporting
- **Multi-region testing** - Change languages, timezones, and locale settings instantly
- **Security hardening** - Lock down permissions and disable unnecessary features
- **Advanced fingerprinting control** - Modify browser install dates, engagement history, and behavioral patterns

**Fingerprint customization for stealth automation:**
```python
import time

# Simulate a browser that's been around for months
fake_engagement_time = int(time.time()) - (7 * 24 * 60 * 60)  # 7 days ago

options.browser_preferences = {
    'settings': {
        'touchpad': {
            'natural_scroll': True,
        }
    },
    'profile': {
        'last_engagement_time': fake_engagement_time,
        'exit_type': 'Normal',
        'exited_cleanly': True
    },
    'newtab_page_location_override': 'https://www.google.com',
    'session': {
        'restore_on_startup': 1,  # Restore last session
        'startup_urls': ['https://www.google.com']
    }
}
```

This level of control was previously only available to Chrome extension developers - now it's in your automation toolkit!

Check the [documentation](https://pydoll.tech/docs/features/#custom-browser-preferences/) for more details.

### Concurrent Automation

One of the great advantages of Pydoll is the ability to process multiple tasks simultaneously thanks to its asynchronous implementation. We can automate multiple tabs
at the same time! Let's see an example:

```python
import asyncio
from pydoll.browser import Chrome

async def scrape_page(url, tab):
    await tab.go_to(url)
    title = await tab.execute_script('return document.title')
    links = await tab.find(tag_name='a', find_all=True)
    return {
        'url': url,
        'title': title,
        'link_count': len(links)
    }

async def concurrent_scraping():
    browser = Chrome()
    tab_google = await browser.start()
    tab_duckduckgo = await browser.new_tab()
    tasks = [
        scrape_page('https://google.com/', tab_google),
        scrape_page('https://duckduckgo.com/', tab_duckduckgo)
    ]
    results = await asyncio.gather(*tasks)
    print(results)
    await browser.stop()

asyncio.run(concurrent_scraping())
```

We managed to extract data from two pages at the same time!

And there's much, much more! Event system for reactive automations, request interception and modification, and so on. Take a look at the documentation, you won't
regret it!


## 🔧 Quick Troubleshooting

**Browser not found?**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.binary_location = '/path/to/your/chrome'
browser = Chrome(options=options)
```

**Browser starts after a FailedToStartBrowser error?**
```python
from pydoll.browser import Chrome
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()
options.start_timeout = 20  # default is 10 seconds

browser = Chrome(options=options)
```

**Need a proxy?**
```python
options.add_argument('--proxy-server=your-proxy:port')
```

**Running in Docker?**
```python
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

## 📚 Documentation

For complete documentation, detailed examples and deep dives into all Pydoll functionalities, visit our [official documentation](https://pydoll.tech/).

The documentation includes:
- **Getting Started Guide** - Step-by-step tutorials
- **API Reference** - Complete method documentation
- **Advanced Techniques** - Network interception, event handling, performance optimization

>The chinese version of this README is [here](README_zh.md).

## 🤝 Contributing

We would love your help to make Pydoll even better! Check out our [contribution guidelines](CONTRIBUTING.md) to get started. Whether it's fixing bugs, adding features or improving documentation - all contributions are welcome!

Please make sure to:
- Write tests for new features or bug fixes
- Follow code style and conventions
- Use conventional commits for pull requests
- Run lint checks and tests before submitting

## 💖 Support My Work

If you find Pydoll useful, consider [supporting me on GitHub](https://github.com/sponsors/thalissonvs).  
You'll get access to exclusive benefits like priority support, custom features and much more!

Can't sponsor right now? No problem, you can still help a lot by:
- Starring the repository
- Sharing on social media
- Writing posts or tutorials
- Giving feedback or reporting issues

Every bit of support makes a difference/

## 💬 Spread the word

If Pydoll saved you time, mental health, or a keyboard from being smashed, give it a ⭐, share it, or tell your weird dev friends.

## 📄 License

Pydoll is licensed under the [MIT License](LICENSE).

<p align="center">
  <b>Pydoll</b> — Making browser automation magical!
</p>
