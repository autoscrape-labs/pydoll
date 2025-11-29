# Comandos de Alvo (Target)

Os comandos de alvo (Target) gerenciam os alvos do navegador, incluindo abas, janelas e outros contextos de navegação.

## Visão Geral

O módulo de comandos de alvo fornece funcionalidade para criar, gerenciar e controlar os alvos do navegador, como abas, janelas pop-up e service workers.

::: pydoll.commands.target_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de alvo são usados internamente pelas classes do navegador para gerenciar abas e janelas:

```python
from pydoll.commands.target_commands import get_targets, create_target, close_target
from pydoll.connection.connection_handler import ConnectionHandler

# Obter todos os alvos do navegador
connection = ConnectionHandler()
targets = await get_targets(connection)

# Criar uma nova aba
new_target = await create_target(connection, url="https://example.com")

# Fechar um alvo
await close_target(connection, target_id=new_target.target_id)
```

## Funcionalidades Principais

O módulo de comandos de alvo fornece funções para:

### Gerenciamento de Alvo
- `get_targets()` - Listar todos os alvos do navegador
- `create_target()` - Criar novas abas ou janelas
- `close_target()` - Fechar alvos específicos
- `activate_target()` - Trazer alvo para o primeiro plano

### Informações do Alvo
- `get_target_info()` - Obter informações detalhadas do alvo
- Tipos de alvo: page, background_page, service_worker, browser
- Estados do alvo: attached, detached, crashed

### Gerenciamento de Sessão
- `attach_to_target()` - Anexar a um alvo para controle
- `detach_from_target()` - Desanexar de um alvo
- `send_message_to_target()` - Enviar comandos para alvos

### Contexto do Navegador
- `create_browser_context()` - Criar contexto de navegador isolado
- `dispose_browser_context()` - Remover contexto de navegador
- `get_browser_contexts()` - Listar contextos de navegador

## Tipos de Alvos

Diferentes tipos de alvos podem ser gerenciados:

### Alvos de Página
```python
# Criar uma nova aba
page_target = await create_target(
    connection,
    url="https://example.com",
    width=1920,
    height=1080,
    browser_context_id=None  # Contexto padrão
)
```

### Janelas Pop-up
```python
# Criar uma janela pop-up
popup_target = await create_target(
    connection,
    url="https://popup.example.com",
    width=800,
    height=600,
    new_window=True
)
```

### Contextos Anônimos (Incognito)
```python
# Criar contexto de navegador anônimo
incognito_context = await create_browser_context(connection)

# Criar aba no contexto anônimo
incognito_tab = await create_target(
    connection,
    url="https://private.example.com",
    browser_context_id=incognito_context.browser_context_id
)
```

!!! info "Headless vs Headed: como os contextos se manifestam"
    Contextos de navegador são ambientes lógicos isolados. No modo **headed** (com interface gráfica), a primeira página criada dentro de um novo contexto geralmente abrirá em uma nova janela do SO. No modo **headless** (sem interface gráfica), nenhuma janela é mostrada — o isolamento permanece puramente lógico (cookies, armazenamento, cache e estado de autenticação ainda são separados por contexto). Prefira contextos em pipelines headless/CI para performance e isolamento limpo.

## Recursos Avançados

### Eventos de Alvo
Os comandos de alvo funcionam com vários eventos de alvo:
- `Target.targetCreated` - Novo alvo criado
- `Target.targetDestroyed` - Alvo fechado
- `Target.targetInfoChanged` - Informações do alvo atualizadas
- `Target.targetCrashed` - Alvo falhou (crashed)

### Coordenação Multi-Alvo
```python
# Gerenciar múltiplas abas
targets = await get_targets(connection)
page_targets = [t for t in targets if t.type == "page"]

for target in page_targets:
    # Realizar operações em cada aba
    await activate_target(connection, target_id=target.target_id)
    # ... fazer o trabalho nesta aba
```

### Isolamento de Alvo
```python
# Criar contexto de navegador isolado para testes
test_context = await create_browser_context(connection)

# Todos os alvos neste contexto estão isolados
test_tab1 = await create_target(
    connection, 
    url="https://test1.com",
    browser_context_id=test_context.browser_context_id
)

test_tab2 = await create_target(
    connection,
    url="https://test2.com", 
    browser_context_id=test_context.browser_context_id
)
```

!!! note "Integração com o Navegador"
    Os comandos de alvo são usados principalmente internamente pelas classes de navegador `Chrome` e `Edge`. As APIs de navegador de alto nível fornecem métodos mais convenientes para o gerenciamento de abas.