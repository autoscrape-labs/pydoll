from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.script.types import SharedReference


class PointerType(str, Enum):
    """Pointer device types."""

    MOUSE = 'mouse'
    PEN = 'pen'
    TOUCH = 'touch'


class ElementOrigin(TypedDict):
    """Element used as a coordinate origin."""

    type: str  # "element"
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

    type: str  # "pause"
    duration: NotRequired[int]


class KeyDownAction(TypedDict):
    """Key down action."""

    type: str  # "keyDown"
    value: str


class KeyUpAction(TypedDict):
    """Key up action."""

    type: str  # "keyUp"
    value: str


class PointerUpAction(TypedDict):
    """Pointer up action."""

    type: str  # "pointerUp"
    button: int


class PointerDownAction(TypedDict):
    """Pointer down action."""

    type: str  # "pointerDown"
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

    type: str  # "pointerMove"
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

    type: str  # "scroll"
    x: int
    y: int
    deltaX: int
    deltaY: int
    duration: NotRequired[int]
    origin: NotRequired[Origin]


class NoneSourceActions(TypedDict):
    """None input source (pause only)."""

    type: str  # "none"
    id: str
    actions: list[PauseAction]


class KeySourceActions(TypedDict):
    """Key input source."""

    type: str  # "key"
    id: str
    actions: list[PauseAction | KeyDownAction | KeyUpAction]


class PointerSourceActions(TypedDict):
    """Pointer input source."""

    type: str  # "pointer"
    id: str
    parameters: NotRequired[PointerParameters]
    actions: list[PauseAction | PointerDownAction | PointerUpAction | PointerMoveAction]


class WheelSourceActions(TypedDict):
    """Wheel input source."""

    type: str  # "wheel"
    id: str
    actions: list[PauseAction | WheelScrollAction]


SourceActions = NoneSourceActions | KeySourceActions | PointerSourceActions | WheelSourceActions
