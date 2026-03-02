<p align="center">
    <img src="https://github.com/user-attachments/assets/2c380638-b04a-4b04-b1c8-2958e4237a94" alt="Pydoll Logo" /> <br>
</p>
<p align="center">Async-native, fully typed, built for evasion and performance.</p>

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
    <a href="https://pydoll.tech/">Documentation</a> &middot;
    <a href="#getting-started">Getting Started</a> &middot;
    <a href="#features">Features</a> &middot;
    <a href="#support">Support</a>
</p>

Pydoll automates Chromium-based browsers (Chrome, Edge) by connecting directly to the Chrome DevTools Protocol over WebSocket. No WebDriver binary, no `navigator.webdriver` flag, no compatibility issues.

It combines a high-level API for common tasks with low-level CDP access for fine-grained control over network, fingerprinting, and browser behavior. The entire codebase is async-native and fully type-checked with mypy.

### Sponsors

<a href="https://www.thordata.com/?ls=github&lk=pydoll">
<img alt="Thordata" src="public/images/thordata.png" />
</a>

Pydoll is proudly sponsored by **[Thordata](https://www.thordata.com/?ls=github&lk=pydoll)**: a residential proxy network built for serious web scraping and automation. With **190+ real residential and ISP locations**, fully encrypted connections, and infrastructure optimized for high-performance workflows, Thordata is an excellent choice for scaling your Pydoll automations.

**[Sign up through our link](https://www.thordata.com/?ls=github&lk=pydoll)** to support the project and get **1GB free** to get started.

---

<a href="https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc">
<img alt="CapSolver" src="public/images/capsolver.jpeg" />
</a>

Pydoll excels at behavioral evasion, but it doesn't solve captchas. That's where **[CapSolver](https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc)** comes in. An AI-powered service that handles reCAPTCHA, Cloudflare challenges, and more, seamlessly integrating with your automation workflows.

**[Register with our invite code](https://dashboard.capsolver.com/passport/register?inviteCode=WPhTbOsbXEpc)** and use code **PYDOLL** to get an extra **6% balance bonus**.

---

### Why Pydoll

- **Stealth-first**: Human-like mouse movement, realistic typing, and granular [browser preference](https://pydoll.tech/docs/features/configuration/browser-preferences/) control for fingerprint management.
- **Async and typed**: Built on `asyncio` from the ground up, 100% type-checked with `mypy`. Full IDE autocompletion and static error checking.
- **Network control**: [Intercept](https://pydoll.tech/docs/features/network/interception/) requests to block ads/trackers, [monitor](https://pydoll.tech/docs/features/network/monitoring/) traffic for API discovery, and make [authenticated HTTP requests](https://pydoll.tech/docs/features/network/http-requests/) that inherit the browser session.
- **Shadow DOM and iframes**: Full support for [shadow roots](https://pydoll.tech/docs/deep-dive/architecture/shadow-dom/) (including closed) and cross-origin iframes. Discover, query, and interact with elements inside them using the same API.
- **Ergonomic API**: `tab.find()` for most cases, `tab.query()` for complex [CSS/XPath selectors](https://pydoll.tech/docs/deep-dive/guides/selectors-guide/).

## Installation

```bash
pip install pydoll-python
```

No WebDriver binaries or external dependencies required.

## What's New

<details>
<summary><b>HAR Network Recording</b></summary>
<br>

Record network activity during a browser session and export as HAR 1.2. Replay recorded requests to reproduce exact API sequences.

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()

    async with tab.request.record() as capture:
        await tab.go_to('https://example.com')

    capture.save('flow.har')
    print(f'Captured {len(capture.entries)} requests')

    responses = await tab.request.replay('flow.har')
```

Filter by resource type:

```python
from pydoll.protocol.network.types import ResourceType

async with tab.request.record(
    resource_types=[ResourceType.FETCH, ResourceType.XHR]
) as capture:
    await tab.go_to('https://example.com')
```

[HAR Recording Docs](https://pydoll.tech/docs/features/network/network-recording/)
</details>

<details>
<summary><b>Page Bundles</b></summary>
<br>

Save the current page and all its assets (CSS, JS, images, fonts) as a `.zip` bundle for offline viewing. Optionally inline everything into a single HTML file.

```python
await tab.save_bundle('page.zip')
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

[Screenshots, PDFs & Bundles Docs](https://pydoll.tech/docs/features/automation/screenshots-and-pdfs/)
</details>

<details>
<summary><b>Shadow DOM Support</b></summary>
<br>

Full Shadow DOM support, including closed shadow roots. Because Pydoll operates at the CDP level (below JavaScript), the `closed` mode restriction doesn't apply.

```python
shadow = await element.get_shadow_root()
button = await shadow.query('.internal-btn')
await button.click()

# Discover all shadow roots on the page
shadow_roots = await tab.find_shadow_roots()
for sr in shadow_roots:
    checkbox = await sr.query('input[type="checkbox"]', raise_exc=False)
    if checkbox:
        await checkbox.click()
```

Highlights:
- Closed shadow roots work without workarounds
- `find_shadow_roots()` discovers every shadow root on the page
- `timeout` parameter for polling until shadow roots appear
- `deep=True` traverses cross-origin iframes (OOPIFs)
- Standard `find()`, `query()`, `click()` API inside shadow roots

```python
# Cloudflare Turnstile inside a cross-origin iframe
shadow_roots = await tab.find_shadow_roots(deep=True, timeout=10)
for sr in shadow_roots:
    checkbox = await sr.query('input[type="checkbox"]', raise_exc=False)
    if checkbox:
        await checkbox.click()
```

[Shadow DOM Docs](https://pydoll.tech/docs/deep-dive/architecture/shadow-dom/)
</details>

<details>
<summary><b>Humanized Mouse Movement</b></summary>
<br>

Mouse operations produce human-like cursor movement by default:

- **Bezier curve paths** with asymmetric control points
- **Fitts's Law timing**: duration scales with distance
- **Minimum-jerk velocity**: bell-shaped speed profile
- **Physiological tremor**: Gaussian noise scaled with velocity
- **Overshoot correction**: ~70% chance on fast movements, then corrects back

```python
await tab.mouse.move(500, 300)
await tab.mouse.click(500, 300)
await tab.mouse.drag(100, 200, 500, 400)

button = await tab.find(id='submit')
await button.click()

# Opt out when speed matters
await tab.mouse.click(500, 300, humanize=False)
```

[Mouse Control Docs](https://pydoll.tech/docs/features/automation/mouse-control/)
</details>

## Getting Started

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
        await tab.keyboard.press(Key.ENTER)

        first_result = await tab.find(
            tag_name='h3',
            text='autoscrape-labs/pydoll',
            timeout=10,
        )
        await first_result.click()

        await tab.find(id='repository-container-header', timeout=10)
        print(f"Page loaded: {await tab.title}")

asyncio.run(google_search('pydoll site:github.com'))
```

## Features

<details>
<summary><b>Hybrid Automation (UI + API)</b></summary>
<br>

Use UI automation to pass login flows (CAPTCHAs, JS challenges), then switch to `tab.request` for fast API calls that inherit the full browser session: cookies, headers, and all.

```python
# Log in via UI
await tab.go_to('https://my-site.com/login')
await (await tab.find(id='username')).type_text('user')
await (await tab.find(id='password')).type_text('pass123')
await (await tab.find(id='login-btn')).click()

# Make authenticated API calls using the browser session
response = await tab.request.get('https://my-site.com/api/user/profile')
user_data = response.json()
```
[Hybrid Automation Docs](https://pydoll.tech/docs/features/network/http-requests/)
</details>

<details>
<summary><b>Network Interception and Monitoring</b></summary>
<br>

Monitor traffic for API discovery or intercept requests to block ads, trackers, and unnecessary resources.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent, RequestPausedEvent
from pydoll.protocol.network.types import ErrorReason

async def block_images():
    async with Chrome() as browser:
        tab = await browser.start()

        async def block_resource(event: RequestPausedEvent):
            request_id = event['params']['requestId']
            resource_type = event['params']['resourceType']

            if resource_type in ['Image', 'Stylesheet']:
                await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
            else:
                await tab.continue_request(request_id)

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, block_resource)

        await tab.go_to('https://example.com')
        await asyncio.sleep(3)
        await tab.disable_fetch_events()

asyncio.run(block_images())
```
[Network Monitoring](https://pydoll.tech/docs/features/network/monitoring/) | [Request Interception](https://pydoll.tech/docs/features/network/interception/)
</details>

<details>
<summary><b>Browser Fingerprint Control</b></summary>
<br>

Granular control over [browser preferences](https://pydoll.tech/docs/features/configuration/browser-preferences/): hundreds of internal Chrome settings for building consistent fingerprints.

```python
options = ChromiumOptions()

options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,
            'geolocation': 2,
        },
        'password_manager_enabled': False
    },
    'intl': {
        'accept_languages': 'en-US,en',
    },
    'browser': {
        'check_default_browser': False,
    }
}
```
[Browser Preferences Guide](https://pydoll.tech/docs/features/configuration/browser-preferences/)
</details>

<details>
<summary><b>Concurrency, Contexts and Remote Connections</b></summary>
<br>

Manage [multiple tabs](https://pydoll.tech/docs/features/browser-management/tabs/) and [browser contexts](https://pydoll.tech/docs/features/browser-management/contexts/) (isolated sessions) concurrently. Connect to browsers running in Docker or remote servers.

```python
async def scrape_page(url, tab):
    await tab.go_to(url)
    return await tab.title

async def concurrent_scraping():
    async with Chrome() as browser:
        tab_google = await browser.start()
        tab_ddg = await browser.new_tab()

        results = await asyncio.gather(
            scrape_page('https://google.com/', tab_google),
            scrape_page('https://duckduckgo.com/', tab_ddg)
        )
        print(results)
```
[Multi-Tab Management](https://pydoll.tech/docs/features/browser-management/tabs/) | [Remote Connections](https://pydoll.tech/docs/features/advanced/remote-connections/)
</details>

<details>
<summary><b>Retry Decorator</b></summary>
<br>

The `@retry` decorator supports custom recovery logic between attempts (e.g., refreshing the page, rotating proxies) and exponential backoff.

```python
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, NetworkError

@retry(
    max_retries=3,
    exceptions=[ElementNotFound, NetworkError],
    on_retry=my_recovery_function,
    exponential_backoff=True
)
async def scrape_product(self, url: str):
    # scraping logic
    ...
```
[Retry Decorator Docs](https://pydoll.tech/docs/features/advanced/decorators/)
</details>

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

If you find Pydoll useful, consider [sponsoring the project on GitHub](https://github.com/sponsors/thalissonvs).

## License

[MIT License](LICENSE)
