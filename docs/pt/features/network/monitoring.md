# Monitoramento de Rede

O monitoramento de rede no Pydoll permite observar e analisar requisições HTTP, respostas e outras atividades de rede durante a automação do navegador. Isso é essencial para depuração, análise de desempenho, testes de API e para entender como as aplicações web se comunicam com os servidores.

!!! info "Domínio Network vs Fetch"
    O **domínio Network** é para monitoramento passivo (observar o tráfego). O **domínio Fetch** é para interceptação ativa (modificar requisições/respostas). Este guia foca no monitoramento. Para interceptação de requisições, veja a documentação avançada.

## Habilitando Eventos de Rede

Antes de poder monitorar a atividade de rede, você deve habilitar o domínio Network:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Habilitar monitoramento de rede
        await tab.enable_network_events()
        
        # Agora navegue
        await tab.go_to('https://api.github.com')
        
        # Não se esqueça de desabilitar quando terminar (opcional, mas recomendado)
        await tab.disable_network_events()

asyncio.run(main())
```

!!! warning "Habilite Antes de Navegar"
    Sempre habilite os eventos de rede **antes** de navegar para capturar todas as requisições. Requisições feitas antes da habilitação não serão capturadas.

## Obtendo Logs de Rede

O Pydoll armazena automaticamente os logs de rede quando os eventos de rede estão habilitados. Você pode recuperá-los usando `get_network_logs()`:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_requests():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navegar para uma página
        await tab.go_to('https://httpbin.org/json')
        
        # Esperar a página carregar completamente
        await asyncio.sleep(2)
        
        # Obter todos os logs de rede
        logs = await tab.get_network_logs()
        
        print(f"Total de requisições capturadas: {len(logs)}")
        
        for log in logs:
            request = log['params']['request']
            print(f"→ {request['method']} {request['url']}")

asyncio.run(analyze_requests())
```

!!! note "Espera Pronta para Produção"
    Os exemplos acima usam `asyncio.sleep(2)` por simplicidade. Em código de produção, considere usar estratégias de espera mais explícitas:
    
    - Esperar por elementos específicos aparecerem
    - Usar o [Sistema de Eventos](../advanced/event-system.md) para detectar quando todos os recursos foram carregados
    - Implementar detecção de ociosidade da rede (veja a seção Monitoramento de Rede em Tempo Real)
    
    Isso garante que sua automação espere exatamente o tempo necessário, nem mais, nem menos.

### Filtrando Logs de Rede

Você pode filtrar logs por padrão de URL:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def filter_logs_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # Obter todos os logs
        all_logs = await tab.get_network_logs()
        
        # Obter logs para um domínio específico
        api_logs = await tab.get_network_logs(filter='api.example.com')
        
        # Obter logs para um endpoint específico
        user_logs = await tab.get_network_logs(filter='/api/users')

asyncio.run(filter_logs_example())
```

## Entendendo a Estrutura de Eventos de Rede

Os logs de rede contêm informações detalhadas sobre cada requisição. Aqui está a estrutura:

### Evento RequestWillBeSent

Este evento é disparado quando uma requisição está prestes a ser enviada:

```python
{
    'method': 'Network.requestWillBeSent',
    'params': {
        'requestId': 'unique-request-id',
        'loaderId': 'loader-id',
        'documentURL': 'https://example.com',
        'request': {
            'url': 'https://api.example.com/data',
            'method': 'GET',  # ou 'POST', 'PUT', 'DELETE', etc.
            'headers': {
                'User-Agent': 'Chrome/...',
                'Accept': 'application/json',
                ...
            },
            'postData': '...',  # Presente apenas para requisições POST/PUT
            'initialPriority': 'High',
            'referrerPolicy': 'strict-origin-when-cross-origin'
        },
        'timestamp': 1234567890.123,
        'wallTime': 1234567890.123,
        'initiator': {
            'type': 'script',  # ou 'parser', 'other'
            'stack': {...}  # Call stack se iniciado por script
        },
        'type': 'XHR',  # Tipo de recurso: Document, Script, Image, XHR, etc.
        'frameId': 'frame-id',
        'hasUserGesture': False
    }
}
```

### Referência de Campos Chave

| Campo | Localização | Tipo | Descrição |
|---|---|---|---|
| `requestId` | `params.requestId` | `str` | Identificador único para esta requisição |
| `url` | `params.request.url` | `str` | URL completa da requisição |
| `method` | `params.request.method` | `str` | Método HTTP (GET, POST, etc.) |
| `headers` | `params.request.headers` | `dict` | Cabeçalhos da requisição |
| `postData` | `params.request.postData` | `str` | Corpo da requisição (POST/PUT) |
| `timestamp` | `params.timestamp` | `float` | Tempo monotônico quando a requisição iniciou |
| `type` | `params.type` | `str` | Tipo de recurso (Document, XHR, Image, etc.) |
| `initiator` | `params.initiator` | `dict` | O que disparou esta requisição |

## Obtendo Corpos de Resposta

Para obter o conteúdo real da resposta, use `get_network_response_body()`:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def fetch_api_response():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navegar para o endpoint da API
        await tab.go_to('https://httpbin.org/json')
        await asyncio.sleep(2)
        
        # Obter todas as requisições
        logs = await tab.get_network_logs()
        
        for log in logs:
            request_id = log['params']['requestId']
            url = log['params']['request']['url']
            
            # Obter resposta apenas para o endpoint JSON
            if 'httpbin.org/json' in url:
                try:
                    # Obter corpo da resposta
                    response_body = await tab.get_network_response_body(request_id)
                    print(f"Resposta de {url}:")
                    print(response_body)
                except Exception as e:
                    print(f"Não foi possível obter o corpo da resposta: {e}")

asyncio.run(fetch_api_response())
```

