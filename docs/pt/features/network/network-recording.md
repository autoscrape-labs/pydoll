# Gravacao de Rede HAR

Capture toda a atividade de rede durante uma sessao do navegador e exporte como um arquivo HAR (HTTP Archive) 1.2 padrao. Perfeito para depuracao, analise de desempenho e replay de requisicoes.

!!! tip "Depure Como um Profissional"
    Arquivos HAR sao o padrao da industria para gravar trafego de rede. Voce pode importa-los diretamente no Chrome DevTools, Charles Proxy ou qualquer visualizador HAR para analise detalhada.

## Por que Usar Gravacao HAR?

| Caso de Uso | Beneficio |
|-------------|-----------|
| Depurar requisicoes com falha | Veja headers exatos, timing e corpos de resposta |
| Analise de desempenho | Identifique requisicoes lentas e gargalos |
| Replay de requisicoes | Reproduza sequencias exatas de requisicoes |
| Documentacao de API | Capture pares reais de requisicao/resposta |
| Fixtures de teste | Grave trafego real para mocking em testes |

## Inicio Rapido

Grave todo o trafego de rede durante uma navegacao:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def gravar_trafego():
    async with Chrome() as browser:
        tab = await browser.start()

        async with tab.request.record() as recording:
            await tab.go_to('https://example.com')

        # Salve a gravacao como arquivo HAR
        recording.save('flow.har')
        print(f'Capturadas {len(recording.entries)} requisicoes')

asyncio.run(gravar_trafego())
```

## API de Gravacao

### `tab.request.record()`

Gerenciador de contexto que captura todo o trafego de rede na aba.

```python
async with tab.request.record() as recording:
    # Toda atividade de rede dentro deste bloco e capturada
    await tab.go_to('https://example.com')
    await (await tab.find(id='search')).type_text('pydoll')
    await (await tab.find(type='submit')).click()
```

O objeto `recording` fornece:

| Propriedade/Metodo | Descricao |
|-------------------|-----------|
| `recording.entries` | Lista de entradas HAR capturadas |
| `recording.to_dict()` | Dict HAR 1.2 completo (para processamento customizado) |
| `recording.save(path)` | Salvar como arquivo JSON HAR |

### Salvando Gravacoes

```python
# Salvar como arquivo HAR (pode ser aberto no Chrome DevTools)
recording.save('flow.har')

# Salvar em diretorio aninhado (criado automaticamente)
recording.save('recordings/session1/flow.har')

# Acessar o dict HAR bruto para processamento customizado
har_dict = recording.to_dict()
print(har_dict['log']['version'])  # "1.2"
```

### Inspecionando Entradas

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

for entry in recording.entries:
    req = entry['request']
    resp = entry['response']
    print(f"{req['method']} {req['url']} -> {resp['status']}")
```

## Replay de Requisicoes

Reproduza um arquivo HAR previamente gravado, executando cada requisicao sequencialmente pelo navegador:

```python
async def replay_trafego():
    async with Chrome() as browser:
        tab = await browser.start()

        # Navegue para configurar o contexto da sessao
        await tab.go_to('https://example.com')

        # Reproduza todas as requisicoes gravadas
        responses = await tab.request.replay('flow.har')

        for resp in responses:
            print(f"Status: {resp.status_code}")

asyncio.run(replay_trafego())
```

### `tab.request.replay(path)`

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `path` | `str \| Path` | Caminho para o arquivo HAR a reproduzir |

**Retorna:** `list[Response]` -- respostas de cada requisicao reproduzida.

**Levanta:** `HarReplayError` -- se o arquivo HAR for invalido ou ilegivel.

## Uso Avancado

### Fluxo de Gravacao e Replay

```python
async def gravar_e_reproduzir():
    async with Chrome() as browser:
        tab = await browser.start()

        # Passo 1: Gravar a sessao original
        async with tab.request.record() as recording:
            await tab.go_to('https://api.example.com')
            await tab.request.post(
                'https://api.example.com/data',
                json={'key': 'value'}
            )

        recording.save('api_session.har')

        # Passo 2: Reproduzir depois
        responses = await tab.request.replay('api_session.har')
```

### Filtrando Entradas Gravadas

```python
async with tab.request.record() as recording:
    await tab.go_to('https://example.com')

# Filtrar apenas chamadas de API
api_entries = [
    e for e in recording.entries
    if '/api/' in e['request']['url']
]

# Filtrar apenas requisicoes com falha
falhas = [
    e for e in recording.entries
    if e['response']['status'] >= 400
]
```

### Processamento HAR Customizado

```python
har = recording.to_dict()

# Contar requisicoes por tipo
from collections import Counter
tipos = Counter(
    e.get('_resourceType', 'Other')
    for e in har['log']['entries']
)
print(tipos)  # Counter({'Document': 1, 'Script': 5, 'Stylesheet': 3, ...})
```

## Formato de Arquivo HAR

O HAR exportado segue a [especificacao HAR 1.2](http://www.softwareishard.com/blog/har-12-spec/). Cada entrada contem:

- **Request**: metodo, URL, headers, parametros de query, dados POST
- **Response**: status, headers, corpo da resposta (texto ou codificado em base64)
- **Timings**: DNS, conexao, SSL, envio, espera (TTFB), recebimento
- **Metadata**: IP do servidor, ID de conexao, tipo de recurso

!!! note "Corpos de Resposta"
    Os corpos de resposta sao capturados automaticamente apos cada requisicao ser concluida. Conteudo binario (imagens, fontes, etc.) e armazenado como strings codificadas em base64.
