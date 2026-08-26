# Encontrar elementos

Localizar elementos é a base de toda automação. O Pydoll oferece duas formas de fazer isso: `find()`, onde você descreve o elemento pelos seus atributos HTML, e `query()`, onde você passa um seletor CSS ou XPath. Ambos aguardam o elemento aparecer, então você nunca escreve laços `sleep` manuais.

Edite os atributos abaixo e veja o `find()` localizar o elemento ao vivo. O Pydoll transforma os atributos que você passa em um seletor para você, e o elemento correspondente se destaca.

<iframe scrolling="no" src="/docs/resources/visuals/element-find-playground.html" aria-label="Edit find() attributes and see which element it locates" style="width: 100%; height: 365px; border: 0;" loading="lazy"></iframe>

## Encontrar por atributos

O `find()` é a ferramenta do dia a dia. Você passa os atributos que usaria para descrever o elemento a uma pessoa, e o Pydoll monta o seletor para você.

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

Você pode localizar um elemento por qualquer um destes atributos. Cada um deles retorna a primeira correspondência:

```python
await tab.find(id='username')        # por id
await tab.find(class_name='quote')   # por nome de classe
await tab.find(tag_name='h1')        # por nome de tag
await tab.find(name='username')      # pelo atributo name
await tab.find(text='Login')         # por texto visível
```

## Combine atributos para mais precisão

Passe vários atributos e o `find()` corresponde ao elemento que tem **todos** eles (um AND). Use underscores para nomes de atributos com hífen: `data-testid` vira `data_testid`, `aria-label` vira `aria_label`.

```python
# um <input type="password" name="password">
password = await tab.find(tag_name='input', type='password', name='password')

# um <button class="btn" type="submit">
submit = await tab.find(tag_name='button', class_name='btn', type='submit')

# um atributo data
card = await tab.find(tag_name='div', data_testid='product-card')
```

Para lógica OU (o elemento pode ter um atributo ou outro), encadeie duas chamadas com `raise_exc=False`, como mostrado em [Lidar com elementos ausentes](#handle-missing-elements).

## Encontrar todas as correspondências

Passe `find_all=True` para obter uma lista de todos os elementos correspondentes em vez do primeiro:

```python
await tab.go_to('https://books.toscrape.com')

books = await tab.find(class_name='product_pod', find_all=True)
print(f'{len(books)} books on this page')

for book in books:
    title = await book.find(tag_name='h3')
    price = await book.find(class_name='price_color')
    print(await title.text, await price.text)
```

## Aguardar elementos que carregam tarde

Páginas modernas renderizam conteúdo após o carregamento inicial. Passe `timeout` (em segundos) e o `find()` verifica repetidamente até o elemento aparecer ou o tempo se esgotar. Você não adiciona chamadas `sleep`; a espera já é embutida.

```python
# aguarda até 10 segundos por um elemento que carrega tarde
content = await tab.find(class_name='dynamic-content', timeout=10)
```

!!! tip "Escolha os timeouts deliberadamente"
    Curto demais e você perde elementos lentos; longo demais e você espera por coisas que nunca vão aparecer. De cinco a dez segundos serve para a maior parte do conteúdo dinâmico. Para um elemento que só às vezes está presente, combine um timeout curto com `raise_exc=False` (abaixo).

## Encontrar por seletor CSS ou XPath

Quando você já tem um seletor, ou precisa de uma relação que o `find()` não consegue expressar, use `query()`. Ele detecta automaticamente CSS ou XPath.

```python
# CSS
submit = await tab.query("button[type='submit']")
required = await tab.query('input[required]', find_all=True)
nested = await tab.query('div.container > .content .item:nth-child(2)')

# XPath: correspondência de texto e relações que o CSS não alcança
button = await tab.query("//button[contains(text(), 'Submit')]")
label_input = await tab.query("//label[text()='Email:']/following-sibling::input")
```

O `query()` recebe os mesmos parâmetros `find_all`, `timeout` e `raise_exc` que o `find()`. Para saber quando usar CSS ou XPath, veja [Seletores: CSS e XPath](../basics/selectors.md).

## Buscar dentro de um elemento

Todo elemento oferece `find()` e `query()` restritos à sua própria subárvore, que é como você trabalha com estruturas repetidas como cards ou linhas. Uma busca com escopo percorre **todos** os descendentes do elemento, não apenas seus filhos diretos, seguindo o comportamento do `querySelector`.

```python
await tab.go_to('https://books.toscrape.com')

book = await tab.find(class_name='product_pod')

title = await book.find(tag_name='h3')          # em qualquer lugar dentro deste book
price = await book.find(class_name='price_color')
cover = await book.query('img.thumbnail')
```

Para navegar pela árvore do DOM de forma deliberada (apenas filhos diretos, irmãos, shadow roots), veja [Percorrer o DOM](dom-traversal.md).

## Lidar com elementos ausentes {#handle-missing-elements}

Por padrão, o `find()` levanta `ElementNotFound` quando nada corresponde. Passe `raise_exc=False` para obter `None` em vez disso, o que deixa elementos opcionais e lógica OU nas suas mãos.

```python
from pydoll.exceptions import ElementNotFound

# elemento obrigatório: deixe levantar a exceção
submit = await tab.find(id='submit')

# elemento opcional: trate o None
banner = await tab.find(class_name='promo-banner', timeout=2, raise_exc=False)
if banner:
    close = await banner.find(class_name='close')
    await close.click()

# lógica OU: tente um atributo, depois outro
checkbox = (
    await tab.find(id='terms', raise_exc=False)
    or await tab.find(name='accept_terms', raise_exc=False)
)
```

## Prefira seletores estáveis

Escolha atributos que dificilmente mudarão em um redesign. A estrutura do seu DOM muda com frequência, então seletores que dependem dela quebram com facilidade.

```python
# semântico e estável: sobrevive a um redesign
await tab.find(id='user-profile')
await tab.find(data_testid='submit-button')
await tab.find(name='username')

# preso à estrutura: quebra no momento em que o layout muda
await tab.query('div > div > div:nth-child(3) > input')
```

Use o seletor mais simples que funcione, e só adicione complexidade quando a página exigir. Use `find()` para buscas baseadas em atributos e `query()` para padrões CSS ou XPath que o `find()` não consegue expressar.

## Exemplo completo: fazer login e ler o resultado

Isto faz login em [quotes.toscrape.com](https://quotes.toscrape.com/login) (que aceita quaisquer credenciais) e confirma o resultado encontrando o link de Logout.

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

## Próximos passos

- [Percorrer o DOM](dom-traversal.md): navegue de um elemento para seus filhos, irmãos e shadow roots.
- [Seletores: CSS e XPath](../basics/selectors.md): escolha e escreva o seletor certo.
- [Extração estruturada](structured-extraction.md): extraia dados tipados de muitos elementos de uma vez com um modelo.
