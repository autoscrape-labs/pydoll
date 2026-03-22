# Structured Data Extraction

Pydoll's extraction engine lets you define **what** you want from a page using typed models, and handles the **how** automatically. Instead of manually querying elements one by one, you declare a model with selectors and call `tab.extract()`. The result is a fully typed, validated Python object powered by [Pydantic](https://docs.pydantic.dev/).

## Why Use Structured Extraction?

Traditional scraping code tends to grow into a tangled mess of `find()` calls, `await element.text`, attribute reads, and manual type conversions scattered across dozens of lines. When the page changes, you hunt through that code to find which selector broke.

With structured extraction, all your selectors live in one place (the model), the types are enforced automatically, and the output is a clean Pydantic object with IDE autocomplete and serialization built in.

## Basic Usage

### Defining a Model

An extraction model is a class that inherits from `ExtractionModel`. Each field uses `Field()` to declare a CSS or XPath selector.

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Associated tags')
```

The `selector` parameter accepts both CSS selectors and XPath expressions. Pydoll auto-detects the type, exactly like `tab.query()`.

### Extracting a Single Item

Use `tab.extract()` to populate one model instance from the page:

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com/article')

    article = await tab.extract(Article)
    print(article.title)       # str, fully typed
    print(article.model_dump()) # dict via pydantic
```

### Extracting Multiple Items

Use `tab.extract_all()` with a `scope` selector that identifies the repeating container. Each match generates one model instance, with fields resolved relative to that container.

```python
quotes = await tab.extract_all(Quote, scope='.quote')

for q in quotes:
    print(f'{q.author}: {q.text}')
    print(q.tags)
```

You can limit the number of results:

```python
top_5 = await tab.extract_all(Quote, scope='.quote', limit=5)
```

## Field Options

The `Field()` function accepts the following parameters:

| Parameter     | Type                    | Description                                                  |
|---------------|-------------------------|--------------------------------------------------------------|
| `selector`    | `str` or `None`         | CSS or XPath selector (auto-detected)                        |
| `attribute`   | `str` or `None`         | HTML attribute to read instead of inner text                 |
| `description` | `str` or `None`         | Semantic description of the field                            |
| `default`     | any value               | Default value when the element is not found                  |
| `transform`   | callable or `None`      | Post-processing function applied to the raw string           |

At least one of `selector` or `description` must be provided. Fields with only `description` (no selector) are reserved for future LLM-based extraction and are skipped by the current CSS engine.

## Attribute Extraction

By default, the engine reads the element's visible text (`innerText`). To read an HTML attribute instead, use the `attribute` parameter:

```python
class Article(ExtractionModel):
    title: str = Field(selector='h1', description='Title')
    published: str = Field(
        selector='time.date',
        attribute='datetime',
        description='ISO publication date',
    )
    image_url: str = Field(
        selector='.hero img',
        attribute='src',
        description='Hero image URL',
    )
    link: str = Field(
        selector='a.source',
        attribute='href',
        description='Source link',
    )
    image_id: str = Field(
        selector='.hero img',
        attribute='data-id',
        description='Custom data attribute',
    )
```

Any HTML attribute works, including `data-*`, `aria-*`, `href`, `src`, `alt`, and custom attributes.

## Transforms

The `transform` parameter takes a callable that receives the raw string from the DOM and returns the desired type. This is where you convert strings to numbers, parse dates, or clean up formatting.

```python
from datetime import datetime

def parse_price(raw: str) -> float:
    return float(raw.replace('R$', '').replace('.', '').replace(',', '.').strip())

def parse_date(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), '%B %d, %Y')

class Product(ExtractionModel):
    name: str = Field(selector='.name', description='Product name')
    price: float = Field(
        selector='.price',
        description='Price in BRL',
        transform=parse_price,
    )
    release: datetime = Field(
        selector='.release-date',
        description='Release date',
        transform=parse_date,
    )
```

The transform runs **before** Pydantic validation, so the field type should match what the transform returns.

## Nested Models

When a field's type is another `ExtractionModel`, the engine uses the field's selector to find a scope element, then extracts the nested model's fields within that scope.

```python
class Author(ExtractionModel):
    name: str = Field(selector='.name', description='Author name')
    avatar: str = Field(
        selector='img.avatar',
        attribute='src',
        description='Avatar URL',
    )
    bio: str = Field(selector='.bio', description='Short bio')

class Article(ExtractionModel):
    title: str = Field(selector='h1', description='Title')
    author: Author = Field(
        selector='.author-card',
        description='Author information',
    )
```

