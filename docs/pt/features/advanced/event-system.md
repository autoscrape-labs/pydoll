# Sistema de Eventos

O sistema de eventos do Pydoll permite que você ouça e reaja às atividades do navegador em tempo real. Isso é essencial para construir automações dinâmicas, monitorar requisições de rede, detectar mudanças na página e criar fluxos de trabalho reativos.

!!! info "Análise Profunda Disponível"
    Este guia foca no uso prático. Para detalhes arquitetônicos e implementação interna, veja a [Análise Profunda da Arquitetura de Eventos](../../deep-dive/event-architecture.md).

## Pré-requisitos

Antes de trabalhar com eventos, você precisa habilitar o domínio CDP correspondente:

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    
    # Habilite o domínio antes de ouvir os eventos
    await tab.enable_page_events()     # Para eventos de ciclo de vida da página
    await tab.enable_network_events()  # Para atividade de rede
    await tab.enable_dom_events()      # Para mudanças no DOM
```

!!! warning "Eventos Não Serão Disparados Sem Habilitar"
    Se você registrar um callback mas esquecer de habilitar o domínio, seu callback nunca será acionado. Sempre habilite o domínio primeiro!

## Audição Básica de Eventos

O método `on()` registra ouvintes de eventos:

```python
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

async def handle_page_load(event: LoadEventFiredEvent):
    print(f"Página carregada em {event['params']['timestamp']}")

# Registrar o callback
await tab.enable_page_events()
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_page_load)
```

### Estrutura do Evento

Todos os eventos seguem a mesma estrutura:

```python
{
    'method': 'Page.loadEventFired',  # Nome do evento
    'params': {                        # Dados específicos do evento
        'timestamp': 123456.789
    }
}
```

Acesse os dados do evento através de `event['params']`:

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

async def handle_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    print(f"{method} {url}")
```

### Usando Dicas de Tipo (Type Hints) para Melhor Suporte da IDE

Use dicas de tipo com os tipos de parâmetros de evento para obter autocompletar para as chaves do evento:

```python
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent
from pydoll.protocol.page.events import PageEvent, LoadEventFiredEvent

# Com dicas de tipo - a IDE conhece todas as chaves disponíveis!
async def handle_request(event: RequestWillBeSentEvent):
    # A IDE irá autocompletar 'params', 'request', 'url', etc.
    url = event['params']['request']['url']
    method = event['params']['request']['method']
    timestamp = event['params']['timestamp']
    print(f"{method} {url} em {timestamp}")

async def handle_load(event: LoadEventFiredEvent):
    # A IDE sabe que este evento tem 'timestamp' em params
    timestamp = event['params']['timestamp']
    print(f"Página carregada em {timestamp}")

await tab.enable_network_events()
await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, handle_request)

await tab.enable_page_events()
await tab.on(PageEvent.LOAD_EVENT_FIRED, handle_load)
```

!!! tip "Dicas de Tipo para Parâmetros de Evento"
    Todos os tipos de evento são definidos em `pydoll.protocol.<domain>.events`. Usá-los oferece a você:
    
    - **Autocompletar**: A IDE sugere chaves disponíveis em `event['params']`
    - **Segurança de tipo**: Pega erros de digitação antes de rodar o código
    - **Documentação**: Veja quais dados cada evento fornece
    
    Os tipos de evento seguem o padrão: `<EventName>Event` (ex: `RequestWillBeSentEvent`, `ResponseReceivedEvent`)

## Domínios de Eventos Comuns

### Eventos de Página (Page)

Monitore o ciclo de vida da página e diálogos:

```python
from pydoll.protocol.page.events import PageEvent, JavascriptDialogOpeningEvent

await tab.enable_page_events()

# Página carregada
await tab.on(PageEvent.LOAD_EVENT_FIRED, lambda e: print("Página carregada!"))

# DOM pronto
await tab.on(PageEvent.DOM_CONTENT_EVENT_FIRED, lambda e: print("DOM pronto!"))

# Diálogo JavaScript
async def handle_dialog(event: JavascriptDialogOpeningEvent):
    message = event['params']['message']
    dialog_type = event['params']['type']
    print(f"Diálogo ({dialog_type}): {message}")
    
    # Lidar com isso automaticamente
    if await tab.has_dialog():
        await tab.handle_dialog(accept=True)

await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, handle_dialog)
```

