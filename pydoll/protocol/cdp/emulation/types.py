from enum import Enum

from typing_extensions import NotRequired, TypedDict


class ScreenOrientationType(str, Enum):
    """Orientation type."""

    PORTRAIT_PRIMARY = 'portraitPrimary'
    PORTRAIT_SECONDARY = 'portraitSecondary'
    LANDSCAPE_PRIMARY = 'landscapePrimary'
    LANDSCAPE_SECONDARY = 'landscapeSecondary'


class DisplayFeatureOrientation(str, Enum):
    """Orientation of a display feature in relation to screen."""

    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'


class DevicePostureType(str, Enum):
    """Current posture of the device."""

    CONTINUOUS = 'continuous'
    FOLDED = 'folded'


class VirtualTimePolicy(str, Enum):
    """advance: If the scheduler runs out of immediate work, the virtual time base may fast forward
    to allow the next delayed task (if any) to run; pause: The virtual time base may not advance;
    pauseIfNetworkFetchesPending: The virtual time base may not advance if there are any pending
    resource fetches."""

    ADVANCE = 'advance'
    PAUSE = 'pause'
    PAUSE_IF_NETWORK_FETCHES_PENDING = 'pauseIfNetworkFetchesPending'


class SensorType(str, Enum):
    """Used to specify sensor types to emulate.
    See https://w3c.github.io/sensors/#automation for more information."""

    ABSOLUTE_ORIENTATION = 'absolute-orientation'
    ACCELEROMETER = 'accelerometer'
    AMBIENT_LIGHT = 'ambient-light'
    GRAVITY = 'gravity'
    GYROSCOPE = 'gyroscope'
    LINEAR_ACCELERATION = 'linear-acceleration'
    MAGNETOMETER = 'magnetometer'
    RELATIVE_ORIENTATION = 'relative-orientation'


class PressureSource(str, Enum):
    """Pressure source type."""

    CPU = 'cpu'


class PressureState(str, Enum):
    """Pressure state."""

    NOMINAL = 'nominal'
    FAIR = 'fair'
    SERIOUS = 'serious'
    CRITICAL = 'critical'


class DisabledImageType(str, Enum):
    """Enum of image types that can be disabled."""

    AVIF = 'avif'
    WEBP = 'webp'


class SafeAreaInsets(TypedDict, total=False):
    """Safe area insets configuration."""

    top: int  # Overrides safe-area-inset-top
    topMax: int  # Overrides safe-area-max-inset-top
    left: int  # Overrides safe-area-inset-left
    leftMax: int  # Overrides safe-area-max-inset-left
    bottom: int  # Overrides safe-area-inset-bottom
    bottomMax: int  # Overrides safe-area-max-inset-bottom
    right: int  # Overrides safe-area-inset-right
    rightMax: int  # Overrides safe-area-max-inset-right


class ScreenOrientation(TypedDict):
    """Screen orientation."""

    type: ScreenOrientationType  # Orientation type
    angle: int  # Orientation angle


class DisplayFeature(TypedDict):
    """Display feature configuration."""

    # Orientation of a display feature in relation to screen
    orientation: DisplayFeatureOrientation
    # The offset from the screen origin in either the x or y
    offset: int
    # A display feature may mask content such that it is not physically displayed
    # this length along with the offset describes this area. A display feature that only split
    # content will have a 0 mask_length
    maskLength: int


class DevicePosture(TypedDict):
    """Device posture configuration."""

    type: DevicePostureType  # Current posture of the device


class MediaFeature(TypedDict):
    """Media feature configuration."""

    name: str
    value: str


class UserAgentBrandVersion(TypedDict):
    """Used to specify User Agent Client Hints to emulate.
    See https://wicg.github.io/ua-client-hints"""

    brand: str
    version: str


class UserAgentMetadata(TypedDict):
    """Used to specify User Agent Client Hints to emulate.
    See https://wicg.github.io/ua-client-hints
    Missing optional values will be filled in by the target with what it would normally use."""

    platform: str
    platformVersion: str
    architecture: str
    model: str
    mobile: bool
    brands: NotRequired[list[UserAgentBrandVersion]]  # Brands appearing in Sec-CH-UA
    fullVersionList: NotRequired[
        list[UserAgentBrandVersion]
    ]  # Brands appearing in Sec-CH-UA-Full-Version-List
    fullVersion: NotRequired[str]  # deprecated
    bitness: NotRequired[str]
    wow64: NotRequired[bool]
    formFactors: NotRequired[list[str]]  # Used to specify User Agent form-factor values.
    # See https://wicg.github.io/ua-client-hints/#sec-ch-ua-form-factors


class SensorMetadata(TypedDict, total=False):
    """Sensor metadata configuration."""

    available: bool
    minimumFrequency: float
    maximumFrequency: float


class SensorReadingSingle(TypedDict):
    """Single sensor reading value."""

    value: float


class SensorReadingXYZ(TypedDict):
    """XYZ sensor reading values."""

    x: float
    y: float
    z: float


class SensorReadingQuaternion(TypedDict):
    """Quaternion sensor reading values."""

    x: float
    y: float
    z: float
    w: float


class SensorReading(TypedDict, total=False):
    """Sensor reading configuration."""

    single: 'SensorReadingSingle'
    xyz: 'SensorReadingXYZ'
    quaternion: 'SensorReadingQuaternion'


class PressureMetadata(TypedDict, total=False):
    """Pressure metadata configuration."""

    available: bool
