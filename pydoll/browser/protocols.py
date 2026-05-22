from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Optional, Protocol, TypeAlias, TypeVar, runtime_checkable

from pydoll.constants import PageLoadState
from pydoll.protocol.events import Event
from pydoll.protocol.types import (
    BrowserVersion,
    Cookie,
    CookieParam,
    DownloadBehavior,
    Permission,
    WindowBounds,
)

if TYPE_CHECKING:
    from pydoll.browser.intercepted_request import InterceptedRequest

T_Tab = TypeVar('T_Tab')

BrowserEventCallback: TypeAlias = (
    Callable[[dict], object] | Callable[[dict], Awaitable[object]]
)
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


class BrowserOptionsManagerProtocol(Protocol):
    """Contract for browser options manager implementations."""

    def initialize_options(self) -> OptionsProtocol: ...

    def add_default_arguments(self) -> None: ...


@runtime_checkable
class BrowserProtocol(Protocol[T_Tab]):
    """Portable browser-level contract shared by browser implementations.

    This protocol intentionally models only the cross-browser surface. Browser-specific
    protocol escape hatches and advanced CDP/BiDi methods should live on the concrete
    browser classes instead of being added here.
    """

    options: OptionsProtocol

    async def start(self, headless: bool = False) -> T_Tab: ...

    async def stop(self) -> None: ...

    async def close(self) -> None: ...

    async def connect(self, ws_address: str) -> T_Tab: ...

    async def create_browser_context(
        self,
        proxy_server: Optional[str] = None,
        proxy_bypass_list: Optional[str] = None,
    ) -> str: ...

    async def delete_browser_context(self, browser_context_id: str) -> None: ...

    async def get_browser_contexts(self) -> list[str]: ...

    async def get_opened_tabs(self) -> list[T_Tab]: ...

    async def new_tab(
        self,
        url: str = '',
        browser_context_id: Optional[str] = None,
    ) -> T_Tab: ...

    async def get_version(self) -> BrowserVersion: ...

    async def set_download_path(
        self,
        path: str,
        browser_context_id: Optional[str] = None,
    ) -> None: ...

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ) -> None: ...

    async def delete_all_cookies(
        self,
        browser_context_id: Optional[str] = None,
    ) -> None: ...

    async def set_cookies(
        self,
        cookies: list[CookieParam],
        browser_context_id: Optional[str] = None,
    ) -> None: ...

    async def get_cookies(
        self,
        browser_context_id: Optional[str] = None,
    ) -> list[Cookie]: ...

    async def set_window_maximized(self) -> None: ...

    async def set_window_minimized(self) -> None: ...

    async def set_window_bounds(self, bounds: WindowBounds) -> None: ...

    async def grant_permissions(
        self,
        permissions: Sequence[Permission],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ) -> None: ...

    async def reset_permissions(
        self,
        browser_context_id: Optional[str] = None,
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
        url_patterns: Optional[list[str]] = None,
    ) -> str: ...

    async def remove_intercept(self, intercept_id: str) -> None: ...
