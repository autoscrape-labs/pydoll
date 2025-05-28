from typing import TypedDict

from pydoll.protocol.browser.types import WindowBoundsDict


class GetWindowForTargetResultDict(TypedDict):
    """Result structure for GetWindowForTarget command."""

    windowId: int
    bounds: WindowBoundsDict


class GetVersionResultDict(TypedDict):
    """Result structure for GetVersion command."""

    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str


class GetWindowForTargetResponse(TypedDict):
    """Response structure for GetWindowForTarget command."""

    result: GetWindowForTargetResultDict


class GetVersionResponse(TypedDict):
    """Response structure for GetVersion command."""

    result: GetVersionResultDict
