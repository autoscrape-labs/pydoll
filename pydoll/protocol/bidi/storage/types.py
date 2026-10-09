from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.network.types import BytesValue, SameSite


class PartitionKey(TypedDict, total=False):
    """Storage partition key."""

    userContext: str
    sourceOrigin: str


class CookieFilter(TypedDict, total=False):
    """Filter for matching cookies."""

    name: str
    value: BytesValue
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: SameSite
    expiry: int


class BrowsingContextPartitionDescriptor(TypedDict):
    """Partition descriptor using a browsing context."""

    type: str  # "context"
    context: BrowsingContext


class StorageKeyPartitionDescriptor(TypedDict, total=False):
    """Partition descriptor using storage key attributes."""

    type: str  # "storageKey"
    userContext: str
    sourceOrigin: str


PartitionDescriptor = BrowsingContextPartitionDescriptor | StorageKeyPartitionDescriptor


class PartialCookie(TypedDict):
    """Cookie data for creating a new cookie."""

    name: str
    value: BytesValue
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[SameSite]
    expiry: NotRequired[int]
