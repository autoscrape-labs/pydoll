from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.runtime.types import StackTrace
from pydoll.protocol.cdp.security.types import MixedContentType, SecurityState


class ResourceType(str, Enum):
    """Resource type as it was perceived by the rendering engine."""

    DOCUMENT = 'Document'
    STYLESHEET = 'Stylesheet'
    IMAGE = 'Image'
    MEDIA = 'Media'
    FONT = 'Font'
    SCRIPT = 'Script'
    TEXT_TRACK = 'TextTrack'
    XHR = 'XHR'
    FETCH = 'Fetch'
    PREFETCH = 'Prefetch'
    EVENT_SOURCE = 'EventSource'
    WEB_SOCKET = 'WebSocket'
    MANIFEST = 'Manifest'
    SIGNED_EXCHANGE = 'SignedExchange'
    PING = 'Ping'
    CSP_VIOLATION_REPORT = 'CSPViolationReport'
    PREFLIGHT = 'Preflight'
    FED_CM = 'FedCM'
    OTHER = 'Other'


LoaderId = str
RequestId = str
InterceptionId = str


class ErrorReason(str, Enum):
    """Network level fetch failure reason."""

    FAILED = 'Failed'
    ABORTED = 'Aborted'
    TIMED_OUT = 'TimedOut'
    ACCESS_DENIED = 'AccessDenied'
    CONNECTION_CLOSED = 'ConnectionClosed'
    CONNECTION_RESET = 'ConnectionReset'
    CONNECTION_REFUSED = 'ConnectionRefused'
    CONNECTION_ABORTED = 'ConnectionAborted'
    CONNECTION_FAILED = 'ConnectionFailed'
    NAME_NOT_RESOLVED = 'NameNotResolved'
    INTERNET_DISCONNECTED = 'InternetDisconnected'
    ADDRESS_UNREACHABLE = 'AddressUnreachable'
    BLOCKED_BY_CLIENT = 'BlockedByClient'
    BLOCKED_BY_RESPONSE = 'BlockedByResponse'


TimeSinceEpoch = float
MonotonicTime = float
Headers = dict[str, str]


class RequestMethod(str, Enum):
    """HTTP request method."""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'


class ConnectionType(str, Enum):
    """The underlying connection technology that the browser is supposedly using."""

    NONE = 'none'
    CELLULAR2G = 'cellular2g'
    CELLULAR3G = 'cellular3g'
    CELLULAR4G = 'cellular4g'
    BLUETOOTH = 'bluetooth'
    ETHERNET = 'ethernet'
    WIFI = 'wifi'
    WIMAX = 'wimax'
    OTHER = 'other'


class CookieSameSite(str, Enum):
    """Represents the cookie's 'SameSite' status"""

    STRICT = 'Strict'
    LAX = 'Lax'
    NONE = 'None'


class CookiePriority(str, Enum):
    """Represents the cookie's 'Priority' status"""

    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'


class CookieSourceScheme(str, Enum):
    """
    Represents the source scheme of the origin that originally set the cookie.
    A value of "Unset" allows protocol clients to emulate legacy cookie scope for the scheme.
    This is a temporary ability and it will be removed in the future."""

    UNSET = 'Unset'
    NON_SECURE = 'NonSecure'
    SECURE = 'Secure'


class ResourceTiming(TypedDict):
    """Timing information for the request."""

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


class ResourcePriority(str, Enum):
    """Loading priority of a resource request."""

    VERY_LOW = 'VeryLow'
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    VERY_HIGH = 'VeryHigh'


class PostDataEntry(TypedDict):
    """Post data entry for HTTP request"""

    bytes: NotRequired[str]


class Request(TypedDict):
    """HTTP request data."""

    url: str
    urlFragment: NotRequired[str]
    method: str
    headers: 'Headers'
    postData: NotRequired[str]
    hasPostData: NotRequired[bool]
    postDataEntries: NotRequired[list['PostDataEntry']]
    mixedContentType: NotRequired['MixedContentType']
    initialPriority: 'ResourcePriority'
    referrerPolicy: str
    isLinkPreload: NotRequired[bool]
    trustTokenParams: NotRequired['TrustTokenParams']
    isSameSite: NotRequired[bool]


