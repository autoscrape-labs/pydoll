# Interceptação de requisições

A interceptação permite que você se coloque entre o navegador e a rede. Cada requisição correspondente pausa no seu handler, onde você decide deixá-la passar (como está ou modificada), bloqueá-la ou respondê-la você mesmo com uma resposta simulada. Use-a para descartar imagens em prol da velocidade, injetar cabeçalhos ou forjar uma API enquanto você desenvolve contra ela.

Esta é a contraparte ativa do [Monitoramento de rede](network-monitoring.md), que apenas observa o tráfego. A interceptação pode alterá-lo.

<iframe scrolling="no" src="/docs/resources/visuals/request-lifecycle.html" aria-label="What happens to an intercepted request under continue, block, or fulfill" style="width: 100%; height: 400px; border: 0;" loading="lazy"></iframe>

Experimente cada botão: `continue_request()` deixa a requisição chegar ao servidor, `fail_request()` a descarta e `fulfill_request()` responde a partir do seu handler sem nunca contatar o servidor.

## Habilite a interceptação

A interceptação roda no domínio Fetch do Chrome. Habilite-o, registre um handler para o evento de requisição pausada e resolva cada requisição que o handler receber.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def on_request(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']
    print(f'paused: {url}')
    await tab.continue_request(request_id)   # deixa passar sem alteração


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(on_request, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! warning "Resolva cada requisição pausada, exatamente uma vez"
    Uma requisição pausada segura a página até você agir sobre ela. Cada uma deve terminar em exatamente um entre `continue_request`, `fail_request` ou `fulfill_request`. Esqueça de uma e essa requisição trava até expirar; chame duas e você recebe um erro. Envolva a lógica arriscada do handler em `try`/`except` e continue a requisição no ramo `except`, para que um bug nunca congele a página.

## Intercepte apenas as requisições que você quer

A interceptação adiciona um ida e volta pelo seu handler para cada requisição correspondente, então restrinja o escopo. Passe um `resource_type` para pausar apenas um tipo de requisição, e leia `event['params']['resourceType']` no handler para ramificar ainda mais.

```python
from pydoll.protocol.network.types import ResourceType

# pausa apenas chamadas XHR/fetch, não documentos, imagens ou estilos
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
```

`ResourceType` cobre `DOCUMENT`, `STYLESHEET`, `IMAGE`, `MEDIA`, `FONT`, `SCRIPT`, `XHR`, `FETCH` e mais; veja o enum `ResourceType` em `pydoll.protocol.network.types` para o conjunto completo.

## Bloqueie requisições

`fail_request` descarta uma requisição com um motivo de erro. Bloquear imagens e folhas de estilo é uma forma comum de tornar o scraping mais rápido e leve.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ErrorReason


async def block_heavy(tab, event):
    request_id = event['params']['requestId']
    resource_type = event['params']['resourceType']

    if resource_type in ('Image', 'Stylesheet', 'Font'):
        await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(block_heavy, tab))

        await tab.go_to('https://books.toscrape.com')
        await tab.disable_fetch_events()

asyncio.run(main())
```

Valores comuns de `ErrorReason` são `BLOCKED_BY_CLIENT` (parece um bloqueador de anúncios), `FAILED`, `ABORTED`, `TIMED_OUT` e `CONNECTION_REFUSED`, úteis para testar como uma página lida com falhas de rede. A lista completa é o enum `ErrorReason` em `pydoll.protocol.network.types`.

## Modifique uma requisição

`continue_request` pode reescrever a requisição antes que ela seja enviada: mudar a URL, o método, os cabeçalhos ou o corpo. Cabeçalhos são uma lista de dicts `HeaderEntry` (`{'name': ..., 'value': ...}`).

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ResourceType


async def add_header(tab, event):
    request_id = event['params']['requestId']
    headers = [
        {'name': 'X-Automated-By', 'value': 'pydoll'},
    ]
    await tab.continue_request(request_id, headers=headers)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(add_header, tab))

        await tab.go_to('https://httpbin.org/headers')  # devolve os cabeçalhos que recebeu
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "Os cabeçalhos que você passa substituem os cabeçalhos da requisição"
    Fornecer `headers` define a lista completa de cabeçalhos daquela requisição, não faz merge com os do navegador. Inclua os cabeçalhos que a requisição ainda precisa, não apenas o que você está adicionando.

Você também pode mudar para onde uma requisição vai passando `url`, ou substituir os dados do `POST` passando `post_data`.

## Simule uma resposta

`fulfill_request` responde a uma requisição você mesmo, então o servidor nunca é contatado. É assim que você desenvolve contra uma API que ainda não existe ou força um payload específico. O `body` é codificado em base64.

```python
import asyncio
import base64
import json
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent


async def mock_json(tab, event):
    request_id = event['params']['requestId']
    url = event['params']['request']['url']

    if url.endswith('/json'):
        payload = {'source': 'mocked by pydoll', 'items': [1, 2, 3]}
        body = base64.b64encode(json.dumps(payload).encode()).decode()
        await tab.fulfill_request(
            request_id,
            response_code=200,
            response_headers=[{'name': 'Content-Type', 'value': 'application/json'}],
            body=body,
        )
    else:
        await tab.continue_request(request_id)


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events()
        await tab.on(FetchEvent.REQUEST_PAUSED, partial(mock_json, tab))

        await tab.go_to('https://httpbin.org/json')  # normalmente retorna um documento de exemplo
        await tab.disable_fetch_events()

asyncio.run(main())
```

## Intercepte a resposta, não apenas a requisição

Por padrão, as requisições pausam antes de serem enviadas. Passe `request_stage=RequestStage.RESPONSE` para pausar depois que a resposta chega, para que você possa inspecioná-la ou substituí-la. Para uma única requisição continuada no estágio de requisição, `intercept_response=True` a pausa novamente assim que a resposta dela chega.

```python
from pydoll.protocol.fetch.types import RequestStage

await tab.enable_fetch_events(request_stage=RequestStage.RESPONSE)
```

## Lide com desafios de autenticação

Com `handle_auth=True`, o navegador levanta um desafio de autenticação que você responde com `continue_with_auth`. Isso cobre autenticação HTTP Basic/Digest (401) e autenticação de proxy (407).

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.fetch.types import AuthChallengeResponseType


async def answer_auth(tab, event):
    request_id = event['params']['requestId']
    await tab.continue_with_auth(
        request_id,
        auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
        proxy_username='user',
        proxy_password='passwd',
    )


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_fetch_events(handle_auth=True)
        await tab.on(FetchEvent.AUTH_REQUIRED, partial(answer_auth, tab))

        await tab.go_to('https://httpbin.org/basic-auth/user/passwd')
        await tab.disable_fetch_events()

asyncio.run(main())
```

!!! note "Autenticação de proxy já é automática"
    Você não precisa disso para um proxy normal. Quando você define as credenciais do proxy nas opções do navegador, o Pydoll responde ao desafio do proxy por você. Recorra ao `continue_with_auth` manual apenas para autenticação de servidor ou lógica de credenciais personalizada. Veja [Proxies](proxies.md).

## Próximos passos

- [Monitoramento de rede](network-monitoring.md): observe o tráfego sem alterá-lo.
- [Eventos](events.md): o modelo de eventos sobre o qual a interceptação é construída.
- [Proxies](proxies.md): direcione o tráfego por um proxy, com a autenticação tratada para você.
