from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.emulation.methods import (
    EmulationMethod,
    SetDeviceMetricsOverrideParams,
    SetGeolocationOverrideParams,
    SetHardwareConcurrencyOverrideParams,
    SetLocaleOverrideParams,
    SetTimezoneOverrideParams,
    SetUserAgentOverrideParams,
)

if TYPE_CHECKING:
    from pydoll.protocol.emulation.methods import (
        SetDeviceMetricsOverrideCommand,
        SetGeolocationOverrideCommand,
        SetHardwareConcurrencyOverrideCommand,
        SetLocaleOverrideCommand,
        SetTimezoneOverrideCommand,
        SetUserAgentOverrideCommand,
    )
    from pydoll.protocol.emulation.types import (
        DevicePosture,
        DisplayFeature,
        ScreenOrientation,
        UserAgentMetadata,
    )
    from pydoll.protocol.page.types import Viewport


class EmulationCommands:
    """
    Implementation of Chrome DevTools Protocol for the Emulation domain.

    This class provides commands for emulating different environments,
    including user agent overrides, device metrics, and other browser
    characteristics useful for testing and automation.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/
    """

    @staticmethod
    def set_user_agent_override(
        user_agent: str,
        accept_language: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent_metadata: Optional[UserAgentMetadata] = None,
    ) -> SetUserAgentOverrideCommand:
        """
        Overrides the browser's User-Agent string via the Emulation domain.

        This is the canonical CDP method for User-Agent override. It modifies
        both HTTP headers and navigator JavaScript properties, ensuring
        consistency between all layers.

        When userAgentMetadata is provided, Client Hint headers (Sec-CH-UA-*)
        will also be sent consistently with the overridden User-Agent.

        Args:
            user_agent: Complete User-Agent string to use.
            accept_language: Browser language preference (e.g., 'en-US,en;q=0.9').
            platform: Value for navigator.platform (e.g., 'Win32', 'MacIntel').
            user_agent_metadata: Client Hints metadata for Sec-CH-UA-* headers
                and navigator.userAgentData.

        Returns:
            SetUserAgentOverrideCommand: CDP command to override user agent.
        """
        params = SetUserAgentOverrideParams(userAgent=user_agent)
        if accept_language is not None:
            params['acceptLanguage'] = accept_language
        if platform is not None:
            params['platform'] = platform
        if user_agent_metadata is not None:
            params['userAgentMetadata'] = user_agent_metadata
        return Command(method=EmulationMethod.SET_USER_AGENT_OVERRIDE, params=params)

    @staticmethod
    def set_timezone_override(timezone_id: str) -> SetTimezoneOverrideCommand:
        """Override the default timezone with an IANA timezone identifier.

        Args:
            timezone_id: IANA timezone (e.g., 'America/New_York').
                Empty string disables the override.

        Returns:
            SetTimezoneOverrideCommand: CDP command to override timezone.
        """
        params = SetTimezoneOverrideParams(timezoneId=timezone_id)
        return Command(method=EmulationMethod.SET_TIMEZONE_OVERRIDE, params=params)

    @staticmethod
    def set_geolocation_override(
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy: Optional[float] = None,
        altitude: Optional[float] = None,
        altitude_accuracy: Optional[float] = None,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
    ) -> SetGeolocationOverrideCommand:
        """Override the Geolocation Position reported by the browser.

        Args:
            latitude: Mock latitude.
            longitude: Mock longitude.
            accuracy: Mock accuracy in meters.
            altitude: Mock altitude in meters.
            altitude_accuracy: Mock altitude accuracy in meters.
            heading: Mock heading in degrees (0-360).
            speed: Mock speed in m/s.

        Returns:
            SetGeolocationOverrideCommand: CDP command to override geolocation.
        """
        params = SetGeolocationOverrideParams()
        if latitude is not None:
            params['latitude'] = latitude
        if longitude is not None:
            params['longitude'] = longitude
        if accuracy is not None:
            params['accuracy'] = accuracy
        if altitude is not None:
            params['altitude'] = altitude
        if altitude_accuracy is not None:
            params['altitudeAccuracy'] = altitude_accuracy
        if heading is not None:
            params['heading'] = heading
        if speed is not None:
            params['speed'] = speed
        return Command(method=EmulationMethod.SET_GEOLOCATION_OVERRIDE, params=params)

    @staticmethod
    def set_device_metrics_override(
        width: int,
        height: int,
        device_scale_factor: float,
        mobile: bool,
        *,
        scale: Optional[float] = None,
        screen_width: Optional[int] = None,
        screen_height: Optional[int] = None,
        position_x: Optional[int] = None,
        position_y: Optional[int] = None,
        dont_set_visible_size: Optional[bool] = None,
        screen_orientation: Optional[ScreenOrientation] = None,
        viewport: Optional[Viewport] = None,
        display_feature: Optional[DisplayFeature] = None,
        device_posture: Optional[DevicePosture] = None,
    ) -> SetDeviceMetricsOverrideCommand:
        """Override device screen metrics.

        Args:
            width: Overriding width in pixels (0 disables).
            height: Overriding height in pixels (0 disables).
            device_scale_factor: Device scale factor (0 disables).
            mobile: Whether to emulate mobile device.
            scale: Scale to apply to resulting view image.
            screen_width: Overriding screen width in pixels.
            screen_height: Overriding screen height in pixels.
            position_x: Overriding view X position on screen.
            position_y: Overriding view Y position on screen.
            dont_set_visible_size: Do not set visible view size.
            screen_orientation: Screen orientation override.
            viewport: Visible area of the page override.
            display_feature: Multi-segment screen display feature.
            device_posture: Foldable device posture setting.

        Returns:
            SetDeviceMetricsOverrideCommand: CDP command to override device metrics.
        """
        params = SetDeviceMetricsOverrideParams(
            width=width,
            height=height,
            deviceScaleFactor=device_scale_factor,
            mobile=mobile,
        )
        if scale is not None:
            params['scale'] = scale
        if screen_width is not None:
            params['screenWidth'] = screen_width
        if screen_height is not None:
            params['screenHeight'] = screen_height
        if position_x is not None:
            params['positionX'] = position_x
        if position_y is not None:
            params['positionY'] = position_y
        if dont_set_visible_size is not None:
            params['dontSetVisibleSize'] = dont_set_visible_size
        if screen_orientation is not None:
            params['screenOrientation'] = screen_orientation
        if viewport is not None:
            params['viewport'] = viewport
        if display_feature is not None:
            params['displayFeature'] = display_feature
        if device_posture is not None:
            params['devicePosture'] = device_posture
        return Command(method=EmulationMethod.SET_DEVICE_METRICS_OVERRIDE, params=params)

    @staticmethod
    def set_locale_override(locale: str = '') -> SetLocaleOverrideCommand:
        """Override the default locale used by the browser.

        Args:
            locale: ICU style C locale (e.g., 'en_US').
                Empty string disables the override.

        Returns:
            SetLocaleOverrideCommand: CDP command to override locale.
        """
        params = SetLocaleOverrideParams()
        if locale:
            params['locale'] = locale
        return Command(method=EmulationMethod.SET_LOCALE_OVERRIDE, params=params)

    @staticmethod
    def set_hardware_concurrency_override(
        hardware_concurrency: int,
    ) -> SetHardwareConcurrencyOverrideCommand:
        """Override the value reported by navigator.hardwareConcurrency.

        Applied natively by the browser, so the reported getter still looks
        native to fingerprinting scripts (unlike a JavaScript override).

        Args:
            hardware_concurrency: Number of logical processors to report (>= 1).

        Returns:
            SetHardwareConcurrencyOverrideCommand: CDP command to override the value.
        """
        params = SetHardwareConcurrencyOverrideParams(hardwareConcurrency=hardware_concurrency)
        return Command(method=EmulationMethod.SET_HARDWARE_CONCURRENCY_OVERRIDE, params=params)