class SignedCertificateTimestamp(TypedDict):
    """Details of a signed certificate timestamp (SCT)."""

    status: str
    origin: str
    logDescription: str
    logId: str
    timestamp: float
    hashAlgorithm: str
    signatureAlgorithm: str
    signatureData: str


class SecurityDetails(TypedDict):
    """Security details about a request."""

    protocol: str
    keyExchange: str
    keyExchangeGroup: NotRequired[str]
    cipher: str
    mac: NotRequired[str]
    certificateId: int
    subjectName: str
    sanList: list[str]
    issuer: str
    validFrom: 'TimeSinceEpoch'
    validTo: 'TimeSinceEpoch'
    signedCertificateTimestampList: list['SignedCertificateTimestamp']
    certificateTransparencyCompliance: 'CertificateTransparencyCompliance'
    serverSignatureAlgorithm: NotRequired[int]
    encryptedClientHello: bool


class CertificateTransparencyCompliance(str, Enum):
    """Whether the request complied with Certificate Transparency policy."""

    UNKNOWN = 'unknown'
    NOT_COMPLIANT = 'not-compliant'
    COMPLIANT = 'compliant'


class BlockedReason(str, Enum):
    """The reason why request was blocked."""

    OTHER = 'other'
    CSP = 'csp'
    MIXED_CONTENT = 'mixed-content'
    ORIGIN = 'origin'
    INSPECTOR = 'inspector'
    INTEGRITY = 'integrity'
    SUBRESOURCE_FILTER = 'subresource-filter'
    CONTENT_TYPE = 'content-type'
    COEP_FRAME_RESOURCE_NEEDS_COEP_HEADER = 'coep-frame-resource-needs-coep-header'
    COOP_SANDBOXED_IFRAME_CANNOT_NAVIGATE_TO_COOP_PAGE = (
        'coop-sandboxed-iframe-cannot-navigate-to-coop-page'
    )
    CORP_NOT_SAME_ORIGIN = 'corp-not-same-origin'
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_COEP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-coep'
    )
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_DIP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-dip'
    )
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_COEP_AND_DIP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-coep-and-dip'
    )
    CORP_NOT_SAME_SITE = 'corp-not-same-site'
    SRI_MESSAGE_SIGNATURE_MISMATCH = 'sri-message-signature-mismatch'


