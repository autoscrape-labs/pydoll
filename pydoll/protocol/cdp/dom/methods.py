from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.cdp.base import Command, EmptyParams, EmptyResponse, Response
from pydoll.protocol.cdp.dom.types import (
    BackendNodeId,
    BoxModel,
    CSSComputedStyleProperty,
    DetachedElementInfo,
    IncludeWhitespace,
    LogicalAxes,
    Node,
    NodeId,
    PhysicalAxes,
    Quad,
    Rect,
    RelationType,
)
from pydoll.protocol.cdp.page.types import FrameId
from pydoll.protocol.cdp.runtime.types import (
    ExecutionContextId,
    RemoteObject,
    RemoteObjectId,
    StackTrace,
)


class DomMethod(str, Enum):
    """DOM domain method names."""

    COLLECT_CLASS_NAMES_FROM_SUBTREE = 'DOM.collectClassNamesFromSubtree'
    COPY_TO = 'DOM.copyTo'
    DESCRIBE_NODE = 'DOM.describeNode'
    DISABLE = 'DOM.disable'
    DISCARD_SEARCH_RESULTS = 'DOM.discardSearchResults'
    ENABLE = 'DOM.enable'
    FOCUS = 'DOM.focus'
    FORCE_SHOW_POPOVER = 'DOM.forceShowPopover'
    GET_ANCHOR_ELEMENT = 'DOM.getAnchorElement'
    GET_ATTRIBUTES = 'DOM.getAttributes'
    GET_BOX_MODEL = 'DOM.getBoxModel'
    GET_CONTAINER_FOR_NODE = 'DOM.getContainerForNode'
    GET_CONTENT_QUADS = 'DOM.getContentQuads'
    GET_DETACHED_DOM_NODES = 'DOM.getDetachedDomNodes'
    GET_DOCUMENT = 'DOM.getDocument'
    GET_ELEMENT_BY_RELATION = 'DOM.getElementByRelation'
    GET_FILE_INFO = 'DOM.getFileInfo'
    GET_FLATTENED_DOCUMENT = 'DOM.getFlattenedDocument'
    GET_FRAME_OWNER = 'DOM.getFrameOwner'
    GET_NODE_FOR_LOCATION = 'DOM.getNodeForLocation'
    GET_NODE_STACK_TRACES = 'DOM.getNodeStackTraces'
    GET_NODES_FOR_SUBTREE_BY_STYLE = 'DOM.getNodesForSubtreeByStyle'
    GET_OUTER_HTML = 'DOM.getOuterHTML'
    GET_QUERYING_DESCENDANTS_FOR_CONTAINER = 'DOM.getQueryingDescendantsForContainer'
    GET_RELAYOUT_BOUNDARY = 'DOM.getRelayoutBoundary'
    GET_SEARCH_RESULTS = 'DOM.getSearchResults'
    GET_TOP_LAYER_ELEMENTS = 'DOM.getTopLayerElements'
    HIDE_HIGHLIGHT = 'DOM.hideHighlight'
    HIGHLIGHT_NODE = 'DOM.highlightNode'
    HIGHLIGHT_RECT = 'DOM.highlightRect'
    MARK_UNDOABLE_STATE = 'DOM.markUndoableState'
    MOVE_TO = 'DOM.moveTo'
    PERFORM_SEARCH = 'DOM.performSearch'
    PUSH_NODE_BY_PATH_TO_FRONTEND = 'DOM.pushNodeByPathToFrontend'
    PUSH_NODES_BY_BACKEND_IDS_TO_FRONTEND = 'DOM.pushNodesByBackendIdsToFrontend'
    QUERY_SELECTOR = 'DOM.querySelector'
    QUERY_SELECTOR_ALL = 'DOM.querySelectorAll'
    REDO = 'DOM.redo'
    REMOVE_ATTRIBUTE = 'DOM.removeAttribute'
    REMOVE_NODE = 'DOM.removeNode'
    REQUEST_CHILD_NODES = 'DOM.requestChildNodes'
    REQUEST_NODE = 'DOM.requestNode'
    RESOLVE_NODE = 'DOM.resolveNode'
    SCROLL_INTO_VIEW_IF_NEEDED = 'DOM.scrollIntoViewIfNeeded'
    SET_ATTRIBUTE_VALUE = 'DOM.setAttributeValue'
    SET_ATTRIBUTES_AS_TEXT = 'DOM.setAttributesAsText'
    SET_FILE_INPUT_FILES = 'DOM.setFileInputFiles'
    SET_INSPECTED_NODE = 'DOM.setInspectedNode'
    SET_NODE_NAME = 'DOM.setNodeName'
    SET_NODE_STACK_TRACES_ENABLED = 'DOM.setNodeStackTracesEnabled'
    SET_NODE_VALUE = 'DOM.setNodeValue'
    SET_OUTER_HTML = 'DOM.setOuterHTML'
    UNDO = 'DOM.undo'


