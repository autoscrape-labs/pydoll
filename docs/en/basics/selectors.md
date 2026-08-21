# Selectors: CSS and XPath

A selector is the string you hand to `tab.query()` (and to the `selector=` in extraction models) to point at an element. Pydoll speaks two selector languages, CSS and XPath, and picks the right engine for you: if the string starts with `/` or `./` it runs as XPath, otherwise as a CSS selector. This page teaches enough of both to find anything on a page.

You only need selectors for `query()`. The `find()` method takes plain attributes instead (see [Element finding](../guides/element-finding.md)); reach for a selector when you want a relationship `find()` can't express.

Try it: type a selector below and the matching elements light up. It runs the same `querySelectorAll` / XPath the browser does, so what matches here matches in your automation.

<iframe src="../selector-playground.html" aria-label="Type a CSS or XPath selector and see which elements it matches" style="width: 100%; height: 500px; border: 0;" loading="lazy"></iframe>

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        # CSS: the article title, by its id
        title = await tab.query('#firstHeading')
        print(await title.text)

        # XPath: the first link whose href mentions python.org
        link = await tab.query("//a[contains(@href, 'python.org')]")
        print(link.get_attribute('href'))

asyncio.run(main())
```

Both queries above ran through the same `query()` call. Pydoll saw the leading `//` on the second one and treated it as XPath.

## When to use which

Most of the time CSS is enough, and it reads more naturally. Reach for XPath when you need something CSS cannot do.

- **CSS** selects by id, class, tag, attribute, and position, and moves downward and sideways through the page. It is the shorter, more familiar language.
- **XPath** does all of that and also matches on visible text, walks *upward* to a parent or ancestor, and expresses conditions like "the row that contains this text". If you need to find an element by its text or navigate from a child back up to a container, that is an XPath job.

A rough rule: start in CSS, switch to XPath the moment you catch yourself wanting to say "the element whose text is X" or "the parent of Y".

## CSS reference

The snippets below assume a started `tab`. Pass `find_all=True` to any of them to get a list instead of the first match.

### Select by id, class, and tag

```python
await tab.query('div')             # first <div>
await tab.query('#username')       # element with id="username"
await tab.query('.submit-btn')     # first element with class="submit-btn"
await tab.query('.btn.primary')    # element with both classes
await tab.query('input')           # first <input>
```

### Combinators

Combinators describe relationships between elements.

```python
await tab.query('nav a')           # any <a> inside a <nav>, at any depth
await tab.query('nav > a')         # <a> that is a direct child of <nav>
await tab.query('h1 + p')          # <p> immediately after an <h1>
await tab.query('h1 ~ p')          # first <p> that follows an <h1> as a sibling
```

### Attribute selectors

```python
await tab.query('input[required]')            # has the attribute
await tab.query("input[type='email']")        # attribute equals a value
await tab.query("a[href^='https://']")        # value starts with
await tab.query("img[src$='.png']")           # value ends with
await tab.query("a[href*='wikipedia']")       # value contains
```

### Pseudo-classes

Pseudo-classes select by position or state.

```python
await tab.query('li:first-child')             # first <li> among its siblings
await tab.query('li:nth-child(2)')            # the second <li>
await tab.query('tr:nth-child(odd)', find_all=True)  # every odd row
await tab.query('input:checked')              # a checked checkbox or radio
await tab.query('button:not([disabled])')     # a button without the disabled attribute
```

## XPath reference

### Paths

```python
await tab.query('//div')           # any <div>, anywhere
await tab.query('//nav/a')         # <a> that is a direct child of a <nav>
await tab.query('//nav//a')        # <a> anywhere inside a <nav>
await tab.query('(//div)[1]')      # the first <div> in the document
await tab.query('//ul/li[last()]') # the last <li> in a <ul>
```

### Match on attributes and text

This is where you need XPath. CSS cannot select by visible text; XPath can.

```python
await tab.query("//input[@type='email']")            # attribute equals
await tab.query("//input[@type='text' and @required]")  # two conditions
await tab.query("//button[text()='Submit']")         # exact text
await tab.query("//p[contains(text(), 'welcome')]")  # partial text
await tab.query("//a[starts-with(@href, 'https://')]")  # attribute starts with
```

