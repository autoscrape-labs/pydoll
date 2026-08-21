# Eventos

Eventos permitem que você reaja ao que o navegador faz, no momento em que acontece: uma página terminando de carregar, uma requisição saindo, uma resposta chegando, um diálogo abrindo. Em vez de ficar em um loop de polling adivinhando, você registra um callback e o Pydoll o executa no instante em que o evento dispara.

## Habilite e depois escute

Trabalhar com eventos é sempre a mesma sequência de três passos: habilite o domínio que te interessa, registre um callback com `on()` e depois deixe os eventos dispararem. Um callback registrado antes de seu domínio ser habilitado nunca roda, então habilite primeiro.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.page.events import PageEvent


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async def on_load(event):
            print('page finished loading')

        await tab.enable_page_events()
        await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(2)

asyncio.run(main())
```

`on(event_name, callback)` retorna um id inteiro que você pode usar depois para remover o callback. O callback pode ser síncrono ou assíncrono, e recebe um argumento: o evento.

<iframe src="/docs/resources/visuals/events-flow.html" aria-label="Events firing on a page and your callbacks running" style="width: 100%; height: 395px; border: 0;" loading="lazy"></iframe>

Pressione Navigate: os eventos disparam na página em ordem, e os callbacks que você registrou rodam conforme cada evento dispara.

## Leia os dados do evento

Todo evento é um dict com um nome `method` e um payload `params`. Você lê o que precisa de `event['params']`:

```python
{
    'method': 'Page.loadEventFired',
    'params': {'timestamp': 123456.789},
}
```

Cada tipo de evento é um `TypedDict` em `pydoll.protocol.<domain>.events`, então adicionar type hint a um callback te dá autocomplete nas chaves de `params`:

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent


async def on_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")
```

Os exemplos abaixo assumem uma `tab` em execução, como configurada no primeiro exemplo.

## Observe requisições e respostas de rede

Habilite o domínio de rede para ver cada requisição sair e cada resposta chegar:

```python
from pydoll.protocol.network.events import NetworkEvent


async def on_request(event):
    print(f"→ {event['params']['request']['url']}")


async def on_response(event):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")


await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)

await tab.go_to('https://news.ycombinator.com')
```

Para modificar ou bloquear requisições em vez de apenas observá-las, veja [Interceptação de requisições](request-interception.md).

## Execute um listener uma única vez

Passe `temporary=True` e o callback se remove depois de disparar pela primeira vez. É isso que você quer para uma configuração pontual que não deve se repetir a cada carregamento posterior:

```python
from pydoll.protocol.page.events import PageEvent

await tab.on(PageEvent.LOAD_EVENT_FIRED, on_load, temporary=True)

await tab.go_to('https://the-internet.herokuapp.com')  # dispara uma vez
await tab.refresh()                                      # não dispara de novo
```

## Espere por um evento específico

Eventos combinam naturalmente com `asyncio.Event` quando você precisa pausar até que algo aconteça. Registre um listener temporário que ativa a flag, dispare a ação e depois aguarde a flag:

```python
import asyncio

from pydoll.protocol.page.events import PageEvent


async def click_and_wait_for_navigation(tab):
    navigated = asyncio.Event()

    async def on_navigated(event):
        navigated.set()

    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)

    link = await tab.find(text='Form Authentication')
    await link.click()

    await navigated.wait()
    print('navigation finished')
```

## Use a aba dentro de um callback

`on()` passa apenas o evento para o seu callback. Para usar a aba também (por exemplo, para ler o corpo de uma resposta), vincule-a com `functools.partial`:

```python
from functools import partial

from pydoll.protocol.network.events import NetworkEvent


async def capture_json(tab, event):
    url = event['params']['response']['url']
    if '/api/' not in url:
        return
    request_id = event['params']['requestId']
    body = await tab.get_network_response_body(request_id)
    print(f'{url}: {body[:80]}')


await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, partial(capture_json, tab))
```

Filtre cedo, como acima: retorne assim que o evento não for um que te interessa, para que o trabalho custoso só rode quando deve.

## Trate diálogos JavaScript

Assine os eventos de diálogo para responder caixas `alert`, `confirm` e `prompt` automaticamente, em vez de deixá-las travar a página:

```python
from pydoll.protocol.page.events import PageEvent


async def on_dialog(event):
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)


await tab.enable_page_events()
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, on_dialog)
await tab.go_to('https://the-internet.herokuapp.com/javascript_alerts')
```

## Faça a limpeza quando terminar

Mantenha os listeners restritos ao trabalho que precisa deles. Remova um único callback pelo seu id, ou limpe todos, e desabilite um domínio assim que terminar de usá-lo:

```python
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# ... faça o trabalho que precisa dele ...

await tab.remove_callback(callback_id)   # remove um
await tab.clear_callbacks()              # ou remove todos os callbacks da aba
await tab.disable_network_events()       # para o domínio
```

Habilite apenas os domínios que você usa. Eventos de DOM em particular disparam com muita frequência em páginas dinâmicas, então assine-os apenas enquanto precisar deles, e mantenha os callbacks rápidos; delegue trabalho pesado para uma tarefa separada com `asyncio.create_task` para que ele não segure o próximo evento.

## Domínios de eventos e eventos principais

| Domínio | Habilite com | Recorra a ele para |
|---|---|---|
| Page | `enable_page_events()` | reagir a carregamentos, navegação e diálogos |
| Network | `enable_network_events()` | observar requisições e respostas |
| Fetch | `enable_fetch_events()` | interceptar e modificar requisições |
| DOM | `enable_dom_events()` | reagir a mudanças no DOM |
| Runtime | `enable_runtime_events()` | ler mensagens de console e exceções |

Constantes de evento comuns (cada domínio tem mais em `pydoll.protocol.<domain>.events`):

| Constante | Dispara quando |
|---|---|
| `PageEvent.LOAD_EVENT_FIRED` | a página termina de carregar |
| `PageEvent.DOM_CONTENT_EVENT_FIRED` | o DOM está pronto |
| `PageEvent.FRAME_NAVIGATED` | uma navegação é concluída |
| `PageEvent.JAVASCRIPT_DIALOG_OPENING` | um alert, confirm ou prompt abre |
| `NetworkEvent.REQUEST_WILL_BE_SENT` | uma requisição está prestes a sair |
| `NetworkEvent.RESPONSE_RECEIVED` | os cabeçalhos da resposta chegam |
| `NetworkEvent.LOADING_FINISHED` | o corpo da resposta é totalmente carregado |

## Próximos passos

- [Monitoramento de rede](network-monitoring.md): capture e analise o tráfego com esses eventos.
- [Interceptação de requisições](request-interception.md): pause, modifique e bloqueie requisições, não apenas as observe.
- [Repetição](retrying.md): repita ações instáveis com o decorador `@retry`.
