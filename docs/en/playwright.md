# Bring your Playwright script

Your Playwright script works until a site starts blocking it. Pydoll runs the same script over raw CDP, with no driver process and no patched browser, so there is nothing for a detector to find in the transport and nothing for you to rewrite. This page takes an existing Playwright script and gets it running on Pydoll in five minutes, then shows where Pydoll goes further than Playwright when you need it.

**You will learn**

- [How to switch a script with one import](#swap-the-import)
- [What changed under your script](#what-changed-under-your-script)
- [How to use Pydoll features from a Playwright script](#reach-pydoll-from-a-playwright-object)
- [What this does and does not change about detection](#what-this-does-not-change)

## Swap the import {#swap-the-import}

Replace `playwright.sync_api` with `pydoll.playwright.sync_api`, or `playwright.async_api` with `pydoll.playwright.async_api`. Everything else stays. You don't install the `playwright` package or its bundled browsers; Pydoll drives the Chrome or Edge already on your machine.

=== "Sync"

    ```python
    from pydoll.playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://quotes.toscrape.com/login')

        page.get_by_label('Username').fill('john')
        page.locator('#password').fill('SecretPass123')
        page.get_by_role('button', name='Login').click()
        page.wait_for_url('**/')

        print(page.get_by_role('link', name='Logout').is_visible())
        browser.close()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll.playwright.async_api import async_playwright


    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://quotes.toscrape.com/login')

            await page.get_by_label('Username').fill('john')
            await page.locator('#password').fill('SecretPass123')
            await page.get_by_role('button', name='Login').click()
            await page.wait_for_url('**/')

            print(await page.get_by_role('link', name='Logout').is_visible())
            await browser.close()

    asyncio.run(main())
    ```

Run it the way you always did. Locators stay lazy and strict, `get_by_role` resolves the same elements, actions auto-wait for the element to be attached, visible, stable and enabled, and a failed wait raises the same `TimeoutError` with the same call log.

`chromium.launch()` takes the options you already pass: `headless`, `args`, `executable_path`, `proxy`, `downloads_path`. `launch_persistent_context(user_data_dir)` and `connect_over_cdp(url)` work too. `firefox` and `webkit` raise an error, because Pydoll drives Chromium-based browsers only.

!!! note "Drop-in for the automation surface"
    The layer covers what a script uses: `Playwright`, `Browser`, `BrowserContext`, `Page`, `Frame`, `Locator`, `ElementHandle`, `Keyboard`, `Mouse`, routes, dialogs and downloads. It does not cover the test runner: `expect()` assertions, fixtures, the pytest plugin, tracing and video are not implemented. [Playwright API](guides/playwright-api.md) lists every class with what is full, partial or missing.

## What changed under your script {#what-changed-under-your-script}

Playwright talks to the browser through a driver process written in Node. Every call crosses into that process, which then speaks CDP to Chrome. Stealth forks such as Patchright patch that driver after the fact, removing the calls that give automation away.

Pydoll has no driver. Your `page.goto` becomes CDP commands sent straight from Python, over the same connection Pydoll's own API uses. That removes the transport tells at the source instead of patching them:

- The `Runtime` domain, whose activation is the best-known automation tell, is never enabled for your script. Selectors and actionability checks run in an isolated world of each frame, evaluated once, and your `page.evaluate` code runs in the main world without going through `eval`.
- No `--enable-automation`, no `navigator.webdriver`, no console hooks, no init scripts injected on every navigation.
- Evaluations carry no synthetic user gesture, popups open only from a real user action, and a `user_agent` override ships coherent Client Hints, as in a browser someone is using.

The rest of the browser is a real Chrome: its TLS, HTTP/2 and rendering fingerprints are the ones Chrome has, because it is Chrome.

## Reach Pydoll from a Playwright object {#reach-pydoll-from-a-playwright-object}

Every Playwright object exposes the Pydoll object underneath, so features Playwright has no name for are one attribute away. You don't rewrite the script to use them.

| Playwright object | Pydoll object underneath |
|-------------------|--------------------------|
| `browser.chrome` | [Chrome](api/browser/chrome.md) |
| `page.tab` | [Tab](api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](api/elements/web_element.md) |

Three things a blocked script usually needs next, each one line:

=== "Sync"

    ```python
    from pydoll.sync import ExtractionModel, Field
    from pydoll.playwright.sync_api import sync_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        with page.tab.expect_cloudflare_turnstile():
            page.goto('https://quotes.toscrape.com')

        quotes = page.tab.extract_all(Quote, scope='.quote')
        submit = page.get_by_role('link', name='Login').element_handle().web_element
        submit.click(humanize=True)
    ```

=== "Async"

    ```python
    from pydoll import ExtractionModel, Field
    from pydoll.playwright.async_api import async_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        async with page.tab.expect_cloudflare_turnstile():
            await page.goto('https://quotes.toscrape.com')

        quotes = await page.tab.extract_all(Quote, scope='.quote')
        submit = (await page.get_by_role('link', name='Login').element_handle()).web_element
        await submit.click(humanize=True)
    ```

`apply_fingerprint` sets a coherent identity across every layer ([Fingerprint injection](stealth/fingerprint-injection.md)), `expect_cloudflare_turnstile` clicks the Turnstile widget if the navigation inside its block meets one ([Captcha bypass](stealth/captcha-bypass.md)), `extract_all` returns typed, validated objects ([Structured extraction](guides/structured-extraction.md)), and `humanize=True` moves the mouse along a curved path with human timing ([Human-like interactions](stealth/human-like-interactions.md)). Raw CDP is one call away as well: `page.tab.execute_command(...)`.

## What this does not change {#what-this-does-not-change}

!!! warning "What detection still sees"
    Pydoll removes the automation tells a library adds; it does not make a bot a person. A headless browser is still recognizable by its rendering and its missing media devices, so run headful or apply a fingerprint profile that covers the headless signals. Your IP reputation counts as much as the browser; a datacenter IP fails challenges a residential one passes. Signals baked into the Chrome binary are not touched. And behavior matters: instant clicks and perfectly regular typing look like what they are, which is what `humanize=True` is for.

[Staying undetected](stealth/index.md) walks through each layer with the minimum setup for it.

## What's next

- [Playwright API](guides/playwright-api.md): the full compatibility matrix and the behaviors that differ.
- [Staying undetected](stealth/index.md): identity, behavior and challenges, in that order.
- [Migrating from Selenium and Playwright](migrating.md): the same moves in Pydoll's own API, when you want to go native.
