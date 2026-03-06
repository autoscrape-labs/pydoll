from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.accessibility.types import AXNode, AXNodeId
from pydoll.protocol.base import Command, EmptyParams, EmptyResponse, Response


class AccessibilityMethod(str, Enum):
    """Accessibility domain method names."""

    DISABLE = 'Accessibility.disable'
    ENABLE = 'Accessibility.enable'
    GET_PARTIAL_AX_TREE = 'Accessibility.getPartialAXTree'
    GET_FULL_AX_TREE = 'Accessibility.getFullAXTree'
    GET_ROOT_AX_NODE = 'Accessibility.getRootAXNode'
    GET_AX_NODE_AND_ANCESTORS = 'Accessibility.getAXNodeAndAncestors'
    GET_CHILD_AX_NODES = 'Accessibility.getChildAXNodes'
    QUERY_AX_TREE = 'Accessibility.queryAXTree'


class GetPartialAXTreeParams(TypedDict, total=False):
    """Parameters for getPartialAXTree command."""

    nodeId: int
    backendNodeId: int
    objectId: str
    fetchRelatives: bool


class GetFullAXTreeParams(TypedDict, total=False):
    """Parameters for getFullAXTree command."""

    depth: int
    frameId: str


class GetRootAXNodeParams(TypedDict, total=False):
    """Parameters for getRootAXNode command."""

    frameId: str


class GetAXNodeAndAncestorsParams(TypedDict, total=False):
    """Parameters for getAXNodeAndAncestors command."""

    nodeId: int
    backendNodeId: int
    objectId: str


class GetChildAXNodesParams(TypedDict, total=False):
    """Parameters for getChildAXNodes command."""

    id: AXNodeId
    frameId: str


class QueryAXTreeParams(TypedDict, total=False):
    """Parameters for queryAXTree command."""

    nodeId: int
    backendNodeId: int
    objectId: str
    accessibleName: str
    role: str


# Result types
class GetPartialAXTreeResult(TypedDict):
    """Result for getPartialAXTree command."""

    nodes: list[AXNode]


class GetFullAXTreeResult(TypedDict):
    """Result for getFullAXTree command."""

    nodes: list[AXNode]


class GetRootAXNodeResult(TypedDict):
    """Result for getRootAXNode command."""

    node: AXNode


class GetAXNodeAndAncestorsResult(TypedDict):
    """Result for getAXNodeAndAncestors command."""

    nodes: list[AXNode]


class GetChildAXNodesResult(TypedDict):
    """Result for getChildAXNodes command."""

    nodes: list[AXNode]


class QueryAXTreeResult(TypedDict):
    """Result for queryAXTree command."""

    nodes: list[AXNode]


# Response types
GetPartialAXTreeResponse = Response[GetPartialAXTreeResult]
GetFullAXTreeResponse = Response[GetFullAXTreeResult]
GetRootAXNodeResponse = Response[GetRootAXNodeResult]
GetAXNodeAndAncestorsResponse = Response[GetAXNodeAndAncestorsResult]
GetChildAXNodesResponse = Response[GetChildAXNodesResult]
QueryAXTreeResponse = Response[QueryAXTreeResult]

# Command types
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EmptyParams, Response[EmptyResponse]]
GetPartialAXTreeCommand = Command[GetPartialAXTreeParams, GetPartialAXTreeResponse]
GetFullAXTreeCommand = Command[GetFullAXTreeParams, GetFullAXTreeResponse]
GetRootAXNodeCommand = Command[GetRootAXNodeParams, GetRootAXNodeResponse]
GetAXNodeAndAncestorsCommand = Command[
    GetAXNodeAndAncestorsParams, GetAXNodeAndAncestorsResponse
]
GetChildAXNodesCommand = Command[GetChildAXNodesParams, GetChildAXNodesResponse]
QueryAXTreeCommand = Command[QueryAXTreeParams, QueryAXTreeResponse]
