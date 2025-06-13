from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class RemoteLocation(TypedDict):
    host: str
    port: int


class TargetInfo(TypedDict):
    targetId: str
    type: str
    title: str
    url: str
    attached: bool
    openerId: NotRequired[str]
    canAccessOpener: bool
    openerFrameId: NotRequired[str]
    browserContextId: NotRequired[str]
    subtype: NotRequired[str]
