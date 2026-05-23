from typing import Generic, TypeVar

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command as Command  # noqa: PLC0414
from pydoll.protocol.base import T_CommandParams as T_CommandParams  # noqa: PLC0414

T_CommandResult = TypeVar('T_CommandResult')
T_EventParams = TypeVar('T_EventParams')


class EmptyParams(TypedDict):
    """Empty parameters for commands that take no parameters."""

    pass


class EmptyResult(TypedDict):
    """Empty result for commands that return no data."""

    pass


class CommandResponse(TypedDict, Generic[T_CommandResult]):
    """Base structure for successful command responses from the remote end.

    Attributes:
        type: Always "success" for successful responses
        id: The ID matching the originating command
        result: The result data for the command
    """

    type: str
    id: int
    result: T_CommandResult


class ErrorResponse(TypedDict):
    """Base structure for error responses from the remote end.

    Attributes:
        type: Always "error" for error responses
        id: The ID matching the originating command, or null
        error: The error code string
        message: A human-readable error message
        stacktrace: Optional stack trace string
    """

    type: str
    id: int
    error: str
    message: str
    stacktrace: NotRequired[str]


class BiDiEvent(TypedDict, Generic[T_EventParams]):
    """Base structure for all BiDi events emitted by the remote end.

    Attributes:
        type: Always "event" for events
        method: The event method name (e.g. "browsingContext.load")
        params: The event parameters
    """

    type: str
    method: str
    params: NotRequired[T_EventParams]
