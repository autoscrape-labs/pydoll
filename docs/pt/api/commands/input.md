# Comandos de Entrada (Input)

Os comandos de entrada lidam com interações de mouse e teclado, fornecendo simulação de entrada semelhante à humana.

## Visão Geral

O módulo de comandos de entrada fornece funcionalidade para simular a entrada do usuário, incluindo movimentos do mouse, cliques, digitação no teclado e pressionamento de teclas.

::: pydoll.commands.input_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de entrada são usados por métodos de interação de elementos e podem ser usados diretamente para cenários de entrada avançados:

```python
from pydoll.commands.input_commands import dispatch_mouse_event, dispatch_key_event
from pydoll.connection.connection_handler import ConnectionHandler

# Simular clique do mouse
connection = ConnectionHandler()
await dispatch_mouse_event(
    connection, 
    type="mousePressed", 
    x=100, 
    y=200, 
    button="left"
)

# Simular digitação do teclado
await dispatch_key_event(
    connection,
    type="keyDown",
    key="Enter"
)
```

## Funcionalidades Principais

O módulo de comandos de entrada fornece funções para:

### Eventos de Mouse
- `dispatch_mouse_event()` - Cliques, movimentos e eventos de roda do mouse
- Estados dos botões do mouse (esquerdo, direito, meio)
- Posicionamento baseado em coordenadas
- Operações de arrastar e soltar (drag and drop)

### Eventos de Teclado
- `dispatch_key_event()` - Eventos de pressionar e soltar tecla
- `insert_text()` - Inserção direta de texto
- Manipulação de teclas especiais (Enter, Tab, teclas de seta, etc.)
- Teclas modificadoras (Ctrl, Alt, Shift)

### Eventos de Toque (Touch)
- Simulação de tela de toque
- Gestos multitoque (multi-touch)
- Coordenadas e pressão do toque

## Comportamento Semelhante ao Humano

Os comandos de entrada suportam padrões de comportamento semelhantes ao humano:

- Curvas naturais de movimento do mouse
- Velocidades e padrões de digitação realistas
- Micro-atrasos aleatórios entre ações
- Eventos de toque sensíveis à pressão

!!! tip "Métodos de Elemento"
    Para a maioria dos casos de uso, utilize os métodos de elemento de nível superior, como `element.click()` e `element.type_text()`, que fornecem uma API mais conveniente e lidam com cenários comuns automaticamente.