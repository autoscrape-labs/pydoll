from typing import Generic, TypeVar

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command as Command  # noqa: PLC0414
from pydoll.protocol.base import T_CommandParams as T_CommandParams  # noqa: PLC0414
from pydoll.protocol.base import T_CommandResponse as T_CommandResponse  # noqa: PLC0414

T_EventParams = TypeVar('T_EventParams')


class EmptyParams(TypedDict):
    """Empty parameters for commands."""

    pass


class EmptyResponse(TypedDict):
    """Empty response for commands."""

    pass


class ResponseError(TypedDict):
    """Error payload the browser sends in place of a result.

    Attributes:
        code: JSON-RPC style error code (-32000 for domain errors, -32601 unknown method...)
        message: Human readable reason
        data: Optional extra detail attached by the browser
    """

    code: int
    message: str
    data: NotRequired[str]


class Response(TypedDict, Generic[T_CommandResponse]):
    """Base structure for all responses.

    Exactly one of ``result`` or ``error`` is present for a given command id.

    Attributes:
        id: The ID that matches the command ID
        result: The result data for the command
        error: Error payload when the browser rejected the command
        sessionId: Optional target session identifier (flattened sessions)
    """

    id: int
    result: T_CommandResponse
    error: NotRequired[ResponseError]
    sessionId: NotRequired[str]


class CDPEvent(TypedDict, Generic[T_EventParams]):
    """Base structure for all events."""

    method: str
    params: NotRequired[T_EventParams]
    sessionId: NotRequired[str]
