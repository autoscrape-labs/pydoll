# Esperas

As páginas mudam depois de carregar: um spinner some, um botão fica habilitado, um clique dispara uma requisição, o envio de um formulário navega. O Pydoll oferece uma espera para cada um desses momentos, então você aguarda exatamente o que precisa em vez de dormir e torcer. Toda espera lança `WaitTimeout` (ou `WaitElementTimeout`, para estados de elemento) quando o tempo acaba.

## Aguardar um estado do elemento

`find()` com `timeout` aguarda um elemento existir. `wait_until()` aguarda o que vem depois: o elemento ficar visível, oculto, habilitado, interagível ou removido da página. Defina uma ou mais condições e a chamada retorna quando todas valem.

=== "Sync"

    ```python
    from pydoll import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            tab.find(tag_name='button').click()

            loading = tab.find(id='loading')
            loading.wait_until(is_hidden=True, timeout=10)

            print(tab.find(id='finish').text())

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://the-internet.herokuapp.com/dynamic_loading/1')

            await (await tab.find(tag_name='button')).click()

            loading = await tab.find(id='loading')
            await loading.wait_until(is_hidden=True, timeout=10)

            print(await (await tab.find(id='finish')).text())

    asyncio.run(main())
    ```

As condições que você pode definir:

| Flag | Vale quando |
|------|-------------|
| `is_visible` | O elemento tem uma caixa na tela e não está oculto por CSS. |
| `is_hidden` | O oposto de `is_visible`. |
| `is_enabled` | O elemento não tem o atributo `disabled`. |
| `is_interactable` | O elemento está visível, por cima dos outros e pode receber um clique. |
| `is_detached` | O elemento foi removido do DOM. |

Cada elemento também responde às mesmas perguntas diretamente: `is_visible()`, `is_enabled()`, `is_interactable()`, `is_on_top()` e `is_detached()`.

## Aguardar um elemento sumir

Quando você nunca segurou o elemento, ou um novo `find()` continuaria encontrando outro igual, aguarde pela tab. `wait_for_absence()` aceita os mesmos critérios de `find()` e retorna quando nada corresponde.

=== "Sync"

    ```python
    tab.find(text='Iniciar').click()
    tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

=== "Async"

    ```python
    await (await tab.find(text='Iniciar')).click()
    await tab.wait_for_absence(class_name='spinner', timeout=10)
    ```

## Aguardar uma URL

Aplicações de página única mudam a URL sem carregar a página. `wait_for_url()` consulta a URL atual até ela corresponder e retorna a URL que correspondeu. O padrão pode ser um glob, uma expressão regular compilada ou um callable que recebe a URL e retorna um bool.

=== "Sync"

    ```python
    import re

    tab.find(id='checkout').click()

    tab.wait_for_url('**/checkout/*', timeout=10)
    tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

=== "Async"

    ```python
    import re

    await (await tab.find(id='checkout')).click()

    await tab.wait_for_url('**/checkout/*', timeout=10)
    await tab.wait_for_url(re.compile(r'/checkout/\d+$'))
    await tab.wait_for_url(lambda url: 'checkout' in url and 'error' not in url)
    ```

Em um glob, `*` corresponde a qualquer coisa exceto `/`, `**` corresponde a qualquer coisa incluindo `/`, e `{a,b}` corresponde a qualquer uma das alternativas. As mesmas três formas de padrão funcionam em todo lugar deste guia que aceita um padrão de URL.

## Aguardar uma condição em JavaScript

`wait_for_script()` avalia uma expressão na página até ela retornar um valor verdadeiro, e retorna esse valor. Use para estado que o DOM não mostra: uma global definida pela aplicação, a flag de pronto de um store, uma contagem.

=== "Sync"

    ```python
    tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

=== "Async"

    ```python
    await tab.wait_for_script('window.dataLayer && window.dataLayer.length > 0', timeout=10)

    rows = await tab.wait_for_script("document.querySelectorAll('tr.row').length >= 20")
    print(rows)
    ```

## Aguardar a rede ficar quieta

`wait_for_network_idle()` retorna quando nenhuma requisição ficou em andamento por `idle_time` segundos. Chame logo depois da ação que inicia as requisições, porque só as requisições iniciadas depois da chamada são contadas.

=== "Sync"

    ```python
    tab.find(id='load-more').click()
    tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = tab.find(class_name='card', find_all=True)
    ```

=== "Async"

    ```python
    await (await tab.find(id='load-more')).click()
    await tab.wait_for_network_idle(idle_time=0.5, timeout=15)
    cards = await tab.find(class_name='card', find_all=True)
    ```

!!! note "Páginas que nunca ficam quietas"
    Beacons de analytics e long polling mantêm algumas páginas ocupadas para sempre. Nelas, aguarde o elemento ou a resposta de que você precisa em vez da rede inteira.

## Capturar a resposta que um clique dispara

Os dados que você quer costumam estar no JSON que a página busca, não no DOM. `expect_response()` é um gerenciador de contexto: entre nele, faça a ação dentro do bloco e, quando o bloco sai, o handle contém a primeira resposta correspondente, corpo incluído.

=== "Sync"

    ```python
    with tab.expect_response('**/api/prices*') as response:
        tab.find(id='refresh').click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

