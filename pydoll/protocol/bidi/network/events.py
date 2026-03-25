from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import BiDiEvent
from pydoll.protocol.bidi.network.types import (
    BaseParameters,
    Initiator,
    ResponseData,
)


class NetworkEvent(str, Enum):
    """Network module event names."""

    AUTH_REQUIRED = 'network.authRequired'
    BEFORE_REQUEST_SENT = 'network.beforeRequestSent'
    FETCH_ERROR = 'network.fetchError'
    RESPONSE_COMPLETED = 'network.responseCompleted'
    RESPONSE_STARTED = 'network.responseStarted'


class AuthRequiredParameters(BaseParameters):
    """Parameters for network.authRequired event."""

    response: ResponseData


class BeforeRequestSentParameters(BaseParameters):
    """Parameters for network.beforeRequestSent event."""

    initiator: NotRequired[Initiator]


class FetchErrorParameters(BaseParameters):
    """Parameters for network.fetchError event."""

    errorText: str


class ResponseCompletedParameters(BaseParameters):
    """Parameters for network.responseCompleted event."""

    response: ResponseData


class ResponseStartedParameters(BaseParameters):
    """Parameters for network.responseStarted event."""

    response: ResponseData


AuthRequiredEvent = BiDiEvent[AuthRequiredParameters]
BeforeRequestSentEvent = BiDiEvent[BeforeRequestSentParameters]
FetchErrorEvent = BiDiEvent[FetchErrorParameters]
ResponseCompletedEvent = BiDiEvent[ResponseCompletedParameters]
ResponseStartedEvent = BiDiEvent[ResponseStartedParameters]
