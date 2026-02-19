# Mouse Control

The Mouse API provides complete control over mouse input at the page level, enabling you to simulate realistic cursor movement, clicks, double-clicks, and drag operations. When `humanize=True` is passed, mouse operations use humanized simulation: paths follow natural Bezier curves with Fitts's Law timing, minimum-jerk velocity profiles, physiological tremor, and overshoot correction, making automation virtually indistinguishable from human behavior.

!!! info "Centralized Mouse Interface"
    All mouse operations are accessible via `tab.mouse`, providing a clean, unified API for all mouse interactions.

## Quick Start

```python
from pydoll.browser.chromium import Chrome
from pydoll.protocol.input.types import MouseButton

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')

    # Move cursor to position
    await tab.mouse.move(500, 300)

    # Click at position
    await tab.mouse.click(500, 300)

    # Right-click
    await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

    # Double-click
    await tab.mouse.double_click(500, 300)

    # Drag from one position to another
    await tab.mouse.drag(100, 200, 500, 400)
```

## Core Methods

### move: Move Cursor

Move the mouse cursor to a specific position on the page:

```python
# Default move (single CDP event, no simulation)
await tab.mouse.move(500, 300)

# Humanized move (curved path with natural timing)
await tab.mouse.move(500, 300, humanize=True)
```

**Parameters:**

- `x`: Target X coordinate (CSS pixels)
- `y`: Target Y coordinate (CSS pixels)
- `humanize` (keyword-only): Simulate human-like curved movement (default: `False`)

### click: Click at Position

Move to position and perform a mouse click:

```python
from pydoll.protocol.input.types import MouseButton

# Left click (default, instant)
await tab.mouse.click(500, 300)

# Right click
await tab.mouse.click(500, 300, button=MouseButton.RIGHT)

# Double click via click_count
await tab.mouse.click(500, 300, click_count=2)

# Humanized click with natural movement
await tab.mouse.click(500, 300, humanize=True)
```

**Parameters:**

- `x`: Target X coordinate
- `y`: Target Y coordinate
- `button` (keyword-only): Mouse button, one of `LEFT`, `RIGHT`, `MIDDLE` (default: `LEFT`)
- `click_count` (keyword-only): Number of clicks (default: `1`)
- `humanize` (keyword-only): Simulate human-like behavior (default: `False`)

### double_click: Double-Click at Position

Convenience method equivalent to `click(x, y, click_count=2)`:

```python
await tab.mouse.double_click(500, 300)
await tab.mouse.double_click(500, 300, humanize=False)
```

### down / up: Low-Level Button Control

Press or release mouse buttons independently:

```python
# Press left button at current position
await tab.mouse.down()

# Release left button
await tab.mouse.up()

# Right button
await tab.mouse.down(button=MouseButton.RIGHT)
await tab.mouse.up(button=MouseButton.RIGHT)
```

These are primitives that operate at the current cursor position and have no `humanize` parameter.

### drag: Drag and Drop

Move from start to end while holding the mouse button:

```python
# Default drag (instant)
await tab.mouse.drag(100, 200, 500, 400)

# Humanized drag with natural movement
await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

**Parameters:**

- `start_x`, `start_y`: Start coordinates
- `end_x`, `end_y`: End coordinates
- `humanize` (keyword-only): Simulate human-like drag (default: `False`)

## Enabling Humanization

All mouse methods default to `humanize=False`. To enable humanized simulation with natural Bezier curve paths and realistic timing, pass `humanize=True`:

```python
# Humanized move, natural curved path with Fitts's Law timing
await tab.mouse.move(500, 300, humanize=True)

# Humanized click: curved movement + pre-click pause + press + release
await tab.mouse.click(500, 300, humanize=True)

# Humanized drag, natural curves and pauses
await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

This is recommended when detection evasion is important, for example when interacting with sites that employ bot detection.

## Humanized Mode

When `humanize=True` is passed, the mouse module applies multiple layers of realism:

### Bezier Curve Paths

Mouse follows a natural curved trajectory instead of a straight line. Control points are randomly offset perpendicular to the start→end line, with asymmetric placement (more curvature early in the movement, like a real ballistic reach).

### Fitts's Law Timing

Movement duration follows Fitts's Law: `MT = a + b × log₂(D/W + 1)`. Longer distances take proportionally more time, matching human motor control behavior.

### Minimum-Jerk Velocity Profile

