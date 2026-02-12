from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.emulation.methods import (
    EmulationMethod,
    SetUserAgentOverrideParams,
)

if TYPE_CHECKING:
    from pydoll.protocol.emulation.methods import SetUserAgentOverrideCommand
    from pydoll.protocol.emulation.types import UserAgentMetadata


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
