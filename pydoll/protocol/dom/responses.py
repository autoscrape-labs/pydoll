from typing import TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from typing_extensions import TypedDict

from pydoll.protocol.dom.types import (
    BoxModel,
    DetachedElementInfo,
    Node,
    Quad,
)
from pydoll.protocol.runtime.types import RemoteObject, StackTrace


class DescribeNodeResultDict(TypedDict):
    node: Node


class GetAttributesResultDict(TypedDict):
    attributes: list[str]


class GetBoxModelResultDict(TypedDict):
    model: BoxModel


class GetDocumentResultDict(TypedDict):
    root: Node


class GetNodeForLocationResultDict(TypedDict):
    backendNodeId: int
    frameId: str
    nodeId: NotRequired[int]


class GetOuterHTMLResultDict(TypedDict):
    outerHTML: str


class MoveToResultDict(TypedDict):
    nodeId: int


class QuerySelectorResultDict(TypedDict):
    nodeId: int


class QuerySelectorAllResultDict(TypedDict):
    nodeIds: list[int]


class RequestNodeResultDict(TypedDict):
    nodeId: int


class ResolveNodeResultDict(TypedDict):
    object: RemoteObject


class SetNodeNameResultDict(TypedDict):
    nodeId: int


class CollectClassNamesFromSubtreeResultDict(TypedDict):
    classNames: list[str]


class CopyToResultDict(TypedDict):
    nodeId: int


class GetAnchorElementResultDict(TypedDict):
    nodeId: int


class GetContainerForNodeResultDict(TypedDict):
    nodeId: int


class GetContentQuadsResultDict(TypedDict):
    quads: list[Quad]


class GetDetachedDomNodesResultDict(TypedDict):
    detachedNodes: list[DetachedElementInfo]


class GetElementByRelationResultDict(TypedDict):
    nodeId: int


class GetFileInfoResultDict(TypedDict):
    path: str


class GetFrameOwnerResultDict(TypedDict):
    backendNodeId: int
    nodeId: NotRequired[int]


class GetNodesForSubtreeByStyleResultDict(TypedDict):
    nodeIds: list[int]


class GetNodeStackTracesResultDict(TypedDict):
    creation: StackTrace


class GetQueryingDescendantForContainerResultDict(TypedDict):
    nodeIds: list[int]


class GetRelayoutBoundaryResultDict(TypedDict):
    nodeId: int


class GetSearchResultsResultDict(TypedDict):
    nodeIds: list[int]


class GetTopLayerElementsResultDict(TypedDict):
    nodeIds: list[int]


class PerformSearchResultDict(TypedDict):
    searchId: str
    resultCount: int


class PushNodeByPathToFrontendResultDict(TypedDict):
    nodeId: int


class PushNodesByBackendIdsToFrontendResultDict(TypedDict):
    nodeIds: list[int]


class DescribeNodeResponse(TypedDict):
    result: DescribeNodeResultDict


class GetAttributesResponse(TypedDict):
    result: GetAttributesResultDict


class GetBoxModelResponse(TypedDict):
    result: GetBoxModelResultDict


class GetDocumentResponse(TypedDict):
    result: GetDocumentResultDict


class GetNodeForLocationResponse(TypedDict):
    result: GetNodeForLocationResultDict


class GetOuterHTMLResponse(TypedDict):
    result: GetOuterHTMLResultDict


class MoveToResponse(TypedDict):
    result: MoveToResultDict


class QuerySelectorResponse(TypedDict):
    result: QuerySelectorResultDict


class QuerySelectorAllResponse(TypedDict):
    result: QuerySelectorAllResultDict


class RequestNodeResponse(TypedDict):
    result: RequestNodeResultDict


class ResolveNodeResponse(TypedDict):
    result: ResolveNodeResultDict


class SetNodeNameResponse(TypedDict):
    result: SetNodeNameResultDict


class CollectClassNamesFromSubtreeResponse(TypedDict):
    result: CollectClassNamesFromSubtreeResultDict


class CopyToResponse(TypedDict):
    result: CopyToResultDict


class GetAnchorElementResponse(TypedDict):
    result: GetAnchorElementResultDict


class GetContainerForNodeResponse(TypedDict):
    result: GetContainerForNodeResultDict


class GetContentQuadsResponse(TypedDict):
    result: GetContentQuadsResultDict


class GetDetachedDomNodesResponse(TypedDict):
    result: GetDetachedDomNodesResultDict


class GetElementByRelationResponse(TypedDict):
    result: GetElementByRelationResultDict


class GetFileInfoResponse(TypedDict):
    result: GetFileInfoResultDict


class GetFrameOwnerResponse(TypedDict):
    result: GetFrameOwnerResultDict


class GetNodesForSubtreeByStyleResponse(TypedDict):
    result: GetNodesForSubtreeByStyleResultDict


class GetNodeStackTracesResponse(TypedDict):
    result: GetNodeStackTracesResultDict


class GetQueryingDescendantForContainerResponse(TypedDict):
    result: GetQueryingDescendantForContainerResultDict


class GetRelayoutBoundaryResponse(TypedDict):
    result: GetRelayoutBoundaryResultDict


class GetSearchResultsResponse(TypedDict):
    result: GetSearchResultsResultDict


class GetTopLayerElementsResponse(TypedDict):
    result: GetTopLayerElementsResultDict


class PerformSearchResponse(TypedDict):
    result: PerformSearchResultDict


class PushNodeByPathToFrontendResponse(TypedDict):
    result: PushNodeByPathToFrontendResultDict


class PushNodesByBackendIdsToFrontendResponse(TypedDict):
    result: PushNodesByBackendIdsToFrontendResultDict
