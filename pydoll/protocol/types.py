from typing_extensions import TypedDict


class Header(TypedDict):
    """HTTP header."""

    name: str
    value: str


class ResponseCookie(TypedDict):
    """A cookie set by a response, parsed (name/value) from a Set-Cookie header."""

    name: str
    value: str
