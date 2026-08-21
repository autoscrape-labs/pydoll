# Keyboard

Drive keyboard input through `tab.keyboard`: type into fields, press special keys like Enter and Tab, and run shortcuts such as Ctrl+A. Reach for it when a form needs keyboard navigation or a web app responds to key combinations that a click can't trigger.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.constants import Key


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://www.wikipedia.org')

        search = await tab.find(id='searchInput')
        await search.type_text('web scraping', humanize=True)

        await tab.keyboard.press(Key.ENTER)
        await asyncio.sleep(2)
        print(await tab.current_url)

asyncio.run(main())
```

## Type into a field

To type character by character into the focused element, use `type_text` on the element. Pass `humanize=True` for variable timing with the occasional corrected typo; leave it off for a fixed, faster rhythm.

```python
field = await tab.find(id='searchInput')
await field.type_text('search query', humanize=True)
```

Type your own text below and run it both ways. With `humanize=True` the rhythm varies and the occasional typo is corrected, so every run differs; without it, every gap is a flat 50ms.

<iframe src="/docs/resources/visuals/keyboard-humanize.html" aria-label="Interactive humanized typing: type text and watch it typed with human rhythm and corrected typos" style="width: 100%; height: 350px; border: 0;" loading="lazy"></iframe>

If you only need the text to appear and don't care about per-key events, `insert_text` pastes the whole string at once:

```python
await field.insert_text('search query')   # instant, no keystroke events
```

!!! note "`tab.keyboard` types wherever focus already is"
    `type_text` and `insert_text` on an element focus that element for you, so the text lands in the right place. The lower-level `tab.keyboard` methods (below) do not: they send keystrokes to whatever the page currently has focused. Focus the field first (clicking it focuses it) before typing through `tab.keyboard`.

## Press a key

`press()` runs a full key press (down, brief hold, up). Use it for keys that trigger behavior rather than text: Enter to submit, Tab to move between fields, Escape to dismiss.

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# arrow and navigation keys
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.END)
```

`press(key, interval=0.1)` holds the key for `interval` seconds before releasing; raise it to simulate a longer hold.

## Run a keyboard shortcut

`hotkey()` presses a combination and releases it in the right order, so you don't compute modifier bitmasks yourself. Pass the modifier first.

```python
from pydoll.constants import Key

await tab.keyboard.hotkey(Key.CONTROL, Key.A)   # select all
await tab.keyboard.hotkey(Key.CONTROL, Key.C)   # copy
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # select word left
```

macOS uses Command (Meta) where Windows and Linux use Control, so pick the modifier from the platform:

```python
import sys
from pydoll.constants import Key

mod = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(mod, Key.C)
```

## Apply a modifier to a single key

`press()` and `down()` take a `modifiers` argument from the `KeyModifier` enum:

```python
from pydoll.protocol.input.types import KeyModifier

await tab.keyboard.press(Key.S, modifiers=KeyModifier.CTRL)   # Ctrl+S
```

The members are `KeyModifier.ALT`, `.CTRL`, `.META`, and `.SHIFT`. `hotkey()` already applies modifiers for you, so reach for `modifiers` only when you press or hold a single key manually.

## Hold and release keys

For sequences where a modifier stays down across several presses, drive `down()` and `up()` yourself. Release in a `finally` block so an error mid-sequence doesn't leave a key stuck.

```python
from pydoll.constants import Key

try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)   # extend selection
    await tab.keyboard.press(Key.ARROWRIGHT)
finally:
    await tab.keyboard.up(Key.SHIFT)
```

## Browser UI shortcuts do not work

Keys sent over the DevTools Protocol are marked untrusted, so they never trigger Chrome's own UI. Shortcuts that open tabs, DevTools, or the address bar are inert. Page-level shortcuts inside the document work normally.

!!! warning "Use browser commands, not UI shortcuts"
    Ctrl+T, Ctrl+W, F12, and Ctrl+L will not do anything. Drive the browser through its API instead: `await browser.new_tab()`, `await tab.close()`, `await tab.go_to(url)`, `await tab.refresh()`. Shortcuts that act on the page content (Ctrl+A, Ctrl+C, Tab, Enter, arrow keys) work as expected.

## Key reference

`Key` (`from pydoll.constants import Key`) covers the full keyboard:

| Category | Members |
|----------|---------|
| Letters | `Key.A` through `Key.Z` |
| Numbers | `Key.DIGIT0` to `Key.DIGIT9`, `Key.NUMPAD0` to `Key.NUMPAD9` |
| Function | `Key.F1` through `Key.F12` |
| Navigation | `ARROWUP`, `ARROWDOWN`, `ARROWLEFT`, `ARROWRIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN` |
| Modifiers | `CONTROL`, `SHIFT`, `ALT`, `META` |
| Editing | `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`, `ESCAPE`, `INSERT` |

## What's next

- [Mouse](mouse.md): clicks, movement, and drag with humanized timing.
- [Element finding](element-finding.md): locate the fields you type into.
- [Human-like interactions](../stealth/human-like-interactions.md): what `humanize=True` does internally.
