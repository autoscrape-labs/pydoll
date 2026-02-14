# Cookies e Sessões

Gerenciar cookies e sessões de forma eficaz é crucial para uma automação de navegador realista. Os sites usam cookies para rastrear autenticação, preferências e comportamento do usuário, e esperam que os navegadores se comportem de acordo.

## Por que os Cookies Importam para a Automação

Cookies são mais do que apenas dados armazenados: eles são uma impressão digital (fingerprint) da atividade do navegador:

- **Autenticação**: Cookies de sessão mantêm o estado de login entre as requisições
- **Prevenção de Rastreamento**: Sistemas anti-bot analisam padrões de cookies
- **Comportamento Realista**: Um navegador sem cookies parece suspeito
- **Persistência de Sessão**: Reutilizar cookies pode economizar tempo em logins repetidos

!!! warning "O Paradoxo dos Cookies"
    - **Muito limpo**: Um navegador sem cookies ou histórico parece ser um bot
    - **Muito obsoleto**: Usar a mesma sessão por semanas aciona alertas de segurança
    - **Ponto ideal**: Cookies novos com rotação ocasional e padrões de atividade realistas

## Guia Rápido

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def basic_cookie_management():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        # Definir um cookie (usando um dict simples)
        cookies = [
            {
                'name': 'session_id',
                'value': 'abc123xyz',
                'domain': 'example.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            }
        ]
        await tab.set_cookies(cookies)
        
        # Obter todos os cookies
        all_cookies = await browser.get_cookies()
        print(f"Total de cookies: {len(all_cookies)}")
        
        # Deletar todos os cookies
        await tab.delete_all_cookies()

asyncio.run(basic_cookie_management())
```

## Entendendo os Tipos de Cookie

!!! info "TypedDict: Use Dicionários Regulares na Prática"
    Ao longo desta documentação, você verá referências a `CookieParam` e `Cookie`. Estes são tipos **TypedDict**, eles são apenas dicionários Python regulares com dicas de tipo para autocompletar da IDE e verificação de tipo.
    
    **Na prática, você usa dicionários regulares:**
    ```python
    # Isso é o que você realmente escreve:
    cookie = {'name': 'session', 'value': 'abc123', 'domain': 'example.com'}
    
    # A anotação de tipo é apenas para sua IDE:
    from pydoll.protocol.network.types import CookieParam
    cookie: CookieParam = {'name': 'session', 'value': 'abc123'}
    ```
    
    Todos os exemplos abaixo usam dicionários simples por simplicidade.

### Estrutura do Cookie

O tipo `Cookie` (recuperado do navegador) contém informações completas do cookie:

```python
{
    "name": str,           # Nome do cookie
    "value": str,          # Valor do cookie
    "domain": str,         # Domínio onde o cookie é válido
    "path": str,           # Caminho onde o cookie é válido
    "expires": float,      # Timestamp Unix (0 = cookie de sessão)
    "size": int,           # Tamanho em bytes
    "httpOnly": bool,      # Acessível apenas via HTTP (não JavaScript)
    "secure": bool,        # Enviado apenas por HTTPS
    "session": bool,       # True se expira quando o navegador fecha
    "sameSite": str,       # "Strict", "Lax", ou "None"
    "priority": str,       # "Low", "Medium", ou "High"
    "sourceScheme": str,   # "Unset", "NonSecure", ou "Secure"
    "sourcePort": int,     # Porta onde o cookie foi definido
}
```

### Estrutura do CookieParam

Ao **definir** cookies, use um dict (apenas `name` e `value` são obrigatórios):

```python
# Cookie simples com apenas campos obrigatórios
cookie = {
    'name': 'user_token',
    'value': 'token_value'
}

# Cookie completo com todos os campos opcionais
cookie = {
    'name': 'user_token',       # Obrigatório
    'value': 'token_value',     # Obrigatório
    'domain': 'example.com',    # Opcional: padrão é o domínio da página atual
    'path': '/',                # Opcional: padrão é /
    'secure': True,             # Opcional: Apenas HTTPS
    'httpOnly': True,           # Opcional: sem acesso JS
    'sameSite': 'Lax',          # Opcional: 'Strict', 'Lax', ou 'None'
    'expires': 1735689600,      # Opcional: timestamp Unix
    'priority': 'High',         # Opcional: 'Low', 'Medium', ou 'High'
}
```

!!! info "Comportamento Padrão de Campos Opcionais"
    Quando você omite campos opcionais:
    
    - `domain`: Usa o domínio da página atual
    - `path`: Padrão é `/`
    - `secure`: Padrão é `False`
    - `httpOnly`: Padrão é `False`
    - `sameSite`: Padrão do navegador (geralmente `Lax`)
    - `expires`: Cookie de sessão (deletado quando o navegador fecha)

## Operações de Gerenciamento de Cookies

### Definindo Cookies

#### Definir Múltiplos Cookies de Uma Vez

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def set_multiple_cookies():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com')
        
        cookies = [
            {
                'name': 'session_id',
                'value': 'xyz789',
                'domain': 'example.com',
                'secure': True,
                'httpOnly': True,
                'sameSite': 'Strict'
            },
            {
                'name': 'preferences',
                'value': 'dark_mode=true',
                'domain': 'example.com',
                'path': '/settings'
            },
            {
                'name': 'analytics',
                'value': 'tracking_id_12345',
                'domain': 'example.com',
                'expires': 1735689600  # Expira em data específica
            }
        ]
        
        await tab.set_cookies(cookies)
        print(f"Definidos {len(cookies)} cookies")

asyncio.run(set_multiple_cookies())
```

#### Definir Cookies em Contexto Específico

```python
# Definir cookies em um contexto de navegador específico
context_id = await browser.create_browser_context()
await browser.set_cookies(cookies, browser_context_id=context_id)
```

!!! tip "Métodos de Aba vs Navegador para Definir Cookies"
    - `tab.set_cookies(cookies)`: Define cookies no contexto de navegador da aba (atalho conveniente)
    - `browser.set_cookies(cookies, browser_context_id=...)`: Define cookies com controle explícito de contexto
    
    Ambos os métodos adicionam cookies ao **contexto inteiro**, não apenas à página atual. Os cookies estarão disponíveis para todas as abas naquele contexto.

### Recuperando Cookies

#### Obter Todos os Cookies (Nível do Contexto)

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def get_cookies_example():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://github.com')
        
        # Esperar a página definir cookies
        await asyncio.sleep(2)
        
        # Opção 1: Obter cookies via aba (atalho para o contexto atual)
        cookies = await tab.get_cookies()
        
        # Opção 2: Obter cookies via navegador (controle explícito de contexto)
        # cookies = await browser.get_cookies()  # Mesmo que tab.get_cookies() para o contexto padrão
        
        print(f"Encontrados {len(cookies)} cookies:")
        for cookie in cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
            print(f"    Domínio: {cookie['domain']}, Secure: {cookie['secure']}")

asyncio.run(get_cookies_example())
```

!!! tip "Métodos de Aba vs Navegador"
    - `tab.get_cookies()`: Retorna cookies do contexto de navegador da aba (atalho conveniente)
    - `browser.get_cookies()`: Retorna cookies do contexto padrão (ou especifique `browser_context_id`)
    
    Ambos os métodos retornam **todos os cookies** do contexto, não apenas os cookies para o domínio da página atual.

!!! warning "Limitação do Modo Incógnito"
    `browser.get_cookies()` **não funciona** com o modo incógnito nativo (flag `--incognito`). Esta é uma limitação do Chrome DevTools Protocol onde `Storage.getCookies` não consegue acessar cookies no modo incógnito nativo.
    
    **Solução:** Use `tab.get_cookies()` em vez disso, que usa `Network.getCookies` e funciona corretamente no modo incógnito.

#### Obter Cookies de Contexto Específico

```python
# Obter cookies de um contexto de navegador específico
context_id = await browser.create_browser_context()
cookies = await browser.get_cookies(browser_context_id=context_id)
```

### Deletando Cookies

#### Deletar Todos os Cookies

```python
# Deletar todos os cookies do contexto da aba atual
await tab.delete_all_cookies()

# Deletar todos os cookies de um contexto específico
await browser.delete_all_cookies(browser_context_id=context_id)
```

!!! warning "Cookies São Deletados Imediatamente"
    Quando você deleta cookies, eles são removidos do navegador imediatamente. O site pode não detectar isso até a próxima requisição ou recarregamento da página.

## Casos de Uso Práticos

### 1. Sessões de Login Persistentes

Reutilize cookies de autenticação entre execuções do script:

```python
import asyncio
import json
from pathlib import Path
from pydoll.browser.chromium import Chrome

COOKIE_FILE = Path('cookies.json')

async def save_cookies_after_login():
    """Fazer login e salvar cookies para uso futuro."""
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('https://example.com/login')
        
        # Realizar login (simplificado)
        email = await tab.find(id='email')
        password = await tab.find(id='password')
        await email.type_text('user@example.com')
        await password.type_text('secret')
        
        login_btn = await tab.find(id='login')
        await login_btn.click()
        await asyncio.sleep(3)
        
        # Salvar cookies
        cookies = await browser.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"Salvos {len(cookies)} cookies em {COOKIE_FILE}")

