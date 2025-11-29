# CSS Selectors vs XPath: A Complete Guide

When using the `query()` method, you have two powerful selector languages at your disposal: CSS Selectors and XPath. Understanding when and how to use each is crucial for effective element location.

## Fundamental Differences

| Aspect | CSS Selector | XPath |
|--------|--------------|-------|
| **Syntax** | Simple, CSS-like | XML path language |
| **Performance** | Faster (native browser support) | Slightly slower |
| **Direction** | Only traverses down and sideways | Can traverse in any direction |
| **Text Matching** | Limited (pseudo-selectors) | Powerful text functions |
| **Complexity** | Best for simple to moderate cases | Excels at complex relationships |
| **Readability** | More intuitive for web developers | Steeper learning curve |

## When to Use CSS Selectors

CSS selectors are ideal for:

- Simple element selection by ID, class, or tag
- Direct parent-child relationships
- Attribute matching with simple patterns
- Performance-critical scenarios
- When traversing downward in the DOM

```python
# Clean and performant CSS examples
await tab.query("#login-form")
await tab.query(".submit-button")
await tab.query("div.container > p.intro")
await tab.query("input[type='email'][required]")
await tab.query("ul.menu li:first-child")
```

## When to Use XPath

XPath is ideal for:

- Complex text matching and partial text searches
- Traversing upward to parent elements
- Finding elements relative to siblings
- Conditional logic in selectors
- Complex DOM relationships

```python
# Powerful XPath examples
await tab.query("//button[contains(text(), 'Submit')]")
await tab.query("//input[@name='email']/parent::div")
await tab.query("//td[text()='John']/following-sibling::td[2]")
await tab.query("//div[contains(@class, 'product') and @data-price > 100]")
```

## CSS Selector Syntax Reference

### Basic Selectors

```python
# Element selector
await tab.query("div")              # First <div> element
await tab.query("div", find_all=True)  # All <div> elements
await tab.query("button")           # First <button> element

# ID selector
await tab.query("#username")        # Element with id="username"

# Class selector
await tab.query(".submit-btn")      # First element with class="submit-btn"
await tab.query(".submit-btn", find_all=True)  # All elements with class
await tab.query(".btn.primary")     # First element with both classes

# Universal selector
await tab.query("*", find_all=True) # All elements
```

### Combinators

```python
# Descendant combinator (space)
await tab.query("div p")            # First <p> inside <div>
await tab.query("div p", find_all=True)  # All <p> inside <div> (any depth)

# Child combinator (>)
await tab.query("div > p")          # First <p> that is direct child of <div>
await tab.query("div > p", find_all=True)  # All <p> that are direct children

# Adjacent sibling combinator (+)
await tab.query("h1 + p")           # <p> immediately after <h1>

# General sibling combinator (~)
await tab.query("h1 ~ p")           # First <p> sibling after <h1>
await tab.query("h1 ~ p", find_all=True)  # All <p> siblings after <h1>
```

### Attribute Selectors

```python
# Attribute exists
await tab.query("input[required]")                # First input with 'required'
await tab.query("input[required]", find_all=True) # All inputs with 'required'

# Attribute equals
await tab.query("input[type='email']")            # First email input
await tab.query("input[type='email']", find_all=True)  # All email inputs

# Attribute contains word
await tab.query("div[class~='active']")           # First div with 'active' class

# Attribute starts with
await tab.query("a[href^='https://']")            # First HTTPS link
await tab.query("a[href^='https://']", find_all=True)  # All HTTPS links

# Attribute ends with
await tab.query("img[src$='.png']")               # First PNG image
await tab.query("img[src$='.png']", find_all=True)     # All PNG images

# Attribute contains substring
await tab.query("a[href*='example']")             # First link with 'example'
await tab.query("a[href*='example']", find_all=True)   # All links with 'example'

# Case-insensitive matching
await tab.query("input[type='text' i]")           # Case-insensitive match
```

### Pseudo-Classes

