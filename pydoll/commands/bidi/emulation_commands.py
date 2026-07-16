from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.emulation.methods import (
    EmulationMethod,
    SetForcedColorsModeThemeOverrideParameters,
    SetGeolocationOverrideParameters,
    SetLocaleOverrideParameters,
    SetNetworkConditionsParameters,
    SetScreenOrientationOverrideParameters,
    SetScreenSettingsOverrideParameters,
    SetScriptingEnabledParameters,
    SetScrollbarTypeOverrideParameters,
    SetTimezoneOverrideParameters,
    SetTouchOverrideParameters,
    SetUserAgentOverrideParameters,
)
from pydoll.protocol.bidi.emulation.types import (
    ForcedColorsModeTheme,
    GeolocationCoordinates,
    NetworkConditions,
    ScreenArea,
    ScreenOrientation,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.emulation.methods import (
        SetForcedColorsModeThemeOverrideCommand,
        SetGeolocationOverrideCommand,
        SetLocaleOverrideCommand,
        SetNetworkConditionsCommand,
        SetScreenOrientationOverrideCommand,
        SetScreenSettingsOverrideCommand,
        SetScriptingEnabledCommand,
        SetScrollbarTypeOverrideCommand,
        SetTimezoneOverrideCommand,
        SetTouchOverrideCommand,
        SetUserAgentOverrideCommand,
    )
    from pydoll.protocol.bidi.emulation.types import GeolocationPositionError


class EmulationCommands:
    """Command builders for the BiDi emulation module."""

    @staticmethod
    def set_forced_colors_mode_theme_override(
        theme: ForcedColorsModeTheme | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetForcedColorsModeThemeOverrideCommand:
        """Generates a command to override forced colors mode theme."""
        params = SetForcedColorsModeThemeOverrideParameters(theme=theme)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_FORCED_COLORS_MODE_THEME_OVERRIDE, params=params)

    @staticmethod
    def set_geolocation_override(
        coordinates: Optional[GeolocationCoordinates] = None,
        error: Optional[GeolocationPositionError] = None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetGeolocationOverrideCommand:
        """Generates a command to override geolocation."""
        params = SetGeolocationOverrideParameters()
        if coordinates is not None:
            params['coordinates'] = coordinates
        if error is not None:
            params['error'] = error
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_GEOLOCATION_OVERRIDE, params=params)

    @staticmethod
    def set_locale_override(
        locale: str | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetLocaleOverrideCommand:
        """Generates a command to override locale."""
        params = SetLocaleOverrideParameters(locale=locale)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_LOCALE_OVERRIDE, params=params)

    @staticmethod
    def set_network_conditions(
        network_conditions: NetworkConditions | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetNetworkConditionsCommand:
        """Generates a command to emulate network conditions."""
        params = SetNetworkConditionsParameters(networkConditions=network_conditions)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_NETWORK_CONDITIONS, params=params)

    @staticmethod
    def set_screen_orientation_override(
        screen_orientation: ScreenOrientation | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetScreenOrientationOverrideCommand:
        """Generates a command to override screen orientation."""
        params = SetScreenOrientationOverrideParameters(screenOrientation=screen_orientation)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_SCREEN_ORIENTATION_OVERRIDE, params=params)

    @staticmethod
    def set_screen_settings_override(
        screen_area: ScreenArea | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetScreenSettingsOverrideCommand:
        """Generates a command to override screen settings."""
        params = SetScreenSettingsOverrideParameters(screenArea=screen_area)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_SCREEN_SETTINGS_OVERRIDE, params=params)

    @staticmethod
    def set_scripting_enabled(
        enabled: bool | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetScriptingEnabledCommand:
        """Generates a command to enable/disable scripting."""
        params = SetScriptingEnabledParameters(enabled=enabled)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_SCRIPTING_ENABLED, params=params)

    @staticmethod
    def set_scrollbar_type_override(
        scrollbar_type: str | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetScrollbarTypeOverrideCommand:
        """Generates a command to override scrollbar type."""
        params = SetScrollbarTypeOverrideParameters(scrollbarType=scrollbar_type)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_SCROLLBAR_TYPE_OVERRIDE, params=params)

    @staticmethod
    def set_timezone_override(
        timezone: str | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetTimezoneOverrideCommand:
        """Generates a command to override timezone."""
        params = SetTimezoneOverrideParameters(timezone=timezone)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_TIMEZONE_OVERRIDE, params=params)

    @staticmethod
    def set_touch_override(
        max_touch_points: int | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetTouchOverrideCommand:
        """Generates a command to override touch support."""
        params = SetTouchOverrideParameters(maxTouchPoints=max_touch_points)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_TOUCH_OVERRIDE, params=params)

    @staticmethod
    def set_user_agent_override(
        user_agent: str | None,
        contexts: Optional[list[str]] = None,
        user_contexts: Optional[list[str]] = None,
    ) -> SetUserAgentOverrideCommand:
        """Generates a command to override user agent."""
        params = SetUserAgentOverrideParameters(userAgent=user_agent)
        if contexts is not None:
            params['contexts'] = contexts
        if user_contexts is not None:
            params['userContexts'] = user_contexts
        return Command(method=EmulationMethod.SET_USER_AGENT_OVERRIDE, params=params)