class CorsError(str, Enum):
    """The reason why request was blocked."""

    DISALLOWED_BY_MODE = 'DisallowedByMode'
    INVALID_RESPONSE = 'InvalidResponse'
    WILDCARD_ORIGIN_NOT_ALLOWED = 'WildcardOriginNotAllowed'
    MISSING_ALLOW_ORIGIN_HEADER = 'MissingAllowOriginHeader'
    MULTIPLE_ALLOW_ORIGIN_VALUES = 'MultipleAllowOriginValues'
    INVALID_ALLOW_ORIGIN_VALUE = 'InvalidAllowOriginValue'
    ALLOW_ORIGIN_MISMATCH = 'AllowOriginMismatch'
    INVALID_ALLOW_CREDENTIALS = 'InvalidAllowCredentials'
    CORS_DISABLED_SCHEME = 'CorsDisabledScheme'
    PREFLIGHT_INVALID_STATUS = 'PreflightInvalidStatus'
    PREFLIGHT_DISALLOWED_REDIRECT = 'PreflightDisallowedRedirect'
    PREFLIGHT_WILDCARD_ORIGIN_NOT_ALLOWED = 'PreflightWildcardOriginNotAllowed'
    PREFLIGHT_MISSING_ALLOW_ORIGIN_HEADER = 'PreflightMissingAllowOriginHeader'
    PREFLIGHT_MULTIPLE_ALLOW_ORIGIN_VALUES = 'PreflightMultipleAllowOriginValues'
    PREFLIGHT_INVALID_ALLOW_ORIGIN_VALUE = 'PreflightInvalidAllowOriginValue'
    PREFLIGHT_ALLOW_ORIGIN_MISMATCH = 'PreflightAllowOriginMismatch'
    PREFLIGHT_INVALID_ALLOW_CREDENTIALS = 'PreflightInvalidAllowCredentials'
    PREFLIGHT_MISSING_ALLOW_EXTERNAL = 'PreflightMissingAllowExternal'
    PREFLIGHT_INVALID_ALLOW_EXTERNAL = 'PreflightInvalidAllowExternal'
    PREFLIGHT_MISSING_ALLOW_PRIVATE_NETWORK = 'PreflightMissingAllowPrivateNetwork'
    PREFLIGHT_INVALID_ALLOW_PRIVATE_NETWORK = 'PreflightInvalidAllowPrivateNetwork'
    INVALID_ALLOW_METHODS_PREFLIGHT_RESPONSE = 'InvalidAllowMethodsPreflightResponse'
    INVALID_ALLOW_HEADERS_PREFLIGHT_RESPONSE = 'InvalidAllowHeadersPreflightResponse'
    METHOD_DISALLOWED_BY_PREFLIGHT_RESPONSE = 'MethodDisallowedByPreflightResponse'
    HEADER_DISALLOWED_BY_PREFLIGHT_RESPONSE = 'HeaderDisallowedByPreflightResponse'
    REDIRECT_CONTAINS_CREDENTIALS = 'RedirectContainsCredentials'
    INSECURE_PRIVATE_NETWORK = 'InsecurePrivateNetwork'
    INVALID_PRIVATE_NETWORK_ACCESS = 'InvalidPrivateNetworkAccess'
    UNEXPECTED_PRIVATE_NETWORK_ACCESS = 'UnexpectedPrivateNetworkAccess'
    NO_CORS_REDIRECT_MODE_NOT_FOLLOW = 'NoCorsRedirectModeNotFollow'
    PREFLIGHT_MISSING_PRIVATE_NETWORK_ACCESS_ID = 'PreflightMissingPrivateNetworkAccessId'
    PREFLIGHT_MISSING_PRIVATE_NETWORK_ACCESS_NAME = 'PreflightMissingPrivateNetworkAccessName'
    PRIVATE_NETWORK_ACCESS_PERMISSION_UNAVAILABLE = 'PrivateNetworkAccessPermissionUnavailable'
    PRIVATE_NETWORK_ACCESS_PERMISSION_DENIED = 'PrivateNetworkAccessPermissionDenied'
    LOCAL_NETWORK_ACCESS_PERMISSION_DENIED = 'LocalNetworkAccessPermissionDenied'


class CorsErrorStatus(TypedDict):
    corsError: CorsError
    failedParameter: str


class ServiceWorkerResponseSource(str, Enum):
    """Source of serviceworker response."""

    CACHE_STORAGE = 'cache-storage'
    HTTP_CACHE = 'http-cache'
    FALLBACK_CODE = 'fallback-code'
    NETWORK = 'network'


class TrustTokenParams(TypedDict):
    """
    Determines what type of Trust Token operation is executed and depending on the type,
    some additional parameters. The values are specified in
    third_party/blink/renderer/core/fetch/trust_token.idl.
    """

    operation: 'TrustTokenOperationType'
    refreshPolicy: str
    issuers: NotRequired[list[str]]


class TrustTokenOperationType(str, Enum):
    ISSUANCE = 'Issuance'
    REDEMPTION = 'Redemption'
    SIGNING = 'Signing'


class AlternateProtocolUsage(str, Enum):
    """The reason why Chrome uses a specific transport protocol for HTTP semantics."""

    ALTERNATIVE_JOB_WON_WITHOUT_RACE = 'alternativeJobWonWithoutRace'
    ALTERNATIVE_JOB_WON_RACE = 'alternativeJobWonRace'
    MAIN_JOB_WON_RACE = 'mainJobWonRace'
    MAPPING_MISSING = 'mappingMissing'
    BROKEN = 'broken'
    DNS_ALPN_H3_JOB_WON_WITHOUT_RACE = 'dnsAlpnH3JobWonWithoutRace'
    DNS_ALPN_H3_JOB_WON_RACE = 'dnsAlpnH3JobWonRace'
    UNSPECIFIED_REASON = 'unspecifiedReason'


