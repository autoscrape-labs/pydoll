# Requisições HTTP no Contexto do Navegador

Faça requisições HTTP que herdam automaticamente o estado de sessão, cookies e autenticação do seu navegador. Perfeito para automação híbrida, combinando navegação de UI com a eficiência de APIs.

!!! tip "Uma Revolução para Automação Híbrida"
    Já desejou poder fazer requisições HTTP que automaticamente obtêm todos os cookies e autenticação do seu navegador? Agora você pode! A propriedade `tab.request` oferece uma bela interface semelhante ao `requests` que executa chamadas HTTP **diretamente no contexto JavaScript do navegador**.

## Por que Usar Requisições no Contexto do Navegador?

A automação tradicional frequentemente exige que você extraia cookies e cabeçalhos manualmente para fazer chamadas de API. As requisições no contexto do navegador eliminam esse incômodo:

| Abordagem Tradicional | Requisições no Contexto do Navegador |
|---|---|
| Extrair cookies manualmente | Cookies herdados automaticamente |
| Gerenciar tokens de sessão | Estado da sessão preservado |
| Lidar com CORS separadamente | Políticas CORS respeitadas |
| Lidar com dois clientes HTTP | Uma interface unificada |
| Sincronizar estado de autenticação | Sempre autenticado |

**Perfeito para:**

- Raspar APIs autenticadas após login via UI
- Fluxos de trabalho híbridos misturando interação de navegador e chamadas de API
- Testar endpoints autenticados sem gerenciamento de token
- Contornar fluxos complexos de autenticação
- Trabalhar com aplicações de página única (SPAs)

## Guia Rápido

