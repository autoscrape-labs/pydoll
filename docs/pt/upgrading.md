# Atualizando para o Pydoll 3

O Pydoll 3 torna a API síncrona parte de primeira classe da biblioteca e limpa a superfície que cresceu em volta da assíncrona. Um script do Pydoll 2 precisa de três mudanças mecânicas, e as APIs que já estavam obsoletas na 2.x foram removidas. Nada mudou na forma como o navegador é controlado.

**Você vai aprender**

- [De onde importar](#importe-de-pydoll)
- [Quais propriedades viraram métodos](#chame-o-que-antes-era-propriedade)
- [Quais APIs obsoletas foram removidas](#apis-removidas)

## Importe de `pydoll` {#importe-de-pydoll}

As classes que você usa em todo script são exportadas pelo pacote de nível superior. A API síncrona exporta os mesmos nomes em `pydoll.sync`, então as duas formas diferem em uma linha de import.

=== "Sync"

    ```python
    from pydoll.sync import Chrome, ChromiumOptions, Key
    ```

=== "Async"

    ```python
    from pydoll import Chrome, ChromiumOptions, Key
    ```

Os caminhos antigos continuam funcionando (`pydoll.browser.chromium`, `pydoll.browser.options`, `pydoll.constants`), então essa mudança é opcional. Os nomes disponíveis no nível superior são `Chrome`, `Edge`, `ChromiumOptions`, `Tab`, `WebElement`, `ShadowRoot`, `Keyboard`, `Mouse`, `Scroll`, `Request`, `RequestHandle`, `Response`, `ResponseHandle`, `DownloadHandle`, `Key`, `ExtractionModel`, `Field`, `PageEvent`, `NetworkEvent` e `FetchEvent`.

## Chame o que antes era propriedade {#chame-o-que-antes-era-propriedade}

O Pydoll 2 expunha alguns valores como propriedades que precisavam de `await`. Uma propriedade que precisa de `await` surpreende leitores e IDEs, e não tinha um equivalente síncrono honesto, então no Pydoll 3 cada uma delas é um método:

| Pydoll 2 | Pydoll 3 |
|----------|----------|
| `await tab.title` | `await tab.title()` |
| `await tab.current_url` | `await tab.current_url()` |
| `await tab.page_source` | `await tab.page_source()` |
| `await element.text` | `await element.text()` |
| `await element.inner_html` | `await element.inner_html()` |
| `await element.bounds` | `await element.bounds()` |
| `await element.iframe_context` | `await element.iframe_context()` |
| `await shadow_root.inner_html` | `await shadow_root.inner_html()` |

Propriedades comuns, que nunca precisaram de `await`, não mudaram: `tab.keyboard`, `element.tag_name`, `element.is_enabled` e as demais.

=== "Sync"

    ```python
    from pydoll.sync import Chrome

    with Chrome() as browser:
        tab = browser.start()
        tab.go_to('https://quotes.toscrape.com')
        print(tab.title())
        print(tab.find(class_name='text').text())
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll import Chrome


    async def main():
        async with Chrome() as browser:
            tab = await browser.start()
            await tab.go_to('https://quotes.toscrape.com')
            print(await tab.title())
            print(await (await tab.find(class_name='text')).text())

    asyncio.run(main())
    ```

## APIs removidas {#apis-removidas}

Tudo que emitia `DeprecationWarning` no Pydoll 2 foi removido. Cada linha lista a substituição, que já funcionava na 2.x.

| Removido | Use no lugar |
|----------|--------------|
| `find_or_wait_element(by, value, ...)` | `find()` com atributos ou `query()` com um seletor; os dois aceitam `timeout`, `find_all` e `raise_exc`. Veja [Encontrar elementos](guides/element-finding.md). |
| `tab.get_frame(element)` | O próprio `WebElement` do iframe: `find()` e `query()` nele alcançam o conteúdo do frame. Veja [Iframes](guides/iframes.md). |
| `tab.execute_script(script, element)` | `element.execute_script(script)` |
| `element.key_down()`, `element.key_up()`, `element.press_keyboard_key()` | `tab.keyboard.down()`, `tab.keyboard.up()`, `tab.keyboard.press()`. Veja [Teclado](guides/keyboard.md). |
| `type_text(text, interval=...)` | `type_text(text, humanize=True)` |
| `browser.start(headless=True)` | `options.headless = True` antes de criar o navegador |
| `expect_and_bypass_cloudflare_captcha()` | `expect_cloudflare_turnstile()` |
| `enable_auto_solve_cloudflare_captcha()`, `disable_auto_solve_cloudflare_captcha()` | `expect_cloudflare_turnstile()` em volta da navegação; não há mais modo em segundo plano |
| `custom_selector` e `time_before_click` nesses métodos | Remova-os; o widget Turnstile é localizado automaticamente |
| Exceções `NotAnIFrame` e `IFrameNotFound` | Nada mais as lança |

O handle de download retornado por `tab.expect_download()` agora é a classe pública `DownloadHandle`, importável de `pydoll` e `pydoll.sync`.

## Próximos passos

- [Primeiros passos](getting-started.md): o primeiro script, nas duas formas.
- [Conceitos centrais](guides/core-concepts.md#sync-and-async): como as APIs síncrona e assíncrona se relacionam.
- [Migrando do Selenium e Playwright](migrating.md): se você vem de outra ferramenta.