async def reuse_saved_cookies():
    """Carregar cookies salvos para pular o login."""
    if not COOKIE_FILE.exists():
        print("Nenhum cookie salvo encontrado. Execute save_cookies_after_login() primeiro.")
        return
    
    # Carregar cookies do arquivo
    saved_cookies = json.loads(COOKIE_FILE.read_text())
    
    # Converter para formato simplificado (apenas campos obrigatórios)
    # Nota: get_cookies() retorna objetos Cookie detalhados com campos somente leitura
    # (size, session, sourceScheme, etc.). set_cookies() espera o formato CookieParam
    # apenas com os campos configuráveis.
    cookies_to_set = [
        {
            'name': c['name'],
            'value': c['value'],
            'domain': c['domain'],
            'path': c.get('path', '/'),
            'secure': c.get('secure', False),
            'httpOnly': c.get('httpOnly', False)
        }
        for c in saved_cookies
    ]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Definir cookies antes de navegar
        await tab.set_cookies(cookies_to_set)
        print(f"Carregados {len(cookies_to_set)} cookies do arquivo")
        
        # Navegar - já deve estar logado
        await tab.go_to('https://example.com/dashboard')
        await asyncio.sleep(2)
        
        # Verificar login
        try:
            username = await tab.find(class_name='username')
            print(f"Logado como: {await username.text}")
        except Exception:
            print("Login falhou - os cookies podem ter expirado")

