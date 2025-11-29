# Python's Type System & Pydoll

Pydoll leverages Python's type system extensively to provide excellent IDE support, catch errors early, and make the API self-documenting. This guide explains the basics of type hints and how Pydoll uses them to enhance your development experience.

## Type Hints Basics

Type hints are optional annotations that specify what type of value a variable, parameter, or return value should be. They don't affect runtime behavior but enable powerful tooling.

### Simple Type Hints

```python
# Basic types
name: str = "Pydoll"
port: int = 9222
is_headless: bool = False
quality: float = 0.85

# Function annotations
def navigate(url: str, timeout: int = 30) -> bool:
    # ... implementation
    return True
```

### Container Types

```python
from typing import List, Dict, Optional

# Lists and dictionaries
urls: List[str] = ['https://example.com', 'https://google.com']
headers: Dict[str, str] = {'User-Agent': 'MyBot/1.0'}

# Optional values (can be None)
target_id: Optional[str] = None

# Modern syntax (Python 3.9+)
urls: list[str] = ['https://example.com']
headers: dict[str, str] = {'User-Agent': 'MyBot/1.0'}
```

!!! tip "Python 3.9+ Syntax"
    Pydoll's codebase uses the older `List[]`, `Dict[]` syntax for backward compatibility, but you can use lowercase `list[]`, `dict[]` in your code if you're on Python 3.9+.

## TypedDict: Structured Dictionaries

TypedDict allows you to define dictionary structures with specific keys and value types. This is **heavily used** in Pydoll's CDP protocol definitions.

### Basic TypedDict

```python
from typing import TypedDict

class UserInfo(TypedDict):
    name: str
    age: int
    email: str

# IDE knows exactly what keys exist
user: UserInfo = {
    'name': 'Alice',
    'age': 30,
    'email': 'alice@example.com'
}

# Autocomplete works!
print(user['name'])  # IDE suggests: name, age, email
```

### How Pydoll Uses TypedDict

Pydoll defines **every CDP command, response, and event** as a TypedDict. This means your IDE knows exactly what properties are available:

```python
# From pydoll/protocol/page/methods.py
class CaptureScreenshotParams(TypedDict, total=False):
    """Parameters for captureScreenshot."""
    format: ScreenshotFormat
    quality: int
    clip: Viewport
    fromSurface: bool
    captureBeyondViewport: bool
    optimizeForSpeed: bool

class CaptureScreenshotResult(TypedDict):
    """Result for captureScreenshot command."""
    data: str
```

When you call methods that return CDP responses, your IDE autocompletes the response keys:

```python
async def example():
    response = await tab.take_screenshot(as_base64=True)
    
    # IDE knows this is CaptureScreenshotResponse
    # and suggests 'result' -> 'data'
    screenshot_data = response['result']['data']  # Full autocomplete!
```

### Optional vs Required Fields

TypedDict supports optional fields using `NotRequired[]`:

```python
from typing import TypedDict, NotRequired

# From pydoll/protocol/network/methods.py
class GetCookiesParams(TypedDict):
    """Parameters for retrieving browser cookies."""
    urls: NotRequired[list[str]]  # This field is optional
```

The `total=False` flag makes **all** fields optional:

```python
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat  # All fields optional
    quality: int
    clip: Viewport
```

!!! info "Autocomplete Magic"
    When you type `response['`, your IDE shows you all available keys with their types. This is TypedDict's superpower in action!

## Enums: Type-Safe Constants

Enums provide type-safe constants that your IDE can autocomplete. Pydoll uses them extensively for CDP values.

### Basic Enums

```python
from enum import Enum

class ScreenshotFormat(str, Enum):
    JPEG = 'jpeg'
    PNG = 'png'
    WEBP = 'webp'

# IDE autocompletes available formats
format = ScreenshotFormat.PNG  # Type is ScreenshotFormat
print(format.value)  # 'png'
```

### Pydoll's Enum Usage

