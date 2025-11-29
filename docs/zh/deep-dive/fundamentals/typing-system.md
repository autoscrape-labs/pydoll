# Python 的类型系统与 Pydoll

Pydoll 广泛利用 Python 的类型系统来提供出色的 IDE 支持、及早发现错误并使 API 自我记录。本指南将解释类型提示的基础知识，以及 Pydoll 如何使用它们来增强您的开发体验。

## 类型提示基础

类型提示是可选的注解，用于指定变量、参数或返回值应该是什么类型的值。它们不影响运行时行为，但能启用强大的工具。

### 简单类型提示

```python
# 基本类型
name: str = "Pydoll"
port: int = 9222
is_headless: bool = False
quality: float = 0.85

# 函数注解
def navigate(url: str, timeout: int = 30) -> bool:
    # ... 实现
    return True
```

### 容器类型

```python
from typing import List, Dict, Optional

# 列表和字典
urls: List[str] = ['https://example.com', 'https://google.com']
headers: Dict[str, str] = {'User-Agent': 'MyBot/1.0'}

# 可选值 (可以是 None)
target_id: Optional[str] = None

# 现代语法 (Python 3.9+)
urls: list[str] = ['https://example.com']
headers: dict[str, str] = {'User-Agent': 'MyBot/1.0'}
```

!!! tip "Python 3.9+ 语法"
    Pydoll 的代码库使用较旧的 `List[]`、`Dict[]` 语法以实现向后兼容，但如果您使用的是 Python 3.9+，您可以在代码中使用小写的 `list[]`、`dict[]`。

## TypedDict：结构化字典

TypedDict 允许您定义具有特定键和值类型的字典结构。这在 Pydoll 的 CDP 协议定义中被 **大量使用**。

### 基本 TypedDict

```python
from typing import TypedDict

class UserInfo(TypedDict):
    name: str
    age: int
    email: str

# IDE 完全知道存在哪些键
user: UserInfo = {
    'name': 'Alice',
    'age': 30,
    'email': 'alice@example.com'
}

# 自动补全功能可用！
print(user['name'])  # IDE 建议: name, age, email
```

### Pydoll 如何使用 TypedDict

Pydoll 将 **每个 CDP 命令、响应和事件** 定义为 TypedDict。这意味着您的 IDE 完全知道哪些属性可用：

```python
# 来自 pydoll/protocol/page/methods.py
class CaptureScreenshotParams(TypedDict, total=False):
    """captureScreenshot 的参数。"""
    format: ScreenshotFormat
    quality: int
    clip: Viewport
    fromSurface: bool
    captureBeyondViewport: bool
    optimizeForSpeed: bool

class CaptureScreenshotResult(TypedDict):
    """captureScreenshot 命令的结果。"""
    data: str
```

当您调用返回 CDP 响应的方法时，您的 IDE 会自动补全响应键：

```python
async def example():
    response = await tab.take_screenshot(as_base64=True)
    
    # IDE 知道这是 CaptureScreenshotResponse
    # 并建议 'result' -> 'data'
    screenshot_data = response['result']['data']  # 完整的自动补全！
```

### 可选字段与必选字段

TypedDict 使用 `NotRequired[]` 支持可选字段：

```python
from typing import TypedDict, NotRequired

# 来自 pydoll/protocol/network/methods.py
class GetCookiesParams(TypedDict):
    """用于检索浏览器 cookie 的参数。"""
    urls: NotRequired[list[str]]  # 此字段是可选的
```

`total=False` 标志使 **所有** 字段都可选：

```python
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat  # 所有字段都可选
    quality: int
    clip: Viewport
```

!!! info "自动补全的魔力"
    当您键入 `response['` 时，您的 IDE 会显示所有可用的键及其类型。这就是 TypedDict 的超能力在起作用！

## Enums (枚举)：类型安全的常量

枚举提供了类型安全的常量，您的 IDE 可以自动补全。Pydoll 广泛使用它们来表示 CDP 的值。

### 基本枚举

```python
from enum import Enum

class ScreenshotFormat(str, Enum):
    JPEG = 'jpeg'
    PNG = 'png'
    WEBP = 'webp'

# IDE 自动补全可用的格式
format = ScreenshotFormat.PNG  # 类型是 ScreenshotFormat
print(format.value)  # 'png'
```

### Pydoll 的枚举用法

