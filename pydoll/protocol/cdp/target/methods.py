from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.browser.types import BrowserContextID, WindowState
from pydoll.protocol.cdp.target.types import (
    RemoteLocation,
    SessionID,
    TargetFilter,
    TargetID,
    TargetInfo,
)


class TargetMethod(str, Enum):
    """Target domain method names."""

    ACTIVATE_TARGET = 'Target.activateTarget'
    ATTACH_TO_TARGET = 'Target.attachToTarget'
    ATTACH_TO_BROWSER_TARGET = 'Target.attachToBrowserTarget'
    CLOSE_TARGET = 'Target.closeTarget'
    EXPOSE_DEV_TOOLS_PROTOCOL = 'Target.exposeDevToolsProtocol'
    CREATE_BROWSER_CONTEXT = 'Target.createBrowserContext'
    GET_BROWSER_CONTEXTS = 'Target.getBrowserContexts'
    CREATE_TARGET = 'Target.createTarget'
    DETACH_FROM_TARGET = 'Target.detachFromTarget'
    DISPOSE_BROWSER_CONTEXT = 'Target.disposeBrowserContext'
    GET_TARGET_INFO = 'Target.getTargetInfo'
    GET_TARGETS = 'Target.getTargets'
    SEND_MESSAGE_TO_TARGET = 'Target.sendMessageToTarget'
    SET_AUTO_ATTACH = 'Target.setAutoAttach'
    AUTO_ATTACH_RELATED = 'Target.autoAttachRelated'
    SET_DISCOVER_TARGETS = 'Target.setDiscoverTargets'
    SET_REMOTE_LOCATIONS = 'Target.setRemoteLocations'
    OPEN_DEV_TOOLS = 'Target.openDevTools'


# Parameter types
class ActivateTargetParams(TypedDict):
    """Parameters for the activateTarget command."""

    targetId: TargetID


class AttachToTargetParams(TypedDict):
    """Parameters for the attachToTarget command."""

    targetId: TargetID
    flatten: NotRequired[bool]


class AttachToBrowserTargetParams(TypedDict):
    """Parameters for the attachToBrowserTarget command."""

    sessionId: SessionID


class CloseTargetParams(TypedDict):
    """Parameters for the closeTarget command."""

    targetId: TargetID


class ExposeDevToolsProtocolParams(TypedDict):
    """Parameters for the exposeDevToolsProtocol command."""

    targetId: TargetID
    bindingName: NotRequired[str]
    inheritPermissions: NotRequired[bool]


class CreateBrowserContextParams(TypedDict):
    """Parameters for the createBrowserContext command."""

    disposeOnDetach: NotRequired[bool]
    proxyServer: NotRequired[str]
    proxyBypassList: NotRequired[str]
    originsWithUniversalNetworkAccess: NotRequired[list[str]]


class CreateTargetParams(TypedDict):
    """Parameters for the createTarget command."""

    url: str
    left: NotRequired[int]
    top: NotRequired[int]
    width: NotRequired[int]
    height: NotRequired[int]
    windowState: NotRequired[WindowState]
    browserContextId: NotRequired[BrowserContextID]
    enableBeginFrameControl: NotRequired[bool]
    newWindow: NotRequired[bool]
    background: NotRequired[bool]
    forTab: NotRequired[bool]
    hidden: NotRequired[bool]


class DetachFromTargetParams(TypedDict):
    """Parameters for the detachFromTarget command."""

    sessionId: NotRequired[SessionID]
    targetId: NotRequired[TargetID]


class DisposeBrowserContextParams(TypedDict):
    """Parameters for the disposeBrowserContext command."""

    browserContextId: BrowserContextID


class GetTargetInfoParams(TypedDict):
    """Parameters for the getTargetInfo command."""

    targetId: NotRequired[TargetID]


class GetTargetsParams(TypedDict):
    """Parameters for the getTargets command."""

    filter: NotRequired[TargetFilter]


class SendMessageToTargetParams(TypedDict):
    """Parameters for the sendMessageToTarget command."""

    message: str
    sessionId: NotRequired[SessionID]
    targetId: NotRequired[TargetID]


class SetAutoAttachParams(TypedDict):
    """Parameters for the setAutoAttach command."""

    autoAttach: bool
    waitForDebuggerOnStart: bool
    flatten: NotRequired[bool]
    filter: NotRequired[TargetFilter]


