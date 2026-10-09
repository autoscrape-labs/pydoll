from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.cdp.base import CDPEvent
from pydoll.protocol.cdp.dom.types import BackendNode, Node, NodeId


class DomEvent(str, Enum):
    """
    Events from the DOM domain of the Chrome DevTools Protocol.

    This enumeration contains the names of DOM-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about changes to the DOM structure, attributes, and other DOM-related activities.
    """

    ATTRIBUTE_MODIFIED = 'DOM.attributeModified'
    """
    Fired when Element's attribute is modified.

    Args:
        nodeId (NodeId): Id of the node that has changed.
        name (str): Attribute name.
        value (str): Attribute value.
    """

    ATTRIBUTE_REMOVED = 'DOM.attributeRemoved'
    """
    Fired when Element's attribute is removed.

    Args:
        nodeId (NodeId): Id of the node that has changed.
        name (str): Attribute name.
    """

    CHARACTER_DATA_MODIFIED = 'DOM.characterDataModified'
    """
    Mirrors DOMCharacterDataModified event.

    Args:
        nodeId (NodeId): Id of the node that has changed.
        characterData (str): New text value.
    """

    CHILD_NODE_COUNT_UPDATED = 'DOM.childNodeCountUpdated'
    """
    Fired when Container's child node count has changed.

    Args:
        nodeId (NodeId): Id of the node that has changed.
        childNodeCount (int): New node count.
    """

    CHILD_NODE_INSERTED = 'DOM.childNodeInserted'
    """
    Mirrors DOMNodeInserted event.

    Args:
        parentNodeId (NodeId): Id of the node that has changed.
        previousNodeId (NodeId): Id of the previous sibling.
        node (Node): Inserted node data.
    """

    CHILD_NODE_REMOVED = 'DOM.childNodeRemoved'
    """
    Mirrors DOMNodeRemoved event.

    Args:
        parentNodeId (NodeId): Parent id.
        nodeId (NodeId): Id of the node that has been removed.
    """

    DISTRIBUTED_NODES_UPDATED = 'DOM.distributedNodesUpdated'
    """
    Called when distribution is changed.

    Args:
        insertionPointId (NodeId): Insertion point where distributed nodes were updated.
        distributedNodes (array[BackendNode]): Distributed nodes for given insertion point.
    """

    DOCUMENT_UPDATED = 'DOM.documentUpdated'
    """
    Fired when Document has been totally updated. Node ids are no longer valid.
    """

    INLINE_STYLE_INVALIDATED = 'DOM.inlineStyleInvalidated'
    """
    Fired when Element's inline style is modified via a CSS property modification.

    Args:
        nodeIds (array[NodeId]): Ids of the nodes for which the inline styles have been invalidated.
    """

    PSEUDO_ELEMENT_ADDED = 'DOM.pseudoElementAdded'
    """
    Called when a pseudo element is added to an element.

    Args:
        parentId (NodeId): Pseudo element's parent element id.
        pseudoElement (Node): The added pseudo element.
    """

    PSEUDO_ELEMENT_REMOVED = 'DOM.pseudoElementRemoved'
    """
    Called when a pseudo element is removed from an element.

    Args:
        parentId (NodeId): Pseudo element's parent element id.
        pseudoElementId (NodeId): The removed pseudo element id.
    """

    SCROLLABLE_FLAG_UPDATED = 'DOM.scrollableFlagUpdated'
    """
    Fired when a node's scrollability state changes.

    Args:
        nodeId (DOM.NodeId): The id of the node.
        isScrollable (bool): If the node is scrollable.
    """

    SHADOW_ROOT_POPPED = 'DOM.shadowRootPopped'
    """
    Called when shadow root is popped from the element.

    Args:
        hostId (NodeId): Host element id.
        rootId (NodeId): Shadow root id.
    """

    SHADOW_ROOT_PUSHED = 'DOM.shadowRootPushed'
    """
    Called when shadow root is pushed into the element.

    Args:
        hostId (NodeId): Host element id.
        root (Node): Shadow root.
    """

    SET_CHILD_NODES = 'DOM.setChildNodes'
    """
    Fired when backend wants to provide client with the missing DOM structure.
    This happens upon most of the calls requesting node ids.

    Args:
        parentId (NodeId): Parent node id to populate with children.
        nodes (array[Node]): Child nodes array.
    """

    TOP_LAYER_ELEMENTS_UPDATED = 'DOM.topLayerElementsUpdated'
    """
    Called when top layer elements are changed.
    """


