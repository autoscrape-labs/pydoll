# 结构化提取

Pydoll 的提取引擎让你用类型化模型来定义你想从页面得到**什么**，而自动处理**怎么做**。你不必再逐个手动查询元素，只需声明一个带有选择器的模型，然后调用 `tab.extract()`。结果是一个完全类型化、经过校验的 Python 对象，基于 [Pydantic](https://docs.pydantic.dev/) 构建。

<iframe src="/docs/resources/visuals/extraction-flow.html" aria-label="A page and a model producing a typed, validated object through tab.extract" style="width: 100%; height: 360px; border: 0;" loading="lazy"></iframe>

## 为什么要用模型

传统的抓取代码会把 `find()` 调用、`await element.text`、属性读取和手动类型转换散落在几十行里。当页面发生变化时，你得在这些代码里翻找，找出是哪个选择器失效了。

有了结构化提取，你所有的选择器都集中在一处（即模型里），类型会被自动强制执行，输出是一个带有 IDE 自动补全和内置序列化的 Pydantic 对象。

## 基本用法

### 定义一个模型

一个提取模型是继承自 `ExtractionModel` 的类。每个字段用 `Field()` 来声明一个 CSS 或 XPath 选择器。

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Associated tags')
```

`selector` 参数同时接受 CSS 选择器和 XPath 表达式。Pydoll 会自动检测类型，就和 `tab.query()` 完全一样。

### 提取单个条目

用 `tab.extract()` 从页面填充一个模型实例。它会针对页面解析每个字段的选择器，并返回第一个匹配项，且已类型化并校验：

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.extractor import ExtractionModel, Field


class Quote(ExtractionModel):
    text: str = Field(selector='.text')
    author: str = Field(selector='.author')


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

        quote = await tab.extract(Quote)
        print(quote.author, quote.text)   # str 字段，完全类型化
        print(quote.model_dump())         # 通过 pydantic 得到 dict

asyncio.run(main())
```

### 提取多个条目

用 `tab.extract_all()`，并给一个用于标识重复容器的 `scope` 选择器。每个匹配项生成一个模型实例，其字段是相对于该容器解析的。

```python
quotes = await tab.extract_all(Quote, scope='.quote')

for q in quotes:
    print(f'{q.author}: {q.text}')
    print(q.tags)
```

你可以限制结果数量：

```python
top_5 = await tab.extract_all(Quote, scope='.quote', limit=5)
```

## 字段选项

`Field()` 函数接受以下参数：

| 参数          | 类型                    | 说明                                                         |
|---------------|-------------------------|--------------------------------------------------------------|
| `selector`    | `str` 或 `None`         | CSS 或 XPath 选择器（自动检测）                              |
| `attribute`   | `str` 或 `None`         | 要读取的 HTML 属性，而非内部文本                            |
| `description` | `str` 或 `None`         | 字段的语义描述                                              |
| `default`     | 任意值                  | 找不到元素时的默认值                                        |
| `transform`   | 可调用对象 或 `None`    | 应用于原始字符串的后处理函数                                |

`selector` 和 `description` 至少要提供其中之一。只有 `description`（没有 `selector`）的字段是为将来基于 LLM 的提取保留的，当前的 CSS 引擎会跳过它们。

## 读取 HTML 属性

默认情况下，引擎读取元素的可见文本（`innerText`）。若要改为读取某个 HTML 属性，使用 `attribute` 参数：

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

任何 HTML 属性都可以，包括 `data-*`、`aria-*`、`href`、`src`、`alt` 以及自定义属性。

## 转换值

`transform` 参数接受一个可调用对象，它接收来自 DOM 的原始字符串并返回你想要的类型。你在这里把字符串转换为数字、解析日期，或清理格式。

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

transform 在 Pydantic 校验**之前**运行，所以字段类型应当与 transform 返回的类型一致。

## 嵌套模型

当一个字段的类型是另一个 `ExtractionModel` 时，引擎会用该字段的选择器找到一个作用域元素，然后在这个作用域内提取嵌套模型的字段。

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

`.author-card` 选择器定义了作用域。`Author` 的字段（`.name`、`img.avatar`、`.bio`）是在该元素**内部**解析的，而不是从整个页面解析。当页面在不同区块里有多个 `.name` 元素时，这可以防止选择器冲突。

### 嵌套模型的列表

你也可以提取一个嵌套模型的列表：

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

每个 `.contributor` 元素都成为一个 `Contributor` 实例的作用域。

## 可选字段与默认值

那些未必出现在每个页面上的字段，应当配合 `default` 使用 `Optional`：

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

当找不到元素时：

- **带有**默认值的字段会静默地使用该默认值。
- **没有**默认值的字段（必填字段）会抛出 `FieldExtractionFailed`。

`typing.Optional[str]` 和 PEP 604 语法 `str | None` 都受支持。

## 等待元素

`timeout` 参数控制引擎等待元素出现的时长，单位为秒。它会传播到每一个内部查询，包括嵌套模型和列表字段。

```python
# 最多等待 10 秒让元素出现
article = await tab.extract(Article, timeout=10)

# 不等待（默认），元素必须已经在 DOM 中
article = await tab.extract(Article)

# 同样适用于 extract_all
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
```

它使用与 `tab.query(timeout=...)` 相同的轮询机制，所以在导航和提取之间无需手动调用 `asyncio.sleep()`。

## 将提取限定到某个区域

`scope` 参数把提取限制到页面的某个特定区域：

```python
# 只从主文章中提取，忽略侧边栏/页脚
article = await tab.extract(Article, scope='#main-article')

# extract_all 需要 scope（它定义了重复容器）
quotes = await tab.extract_all(Quote, scope='.quote')
```

## XPath 选择器

XPath 表达式会被自动检测（它们以 `/` 或 `./` 开头），并且在所有 CSS 选择器可用的地方都可用：

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

## 处理错误

提取引擎会抛出你可以捕获并处理的特定异常：

```python
from pydoll.extractor import FieldExtractionFailed, InvalidExtractionModel

# InvalidExtractionModel：在模型定义时抛出，
# 当某个 Field 既没有 selector 也没有 description 时
try:
    class BadModel(ExtractionModel):
        field: str = Field()  # 既没有 selector，也没有 description
except InvalidExtractionModel:
    print('Invalid model definition')

# FieldExtractionFailed：在提取时抛出，
# 当某个必填字段的元素找不到时
try:
    result = await tab.extract(MyModel)
except FieldExtractionFailed as e:
    print(f'Extraction failed: {e}')
```

对于可选字段，提取失败会被静默处理并使用默认值。只有必填字段（那些没有 `default` 的字段）才会抛出异常。

## Pydantic 集成

`ExtractionModel` 继承自 `pydantic.BaseModel`，所以所有 Pydantic 特性都开箱即用：

```python
article = await tab.extract(Article)

# 序列化
article.model_dump()          # dict
article.model_dump_json()     # JSON 字符串

# JSON Schema（对 API 文档或 LLM 提示很有用）
Article.model_json_schema()

# 校验会自动进行
# 如果 transform 返回了错误的类型，Pydantic 会抛出 ValidationError
```

你可以在模型中使用任何 Pydantic 特性：校验器、字段别名、模型配置等等。提取引擎在其之上添加了选择器/transform 层，而不干扰 Pydantic 的行为。

## 完整示例

下面是一个完整、可运行的示例，它从 [quotes.toscrape.com](https://quotes.toscrape.com) 提取名言：

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

        # Pydantic 序列化
        for q in quotes:
            print(q.model_dump_json())

asyncio.run(main())
```

## 下一步

- [元素查找](element-finding.md)：提取所构建于其上的 `find()` 和 `query()` 调用。
- [选择器：CSS 与 XPath](../basics/selectors.md)：编写你的字段所使用的选择器。
- [DOM 遍历](dom-traversal.md)：当页面需要手动导航而非用模型时。
