# Requisições do Navegador

O módulo de requisições (requests) fornece capacidades de requisição HTTP dentro do contexto do navegador, permitindo chamadas de API contínuas que herdam o estado de sessão, cookies e autenticação do navegador.

## Visão Geral

O módulo de requisições do navegador oferece uma interface semelhante à do `requests` para fazer chamadas HTTP diretamente dentro do contexto JavaScript do navegador. Esta abordagem oferece várias vantagens sobre as bibliotecas HTTP tradicionais:

- **Herança de sessão**: Manipulação automática de cookies, autenticação e CORS
- **Contexto do navegador**: As requisições são executadas no mesmo contexto de segurança da página
- **Sem malabarismo de sessão**: Elimina a necessidade de transferir cookies e tokens entre a automação e as chamadas de API
- **Compatibilidade com SPA**: Perfeito para Single Page Applications (Aplicações de Página Única) com fluxos de autenticação complexos

## Classe Request

A interface principal para fazer requisições HTTP dentro do contexto do navegador.

::: pydoll.browser.requests.request.Request
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## Classe Response

Representa a resposta de requisições HTTP, fornecendo uma interface familiar semelhante à biblioteca `requests`.

::: pydoll.browser.requests.response.Response
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      group_by_category: true
      members_order: source
      filters:
        - "!^__"

## Exemplos de Uso

### Métodos HTTP Básicos

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://api.example.com")
    
    # Requisição GET
    response = await tab.request.get("/users/123")
    user_data = await response.json()
    
    # Requisição POST
    response = await tab.request.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    
    # Requisição PUT com cabeçalhos
    response = await tab.request.put("/users/123", 
        json={"name": "Jane Doe"},
        headers={"Authorization": "Bearer token123"}
    )
```

### Manipulação de Resposta

```python
# Verificar status da resposta
if response.ok:
    print(f"Sucesso: {response.status_code}")
else:
    print(f"Erro: {response.status_code}")
    response.raise_for_status()  # Levanta HTTPError para 4xx/5xx

# Acessar dados da resposta
text_data = response.text
json_data = await response.json()
raw_bytes = response.content

# Inspecionar cabeçalhos e cookies
print("Cabeçalhos da resposta:", response.headers)
print("Cabeçalhos da requisição:", response.request_headers)
for cookie in response.cookies:
    print(f"Cookie: {cookie.name}={cookie.value}")
```

### Recursos Avançados

```python
# Requisição com cabeçalhos e parâmetros customizados
response = await tab.request.get("/search", 
    params={"q": "python", "limit": 10},
    headers={
        "User-Agent": "Custom Bot 1.0",
        "Accept": "application/json"
    }
)

# Simulação de upload de arquivo
response = await tab.request.post("/upload",
    data={"description": "Test file"},
    files={"file": ("test.txt", "file content", "text/plain")}
)

# Submissão de dados de formulário
response = await tab.request.post("/login",
    data={"username": "user", "password": "pass"}
)
```

## Integração com a Aba (Tab)

A funcionalidade de requisição é acessada através da propriedade `tab.request`, que fornece uma instância `Request` singleton para cada aba:

```python
# Cada aba tem sua própria instância de requisição
tab1 = await browser.get_tab(0)
tab2 = await browser.new_tab()

# Estas são instâncias de Request separadas
request1 = tab1.request  # Requisição vinculada à tab1
request2 = tab2.request  # Requisição vinculada à tab2

# Requisições herdam o contexto da aba
await tab1.go_to("https://site1.com")
await tab2.go_to("https://site2.com")

# Estas requisições terão contextos de cookie/sessão diferentes
response1 = await tab1.request.get("/api/data")  # Usa cookies de site1.com
response2 = await tab2.request.get("/api/data")  # Usa cookies de site2.com
```

!!! tip "Automação Híbrida"
    Este módulo é particularmente poderoso para cenários de automação híbrida onde você precisa combinar interações de UI com chamadas de API. Por exemplo, faça login através da UI, depois use a sessão autenticada para chamadas de API sem manipular manualmente cookies ou tokens.