# Event parameter types
class AttributeModifiedEventParams(TypedDict):
    """Parameters for attributeModified event."""

    nodeId: NodeId
    name: str
    value: str


class AttributeRemovedEventParams(TypedDict):
    """Parameters for attributeRemoved event."""

    nodeId: NodeId
    name: str


class CharacterDataModifiedEventParams(TypedDict):
    """Parameters for characterDataModified event."""

    nodeId: NodeId
    characterData: str


class ChildNodeCountUpdatedEventParams(TypedDict):
    """Parameters for childNodeCountUpdated event."""

    nodeId: NodeId
    childNodeCount: int


class ChildNodeInsertedEventParams(TypedDict):
    """Parameters for childNodeInserted event."""

    parentNodeId: NodeId
    previousNodeId: NodeId
    node: Node


class ChildNodeRemovedEventParams(TypedDict):
    """Parameters for childNodeRemoved event."""

    parentNodeId: NodeId
    nodeId: NodeId


class DistributedNodesUpdatedEventParams(TypedDict):
    """Parameters for distributedNodesUpdated event."""

    insertionPointId: NodeId
    distributedNodes: list[BackendNode]


class DocumentUpdatedEventParams(TypedDict):
    """Parameters for documentUpdated event."""

    pass


class InlineStyleInvalidatedEventParams(TypedDict):
    """Parameters for inlineStyleInvalidated event."""

    nodeIds: list[NodeId]


class PseudoElementAddedEventParams(TypedDict):
    """Parameters for pseudoElementAdded event."""

    parentId: NodeId
    pseudoElement: Node


class PseudoElementRemovedEventParams(TypedDict):
    """Parameters for pseudoElementRemoved event."""

    parentId: NodeId
    pseudoElementId: NodeId


class ScrollableFlagUpdatedEventParams(TypedDict):
    """Parameters for scrollableFlagUpdated event."""

    nodeId: NodeId
    isScrollable: bool


class ShadowRootPoppedEventParams(TypedDict):
    """Parameters for shadowRootPopped event."""

    hostId: NodeId
    rootId: NodeId


class ShadowRootPushedEventParams(TypedDict):
    """Parameters for shadowRootPushed event."""

    hostId: NodeId
    root: Node


class SetChildNodesEventParams(TypedDict):
    """Parameters for setChildNodes event."""

    parentId: NodeId
    nodes: list[Node]


class TopLayerElementsUpdatedEventParams(TypedDict):
    """Parameters for topLayerElementsUpdated event."""

    pass


# Event types
AttributeModifiedEvent = CDPEvent[AttributeModifiedEventParams]
AttributeRemovedEvent = CDPEvent[AttributeRemovedEventParams]
CharacterDataModifiedEvent = CDPEvent[CharacterDataModifiedEventParams]
ChildNodeCountUpdatedEvent = CDPEvent[ChildNodeCountUpdatedEventParams]
ChildNodeInsertedEvent = CDPEvent[ChildNodeInsertedEventParams]
ChildNodeRemovedEvent = CDPEvent[ChildNodeRemovedEventParams]
DistributedNodesUpdatedEvent = CDPEvent[DistributedNodesUpdatedEventParams]
DocumentUpdatedEvent = CDPEvent[DocumentUpdatedEventParams]
InlineStyleInvalidatedEvent = CDPEvent[InlineStyleInvalidatedEventParams]
PseudoElementAddedEvent = CDPEvent[PseudoElementAddedEventParams]
PseudoElementRemovedEvent = CDPEvent[PseudoElementRemovedEventParams]
ScrollableFlagUpdatedEvent = CDPEvent[ScrollableFlagUpdatedEventParams]
ShadowRootPoppedEvent = CDPEvent[ShadowRootPoppedEventParams]
ShadowRootPushedEvent = CDPEvent[ShadowRootPushedEventParams]
SetChildNodesEvent = CDPEvent[SetChildNodesEventParams]
TopLayerElementsUpdatedEvent = CDPEvent[TopLayerElementsUpdatedEventParams]
