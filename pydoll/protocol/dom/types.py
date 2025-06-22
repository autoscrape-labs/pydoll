from typing import Annotated, Any, TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

from typing_extensions import TypedDict

from pydoll.constants import CompatibilityMode, PseudoType, ShadowRootType

Quad = Annotated[list[float], 'Format: [x1, y1, x2, y2, x3, y3, x4, y4]']


class Rect(TypedDict):
    """Rectangle for capturing screenshot or clip rectangle."""

    x: float
    y: float
    width: float
    height: float


class CSSComputedStyleProperty(TypedDict):
    name: str
    value: str


class BackendNode(TypedDict):
    nodeType: int
    nodeName: str
    backendNodeId: int


class Node(TypedDict):
    nodeId: int
    parentId: NotRequired[int]
    backendNodeId: int
    nodeType: int
    nodeName: str
    localName: str
    nodeValue: str
    childNodeCount: NotRequired[int]
    children: NotRequired[list['Node']]
    attributes: NotRequired[list[str]]
    documentURL: NotRequired[str]
    baseURL: NotRequired[str]
    publicId: NotRequired[str]
    systemId: NotRequired[str]
    internalSubset: NotRequired[str]
    xmlVersion: NotRequired[str]
    name: NotRequired[str]
    value: NotRequired[str]
    pseudoType: NotRequired[PseudoType]
    pseudoIdentifier: NotRequired[str]
    shadowRootType: NotRequired[ShadowRootType]
    frameId: NotRequired[str]
    contentDocument: NotRequired['Node']
    shadowRoots: NotRequired[list['Node']]
    templateContent: NotRequired['Node']
    pseudoElements: NotRequired[list['Node']]
    importedDocument: NotRequired['Node']
    distributedNodes: NotRequired[list[BackendNode]]
    isSVG: NotRequired[bool]
    compatibilityMode: NotRequired[CompatibilityMode]
    assignedSlot: NotRequired[BackendNode]
    isScrollable: NotRequired[bool]


class DetachedElementInfo(TypedDict):
    treeNode: Node
    retainedNodeIds: list[int]


class ShapeOutsideInfo(TypedDict):
    bounds: Quad
    shape: list[Any]
    marginShape: list[Any]


class BoxModel(TypedDict):
    content: Quad
    padding: Quad
    border: Quad
    margin: Quad
    width: int
    height: int
    shapeOutside: NotRequired[ShapeOutsideInfo]


class EventFileChooserOpenedParams(TypedDict):
    frameId: str
    mode: str
    backendNodeId: int


class EventFileChooserOpened(TypedDict):
    method: str
    params: EventFileChooserOpenedParams