The `.author-card` selector defines the scope. The `Author` fields (`.name`, `img.avatar`, `.bio`) are resolved **inside** that element, not from the full page. This prevents selector collisions when the page has multiple `.name` elements in different sections.

### Lists of Nested Models

You can also extract a list of nested models:

```python
class Contributor(ExtractionModel):
    name: str = Field(selector='.name', description='Contributor name')
    role: str = Field(selector='.role', description='Role')

class Project(ExtractionModel):
    title: str = Field(selector='h1', description='Project title')
    contributors: list[Contributor] = Field(
        selector='.contributor',
        description='Project contributors',
    )
```

Each `.contributor` element becomes the scope for one `Contributor` instance.

## Optional Fields and Defaults

Fields that might not be present on every page should use `Optional` with a `default`:

```python
from typing import Optional

class Article(ExtractionModel):
    title: str = Field(selector='h1', description='Title')
    subtitle: Optional[str] = Field(
        selector='.subtitle',
        description='Optional subtitle',
        default=None,
    )
    category: str = Field(
        selector='.category',
        description='Category with fallback',
        default='uncategorized',
    )
```

When the element is not found:

- Fields **with** a default silently use that default value.
- Fields **without** a default (required) raise `FieldExtractionFailed`.

Both `typing.Optional[str]` and the PEP 604 syntax `str | None` are supported.

## Timeout and Waiting

The `timeout` parameter controls how long the engine waits for elements to appear, in seconds. This is propagated to every internal query, including nested models and list fields.

```python
# Wait up to 10 seconds for elements to appear
article = await tab.extract(Article, timeout=10)

# No waiting (default), elements must already be in the DOM
article = await tab.extract(Article)

# Also works with extract_all
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
```

This uses the same polling mechanism as `tab.query(timeout=...)`, so there is no need for manual `asyncio.sleep()` calls between navigation and extraction.

## Scoped Extraction

The `scope` parameter limits extraction to a specific region of the page:

```python
# Extract only from the main article, ignoring sidebar/footer
article = await tab.extract(Article, scope='#main-article')

# extract_all requires scope (it defines the repeating container)
quotes = await tab.extract_all(Quote, scope='.quote')
```

## XPath Selectors

XPath expressions are auto-detected (they start with `/` or `./`) and work everywhere CSS selectors work:

```python
class SearchResult(ExtractionModel):
    title: str = Field(
        selector='//h3[@class="title"]',
        description='Result title via XPath',
    )
    url: str = Field(
        selector='.//a',
        attribute='href',
        description='Result URL',
    )
```

## Error Handling

The extraction engine raises specific exceptions that you can catch and handle:

```python
from pydoll.extractor import FieldExtractionFailed, InvalidExtractionModel

# InvalidExtractionModel: raised at model definition time
# when a Field has neither selector nor description
try:
    class BadModel(ExtractionModel):
        field: str = Field()  # no selector, no description
except InvalidExtractionModel:
    print('Invalid model definition')

# FieldExtractionFailed: raised at extraction time
# when a required field's element is not found
try:
    result = await tab.extract(MyModel)
except FieldExtractionFailed as e:
    print(f'Extraction failed: {e}')
```

For optional fields, extraction failures are silently handled and the default value is used. Only required fields (those without a `default`) raise exceptions.

## Pydantic Integration

`ExtractionModel` inherits from `pydantic.BaseModel`, so all Pydantic features work out of the box:

```python
article = await tab.extract(Article)

# Serialization
article.model_dump()          # dict
article.model_dump_json()     # JSON string

# JSON Schema (useful for API docs or LLM prompts)
Article.model_json_schema()

# Validation happens automatically
# If a transform returns the wrong type, Pydantic raises ValidationError
```

You can use any Pydantic feature in your models: validators, field aliases, model configuration, and more. The extraction engine adds the selector/transform layer on top without interfering with Pydantic's behavior.

## Complete Example

Here is a complete, runnable example that extracts quotes from [quotes.toscrape.com](https://quotes.toscrape.com):

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said the quote')
    tags: list[str] = Field(selector='.tag', description='Associated tags')

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)

        print(f'Extracted {len(quotes)} quotes\n')
        for q in quotes:
            print(f'"{q.text}"')
            print(f'  by {q.author} | tags: {", ".join(q.tags)}\n')

        # Pydantic serialization
        for q in quotes:
            print(q.model_dump_json())

asyncio.run(main())
```
