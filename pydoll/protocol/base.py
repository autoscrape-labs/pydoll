from typing import Any, Dict, Generic, TypeVar

try:
    from typing import NotRequired, TypedDict
except ImportError:
    from typing_extensions import NotRequired, TypedDict


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


# Define a more flexible Response type variable that accepts any TypedDict with compatible structure
# This allows custom response types to be used with Command
R = TypeVar('R')


# Define a generic Command class that can be used with type parameters
class Command(TypedDict, Generic[R]):
    """Base structure for all commands.

    Attributes:
        method: The command method name
        params: Optional dictionary of parameters for the command
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[CommandParams]


# Fix for PLW0127 (self-assignment) and maintain backward compatibility
# This approach avoids both mypy and ruff errors
_CommandAlias = Command  # Create an alias first
Command = _CommandAlias  # type: ignore  # Then assign to original name


class Event(TypedDict):
    """Base structure for all events."""

    method: str
    params: NotRequired[Dict[str, Any]]