```python
# Structural pseudo-classes
await tab.query("li:first-child")                 # First <li> that is first child
await tab.query("li:last-child")                  # First <li> that is last child
await tab.query("li:nth-child(2)")                # First <li> that is 2nd child
await tab.query("li:nth-child(odd)", find_all=True)  # All odd-numbered <li>
await tab.query("li:nth-child(even)", find_all=True)  # All even-numbered <li>
await tab.query("li:nth-child(3n)", find_all=True)    # Every 3rd <li>

# Type-based pseudo-classes
await tab.query("p:first-of-type")                # First <p> among siblings
await tab.query("p:last-of-type")                 # Last <p> among siblings
await tab.query("p:nth-of-type(2)")               # Second <p> among siblings

# State pseudo-classes
await tab.query("input:enabled")                  # First enabled input
await tab.query("input:enabled", find_all=True)   # All enabled inputs
await tab.query("input:disabled")                 # First disabled input
await tab.query("input:checked")                  # First checked checkbox/radio
await tab.query("input:focus")                    # Currently focused input

# Other useful pseudo-classes
await tab.query("div:empty")                      # First empty element
await tab.query("div:empty", find_all=True)       # All empty elements
await tab.query("div:not(.exclude)")              # First div without class
await tab.query("div:not(.exclude)", find_all=True)  # All divs without class
```

## XPath Syntax Reference

### Basic Path Expressions

```python
# Absolute path (from root)
await tab.query("/html/body/div")                 # First div at exact path

# Relative path (from anywhere)
await tab.query("//div")                          # First <div> element
await tab.query("//div", find_all=True)           # All <div> elements
await tab.query("//div/p")                        # First <p> inside any <div>
await tab.query("//div/p", find_all=True)         # All <p> inside any <div>

# Current node
await tab.query("./div")                          # First <div> relative to current

# Parent node
await tab.query("..")                             # Parent of current node
```

### Attribute Selection

```python
# Basic attribute matching
await tab.query("//input[@type='email']")         # First email input
await tab.query("//input[@type='email']", find_all=True)  # All email inputs
await tab.query("//div[@id='content']")           # Div with id='content'

# Multiple attributes
await tab.query("//input[@type='text' and @required]")  # First match
await tab.query("//input[@type='text' and @required]", find_all=True)  # All matches
await tab.query("//div[@class='card' or @class='panel']")  # First card or panel

# Attribute exists
await tab.query("//button[@disabled]")            # First disabled button
await tab.query("//button[@disabled]", find_all=True)  # All disabled buttons
```

## XPath Axes (Directional Navigation)

The real power of XPath comes from its ability to navigate in any direction through the DOM tree.

### Axes Reference Table

| Axis | Direction | Description | Example |
|------|-----------|-------------|---------|
| `child::` | Down | Direct children only | `//div/child::p` |
| `descendant::` | Down | All descendants (any depth) | `//div/descendant::a` |
| `parent::` | Up | Immediate parent | `//input/parent::div` |
| `ancestor::` | Up | All ancestors (any depth) | `//span/ancestor::div` |
| `following-sibling::` | Sideways | Siblings after current | `//h1/following-sibling::p` |
| `preceding-sibling::` | Sideways | Siblings before current | `//p/preceding-sibling::h1` |
| `following::` | Forward | All nodes after current | `//h1/following::*` |
| `preceding::` | Backward | All nodes before current | `//h1/preceding::*` |
| `ancestor-or-self::` | Up | Ancestors + current | `//div/ancestor-or-self::*` |
| `descendant-or-self::` | Down | Descendants + current | `//div/descendant-or-self::*` |
| `self::` | Current | Current node only | `//div/self::div` |
| `attribute::` | Attribute | Attributes of current | `//div/attribute::class` |

!!! info "Shorthand Syntax"
    - `//div` is short for `//descendant-or-self::div`
    - `//div/p` is short for `//div/child::p`
    - `@id` is short for `attribute::id`
    - `..` is short for `parent::node()`

### Practical Axis Examples

```python
# Navigate to parent
await tab.query("//input[@name='email']/parent::div")
await tab.query("//span[@class='error']/..")       # Shorthand

# Find ancestor
await tab.query("//input/ancestor::form")          # First ancestor <form>
await tab.query("//button/ancestor::div[@class='modal']")

# Sibling navigation
await tab.query("//label[text()='Email:']/following-sibling::input")
await tab.query("//h2/following-sibling::p[1]")    # First <p> after <h2>
await tab.query("//h2/following-sibling::p", find_all=True)  # All <p> after <h2>
await tab.query("//button/preceding-sibling::input[last()]")

# Complex relationships
await tab.query("//tr/td[1]/following-sibling::td[2]")  # 3rd cell in first row
await tab.query("//tr/td[1]/following-sibling::td[2]", find_all=True)  # 3rd cell in all rows
```

## XPath Functions

### Text Functions

```python
# Exact text match
await tab.query("//button[text()='Submit']")

# Contains text
await tab.query("//p[contains(text(), 'welcome')]")

# Starts with
await tab.query("//a[starts-with(@href, 'https://')]")

# Text normalization (removes extra whitespace)
await tab.query("//button[normalize-space(text())='Submit']")

# String length
await tab.query("//input[string-length(@value) > 5]")

# Concatenation
await tab.query("//div[concat(@data-first, @data-last)='JohnDoe']")
```

