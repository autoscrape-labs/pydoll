# Opções do navegador

`ChromiumOptions` é o objeto que você configura antes de lançar o navegador. Ele guarda as flags de linha de comando, o binário do navegador a executar, timeouts e um punhado de configurações de conveniência. Você monta um, passa para `Chrome` ou `Edge`, e inicia.

## Configurar e lançar

Crie um `ChromiumOptions`, defina o que precisar e entregue-o ao navegador:

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions


async def main():
    options = ChromiumOptions()
    options.headless = True
    options.add_argument('--window-size=1920,1080')

    async with Chrome(options=options) as browser:
        tab = await browser.start()
        await tab.go_to('https://quotes.toscrape.com')

asyncio.run(main())
```

O mesmo objeto de opções funciona para o Edge; importe `Edge` em vez de `Chrome`.

## Adicionar flags de linha de comando

O Chromium aceita centenas de chaves de linha de comando. Use `add_argument()` para passar qualquer uma delas, `remove_argument()` para tirar uma, e `arguments` para ler a lista atual.

```python
options = ChromiumOptions()

options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')

options.remove_argument('--start-maximized')
print(options.arguments)
```

A lista completa de chaves é o [Chromium command-line switches](https://peter.sh/experiments/chromium-command-line-switches/) do Peter Beverloo. Algumas que aparecem com frequência: `--window-size=W,H` para uma viewport fixa, `--disable-gpu` em máquinas sem GPU, e o par para Docker abaixo.

!!! note "Não defina a porta de depuração você mesmo"
    O Pydoll gerencia `--remote-debugging-port` internamente. Passar sua própria `--remote-debugging-port` conflita com isso.

## Rodar em headless

Defina `headless` para rodar sem uma janela visível, que é o que você quer em um servidor ou em CI:

```python
options = ChromiumOptions()
options.headless = True   # adiciona a flag --headless
```

!!! warning "Headless é detectável"
    O Chrome headless vaza mais do que uma flag: ele renderiza WebGL por um rasterizador de software, não expõe plugins de PDF e reporta métricas de tela diferentes. Sistemas anti-bot checam tudo isso. Definir um User-Agent não esconde isso. Se você automatiza sites que combatem bots, rode headful ou neutralize os sinais de headless com [Injeção de fingerprint](../stealth/fingerprint-injection.md).

## Usar uma build de navegador diferente

Aponte `binary_location` para qualquer build Chromium (Beta, Canary, Chromium, Brave) em vez do padrão do sistema:

```python
options = ChromiumOptions()
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
```

## Esperar mais pela inicialização

`start_timeout` é quantos segundos o Pydoll espera o navegador subir antes de desistir. Aumente-o em máquinas lentas ou perfis pesados:

```python
options = ChromiumOptions()
options.start_timeout = 20   # segundos, padrão 10
```

## Escolher quando a navegação termina

`page_load_state` decide quando `tab.go_to()` retorna. `COMPLETE` (o padrão) espera cada recurso; `INTERACTIVE` retorna assim que o DOM está pronto, o que é mais rápido quando você só lê texto ou markup.

```python
from pydoll.constants import PageLoadState

options = ChromiumOptions()
options.page_load_state = PageLoadState.INTERACTIVE
```

Os três estados são `PageLoadState.COMPLETE`, `PageLoadState.INTERACTIVE` e `PageLoadState.LOADING`.

## Definir a pasta de downloads e os idiomas

Dois helpers cobrem as preferências mais comuns sem tocar no dicionário bruto de preferências:

```python
options = ChromiumOptions()
options.set_default_download_directory('/home/user/downloads')
options.set_accept_languages('en-US,en;q=0.9')
```

Para qualquer coisa mais profunda nas preferências do Chromium, veja [Preferências do navegador](browser-preferences.md).

## Silenciar o navegador

Um conjunto de propriedades booleanas alterna as interrupções que atrapalham a automação:

```python
options = ChromiumOptions()
options.block_popups = True
options.block_notifications = True
options.password_manager_enabled = False
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True   # baixa PDFs em vez de abrir o visualizador
```

## Proteger contra vazamentos de IP via WebRTC

O WebRTC pode revelar seu IP real mesmo atrás de um proxy. `webrtc_leak_protection` adiciona a flag que bloqueia UDP não roteado pelo proxy:

```python
options = ChromiumOptions()
options.webrtc_leak_protection = True
```

Use isso quando você roteia o tráfego por um [proxy](proxies.md).

## Rodar em Docker ou CI

Contêineres precisam de duas flags: `--no-sandbox` (o sandbox colide com o isolamento do contêiner) e `--disable-dev-shm-usage` (contêineres costumam ter um `/dev/shm` minúsculo).

```python
options = ChromiumOptions()
options.headless = True
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
```

!!! warning "`--no-sandbox` reduz a segurança do Chrome"
    Use apenas em um ambiente controlado (um contêiner, um runner de CI) onde você confia nas páginas que carrega. Não use ao visitar sites não confiáveis.

## Próximos passos

- [Preferências do navegador](browser-preferences.md): o dicionário de preferências mais profundo do Chromium.
- [Proxies](proxies.md): roteie o tráfego do navegador por um proxy.
- [Injeção de fingerprint](../stealth/fingerprint-injection.md): faça o headless passar por headful, e mantenha a identidade do navegador consistente.