### Eventos de Rede (Network)

Monitore requisições e respostas:

```python
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    ResponseReceivedEvent,
    LoadingFailedEvent
)

await tab.enable_network_events()

# Rastrear requisições
async def log_request(event: RequestWillBeSentEvent):
    request = event['params']['request']
    print(f"→ {request['method']} {request['url']}")

await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# Rastrear respostas
async def log_response(event: ResponseReceivedEvent):
    response = event['params']['response']
    print(f"← {response['status']} {response['url']}")

await tab.on(NetworkEvent.RESPONSE_RECEIVED, log_response)

# Rastrear falhas
async def log_failure(event: LoadingFailedEvent):
    url = event['params']['type']
    error = event['params']['errorText']
    print(f"[FALHOU] {url} - {error}")

await tab.on(NetworkEvent.LOADING_FAILED, log_failure)
```

### Eventos DOM

Reaja a mudanças no DOM:

```python
from pydoll.protocol.dom.events import DomEvent, AttributeModifiedEvent

await tab.enable_dom_events()

# Rastrear mudanças de atributo
async def on_attribute_change(event: AttributeModifiedEvent):
    node_id = event['params']['nodeId']
    attr_name = event['params']['name']
    attr_value = event['params']['value']
    print(f"Nó {node_id}: {attr_name}={attr_value}")

await tab.on(DomEvent.ATTRIBUTE_MODIFIED, on_attribute_change)

# Rastrear atualizações do documento
await tab.on(DomEvent.DOCUMENT_UPDATED, lambda e: print("Documento atualizado!"))
```

## Callbacks Temporários

Use `temporary=True` para ouvintes de uma única vez:

```python
from pydoll.protocol.page.events import PageEvent

# Isso disparará apenas uma vez e depois se auto-removerá
await tab.on(
    PageEvent.LOAD_EVENT_FIRED,
    lambda e: print("Primeiro carregamento!"),
    temporary=True
)

await tab.go_to("https://example.com")  # Dispara o callback
await tab.refresh()                      # Callback não disparará novamente
```

!!! tip "Perfeito para Configuração Única"
    Callbacks temporários são ideais para tarefas de inicialização que devem acontecer apenas uma vez.

## Acessando a Aba (Tab) nos Callbacks

Use `functools.partial` para passar a aba para seus callbacks:

```python
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def process_response(tab, event: ResponseReceivedEvent):
    # Agora podemos usar o objeto tab!
    request_id = event['params']['requestId']
    
    # Obter corpo da resposta
    body = await tab.get_network_response_body(request_id)
    print(f"Corpo da resposta: {body[:100]}...")

await tab.enable_network_events()
await tab.on(
    NetworkEvent.RESPONSE_RECEIVED,
    partial(process_response, tab)
)
```

!!! info "Por que Usar Partial?"
    O sistema de eventos passa apenas os dados do evento para os callbacks. `partial` permite que você vincule parâmetros adicionais, como a instância da aba.

## Gerenciando Callbacks

### Removendo Callbacks

```python
from pydoll.protocol.page.events import PageEvent

# Salvar o ID do callback
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, my_callback)

# Removê-lo mais tarde
await tab.remove_callback(callback_id)
```

### Limpando Todos os Callbacks

```python
# Remover todos os callbacks registrados para esta aba
await tab.clear_callbacks()
```

## Exemplos Práticos

### Monitorar Chamadas de API

```python
import asyncio
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def monitor_api_calls(tab):
    collected_data = []
    
    # Dica de tipo ajuda a IDE a autocompletar chaves de evento
    async def capture_api_response(tab, data_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # Filtrar apenas chamadas de API
        if '/api/' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        data_list.append({
            'url': url,
            'body': body,
            'status': event['params']['response']['status']
        })
        print(f"Capturada chamada de API: {url}")
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_api_response, tab, collected_data)
    )
    
    # Navegar e coletar
    await tab.go_to("https://example.com")
    await asyncio.sleep(3)  # Esperar requisições completarem
    
    return collected_data
```

