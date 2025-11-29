# Comandos de Página (Page)

Os comandos de página lidam com a navegação da página, eventos do ciclo de vida e operações em nível de página.

## Visão Geral

O módulo de comandos de página fornece funcionalidade para navegar entre páginas, gerenciar o ciclo de vida da página, lidar com a execução de JavaScript e controlar o comportamento da página.

::: pydoll.commands.page_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de página são usados extensivamente pela classe `Tab` para navegação e gerenciamento da página:

```python
from pydoll.commands.page_commands import navigate, reload, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Navegar para uma URL
connection = ConnectionHandler()
await enable(connection)  # Habilitar eventos da página
await navigate(connection, url="https://example.com")

# Recarregar a página
await reload(connection)
```

## Funcionalidades Principais

O módulo de comandos de página fornece funções para:

### Navegação
- `Maps()` - Navegar para URLs
- `reload()` - Recarregar página atual
- `go_back()` - Navegar para trás no histórico
- `go_forward()` - Navegar para frente no histórico
- `stop_loading()` - Parar carregamento da página

### Ciclo de Vida da Página
- `enable()` / `disable()` - Habilitar/desabilitar eventos da página
- `get_frame_tree()` - Obter estrutura de frames da página
- `get_navigation_history()` - Obter histórico de navegação

### Gerenciamento de Conteúdo
- `get_resource_content()` - Obter conteúdo de recurso da página
- `search_in_resource()` - Pesquisar dentro de recursos da página
- `set_document_content()` - Definir conteúdo HTML da página

### Capturas de Tela & PDF
- `capture_screenshot()` - Tirar capturas de tela da página
- `print_to_pdf()` - Gerar PDF a partir da página
- `capture_snapshot()` - Capturar snapshots da página

### Execução de JavaScript
- `add_script_to_evaluate_on_new_document()` - Adicionar scripts para avaliar em novo documento (scripts de inicialização)
- `remove_script_to_evaluate_on_new_document()` - Remover scripts de inicialização

### Configurações da Página
- `set_lifecycle_events_enabled()` - Controlar eventos do ciclo de vida
- `set_ad_blocking_enabled()` - Habilitar/desabilitar bloqueio de anúncios
- `set_bypass_csp()` - Contornar (Bypass) Política de Segurança de Conteúdo (CSP)

## Recursos Avançados

### Gerenciamento de Frames
```python
# Obter todos os frames na página
frame_tree = await get_frame_tree(connection)
for frame in frame_tree.child_frames:
    print(f"Frame: {frame.frame.url}")
```

### Interceptação de Recursos
```python
# Obter conteúdo do recurso
content = await get_resource_content(
    connection, 
    frame_id=frame_id, 
    url="https://example.com/script.js"
)
```

### Eventos da Página
Os comandos de página funcionam com vários eventos de página:
- `Page.loadEventFired` - Carregamento da página concluído
- `Page.domContentEventFired` - Conteúdo DOM carregado
- `Page.frameNavigated` - Navegação do frame
- `Page.frameStartedLoading` - Carregamento do frame iniciado

!!! tip "Integração com a Classe Tab"
    A maioria das operações de página está disponível através dos métodos da classe `Tab`, como `tab.go_to()`, `tab.reload()` e `tab.screenshot()`, que fornecem uma API mais conveniente.