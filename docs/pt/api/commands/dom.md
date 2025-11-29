# Comandos DOM

Os comandos DOM fornecem funcionalidade abrangente para interagir com o Document Object Model (Modelo de Objeto de Documento) das páginas web.

## Visão Geral

O módulo de comandos DOM é um dos módulos mais importantes no Pydoll, fornecendo toda a funcionalidade necessária para encontrar, interagir com e manipular elementos HTML em páginas web.

::: pydoll.commands.dom_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos DOM são usados extensivamente pela classe `WebElement` e pelos métodos de localização de elementos:

```python
from pydoll.commands.dom_commands import query_selector, get_attributes
from pydoll.connection.connection_handler import ConnectionHandler

# Encontrar elemento e obter seus atributos
connection = ConnectionHandler()
node_id = await query_selector(connection, selector="#username")
attributes = await get_attributes(connection, node_id=node_id)
```

## Funcionalidades Principais

O módulo de comandos DOM fornece funções para:

### Localização de Elementos
- `query_selector()` - Encontrar elemento único por seletor CSS
- `query_selector_all()` - Encontrar múltiplos elementos por seletor CSS
- `get_document()` - Obter o nó raiz do documento

### Interação com Elementos
- `click_element()` - Clicar em elementos
- `focus_element()` - Focar em elementos
- `set_attribute_value()` - Definir atributos do elemento
- `get_attributes()` - Obter atributos do elemento

### Informações do Elemento
- `get_box_model()` - Obter posicionamento e dimensões do elemento
- `describe_node()` - Obter informações detalhadas do elemento
- `get_outer_html()` - Obter o conteúdo HTML do elemento

### Manipulação do DOM
- `remove_node()` - Remover elementos do DOM
- `set_node_value()` - Definir valores do elemento
- `request_child_nodes()` - Obter elementos filhos

!!! tip "APIs de Alto Nível"
    Embora esses comandos forneçam acesso poderoso de baixo nível, a maioria dos usuários deve usar os métodos de nível superior da classe `WebElement`, como `click()`, `type_text()` e `get_attribute()`, que usam esses comandos internamente.