# Percorrer o DOM

Depois de ter um elemento, você muitas vezes precisa dos que estão ao redor dele: seus filhos, seus irmãos, elementos dentro de um shadow root, ou conteúdo dentro de um iframe. Este guia cobre a movimentação pela árvore do DOM a partir de um ponto de partida conhecido. Para localizar esse elemento inicial, veja [Encontrar elementos](element-finding.md).

<iframe scrolling="no" src="/docs/resources/visuals/dom-traversal-tree.html" aria-label="Move a focus through a DOM tree with parent, child, and sibling methods" style="width: 100%; height: 480px; border: 0;" loading="lazy"></iframe>

## Obter elementos filhos

O `get_children_elements()` retorna os descendentes de um elemento. `max_depth` controla até que profundidade ele vai (1 são apenas os filhos diretos), e `tag_filter` mantém somente as tags que você indicar.

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://books.toscrape.com')

            container = tab.find(class_name='row', tag_name='ol')

            direct = container.get_children_elements(max_depth=1)
            print(f'{len(direct)} direct children')

            # descendentes até 2 níveis de profundidade, apenas links
            links = container.get_children_elements(max_depth=2, tag_filter=['a'])
            print(f'{len(links)} links within two levels')

    main()
    ```

=== "Async"

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

            # descendentes até 2 níveis de profundidade, apenas links
            links = await container.get_children_elements(max_depth=2, tag_filter=['a'])
            print(f'{len(links)} links within two levels')

    asyncio.run(main())
    ```

## Obter elementos irmãos

O `get_siblings_elements()` retorna os elementos no mesmo nível do seu elemento, excluindo ele mesmo. `tag_filter` restringe o resultado a tags específicas.

=== "Sync"

    ```python
    active = tab.find(class_name='active')

    siblings = active.get_siblings_elements()
    print(f'{len(siblings)} siblings')

    link_siblings = active.get_siblings_elements(tag_filter=['a'])
    ```

=== "Async"

    ```python
    active = await tab.find(class_name='active')

    siblings = await active.get_siblings_elements()
    print(f'{len(siblings)} siblings')

    link_siblings = await active.get_siblings_elements(tag_filter=['a'])
    ```

## Busca com escopo vs filhos diretos

Um `find()` ou `query()` com escopo busca em **todos** os descendentes de um elemento. Quando você quer apenas os filhos diretos, use o combinador de filho do CSS `>` ou um passo XPath, que o `query()` aceita:

=== "Sync"

    ```python
    container = tab.find(id='cards')

    # todo .card em qualquer lugar da subárvore
    all_cards = container.find(class_name='card', find_all=True)

    # apenas os elementos .card que são filhos diretos
    direct_cards = container.query('> .card', find_all=True)
    ```

=== "Async"

    ```python
    container = await tab.find(id='cards')

    # todo .card em qualquer lugar da subárvore
    all_cards = await container.find(class_name='card', find_all=True)

    # apenas os elementos .card que são filhos diretos
    direct_cards = await container.query('> .card', find_all=True)
    ```

Use `get_children_elements()` quando quiser explorar a estrutura ou filtrar por tag; use um `find()`/`query()` com escopo quando quiser elementos que correspondam a atributos específicos em qualquer lugar da subárvore.

## Ler texto e atributos

De qualquer elemento você pode ler seu texto visível e seus atributos HTML:

=== "Sync"

    ```python
    book = tab.find(class_name='product_pod')

    title = book.find(tag_name='h3')
    print(title.text)                       # texto visível

    link = title.find(tag_name='a')
    print(link.get_attribute('href'))             # o valor de um atributo
    print(link.get_attribute('title'))
    ```

=== "Async"

    ```python
    book = await tab.find(class_name='product_pod')

    title = await book.find(tag_name='h3')
    print(await title.text)                       # texto visível

    link = await title.find(tag_name='a')
    print(link.get_attribute('href'))             # o valor de um atributo
    print(link.get_attribute('title'))
    ```

`text` é uma propriedade (aguardada com `await` na API assíncrona); `get_attribute(name)` retorna a string do atributo, ou `None` quando o atributo está ausente.

## Shadow DOM {#shadow-dom}

Muitos componentes escondem suas partes internas dentro de um [shadow root](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM), que consultas normais ao DOM não conseguem ver. Acesse o shadow host, obtenha seu shadow root, e então busque dentro dele.

=== "Sync"

    ```python
    host = tab.find(id='my-component')
    shadow = host.get_shadow_root()

    button = shadow.query('.internal-btn')
    button.click()
    ```

