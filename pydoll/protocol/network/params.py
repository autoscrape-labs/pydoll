try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


from pydoll.constants import (
    ConnectionType,
    ContentEncoding,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
)
from pydoll.protocol.base import CommandParams
from pydoll.protocol.fetch.types import HeaderEntry, RequestPattern
from pydoll.protocol.network.types import (
    CookiePartitionKey,
    LoadNetworkResourceOptions,
    UserAgentMetadata,
)


class DeleteCookiesParams(CommandParams):
    """Parameters for deleting browser cookies."""

    name: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    partitionKey: NotRequired[CookiePartitionKey]


class EmulateNetworkConditionsParams(CommandParams):
    """Parameters for emulating network conditions."""

    offline: bool
    latency: float
    downloadThroughput: float
    uploadThroughput: float
    connectionType: NotRequired[ConnectionType]
    packetLoss: NotRequired[float]
    packetQueueLength: NotRequired[int]
    packetReordering: NotRequired[bool]


class NetworkEnableParams(CommandParams):
    """Parameters for enabling network tracking."""

    maxTotalBufferSize: NotRequired[int]
    maxResourceBufferSize: NotRequired[int]
    maxPostDataSize: NotRequired[int]


class GetCookiesParams(CommandParams):
    """Parameters for retrieving browser cookies."""

    urls: NotRequired[list[str]]


class GetRequestPostDataParams(CommandParams):
    """Parameters for retrieving request POST data."""

    requestId: str


class GetResponseBodyParams(CommandParams):
    """Parameters for retrieving response body."""

    requestId: str


class GetCertificateParams(CommandParams):
    """Parameters for retrieving DER-encoded certificate."""

    origin: str


class GetResponseBodyForInterceptionParams(CommandParams):
    """Parameters for retrieving response body for intercepted request."""

    interceptionId: str


class SearchInResponseBodyParams(CommandParams):
    """Parameters for searching in response content."""

    requestId: str
    query: str
    caseSensitive: NotRequired[bool]
    isRegex: NotRequired[bool]


class SetBypassServiceWorkerParams(CommandParams):
    """Parameters for toggling service worker bypass."""

    bypass: bool


class SetCacheDisabledParams(CommandParams):
    """Parameters for toggling cache for requests."""

    cacheDisabled: bool


class SetCookieParams(CommandParams):
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


class SetCookiesParams(CommandParams):
    """Parameters for setting multiple cookies."""

    cookies: list[SetCookieParams]


class SetExtraHTTPHeadersParams(CommandParams):
    """Parameters for setting extra HTTP headers."""

    headers: list[HeaderEntry]


class SetUserAgentOverrideParams(CommandParams):
    """Parameters for overriding user agent string."""

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


class SetBlockedURLsParams(CommandParams):
    """Parameters for blocking URLs from loading."""

    urls: list[str]


class SetAcceptedEncodingsParams(CommandParams):
    """Parameters for setting accepted content encodings."""

    encodings: list[ContentEncoding]


class SetAttachDebugStackParams(CommandParams):
    """Parameters for attaching a page script stack in requests."""

    enabled: bool


class SetCookieControlsParams(CommandParams):
    """Parameters for setting controls for third-party cookie access."""

    enableThirdPartyCookieRestriction: bool
    disableThirdPartyCookieMetadata: NotRequired[bool]
    disableThirdPartyCookieHeuristics: NotRequired[bool]


class StreamResourceContentParams(CommandParams):
    """Parameters for enabling streaming of the response."""

    requestId: str


class TakeResponseBodyForInterceptionAsStreamParams(CommandParams):
    """Parameters for taking response body for interception as a stream."""

    interceptionId: str


class SetRequestInterceptionParams(CommandParams):
    """Parameters for setting request interception patterns."""

    patterns: list[RequestPattern]


class AuthChallengeResponseParams(CommandParams):
    """Parameters for responding to an auth challenge."""

    response: str
    username: NotRequired[str]
    password: NotRequired[str]


class EnableReportingApiParams(CommandParams):
    """Parameters for enabling Reporting API."""

    enabled: bool


class GetSecurityIsolationStatusParams(CommandParams):
    frameId: NotRequired[str]


class LoadNetworkResourceParams(CommandParams):
    """Parameters for loading a network resource."""

    url: str
    options: LoadNetworkResourceOptions
    frameId: NotRequired[str]


class ReplayXHRParams(CommandParams):
    """Parameters for replaying an XMLHttpRequest."""

    requestId: str