```python
from pydoll.constants import Key
from pydoll.protocol.page.types import ScreenshotFormat
from pydoll.protocol.input.types import KeyModifier

# Finding elements - uses kwargs, not enums
element = await tab.find(id='submit-btn')
element = await tab.find(class_name='btn-primary')
element = await tab.find(tag_name='button')

# Keyboard input - IDE suggests all keys
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB)
await element.press_keyboard_key(Key.ESCAPE)

# Modifiers are integer enums (for special keys)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# Screenshot format enum
await tab.take_screenshot('file.webp', format=ScreenshotFormat.WEBP)
```

!!! tip "Enum Autocomplete"
    Type `Key.` or `ScreenshotFormat.` and your IDE shows all available options. No more memorizing strings!

## Function Overloads

Overloads allow a function to return different types based on its parameters. Pydoll uses this to provide precise type information.

### Basic Overload Example

```python
from typing import overload

# Overload signatures (not executed)
@overload
def process(data: str) -> str: ...

@overload
def process(data: int) -> int: ...

# Actual implementation
def process(data):
    return data * 2

# IDE knows return types
result1 = process("hello")  # Type: str
result2 = process(42)       # Type: int
```

### Pydoll's Overload Usage

The `find()` and `query()` methods return different types depending on the `find_all` parameter:

```python
# From pydoll/elements/mixins/find_elements_mixin.py
class FindElementsMixin:
    @overload
    async def find(
        self, find_all: Literal[False] = False, **kwargs
    ) -> WebElement: ...
    
    @overload
    async def find(
        self, find_all: Literal[True], **kwargs
    ) -> list[WebElement]: ...
    
    async def find(
        self, find_all: bool = False, **kwargs
    ) -> Union[WebElement, list[WebElement]]:
        # Implementation...
```

In your code:

```python
# find_all=False (default) - IDE knows return type is WebElement
button = await tab.find(id='submit-btn')
await button.click()  # Single element methods available!

# find_all=True - IDE knows return type is list[WebElement]
buttons = await tab.find(class_name='btn', find_all=True)
for btn in buttons:  # IDE knows this is a list!
    await btn.click()

# Same with query()
element = await tab.query('#submit-btn')  # Type: WebElement
elements = await tab.query('.btn', find_all=True)  # Type: list[WebElement]
```

!!! tip "Smart Type Inference"
    Your IDE automatically knows whether you're getting a single element or a list based on the `find_all` parameter. No casting or type assertions needed!

## Generic Types

Generics are like "type containers" that work with different types while preserving type information. Think of them as templates that adapt to whatever you put inside.

### Understanding Generics: A Simple Analogy

Imagine a `Box` that can hold anything. Without generics:

```python
# Without generics - IDE doesn't know what's inside
class Box:
    def __init__(self, content):
        self.content = content
    
    def get(self):
        return self.content

my_box = Box("hello")
item = my_box.get()  # Type: Unknown - could be anything!
```

With generics:

```python
from typing import Generic, TypeVar

T = TypeVar('T')  # T is a "type placeholder"

class Box(Generic[T]):
    def __init__(self, content: T):
        self.content = content
    
    def get(self) -> T:
        return self.content

# Now IDE knows exactly what's inside each box
string_box: Box[str] = Box("hello")
item1 = string_box.get()  # Type: str

number_box: Box[int] = Box(42)
item2 = number_box.get()  # Type: int

# List is a built-in generic
numbers: list[int] = [1, 2, 3]  # List that contains ints
names: list[str] = ["Alice", "Bob"]  # List that contains strings
```

!!! tip "Generics Simplify Type Hints"
    Instead of writing `Union[List[str], List[int], List[float], ...]` for every possible list type, generics let you write one reusable `list[T]` that adapts to whatever you put inside.

### Real-World Generic Example

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Response(Generic[T]):
    """A generic API response wrapper."""
    def __init__(self, data: T, status: int):
        self.data = data
        self.status = status
    
    def get_data(self) -> T:
        return self.data

# Each response preserves its data type
user_response: Response[dict] = Response({"name": "Alice"}, 200)
user_data = user_response.get_data()  # Type: dict

count_response: Response[int] = Response(42, 200)
count = count_response.get_data()  # Type: int
```

### How Pydoll Uses Generics

Pydoll's CDP command system uses generics to ensure the response type matches the command:

```python
# From pydoll/protocol/base.py
from typing import Generic, TypeVar

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')

