
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from pydoll.constants import NetworkErrorReason, RequestMethod
from pydoll.protocol.base import CommandParams
from pydoll.protocol.fetch.types import (
    AuthChallengeResponseDict,
    HeaderEntry,
    RequestPattern,
)


class ContinueRequestParams(CommandParams):
    """Parameters for continuing a request."""

    requestId: str
    url: NotRequired[str]
    method: NotRequired[RequestMethod]
    postData: NotRequired[str]
    headers: NotRequired[list[HeaderEntry]]
    interceptResponse: NotRequired[bool]


class ContinueWithAuthParams(CommandParams):
    requestId: str
    authChallengeResponse: AuthChallengeResponseDict


class FetchEnableParams(CommandParams):
    patterns: NotRequired[list[RequestPattern]]
    handleAuthRequests: NotRequired[bool]


class FailRequestParams(CommandParams):
    requestId: str
    errorReason: NetworkErrorReason


class FulfillRequestParams(CommandParams):
    requestId: str
    responseCode: int
    responseHeaders: NotRequired[list[HeaderEntry]]
    body: NotRequired[dict]
    responsePhrase: NotRequired[str]


class GetResponseBodyParams(CommandParams):
    requestId: str


class TakeResponseBodyAsStreamParams(CommandParams):
    requestId: str


class ContinueResponseParams(CommandParams):
    requestId: str
    responseCode: NotRequired[int]
    responsePhrase: NotRequired[str]
    responseHeaders: NotRequired[list[HeaderEntry]]
