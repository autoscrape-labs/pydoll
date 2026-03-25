from enum import Enum

from typing_extensions import NotRequired, TypedDict


Subscription = str
"""Unique subscription identifier."""


class UserPromptHandlerType(str, Enum):
    """Behavior options for user prompt handlers."""

    ACCEPT = 'accept'
    DISMISS = 'dismiss'
    IGNORE = 'ignore'


class UserPromptHandler(TypedDict, total=False):
    """Configuration of the user prompt handler per prompt type."""

    alert: UserPromptHandlerType
    beforeUnload: UserPromptHandlerType
    confirm: UserPromptHandlerType
    default: UserPromptHandlerType
    file: UserPromptHandlerType
    prompt: UserPromptHandlerType


class AutodetectProxyConfiguration(TypedDict):
    """Autodetect proxy configuration."""

    proxyType: str


class DirectProxyConfiguration(TypedDict):
    """Direct (no proxy) configuration."""

    proxyType: str


class ManualProxyConfiguration(TypedDict, total=False):
    """Manual proxy configuration with explicit proxy servers."""

    proxyType: str  # "manual" (required but total=False for optional fields)
    httpProxy: str
    sslProxy: str
    socksProxy: str
    socksVersion: int
    noProxy: list[str]


class PacProxyConfiguration(TypedDict):
    """PAC (Proxy Auto-Config) URL configuration."""

    proxyType: str  # "pac"
    proxyAutoconfigUrl: str


class SystemProxyConfiguration(TypedDict):
    """System proxy configuration."""

    proxyType: str  # "system"


ProxyConfiguration = (
    AutodetectProxyConfiguration
    | DirectProxyConfiguration
    | ManualProxyConfiguration
    | PacProxyConfiguration
    | SystemProxyConfiguration
)
"""Union of all proxy configuration variants."""


class CapabilityRequest(TypedDict, total=False):
    """A specific set of requested capabilities for a session."""

    acceptInsecureCerts: bool
    browserName: str
    browserVersion: str
    platformName: str
    proxy: ProxyConfiguration
    unhandledPromptBehavior: UserPromptHandler
    webSocketUrl: bool


class CapabilitiesRequest(TypedDict, total=False):
    """Capabilities requested for a session, with match strategies."""

    alwaysMatch: CapabilityRequest
    firstMatch: list[CapabilityRequest]


class SubscribeParameters(TypedDict):
    """Parameters for subscribing to events."""

    events: list[str]
    contexts: NotRequired[list[str]]
    userContexts: NotRequired[list[str]]


class UnsubscribeByIDRequest(TypedDict):
    """Request to remove event subscriptions identified by subscription IDs."""

    subscriptions: list[Subscription]


class UnsubscribeByAttributesRequest(TypedDict):
    """Request to unsubscribe using subscription attributes."""

    events: list[str]
