# Cloudflare Turnstile

Pydoll can click a Cloudflare Turnstile checkbox for you, the same click a person makes on the widget. It does not solve image or puzzle challenges, and whether the click is accepted depends on your IP reputation and fingerprint, not on Pydoll. Treat this as automating the click, not defeating the captcha.

<iframe src="../captcha-turnstile.html" aria-label="Pydoll clicking a Turnstile checkbox, with the outcome depending on IP reputation" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## Handle Turnstile while you navigate

The context manager waits for the Turnstile widget to appear during the block, clicks its checkbox, and lets your code continue once it has acted. Put the navigation that triggers the challenge inside the block.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.expect_and_bypass_cloudflare_captcha():
            await tab.go_to('https://a-site-behind-turnstile.com')

        content = await tab.find(id='protected-content', timeout=10, raise_exc=False)
        print(await content.text if content else 'Still challenged.')

asyncio.run(main())
```

Replace the URL with the site you are automating. There is no public, stable Turnstile page to point at.

## Handle Turnstile in the background

When you don't want to wrap a specific navigation, enable background handling: Pydoll clicks the widget whenever it appears, until you disable it.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_auto_solve_cloudflare_captcha()
        await tab.go_to('https://a-site-behind-turnstile.com')
        await asyncio.sleep(5)   # give the widget time to appear and be clicked

        await tab.disable_auto_solve_cloudflare_captcha()

asyncio.run(main())
```

## How it finds the checkbox

Pydoll detects Turnstile by polling the page's shadow DOM for the Cloudflare widget: it looks for the shadow root that hosts `challenges.cloudflare.com`, steps into its cross-origin iframe, finds the inner shadow root, and clicks the checkbox as soon as it appears. You don't configure a selector, and there is no click delay to tune.

## Give the widget time to appear

Some sites render Turnstile after the initial load. `time_to_wait_captcha` (default 5 seconds) is how long Pydoll waits for the widget before giving up. Raise it for a slow site.

```python
async with tab.expect_and_bypass_cloudflare_captcha(time_to_wait_captcha=15):
    await tab.go_to('https://a-site-behind-turnstile.com')
```

`time_to_wait_captcha` is the only timing parameter. If the widget never appears within that window, the interaction is skipped.

!!! note "Migrating from older versions"
    `custom_selector` and `time_before_click` still exist on these methods but are deprecated and ignored. Detection is automatic now, so remove them from old code.

## What determines whether the click is accepted

Clicking the checkbox is only part of it. Turnstile decides whether to accept it from signals Pydoll does not control:

- **IP reputation.** A clean residential or mobile IP is usually accepted; a datacenter IP is often challenged or blocked. No browser configuration overcomes a flagged IP. See [Proxies](../guides/proxies.md).
- **Fingerprint consistency.** The identity your browser presents must agree with itself and with your IP. A common failure is a Chrome version mismatch: if you combine this with [Fingerprint Injection](fingerprint-injection.md), the profile's advertised version must match the real binary, or Turnstile stays on "Just a moment...". Align it to `await browser.get_version()`.
- **Headful vs headless.** Headless leaks rendering signals that lower the trust score. Prefer headful for Turnstile, or neutralize the headless signals first (see [Fingerprint Injection](fingerprint-injection.md)).

If the checkbox is clicked but a puzzle or image challenge follows, the trust score was too low. Pydoll cannot solve that challenge; improve the IP and fingerprint instead.

> 🎞️ **Interactive visual placeholder** — the Turnstile decision: IP reputation + fingerprint consistency + behavior feed a trust score that resolves to accepted / challenged / blocked, showing that the click is only one input.

## What it does not do

- It does not solve image selection or puzzle challenges.
- It does not handle reCAPTCHA or hCaptcha. Those are not supported by this feature.
- It does not change your IP or fingerprint. Pair it with a good proxy and a consistent fingerprint for the click to land.

!!! warning "Respect the site's terms"
    Automating a captcha may violate a site's Terms of Service. Use this only where you are authorized to: testing your own applications, monitoring services you control, or research with permission.

## What's next

- [Staying undetected](index.md): how captcha handling fits with the rest of the stealth layers.
- [Proxies](../guides/proxies.md): the IP reputation that decides most Turnstile outcomes.
- [Human-like interactions](human-like-interactions.md): humanized behavior before and around the click.
