# Human-Like Interactions

One of the key differentiators between successful automation and easily-detected bots is how realistic the interactions are. Pydoll provides sophisticated tools to make your automation virtually indistinguishable from human behavior.

!!! info "Feature Status"
    **Already Implemented:**

    - **Humanized Keyboard**: Variable typing speed, realistic typos with auto-correction (`humanize=True`)
    - **Humanized Scroll**: Physics-based scrolling with momentum, friction, jitter, and overshoot (`humanize=True`)
    - **Humanized Mouse**: Bezier curve paths, Fitts's Law timing, minimum-jerk velocity, tremor, and overshoot (`humanize=True`)

    **Coming Soon:**

    - **Automatic random click offsets**: Optional parameter to automatically randomize click positions within elements
    - **Hover behavior**: Realistic delays and movement when hovering over elements

## Why Human-Like Interactions Matter

Modern websites employ sophisticated bot detection techniques:

- **Event timing analysis**: Detecting impossibly fast or perfectly timed actions
- **Mouse movement tracking**: Identifying straight-line movements or instant teleportation
- **Keyboard patterns**: Spotting instant text insertion without individual keystrokes
- **Click positions**: Detecting clicks always at exact center of elements
- **Action sequences**: Identifying non-human patterns in user behavior

Pydoll helps you avoid detection by providing realistic interaction methods that mimic real user behavior.

## Realistic Mouse Movement

The Mouse API (`tab.mouse`) provides humanized cursor control with multiple layers of realism. When `humanize=True`, mouse movements follow natural Bezier curve paths with Fitts's Law timing, minimum-jerk velocity profiles, physiological tremor, and overshoot correction.

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')

    # Move with natural curved path
    await tab.mouse.move(500, 300, humanize=True)

    # Click with realistic movement, offset, and timing
    await tab.mouse.click(500, 300, humanize=True)

    # Drag with natural movement
    await tab.mouse.drag(100, 200, 500, 400, humanize=True)
```

Key techniques applied during humanized mouse operations:

- **Bezier curve paths**: Curved trajectories with asymmetric control points (more curvature early in the movement)
- **Fitts's Law timing**: Movement duration scales with distance: `MT = a + b × log₂(D/W + 1)`
- **Minimum-jerk velocity**: Bell-shaped speed profile — slow start, peak in the middle, slow end
- **Physiological tremor**: Gaussian noise (σ ≈ 1px) scaled inversely with velocity
- **Overshoot and correction**: ~70% chance of overshooting fast movements by 3–12%, then correcting back
!!! info "Dedicated Mouse Control Documentation"
    For comprehensive mouse control documentation, including all methods, custom timing configuration, position tracking, and debug mode, see **[Mouse Control](mouse-control.md)**.

## Realistic Clicking

### Basic Click with Simulated Mouse Events

The `click()` method simulates real mouse press and release events, unlike JavaScript-based clicking:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def realistic_clicking():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        button = await tab.find(id="submit-button")
        
        # Basic realistic click
        await button.click()
        
        # The click includes:
        # - Mouse move to element
        # - Mouse press event
        # - Configurable hold time
        # - Mouse release event

asyncio.run(realistic_clicking())
```

### Click with Position Offset

Real users rarely click at the exact center of elements. Use offsets to vary click positions:

!!! info "Current State: Manual Offset Calculation"
    Currently, you must manually calculate and randomize click offsets for each interaction. Future versions will include an optional parameter to automatically randomize click positions within element bounds.

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def click_with_offset():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/form')
        
        submit_button = await tab.find(tag_name="button", type="submit")
        
        # Click slightly off-center (more natural)
        await submit_button.click(
            x_offset=5,   # 5 pixels right of center
            y_offset=-3   # 3 pixels above center
        )
        
        # Currently: Manually vary the offset for each click to appear more human
        for item in await tab.find(class_name="clickable-item", find_all=True):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            await item.click(x_offset=offset_x, y_offset=offset_y)
            await asyncio.sleep(random.uniform(0.5, 2.0))

asyncio.run(click_with_offset())
```

### Adjustable Click Hold Time

Vary the duration of mouse button press to simulate different click styles:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def variable_hold_time():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        button = await tab.find(class_name="action-button")
        
        # Quick click (default is 0.1s)
        await button.click(hold_time=0.05)
        
        # Normal click
        await button.click(hold_time=0.1)
        
        # Slower, more deliberate click
        await button.click(hold_time=0.2)
        
        # Simulate user hesitation
        await asyncio.sleep(0.8)
        await button.click(hold_time=0.15)

asyncio.run(variable_hold_time())
```

