# Seletores: CSS e XPath

Um seletor é a string que você entrega ao `tab.query()` (e ao `selector=` nos modelos de extração) para apontar para um elemento. O Pydoll fala duas linguagens de seletor, CSS e XPath, e escolhe o motor certo para você: se a string começa com `/` ou `./`, ela roda como XPath, caso contrário como um seletor CSS. Esta página ensina o suficiente das duas para encontrar qualquer coisa em uma página.

Você só precisa de seletores para o `query()`. O método `find()` recebe atributos simples no lugar (veja [Encontrando elementos](../guides/element-finding.md)); recorra a um seletor quando quiser uma relação que o `find()` não consegue expressar.

Experimente: digite um seletor abaixo e os elementos correspondentes se acendem. Ele roda o mesmo `querySelectorAll` / XPath que o navegador roda, então o que corresponde aqui corresponde na sua automação.

<iframe src="/docs/resources/visuals/selector-playground.html" aria-label="Digite um seletor CSS ou XPath e veja quais elementos ele corresponde" style="width: 100%; height: 500px; border: 0;" loading="lazy"></iframe>

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://en.wikipedia.org/wiki/Python_(programming_language)')

        # CSS: o título do artigo, pelo id dele
        title = await tab.query('#firstHeading')
        print(await title.text)

        # XPath: o primeiro link cujo href menciona python.org
        link = await tab.query("//a[contains(@href, 'python.org')]")
        print(link.get_attribute('href'))

asyncio.run(main())
```

As duas consultas acima passaram pela mesma chamada de `query()`. O Pydoll viu o `//` inicial na segunda e a tratou como XPath.

## Quando usar cada um

Na maior parte do tempo o CSS é suficiente, e ele se lê de forma mais natural. Recorra ao XPath quando precisar de algo que o CSS não consegue fazer.

- **CSS** seleciona por id, classe, tag, atributo e posição, e se move para baixo e para os lados pela página. É a linguagem mais curta e mais familiar.
- **XPath** faz tudo isso e também corresponde a texto visível, sobe *para cima* até um pai ou ancestral, e expressa condições como "a linha que contém este texto". Se você precisa encontrar um elemento pelo texto dele ou navegar de um filho de volta para um contêiner, isso é trabalho de XPath.

Uma regra aproximada: comece no CSS, mude para XPath no momento em que você se pegar querendo dizer "o elemento cujo texto é X" ou "o pai de Y".

## Referência de CSS

Os trechos abaixo assumem um `tab` já iniciado. Passe `find_all=True` para qualquer um deles para obter uma lista em vez da primeira correspondência.

### Selecionar por id, classe e tag

```python
await tab.query('div')             # o primeiro <div>
await tab.query('#username')       # elemento com id="username"
await tab.query('.submit-btn')     # o primeiro elemento com class="submit-btn"
await tab.query('.btn.primary')    # elemento com as duas classes
await tab.query('input')           # o primeiro <input>
```

### Combinadores

Os combinadores descrevem relações entre elementos.

```python
await tab.query('nav a')           # qualquer <a> dentro de um <nav>, em qualquer profundidade
await tab.query('nav > a')         # <a> que é filho direto de <nav>
await tab.query('h1 + p')          # <p> imediatamente após um <h1>
await tab.query('h1 ~ p')          # o primeiro <p> que segue um <h1> como irmão
```

### Seletores de atributo

```python
await tab.query('input[required]')            # tem o atributo
await tab.query("input[type='email']")        # atributo igual a um valor
await tab.query("a[href^='https://']")        # valor começa com
await tab.query("img[src$='.png']")           # valor termina com
await tab.query("a[href*='wikipedia']")       # valor contém
```

### Pseudo-classes

As pseudo-classes selecionam por posição ou estado.

```python
await tab.query('li:first-child')             # o primeiro <li> entre seus irmãos
await tab.query('li:nth-child(2)')            # o segundo <li>
await tab.query('tr:nth-child(odd)', find_all=True)  # toda linha ímpar
await tab.query('input:checked')              # um checkbox ou radio marcado
await tab.query('button:not([disabled])')     # um botão sem o atributo disabled
```

## Referência de XPath

### Caminhos

```python
await tab.query('//div')           # qualquer <div>, em qualquer lugar
await tab.query('//nav/a')         # <a> que é filho direto de um <nav>
await tab.query('//nav//a')        # <a> em qualquer lugar dentro de um <nav>
await tab.query('(//div)[1]')      # o primeiro <div> no documento
await tab.query('//ul/li[last()]') # o último <li> em um <ul>
```

### Corresponder por atributos e texto

É aqui que você precisa de XPath. O CSS não consegue selecionar por texto visível; o XPath consegue.

