# Comandos Fetch

Os comandos Fetch fornecem capacidades avançadas de manipulação e interceptação de requisições de rede usando o domínio da API Fetch.

## Visão Geral

O módulo de comandos fetch permite o gerenciamento sofisticado de requisições de rede, incluindo modificação de requisições, interceptação de respostas e manipulação de autenticação.

::: pydoll.commands.fetch_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos Fetch são usados para interceptação avançada de rede e manipulação de requisições:

```python
from pydoll.commands.fetch_commands import enable, request_paused, continue_request
from pydoll.connection.connection_handler import ConnectionHandler

# Habilitar domínio fetch
connection = ConnectionHandler()
await enable(connection, patterns=[{
    "urlPattern": "*",
    "requestStage": "Request"
}])

# Lidar com requisições pausadas
async def handle_paused_request(request_id, request):
    # Modificar requisição ou continuar como está
    await continue_request(connection, request_id=request_id)
```

## Funcionalidades Principais

O módulo de comandos fetch fornece funções para:

### Interceptação de Requisição
- `enable()` - Habilitar domínio fetch com padrões
- `disable()` - Desabilitar domínio fetch
- `continue_request()` - Continuar requisições interceptadas
- `fail_request()` - Falhar requisições com erros específicos

### Modificação de Requisição
- Modificar cabeçalhos da requisição
- Alterar URLs da requisição
- Alterar métodos da requisição (GET, POST, etc.)
- Modificar corpos (bodies) da requisição

### Manipulação de Resposta
- `fulfill_request()` - Fornecer respostas customizadas
- `get_response_body()` - Obter conteúdo da resposta
- Modificação de cabeçalho de resposta
- Controle do código de status da resposta

### Autenticação
- `continue_with_auth()` - Lidar com desafios de autenticação
- Suporte a autenticação básica
- Fluxos de autenticação customizados

## Recursos Avançados

### Interceptação Baseada em Padrões
```python
# Interceptar padrões de URL específicos
patterns = [
    {"urlPattern": "*/api/*", "requestStage": "Request"},
    {"urlPattern": "*.js", "requestStage": "Response"},
    {"urlPattern": "https://example.com/*", "requestStage": "Request"}
]

await enable(connection, patterns=patterns)
```

### Modificação de Requisição
```python
# Modificar requisições interceptadas
async def modify_request(request_id, request):
    # Adicionar cabeçalho de autenticação
    headers = request.headers.copy()
    headers["Authorization"] = "Bearer token123"
    
    # Continuar com cabeçalhos modificados
    await continue_request(
        connection,
        request_id=request_id,
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
    response_headers=[
        {"name": "Content-Type", "value": "application/json"},
        {"name": "Access-Control-Allow-Origin", "value": "*"}
    ],
    body='{"status": "success", "data": {"mocked": true}}'
)
```

### Manipulação de Autenticação
```python
# Lidar com desafios de autenticação
await continue_with_auth(
    connection,
    request_id=request_id,
    auth_challenge_response={
        "response": "ProvideCredentials",
        "username": "user",
        "password": "pass"
    }
)
```

## Estágios da Requisição

Os comandos Fetch podem interceptar requisições em diferentes estágios:

| Estágio | Descrição | Casos de Uso |
|-------|-------------|-----------|
| Requisição | Antes da requisição ser enviada | Modificar cabeçalhos, URL, método |
| Resposta | Após a resposta ser recebida | Simular respostas, modificar conteúdo |

## Manipulação de Erros

```python
# Falhar requisições com erros específicos
await fail_request(
    connection,
    request_id=request_id,
    error_reason="ConnectionRefused"  # ou "AccessDenied", "TimedOut", etc.
)
```

## Integração com Comandos de Rede (Network)

Os comandos Fetch trabalham em conjunto com os comandos de rede (Network), mas fornecem controle mais granular:

- **Comandos de Rede (Network)**: Monitoramento e controle de rede mais amplos
- **Comandos Fetch**: Interceptação e modificação específicas de requisição/resposta

!!! tip "Considerações de Performance"
    A interceptação do Fetch pode impactar a performance de carregamento da página. Use padrões de URL específicos e desabilite quando não for necessário para minimizar a sobrecarga (overhead).