### When to Use click() vs click_using_js()

Understanding the difference is crucial for avoiding detection:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def click_methods_comparison():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        button = await tab.find(id="interactive-button")
        
        # Method 1: click() - Simulates real mouse events
        # ✅ Triggers all mouse events (mousedown, mouseup, click)
        # ✅ Respects element positioning
        # ✅ More realistic and harder to detect
        # ❌ Requires element to be visible and in viewport
        await button.click()
        
        # Method 2: click_using_js() - Uses JavaScript click()
        # ✅ Works on hidden elements
        # ✅ Faster execution
        # ✅ Bypasses visual overlays
        # ❌ May be detected as automation
        # ❌ Doesn't trigger same event sequence as real user
        await button.click_using_js()

asyncio.run(click_methods_comparison())
```

!!! tip "Best Practice: Prefer Mouse Events"
    Use `click()` for user-facing interactions to maintain realism. Reserve `click_using_js()` for backend operations, hidden elements, or when speed is critical and detection isn't a concern.

## Realistic Text Input

Pydoll's keyboard API provides two typing modes to balance speed and stealth.

!!! info "Understanding Typing Modes"
    | Mode | Parameters | Behavior | Use Case |
    |------|------------|----------|----------|
    | **Default (Humanized)** | `humanize=True` | Variable timing, ~2% typo rate with auto-correction | **Anti-bot evasion** (default) |
    | **Fast** | `humanize=False` | Fixed 50ms intervals, no typos | Speed-critical, low-risk scenarios |

    The `interval` parameter is deprecated. Use the default `humanize=True` for realistic typing.

### Natural Typing with Humanization

By default, `type_text()` uses humanized mode — simulating realistic human typing with variable speeds and occasional typos that are automatically corrected:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def natural_typing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/login')
        
        username_field = await tab.find(id="username")
        password_field = await tab.find(id="password")

        # Variable speed: 30-120ms between keystrokes
        # ~2% typo rate with realistic correction behavior
        await username_field.type_text("john.doe@example.com")  # humanize=True by default
        await password_field.type_text("MyC0mpl3xP@ssw0rd!")

asyncio.run(natural_typing())
```

### Fast Input for Non-Visible Fields

For fields that don't require realism (like hidden fields or backend operations), use `insert_text()`:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def fast_vs_realistic_input():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/form')
        
        username = await tab.find(id="username")
        await username.click()
        await username.type_text("john_doe")  # humanize=True by default
        
        hidden_field = await tab.find(id="hidden-token")
        await hidden_field.insert_text("very-long-generated-token-12345678")
        
        comment = await tab.find(id="comment-box")
        await comment.click()
        await comment.type_text("This looks like human input!")  # humanize=True by default

asyncio.run(fast_vs_realistic_input())
```

!!! info "Advanced Keyboard Control"
    For comprehensive keyboard control documentation, including special keys, key combinations, modifiers, and complete key reference tables, see **[Keyboard Control](keyboard-control.md)**.

## Realistic Page Scrolling

Pydoll provides a dedicated scroll API that waits for scroll completion before proceeding, making your automations more realistic and reliable.

!!! info "Understanding Scroll Modes"
    Pydoll's scroll API offers **three distinct modes**:

    | Mode | Parameters | Behavior | Use Case |
    |------|------------|----------|----------|
    | **Humanized (Default)** | `humanize=True` | Physics engine with momentum, jitter, overshoot | **Anti-bot evasion** (default) |
    | **Smooth** | `humanize=False, smooth=True` | CSS-based animation, predictable | General browsing simulation |
    | **Instant** | `humanize=False, smooth=False` | Teleports to position immediately | Speed-critical operations |

    Humanized scrolling is now the default. Pass `humanize=False` to use CSS-based or instant scrolling.

### Basic Directional Scrolling

Use the `scroll.by()` method to scroll the page in any direction with precise control:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def basic_scrolling():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/long-page')
        
        # Humanized (default) - physics engine with Bezier curves
        # Includes: momentum, friction, jitter, micro-pauses, overshoot
        await tab.scroll.by(ScrollPosition.DOWN, 500)
        await tab.scroll.by(ScrollPosition.UP, 300)

        # CSS-based animation - looks nice but predictable timing
        await tab.scroll.by(ScrollPosition.DOWN, 500, humanize=False, smooth=True)

        # Teleports instantly - fastest but easily detectable
        await tab.scroll.by(ScrollPosition.DOWN, 1000, humanize=False, smooth=False)

asyncio.run(basic_scrolling())
```