```python
await tab.query("//input[@type='email']")            # atributo igual a
await tab.query("//input[@type='text' and @required]")  # duas condições
await tab.query("//button[text()='Submit']")         # texto exato
await tab.query("//p[contains(text(), 'welcome')]")  # texto parcial
await tab.query("//a[starts-with(@href, 'https://')]")  # atributo começa com
```

!!! tip "Normalize o texto antes de corresponder"
    O texto renderizado costuma carregar espaços em branco perdidos. `//button[normalize-space(text())='Submit']` colapsa sequências de espaços e apara as pontas, então ele corresponde mesmo quando o HTML tem indentação irregular.

### Eixos: mova-se em qualquer direção

Um eixo diz em qual direção viajar a partir do nó atual. Essa é a vantagem do XPath: você pode subir até um pai ou atravessar até um irmão, o que o CSS não consegue.

| Eixo | Direção | Encontra |
|------|-----------|-------|
| `parent::` | para cima | o pai imediato |
| `ancestor::` | para cima | qualquer ancestral, em qualquer profundidade |
| `following-sibling::` | para os lados | irmãos depois deste nó |
| `preceding-sibling::` | para os lados | irmãos antes deste nó |
| `child::` | para baixo | filhos diretos |
| `descendant::` | para baixo | qualquer descendente |

Abreviações que você verá com frequência: `//div/p` é `//div/child::p`, `@id` é `attribute::id`, e `..` é `parent::node()`.

```python
await tab.query("//input[@name='email']/parent::div")   # sobe até o div que envolve
await tab.query('//button/ancestor::form')              # sobe até o form que contém
await tab.query("//label[text()='Email:']/following-sibling::input")  # o input ao lado de um label
```

## Exemplos trabalhados

Estes usam o formulário de exemplo abaixo. Ele mostra os padrões que você encontra com mais frequência em páginas reais: encontrar um elemento pelo texto ao lado dele, e caminhar de um controle até a linha dele.

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

### Encontrar um input pelo label dele

Você conhece o texto do label, não o id do input. Encontre o label, depois dê um passo para o lado até o input:

```python
email = await tab.query("//label[text()='Email:']/following-sibling::input")
```

### Encontrar a mensagem de erro ao lado de um campo

```python
error = await tab.query("//input[@id='email']/following-sibling::span[@class='error']")
if await error.is_visible():
    print('Email was rejected')
```

`is_visible()` informa se o elemento está de fato sendo exibido, o que importa aqui porque o span começa oculto.

### Diferenciar os dois botões

O botão de envio é o que tem `type='submit'`, então você nunca depende da posição dele:

```python
save = await tab.query("button[type='submit']")          # o CSS já basta aqui
save = await tab.query("//button[text()='Save']")        # ou corresponda pelo texto do label
```

### Ler o label de um checkbox

O atributo `for` amarra um label ao controle dele, então você pode pular direto para ele:

```python
label = await tab.query("//label[@for='newsletter']")
print(await label.text)   # "Subscribe to the newsletter"
```

### Caminhar de um controle até a linha dele

Em uma tabela, muitas vezes você tem um botão e quer a linha em que ele está. Consulte a partir do elemento com um XPath que sobe pela árvore:

```python
delete = await tab.query("//tr[@data-product-id='101']//button[@class='delete']")

row = await delete.query('./ancestor::tr')
print(row.get_attribute('data-product-id'))   # "101", get_attribute não é aguardado com await
```

`get_attribute()` lê um valor de forma síncrona a partir do elemento que você já localizou, então ele não leva `await`.

## Monte seletores a partir de variáveis

Quando o valor pelo qual você corresponde vem do seu programa, monte a string com uma f-string. Escape quaisquer aspas no valor para que elas não quebrem a expressão:

```python
async def row_for(tab, product_name):
    safe = product_name.replace("'", "\\'")
    return await tab.query(f"//tr[td[text()='{safe}']]")


laptop_row = await row_for(tab, 'Laptop')
```

## Mantenha os seletores estáveis

Escolha atributos que um redesign dificilmente vai mexer, e apoie-se na expressão mais simples que funciona.

```python
# estável: nomes e ids sobrevivem a mudanças de layout
await tab.query('#signup')
await tab.query("[data-testid='save-button']")
await tab.query("input[name='email']")

# frágil: cadeias baseadas em posição quebram quando a marcação muda
await tab.query('div > div > div:nth-child(3) > input')
```

O CSS é marginalmente mais rápido que o XPath para buscas simples, mas a diferença é de milissegundos por consulta e raramente vale a pena otimizar. Escolha o seletor que se lê com clareza e sobrevive a mudanças de página.

## Próximos passos

- [Encontrando elementos](../guides/element-finding.md): use estes seletores com o `query()`, e o `find()` baseado em atributos.
- [Percorrendo o DOM](../guides/dom-traversal.md): navegue pela árvore a partir de um elemento que você já tem.
- [Extração estruturada](../guides/structured-extraction.md): coloque estes seletores no `Field(selector=...)` de um modelo para extrair dados tipados.
