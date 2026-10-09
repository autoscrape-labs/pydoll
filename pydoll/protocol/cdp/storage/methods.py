from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.browser.types import BrowserContextID
from pydoll.protocol.cdp.network.types import Cookie, CookieParam
from pydoll.protocol.cdp.page.types import FrameId
from pydoll.protocol.cdp.storage.types import (
    RelatedWebsiteSet,
    SerializedStorageKey,
    SharedStorageEntry,
    SharedStorageMetadata,
    StorageBucket,
    TrustTokens,
    UsageForType,
)


class StorageMethod(str, Enum):
    CLEAR_COOKIES = 'Storage.clearCookies'
    CLEAR_DATA_FOR_ORIGIN = 'Storage.clearDataForOrigin'
    CLEAR_DATA_FOR_STORAGE_KEY = 'Storage.clearDataForStorageKey'
    GET_COOKIES = 'Storage.getCookies'
    GET_STORAGE_KEY_FOR_FRAME = 'Storage.getStorageKeyForFrame'
    GET_USAGE_AND_QUOTA = 'Storage.getUsageAndQuota'
    SET_COOKIES = 'Storage.setCookies'
    SET_PROTECTED_AUDIENCE_K_ANONYMITY = 'Storage.setProtectedAudienceKAnonymity'
    TRACK_CACHE_STORAGE_FOR_ORIGIN = 'Storage.trackCacheStorageForOrigin'
    TRACK_CACHE_STORAGE_FOR_STORAGE_KEY = 'Storage.trackCacheStorageForStorageKey'
    TRACK_INDEXED_DB_FOR_ORIGIN = 'Storage.trackIndexedDBForOrigin'
    TRACK_INDEXED_DB_FOR_STORAGE_KEY = 'Storage.trackIndexedDBForStorageKey'
    UNTRACK_CACHE_STORAGE_FOR_ORIGIN = 'Storage.untrackCacheStorageForOrigin'
    UNTRACK_CACHE_STORAGE_FOR_STORAGE_KEY = 'Storage.untrackCacheStorageForStorageKey'
    UNTRACK_INDEXED_DB_FOR_ORIGIN = 'Storage.untrackIndexedDBForOrigin'
    UNTRACK_INDEXED_DB_FOR_STORAGE_KEY = 'Storage.untrackIndexedDBForStorageKey'
    CLEAR_SHARED_STORAGE_ENTRIES = 'Storage.clearSharedStorageEntries'
    CLEAR_TRUST_TOKENS = 'Storage.clearTrustTokens'
    DELETE_SHARED_STORAGE_ENTRY = 'Storage.deleteSharedStorageEntry'
    DELETE_STORAGE_BUCKET = 'Storage.deleteStorageBucket'
    GET_AFFECTED_URLS_FOR_THIRD_PARTY_COOKIE_METADATA = (
        'Storage.getAffectedUrlsForThirdPartyCookieMetadata'
    )
    GET_INTEREST_GROUP_DETAILS = 'Storage.getInterestGroupDetails'
    GET_RELATED_WEBSITE_SETS = 'Storage.getRelatedWebsiteSets'
    GET_SHARED_STORAGE_ENTRIES = 'Storage.getSharedStorageEntries'
    GET_SHARED_STORAGE_METADATA = 'Storage.getSharedStorageMetadata'
    GET_TRUST_TOKENS = 'Storage.getTrustTokens'
    OVERRIDE_QUOTA_FOR_ORIGIN = 'Storage.overrideQuotaForOrigin'
    RESET_SHARED_STORAGE_BUDGET = 'Storage.resetSharedStorageBudget'
    RUN_BOUNCE_TRACKING_MITIGATIONS = 'Storage.runBounceTrackingMitigations'
    SEND_PENDING_ATTRIBUTION_REPORTS = 'Storage.sendPendingAttributionReports'
    SET_ATTRIBUTION_REPORTING_LOCAL_TESTING_MODE = 'Storage.setAttributionReportingLocalTestingMode'
    SET_ATTRIBUTION_REPORTING_TRACKING = 'Storage.setAttributionReportingTracking'
    SET_INTEREST_GROUP_AUCTION_TRACKING = 'Storage.setInterestGroupAuctionTracking'
    SET_INTEREST_GROUP_TRACKING = 'Storage.setInterestGroupTracking'
    SET_SHARED_STORAGE_ENTRY = 'Storage.setSharedStorageEntry'
    SET_SHARED_STORAGE_TRACKING = 'Storage.setSharedStorageTracking'
    SET_STORAGE_BUCKET_TRACKING = 'Storage.setStorageBucketTracking'


class GetStorageKeyForFrameParams(TypedDict):
    frameId: FrameId


class GetStorageKeyForFrameResult(TypedDict):
    storageKey: SerializedStorageKey


class ClearDataForOriginParams(TypedDict):
    origin: str
    storageTypes: str


