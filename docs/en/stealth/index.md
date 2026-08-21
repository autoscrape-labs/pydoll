# Staying undetected

When a scraper gets blocked, the code is usually fine; the signals are not. Sites read three layers: what your browser says it is (User-Agent, headless markers, fingerprint), how it behaves (instant clicks, perfectly regular typing), and how it answers challenges (Cloudflare Turnstile). This page sets up the minimum for each layer and points to the deeper guides.

Some of the hard parts you get for free: because Pydoll drives a real Chrome over CDP, the network and browser fingerprints are authentic, and `navigator.webdriver` is `false` without any patching. What follows is what you still control.

**You will learn**

- [How to keep the browser's identity consistent](#keep-the-identity-consistent)
- [How to interact like a person](#interact-like-a-person)
- [How to handle Cloudflare Turnstile](#handle-cloudflare-turnstile)

## Keep the identity consistent {#keep-the-identity-consistent}

Identity is the hardest layer, because the signals have to agree with each other and with your IP and OS. The User-Agent, Client Hints, language, timezone, WebGL renderer, and fonts are all cross-checked; overriding one in isolation usually makes you more detectable, not less. Pydoll already keeps some of this consistent for you (it fixes the User-Agent and Client Hints together when you set `--user-agent=`), and applies a full coherent identity through `apply_fingerprint()`.

Start with [Evasion techniques](evasion-techniques.md) for the levers you control (User-Agent, language, WebRTC, realistic profile), and [Fingerprint Injection](fingerprint-injection.md) for applying a complete identity from one profile.

## Interact like a person {#interact-like-a-person}

Instant clicks in the exact center of an element and keystrokes every 50ms are behavioral fingerprints. Pass `humanize=True` and Pydoll moves the cursor along a curved path with human timing before clicking, and types with variable rhythm and occasional corrected typos:

```python
search_box = await tab.find(id='search')
await search_box.type_text('browser automation', humanize=True)

submit = await tab.find(tag_name='button', type='submit')
await submit.click(humanize=True)
```

Humanization is opt-in per interaction, so you keep it where behavior is watched and skip it where speed matters. [Human-like interactions](human-like-interactions.md) explains the timing model and how to tune it.

## Handle Cloudflare Turnstile {#handle-cloudflare-turnstile}

When a protected page shows the Turnstile checkbox, Pydoll can detect and click it for you:

```python
async with tab.expect_and_bypass_cloudflare_captcha():
    await tab.go_to('https://site-protected-by-cloudflare.com')

print('Challenge handled, page loaded.')
```

Clicking the widget is only part of it: whether Cloudflare accepts the click also depends on your IP reputation and how consistent the rest of your browser looks. If challenges keep failing, work through [Captcha bypass](captcha-bypass.md) and consider [a residential proxy](../guides/proxies.md).

## What's next

- [Evasion techniques](evasion-techniques.md): the full detection model and the levers you control.
- [Human-like interactions](human-like-interactions.md): the timing model behind `humanize=True`.
- [Captcha bypass](captcha-bypass.md): Cloudflare Turnstile handling in depth.
- [Fingerprint Injection](fingerprint-injection.md): apply a coherent identity across every layer.
