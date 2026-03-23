<p align="center">
    <img src="resources/images/logo.png" alt="Pydoll Logo" /> <br><br>
</p>

<p align="center">
    <a href="https://codecov.io/gh/autoscrape-labs/pydoll">
        <img src="https://codecov.io/gh/autoscrape-labs/pydoll/graph/badge.svg?token=40I938OGM9"/> 
    </a>
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/tests.yml/badge.svg" alt="Tests">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/ruff-ci.yml/badge.svg" alt="Ruff CI">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/release.yml/badge.svg" alt="Release">
    <img src="https://github.com/thalissonvs/pydoll/actions/workflows/mypy.yml/badge.svg" alt="MyPy CI">
</p>


# Welcome to Pydoll

Hey there! Thanks for checking out Pydoll, the next generation of browser automation for Python. If you're tired of wrestling with webdrivers and looking for a smoother, more reliable way to automate browsers, you're in the right place.

## What is Pydoll?

Pydoll is revolutionizing browser automation by **eliminating the need for webdrivers** completely! Unlike other solutions that rely on external dependencies, Pydoll connects directly to browsers using their DevTools Protocol, providing a seamless and reliable automation experience with native asynchronous performance.

Whether you're scraping data, [testing web applications](https://www.lambdatest.com/web-testing), or automating repetitive tasks, Pydoll makes it surprisingly easy with its intuitive API and powerful features.

## Installation

