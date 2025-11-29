# Keyboard Control

The Keyboard API provides complete control over keyboard input at the page level, enabling you to simulate realistic typing, execute shortcuts, and control complex key sequences. Unlike element-level keyboard methods, the Keyboard API operates globally on the page, giving you the flexibility to interact with any focused element or trigger page-level keyboard actions.

!!! info "Centralized Keyboard Interface"
    All keyboard operations are accessible via `tab.keyboard`, providing a clean, unified API for all keyboard interactions.

!!! warning "Important CDP Limitation: Browser UI Shortcuts Don't Work"
    **Known Issue**: Events injected via Chrome DevTools Protocol are marked as "untrusted" and do **not** trigger browser UI actions or create user gestures.
    
    **What DOESN'T work:**

    - Browser shortcuts (Ctrl+T, Ctrl+W, Ctrl+N)
    - DevTools shortcuts (F12, Ctrl+Shift+I)
    - Browser navigation (Ctrl+Shift+T to reopen tabs)
    - Any shortcut that modifies browser UI or windows
    
    **What WORKS perfectly:**

    - Page-level shortcuts (Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+F)
    - Text selection and manipulation
    - Form navigation (Tab, Enter, Arrow keys)
    - Input field interactions
    - Custom application shortcuts (in web apps)
    
    **Technical reason**: CDP events don't create "user gestures" required by browser security. See [chromium issue #615341](https://bugs.chromium.org/p/chromium/issues/detail?id=615341) and [CDP documentation](https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-dispatchKeyEvent).
    
    For browser-level automation, use CDP browser commands directly (like `tab.close()`, `browser.new_tab()`) instead of keyboard shortcuts.

## Quick Start

The Keyboard API provides three primary methods:

```python
from pydoll.browser.chromium import Chrome
from pydoll.constants import Key

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com')

    # Press and release a key
    await tab.keyboard.press(Key.ENTER)
    
    # Execute a hotkey combination
    await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # Ctrl+S
    
    # Manual control
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    await tab.keyboard.up(Key.SHIFT)
```

## Core Methods

### Press: Complete Key Action

The `press()` method executes a full key press cycle (down → wait → up):

```python
from pydoll.constants import Key

# Basic key press
await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.ESCAPE)

# Press with modifiers
await tab.keyboard.press(Key.S, modifiers=2)  # Ctrl+S (manual modifier)

# Custom hold duration
await tab.keyboard.press(Key.SPACE, interval=0.5)  # Hold for 500ms
```

**Parameters:**

- `key`: Key to press (from `Key` enum)
- `modifiers` (optional): Modifier flags (Alt=1, Ctrl=2, Meta=4, Shift=8)
- `interval` (optional): Duration to hold key in seconds (default: 0.1)

### Down: Press Key Without Releasing

The `down()` method presses a key without releasing it, useful for holding modifiers or creating key sequences:

```python
from pydoll.constants import Key

# Hold Shift while pressing other keys
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)  # Select text
await tab.keyboard.press(Key.ARROWRIGHT)  # Continue selecting
await tab.keyboard.up(Key.SHIFT)

# Press with modifier flags
await tab.keyboard.down(Key.A, modifiers=2)  # Ctrl+A (select all)
```

**Parameters:**

- `key`: Key to press down
- `modifiers` (optional): Modifier flags to apply

### Up: Release a Key

The `up()` method releases a previously pressed key:

```python
from pydoll.constants import Key

# Manual key sequence
await tab.keyboard.down(Key.CONTROL)
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.T)  # Ctrl+Shift+T
await tab.keyboard.up(Key.SHIFT)
await tab.keyboard.up(Key.CONTROL)
```

**Parameters:**

- `key`: Key to release

!!! tip "When to Use Each Method"

    - **`press()`**: Single key actions (Enter, Tab, letters)
    - **`hotkey()`**: Keyboard shortcuts (Ctrl+C, Ctrl+Shift+T)
    - **`down()`/`up()`**: Complex sequences, holding modifiers, custom timing

## Hotkeys: Keyboard Shortcuts Made Easy

The `hotkey()` method automatically detects modifier keys and executes shortcuts correctly:

### Basic Hotkeys

