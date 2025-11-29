# FindElements Mixin Architecture

The FindElementsMixin represents a critical architectural decision in Pydoll: using **composition over inheritance** to share element-finding capabilities between `Tab` and `WebElement` without coupling them through a common base class. This document explores the mixin pattern, its implementation, and the internal mechanics of element location.

!!! info "Practical Usage Guide"
    For practical examples and usage patterns, see the [Element Finding Guide](../features/automation/element-finding.md) and [Selectors Guide](./selectors-guide.md).

## Mixin Pattern: Design Philosophy

### What is a Mixin?

A mixin is a class designed to **provide methods to other classes** without being a base class in a traditional inheritance hierarchy. Unlike standard inheritance (which models "is-a" relationships), mixins model **"can-do" capabilities**.

```python
# Traditional inheritance: "is-a"
class Animal:
    def breathe(self): ...

class Dog(Animal):  # Dog IS-A Animal
    def bark(self): ...

# Mixin pattern: "can-do"
class FlyableMixin:
    def fly(self): ...

class Bird(Animal, FlyableMixin):  # Bird IS-A Animal, CAN fly
    pass
```

### Why Mixins Over Inheritance?

Pydoll faces a specific architectural challenge:

- **`Tab`** needs to find elements in the **document context**
- **`WebElement`** needs to find elements **relative to itself** (child elements)
- Both need **identical selector logic** (CSS, XPath, attribute building)

**Option 1: Shared Base Class**

```python
class ElementLocator:
    def find(...): ...

class Tab(ElementLocator):
    pass

class WebElement(ElementLocator):
    pass
```

**Problems:**
- Tight coupling: `Tab` and `WebElement` now share inheritance hierarchy
- Violates Single Responsibility: `Tab` shouldn't inherit from same class as `WebElement`
- Hard to extend: Adding new capabilities requires modifying base class

**Option 2: Mixin Pattern (Chosen Approach)**

```python
class FindElementsMixin:
    def find(...): ...
    def query(...): ...

class Tab(FindElementsMixin):
    # Tab-specific logic
    pass

class WebElement(FindElementsMixin):
    # WebElement-specific logic
    pass
```

**Benefits:**

- **Decoupling**: `Tab` and `WebElement` remain independent
- **Reusability**: Same element-finding logic in both classes
- **Composability**: Can add other mixins without conflicts
- **Testability**: Mixin can be tested in isolation

!!! tip "Mixin Characteristics"
    1. **Stateless**: Mixins don't maintain their own state (no `__init__`)
    2. **Dependency Injection**: Assumes consuming class provides dependencies (e.g., `_connection_handler`)
    3. **Single Purpose**: Each mixin provides one cohesive capability
    4. **Not Instantiable**: Never create `FindElementsMixin()` directly

## Mixin Implementation in Pydoll

### Class Structure

The FindElementsMixin uses **dependency injection** to work with any class that provides a `_connection_handler`:

```python
class FindElementsMixin:
    """
    Mixin providing element finding capabilities.
    
    Assumes the consuming class has:
    - _connection_handler: ConnectionHandler instance for CDP commands
    - _object_id: Optional[str] for context-relative searches (WebElement only)
    """
    
    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler  # Type hint, not actual attribute
    
    async def find(self, ...):
        # Implementation uses self._connection_handler
        # Checks for self._object_id to determine context
```

**Key insight:** The mixin doesn't define `_connection_handler` or `_object_id`. It **assumes** they exist via duck typing.

### How Tab and WebElement Use the Mixin

```python
# Tab: Document-level searches
class Tab(FindElementsMixin):
    def __init__(self, browser, target_id, connection_port):
        self._connection_handler = ConnectionHandler(connection_port)
        # No _object_id → searches from document root

# WebElement: Element-relative searches
class WebElement(FindElementsMixin):
    def __init__(self, object_id, connection_handler, ...):
        self._object_id = object_id  # CDP object ID
        self._connection_handler = connection_handler
        # Has _object_id → searches relative to this element
```

