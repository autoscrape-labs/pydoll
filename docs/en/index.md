<p align="center">
    <img src="resources/images/logo.png" alt="Pydoll Logo" /> <br><br>
</p>

# Pydoll

Pydoll automates Chromium browsers over the Chrome DevTools Protocol, with no webdriver and no manual waits. Use it to scrape data, test web applications, and automate real browser workflows in async Python.

## Installation

<div class="termy">
```bash
$ pip install pydoll-python

---> 100%
```
</div>

Pydoll drives the Chrome or Edge already installed on your machine. You don't need to download a webdriver or keep driver versions in sync with your browser.

New to Pydoll? Follow [Getting started](getting-started.md) for a complete walkthrough.

## Quick start

Open a page, find elements by how you'd describe them to a person, and interact with humanized timing:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com/autoscrape-labs/pydoll')

        star_button = await tab.find(
            tag_name='button',
            timeout=5,
            raise_exc=False
        )
        if not star_button:
            print('Button not found.')
            return

        await star_button.click()
        await asyncio.sleep(3)

asyncio.run(main())
```

When the goal is data rather than interaction, define a model and let Pydoll extract it, typed and validated:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')
    tags: list[str] = Field(selector='.tag')


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
        for quote in quotes:
            print(f'{quote.author}: {quote.text}')

asyncio.run(main())
```

Models support CSS and XPath selectors, HTML attribute targeting, custom transforms, and nested models. Learn more in [Structured extraction](guides/structured-extraction.md).

## Why Pydoll

- **No webdriver**: Pydoll connects straight to the browser over the Chrome DevTools Protocol. Nothing to download, no version mismatches to debug.
- **Humanized interactions**: clicks follow curved mouse paths and typing has variable rhythm with occasional corrected typos, so your automation behaves like a person at the keyboard.
- **Async by design**: built on `asyncio`, so one process can drive many tabs and browsers concurrently.
- **Cloudflare Turnstile handling**: Pydoll detects the Turnstile widget and clicks it natively. No external captcha service to pay for or integrate.
- **Network control**: monitor, intercept, and modify requests as the page makes them.
- **Typed extraction**: declare a Pydantic model and get validated, IDE-friendly objects instead of raw elements.

## What's next

- [Getting started](getting-started.md): install Pydoll and run your first script.
- [Your first automation](first-automation.md): log in to a site and extract typed data.
- [Migrating from Selenium and Playwright](migrating.md): map the moves you know to Pydoll.
- [Staying undetected](stealth/index.md): the minimum setup to avoid the obvious bot signals.
- [Guides](guides/index.md): one guide per capability, from element finding to request interception.
- [API Reference](api/index.md): every public class and method.

## Top Sponsors

<div class="sponsor-grid-top">
  <a class="sponsor-card" href="https://substack.thewebscraping.club/p/pydoll-webdriver-scraping?utm_source=github&utm_medium=repo&utm_campaign=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="resources/images/banner-the-webscraping-club.png" alt="The Web Scraping Club" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">The Web Scraping Club</span>
      <span class="sponsor-desc">The #1 newsletter dedicated to web scraping. Read their full review of Pydoll.</span>
    </span>
  </a>
  <a class="sponsor-card" href="https://go.nodemaven.com/pydollaugust" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner"><img src="resources/images/nodemaven-banner.png" alt="NodeMaven" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NodeMaven</span>
      <span class="sponsor-desc">High-quality proxies for scraping and automation. ZIP targeting, 99.9% uptime, no KYC.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PYDOLL35</code> 35% off</span>
        <span class="sponsor-chip"><code>PYDOLL40</code> 40% off ISP</span>
      </span>
    </span>
  </a>
  <a class="sponsor-card" href="https://niuproxy.com/?utm_source=pydoll&utm_medium=pydoll&ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-banner sponsor-banner--niuproxy"><img src="resources/images/niuproxy-banner.jpg" alt="NiuProxy" /></span>
    <span class="sponsor-body">
      <span class="sponsor-name">NiuProxy</span>
      <span class="sponsor-desc">Rotating residential proxies: 10TB at $0.35/GB or 1TB at $0.50/GB for Pydoll users.</span>
      <span class="sponsor-chips">
        <span class="sponsor-chip"><code>PAY2</code> 10% off recharge</span>
      </span>
    </span>
  </a>
</div>

## Sponsors

Sponsors keep the project running and help fund ongoing development. Thanks to everyone who supports Pydoll.

<div class="sponsor-grid-mini">
  <a class="sponsor-card sponsor-tile" href="https://proxy-seller.com/?partner=8DES01TZ1QGWR3" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="resources/images/proxy-seller-logo-white.svg" alt="Proxy-Seller" /></span>
    <span class="sponsor-desc">Premium proxies for AI agents, scraping &amp; automation</span>
    <span class="sponsor-chip"><code>PYDOLL</code> 15% off</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.thordata.com/?ls=github&lk=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="resources/images/Thordata-logo.png" alt="Thordata" /></span>
    <span class="sponsor-desc">Residential proxy network with 190+ locations</span>
    <span class="sponsor-desc"><b>1GB free</b> via our link</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.testmuai.com/?utm_medium=sponsor&utm_source=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="resources/images/logo-lamda-test.svg" alt="TestMu AI by LambdaTest" /></span>
    <span class="sponsor-desc">AI-native testing cloud by LambdaTest</span>
  </a>
  <a class="sponsor-card sponsor-tile" href="https://www.swiftproxy.net/?ref=pydoll" target="_blank" rel="noopener nofollow sponsored">
    <span class="sponsor-tile-logo"><img src="resources/images/swiftproxy-logo.png" alt="Swiftproxy" /></span>
    <span class="sponsor-desc">Proxies for web scraping &amp; automation</span>
  </a>
  <a class="sponsor-card sponsor-tile sponsor-tile--ghost" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">
    <span class="sponsor-ghost-plus">+</span>
    <span class="sponsor-name">Your logo here</span>
    <span class="sponsor-desc">Become a sponsor</span>
  </a>
</div>

<p>
  <a class="sponsor-cta" href="https://github.com/sponsors/thalissonvs" target="_blank" rel="noopener">&#10084;&#65039; Become a sponsor</a>
</p>

## License

Pydoll is released under the [MIT License](https://github.com/autoscrape-labs/pydoll/blob/main/LICENSE), so you can use it freely in personal and commercial projects.
