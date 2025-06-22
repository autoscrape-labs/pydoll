from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from typing_extensions import TypedDict


from pydoll.constants import WindowState


class WindowBoundsDict(TypedDict):
    """Structure for window bounds parameters."""

    windowState: WindowState
    width: NotRequired[int]
    height: NotRequired[int]
    x: NotRequired[int]
    y: NotRequired[int]