The cursor follows a bell-shaped speed profile, starting slow, accelerating to peak velocity in the middle, then decelerating at the end. This matches the smoothest possible human movement trajectory.

### Physiological Tremor

Small Gaussian noise (σ ≈ 1px) is added to each frame, simulating hand tremor. The tremor amplitude scales inversely with velocity, with more tremor when the cursor is slow or hovering and less during fast ballistic movements.

### Overshoot and Correction

For fast, long-distance movements (~70% probability), the cursor overshoots the target by 3–12% of the distance, then makes a small corrective sub-movement back to the target. This matches real human motor control data.

### Pre-Click Pause

Humanized clicks include a pre-click pause (50–200ms) that simulates the natural settle time before pressing the button.

## Automatic Humanized Element Clicks

When you use `element.click(humanize=True)`, the Mouse API is used to produce a realistic Bezier curve movement from the current cursor position to the element center before clicking, making element clicks indistinguishable from human behavior.

```python
# Default click: raw CDP press/release
button = await tab.find(id='submit')
await button.click()

# With offset from center
await button.click(x_offset=10, y_offset=5)

# Humanized click: Bezier curve movement + click
await button.click(humanize=True)
```

Position tracking is maintained across element clicks. Clicking element A, then element B, produces a natural curved path from A's position to B.

## Custom Timing Configuration

All humanization parameters are configurable via `MouseTimingConfig`:

```python
from pydoll.interactions.mouse import MouseTimingConfig

config = MouseTimingConfig(
    fitts_a=0.070,              # Fitts's Law intercept (seconds)
    fitts_b=0.150,              # Fitts's Law slope (seconds/bit)
    frame_interval=0.012,       # Base interval between mouseMoved events
    curvature_min=0.10,         # Min path curvature as fraction of distance
    curvature_max=0.30,         # Max path curvature
    tremor_amplitude=1.0,       # Tremor sigma in pixels
    overshoot_probability=0.70, # Chance of overshoot on fast moves
    min_duration=0.08,          # Minimum movement duration
    max_duration=2.5,           # Maximum movement duration
)

# Apply to the tab's mouse instance
tab.mouse.timing = config
```

See the `MouseTimingConfig` dataclass for all available parameters.

## Position Tracking

The Mouse API tracks the cursor position across operations:

```python
# Initial position is (0, 0)
await tab.mouse.move(100, 200)
# Position is now (100, 200)

await tab.mouse.click(300, 400)
# Position is now (300, 400)

# Low-level methods use the tracked position
await tab.mouse.down()   # Presses at (300, 400)
await tab.mouse.up()     # Releases at (300, 400)
```

!!! note "Position State"
    The mouse position is tracked internally. `WebElement.click()` automatically uses `tab.mouse` when available, so position tracking is maintained across element clicks.

## Debug Mode

Enable debug mode to visualize mouse movement on the page. When active, colored dots are drawn on a transparent overlay canvas:

- **Blue dots**: cursor path during movement
- **Red dots**: click positions

```python
# Enable at runtime via property
tab.mouse.debug = True

# Now all movements draw colored dots
await tab.mouse.click(500, 300)

# Disable when done
tab.mouse.debug = False
```

This is useful for tuning timing parameters and verifying that paths look natural.

## Practical Examples

### Click a Button with Realistic Movement

```python
async def click_button_naturally(tab):
    # element.click() automatically uses tab.mouse for humanized movement
    button = await tab.find(id='submit')
    await button.click()
```

### Drag a Slider

```python
async def drag_slider(tab):
    slider = await tab.find(css_selector='.slider-handle')
    bounds = await slider.get_bounds_using_js()

    start_x = bounds['x'] + bounds['width'] / 2
    start_y = bounds['y'] + bounds['height'] / 2
    end_x = start_x + 200  # Drag 200px to the right

    await tab.mouse.drag(start_x, start_y, end_x, start_y)
```

### Hover Over Elements

```python
async def hover_menu(tab):
    menu = await tab.find(css_selector='.dropdown-trigger')
    bounds = await menu.get_bounds_using_js()

    await tab.mouse.move(
        bounds['x'] + bounds['width'] / 2,
        bounds['y'] + bounds['height'] / 2,
    )
    # Menu should now be visible via CSS :hover
```

## Learn More

- **[Human Interactions](human-interactions.md)**: Overview of all humanized interactions
- **[Keyboard Control](keyboard-control.md)**: Realistic keyboard simulation
