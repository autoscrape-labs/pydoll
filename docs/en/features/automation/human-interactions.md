# Human-Like Interactions

One of the key differentiators between successful automation and easily-detected bots is how realistic the interactions are. Pydoll provides sophisticated tools to make your automation virtually indistinguishable from human behavior.

!!! warning "Future Enhancements"
    Pydoll is continuously improving its human-like interaction capabilities. Future versions will include:
    
    - **Variable typing speed**: Built-in random intervals between keystrokes to eliminate the need for manual randomization
    - **Realistic keyboard sequences**: Automatic simulation of typing mistakes, backspacing, corrections, and dynamic pauses for maximum realism
    - **Automatic random click offsets**: Optional parameter to automatically randomize click positions within elements, eliminating manual offset calculations
    - **Mouse movement simulation**: Realistic cursor paths with bezier curves
    - **Mouse delta events**: Natural acceleration and deceleration patterns
    - **Hover behavior**: Realistic delays and movement when hovering
    - **Timing variations**: Randomized delays to avoid predictable patterns
    
    These features leverage CDP and JavaScript capabilities for maximum realism.

## Why Human-Like Interactions Matter

Modern websites employ sophisticated bot detection techniques:

- **Event timing analysis**: Detecting impossibly fast or perfectly timed actions
- **Mouse movement tracking**: Identifying straight-line movements or instant teleportation
- **Keyboard patterns**: Spotting instant text insertion without individual keystrokes
- **Click positions**: Detecting clicks always at exact center of elements
- **Action sequences**: Identifying non-human patterns in user behavior

Pydoll helps you avoid detection by providing realistic interaction methods that mimic real user behavior.

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

### Natural Typing with Intervals

The `type_text()` method simulates human typing by sending individual keystrokes. The `interval` parameter adds a **fixed delay** between each keystroke.

!!! info "Current State: Manual Randomization Required"
    Currently, the `interval` parameter uses a **constant delay** for all characters. For maximum realism, you need to manually randomize typing speeds (as shown in the advanced examples below). Future versions will include automatic variable typing speed with built-in randomization.

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def natural_typing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/login')
        
        username_field = await tab.find(id="username")
        password_field = await tab.find(id="password")
        
        # Type with fixed intervals (currently)
        # Average human typing: 0.1-0.3 seconds per character
        await username_field.type_text("john.doe@example.com", interval=0.15)
        
        # Slower typing for complex passwords
        await password_field.type_text("MyC0mpl3xP@ssw0rd!", interval=0.12)

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
        
        # Realistic typing for visible fields
        username = await tab.find(id="username")
        await username.click()
        await username.type_text("john_doe", interval=0.12)
        
        # Fast insertion for hidden or backend fields
        hidden_field = await tab.find(id="hidden-token")
        await hidden_field.insert_text("very-long-generated-token-12345678")
        
        # Realistic typing for fields that matter
        comment = await tab.find(id="comment-box")
        await comment.click()
        await comment.type_text("This looks like human input!", interval=0.15)

asyncio.run(fast_vs_realistic_input())
```

!!! info "Advanced Keyboard Control"
    For comprehensive keyboard control documentation, including special keys, key combinations, modifiers, and complete key reference tables, see **[Keyboard Control](keyboard-control.md)**.

## Realistic Page Scrolling

Pydoll provides a dedicated scroll API that waits for scroll completion before proceeding, making your automations more realistic and reliable.

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
        
        # Scroll down 500 pixels (with smooth animation)
        await tab.scroll.by(ScrollPosition.DOWN, 500, smooth=True)
        
        # Scroll up 300 pixels
        await tab.scroll.by(ScrollPosition.UP, 300, smooth=True)
        
        # Scroll right (useful for horizontal scroll pages)
        await tab.scroll.by(ScrollPosition.RIGHT, 200, smooth=True)
        
        # Scroll left
        await tab.scroll.by(ScrollPosition.LEFT, 200, smooth=True)
        
        # Instant scroll (no animation)
        await tab.scroll.by(ScrollPosition.DOWN, 1000, smooth=False)

asyncio.run(basic_scrolling())
```

### Scrolling to Specific Positions

Navigate quickly to the top or bottom of the page:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scroll_to_positions():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/article')
        
        # Read the beginning of the article
        await asyncio.sleep(2.0)
        
        # Smoothly scroll to the bottom
        await tab.scroll.to_bottom(smooth=True)
        
        # Pause at the bottom
        await asyncio.sleep(1.5)
        
        # Return to the top
        await tab.scroll.to_top(smooth=True)

asyncio.run(scroll_to_positions())
```

!!! tip "Smooth vs Instant"
    - **smooth=True**: Uses browser's smooth animation and waits for `scrollend` event
    - **smooth=False**: Instant scrolling for maximum speed when realism isn't critical

### Human-Like Scrolling Patterns

!!! info "Future Enhancement: Built-in Realistic Scrolling"
    Currently, you must manually implement random scrolling patterns. Future versions will include a `realistic=True` parameter that automatically adds natural variations in scroll distances, speeds, and pauses to mimic human reading behavior.

Simulate natural reading and navigation behavior:

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
        for _ in range(random.randint(5, 8)):
            # Varied scroll distances (simulates reading speed)
            scroll_distance = random.randint(300, 600)
            await tab.scroll.by(
                ScrollPosition.DOWN, 
                scroll_distance, 
                smooth=True
            )
            
            # Pause to "read" content
            await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # Quick scroll to check the end
        await tab.scroll.to_bottom(smooth=True)
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Scroll back to top to re-read something
        await tab.scroll.to_top(smooth=True)

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
