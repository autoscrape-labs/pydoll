from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.emulation.types import (
    ForcedColorsModeTheme,
    GeolocationCoordinates,
    GeolocationPositionError,
    NetworkConditions,
    ScreenArea,
    ScreenOrientation,
)


class EmulationMethod(str, Enum):
    """Emulation module method names."""

    SET_FORCED_COLORS_MODE_THEME_OVERRIDE = 'emulation.setForcedColorsModeThemeOverride'
    SET_GEOLOCATION_OVERRIDE = 'emulation.setGeolocationOverride'
    SET_LOCALE_OVERRIDE = 'emulation.setLocaleOverride'
    SET_NETWORK_CONDITIONS = 'emulation.setNetworkConditions'
    SET_SCREEN_ORIENTATION_OVERRIDE = 'emulation.setScreenOrientationOverride'
    SET_SCREEN_SETTINGS_OVERRIDE = 'emulation.setScreenSettingsOverride'
    SET_SCRIPTING_ENABLED = 'emulation.setScriptingEnabled'
    SET_SCROLLBAR_TYPE_OVERRIDE = 'emulation.setScrollbarTypeOverride'
    SET_TIMEZONE_OVERRIDE = 'emulation.setTimezoneOverride'
    SET_TOUCH_OVERRIDE = 'emulation.setTouchOverride'
    SET_USER_AGENT_OVERRIDE = 'emulation.setUserAgentOverride'


class SetForcedColorsModeThemeOverrideParameters(TypedDict):
    """Parameters for emulation.setForcedColorsModeThemeOverride command."""

    theme: ForcedColorsModeTheme | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetGeolocationOverrideParameters(TypedDict, total=False):
    """Parameters for emulation.setGeolocationOverride command."""

    coordinates: GeolocationCoordinates | None
    error: GeolocationPositionError
    contexts: list[BrowsingContext]
    userContexts: list[UserContext]


class SetLocaleOverrideParameters(TypedDict):
    """Parameters for emulation.setLocaleOverride command."""

    locale: str | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetNetworkConditionsParameters(TypedDict):
    """Parameters for emulation.setNetworkConditions command."""

    networkConditions: NetworkConditions | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetScreenOrientationOverrideParameters(TypedDict):
    """Parameters for emulation.setScreenOrientationOverride command."""

    screenOrientation: ScreenOrientation | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetScreenSettingsOverrideParameters(TypedDict):
    """Parameters for emulation.setScreenSettingsOverride command."""

    screenArea: ScreenArea | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetScriptingEnabledParameters(TypedDict):
    """Parameters for emulation.setScriptingEnabled command."""

    enabled: bool | None  # only false or null
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetScrollbarTypeOverrideParameters(TypedDict):
    """Parameters for emulation.setScrollbarTypeOverride command."""

    scrollbarType: str | None  # "classic" / "overlay" / null
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetTimezoneOverrideParameters(TypedDict):
    """Parameters for emulation.setTimezoneOverride command."""

    timezone: str | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetTouchOverrideParameters(TypedDict):
    """Parameters for emulation.setTouchOverride command."""

    maxTouchPoints: int | None  # >= 1
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetUserAgentOverrideParameters(TypedDict):
    """Parameters for emulation.setUserAgentOverride command."""

    userAgent: str | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


SetForcedColorsModeThemeOverrideCommand = Command[
    SetForcedColorsModeThemeOverrideParameters, CommandResponse[EmptyResult]
]
SetForcedColorsModeThemeOverrideResponse = CommandResponse[EmptyResult]

SetGeolocationOverrideCommand = Command[
    SetGeolocationOverrideParameters, CommandResponse[EmptyResult]
]
SetGeolocationOverrideResponse = CommandResponse[EmptyResult]

SetLocaleOverrideCommand = Command[SetLocaleOverrideParameters, CommandResponse[EmptyResult]]
SetLocaleOverrideResponse = CommandResponse[EmptyResult]

SetNetworkConditionsCommand = Command[SetNetworkConditionsParameters, CommandResponse[EmptyResult]]
SetNetworkConditionsResponse = CommandResponse[EmptyResult]

SetScreenOrientationOverrideCommand = Command[
    SetScreenOrientationOverrideParameters, CommandResponse[EmptyResult]
]
SetScreenOrientationOverrideResponse = CommandResponse[EmptyResult]

SetScreenSettingsOverrideCommand = Command[
    SetScreenSettingsOverrideParameters, CommandResponse[EmptyResult]
]
SetScreenSettingsOverrideResponse = CommandResponse[EmptyResult]

SetScriptingEnabledCommand = Command[SetScriptingEnabledParameters, CommandResponse[EmptyResult]]
SetScriptingEnabledResponse = CommandResponse[EmptyResult]

SetScrollbarTypeOverrideCommand = Command[
    SetScrollbarTypeOverrideParameters, CommandResponse[EmptyResult]
]
SetScrollbarTypeOverrideResponse = CommandResponse[EmptyResult]

SetTimezoneOverrideCommand = Command[SetTimezoneOverrideParameters, CommandResponse[EmptyResult]]
SetTimezoneOverrideResponse = CommandResponse[EmptyResult]

SetTouchOverrideCommand = Command[SetTouchOverrideParameters, CommandResponse[EmptyResult]]
SetTouchOverrideResponse = CommandResponse[EmptyResult]

SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParameters, CommandResponse[EmptyResult]]
SetUserAgentOverrideResponse = CommandResponse[EmptyResult]
