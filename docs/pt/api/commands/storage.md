# Comandos de Armazenamento (Storage)

Os comandos de armazenamento fornecem gerenciamento abrangente do armazenamento do navegador, incluindo cookies, localStorage, sessionStorage e IndexedDB.

## Visão Geral

O módulo de comandos de armazenamento permite o gerenciamento de todos os mecanismos de armazenamento do navegador, fornecendo funcionalidade para persistência e recuperação de dados.

::: pydoll.commands.storage_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de armazenamento são usados para gerenciar o armazenamento do navegador em diferentes mecanismos:

```python
from pydoll.commands.storage_commands import get_cookies, set_cookies, clear_data_for_origin
from pydoll.connection.connection_handler import ConnectionHandler

# Obter cookies para um domínio
connection = ConnectionHandler()
cookies = await get_cookies(connection, urls=["https://example.com"])

# Definir um novo cookie
await set_cookies(connection, cookies=[{
    "name": "session_id",
    "value": "abc123",
    "domain": "example.com",
    "path": "/",
    "httpOnly": True,
    "secure": True
}])

# Limpar todo o armazenamento para uma origem
await clear_data_for_origin(
    connection,
    origin="https://example.com",
    storage_types="all"
)
```

## Funcionalidades Principais

O módulo de comandos de armazenamento fornece funções para:

### Gerenciamento de Cookies
- `get_cookies()` - Obter cookies por URL ou domínio
- `set_cookies()` - Definir novos cookies
- `delete_cookies()` - Deletar cookies específicos
- `clear_cookies()` - Limpar todos os cookies

### Local Storage
- `get_dom_storage_items()` - Obter itens do localStorage
- `set_dom_storage_item()` - Definir item do localStorage
- `remove_dom_storage_item()` - Remover item do localStorage
- `clear_dom_storage()` - Limpar localStorage

### Session Storage
- Operações de session storage (semelhantes ao localStorage)
- Gerenciamento de dados específicos da sessão
- Armazenamento isolado por aba

### IndexedDB
- `get_database_names()` - Obter bancos de dados IndexedDB
- `request_database()` - Acessar a estrutura do banco de dados
- `request_data()` - Consultar dados do banco de dados
- `clear_object_store()` - Limpar object stores

### Cache Storage
- `request_cache_names()` - Obter nomes de cache
- `request_cached_response()` - Obter respostas em cache
- `delete_cache()` - Deletar entradas de cache

### Application Cache (Obsoleto)
- Suporte a cache de aplicação legado
- Cache baseado em manifesto

## Recursos Avançados

### Operações em Massa
```python
# Limpar todos os tipos de armazenamento para múltiplas origens
origins = ["https://example.com", "https://api.example.com"]
for origin in origins:
    await clear_data_for_origin(
        connection,
        origin=origin,
        storage_types="cookies,local_storage,session_storage,indexeddb"
    )
```

### Cotas de Armazenamento
```python
# Obter informações de uso e cota de armazenamento
quota_info = await get_usage_and_quota(connection, origin="https://example.com")
print(f"Usado: {quota_info.usage} bytes")
print(f"Cota: {quota_info.quota} bytes")
```

### Armazenamento Cross-Origin
```python
# Gerenciar armazenamento entre diferentes origens
await set_cookies(connection, cookies=[{
    "name": "cross_site_token",
    "value": "token123",
    "domain": ".example.com",  # Aplica-se a todos os subdomínios
    "sameSite": "None",
    "secure": True
}])
```

## Tipos de Armazenamento

O módulo suporta vários mecanismos de armazenamento:

| Tipo de Armazenamento | Persistência | Escopo | Capacidade |
|--------------|-------------|-------|----------|
| Cookies | Persistente | Domínio/Caminho | ~4KB por cookie |
| localStorage | Persistente | Origem | ~5-10MB |
| sessionStorage | Sessão | Aba | ~5-10MB |
| IndexedDB | Persistente | Origem | Grande (GB+) |
| Cache API | Persistente | Origem | Grande |

!!! warning "Considerações de Privacidade"
    Operações de armazenamento podem afetar a privacidade do usuário. Sempre lide com dados de armazenamento de forma responsável e em conformidade com as regulamentações de privacidade.