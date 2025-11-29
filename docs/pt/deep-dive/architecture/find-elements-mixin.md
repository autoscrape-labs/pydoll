# Arquitetura do Mixin FindElements

O FindElementsMixin representa uma decisão arquitetural crítica no Pydoll: usar **composição sobre herança** para compartilhar capacidades de localização de elementos entre `Tab` e `WebElement` sem acoplá-los através de uma classe base comum. Este documento explora o padrão mixin, sua implementação e a mecânica interna de localização de elementos.

!!! info "Guia de Uso Prático"
    Para exemplos práticos e padrões de uso, consulte o [Guia de Localização de Elementos](../features/automation/element-finding.md) e o [Guia de Seletores](./selectors-guide.md).

## Padrão Mixin: Filosofia de Design

### O que é um Mixin?

Um mixin é uma classe projetada para **fornecer métodos a outras classes** sem ser uma classe base em uma hierarquia de herança tradicional. Diferente da herança padrão (que modela relações "é-um" (is-a)), mixins modelam **capacidades "pode-fazer" (can-do)**.

```python
# Herança tradicional: "é-um" (is-a)
class Animal:
    def breathe(self): ...

class Dog(Animal):  # Dog É-UM Animal
    def bark(self): ...

# Padrão Mixin: "pode-fazer" (can-do)
class FlyableMixin:
    def fly(self): ...

class Bird(Animal, FlyableMixin):  # Bird É-UM Animal, PODE voar
    pass
```

### Por que Mixins em vez de Herança?

O Pydoll enfrenta um desafio arquitetural específico:

- **`Tab`** precisa encontrar elementos no **contexto do documento**
- **`WebElement`** precisa encontrar elementos **relativos a si mesmo** (elementos filhos)
- Ambos precisam de **lógica de seletor idêntica** (CSS, XPath, construção de atributos)

**Opção 1: Classe Base Compartilhada**

```python
class ElementLocator:
    def find(...): ...

class Tab(ElementLocator):
    pass

class WebElement(ElementLocator):
    pass
```

**Problemas:**
- Alto acoplamento: `Tab` e `WebElement` agora compartilham a hierarquia de herança
- Viola a Responsabilidade Única: `Tab` não deveria herdar da mesma classe que `WebElement`
- Difícil de estender: Adicionar novas capacidades requer modificar a classe base

**Opção 2: Padrão Mixin (Abordagem Escolhida)**

```python
class FindElementsMixin:
    def find(...): ...
    def query(...): ...

class Tab(FindElementsMixin):
    # Lógica específica do Tab
    pass

class WebElement(FindElementsMixin):
    # Lógica específica do WebElement
    pass
```

**Benefícios:**

- **Desacoplamento**: `Tab` e `WebElement` permanecem independentes
- **Reutilização**: Mesma lógica de localização de elementos em ambas as classes
- **Componibilidade**: Pode adicionar outros mixins sem conflitos
- **Testabilidade**: O Mixin pode ser testado isoladamente

!!! tip "Características do Mixin"
    1. **Sem Estado (Stateless)**: Mixins não mantêm seu próprio estado (sem `__init__`)
    2. **Injeção de Dependência**: Assume que a classe consumidora fornece dependências (ex: `_connection_handler`)
    3. **Propósito Único**: Cada mixin fornece uma capacidade coesa
    4. **Não Instanciável**: Nunca crie `FindElementsMixin()` diretamente

## Implementação do Mixin no Pydoll

### Estrutura da Classe

O FindElementsMixin usa **injeção de dependência** para funcionar com qualquer classe que forneça um `_connection_handler`:

```python
class FindElementsMixin:
    """
    Mixin que fornece capacidades de localização de elementos.
    
    Assume que a classe consumidora possui:
    - _connection_handler: Instância de ConnectionHandler para comandos CDP
    - _object_id: Optional[str] para buscas relativas ao contexto (apenas WebElement)
    """
    
    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler  # Dica de tipo (type hint), não um atributo real
    
    async def find(self, ...):
        # Implementação usa self._connection_handler
        # Verifica self._object_id para determinar o contexto
```

**Insight principal:** O mixin não define `_connection_handler` ou `_object_id`. Ele **assume** que eles existem via duck typing.

### Como Tab e WebElement Usam o Mixin

```python
# Tab: buscas em nível de documento
class Tab(FindElementsMixin):
    def __init__(self, browser, target_id, connection_port):
        self._connection_handler = ConnectionHandler(connection_port)
        # Sem _object_id → busca a partir da raiz do documento

# WebElement: buscas relativas ao elemento
class WebElement(FindElementsMixin):
    def __init__(self, object_id, connection_handler, ...):
        self._object_id = object_id  # ID do objeto CDP
        self._connection_handler = connection_handler
        # Tem _object_id → busca relativa a este elemento
```

