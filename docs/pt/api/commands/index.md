# Visão Geral dos Comandos

O módulo de Comandos (Commands) fornece interfaces de alto nível para interagir com os domínios do Chrome DevTools Protocol (CDP). Cada módulo de comando corresponde a um domínio CDP específico e fornece métodos para executar várias operações do navegador.

## Módulos de Comando Disponíveis

### Comandos do Navegador (Browser)
- **Módulo**: `browser_commands.py`
- **Propósito**: Operações em nível de navegador e gerenciamento de janelas
- **Documentação**: [Comandos do Navegador](browser.md)

### Comandos DOM
- **Módulo**: `dom_commands.py`
- **Propósito**: Manipulação da árvore DOM e operações de elementos
- **Documentação**: [Comandos DOM](dom.md)

### Comandos de Entrada (Input)
- **Módulo**: `input_commands.py`
- **Propósito**: Simulação de eventos de entrada (teclado, mouse, toque)
- **Documentação**: [Comandos de Entrada](input.md)

### Comandos de Rede (Network)
- **Módulo**: `network_commands.py`
- **Propósito**: Monitoramento de rede e interceptação de requisições
- **Documentação**: [Comandos de Rede](network.md)

### Comandos de Página (Page)
- **Módulo**: `page_commands.py`
- **Propósito**: Gerenciamento do ciclo de vida da página e navegação
- **Documentação**: [Comandos de Página](page.md)

### Comandos de Tempo de Execução (Runtime)
- **Módulo**: `runtime_commands.py`
- **Propósito**: Execução de JavaScript e gerenciamento de tempo de execução
- **Documentação**: [Comandos de Tempo de Execução](runtime.md)

### Comandos de Armazenamento (Storage)
- **Módulo**: `storage_commands.py`
- **Propósito**: Acesso ao armazenamento do navegador (cookies, local storage, etc.)
- **Documentação**: [Comandos de Armazenamento](storage.md)

### Comandos de Alvo (Target)
- **Módulo**: `target_commands.py`
- **Propósito**: Gerenciamento de alvos (targets) e operações de aba
- **Documentação**: [Comandos de Alvo](target.md)

### Comandos Fetch
- **Módulo**: `fetch_commands.py`
- **Propósito**: Interceptação e modificação de requisições de rede
- **Documentação**: [Comandos Fetch](fetch.md)

## Padrão de Uso

Os comandos são tipicamente acessados através das instâncias do navegador (browser) ou aba (tab):

```python
from pydoll.browser.chromium import Chrome

# Inicializa o navegador
browser = Chrome()
await browser.start()

# Obtém a aba ativa
tab = await browser.get_active_tab()

# Usa comandos através da aba
await tab.navigate("https://example.com")
element = await tab.find(id="button")
await element.click()
```

## Estrutura dos Comandos

Cada módulo de comando segue um padrão consistente:
- **Métodos estáticos**: Para execução direta de comandos
- **Dicas de tipo (Type hints)**: Segurança de tipo (type safety) completa com tipos de protocolo
- **Tratamento de erros**: Tratamento de exceção adequado para erros CDP
- **Documentação**: Docstrings abrangentes com exemplos