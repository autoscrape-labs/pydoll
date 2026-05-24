from enum import Enum

from typing_extensions import NotRequired, TypedDict


class ForcedColorsModeTheme(str, Enum):
    """Forced colors mode theme options."""

    LIGHT = 'light'
    DARK = 'dark'


class GeolocationCoordinates(TypedDict):
    """Geolocation coordinates for emulation."""

    latitude: float  # -90.0..90.0
    longitude: float  # -180.0..180.0
    accuracy: NotRequired[float]  # >= 0.0, default 1.0
    altitude: NotRequired[float | None]  # default null
    altitudeAccuracy: NotRequired[float | None]  # >= 0.0, default null
    heading: NotRequired[float | None]  # 0.0..360.0, default null
    speed: NotRequired[float | None]  # >= 0.0, default null


class GeolocationPositionError(TypedDict):
    """Geolocation position error for emulation."""

    type: str  # "positionUnavailable"


class NetworkConditionsOffline(TypedDict):
    """Offline network conditions."""

    type: str  # "offline"


NetworkConditions = NetworkConditionsOffline


class ScreenArea(TypedDict):
    """Screen area dimensions for emulation."""

    width: int
    height: int


class ScreenOrientationNatural(str, Enum):
    """Natural screen orientation."""

    PORTRAIT = 'portrait'
    LANDSCAPE = 'landscape'


class ScreenOrientationType(str, Enum):
    """Screen orientation type."""

    PORTRAIT_PRIMARY = 'portrait-primary'
    PORTRAIT_SECONDARY = 'portrait-secondary'
    LANDSCAPE_PRIMARY = 'landscape-primary'
    LANDSCAPE_SECONDARY = 'landscape-secondary'


class ScreenOrientation(TypedDict):
    """Screen orientation for emulation."""

    natural: ScreenOrientationNatural
    type: ScreenOrientationType
