from enum import Enum
from typing import Any

from typing_extensions import NotRequired, TypedDict

AXNodeId = str


class AXValueType(str, Enum):
    """Enum of possible property types."""

    BOOLEAN = 'boolean'
    TRISTATE = 'tristate'
    BOOLEAN_OR_UNDEFINED = 'booleanOrUndefined'
    IDREF = 'idref'
    IDREF_LIST = 'idrefList'
    INTEGER = 'integer'
    NODE = 'node'
    NODE_LIST = 'nodeList'
    NUMBER = 'number'
    STRING = 'string'
    COMPUTED_STRING = 'computedString'
    TOKEN = 'token'
    TOKEN_LIST = 'tokenList'
    DOM_RELATION = 'domRelation'
    ROLE = 'role'
    INTERNAL_ROLE = 'internalRole'
    VALUE_UNDEFINED = 'valueUndefined'


class AXValueSourceType(str, Enum):
    """Enum of possible property sources."""

    ATTRIBUTE = 'attribute'
    IMPLICIT = 'implicit'
    STYLE = 'style'
    CONTENTS = 'contents'
    PLACEHOLDER = 'placeholder'
    RELATED_ELEMENT = 'relatedElement'


class AXValueNativeSourceType(str, Enum):
    """Enum of possible native property sources."""

    DESCRIPTION = 'description'
    FIGCAPTION = 'figcaption'
    LABEL = 'label'
    LABELFOR = 'labelfor'
    LABELWRAPPED = 'labelwrapped'
    LEGEND = 'legend'
    RUBYANNOTATION = 'rubyannotation'
    TABLECAPTION = 'tablecaption'
    TITLE = 'title'
    OTHER = 'other'


class AXPropertyName(str, Enum):
    """Values of AXProperty name.

    See https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/#type-AXPropertyName
    """

    # States
    BUSY = 'busy'
    DISABLED = 'disabled'
    EDITABLE = 'editable'
    FOCUSABLE = 'focusable'
    FOCUSED = 'focused'
    HIDDEN = 'hidden'
    HIDDEN_ROOT = 'hiddenRoot'
    INVALID = 'invalid'
    KEYSHORTCUTS = 'keyshortcuts'
    SETTABLE = 'settable'
    ROLEDESCRIPTION = 'roledescription'
    # Live region attributes
    LIVE = 'live'
    ATOMIC = 'atomic'
    RELEVANT = 'relevant'
    ROOT = 'root'
    # Widget attributes
    AUTOCOMPLETE = 'autocomplete'
    HAS_POPUP = 'hasPopup'
    LEVEL = 'level'
    MULTISELECTABLE = 'multiselectable'
    ORIENTATION = 'orientation'
    MULTILINE = 'multiline'
    READONLY = 'readonly'
    REQUIRED = 'required'
    VALUEMIN = 'valuemin'
    VALUEMAX = 'valuemax'
    VALUETEXT = 'valuetext'
    # Widget states
    CHECKED = 'checked'
    EXPANDED = 'expanded'
    MODAL = 'modal'
    PRESSED = 'pressed'
    SELECTED = 'selected'
    # Relationship attributes
    ACTIVEDESCENDANT = 'activedescendant'
    CONTROLS = 'controls'
    DESCRIBEDBY = 'describedby'
    DETAILS = 'details'
    ERRORMESSAGE = 'errormessage'
    FLOWTO = 'flowto'
    LABELLEDBY = 'labelledby'
    OWNS = 'owns'
    # Extra attributes
    ACTIONS = 'actions'
    URL = 'url'
    # Hidden reasons
    ACTIVE_FULLSCREEN_ELEMENT = 'activeFullscreenElement'
    ANCESTOR_DISALLOWS_CHILD = 'ancestorDisallowsChild'
    ANCESTOR_IS_LEAF_NODE = 'ancestorIsLeafNode'
    ARIA_HIDDEN_ELEMENT = 'ariaHiddenElement'
    ARIA_HIDDEN_SUBTREE = 'ariaHiddenSubtree'
    DISPLAY_LOCK = 'displayLock'
    EMPTY_ALT = 'emptyAlt'
    FROM_SUBTREE_HTML = 'fromSubtreeHtml'
    HIDDEN_BY_CHILD_TREE = 'hiddenByChildTree'
    IGNORED_PARENT = 'ignoredParent'
    INLINE_TEXT_BOX = 'inlineTextBox'
    NOT_RENDERED = 'notRendered'
    NOT_VISIBLE = 'notVisible'
    POTENTIALLY_OFFSCREEN = 'potentiallyOffscreen'
    PRESENTATIONAL_ROLE = 'presentationalRole'
    ROLE_PRESENTATION = 'rolePresentation'
    ACTIVE_MODAL_DIALOG = 'activeModalDialog'
    ACTIVE_ARIA_MODAL_DIALOG = 'activeAriaModalDialog'
    EMPTY_TEXT = 'emptyText'
    INERT_ELEMENT = 'inertElement'
    INERT_SUBTREE = 'inertSubtree'
    LABEL_CONTAINER = 'labelContainer'
    LABEL_FOR = 'labelFor'
    PROBABLY_PRESENTATIONAL = 'probablyPresentational'
    INACTIVE_CAROUSEL_TAB_CONTENT = 'inactiveCarouselTabContent'
    UNINTERESTING = 'uninteresting'


class AXRelatedNode(TypedDict):
    """A node related to the current node via an accessibility property."""

    backendDOMNodeId: int
    idref: NotRequired[str]
    text: NotRequired[str]


class AXValueSource(TypedDict):
    """A single source for a computed AX property."""

    type: AXValueSourceType
    value: NotRequired['AXValue']
    attribute: NotRequired[str]
    attributeValue: NotRequired['AXValue']
    superseded: NotRequired[bool]
    nativeSource: NotRequired[AXValueNativeSourceType]
    nativeSourceValue: NotRequired['AXValue']
    invalid: NotRequired[bool]
    invalidReason: NotRequired[str]


class AXValue(TypedDict):
    """A single computed AX property."""

    type: AXValueType
    value: NotRequired[Any]
    relatedNodes: NotRequired[list[AXRelatedNode]]
    sources: NotRequired[list[AXValueSource]]


class AXProperty(TypedDict):
    """A name/value pair that is an accessibility property."""

    name: AXPropertyName
    value: AXValue


class AXNode(TypedDict):
    """A node in the accessibility tree."""

    nodeId: AXNodeId
    ignored: bool
    ignoredReasons: NotRequired[list[AXProperty]]
    role: NotRequired[AXValue]
    chromeRole: NotRequired[AXValue]
    name: NotRequired[AXValue]
    description: NotRequired[AXValue]
    value: NotRequired[AXValue]
    properties: NotRequired[list[AXProperty]]
    parentId: NotRequired[AXNodeId]
    childIds: NotRequired[list[AXNodeId]]
    backendDOMNodeId: NotRequired[int]
    frameId: NotRequired[str]