O exemplo mais simples: fazer login via UI e, em seguida, fazer chamadas de API autenticadas:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def hybrid_automation():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 1. Faça login normalmente através da UI
        await tab.go_to('https://example.com/login')
        await (await tab.find(id='username')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password123')
        await (await tab.find(id='login-btn')).click()
        
        # Aguarde o redirecionamento após o login
        await asyncio.sleep(2)
        
        # 2. Agora faça chamadas de API com a sessão autenticada!
        response = await tab.request.get('https://example.com/api/user/profile')
        user_data = response.json()
        
        print(f"Logado como: {user_data['name']}")
        print(f"Email: {user_data['email']}")

asyncio.run(hybrid_automation())
```

!!! success "Nenhum Gerenciamento de Cookie Necessário"
    Percebeu como não extraímos ou passamos nenhum cookie? A requisição herdou automaticamente a sessão autenticada do navegador!

## Casos de Uso Comuns

### 1. Raspagem de APIs Autenticadas

Use a UI para fazer login e, em seguida, dispare requisições às APIs para extração de dados:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def scrape_user_data():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Login via UI (lida com fluxos de autenticação complexos)
        await tab.go_to('https://app.example.com/login')
        await (await tab.find(id='email')).type_text('user@example.com')
        await (await tab.find(id='password')).type_text('password')
        await (await tab.find(type='submit')).click()
        await asyncio.sleep(2)
        
        # Agora extraia dados via API (muito mais rápido que raspar UI)
        all_users = []
        for page in range(1, 6):
            response = await tab.request.get(
                f'https://app.example.com/api/users',
                params={'page': str(page), 'limit': '100'}
            )
            users = response.json()['users']
            all_users.extend(users)
            print(f"Página {page}: buscou {len(users)} usuários")
        
        print(f"Total de usuários raspados: {len(all_users)}")

asyncio.run(scrape_user_data())
```

### 2. Testando Endpoints Protegidos

Teste endpoints de API sem gerenciar tokens de autenticação:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_api_endpoints():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Autentique uma vez
        await tab.go_to('https://api.example.com/login')
        # ... realize o login ...
        await asyncio.sleep(2)
        
        # Teste múltiplos endpoints
        endpoints = [
            '/api/users/me',
            '/api/settings',
            '/api/notifications',
            '/api/dashboard/stats'
        ]
        
        for endpoint in endpoints:
            response = await tab.request.get(f'https://api.example.com{endpoint}')
            
            if response.ok:
                print(f"Sucesso {endpoint}: {response.status_code}")
            else:
                print(f"Falha {endpoint}: {response.status_code}")
                print(f"   Erro: {response.text[:100]}")

asyncio.run(test_api_endpoints())
```

### 3. Enviando Formulários via API

Preencha formulários mais rapidamente postando diretamente para a API:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def bulk_form_submission():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Faça login primeiro
        await tab.go_to('https://crm.example.com/login')
        # ... lógica de login ...
        await asyncio.sleep(2)
        
        # Envie múltiplas entradas via API (muito mais rápido que preencher formulários)
        contacts = [
            {'name': 'John Doe', 'email': 'john@example.com', 'company': 'Acme Inc'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'company': 'Tech Corp'},
            {'name': 'Bob Wilson', 'email': 'bob@example.com', 'company': 'StartupXYZ'},
        ]
        
        for contact in contacts:
            response = await tab.request.post(
                'https://crm.example.com/api/contacts',
                json=contact
            )
            
            if response.ok:
                print(f"Adicionado: {contact['name']}")
            else:
                print(f"Falha: {contact['name']} - {response.status_code}")

asyncio.run(bulk_form_submission())
```

### 4. Baixando Arquivos com Sessão

Baixe arquivos que exigem autenticação:

```python
import asyncio
from pathlib import Path
from pydoll.browser.chromium import Chrome

async def download_authenticated_file():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Autentique
        await tab.go_to('https://portal.example.com/login')
        # ... lógica de login ...
        await asyncio.sleep(2)
        
        # Baixe o arquivo que requer autenticação
        response = await tab.request.get(
            'https://portal.example.com/api/reports/monthly.pdf'
        )
        
        if response.ok:
            # Salve o arquivo
            output_path = Path('/tmp/monthly_report.pdf')
            output_path.write_bytes(response.content)
            print(f"Baixado: {output_path} ({len(response.content)} bytes)")
        else:
            print(f"Download falhou: {response.status_code}")

asyncio.run(download_authenticated_file())
```

### 5. Trabalhando com Cabeçalhos Personalizados

Adicione cabeçalhos personalizados às suas requisições:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def custom_headers_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Faça login primeiro
        await tab.go_to('https://api.example.com/login')
        # ... lógica de login ...
        
        # Faça requisição com cabeçalhos personalizados
        headers: list[HeaderEntry] = [
            {'name': 'X-API-Version', 'value': '2.0'},
            {'name': 'X-Request-ID', 'value': 'unique-id-123'},
            {'name': 'Accept-Language', 'value': 'pt-BR,pt;q=0.9'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/data',
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json()}")

asyncio.run(custom_headers_example())
```

### 6. Lidando com Diferentes Tipos de Resposta

Acesse dados de resposta em múltiplos formatos:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def response_formats():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://api.example.com')
        
        # Resposta JSON
        json_response = await tab.request.get('/api/users/1')
        user = json_response.json()
        print(f"JSON: {user}")
        
        # Resposta de texto
        text_response = await tab.request.get('/api/status')
        status_text = text_response.text
        print(f"Texto: {status_text}")
        
        # Resposta binária (ex: imagem)
        image_response = await tab.request.get('/api/avatar/1')
        image_bytes = image_response.content
        print(f"Binário: {len(image_bytes)} bytes")
        
        # Verificar status da resposta
        if json_response.ok:
            print("Requisição bem-sucedida!")
        
        # Acessar URL da resposta (útil após redirecionamentos)
        print(f"URL Final: {json_response.url}")

asyncio.run(response_formats())
```

## Métodos HTTP

Todos os métodos HTTP padrão são suportados:

### GET - Recuperar Dados

```python
# GET simples
response = await tab.request.get('https://api.example.com/users')

# GET com parâmetros de consulta
response = await tab.request.get(
    'https://api.example.com/search',
    params={'q': 'python', 'limit': '10'}
)
```

### POST - Criar Recursos

```python
# POST com dados JSON
response = await tab.request.post(
    'https://api.example.com/users',
    json={'name': 'John Doe', 'email': 'john@example.com'}
)

# POST com dados de formulário
response = await tab.request.post(
    'https://api.example.com/login',
    data={'username': 'john', 'password': 'secret'}
)
```

### PUT - Atualizar Recursos

```python
# Atualizar recurso inteiro
response = await tab.request.put(
    'https://api.example.com/users/123',
    json={'name': 'Jane Doe', 'email': 'jane@example.com', 'role': 'admin'}
)
```

### PATCH - Atualizações Parciais

```python
# Atualizar campos específicos
response = await tab.request.patch(
    'https://api.example.com/users/123',
    json={'email': 'newemail@example.com'}
)
```

### DELETE - Remover Recursos

```python
# Deletar um recurso
response = await tab.request.delete('https://api.example.com/users/123')
```

### HEAD - Obter Apenas Cabeçalhos

```python
# Verificar se o recurso existe sem baixá-lo
response = await tab.request.head('https://example.com/large-file.zip')
print(f"Content-Length: {response.headers}")
```

### OPTIONS - Verificar Capacidades

```python
# Verificar métodos permitidos
response = await tab.request.options('https://api.example.com/users')
print(f"Métodos permitidos: {response.headers}")
```

!!! info "Como Isso Funciona?"
    Requisições no contexto do navegador executam chamadas HTTP diretamente no contexto JavaScript do navegador usando a API Fetch, enquanto monitoram eventos de rede CDP para capturar metadados abrangentes (cabeçalhos, cookies, tempo).
    
    Para uma explicação detalhada da arquitetura interna, monitoramento de eventos e detalhes de implementação, veja a [Arquitetura de Requisições do Navegador](../../deep-dive/browser-requests-architecture.md).

## Objeto Response

O objeto `Response` fornece uma interface familiar semelhante ao `requests.Response`:

```python
response = await tab.request.get('https://api.example.com/users')

# Código de status
print(response.status_code)  # 200, 404, 500, etc.

# Verificar se foi bem-sucedido (2xx ou 3xx)
if response.ok:
    print("Sucesso!")

# Corpo da resposta
text_data = response.text      # Como string
byte_data = response.content   # Como bytes
json_data = response.json()    # JSON parseado

# Cabeçalhos
for header in response.headers:
    print(f"{header['name']}: {header['value']}")

# Cabeçalhos da requisição (o que foi realmente enviado)
for header in response.request_headers:
    print(f"{header['name']}: {header['value']}")

# Cookies definidos pela resposta
for cookie in response.cookies:
    print(f"{cookie['name']} = {cookie['value']}")

# URL final (após redirecionamentos)
print(response.url)

# Lançar exceção para códigos de status de erro
response.raise_for_status()  # Lança HTTPError se for 4xx ou 5xx
```

!!! note "Redirecionamentos e Rastreamento de URL"
    A propriedade `response.url` contém apenas a **URL final** após todos os redirecionamentos. Se você precisar rastrear a cadeia completa de redirecionamento (URLs intermediárias, códigos de status, tempo), use o [Monitoramento de Rede](monitoring.md) para observar todas as requisições em detalhes.

## Cabeçalhos e Cookies

### Trabalhando com Cabeçalhos

Cabeçalhos são representados como objetos `HeaderEntry`:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.fetch.types import HeaderEntry

async def header_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Usando o tipo HeaderEntry para autocompletar da IDE e verificação de tipo
        headers: list[HeaderEntry] = [
            {'name': 'Authorization', 'value': 'Bearer token-123'},
            {'name': 'X-Custom-Header', 'value': 'custom-value'},
        ]
        
        response = await tab.request.get(
            'https://api.example.com/protected',
            headers=headers
        )
        
        # Inspecionar cabeçalhos de resposta (também são dicts tipados HeaderEntry)
        for header in response.headers:
            if header['name'] == 'Content-Type':
                print(f"Content-Type: {header['value']}")

asyncio.run(header_example())
```

!!! tip "Dicas de Tipo para Cabeçalhos"
    `HeaderEntry` é um `TypedDict` de `pydoll.protocol.fetch.types`. Usá-lo como uma dica de tipo oferece a você:
    
    - **Autocompletar**: IDE sugere chaves `name` e `value`
    - **Segurança de tipo**: Pega erros de digitação e chaves faltantes antes de rodar
    - **Documentação**: Estrutura clara para cabeçalhos
    
    Embora você possa passar dicionários simples, usar a dica de tipo melhora a qualidade do código e o suporte da IDE.

!!! tip "Comportamento de Cabeçalhos Personalizados"
    Cabeçalhos personalizados são enviados **juntamente com** os cabeçalhos automáticos do navegador (como `User-Agent`, `Accept`, `Referer`, etc.). 
    
    Se você tentar definir um cabeçalho padrão do navegador (ex: `User-Agent`), o comportamento depende do cabeçalho específico; alguns podem ser sobrescritos, outros ignorados, e alguns podem causar conflitos. Para a maioria dos casos de uso, atenha-se a cabeçalhos personalizados (ex: `X-API-Key`, `Authorization`) para evitar comportamentos inesperados.

### Entendendo Cookies

Cookies são gerenciados automaticamente pelo navegador:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def cookie_example():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Primeira requisição define cookies
        login_response = await tab.request.post(
            'https://api.example.com/login',
            json={'username': 'user', 'password': 'pass'}
        )
        
        # Verificar cookies definidos pelo servidor
        print("Cookies definidos pelo servidor:")
        for cookie in login_response.cookies:
            print(f"  {cookie['name']} = {cookie['value']}")
        
        # Requisições subsequentes incluem cookies automaticamente
        profile_response = await tab.request.get(
            'https://api.example.com/profile'
        )
        # Não é preciso passar cookies - o navegador cuida disso!
        
        print(f"Dados do perfil: {profile_response.json()}")

asyncio.run(cookie_example())
```

## Comparação com Requisições Tradicionais

| Funcionalidade | Biblioteca `requests` | Requisições no Contexto do Navegador |
|---|---|---|
| **Gerenciamento de Sessão** | Manual (cookies) | Automático via navegador |
| **Autenticação** | Extrair e passar tokens | Herdada do navegador |
| **CORS** | Não aplicável | Navegador impõe políticas |
| **JavaScript** | Não pode executar | Acesso total ao contexto do navegador |
| **Armazenamento de Cookies** | Instância separada | Armazenamento nativo de cookies do navegador |
| **Cabeçalhos** | Definidos manualmente | Navegador adiciona cabeçalhos padrão |
| **Caso de Uso** | Scripts do lado do servidor | Automação de navegador |
| **Configuração** | Biblioteca externa | Embutido no Pydoll |

## Veja Também

- **[Arquitetura de Requisições do Navegador](../../deep-dive/browser-requests-architecture.md)** - Implementação interna e arquitetura
- **[Monitoramento de Rede](monitoring.md)** - Observe todo o tráfego de rede
- **[Interceptação de Requisições](interception.md)** - Modifique requisições antes de serem enviadas
- **[Sistema de Eventos](../advanced/event-system.md)** - Reaja a eventos do navegador
- **[Análise Profunda: Capacidades de Rede](../../deep-dive/network-capabilities.md)** - Detalhes técnicos

Requisições no contexto do navegador são uma virada de jogo para automação híbrida. Combine o poder da automação de UI com a velocidade de chamadas diretas de API, tudo isso mantendo a continuidade perfeita da sessão!