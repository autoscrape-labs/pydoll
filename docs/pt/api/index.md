# Referência da API

Bem-vindo à Referência da API do Pydoll! Esta seção fornece documentação abrangente para todas as classes, métodos e funções disponíveis na biblioteca Pydoll.

---

## Visão Geral

O Pydoll está organizado em vários módulos chave, cada um servindo a um propósito específico na automação do navegador:

### Módulo Browser (Navegador)
O módulo `browser` contém classes para gerenciar instâncias de navegador e seu ciclo de vida.

* **[Chrome](browser/chrome.md)** - Automação do navegador Chrome
* **[Edge](browser/edge.md)** - Automação do navegador Microsoft Edge
* **[Options](browser/options.md)** - Opções de configuração do navegador
* **[Tab](browser/tab.md)** - Gerenciamento e interação de abas
* **[Requests](browser/requests.md)** - Requisições HTTP dentro do contexto do navegador
* **[Managers](browser/managers.md)** - Gerenciadores do ciclo de vida do navegador

### Módulo Elements (Elementos)
O módulo `elements` fornece classes para interagir com elementos de página web.

* **[WebElement](elements/web_element.md)** - Interação com elemento individual
* **[Mixins](elements/mixins.md)** - Funcionalidade de elemento reutilizável

### Módulo Connection (Conexão)
O módulo `connection` lida com a comunicação com o navegador através do Chrome DevTools Protocol.

* **[Connection Handler](connection/connection.md)** - Gerenciamento de conexão WebSocket
* **[Managers](connection/managers.md)** - Gerenciadores do ciclo de vida da conexão

### Módulo Commands (Comandos)
O módulo `commands` fornece implementações de comando de baixo nível do Chrome DevTools Protocol.

* **[Visão Geral dos Comandos](commands/index.md)** - Implementações de comando CDP por domínio

### Módulo Protocol (Protocolo)
O módulo `protocol` implementa os comandos e eventos do Chrome DevTools Protocol.

* **[Tipos Base](protocol/base.md)** - Tipos base para o Chrome DevTools Protocol
* **[Browser](protocol/browser.md)** - Comandos e eventos do domínio Browser
* **[DOM](protocol/dom.md)** - Comandos e eventos do domínio DOM
* **[Fetch](protocol/fetch.md)** - Comandos e eventos do domínio Fetch
* **[Input](protocol/input.md)** - Comandos e eventos do domínio Input
* **[Network](protocol/network.md)** - Comandos e eventos do domínio Network
* **[Page](protocol/page.md)** - Comandos e eventos do domínio Page
* **[Runtime](protocol/runtime.md)** - Comandos e eventos do domínio Runtime
* **[Storage](protocol/storage.md)** - Comandos e eventos do domínio Storage
* **[Target](protocol/target.md)** - Comandos e eventos do domínio Target

### Módulo Core (Núcleo)
O módulo `core` contém utilitários fundamentais, constantes e exceções.

* **[Constants](core/constants.md)** - Constantes e enums da biblioteca
* **[Exceptions](core/exceptions.md)** - Classes de exceção customizadas
* **[Utils](core/utils.md)** - Funções de utilidade

---

## Navegação Rápida

### Classes Mais Comuns

| Classe | Propósito | Módulo |
|-------|---------|--------|
| `Chrome` | Automação do navegador Chrome | `pydoll.browser.chromium` |
| `Edge` | Automação do navegador Edge | `pydoll.browser.chromium` |
| `Tab` | Interação e controle de abas | `pydoll.browser.tab` |
| `WebElement` | Interação com elementos | `pydoll.elements.web_element` |
| `ChromiumOptions` | Configuração do navegador | `pydoll.browser.options` |

### Enums e Constantes Chave

| Nome | Propósito | Módulo |
|------|---------|--------|
| `By` | Estratégias de seletor de elemento | `pydoll.constants` |
| `Key` | Constantes de tecla do teclado | `pydoll.constants` |
| `PermissionType` | Tipos de permissão do navegador | `pydoll.constants` |

### Exceções Comuns

| Exceção | Quando Levantada | Módulo |
|-----------|-------------|--------|
| `ElementNotFound` | Elemento não encontrado no DOM | `pydoll.exceptions` |
| `WaitElementTimeout` | Timeout de espera de elemento | `pydoll.exceptions` |
| `BrowserNotStarted` | Navegador não iniciado | `pydoll.exceptions` |

---

## Padrões de Uso

### Automação Básica do Navegador

```python
from pydoll.browser.chromium import Chrome

async with Chrome() as browser:
    tab = await browser.start()
    await tab.go_to("https://example.com")
    element = await tab.find(id="my-element")
    await element.click()
```

### Localização de Elementos

```python
# Usando o método moderno find()
element = await tab.find(id="username")
element = await tab.find(tag_name="button", class_name="submit")

# Usando seletores CSS ou XPath
element = await tab.query("#username")
element = await tab.query("//button[@class='submit']")
```

### Manipulação de Eventos

```python
await tab.enable_page_events()
await tab.on('Page.loadEventFired', handle_page_load)
```

---

## Suporte a Tipagem e Assincronismo

### Dicas de Tipo (Type Hints)
O Pydoll é totalmente tipado e fornece **dicas de tipo** abrangentes para melhor suporte da IDE e segurança de código. Todas as APIs públicas incluem anotações de tipo adequadas.

```python
from typing import Optional, List
from pydoll.elements.web_element import WebElement

# Métodos retornam objetos tipados corretamente
element: Optional[WebElement] = await tab.find(id="test", raise_exc=False)
elements: List[WebElement] = await tab.find(class_name="item", find_all=True)
```

### Suporte Async/Await
Todas as operações do Pydoll são **assíncronas** e devem ser usadas com **`async`**/**`await`**:

```python
import asyncio

async def main():
    # Todas as operações do Pydoll são assíncronas
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to("https://example.com")
        
asyncio.run(main())
```

Navegue pelas seções abaixo para explorar a documentação completa da API para cada módulo.