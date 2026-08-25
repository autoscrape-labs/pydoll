# Element finding

Locating elements is the foundation of every automation. Pydoll gives you two ways to do it: `find()`, where you describe the element by its HTML attributes, and `query()`, where you pass a CSS selector or XPath. Both wait for the element to appear, so you never write manual `sleep` loops.

Edit the attributes below and watch `find()` locate the element live. Pydoll turns the attributes you pass into a selector for you, and the matching element lights up.

<iframe scrolling="no" src="/docs/resources/visuals/element-find-playground.html" aria-label="Edit find() attributes and see which element it locates" style="width: 100%; height: 365px; border: 0;" loading="lazy"></iframe>

## Find by attributes

`find()` is the everyday tool. You pass the attributes you'd use to describe the element to a person, and Pydoll builds the selector for you.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quote = await tab.find(class_name='quote')
        text = await quote.find(class_name='text')
        author = await quote.find(class_name='author')
        print(f'{await author.text}: {await text.text}')

asyncio.run(main())
```

You can locate an element by any of these attributes. Each of these returns the first match:

```python
await tab.find(id='username')        # by id
await tab.find(class_name='quote')   # by class name
await tab.find(tag_name='h1')        # by tag name
await tab.find(name='username')      # by name attribute
await tab.find(text='Login')         # by visible text
```

## Combine attributes for precision

Pass several attributes and `find()` matches the element that has **all** of them (an AND). Use underscores for hyphenated attribute names: `data-testid` becomes `data_testid`, `aria-label` becomes `aria_label`.

```python
# an <input type="password" name="password">
password = await tab.find(tag_name='input', type='password', name='password')

# a <button class="btn" type="submit">
submit = await tab.find(tag_name='button', class_name='btn', type='submit')

# a data attribute
card = await tab.find(tag_name='div', data_testid='product-card')
```

For OR logic (the element might have one attribute or another), chain two calls with `raise_exc=False`, shown under [Handle missing elements](#handle-missing-elements).

## Find every match

Pass `find_all=True` to get a list of every matching element instead of the first one:

```python
await tab.go_to('https://books.toscrape.com')

books = await tab.find(class_name='product_pod', find_all=True)
print(f'{len(books)} books on this page')

for book in books:
    title = await book.find(tag_name='h3')
    price = await book.find(class_name='price_color')
    print(await title.text, await price.text)
```

## Wait for elements that load late

Modern pages render content after the initial load. Pass `timeout` (in seconds) and `find()` polls until the element appears or the time runs out. You don't add `sleep` calls; the wait is built in.

```python
# wait up to 10 seconds for a late-loading element
content = await tab.find(class_name='dynamic-content', timeout=10)
```

!!! tip "Pick timeouts deliberately"
    Too short and you miss slow elements; too long and you wait on things that will never appear. Five to ten seconds fits most dynamic content. For an element that is only sometimes present, pair a short timeout with `raise_exc=False` (below).

## Find by CSS selector or XPath

When you already have a selector, or need a relationship `find()` can't express, use `query()`. It auto-detects CSS versus XPath.

```python
# CSS
submit = await tab.query("button[type='submit']")
required = await tab.query('input[required]', find_all=True)
nested = await tab.query('div.container > .content .item:nth-child(2)')

# XPath: text matching and relationships CSS can't reach
button = await tab.query("//button[contains(text(), 'Submit')]")
label_input = await tab.query("//label[text()='Email:']/following-sibling::input")
```

`query()` takes the same `find_all`, `timeout`, and `raise_exc` parameters as `find()`. For when to reach for CSS versus XPath, see [Selectors: CSS and XPath](../basics/selectors.md).

## Search within an element

Every element supports `find()` and `query()` scoped to its own subtree, which is how you work with repeating structures like cards or rows. A scoped search looks through **all** descendants of the element, not only its direct children, matching how `querySelector` behaves.

```python
await tab.go_to('https://books.toscrape.com')

book = await tab.find(class_name='product_pod')

title = await book.find(tag_name='h3')          # anywhere inside this book
price = await book.find(class_name='price_color')
cover = await book.query('img.thumbnail')
```

To navigate the DOM tree deliberately (direct children only, siblings, shadow roots), see [DOM traversal](dom-traversal.md).

## Handle missing elements {#handle-missing-elements}

By default `find()` raises `ElementNotFound` when nothing matches. Pass `raise_exc=False` to get `None` instead, which keeps optional elements and OR logic in your hands.

```python
from pydoll.exceptions import ElementNotFound

# required element: let it raise
submit = await tab.find(id='submit')

# optional element: handle the None
banner = await tab.find(class_name='promo-banner', timeout=2, raise_exc=False)
if banner:
    close = await banner.find(class_name='close')
    await close.click()

# OR logic: try one attribute, then another
checkbox = (
    await tab.find(id='terms', raise_exc=False)
    or await tab.find(name='accept_terms', raise_exc=False)
)
```

## Prefer stable selectors

Choose attributes a redesign is unlikely to change. Your DOM structure shifts often, so selectors that depend on it break easily.

```python
# semantic and stable: survives a redesign
await tab.find(id='user-profile')
await tab.find(data_testid='submit-button')
await tab.find(name='username')

# tied to structure: breaks the moment the layout shifts
await tab.query('div > div > div:nth-child(3) > input')
```

Reach for the simplest selector that works, and only add complexity when the page forces it. Use `find()` for attribute-based lookups and `query()` for CSS or XPath patterns `find()` can't express.

## Complete example: log in and read the result

This logs in on [quotes.toscrape.com](https://quotes.toscrape.com/login) (which accepts any credentials) and confirms the result by finding the Logout link.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com/login')

        username = await tab.find(id='username')
        await username.type_text('tester', humanize=True)

        password = await tab.find(id='password')
        await password.type_text('secret', humanize=True)

        submit = await tab.find(tag_name='input', type='submit')
        await submit.click()

        logout = await tab.find(text='Logout', timeout=5, raise_exc=False)
        print('Logged in.' if logout else 'Login failed.')

asyncio.run(main())
```

## What's next

- [DOM traversal](dom-traversal.md): navigate from an element to its children, siblings, and shadow roots.
- [Selectors: CSS and XPath](../basics/selectors.md): choose and write the right selector.
- [Structured extraction](structured-extraction.md): pull typed data from many elements at once with a model.