**Distinção crítica:**

- **Tab**: `hasattr(self, '_object_id')` → `False` → usa `RuntimeCommands.evaluate()` (contexto do documento)
- **WebElement**: `hasattr(self, '_object_id')` → `True` → usa `RuntimeCommands.call_function_on()` (contexto do elemento)

### Detecção de Contexto

O mixin detecta dinamicamente o contexto da busca:

```python
async def _find_element(self, by, value, raise_exc=True):
    if hasattr(self, '_object_id'):
        # Busca relativa: chama a função JavaScript NESTE elemento
        command = self._get_find_element_command(by, value, self._object_id)
    else:
        # Busca no documento: avalia o JavaScript no contexto global
        command = self._get_find_element_command(by, value)
    
    response = await self._execute_command(command)
    # ...
```

Esta implementação única lida com ambos:

- `tab.find(id='submit')` → busca no documento inteiro
- `form_element.find(id='submit')` → busca dentro do `form_element`

!!! warning "Acoplamento de Dependência do Mixin"
    O mixin é **fortemente acoplado** ao modelo de objeto do CDP. Ele assume que:
    
    - Elementos são representados por strings `objectId`
    - `Runtime.evaluate()` para buscas no documento
    - `Runtime.callFunctionOn()` para buscas relativas a elementos
    
    Isso é aceitável porque o Pydoll é **específico do CDP**. Um design mais genérico exigiria camadas de abstração.

## Design da API Pública

O mixin expõe dois métodos de alto nível com filosofias de design distintas:

### find(): Seleção Baseada em Atributos

```python
@overload
async def find(self, find_all: Literal[False], ...) -> WebElement: ...

@overload
async def find(self, find_all: Literal[True], ...) -> list[WebElement]: ...

async def find(
    self,
    id: Optional[str] = None,
    class_name: Optional[str] = None,
    name: Optional[str] = None,
    tag_name: Optional[str] = None,
    text: Optional[str] = None,
    timeout: int = 0,
    find_all: bool = False,
    raise_exc: bool = True,
    **attributes,
) -> Union[WebElement, list[WebElement], None]:
```

**Decisões de design:**

1. **Kwargs (argumentos nomeados) em vez de Enum By posicional**:
   ```python
   # Pydoll (intuitivo)
   await tab.find(id='submit', class_name='primary')
   
   # Selenium (verboso)
   driver.find_element(By.ID, 'submit')  # Não pode combinar atributos facilmente
   ```

2. **Resolução automática para o seletor ideal**:
   - Atributo único → usa `By.ID`, `By.CLASS_NAME`, etc. (mais rápido)
   - Múltiplos atributos → constrói XPath (flexível, mas mais lento)

3. **`**attributes` para extensibilidade**:
   ```python
   await tab.find(data_testid='submit-btn', aria_label='Submit form')
   # Constrói: //\*[@data-testid='submit-btn' and @aria-label='Submit form']
   ```

### query(): Seleção Baseada em Expressão

```python
@overload
async def query(self, expression, find_all: Literal[False], ...) -> WebElement: ...

@overload
async def query(self, expression, find_all: Literal[True], ...) -> list[WebElement]: ...

async def query(
    self, 
    expression: str, 
    timeout: int = 0, 
    find_all: bool = False, 
    raise_exc: bool = True
) -> Union[WebElement, list[WebElement], None]:
```

**Decisões de design:**

1. **Detecção automática de CSS vs XPath**:
   ```python
   # Detecção de XPath (começa com / ou ./)
   await tab.query("//div[@id='content']")
   
   # Detecção de CSS (padrão)
   await tab.query("div#content > p.intro")
   ```

2. **Parâmetro de expressão única** (diferente do `find()`):
   - Assume que o usuário conhece a sintaxe do seletor
   - Sem sobrecarga de abstração

3. **Passagem direta (passthrough) para o navegador**:
   - `querySelector()` / `querySelectorAll()` para CSS
   - `document.evaluate()` para XPath

### Padrão de Sobrecarga (Overload) para Segurança de Tipos

Ambos os métodos usam `@overload` para fornecer **tipos de retorno precisos**:

```python
# A IDE sabe que o tipo de retorno é WebElement
element = await tab.find(id='submit')

# A IDE sabe que o tipo de retorno é list[WebElement]
elements = await tab.find(class_name='item', find_all=True)

# A IDE sabe que o tipo de retorno é Optional[WebElement]
maybe_element = await tab.find(id='optional', raise_exc=False)
```

Isso é crítico para o autocomplete da IDE e verificação de tipos. Veja [Análise Profunda do Sistema de Tipos](./typing-system.md) para detalhes.

