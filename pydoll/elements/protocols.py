from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Optional, Protocol, Union, runtime_checkable


@runtime_checkable
class ShadowRootProtocol(Protocol):
    """Contract for shadow root finders across protocols (CDP, BiDi)."""

    @property
    def mode(self) -> str: ...

    @property
    async def inner_html(self) -> str: ...

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
        **attributes: dict[str, str],
    ) -> Union[WebElementProtocol, Sequence[WebElementProtocol], None]: ...

    async def query(
        self,
        expression: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> Union[WebElementProtocol, Sequence[WebElementProtocol], None]: ...


@runtime_checkable
class WebElementProtocol(Protocol):
    """Contract for web element implementations across protocols (CDP, BiDi)."""

    @property
    def attributes(self) -> dict[str, str]: ...

    @property
    def tag_name(self) -> Optional[str]: ...

    @property
    def id(self) -> Optional[str]: ...

    @property
    def class_name(self) -> Optional[str]: ...

    @property
    def value(self) -> Optional[str]: ...

    @property
    def is_iframe(self) -> bool: ...

    @property
    def is_enabled(self) -> bool: ...

    @property
    async def text(self) -> str: ...

    @property
    async def bounds(self) -> object: ...

    @property
    async def inner_html(self) -> str: ...

    def get_attribute(self, name: str) -> Optional[str]: ...

    async def get_bounds_using_js(self) -> dict[str, int]: ...

    async def get_parent_element(self) -> WebElementProtocol: ...

    async def get_shadow_root(self) -> ShadowRootProtocol: ...

    async def get_children_elements(
        self,
        max_depth: int = 1,
        tag_filter: Optional[list[str]] = None,
    ) -> Sequence[WebElementProtocol]: ...

    async def get_siblings_elements(
        self,
        tag_filter: Optional[list[str]] = None,
    ) -> Sequence[WebElementProtocol]: ...

    async def take_screenshot(
        self,
        path: Optional[Union[str, Path]] = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> Optional[str]: ...

    async def scroll_into_view(self) -> None: ...

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        timeout: int = 0,
    ) -> None: ...

    async def click_using_js(self) -> None: ...

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0.1,
        humanize: bool = False,
    ) -> None: ...

    async def focus(self) -> None: ...

    async def clear(self) -> None: ...

    async def insert_text(self, text: str) -> None: ...

    async def set_input_files(
        self, files: Union[str, Path, list[Union[str, Path]]]
    ) -> None: ...

    async def type_text(
        self,
        text: str,
        humanize: bool = False,
        interval: float = 0.1,
    ) -> None: ...

    async def is_editable(self) -> bool: ...

    async def is_visible(self) -> bool: ...

    async def is_on_top(self) -> bool: ...

    async def is_interactable(self) -> bool: ...

    async def execute_script(self, script: str) -> object: ...

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
        **attributes: dict[str, str],
    ) -> Union[WebElementProtocol, Sequence[WebElementProtocol], None]: ...

    async def query(
        self,
        expression: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> Union[WebElementProtocol, Sequence[WebElementProtocol], None]: ...
