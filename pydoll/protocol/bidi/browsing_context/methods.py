from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import (
    Command,
    CommandResponse,
    EmptyResult,
)
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import (
    BrowsingContext,
    ClipRectangle,
    CreateType,
    ImageFormat,
    InfoList,
    Locator,
    Navigation,
    PrintMarginParameters,
    PrintPageParameters,
    ReadinessState,
    Viewport,
)


class BrowsingContextMethod(str, Enum):
    """browsingContext module method names."""

    ACTIVATE = 'browsingContext.activate'
    CAPTURE_SCREENSHOT = 'browsingContext.captureScreenshot'
    CLOSE = 'browsingContext.close'
    CREATE = 'browsingContext.create'
    GET_TREE = 'browsingContext.getTree'
    HANDLE_USER_PROMPT = 'browsingContext.handleUserPrompt'
    LOCATE_NODES = 'browsingContext.locateNodes'
    NAVIGATE = 'browsingContext.navigate'
    PRINT = 'browsingContext.print'
    RELOAD = 'browsingContext.reload'
    SET_BYPASS_CSP = 'browsingContext.setBypassCSP'
    SET_VIEWPORT = 'browsingContext.setViewport'
    TRAVERSE_HISTORY = 'browsingContext.traverseHistory'


class ActivateParameters(TypedDict):
    """Parameters for browsingContext.activate command."""

    context: BrowsingContext


class CaptureScreenshotParameters(TypedDict):
    """Parameters for browsingContext.captureScreenshot command."""

    context: BrowsingContext
    origin: NotRequired[str]  # "viewport" / "document", default "viewport"
    format: NotRequired[ImageFormat]
    clip: NotRequired[ClipRectangle]


class CaptureScreenshotResult(TypedDict):
    """Result for browsingContext.captureScreenshot command."""

    data: str


class CloseParameters(TypedDict):
    """Parameters for browsingContext.close command."""

    context: BrowsingContext
    promptUnload: NotRequired[bool]  # default false


class CreateParameters(TypedDict):
    """Parameters for browsingContext.create command."""

    type: CreateType
    referenceContext: NotRequired[BrowsingContext]
    background: NotRequired[bool]  # default false
    userContext: NotRequired[UserContext]


class CreateResult(TypedDict):
    """Result for browsingContext.create command."""

    context: BrowsingContext
    userContext: NotRequired[UserContext]


class GetTreeParameters(TypedDict, total=False):
    """Parameters for browsingContext.getTree command."""

    maxDepth: int
    root: BrowsingContext


class GetTreeResult(TypedDict):
    """Result for browsingContext.getTree command."""

    contexts: InfoList


class HandleUserPromptParameters(TypedDict):
    """Parameters for browsingContext.handleUserPrompt command."""

    context: BrowsingContext
    accept: NotRequired[bool]
    userText: NotRequired[str]


class LocateNodesParameters(TypedDict):
    """Parameters for browsingContext.locateNodes command."""

    context: BrowsingContext
    locator: Locator
    maxNodeCount: NotRequired[int]
    serializationOptions: NotRequired[dict]  # script.SerializationOptions
    startNodes: NotRequired[list[dict]]  # list of script.SharedReference


class LocateNodesResult(TypedDict):
    """Result for browsingContext.locateNodes command."""

    nodes: list[dict]  # list of script.NodeRemoteValue


class NavigateParameters(TypedDict):
    """Parameters for browsingContext.navigate command."""

    context: BrowsingContext
    url: str
    wait: NotRequired[ReadinessState]


class NavigateResult(TypedDict):
    """Result for browsingContext.navigate command."""

    navigation: Navigation | None
    url: str


class PrintParameters(TypedDict):
    """Parameters for browsingContext.print command."""

    context: BrowsingContext
    background: NotRequired[bool]  # default false
    margin: NotRequired[PrintMarginParameters]
    orientation: NotRequired[str]  # "portrait" / "landscape", default "portrait"
    page: NotRequired[PrintPageParameters]
    pageRanges: NotRequired[list[int | str]]
    scale: NotRequired[float]  # 0.1..2.0, default 1.0
    shrinkToFit: NotRequired[bool]  # default true


class PrintResult(TypedDict):
    """Result for browsingContext.print command."""

    data: str


class ReloadParameters(TypedDict):
    """Parameters for browsingContext.reload command."""

    context: BrowsingContext
    ignoreCache: NotRequired[bool]
    wait: NotRequired[ReadinessState]


class SetBypassCSPParameters(TypedDict):
    """Parameters for browsingContext.setBypassCSP command."""

    bypass: bool | None
    contexts: NotRequired[list[BrowsingContext]]
    userContexts: NotRequired[list[UserContext]]


class SetViewportParameters(TypedDict, total=False):
    """Parameters for browsingContext.setViewport command."""

    context: BrowsingContext
    viewport: Viewport | None
    devicePixelRatio: float | None
    userContexts: list[UserContext]


class TraverseHistoryParameters(TypedDict):
    """Parameters for browsingContext.traverseHistory command."""

    context: BrowsingContext
    delta: int


ActivateCommand = Command[ActivateParameters, CommandResponse[EmptyResult]]
ActivateResponse = CommandResponse[EmptyResult]

CaptureScreenshotCommand = Command[
    CaptureScreenshotParameters, CommandResponse[CaptureScreenshotResult]
]
CaptureScreenshotResponse = CommandResponse[CaptureScreenshotResult]

CloseCommand = Command[CloseParameters, CommandResponse[EmptyResult]]
CloseResponse = CommandResponse[EmptyResult]

CreateCommand = Command[CreateParameters, CommandResponse[CreateResult]]
CreateResponse = CommandResponse[CreateResult]

GetTreeCommand = Command[GetTreeParameters, CommandResponse[GetTreeResult]]
GetTreeResponse = CommandResponse[GetTreeResult]

HandleUserPromptCommand = Command[HandleUserPromptParameters, CommandResponse[EmptyResult]]
HandleUserPromptResponse = CommandResponse[EmptyResult]

LocateNodesCommand = Command[LocateNodesParameters, CommandResponse[LocateNodesResult]]
LocateNodesResponse = CommandResponse[LocateNodesResult]

NavigateCommand = Command[NavigateParameters, CommandResponse[NavigateResult]]
NavigateResponse = CommandResponse[NavigateResult]

PrintCommand = Command[PrintParameters, CommandResponse[PrintResult]]
PrintResponse = CommandResponse[PrintResult]

ReloadCommand = Command[ReloadParameters, CommandResponse[NavigateResult]]
ReloadResponse = CommandResponse[NavigateResult]

SetBypassCSPCommand = Command[SetBypassCSPParameters, CommandResponse[EmptyResult]]
SetBypassCSPResponse = CommandResponse[EmptyResult]

SetViewportCommand = Command[SetViewportParameters, CommandResponse[EmptyResult]]
SetViewportResponse = CommandResponse[EmptyResult]

TraverseHistoryCommand = Command[TraverseHistoryParameters, CommandResponse[EmptyResult]]
TraverseHistoryResponse = CommandResponse[EmptyResult]
