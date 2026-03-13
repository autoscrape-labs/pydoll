from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class BytesValue(TypedDict):
    type: str
    value: str


class Header(TypedDict):
    name: str
    value: BytesValue


def make_header(name: str, value: str) -> Header:
    """Build a BiDi-compliant header dict with a string value."""
    return Header(name=name, value=BytesValue(type='string', value=value))


class UrlPatternString(TypedDict):
    type: str
    pattern: str


class AuthCredentials(TypedDict):
    type: str
    username: str
    password: str


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
    action: str
    credentials: NotRequired[AuthCredentials]


class FailRequestParams(TypedDict):
    request: str


class ProvideResponseParams(TypedDict):
    request: str
    body: NotRequired[BytesValue]
    headers: NotRequired[list[Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]


class AddInterceptResult(TypedDict):
    intercept: str


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


class InterceptPhase:
    """BiDi network intercept phase constants."""

    BEFORE_REQUEST_SENT = 'beforeRequestSent'
    RESPONSE_STARTED = 'responseStarted'
    AUTH_REQUIRED = 'authRequired'


def add_intercept(
    phases: list[str],
    contexts: Optional[list[str]] = None,
    url_patterns: Optional[list[str]] = None,
) -> AddInterceptCommand:
    """
    Register a network intercept.

    Args:
        phases: Phases to intercept. Use ``InterceptPhase`` constants.
        contexts: Browsing context IDs to scope the intercept to.
        url_patterns: URL patterns to match (must be valid URL pattern strings).

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
    """
    Args:
        action: ``'provideCredentials'``, ``'default'``, or ``'cancel'``.
    """
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