```python
from pydoll.constants import Key
from pydoll.protocol.page.types import ScreenshotFormat
from pydoll.protocol.input.types import KeyModifier

# 查找元素 - 使用 kwargs，而非枚举
element = await tab.find(id='submit-btn')
element = await tab.find(class_name='btn-primary')
element = await tab.find(tag_name='button')

# 键盘输入 - IDE 建议所有键
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB)
await element.press_keyboard_key(Key.ESCAPE)

# 修饰键是整数枚举 (用于特殊键)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# 截图格式枚举
await tab.take_screenshot('file.webp', format=ScreenshotFormat.WEBP)
```

!!! tip "枚举自动补全"
    键入 `Key.` 或 `ScreenshotFormat.`，您的 IDE 就会显示所有可用选项。再也不用记忆字符串了！

## 函数重载 (Function Overloads)

重载允许一个函数根据其参数返回不同的类型。Pydoll 使用它来提供精确的类型信息。

### 基本重载示例

```python
from typing import overload

# 重载签名 (不执行)
@overload
def process(data: str) -> str: ...

@overload
def process(data: int) -> int: ...

# 实际实现
def process(data):
    return data * 2

# IDE 知道返回类型
result1 = process("hello")  # 类型: str
result2 = process(42)       # 类型: int
```

### Pydoll 的重载用法

`find()` 和 `query()` 方法根据 `find_all` 参数返回不同的类型：

```python
# 来自 pydoll/elements/mixins/find_elements_mixin.py
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
        # 实现...
```

在您的代码中：

```python
# find_all=False (默认) - IDE 知道返回类型是 WebElement
button = await tab.find(id='submit-btn')
await button.click()  # 单个元素的方法可用！

# find_all=True - IDE 知道返回类型是 list[WebElement]
buttons = await tab.find(class_name='btn', find_all=True)
for btn in buttons:  # IDE 知道这是一个列表！
    await btn.click()

# query() 也是如此
element = await tab.query('#submit-btn')  # 类型: WebElement
elements = await tab.query('.btn', find_all=True)  # 类型: list[WebElement]
```

!!! tip "智能类型推断"
    您的 IDE 会根据 `find_all` 参数自动知道您获取的是单个元素还是列表。无需类型转换或类型断言！

## 泛型 (Generic Types)

泛型就像“类型容器”，可以与不同类型一起工作，同时保留类型信息。可以把它们想象成能适应您放入任何东西的模板。

### 理解泛型：一个简单的类比

想象一个可以装任何东西的 `Box`。没有泛型：

```python
# 没有泛型 - IDE 不知道里面是什么
class Box:
    def __init__(self, content):
        self.content = content
    
    def get(self):
        return self.content

my_box = Box("hello")
item = my_box.get()  # 类型: Unknown - 可能是任何东西！
```

使用泛型：

```python
from typing import Generic, TypeVar

T = TypeVar('T')  # T 是一个 "类型占位符"

class Box(Generic[T]):
    def __init__(self, content: T):
        self.content = content
    
    def get(self) -> T:
        return self.content

# 现在 IDE 完全知道每个盒子里装的是什么
string_box: Box[str] = Box("hello")
item1 = string_box.get()  # 类型: str

number_box: Box[int] = Box(42)
item2 = number_box.get()  # 类型: int

# List 是一个内置的泛型
numbers: list[int] = [1, 2, 3]  # 包含 int 的列表
names: list[str] = ["Alice", "Bob"]  # 包含 str 的列表
```

!!! tip "泛型简化了类型提示"
    泛型让您只需编写一个可重用的 `list[T]`，它能适应您放入的任何东西，而无需为每种可能的列表类型编写 `Union[List[str], List[int], List[float], ...]`。

### 现实世界中的泛型示例

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Response(Generic[T]):
    """一个通用的 API 响应包装器。"""
    def __init__(self, data: T, status: int):
        self.data = data
        self.status = status
    
    def get_data(self) -> T:
        return self.data

# 每个响应都保留了其数据类型
user_response: Response[dict] = Response({"name": "Alice"}, 200)
user_data = user_response.get_data()  # 类型: dict

count_response: Response[int] = Response(42, 200)
count = count_response.get_data()  # 类型: int
```

### Pydoll 如何使用泛型

Pydoll 的 CDP 命令系统使用泛型来确保响应类型与命令匹配：

```python
# 来自 pydoll/protocol/base.py
from typing import Generic, TypeVar

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')

class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """所有命令的基础结构。"""
    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]