```python
from pydoll.constants import Key

# Common shortcuts
await tab.keyboard.hotkey(Key.CONTROL, Key.C)  # Copy
await tab.keyboard.hotkey(Key.CONTROL, Key.V)  # Paste
await tab.keyboard.hotkey(Key.CONTROL, Key.X)  # Cut
await tab.keyboard.hotkey(Key.CONTROL, Key.Z)  # Undo
await tab.keyboard.hotkey(Key.CONTROL, Key.Y)  # Redo
await tab.keyboard.hotkey(Key.CONTROL, Key.A)  # Select all
await tab.keyboard.hotkey(Key.CONTROL, Key.S)  # Save

```

### Three-Key Combinations

```python
from pydoll.constants import Key

# Text editing shortcuts (these work!)
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWLEFT)  # Select word left
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.ARROWRIGHT)  # Select word right
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.HOME)  # Select to start of document
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.END)  # Select to end of document

# Application-specific shortcuts (if supported by the web app)
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.Z)  # Redo in many apps
await tab.keyboard.hotkey(Key.CONTROL, Key.SHIFT, Key.S)  # Save As (if app supports it)
```

### Platform-Specific Shortcuts

```python
import sys
from pydoll.constants import Key

# Use Meta (Command) on macOS, Control on Windows/Linux
modifier = Key.META if sys.platform == 'darwin' else Key.CONTROL

await tab.keyboard.hotkey(modifier, Key.C)  # Copy (platform-aware)
await tab.keyboard.hotkey(modifier, Key.V)  # Paste (platform-aware)
```

### How Hotkeys Work

The `hotkey()` method intelligently handles modifier keys:

1. **Detects modifiers**: Automatically identifies Ctrl, Shift, Alt, Meta
2. **Calculates flags**: Combines modifiers using bitwise OR (Ctrl=2, Shift=8 → 10)
3. **Applies correctly**: Presses non-modifier keys with modifier flags applied
4. **Clean release**: Releases keys in reverse order

```python
from pydoll.constants import Key

# Behind the scenes for hotkey(Key.CONTROL, Key.SHIFT, Key.T):
# 1. Detect: modifiers=[CONTROL, SHIFT], keys=[T]
# 2. Calculate: modifier_value = 2 | 8 = 10
# 3. Execute: press T with modifiers=10
# 4. Release: release T
```

!!! tip "Modifier Values"
    When using `modifiers` parameter manually:

    - Alt = 1
    - Ctrl = 2
    - Meta/Command = 4
    - Shift = 8
    
    Combine them: Ctrl+Shift = 2 + 8 = 10

## Available Keys

The `Key` enum provides comprehensive keyboard coverage:

### Letter Keys (A-Z)

```python
from pydoll.constants import Key

# All letters A through Z
await tab.keyboard.press(Key.A)
await tab.keyboard.press(Key.Z)
```

### Number Keys

```python
from pydoll.constants import Key

# Top row numbers (0-9)
await tab.keyboard.press(Key.DIGIT0)
await tab.keyboard.press(Key.DIGIT9)

# Numpad numbers
await tab.keyboard.press(Key.NUMPAD0)
await tab.keyboard.press(Key.NUMPAD9)
```

### Function Keys

```python
from pydoll.constants import Key

# F1 through F12
await tab.keyboard.press(Key.F1)
await tab.keyboard.press(Key.F12)
```

### Navigation Keys

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ARROWUP)
await tab.keyboard.press(Key.ARROWDOWN)
await tab.keyboard.press(Key.ARROWLEFT)
await tab.keyboard.press(Key.ARROWRIGHT)
await tab.keyboard.press(Key.HOME)
await tab.keyboard.press(Key.END)
await tab.keyboard.press(Key.PAGEUP)
await tab.keyboard.press(Key.PAGEDOWN)
```

### Modifier Keys

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.CONTROL)
await tab.keyboard.press(Key.SHIFT)
await tab.keyboard.press(Key.ALT)
await tab.keyboard.press(Key.META)  # Command on macOS, Windows key on Windows
```

### Special Keys

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.press(Key.SPACE)
await tab.keyboard.press(Key.BACKSPACE)
await tab.keyboard.press(Key.DELETE)
await tab.keyboard.press(Key.ESCAPE)
await tab.keyboard.press(Key.INSERT)
```

## Practical Examples

### Form Navigation

```python
from pydoll.browser import Chrome
from pydoll.constants import Key