class ServiceWorkerRouterSource(str, Enum):
    """Source of service worker router."""

    NETWORK = 'network'
    CACHE = 'cache'
    FETCH_EVENT = 'fetch-event'
    RACE_NETWORK_AND_FETCH_HANDLER = 'race-network-and-fetch-handler'


class ServiceWorkerRouterInfo(TypedDict):
    ruleIdMatched: NotRequired[int]
    matchedSourceType: NotRequired['ServiceWorkerRouterSource']
    actualSourceType: NotRequired['ServiceWorkerRouterSource']


class Response(TypedDict):
    """HTTP response data."""

    url: str
    status: int
    statusText: str
    headers: 'Headers'
    headersText: NotRequired[str]
    mimeType: str
    charset: str
    requestHeaders: NotRequired['Headers']
    requestHeadersText: NotRequired[str]
    connectionReused: bool
    connectionId: float
    remoteIPAddress: NotRequired[str]
    remotePort: NotRequired[int]
    fromDiskCache: NotRequired[bool]
    fromServiceWorker: NotRequired[bool]
    fromPrefetchCache: NotRequired[bool]
    fromEarlyHints: NotRequired[bool]
    serviceWorkerRouterInfo: NotRequired['ServiceWorkerRouterInfo']
    encodedDataLength: float
    timing: NotRequired['ResourceTiming']
    serviceWorkerResponseSource: NotRequired[ServiceWorkerResponseSource]
    responseTime: NotRequired['TimeSinceEpoch']
    cacheStorageCacheName: NotRequired[str]
    protocol: NotRequired[str]
    alternateProtocolUsage: NotRequired[AlternateProtocolUsage]
    securityState: SecurityState
    securityDetails: NotRequired['SecurityDetails']
    isIpProtectionUsed: NotRequired[bool]


class WebSocketRequest(TypedDict):
    """WebSocket request data."""

    headers: 'Headers'


class WebSocketResponse(TypedDict):
    """WebSocket response data."""

    status: int
    statusText: str
    headers: 'Headers'
    headersText: NotRequired[str]
    requestHeaders: NotRequired['Headers']
    requestHeadersText: NotRequired[str]


class WebSocketFrame(TypedDict):
    """
    WebSocket message data. This represents an entire WebSocket message,
    not just a fragmented frame as the name suggests.
    """

    opcode: float
    mask: bool
    payloadData: str


class CachedResource(TypedDict):
    """Information about the cached resource."""

    url: str
    type: ResourceType
    response: NotRequired['Response']
    bodySize: float


class Initiator(TypedDict):
    """Information about the request initiator."""

    type: str
    stack: NotRequired[StackTrace]
    url: NotRequired[str]
    lineNumber: NotRequired[float]
    columnNumber: NotRequired[float]
    requestId: NotRequired[RequestId]


class CookiePartitionKey(TypedDict):
    """
    cookiePartitionKey object. The representation of the components of the key that are created
    by the cookiePartitionKey class contained in net/cookies/cookie_partition_key.h.
    """

    topLevelSite: str
    hasCrossSiteAncestor: bool


class Cookie(TypedDict):
    """Cookie object"""

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
    sourcePort: int
    partitionKey: NotRequired['CookiePartitionKey']


