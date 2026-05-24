from typing import Generic, TypeVar

# TODO: typeddict comes from typing_extensions
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


class Response(TypedDict, Generic[T_CommandResponse]):
    """Base structure for all responses.

    Attributes:
        id: The ID that matches the command ID
        result: The result data for the command
        sessionId: Optional target session identifier (flattened sessions)
    """

    id: int
    result: T_CommandResponse
    sessionId: NotRequired[str]


class CDPEvent(TypedDict, Generic[T_EventParams]):
    """Base structure for all events."""

    method: str
    params: NotRequired[T_EventParams]
    sessionId: NotRequired[str]
