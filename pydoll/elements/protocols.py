from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ShadowRootProtocol(Protocol):
    """Contract for shadow root finders across protocols (CDP, BiDi).

    Covers only what both backends implement; ``mode`` is the CDP
    ``ShadowRootType`` (a ``str`` enum) or the BiDi mode string.
    """

    @property
    def mode(self) -> str: ...

    async def inner_html(self) -> str: ...

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


@runtime_checkable
class WebElementProtocol(Protocol):
    """Contract for web element implementations across protocols (CDP, BiDi).

    The portable element surface of pydoll 3.0: cached-attribute properties,
    async inspection methods (``text()``, ``inner_html()``, ``bounds()``),
    trusted input (``click``, ``hover``, ``double_click``, ``type_text``),
    state checks and waits, and ``evaluate()`` for JavaScript that returns a
    value. Backend-specific extras (CDP ``execute_script`` / ``query_script`` /
    ``iframe_context``) are deliberately left out.
    """

    @property
    def attributes(self) -> dict[str, str]: ...

    @property
    def tag_name(self) -> str | None: ...

    @property
    def id(self) -> str | None: ...

    @property
    def class_name(self) -> str | None: ...

    @property
    def value(self) -> str | None: ...

    @property
    def is_iframe(self) -> bool: ...

    @property
    def is_enabled(self) -> bool: ...

    async def text(self) -> str: ...

    async def bounds(self) -> object: ...

    async def inner_html(self) -> str: ...

    def get_attribute(self, name: str) -> str | None: ...

    async def get_bounds_using_js(self) -> dict[str, int]: ...

    async def get_parent_element(self) -> WebElementProtocol: ...

    async def get_shadow_root(self, timeout: float = 0) -> ShadowRootProtocol: ...

    async def get_children_elements(
        self,
        max_depth: int = 1,
        tag_filter: list[str] = ...,
        raise_exc: bool = False,
    ) -> Sequence[WebElementProtocol]: ...

    async def get_siblings_elements(
        self,
        tag_filter: list[str] = ...,
        raise_exc: bool = False,
    ) -> Sequence[WebElementProtocol]: ...

    async def take_screenshot(
        self,
        path: str | Path | None = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> str | None: ...

    async def scroll_into_view(self) -> None: ...

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        is_hidden: bool = False,
        is_detached: bool = False,
        is_enabled: bool = False,
        timeout: float = 0,
    ) -> None: ...

    async def click_using_js(self) -> None: ...

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0,
        humanize: bool = False,
    ) -> None: ...

    async def hover(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        humanize: bool = False,
    ) -> None: ...

    async def double_click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        humanize: bool = False,
    ) -> None: ...

    async def focus(self) -> None: ...

    async def clear(self) -> None: ...

    async def insert_text(self, text: str) -> None: ...

    async def set_input_files(self, files: str | Path | list[str | Path]) -> None: ...

    async def type_text(self, text: str, humanize: bool = False) -> None: ...

    async def is_editable(self) -> bool: ...

    async def is_visible(self) -> bool: ...

    async def is_detached(self) -> bool: ...

    async def is_on_top(self) -> bool: ...

    async def is_interactable(self) -> bool: ...

    async def evaluate(self, script: str, *args: object) -> object: ...

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