class CollectClassNamesFromSubtreeParams(TypedDict):
    """Parameters for collecting class names from subtree."""

    nodeId: NodeId


class CopyToParams(TypedDict, total=False):
    """Parameters for copying a node."""

    nodeId: NodeId
    targetNodeId: NodeId
    insertBeforeNodeId: NodeId


class DescribeNodeParams(TypedDict, total=False):
    """Parameters for describing a node."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    depth: int
    pierce: bool


class ScrollIntoViewIfNeededParams(TypedDict, total=False):
    """Parameters for scrolling into view if needed."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    rect: Rect


class DiscardSearchResultsParams(TypedDict):
    """Parameters for discarding search results."""

    searchId: str


class EnableParams(TypedDict, total=False):
    """Parameters for enabling DOM agent."""

    includeWhitespace: IncludeWhitespace


class FocusParams(TypedDict, total=False):
    """Parameters for focusing an element."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetAttributesParams(TypedDict):
    """Parameters for getting attributes."""

    nodeId: NodeId


class GetBoxModelParams(TypedDict, total=False):
    """Parameters for getting box model."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetContentQuadsParams(TypedDict, total=False):
    """Parameters for getting content quads."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetDocumentParams(TypedDict, total=False):
    """Parameters for getting document."""

    depth: int
    pierce: bool


class GetFlattenedDocumentParams(TypedDict, total=False):
    """Parameters for getting flattened document."""

    depth: int
    pierce: bool


class GetNodesForSubtreeByStyleParams(TypedDict, total=False):
    """Parameters for getting nodes by style."""

    nodeId: NodeId
    computedStyles: list[CSSComputedStyleProperty]
    pierce: bool


class GetNodeForLocationParams(TypedDict, total=False):
    """Parameters for getting node for location."""

    x: int
    y: int
    includeUserAgentShadowDOM: bool
    ignorePointerEventsNone: bool


class GetOuterHTMLParams(TypedDict, total=False):
    """Parameters for getting outer HTML."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    includeShadowDOM: bool


class GetRelayoutBoundaryParams(TypedDict):
    """Parameters for getting relayout boundary."""

    nodeId: NodeId


class GetSearchResultsParams(TypedDict):
    """Parameters for getting search results."""

    searchId: str
    fromIndex: int
    toIndex: int


class MoveToParams(TypedDict, total=False):
    """Parameters for moving a node."""

    nodeId: NodeId
    targetNodeId: NodeId
    insertBeforeNodeId: NodeId


class PerformSearchParams(TypedDict, total=False):
    """Parameters for performing search."""

    query: str
    includeUserAgentShadowDOM: bool


class PushNodeByPathToFrontendParams(TypedDict):
    """Parameters for pushing node by path to frontend."""

    path: str


class PushNodesByBackendIdsToFrontendParams(TypedDict):
    """Parameters for pushing nodes by backend IDs to frontend."""

    backendNodeIds: list[BackendNodeId]


class QuerySelectorParams(TypedDict):
    """Parameters for querySelector."""

    nodeId: NodeId
    selector: str


class QuerySelectorAllParams(TypedDict):
    """Parameters for querySelectorAll."""

    nodeId: NodeId
    selector: str


class GetElementByRelationParams(TypedDict):
    """Parameters for getting element by relation."""

    nodeId: NodeId
    relation: RelationType


class RemoveAttributeParams(TypedDict):
    """Parameters for removing attribute."""

    nodeId: NodeId
    name: str


class RemoveNodeParams(TypedDict):
    """Parameters for removing node."""

    nodeId: NodeId


class RequestChildNodesParams(TypedDict, total=False):
    """Parameters for requesting child nodes."""

    nodeId: NodeId
    depth: int
    pierce: bool


class RequestNodeParams(TypedDict):
    """Parameters for requesting node."""

    objectId: RemoteObjectId


class ResolveNodeParams(TypedDict, total=False):
    """Parameters for resolving node."""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectGroup: str
    executionContextId: ExecutionContextId


class SetAttributeValueParams(TypedDict):
    """Parameters for setting attribute value."""

    nodeId: NodeId
    name: str
    value: str