### Scrolling to Specific Positions

Navigate to the top or bottom of the page with control over realism:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scroll_to_positions():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/article')
        
        # Read the beginning of the article
        await asyncio.sleep(2.0)
        
        # Humanized scroll (default — physics engine, anti-bot evasion)
        await tab.scroll.to_bottom()
        await asyncio.sleep(1.5)
        await tab.scroll.to_top()

        # CSS smooth scroll (predictable animation)
        await tab.scroll.to_bottom(humanize=False, smooth=True)
        await asyncio.sleep(1.5)
        await tab.scroll.to_top(humanize=False, smooth=True)

asyncio.run(scroll_to_positions())
```

!!! tip "Choosing the Right Mode"
    - **Default** (`humanize=True`): Best for anti-bot evasion — used automatically
    - **`humanize=False, smooth=True`**: Good for demos, screenshots, and general automation
    - **`humanize=False, smooth=False`**: Maximum speed when stealth is not a concern

### Human-Like Scrolling Patterns

Pydoll's scroll engine uses **Cubic Bezier curves** to simulate the physics of human scrolling. This includes:

- **Momentum**: Initial burst of speed followed by gradual deceleration.
- **Friction**: Natural slowing down based on "physical" resistance.
- **Micro-pauses**: Brief stops during long scrolls, mimicking reading or eye movement.
- **Overshoot**: Occasional scrolling past the target and correcting back.

This behavior is automatically enabled when you use `humanize=True`.

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def human_like_scrolling():
    """Simulate natural scrolling patterns while reading an article."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/article')
        
        # User starts reading from top
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Gradually scroll while reading
        # The scroll engine handles the physics (acceleration/deceleration)
        for _ in range(random.randint(5, 8)):
            # Varied scroll distances (simulates reading speed)
            scroll_distance = random.randint(300, 600)
            await tab.scroll.by(
                ScrollPosition.DOWN, 
                scroll_distance, 
                humanize=True # Enables Bezier curve physics
            )
            
            # Pause to "read" content
            await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # Quick scroll to check the end
        await tab.scroll.to_bottom(humanize=True)
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Scroll back to top to re-read something
        await tab.scroll.to_top(humanize=True)

asyncio.run(human_like_scrolling())
```

### Scrolling Elements into View

Use `scroll_into_view()` to ensure elements are visible before taking page screenshots:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scroll_for_screenshots():
    """Scroll elements into view before capturing page screenshots."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/product')
        
        # Scroll to pricing section before taking full page screenshot
        pricing_section = await tab.find(id="pricing")
        await pricing_section.scroll_into_view()
        await tab.take_screenshot(path="page_with_pricing.png")
        
        # Scroll to reviews section before screenshot
        reviews = await tab.find(class_name="reviews")
        await reviews.scroll_into_view()
        await tab.take_screenshot(path="page_with_reviews.png")
        
        # Scroll to footer to capture complete page state
        footer = await tab.find(tag_name="footer")
        await footer.scroll_into_view()
        await tab.take_screenshot(path="page_with_footer.png")
        
        # Note: click() already scrolls automatically, so no need for:
        # await button.scroll_into_view()  # Unnecessary!
        # await button.click()  # This already scrolls the button into view

asyncio.run(scroll_for_screenshots())
```

### Handling Infinite Scroll Content

Implement scrolling patterns to load lazy-loaded content:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.constants import ScrollPosition

async def infinite_scroll_loading():
    """Load content on infinite scroll pages."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/feed')
        
        items_loaded = 0
        max_scrolls = 10
        
        for scroll_num in range(max_scrolls):
            # Scroll to bottom to trigger loading
            await tab.scroll.to_bottom(smooth=True)
            
            # Wait for content to load
            await asyncio.sleep(random.uniform(2.0, 3.0))
            
            # Check if new items were loaded
            items = await tab.find(class_name="feed-item", find_all=True)
            new_count = len(items)
            
            if new_count == items_loaded:
                print("No more content to load")
                break
            
            items_loaded = new_count
            print(f"Scroll {scroll_num + 1}: {items_loaded} items loaded")
            
            # Small scroll up (human behavior)
            if random.random() > 0.7:
                await tab.scroll.by(ScrollPosition.UP, 200, smooth=True)
                await asyncio.sleep(random.uniform(0.5, 1.0))