=== "Async"

    ```python
    async with tab.expect_response('**/api/prices*') as response:
        await (await tab.find(id='refresh')).click()

    print(response.status, response.headers['content-type'])
    prices = response.json()
    ```

O handle expõe `url`, `status`, `ok` (verdadeiro para status 2xx), `headers`, `mime_type` e `request_id`, além de `body()` em bytes, `text()` e `json()`. Ler um campo dentro do bloco, antes de algo chegar, lança `WaitTimeout`. Se o navegador falhou o carregamento depois de os cabeçalhos chegarem, `status` e `headers` continuam definidos e `body()` lança `WaitTimeout`.

`expect_request()` funciona do mesmo jeito para o lado de saída, e seu handle expõe `url`, `method`, `headers`, `post_data` e `resource_type`.

=== "Sync"

    ```python
    with tab.expect_request('**/api/search') as request:
        tab.find(id='search').click()

    print(request.method, request.post_data)
    ```

=== "Async"

    ```python
    async with tab.expect_request('**/api/search') as request:
        await (await tab.find(id='search')).click()

    print(request.method, request.post_data)
    ```

Os dois gerenciadores ligam os eventos de rede durante o bloco se estavam desligados, e os desligam de novo depois. Você não gerencia `enable_network_events()` por conta própria.

## Aguardar uma navegação que você causa

`go_to()` já aguarda a página carregar. Quando é um clique ou o envio de um formulário que navega, envolva-o em `expect_navigation()`: o bloco sai quando o frame principal mudou (para uma URL que corresponde a `url`, quando informada) e alcançou o estado de carregamento configurado em `options.page_load_state`.

=== "Sync"

    ```python
    with tab.expect_navigation(url='**/dashboard'):
        tab.find(id='login').click()

    print(tab.current_url())
    ```

=== "Async"

    ```python
    async with tab.expect_navigation(url='**/dashboard'):
        await (await tab.find(id='login')).click()

    print(await tab.current_url())
    ```

## Registre antes de agir

Os três gerenciadores `expect_*` começam a escutar quando você entra no bloco, e a ação vai dentro dele. Fazer a ação primeiro e só depois aguardar perderia uma resposta que chegou no meio, que é justamente o caso rápido que você quer tratar.

=== "Sync"

    ```python
    # o listener já está no lugar quando o clique dispara
    with tab.expect_response('**/api/data') as response:
        tab.find(id='fetch').click()
    ```

=== "Async"

    ```python
    # o listener já está no lugar quando o clique dispara
    async with tab.expect_response('**/api/data') as response:
        await (await tab.find(id='fetch')).click()
    ```

## Exemplo completo: ler uma API em vez do DOM

=== "Sync"

    ```python
    from pydoll import Chrome

    def main():
        with Chrome() as browser:
            tab = browser.start()
            tab.go_to('https://quotes.toscrape.com/scroll')

            with tab.expect_response('**/api/quotes?page=2') as response:
                tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            tab.wait_for_network_idle(idle_time=0.5)

    main()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com/scroll')

            async with tab.expect_response('**/api/quotes?page=2') as response:
                await tab.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            for quote in response.json()['quotes']:
                print(quote['author']['name'], '-', quote['text'][:60])

            await tab.wait_for_network_idle(idle_time=0.5)

    asyncio.run(main())
    ```

## Próximos passos

- [Encontrar elementos](element-finding.md): `find()` com timeout, a espera que vem antes de todas estas.
- [Monitoramento de rede](network-monitoring.md): observe todas as requisições da página, não só a que você espera.
- [Eventos](events.md): reaja a eventos de página e de rede conforme acontecem.
- [Repetição](retrying.md): execute um passo inteiro de novo quando uma espera expira.
