# Comandos de Tempo de Execução (Runtime)

Os comandos de tempo de execução fornecem capacidades de execução de JavaScript e gerenciamento do ambiente de tempo de execução.

## Visão Geral

O módulo de comandos de tempo de execução habilita a execução de código JavaScript, inspeção de objetos e controle do ambiente de tempo de execução dentro dos contextos do navegador.

::: pydoll.commands.runtime_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos de tempo de execução são usados para execução de JavaScript e gerenciamento do tempo de execução:

```python
from pydoll.commands.runtime_commands import evaluate, enable
from pydoll.connection.connection_handler import ConnectionHandler

# Habilitar eventos de tempo de execução
connection = ConnectionHandler()
await enable(connection)

# Executar JavaScript
result = await evaluate(
    connection, 
    expression="document.title",
    return_by_value=True
)
print(result.value)  # Título da página
```

## Funcionalidades Principais

O módulo de comandos de tempo de execução fornece funções para:

### Execução de JavaScript
- `evaluate()` - Executar expressões JavaScript
- `call_function_on()` - Chamar funções em objetos
- `compile_script()` - Compilar JavaScript para reutilização
- `run_script()` - Executar scripts compilados

### Gerenciamento de Objetos
- `get_properties()` - Obter propriedades do objeto
- `release_object()` - Liberar referências de objeto
- `release_object_group()` - Liberar grupos de objetos

### Controle de Tempo de Execução
- `enable()` / `disable()` - Habilitar/desabilitar eventos de tempo de execução
- `discard_console_entries()` - Limpar entradas do console
- `set_custom_object_formatter_enabled()` - Habilitar formatadores customizados

### Manipulação de Exceções
- `set_async_call_stack_depth()` - Definir profundidade da pilha de chamadas assíncronas
- Captura e relatório de exceções
- Inspeção de objeto de erro

## Uso Avançado

### Execução de JavaScript Complexo
```python
# Executar JavaScript complexo com tratamento de erros
script = """
try {
    const elements = document.querySelectorAll('.item');
    return Array.from(elements).map(el => ({
        text: el.textContent,
        href: el.href
    }));
} catch (error) {
    return { error: error.message };
}
"""

result = await evaluate(
    connection,
    expression=script,
    return_by_value=True,
    await_promise=True
)
```

### Inspeção de Objeto
```python
# Obter propriedades detalhadas do objeto
properties = await get_properties(
    connection,
    object_id=object_id,
    own_properties=True,
    accessor_properties_only=False
)

for prop in properties:
    print(f"{prop.name}: {prop.value}")
```

### Integração com Console
Os comandos de tempo de execução se integram ao console do navegador:
- Mensagens e erros do console
- Chamadas de método da API Console
- Formatadores de console customizados

!!! note "Considerações de Performance"
    A execução de JavaScript através dos comandos de tempo de execução pode ser mais lenta do que a execução nativa do navegador. Use com moderação para operações complexas.