class SetAttributesAsTextParams(TypedDict, total=False):
    """Parameters for setting attributes as text."""

    nodeId: NodeId
    text: str
    name: str


class SetFileInputFilesParams(TypedDict, total=False):
    """Parameters for setting file input files."""

    files: list[str]
    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class SetNodeStackTracesEnabledParams(TypedDict):
    """Parameters for setting node stack traces enabled."""

    enable: bool


class GetNodeStackTracesParams(TypedDict):
    """Parameters for getting node stack traces."""

    nodeId: NodeId


class GetFileInfoParams(TypedDict):
    """Parameters for getting file info."""

    objectId: RemoteObjectId


class SetInspectedNodeParams(TypedDict):
    """Parameters for setting inspected node."""

    nodeId: NodeId


class SetNodeNameParams(TypedDict):
    """Parameters for setting node name."""

    nodeId: NodeId
    name: str


class SetNodeValueParams(TypedDict):
    """Parameters for setting node value."""

    nodeId: NodeId
    value: str


class SetOuterHTMLParams(TypedDict):
    """Parameters for setting outer HTML."""

    nodeId: NodeId
    outerHTML: str


class GetFrameOwnerParams(TypedDict):
    """Parameters for getting frame owner."""

    frameId: FrameId


class GetContainerForNodeParams(TypedDict, total=False):
    """Parameters for getting container for node."""

    nodeId: NodeId
    containerName: str
    physicalAxes: PhysicalAxes
    logicalAxes: LogicalAxes
    queriesScrollState: bool
    queriesAnchored: bool


class GetQueryingDescendantsForContainerParams(TypedDict):
    """Parameters for getting querying descendants for container."""

    nodeId: NodeId


class GetAnchorElementParams(TypedDict, total=False):
    """Parameters for getting anchor element."""

    nodeId: NodeId
    anchorSpecifier: str


class ForceShowPopoverParams(TypedDict):
    """Parameters for forcing show popover."""

    nodeId: NodeId
    enable: bool


# Result types
class CollectClassNamesFromSubtreeResult(TypedDict):
    """Result for collectClassNamesFromSubtree command."""

    classNames: list[str]


class CopyToResult(TypedDict):
    """Result for copyTo command."""

    nodeId: NodeId


class DescribeNodeResult(TypedDict):
    """Result for describeNode command."""

    node: Node


class GetAttributesResult(TypedDict):
    """Result for getAttributes command."""

    attributes: list[str]


class GetBoxModelResult(TypedDict):
    """Result for getBoxModel command."""

    model: BoxModel


class GetContentQuadsResult(TypedDict):
    """Result for getContentQuads command."""

    quads: list[Quad]


class GetDocumentResult(TypedDict):
    """Result for getDocument command."""

    root: Node


class GetFlattenedDocumentResult(TypedDict):
    """Result for getFlattenedDocument command."""

    nodes: list[Node]


class GetNodesForSubtreeByStyleResult(TypedDict):
    """Result for getNodesForSubtreeByStyle command."""

    nodeIds: list[NodeId]


class GetNodeForLocationResult(TypedDict, total=False):
    """Result for getNodeForLocation command."""

    backendNodeId: BackendNodeId
    frameId: FrameId
    nodeId: NodeId


class GetOuterHTMLResult(TypedDict):
    """Result for getOuterHTML command."""

    outerHTML: str


class GetRelayoutBoundaryResult(TypedDict):
    """Result for getRelayoutBoundary command."""

    nodeId: NodeId


class GetSearchResultsResult(TypedDict):
    """Result for getSearchResults command."""

    nodeIds: list[NodeId]


class GetTopLayerElementsResult(TypedDict):
    """Result for getTopLayerElements command."""

    nodeIds: list[NodeId]


class GetElementByRelationResult(TypedDict):
    """Result for getElementByRelation command."""

    nodeId: NodeId


class MoveToResult(TypedDict):
    """Result for moveTo command."""

    nodeId: NodeId


class PerformSearchResult(TypedDict):
    """Result for performSearch command."""

    searchId: str
    resultCount: int


class PushNodeByPathToFrontendResult(TypedDict):
    """Result for pushNodeByPathToFrontend command."""

    nodeId: NodeId


class PushNodesByBackendIdsToFrontendResult(TypedDict):
    """Result for pushNodesByBackendIdsToFrontend command."""

    nodeIds: list[NodeId]


class QuerySelectorResult(TypedDict):
    """Result for querySelector command."""

    nodeId: NodeId


class QuerySelectorAllResult(TypedDict):
    """Result for querySelectorAll command."""

    nodeIds: list[NodeId]


