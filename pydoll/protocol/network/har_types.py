"""HAR 1.2 format type definitions.

Based on the HAR 1.2 specification: http://www.softwareishard.com/blog/har-12-spec/
These TypedDicts define the structure of HAR (HTTP Archive) files used for
recording and replaying network traffic.
"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class HarTimings(TypedDict):
    """Timing information about a request/response round trip."""

    blocked: float
    dns: float
    connect: float
    ssl: float
    send: float
    wait: float
    receive: float


class HarCookie(TypedDict):
    """Cookie used in a request or response."""

    name: str
    value: str
    path: NotRequired[str]
    domain: NotRequired[str]
    expires: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]


class HarHeader(TypedDict):
    """HTTP header name-value pair."""

    name: str
    value: str


class HarQueryParam(TypedDict):
    """URL query string parameter."""

    name: str
    value: str


class HarPostData(TypedDict):
    """Posted data info."""

    mimeType: str
    text: str
    params: NotRequired[list[dict]]


class HarRequest(TypedDict):
    """Detailed info about the request."""

    method: str
    url: str
    httpVersion: str
    cookies: list[HarCookie]
    headers: list[HarHeader]
    queryString: list[HarQueryParam]
    headersSize: int
    bodySize: int
    postData: NotRequired[HarPostData]


class HarContent(TypedDict):
    """Response content body info."""

    size: int
    mimeType: str
    text: NotRequired[str]
    encoding: NotRequired[str]


class HarResponse(TypedDict):
    """Detailed info about the response."""

    status: int
    statusText: str
    httpVersion: str
    cookies: list[HarCookie]
    headers: list[HarHeader]
    content: HarContent
    redirectURL: str
    headersSize: int
    bodySize: int


class HarCache(TypedDict, total=False):
    """Cache state for a request/response pair."""

    beforeRequest: dict
    afterRequest: dict


class HarEntry(TypedDict):
    """Represents an exported HTTP request."""

    startedDateTime: str
    time: float
    request: HarRequest
    response: HarResponse
    cache: HarCache
    timings: HarTimings
    serverIPAddress: NotRequired[str]
    connection: NotRequired[str]
    _resourceType: NotRequired[str]


class HarPage(TypedDict):
    """Represents an exported page."""

    startedDateTime: str
    id: str
    title: str


class HarCreator(TypedDict):
    """Information about the creator of the HAR file."""

    name: str
    version: str


class HarLog(TypedDict):
    """Root of the HAR data."""

    version: str
    creator: HarCreator
    pages: list[HarPage]
    entries: list[HarEntry]


class Har(TypedDict):
    """Top-level HAR object."""

    log: HarLog