## Arquitetura de Resolução de Seletor

O mixin converte a entrada do usuário em comandos CDP através de um pipeline de resolução:

| Estágio | Entrada | Saída | Decisão Chave |
|-------|-------|--------|-------------|
| **1. Seleção de Método** | `find()` kwargs ou `query()` expressão | Estratégia de seletor | Baseado em atributo vs. baseado em expressão |
| **2. Resolução da Estratégia** | Atributos ou expressão | Enum `By` + valor | Atributo único → método nativo, Múltiplos → XPath |
| **3. Detecção de Contexto** | `By` + valor + `hasattr(_object_id)` | Tipo de comando CDP | Documento vs. busca relativa ao elemento |
| **4. Geração do Comando** | Tipo de comando CDP + seletor | JavaScript + método CDP | `evaluate()` vs `callFunctionOn()` |
| **5. Execução** | Comando CDP | `objectId` ou array de `objectId`s | Via ConnectionHandler |
| **6. Criação do WebElement** | `objectId` + atributos | Instância(s) de `WebElement` | Função de fábrica (factory) para evitar importações circulares |

### Principais Decisões Arquiteturais

**1. Atributos Únicos vs. Múltiplos**

```python
# Atributo único → Seletor direto (rápido)
await tab.find(id='username')  # Usa By.ID → getElementById()

# Múltiplos atributos → XPath (flexível)
await tab.find(tag_name='input', type='password', name='pwd')
# → //input[@type='password' and @name='pwd']
```

**Por que isso importa:**
- Métodos nativos (`getElementById`, `getElementsByClassName`) são 10-50% mais rápidos que XPath
- A sobrecarga do XPath é aceitável ao combinar atributos (não há alternativa)

**2. Detecção Automática do Tipo de Seletor**

```python
await tab.query("//div")       # Começa com / → XPath
await tab.query("#login")      # Padrão → CSS
```

**Implementação:**
```python
if expression.startswith(('./', '/', '(/')):
    return By.XPATH
return By.CSS_SELECTOR
```

A heurística é **inequívoca** - seletores CSS não podem começar com `/`.

**3. Ajuste de Caminho Relativo do XPath**

Para buscas relativas a elementos, o XPath absoluto deve ser convertido:

```python
# Usuário fornece: //div
# Para WebElement: .//div (relativo ao elemento, não ao documento)

def _ensure_relative_xpath(xpath):
    return f'.{xpath}' if not xpath.startswith('.') else xpath
```

Sem isso, `element.find()` buscaria a partir da raiz do documento.

## Geração de Comando CDP

O mixin roteia para diferentes métodos CDP com base no contexto da busca:

| Contexto | Tipo de Seletor | Método CDP | Equivalente JavaScript |
|---------|--------------|------------|---------------------|
| Documento | CSS | `Runtime.evaluate` | `document.querySelector()` |
| Documento | XPath | `Runtime.evaluate` | `document.evaluate()` |
| Elemento | CSS | `Runtime.callFunctionOn` | `this.querySelector()` |
| Elemento | XPath | `Runtime.callFunctionOn` | `document.evaluate(..., this)` |

**Insight principal:** `Runtime.callFunctionOn` requer um `objectId` (o elemento no qual a função será chamada), enquanto `Runtime.evaluate` executa no escopo global.

### Modelos (Templates) JavaScript

O Pydoll usa modelos pré-definidos para consistência e performance:

```python
# Seletores CSS
Scripts.QUERY_SELECTOR = 'document.querySelector("{selector}")'
Scripts.RELATIVE_QUERY_SELECTOR = 'this.querySelector("{selector}")'

# Expressões XPath
Scripts.FIND_XPATH_ELEMENT = '''
    document.evaluate("{escaped_value}", document, null,
                      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
'''
```

Modelos evitam concatenação de strings em tempo de execução e centralizam o código JavaScript.

## Resolução de ObjectID e Criação de WebElement

O CDP representa nós DOM como **strings `objectId`**. O mixin abstrai isso:

**Fluxo de elemento único:**
1. Executar comando CDP → Extrair `objectId` da resposta
2. Chamar `DOM.describeNode(objectId)` → Obter atributos, nome da tag
3. Criar `WebElement(objectId, connection_handler, attributes)`

**Fluxo de múltiplos elementos:**
1. Executar comando CDP → Retorna **array como um único objeto remoto**
2. Chamar `Runtime.getProperties(array_objectId)` → Enumerar índices do array
3. Extrair `objectId` individual para cada elemento
4. Descrever e criar `WebElement` para cada

