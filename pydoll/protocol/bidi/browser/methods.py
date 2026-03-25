from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import (
    Command,
    CommandResponse,
    EmptyParams,
    EmptyResult,
)
from pydoll.protocol.bidi.browser.types import (
    ClientWindow,
    ClientWindowInfo,
    ClientWindowState,
    DownloadBehavior,
    UserContext,
    UserContextInfo,
)
from pydoll.protocol.bidi.session.types import (
    ProxyConfiguration,
    UserPromptHandler,
)


class BrowserMethod(str, Enum):
    """Browser module method names."""

    CLOSE = 'browser.close'
    CREATE_USER_CONTEXT = 'browser.createUserContext'
    GET_CLIENT_WINDOWS = 'browser.getClientWindows'
    GET_USER_CONTEXTS = 'browser.getUserContexts'
    REMOVE_USER_CONTEXT = 'browser.removeUserContext'
    SET_CLIENT_WINDOW_STATE = 'browser.setClientWindowState'
    SET_DOWNLOAD_BEHAVIOR = 'browser.setDownloadBehavior'


class CreateUserContextParameters(TypedDict, total=False):
    """Parameters for browser.createUserContext command."""

    acceptInsecureCerts: bool
    proxy: ProxyConfiguration
    unhandledPromptBehavior: UserPromptHandler


class GetClientWindowsResult(TypedDict):
    """Result for browser.getClientWindows command."""

    clientWindows: list[ClientWindowInfo]


class GetUserContextsResult(TypedDict):
    """Result for browser.getUserContexts command."""

    userContexts: list[UserContextInfo]


class RemoveUserContextParameters(TypedDict):
    """Parameters for browser.removeUserContext command."""

    userContext: UserContext


class SetClientWindowStateParameters(TypedDict):
    """Parameters for browser.setClientWindowState command."""

    clientWindow: ClientWindow
    state: ClientWindowState
    width: NotRequired[int]
    height: NotRequired[int]
    x: NotRequired[int]
    y: NotRequired[int]


class SetDownloadBehaviorParameters(TypedDict):
    """Parameters for browser.setDownloadBehavior command."""

    downloadBehavior: DownloadBehavior | None
    userContexts: NotRequired[list[UserContext]]


CloseCommand = Command[EmptyParams, EmptyResult]
CloseResponse = CommandResponse[EmptyResult]

CreateUserContextCommand = Command[CreateUserContextParameters, UserContextInfo]
CreateUserContextResponse = CommandResponse[UserContextInfo]

GetClientWindowsCommand = Command[EmptyParams, GetClientWindowsResult]
GetClientWindowsResponse = CommandResponse[GetClientWindowsResult]

GetUserContextsCommand = Command[EmptyParams, GetUserContextsResult]
GetUserContextsResponse = CommandResponse[GetUserContextsResult]

RemoveUserContextCommand = Command[RemoveUserContextParameters, EmptyResult]
RemoveUserContextResponse = CommandResponse[EmptyResult]

SetClientWindowStateCommand = Command[SetClientWindowStateParameters, ClientWindowInfo]
SetClientWindowStateResponse = CommandResponse[ClientWindowInfo]

SetDownloadBehaviorCommand = Command[SetDownloadBehaviorParameters, EmptyResult]
SetDownloadBehaviorResponse = CommandResponse[EmptyResult]