# Primeira execução: fazer login e salvar cookies
# asyncio.run(save_cookies_after_login())

# Execuções subsequentes: reutilizar cookies
asyncio.run(reuse_saved_cookies())
```

!!! note "Reformatação de Cookies Necessária"
    `get_cookies()` retorna **objetos `Cookie` detalhados** com atributos somente leitura como `size`, `session`, `sourceScheme` e `sourcePort`. Ao usar `set_cookies()`, você deve fornecer o **formato `CookieParam`** contendo apenas os campos configuráveis (`name`, `value`, `domain`, `path`, `secure`, `httpOnly`, `sameSite`, `expires`, `priority`).
    
    A etapa de reformatação no exemplo acima é **essencial**. Passar objetos `Cookie` brutos para `set_cookies()` pode causar erros ou comportamento inesperado.

!!! tip "Expiração de Cookies"
    Sempre verifique se os cookies salvos expiraram. Cookies de sessão (`session=True`) expiram quando o navegador fecha, enquanto cookies persistentes têm um timestamp `expires` que você pode validar.

### 2. Teste de Múltiplas Contas com Cookies Isolados

Cada contexto de navegador mantém cookies separados:

```python
import asyncio
from pydoll.browser.chromium import Chrome

async def test_multiple_accounts():
    accounts = [
        {'email': 'user1@example.com', 'cookie_value': 'session_user1'},
        {'email': 'user2@example.com', 'cookie_value': 'session_user2'},
    ]
    
    async with Chrome() as browser:
        initial_tab = await browser.start()
        
        # Primeira conta no contexto padrão
        cookies_user1 = [{
            'name': 'session',
            'value': accounts[0]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await initial_tab.set_cookies(cookies_user1)
        await initial_tab.go_to('https://example.com/dashboard')
        
        # Segunda conta em contexto isolado
        context2 = await browser.create_browser_context()
        tab2 = await browser.new_tab(browser_context_id=context2)
        
        cookies_user2 = [{
            'name': 'session',
            'value': accounts[1]['cookie_value'],
            'domain': 'example.com',
            'secure': True,
            'httpOnly': True
        }]
        await browser.set_cookies(cookies_user2, browser_context_id=context2)
        await tab2.go_to('https://example.com/dashboard')
        
        # Ambos os usuários estão logados simultaneamente com sessões diferentes
        print("Usuário 1 e Usuário 2 logados com cookies isolados")
        
        await asyncio.sleep(5)
        
        # Limpeza
        await tab2.close()
        await browser.delete_browser_context(context2)

asyncio.run(test_multiple_accounts())
```

### 3. Rotação de Cookies para Scripts de Longa Duração

Atualize os cookies periodicamente para evitar detecção:

```python
import asyncio
import time
from pydoll.browser.chromium import Chrome

async def scrape_with_cookie_rotation():
    urls = [f'https://example.com/page{i}' for i in range(100)]
    
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Fazer login inicialmente
        await tab.go_to('https://example.com/login')
        # ... realizar login ...
        await asyncio.sleep(2)
        
        last_rotation = time.time()
        rotation_interval = 600  # Rotacionar a cada 10 minutos
        
        for url in urls:
            # Verificar se é hora de rotacionar os cookies
            if time.time() - last_rotation > rotation_interval:
                print("Rotacionando sessão...")
                
                # Deletar cookies antigos
                await tab.delete_all_cookies()
                
                # Fazer login novamente ou carregar cookies novos
                await tab.go_to('https://example.com/login')
                # ... realizar login novamente ...
                
                last_rotation = time.time()
            
            # Raspar página
            await tab.go_to(url)
            await asyncio.sleep(2)
            # ... extrair dados ...

asyncio.run(scrape_with_cookie_rotation())
```

!!! tip "Frequência de Rotação"
    A frequência ideal de rotação depende do seu caso de uso:
    
    - **Sites de alta segurança**: Rotacione a cada 5-15 minutos
    - **Sites normais**: Rotacione a cada 30-60 minutos
    - **Raspagem de baixo risco**: Rotacione a cada poucas horas


## Referência de Atributos de Cookie

| Atributo | Tipo | Descrição | Padrão |
|---|---|---|---|
| `name` | `str` | Nome do cookie | *Obrigatório* |
| `value` | `str` | Valor do cookie | *Obrigatório* |
| `domain` | `str` | Domínio onde o cookie é válido | Domínio da página atual |
| `path` | `str` | Caminho onde o cookie é válido | `/` |
| `secure` | `bool` | Enviar apenas por HTTPS | `False` |
| `httpOnly` | `bool` | Não acessível via JavaScript | `False` |
| `sameSite` | `CookieSameSite` | Proteção CSRF: `Strict`, `Lax`, `None` | Padrão do navegador (`Lax`) |
| `expires` | `float` | Timestamp Unix (0 = cookie de sessão) | `0` (sessão) |
| `priority` | `CookiePriority` | Prioridade do cookie: `Low`, `Medium`, `High` | `Medium` |

### Valores SameSite

```python
# Use valores string diretamente no seu dict de cookie:

'sameSite': 'Strict'  # Cookie enviado apenas para requisições do mesmo site
'sameSite': 'Lax'     # Cookie enviado para navegação de nível superior (padrão)
'sameSite': 'None'    # Cookie enviado para todas as requisições (requer secure=True)

# Ou use o enum para autocompletar da IDE:
from pydoll.protocol.network.types import CookieSameSite

cookie = {
    'name': 'session',
    'value': 'xyz',
    'sameSite': CookieSameSite.STRICT  # IDE autocompletará: STRICT, LAX, NONE
}
```

### Valores de Priority

```python
# Use valores string diretamente:

'priority': 'Low'     # Baixa prioridade (deletado primeiro quando espaço é necessário)
'priority': 'Medium'  # Média prioridade (padrão)
'priority': 'High'    # Alta prioridade (deletado por último)

# Ou use o enum:
from pydoll.protocol.network.types import CookiePriority

cookie = {
    'name': 'session',
    'value': 'xyz',
    'priority': CookiePriority.HIGH  # IDE autocompletará: LOW, MEDIUM, HIGH
}
```

## Padrões Comuns

### Gerenciador de Contexto para Cookies Temporários

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def temporary_cookies(browser, tab, cookies):
    """Define cookies temporários, executa código, depois restaura os cookies originais."""
    # Salvar cookies atuais
    original_cookies = await browser.get_cookies()
    
    try:
        # Definir cookies temporários
        await tab.delete_all_cookies()
        await tab.set_cookies(cookies)
        yield tab
    finally:
        # Restaurar cookies originais
        await tab.delete_all_cookies()
        cookies_to_restore = [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c['domain'],
                'path': c.get('path', '/')
            }
            for c in original_cookies
        ]
        await tab.set_cookies(cookies_to_restore)

# Uso
async with temporary_cookies(browser, tab, test_cookies):
    await tab.go_to('https://example.com')
    # ... realizar ações com cookies temporários ...
# Cookies originais restaurados automaticamente
```

!!! tip "Usando APIs Públicas"
    Este gerenciador de contexto aceita tanto `browser` quanto `tab` como parâmetros para usar APIs públicas. Como `tab` não expõe seu `browser` pai como uma propriedade pública, passá-lo explicitamente é a abordagem recomendada para acessar métodos de nível de navegador.

### Comparação de Fingerprint de Cookies

```python
def cookie_fingerprint(cookies):
    """Gera um fingerprint simples do estado dos cookies."""
    return {
        'count': len(cookies),
        'domains': set(c['domain'] for c in cookies),
        'names': sorted(c['name'] for c in cookies),
        'secure_count': sum(1 for c in cookies if c.get('secure')),
        'httponly_count': sum(1 for c in cookies if c.get('httpOnly')),
    }

# Comparar estados de cookies
before = await browser.get_cookies()
await tab.go_to('https://example.com')
after = await browser.get_cookies()

print(f"Antes: {cookie_fingerprint(before)}")
print(f"Depois: {cookie_fingerprint(after)}")
```

## Considerações de Segurança

!!! danger "Nunca Codifique Cookies Sensíveis"
    Sempre carregue cookies de autenticação de armazenamento seguro (variáveis de ambiente, arquivos criptografados, gerenciadores de segredos).
    
    ```python
    # Ruim - codificado no código
    cookies = [{'name': 'session', 'value': 'abc123secret'}]
    
    # Bom - carregado do ambiente
    import os
    cookies = [{
        'name': 'session',
        'value': os.getenv('SESSION_COOKIE'),
        'domain': os.getenv('COOKIE_DOMAIN')
    }]
    ```

!!! warning "Proteção Contra Roubo de Cookies"
    Ao salvar cookies em disco:
    
    - Use armazenamento criptografado (ex: biblioteca `cryptography`)
    - Defina permissões restritivas de arquivo
    - Nunca envie arquivos de cookies para o controle de versão
    - Rotacione os cookies regularmente

## Resumo das Melhores Práticas

1.  **Comece com cookies realistas** - Não execute automação com um navegador completamente limpo
2.  **Rotacione sessões periodicamente** - Evite usar os mesmos cookies por longos períodos
3.  **Respeite os atributos de segurança dos cookies** - Use `secure`, `httpOnly`, `sameSite` apropriadamente
4.  **Salve e reutilize cookies de autenticação** - Pule logins repetitivos quando apropriado
5.  **Isole contextos para testes de múltiplas contas** - Cada contexto tem cookies independentes
6.  **Monitore a evolução dos cookies** - A navegação real acumula cookies naturalmente
7.  **Limpe cookies expirados** - Remova cookies inválidos antes de reutilizar
8.  **Use armazenamento seguro** - Criptografe cookies salvos, nunca codifique segredos

## Veja Também

- **[Contextos de Navegador](contexts.md)** - Ambientes de cookies isolados
- **[Requisições HTTP](../network/http-requests.md)** - Requisições no contexto do navegador herdam cookies automaticamente
- **[Interações Semelhantes a Humanas](../automation/human-interactions.md)** - Combine cookies com comportamento realista
- **[Referência da API: Comandos de Armazenamento](/api/commands/storage_commands/)** - Métodos completos de cookies do CDP

O gerenciamento eficaz de cookies é a base para uma automação de navegador realista. Ao equilibrar o frescor com a persistência e respeitar os atributos de segurança, você pode construir uma automação que se comporta como um usuário real, mantendo-se eficiente e sustentável.