**Critical distinction:**

- **Tab**: `hasattr(self, '_object_id')` → `False` → uses `RuntimeCommands.evaluate()` (document context)
- **WebElement**: `hasattr(self, '_object_id')` → `True` → uses `RuntimeCommands.call_function_on()` (element context)

### Context Detection

The mixin dynamically detects search context:

```python
async def _find_element(self, by, value, raise_exc=True):
    if hasattr(self, '_object_id'):
        # Relative search: call JavaScript function on THIS element
        command = self._get_find_element_command(by, value, self._object_id)
    else:
        # Document search: evaluate JavaScript in global context
        command = self._get_find_element_command(by, value)
    
    response = await self._execute_command(command)
    # ...
```

This single implementation handles both:

- `tab.find(id='submit')` → searches entire document
- `form_element.find(id='submit')` → searches within `form_element`

!!! warning "Mixin Dependency Coupling"
    The mixin is **tightly coupled** to CDP's object model. It assumes:
    
    - Elements are represented by `objectId` strings
    - `Runtime.evaluate()` for document searches
    - `Runtime.callFunctionOn()` for element-relative searches
    
    This is acceptable because Pydoll is **CDP-specific**. A more generic design would require abstraction layers.

## Public API Design

The mixin exposes two high-level methods with distinct design philosophies:

### find(): Attribute-Based Selection

```python
@overload
async def find(self, find_all: Literal[False], ...) -> WebElement: ...

@overload
async def find(self, find_all: Literal[True], ...) -> list[WebElement]: ...

async def find(
    self,
    id: Optional[str] = None,
    class_name: Optional[str] = None,
    name: Optional[str] = None,
    tag_name: Optional[str] = None,
    text: Optional[str] = None,
    timeout: int = 0,
    find_all: bool = False,
    raise_exc: bool = True,
    **attributes,
) -> Union[WebElement, list[WebElement], None]:
```

**Design decisions:**

1. **Kwargs over positional By enum**:
   ```python
   # Pydoll (intuitive)
   await tab.find(id='submit', class_name='primary')
   
   # Selenium (verbose)
   driver.find_element(By.ID, 'submit')  # Can't combine attributes easily
   ```

2. **Auto-resolution to optimal selector**:
   - Single attribute → uses `By.ID`, `By.CLASS_NAME`, etc. (fastest)
   - Multiple attributes → builds XPath (flexible but slower)

3. **`**attributes` for extensibility**:
   ```python
   await tab.find(data_testid='submit-btn', aria_label='Submit form')
   # Builds: //\*[@data-testid='submit-btn' and @aria-label='Submit form']
   ```

### query(): Expression-Based Selection

```python
@overload
async def query(self, expression, find_all: Literal[False], ...) -> WebElement: ...

@overload
async def query(self, expression, find_all: Literal[True], ...) -> list[WebElement]: ...

async def query(
    self, 
    expression: str, 
    timeout: int = 0, 
    find_all: bool = False, 
    raise_exc: bool = True
) -> Union[WebElement, list[WebElement], None]:
```

**Design decisions:**

1. **Auto-detect CSS vs XPath**:
   ```python
   # XPath detection (starts with / or ./)
   await tab.query("//div[@id='content']")
   
   # CSS detection (default)
   await tab.query("div#content > p.intro")
   ```

2. **Single expression parameter** (unlike `find()`):
   - Assumes user knows selector syntax
   - No abstraction overhead

3. **Direct passthrough to browser**:
   - `querySelector()` / `querySelectorAll()` for CSS
   - `document.evaluate()` for XPath

### Overload Pattern for Type Safety

Both methods use `@overload` to provide **precise return types**:

```python
# IDE knows return type is WebElement
element = await tab.find(id='submit')

# IDE knows return type is list[WebElement]
elements = await tab.find(class_name='item', find_all=True)

# IDE knows return type is Optional[WebElement]
maybe_element = await tab.find(id='optional', raise_exc=False)
```

