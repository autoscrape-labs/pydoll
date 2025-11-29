# O Sistema de Tipos do Python e o Pydoll

O Pydoll utiliza extensivamente o sistema de tipos do Python para fornecer excelente suporte de IDE, detectar erros precocemente e tornar a API autodocumentada. Este guia explica o básico das dicas de tipo (type hints) e como o Pydoll as utiliza para aprimorar sua experiência de desenvolvimento.

## O Básico de Dicas de Tipo (Type Hints)

Dicas de tipo são anotações opcionais que especificam o tipo de valor que uma variável, parâmetro ou valor de retorno deve ter. Elas não afetam o comportamento em tempo de execução, mas habilitam ferramentas poderosas.

### Dicas de Tipo Simples

```python
# Tipos básicos
name: str = "Pydoll"
port: int = 9222
is_headless: bool = False
quality: float = 0.85

# Anotações de função
def navigate(url: str, timeout: int = 30) -> bool:
    # ... implementação
    return True
```

### Tipos de Contêineres

```python
from typing import List, Dict, Optional

# Listas e dicionários
urls: List[str] = ['https://example.com', 'https://google.com']
headers: Dict[str, str] = {'User-Agent': 'MyBot/1.0'}

# Valores opcionais (podem ser None)
target_id: Optional[str] = None

# Sintaxe moderna (Python 3.9+)
urls: list[str] = ['https://example.com']
headers: dict[str, str] = {'User-Agent': 'MyBot/1.0'}
```

!!! tip "Sintaxe do Python 3.9+"
    O código-fonte do Pydoll usa a sintaxe mais antiga `List[]`, `Dict[]` para compatibilidade retroativa, mas você pode usar `list[]`, `dict[]` em minúsculas no seu código se estiver usando Python 3.9+.

## TypedDict: Dicionários Estruturados

O `TypedDict` permite definir estruturas de dicionário com chaves e tipos de valor específicos. Isso é **amplamente utilizado** nas definições de protocolo CDP do Pydoll.

### TypedDict Básico

```python
from typing import TypedDict

class UserInfo(TypedDict):
    name: str
    age: int
    email: str

# A IDE sabe exatamente quais chaves existem
user: UserInfo = {
    'name': 'Alice',
    'age': 30,
    'email': 'alice@example.com'
}

# O Autocomplete funciona!
print(user['name'])  # IDE sugere: name, age, email
```

### Como o Pydoll Usa o TypedDict

O Pydoll define **cada comando, resposta e evento do CDP** como um TypedDict. Isso significa que sua IDE sabe exatamente quais propriedades estão disponíveis:

```python
# De pydoll/protocol/page/methods.py
class CaptureScreenshotParams(TypedDict, total=False):
    """Parâmetros para captureScreenshot."""
    format: ScreenshotFormat
    quality: int
    clip: Viewport
    fromSurface: bool
    captureBeyondViewport: bool
    optimizeForSpeed: bool

class CaptureScreenshotResult(TypedDict):
    """Resultado para o comando captureScreenshot."""
    data: str
```

Quando você chama métodos que retornam respostas do CDP, sua IDE autocompleta as chaves da resposta:

```python
async def example():
    response = await tab.take_screenshot(as_base64=True)
    
    # A IDE sabe que esta é uma CaptureScreenshotResponse
    # e sugere 'result' -> 'data'
    screenshot_data = response['result']['data']  # Autocomplete completo!
```

### Campos Opcionais vs Obrigatórios

O TypedDict suporta campos opcionais usando `NotRequired[]`:

```python
from typing import TypedDict, NotRequired

# De pydoll/protocol/network/methods.py
class GetCookiesParams(TypedDict):
    """Parâmetros para recuperar cookies do navegador."""
    urls: NotRequired[list[str]]  # Este campo é opcional
```

A flag `total=False` torna **todos** os campos opcionais:

