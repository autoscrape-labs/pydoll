from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response
from pydoll.protocol.emulation.types import (
    DevicePosture,
    DisplayFeature,
    ScreenOrientation,
    UserAgentMetadata,
)
from pydoll.protocol.page.types import Viewport


class EmulationMethod(str, Enum):
    SET_USER_AGENT_OVERRIDE = 'Emulation.setUserAgentOverride'
    SET_TIMEZONE_OVERRIDE = 'Emulation.setTimezoneOverride'
    SET_GEOLOCATION_OVERRIDE = 'Emulation.setGeolocationOverride'
    SET_DEVICE_METRICS_OVERRIDE = 'Emulation.setDeviceMetricsOverride'
    SET_LOCALE_OVERRIDE = 'Emulation.setLocaleOverride'
    SET_HARDWARE_CONCURRENCY_OVERRIDE = 'Emulation.setHardwareConcurrencyOverride'


class SetUserAgentOverrideParams(TypedDict):
    """Parameters for overriding user agent string.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setUserAgentOverride
    """

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParams, Response[EmptyResponse]]


class SetTimezoneOverrideParams(TypedDict):
    """Parameters for overriding timezone.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setTimezoneOverride
    """

    timezoneId: str


SetTimezoneOverrideCommand = Command[SetTimezoneOverrideParams, Response[EmptyResponse]]


class SetGeolocationOverrideParams(TypedDict, total=False):
    """Parameters for overriding geolocation.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setGeolocationOverride
    """

    latitude: float
    longitude: float
    accuracy: float
    altitude: float
    altitudeAccuracy: float
    heading: float
    speed: float


SetGeolocationOverrideCommand = Command[SetGeolocationOverrideParams, Response[EmptyResponse]]


class SetDeviceMetricsOverrideParams(TypedDict):
    """Parameters for overriding device metrics.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setDeviceMetricsOverride
    """

    width: int
    height: int
    deviceScaleFactor: float
    mobile: bool
    scale: NotRequired[float]
    screenWidth: NotRequired[int]
    screenHeight: NotRequired[int]
    positionX: NotRequired[int]
    positionY: NotRequired[int]
    dontSetVisibleSize: NotRequired[bool]
    screenOrientation: NotRequired[ScreenOrientation]
    viewport: NotRequired[Viewport]
    displayFeature: NotRequired[DisplayFeature]
    devicePosture: NotRequired[DevicePosture]


SetDeviceMetricsOverrideCommand = Command[SetDeviceMetricsOverrideParams, Response[EmptyResponse]]


class SetLocaleOverrideParams(TypedDict, total=False):
    """Parameters for overriding locale.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setLocaleOverride
    """

    locale: str


SetLocaleOverrideCommand = Command[SetLocaleOverrideParams, Response[EmptyResponse]]


class SetHardwareConcurrencyOverrideParams(TypedDict):
    """Parameters for overriding navigator.hardwareConcurrency.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setHardwareConcurrencyOverride
    """

    hardwareConcurrency: int


SetHardwareConcurrencyOverrideCommand = Command[
    SetHardwareConcurrencyOverrideParams, Response[EmptyResponse]
]
