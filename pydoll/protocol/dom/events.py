from enum import Enum


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

    DOCUMENT_UPDATED = 'DOM.documentUpdated'
    """
    Fired when Document has been totally updated. Node ids are no longer valid.
    """

    SET_CHILD_NODES = 'DOM.setChildNodes'
    """
    Fired when backend wants to provide client with the missing DOM structure.
    This happens upon most of the calls requesting node ids.

    Args:
        parentId (NodeId): Parent node id to populate with children.
        nodes (array[Node]): Child nodes array.
    """

    DISTRIBUTED_NODES_UPDATED = 'DOM.distributedNodesUpdated'
    """
    Called when distribution is changed.

    Args:
        insertionPointId (NodeId): Insertion point where distributed nodes were updated.
        distributedNodes (array[BackendNode]): Distributed nodes for given insertion point.
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

    TOP_LAYER_ELEMENTS_UPDATED = 'DOM.topLayerElementsUpdated'
    """
    Called when top layer elements are changed.
    """