class AutoAttachRelatedParams(TypedDict):
    """Parameters for the autoAttachRelated command."""

    targetId: TargetID
    waitForDebuggerOnStart: bool
    filter: NotRequired[TargetFilter]


class SetDiscoverTargetsParams(TypedDict):
    """Parameters for the setDiscoverTargets command."""

    discover: bool
    filter: NotRequired[TargetFilter]


class SetRemoteLocationsParams(TypedDict):
    """Parameters for the setRemoteLocations command."""

    locations: list[RemoteLocation]


class OpenDevToolsParams(TypedDict):
    """Parameters for the openDevTools command."""

    targetId: TargetID


# Result types
class AttachToTargetResult(TypedDict):
    """Result for the attachToTarget command."""

    sessionId: SessionID


class AttachToBrowserTargetResult(TypedDict):
    """Result for the attachToBrowserTarget command."""

    sessionId: SessionID


class CloseTargetResult(TypedDict):
    """Result for the closeTarget command."""

    success: bool


class CreateBrowserContextResult(TypedDict):
    """Result for the createBrowserContext command."""

    browserContextId: BrowserContextID


class GetBrowserContextsResult(TypedDict):
    """Result for the getBrowserContexts command."""

    browserContextIds: list[BrowserContextID]


class CreateTargetResult(TypedDict):
    """Result for the createTarget command."""

    targetId: TargetID


class GetTargetInfoResult(TypedDict):
    """Result for the getTargetInfo command."""

    targetInfo: TargetInfo


class GetTargetsResult(TypedDict):
    """Result for the getTargets command."""

    targetInfos: list[TargetInfo]


class OpenDevToolsResult(TypedDict):
    """Result for the openDevTools command."""

    targetId: TargetID


# Response types
AttachToTargetResponse = Response[AttachToTargetResult]
AttachToBrowserTargetResponse = Response[AttachToBrowserTargetResult]
CloseTargetResponse = Response[CloseTargetResult]
CreateBrowserContextResponse = Response[CreateBrowserContextResult]
GetBrowserContextsResponse = Response[GetBrowserContextsResult]
CreateTargetResponse = Response[CreateTargetResult]
GetTargetInfoResponse = Response[GetTargetInfoResult]
GetTargetsResponse = Response[GetTargetsResult]
OpenDevToolsResponse = Response[OpenDevToolsResult]


# Command types
ActivateTargetCommand = Command[ActivateTargetParams, Response[EmptyResponse]]
AttachToTargetCommand = Command[AttachToTargetParams, AttachToTargetResponse]
AttachToBrowserTargetCommand = Command[EmptyParams, AttachToBrowserTargetResponse]
CloseTargetCommand = Command[CloseTargetParams, CloseTargetResponse]
ExposeDevToolsProtocolCommand = Command[ExposeDevToolsProtocolParams, Response[EmptyResponse]]
CreateBrowserContextCommand = Command[CreateBrowserContextParams, CreateBrowserContextResponse]
GetBrowserContextsCommand = Command[EmptyParams, GetBrowserContextsResponse]
CreateTargetCommand = Command[CreateTargetParams, CreateTargetResponse]
DetachFromTargetCommand = Command[DetachFromTargetParams, Response[EmptyResponse]]
DisposeBrowserContextCommand = Command[DisposeBrowserContextParams, Response[EmptyResponse]]
GetTargetInfoCommand = Command[GetTargetInfoParams, GetTargetInfoResponse]
GetTargetsCommand = Command[GetTargetsParams, GetTargetsResponse]
SendMessageToTargetCommand = Command[SendMessageToTargetParams, Response[EmptyResponse]]
SetAutoAttachCommand = Command[SetAutoAttachParams, Response[EmptyResponse]]
AutoAttachRelatedCommand = Command[AutoAttachRelatedParams, Response[EmptyResponse]]
SetDiscoverTargetsCommand = Command[SetDiscoverTargetsParams, Response[EmptyResponse]]
SetRemoteLocationsCommand = Command[SetRemoteLocationsParams, Response[EmptyResponse]]
OpenDevToolsCommand = Command[OpenDevToolsParams, OpenDevToolsResponse]
