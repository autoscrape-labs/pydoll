from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from pydoll.constants import (
    ContentSecurityPolicySource,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
    MixedContentType,
    ReferrerPolicy,
    RefreshPolicy,
    ResourcePriority,
    TrustTokenOperationType,
)


class SearchMatch(TypedDict):
    """Search match object."""

    lineNumber: int
    lineContent: str


class CookiePartitionKey(TypedDict):
    topLevelSite: str
    hasCrossSiteAncestor: bool


class Cookie(TypedDict):
    """Cookie object."""

    name: str
    value: str
    domain: str
    path: str
    expires: float
    size: int
    httpOnly: bool
    secure: bool
    session: bool
    sameSite: NotRequired[CookieSameSite]
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: NotRequired[int]
    partitionKey: NotRequired[CookiePartitionKey]
    partitionKeyOpaque: NotRequired[bool]


class CrossOriginOpenerPolicyStatus(TypedDict):
    value: 'CrossOriginOpenerPolicyStatus'
    reportOnlyValue: 'CrossOriginOpenerPolicyStatus'
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class CrossOriginEmbedderPolicyStatus(TypedDict):
    value: 'CrossOriginEmbedderPolicyStatus'
    reportOnlyValue: 'CrossOriginEmbedderPolicyStatus'
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class ContentSecurityPolicyStatus(TypedDict):
    """Content security policy status object."""

    effectiveDirective: str
    isEnforced: bool
    source: ContentSecurityPolicySource


class SecurityIsolationStatus(TypedDict):
    """Security isolation status object."""

    coop: NotRequired[CrossOriginOpenerPolicyStatus]
    coep: NotRequired[CrossOriginEmbedderPolicyStatus]
    csp: NotRequired[list[ContentSecurityPolicyStatus]]


class LoadNetworkResourceOptions(TypedDict):
    """Load network resource options object."""

    disableCache: NotRequired[bool]
    includeCredentials: NotRequired[bool]


class CookieParam(TypedDict):
    name: str
    value: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    secure: NotRequired[bool]
    httpOnly: NotRequired[bool]
    sameSite: NotRequired[CookieSameSite]
    expires: NotRequired[float]
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: NotRequired[int]
    partitionKey: NotRequired[CookiePartitionKey]


class UserAgentBrand(TypedDict):
    brand: str
    version: str


class UserAgentMetadata(TypedDict):
    brands: NotRequired[list[UserAgentBrand]]
    fullVersionList: NotRequired[list[UserAgentBrand]]
    platform: str
    platformVersion: str
    architecture: str
    model: str
    mobile: bool
    bitness: NotRequired[str]
    wow64: NotRequired[bool]


class PostDataEntry(TypedDict):
    bytes: NotRequired[str]


class TrustTokenParams(TypedDict):
    operation: TrustTokenOperationType
    refreshPolicy: RefreshPolicy
    issuers: NotRequired[list[str]]


class Request(TypedDict):
    url: str
    urlFragment: NotRequired[str]
    method: str
    headers: NotRequired[dict]
    hasPostData: NotRequired[bool]
    postDataEntries: NotRequired[list[PostDataEntry]]
    mixedContentType: NotRequired[MixedContentType]
    initialPriority: NotRequired[ResourcePriority]
    referrerPolicy: NotRequired[ReferrerPolicy]
    isLinkPreload: NotRequired[bool]
    trustTokenParams: NotRequired[TrustTokenParams]
    isSameSite: NotRequired[bool]


class RequestPausedEventParams(TypedDict):
    requestId: str
    request: Request


class RequestPausedEvent(TypedDict):
    method: str
    params: RequestPausedEventParams
