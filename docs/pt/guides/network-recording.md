# Gravação de rede em HAR

Grave cada requisição que uma página faz durante uma sessão e exporte como um arquivo HAR, o formato padrão HTTP Archive. Um arquivo HAR captura cada requisição e resposta com cabeçalhos, corpos e tempos, e abre no Chrome DevTools ou em qualquer visualizador de HAR. Use-o para depuração, análise de desempenho ou como fixture para testes.

## Grave uma sessão

Envolva a navegação que você quer capturar em `tab.request.record()`. Tudo o que a página requisitar dentro do bloco é gravado, e o objeto `capture` fica pronto assim que o bloco termina.

```python
import asyncio

from pydoll.browser.chromium import Chrome


async def main():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as capture:
            await tab.go_to('https://news.ycombinator.com')

        print(f'captured {len(capture.entries)} requests')

asyncio.run(main())
```

## Salve a gravação

`capture.save()` escreve um arquivo `.har`. Abra-o no Chrome DevTools (aba Network, importar) ou em qualquer visualizador de HAR para inspecionar o tráfego visualmente. Diretórios que não existem são criados para você.

```python
capture.save('flow.har')
capture.save('recordings/session-1/flow.har')
```

## Inspecione as entradas no código

`capture.entries` é uma lista de entradas HAR. Cada entrada tem uma `request` e uma `response` que você pode ler diretamente, o que é útil para fazer asserções sobre o tráfego em um teste ou extrair chamadas específicas.

```python
async with tab.request.record() as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')

for entry in capture.entries:
    request = entry['request']
    response = entry['response']
    print(f"{request['method']} {request['url']} -> {response['status']}")

# mantém apenas as chamadas de API que falharam
failed_api = [
    entry for entry in capture.entries
    if '/api/' in entry['request']['url'] and entry['response']['status'] >= 400
]
```

## Grave apenas alguns tipos de recurso

Gravar cada imagem, fonte e folha de estilo produz um arquivo grande. Passe `resource_types` para manter apenas os tipos que te interessam, que é a forma usual de capturar só o tráfego de API de uma página.

```python
from pydoll.protocol.network.types import ResourceType

# apenas as chamadas fetch/XHR, ignorando documentos, imagens e estilos
async with tab.request.record(
    resource_types=[ResourceType.FETCH, ResourceType.XHR]
) as capture:
    await tab.go_to('https://github.com/autoscrape-labs/pydoll')
```

Os valores comuns de `ResourceType` são `DOCUMENT`, `STYLESHEET`, `SCRIPT`, `IMAGE`, `FONT`, `MEDIA`, `FETCH`, `XHR` e `WEB_SOCKET`. Veja o enum `ResourceType` em `pydoll.protocol.network.types` para a lista completa.

## Obtenha o dict HAR bruto

`capture.to_dict()` retorna a estrutura HAR 1.2 completa, então você pode processá-la por conta própria ou entregá-la a outra ferramenta em vez de escrever um arquivo.

```python
har = capture.to_dict()
print(har['log']['version'])  # '1.2'

from collections import Counter

by_type = Counter(entry.get('_resourceType', 'Other') for entry in har['log']['entries'])
print(by_type)  # Counter({'Script': 5, 'Stylesheet': 3, 'Document': 1, ...})
```

!!! note "Corpos de resposta"
    Os corpos de resposta são capturados depois que cada requisição termina. Conteúdo binário como imagens e fontes é armazenado codificado em base64, seguindo a especificação HAR.

## Próximos passos

- [Monitoramento de rede](network-monitoring.md): observe requisições e leia respostas ao vivo, sem gravar um arquivo.
- [Interceptação de requisições](request-interception.md): pause, modifique, bloqueie ou simule requisições conforme acontecem.
- [Requisições HTTP no contexto do navegador](http-requests.md): faça requisições autenticadas pela própria sessão da página.