class ClearDataForStorageKeyParams(TypedDict):
    storageKey: str
    storageTypes: str


class GetCookiesParams(TypedDict):
    browserContextId: NotRequired[BrowserContextID]


class GetCookiesResult(TypedDict):
    cookies: list[Cookie]


class SetCookiesParams(TypedDict):
    cookies: list[CookieParam]
    browserContextId: NotRequired[BrowserContextID]


class ClearCookiesParams(TypedDict):
    browserContextId: NotRequired[BrowserContextID]


class GetUsageAndQuotaParams(TypedDict):
    origin: str


class GetUsageAndQuotaResult(TypedDict):
    usage: float
    quota: float
    overrideActive: bool
    usageBreakdown: list[UsageForType]


class OverrideQuotaForOriginParams(TypedDict):
    origin: str
    quotaSize: NotRequired[float]


class TrackCacheStorageForOriginParams(TypedDict):
    origin: str


class TrackCacheStorageForStorageKeyParams(TypedDict):
    storageKey: str


class TrackIndexedDBForOriginParams(TypedDict):
    origin: str


class TrackIndexedDBForStorageKeyParams(TypedDict):
    storageKey: str


class UntrackCacheStorageForOriginParams(TypedDict):
    origin: str


class UntrackCacheStorageForStorageKeyParams(TypedDict):
    storageKey: str


class UntrackIndexedDBForOriginParams(TypedDict):
    origin: str


class UntrackIndexedDBForStorageKeyParams(TypedDict):
    storageKey: str


class GetTrustTokensResult(TypedDict):
    tokens: list[TrustTokens]


class ClearTrustTokensParams(TypedDict):
    issuerOrigin: str


class ClearTrustTokensResult(TypedDict):
    didDeleteTokens: bool


class GetInterestGroupDetailsParams(TypedDict):
    ownerOrigin: str
    name: str


class GetInterestGroupDetailsResult(TypedDict):
    details: dict


class SetInterestGroupTrackingParams(TypedDict):
    enable: bool


class SetInterestGroupAuctionTrackingParams(TypedDict):
    enable: bool


class GetSharedStorageMetadataParams(TypedDict):
    ownerOrigin: str


class GetSharedStorageMetadataResult(TypedDict):
    metadata: SharedStorageMetadata


class GetSharedStorageEntriesParams(TypedDict):
    ownerOrigin: str


class GetSharedStorageEntriesResult(TypedDict):
    entries: list[SharedStorageEntry]


class SetSharedStorageEntryParams(TypedDict):
    ownerOrigin: str
    key: str
    value: str
    ignoreIfPresent: NotRequired[bool]


class DeleteSharedStorageEntryParams(TypedDict):
    ownerOrigin: str
    key: str


class ClearSharedStorageEntriesParams(TypedDict):
    ownerOrigin: str


class ResetSharedStorageBudgetParams(TypedDict):
    ownerOrigin: str


class SetSharedStorageTrackingParams(TypedDict):
    enable: bool


class SetStorageBucketTrackingParams(TypedDict):
    storageKey: str
    enable: bool


class DeleteStorageBucketParams(TypedDict):
    bucket: StorageBucket


class RunBounceTrackingMitigationsResult(TypedDict):
    deletedSites: list[str]


class SetAttributionReportingLocalTestingModeParams(TypedDict):
    enabled: bool


class SetAttributionReportingTrackingParams(TypedDict):
    enable: bool


class SendPendingAttributionReportsResult(TypedDict):
    numSent: int


class GetRelatedWebsiteSetsResult(TypedDict):
    sets: list[RelatedWebsiteSet]


class GetAffectedUrlsForThirdPartyCookieMetadataParams(TypedDict):
    firstPartyUrl: str
    thirdPartyUrls: list[str]


class GetAffectedUrlsForThirdPartyCookieMetadataResult(TypedDict):
    matchedUrls: list[str]


class SetProtectedAudienceKAnonymityParams(TypedDict):
    owner: str
    name: str
    hashes: list[str]


GetStorageKeyForFrameResponse = Response[GetStorageKeyForFrameResult]
GetCookiesResponse = Response[GetCookiesResult]
GetUsageAndQuotaResponse = Response[GetUsageAndQuotaResult]
GetTrustTokensResponse = Response[GetTrustTokensResult]
GetInterestGroupDetailsResponse = Response[GetInterestGroupDetailsResult]
GetSharedStorageMetadataResponse = Response[GetSharedStorageMetadataResult]
GetSharedStorageEntriesResponse = Response[GetSharedStorageEntriesResult]
RunBounceTrackingMitigationsResponse = Response[RunBounceTrackingMitigationsResult]
SendPendingAttributionReportsResponse = Response[SendPendingAttributionReportsResult]
GetRelatedWebsiteSetsResponse = Response[GetRelatedWebsiteSetsResult]
GetAffectedUrlsForThirdPartyCookieMetadataResponse = Response[
    GetAffectedUrlsForThirdPartyCookieMetadataResult
]


