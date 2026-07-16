from enum import Enum
from typing import Annotated, Any

from typing_extensions import TypedDict

NodeId = int
BackendNodeId = int
Quad = Annotated[list[float], 'Format: [x1, y1, x2, y2, x3, y3, x4, y4]']


class PseudoType(str, Enum):
    """Pseudo element type."""

    FIRST_LINE = 'first-line'
    FIRST_LETTER = 'first-letter'
    CHECKMARK = 'checkmark'
    BEFORE = 'before'
    AFTER = 'after'
    PICKER_ICON = 'picker-icon'
    MARKER = 'marker'
    BACKDROP = 'backdrop'
    COLUMN = 'column'
    SELECTION = 'selection'
    SEARCH_TEXT = 'search-text'
    TARGET_TEXT = 'target-text'
    SPELLING_ERROR = 'spelling-error'
    GRAMMAR_ERROR = 'grammar-error'
    HIGHLIGHT = 'highlight'
    FIRST_LINE_INHERITED = 'first-line-inherited'
    SCROLL_MARKER = 'scroll-marker'
    SCROLL_MARKER_GROUP = 'scroll-marker-group'
    SCROLL_BUTTON = 'scroll-button'
    SCROLLBAR = 'scrollbar'
    SCROLLBAR_THUMB = 'scrollbar-thumb'
    SCROLLBAR_BUTTON = 'scrollbar-button'
    SCROLLBAR_TRACK = 'scrollbar-track'
    SCROLLBAR_TRACK_PIECE = 'scrollbar-track-piece'
    SCROLLBAR_CORNER = 'scrollbar-corner'
    RESIZER = 'resizer'
    INPUT_LIST_BUTTON = 'input-list-button'
    VIEW_TRANSITION = 'view-transition'
    VIEW_TRANSITION_GROUP = 'view-transition-group'
    VIEW_TRANSITION_IMAGE_PAIR = 'view-transition-image-pair'
    VIEW_TRANSITION_GROUP_CHILDREN = 'view-transition-group-children'
    VIEW_TRANSITION_OLD = 'view-transition-old'
    VIEW_TRANSITION_NEW = 'view-transition-new'
    PLACEHOLDER = 'placeholder'
    FILE_SELECTOR_BUTTON = 'file-selector-button'
    DETAILS_CONTENT = 'details-content'
    PICKER = 'picker'
    PERMISSION_ICON = 'permission-icon'


class ShadowRootType(str, Enum):
    """Shadow root type."""

    USER_AGENT = 'user-agent'
    OPEN = 'open'
    CLOSED = 'closed'


class CompatibilityMode(str, Enum):
    """Document compatibility mode."""

    QUIRKS_MODE = 'QuirksMode'
    LIMITED_QUIRKS_MODE = 'LimitedQuirksMode'
    NO_QUIRKS_MODE = 'NoQuirksMode'


class PhysicalAxes(str, Enum):
    """ContainerSelector physical axes."""

    HORIZONTAL = 'Horizontal'
    VERTICAL = 'Vertical'
    BOTH = 'Both'


class LogicalAxes(str, Enum):
    """ContainerSelector logical axes."""

    INLINE = 'Inline'
    BLOCK = 'Block'
    BOTH = 'Both'


class ScrollOrientation(str, Enum):
    """Physical scroll orientation."""

    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'


class IncludeWhitespace(str, Enum):
    """Include whitespace options."""

    NONE = 'none'
    ALL = 'all'


class RelationType(str, Enum):
    """Element relation types."""

    POPOVER_TARGET = 'PopoverTarget'
    INTEREST_TARGET = 'InterestTarget'
    COMMAND_FOR = 'CommandFor'


class BackendNode(TypedDict):
    """Backend node with a friendly name."""

    nodeType: int
    nodeName: str
    backendNodeId: BackendNodeId


class Node(TypedDict, total=False):
    """DOM interaction is implemented in terms of mirror objects that represent the actual DOM
    nodes."""

    nodeId: NodeId
    parentId: NodeId
    backendNodeId: BackendNodeId
    nodeType: int
    nodeName: str
    localName: str
    nodeValue: str
    childNodeCount: int
    children: list['Node']
    attributes: list[str]
    documentURL: str
    baseURL: str
    publicId: str
    systemId: str
    internalSubset: str
    xmlVersion: str
    name: str
    value: str
    pseudoType: PseudoType
    pseudoIdentifier: str
    shadowRootType: ShadowRootType
    frameId: str
    contentDocument: 'Node'
    shadowRoots: list['Node']
    templateContent: 'Node'
    pseudoElements: list['Node']
    importedDocument: 'Node'  # deprecated
    distributedNodes: list[BackendNode]
    isSVG: bool
    compatibilityMode: CompatibilityMode
    assignedSlot: BackendNode
    isScrollable: bool


class DetachedElementInfo(TypedDict):
    """A structure to hold the top-level node of a detached tree and an array of its retained
    descendants."""

    treeNode: Node
    retainedNodeIds: list[NodeId]


class RGBA(TypedDict, total=False):
    """A structure holding an RGBA color."""

    r: int  # The red component, in the [0-255] range.
    g: int  # The green component, in the [0-255] range.
    b: int  # The blue component, in the [0-255] range.
    a: float  # The alpha component, in the [0-1] range (default: 1).


class BoxModel(TypedDict, total=False):
    """Box model."""

    content: Quad
    padding: Quad
    border: Quad
    margin: Quad
    width: int
    height: int
    shapeOutside: 'ShapeOutsideInfo'


class ShapeOutsideInfo(TypedDict):
    """CSS Shape Outside details."""

    bounds: Quad
    shape: list[Any]
    marginShape: list[Any]


class Rect(TypedDict):
    """Rectangle."""

    x: float
    y: float
    width: float
    height: float


class CSSComputedStyleProperty(TypedDict):
    """CSS computed style property."""

    name: str
    value: str
