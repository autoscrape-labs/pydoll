from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response
from pydoll.protocol.emulation.types import UserAgentMetadata


class EmulationMethod(str, Enum):
    SET_USER_AGENT_OVERRIDE = 'Emulation.setUserAgentOverride'


class SetUserAgentOverrideParams(TypedDict):
    """Parameters for overriding user agent string.

    See https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setUserAgentOverride
    """

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParams, Response[EmptyResponse]]
