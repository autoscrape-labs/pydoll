from enum import Enum
from typing import Literal

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.script.types import SharedReference


class PointerType(str, Enum):
    """Pointer device types."""

    MOUSE = 'mouse'
    PEN = 'pen'
    TOUCH = 'touch'


class ElementOrigin(TypedDict):
    """Element used as a coordinate origin."""

    type: Literal['element']
    element: SharedReference


Origin = str | ElementOrigin
"""Action origin: "viewport", "pointer", or ElementOrigin."""


class PointerParameters(TypedDict, total=False):
    """Parameters for pointer input sources."""

    pointerType: PointerType  # default "mouse"


class PointerCommonProperties(TypedDict, total=False):
    """Properties common to pointer actions."""

    width: int
    height: int
    pressure: float  # 0.0..1.0
    tangentialPressure: float  # -1.0..1.0
    twist: int  # 0..359
    altitudeAngle: float  # 0.0..PI/2
    azimuthAngle: float  # 0.0..2*PI


class PauseAction(TypedDict):
    """Pause action."""

    type: Literal['pause']
    duration: NotRequired[int]


class KeyDownAction(TypedDict):
    """Key down action."""

    type: Literal['keyDown']
    value: str


class KeyUpAction(TypedDict):
    """Key up action."""

    type: Literal['keyUp']
    value: str


class PointerUpAction(TypedDict):
    """Pointer up action."""

    type: Literal['pointerUp']
    button: int


class PointerDownAction(TypedDict):
    """Pointer down action."""

    type: Literal['pointerDown']
    button: int
    width: NotRequired[int]
    height: NotRequired[int]
    pressure: NotRequired[float]
    tangentialPressure: NotRequired[float]
    twist: NotRequired[int]
    altitudeAngle: NotRequired[float]
    azimuthAngle: NotRequired[float]


class PointerMoveAction(TypedDict):
    """Pointer move action."""

    type: Literal['pointerMove']
    x: float
    y: float
    duration: NotRequired[int]
    origin: NotRequired[Origin]
    width: NotRequired[int]
    height: NotRequired[int]
    pressure: NotRequired[float]
    tangentialPressure: NotRequired[float]
    twist: NotRequired[int]
    altitudeAngle: NotRequired[float]
    azimuthAngle: NotRequired[float]


class WheelScrollAction(TypedDict):
    """Wheel scroll action."""

    type: Literal['scroll']
    x: int
    y: int
    deltaX: int
    deltaY: int
    duration: NotRequired[int]
    origin: NotRequired[Origin]


KeyAction = PauseAction | KeyDownAction | KeyUpAction
"""An action belonging to a key input source."""

PointerAction = PauseAction | PointerDownAction | PointerUpAction | PointerMoveAction
"""An action belonging to a pointer input source."""

WheelAction = PauseAction | WheelScrollAction
"""An action belonging to a wheel input source."""


class NoneSourceActions(TypedDict):
    """None input source (pause only)."""

    type: Literal['none']
    id: str
    actions: list[PauseAction]


class KeySourceActions(TypedDict):
    """Key input source."""

    type: Literal['key']
    id: str
    actions: list[KeyAction]


class PointerSourceActions(TypedDict):
    """Pointer input source."""

    type: Literal['pointer']
    id: str
    parameters: NotRequired[PointerParameters]
    actions: list[PointerAction]


class WheelSourceActions(TypedDict):
    """Wheel input source."""

    type: Literal['wheel']
    id: str
    actions: list[WheelAction]


SourceActions = NoneSourceActions | KeySourceActions | PointerSourceActions | WheelSourceActions
