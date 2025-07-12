try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


from pydoll.constants import ElementRelation, IncludeWhitespace, LogicalAxes, PhysicalAxes
from pydoll.protocol.base import CommandParams
from pydoll.protocol.dom.types import (
    CSSComputedStyleProperty,
    Rect,
)


class DescribeNodeParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]
    depth: NotRequired[int]
    pierce: NotRequired[bool]


class DomEnableParams(CommandParams):
    includeWhitespace: NotRequired[IncludeWhitespace]


class DomFocusParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]


class GetAttributesParams(CommandParams):
    nodeId: int


class GetBoxModelParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]


class GetDocumentParams(CommandParams):
    depth: NotRequired[int]
    pierce: NotRequired[bool]


class GetNodeForLocationParams(CommandParams):
    x: int
    y: int
    includeUserAgentShadowDOM: NotRequired[bool]
    ignorePointerEventsNone: NotRequired[bool]


class GetOuterHTMLParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]


class MoveToParams(CommandParams):
    nodeId: int
    targetNodeId: int
    insertBeforeNodeId: NotRequired[int]


class QuerySelectorParams(CommandParams):
    nodeId: int
    selector: str


class QuerySelectorAllParams(CommandParams):
    nodeId: int
    selector: str


class RemoveAttributeParams(CommandParams):
    nodeId: int
    name: str


class RemoveNodeParams(CommandParams):
    nodeId: int


class RequestChildNodesParams(CommandParams):
    nodeId: int
    depth: NotRequired[int]
    pierce: NotRequired[bool]


class RequestNodeParams(CommandParams):
    objectId: str


class ResolveNodeParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectGroup: NotRequired[str]
    executionContextId: NotRequired[int]


class ScrollIntoViewIfNeededParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]
    rect: NotRequired[Rect]


class SetAttributeAsTextParams(CommandParams):
    nodeId: int
    text: str
    name: NotRequired[str]


class SetAttributeValueParams(CommandParams):
    nodeId: int
    name: str
    value: str


class SetFileInputFilesParams(CommandParams):
    files: list[str]
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]


class SetNodeNameParams(CommandParams):
    nodeId: int
    name: str


class SetNodeValueParams(CommandParams):
    nodeId: int
    value: str


class SetOuterHTMLParams(CommandParams):
    nodeId: int
    outerHTML: str


class CollectClassNamesFromSubtreeParams(CommandParams):
    nodeId: int


class CopyToParams(CommandParams):
    nodeId: int
    targetNodeId: int
    insertBeforeNodeId: NotRequired[int]


class DiscardSearchResultsParams(CommandParams):
    searchId: str


class GetAnchorElementParams(CommandParams):
    nodeId: int
    anchorSpecifier: NotRequired[str]


class GetContainerForNodeParams(CommandParams):
    nodeId: int
    containerName: NotRequired[str]
    physicalAxes: NotRequired[PhysicalAxes]
    logicalAxes: NotRequired[LogicalAxes]
    queriesScrollState: NotRequired[bool]


class GetContentQuadsParams(CommandParams):
    nodeId: NotRequired[int]
    backendNodeId: NotRequired[int]
    objectId: NotRequired[str]


class GetElementByRelationParams(CommandParams):
    nodeId: int
    relation: ElementRelation


class GetFileInfoParams(CommandParams):
    objectId: str


class GetFrameOwnerParams(CommandParams):
    frameId: str


class GetNodesForSubtreeByStyleParams(CommandParams):
    nodeId: int
    computedStyles: list[CSSComputedStyleProperty]
    pierce: NotRequired[bool]


class GetNodeStackTracesParams(CommandParams):
    nodeId: int


class GetQueryingDescendantForContainerParams(CommandParams):
    nodeId: int


class GetRelayoutBoundaryParams(CommandParams):
    nodeId: int


class GetSearchResultsParams(CommandParams):
    searchId: str
    fromIndex: int
    toIndex: int


class PerformSearchParams(CommandParams):
    query: str
    includeUserAgentShadowDOM: NotRequired[bool]


class PushNodeByPathToFrontendParams(CommandParams):
    path: str


class PushNodesByBackendIdsToFrontendParams(CommandParams):
    backendNodeIds: list[int]


class SetNodeStackTracesEnabledParams(CommandParams):
    enable: bool


class SetInspectedNodeParams(CommandParams):
    nodeId: int
