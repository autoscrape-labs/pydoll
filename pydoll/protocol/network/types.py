from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from typing_extensions import TypedDict

from pydoll.constants import (
    AlternateProtocolUsage,
    CertificateTransparencyCompliance,
    ContentSecurityPolicySource,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
    InitiatorType,
    MixedContentType,
    NetworkServiceWorkerResponseSource,
    NetworkServiceWorkerRouterSourceType,
    ReferrerPolicy,
    RefreshPolicy,
    ResourcePriority,
    ResourceType,
    SecurityState,
    TrustTokenOperationType,
)
from pydoll.protocol.runtime.types import StackTrace


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


class Initiator(TypedDict):
    type: InitiatorType
    stack: NotRequired[StackTrace]
    url: NotRequired[str]
    lineNumber: NotRequired[int]
    columnNumber: NotRequired[int]
    requestId: NotRequired[str]


class ServiceWorkerRouterInfo(TypedDict):
    """Service worker router info object."""

    ruleIdMatched: NotRequired[int]
    matchedSourceType: NotRequired[NetworkServiceWorkerRouterSourceType]
    actualSourceType: NotRequired[NetworkServiceWorkerRouterSourceType]


class ResourceTiming(TypedDict):
    """Resource timing object."""

    requestTime: float
    proxyStart: float
    proxyEnd: float
    dnsStart: float
    dnsEnd: float
    connectStart: float
    connectEnd: float
    sslStart: float
    sslEnd: float
    workerStart: float
    workerReady: float
    workerFetchStart: float
    workerRespondWithSettled: float
    workerRouterEvaluationStart: NotRequired[float]
    workerCacheLookupStart: NotRequired[float]
    sendStart: float
    sendEnd: float
    pushStart: float
    pushEnd: float
    receiveHeadersStart: float
    receiveHeadersEnd: float


class SignedCertificateTimestamp(TypedDict):
    """Signed certificate timestamp object."""

    status: str
    origin: str
    logDescription: str
    logId: str
    timestamp: float
    hashAlgorithm: str
    signatureAlgorithm: str
    signatureData: str


class SecurityDetails(TypedDict):
    """Security details object."""

    protocol: str
    keyExchange: str
    keyExchangeGroup: NotRequired[str]
    cipher: str
    mac: NotRequired[str]
    certificateId: int
    subjectName: str
    sanList: list[str]
    issuer: str
    validFrom: float
    validTo: float
    signedCertificateTimestampList: list[SignedCertificateTimestamp]
    certificateTransparencyCompliance: CertificateTransparencyCompliance
    serverSignatureAlgorithm: NotRequired[int]
    encryptedClientHello: bool


class Response(TypedDict):
    url: str
    status: int
    statusText: str
    headers: list[dict]
    headersText: NotRequired[str]
    mimeType: str
    charset: str
    requestHeaders: NotRequired[list[dict]]
    requestHeadersText: NotRequired[str]
    connectionReused: bool
    connectionId: float
    remoteIPAddress: NotRequired[str]
    remotePort: NotRequired[int]
    fromDiskCache: NotRequired[bool]
    fromServiceWorker: NotRequired[bool]
    fromPrefetchCache: NotRequired[bool]
    fromEarlyHints: NotRequired[bool]
    serviceWorkerRouterInfo: NotRequired[ServiceWorkerRouterInfo]
    encodedDataLength: float
    timing: NotRequired[ResourceTiming]
    serviceWorkerResponseSource: NotRequired[NetworkServiceWorkerResponseSource]
    responseTime: NotRequired[float]
    cacheStorageCacheName: NotRequired[str]
    protocol: NotRequired[str]
    alternateProtocolUsage: NotRequired[AlternateProtocolUsage]
    securityState: SecurityState
    securityDetails: NotRequired[SecurityDetails]


class NetworkLogParams(TypedDict):
    requestId: str
    loaderId: str
    documentURL: str
    request: Request
    timestamp: float
    wallTime: float
    initiator: Initiator
    redirectHasExtraInfo: bool
    redirectResponse: NotRequired[Response]
    type: NotRequired[ResourceType]
    frameId: NotRequired[str]
    hasUserGesture: NotRequired[bool]


class NetworkLog(TypedDict):
    """Network log object."""

    method: str
    params: RequestPausedEventParams
