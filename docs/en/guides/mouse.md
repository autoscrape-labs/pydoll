# Mouse

Pydoll drives the mouse two ways: through an element you found, which is what you want most of the time, or at raw page coordinates when you need precise positions. Both support `humanize=True`, which moves the cursor along a curved, human-timed path instead of teleporting to the target.

<iframe scrolling="no" src="/docs/resources/visuals/mouse-humanize.html" aria-label="Humanized curved cursor path versus an instant robotic jump" style="width: 100%; height: 345px; border: 0;" loading="lazy"></iframe>

## Click an element

The common case is clicking an element you already located with `find()` or `query()`. Call `click()` on it; you don't compute coordinates, and the element is scrolled into view first.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/add_remove_elements/')

        add_button = await tab.find(text='Add Element')
        await add_button.click()

        # the click added a Delete button
        delete = await tab.find(class_name='added-manually')
        print('Added:', await delete.text)

asyncio.run(main())
```

`click()` takes a few options:

```python
# click a point offset from the element center (pixels)
await element.click(x_offset=10, y_offset=5)

# hold the button down longer before releasing (seconds)
await element.click(hold_time=0.3)

# humanized: curved cursor path to the element, then click
await element.click(humanize=True)
```

!!! note "Element click vs raw coordinates"
    Prefer `element.click()`. It finds the element's position for you and survives layout changes. Reach for the coordinate API below only when there is no element to target, such as clicking inside a `<canvas>` or dragging a handle by pixel.

## The coordinate mouse API

`tab.mouse` clicks, moves, and drags at explicit coordinates in CSS pixels, measured from the top-left of the page. You usually get those coordinates from an element's bounds (see [Drag a slider](#drag-a-slider)).

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://the-internet.herokuapp.com/')

        await tab.mouse.move(500, 300)                        # move the cursor
        await tab.mouse.click(500, 300)                       # left click
        await tab.mouse.click(500, 300, button=MouseButton.RIGHT)  # right click
        await tab.mouse.double_click(500, 300)               # double click
        await tab.mouse.drag(100, 200, 500, 400)             # press, move, release

asyncio.run(main())
```

`MouseButton` (from `pydoll.protocol.input.types`) has `LEFT`, `MIDDLE`, and `RIGHT`. `click()` also takes `click_count` (pass `2` for a double click) and every method takes the keyword-only `humanize`.

For pressing and releasing separately, `down()` and `up()` operate at the current cursor position:

```python
await tab.mouse.move(300, 400)
await tab.mouse.down(button=MouseButton.LEFT)
await tab.mouse.move(600, 400)     # drag by hand
await tab.mouse.up(button=MouseButton.LEFT)
```

`tab.mouse` tracks the cursor position across calls, so `down()`/`up()` act wherever the last `move()` or `click()` left it.

## Move like a human

By default a move or click jumps straight to the target, which is a behavioral tell. Pass `humanize=True` and Pydoll moves the cursor along a curved path with human timing (a Fitts's-Law duration, a bell-shaped speed profile, small tremor, and occasional overshoot with correction):

```python
await tab.mouse.move(500, 300, humanize=True)
await tab.mouse.click(500, 300, humanize=True)
await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

<p align="center">
  <img src="/docs/resources/images/gif-humanized-cursor-path.gif" alt="Humanized cursor moving along two curved paths" width="760" />
</p>
<p align="center"><sub>Two humanized moves: curved paths with easing and a slight overshoot, not straight jumps.</sub></p>

Humanized element clicks work the same way. Because the position is tracked, clicking element A then element B traces a natural curve from one to the other:

```python
# instant: the cursor jumps straight to each target
await (await tab.find(id='first')).click()
await (await tab.find(id='second')).click()

# humanized: the cursor curves naturally from one target to the next
await (await tab.find(id='first')).click(humanize=True)
await (await tab.find(id='second')).click(humanize=True)
```

See [Human-like interactions](../stealth/human-like-interactions.md) for the full timing model and when humanization matters.

### Tune the timing {#tune-the-timing}

The humanized physics are configurable through `MouseTimingConfig`. Assign a new config to `tab.mouse.timing`:

```python
from pydoll.interactions.mouse import MouseTimingConfig

tab.mouse.timing = MouseTimingConfig(
    fitts_a=0.070,               # base movement time (seconds)
    fitts_b=0.150,               # time added per bit of difficulty
    curvature_min=0.10,          # least path curvature (fraction of distance)
    curvature_max=0.30,          # most path curvature
    tremor_amplitude=1.0,        # hand-tremor sigma in pixels
    overshoot_probability=0.70,  # chance of overshoot on fast, long moves
    max_duration=2.5,            # cap on a single movement (seconds)
)
```

Every field has a default, so override only what you need. See the `MouseTimingConfig` dataclass in `pydoll/interactions/mouse.py` for the full list.

## Watch the cursor while tuning

Set `tab.mouse.debug = True` and Pydoll draws the cursor path on a transparent overlay: blue dots trace movement, red dots mark clicks. Use it to check that humanized paths look natural, then turn it off.

```python
tab.mouse.debug = True
await tab.mouse.click(500, 300, humanize=True)
tab.mouse.debug = False
```

## Practical examples

### Drag a slider {#drag-a-slider}

Read the handle's position from its bounds, then drag from there:

```python
slider = await tab.query('.slider-handle')
bounds = await slider.get_bounds_using_js()   # {'x', 'y', 'width', 'height'}, viewport pixels

start_x = bounds['x'] + bounds['width'] / 2
start_y = bounds['y'] + bounds['height'] / 2

await tab.mouse.drag(start_x, start_y, start_x + 200, start_y, humanize=True)
```

<p align="center">
  <img src="/docs/resources/images/gif-humanized-slider-drag.gif" alt="Slider handle dragged along a humanized path" width="760" />
</p>
<p align="center"><sub>Dragging the handle along a humanized path.</sub></p>

### Hover over a menu

Move the cursor onto an element to trigger its CSS `:hover` state, without clicking:

```python
trigger = await tab.query('.dropdown-trigger')
bounds = await trigger.get_bounds_using_js()

await tab.mouse.move(
    bounds['x'] + bounds['width'] / 2,
    bounds['y'] + bounds['height'] / 2,
    humanize=True,
)
```

<p align="center">
  <img src="/docs/resources/images/gif-hover-menu.gif" alt="Cursor moving onto a menu trigger, opening the dropdown" width="760" />
</p>
<p align="center"><sub>Moving onto the trigger, the dropdown expands and the cursor settles on an item.</sub></p>

## What's next

- [Keyboard](keyboard.md): type text and press keys, with the same humanized timing.
- [Human-like interactions](../stealth/human-like-interactions.md): the timing model behind `humanize=True` and when to use it.
- [Element finding](element-finding.md): locate the elements you click and drag.