class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """Base structure for all commands."""
    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]

class Response(TypedDict, Generic[T_CommandResponse]):
    """Base structure for all responses."""
    id: int
    result: T_CommandResponse
```

This means when you execute a command, the response type is automatically inferred:

```python
# PageCommands.navigate returns Command[NavigateParams, NavigateResult]
command = PageCommands.navigate('https://example.com')

# ConnectionHandler.execute_command preserves the generic type
response = await connection_handler.execute_command(command)

# IDE knows response['result'] is NavigateResult (not just "any dict")
frame_id = response['result']['frameId']  # Autocomplete works!
loader_id = response['result']['loaderId']  # All fields are known!
```

!!! info "Why Generics Matter in Pydoll"
    Without generics, every CDP response would just be typed as `dict[str, Any]`, and you'd lose all autocomplete. With generics, the IDE knows the exact structure of each response based on which command you sent.

## Union Types

Unions represent values that could be one of several types:

```python
from typing import Union

# Can be string or int
identifier: Union[str, int] = "user-123"
identifier = 456  # Also valid

# Modern syntax (Python 3.10+)
identifier: str | int = "user-123"
```

### Pydoll's Union Usage

```python
# File paths can be strings or Path objects
from pathlib import Path

async def upload_file(files: Union[str, Path, list[Union[str, Path]]]):
    # Handles multiple input types
    pass

# All of these work:
await tab.expect_file_chooser('/path/to/file.txt')
await tab.expect_file_chooser(Path('/path/to/file.txt'))
await tab.expect_file_chooser(['/file1.txt', Path('/file2.txt')])
```

## Practical Benefits in Pydoll

### 1. Intelligent Autocomplete

Your IDE suggests available keys, methods, and values:

```python
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.network.types import ResourceType
from pydoll.protocol.input.types import KeyModifier
from pydoll.constants import Key

# Autocomplete for event names
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, callback)

# Autocomplete for resource types
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)

# Autocomplete for keys
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# Autocomplete for kwargs in find()
element = await tab.find(id='submit-btn')  # IDE suggests: id, class_name, tag_name, etc.
```

### 2. Catch Errors Early

Type checkers like mypy or Pylance catch errors before runtime:

```python
# Type checker catches this
await tab.take_screenshot('file.png', quality='high')  # Error: quality must be int

# Type checker catches this
event = await tab.find(id='button')
await tab.on(event, callback)  # Error: event is WebElement, not str

# Correct
await tab.take_screenshot('file.png', quality=90)
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
```

### 3. Self-Documenting Code

Types serve as inline documentation:

```python
# You immediately know what each parameter expects
async def take_screenshot(
    self,
    path: Optional[str] = None,
    quality: int = 100,
    beyond_viewport: bool = False,
    as_base64: bool = False,
) -> Optional[str]:
    pass
```

### 4. CDP Response Navigation

Navigate complex CDP responses with confidence:

```python
# From pydoll/protocol/browser/methods.py
class GetVersionResult(TypedDict):
    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str

# In your code
version_info = await browser.get_version()

# IDE suggests all available keys
print(version_info['product'])         # Autocomplete!
print(version_info['userAgent'])       # Autocomplete!
print(version_info['protocolVersion']) # Autocomplete!
```

## Type Checking Your Code

### Using Pylance (VS Code)

Pylance provides real-time type checking in VS Code:

1. Install the Pylance extension
2. Set type checking mode in settings:

```json
{
    "python.analysis.typeCheckingMode": "basic"  // or "strict"
}
```

Now you get instant feedback:

```python
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Pylance shows parameter types as you type
        await tab.go_to('https://example.com', timeout=30)
        
        # Pylance warns about wrong types
        await tab.take_screenshot(quality='high')  # Warning!