**Por que `Runtime.getProperties`?** O CDP não retorna arrays diretamente - ele retorna uma **referência a um objeto array**. Devemos enumerar suas propriedades para extrair os elementos individuais.

## Insights Arquiteturais e Tradeoffs de Design

### Por que Kwargs em vez de Enum By?

**A escolha do Pydoll:**
```python
await tab.find(id='submit', class_name='primary')
```

**A abordagem do Selenium:**
```python
driver.find_element(By.ID, 'submit')  # Não pode combinar atributos
```

**Justificativa:**

- **Descoberta (Discoverability)**: O autocomplete da IDE mostra todos os parâmetros disponíveis
- **Componibilidade**: Pode combinar múltiplos atributos em uma chamada
- **Legibilidade**: `id='submit'` é mais intuitivo do que `(By.ID, 'submit')`

**Tradeoff:** Kwargs são menos explícitos sobre a estratégia do seletor. Resolvido com documentação e logs.

### Por que Detectar Automaticamente CSS vs. XPath?

A heurística `_get_expression_type()` elimina o fardo do usuário:

```python
await tab.query("//div")       # Auto: XPath
await tab.query("#login")      # Auto: CSS
await tab.query("div > p")     # Auto: CSS
```

**Benefícios:**

- **Ergonomia**: Usuários não precisam especificar o tipo de seletor
- **Correção**: Impossível usar incorretamente (XPath com método CSS, vice-versa)

**Limitação:** Nenhuma maneira de forçar a interpretação de CSS para seletores ambíguos (caso extremo raro).

### Prevenção de Importação Circular: create_web_element()

O mixin usa uma **função de fábrica (factory function)** para evitar importações circulares:

```python
def create_web_element(*args, **kwargs):
    """Importa WebElement dinamicamente em tempo de execução."""
    from pydoll.elements.web_element import WebElement  # Importação tardia
    return WebElement(*args, **kwargs)
```

**Por que é necessário?**

- `FindElementsMixin` → precisa criar `WebElement`
- `WebElement` → herda de `FindElementsMixin`
- Dependência circular!

**Solução:** Importação tardia (late import) dentro da função de fábrica. A importação só é executada quando a função é chamada, quebrando o ciclo.

### hasattr() para Detecção de Contexto: Elegante ou Hacky?

O mixin usa `hasattr(self, '_object_id')` para detectar Tab vs WebElement:

```python
if hasattr(self, '_object_id'):
    # WebElement: busca relativa ao elemento
else:
    # Tab: busca em nível de documento
```

**Isso é "hacky" (gambiarra)?**

- **Não**: É **duck typing** (um idioma Pythônico)
- O Mixin não precisa saber a hierarquia de classes
- Tanto Tab quanto WebElement fornecem `_connection_handler`
- WebElement adicionalmente fornece `_object_id`

**Abordagens alternativas:**

1. **Verificação de tipo**: `if isinstance(self, WebElement)` → Acopla o mixin ao WebElement
2. **Método abstrato**: Exigiria que Tab/WebElement implementassem `get_search_context()` → Mais código boilerplate
3. **Injeção de dependência**: Passar o contexto como parâmetro → Quebra a ergonomia da API

**Veredito:** `hasattr()` é a melhor solução para este caso de uso.

## Principais Conclusões

1. **Mixins permitem o compartilhamento de código** sem acoplar `Tab` e `WebElement` através de herança
2. **Detecção de contexto via duck typing** (`hasattr`) mantém o mixin desacoplado da hierarquia de classes
3. **Resolução automática otimiza a performance** usando métodos nativos para atributos únicos
4. **Construção de XPath fornece componibilidade** para consultas com múltiplos atributos
5. **Espera baseada em polling (sondagem) é simples**, mas troca ciclos de CPU por simplicidade de implementação
6. **Complexidade do modelo de objeto CDP** é escondida atrás da abstração do WebElement
7. **Segurança de tipos via sobrecargas (overloads)** fornece tipos de retorno precisos para suporte da IDE

## Documentação Relacionada

Para um entendimento mais profundo dos componentes arquiteturais relacionados:

- **[Sistema de Tipos](./typing-system.md)**: Padrão Overload, TypedDict, tipos Genéricos
- **[Domínio do WebElement](./webelement-domain.md)**: Arquitetura do WebElement e métodos de interação
- **[Guia de Seletores](./selectors-guide.md)**: Sintaxe e boas práticas de CSS vs XPath
- **[Domínio da Tab](./tab-domain.md)**: Operações em nível de aba e gerenciamento de contexto

Para padrões de uso prático:

- **[Guia de Localização de Elementos](../features/automation/element-finding.md)**: Exemplos práticos e padrões
- **[Interações Humanizadas](../features/automation/human-interactions.md)**: Interação realista com elementos