from enum import Enum

from typing_extensions import NotRequired, TypedDict


class Header(TypedDict):
    """HTTP header."""

    name: str
    value: str


class CookieParam(TypedDict):
    """Cookie parameters for setting cookies."""

    name: str
    value: str
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[str]
    expiry: NotRequired[int]


class Cookie(TypedDict):
    """Cookie returned by get_cookies."""

    name: str
    value: str
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: str
    expiry: NotRequired[int]


class WindowBounds(TypedDict, total=False):
    """Window position and dimensions."""

    width: int
    height: int
    x: int
    y: int


class BrowserVersion(TypedDict):
    """Browser version information."""

    browserName: str
    browserVersion: str
    userAgent: str


class DownloadBehavior(str, Enum):
    """Download behavior options."""

    ALLOW = 'allow'
    DENY = 'deny'
    DEFAULT = 'default'


class RequestMethod(str, Enum):
    """HTTP request methods."""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