### Esperar por Evento Específico

```python
import asyncio
from pydoll.protocol.page.events import PageEvent, FrameNavigatedEvent

async def wait_for_navigation():
    navigation_done = asyncio.Event()
    
    async def on_navigated(event: FrameNavigatedEvent):
        navigation_done.set()
    
    await tab.enable_page_events()
    await tab.on(PageEvent.FRAME_NAVIGATED, on_navigated, temporary=True)
    
    # Disparar navegação
    button = await tab.find(id='next-page')
    await button.click()
    
    # Esperar completar
    await navigation_done.wait()
    print("Navegação concluída!")
```

### Detecção de Ociosidade da Rede (Network Idle)

```python
import asyncio
from pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    LoadingFinishedEvent,
    LoadingFailedEvent
)

async def wait_for_network_idle(tab, timeout=5):
    in_flight = 0
    idle_event = asyncio.Event()
    last_activity = asyncio.get_event_loop().time()
    
    async def on_request(event: RequestWillBeSentEvent):
        nonlocal in_flight, last_activity
        in_flight += 1
        last_activity = asyncio.get_event_loop().time()
    
    async def on_finished(event: LoadingFinishedEvent | LoadingFailedEvent):
        nonlocal in_flight, last_activity
        in_flight -= 1
        last_activity = asyncio.get_event_loop().time()
        
        if in_flight == 0:
            idle_event.set()
    
    await tab.enable_network_events()
    req_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, on_request)
    fin_id = await tab.on(NetworkEvent.LOADING_FINISHED, on_finished)
    fail_id = await tab.on(NetworkEvent.LOADING_FAILED, on_finished)
    
    try:
        await asyncio.wait_for(idle_event.wait(), timeout=timeout)
        print("Rede está ociosa!")
    except asyncio.TimeoutError:
        print(f"Rede ainda ativa após {timeout}s")
    finally:
        # Limpeza
        await tab.remove_callback(req_id)
        await tab.remove_callback(fin_id)
        await tab.remove_callback(fail_id)
```

### Raspagem de Conteúdo Dinâmico

```python
import asyncio
import json
from functools import partial
from pydoll.protocol.network.events import NetworkEvent, ResponseReceivedEvent

async def scrape_infinite_scroll(tab, max_items=100):
    items = []
    
    async def capture_products(tab, items_list, event: ResponseReceivedEvent):
        url = event['params']['response']['url']
        
        # Procurar por endpoint de API de produtos
        if '/products' not in url:
            return
        
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        
        try:
            data = json.loads(body)
            if 'items' in data:
                items_list.extend(data['items'])
                print(f"Coletados {len(data['items'])} itens (total: {len(items_list)})")
        except json.JSONDecodeError:
            pass
    
    await tab.enable_network_events()
    await tab.on(
        NetworkEvent.RESPONSE_RECEIVED,
        partial(capture_products, tab, items)
    )
    
    await tab.go_to("https://example.com/products")
    
    # Rolar para disparar carregamento infinito
    while len(items) < max_items:
        await tab.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
    
    return items[:max_items]
```

## Tabelas de Referência de Eventos

### Domínios Disponíveis

| Domínio | Método de Habilitação | Casos de Uso Comuns |
|---|---|---|
| Page | `enable_page_events()` | Ciclo de vida da página, navegação, diálogos |
| Network | `enable_network_events()` | Monitoramento de requisição/resposta, rastreamento de API |
| DOM | `enable_dom_events()` | Mudanças na estrutura DOM, modificações de atributos |
| Fetch | `enable_fetch_events()` | Interceptação e modificação de requisições |
| Runtime | `enable_runtime_events()` | Mensagens do console, exceções JavaScript |

### Eventos Chave de Página (Page)

