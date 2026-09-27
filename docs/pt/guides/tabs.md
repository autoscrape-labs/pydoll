# Abas

Uma aba é o objeto que você controla: navegação, busca de elementos e tudo em uma página acontece através dela. Um navegador pode manter muitas abas ao mesmo tempo, e você pode controlá-las de forma concorrente em vez de uma de cada vez.

## Abrir e fechar abas

`browser.start()` te dá a primeira aba. `browser.new_tab()` abre mais, e `tab.close()` fecha uma. O próprio navegador fecha quando o bloco `with` termina, levando toda aba junto.

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://news.ycombinator.com')

            # abre outra aba, já navegada
            docs = browser.new_tab('https://en.wikipedia.org/wiki/Web_scraping')
            print(docs.title)

            docs.close()

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll.browser.chromium import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://news.ycombinator.com')

            # abre outra aba, já navegada
            docs = await browser.new_tab('https://en.wikipedia.org/wiki/Web_scraping')
            print(await docs.title)

            await docs.close()

    asyncio.run(main())
    ```

Passe uma URL para `new_tab(url)` e a aba navega até lá antes de retornar. Chame `new_tab()` sem argumento para uma aba em branco que você navega depois.

## Fazer scraping de várias páginas de uma vez

Dê a cada página sua própria aba e carregue todas ao mesmo tempo, para que os tempos de carregamento se sobreponham em vez de se somarem: um pool de threads na API síncrona, em que cada thread bloqueia na sua própria aba, ou `asyncio.gather` na API assíncrona. Reutilize a aba de `start()` como o primeiro worker em vez de deixá-la ociosa.

=== "Sync"

    ```python
    from concurrent.futures import ThreadPoolExecutor

    from pydoll.sync import Chrome


    def title_of(tab, url):
        tab.go_to(url)
        return tab.title


    def main():
        urls = [
            'https://en.wikipedia.org/wiki/Async/await',
            'https://en.wikipedia.org/wiki/Coroutine',
            'https://en.wikipedia.org/wiki/Web_scraping',
        ]
        with Chrome() as browser:
            first = browser.start()
            tabs = [first] + [browser.new_tab() for _ in urls[1:]]

            with ThreadPoolExecutor() as pool:
                titles = list(pool.map(title_of, tabs, urls))
            for title in titles:
                print(title)

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll.browser.chromium import Chrome


    async def title_of(tab, url):
        await tab.go_to(url)
        return await tab.title


    async def main():
        urls = [
            'https://en.wikipedia.org/wiki/Async/await',
            'https://en.wikipedia.org/wiki/Coroutine',
            'https://en.wikipedia.org/wiki/Web_scraping',
        ]
        async with Chrome() as browser:
            first = await browser.start()
            tabs = [first] + [await browser.new_tab() for _ in urls[1:]]

            titles = await asyncio.gather(*(title_of(tab, url) for tab, url in zip(tabs, urls)))
            for title in titles:
                print(title)

    asyncio.run(main())
    ```

As três páginas carregam de forma concorrente, então a execução leva mais ou menos o tempo da página isolada mais lenta. As chamadas síncronas podem ser feitas de várias threads ao mesmo tempo com segurança. Veja [Python assíncrono na prática](../basics/async-python.md) para entender como o `gather` funciona.

## Listar as abas abertas

`browser.get_opened_tabs()` retorna toda aba aberta. O último item é o aberto mais recentemente.

=== "Sync"

    ```python
    with Chrome() as browser:
        browser.start()
        browser.new_tab('https://github.com')
        browser.new_tab('https://news.ycombinator.com')

        tabs = browser.get_opened_tabs()
        for tab in tabs:
            print(tab.current_url)
    ```

=== "Async"

    ```python
    async with Chrome() as browser:
        await browser.start()
        await browser.new_tab('https://github.com')
        await browser.new_tab('https://news.ycombinator.com')

        tabs = await browser.get_opened_tabs()
        for tab in tabs:
            print(await tab.current_url)
    ```

## Lidar com uma aba que a página abriu

Quando um clique abre uma aba (um link com `target="_blank"`), ela aparece em `get_opened_tabs()`. Compare a lista antes e depois do clique, e a nova aba é a última.

=== "Sync"

    ```python
    before = len(browser.get_opened_tabs())

    link = tab.find(text='Open in new tab')
    link.click()

    tabs = browser.get_opened_tabs()
    if len(tabs) > before:
        new_tab = tabs[-1]
        print(new_tab.current_url)
    ```

=== "Async"

    ```python
    before = len(await browser.get_opened_tabs())

    link = await tab.find(text='Open in new tab')
    await link.click()

    tabs = await browser.get_opened_tabs()
    if len(tabs) > before:
        new_tab = tabs[-1]
        print(await new_tab.current_url)
    ```

## Trazer uma aba para frente

A automação controla abas em segundo plano sem problema, mas algumas páginas só rodam timers ou animações enquanto estão visíveis. `bring_to_front()` torna uma aba a ativa.

=== "Sync"

    ```python
    background_tab.bring_to_front()
    ```

=== "Async"

    ```python
    await background_tab.bring_to_front()
    ```

## Próximos passos

- [Contextos do navegador](browser-contexts.md): dê às abas cookies e sessões isolados.
- [Cookies e sessões](cookies-and-sessions.md): leve um login entre abas.
- [Python assíncrono na prática](../basics/async-python.md): o padrão `gather` por trás das abas concorrentes.