async def fill_form_with_keyboard():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/form')
        
        # Focus first field and type
        first_field = await tab.find(id='name')
        await first_field.click()
        await first_field.insert_text('John Doe')
        
        # Navigate to next field with Tab
        await tab.keyboard.press(Key.TAB)
        await tab.keyboard.press(Key.TAB)  # Skip a field
        
        # Type in current focused field
        second_field = await tab.find(id='email')
        await second_field.insert_text('john@example.com')
        
        # Submit with Enter
        await tab.keyboard.press(Key.ENTER)
```

### Text Selection and Manipulation

```python
from pydoll.constants import Key

async def select_and_replace_text():
    # Select all text
    await tab.keyboard.hotkey(Key.CONTROL, Key.A)
    
    # Copy selection
    await tab.keyboard.hotkey(Key.CONTROL, Key.C)
    
    # Move to end
    await tab.keyboard.press(Key.END)
    
    # Select word by word
    await tab.keyboard.down(Key.CONTROL)
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.press(Key.ARROWLEFT)
    await tab.keyboard.up(Key.SHIFT)
    await tab.keyboard.up(Key.CONTROL)
    
    # Delete selection
    await tab.keyboard.press(Key.DELETE)
```

### Dropdown and Select Navigation

```python
from pydoll.constants import Key

async def navigate_dropdown():
    # Open dropdown
    select = await tab.find(tag_name='select')
    await select.click()
    
    # Navigate options with arrow keys
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.press(Key.ARROWDOWN)
    
    # Select with Enter
    await tab.keyboard.press(Key.ENTER)
    
    # Or cancel with Escape
    await tab.keyboard.press(Key.ESCAPE)
```

### Complex Key Sequences

```python
from pydoll.constants import Key
import asyncio

async def complex_editing():
    # Select line
    await tab.keyboard.press(Key.HOME)  # Go to start
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.END)  # Select to end
    await tab.keyboard.up(Key.SHIFT)
    
    # Cut
    await tab.keyboard.hotkey(Key.CONTROL, Key.X)
    
    # Move down and paste
    await tab.keyboard.press(Key.ARROWDOWN)
    await tab.keyboard.hotkey(Key.CONTROL, Key.V)
    
    # Undo if needed
    await tab.keyboard.hotkey(Key.CONTROL, Key.Z)
```

## Best Practices

### 1. Add Delays for Reliability

```python
from pydoll.constants import Key
import asyncio

# Good: Wait for UI to update
await tab.keyboard.hotkey(Key.CONTROL, Key.F)  # Open find
await asyncio.sleep(0.2)  # Wait for dialog
await tab.keyboard.press(Key.ESCAPE)  # Close it

# Bad: No delay, it might not work
await tab.keyboard.hotkey(Key.CONTROL, Key.F)
await tab.keyboard.press(Key.ESCAPE)  # Might be too fast
```

### 2. Focus Elements Before Typing

```python
from pydoll.constants import Key

# Good: Ensure element is focused
input_field = await tab.find(id='search')
await input_field.click()  # Focus it
await input_field.insert_text('query')

# Bad: Keyboard input goes to wrong element
await tab.keyboard.press(Key.A)  # Where does this go?
```

### 3. Use Platform-Aware Shortcuts

```python
import sys
from pydoll.constants import Key

# Good: Platform-aware
cmd_key = Key.META if sys.platform == 'darwin' else Key.CONTROL
await tab.keyboard.hotkey(cmd_key, Key.C)

# Bad: Hardcoded (won't work on macOS)
await tab.keyboard.hotkey(Key.CONTROL, Key.C)
```

### 4. Clean Up Long Sequences

```python
from pydoll.constants import Key

# Good: Ensure modifiers are released
try:
    await tab.keyboard.down(Key.SHIFT)
    await tab.keyboard.press(Key.ARROWRIGHT)
    # ... more operations
finally:
    await tab.keyboard.up(Key.SHIFT)  # Always release