| Evento | Quando Dispara | Caso de Uso |
|---|---|---|
| `LOAD_EVENT_FIRED` | Carregamento da página completo | Esperar pelo carregamento completo da página |
| `DOM_CONTENT_EVENT_FIRED` | DOM pronto | Iniciar manipulação do DOM |
| `JAVASCRIPT_DIALOG_OPENING` | Alert/confirm/prompt | Lidar automaticamente com diálogos |
| `FRAME_NAVIGATED` | Navegação completa | Rastrear navegação de SPA |
| `FILE_CHOOSER_OPENED` | Input de arquivo clicado | Uploads automáticos de arquivos |

### Eventos Chave de Rede (Network)

| Evento | Quando Dispara | Caso de Uso |
|---|---|---|
| `REQUEST_WILL_BE_SENT` | Antes da requisição ser enviada | Registrar/modificar requisições de saída |
| `RESPONSE_RECEIVED` | Cabeçalhos da resposta recebidos | Capturar respostas de API |
| `LOADING_FINISHED` | Corpo da resposta carregado | Obter dados completos da resposta |
| `LOADING_FAILED` | Requisição falhou | Rastrear erros e retentativas |
| `WEB_SOCKET_CREATED` | WebSocket aberto | Monitorar conexões em tempo real |

### Eventos Chave do DOM

| Evento | Quando Dispara | Caso de Uso |
|---|---|---|
| `DOCUMENT_UPDATED` | DOM reconstruído | Atualizar referências de elementos |
| `ATTRIBUTE_MODIFIED` | Atributo do elemento mudou | Rastrear mudanças dinâmicas de atributos |
| `CHILD_NODE_INSERTED` | Novo elemento adicionado | Detectar conteúdo adicionado dinamicamente |
| `CHILD_NODE_REMOVED` | Elemento removido | Detectar conteúdo removido |

### Referência de Tipo de Evento

Todos os tipos de evento e suas estruturas de parâmetros são definidos nos módulos de protocolo:

| Domínio | Caminho de Importação | Tipos de Exemplo |
|---|---|---|
| Page | `pydoll.protocol.page.events` | `LoadEventFiredEvent`, `FrameNavigatedEvent`, `JavascriptDialogOpeningEvent` |
| Network | `pydoll.protocol.network.events` | `RequestWillBeSentEvent`, `ResponseReceivedEvent`, `LoadingFinishedEvent` |
| DOM | `pydoll.protocol.dom.events` | `DocumentUpdatedEvent`, `AttributeModifiedEvent`, `ChildNodeInsertedEvent` |
| Fetch | `pydoll.protocol.fetch.events` | `RequestPausedEvent`, `AuthRequiredEvent` |
| Runtime | `pydoll.protocol.runtime.events` | `ConsoleAPICalledEvent`, `ExceptionThrownEvent` |

Cada tipo de evento é um `TypedDict` que define a estrutura exata do evento, incluindo todas as chaves disponíveis no dicionário `params`.

## Melhores Práticas

### 1. Sempre Habilite os Domínios Primeiro

```python
from pydoll.protocol.network.events import NetworkEvent

# Bom
await tab.enable_network_events()
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)

# Ruim: callback nunca será disparado
await tab.on(NetworkEvent.RESPONSE_RECEIVED, callback)
await tab.enable_network_events()
```

### 2. Limpe Quando Terminar

```python
from pydoll.protocol.network.events import NetworkEvent

# Habilitar para tarefa específica
await tab.enable_network_events()
callback_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)

# Faça seu trabalho...
await tab.go_to("https://example.com")

# Limpar
await tab.remove_callback(callback_id)
await tab.disable_network_events()
```

### 3. Use Filtragem Precoce

```python
from pydoll.protocol.network.events import RequestWillBeSentEvent

# Bom: filtrar cedo
async def handle_api_request(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    if '/api/' not in url:
        return  # Sair cedo
    
    # Processar apenas requisições de API
    process_request(event)

# Ruim: processa tudo
async def handle_all_requests(event: RequestWillBeSentEvent):
    url = event['params']['request']['url']
    process_request(event)
    if '/api/' in url:
        do_extra_work(event)
```

