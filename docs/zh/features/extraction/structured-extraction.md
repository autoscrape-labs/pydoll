# 结构化数据提取

Pydoll 的提取引擎让您使用类型化模型定义想要从页面获取**什么**数据，并自动处理**如何**获取。无需逐个手动查询元素，您只需声明一个带有选择器的模型并调用 `tab.extract()`。结果是一个由 [Pydantic](https://docs.pydantic.dev/) 驱动的、完全类型化和验证过的 Python 对象。

## 为什么使用结构化提取？

传统的抓取代码往往会变成一堆散落在数十行中的 `find()` 调用、`await element.text`、属性读取和手动类型转换。当页面发生变化时，您需要在代码中逐行排查哪个选择器出了问题。

使用结构化提取后，所有选择器都集中在一个地方（模型），类型会自动强制执行，输出是一个干净的 Pydantic 对象，内置 IDE 自动补全和序列化功能。

## 基本用法

### 定义模型

提取模型是一个继承自 `ExtractionModel` 的类。每个字段使用 `Field()` 来声明 CSS 或 XPath 选择器。

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Associated tags')
```

`selector` 参数同时接受 CSS 选择器和 XPath 表达式。Pydoll 会自动检测类型，与 `tab.query()` 的行为完全一致。

### 提取单个项目

使用 `tab.extract()` 从页面填充一个模型实例：

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com/article')

    article = await tab.extract(Article)
    print(article.title)       # str, fully typed
    print(article.model_dump()) # dict via pydantic
```

### 提取多个项目

使用 `tab.extract_all()` 并配合 `scope` 选择器来标识重复的容器。每个匹配项生成一个模型实例，字段相对于该容器解析。

```python
quotes = await tab.extract_all(Quote, scope='.quote')

for q in quotes:
    print(f'{q.author}: {q.text}')
    print(q.tags)
```

您可以限制结果数量：

```python
top_5 = await tab.extract_all(Quote, scope='.quote', limit=5)
```

## Field 选项

`Field()` 函数接受以下参数：

| 参数          | 类型                    | 描述                                                         |
|---------------|-------------------------|--------------------------------------------------------------|
| `selector`    | `str` 或 `None`         | CSS 或 XPath 选择器（自动检测）                              |
| `attribute`   | `str` 或 `None`         | 要读取的 HTML 属性，而非内部文本                             |
| `description` | `str` 或 `None`         | 字段的语义描述                                               |
| `default`     | 任意值                  | 未找到元素时的默认值                                         |
| `transform`   | callable 或 `None`      | 应用于原始字符串的后处理函数                                 |

必须提供 `selector` 或 `description` 中的至少一个。仅有 `description`（无 selector）的字段保留用于未来基于 LLM 的提取，当前 CSS 引擎会跳过这些字段。

## 属性提取

默认情况下，引擎读取元素的可见文本（`innerText`）。要读取 HTML 属性，请使用 `attribute` 参数：

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

任何 HTML 属性都可以使用，包括 `data-*`、`aria-*`、`href`、`src`、`alt` 和自定义属性。

## 转换函数

`transform` 参数接受一个 callable，它接收来自 DOM 的原始字符串并返回所需类型。这是您将字符串转换为数字、解析日期或清理格式的地方。

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

转换函数在 Pydantic 验证**之前**运行，因此字段类型应与转换函数的返回值匹配。

## 嵌套模型

当字段的类型是另一个 `ExtractionModel` 时，引擎使用该字段的选择器找到作用域元素，然后在该作用域内提取嵌套模型的字段。

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

`.author-card` 选择器定义了作用域。`Author` 的字段（`.name`、`img.avatar`、`.bio`）在该元素**内部**解析，而非从整个页面解析。这可以防止当页面在不同区域有多个 `.name` 元素时发生选择器冲突。

### 嵌套模型列表

您还可以提取嵌套模型的列表：

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

每个 `.contributor` 元素成为一个 `Contributor` 实例的作用域。

## 可选字段和默认值

可能不会出现在每个页面上的字段应使用 `Optional` 和 `default`：

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

当未找到元素时：

- **有**默认值的字段会静默使用该默认值。
- **没有**默认值的字段（必填）会抛出 `FieldExtractionFailed`。

`typing.Optional[str]` 和 PEP 604 语法 `str | None` 都受支持。

## 超时和等待

`timeout` 参数控制引擎等待元素出现的时间，单位为秒。它会传播到每个内部查询，包括嵌套模型和列表字段。

```python
# Wait up to 10 seconds for elements to appear
article = await tab.extract(Article, timeout=10)

# No waiting (default), elements must already be in the DOM
article = await tab.extract(Article)

# Also works with extract_all
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
```

这使用与 `tab.query(timeout=...)` 相同的轮询机制，因此在导航和提取之间不需要手动调用 `asyncio.sleep()`。

## 限定范围提取

`scope` 参数将提取限制在页面的特定区域：

```python
# Extract only from the main article, ignoring sidebar/footer
article = await tab.extract(Article, scope='#main-article')

# extract_all requires scope (it defines the repeating container)
quotes = await tab.extract_all(Quote, scope='.quote')
```

## XPath 选择器

XPath 表达式会自动检测（以 `/` 或 `./` 开头），并且在 CSS 选择器适用的所有地方都可以使用：

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

## 错误处理

提取引擎会抛出特定的异常，您可以捕获和处理：

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

对于可选字段，提取失败会被静默处理并使用默认值。只有必填字段（没有 `default` 的字段）会抛出异常。

## Pydantic 集成

`ExtractionModel` 继承自 `pydantic.BaseModel`，因此所有 Pydantic 功能都可以直接使用：

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

您可以在模型中使用任何 Pydantic 功能：验证器、字段别名、模型配置等。提取引擎在 Pydantic 行为之上添加了选择器/转换层，不会干扰 Pydantic 的行为。

## 完整示例

以下是一个完整的、可运行的示例，从 [quotes.toscrape.com](https://quotes.toscrape.com) 提取名言：

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
