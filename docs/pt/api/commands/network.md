# Comandos de Rede (Network)

Os comandos de rede fornecem controle abrangente sobre requisições de rede, respostas e comportamento de rede do navegador.

## Visão Geral

O módulo de comandos de rede habilita a interceptação de requisições, modificação de respostas, gerenciamento de cookies e capacidades de monitoramento de rede.

::: pydoll.commands.network_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de rede são usados para cenários avançados como interceptação de requisições e monitoramento de rede:

```python
from pydoll.commands.network_commands import enable, set_request_interception
from pydoll.connection.connection_handler import ConnectionHandler

# Habilitar monitoramento de rede
connection = ConnectionHandler()
await enable(connection)

# Habilitar interceptação de requisições
await set_request_interception(connection, patterns=[{"urlPattern": "*"}])
```

## Funcionalidades Principais

O módulo de comandos de rede fornece funções para:

### Gerenciamento de Requisições
- `enable()` / `disable()` - Habilitar/desabilitar monitoramento de rede
- `set_request_interception()` - Interceptar e modificar requisições
- `continue_intercepted_request()` - Continuar ou modificar requisições interceptadas
- `get_request_post_data()` - Obter dados do corpo (body) da requisição

### Manipulação de Respostas
- `get_response_body()` - Obter conteúdo da resposta
- `fulfill_request()` - Fornecer respostas customizadas
- `fail_request()` - Simular falhas de rede

### Gerenciamento de Cookies
- `get_cookies()` - Obter cookies do navegador
- `set_cookies()` - Definir cookies do navegador
- `delete_cookies()` - Deletar cookies específicos
- `clear_browser_cookies()` - Limpar todos os cookies

### Controle de Cache
- `clear_browser_cache()` - Limpar cache do navegador
- `set_cache_disabled()` - Desabilitar cache do navegador
- `get_response_body_for_interception()` - Obter respostas em cache

### Segurança & Cabeçalhos
- `set_user_agent_override()` - Sobrescrever user agent
- `set_extra_http_headers()` - Adicionar cabeçalhos customizados
- `emulate_network_conditions()` - Simular condições de rede

## Casos de Uso Avançados

### Interceptação de Requisição
```python
# Interceptar e modificar requisições
await set_request_interception(connection, patterns=[
    {"urlPattern": "*/api/*", "requestStage": "Request"}
])

# Lidar com requisição interceptada
async def handle_request(request):
    if "api/login" in request.url:
        # Modificar cabeçalhos da requisição
        headers = request.headers.copy()
        headers["Authorization"] = "Bearer token"
        await continue_intercepted_request(
            connection, 
            request_id=request.request_id,
            headers=headers
        )
```

### Simulação de Resposta (Mocking)
```python
# Simular (mockar) respostas de API
await fulfill_request(
    connection,
    request_id=request_id,
    response_code=200,
    response_headers={"Content-Type": "application/json"},
    body='{"status": "success"}'
)
```

!!! warning "Impacto na Performance"
    A interceptação de rede pode impactar a performance de carregamento da página. Use seletivamente e desabilite quando não for necessário.