```python
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat  # Todos os campos são opcionais
    quality: int
    clip: Viewport
```

!!! info "Mágica do Autocomplete"
    Quando você digita `response['`, sua IDE mostra todas as chaves disponíveis com seus tipos. Este é o superpoder do TypedDict em ação!

## Enums: Constantes com Tipo Seguro (Type-Safe)

Enums (enumerações) fornecem constantes com tipo seguro que sua IDE pode autocompletar. O Pydoll os usa extensivamente para valores CDP.

### Enums Básicos

```python
from enum import Enum

class ScreenshotFormat(str, Enum):
    JPEG = 'jpeg'
    PNG = 'png'
    WEBP = 'webp'

# IDE autocompleta os formatos disponíveis
format = ScreenshotFormat.PNG  # O tipo é ScreenshotFormat
print(format.value)  # 'png'
```

### Uso de Enums no Pydoll

```python
from pydoll.constants import Key
from pydoll.protocol.page.types import ScreenshotFormat
from pydoll.protocol.input.types import KeyModifier

# Encontrando elementos - usa kwargs, não enums
element = await tab.find(id='submit-btn')
element = await tab.find(class_name='btn-primary')
element = await tab.find(tag_name='button')

# Entrada de teclado - IDE sugere todas as teclas
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB)
await element.press_keyboard_key(Key.ESCAPE)

# Modificadores são enums inteiros (para teclas especiais)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# Enum de formato de captura de tela
await tab.take_screenshot('file.webp', format=ScreenshotFormat.WEBP)
```

!!! tip "Autocomplete de Enum"
    Digite `Key.` ou `ScreenshotFormat.` e sua IDE mostrará todas as opções disponíveis. Chega de memorizar strings!

## Sobrecarga de Funções (Function Overloads)

Sobrecargas permitem que uma função retorne tipos diferentes com base em seus parâmetros. O Pydoll usa isso para fornecer informações de tipo precisas.

### Exemplo Básico de Sobrecarga

```python
from typing import overload

# Assinaturas de sobrecarga (não executadas)
@overload
def process(data: str) -> str: ...

@overload
def process(data: int) -> int: ...

# Implementação real
def process(data):
    return data * 2

# A IDE conhece os tipos de retorno
result1 = process("hello")  # Tipo: str
result2 = process(42)       # Tipo: int
```

### Uso de Sobrecarga no Pydoll

Os métodos `find()` e `query()` retornam tipos diferentes dependendo do parâmetro `find_all`:

```python
# De pydoll/elements/mixins/find_elements_mixin.py
class FindElementsMixin:
    @overload
    async def find(
        self, find_all: Literal[False] = False, **kwargs
    ) -> WebElement: ...
    
    @overload
    async def find(
        self, find_all: Literal[True], **kwargs
    ) -> list[WebElement]: ...
    
    async def find(
        self, find_all: bool = False, **kwargs
    ) -> Union[WebElement, list[WebElement]]:
        # Implementação...
```

No seu código:

```python
# find_all=False (padrão) - A IDE sabe que o tipo de retorno é WebElement
button = await tab.find(id='submit-btn')
await button.click()  # Métodos de elemento único disponíveis!

# find_all=True - A IDE sabe que o tipo de retorno é list[WebElement]
buttons = await tab.find(class_name='btn', find_all=True)
for btn in buttons:  # A IDE sabe que isso é uma lista!
    await btn.click()

# O mesmo com query()
element = await tab.query('#submit-btn')  # Tipo: WebElement
elements = await tab.query('.btn', find_all=True)  # Tipo: list[WebElement]
```

!!! tip "Inferência de Tipo Inteligente"
    Sua IDE sabe automaticamente se você está obtendo um único elemento ou uma lista com base no parâmetro `find_all`. Não é necessário casting ou asserções de tipo!

## Tipos Genéricos (Generic Types)

