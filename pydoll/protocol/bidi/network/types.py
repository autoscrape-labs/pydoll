from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext, Navigation

Request = str
"""Unique identifier for a network request."""

Intercept = str
"""Unique identifier for a network intercept."""

Collector = str
"""Unique identifier for a data collector."""


class SameSite(str, Enum):
    """Cookie SameSite attribute values."""

    STRICT = 'strict'
    LAX = 'lax'
    NONE = 'none'
    DEFAULT = 'default'


class InterceptPhase(str, Enum):
    """Phases at which a network intercept can be triggered."""

    BEFORE_REQUEST_SENT = 'beforeRequestSent'
    RESPONSE_STARTED = 'responseStarted'
    AUTH_REQUIRED = 'authRequired'


class DataType(str, Enum):
    """Types of network data that can be collected."""

    REQUEST = 'request'
    RESPONSE = 'response'


class CollectorType(str, Enum):
    """Types of data collectors."""

    BLOB = 'blob'


class StringValue(TypedDict):
    """UTF-8 string bytes value."""

    type: str  # "string"
    value: str


class Base64Value(TypedDict):
    """Base64-encoded bytes value."""

    type: str  # "base64"
    value: str


BytesValue = StringValue | Base64Value


class AuthChallenge(TypedDict):
    """Authentication challenge from the server."""

    scheme: str
    realm: str


class AuthCredentials(TypedDict):
    """Authentication credentials."""

    type: str  # "password"
    username: str
    password: str


class Header(TypedDict):
    """HTTP header name-value pair."""

    name: str
    value: BytesValue


class Cookie(TypedDict):
    """HTTP cookie."""

    name: str
    value: BytesValue
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: SameSite
    expiry: NotRequired[int]


class CookieHeader(TypedDict):
    """Cookie data as it appears in a Cookie request header."""

    name: str
    value: BytesValue


class SetCookieHeader(TypedDict):
    """Data in a Set-Cookie response header."""

    name: str
    value: BytesValue
    domain: NotRequired[str]
    httpOnly: NotRequired[bool]
    expiry: NotRequired[str]
    maxAge: NotRequired[int]
    path: NotRequired[str]
    sameSite: NotRequired[SameSite]
    secure: NotRequired[bool]


class FetchTimingInfo(TypedDict):
    """Timing information for a network request."""

    timeOrigin: float
    requestTime: float
    redirectStart: float
    redirectEnd: float
    fetchStart: float
    dnsStart: float
    dnsEnd: float
    connectStart: float
    connectEnd: float
    tlsStart: float
    requestStart: float
    responseStart: float
    responseEnd: float


class Initiator(TypedDict, total=False):
    """Source of a network request."""

    columnNumber: int
    lineNumber: int
    request: Request
    stackTrace: dict  # script.StackTrace
    type: str  # "parser" / "script" / "preflight" / "other"


class RequestData(TypedDict):
    """Data for an ongoing network request."""

    request: Request
    url: str
    method: str
    headers: list[Header]
    cookies: list[Cookie]
    headersSize: int
    bodySize: int | None
    destination: str
    initiatorType: str | None
    timings: FetchTimingInfo


class ResponseContent(TypedDict):
    """Decoded response content info."""

    size: int


class ResponseData(TypedDict):
    """Response to a network request."""

    url: str
    protocol: str
    status: int
    statusText: str
    fromCache: bool
    headers: list[Header]
    mimeType: str
    bytesReceived: int
    headersSize: int | None
    bodySize: int | None
    content: ResponseContent
    authChallenges: NotRequired[list[AuthChallenge]]


class UrlPatternPattern(TypedDict):
    """URL pattern using individual components."""

    type: str  # "pattern"
    protocol: NotRequired[str]
    hostname: NotRequired[str]
    port: NotRequired[str]
    pathname: NotRequired[str]
    search: NotRequired[str]


class UrlPatternString(TypedDict):
    """URL pattern using a single string."""

    type: str  # "string"
    pattern: str


UrlPattern = UrlPatternPattern | UrlPatternString


class BaseParameters(TypedDict):
    """Data common to all network events."""

    context: BrowsingContext | None
    isBlocked: bool
    navigation: Navigation | None
    redirectCount: int
    request: RequestData
    timestamp: int
    userContext: NotRequired[UserContext | None]
    intercepts: NotRequired[list[Intercept]]
