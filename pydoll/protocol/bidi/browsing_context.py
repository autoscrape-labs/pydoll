from __future__ import annotations

from typing import Optional

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.base import Command, EmptyResponse, Response


class NavigateParams(TypedDict):
    context: str
    url: str
    wait: NotRequired[str]


class CreateParams(TypedDict):
    type: str
    referenceContext: NotRequired[str]


class GetTreeParams(TypedDict):
    root: NotRequired[str]


class CaptureScreenshotParams(TypedDict):
    context: str


class LocateNodesParams(TypedDict):
    context: str
    locator: dict
    maxNodeCount: NotRequired[int]
    startNodes: NotRequired[list[dict]]


class CloseParams(TypedDict):
    context: str


class ReloadParams(TypedDict):
    context: str
    wait: NotRequired[str]


class TraverseHistoryParams(TypedDict):
    context: str
    delta: int


class NavigateResult(TypedDict):
    navigation: Optional[str]
    url: str


class BrowsingContextInfo(TypedDict):
    context: str
    url: str
    children: NotRequired[list]
    parent: NotRequired[Optional[str]]


class GetTreeResult(TypedDict):
    contexts: list[BrowsingContextInfo]


class CreateResult(TypedDict):
    context: str


class CaptureScreenshotResult(TypedDict):
    data: str


class LocateNodesResult(TypedDict):
    nodes: list[dict]


NavigateResponse = Response[NavigateResult]
CreateResponse = Response[CreateResult]
GetTreeResponse = Response[GetTreeResult]
CaptureScreenshotResponse = Response[CaptureScreenshotResult]
LocateNodesResponse = Response[LocateNodesResult]
CloseResponse = Response[EmptyResponse]
ReloadResponse = Response[NavigateResult]
TraverseHistoryResponse = Response[EmptyResponse]

NavigateCommand = Command[NavigateParams, NavigateResponse]
CreateCommand = Command[CreateParams, CreateResponse]
GetTreeCommand = Command[GetTreeParams, GetTreeResponse]
CaptureScreenshotCommand = Command[CaptureScreenshotParams, CaptureScreenshotResponse]
LocateNodesCommand = Command[LocateNodesParams, LocateNodesResponse]
CloseCommand = Command[CloseParams, CloseResponse]
ReloadCommand = Command[ReloadParams, ReloadResponse]
TraverseHistoryCommand = Command[TraverseHistoryParams, TraverseHistoryResponse]


def navigate(context: str, url: str, wait: str = 'complete') -> NavigateCommand:
    return Command(
        method='browsingContext.navigate',
        params=NavigateParams(context=context, url=url, wait=wait),
    )


def create(type_: str = 'tab', reference_context: Optional[str] = None) -> CreateCommand:
    params = CreateParams(type=type_)
    if reference_context is not None:
        params['referenceContext'] = reference_context
    return Command(method='browsingContext.create', params=params)


def get_tree(root: Optional[str] = None) -> GetTreeCommand:
    params: GetTreeParams = {}
    if root is not None:
        params['root'] = root
    return Command(method='browsingContext.getTree', params=params)


def capture_screenshot(context: str) -> CaptureScreenshotCommand:
    return Command(
        method='browsingContext.captureScreenshot',
        params=CaptureScreenshotParams(context=context),
    )


def locate_nodes(
    context: str,
    locator: dict,
    max_node_count: Optional[int] = None,
    start_nodes: Optional[list[dict]] = None,
) -> LocateNodesCommand:
    params = LocateNodesParams(context=context, locator=locator)
    if max_node_count is not None:
        params['maxNodeCount'] = max_node_count
    if start_nodes is not None:
        params['startNodes'] = start_nodes
    return Command(method='browsingContext.locateNodes', params=params)


def close(context: str) -> CloseCommand:
    return Command(method='browsingContext.close', params=CloseParams(context=context))


def reload(context: str, wait: str = 'complete') -> ReloadCommand:
    return Command(
        method='browsingContext.reload',
        params=ReloadParams(context=context, wait=wait),
    )


def traverse_history(context: str, delta: int) -> TraverseHistoryCommand:
    return Command(
        method='browsingContext.traverseHistory',
        params=TraverseHistoryParams(context=context, delta=delta),
    )


class ActivateParams(TypedDict):
    context: str


class PrintPageParams(TypedDict):
    context: str
    landscape: NotRequired[bool]
    printBackground: NotRequired[bool]
    scale: NotRequired[float]


class PrintPageResult(TypedDict):
    data: str


class HandleUserPromptParams(TypedDict):
    context: str
    accept: bool
    userText: NotRequired[str]


ActivateResponse = Response[EmptyResponse]
PrintPageResponse = Response[PrintPageResult]
HandleUserPromptResponse = Response[EmptyResponse]

ActivateCommand = Command[ActivateParams, ActivateResponse]
PrintPageCommand = Command[PrintPageParams, PrintPageResponse]
HandleUserPromptCommand = Command[HandleUserPromptParams, HandleUserPromptResponse]


class BrowsingContextEvent:
    USER_PROMPT_OPENED = 'browsingContext.userPromptOpened'
    USER_PROMPT_CLOSED = 'browsingContext.userPromptClosed'


def activate(context: str) -> ActivateCommand:
    return Command(
        method='browsingContext.activate',
        params=ActivateParams(context=context),
    )


def print_page(
    context: str,
    landscape: bool = False,
    print_background: bool = True,
    scale: float = 1.0,
) -> PrintPageCommand:
    return Command(
        method='browsingContext.print',
        params=PrintPageParams(
            context=context,
            landscape=landscape,
            printBackground=print_background,
            scale=scale,
        ),
    )


def handle_user_prompt(
    context: str, accept: bool, user_text: Optional[str] = None
) -> HandleUserPromptCommand:
    params = HandleUserPromptParams(context=context, accept=accept)
    if user_text is not None:
        params['userText'] = user_text
    return Command(method='browsingContext.handleUserPrompt', params=params)
