# Extração Estruturada de Dados

O motor de extração do Pydoll permite que você defina **o que** deseja de uma página usando modelos tipados, e cuida do **como** automaticamente. Em vez de consultar elementos manualmente um a um, você declara um modelo com seletores e chama `tab.extract()`. O resultado é um objeto Python totalmente tipado e validado, alimentado pelo [Pydantic](https://docs.pydantic.dev/).

## Por Que Usar Extração Estruturada?

Código de scraping tradicional tende a crescer em uma confusão de chamadas `find()`, `await element.text`, leitura de atributos e conversões manuais de tipo espalhadas por dezenas de linhas. Quando a página muda, você precisa caçar no código para encontrar qual seletor quebrou.

Com extração estruturada, todos os seus seletores ficam em um único lugar (o modelo), os tipos são garantidos automaticamente, e a saída é um objeto Pydantic limpo com autocomplete da IDE e serialização embutida.

## Uso Básico

### Definindo um Modelo

Um modelo de extração é uma classe que herda de `ExtractionModel`. Cada campo usa `Field()` para declarar um seletor CSS ou XPath.

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Associated tags')
```

O parâmetro `selector` aceita tanto seletores CSS quanto expressões XPath. O Pydoll auto-detecta o tipo, exatamente como o `tab.query()`.

### Extraindo um Único Item

Use `tab.extract()` para preencher uma instância do modelo a partir da página:

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to('https://example.com/article')

    article = await tab.extract(Article)
    print(article.title)       # str, fully typed
    print(article.model_dump()) # dict via pydantic
```

### Extraindo Múltiplos Itens

Use `tab.extract_all()` com um seletor `scope` que identifica o container repetido. Cada match gera uma instância do modelo, com os campos resolvidos relativamente àquele container.

```python
quotes = await tab.extract_all(Quote, scope='.quote')

for q in quotes:
    print(f'{q.author}: {q.text}')
    print(q.tags)
```

Você pode limitar o número de resultados:

```python
top_5 = await tab.extract_all(Quote, scope='.quote', limit=5)
```

## Opções do Field

A função `Field()` aceita os seguintes parâmetros:

| Parâmetro     | Tipo                    | Descrição                                                    |
|---------------|-------------------------|--------------------------------------------------------------|
| `selector`    | `str` ou `None`         | Seletor CSS ou XPath (auto-detectado)                        |
| `attribute`   | `str` ou `None`         | Atributo HTML a ler em vez do texto interno                  |
| `description` | `str` ou `None`         | Descrição semântica do campo                                 |
| `default`     | qualquer valor          | Valor padrão quando o elemento não é encontrado              |
| `transform`   | callable ou `None`      | Função de pós-processamento aplicada à string bruta          |

Pelo menos um entre `selector` ou `description` deve ser fornecido. Campos com apenas `description` (sem selector) são reservados para futura extração baseada em LLM e são ignorados pelo motor CSS atual.

## Extração de Atributos

Por padrão, o motor lê o texto visível do elemento (`innerText`). Para ler um atributo HTML em vez disso, use o parâmetro `attribute`:

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

Qualquer atributo HTML funciona, incluindo `data-*`, `aria-*`, `href`, `src`, `alt` e atributos customizados.

## Transforms

O parâmetro `transform` recebe um callable que recebe a string bruta do DOM e retorna o tipo desejado. É aqui que você converte strings para números, parseia datas ou limpa formatação.

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

O transform executa **antes** da validação do Pydantic, então o tipo do campo deve corresponder ao que o transform retorna.

## Modelos Aninhados

Quando o tipo de um campo é outro `ExtractionModel`, o motor usa o seletor do campo para encontrar um elemento de escopo, e então extrai os campos do modelo aninhado dentro daquele escopo.

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

O seletor `.author-card` define o escopo. Os campos do `Author` (`.name`, `img.avatar`, `.bio`) são resolvidos **dentro** daquele elemento, não da página inteira. Isso previne colisões de seletores quando a página tem múltiplos elementos `.name` em seções diferentes.

### Listas de Modelos Aninhados

Você também pode extrair uma lista de modelos aninhados:

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

Cada elemento `.contributor` se torna o escopo para uma instância de `Contributor`.

## Campos Opcionais e Defaults

Campos que podem não estar presentes em toda página devem usar `Optional` com um `default`:

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

Quando o elemento não é encontrado:

- Campos **com** default usam silenciosamente aquele valor padrão.
- Campos **sem** default (obrigatórios) levantam `FieldExtractionFailed`.

Tanto `typing.Optional[str]` quanto a sintaxe PEP 604 `str | None` são suportados.

## Timeout e Espera

O parâmetro `timeout` controla quanto tempo o motor espera pelos elementos aparecerem, em segundos. Ele é propagado para toda query interna, incluindo modelos aninhados e campos lista.

```python
# Wait up to 10 seconds for elements to appear
article = await tab.extract(Article, timeout=10)

# No waiting (default), elements must already be in the DOM
article = await tab.extract(Article)

# Also works with extract_all
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
```

Isso usa o mesmo mecanismo de polling que `tab.query(timeout=...)`, então não há necessidade de chamadas manuais `asyncio.sleep()` entre navegação e extração.

## Extração com Escopo

O parâmetro `scope` limita a extração a uma região específica da página:

```python
# Extract only from the main article, ignoring sidebar/footer
article = await tab.extract(Article, scope='#main-article')

# extract_all requires scope (it defines the repeating container)
quotes = await tab.extract_all(Quote, scope='.quote')
```

## Seletores XPath

Expressões XPath são auto-detectadas (começam com `/` ou `./`) e funcionam em todo lugar que seletores CSS funcionam:

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

## Tratamento de Erros

O motor de extração levanta exceções específicas que você pode capturar e tratar:

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

Para campos opcionais, falhas de extração são tratadas silenciosamente e o valor default é utilizado. Apenas campos obrigatórios (aqueles sem `default`) levantam exceções.

## Integração com Pydantic

`ExtractionModel` herda de `pydantic.BaseModel`, então todas as funcionalidades do Pydantic funcionam imediatamente:

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

Você pode usar qualquer funcionalidade do Pydantic nos seus modelos: validadores, aliases de campos, configuração de modelo e mais. O motor de extração adiciona a camada de seletor/transform por cima sem interferir no comportamento do Pydantic.

## Exemplo Completo

Aqui está um exemplo completo e executável que extrai citações do [quotes.toscrape.com](https://quotes.toscrape.com):

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