=== "Async"

    ```python
    host = await tab.find(id='my-component')
    shadow = await host.get_shadow_root()

    button = await shadow.query('.internal-btn')
    await button.click()
    ```

!!! warning "Dentro de um shadow root, use `query()` com CSS"
    `find()` e XPath não são suportados em um `ShadowRoot` e levantam `NotImplementedError`. Busque em shadow roots apenas com `query()` e seletores CSS.

O `query()` dentro de um shadow root recebe os parâmetros habituais `find_all`, `timeout` e `raise_exc`:

=== "Sync"

    ```python
    items = shadow.query('.item', find_all=True)
    dynamic = shadow.query('#late', timeout=5, raise_exc=False)
    ```

=== "Async"

    ```python
    items = await shadow.query('.item', find_all=True)
    dynamic = await shadow.query('#late', timeout=5, raise_exc=False)
    ```

Web components se aninham, então um shadow root pode conter outro shadow host:

=== "Sync"

    ```python
    outer = tab.find(tag_name='outer-component')
    outer_shadow = outer.get_shadow_root()

    inner = outer_shadow.query('inner-component')
    inner_shadow = inner.get_shadow_root()

    deep = inner_shadow.query('.deep-btn')
    ```

=== "Async"

    ```python
    outer = await tab.find(tag_name='outer-component')
    outer_shadow = await outer.get_shadow_root()

    inner = await outer_shadow.query('inner-component')
    inner_shadow = await inner.get_shadow_root()

    deep = await inner_shadow.query('.deep-btn')
    ```

### Descobrir shadow roots em uma página

Quando você não sabe quais shadow roots existem (depuração, ou widgets dinâmicos como o Cloudflare Turnstile), `find_shadow_roots()` retorna todos eles. Shadow hosts costumam carregar tarde, então passe `timeout` para verificar repetidamente até que apareçam:

=== "Sync"

    ```python
    shadow_roots = tab.find_shadow_roots(timeout=10)

    for sr in shadow_roots:
        print(f'mode={sr.mode}, host={sr.host_element}')
        checkbox = sr.query('input[type="checkbox"]', raise_exc=False)
        if checkbox:
            checkbox.click()
    ```

=== "Async"

    ```python
    shadow_roots = await tab.find_shadow_roots(timeout=10)

    for sr in shadow_roots:
        print(f'mode={sr.mode}, host={sr.host_element}')
        checkbox = await sr.query('input[type="checkbox"]', raise_exc=False)
        if checkbox:
            await checkbox.click()
    ```

Por padrão a busca cobre o documento principal (incluindo iframes de mesma origem). Passe `deep=True` para também alcançar shadow roots dentro de iframes de origem cruzada (OOPIFs), que é o que widgets como o Turnstile usam:

=== "Sync"

    ```python
    shadow_roots = tab.find_shadow_roots(deep=True, timeout=10)
    ```

=== "Async"

    ```python
    shadow_roots = await tab.find_shadow_roots(deep=True, timeout=10)
    ```

## Trabalhar dentro de um iframe

Um iframe tem seu próprio contexto de DOM. Encontre o elemento iframe, e então chame `find()` ou `query()` nele; o Pydoll direciona a busca para dentro do frame automaticamente. Continue encadeando para iframes aninhados.

=== "Sync"

    ```python
    iframe = tab.query('iframe.embedded-content', timeout=10)

    button = iframe.find(tag_name='button', class_name='submit')
    button.click()

    # iframe aninhado
    inner = iframe.find(tag_name='iframe')
    link = inner.find(text='Download PDF')
    link.click()
    ```

=== "Async"

    ```python
    iframe = await tab.query('iframe.embedded-content', timeout=10)

    button = await iframe.find(tag_name='button', class_name='submit')
    await button.click()

    # iframe aninhado
    inner = await iframe.find(tag_name='iframe')
    link = await inner.find(text='Download PDF')
    await link.click()
    ```

Para um guia completo de iframes, incluindo frames de CAPTCHA e resolução de problemas, veja [Iframes](iframes.md).

!!! note "Capturas de tela dentro de iframes"
    `tab.take_screenshot()` captura apenas a página de nível superior. Para capturar o conteúdo de um iframe, encontre um elemento dentro do frame e chame `element.take_screenshot()`.

## Próximos passos

- [Encontrar elementos](element-finding.md): localize os elementos a partir dos quais você navega.
- [Iframes](iframes.md): o guia completo para contextos de frame.
- [Extração estruturada](structured-extraction.md): deixe um modelo percorrer estruturas repetidas por você.
