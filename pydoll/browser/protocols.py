from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

from pydoll.constants import PageLoadState
from pydoll.elements.protocols import ShadowRootProtocol, WebElementProtocol
from pydoll.interactions.keyboard import Keyboard
from pydoll.interactions.mouse import Mouse
from pydoll.interactions.scroll import Scroll
from pydoll.protocol.cdp.browser.methods import GetVersionResult
from pydoll.protocol.cdp.browser.types import Bounds, DownloadBehavior, PermissionType
from pydoll.protocol.cdp.network.types import Cookie, CookieParam
from pydoll.protocol.events import Event
from pydoll.protocol.types import Header
from pydoll.utils import UrlPattern

if TYPE_CHECKING:
    from pydoll.browser.intercepted_request import InterceptedRequest
    from pydoll.browser.requests.response import Response

T_Tab = TypeVar('T_Tab')

BrowserEventCallback: TypeAlias = Callable[[dict], object] | Callable[[dict], Awaitable[object]]
InterceptCallback: TypeAlias = Callable[['InterceptedRequest'], Awaitable[object]]


@runtime_checkable
class OptionsProtocol(Protocol):
    """Contract for browser options across all browser implementations."""

    @property
    def arguments(self) -> list[str]: ...

    @property
    def binary_location(self) -> str: ...

    @property
    def start_timeout(self) -> int: ...

    def add_argument(self, argument: str) -> None: ...

    @property
    def browser_preferences(self) -> dict: ...

    @property
    def headless(self) -> bool: ...

    @headless.setter
    def headless(self, headless: bool) -> None: ...

    @property
    def page_load_state(self) -> PageLoadState: ...

    @page_load_state.setter
    def page_load_state(self, state: PageLoadState) -> None: ...

    @property
    def user_agent(self) -> str | None: ...

    @user_agent.setter
    def user_agent(self, user_agent: str | None) -> None: ...


class BrowserOptionsManagerProtocol(Protocol):
    """Contract for browser options manager implementations."""

    def initialize_options(self) -> OptionsProtocol: ...

    def add_default_arguments(self) -> None: ...


@runtime_checkable
class BrowserProtocol(Protocol[T_Tab]):
    """Portable browser-level contract shared by browser implementations.

    Models only the cross-browser surface, typed with the CDP shapes the Chromium
    backend returns natively (GetVersionResult, Cookie, Bounds, PermissionType,
    DownloadBehavior); the BiDi backend converts to and from them. Browser-specific
    escape hatches (``execute_command`` with a protocol-typed command, the CDP Fetch
    helpers, ``get_targets``) live on the concrete browser classes.
    """

    options: OptionsProtocol

    async def start(self) -> T_Tab: ...

    async def stop(self) -> None: ...

    async def close(self) -> None: ...

    async def connect(self, ws_address: str) -> T_Tab: ...

    async def create_browser_context(
        self,
        proxy_server: str | None = None,
        proxy_bypass_list: str | None = None,
    ) -> str: ...

    async def delete_browser_context(self, browser_context_id: str) -> None: ...

    async def get_browser_contexts(self) -> list[str]: ...

    async def get_opened_tabs(self) -> list[T_Tab]: ...

    async def new_tab(
        self,
        url: str = '',
        browser_context_id: str | None = None,
    ) -> T_Tab: ...

    async def get_version(self) -> GetVersionResult: ...

    async def set_download_path(
        self,
        path: str,
        browser_context_id: str | None = None,
    ) -> None: ...

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: str | None = None,
        browser_context_id: str | None = None,
    ) -> None: ...

    async def delete_all_cookies(
        self,
        browser_context_id: str | None = None,
    ) -> None: ...

    async def set_cookies(
        self,
        cookies: list[CookieParam],
        browser_context_id: str | None = None,
    ) -> None: ...

    async def get_cookies(
        self,
        browser_context_id: str | None = None,
    ) -> list[Cookie]: ...

    async def set_window_maximized(self) -> None: ...

    async def set_window_minimized(self) -> None: ...

    async def set_window_bounds(self, bounds: Bounds) -> None: ...

    async def grant_permissions(
        self,
        permissions: list[PermissionType],
        origin: str | None = None,
        browser_context_id: str | None = None,
    ) -> None: ...

    async def reset_permissions(
        self,
        browser_context_id: str | None = None,
    ) -> None: ...

    async def on(
        self,
        event_name: Event | str,
        callback: BrowserEventCallback,
        temporary: bool = False,
    ) -> int: ...

    async def remove_callback(self, callback_id: int) -> None: ...

    async def intercept_requests(
        self,
        callback: InterceptCallback,
        url_patterns: list[str] | None = None,
    ) -> str: ...

    async def remove_intercept(self, intercept_id: str) -> None: ...


