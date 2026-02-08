# Arquitetura do Shadow DOM

O Shadow DOM e um dos aspectos mais desafiadores da automacao web moderna. Elementos dentro de shadow trees sao invisiveis para consultas DOM regulares, o que quebra abordagens tradicionais de automacao. Este documento explica como o Shadow DOM funciona no nivel do navegador, por que ferramentas convencionais falham com shadow roots fechados, e como o Pydoll contorna essas restricoes atraves de acesso direto via CDP.

!!! info "Guia de Uso Pratico"
    Para exemplos de uso e padroes de inicio rapido, consulte o [Guia de Pesquisa de Elementos — secao Shadow DOM](../../features/element-finding.md#suporte-a-shadow-dom).

## O que e Shadow DOM?

Shadow DOM e um padrao web que permite **encapsulamento DOM**. Ele permite que um componente tenha sua propria arvore DOM isolada (a "shadow tree") anexada a um elemento DOM regular (o "shadow host"). Elementos dentro de uma shadow tree ficam ocultos das consultas do documento principal.

```mermaid
graph TB
    subgraph "DOM Principal (Light DOM)"
        Document["document"]
        Host["div#my-component\n(shadow host)"]
        Other["p.normal-content"]
    end

    subgraph "Shadow Tree (Encapsulada)"
        SR["#shadow-root (open)"]
        Style["style"]
        Button["button.internal"]
        Input["input.private"]
    end

    Document --> Host
    Document --> Other
    Host -.->|"attachShadow()"| SR
    SR --> Style
    SR --> Button
    SR --> Input
```

### Modos do Shadow Root

Quando um componente cria um shadow root via `attachShadow()`, ele especifica um **modo**:

| Modo | Acesso JavaScript | Acesso CDP | Uso Comum |
|------|-------------------|------------|-----------|
| `open` | `element.shadowRoot` retorna o root | Acesso total via `backendNodeId` | Web components customizados (Lit, Stencil) |
| `closed` | `element.shadowRoot` retorna `null` | Acesso total via `backendNodeId` | Componentes sensiveis, formularios de pagamento |
| `user-agent` | Nao acessivel via JS | Acesso limitado | UI interna do navegador (placeholders, controles de video) |

Essa distincao e critica: **o acesso no nivel JavaScript e restrito pelo modo, mas o acesso no nivel CDP nao e.**

### Por que a Automacao Tradicional Falha

Ferramentas de automacao tradicionais dependem da execucao de JavaScript no contexto da pagina:

```javascript
// Abordagem WebDriver / Selenium
document.querySelector('#my-component')        // ✓ Encontra o host
document.querySelector('#my-component button') // ✗ Nao cruza a fronteira do shadow
element.shadowRoot                             // ✗ Retorna null para roots fechados
```

A fronteira do shadow e imposta pelo motor JavaScript do navegador. Qualquer ferramenta de automacao que executa JavaScript para encontrar elementos vai encontrar essa barreira. Isso inclui Selenium, `page.evaluate()` do Playwright, e qualquer ferramenta usando `Runtime.evaluate()` com `document.querySelector()` no nivel do documento.

## Como o Pydoll Contorna as Fronteiras do Shadow

A abordagem do Pydoll funciona em uma camada **abaixo do JavaScript**: o Chrome DevTools Protocol. O CDP tem acesso direto a representacao interna do DOM do navegador, que ignora restricoes de modo do shadow completamente.

### A Vantagem do CDP

```mermaid
sequenceDiagram
    participant User as Codigo do Usuario
    participant SR as ShadowRoot
    participant CH as ConnectionHandler
    participant CDP as Chrome CDP
    participant DOM as DOM do Navegador

    User->>SR: shadow_root.query('.btn')
    SR->>SR: _get_find_element_command(object_id)
    SR->>CH: execute_command(Runtime.callFunctionOn)
    CH->>CDP: WebSocket send
    CDP->>DOM: Executa querySelector no objeto shadow root
    DOM-->>CDP: Resultado do elemento
    CDP-->>CH: Resposta com objectId
    CH-->>SR: Dados do elemento
    SR-->>User: Instancia WebElement
```

O insight chave esta em **como o objeto shadow root e obtido** e **como as consultas sao executadas contra ele**:

1. **Descoberta**: `DOM.describeNode` com `pierce=true` retorna nos de shadow root com seu `backendNodeId`, independente do modo
2. **Resolucao**: `DOM.resolveNode` converte um `backendNodeId` em um `objectId` JavaScript que referencia o shadow root diretamente
3. **Consulta**: `Runtime.callFunctionOn` executa `this.querySelector()` no `objectId` do shadow root; isso funciona porque a chamada e feita **no proprio objeto shadow root**, nao a partir do contexto do documento

### Passo a Passo: Acesso ao Shadow Root

```mermaid
flowchart TD
    A["WebElement\n(shadow host)"]
    B["shadowRoots[] com\nbackendNodeId"]
    C["objectId JavaScript\npara o shadow root"]
    D["Instancia ShadowRoot"]
    E["WebElement\n(dentro do shadow)"]

    A -->|"DOM.describeNode\ndepth=1, pierce=true"| B
    B -->|"DOM.resolveNode\nbackendNodeId"| C
    C -->|"Criar ShadowRoot\ncom objectId"| D
    D -->|"find() / query()\nvia callFunctionOn"| E
```

#### Passo 1: Descrever o No Host

```python
# Pydoll envia este comando CDP:
{
    "method": "DOM.describeNode",
    "params": {
        "objectId": "<host-element-object-id>",
        "depth": 1,
        "pierce": true  # ← Esta e a flag chave
    }
}
```

O parametro `pierce` diz ao CDP para atravessar fronteiras do shadow ao descrever o no. A resposta inclui informacoes do shadow root independente do modo do shadow root:

```json
{
    "result": {
        "node": {
            "nodeName": "DIV",
            "shadowRoots": [
                {
                    "nodeId": 0,
                    "backendNodeId": 5,
                    "shadowRootType": "closed",
                    "childNodeCount": 4
                }
            ]
        }
    }
}
```

!!! warning "nodeId vs backendNodeId"
    Quando o dominio DOM nao esta explicitamente habilitado (que e o padrao do Pydoll para minimizar overhead), `nodeId` e sempre `0`. O `backendNodeId` e o identificador estavel e sempre disponivel. O Pydoll usa `backendNodeId` exclusivamente para resolucao de shadow root, e por isso funciona sem necessitar de `DOM.enable()`.

#### Passo 2: Resolver para Objeto JavaScript

```python
# Converter backendNodeId em um objectId utilizavel:
{
    "method": "DOM.resolveNode",
    "params": {
        "backendNodeId": 5
    }
}
```

A resposta fornece um `objectId`, um handle para o shadow root no espaco de objetos do JavaScript:

```json
{
    "result": {
        "object": {
            "objectId": "-2296764575741119861.1.3"
        }
    }
}
```

#### Passo 3: Consultar Dentro do Shadow Root

Com o `objectId` do shadow root, o Pydoll aproveita o mecanismo de busca relativa existente do `FindElementsMixin`:

```python
# Quando ShadowRoot.query('.btn') e chamado:
{
    "method": "Runtime.callFunctionOn",
    "params": {
        "functionDeclaration": "function() { return this.querySelector(\".btn\"); }",
        "objectId": "-2296764575741119861.1.3"
    }
}
```

A funcao executa com `this` vinculado ao objeto shadow root. Como shadow roots implementam as interfaces `querySelector()` e `querySelectorAll()` nativamente, seletores CSS funcionam naturalmente dentro da fronteira do shadow.

## Arquitetura do ShadowRoot

### Decisao de Design: Reutilizar FindElementsMixin

A decisao arquitetural mais critica foi fazer `ShadowRoot` herdar de `FindElementsMixin`:

```python
class ShadowRoot(FindElementsMixin):
    def __init__(self, object_id, connection_handler, mode, host_element):
        self._object_id = object_id               # Referencia CDP do shadow root
        self._connection_handler = connection_handler  # Para comunicacao CDP
        self._mode = mode                          # Enum ShadowRootType
        self._host_element = host_element          # Referencia de volta ao host
```

**Por que isso funciona**: `FindElementsMixin._find_element()` verifica `hasattr(self, '_object_id')`. Quando presente, usa `RELATIVE_QUERY_SELECTOR`, que chama `this.querySelector()` no objeto referenciado. Como shadow roots suportam `querySelector()` nativamente, `query()` com seletores CSS funciona automaticamente. A flag `_css_only = True` no `ShadowRoot` bloqueia `find()` e `query()` com XPath, lancando `NotImplementedError`.

```python
# Esta unica linha no FindElementsMixin habilita buscas em shadow root:
elif hasattr(self, '_object_id'):
    command = self._get_find_element_command(by, value, self._object_id)
```

Isso significa que `ShadowRoot` herda `query()` e `find_or_wait_element()` do mixin. Porem, a flag `_css_only = True` restringe o uso a apenas `query()` com seletores CSS; `find()` e XPath lancam `NotImplementedError`.

!!! tip "Consistencia Arquitetural"
    Este e o mesmo mecanismo que faz `WebElement.find()` buscar dentro dos filhos de um elemento: o atributo `_object_id` sinaliza "busque relativo a mim" em vez de "busque no documento inteiro." `ShadowRoot`, `WebElement` e `Tab` compartilham comportamento identico de busca de elementos atraves do `FindElementsMixin`.

### Relacionamento entre Classes

| Classe | Tem `_object_id` | Tem `_connection_handler` | Escopo de Busca |
|--------|:-:|:-:|---|
| `Tab` | Nao | Sim | Documento inteiro |
| `WebElement` | Sim | Sim | Dentro da subarvore do elemento |
| `ShadowRoot` | Sim | Sim | Dentro da shadow tree |

Todos os tres herdam de `FindElementsMixin`. A presenca ou ausencia de `_object_id` determina se as buscas sao globais no documento ou com escopo para um no especifico.

### Resolvendo Shadow Roots: Estrategia backendNodeId

O Pydoll deliberadamente usa `backendNodeId` em vez de `nodeId` para resolucao de shadow root:

| Propriedade | `nodeId` | `backendNodeId` |
|-------------|----------|-----------------|
| Requer `DOM.enable()` | Sim | Nao |
| Estavel entre chamadas describe | Nao (0 quando DOM nao habilitado) | Sim |
| Funciona para resolucao de shadow root | Apenas com DOM habilitado | Sempre |
| Overhead de performance | Maior (rastreamento do dominio DOM) | Nenhum |

Ao confiar no `backendNodeId`, o Pydoll evita o overhead de habilitar o dominio DOM enquanto mantem acesso confiavel ao shadow root. Esta e uma escolha pragmatica: a maioria dos cenarios de automacao nao precisa do stream de eventos do dominio DOM, e habilita-lo adiciona overhead de memoria e processamento para rastrear cada mutacao do DOM.

## Shadow Roots Fechados: Por que o Acesso CDP Funciona

Esta e a pergunta mais frequente: **se `element.shadowRoot` retorna `null` para shadow roots fechados em JavaScript, como o CDP pode acessa-los?**

A resposta esta em entender a arquitetura do navegador:

```mermaid
graph TB
    subgraph "Runtime JavaScript"
        JS["Codigo JavaScript"]
        API["Web APIs\n(propriedade shadowRoot)"]
    end

    subgraph "Internos do Navegador"
        CDP_Layer["Camada CDP"]
        DOM_Internal["Arvore DOM Interna"]
    end

    JS -->|"element.shadowRoot"| API
    API -->|"mode == 'closed'\n→ retorna null"| JS
    CDP_Layer -->|"DOM.describeNode\npierce=true"| DOM_Internal
    DOM_Internal -->|"Sempre retorna\nshadow tree completa"| CDP_Layer
```

**Acesso JavaScript** passa pela camada de Web API, que impoe a restricao de modo do shadow. Quando `mode='closed'`, a API retorna `null`; esta e uma fronteira de controle de acesso intencional para codigo de paginas web.

**Acesso CDP** opera abaixo da camada de Web API. Ele se comunica diretamente com a representacao interna do DOM do navegador. A restricao do modo `closed` e uma **politica no nivel JavaScript**, nao uma **restricao no nivel DOM**. A shadow tree ainda existe no DOM; ela apenas esta oculta da visao do JavaScript.

!!! info "Implicacoes de Seguranca"
    Isso e por design no DevTools Protocol. O CDP e destinado a ferramentas de depuracao e automacao que precisam de acesso total ao DOM. O modo `closed` protege conteudos do shadow de outros scripts na mesma pagina (ex: scripts de terceiros), nao da interface de depuracao do navegador. Esta e a mesma razao pela qual o DevTools do navegador consegue inspecionar shadow roots fechados no painel Elements.

### Verificacao Pratica

Voce pode verificar esse comportamento:

```python
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.protocol.dom.types import ShadowRootType

async def verify_closed_access():
    async with Chrome() as browser:
        tab = await browser.start()
        await tab.go_to('about:blank')

        # Criar um shadow root fechado via JavaScript
        await tab.execute_script("""
            const host = document.createElement('div');
            host.id = 'test-host';
            document.body.appendChild(host);
            const shadow = host.attachShadow({ mode: 'closed' });
            shadow.innerHTML = '<p class="secret">Conteudo oculto</p>';
        """)

        # JavaScript nao consegue acessar:
        result = await tab.execute_script(
            "return document.getElementById('test-host').shadowRoot",
            return_by_value=True,
        )
        js_value = result['result']['result'].get('value')
        print(f"JS shadowRoot: {js_value}")  # None

        # Mas o Pydoll consegue:
        host = await tab.find(id='test-host')
        shadow = await host.get_shadow_root()
        print(f"Modo do shadow: {shadow.mode}")  # ShadowRootType.CLOSED

        secret = await shadow.query('.secret')
        text = await secret.text
        print(f"Conteudo: {text}")  # "Conteudo oculto"

asyncio.run(verify_closed_access())
```

## Shadow Roots Aninhados

Web components frequentemente compoem outros web components, criando shadow trees em multiplos niveis:

```mermaid
graph TB
    subgraph "Light DOM"
        Host1["outer-component\n(shadow host)"]
    end

    subgraph "Shadow Tree Externa"
        SR1["#shadow-root (open)"]
        Host2["inner-component\n(shadow host)"]
        P1["p.outer-text"]
    end

    subgraph "Shadow Tree Interna"
        SR2["#shadow-root (closed)"]
        Button["button.deep-btn"]
        P2["p.inner-text"]
    end

    Host1 -.-> SR1
    SR1 --> P1
    SR1 --> Host2
    Host2 -.-> SR2
    SR2 --> P2
    SR2 --> Button
```

O Pydoll lida com isso naturalmente encadeando chamadas `get_shadow_root()`. Cada `ShadowRoot` produz instancias `WebElement` que podem ter seus proprios shadow roots:

```python
outer_host = await tab.find(tag_name='outer-component')
outer_shadow = await outer_host.get_shadow_root()        # open

inner_host = await outer_shadow.query('inner-component')
inner_shadow = await inner_host.get_shadow_root()        # closed, ainda funciona

deep_button = await inner_shadow.query('.deep-btn')
await deep_button.click()
```

Cada nivel segue o mesmo fluxo de resolucao CDP: `describeNode` depois `resolveNode` depois `ShadowRoot` com `_object_id` depois `querySelector` via `callFunctionOn`.

## Shadow Roots Dentro de IFrames

Um cenario comum no mundo real envolve shadow roots dentro de iframes cross-origin — por exemplo, captchas Cloudflare Turnstile. Isso combina dois mecanismos de isolamento: a fronteira do iframe e a fronteira do shadow.

```mermaid
graph TB
    subgraph "Pagina Principal"
        Host["div.widget\n(shadow host)"]
    end

    subgraph "Shadow Tree"
        SR1["#shadow-root"]
        IFrame["iframe\n(cross-origin)"]
    end

    subgraph "IFrame (OOPIF)"
        Body["body"]
    end

    subgraph "Shadow Tree do IFrame"
        SR2["#shadow-root"]
        Button["label.checkbox"]
    end

    Host -.-> SR1
    SR1 --> IFrame
    IFrame -.->|"processo separado"| Body
    Body -.-> SR2
    SR2 --> Button
```

O Pydoll lida com isso de forma transparente atraves da **propagacao de contexto do iframe**. Quando um `ShadowRoot` e criado, ele herda o contexto de roteamento do iframe do seu elemento host:

```python
# A cadeia completa: pagina principal → shadow root → iframe → shadow root → elemento
shadow_host = await tab.find(id='widget-container')
first_shadow = await shadow_host.get_shadow_root()

iframe = await first_shadow.query('iframe')
body = await iframe.find(tag_name='body')
second_shadow = await body.get_shadow_root()

# click() funciona corretamente — eventos de mouse roteados pela sessao OOPIF
button = await second_shadow.query('label.checkbox')
await button.click()
```

### Como a Propagacao de Contexto Funciona

IFrames cross-origin rodam em um processo separado do navegador (Out-of-Process IFrame, ou OOPIF). Comandos CDP para esses iframes devem ser roteados atraves de um `sessionId` dedicado. O Pydoll propaga esse contexto de roteamento automaticamente por toda a cadeia:

1. **IFrame resolve seu contexto**: `iframe.find()` estabelece um `IFrameContext` com `session_id` e `session_handler` para o OOPIF
2. **Elementos filhos herdam o contexto**: Elementos encontrados dentro do iframe recebem o `IFrameContext`
3. **Shadow roots herdam do host**: `ShadowRoot` copia o `_iframe_context` do seu elemento host
4. **Elementos no shadow herdam do shadow root**: Elementos encontrados via `shadow.query()` recebem o contexto propagado
5. **Comandos roteiam corretamente**: `_execute_command()` detecta o contexto herdado e roteia comandos CDP (incluindo `Input.dispatchMouseEvent` para `click()`) pela sessao OOPIF

Isso significa que coordenadas de `DOM.getBoxModel` (que sao relativas ao viewport do iframe) sao corretamente pareadas com eventos de mouse despachados para a mesma sessao OOPIF.

## Buscando Shadow Roots: find_shadow_roots()

`Tab.find_shadow_roots()` percorre toda a arvore DOM para coletar todos os shadow roots encontrados na pagina.

### Como Funciona

```
Tab.find_shadow_roots()
  ├─ DOM.getDocument(depth=-1, pierce=true)
  │   └─ Retorna arvore DOM completa com arrays shadowRoots
  ├─ Percurso recursivo da arvore: _collect_shadow_roots_from_tree()
  │   ├─ Coleta entradas shadowRoots com backendNodeId do host
  │   ├─ Percorre filhos recursivamente
  │   └─ Percorre contentDocument (iframes same-origin)
  ├─ Para cada entrada de shadow root:
  │   ├─ DOM.resolveNode(backendNodeId) → objectId
  │   └─ Resolver elemento host (melhor esforco)
  └─ Retorna list[ShadowRoot] com referencias de host
```

### Timeout: Esperando Shadow Roots

Shadow hosts sao frequentemente injetados de forma assincrona. `Tab.find_shadow_roots()` aceita um parametro `timeout` que faz polling a cada 0.5s ate que pelo menos um shadow root seja encontrado ou o timeout expire (lanca `WaitElementTimeout`). Da mesma forma, `WebElement.get_shadow_root()` tambem suporta `timeout` para esperar pelo shadow root de um elemento especifico:

```python
# Esperar ate 10 segundos pelos shadow roots
shadow_roots = await tab.find_shadow_roots(timeout=10)

# Esperar pelo shadow root de um elemento especifico
shadow = await element.get_shadow_root(timeout=5)
```

### Detalhes Importantes

- **`pierce=True`** em `DOM.getDocument` faz o navegador incluir arrays `shadowRoots` nas descricoes de nos, permitindo a descoberta de todos os shadow roots sem navegar individualmente ate cada host.
- **Conteudo de iframes same-origin** e incluido na arvore via nos `contentDocument`. A travessia os manipula.
- Cada `ShadowRoot` retornado tem uma referencia ao seu `host_element` (resolvido por melhor esforco via `DOM.resolveNode`).

### Travessia Profunda: IFrames Cross-Origin (OOPIFs)

Por padrao, iframes cross-origin (OOPIFs) **nao** sao incluidos na arvore DOM — seu conteudo vive em um processo separado do navegador. Passe `deep=True` para tambem descobrir shadow roots dentro de OOPIFs:

```python
shadow_roots = await tab.find_shadow_roots(deep=True, timeout=10)
```

Quando `deep=True` e definido, o metodo executa etapas adicionais:

```
Tab.find_shadow_roots(deep=True)
  ├─ ... (travessia do documento principal como acima) ...
  └─ _collect_oopif_shadow_roots()
      ├─ ConnectionHandler de nivel browser (sem page_id → endpoint do browser)
      ├─ Target.getTargets() → filtrar type='iframe'
      └─ Para cada target iframe:
          ├─ Target.attachToTarget(targetId, flatten=True) → sessionId
          ├─ DOM.getDocument(depth=-1, pierce=True) com sessionId
          ├─ _collect_shadow_roots_from_tree() no DOM do OOPIF
          └─ Para cada shadow root encontrado:
              ├─ DOM.resolveNode(backendNodeId) com sessionId
              ├─ Resolver elemento host (melhor esforco) com sessionId
              ├─ Criar IFrameContext(frame_id, session_handler, session_id)
              └─ Definir IFrameContext no elemento host (ou diretamente no ShadowRoot)
```

Os objetos `ShadowRoot` retornados carregam o contexto de roteamento OOPIF (`IFrameContext`), entao elementos encontrados via `shadow_root.query()` roteiam automaticamente comandos CDP pela sessao OOPIF correta. Isso e critico para cenarios como captchas Cloudflare Turnstile, onde o checkbox esta dentro de um shadow root fechado dentro de um iframe cross-origin.

## Limitacoes e Casos Especiais

### Estrategias de Seletores Dentro de Shadow Roots

!!! warning "Use Apenas query() com CSS Dentro de Shadow Roots"
    `ShadowRoot` define `_css_only = True`, o que significa que apenas `query()` com seletores CSS e suportado. `find()` e `query()` com XPath lancam `NotImplementedError`.

Shadow roots implementam nativamente `querySelector()` e `querySelectorAll()`, tornando seletores CSS a escolha natural e confiavel:

| Metodo | Dentro do Shadow Root | Notas |
|--------|:--:|---|
| `query('seletor-css')` | Totalmente suportado | Abordagem recomendada |
| `query('seletor-css', find_all=True)` | Totalmente suportado | Retorna lista de elementos |
| `find()` | Nao suportado | Lanca `NotImplementedError` |
| `query('//xpath')` | Nao suportado | Lanca `NotImplementedError` |

```python
shadow = await host.get_shadow_root()

# ✓ Recomendado: query() com seletores CSS
button = await shadow.query('button.submit')
email = await shadow.query('#email-input')
items = await shadow.query('.item', find_all=True)

# ✗ Nao suportado: find() e XPath lancam NotImplementedError
# shadow.find(id='email-input')        # NotImplementedError
# shadow.query('//button')             # NotImplementedError
```

### XPath Nao Cruza Fronteiras do Shadow

Expressoes XPath a partir da raiz do documento nao conseguem atravessar fronteiras do shadow. Esta e uma limitacao fundamental do XPath, que foi projetado antes do Shadow DOM existir:

```python
# Nao encontra conteudo shadow: XPath no nivel do documento nao cruza a fronteira
element = await tab.find(xpath='//div[@id="host"]//button')
```

### Shadow Roots User-Agent

Shadow roots internos do navegador (ex: estilizacao de placeholder de `<input>`, controles de `<video>`) sao do tipo `user-agent`. Eles sao acessiveis via CDP, mas sua estrutura interna varia entre versoes do navegador e nao faz parte de nenhum padrao web.

```python
input_element = await tab.find(tag_name='input')
try:
    ua_shadow = await input_element.get_shadow_root()
    # ua_shadow.mode == ShadowRootType.USER_AGENT
    # Estrutura interna e especifica do navegador
except ShadowRootNotFound:
    pass  # Nem todos os inputs tem shadow roots user-agent
```

!!! warning "Estabilidade de Shadow Roots User-Agent"
    Nao construa logica de automacao que dependa da estrutura interna de shadow roots user-agent. Sua estrutura DOM e um detalhe de implementacao que pode mudar entre versoes do navegador sem aviso.

### Referencias de Shadow Root Obsoletas

Se o elemento host for removido do DOM e re-adicionado (comum em aplicacoes single-page), o `objectId` do shadow root se torna obsoleto. A solucao e re-adquirir o shadow root:

```python
# Apos uma navegacao de pagina ou reconstrucao do DOM:
host = await tab.find(id='my-component', timeout=5)  # Re-encontrar o host
shadow = await host.get_shadow_root()                 # Shadow root atualizado
```

## Pontos-Chave

- **Encapsulamento Shadow DOM** oculta elementos do `querySelector()` no nivel do documento, quebrando automacao tradicional
- **CDP opera abaixo da camada de API JavaScript**, contornando restricoes de modo do shadow completamente
- **`backendNodeId`** e o identificador estavel usado para resolucao de shadow root, evitando a necessidade de habilitar o dominio DOM
- **`ShadowRoot` herda `FindElementsMixin`** com `_css_only = True`, suportando apenas `query()` com seletores CSS; `find()` e XPath lancam `NotImplementedError`
- **Shadow roots fechados** sao totalmente acessiveis porque o modo `closed` e uma politica no nivel JavaScript, nao uma restricao no nivel DOM
- **Shadow roots aninhados** funcionam naturalmente encadeando chamadas `get_shadow_root()` em cada nivel
- **Shadow roots dentro de iframes** funcionam de forma transparente atraves da propagacao automatica de contexto do iframe
- **Use seletores CSS** (`query()`) dentro de shadow roots; `find()` e XPath nao sao suportados
- **`find_shadow_roots()`** descobre todos os shadow roots na pagina; suporta `timeout` para polling e `deep=True` para iframes cross-origin (OOPIFs)
- **`get_shadow_root(timeout)`** espera pelo shadow root de um elemento especifico

## Documentacao Relacionada

- **[Guia de Pesquisa de Elementos](../../features/element-finding.md)**: Uso pratico de `find()`, `query()`, e acesso a shadow root
- **[IFrames e Contextos](../fundamentals/iframes-and-contexts.md)**: Como o Pydoll resolve e roteia comandos para iframes, incluindo tratamento de OOPIF
- **[Arquitetura do FindElements Mixin](./find-elements-mixin.md)**: Como o mecanismo `_object_id` habilita buscas com escopo
- **[Dominio WebElement](./webelement-domain.md)**: Como elementos interagem com CDP
- **[Camada de Conexao](../fundamentals/connection-layer.md)**: Comunicacao WebSocket com o navegador