class RequestNodeResult(TypedDict):
    """Result for requestNode command."""

    nodeId: NodeId


class ResolveNodeResult(TypedDict):
    """Result for resolveNode command."""

    object: RemoteObject


class SetNodeNameResult(TypedDict):
    """Result for setNodeName command."""

    nodeId: NodeId


class GetNodeStackTracesResult(TypedDict, total=False):
    """Result for getNodeStackTraces command."""

    creation: StackTrace


class GetFileInfoResult(TypedDict):
    """Result for getFileInfo command."""

    path: str


class GetDetachedDomNodesResult(TypedDict):
    """Result for getDetachedDomNodes command."""

    detachedNodes: list[DetachedElementInfo]


class GetFrameOwnerResult(TypedDict, total=False):
    """Result for getFrameOwner command."""

    backendNodeId: BackendNodeId
    nodeId: NodeId


class GetContainerForNodeResult(TypedDict, total=False):
    """Result for getContainerForNode command."""

    nodeId: NodeId


class GetQueryingDescendantsForContainerResult(TypedDict):
    """Result for getQueryingDescendantsForContainer command."""

    nodeIds: list[NodeId]


class GetAnchorElementResult(TypedDict):
    """Result for getAnchorElement command."""

    nodeId: NodeId


class ForceShowPopoverResult(TypedDict):
    """Result for forceShowPopover command."""

    nodeIds: list[NodeId]


# Response types
CollectClassNamesFromSubtreeResponse = Response[CollectClassNamesFromSubtreeResult]
CopyToResponse = Response[CopyToResult]
DescribeNodeResponse = Response[DescribeNodeResult]
GetAttributesResponse = Response[GetAttributesResult]
GetBoxModelResponse = Response[GetBoxModelResult]
GetContentQuadsResponse = Response[GetContentQuadsResult]
GetDocumentResponse = Response[GetDocumentResult]
GetFlattenedDocumentResponse = Response[GetFlattenedDocumentResult]
GetNodesForSubtreeByStyleResponse = Response[GetNodesForSubtreeByStyleResult]
GetNodeForLocationResponse = Response[GetNodeForLocationResult]
GetOuterHTMLResponse = Response[GetOuterHTMLResult]
GetRelayoutBoundaryResponse = Response[GetRelayoutBoundaryResult]
GetSearchResultsResponse = Response[GetSearchResultsResult]
GetTopLayerElementsResponse = Response[GetTopLayerElementsResult]
GetElementByRelationResponse = Response[GetElementByRelationResult]
MoveToResponse = Response[MoveToResult]
PerformSearchResponse = Response[PerformSearchResult]
PushNodeByPathToFrontendResponse = Response[PushNodeByPathToFrontendResult]
PushNodesByBackendIdsToFrontendResponse = Response[PushNodesByBackendIdsToFrontendResult]
QuerySelectorResponse = Response[QuerySelectorResult]
QuerySelectorAllResponse = Response[QuerySelectorAllResult]
RequestNodeResponse = Response[RequestNodeResult]
ResolveNodeResponse = Response[ResolveNodeResult]
SetNodeNameResponse = Response[SetNodeNameResult]
GetNodeStackTracesResponse = Response[GetNodeStackTracesResult]
GetFileInfoResponse = Response[GetFileInfoResult]
GetDetachedDomNodesResponse = Response[GetDetachedDomNodesResult]
GetFrameOwnerResponse = Response[GetFrameOwnerResult]
GetContainerForNodeResponse = Response[GetContainerForNodeResult]
GetQueryingDescendantsForContainerResponse = Response[GetQueryingDescendantsForContainerResult]
GetAnchorElementResponse = Response[GetAnchorElementResult]
ForceShowPopoverResponse = Response[ForceShowPopoverResult]


