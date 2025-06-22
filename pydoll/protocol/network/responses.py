from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from typing_extensions import TypedDict

from pydoll.protocol.fetch.types import HeaderEntry
from pydoll.protocol.network.types import Cookie, SearchMatch, SecurityIsolationStatus


class GetCookiesResultDict(TypedDict):
    """Response result for getCookies command."""

    cookies: list[Cookie]


class GetRequestPostDataResultDict(TypedDict):
    """Response result for getRequestPostData command."""

    postData: str


class GetResponseBodyResultDict(TypedDict):
    """Response result for getResponseBody command."""

    body: str
    base64Encoded: bool


class GetResponseBodyForInterceptionResultDict(TypedDict):
    """Response result for getResponseBodyForInterception command."""

    body: str
    base64Encoded: bool


class GetCertificateResultDict(TypedDict):
    """Response result for getCertificate command."""

    tableNames: list[str]


class SearchInResponseBodyResultDict(TypedDict):
    """Response result for searchInResponseBody command."""

    result: list[SearchMatch]


class SetCookieResultDict(TypedDict):
    """Response result for setCookie command."""

    success: bool


class StreamResourceContentResultDict(TypedDict):
    """Response result for streamResourceContent command."""

    bufferedData: str


class TakeResponseBodyForInterceptionAsStreamResultDict(TypedDict):
    """Response result for takeResponseBodyForInterceptionAsStream command."""

    stream: str


class CanClearBrowserCacheResultDict(TypedDict):
    """Response result for canClearBrowserCache command."""

    result: bool


class CanClearBrowserCookiesResultDict(TypedDict):
    """Response result for canClearBrowserCookies command."""

    result: bool


class CanEmulateNetworkConditionsResultDict(TypedDict):
    """Response result for canEmulateNetworkConditions command."""

    result: bool


class GetSecurityIsolationStatusResultDict(TypedDict):
    """Response result for getSecurityIsolationStatus command."""

    status: SecurityIsolationStatus


class LoadNetworkResourceResultDict(TypedDict):
    """Response result for loadNetworkResource command."""

    success: bool
    netError: NotRequired[float]
    netErrorName: NotRequired[str]
    httpStatusCode: NotRequired[float]
    stream: NotRequired[str]
    headers: NotRequired[list[HeaderEntry]]


# Response classes that inherit from Response
class GetCookiesResponse(TypedDict):
    """Response for getCookies command."""

    result: GetCookiesResultDict


class GetRequestPostDataResponse(TypedDict):
    """Response for getRequestPostData command."""

    result: GetRequestPostDataResultDict


class GetResponseBodyResponse(TypedDict):
    """Response for getResponseBody command."""

    result: GetResponseBodyResultDict


class GetResponseBodyForInterceptionResponse(TypedDict):
    """Response for getResponseBodyForInterception command."""

    result: GetResponseBodyForInterceptionResultDict


class GetCertificateResponse(TypedDict):
    """Response for getCertificate command."""

    result: GetCertificateResultDict


class SearchInResponseBodyResponse(TypedDict):
    """Response for searchInResponseBody command."""

    result: SearchInResponseBodyResultDict


class SetCookieResponse(TypedDict):
    """Response for setCookie command."""

    result: SetCookieResultDict


class StreamResourceContentResponse(TypedDict):
    """Response for streamResourceContent command."""

    result: StreamResourceContentResultDict


class TakeResponseBodyForInterceptionAsStreamResponse(TypedDict):
    """Response for takeResponseBodyForInterceptionAsStream command."""

    result: TakeResponseBodyForInterceptionAsStreamResultDict


class CanClearBrowserCacheResponse(TypedDict):
    """Response for canClearBrowserCache command."""

    result: CanClearBrowserCacheResultDict


class CanClearBrowserCookiesResponse(TypedDict):
    """Response for canClearBrowserCookies command."""

    result: CanClearBrowserCookiesResultDict


class CanEmulateNetworkConditionsResponse(TypedDict):
    """Response for canEmulateNetworkConditions command."""

    result: CanEmulateNetworkConditionsResultDict


class GetSecurityIsolationStatusResponse(TypedDict):
    """Response for getSecurityIsolationStatus command."""

    result: GetSecurityIsolationStatusResultDict


class LoadNetworkResourceResponse(TypedDict):
    """Response for loadNetworkResource command."""

    result: LoadNetworkResourceResultDict
