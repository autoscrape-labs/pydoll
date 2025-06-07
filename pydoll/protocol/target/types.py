from typing import NotRequired, TypedDict


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