!!! warning "Disponibilidade do Corpo da Resposta"
    Corpos de resposta estão disponíveis apenas para requisições que foram concluídas. Além disso, alguns tipos de resposta (como imagens ou redirecionamentos) podem não ter corpos acessíveis.

## Casos de Uso Práticos

### 1. Teste e Validação de API

Monitore chamadas de API para verificar se as requisições corretas estão sendo feitas:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def validate_api_calls():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Navegar para sua aplicação
        await tab.go_to('https://your-app.com')
        
        # Disparar alguma ação que faça chamadas de API
        button = await tab.find(id='load-data-button')
        await button.click()
        await asyncio.sleep(2)
        
        # Obter logs da API
        api_logs = await tab.get_network_logs(filter='/api/')
        
        print(f"\n📊 Resumo das Chamadas de API:")
        print(f"Total de chamadas de API: {len(api_logs)}")
        
        for log in api_logs:
            request = log['params']['request']
            method = request['method']
            url = request['url']
            
            # Verificar se o cabeçalho de autenticação correto está presente
            headers = request.get('headers', {})
            has_auth = 'Authorization' in headers or 'authorization' in headers
            
            print(f"\n{method} {url}")
            print(f"  ✓ Possui Autorização: {has_auth}")
            
            # Validar dados POST se aplicável
            if method == 'POST' and 'postData' in request:
                print(f"  📤 Corpo: {request['postData'][:100]}...")

asyncio.run(validate_api_calls())
```

### 2. Análise de Desempenho

Analise o tempo das requisições e identifique recursos lentos:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def analyze_performance():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # Armazenar dados de tempo
        timings = []
        
        for log in logs:
            params = log['params']
            request_id = params['requestId']
            url = params['request']['url']
            resource_type = params.get('type', 'Other')
            
            timings.append({
                'url': url,
                'type': resource_type,
                'timestamp': params['timestamp']
            })
        
        # Ordenar por timestamp
        timings.sort(key=lambda x: x['timestamp'])
        
        print("\n⏱️  Linha do Tempo das Requisições:")
        start_time = timings[0]['timestamp'] if timings else 0
        
        for timing in timings[:20]:  # Mostrar as primeiras 20
            elapsed = (timing['timestamp'] - start_time) * 1000  # Converter para ms
            print(f"{elapsed:7.0f}ms | {timing['type']:12} | {timing['url'][:80]}")

asyncio.run(analyze_performance())
```

### 3. Detectando Recursos Externos

Encontre todos os domínios externos aos quais sua página se conecta:

```python
import asyncio
from urllib.parse import urlparse
from collections import Counter
from pydoll.browser.chromium import Chrome

async def analyze_domains():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://news.ycombinator.com')
        await asyncio.sleep(5)
        
        logs = await tab.get_network_logs()
        
        # Contar requisições por domínio
        domains = Counter()
        
        for log in logs:
            url = log['params']['request']['url']
            try:
                domain = urlparse(url).netloc
                if domain:
                    domains[domain] += 1
            except:
                pass
        
        print("\n🌐 Domínios Externos:")
        for domain, count in domains.most_common(10):
            print(f"  {count:3} requisições | {domain}")

asyncio.run(analyze_domains())
```

### 4. Monitorando Tipos Específicos de Recursos

