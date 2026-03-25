from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.debugger.types import SearchMatch
from pydoll.protocol.cdp.emulation.types import UserAgentMetadata
from pydoll.protocol.cdp.fetch.types import HeaderEntry, RequestPattern
from pydoll.protocol.cdp.network.types import (
    ConnectionType,
    ContentEncoding,
    Cookie,
    CookiePartitionKey,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
    LoadNetworkResourceOptions,
    SecurityIsolationStatus,
)


class NetworkMethod(str, Enum):
    CLEAR_BROWSER_CACHE = 'Network.clearBrowserCache'
    CLEAR_BROWSER_COOKIES = 'Network.clearBrowserCookies'
    DELETE_COOKIES = 'Network.deleteCookies'
    DISABLE = 'Network.disable'
    EMULATE_NETWORK_CONDITIONS = 'Network.emulateNetworkConditions'
    ENABLE = 'Network.enable'
    GET_COOKIES = 'Network.getCookies'
    GET_REQUEST_POST_DATA = 'Network.getRequestPostData'
    GET_RESPONSE_BODY = 'Network.getResponseBody'
    SET_BYPASS_SERVICE_WORKER = 'Network.setBypassServiceWorker'
    SET_CACHE_DISABLED = 'Network.setCacheDisabled'
    SET_COOKIE = 'Network.setCookie'
    SET_COOKIES = 'Network.setCookies'
    SET_EXTRA_HTTP_HEADERS = 'Network.setExtraHTTPHeaders'
    SET_USER_AGENT_OVERRIDE = 'Network.setUserAgentOverride'
    CLEAR_ACCEPTED_ENCODINGS_OVERRIDE = 'Network.clearAcceptedEncodingsOverride'
    ENABLE_REPORTING_API = 'Network.enableReportingApi'
    GET_CERTIFICATE = 'Network.getCertificate'
    GET_RESPONSE_BODY_FOR_INTERCEPTION = 'Network.getResponseBodyForInterception'
    GET_SECURITY_ISOLATION_STATUS = 'Network.getSecurityIsolationStatus'
    LOAD_NETWORK_RESOURCE = 'Network.loadNetworkResource'
    REPLAY_XHR = 'Network.replayXHR'
    SEARCH_IN_RESPONSE_BODY = 'Network.searchInResponseBody'
    SET_ACCEPTED_ENCODINGS = 'Network.setAcceptedEncodings'
    SET_ATTACH_DEBUG_STACK = 'Network.setAttachDebugStack'
    SET_BLOCKED_URLS = 'Network.setBlockedURLs'
    SET_COOKIE_CONTROLS = 'Network.setCookieControls'
    STREAM_RESOURCE_CONTENT = 'Network.streamResourceContent'
    TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM = (
        'Network.takeResponseBodyForInterceptionAsStream'
    )


class DeleteCookiesParams(TypedDict):
    """Parameters for deleting browser cookies."""

    name: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    partitionKey: NotRequired[CookiePartitionKey]


class EmulateNetworkConditionsParams(TypedDict):
    """Parameters for emulating network conditions."""

    offline: bool
    latency: float
    downloadThroughput: float
    uploadThroughput: float
    connectionType: NotRequired[ConnectionType]
    packetLoss: NotRequired[float]
    packetQueueLength: NotRequired[int]
    packetReordering: NotRequired[bool]


class NetworkEnableParams(TypedDict):
    """Parameters for enabling network tracking."""

    maxTotalBufferSize: NotRequired[int]
    maxResourceBufferSize: NotRequired[int]
    maxPostDataSize: NotRequired[int]


class GetCookiesParams(TypedDict):
    """Parameters for retrieving browser cookies."""

    urls: NotRequired[list[str]]


class GetRequestPostDataParams(TypedDict):
    """Parameters for retrieving request POST data."""

    requestId: str


class GetResponseBodyParams(TypedDict):
    """Parameters for retrieving response body."""

    requestId: str


class GetCertificateParams(TypedDict):
    """Parameters for retrieving DER-encoded certificate."""

    origin: str


class GetResponseBodyForInterceptionParams(TypedDict):
    """Parameters for retrieving response body for intercepted request."""

    interceptionId: str