class SetCookieBlockedReason(str, Enum):
    """Types of reasons why a cookie may not be stored from a response."""

    SECURE_ONLY = 'SecureOnly'
    SAME_SITE_STRICT = 'SameSiteStrict'
    SAME_SITE_LAX = 'SameSiteLax'
    SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SameSiteUnspecifiedTreatedAsLax'
    SAME_SITE_NONE_INSECURE = 'SameSiteNoneInsecure'
    USER_PREFERENCES = 'UserPreferences'
    THIRD_PARTY_PHASEOUT = 'ThirdPartyPhaseout'
    THIRD_PARTY_BLOCKED_IN_FIRST_PARTY_SET = 'ThirdPartyBlockedInFirstPartySet'
    SYNTAX_ERROR = 'SyntaxError'
    SCHEME_NOT_SUPPORTED = 'SchemeNotSupported'
    OVERWRITE_SECURE = 'OverwriteSecure'
    INVALID_DOMAIN = 'InvalidDomain'
    INVALID_PREFIX = 'InvalidPrefix'
    UNKNOWN_ERROR = 'UnknownError'
    SCHEMEFUL_SAME_SITE_STRICT = 'SchemefulSameSiteStrict'
    SCHEMEFUL_SAME_SITE_LAX = 'SchemefulSameSiteLax'
    SCHEMEFUL_SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SchemefulSameSiteUnspecifiedTreatedAsLax'
    SAME_PARTY_FROM_CROSS_PARTY_CONTEXT = 'SamePartyFromCrossPartyContext'
    SAME_PARTY_CONFLICTS_WITH_OTHER_ATTRIBUTES = 'SamePartyConflictsWithOtherAttributes'
    NAME_VALUE_PAIR_EXCEEDS_MAX_SIZE = 'NameValuePairExceedsMaxSize'
    DISALLOWED_CHARACTER = 'DisallowedCharacter'
    NO_COOKIE_CONTENT = 'NoCookieContent'


class CookieBlockedReason(str, Enum):
    """Types of reasons why a cookie may not be sent with a request."""

    SECURE_ONLY = 'SecureOnly'
    NOT_ON_PATH = 'NotOnPath'
    DOMAIN_MISMATCH = 'DomainMismatch'
    SAME_SITE_STRICT = 'SameSiteStrict'
    SAME_SITE_LAX = 'SameSiteLax'
    SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SameSiteUnspecifiedTreatedAsLax'
    SAME_SITE_NONE_INSECURE = 'SameSiteNoneInsecure'
    USER_PREFERENCES = 'UserPreferences'
    THIRD_PARTY_PHASEOUT = 'ThirdPartyPhaseout'
    THIRD_PARTY_BLOCKED_IN_FIRST_PARTY_SET = 'ThirdPartyBlockedInFirstPartySet'
    UNKNOWN_ERROR = 'UnknownError'
    SCHEMEFUL_SAME_SITE_STRICT = 'SchemefulSameSiteStrict'
    SCHEMEFUL_SAME_SITE_LAX = 'SchemefulSameSiteLax'
    SCHEMEFUL_SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SchemefulSameSiteUnspecifiedTreatedAsLax'
    SAME_PARTY_FROM_CROSS_PARTY_CONTEXT = 'SamePartyFromCrossPartyContext'
    NAME_VALUE_PAIR_EXCEEDS_MAX_SIZE = 'NameValuePairExceedsMaxSize'
    PORT_MISMATCH = 'PortMismatch'
    SCHEME_MISMATCH = 'SchemeMismatch'
    ANONYMOUS_CONTEXT = 'AnonymousContext'


class CookieExemptionReason(str, Enum):
    """
    Types of reasons why a cookie should have been blocked by 3PCD but is exempted for the request.
    """

    NONE = 'None'
    USER_SETTING = 'UserSetting'
    TPCD_METADATA = 'TPCDMetadata'
    TPCD_DEPRECATION_TRIAL = 'TPCDDeprecationTrial'
    TOP_LEVEL_TPCD_DEPRECATION_TRIAL = 'TopLevelTPCDDeprecationTrial'
    TPCD_HEURISTICS = 'TPCDHeuristics'
    ENTERPRISE_POLICY = 'EnterprisePolicy'
    STORAGE_ACCESS = 'StorageAccess'
    TOP_LEVEL_STORAGE_ACCESS = 'TopLevelStorageAccess'
    SCHEME = 'Scheme'
    SAME_SITE_NONE_COOKIES_IN_SANDBOX = 'SameSiteNoneCookiesInSandbox'


class BlockedSetCookieWithReason(TypedDict):
    """A cookie which was not stored from a response with the corresponding reason."""

    blockedReasons: list[SetCookieBlockedReason]
    cookieLine: str
    cookie: NotRequired['Cookie']


