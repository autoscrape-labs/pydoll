# Conexões remotas

`browser.connect()` conecta o Pydoll a um Chrome que já está em execução, em vez de lançar um. Use-o para controlar um navegador que você não iniciou: um em um contêiner, em um host remoto ou uma instância de longa duração compartilhada entre execuções. Você obtém a mesma API `Tab` de um navegador que você lançou.

## Iniciar o Chrome com uma porta de depuração

O navegador alvo precisa expor o Chrome DevTools Protocol. Inicie-o com `--remote-debugging-port`:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-remote
```

Isso serve uma pequena API JSON na porta. Peça a ela o endereço WebSocket do navegador:

```bash
curl http://localhost:9222/json/version
```

O campo `webSocketDebuggerUrl` na resposta (algo como `ws://localhost:9222/devtools/browser/<id>`) é o que você passa para o Pydoll.

## Conectar e controlar a aba

Crie um objeto browser, chame `connect()` com o endereço WebSocket, e use a aba retornada como qualquer outra:

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    browser = Chrome()
    tab = await browser.connect('ws://localhost:9222/devtools/browser/<id>')

    print(await tab.title)

    await tab.go_to('https://news.ycombinator.com')
    headline = await tab.find(class_name='titleline')
    print(await headline.text)

    await browser.close()

asyncio.run(main())
```

`connect()` retorna a primeira aba aberta. Alcance as outras com `await browser.get_opened_tabs()`, exatamente como quando você lança o navegador por conta própria. Veja [Abas](tabs.md).

!!! warning "Desconecte com `close()`, não `stop()`"
    Você não lançou este navegador, então não o encerre. `await browser.close()` fecha apenas a conexão WebSocket do Pydoll e deixa o navegador rodando para o que mais o use. `await browser.stop()` envia ao navegador um comando de fechamento e mata o processo, que é o que você quer para um navegador que você iniciou, não um ao qual você se conectou.

## Buscar o endereço WebSocket em código

Normalmente você descobre o endereço em tempo de execução em vez de embuti-lo no código. Consulte o endpoint JSON com qualquer cliente HTTP:

```python
import asyncio

import aiohttp
from pydoll.browser.chromium import Chrome


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:9222/json/version') as resp:
            ws_address = (await resp.json())['webSocketDebuggerUrl']

    browser = Chrome()
    tab = await browser.connect(ws_address)
    print(await tab.title)
    await browser.close()

asyncio.run(main())
```

Para um navegador em outra máquina, substitua `localhost` pelo endereço do servidor e consulte `http://<host>:9222/json/version` a partir do cliente.

## Rodar o Chrome em um contêiner

No Docker, inicie o Chrome headless com a porta de depuração vinculada e um segmento de memória compartilhada grande o suficiente (o Chrome usa `/dev/shm`, e o padrão de 64MB do Docker é pequeno demais):

```bash
docker run -d --shm-size=2g -p 127.0.0.1:9222:9222 \
  zenika/alpine-chrome \
  --no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222
```

Então conecte a partir do host com `browser.connect('ws://localhost:9222/devtools/browser/<id>')`. `--remote-debugging-address=0.0.0.0` permite conexões de fora do contêiner; `--no-sandbox` é necessário na maioria dos contêineres.

!!! warning "Nunca exponha a porta de depuração à internet"
    Uma porta de depuração acessível é controle total do navegador: cada página, cookie e sessão, além de JavaScript arbitrário. Vincule-a ao localhost (como faz `-p 127.0.0.1:9222:9222`) e alcance uma remota por um túnel SSH (`ssh -L 9222:localhost:9222 user@host`) ou uma rede privada, nunca por uma interface pública.

## Envolver um elemento a partir da sua própria ferramenta CDP

Se você já tem uma integração CDP e o `objectId` de um elemento, envolva-o em um `WebElement` do Pydoll para usar a API de interação de alto nível. Construa um `ConnectionHandler` para o WebSocket da página e passe-o:

```python
from pydoll.connection import ConnectionHandler
from pydoll.elements.web_element import WebElement

connection = ConnectionHandler(ws_address='ws://localhost:9222/devtools/page/<id>')

button = WebElement(
    object_id='<objectId from your CDP call>',
    connection_handler=connection,
)

await button.wait_until(is_visible=True, timeout=5)
await button.click(x_offset=5, y_offset=5)

await connection.close()
```

O `objectId` é o que comandos CDP como `Runtime.evaluate` ou `DOM.resolveNode` retornam para um nó. Isso mantém sua configuração existente e toma emprestado por cima as esperas e interações do Pydoll.

## Próximos passos

- [Abas](tabs.md): controle as abas que o navegador remoto já tem abertas.
- [Opções do navegador](browser-options.md): configure um navegador que você mesmo lança em vez de se conectar a um.
- [Monitoramento de rede](network-monitoring.md): observe o tráfego no navegador ao qual você se conectou.