```

### Using mypy

Run mypy to check your entire project:

```bash
pip install mypy
mypy your_script.py
```

Example output:

```
your_script.py:10: error: Argument "quality" to "take_screenshot" has incompatible type "str"; expected "int"
Found 1 error in 1 file (checked 1 source file)
```

## Pydoll's Protocol Type System

Pydoll's `protocol/` directory contains comprehensive type definitions for the entire Chrome DevTools Protocol:

```
pydoll/protocol/
├── base.py              # Generic Command, Response, CDPEvent types
├── browser/
│   ├── events.py        # BrowserEvent enum, event parameter TypedDicts
│   ├── methods.py       # Browser method enums, parameter/result TypedDicts
│   └── types.py         # Browser domain types (Bounds, PermissionType, etc.)
├── dom/
│   ├── events.py        # DOM event definitions
│   ├── methods.py       # DOM command definitions
│   └── types.py         # DOM types (Node, BackendNode, etc.)
├── page/
│   ├── events.py        # Page events (LOAD_EVENT_FIRED, etc.)
│   ├── methods.py       # Page methods (navigate, captureScreenshot, etc.)
│   └── types.py         # Page types (Frame, ScreenshotFormat, etc.)
├── network/
│   └── ...              # Network domain types
└── ...                  # Other CDP domains
```

### Example: Complete Type Flow

Let's trace a complete type flow from command to response:

```python
# 1. Method enum (protocol/page/methods.py)
class PageMethod(str, Enum):
    CAPTURE_SCREENSHOT = 'Page.captureScreenshot'

# 2. Parameter TypedDict (protocol/page/methods.py)
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat
    quality: int
    clip: Viewport

# 3. Result TypedDict (protocol/page/methods.py)
class CaptureScreenshotResult(TypedDict):
    data: str

# 4. Command creation (commands/page_commands.py)
class PageCommands:
    @staticmethod
    def capture_screenshot(
        format: Optional[ScreenshotFormat] = None,
        quality: Optional[int] = None,
        ...
    ) -> Command[CaptureScreenshotParams, CaptureScreenshotResult]:
        return {
            'method': PageMethod.CAPTURE_SCREENSHOT,
            'params': {...}
        }

# 5. Usage in Tab (browser/tab.py)
class Tab:
    async def take_screenshot(...) -> Optional[str]:
        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(...)
        )
        screenshot_data = response['result']['data']  # Fully typed!
        return screenshot_data
```

Every step maintains type information, giving you autocomplete and type checking throughout!

## Best Practices

### 1. Let Pydoll's Types Guide You

Don't fight the types, they're there to help:

```python
# Good: Use kwargs (IDE autocompletes parameter names)
element = await tab.find(id='submit-btn')
button = await tab.find(class_name='btn-primary')

# Good: Use enums where applicable
from pydoll.constants import Key
await element.press_keyboard_key(Key.ENTER)

# Avoid: Magic strings
await element.press_keyboard_key('Enter')  # No autocomplete, error-prone
```

### 2. Explore Types in Your IDE

Hover over variables to see their types:

```python
# Hover over 'response' to see: Response[CaptureScreenshotResult]
response = await tab._execute_command(PageCommands.capture_screenshot(...))

# Hover over 'data' to see: str
data = response['result']['data']
```


### 3. Don't Over-Annotate

Python's type inference is smart, don't annotate everything:

```python
# Too much
name: str = "Alice"
count: int = 5
is_active: bool = True

# Let Python infer simple literals
name = "Alice"
count = 5
is_active = True

# Annotate when type isn't obvious
from typing import Optional

result: Optional[WebElement] = await tab.find(id='missing', raise_exc=False)
```

## Learn More

For deeper understanding of Python's type system and CDP protocol:

- **[Python typing documentation](https://docs.python.org/3/library/typing.html)**: Official Python typing reference
- **[PEP 484](https://peps.python.org/pep-0484/)**: The original type hints proposal
- **[Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)**: CDP documentation
- **[Deep Dive: CDP](./cdp.md)**: How Pydoll implements CDP
- **[API Reference: Protocol](../api/protocol/base.md)**: Pydoll's protocol type definitions

The type system transforms Pydoll from a simple automation library into a **type-safe, self-documenting, IDE-friendly** framework. It catches bugs before they happen and makes exploring the API a breeze!