### Numeric Functions

```python
# Position matching
await tab.query("//li[position()=1]")              # First <li>
await tab.query("//li[position() > 3]", find_all=True)  # All <li> after 3rd
await tab.query("//li[last()]")                    # Last <li>
await tab.query("//li[last()-1]")                  # Second to last

# Counting
await tab.query("//ul[count(li) > 5]")             # First <ul> with more than 5 items
await tab.query("//ul[count(li) > 5]", find_all=True)  # All <ul> with > 5 items

# Numeric operations
await tab.query("//div[@data-price > 100]")        # First div with price > 100
await tab.query("//div[@data-price > 100]", find_all=True)  # All divs
await tab.query("//div[number(@data-stock) = 0]")  # First with stock = 0
```

### Boolean Functions

```python
# Boolean logic
await tab.query("//div[@visible='true' and @enabled='true']")  # First match
await tab.query("//input[@type='text' or @type='email']")  # First text or email
await tab.query("//input[@type='text' or @type='email']", find_all=True)  # All
await tab.query("//button[not(@disabled)]")        # First enabled button
await tab.query("//button[not(@disabled)]", find_all=True)  # All enabled buttons

# Existence checks
await tab.query("//div[child::p]")                 # First div with <p> children
await tab.query("//div[child::p]", find_all=True)  # All divs with <p> children
await tab.query("//div[not(child::*)]")            # First empty div
await tab.query("//div[not(child::*)]", find_all=True)  # All empty divs
```

## XPath Predicates

Predicates filter node sets using conditions in square brackets `[]`.

```python
# Position predicates
await tab.query("(//div)[1]")                      # First <div> in document
await tab.query("(//div)[last()]")                 # Last <div> in document
await tab.query("//ul/li[3]")                      # First 3rd <li> in a <ul>
await tab.query("//ul/li[3]", find_all=True)       # All 3rd <li> in each <ul>

# Multiple predicates (AND logic)
await tab.query("//input[@type='text'][@required]")  # First match
await tab.query("//div[@class='product'][position() < 4]", find_all=True)  # First 3

# Attribute predicates
await tab.query("//div[@data-id='123']")
await tab.query("//a[contains(@class, 'button')]")  # First matching link
await tab.query("//input[starts-with(@name, 'user')]")  # First matching input
```

## Real-World Examples: Complex Element Finding

Let's work with a realistic HTML structure to demonstrate advanced selectors.

### Sample HTML Structure

```html
<div class="dashboard">
    <header>
        <h1>User Dashboard</h1>
        <nav class="menu">
            <a href="/home" class="active">Home</a>
            <a href="/profile">Profile</a>
            <a href="/settings">Settings</a>
        </nav>
    </header>
    
    <main>
        <section class="products">
            <h2>Available Products</h2>
            <table id="products-table">
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr data-product-id="101">
                        <td>Laptop</td>
                        <td class="price">$999</td>
                        <td class="stock">15</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="102">
                        <td>Mouse</td>
                        <td class="price">$25</td>
                        <td class="stock">0</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete" disabled>Delete</button>
                        </td>
                    </tr>
                    <tr data-product-id="103">
                        <td>Keyboard</td>
                        <td class="price">$75</td>
                        <td class="stock">8</td>
                        <td>
                            <button class="btn-edit">Edit</button>
                            <button class="btn-delete">Delete</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section class="user-form">
            <h2>User Information</h2>
            <form id="user-form">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                    <span class="error-message" style="display:none;">Invalid username</span>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                    <span class="error-message" style="display:none;">Invalid email</span>
                </div>
                <div class="form-group">
                    <input type="checkbox" id="newsletter" name="newsletter">
                    <label for="newsletter">Subscribe to newsletter</label>
                </div>
                <button type="submit" class="btn-primary">Save Changes</button>
                <button type="button" class="btn-secondary">Cancel</button>
            </form>
        </section>
    </main>
</div>
```

### Challenge 1: Find Active Navigation Link

**Goal**: Find the currently active navigation link.

```python
# CSS Selector
active_link = await tab.query("nav.menu a.active")

# XPath
active_link = await tab.query("//nav[@class='menu']//a[@class='active']")

# Get its text
text = await active_link.text
print(text)  # "Home"
```

### Challenge 2: Find Edit Button for Specific Product

**Goal**: Find the Edit button for the product "Mouse" (without knowing its row position).

