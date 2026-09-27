# Traga seu script Playwright

Seu script Playwright funciona até um site começar a bloqueá-lo. O Pydoll roda o mesmo script sobre CDP puro, sem processo driver e sem navegador patcheado, então não há nada para um detector encontrar no transporte e nada para você reescrever. Esta página pega um script Playwright existente, coloca ele para rodar no Pydoll em cinco minutos e depois mostra onde o Pydoll vai além do Playwright quando você precisar.

**Você vai aprender**

- [Como trocar um script com um import](#swap-the-import)
- [O que mudou por baixo do seu script](#what-changed-under-your-script)
- [Como usar recursos do Pydoll a partir de um script Playwright](#reach-pydoll-from-a-playwright-object)
- [O que isso muda e o que não muda na detecção](#what-this-does-not-change)

## Troque o import {#swap-the-import}

Substitua `playwright.sync_api` por `pydoll.playwright.sync_api`, ou `playwright.async_api` por `pydoll.playwright.async_api`. Todo o resto fica igual. Você não instala o pacote `playwright` nem os navegadores que ele baixa; o Pydoll controla o Chrome ou o Edge que já está na sua máquina.

=== "Sync"

    ```python
    from pydoll.playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://quotes.toscrape.com/login')

        page.get_by_label('Username').fill('john')
        page.locator('#password').fill('SecretPass123')
        page.get_by_role('button', name='Login').click()
        page.wait_for_url('**/')

        print(page.get_by_role('link', name='Logout').is_visible())
        browser.close()
    ```

=== "Async"

    ```python
    import asyncio

    from pydoll.playwright.async_api import async_playwright


    async def main():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://quotes.toscrape.com/login')

            await page.get_by_label('Username').fill('john')
            await page.locator('#password').fill('SecretPass123')
            await page.get_by_role('button', name='Login').click()
            await page.wait_for_url('**/')

            print(await page.get_by_role('link', name='Logout').is_visible())
            await browser.close()

    asyncio.run(main())
    ```

Rode do jeito que sempre rodou. Os locators continuam preguiçosos e estritos, `get_by_role` resolve os mesmos elementos, as ações esperam o elemento estar anexado, visível, estável e habilitado, e uma espera que falha lança o mesmo `TimeoutError` com o mesmo call log.

`chromium.launch()` aceita as opções que você já passa: `headless`, `args`, `executable_path`, `proxy`, `downloads_path`. `launch_persistent_context(user_data_dir)` e `connect_over_cdp(url)` também funcionam. `firefox` e `webkit` lançam erro, porque o Pydoll controla apenas navegadores baseados em Chromium.

!!! note "Drop-in para a superfície de automação"
    A camada cobre o que um script usa: `Playwright`, `Browser`, `BrowserContext`, `Page`, `Frame`, `Locator`, `ElementHandle`, `Keyboard`, `Mouse`, rotas, diálogos e downloads. Ela não cobre o test runner: assertions `expect()`, fixtures, o plugin do pytest, tracing e vídeo não estão implementados. [API do Playwright](guides/playwright-api.md) lista cada classe com o que é completo, parcial ou ausente.

## O que mudou por baixo do seu script {#what-changed-under-your-script}

O Playwright fala com o navegador por um processo driver escrito em Node. Toda chamada atravessa esse processo, que então fala CDP com o Chrome. Forks de stealth como o Patchright patcheiam esse driver depois do fato, removendo as chamadas que entregam a automação.

O Pydoll não tem driver. Seu `page.goto` vira comandos CDP enviados direto do Python, pela mesma conexão que a API própria do Pydoll usa. Isso remove os sinais do transporte na origem em vez de patcheá-los:

- O domínio `Runtime`, cuja ativação é o sinal de automação mais conhecido, nunca é habilitado para o seu script. Seletores e verificações de acionabilidade rodam em um isolated world de cada frame, avaliado uma vez, e o seu código de `page.evaluate` roda no main world sem passar por `eval`.
- Sem `--enable-automation`, sem `navigator.webdriver`, sem hooks de console, sem init scripts injetados a cada navegação.
- Avaliações não carregam gesto de usuário sintético, popups só abrem a partir de uma ação real do usuário, e um override de `user_agent` vem com Client Hints coerentes, como em um navegador que alguém está usando.

O resto do navegador é um Chrome de verdade: as impressões digitais de TLS, HTTP/2 e renderização são as que o Chrome tem, porque é o Chrome.

## Alcance o Pydoll a partir de um objeto Playwright {#reach-pydoll-from-a-playwright-object}

Todo objeto Playwright expõe o objeto Pydoll por baixo, então recursos que o Playwright não tem nome para ficam a um atributo de distância. Você não reescreve o script para usá-los.

| Objeto Playwright | Objeto Pydoll por baixo |
|-------------------|-------------------------|
| `browser.chrome` | [Chrome](api/browser/chrome.md) |
| `page.tab` | [Tab](api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](api/elements/web_element.md) |

Três coisas que um script bloqueado costuma precisar em seguida, cada uma em uma linha:

=== "Sync"

    ```python
    from pydoll.sync import ExtractionModel, Field
    from pydoll.playwright.sync_api import sync_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        page.tab.enable_cloudflare_turnstile_handling()
        page.goto('https://quotes.toscrape.com')

        quotes = page.tab.extract_all(Quote, scope='.quote')
        submit = page.get_by_role('link', name='Login').element_handle().web_element
        submit.click(humanize=True)
    ```

=== "Async"

    ```python
    from pydoll import ExtractionModel, Field
    from pydoll.playwright.async_api import async_playwright

    from examples.fingerprints import FINGERPRINTS


    class Quote(ExtractionModel):
        text: str = Field(selector='.text')
        author: str = Field(selector='.author')


    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.tab.apply_fingerprint(FINGERPRINTS['macos_m3_new_york'])
        await page.tab.enable_cloudflare_turnstile_handling()
        await page.goto('https://quotes.toscrape.com')

        quotes = await page.tab.extract_all(Quote, scope='.quote')
        submit = (await page.get_by_role('link', name='Login').element_handle()).web_element
        await submit.click(humanize=True)
    ```

`apply_fingerprint` define uma identidade coerente em todas as camadas ([Injeção de fingerprint](stealth/fingerprint-injection.md)), `enable_cloudflare_turnstile_handling` clica no widget Turnstile quando uma página carrega com um ([Cloudflare Turnstile](stealth/captcha-bypass.md)), `extract_all` retorna objetos tipados e validados ([Extração estruturada](guides/structured-extraction.md)), e `humanize=True` move o mouse por um caminho curvo com tempo humano ([Interações humanizadas](stealth/human-like-interactions.md)). CDP cru também está a uma chamada de distância: `page.tab.execute_command(...)`.

## O que isso não muda {#what-this-does-not-change}

!!! warning "O que a detecção ainda vê"
    O Pydoll remove os sinais de automação que uma biblioteca adiciona; ele não transforma um bot em pessoa. Um navegador headless continua reconhecível pela renderização e pela falta de dispositivos de mídia, então rode com janela ou aplique um perfil de fingerprint que cubra os sinais de headless. A reputação do seu IP conta tanto quanto o navegador; um IP de datacenter falha em desafios que um residencial passa. Sinais embutidos no binário do Chrome não são tocados. E o comportamento importa: cliques instantâneos e digitação perfeitamente regular parecem o que são, e é para isso que existe o `humanize=True`.

[Passando despercebido](stealth/index.md) percorre cada camada com o mínimo de configuração para ela.

## Próximos passos

- [API do Playwright](guides/playwright-api.md): a matriz completa de compatibilidade e os comportamentos que diferem.
- [Passando despercebido](stealth/index.md): identidade, comportamento e desafios, nessa ordem.
- [Migrando do Selenium e do Playwright](migrating.md): os mesmos movimentos na API própria do Pydoll, quando quiser ir para o nativo.