This is critical for IDE autocomplete and type checking. See [Type System Deep Dive](./typing-system.md) for details.

## Selector Resolution Architecture

The mixin converts user input into CDP commands through a resolution pipeline:

| Stage | Input | Output | Key Decision |
|-------|-------|--------|-------------|
| **1. Method Selection** | `find()` kwargs or `query()` expression | Selector strategy | Attribute-based vs expression-based |
| **2. Strategy Resolution** | Attributes or expression | `By` enum + value | Single attr → native method, Multiple → XPath |
| **3. Context Detection** | `By` + value + `hasattr(_object_id)` | CDP command type | Document vs element-relative search |
| **4. Command Generation** | CDP command type + selector | JavaScript + CDP method | `evaluate()` vs `callFunctionOn()` |
| **5. Execution** | CDP command | `objectId` or array of `objectId`s | Via ConnectionHandler |
| **6. WebElement Creation** | `objectId` + attributes | `WebElement` instance(s) | Factory function to avoid circular imports |

### Key Architectural Decisions

**1. Single vs Multiple Attributes**

```python
# Single attribute → Direct selector (fast)
await tab.find(id='username')  # Uses By.ID → getElementById()

# Multiple attributes → XPath (flexible)
await tab.find(tag_name='input', type='password', name='pwd')
# → //input[@type='password' and @name='pwd']
```

**Why this matters:**
- Native methods (`getElementById`, `getElementsByClassName`) are 10-50% faster than XPath
- XPath overhead is acceptable when combining attributes (no alternative)

**2. Auto-Detection of Selector Type**

```python
await tab.query("//div")       # Starts with / → XPath
await tab.query("#login")      # Default → CSS
```

**Implementation:**
```python
if expression.startswith(('./', '/', '(/')):
    return By.XPATH
return By.CSS_SELECTOR
```

Heuristic is **unambiguous** - CSS selectors cannot start with `/`.

**3. XPath Relative Path Adjustment**

For element-relative searches, absolute XPath must be converted:

```python
# User provides: //div
# For WebElement: .//div (relative to element, not document)

def _ensure_relative_xpath(xpath):
    return f'.{xpath}' if not xpath.startswith('.') else xpath
```

Without this, `element.find()` would search from document root.

## CDP Command Generation

The mixin routes to different CDP methods based on search context:

| Context | Selector Type | CDP Method | JavaScript Equivalent |
|---------|--------------|------------|---------------------|
| Document | CSS | `Runtime.evaluate` | `document.querySelector()` |
| Document | XPath | `Runtime.evaluate` | `document.evaluate()` |
| Element | CSS | `Runtime.callFunctionOn` | `this.querySelector()` |
| Element | XPath | `Runtime.callFunctionOn` | `document.evaluate(..., this)` |

**Key insight:** `Runtime.callFunctionOn` requires an `objectId` (the element to call on), while `Runtime.evaluate` executes in global scope.

### JavaScript Templates

Pydoll uses pre-defined templates for consistency and performance:

```python
# CSS selectors
Scripts.QUERY_SELECTOR = 'document.querySelector("{selector}")'
Scripts.RELATIVE_QUERY_SELECTOR = 'this.querySelector("{selector}")'

# XPath expressions
Scripts.FIND_XPATH_ELEMENT = '''
    document.evaluate("{escaped_value}", document, null,
                      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
'''
```

Templates avoid runtime string concatenation and centralize JavaScript code.

## Object ID Resolution and WebElement Creation

CDP represents DOM nodes as **`objectId` strings**. The mixin abstracts this:

**Single element flow:**
1. Execute CDP command → Extract `objectId` from response
2. Call `DOM.describeNode(objectId)` → Get attributes, tag name
3. Create `WebElement(objectId, connection_handler, attributes)`

**Multiple elements flow:**
1. Execute CDP command → Returns **array as single remote object**
2. Call `Runtime.getProperties(array_objectId)` → Enumerate array indices
3. Extract individual `objectId` for each element
4. Describe and create `WebElement` for each