@runtime_checkable
class DownloadHandleProtocol(Protocol):
    """Handle to a download captured by ``Tab.expect_download`` (CDP and BiDi).

    Yielded inside the ``expect_download`` block to await completion and read the
    downloaded bytes, regardless of the underlying protocol.
    """

    @property
    def file_path(self) -> str | None: ...

    async def wait_started(self, timeout: float | None = None) -> None: ...

    async def wait_finished(self, timeout: float | None = None) -> None: ...

    async def read_bytes(self) -> bytes: ...

    async def read_base64(self) -> str: ...


@runtime_checkable
class RequestProtocol(Protocol):
    """Portable HTTP client that runs in a tab's fetch context (CDP and BiDi).

    Mirrors the requests-library surface; every call reuses the browser's cookies
    and session and returns a Response.
    """

    async def request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        data: dict | list | tuple | str | bytes | None = None,
        json: dict[str, Any] | None = None,
        headers: list[Header] | None = None,
        **kwargs,
    ) -> Response: ...

    async def get(self, url: str, params: dict[str, str] | None = None, **kwargs) -> Response: ...

    async def post(
        self,
        url: str,
        data: dict | list | tuple | str | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs,
    ) -> Response: ...

    async def put(
        self,
        url: str,
        data: dict | list | tuple | str | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs,
    ) -> Response: ...

    async def patch(
        self,
        url: str,
        data: dict | list | tuple | str | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs,
    ) -> Response: ...

    async def delete(self, url: str, **kwargs) -> Response: ...

    async def head(self, url: str, **kwargs) -> Response: ...

    async def options(self, url: str, **kwargs) -> Response: ...


@runtime_checkable
class TabProtocol(Protocol):
    """Portable tab-level contract shared by Tab (CDP) and BiDiTab (BiDi).

    Models only the cross-protocol surface. Protocol-specific features live on the
    concrete tab classes and are intentionally absent here: CDP Fetch control
    (continue/fail/fulfill_request), OOPIF iframes (get_frame), network introspection
    (get_network_logs), the Cloudflare Turnstile helper, save_bundle, the extractor
    (extract/extract_all), the ``expect_request``/``expect_response``/
    ``wait_for_network_idle`` waits (whose handles carry protocol-shaped events),
    and the ``execute_command`` escape hatch (typed per protocol).
    """

    @property
    def mouse(self) -> Mouse: ...

    @property
    def keyboard(self) -> Keyboard: ...

    @property
    def scroll(self) -> Scroll: ...

    @property
    def request(self) -> RequestProtocol: ...

    async def current_url(self) -> str: ...

    async def page_source(self) -> str: ...

    async def title(self) -> str: ...

    async def go_to(self, url: str, timeout: int = 300) -> None: ...

    async def refresh(self, ignore_cache: bool = False) -> None: ...

    async def close(self) -> None: ...

    async def bring_to_front(self) -> None: ...

    async def useragent_override(self, user_agent: str) -> None: ...

    async def find(
        self,
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        **attributes: dict[str, str],
    ) -> WebElementProtocol | Sequence[WebElementProtocol] | None: ...

    async def query(
        self,
        expression: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> WebElementProtocol | Sequence[WebElementProtocol] | None: ...

    async def find_shadow_roots(
        self, deep: bool = False, timeout: float = 0
    ) -> Sequence[ShadowRootProtocol]: ...

    async def evaluate(self, script: str, *args: object) -> object: ...

    async def wait_for_url(self, url: UrlPattern, timeout: float = 30) -> str: ...

    async def wait_for_script(self, script: str, timeout: float = 30) -> Any: ...

    async def wait_for_absence(
        self,
        id: str | None = None,
        class_name: str | None = None,
        name: str | None = None,
        tag_name: str | None = None,
        text: str | None = None,
        timeout: float = 30,
        **attributes: str,
    ) -> None: ...

    def expect_navigation(
        self, url: UrlPattern | None = None, timeout: float = 30
    ) -> AbstractAsyncContextManager[None]: ...

    async def take_screenshot(
        self,
        path: str | Path | None = None,
        quality: int = 100,
        beyond_viewport: bool = False,
        as_base64: bool = False,
    ) -> str | None: ...

    async def print_to_pdf(
        self,
        path: str | Path | None = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> str | None: ...

    async def get_cookies(self) -> list[Cookie]: ...

    async def set_cookies(self, cookies: list[CookieParam]) -> None: ...

    async def delete_all_cookies(self) -> None: ...

    async def has_dialog(self) -> bool: ...

    async def get_dialog_message(self) -> str: ...

    async def handle_dialog(self, accept: bool, prompt_text: str | None = None) -> None: ...

    def expect_file_chooser(
        self, files: str | Path | list[str | Path]
    ) -> AbstractAsyncContextManager[None]: ...

    def expect_download(
        self,
        keep_file_at: str | Path | None = None,
        timeout: float | None = None,
    ) -> AbstractAsyncContextManager[DownloadHandleProtocol]: ...

    async def on(
        self,
        event_name: Event | str,
        callback: BrowserEventCallback,
        temporary: bool = False,
    ) -> int: ...

    async def remove_callback(self, callback_id: int) -> None: ...

    async def clear_callbacks(self) -> None: ...