Genéricos são como "contêineres de tipo" que funcionam com tipos diferentes enquanto preservam a informação de tipo. Pense neles como modelos que se adaptam ao que você coloca dentro.

### Entendendo Genéricos: Uma Analogia Simples

Imagine uma `Caixa` que pode conter qualquer coisa. Sem genéricos:

```python
# Sem genéricos - A IDE não sabe o que está dentro
class Box:
    def __init__(self, content):
        self.content = content
    
    def get(self):
        return self.content

my_box = Box("hello")
item = my_box.get()  # Tipo: Unknown - poderia ser qualquer coisa!
```

Com genéricos:

```python
from typing import Generic, TypeVar

T = TypeVar('T')  # T é um "marcador de posição de tipo"

class Box(Generic[T]):
    def __init__(self, content: T):
        self.content = content
    
    def get(self) -> T:
        return self.content

# Agora a IDE sabe exatamente o que está dentro de cada caixa
string_box: Box[str] = Box("hello")
item1 = string_box.get()  # Tipo: str

number_box: Box[int] = Box(42)
item2 = number_box.get()  # Tipo: int

# List é um genérico embutido
numbers: list[int] = [1, 2, 3]  # Lista que contém ints
names: list[str] = ["Alice", "Bob"]  # Lista que contém strs
```

!!! tip "Genéricos Simplificam Dicas de Tipo"
    Em vez de escrever `Union[List[str], List[int], List[float], ...]` para todo tipo de lista possível, genéricos permitem que você escreva um `list[T]` reutilizável que se adapta ao que você coloca dentro.

### Exemplo de Genérico do Mundo Real

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Response(Generic[T]):
    """Um wrapper de resposta de API genérico."""
    def __init__(self, data: T, status: int):
        self.data = data
        self.status = status
    
    def get_data(self) -> T:
        return self.data

# Cada resposta preserva seu tipo de dado
user_response: Response[dict] = Response({"name": "Alice"}, 200)
user_data = user_response.get_data()  # Tipo: dict

count_response: Response[int] = Response(42, 200)
count = count_response.get_data()  # Tipo: int
```

### Como o Pydoll Usa Genéricos

O sistema de comandos CDP do Pydoll usa genéricos para garantir que o tipo de resposta corresponda ao comando:

```python
# De pydoll/protocol/base.py
from typing import Generic, TypeVar

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')

class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """Estrutura base para todos os comandos."""
    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]

class Response(TypedDict, Generic[T_CommandResponse]):
    """Estrutura base para todas as respostas."""
    id: int
    result: T_CommandResponse
```

Isso significa que quando você executa um comando, o tipo de resposta é automaticamente inferido:

```python
# PageCommands.navigate retorna Command[NavigateParams, NavigateResult]
command = PageCommands.navigate('https://example.com')

# ConnectionHandler.execute_command preserva o tipo genérico
response = await connection_handler.execute_command(command)

# A IDE sabe que response['result'] é NavigateResult (não apenas "qualquer dict")
frame_id = response['result']['frameId']  # Autocomplete funciona!
loader_id = response['result']['loaderId']  # Todos os campos são conhecidos!
```

!!! info "Por que Genéricos Importam no Pydoll"
    Sem genéricos, cada resposta CDP seria apenas tipada como `dict[str, Any]`, e você perderia todo o autocomplete. Com genéricos, a IDE sabe a estrutura exata de cada resposta com base em qual comando você enviou.

## Tipos de União (Union Types)

Uniões representam valores que podem ser de um de vários tipos:

```python
from typing import Union

# Pode ser string ou int
identifier: Union[str, int] = "user-123"
identifier = 456  # Também válido

# Sintaxe moderna (Python 3.10+)
identifier: str | int = "user-123"
```

### Uso de União no Pydoll

```python
# Caminhos de arquivo podem ser strings ou objetos Path
from pathlib import Path

async def upload_file(files: Union[str, Path, list[Union[str, Path]]]):
    # Lida com múltiplos tipos de entrada
    pass

