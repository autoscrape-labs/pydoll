from typing import List, NotRequired, TypedDict

from pydoll.constants import StorageType


class StorageBucket(TypedDict):
    storageKey: str
    name: NotRequired[str]


class RelatedWebsiteSet(TypedDict):
    primarySites: List[str]
    associatedSites: List[str]
    serviceSites: List[str]


class UsageForType(TypedDict):
    storageType: StorageType
    usage: float


class SharedStorageEntry(TypedDict):
    key: str
    value: str


class SharedStorageMetadata(TypedDict):
    creationTime: float
    length: int
    remainingBudget: float
    bytesUsed: int


class TrustToken(TypedDict):
    issuerOrigin: str
    count: float