```python
# XPath (recommended for this case)
edit_button = await tab.query(
    "//tr[td[text()='Mouse']]//button[contains(@class, 'btn-edit')]"
)

# Alternative: Using following-sibling
edit_button = await tab.query(
    "//td[text()='Mouse']/following-sibling::td//button[@class='btn-edit']"
)
```

!!! tip "Why XPath Here?"
    CSS selectors can't traverse upward to find the row and then back down to the button. XPath's ability to move freely through the DOM makes this trivial.

### Challenge 3: Find All Products with Price Over $50

**Goal**: Get all table rows where the price is greater than $50.

```python
# XPath with numeric comparison
expensive_products = await tab.query(
    "//tr[number(translate(td[@class='price'], '$,', '')) > 50]",
    find_all=True
)

# More readable version: using contains for simpler cases
# This finds products with price containing specific amounts
products = await tab.query("//tr[contains(td[@class='price'], '$75')]", find_all=True)
```

!!! note "Text to Number Conversion"
    The `translate()` function removes `$` and `,` characters, then `number()` converts to numeric for comparison.

### Challenge 4: Find All Out-of-Stock Products

**Goal**: Find all products where stock is 0.

```python
# XPath
out_of_stock = await tab.query(
    "//tr[td[@class='stock' and text()='0']]",
    find_all=True
)

# Alternative: Find all rows and check stock
rows = await tab.query("//tbody/tr[td[@class='stock']/text()='0']", find_all=True)
```

### Challenge 5: Find Input Field by Its Label

**Goal**: Find the email input by locating its label first.

```python
# XPath using label's 'for' attribute
email_input = await tab.query("//label[text()='Email:']/following-sibling::input")

# Alternative: Using the for attribute
email_input = await tab.query("//input[@id=(//label[text()='Email:']/@for)]")

# More generic: Find by label text
username_input = await tab.query(
    "//label[contains(text(), 'Username')]/following-sibling::input"
)
```

### Challenge 6: Find Error Message Next to Email Field

**Goal**: Get the error message span that appears next to the email input.

```python
# XPath - find error sibling of email input
error_span = await tab.query(
    "//input[@id='email']/following-sibling::span[@class='error-message']"
)

# Alternative: Navigate from parent div
error_span = await tab.query(
    "//input[@id='email']/parent::div//span[@class='error-message']"
)

# Check visibility
is_visible = await error_span.is_visible()
```

### Challenge 7: Find Submit Button (Not Cancel)

**Goal**: Find the submit button, excluding the cancel button.

```python
# CSS Selector (simple)
submit_button = await tab.query("button[type='submit']")
submit_button = await tab.query("button.btn-primary")

# XPath with text
submit_button = await tab.query("//button[text()='Save Changes']")

# XPath excluding others
submit_button = await tab.query(
    "//button[@type='submit' and not(@class='btn-secondary')]"
)
```

### Challenge 8: Find All Required Form Fields

**Goal**: Get all required input fields in the form.

```python
# CSS Selector (clean)
required_fields = await tab.query(
    "#user-form input[required]",
    find_all=True
)

# XPath
required_fields = await tab.query(
    "//form[@id='user-form']//input[@required]",
    find_all=True
)

# Verify
for field in required_fields:
    field_name = await field.get_attribute("name")
    print(f"Required: {field_name}")
```

### Challenge 9: Find First Non-Disabled Delete Button

**Goal**: Find the first delete button that is not disabled.

```python
# CSS Selector
first_enabled_delete = await tab.query("button.btn-delete:not([disabled])")

# XPath
first_enabled_delete = await tab.query(
    "//button[contains(@class, 'btn-delete') and not(@disabled)]"
)

# Get all enabled delete buttons
all_enabled = await tab.query(
    "//button[@class='btn-delete' and not(@disabled)]",
    find_all=True
)
```

### Challenge 10: Find Table Row by Multiple Conditions

**Goal**: Find products with stock > 0 AND price < $100.

```python
# XPath with complex logic
available_affordable = await tab.query(
    """
    //tr[
        number(td[@class='stock']) > 0 
        and 
        number(translate(td[@class='price'], '$', '')) < 100
    ]
    """,
    find_all=True
)

# For each matching product
for row in available_affordable:
    cells = await row.query("td", find_all=True)
    product_name = await cells[0].text
    print(f"Available: {product_name}")
```

### Challenge 11: Navigate Complex Relationships

**Goal**: From a delete button, get the product name in the same row.