asyncio.run(infinite_scroll_loading())
```

!!! success "Automatic Completion Waiting"
    Unlike `execute_script("window.scrollBy(...)")` which returns immediately, the `scroll` API uses CDP's `awaitPromise` parameter to wait for the browser's `scrollend` event. This ensures your subsequent actions only execute after scrolling completely finishes.

## Combining Techniques for Maximum Realism

### Complete Form Filling Example

Here's a comprehensive example combining all human-like interaction techniques. **This demonstrates the current manual approach** for achieving maximum realism—future versions will automate much of this randomization:

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

async def human_like_form_filling():
    """Fill a form with maximum realism to avoid detection."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/registration')
        
        # Wait a bit (user reading the page)
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # Fill first name with variable typing speed
        first_name = await tab.find(id="first-name")
        await first_name.click(
            x_offset=random.randint(-5, 5),
            y_offset=random.randint(-5, 5)
        )
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Manual character-by-character typing with randomized delays
        # (This will be automated in future versions)
        name_text = "John"
        for char in name_text:
            await first_name.type_text(char, interval=0)
            await asyncio.sleep(random.uniform(0.08, 0.22))
        
        # Tab to next field
        await asyncio.sleep(random.uniform(0.3, 0.8))
        await first_name.press_keyboard_key(Key.TAB)
        
        # Fill last name
        await asyncio.sleep(random.uniform(0.2, 0.5))
        last_name = await tab.find(id="last-name")
        await last_name.type_text("Doe", interval=random.uniform(0.1, 0.18))
        
        # Tab to email
        await asyncio.sleep(random.uniform(0.4, 1.0))
        await last_name.press_keyboard_key(Key.TAB)
        
        # Fill email with realistic pauses
        await asyncio.sleep(random.uniform(0.2, 0.5))
        email = await tab.find(id="email")
        
        email_text = "john.doe@example.com"
        for i, char in enumerate(email_text):
            await email.type_text(char, interval=0)
            # Longer pause at @ and . symbols (natural)
            if char in ['@', '.']:
                await asyncio.sleep(random.uniform(0.2, 0.4))
            else:
                await asyncio.sleep(random.uniform(0.08, 0.2))
        
        # Simulate user reviewing what they typed
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # Accept terms checkbox with offset
        terms_checkbox = await tab.find(id="accept-terms")
        await terms_checkbox.click(
            x_offset=random.randint(-3, 3),
            y_offset=random.randint(-3, 3),
            hold_time=random.uniform(0.08, 0.15)
        )
        
        # Pause before submitting (user reviewing form)
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # Click submit with realistic parameters
        submit_button = await tab.find(tag_name="button", type="submit")
        await submit_button.click(
            x_offset=random.randint(-8, 8),
            y_offset=random.randint(-5, 5),
            hold_time=random.uniform(0.1, 0.2)
        )
        
        print("Form submitted with human-like behavior")

asyncio.run(human_like_form_filling())
```

## Best Practices for Avoiding Detection

!!! tip "Manual Randomization Currently Required"
    The following best practices represent the **current state of Pydoll**, where you must manually implement randomization. While this requires more code, it gives you fine-grained control over behavior. Future versions will automate these patterns while maintaining the same level of realism.

### 1. Always Add Random Delays

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

# Bad: Predictable timing
await element1.click()
await element2.click()
await element3.click()

# Good: Variable timing (currently required)
await element1.click()
await asyncio.sleep(random.uniform(0.5, 1.5))
await element2.click()
await asyncio.sleep(random.uniform(0.8, 2.0))
await element3.click()
```

### 2. Vary Click Positions

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

# Bad: Always center clicks
for button in buttons:
    await button.click()

# Good: Varied positions (currently manual)
for button in buttons:
    await button.click(
        x_offset=random.randint(-10, 10),
        y_offset=random.randint(-10, 10)
    )
```

### 3. Simulate Natural User Behavior

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def natural_user_simulation(tab):
    # User arrives at page
    await tab.go_to('https://example.com')
    
    # User reads page content (1-3 seconds)
    await asyncio.sleep(random.uniform(1.0, 3.0))
    
    # User scrolls down to see more
    await tab.scroll.by(ScrollPosition.DOWN, 300, smooth=True)
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    # User finds and clicks button
    button = await tab.find(class_name="cta-button")
    await button.click(
        x_offset=random.randint(-5, 5),
        y_offset=random.randint(-5, 5)
    )
    
    # User waits for content to load
    await asyncio.sleep(random.uniform(0.8, 1.5))