!!! tip "Normalize text before matching"
    Rendered text often carries stray whitespace. `//button[normalize-space(text())='Submit']` collapses runs of spaces and trims the ends, so it matches even when the HTML has ragged indentation.

### Axes: move in any direction

An axis says which direction to travel from the current node. This is XPath's advantage: you can go up to a parent or across to a sibling, which CSS cannot.

| Axis | Direction | Finds |
|------|-----------|-------|
| `parent::` | up | the immediate parent |
| `ancestor::` | up | any ancestor, at any depth |
| `following-sibling::` | sideways | siblings after this node |
| `preceding-sibling::` | sideways | siblings before this node |
| `child::` | down | direct children |
| `descendant::` | down | any descendant |

Shorthands you will see often: `//div/p` is `//div/child::p`, `@id` is `attribute::id`, and `..` is `parent::node()`.

```python
await tab.query("//input[@name='email']/parent::div")   # up to the wrapping div
await tab.query('//button/ancestor::form')              # up to the enclosing form
await tab.query("//label[text()='Email:']/following-sibling::input")  # the input next to a label
```

## Worked examples

These use the sample form below. It shows the patterns you hit most in real pages: finding an element by the text next to it, and walking from a control up to its row.

```html
<form id="signup">
  <div class="field">
    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required>
    <span class="error" style="display:none;">Invalid email</span>
  </div>
  <div class="field">
    <input type="checkbox" id="newsletter" name="newsletter">
    <label for="newsletter">Subscribe to the newsletter</label>
  </div>
  <button type="submit">Save</button>
  <button type="button">Cancel</button>
</form>
```

### Find an input by its label

You know the label text, not the input's id. Find the label, then step sideways to the input:

```python
email = await tab.query("//label[text()='Email:']/following-sibling::input")
```

### Find the error message next to a field

```python
error = await tab.query("//input[@id='email']/following-sibling::span[@class='error']")
if await error.is_visible():
    print('Email was rejected')
```

`is_visible()` reports whether the element is actually shown, which matters here because the span starts hidden.

### Tell the two buttons apart

The submit button is the one with `type='submit'`, so you never rely on its position:

```python
save = await tab.query("button[type='submit']")          # CSS is enough here
save = await tab.query("//button[text()='Save']")        # or match the label text
```

### Read a checkbox's label

The `for` attribute ties a label to its control, so you can jump straight to it:

```python
label = await tab.query("//label[@for='newsletter']")
print(await label.text)   # "Subscribe to the newsletter"
```

### Walk from a control up to its row

In a table, you often have a button and want the row it lives in. Query from the element with an XPath that climbs the tree:

```python
delete = await tab.query("//tr[@data-product-id='101']//button[@class='delete']")

row = await delete.query('./ancestor::tr')
print(row.get_attribute('data-product-id'))   # "101", get_attribute is not awaited
```

`get_attribute()` reads a value synchronously from the element you already located, so it takes no `await`.

## Build selectors from variables

When the value you match on comes from your program, build the string with an f-string. Escape any quotes in the value so they do not break the expression:

```python
async def row_for(tab, product_name):
    safe = product_name.replace("'", "\\'")
    return await tab.query(f"//tr[td[text()='{safe}']]")


laptop_row = await row_for(tab, 'Laptop')
```

## Keep selectors stable

Pick attributes a redesign is unlikely to touch, and lean on the simplest expression that works.

```python
# stable: names and ids survive layout changes
await tab.query('#signup')
await tab.query("[data-testid='save-button']")
await tab.query("input[name='email']")

# fragile: position-based chains break when the markup shifts
await tab.query('div > div > div:nth-child(3) > input')
```

CSS is marginally faster than XPath for simple lookups, but the difference is milliseconds per query and rarely worth optimizing for. Choose the selector that reads clearly and survives page changes.

## What's next

- [Element finding](../guides/element-finding.md): use these selectors with `query()`, and the attribute-based `find()`.
- [DOM traversal](../guides/dom-traversal.md): navigate the tree from an element you already have.
- [Structured extraction](../guides/structured-extraction.md): put these selectors in a model's `Field(selector=...)` to pull typed data.
