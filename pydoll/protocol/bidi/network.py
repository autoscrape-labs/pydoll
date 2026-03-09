from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------


class Header(TypedDict):
    name: str
    value: BytesValue


def make_header(name: str, value: str) -> Header:
    """Build a BiDi-compliant header dict with a string value."""
    return Header(name=name, value=BytesValue(type='string', value=value))


class UrlPatternString(TypedDict):
    type: str  # 'string'
    pattern: str


class BytesValue(TypedDict):
    type: str  # 'string' | 'base64'
    value: str


class AuthCredentials(TypedDict):
    type: str  # 'password'
    username: str
    password: str


# ---------------------------------------------------------------------------
# Command params
# ---------------------------------------------------------------------------


class AddInterceptParams(TypedDict):
    phases: list[str]
    contexts: NotRequired[list[str]]
    urlPatterns: NotRequired[list[UrlPatternString]]


class RemoveInterceptParams(TypedDict):
    intercept: str


class ContinueRequestParams(TypedDict):
    request: str
    body: NotRequired[BytesValue]
    headers: NotRequired[list[Header]]
    method: NotRequired[str]
    url: NotRequired[str]


class ContinueResponseParams(TypedDict):
    request: str
    headers: NotRequired[list[Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]


class ContinueWithAuthParams(TypedDict):
    request: str
    action: str  # 'provideCredentials' | 'default' | 'cancel'
    credentials: NotRequired[AuthCredentials]


class FailRequestParams(TypedDict):
    request: str


class ProvideResponseParams(TypedDict):
    request: str
    body: NotRequired[BytesValue]
    headers: NotRequired[list[Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class AddInterceptResult(TypedDict):
    intercept: str


# ---------------------------------------------------------------------------
# Response / Command aliases
# ---------------------------------------------------------------------------

AddInterceptResponse = Response[AddInterceptResult]
RemoveInterceptResponse = Response[EmptyResponse]
ContinueRequestResponse = Response[EmptyResponse]
ContinueResponseResponse = Response[EmptyResponse]
ContinueWithAuthResponse = Response[EmptyResponse]
FailRequestResponse = Response[EmptyResponse]
ProvideResponseResponse = Response[EmptyResponse]

AddInterceptCommand = Command[AddInterceptParams, AddInterceptResponse]
RemoveInterceptCommand = Command[RemoveInterceptParams, RemoveInterceptResponse]
ContinueRequestCommand = Command[ContinueRequestParams, ContinueRequestResponse]
ContinueResponseCommand = Command[ContinueResponseParams, ContinueResponseResponse]
ContinueWithAuthCommand = Command[ContinueWithAuthParams, ContinueWithAuthResponse]
FailRequestCommand = Command[FailRequestParams, FailRequestResponse]
ProvideResponseCommand = Command[ProvideResponseParams, ProvideResponseResponse]


# ---------------------------------------------------------------------------
# Event name constants
# ---------------------------------------------------------------------------


class NetworkEvent:
    """BiDi network event name constants."""

    BEFORE_REQUEST_SENT = 'network.beforeRequestSent'
    RESPONSE_STARTED = 'network.responseStarted'
    RESPONSE_COMPLETED = 'network.responseCompleted'
    FETCH_ERROR = 'network.fetchError'
    AUTH_REQUIRED = 'network.authRequired'

    ALL_EVENTS = [
        BEFORE_REQUEST_SENT,
        RESPONSE_STARTED,
        RESPONSE_COMPLETED,
        FETCH_ERROR,
        AUTH_REQUIRED,
    ]


# ---------------------------------------------------------------------------
# Intercept phases
# ---------------------------------------------------------------------------


class InterceptPhase:
    BEFORE_REQUEST_SENT = 'beforeRequestSent'
    RESPONSE_STARTED = 'responseStarted'
    AUTH_REQUIRED = 'authRequired'


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def add_intercept(
    phases: list[str],
    contexts: Optional[list[str]] = None,
    url_patterns: Optional[list[str]] = None,
) -> AddInterceptCommand:
    """
    Register a network intercept.

    Args:
        phases: List of phases to intercept. Use ``InterceptPhase`` constants.
        contexts: Browsing context IDs to scope the intercept to (tab-level).
        url_patterns: Optional URL glob patterns to match (e.g. '*://example.com/*').

    Returns:
        Command dict for ``network.addIntercept``.
    """
    params = AddInterceptParams(phases=phases)
    if contexts is not None:
        params['contexts'] = contexts
    if url_patterns is not None:
        params['urlPatterns'] = [UrlPatternString(type='string', pattern=p) for p in url_patterns]
    return Command(method='network.addIntercept', params=params)


def remove_intercept(intercept_id: str) -> RemoveInterceptCommand:
    return Command(
        method='network.removeIntercept',
        params=RemoveInterceptParams(intercept=intercept_id),
    )


def continue_request(
    request_id: str,
    url: Optional[str] = None,
    method: Optional[str] = None,
    headers: Optional[list[Header]] = None,
    body: Optional[str] = None,
) -> ContinueRequestCommand:
    params = ContinueRequestParams(request=request_id)
    if url is not None:
        params['url'] = url
    if method is not None:
        params['method'] = method
    if headers is not None:
        params['headers'] = headers
    if body is not None:
        params['body'] = BytesValue(type='string', value=body)
    return Command(method='network.continueRequest', params=params)


def continue_response(
    request_id: str,
    status_code: Optional[int] = None,
    reason_phrase: Optional[str] = None,
    headers: Optional[list[Header]] = None,
) -> ContinueResponseCommand:
    params = ContinueResponseParams(request=request_id)
    if status_code is not None:
        params['statusCode'] = status_code
    if reason_phrase is not None:
        params['reasonPhrase'] = reason_phrase
    if headers is not None:
        params['headers'] = headers
    return Command(method='network.continueResponse', params=params)


def continue_with_auth(
    request_id: str,
    action: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> ContinueWithAuthCommand:
    params = ContinueWithAuthParams(request=request_id, action=action)
    if action == 'provideCredentials' and username is not None and password is not None:
        params['credentials'] = AuthCredentials(
            type='password', username=username, password=password
        )
    return Command(method='network.continueWithAuth', params=params)


def fail_request(request_id: str) -> FailRequestCommand:
    return Command(
        method='network.failRequest',
        params=FailRequestParams(request=request_id),
    )


def provide_response(
    request_id: str,
    status_code: int = 200,
    reason_phrase: Optional[str] = None,
    headers: Optional[list[Header]] = None,
    body: Optional[str] = None,
) -> ProvideResponseCommand:
    params = ProvideResponseParams(request=request_id, statusCode=status_code)
    if reason_phrase is not None:
        params['reasonPhrase'] = reason_phrase
    if headers is not None:
        params['headers'] = headers
    if body is not None:
        params['body'] = BytesValue(type='string', value=body)
    return Command(method='network.provideResponse', params=params)
