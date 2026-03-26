# Plano: API unificada agnóstica de protocolo

## Problema

A API pública expõe conceitos CDP diretamente: tipos, enums, nomes de eventos, métodos de domínio, e parâmetros protocol-specific. Precisamos criar uma camada de tipos e interfaces públicas agnósticas em `pydoll/protocol/types.py` e ajustar toda a API pública pra usar esses tipos.

## 1. Criar `pydoll/protocol/types.py` — tipos públicos unificados

Tipos que a API pública usa, agnósticos de protocolo. Internamente cada browser converte pro formato do seu protocolo.

```python
# pydoll/protocol/types.py

class Header(TypedDict):
    name: str
    value: str

class CookieParam(TypedDict):
    """Cookie pra set_cookies() — campos comuns CDP/BiDi."""
    name: str
    value: str
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[str]  # "Strict" / "Lax" / "None"
    expiry: NotRequired[int]

class Cookie(TypedDict):
    """Cookie retornado por get_cookies()."""
    name: str
    value: str
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: str
    expiry: NotRequired[int]

class WindowBounds(TypedDict, total=False):
    width: int
    height: int
    x: int
    y: int

class BrowserVersion(TypedDict):
    browserName: str
    browserVersion: str
    userAgent: str

class DownloadBehavior(str, Enum):
    ALLOW = 'allow'
    DENY = 'deny'
    DEFAULT = 'default'

class RequestMethod(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
```

## 2. Criar `pydoll/protocol/events.py` — enum de eventos unificado

```python
class Event(str, Enum):
    PAGE_LOADED = 'page.loaded'
    DOM_CONTENT_LOADED = 'page.domContentLoaded'
    REQUEST_SENT = 'network.requestSent'
    RESPONSE_RECEIVED = 'network.responseReceived'
    DIALOG_OPENED = 'dialog.opened'
    DIALOG_CLOSED = 'dialog.closed'
    DOWNLOAD_STARTED = 'download.started'
    DOWNLOAD_COMPLETED = 'download.completed'
    FILE_CHOOSER_OPENED = 'fileChooser.opened'
    FRAME_NAVIGATED = 'frame.navigated'
    CONTEXT_CREATED = 'context.created'
    CONTEXT_DESTROYED = 'context.destroyed'
    ...
```

Cada browser tem um mapa interno `Event → evento nativo`. O `on()` aceita tanto `Event` quanto enum nativo do protocolo.

## 3. Ajustes na API pública do Browser

### Métodos que viram privados

| Método público atual | Ação |
|---|---|
| `enable_page_events()` | `_enable_page_events()` |
| `disable_page_events()` | `_disable_page_events()` |
| `enable_network_events()` | `_enable_network_events()` |
| `disable_network_events()` | `_disable_network_events()` |
| `enable_fetch_events()` | `_enable_fetch_events()` |
| `disable_fetch_events()` | `_disable_fetch_events()` |
| `enable_dom_events()` | `_enable_dom_events()` |
| `disable_dom_events()` | `_disable_dom_events()` |
| `enable_runtime_events()` | `_enable_runtime_events()` |
| `disable_runtime_events()` | `_disable_runtime_events()` |
| `enable_intercept_file_chooser_dialog()` | `_enable_intercept_file_chooser_dialog()` |
| `disable_intercept_file_chooser_dialog()` | `_disable_intercept_file_chooser_dialog()` |
| `get_targets()` | `_get_targets()` (CDP-specific) |
| `get_tab_by_target()` | `_get_tab_by_target()` (CDP-specific) |
| `get_window_id_for_target()` | `_get_window_id_for_target()` (CDP-specific) |
| `get_window_id()` | `_get_window_id()` (interno, usado por set_window_*) |

### Assinaturas que mudam

**`get_version()`**
```python
# Antes: retorna GetVersionResult (CDP) com protocolVersion, product, revision, userAgent, jsVersion
# Depois: retorna BrowserVersion (genérico)
async def get_version(self) -> BrowserVersion:
```

**`set_window_bounds()`**
```python
# Antes: recebe Bounds (CDP) com left, top, width, height, windowState
# Depois: recebe WindowBounds (genérico)
async def set_window_bounds(self, bounds: WindowBounds):
```

**`get_window_id_for_tab()`**
```python
# Mantém público — CDP usa windowId internamente, BiDi usa clientWindow
# Assinatura não muda, implementação difere
```

**`set_download_behavior()`**
```python
# Antes
async def set_download_behavior(self, behavior: DownloadBehavior, download_path=None, browser_context_id=None, events_enabled=False)
# Depois: remove events_enabled, usa DownloadBehavior genérico
async def set_download_behavior(self, behavior: DownloadBehavior, download_path=None, browser_context_id=None)
```

**`set_cookies()`**
```python
# Antes: list[CookieParam] (CDP)
# Depois: list[CookieParam] (genérico de protocol/types.py)
async def set_cookies(self, cookies: list[CookieParam], browser_context_id=None)
```

**`get_cookies()`**
```python
# Antes: retorna list[Cookie] (CDP)
# Depois: retorna list[Cookie] (genérico de protocol/types.py)
async def get_cookies(self, browser_context_id=None) -> list[Cookie]
```

### Interceptação de requests — novo método

```python
async def intercept_requests(
    self,
    callback: Callable[[InterceptedRequest], Awaitable[None]],
    url_patterns: list[str] | None = None,
) -> str:  # retorna intercept_id

async def remove_intercept(self, intercept_id: str):
```

`continue_request`, `fail_request`, `fulfill_request` ficam deprecated no Chrome.

### `InterceptedRequest`

```python
class InterceptedRequest:
    url: str
    method: str
    headers: list[Header]

    async def continue_(self, url=None, method=None, headers=None): ...
    async def fail(self): ...
    async def respond(self, status=200, headers=None, body=None): ...
```

## 4. Ajustes no `on()`

O `on()` aceita:
- `Event` enum unificado (recomendado)
- Enum nativo do protocolo (`PageEvent`, `BrowsingContextEvent`, etc.) — power users

Quando recebe `Event`, resolve pro evento nativo e auto-habilita o domínio/subscription.

## O que NÃO mudar

- `start()`, `stop()`, `close()`, `connect()`
- `new_tab()`, `get_opened_tabs()`
- `delete_all_cookies()`
- `set_download_path()`
- `create_browser_context()`, `delete_browser_context()`, `get_browser_contexts()`
- `set_window_maximized()`, `set_window_minimized()`
- `on()`, `remove_callback()` — interface mantida, aceita novo tipo
- `find()`, `query()` — interface mantida
- `enable_auto_solve_cloudflare_captcha()` — já encapsulado
- `grant_permissions()`, `reset_permissions()`

## Sequência de implementação

1. Criar `pydoll/protocol/types.py` com tipos públicos unificados
2. Criar `pydoll/protocol/events.py` com `Event` enum
3. Criar `InterceptedRequest` em `pydoll/browser/intercepted_request.py`
4. Ajustar API pública do Chrome: usar tipos genéricos, privatizar métodos, implementar `intercept_requests()`, auto-enable no `on()`
5. Ajustar API pública do Firefox: usar tipos genéricos, implementar `intercept_requests()`, `on()` com Event
6. Deprecar métodos antigos com `warnings.warn`
7. Atualizar testes e docs
