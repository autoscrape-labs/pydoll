from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.browser.types import BrowserContextID
from pydoll.protocol.cdp.page.types import FrameId

TargetID = str
SessionID = str


class TargetInfo(TypedDict):
    targetId: TargetID
    type: str
    title: str
    url: str
    attached: bool
    openerId: NotRequired[TargetID]
    canAccessOpener: NotRequired[bool]
    openerFrameId: NotRequired[FrameId]
    browserContextId: NotRequired[BrowserContextID]
    subtype: NotRequired[str]


class FilterEntry(TypedDict, total=False):
    """A filter used by target query/discovery/auto-attach operations."""

    exclude: bool
    type: str


TargetFilter = list[FilterEntry]


class RemoteLocation(TypedDict):
    host: str
    port: int