```

### 4. Combine Multiple Techniques

```python
import asyncio
import random
from pydoll.browser.chromium import Chrome

async def advanced_stealth_automation():
    """Combine multiple techniques for maximum stealth."""
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Use human-like page load waiting
        await tab.go_to('https://example.com/sensitive-page')
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Scroll realistically with the dedicated API
        for _ in range(random.randint(2, 4)):
            scroll_amount = random.randint(200, 500)
            await tab.scroll.by(ScrollPosition.DOWN, scroll_amount, smooth=True)
            await asyncio.sleep(random.uniform(0.8, 2.0))
        
        # Find element with timeout (simulating user search)
        target = await tab.find(
            class_name="target-element",
            timeout=random.randint(3, 7)
        )
        
        # Click with all realistic parameters
        await target.click(
            x_offset=random.randint(-12, 12),
            y_offset=random.randint(-8, 8),
            hold_time=random.uniform(0.09, 0.18)
        )
        
        # Human reaction time
        await asyncio.sleep(random.uniform(0.5, 1.2))

asyncio.run(advanced_stealth_automation())
```

## Performance vs Realism Trade-offs

Sometimes you need to balance speed with realism:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def balanced_automation():
    """Choose appropriate realism level based on context."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/scraping-target')
        
        # Phase 1: Initial interaction (high realism)
        # This is when detection systems are most active
        login_button = await tab.find(text="Login")
        await asyncio.sleep(random.uniform(1.0, 2.0))
        await login_button.click(
            x_offset=random.randint(-5, 5),
            y_offset=random.randint(-5, 5)
        )
        
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        username = await tab.find(id="username")
        await username.type_text("user@example.com", interval=0.12)
        
        await asyncio.sleep(random.uniform(0.3, 0.7))
        
        password = await tab.find(id="password")
        await password.type_text("password123", interval=0.10)
        
        submit = await tab.find(type="submit")
        await asyncio.sleep(random.uniform(0.8, 1.5))
        await submit.click()
        
        # Phase 2: Authenticated data extraction (lower realism, higher speed)
        # Less scrutiny after successful authentication
        await asyncio.sleep(2)
        
        # Fast navigation through pages
        items = await tab.find(class_name="data-item", find_all=True)
        
        for item in items:
            # Quick click without offsets
            await item.click_using_js()
            await asyncio.sleep(0.3)  # Minimal delay
            
            # Extract data
            title = await tab.find(class_name="title")
            data = await title.text
            
            # Fast navigation
            await tab.execute_script("window.history.back()")
            await asyncio.sleep(0.5)

asyncio.run(balanced_automation())
```

## Monitoring and Adjusting

Test your automation's realism:

```python
import asyncio
import random
import time
from pydoll.browser.chromium import Chrome

async def test_interaction_timing():
    """Log timing to ensure realistic patterns."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/test-page')
        
        # Measure and log interaction timing
        elements = await tab.find(class_name="clickable", find_all=True)
        
        timings = []
        last_time = time.time()
        
        for i, element in enumerate(elements):
            await element.click(
                x_offset=random.randint(-8, 8),
                y_offset=random.randint(-8, 8)
            )
            
            current_time = time.time()
            elapsed = current_time - last_time
            timings.append(elapsed)
            
            print(f"Click {i+1}: {elapsed:.3f}s since last action")
            last_time = current_time
            
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Analyze timing distribution
        avg_time = sum(timings) / len(timings)
        print(f"\nAverage time between actions: {avg_time:.3f}s")
        print(f"Min: {min(timings):.3f}s, Max: {max(timings):.3f}s")
        
        # Good: Variable timing with realistic average (1-2 seconds)
        # Bad: Constant timing or unrealistically fast (<0.1s)

asyncio.run(test_interaction_timing())
```

## Learn More

For more information about element interaction methods:

- **[Element Finding](../element-finding.md)**: Locate elements to interact with
- **[WebElement Domain](../../deep-dive/webelement-domain.md)**: Deep dive into WebElement capabilities
- **[File Operations](file-operations.md)**: Upload files and handle downloads

Master human-like interactions, and your automation will be more reliable, harder to detect, and more closely mirror real user behavior.