class Response(TypedDict, Generic[T_CommandResponse]):
    """所有响应的基础结构。"""
    id: int
    result: T_CommandResponse
```

这意味着当您执行一个命令时，响应类型会被自动推断：

```python
# PageCommands.navigate 返回 Command[NavigateParams, NavigateResult]
command = PageCommands.navigate('https://example.com')

# ConnectionHandler.execute_command 保留了泛型类型
response = await connection_handler.execute_command(command)

# IDE 知道 response['result'] 是 NavigateResult (不仅仅是 "any dict")
frame_id = response['result']['frameId']  # 自动补全可用！
loader_id = response['result']['loaderId']  # 所有字段都已知！
```

!!! info "为什么泛型在 Pydoll 中很重要"
    没有泛型，每个 CDP 响应的类型都只是 `dict[str, Any]`，您将失去所有的自动补全功能。有了泛型，IDE 能根据您发送的命令知道每个响应的确切结构。

## 联合类型 (Union Types)

联合 (Union) 表示值可能是多种类型之一：

```python
from typing import Union

# 可以是字符串或整数
identifier: Union[str, int] = "user-123"
identifier = 456  # 也有效

# 现代语法 (Python 3.10+)
identifier: str | int = "user-123"
```

### Pydoll 的联合类型用法

```python
# 文件路径可以是字符串或 Path 对象
from pathlib import Path

async def upload_file(files: Union[str, Path, list[Union[str, Path]]]):
    # 处理多种输入类型
    pass

# 所有这些都有效：
await tab.expect_file_chooser('/path/to/file.txt')
await tab.expect_file_chooser(Path('/path/to/file.txt'))
await tab.expect_file_chooser(['/file1.txt', Path('/file2.txt')])
```

## Pydoll 中的实际好处

### 1. 智能自动补全

您的 IDE 会建议可用的键、方法和值：

```python
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.network.types import ResourceType
from pydoll.protocol.input.types import KeyModifier
from pydoll.constants import Key

# 自动补全事件名称
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
await tab.on(PageEvent.JAVASCRIPT_DIALOG_OPENING, callback)

# 自动补全资源类型
await tab.enable_fetch_events(resource_type=ResourceType.XHR)
await tab.enable_fetch_events(resource_type=ResourceType.DOCUMENT)

# 自动补全按键
await element.press_keyboard_key(Key.ENTER)
await element.press_keyboard_key(Key.TAB, modifiers=KeyModifier.SHIFT)

# 自动补全 find() 中的 kwargs
element = await tab.find(id='submit-btn')  # IDE 建议: id, class_name, tag_name, 等.
```

### 2. 及早发现错误

像 mypy 或 Pylance 这样的类型检查器会在运行时之前捕获错误：

```python
# 类型检查器会捕获这个
await tab.take_screenshot('file.png', quality='high')  # 错误: quality 必须是 int

# 类型检查器会捕获这个
event = await tab.find(id='button')
await tab.on(event, callback)  # 错误: event 是 WebElement, 不是 str

# 正确的
await tab.take_screenshot('file.png', quality=90)
await tab.on(PageEvent.LOAD_EVENT_FIRED, callback)
```

### 3. 自我记录的代码

类型可作为内联文档：

```python
# 您立即知道每个参数期望什么
async def take_screenshot(
    self,
    path: Optional[str] = None,
    quality: int = 100,
    beyond_viewport: bool = False,
    as_base64: bool = False,
) -> Optional[str]:
    pass
```

### 4. CDP 响应导航

自信地浏览复杂的 CDP 响应：

```python
# 来自 pydoll/protocol/browser/methods.py
class GetVersionResult(TypedDict):
    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str

# 在您的代码中
version_info = await browser.get_version()

# IDE 建议所有可用的键
print(version_info['product'])         # 自动补全！
print(version_info['userAgent'])       # 自动补全！
print(version_info['protocolVersion']) # 自动补全！
```

## 类型检查您的代码

### 使用 Pylance (VS Code)

Pylance 在 VS Code 中提供实时类型检查：

1.  安装 Pylance 扩展
2.  在设置中设置类型检查模式：

```json
{
    "python.analysis.typeCheckingMode": "basic"  // 或 "strict"
}
```

现在您可以获得即时反馈：

```python
from pydoll.browser.chromium import Chrome

async def main():
    async with Chrome() as browser:
        tab = await browser.start()
        
        # 当您键入时，Pylance 会显示参数类型
        await tab.go_to('https://example.com', timeout=30)
        
        # Pylance 会对错误的类型发出警告
        await tab.take_screenshot(quality='high')  # 警告！