# Command types
CollectClassNamesFromSubtreeCommand = Command[
    CollectClassNamesFromSubtreeParams, CollectClassNamesFromSubtreeResponse
]
CopyToCommand = Command[CopyToParams, CopyToResponse]
DescribeNodeCommand = Command[DescribeNodeParams, DescribeNodeResponse]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
DiscardSearchResultsCommand = Command[DiscardSearchResultsParams, Response[EmptyResponse]]
EnableCommand = Command[EnableParams, Response[EmptyResponse]]
FocusCommand = Command[FocusParams, Response[EmptyResponse]]
ForceShowPopoverCommand = Command[ForceShowPopoverParams, ForceShowPopoverResponse]
GetAnchorElementCommand = Command[GetAnchorElementParams, GetAnchorElementResponse]
GetAttributesCommand = Command[GetAttributesParams, GetAttributesResponse]
GetBoxModelCommand = Command[GetBoxModelParams, GetBoxModelResponse]
GetContainerForNodeCommand = Command[GetContainerForNodeParams, GetContainerForNodeResponse]
GetContentQuadsCommand = Command[GetContentQuadsParams, GetContentQuadsResponse]
GetDetachedDomNodesCommand = Command[EmptyParams, Response[GetDetachedDomNodesResponse]]
GetDocumentCommand = Command[GetDocumentParams, GetDocumentResponse]
GetElementByRelationCommand = Command[GetElementByRelationParams, GetElementByRelationResponse]
GetFileInfoCommand = Command[GetFileInfoParams, GetFileInfoResponse]
GetFlattenedDocumentCommand = Command[GetFlattenedDocumentParams, GetFlattenedDocumentResponse]
GetFrameOwnerCommand = Command[GetFrameOwnerParams, GetFrameOwnerResponse]
GetNodeForLocationCommand = Command[GetNodeForLocationParams, GetNodeForLocationResponse]
GetNodeStackTracesCommand = Command[GetNodeStackTracesParams, GetNodeStackTracesResponse]
GetNodesForSubtreeByStyleCommand = Command[
    GetNodesForSubtreeByStyleParams, GetNodesForSubtreeByStyleResponse
]
GetOuterHTMLCommand = Command[GetOuterHTMLParams, GetOuterHTMLResponse]
GetQueryingDescendantsForContainerCommand = Command[
    GetQueryingDescendantsForContainerParams, GetQueryingDescendantsForContainerResponse
]
GetRelayoutBoundaryCommand = Command[GetRelayoutBoundaryParams, GetRelayoutBoundaryResponse]
GetSearchResultsCommand = Command[GetSearchResultsParams, GetSearchResultsResponse]
GetTopLayerElementsCommand = Command[EmptyParams, GetTopLayerElementsResponse]
HideHighlightCommand = Command[EmptyParams, Response[EmptyResponse]]
HighlightNodeCommand = Command[EmptyParams, Response[EmptyResponse]]  # redirect to Overlay
HighlightRectCommand = Command[EmptyParams, Response[EmptyResponse]]  # redirect to Overlay
MarkUndoableStateCommand = Command[EmptyParams, Response[EmptyResponse]]
MoveToCommand = Command[MoveToParams, MoveToResponse]
PerformSearchCommand = Command[PerformSearchParams, PerformSearchResponse]
PushNodeByPathToFrontendCommand = Command[
    PushNodeByPathToFrontendParams, PushNodeByPathToFrontendResponse
]
PushNodesByBackendIdsToFrontendCommand = Command[
    PushNodesByBackendIdsToFrontendParams, PushNodesByBackendIdsToFrontendResponse
]
QuerySelectorCommand = Command[QuerySelectorParams, QuerySelectorResponse]
QuerySelectorAllCommand = Command[QuerySelectorAllParams, QuerySelectorAllResponse]
RedoCommand = Command[EmptyParams, Response[EmptyResponse]]
RemoveAttributeCommand = Command[RemoveAttributeParams, Response[EmptyResponse]]
RemoveNodeCommand = Command[RemoveNodeParams, Response[EmptyResponse]]
RequestChildNodesCommand = Command[RequestChildNodesParams, Response[EmptyResponse]]
RequestNodeCommand = Command[RequestNodeParams, RequestNodeResponse]
ResolveNodeCommand = Command[ResolveNodeParams, ResolveNodeResponse]
ScrollIntoViewIfNeededCommand = Command[ScrollIntoViewIfNeededParams, Response[EmptyResponse]]
SetAttributeValueCommand = Command[SetAttributeValueParams, Response[EmptyResponse]]
SetAttributesAsTextCommand = Command[SetAttributesAsTextParams, Response[EmptyResponse]]
SetFileInputFilesCommand = Command[SetFileInputFilesParams, Response[EmptyResponse]]
SetInspectedNodeCommand = Command[SetInspectedNodeParams, Response[EmptyResponse]]
SetNodeNameCommand = Command[SetNodeNameParams, SetNodeNameResponse]
SetNodeStackTracesEnabledCommand = Command[SetNodeStackTracesEnabledParams, Response[EmptyResponse]]
SetNodeValueCommand = Command[SetNodeValueParams, Response[EmptyResponse]]
SetOuterHTMLCommand = Command[SetOuterHTMLParams, Response[EmptyResponse]]
UndoCommand = Command[EmptyParams, Response[EmptyResponse]]
