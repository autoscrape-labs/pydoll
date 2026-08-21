# Extração estruturada

O motor de extração do Pydoll permite que você defina **o que** quer de uma página usando modelos tipados, e cuida do **como** automaticamente. Em vez de consultar elementos manualmente um a um, você declara um modelo com seletores e chama `tab.extract()`. O resultado é um objeto Python totalmente tipado e validado, construído sobre o [Pydantic](https://docs.pydantic.dev/).

<iframe src="/docs/resources/visuals/extraction-flow.html" aria-label="A page and a model producing a typed, validated object through tab.extract" style="width: 100%; height: 360px; border: 0;" loading="lazy"></iframe>

## Por que usar um modelo

Código de scraping tradicional espalha chamadas de `find()`, `await element.text`, leituras de atributos e conversões de tipo manuais por dezenas de linhas. Quando a página muda, você vasculha esse código para descobrir qual seletor quebrou.

Com a extração estruturada, todos os seus seletores ficam em um só lugar (o modelo), os tipos são aplicados automaticamente e a saída é um objeto Pydantic com autocomplete no IDE e serialização já embutidos.

## Uso básico

### Defina um modelo

Um modelo de extração é uma classe que herda de `ExtractionModel`. Cada campo usa `Field()` para declarar um seletor CSS ou XPath.

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Who said it')
    tags: list[str] = Field(selector='.tag', description='Associated tags')
```

O parâmetro `selector` aceita tanto seletores CSS quanto expressões XPath. O Pydoll detecta o tipo automaticamente, exatamente como o `tab.query()`.

### Extraia um único item

Use `tab.extract()` para preencher uma instância de modelo a partir da página. Ele resolve o seletor de cada campo contra a página e retorna a primeira correspondência, tipada e validada:

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
        print(quote.author, quote.text)   # campos str, totalmente tipados
        print(quote.model_dump())         # dict via pydantic

asyncio.run(main())
```

### Extraia vários itens

Use `tab.extract_all()` com um seletor `scope` que identifica o contêiner repetido. Cada correspondência gera uma instância de modelo, com os campos resolvidos em relação a esse contêiner.

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

## Opções de campo

A função `Field()` aceita os seguintes parâmetros:

| Parâmetro     | Tipo                    | Descrição                                                     |
|---------------|-------------------------|--------------------------------------------------------------|
| `selector`    | `str` ou `None`         | Seletor CSS ou XPath (detectado automaticamente)             |
| `attribute`   | `str` ou `None`         | Atributo HTML a ler em vez do texto interno                  |
| `description` | `str` ou `None`         | Descrição semântica do campo                                 |
| `default`     | qualquer valor          | Valor padrão quando o elemento não é encontrado              |
| `transform`   | callable ou `None`      | Função de pós-processamento aplicada à string bruta          |

Pelo menos um entre `selector` ou `description` precisa ser fornecido. Campos apenas com `description` (sem seletor) são reservados para futura extração baseada em LLM e são ignorados pelo motor CSS atual.

## Leia um atributo HTML

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

Qualquer atributo HTML funciona, incluindo `data-*`, `aria-*`, `href`, `src`, `alt` e atributos personalizados.

## Transforme valores

O parâmetro `transform` recebe um callable que recebe a string bruta do DOM e retorna o tipo desejado. É aqui que você converte strings em números, faz o parse de datas ou limpa a formatação.

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

O transform roda **antes** da validação do Pydantic, então o tipo do campo deve corresponder ao que o transform retorna.

## Modelos aninhados

Quando o tipo de um campo é outro `ExtractionModel`, o motor usa o seletor do campo para encontrar um elemento de escopo e depois extrai os campos do modelo aninhado dentro desse escopo.

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

O seletor `.author-card` define o escopo. Os campos de `Author` (`.name`, `img.avatar`, `.bio`) são resolvidos **dentro** desse elemento, não a partir da página inteira. Isso evita colisões de seletores quando a página tem vários elementos `.name` em seções diferentes.

### Listas de modelos aninhados

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

Cada elemento `.contributor` se torna o escopo de uma instância de `Contributor`.

## Campos opcionais e valores padrão

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

- Campos **com** um valor padrão usam esse valor silenciosamente.
- Campos **sem** um valor padrão (obrigatórios) lançam `FieldExtractionFailed`.

Tanto `typing.Optional[str]` quanto a sintaxe da PEP 604 `str | None` são suportados.

## Espere por elementos

O parâmetro `timeout` controla por quanto tempo o motor espera os elementos aparecerem, em segundos. Isso é propagado para cada consulta interna, incluindo modelos aninhados e campos de lista.

```python
# Espera até 10 segundos pelos elementos aparecerem
article = await tab.extract(Article, timeout=10)

# Sem espera (padrão), os elementos já devem estar no DOM
article = await tab.extract(Article)

# Também funciona com extract_all
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
```

Isso usa o mesmo mecanismo de polling que `tab.query(timeout=...)`, então não há necessidade de chamadas manuais de `asyncio.sleep()` entre a navegação e a extração.

## Limite a extração a uma região

O parâmetro `scope` limita a extração a uma região específica da página:

```python
# Extrai apenas do artigo principal, ignorando barra lateral/rodapé
article = await tab.extract(Article, scope='#main-article')

# extract_all exige scope (ele define o contêiner repetido)
quotes = await tab.extract_all(Quote, scope='.quote')
```

## Seletores XPath

Expressões XPath são detectadas automaticamente (começam com `/` ou `./`) e funcionam em todos os lugares onde seletores CSS funcionam:

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

## Trate os erros

O motor de extração lança exceções específicas que você pode capturar e tratar:

```python
from pydoll.extractor import FieldExtractionFailed, InvalidExtractionModel

# InvalidExtractionModel: lançada no momento da definição do modelo
# quando um Field não tem nem selector nem description
try:
    class BadModel(ExtractionModel):
        field: str = Field()  # sem selector, sem description
except InvalidExtractionModel:
    print('Invalid model definition')

# FieldExtractionFailed: lançada no momento da extração
# quando o elemento de um campo obrigatório não é encontrado
try:
    result = await tab.extract(MyModel)
except FieldExtractionFailed as e:
    print(f'Extraction failed: {e}')
```

Para campos opcionais, as falhas de extração são tratadas silenciosamente e o valor padrão é usado. Apenas campos obrigatórios (aqueles sem um `default`) lançam exceções.

## Integração com Pydantic

`ExtractionModel` herda de `pydantic.BaseModel`, então todos os recursos do Pydantic funcionam de imediato:

```python
article = await tab.extract(Article)

# Serialização
article.model_dump()          # dict
article.model_dump_json()     # string JSON

# JSON Schema (útil para documentação de API ou prompts de LLM)
Article.model_json_schema()

# A validação acontece automaticamente
# Se um transform retorna o tipo errado, o Pydantic lança ValidationError
```

Você pode usar qualquer recurso do Pydantic nos seus modelos: validadores, aliases de campo, configuração de modelo e mais. O motor de extração adiciona a camada de seletor/transform por cima sem interferir no comportamento do Pydantic.

## Exemplo completo

Aqui está um exemplo completo e executável que extrai citações de [quotes.toscrape.com](https://quotes.toscrape.com):

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

        # Serialização Pydantic
        for q in quotes:
            print(q.model_dump_json())

asyncio.run(main())
```

## Próximos passos

- [Busca de elementos](element-finding.md): as chamadas `find()` e `query()` sobre as quais a extração é construída.
- [Seletores: CSS e XPath](../basics/selectors.md): escreva os seletores que seus campos usam.
- [Navegação no DOM](dom-traversal.md): quando uma página exige navegação manual em vez de um modelo.
