from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.fetch.types import (
    AuthChallengeResponse,
    HeaderEntry,
    RequestPattern,
)
from pydoll.protocol.cdp.io.types import StreamHandle
from pydoll.protocol.cdp.network.types import ErrorReason


class FetchMethod(str, Enum):
    """Fetch domain method names."""

    CONTINUE_REQUEST = 'Fetch.continueRequest'
    CONTINUE_RESPONSE = 'Fetch.continueResponse'
    CONTINUE_WITH_AUTH = 'Fetch.continueWithAuth'
    DISABLE = 'Fetch.disable'
    ENABLE = 'Fetch.enable'
    FAIL_REQUEST = 'Fetch.failRequest'
    FULFILL_REQUEST = 'Fetch.fulfillRequest'
    GET_RESPONSE_BODY = 'Fetch.getResponseBody'
    TAKE_RESPONSE_BODY_AS_STREAM = 'Fetch.takeResponseBodyAsStream'


RequestId = str


# Parameter types
class EnableParams(TypedDict, total=False):
    """Parameters for enabling the fetch domain."""

    patterns: list[RequestPattern]
    handleAuthRequests: bool


class FailRequestParams(TypedDict):
    """Parameters for failing a request."""

    requestId: RequestId
    errorReason: ErrorReason


class FulfillRequestParams(TypedDict, total=False):
    """Parameters for fulfilling a request."""

    requestId: RequestId
    responseCode: int
    responseHeaders: list[HeaderEntry]
    binaryResponseHeaders: str  # \0-separated name:value pairs (base64)
    body: str  # base64 encoded
    responsePhrase: str


class ContinueRequestParams(TypedDict, total=False):
    """Parameters for continuing a request."""

    requestId: RequestId
    url: str
    method: str
    postData: str  # base64 encoded
    headers: list[HeaderEntry]
    interceptResponse: bool


class ContinueWithAuthParams(TypedDict):
    """Parameters for continuing a request with authentication."""

    requestId: RequestId
    authChallengeResponse: AuthChallengeResponse


class ContinueResponseParams(TypedDict, total=False):
    """Parameters for continuing a response."""

    requestId: RequestId
    responseCode: int
    responsePhrase: str
    responseHeaders: list[HeaderEntry]
    binaryResponseHeaders: str  # \0-separated name:value pairs (base64)


class GetResponseBodyParams(TypedDict):
    """Parameters for getting response body."""

    requestId: RequestId


class TakeResponseBodyAsStreamParams(TypedDict):
    """Parameters for taking response body as stream."""

    requestId: RequestId


# Result types
class GetResponseBodyResult(TypedDict):
    """Result for getResponseBody command."""

    body: str
    base64Encoded: bool


class TakeResponseBodyAsStreamResult(TypedDict):
    """Result for takeResponseBodyAsStream command."""

    stream: StreamHandle


# Response types
GetResponseBodyResponse = Response[GetResponseBodyResult]
TakeResponseBodyAsStreamResponse = Response[TakeResponseBodyAsStreamResult]


# Command types
ContinueRequestCommand = Command[ContinueRequestParams, Response[EmptyResponse]]
ContinueResponseCommand = Command[ContinueResponseParams, Response[EmptyResponse]]
ContinueWithAuthCommand = Command[ContinueWithAuthParams, Response[EmptyResponse]]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EnableParams, Response[EmptyResponse]]
FailRequestCommand = Command[FailRequestParams, Response[EmptyResponse]]
FulfillRequestCommand = Command[FulfillRequestParams, Response[EmptyResponse]]
GetResponseBodyCommand = Command[GetResponseBodyParams, GetResponseBodyResponse]
TakeResponseBodyAsStreamCommand = Command[
    TakeResponseBodyAsStreamParams, TakeResponseBodyAsStreamResponse
]
