from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.network.types import (
    AuthCredentials,
    BytesValue,
    Collector,
    CollectorType,
    CookieHeader,
    DataType,
    Header,
    Intercept,
    InterceptPhase,
    Request,
    SetCookieHeader,
    UrlPattern,
)


class NetworkMethod(str, Enum):
    """Network module method names."""

    ADD_DATA_COLLECTOR = 'network.addDataCollector'
    ADD_INTERCEPT = 'network.addIntercept'
    CONTINUE_REQUEST = 'network.continueRequest'
    CONTINUE_RESPONSE = 'network.continueResponse'
    CONTINUE_WITH_AUTH = 'network.continueWithAuth'
    DISOWN_DATA = 'network.disownData'
    FAIL_REQUEST = 'network.failRequest'
    GET_DATA = 'network.getData'
    PROVIDE_RESPONSE = 'network.provideResponse'
    REMOVE_DATA_COLLECTOR = 'network.removeDataCollector'
    REMOVE_INTERCEPT = 'network.removeIntercept'
    SET_CACHE_BEHAVIOR = 'network.setCacheBehavior'
    SET_EXTRA_HEADERS = 'network.setExtraHeaders'


class AddDataCollectorParameters(TypedDict):
    """Parameters for network.addDataCollector command."""

    dataTypes: list[DataType]
    maxEncodedDataSize: int
    collectorType: NotRequired[CollectorType]  # default "blob"
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class AddDataCollectorResult(TypedDict):
    """Result for network.addDataCollector command."""

    collector: Collector


class AddInterceptParameters(TypedDict):
    """Parameters for network.addIntercept command."""

    phases: list[InterceptPhase]
    contexts: NotRequired[list[BrowsingContext]]
    urlPatterns: NotRequired[list[UrlPattern]]


class AddInterceptResult(TypedDict):
    """Result for network.addIntercept command."""

    intercept: Intercept


class ContinueRequestParameters(TypedDict):
    """Parameters for network.continueRequest command."""

    request: Request
    body: NotRequired[BytesValue]
    cookies: NotRequired[list[CookieHeader]]
    headers: NotRequired[list[Header]]
    method: NotRequired[str]
    url: NotRequired[str]


class ContinueResponseParameters(TypedDict):
    """Parameters for network.continueResponse command."""

    request: Request
    cookies: NotRequired[list[SetCookieHeader]]
    credentials: NotRequired[AuthCredentials]
    headers: NotRequired[list[Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]


class ContinueWithAuthParameters(TypedDict):
    """Parameters for network.continueWithAuth command."""

    request: Request
    action: NotRequired[str]  # "provideCredentials" / "default" / "cancel"
    credentials: NotRequired[AuthCredentials]


class DisownDataParameters(TypedDict):
    """Parameters for network.disownData command."""

    dataType: DataType
    collector: Collector
    request: Request


class FailRequestParameters(TypedDict):
    """Parameters for network.failRequest command."""

    request: Request


class GetDataParameters(TypedDict):
    """Parameters for network.getData command."""

    dataType: DataType
    request: Request
    collector: NotRequired[Collector]
    disown: NotRequired[bool]  # default false


class GetDataResult(TypedDict):
    """Result for network.getData command."""

    bytes: BytesValue


class ProvideResponseParameters(TypedDict):
    """Parameters for network.provideResponse command."""

    request: Request
    body: NotRequired[BytesValue]
    cookies: NotRequired[list[SetCookieHeader]]
    headers: NotRequired[list[Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]


class RemoveDataCollectorParameters(TypedDict):
    """Parameters for network.removeDataCollector command."""

    collector: Collector


class RemoveInterceptParameters(TypedDict):
    """Parameters for network.removeIntercept command."""

    intercept: Intercept


class SetCacheBehaviorParameters(TypedDict):
    """Parameters for network.setCacheBehavior command."""

    cacheBehavior: str  # "default" / "bypass"
    contexts: NotRequired[list[BrowsingContext]]


class SetExtraHeadersParameters(TypedDict):
    """Parameters for network.setExtraHeaders command."""

    headers: list[Header]
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


AddDataCollectorCommand = Command[
    AddDataCollectorParameters, CommandResponse[AddDataCollectorResult]
]
AddDataCollectorResponse = CommandResponse[AddDataCollectorResult]

AddInterceptCommand = Command[AddInterceptParameters, CommandResponse[AddInterceptResult]]
AddInterceptResponse = CommandResponse[AddInterceptResult]

ContinueRequestCommand = Command[ContinueRequestParameters, CommandResponse[EmptyResult]]
ContinueRequestResponse = CommandResponse[EmptyResult]

ContinueResponseCommand = Command[ContinueResponseParameters, CommandResponse[EmptyResult]]
ContinueResponseResponse = CommandResponse[EmptyResult]

ContinueWithAuthCommand = Command[ContinueWithAuthParameters, CommandResponse[EmptyResult]]
ContinueWithAuthResponse = CommandResponse[EmptyResult]

DisownDataCommand = Command[DisownDataParameters, CommandResponse[EmptyResult]]
DisownDataResponse = CommandResponse[EmptyResult]

FailRequestCommand = Command[FailRequestParameters, CommandResponse[EmptyResult]]
FailRequestResponse = CommandResponse[EmptyResult]

GetDataCommand = Command[GetDataParameters, CommandResponse[GetDataResult]]
GetDataResponse = CommandResponse[GetDataResult]

ProvideResponseCommand = Command[ProvideResponseParameters, CommandResponse[EmptyResult]]
ProvideResponseResponse = CommandResponse[EmptyResult]

RemoveDataCollectorCommand = Command[RemoveDataCollectorParameters, CommandResponse[EmptyResult]]
RemoveDataCollectorResponse = CommandResponse[EmptyResult]

RemoveInterceptCommand = Command[RemoveInterceptParameters, CommandResponse[EmptyResult]]
RemoveInterceptResponse = CommandResponse[EmptyResult]

SetCacheBehaviorCommand = Command[SetCacheBehaviorParameters, CommandResponse[EmptyResult]]
SetCacheBehaviorResponse = CommandResponse[EmptyResult]

SetExtraHeadersCommand = Command[SetExtraHeadersParameters, CommandResponse[EmptyResult]]
SetExtraHeadersResponse = CommandResponse[EmptyResult]