```

### 使用 mypy

运行 mypy 来检查您的整个项目：

```bash
pip install mypy
mypy your_script.py
```

示例输出：

```
your_script.py:10: error: Argument "quality" to "take_screenshot" has incompatible type "str"; expected "int"
Found 1 error in 1 file (checked 1 source file)
```

## Pydoll 的协议类型系统

Pydoll 的 `protocol/` 目录包含整个 Chrome DevTools 协议的全面类型定义：

```
pydoll/protocol/
├── base.py              # 泛型 Command, Response, CDPEvent 类型
├── browser/
│   ├── events.py        # BrowserEvent 枚举, 事件参数 TypedDicts
│   ├── methods.py       # Browser 方法枚举, 参数/结果 TypedDicts
│   └── types.py         # Browser 域类型 (Bounds, PermissionType, 等.)
├── dom/
│   ├── events.py        # DOM 事件定义
│   ├── methods.py       # DOM 命令定义
│   └── types.py         # DOM 类型 (Node, BackendNode, 等.)
├── page/
│   ├── events.py        # Page 事件 (LOAD_EVENT_FIRED, 等.)
│   ├── methods.py       # Page 方法 (navigate, captureScreenshot, 等.)
│   └── types.py         # Page 类型 (Frame, ScreenshotFormat, 等.)
├── network/
│   └── ...              # Network 域类型
└── ...                  # 其他 CDP 域
```

### 示例：完整的类型流

让我们追踪一个从命令到响应的完整类型流：

```python
# 1. 方法枚举 (protocol/page/methods.py)
class PageMethod(str, Enum):
    CAPTURE_SCREENSHOT = 'Page.captureScreenshot'

# 2. 参数 TypedDict (protocol/page/methods.py)
class CaptureScreenshotParams(TypedDict, total=False):
    format: ScreenshotFormat
    quality: int
    clip: Viewport

# 3. 结果 TypedDict (protocol/page/methods.py)
class CaptureScreenshotResult(TypedDict):
    data: str

# 4. 命令创建 (commands/page_commands.py)
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

# 5. 在 Tab 中使用 (browser/tab.py)
class Tab:
    async def take_screenshot(...) -> Optional[str]:
        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(...)
        )
        screenshot_data = response['result']['data']  # 完全类型化！
        return screenshot_data
```

每一步都保留了类型信息，让您在整个过程中都能获得自动补全和类型检查！

## 最佳实践

### 1. 让 Pydoll 的类型引导您

不要抗拒类型，它们是来帮助您的：

```python
# 好的：使用 kwargs (IDE 自动补全参数名称)
element = await tab.find(id='submit-btn')
button = await tab.find(class_name='btn-primary')

# 好的：在适用的地方使用枚举
from pydoll.constants import Key
await element.press_keyboard_key(Key.ENTER)

# 避免：魔法字符串
await element.press_keyboard_key('Enter')  # 没有自动补全，容易出错
```

### 2. 在您的 IDE 中探索类型

将鼠标悬停在变量上以查看其类型：

```python
# 悬停在 'response' 上查看: Response[CaptureScreenshotResult]
response = await tab._execute_command(PageCommands.capture_screenshot(...))

# 悬停在 'data' 上查看: str
data = response['result']['data']
```


### 3. 不要过度注解

Python 的类型推断很智能，不要注解所有东西：

```python
# 过多
name: str = "Alice"
count: int = 5
is_active: bool = True

# 让 Python 推断简单的字面量
name = "Alice"
count = 5
is_active = True

# 当类型不明显时进行注解
from typing import Optional

result: Optional[WebElement] = await tab.find(id='missing', raise_exc=False)
```

## 了解更多

要更深入地了解 Python 的类型系统和 CDP 协议：

- **[Python typing 文档](https://docs.python.org/3/library/typing.html)**：官方 Python 类型参考
- **[PEP 484](https://peps.python.org/pep-0484/)**：原始的类型提示提案
- **[Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)**：CDP 文档
- **[深入探讨：CDP](./cdp.md)**：Pydoll 如何实现 CDP
- **[API 参考：Protocol](../api/protocol/base.md)**：Pydoll 的协议类型定义

类型系统将 Pydoll 从一个简单的自动化库转变为一个 **类型安全、自我记录、IDE 友好** 的框架。它能在错误发生之前捕获它们，并使探索 API 变得轻而易举！