GetStorageKeyForFrameCommand = Command[GetStorageKeyForFrameParams, GetStorageKeyForFrameResponse]
ClearDataForOriginCommand = Command[ClearDataForOriginParams, Response[EmptyResponse]]
ClearDataForStorageKeyCommand = Command[ClearDataForStorageKeyParams, Response[EmptyResponse]]
GetCookiesCommand = Command[GetCookiesParams, GetCookiesResponse]
SetCookiesCommand = Command[SetCookiesParams, Response[EmptyResponse]]
ClearCookiesCommand = Command[ClearCookiesParams, Response[EmptyResponse]]
GetUsageAndQuotaCommand = Command[GetUsageAndQuotaParams, GetUsageAndQuotaResponse]
OverrideQuotaForOriginCommand = Command[OverrideQuotaForOriginParams, Response[EmptyResponse]]
TrackCacheStorageForOriginCommand = Command[
    TrackCacheStorageForOriginParams, Response[EmptyResponse]
]
TrackCacheStorageForStorageKeyCommand = Command[
    TrackCacheStorageForStorageKeyParams, Response[EmptyResponse]
]
TrackIndexedDBForOriginCommand = Command[TrackIndexedDBForOriginParams, Response[EmptyResponse]]
TrackIndexedDBForStorageKeyCommand = Command[
    TrackIndexedDBForStorageKeyParams, Response[EmptyResponse]
]
UntrackCacheStorageForOriginCommand = Command[
    UntrackCacheStorageForOriginParams, Response[EmptyResponse]
]
UntrackCacheStorageForStorageKeyCommand = Command[
    UntrackCacheStorageForStorageKeyParams, Response[EmptyResponse]
]
UntrackIndexedDBForOriginCommand = Command[UntrackIndexedDBForOriginParams, Response[EmptyResponse]]
UntrackIndexedDBForStorageKeyCommand = Command[
    UntrackIndexedDBForStorageKeyParams, Response[EmptyResponse]
]
GetTrustTokensCommand = Command[EmptyParams, GetTrustTokensResponse]
ClearTrustTokensCommand = Command[ClearTrustTokensParams, Response[EmptyResponse]]
GetInterestGroupDetailsCommand = Command[
    GetInterestGroupDetailsParams, GetInterestGroupDetailsResponse
]
SetInterestGroupTrackingCommand = Command[SetInterestGroupTrackingParams, Response[EmptyResponse]]
SetInterestGroupAuctionTrackingCommand = Command[
    SetInterestGroupAuctionTrackingParams, Response[EmptyResponse]
]
GetSharedStorageMetadataCommand = Command[
    GetSharedStorageMetadataParams, GetSharedStorageMetadataResponse
]
GetSharedStorageEntriesCommand = Command[
    GetSharedStorageEntriesParams, GetSharedStorageEntriesResponse
]
SetSharedStorageEntryCommand = Command[SetSharedStorageEntryParams, Response[EmptyResponse]]
DeleteSharedStorageEntryCommand = Command[DeleteSharedStorageEntryParams, Response[EmptyResponse]]
ClearSharedStorageEntriesCommand = Command[ClearSharedStorageEntriesParams, Response[EmptyResponse]]
ResetSharedStorageBudgetCommand = Command[ResetSharedStorageBudgetParams, Response[EmptyResponse]]
SetSharedStorageTrackingCommand = Command[SetSharedStorageTrackingParams, Response[EmptyResponse]]
SetStorageBucketTrackingCommand = Command[SetStorageBucketTrackingParams, Response[EmptyResponse]]
DeleteStorageBucketCommand = Command[DeleteStorageBucketParams, Response[EmptyResponse]]
RunBounceTrackingMitigationsCommand = Command[EmptyParams, RunBounceTrackingMitigationsResponse]
SetAttributionReportingLocalTestingModeCommand = Command[
    SetAttributionReportingLocalTestingModeParams, Response[EmptyResponse]
]
SetAttributionReportingTrackingCommand = Command[
    SetAttributionReportingTrackingParams, Response[EmptyResponse]
]
SendPendingAttributionReportsCommand = Command[EmptyParams, SendPendingAttributionReportsResponse]
GetRelatedWebsiteSetsCommand = Command[EmptyParams, GetRelatedWebsiteSetsResponse]
GetAffectedUrlsForThirdPartyCookieMetadataCommand = Command[
    GetAffectedUrlsForThirdPartyCookieMetadataParams,
    GetAffectedUrlsForThirdPartyCookieMetadataResponse,
]
SetProtectedAudienceKAnonymityCommand = Command[
    SetProtectedAudienceKAnonymityParams, Response[EmptyResponse]
]
