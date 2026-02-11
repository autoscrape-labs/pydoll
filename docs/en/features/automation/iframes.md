# Working with IFrames

Modern web pages embed content from other documents using `<iframe>`. In previous versions of Pydoll you had to convert an iframe into a `Tab` using `tab.get_frame()` and keep track of CDP targets manually. **That is no longer necessary.**  
An iframe nowadays behaves like any other `WebElement`: you can call `find()`, `query()`, `execute_script()`, `inner_html`, `text`, and all element helpers directly—Pydoll will transparently execute the request inside the correct browsing context.

!!! info "Simpler mental model"
    Treat an iframe exactly like a div: locate it once and use it as the starting point for new element searches. Pydoll handles cross-origin frames, isolated execution contexts, and nested frames behind the scenes.

## Quick Start

### Interact with the first iframe on the page

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def interact_with_iframe():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/page-with-iframe')

        iframe = await tab.find(tag_name='iframe', id='content-frame')

        # These methods execute inside the iframe automatically
        title = await iframe.find(tag_name='h1')
        await title.click()

        form = await iframe.find(id='login-form')
        username = await form.find(name='username')
        await username.type_text('john_doe')

asyncio.run(interact_with_iframe())
```

### Nested iframes

Need to reach a frame inside another frame? Chain your searches:

```python
outer = await tab.find(id='outer-frame')
inner = await outer.find(tag_name='iframe')   # Search inside the outer iframe

submit_button = await inner.find(id='submit')
await submit_button.click()
```

The algorithm is always the same:

1. Find the iframe element.
2. Use that `WebElement` to continue searching.
3. Repeat for deeper levels if required.

There is no need to cache frame targets or create additional `Tab` instances.

### Execute JavaScript in an iframe

```python
iframe = await tab.find(tag_name='iframe')
result = await iframe.execute_script('return document.title', return_by_value=True)
print(result['result']['result']['value'])
```

Pydoll automatically runs the script within the iframe’s isolated execution context (cross-origin and same-origin frames work the same way).

## Why this is better

- **Intuitive:** what you see in the DOM tree is what you code—if you can select the `iframe` element, you can interact with everything inside it.
- **Cross-origin friendly:** Pydoll spins up an isolated world for you; no more manual target resolution.
- **Nested by design:** each search is scoped to the element you call it on, so deep hierarchies stay manageable.
- **No API split:** you do not have to switch between `Tab` and `WebElement` methods—one set of primitives is enough.

!!! tip "Deprecation notice"
    `Tab.get_frame()` now emits a `DeprecationWarning` and will be removed in a future release. Update existing snippets to work directly with iframe elements as shown above.

## Frequently used patterns

### Take a screenshot from inside an iframe

```python
iframe = await tab.find(tag_name='iframe')
chart = await iframe.find(id='sales-chart')
await chart.take_screenshot('chart.png')
```


## Cross-iframe Selectors

Instead of manually finding each iframe and then searching inside it, you can write a **single selector** that crosses iframe boundaries. Pydoll automatically detects `iframe` steps in your XPath or CSS selector, splits them into segments, and walks the iframe chain for you.

### CSS selectors

Use any standard combinator (`>`, space) after an `iframe` compound:

```python
# Single iframe crossing
button = await tab.query('iframe > .submit-btn')

# With attribute selectors on the iframe
button = await tab.query('iframe[src*="checkout"] > #pay-button')

# Nested iframes
element = await tab.query('iframe.outer > iframe.inner > div.content')

# Multiple steps after the iframe
link = await tab.query('iframe > nav > a.home-link')

# Iframe inside another element (not at root)
button = await tab.query('div > iframe > button.submit')
content = await tab.query('.wrapper iframe > div.content')
```

### XPath expressions

Use `/` after an `iframe` step — Pydoll splits at the iframe node:

```python
# Single iframe crossing
button = await tab.query('//iframe/body/button[@id="submit"]')

# Iframe inside another element (not at root)
div = await tab.query('//div/iframe/div')
item = await tab.query('//div[@class="wrapper"]/iframe/body/div')

# With predicates on the iframe
heading = await tab.query('//iframe[@src*="cloudflare"]//h1')

# Nested iframes
element = await tab.query('//iframe[@id="outer"]//iframe[@id="inner"]//div')
```

### How it works

When Pydoll encounters a selector like `iframe[src*="checkout"] > form > button`:

1. **Parses** the selector into segments: `iframe[src*="checkout"]` and `form > button`
2. **Finds** the iframe element using the first segment
3. **Searches inside** the iframe using the second segment
4. For nested iframes, repeats the process at each boundary

This is equivalent to the manual approach but in a single call:

```python
# Manual (still works)
iframe = await tab.find(tag_name='iframe', src='*checkout*')
button = await iframe.query('form > button')

# Automatic (same result, one line)
button = await tab.query('iframe[src*="checkout"] > form > button')
```

### When splitting does NOT happen

Selectors are only split when `iframe` appears as a **tag name**. These selectors pass through unchanged:

- `.iframe > body` — class selector, not a tag
- `#iframe > body` — ID selector
- `div.iframe > body` — tag is `div`, not `iframe`
- `[data-type="iframe"] > body` — attribute selector
- `iframe` or `//iframe` — no content after iframe (nothing to search inside)

### find_all support

The last segment respects `find_all=True`, returning all matching elements inside the final iframe:

```python
# Get all links inside an iframe
links = await tab.query('iframe > a', find_all=True)
```

## Best practices

- **Use the iframe element as scope:** call `find`, `query`, or other helpers on the iframe itself.
- **Avoid `tab.find` for inner content:** it only sees the top-level document.
- **Remember partial results:** if you need the same iframe repeatedly, store the `WebElement` reference; Pydoll keeps the underlying context cached.
- **Keep existing element workflows:** everything that works for a normal element (scrolling, screenshot, scripts, waiting) works for an iframe element too.

## Further reading

- **[Element Finding](../element-finding.md)** – covers scoped searches and chaining.
- **[Screenshots & PDFs](screenshots-and-pdfs.md)** – details about capturing visual output.
- **[Event System](../advanced/event-system.md)** – reactively monitor page activity, including frames.

Once you adapt to the new model, iframes become just another part of the DOM tree. Focus on building your automation logic—Pydoll takes care of the frame plumbing for you.