# Bad: Modifier stays pressed on error
await tab.keyboard.down(Key.SHIFT)
await tab.keyboard.press(Key.ARROWRIGHT)
# Error here leaves Shift pressed!
```

## Key Reference Tables

### Common Page-Level Shortcuts (These Work!)

| Action | Windows/Linux | macOS | Notes |
|--------|--------------|-------|-------|
| Copy | Ctrl+C | Cmd+C | Works |
| Paste | Ctrl+V | Cmd+V | Works |
| Cut | Ctrl+X | Cmd+X | Works |
| Undo | Ctrl+Z | Cmd+Z | Works |
| Redo | Ctrl+Y | Cmd+Y | Works |
| Select All | Ctrl+A | Cmd+A | Works |
| Find | Ctrl+F | Cmd+F | Only if web app implements it |
| Save | Ctrl+S | Cmd+S | Only if web app implements it |
| Refresh | F5 or Ctrl+R | Cmd+R | Use `await tab.refresh()` instead |

### Browser Shortcuts (These DON'T Work via CDP)

| Action | Shortcut | Use Instead |
|--------|----------|-------------|
| New Tab | Ctrl+T | `await browser.new_tab()` |
| Close Tab | Ctrl+W | `await tab.close()` |
| Reopen Tab | Ctrl+Shift+T | Track tabs manually |
| DevTools | F12, Ctrl+Shift+I | Already available via CDP! |
| Address Bar | Ctrl+L | `await tab.go_to(url)` |

### All Available Keys

| Category | Keys |
|----------|------|
| **Letters** | `Key.A` through `Key.Z` (26 keys) |
| **Numbers** | `Key.DIGIT0` through `Key.DIGIT9` (10 keys) |
| **Numpad** | `Key.NUMPAD0` through `Key.NUMPAD9`, `NUMPADMULTIPLY`, `NUMPADADD`, `NUMPADSUBTRACT`, `NUMPADDECIMAL`, `NUMPADDIVIDE` |
| **Function** | `Key.F1` through `Key.F12` (12 keys) |
| **Navigation** | `ARROWUP`, `ARROWDOWN`, `ARROWLEFT`, `ARROWRIGHT`, `HOME`, `END`, `PAGEUP`, `PAGEDOWN` |
| **Modifiers** | `CONTROL`, `SHIFT`, `ALT`, `META` |
| **Special** | `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `DELETE`, `ESCAPE`, `INSERT` |
| **Locks** | `CAPSLOCK`, `NUMLOCK`, `SCROLLLOCK` |
| **Symbols** | `SEMICOLON`, `EQUALSIGN`, `COMMA`, `MINUS`, `PERIOD`, `SLASH`, `GRAVEACCENT`, `BRACKETLEFT`, `BACKSLASH`, `BRACKETRIGHT`, `QUOTE` |

### Modifier Flag Values

| Modifier | Value | Binary | Usage |
|----------|-------|--------|-------|
| Alt | 1 | 0001 | `modifiers=1` |
| Ctrl | 2 | 0010 | `modifiers=2` |
| Meta | 4 | 0100 | `modifiers=4` |
| Shift | 8 | 1000 | `modifiers=8` |
| Ctrl+Shift | 10 | 1010 | `modifiers=10` |
| Ctrl+Alt | 3 | 0011 | `modifiers=3` |
| Ctrl+Shift+Alt | 11 | 1011 | `modifiers=11` |

## Migration from WebElement Methods

Previous keyboard methods on `WebElement` are deprecated. Here's how to migrate:

### Old vs New

```python
from pydoll.constants import Key

# Old (deprecated)
element = await tab.find(id='input')
await element.key_down(Key.A, modifiers=2)
await element.key_up(Key.A)
await element.press_keyboard_key(Key.ENTER)

# New (recommended)
await tab.keyboard.down(Key.A, modifiers=2)
await tab.keyboard.up(Key.A)
await tab.keyboard.press(Key.ENTER)
```

!!! warning "Deprecation Notice"
    The following `WebElement` methods are deprecated:

    - `key_down()` → Use `tab.keyboard.down()`
    - `key_up()` → Use `tab.keyboard.up()`
    - `press_keyboard_key()` → Use `tab.keyboard.press()`
    
    These methods still work for backward compatibility but will show deprecation warnings.

### Why Migrate?

- **Centralized**: All keyboard operations in one place
- **Cleaner API**: Consistent interface for all keyboard actions
- **More powerful**: Hotkey support, smart modifier detection
- **Better typed**: Full IDE autocomplete support

## Learn More

For additional automation capabilities:

- **[Human Interactions](human-interactions.md)**: Realistic clicking, scrolling, and mouse movement
- **[Form Handling](form-handling.md)**: Complete form automation workflows
- **[File Operations](file-operations.md)**: File upload automation

The Keyboard API eliminates the complexity of keyboard automation, providing clean, reliable methods for everything from simple key presses to complex shortcuts and sequences.