Rastreie tipos específicos de recursos, como imagens ou scripts:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def track_resource_types():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        await tab.go_to('https://example.com')
        await asyncio.sleep(3)
        
        logs = await tab.get_network_logs()
        
        # Agrupar por tipo de recurso
        by_type = {}
        
        for log in logs:
            params = log['params']
            resource_type = params.get('type', 'Other')
            url = params['request']['url']
            
            if resource_type not in by_type:
                by_type[resource_type] = []
            
            by_type[resource_type].append(url)
        
        print("\n📦 Recursos por Tipo:")
        for rtype in sorted(by_type.keys()):
            urls = by_type[rtype]
            print(f"\n{rtype}: {len(urls)} recurso(s)")
            for url in urls[:3]:  # Mostrar os 3 primeiros
                print(f"  • {url}")
            if len(urls) > 3:
                print(f"  ... e mais {len(urls) - 3}")

asyncio.run(track_resource_types())
```

## Monitoramento de Rede em Tempo Real

Para monitoramento em tempo real, use callbacks de eventos em vez de consultar `get_network_logs()`:

!!! info "Entendendo Eventos"
    O monitoramento em tempo real usa o sistema de eventos do Pydoll para reagir à atividade de rede assim que ela acontece. Para uma análise profunda de como os eventos funcionam, veja **[Sistema de Eventos](../advanced/event-system.md)**.

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

async def real_time_monitoring():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Estatísticas
        stats = {
            'requests': 0,
            'responses': 0,
            'failed': 0
        }
        
        # Callback de requisição
        async def on_request(event: RequestWillBeSentEvent):
            stats['requests'] += 1
            url = event['params']['request']['url']
            method = event['params']['request']['method']
            print(f"→ {method:6} | {url}")
        
        # Callback de resposta
        async def on_response(event: ResponseReceivedEvent):
            stats['responses'] += 1
            response = event['params']['response']
            status = response['status']
            url = response['url']
            
            # Código de cor por status
            if 200 <= status < 300:
                color = '\033[92m'  # Verde
            elif 300 <= status < 400:
                color = '\033[93m'  # Amarelo
            else:
                color = '\033[91m'  # Vermelho
            reset = '\033[0m'
            
            print(f"← {color}{status}{reset} | {url}")
        
        # Callback de falha
        async def on_failed(event: LoadingFailedEvent):
            stats['failed'] += 1
            error = event['params']['errorText']
            print(f"✗ FALHOU: {error}")
        
        # Habilitar e registrar callbacks
        await tab.enable_network_events()
        await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.on(NetworkEvent.LOADING_FAILED, on_failed)
        
        # Navegar
        await tab.go_to('https://example.com')
        await asyncio.sleep(5)
        
        print(f"\n📊 Resumo:")
        print(f"  Requisições: {stats['requests']}")
        print(f"  Respostas: {stats['responses']}")
        print(f"  Falhas: {stats['failed']}")

asyncio.run(real_time_monitoring())
```

## Referência de Tipos de Recurso

O Pydoll captura os seguintes tipos de recurso:

| Tipo | Descrição | Exemplos |
|---|---|---|
| `Document` | Documentos HTML principais | Carregamentos de página, fontes de iframe |
| `Stylesheet` | Arquivos CSS | .css externo, estilos inline |
| `Image` | Recursos de imagem | .jpg, .png, .gif, .webp, .svg |
| `Media` | Arquivos de áudio/vídeo | .mp4, .webm, .mp3, .ogg |
| `Font` | Fontes web | .woff, .woff2, .ttf, .otf |
| `Script` | Arquivos JavaScript | Arquivos .js, scripts inline |
| `TextTrack` | Arquivos de legenda | .vtt, .srt |
| `XHR` | XMLHttpRequest | Requisições AJAX, chamadas de API legadas |
| `Fetch` | Requisições da API Fetch | Chamadas de API modernas |
| `EventSource` | Server-Sent Events | Streams em tempo real |
| `WebSocket` | Conexões WebSocket | Comunicação bidirecional |
| `Manifest` | Manifestos de aplicativos web | Configuração de PWA |
| `Other` | Outros tipos de recurso | Diversos |

## Avançado: Extraindo Tempos de Resposta