**Why `Runtime.getProperties`?** CDP doesn't return arrays directly - it returns a **reference to an array object**. We must enumerate its properties to extract individual elements.

## Architectural Insights and Design Tradeoffs

### Why Kwargs Instead of By Enum?

**Pydoll's choice:**
```python
await tab.find(id='submit', class_name='primary')
```

**Selenium's approach:**
```python
driver.find_element(By.ID, 'submit')  # Can't combine attributes
```

**Rationale:**

- **Discoverability**: IDE autocomplete shows all available parameters
- **Composability**: Can combine multiple attributes in one call
- **Readability**: `id='submit'` is more intuitive than `(By.ID, 'submit')`

**Tradeoff:** Kwargs are less explicit about selector strategy. Solved by documentation and logging.

### Why Auto-Detect CSS vs XPath?

The `_get_expression_type()` heuristic eliminates user burden:

```python
await tab.query("//div")       # Auto: XPath
await tab.query("#login")      # Auto: CSS
await tab.query("div > p")     # Auto: CSS
```

**Benefits:**

- **Ergonomics**: Users don't need to specify selector type
- **Correctness**: Impossible to misuse (XPath with CSS method, vice versa)

**Limitation:** No way to force CSS interpretation of ambiguous selectors (rare edge case).

### Circular Import Prevention: create_web_element()

The mixin uses a **factory function** to avoid circular imports:

```python
def create_web_element(*args, **kwargs):
    """Dynamically import WebElement at runtime."""
    from pydoll.elements.web_element import WebElement  # Late import
    return WebElement(*args, **kwargs)
```

**Why needed?**

- `FindElementsMixin` → needs to create `WebElement`
- `WebElement` → inherits from `FindElementsMixin`
- Circular dependency!

**Solution:** Late import inside factory function. Import only executes when function is called, breaking the cycle.

### hasattr() for Context Detection: Elegant or Hacky?

The mixin uses `hasattr(self, '_object_id')` to detect Tab vs WebElement:

```python
if hasattr(self, '_object_id'):
    # WebElement: element-relative search
else:
    # Tab: document-level search
```

**Is this "hacky"?**

- **No**: It's **duck typing** (Pythonic idiom)
- Mixin doesn't need to know class hierarchy
- Both Tab and WebElement provide `_connection_handler`
- WebElement additionally provides `_object_id`

**Alternative approaches:**

1. **Type checking**: `if isinstance(self, WebElement)` → Couples mixin to WebElement
2. **Abstract method**: Requires Tab/WebElement to implement `get_search_context()` → More boilerplate
3. **Dependency injection**: Pass context as parameter → Breaks API ergonomics

**Verdict:** `hasattr()` is the best solution for this use case.

## Key Takeaways

1. **Mixins enable code sharing** without coupling `Tab` and `WebElement` through inheritance
2. **Context detection via duck typing** (`hasattr`) keeps mixin decoupled from class hierarchy
3. **Auto-resolution optimizes performance** by using native methods for single attributes
4. **XPath building provides composability** for multi-attribute queries
5. **Polling-based waiting is simple** but trades CPU cycles for implementation simplicity
6. **CDP object model complexity** is hidden behind WebElement abstraction
7. **Type safety via overloads** provides precise return types for IDE support

## Related Documentation

For deeper understanding of related architectural components:

- **[Type System](./typing-system.md)**: Overload pattern, TypedDict, Generic types
- **[WebElement Domain](./webelement-domain.md)**: WebElement architecture and interaction methods
- **[Selectors Guide](./selectors-guide.md)**: CSS vs XPath syntax and best practices
- **[Tab Domain](./tab-domain.md)**: Tab-level operations and context management

For practical usage patterns:

- **[Element Finding Guide](../features/automation/element-finding.md)**: Practical examples and patterns
- **[Human-Like Interactions](../features/automation/human-interactions.md)**: Realistic element interaction