class SearchInResponseBodyParams(TypedDict):
    """Parameters for searching in response content."""

    requestId: str
    query: str
    caseSensitive: NotRequired[bool]
    isRegex: NotRequired[bool]


class SetBypassServiceWorkerParams(TypedDict):
    """Parameters for toggling service worker bypass."""

    bypass: bool


class SetCacheDisabledParams(TypedDict):
    """Parameters for toggling cache for requests."""

    cacheDisabled: bool


class SetCookieParams(TypedDict):
    """Parameters for setting a cookie."""

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


class SetCookiesParams(TypedDict):
    """Parameters for setting multiple cookies."""

    cookies: list[SetCookieParams]


class SetExtraHTTPHeadersParams(TypedDict):
    """Parameters for setting extra HTTP headers."""

    headers: list[HeaderEntry]


class SetUserAgentOverrideParams(TypedDict):
    """Parameters for overriding user agent string."""

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


class SetBlockedURLsParams(TypedDict):
    """Parameters for blocking URLs from loading."""

    urls: list[str]


class SetAcceptedEncodingsParams(TypedDict):
    """Parameters for setting accepted content encodings."""

    encodings: list[ContentEncoding]


class SetAttachDebugStackParams(TypedDict):
    """Parameters for attaching a page script stack in requests."""

    enabled: bool


class SetCookieControlsParams(TypedDict):
    """Parameters for setting controls for third-party cookie access."""

    enableThirdPartyCookieRestriction: bool
    disableThirdPartyCookieMetadata: NotRequired[bool]
    disableThirdPartyCookieHeuristics: NotRequired[bool]


class StreamResourceContentParams(TypedDict):
    """Parameters for enabling streaming of the response."""

    requestId: str


class TakeResponseBodyForInterceptionAsStreamParams(TypedDict):
    """Parameters for taking response body for interception as a stream."""

    interceptionId: str


class SetRequestInterceptionParams(TypedDict):
    """Parameters for setting request interception patterns."""

    patterns: list[RequestPattern]


class AuthChallengeResponseParams(TypedDict):
    """Parameters for responding to an auth challenge."""

    response: str
    username: NotRequired[str]
    password: NotRequired[str]


class EnableReportingApiParams(TypedDict):
    """Parameters for enabling Reporting API."""

    enabled: bool


class GetSecurityIsolationStatusParams(TypedDict):
    frameId: NotRequired[str]


class LoadNetworkResourceParams(TypedDict):
    """Parameters for loading a network resource."""

    url: str
    options: LoadNetworkResourceOptions
    frameId: NotRequired[str]


class ReplayXHRParams(TypedDict):
    """Parameters for replaying an XMLHttpRequest."""

    requestId: str


class GetCookiesResult(TypedDict):
    """Response result for getCookies command."""

    cookies: list[Cookie]


class GetRequestPostDataResult(TypedDict):
    """Response result for getRequestPostData command."""

    postData: str


class GetResponseBodyResult(TypedDict):
    """Response result for getResponseBody command."""

    body: str
    base64Encoded: bool


class GetResponseBodyForInterceptionResult(TypedDict):
    """Response result for getResponseBodyForInterception command."""

    body: str
    base64Encoded: bool


class GetCertificateResult(TypedDict):
    """Response result for getCertificate command."""

    tableNames: list[str]


class SearchInResponseBodyResult(TypedDict):
    """Response result for searchInResponseBody command."""

    result: list[SearchMatch]


class SetCookieResult(TypedDict):
    """Response result for setCookie command."""

    success: bool


class StreamResourceContentResult(TypedDict):
    """Response result for streamResourceContent command."""

    bufferedData: str


class TakeResponseBodyForInterceptionAsStreamResult(TypedDict):
    """Response result for takeResponseBodyForInterceptionAsStream command."""

    stream: str


class CanClearBrowserCacheResult(TypedDict):
    """Response result for canClearBrowserCache command."""

    result: bool


class CanClearBrowserCookiesResult(TypedDict):
    """Response result for canClearBrowserCookies command."""

    result: bool


class CanEmulateNetworkConditionsResult(TypedDict):
    """Response result for canEmulateNetworkConditions command."""

    result: bool


class GetSecurityIsolationStatusResult(TypedDict):
    """Response result for getSecurityIsolationStatus command."""

    status: SecurityIsolationStatus