Eventos de rede incluem informações detalhadas de tempo:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def analyze_timing():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        
        # Callback personalizado para capturar tempos
        timing_data = []
        
        async def on_response(event: ResponseReceivedEvent):
            response = event['params']['response']
            timing = response.get('timing')
            
            if timing:
                # Calcular diferentes fases
                dns_time = timing.get('dnsEnd', 0) - timing.get('dnsStart', 0)
                connect_time = timing.get('connectEnd', 0) - timing.get('connectStart', 0)
                ssl_time = timing.get('sslEnd', 0) - timing.get('sslStart', 0)
                send_time = timing.get('sendEnd', 0) - timing.get('sendStart', 0)
                wait_time = timing.get('receiveHeadersStart', 0) - timing.get('sendEnd', 0)
                receive_time = timing.get('receiveHeadersEnd', 0) - timing.get('receiveHeadersStart', 0)
                
                timing_data.append({
                    'url': response['url'][:50],
                    'dns': dns_time if dns_time > 0 else 0,
                    'connect': connect_time if connect_time > 0 else 0,
                    'ssl': ssl_time if ssl_time > 0 else 0,
                    'send': send_time,
                    'wait': wait_time,
                    'receive': receive_time,
                    'total': receive_time + wait_time + send_time
                })
        
        await tab.on(NetworkEvent.RESPONSE_RECEIVED, on_response)
        await tab.go_to('https://github.com')
        await asyncio.sleep(5)
        
        # Imprimir detalhamento de tempo
        print("\n⏱️  Detalhamento de Tempo da Requisição (ms):")
        print(f"{'URL':<50} | {'DNS':>6} | {'Connect':>8} | {'SSL':>6} | {'Send':>6} | {'Wait':>6} | {'Receive':>8} | {'Total':>7}")
        print("-" * 120)
        
        for data in sorted(timing_data, key=lambda x: x['total'], reverse=True)[:10]:
            print(f"{data['url']:<50} | {data['dns']:6.1f} | {data['connect']:8.1f} | {data['ssl']:6.1f} | "
                  f"{data['send']:6.1f} | {data['wait']:6.1f} | {data['receive']:8.1f} | {data['total']:7.1f}")

asyncio.run(analyze_timing())
```

## Explicação dos Campos de Tempo

| Fase | Campos | Descrição |
|---|---|---|
| **DNS** | `dnsStart` → `dnsEnd` | Tempo de lookup DNS |
| **Connect** | `connectStart` → `connectEnd` | Estabelecimento da conexão TCP |
| **SSL** | `sslStart` → `sslEnd` | Handshake SSL/TLS |
| **Send** | `sendStart` → `sendEnd` | Tempo para enviar a requisição |
| **Wait** | `sendEnd` → `receiveHeadersStart` | Esperando pela resposta do servidor (TTFB) |
| **Receive** | `receiveHeadersStart` → `receiveHeadersEnd` | Tempo para receber os cabeçalhos da resposta |

!!! tip "Time to First Byte (TTFB)"
    TTFB é a fase "Wait" - o tempo entre enviar a requisição e receber o primeiro byte da resposta. Isso é crucial para análise de desempenho.

## Melhores Práticas

### 1. Habilite Eventos de Rede Apenas Quando Necessário

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_enable():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Bom: Habilitar antes da navegação, desabilitar depois
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        logs = await tab.get_network_logs()
        await tab.disable_network_events()
        
        # Ruim: Deixar habilitado durante toda a sessão
        # await tab.enable_network_events()
        # ... longa sessão de automação ...
```

### 2. Filtre Logs para Reduzir o Uso de Memória

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_filter():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        # Bom: Filtrar por requisições específicas
        api_logs = await tab.get_network_logs(filter='/api/')
        
        # Ruim: Obter todos os logs quando você só precisa de específicos
        all_logs = await tab.get_network_logs()
        filtered = [log for log in all_logs if '/api/' in log['params']['request']['url']]
```

### 3. Acesse Campos Faltantes com Segurança

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def best_practice_safe_access():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.enable_network_events()
        await tab.go_to('https://example.com')
        await asyncio.sleep(2)
        
        logs = await tab.get_network_logs()
        
        # Bom: Acesso seguro com .get()
        for log in logs:
            params = log.get('params', {})
            request = params.get('request', {})
            url = request.get('url', 'Unknown')
            post_data = request.get('postData')  # Pode ser None
            
            if post_data:
                print(f"Dados POST: {post_data}")
        
        # Ruim: Acesso direto pode levantar KeyError
        # url = log['params']['request']['url']
        # post_data = log['params']['request']['postData']  # Pode não existir!
```

### 4. Use Callbacks de Evento para Necessidades em Tempo Real

```python
import asyncio
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

# Bom: Monitoramento em tempo real com callbacks
async def on_request(event: RequestWillBeSentEvent):
    print(f"Nova requisição: {event['params']['request']['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)

# Ruim: Consultar logs repetidamente (ineficiente)
while True:
    logs = await tab.get_network_logs()
    # Processar logs...
    await asyncio.sleep(0.5)  # Desperdício!
```

## Veja Também

- **[Domínio de Rede CDP](../../deep-dive/network-capabilities.md)** - Análise profunda sobre as capacidades de rede
- **[Sistema de Eventos](../advanced/event-system.md)** - Entendendo a arquitetura de eventos do Pydoll
- **[Interceptação de Requisições](interception.md)** - Modificando requisições e respostas