from typing import Generic, TypeVar

from typing_extensions import NotRequired, TypedDict

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')


class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """Wire structure shared by every CDP and BiDi command.

    The first type parameter is the command's ``params`` payload. The second is
    the full parsed response wrapper the remote end sends back (CDP
    ``Response[Result]`` or BiDi ``CommandResponse[Result]``). ``id`` is assigned
    by the connection layer right before the command is sent.

    Attributes:
        id: Unique command identifier assigned at send time.
        method: The command method name (e.g. "Target.getTargets", "script.evaluate").
        params: Optional parameters payload for the command.
        sessionId: Optional CDP flattened-session target identifier (unused by BiDi).
        response: Phantom field, never set at runtime. It carries the response
            type parameter into a structural position so ``execute_command`` can
            recover and return it precisely; mypy cannot infer a TypedDict type
            argument that appears in no field.
    """

    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]
    sessionId: NotRequired[str]
    response: NotRequired[T_CommandResponse]