# Todos estes funcionam:
await tab.expect_file_chooser('/path/to/file.txt')
await tab.expect_file_chooser(Path('/path/to/file.txt'))
await tab.expect_file_chooser(['/file1.txt', Path('/file2.txt')])
```

## Benefícios Práticos no Pydoll

### 1. Autocomplete Inteligente

Sua IDE sugere chaves, métodos e valores disponíveis:

```python
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.network.types import ResourceType
from pydoll.protocol.input.types import KeyModifier
from pydoll.constants import Key

# Autocomplete para nomes de eventos
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, callback)

# Autocomplete para tipos de recursos
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)

# Autocomplete para teclas
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# Autocomplete para kwargs em find()
element = await tab.find(id='submit-btn')  # IDE sugere: id, class_name, tag_name, etc.
```

### 2. Pegue Erros Cedo

Verificadores de tipo como mypy ou Pylance pegam erros antes do tempo de execução:

```python
# Verificador de tipo pega isso
await tab.take_screenshot('file.png', quality='high')  # Erro: quality deve ser int

# Verificador de tipo pega isso
event = await tab.find(id='button')
await tab.on(event, callback)  # Erro: event é WebElement, não str

# Correto
await tab.take_screenshot('file.png', quality=90)
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
```

### 3. Código Autodocumentado

Os tipos servem como documentação embutida:

```python
# Você sabe imediatamente o que cada parâmetro espera
async def take_screenshot(
    self,
    path: Optional[str] = None,
    quality: int = 100,
    beyond_viewport: bool = False,
    as_base64: bool = False,
) -> Optional[str]:
    pass
```

### 4. Navegação em Respostas CDP

Navegue em respostas CDP complexas com confiança:

```python
# De pydoll/protocol/browser/methods.py
class GetVersionResult(TypedDict):
    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str

# No seu código
version_info = await browser.get_version()

# IDE sugere todas as chaves disponíveis
print(version_info['product'])         # Autocomplete!
print(version_info['userAgent'])       # Autocomplete!
print(version_info['protocolVersion']) # Autocomplete!
```

## Verificando Tipos no Seu Código

### Usando Pylance (VS Code)

O Pylance fornece verificação de tipos em tempo real no VS Code:

1.  Instale a extensão Pylance
2.  Defina o modo de verificação de tipos nas configurações:

```json
{
    "python.analysis.typeCheckingMode": "basic"  // ou "strict"
}
```

Agora você obtém feedback instantâneo:

```python
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # Pylance mostra os tipos dos parâmetros enquanto você digita
        await tab.go_to('https://example.com', timeout=30)
        
        # Pylance avisa sobre tipos errados
        await tab.take_screenshot(quality='high')  # Aviso!
```

### Usando mypy

Execute o mypy para verificar seu projeto inteiro:

```bash
pip install mypy
mypy your_script.py
```

Exemplo de saída:

```
your_script.py:10: error: Argument "quality" to "take_screenshot" has incompatible type "str"; expected "int"
Found 1 error in 1 file (checked 1 source file)
```

## Sistema de Tipos de Protocolo do Pydoll

O diretório `protocol/` do Pydoll contém definições de tipo abrangentes para todo o Chrome DevTools Protocol:

```
pydoll/protocol/
├── base.py              # Tipos genéricos Command, Response, CDPEvent
├── browser/
│   ├── events.py        # Enum BrowserEvent, TypedDicts de parâmetros de evento
│   ├── methods.py       # Enums de métodos do Browser, TypedDicts de parâmetro/resultado
│   └── types.py         # Tipos do domínio Browser (Bounds, PermissionType, etc.)
├── dom/
│   ├── events.py        # Definições de eventos DOM
│   ├── methods.py       # Definições de comandos DOM
│   └── types.py         # Tipos DOM (Node, BackendNode, etc.)
├── page/
│   ├── events.py        # Eventos de Page (LOAD_EVENT_FIRED, etc.)
│   ├── methods.py       # Métodos de Page (navigate, captureScreenshot, etc.)
│   └── types.py         # Tipos de Page (Frame, ScreenshotFormat, etc.)
├── network/
│   └── ...              # Tipos do domínio Network
└── ...                  # Outros domínios CDP
```

### Exemplo: Fluxo de Tipo Completo

Vamos rastrear um fluxo de tipo completo, do comando à resposta:

```python
# 1. Enum de Método (protocol/page/methods.py)
class PageMethod(str, Enum):
    CAPTURE_SCREENSHOT = 'Page.captureScreenshot'

