# Monitoramento de rede

O Pydoll permite observar cada requisição que uma página faz, ler corpos de resposta e inspecionar status e tempos, tudo a partir do próprio navegador. Não há proxy para configurar nem certificado para instalar; você habilita o domínio de rede e o tráfego chega até você.

Este guia trata de observar o tráfego. Para alterar, bloquear ou forjar requisições, veja [Interceptação de requisições](request-interception.md).

## Observe as requisições conforme acontecem

Habilite os eventos de rede antes de navegar e depois registre um callback. O Pydoll o chama para cada requisição que a página inicia.

```python
import asyncio
from functools import partial

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_request(tab, event):
    request = event['params']['request']
    print(f"{request['method']} {request['url']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, partial(on_request, tab))

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

Habilite o domínio **antes** de navegar; requisições feitas antes de ele estar habilitado não são capturadas.

<iframe scrolling="no" src="/docs/resources/visuals/request-waterfall.html" aria-label="A request waterfall showing each request's start and duration as the page loads" style="width: 100%; height: 375px; border: 0;" loading="lazy"></iframe>

Pressione Load: cada requisição aparece como uma barra posicionada por quando começa e com largura conforme quanto tempo leva, que é o que os eventos de rede reportam à medida que disparam.

## Leia o corpo de uma resposta

O corpo da resposta não está no evento; você o busca pelo id da requisição assim que a resposta chega. Encontre a requisição que te interessa e chame `get_network_response_body`.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()

        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)

        for log in await tab.get_network_logs():
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            if url.endswith('/json'):
                body = await tab.get_network_response_body(request_id)
                print(body)

asyncio.run(main())
```

!!! note "Os corpos só existem depois que a resposta chega"
    Um corpo fica disponível quando a requisição foi concluída. Redirecionamentos e alguns tipos de recurso (imagens, por exemplo) podem não ter um corpo legível, então envolva a chamada em um `try`/`except` quando você percorrer muitas requisições.

## Obtenha os logs depois de navegar

Se você não precisa de callbacks em tempo real, deixe o Pydoll coletar as requisições e leia-as depois com `get_network_logs`. Passe `filter` para manter apenas URLs que contenham uma substring.

```python
await tab.go_to('https://github.com')
await asyncio.sleep(3)

all_requests = await tab.get_network_logs()
api_requests = await tab.get_network_logs(filter='api.github.com')

print(f'{len(all_requests)} requests, {len(api_requests)} to the API')

for log in api_requests:
    print(log['params']['request']['url'])
```

## Reaja a respostas e falhas

Assine as respostas para verificar códigos de status e as falhas para capturar requisições que nunca se concluíram. A URL e o status da resposta ficam em `event['params']['response']`; o motivo de uma falha está em `event['params']['errorText']`.

```python
import asyncio

from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent


async def on_response(event):
    response = event['params']['response']
    print(f"{response['status']} {response['url']}")


async def on_failed(event):
    print(f"failed: {event['params']['errorText']}")


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        await tab.enable_network_events()
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)

        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(3)

asyncio.run(main())
```

## Habilite apenas enquanto precisar

Eventos de rede adicionam sobrecarga em páginas movimentadas, então habilite-os em torno da parte da sua automação que precisa deles e desabilite-os depois:

```python
await tab.enable_network_events()
await tab.go_to('https://github.com')
await asyncio.sleep(3)
logs = await tab.get_network_logs()
await tab.disable_network_events()
```

## Próximos passos

- [Interceptação de requisições](request-interception.md): altere, bloqueie ou responda requisições em vez de apenas observá-las.
- [Eventos](events.md): o modelo geral de habilitar, assinar e callback por trás dos eventos de rede.
- [Requisições HTTP no contexto do navegador](http-requests.md): chame APIs diretamente a partir da sessão da página.
