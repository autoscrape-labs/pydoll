# Gerenciadores do Navegador

O módulo de gerenciadores (managers) fornece classes especializadas para gerenciar diferentes aspectos do ciclo de vida e configuração do navegador.

## Visão Geral

Os gerenciadores do navegador lidam com responsabilidades específicas na automação do navegador:

::: pydoll.browser.managers
    options:
      show_root_heading: true
      show_source: false
      heading_level: 2
      filters:
        - "!^_"
        - "!^__"

## Classes de Gerenciadores

### Gerenciador de Processo do Navegador
Gerencia o ciclo de vida do processo do navegador, incluindo iniciar, parar e monitorar os processos do navegador.

::: pydoll.browser.managers.browser_process_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Gerenciador de Opções do Navegador
Lida com as opções de configuração do navegador e argumentos de linha de comando.

::: pydoll.browser.managers.browser_options_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Gerenciador de Proxy
Gerencia a configuração de proxy e autenticação para instâncias do navegador.

::: pydoll.browser.managers.proxy_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

### Gerenciador de Diretório Temporário
Lida com a criação e limpeza de diretórios temporários usados pelas instâncias do navegador.

::: pydoll.browser.managers.temp_dir_manager
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3

## Uso

Os gerenciadores são normalmente usados internamente pelas classes do navegador, como `Chrome` e `Edge`. Eles fornecem funcionalidade modular que pode ser composta:

```python
from pydoll.browser.managers.proxy_manager import ProxyManager
from pydoll.browser.managers.temp_dir_manager import TempDirManager

# Gerenciadores são usados internamente pelas classes do navegador
# O uso direto é apenas para cenários avançados
proxy_manager = ProxyManager()
temp_manager = TempDirManager()
```

!!! note "Uso Interno"
    Esses gerenciadores são usados principalmente internamente pelas classes do navegador. O uso direto é recomendado apenas para cenários avançados ou ao estender a biblioteca.