### 4. Lide com Erros Graciosamente

```python
from pydoll.protocol.network.events import ResponseReceivedEvent

async def safe_callback(event: ResponseReceivedEvent):
    try:
        request_id = event['params']['requestId']
        body = await tab.get_network_response_body(request_id)
        process_body(body)
    except KeyError:
        # Evento pode não ter requestId
        pass
    except Exception as e:
        print(f"Erro no callback: {e}")
        # Continuar sem quebrar o loop de eventos
```

## Considerações de Desempenho

!!! warning "Eventos de Alta Frequência"
    Eventos DOM podem disparar **muito frequentemente** em páginas dinâmicas. Use filtragem e debouncing para evitar problemas de desempenho.

### Volume de Eventos por Domínio

| Domínio | Frequência de Eventos | Impacto no Desempenho |
|---|---|---|
| Page | Baixa | Mínimo |
| Network | Moderada-Alta | Moderado |
| DOM | Muito Alta | Alto |
| Fetch | Moderada | Moderado |

### Dicas de Otimização

1.  **Habilite apenas o que você precisa**: Não habilite todos os domínios de uma vez
2.  **Use callbacks temporários**: Limpeza automática quando possível
3.  **Filtre cedo**: Verifique condições antes de operações caras
4.  **Desabilite quando terminar**: Libere recursos
5.  **Evite processamento pesado**: Mantenha callbacks rápidos, descarregue o trabalho para tarefas separadas

```python
import asyncio
from pydoll.protocol.network.events import ResponseReceivedEvent

# Bom: callback rápido, descarrega trabalho pesado
async def handle_response(event: ResponseReceivedEvent):
    if should_process(event):
        asyncio.create_task(heavy_processing(event))  # Não bloqueie

# Ruim: bloqueia o loop de eventos
async def handle_response(event: ResponseReceivedEvent):
    await heavy_processing(event)  # Bloqueia outros eventos
```

## Padrões Comuns

### Gerenciador de Contexto para Eventos

```python
from contextlib import asynccontextmanager
from pydoll.protocol.network.events import NetworkEvent, RequestWillBeSentEvent

@asynccontextmanager
async def monitor_requests(tab):
    """Gerenciador de contexto para monitorar requisições durante um bloco."""
    requests = []
    
    async def capture(event: RequestWillBeSentEvent):
        requests.append(event['params']['request'])
    
    await tab.enable_network_events()
    cb_id = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, capture)
    
    try:
        yield requests
    finally:
        await tab.remove_callback(cb_id)
        await tab.disable_network_events()

# Uso
async with monitor_requests(tab) as requests:
    await tab.go_to("https://example.com")
    # Todas as requisições são capturadas

print(f"Capturadas {len(requests)} requisições")
```

### Registro Condicional de Eventos

```python
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.dom.events import DomEvent

async def setup_monitoring(tab, track_network=False, track_dom=False):
    """Habilitar apenas o monitoramento especificado."""
    callbacks = []
    
    if track_network:
        await tab.enable_network_events()
        cb = await tab.on(NetworkEvent.REQUEST_WILL_BE_SENT, log_request)
        callbacks.append(('network', cb))
    
    if track_dom:
        await tab.enable_dom_events()
        cb = await tab.on(DomEvent.ATTRIBUTE_MODIFIED, log_dom_change)
        callbacks.append(('dom', cb))
    
    return callbacks
```

## Leitura Adicional

- **[Análise Profunda da Arquitetura de Eventos](../../deep-dive/event-architecture.md)** - Implementação interna e comunicação WebSocket
- **[Monitoramento de Rede](../network/monitoring.md)** - Técnicas avançadas de análise de rede
- **[Automação Reativa](reactive-automation.md)** - Construindo fluxos de trabalho orientados a eventos

!!! tip "Comece Simples"
    Comece com eventos de Página (Page) para entender o básico, depois passe para eventos de Rede (Network) e DOM conforme necessário. O sistema de eventos é poderoso, mas pode ser intimidador no início.