# 2. TypedDict de Parâmetro (protocol/page/methods.py)
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat
    quality: int
    clip: Viewport

# 3. TypedDict de Resultado (protocol/page/methods.py)
class CaptureScreenshotResult(TypedDict):
    data: str

# 4. Criação do Comando (commands/page_commands.py)
class PageCommands:
    @staticmethod
    def capture_screenshot(
        format: Optional[ScreenshotFormat] = None,
        quality: Optional[int] = None,
        ...
    ) -> Command[CaptureScreenshotParams, CaptureScreenshotResult]:
        return {
            'method': PageMethod.CAPTURE_SCREENSHOT,
            'params': {...}
        }

# 5. Uso na Tab (browser/tab.py)
class Tab:
    async def take_screenshot(...) -> Optional[str]:
        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(...)
        )
        screenshot_data = response['result']['data']  # Totalmente tipado!
        return screenshot_data
```

Cada etapa mantém a informação de tipo, dando a você autocomplete e verificação de tipos por toda parte!

## Melhores Práticas

### 1. Deixe os Tipos do Pydoll Guiarem Você

Não lute contra os tipos, eles estão lá para ajudar:

```python
# Bom: Use kwargs (IDE autocompleta nomes de parâmetros)
element = await tab.find(id='submit-btn')
button = await tab.find(class_name='btn-primary')

# Bom: Use enums onde aplicável
from pydoll.constants import Key
await element.press_keyboard_key(Key.ENTER)

# Evite: Strings mágicas
await element.press_keyboard_key('Enter')  # Sem autocomplete, propenso a erros
```

### 2. Explore os Tipos na Sua IDE

Passe o mouse sobre as variáveis para ver seus tipos:

```python
# Passe o mouse sobre 'response' para ver: Response[CaptureScreenshotResult]
response = await tab._execute_command(PageCommands.capture_screenshot(...))

# Passe o mouse sobre 'data' para ver: str
data = response['result']['data']
```


### 3. Não Anote em Excesso

A inferência de tipos do Python é inteligente, não anote tudo:

```python
# Demais
name: str = "Alice"
count: int = 5
is_active: bool = True

# Deixe o Python inferir literais simples
name = "Alice"
count = 5
is_active = True

# Anote quando o tipo não for óbvio
from typing import Optional

result: Optional[WebElement] = await tab.find(id='missing', raise_exc=False)
```

## Aprenda Mais

Para um entendimento mais profundo do sistema de tipos do Python e do protocolo CDP:

- **[Documentação de typing do Python](https://docs.python.org/3/library/typing.html)**: Referência oficial de typing do Python
- **[PEP 484](https://peps.python.org/pep-0484/)**: A proposta original das dicas de tipo
- **[Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)**: Documentação do CDP
- **[Análise Profunda: CDP](./cdp.md)**: Como o Pydoll implementa o CDP
- **[Referência da API: Protocol](../api/protocol/base.md)**: Definições de tipo de protocolo do Pydoll

O sistema de tipos transforma o Pydoll de uma simples biblioteca de automação em um framework **seguro em tipos, autodocumentado e amigável à IDE**. Ele pega bugs antes que aconteçam e torna a exploração da API muito mais fácil!