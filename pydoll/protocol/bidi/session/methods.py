from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.bidi.base import (
    Command,
    CommandResponse,
    EmptyParams,
    EmptyResult,
)
from pydoll.protocol.bidi.session.types import (
    CapabilitiesRequest,
    ProxyConfiguration,
    SubscribeParameters,
    Subscription,
    UnsubscribeByAttributesRequest,
    UnsubscribeByIDRequest,
    UserPromptHandler,
)


class SessionMethod(str, Enum):
    """Session module method names."""

    STATUS = 'session.status'
    NEW = 'session.new'
    END = 'session.end'
    SUBSCRIBE = 'session.subscribe'
    UNSUBSCRIBE = 'session.unsubscribe'


class StatusResult(TypedDict):
    """Result for session.status command."""

    ready: bool
    message: str


class NewParameters(TypedDict):
    """Parameters for session.new command."""

    capabilities: CapabilitiesRequest


class NewResultCapabilities(TypedDict, total=False):
    """Capabilities returned by session.new."""

    acceptInsecureCerts: bool
    browserName: str
    browserVersion: str
    platformName: str
    setWindowRect: bool
    userAgent: str
    proxy: ProxyConfiguration
    unhandledPromptBehavior: UserPromptHandler
    webSocketUrl: str


class NewResult(TypedDict):
    """Result for session.new command."""

    sessionId: str
    capabilities: NewResultCapabilities


class SubscribeResult(TypedDict):
    """Result for session.subscribe command."""

    subscription: Subscription


UnsubscribeParameters = UnsubscribeByAttributesRequest | UnsubscribeByIDRequest

StatusCommand = Command[EmptyParams, CommandResponse[StatusResult]]
StatusResponse = CommandResponse[StatusResult]

NewCommand = Command[NewParameters, CommandResponse[NewResult]]
NewResponse = CommandResponse[NewResult]

EndCommand = Command[EmptyParams, CommandResponse[EmptyResult]]
EndResponse = CommandResponse[EmptyResult]

SubscribeCommand = Command[SubscribeParameters, CommandResponse[SubscribeResult]]
SubscribeResponse = CommandResponse[SubscribeResult]

UnsubscribeCommand = Command[UnsubscribeParameters, CommandResponse[EmptyResult]]
UnsubscribeResponse = CommandResponse[EmptyResult]
