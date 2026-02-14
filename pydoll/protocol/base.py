from typing import Generic, TypeVar

# TODO: typeddict comes from typing_extensions
from typing_extensions import NotRequired, TypedDict

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')
T_EventParams = TypeVar('T_EventParams')


class EmptyParams(TypedDict):
    """Empty parameters for commands."""

    pass


class EmptyResponse(TypedDict):
    """Empty response for commands."""

    pass


class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """Base structure for all commands.

    Attributes:
        method: The command method name
        params: Optional dictionary of parameters for the command
        sessionId: Optional target session identifier (flattened sessions)
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]
    sessionId: NotRequired[str]


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
