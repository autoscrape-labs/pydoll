from typing import Any, Dict, Generic, TypedDict, TypeVar

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class CommandParams(TypedDict, total=False):
    """Base structure for all command parameters."""

    pass


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


# Define Response type variable after Response class is defined
R = TypeVar('R', bound=Response)


class CommandGeneric(TypedDict, Generic[R]):
    """Base generic structure for all commands with response type parameter.

    Attributes:
        method: The command method name
        params: Optional dictionary of parameters for the command
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[CommandParams]


# Create non-generic version of Command for backward compatibility
class Command(TypedDict):
    """Base structure for all commands.

    Attributes:
        method: The command method name
        params: Optional dictionary of parameters for the command
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[CommandParams]


# Type alias to support both Command[ResponseType] and Command usage
# This is needed for backward compatibility
Command = CommandGeneric  # type: ignore


class Event(TypedDict):
    """Base structure for all events."""

    method: str
    params: NotRequired[Dict[str, Any]]