class ExemptedSetCookieWithReason(TypedDict):
    """
    A cookie should have been blocked by 3PCD but is exempted and stored from a response with
    the corresponding reason. A cookie could only have at most one exemption reason.
    """

    exemptionReason: CookieExemptionReason
    cookieLine: str
    cookie: 'Cookie'


class AssociatedCookie(TypedDict):
    """
    A cookie associated with the request which may or may not be sent with it.
    Includes the cookies itself and reasons for blocking or exemption.
    """

    cookie: 'Cookie'
    blockedReasons: list[CookieBlockedReason]
    exemptionReason: NotRequired[CookieExemptionReason]


class CookieParam(TypedDict):
    """Cookie parameter object"""

    name: str
    value: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    secure: NotRequired[bool]
    httpOnly: NotRequired[bool]
    sameSite: NotRequired[CookieSameSite]
    expires: NotRequired['TimeSinceEpoch']
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: NotRequired[int]
    partitionKey: NotRequired['CookiePartitionKey']


class AuthChallenge(TypedDict):
    """Authorization challenge for HTTP status code 401 or 407."""

    source: NotRequired[str]
    origin: str
    scheme: str
    realm: str


class AuthChallengeResponse(TypedDict):
    """Response to an AuthChallenge."""

    response: str
    username: NotRequired[str]
    password: NotRequired[str]


class InterceptionStage(str, Enum):
    """
    Stages of the interception to begin intercepting. Request will intercept before the request
    is sent. Response will intercept after the response is received.
    """

    REQUEST = 'Request'
    HEADERS_RECEIVED = 'HeadersReceived'


class RequestPattern(TypedDict):
    """Request pattern for interception."""

    urlPattern: NotRequired[str]
    resourceType: NotRequired[ResourceType]
    interceptionStage: NotRequired[InterceptionStage]


class SignedExchangeSignature(TypedDict):
    """Information about a signed exchange signature."""

    label: str
    signature: str
    integrity: str
    certUrl: NotRequired[str]
    certSha256: NotRequired[str]
    validityUrl: str
    date: int
    expires: int
    certificates: NotRequired[list[str]]


class SignedExchangeHeader(TypedDict):
    """Information about a signed exchange header."""

    requestUrl: str
    responseCode: int
    responseHeaders: 'Headers'
    signatures: list[SignedExchangeSignature]
    headerIntegrity: str


class SignedExchangeErrorField(str, Enum):
    """Field type for a signed exchange related error."""

    SIGNATURE_SIG = 'signatureSig'
    SIGNATURE_INTEGRITY = 'signatureIntegrity'
    SIGNATURE_CERT_URL = 'signatureCertUrl'
    SIGNATURE_CERT_SHA256 = 'signatureCertSha256'
    SIGNATURE_VALIDITY_URL = 'signatureValidityUrl'
    SIGNATURE_TIMESTAMPS = 'signatureTimestamps'


class SignedExchangeError(TypedDict):
    """Information about a signed exchange response."""

    message: str
    signatureIndex: NotRequired[int]
    errorField: NotRequired[SignedExchangeErrorField]


class SignedExchangeInfo(TypedDict):
    """Information about a signed exchange response."""

    outerResponse: 'Response'
    hasExtraInfo: bool
    header: NotRequired[SignedExchangeHeader]
    securityDetails: NotRequired['SecurityDetails']
    errors: NotRequired[list[SignedExchangeError]]


class ContentEncoding(str, Enum):
    """List of content encodings supported by the backend."""

    DEFLATE = 'deflate'
    GZIP = 'gzip'
    BR = 'br'
    ZSTD = 'zstd'


class DirectSocketDnsQueryType(str, Enum):
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'


class DirectTCPSocketOptions(TypedDict):
    noDelay: bool
    keepAliveDelay: NotRequired[float]
    sendBufferSize: NotRequired[float]
    receiveBufferSize: NotRequired[float]
    dnsQueryType: NotRequired[DirectSocketDnsQueryType]


class DirectUDPSocketOptions(TypedDict):
    remoteAddr: NotRequired[str]
    remotePort: NotRequired[int]
    localAddr: NotRequired[str]
    localPort: NotRequired[int]
    dnsQueryType: NotRequired[DirectSocketDnsQueryType]
    sendBufferSize: NotRequired[float]
    receiveBufferSize: NotRequired[float]