```python
# Start with a delete button
delete_button = await tab.query("//tr[@data-product-id='101']//button[@class='btn-delete']")

# Navigate to parent row, then to first cell
product_name_cell = await delete_button.query("./ancestor::tr/td[1]")
product_name = await product_name_cell.text
print(product_name)  # "Laptop"

# Alternative: Get the entire row first
row = await delete_button.query("./ancestor::tr")
product_id = await row.get_attribute("data-product-id")
print(product_id)  # "101"
```

### Challenge 12: Find Checkbox and Its Label Together

**Goal**: Find the newsletter checkbox and verify its label.

```python
# Find checkbox
checkbox = await tab.query("#newsletter")

# Get associated label using 'for' attribute
label = await tab.query("//label[@for='newsletter']")
label_text = await label.text
print(label_text)  # "Subscribe to newsletter"

# Alternative: Navigate from checkbox to label
label = await checkbox.query("//following::label[@for='newsletter']")

# Check if checked
is_checked = await checkbox.is_checked()
```

## Advanced Pattern: Dynamic Selector Building

When dealing with dynamic content, you might need to build selectors programmatically:

```python
async def find_product_by_name(tab, product_name: str):
    """Find a product row by its name dynamically."""
    # Escape quotes in product name to prevent XPath injection
    safe_name = product_name.replace("'", "\\'")
    
    xpath = f"//tr[td[text()='{safe_name}']]"
    return await tab.query(xpath)

async def find_table_cell(tab, row_text: str, column_index: int):
    """Find a specific cell by row content and column position."""
    xpath = f"//tr[td[contains(text(), '{row_text}')]]/td[{column_index}]"
    return await tab.query(xpath)

# Usage
product_row = await find_product_by_name(tab, "Laptop")
price_cell = await find_table_cell(tab, "Laptop", 2)
price = await price_cell.text
print(price)  # "$999"
```

## Performance Comparison

```python
import asyncio
import time

async def benchmark_selectors(tab):
    """Compare CSS vs XPath performance."""
    
    # Warm up
    await tab.query("#products-table")
    
    # Benchmark CSS
    start = time.time()
    for _ in range(100):
        await tab.query("#products-table tbody tr", find_all=True)
    css_time = time.time() - start
    
    # Benchmark XPath
    start = time.time()
    for _ in range(100):
        await tab.query("//table[@id='products-table']//tbody//tr", find_all=True)
    xpath_time = time.time() - start
    
    print(f"CSS: {css_time:.3f}s")
    print(f"XPath: {xpath_time:.3f}s")
    print(f"CSS is {xpath_time/css_time:.2f}x faster")

# Typical results: CSS is 1.2-1.5x faster for simple selectors
```

!!! warning "Performance vs Readability"
    While CSS selectors are generally faster, the difference is usually negligible (milliseconds) for individual queries. Choose the selector that makes your code more readable and maintainable, especially for complex relationships where XPath excels.

## Selector Best Practices

### 1. Prefer Stable Selectors

```python
# Good: Using semantic attributes
await tab.query("#user-email")
await tab.query("[data-testid='submit-button']")
await tab.query("input[name='username']")

# Avoid: Brittle selectors based on structure
await tab.query("div > div > div:nth-child(3) > input")
await tab.query("body > div:nth-child(2) > form > div:first-child")
```

### 2. Use the Simplest Selector That Works

```python
# Good: Simple and efficient
await tab.query("#login-form")
await tab.query(".submit-button")

# Avoid: Over-complicated when unnecessary
await tab.query("//div[@id='content']/descendant::form[@id='login-form']")
```

### 3. Combine find() and query() Appropriately

```python
# Use find() for simple attribute matching
username = await tab.find(id="username")
submit = await tab.find(tag_name="button", type="submit")

# Use query() for complex patterns
active_link = await tab.query("nav.menu a.active")
error_msg = await tab.query("//input[@name='email']/following-sibling::span[@class='error']")
```

### 4. Add Comments for Complex Selectors

```python
# Find the "Edit" button in the row containing product "Laptop"
# XPath: Navigate to row with "Laptop" text, then find edit button
edit_button = await tab.query(
    "//tr[td[text()='Laptop']]//button[@class='btn-edit']"
)
```

## Conclusion

By understanding both CSS selectors and XPath, along with their respective strengths and use cases, you can create robust and maintainable browser automation that handles the complexities of modern web applications. Remember:

- **Use CSS selectors** for simple, performance-critical selections
- **Use XPath** for complex relationships, text matching, and upward navigation
- **Choose stability** over brevity when writing selectors
- **Comment complex queries** to maintain code readability

For more information about how these selectors are used internally by Pydoll, see the [FindElements Mixin](find-elements-mixin.md) documentation.

