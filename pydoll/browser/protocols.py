from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydoll.constants import PageLoadState


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