class DirectUDPMessage(TypedDict):
    data: str
    remoteAddr: NotRequired[str]
    remotePort: NotRequired[int]


class PrivateNetworkRequestPolicy(str, Enum):
    ALLOW = 'Allow'
    BLOCK_FROM_INSECURE_TO_MORE_PRIVATE = 'BlockFromInsecureToMorePrivate'
    WARN_FROM_INSECURE_TO_MORE_PRIVATE = 'WarnFromInsecureToMorePrivate'
    PREFLIGHT_BLOCK = 'PreflightBlock'
    PREFLIGHT_WARN = 'PreflightWarn'


class IPAddressSpace(str, Enum):
    LOOPBACK = 'Loopback'
    LOCAL = 'Local'
    PUBLIC = 'Public'
    UNKNOWN = 'Unknown'


class ConnectTiming(TypedDict):
    requestTime: float


class ClientSecurityState(TypedDict):
    initiatorIsSecureContext: bool
    initiatorIPAddressSpace: IPAddressSpace
    privateNetworkRequestPolicy: PrivateNetworkRequestPolicy


class CrossOriginOpenerPolicyValue(str, Enum):
    SAME_ORIGIN = 'SameOrigin'
    SAME_ORIGIN_ALLOW_POPUPS = 'SameOriginAllowPopups'
    RESTRICT_PROPERTIES = 'RestrictProperties'
    UNSAFE_NONE = 'UnsafeNone'
    SAME_ORIGIN_PLUS_COEP = 'SameOriginPlusCoep'
    RESTRICT_PROPERTIES_PLUS_COEP = 'RestrictPropertiesPlusCoep'
    NO_OPENER_ALLOW_POPUPS = 'NoopenerAllowPopups'


class CrossOriginOpenerPolicyStatus(TypedDict):
    value: CrossOriginOpenerPolicyValue
    reportOnlyValue: CrossOriginOpenerPolicyValue
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class CrossOriginEmbedderPolicyValue(str, Enum):
    NONE = 'None'
    CREDENTIALLESS = 'Credentialless'
    REQUIRE_CORP = 'RequireCorp'


class CrossOriginEmbedderPolicyStatus(TypedDict):
    value: CrossOriginEmbedderPolicyValue
    reportOnlyValue: CrossOriginEmbedderPolicyValue
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class ContentSecurityPolicySource(str, Enum):
    HTTP = 'HTTP'
    META = 'Meta'


class ContentSecurityPolicyStatus(TypedDict):
    effectiveDirectives: str
    isEnforced: bool
    source: ContentSecurityPolicySource


class SecurityIsolationStatus(TypedDict):
    coop: NotRequired[CrossOriginOpenerPolicyStatus]
    coep: NotRequired[CrossOriginEmbedderPolicyStatus]
    csp: NotRequired[list[ContentSecurityPolicyStatus]]


class ReportStatus(str, Enum):
    """The status of a Reporting API report."""

    QUEUED = 'Queued'
    PENDING = 'Pending'
    MARKED_FOR_REMOVAL = 'MarkedForRemoval'
    SUCCESS = 'Success'


class ReportId(str):
    pass


class ReportingApiReport(TypedDict):
    """An object representing a report generated by the Reporting API."""

    id: ReportId
    initiatorUrl: str
    destination: str
    type: str
    timestamp: TimeSinceEpoch
    depth: int
    completedAttempts: int
    body: dict
    status: ReportStatus


class ReportingApiEndpoint(TypedDict):
    url: str
    groupName: str


class LoadNetworkResourcePageResult(TypedDict):
    """An object providing the result of a network resource load."""

    success: bool
    netError: NotRequired[float]
    netErrorName: NotRequired[str]
    httpStatusCode: NotRequired[float]
    stream: NotRequired[str]
    headers: NotRequired['Headers']


class LoadNetworkResourceOptions(TypedDict):
    """An options object that may be extended later to better support CORS, CORB and streaming."""

    disableCache: bool
    includeCredentials: bool
