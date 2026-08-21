# Human-like interactions

Detection systems watch *how* you act, not just what you click. Instant clicks in the exact center of an element, keystrokes at a perfectly fixed rate, and cursor jumps in straight lines are all behavioral tells. Pass `humanize=True` and Pydoll performs the same action with the timing and motion of a person: variable typing rhythm, curved cursor paths, and physics-based scrolling.

Humanization is opt-in per interaction, so you spend the extra milliseconds only where behavior is watched, and it is one layer of stealth, not the whole story. It shapes behavior; it does not change your [identity or network fingerprint](index.md).

## Type like a human

Pass `humanize=True` to `type_text()` and Pydoll varies the delay between keystrokes and adds occasional corrected typos (about 2%). Without it, typing runs at a fixed 50ms per character.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('tester', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('secret-passphrase', humanize=True)

asyncio.run(main())
```

When a field's contents don't need to look typed (a hidden token, a value no one watches), `insert_text()` sets the whole string at once with no per-key events.

> 🎞️ **Interactive visual placeholder** — two keystroke timelines for the same word: a fixed 50ms cadence versus the humanized rhythm with variable gaps and a corrected typo.

## Click like a human

`humanize=True` on `click()` moves the cursor to the element along a curved path with human timing before pressing. You can also shift the click off the exact center with `x_offset`/`y_offset`, and vary how long the button is held with `hold_time`.

```python
button = await tab.find(id='submit')

# curved approach, human press timing
await button.click(humanize=True)

# land slightly off center, hold a touch longer
await button.click(x_offset=6, y_offset=-3, hold_time=0.12)
```

`click()` dispatches real mouse events (move, down, up, click), which is what a page sees from a real user. `click_using_js()` calls the element's JavaScript `click()` instead: it works on hidden or covered elements and is faster, but it fires none of the mouse events, so prefer `click()` where behavior is watched and keep `click_using_js()` for hidden controls or speed-critical steps.

## Move the mouse like a human

For raw coordinates rather than an element, drive `tab.mouse` with `humanize=True`. The cursor follows a Bezier path with a Fitts's-Law duration (longer for farther, smaller targets), a bell-shaped velocity profile, small tremor, and an occasional overshoot that corrects back.

```python
await tab.mouse.move(480, 260, humanize=True)
await tab.mouse.click(480, 260, humanize=True)
await tab.mouse.drag(120, 200, 480, 360, humanize=True)
```

See [Mouse](../guides/mouse.md) for the full coordinate API and [Keyboard](../guides/keyboard.md) for key presses and shortcuts.

## Scroll like a human

Real users don't teleport down a page. `tab.scroll` offers three modes; `humanize=True` runs a physics model with momentum, friction, micro-pauses, and overshoot, and it waits for the browser's `scrollend` event before returning, so the next action runs only after scrolling finishes.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://news.ycombinator.com')

        await tab.scroll.by(ScrollPosition.DOWN, 600, humanize=True)
        await tab.scroll.to_bottom(humanize=True)
        await tab.scroll.to_top(humanize=True)

asyncio.run(main())
```

Without `humanize`, `smooth=True` (the default) does a predictable CSS animation, and `smooth=False` jumps instantly. To bring an element into view before a screenshot, use `await element.scroll_into_view()`.

## Tune the timing

The humanized mouse physics come from a `MouseTimingConfig` on `tab.mouse.timing`: the Fitts's-Law constants, path curvature, tremor, overshoot, and duration caps. Override only the fields you care about. The [Mouse guide](../guides/mouse.md#tune-the-timing) shows the config with each field explained.

## What humanization does not cover

Humanized behavior addresses one detection layer. A site can still flag you on your browser identity (User-Agent, WebGL, canvas) or your network path (IP reputation, TLS), no matter how natural your cursor looks. Treat this page as the behavioral piece and pair it with the rest:

!!! note "One layer of several"
    Humanized behavior does not make automation undetectable on its own. Match it with a consistent identity and a clean IP. See the [Stealth overview](index.md) for how the layers fit together.

## What's next

- [Captcha bypass](captcha-bypass.md): handle Cloudflare Turnstile when it appears.
- [Stealth overview](index.md): the full picture, from behavior to identity to network.
- [Keyboard](../guides/keyboard.md) and [Mouse](../guides/mouse.md): the complete input APIs.
- [Behavioral fingerprinting](../deep-dive/fingerprinting/behavioral-fingerprinting.md): how mouse, keyboard, and timing are analyzed.
