# API do Playwright

`pydoll.playwright` é uma API compatível com o Playwright para a superfície de automação de navegador: as mesmas classes, métodos, seletores e eventos que o seu script Playwright em Python já usa, executados pela conexão CDP do Pydoll, sem processo driver. Esta página é o contrato: o que está implementado por completo, o que funciona com uma diferença nomeada e o que falta, para você saber antes de trocar. Para a versão de cinco minutos, comece por [Traga seu script Playwright](../playwright.md).

A regra que rege a lista: se um script de automação de navegador funciona no Playwright e não aqui, é bug, e [uma issue](https://github.com/autoscrape-labs/pydoll/issues) com o script é bem-vinda. Recursos do test runner não são bugs; estão fora do escopo.

## Caminhos de import

| Playwright | Pydoll |
|------------|--------|
| `from playwright.sync_api import sync_playwright` | `from pydoll.playwright.sync_api import sync_playwright` |
| `from playwright.async_api import async_playwright` | `from pydoll.playwright.async_api import async_playwright` |
| `from playwright.sync_api import Page, Locator, ...` | `from pydoll.playwright.sync_api import Page, Locator, ...` |
| `playwright.sync_api.TimeoutError`, `Error` | `pydoll.playwright.sync_api.TimeoutError`, `Error` |

O módulo sync é gerado a partir do async, como o do próprio Playwright, então os dois nunca diferem em métodos ou argumentos.

## Matriz de compatibilidade

**Completo** significa mesma assinatura e mesmo comportamento. **Parcial** significa que funciona e a diferença está nomeada ao lado. **Ausente** significa não implementado, com a forma Pydoll de fazer quando existe uma.

### Playwright e BrowserType

| Membro | Status | Notas |
|--------|--------|-------|
| `chromium.launch()` | Completo | `headless`, `args`, `executable_path`, `proxy`, `downloads_path` mapeiam para [ChromiumOptions](browser-options.md) |
| `chromium.launch_persistent_context()` | Completo | |
| `chromium.connect_over_cdp()` | Completo | |
| `selectors.set_test_id_attribute()` | Completo | |
| `devices` | Completo | |
| `firefox`, `webkit` | Ausente | O Pydoll controla apenas navegadores baseados em Chromium; lança `Error` |
| `chromium.connect()` | Ausente | O protocolo do servidor Playwright não tem equivalente; use `connect_over_cdp` |
| `request` (`APIRequestContext`) | Ausente | Use [requisições HTTP no contexto do navegador](http-requests.md) por `page.tab.request` |

Aceitos e ignorados em `launch()`: `slow_mo`, `devtools`, `env`, `ignore_default_args`, `channel`, `chromium_sandbox`, `handle_sigint` e afins.

### Browser

| Membro | Status | Notas |
|--------|--------|-------|
| `new_context()`, `new_page()`, `contexts`, `version`, `close()` | Completo | |
| Evento `disconnected` | Parcial | Dispara quando você chama `close()`; não dispara quando o processo do navegador morre por conta própria |
| `new_browser_cdp_session()` | Ausente | Use `browser.chrome.execute_command(...)` |
| `start_tracing()`, `stop_tracing()` | Ausente | Fora do escopo |

### BrowserContext

| Membro | Status | Notas |
|--------|--------|-------|
| `new_page()`, `pages`, `close()` | Completo | |
| `cookies()`, `add_cookies()`, `clear_cookies()` | Completo | |
| `storage_state()` | Completo | Leitura e escrita |
| `grant_permissions()`, `clear_permissions()`, `set_geolocation()` | Completo | |
| `set_extra_http_headers()`, `set_offline()` | Completo | |
| `add_init_script()`, `expose_function()`, `expose_binding()` | Completo | |
| `route()`, `unroute()`, `route_from_har()` | Parcial | `route` e `unroute` são completos; `route_from_har` está ausente |
| `expect_page()`, `expect_event()`, `wait_for_event()` | Completo | |
| `set_default_timeout()`, `set_default_navigation_timeout()` | Completo | |
| Opções: `viewport`, `user_agent`, `locale`, `timezone_id`, `extra_http_headers`, `storage_state`, `permissions`, `offline`, `base_url`, `http_credentials`, `ignore_https_errors`, `java_script_enabled`, `bypass_csp`, `color_scheme`, `device_scale_factor`, `is_mobile`, `has_touch` | Completo | `http_credentials` respondem ao desafio `401` pelo domínio Fetch em vez de enviar um header fixo |
| Opções: `record_video_dir`, `record_har_path`, `client_certificates`, `service_workers`, `strict_selectors`, `accept_downloads=False` | Parcial | Aceitas e ignoradas |
| `new_cdp_session()` | Ausente | Use `page.tab.execute_command(...)` |
| `request` (`APIRequestContext`) | Ausente | Use `page.tab.request` |
| `tracing`, `clock` | Ausente | Fora do escopo |

### Page

| Membro | Status | Notas |
|--------|--------|-------|
| `goto()`, `reload()`, `go_back()`, `go_forward()` | Completo | `wait_until='commit'` resolve quando o novo documento é confirmado (commit) |
| `wait_for_load_state()`, `wait_for_url()`, `expect_navigation()` | Completo | |
| `evaluate()`, `evaluate_handle()` | Parcial | Roda no main world sem `eval`; `Date` volta como string ISO, `undefined` e `null` viram `None` |
| `query_selector()`, `query_selector_all()`, `wait_for_selector()`, `wait_for_function()`, `wait_for_timeout()` | Completo | |
| `content()`, `set_content()`, `title()`, `url` | Completo | |
| `frames`, `main_frame`, `frame()`, `frame_locator()` | Parcial | `frames` é preenchido por eventos de frame; um frame filho reporta o documento do pai até resolver, pouco depois de ser anexado |
| `add_init_script()`, `add_script_tag()`, `add_style_tag()` | Completo | |
| `set_viewport_size()`, `viewport_size`, `emulate_media()`, `set_extra_http_headers()` | Completo | |
| `screenshot()`, `pdf()` | Parcial | As opções `mask`, `animations`, `caret`, `scale` e `style` de `screenshot` são aceitas e ignoradas |
| `route()`, `unroute()`, `expose_function()`, `expose_binding()` | Completo | |
| `keyboard`, `mouse`, `touchscreen` | Completo | Nomes de tecla do Playwright com o layout US: `Enter`, `Control+A`, `KeyA`, `Digit1` |
| Atalhos de seletor: `click()`, `fill()`, `type()`, `press()`, `check()`, `select_option()`, `text_content()`, `inner_text()`, `inner_html()`, `get_attribute()`, `is_visible()`, ... | Completo | |
| `get_by_role()`, `get_by_text()`, `get_by_label()`, `get_by_placeholder()`, `get_by_alt_text()`, `get_by_title()`, `get_by_test_id()` | Completo | Papéis ARIA e nomes acessíveis calculados com um porte do algoritmo do Playwright |
| Eventos: `load`, `domcontentloaded`, `framenavigated`, `request`, `response`, `requestfinished`, `requestfailed`, `dialog`, `console`, `pageerror`, `download`, `popup`, `filechooser`, `close`, `crash` | Completo | Com os context managers `expect_*` correspondentes; `console` e `pageerror` são os únicos listeners que habilitam o domínio `Runtime` |
| Eventos: `websocket`, `worker` | Ausente | |
| `wait_for_request()`, `wait_for_response()` | Ausente | Use `expect_request()` e `expect_response()` |
| `pause()`, `add_locator_handler()`, `aria_snapshot()`, `clock` | Ausente | Fora do escopo |
| `request` (`APIRequestContext`) | Ausente | Use `page.tab.request` |

### Frame, FrameLocator, Locator, ElementHandle, JSHandle

| Membro | Status | Notas |
|--------|--------|-------|
| O conjunto completo de métodos, incluindo `filter()`, `and_()`, `or_()`, `nth()`, `first`, `last`, `count()`, `all()`, `drag_to()`, `select_option()`, `set_input_files()`, `screenshot()`, `evaluate_all()`, `bounding_box()`, `scroll_into_view_if_needed()`, `dispatch_event()` | Completo | Locators são preguiçosos e estritos; as ações seguem as verificações de acionabilidade do Playwright e produzem o mesmo call log em timeout |
| `set_input_files()` | Completo | Caminhos e `FilePayload` |
| `highlight()`, `aria_snapshot()` | Ausente | |

### Seletores

| Sintaxe | Status | Notas |
|---------|--------|-------|
| CSS, XPath, `text=`, `xpath=`, `css=`, `id=`, `data-testid=`, `nth=`, `visible=`, encadeamento com `>>`, engines `internal:` por trás de `get_by_*` | Completo | |
| Pseudo-classes CSS do Playwright `:has-text()`, `:visible`, `:nth-match()`, `:text()` | Ausente | Use `get_by_text()`, `filter(has_text=...)`, `locator(...).nth()` |
| Seletores de layout `:left-of()`, `:right-of()`, `:above()`, `:below()`, `:near()` | Ausente | |
| Engines `react=`, `vue=` e engines de seletor personalizadas | Ausente | |

### Request, Response, Route, Dialog, Download, ConsoleMessage, FileChooser

Completo. O roteamento roda no domínio Fetch que a [interceptação de requisições](request-interception.md) usa. `route.fetch()` deixa a requisição chegar à rede e pausa de novo na etapa de resposta, então um handler pode reescrever um corpo com `route.fulfill(response=..., body=...)`.

### Fora do escopo

Assertions `expect()`, o plugin `pytest-playwright` e suas fixtures, tracing, gravação de vídeo, replay de HAR, `Clock`, `Tracing`, `Worker`, `WebSocket`, `Android`, `Electron`. Um script que precisa do test runner continua usando o Playwright para o runner; a automação de navegador dentro de um teste ainda pode ser Pydoll por `connect_over_cdp`.

## Comportamentos que diferem de propósito

Vêm dos padrões de stealth do Pydoll e ficam por baixo da superfície Playwright:

- Avaliações rodam sem gesto de usuário sintético, então `navigator.userActivation` fica falso até um clique real. Defina `user_gesture_on_evaluate=True` no contexto se um script precisa de `window.open` a partir de `evaluate`.
- Popups são bloqueados a menos que uma ação do usuário os abra, como em um Chrome normal.
- Ações não esperam por uma navegação que elas mesmas iniciam, e `no_wait_after` é aceito e ignorado. Quando um clique envia um formulário ou segue um link, espere com `page.wait_for_url()` ou `page.expect_navigation()` antes de ler a nova página.
- Um override de `user_agent` vem com Client Hints coerentes e segue o formato de UA reduzido do Chrome; a string que você passa é normalizada do jeito que o Pydoll faz nas próprias opções. `locale` define um `Accept-Language` com a forma do Chrome.
- `http_credentials` só respondem a um desafio da própria origem.
- Um iframe cross-origin que o Chrome renderiza em outro processo não é alcançável por `frame_locator()` nem por uma cadeia de seletores que entra no frame: o motor de seletores vive na sessão do pai, e a consulta teria de rodar na do filho. Para esses frames, use `element_handle.content_frame()` e os métodos do próprio frame.
- Init scripts, bindings e emulação definidos no contexto só alcançam um popup depois que ele é adotado, então perdem o primeiríssimo documento do popup.
- A emulação de viewport mantém `screen` pelo menos tão grande quanto a viewport, para que os dois nunca se contradigam.
- O engine de seletores e acionabilidade roda em um isolated world de cada frame, avaliado uma vez e reutilizado, então uma página que envolve os protótipos do DOM, `requestAnimationFrame` ou `window.eval` nunca o vê. O seu próprio código de `page.evaluate` roda no main world, onde vivem os globais da página, e o código-fonte vai embutido na chamada em vez de passar por `eval`.

## Alcançando o Pydoll

| Objeto Playwright | Objeto Pydoll por baixo |
|-------------------|-------------------------|
| `browser.chrome` | [Chrome](../api/browser/chrome.md) |
| `page.tab` | [Tab](../api/browser/tab.md) |
| `locator.element_handle().web_element` | [WebElement](../api/elements/web_element.md) |

=== "Sync"

    ```python
    with page.tab.expect_cloudflare_turnstile():
        page.goto('https://example.com/protected')

    button = page.get_by_role('button', name='Continue').element_handle().web_element
    button.click(humanize=True)
    ```

=== "Async"

    ```python
    async with page.tab.expect_cloudflare_turnstile():
        await page.goto('https://example.com/protected')

    button = (await page.get_by_role('button', name='Continue').element_handle()).web_element
    await button.click(humanize=True)
    ```

## Próximos passos

- [Traga seu script Playwright](../playwright.md): o passo a passo, com a nota honesta sobre o que a detecção ainda vê.
- [Interceptação de requisições](request-interception.md): o domínio Fetch sobre o qual as rotas são construídas.
- [Migrando do Selenium e do Playwright](../migrating.md): os mesmos movimentos na API própria do Pydoll.
