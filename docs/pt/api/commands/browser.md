# Comandos do Navegador

Os comandos do navegador fornecem controle de baixo nível sobre as instâncias do navegador e sua configuração.

## Visão Geral

O módulo de comandos do navegador lida com operações em nível de navegador, como informações de versão, gerenciamento de alvos (targets) e configurações globais do navegador.

::: pydoll.commands.browser_commands
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Uso

Os comandos do navegador são tipicamente usados internamente pelas classes do navegador para gerenciar instâncias do navegador:

```python
from pydoll.commands.browser_commands import get_version
from pydoll.connection.connection_handler import ConnectionHandler

# Obter informações da versão do navegador
connection = ConnectionHandler()
version_info = await get_version(connection)
```

## Comandos Disponíveis

O módulo de comandos do navegador fornece funções para:

- Obter informações de versão do navegador e user agent
- Gerenciar alvos (targets) do navegador (abas, janelas)
- Controlar configurações e permissões globais do navegador
- Lidar com eventos do ciclo de vida do navegador

!!! note "Uso Interno"
    Esses comandos são usados principalmente internamente pelas classes de navegador `Chrome` e `Edge`. O uso direto é recomendado apenas para cenários avançados.