class LoadNetworkResourceResult(TypedDict):
    """Response result for loadNetworkResource command."""

    success: bool
    netError: NotRequired[float]
    netErrorName: NotRequired[str]
    httpStatusCode: NotRequired[float]
    stream: NotRequired[str]
    headers: NotRequired[list[HeaderEntry]]


GetCookiesResponse = Response[GetCookiesResult]
SetCookieResponse = Response[SetCookieResult]
GetRequestPostDataResponse = Response[GetRequestPostDataResult]
GetResponseBodyResponse = Response[GetResponseBodyResult]
GetResponseBodyForInterceptionResponse = Response[GetResponseBodyForInterceptionResult]
SearchInResponseBodyResponse = Response[SearchInResponseBodyResult]
StreamResourceContentResponse = Response[StreamResourceContentResult]
TakeResponseBodyForInterceptionAsStreamResponse = Response[
    TakeResponseBodyForInterceptionAsStreamResult
]
GetCertificateResponse = Response[GetCertificateResult]
CanClearBrowserCacheResponse = Response[CanClearBrowserCacheResult]
CanClearBrowserCookiesResponse = Response[CanClearBrowserCookiesResult]
CanEmulateNetworkConditionsResponse = Response[CanEmulateNetworkConditionsResult]
GetSecurityIsolationStatusResponse = Response[GetSecurityIsolationStatusResult]
LoadNetworkResourceResponse = Response[LoadNetworkResourceResult]


ClearBrowserCacheCommand = Command[EmptyParams, Response[EmptyResponse]]
ClearBrowserCookiesCommand = Command[EmptyParams, Response[EmptyResponse]]
ClearCookiesCommand = Command[DeleteCookiesParams, Response[EmptyResponse]]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EmulateNetworkConditionsCommand = Command[EmulateNetworkConditionsParams, Response[EmptyResponse]]
EnableCommand = Command[NetworkEnableParams, Response[EmptyResponse]]
GetCookiesCommand = Command[GetCookiesParams, GetCookiesResponse]
GetRequestPostDataCommand = Command[GetRequestPostDataParams, GetRequestPostDataResponse]
GetResponseBodyCommand = Command[GetResponseBodyParams, GetResponseBodyResponse]
SetCacheDisabledCommand = Command[SetCacheDisabledParams, Response[EmptyResponse]]
SetCookieCommand = Command[SetCookieParams, SetCookieResponse]
SetCookiesCommand = Command[SetCookiesParams, Response[EmptyResponse]]
SetExtraHTTPHeadersCommand = Command[SetExtraHTTPHeadersParams, Response[EmptyResponse]]
SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParams, Response[EmptyResponse]]
ClearAcceptedEncodingsOverrideCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableReportingApiCommand = Command[EnableReportingApiParams, Response[EmptyResponse]]
SearchInResponseBodyCommand = Command[SearchInResponseBodyParams, SearchInResponseBodyResponse]
SetBlockedURLsCommand = Command[SetBlockedURLsParams, Response[EmptyResponse]]
SetBypassServiceWorkerCommand = Command[SetBypassServiceWorkerParams, Response[EmptyResponse]]
GetCertificateCommand = Command[GetCertificateParams, GetCertificateResponse]
GetResponseBodyForInterceptionCommand = Command[
    GetResponseBodyForInterceptionParams, GetResponseBodyForInterceptionResponse
]
SetAcceptedEncodingsCommand = Command[SetAcceptedEncodingsParams, Response[EmptyResponse]]
SetAttachDebugStackCommand = Command[SetAttachDebugStackParams, Response[EmptyResponse]]
SetCookieControlsCommand = Command[SetCookieControlsParams, Response[EmptyResponse]]
StreamResourceContentCommand = Command[StreamResourceContentParams, StreamResourceContentResponse]
TakeResponseBodyForInterceptionAsStreamCommand = Command[
    TakeResponseBodyForInterceptionAsStreamParams, TakeResponseBodyForInterceptionAsStreamResponse
]
GetSecurityIsolationStatusCommand = Command[
    GetSecurityIsolationStatusParams, GetSecurityIsolationStatusResponse
]
LoadNetworkResourceCommand = Command[LoadNetworkResourceParams, LoadNetworkResourceResponse]
ReplayXHRCommand = Command[ReplayXHRParams, Response[EmptyResponse]]
