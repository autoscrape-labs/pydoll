from typing import List, TypedDict

from pydoll.protocol.network.types import Cookie
from pydoll.protocol.storage.types import (
    RelatedWebsiteSet,
    SharedStorageEntry,
    SharedStorageMetadata,
    TrustToken,
    UsageForType,
)


class GetCookiesResultDict(TypedDict):
    cookies: List[Cookie]


class GetStorageKeyForFrameResultDict(TypedDict):
    storageKey: str


class GetUsageAndQuotaResultDict(TypedDict):
    usage: float
    quota: float
    overrideActive: bool
    usageBreakdown: List[UsageForType]


class ClearTrustTokensResultDict(TypedDict):
    didDeleteTokens: bool


class GetAffectedUrlsForThirdPartyCookieMetadataResultDict(TypedDict):
    matchedUrls: List[str]


class GetInterestGroupDetailsResultDict(TypedDict):
    details: dict


class GetRelatedWebsiteSetsResultDict(TypedDict):
    sets: List[RelatedWebsiteSet]


class GetSharedStorageEntriesResultDict(TypedDict):
    entries: List[SharedStorageEntry]


class GetSharedStorageMetadataResultDict(TypedDict):
    metadata: SharedStorageMetadata


class GetTrustTokensResultDict(TypedDict):
    tokens: List[TrustToken]


class RunBounceTrackingMitigationsResultDict(TypedDict):
    deletedSites: List[str]


class SendPendingAttributionReportsResultDict(TypedDict):
    numSent: int


class GetCookiesResponse(TypedDict):
    result: GetCookiesResultDict


class GetStorageKeyForFrameResponse(TypedDict):
    result: GetStorageKeyForFrameResultDict


class GetUsageAndQuotaResponse(TypedDict):
    result: GetUsageAndQuotaResultDict


class ClearTrustTokensResponse(TypedDict):
    result: ClearTrustTokensResultDict


class GetAffectedUrlsForThirdPartyCookieMetadataResponse(TypedDict):
    result: GetAffectedUrlsForThirdPartyCookieMetadataResultDict


class GetInterestGroupDetailsResponse(TypedDict):
    result: GetInterestGroupDetailsResultDict


class GetRelatedWebsiteSetsResponse(TypedDict):
    result: GetRelatedWebsiteSetsResultDict


class GetSharedStorageEntriesResponse(TypedDict):
    result: GetSharedStorageEntriesResultDict


class GetSharedStorageMetadataResponse(TypedDict):
    result: GetSharedStorageMetadataResultDict


class GetTrustTokensResponse(TypedDict):
    result: GetTrustTokensResultDict


class RunBounceTrackingMitigationsResponse(TypedDict):
    result: RunBounceTrackingMitigationsResultDict


class SendPendingAttributionReportsResponse(TypedDict):
    result: SendPendingAttributionReportsResultDict