Create and activate a [virtual environment](https://docs.python.org/3/tutorial/venv.html) first, then install Pydoll:

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

For the latest development version, you can install directly from GitHub:

```bash
$ pip install git+https://github.com/autoscrape-labs/pydoll.git
```

## Why Choose Pydoll?

- **Genuine Simplicity**: We don't want you wasting time configuring drivers or dealing with compatibility issues. With Pydoll, you install and you're ready to automate.
- **Truly Human Interactions**: Our algorithms simulate real human behavior patterns - from timing between clicks to how the mouse moves across the screen.
- **Native Async Performance**: Built from the ground up with `asyncio`, Pydoll doesn't just support asynchronous operations - it was designed for them.
- **Integrated Intelligence**: Automatic bypass of Cloudflare Turnstile and reCAPTCHA v3 captchas, without external services or complex configurations.
- **Powerful Network Monitoring**: Intercept, modify, and analyze all network traffic with ease, giving you complete control over requests.
- **Event-Driven Architecture**: React to page events, network requests, and user interactions in real-time.
- **Intuitive Element Finding**: Modern `find()` and `query()` methods that make sense and work as you'd expect.
- **Structured Extraction**: Define a [Pydantic](https://docs.pydantic.dev/) model, call `tab.extract()`, get typed and validated data back. No manual element-by-element querying.
- **Robust Type Safety**: Comprehensive type system for better IDE support and error prevention.


Ready to dive in? The following pages will guide you through installation, basic usage, and advanced features to help you get the most out of Pydoll.

Let's start automating the web, the right way! 🚀

## Quick Start Guide

### 1. Stateful Automation & Evasion

When you need to navigate, bypass challenges, or interact with dynamic UI, Pydoll's imperative API handles it with humanized timing by default.

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')

        # Find elements and interact with human-like timing
        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print("Ops! The button was not found.")
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

### 2. Structured Data Extraction

Once you reach the target page, switch to the declarative engine. Define what you want with a model, and Pydoll extracts it — typed, validated, and ready to use.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Tags')
    year: int | None = Field(selector='.year', description='Year', default=None)

async def extract_quotes():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

        for q in quotes:
            print(f'{q.author}: {q.text}')  # fully typed, IDE autocomplete works
            print(q.tags)                    # list[str], not a raw element
            print(q.model_dump_json())       # pydantic serialization built-in

asyncio.run(extract_quotes())
```

Models support CSS/XPath auto-detection, HTML attribute targeting, custom transforms, and nested models.

??? note "Nested models, transforms, and attribute extraction"
    ```python
    from datetime import datetime
    from pydoll.extractor import ExtractionModel, Field

    def parse_date(raw: str) -> datetime:
        return datetime.strptime(raw.strip(), '%B %d, %Y')

    class Author(ExtractionModel):
        name: str = Field(selector='.author-title')
        born: datetime = Field(
            selector='.author-born-date',
            transform=parse_date,
        )

    class Article(ExtractionModel):
        title: str = Field(selector='h1')
        url: str = Field(selector='.source-link', attribute='href')
        author: Author = Field(selector='.author-card', description='Nested model')

    article = await tab.extract(Article, timeout=5)
    article.author.born.year  # int — types are preserved all the way down
    ```

## Extended Example: Combining Both Approaches

A real-world scraping task typically combines both approaches: imperative automation to navigate and bypass challenges, then declarative extraction to collect structured data.

```python
import asyncio
from typing import Optional

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
from pydoll.extractor import ExtractionModel, Field


class GitHubRepo(ExtractionModel):
    name: str = Field(
        selector='[itemprop="name"] a',
        description='Repository name',
    )
    description: Optional[str] = Field(
        selector='[itemprop="description"]',
        description='Repository description',
        default=None,
    )
    language: Optional[str] = Field(
        selector='[itemprop="programmingLanguage"]',
        description='Primary programming language',
        default=None,
    )


async def main():
    options = ChromiumOptions()
    options.add_argument('--headless=new')

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        # 1. Navigate and interact (imperative)
        await tab.go_to('https://github.com/autoscrape-labs')

        # 2. Extract structured data (declarative)
        repos = await tab.extract_all(
            GitHubRepo,
            scope='article.Box-row',
            timeout=10,
        )

        for repo in repos:
            print(f'{repo.name} ({repo.language}): {repo.description}')
            print(repo.model_dump_json())

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates:

1. Defining a typed model for GitHub repository data
2. Configuring headless mode for invisible operation
3. Using `extract_all` to collect multiple repositories at once
4. Getting fully typed objects with IDE autocomplete and pydantic serialization

??? info "About Chromium Options"
    The `options.add_argument()` method allows you to pass any Chromium command-line argument to customize browser behavior. There are hundreds of available options to control everything from networking to rendering behavior.
    
    Common Chrome Options
    
    ```python
    # Performance & Behavior Options
    options.add_argument('--headless=new')         # Run Chrome in headless mode
    options.add_argument('--disable-gpu')          # Disable GPU hardware acceleration
    options.add_argument('--no-sandbox')           # Disable sandbox (use with caution)
    options.add_argument('--disable-dev-shm-usage') # Overcome limited resource issues
    
    # Appearance Options
    options.add_argument('--start-maximized')      # Start with maximized window
    options.add_argument('--window-size=1920,1080') # Set specific window size
    options.add_argument('--hide-scrollbars')      # Hide scrollbars
    
    # Network Options
    options.add_argument('--proxy-server=socks5://127.0.0.1:9050') # Use proxy
    options.add_argument('--disable-extensions')   # Disable extensions
    options.add_argument('--disable-notifications') # Disable notifications
    
    # Privacy & Security
    options.add_argument('--incognito')            # Run in incognito mode
    options.add_argument('--disable-infobars')     # Disable infobars
    ```
    
    Complete Reference Guides
    
    For a comprehensive list of all available Chrome command-line arguments, refer to these resources:
    
    - [Chromium Command Line Switches](https://peter.sh/experiments/chromium-command-line-switches/) - Complete reference list
    - [Chrome Flags](chrome://flags) - Enter this in your Chrome browser address bar to see experimental features
    - [Chromium Source Code Flags](https://source.chromium.org/chromium/chromium/src/+/main:chrome/common/chrome_switches.cc) - Direct source code reference
    
    Remember that some options may behave differently across Chrome versions, so it's a good practice to test your configuration when upgrading Chrome.

With these configurations, you can run Pydoll in various environments, including CI/CD pipelines, servers without displays, or Docker containers.

Continue reading the documentation to explore Pydoll's powerful features for handling captchas, working with multiple tabs, interacting with elements, and more.

## Minimal Dependencies

One of Pydoll's advantages is its lightweight footprint. Unlike other browser automation tools that require numerous dependencies, Pydoll is intentionally designed to be minimalist while maintaining powerful capabilities.

### Core Dependencies

Pydoll relies on just a few carefully selected packages:

```
python = "^3.10"
websockets = "^14"
aiohttp = "^3.9.5"
aiofiles = "^25.1.0"
pydantic = "^2.0"
typing_extensions = "^4.14.0"
```

That's it! This minimal dependency approach means:

- **Faster installation** - No complex dependency tree to resolve
- **Fewer conflicts** - Reduced chance of version conflicts with other packages
- **Smaller footprint** - Lower disk space usage
- **Better security** - Smaller attack surface and dependency-related vulnerabilities
- **Easier updates** - Simpler maintenance and fewer breaking changes

The small number of dependencies also contributes to Pydoll's reliability and performance, as there are fewer external factors that could impact its operation.

## Top Sponsors

<a href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
  <img src="resources/images/banner-the-webscraping-club.png" alt="The Web Scraping Club" />
</a>

<sub>Read a full review of Pydoll on <b><a href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">The Web Scraping Club</a></b>, the #1 newsletter dedicated to web scraping.</sub>

## Sponsors

The support from sponsors is essential to keep the project alive, evolving, and accessible to the entire community. Each partnership helps cover costs, drive new features, and ensure ongoing development. We are truly grateful to everyone who believes in and supports the project!

<div class="sponsors-grid">
  <a href="https://www.thordata.com/?ls=github&lk=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <img src="resources/images/Thordata-logo.png" alt="Thordata" />
  </a>
  <a href="https://www.testmuai.com/?utm_medium=sponsor&utm_source=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <img src="resources/images/logo-lamda-test.svg" alt="LambdaTest" />
  </a>
  <a href="https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc" target="_blank" rel="noopener nofollow sponsored">
    <img src="resources/images/capsolver-logo.png" alt="CapSolver" />
  </a>
</div>

<p>
  <a href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">Become a sponsor</a>
</p>

## License

Pydoll is released under the MIT License, which gives you the freedom to use, modify, and distribute the code with minimal restrictions. This permissive license makes Pydoll suitable for both personal and commercial projects.

??? info "View Full MIT License Text"
    ```
    MIT License
    
    Copyright (c) 2023 Pydoll Contributors
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    ```
