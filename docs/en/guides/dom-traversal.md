# DOM traversal

Once you have an element, you often need the ones around it: its children, its siblings, elements inside a shadow root, or content inside an iframe. This guide covers moving through the DOM tree from a known starting point. To locate that starting element in the first place, see [Element finding](element-finding.md).

<iframe src="../dom-traversal-tree.html" aria-label="Move a focus through a DOM tree with parent, child, and sibling methods" style="width: 100%; height: 480px; border: 0;" loading="lazy"></iframe>

## Get child elements

`get_children_elements()` returns the descendants of an element. `max_depth` controls how deep it goes (1 is direct children only), and `tag_filter` keeps only the tags you name.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://books.toscrape.com')

        container = await tab.find(class_name='row', tag_name='ol')

        direct = await container.get_children_elements(max_depth=1)
        print(f'{len(direct)} direct children')

        # descendants up to 2 levels deep, links only
        links = await container.get_children_elements(max_depth=2, tag_filter=['a'])
        print(f'{len(links)} links within two levels')

asyncio.run(main())
```

## Get sibling elements

`get_siblings_elements()` returns the elements at the same level as your element, excluding it. `tag_filter` narrows the result to specific tags.

```python
active = await tab.find(class_name='active')

siblings = await active.get_siblings_elements()
print(f'{len(siblings)} siblings')

link_siblings = await active.get_siblings_elements(tag_filter=['a'])
```

## Scoped search vs direct children

A scoped `find()` or `query()` searches **all** descendants of an element. When you want only the direct children, use the CSS child combinator `>` or an XPath step, which `query()` accepts:

```python
container = await tab.find(id='cards')

# every .card anywhere in the subtree
all_cards = await container.find(class_name='card', find_all=True)

# only the .card elements that are direct children
direct_cards = await container.query('> .card', find_all=True)
```

Use `get_children_elements()` when you want to explore structure or filter by tag; use a scoped `find()`/`query()` when you want elements matching specific attributes anywhere in the subtree.

## Read text and attributes

From any element you can read its visible text and its HTML attributes:

```python
book = await tab.find(class_name='product_pod')

title = await book.find(tag_name='h3')
print(await title.text)                       # visible text

link = await title.find(tag_name='a')
print(link.get_attribute('href'))             # an attribute value
print(link.get_attribute('title'))
```

`text` is an awaitable property; `get_attribute(name)` returns the attribute string, or `None` when the attribute is absent.

## Shadow DOM

Many components hide their internals inside a [shadow root](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM), which regular DOM queries can't see. Access the shadow host, get its shadow root, then search inside it.

```python
host = await tab.find(id='my-component')
shadow = await host.get_shadow_root()

button = await shadow.query('.internal-btn')
await button.click()
```

!!! warning "Inside a shadow root, use `query()` with CSS"
    `find()` and XPath are not supported on a `ShadowRoot` and raise `NotImplementedError`. Search shadow roots with `query()` and CSS selectors only.

`query()` inside a shadow root takes the usual `find_all`, `timeout`, and `raise_exc` parameters:

```python
items = await shadow.query('.item', find_all=True)
dynamic = await shadow.query('#late', timeout=5, raise_exc=False)
```

Web components nest, so a shadow root can contain another shadow host:

```python
outer = await tab.find(tag_name='outer-component')
outer_shadow = await outer.get_shadow_root()

inner = await outer_shadow.query('inner-component')
inner_shadow = await inner.get_shadow_root()

deep = await inner_shadow.query('.deep-btn')
```

### Discover shadow roots on a page

When you don't know which shadow roots exist (debugging, or dynamic widgets like Cloudflare Turnstile), `find_shadow_roots()` returns all of them. Shadow hosts often load late, so pass `timeout` to poll until they appear:

```python
shadow_roots = await tab.find_shadow_roots(timeout=10)

for sr in shadow_roots:
    print(f'mode={sr.mode}, host={sr.host_element}')
    checkbox = await sr.query('input[type="checkbox"]', raise_exc=False)
    if checkbox:
        await checkbox.click()
```

By default the search covers the main document (including same-origin iframes). Pass `deep=True` to also reach shadow roots inside cross-origin iframes (OOPIFs), which is what widgets like Turnstile use:

```python
shadow_roots = await tab.find_shadow_roots(deep=True, timeout=10)
```

## Work inside an iframe

An iframe has its own DOM context. Find the iframe element, then call `find()` or `query()` on it; Pydoll routes the search into the frame automatically. Keep chaining for nested iframes.

```python
iframe = await tab.query('iframe.embedded-content', timeout=10)

button = await iframe.find(tag_name='button', class_name='submit')
await button.click()

# nested iframe
inner = await iframe.find(tag_name='iframe')
link = await inner.find(text='Download PDF')
await link.click()
```

For a full iframe guide including CAPTCHA frames and troubleshooting, see [Iframes](iframes.md).

!!! note "Screenshots inside iframes"
    `tab.take_screenshot()` captures the top-level page only. To capture iframe content, find an element inside the frame and call `element.take_screenshot()`.

## What's next

- [Element finding](element-finding.md): locate the elements you traverse from.
- [Iframes](iframes.md): the complete guide to frame contexts.
- [Structured extraction](structured-extraction.md): let a model walk repeating structures for you.
