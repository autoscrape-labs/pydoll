from typing import Generic, NotRequired, TypedDict, TypeVar

T_CommandResponse = TypeVar('T_CommandResponse')


class CommandParams(TypedDict, total=False):
    """Base structure for all command parameters."""

    pass


class Command(TypedDict, Generic[T_CommandResponse]):
    """Base structure for all commands.

    Attributes:
        method: The command method name
        params: Optional dictionary of parameters for the command
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[CommandParams]


class ResponseResult(TypedDict, total=False):
    """Base structure for all response results."""

    pass


class Response(TypedDict):
    """Base structure for all responses.

    Attributes:
        id: The ID that matches the command ID
        result: The result data for the command
    """

    id: int
    result: ResponseResult


class Event(TypedDict):
    """Base structure for all events."""

    method: str
    params: NotRequired[dict[str, str]]
