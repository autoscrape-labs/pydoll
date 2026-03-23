from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.accessibility.methods import (
    AccessibilityMethod,
    GetAXNodeAndAncestorsParams,
    GetChildAXNodesParams,
    GetFullAXTreeParams,
    GetPartialAXTreeParams,
    GetRootAXNodeParams,
    QueryAXTreeParams,
)
from pydoll.protocol.base import Command

if TYPE_CHECKING:
    from pydoll.protocol.accessibility.methods import (
        DisableCommand,
        EnableCommand,
        GetAXNodeAndAncestorsCommand,
        GetChildAXNodesCommand,
        GetFullAXTreeCommand,
        GetPartialAXTreeCommand,
        GetRootAXNodeCommand,
        QueryAXTreeCommand,
    )
    from pydoll.protocol.accessibility.types import AXNodeId


class AccessibilityCommands:
    """
    Implementation of Chrome DevTools Protocol for the Accessibility domain.

    This class provides commands for interacting with the accessibility tree,
    enabling inspection and querying of accessible nodes on a page.

    See https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/
    """

    @staticmethod
    def disable() -> DisableCommand:
        """
        Disables the accessibility domain.

        Returns:
            DisableCommand: CDP command to disable the accessibility domain.
        """
        return Command(method=AccessibilityMethod.DISABLE)

    @staticmethod
    def enable() -> EnableCommand:
        """
        Enables the accessibility domain which causes AXNodeIds to remain
        consistent between method calls.

        Returns:
            EnableCommand: CDP command to enable the accessibility domain.
        """
        return Command(method=AccessibilityMethod.ENABLE)

    @staticmethod
    def get_partial_ax_tree(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        fetch_relatives: Optional[bool] = None,
    ) -> GetPartialAXTreeCommand:
        """
        Fetches the accessibility node and partial accessibility tree for this
        DOM node, if it exists.

        Args:
            node_id: Identifier of the node to get the partial accessibility
                tree for.
            backend_node_id: Identifier of the backend node to get the partial
                accessibility tree for.
            object_id: JavaScript object id of the node wrapper to get the
                partial accessibility tree for.
            fetch_relatives: Whether to fetch this node's ancestors, siblings
                and children. Defaults to True.

        Returns:
            GetPartialAXTreeCommand: CDP command to get the partial AX tree.
        """
        params = GetPartialAXTreeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if fetch_relatives is not None:
            params['fetchRelatives'] = fetch_relatives
        return Command(method=AccessibilityMethod.GET_PARTIAL_AX_TREE, params=params)

    @staticmethod
    def get_full_ax_tree(
        depth: Optional[int] = None,
        frame_id: Optional[str] = None,
    ) -> GetFullAXTreeCommand:
        """
        Fetches the entire accessibility tree for the root Document.

        Args:
            depth: The maximum depth at which descendants of the root node
                should be retrieved. If omitted, the full tree is returned.
            frame_id: The frame for whose document the AX tree should be
                retrieved. If omitted, the root frame is used.

        Returns:
            GetFullAXTreeCommand: CDP command to get the full AX tree.
        """
        params = GetFullAXTreeParams()
        if depth is not None:
            params['depth'] = depth
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_FULL_AX_TREE, params=params)

    @staticmethod
    def get_root_ax_node(
        frame_id: Optional[str] = None,
    ) -> GetRootAXNodeCommand:
        """
        Fetches the root node of the accessibility tree for a Document.

        Args:
            frame_id: The frame in whose document the node resides. If omitted,
                the root frame is used.

        Returns:
            GetRootAXNodeCommand: CDP command to get the root AX node.
        """
        params = GetRootAXNodeParams()
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_ROOT_AX_NODE, params=params)

    @staticmethod
    def get_ax_node_and_ancestors(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> GetAXNodeAndAncestorsCommand:
        """
        Fetches a node and all ancestors up to and including the root.

        Args:
            node_id: Identifier of the node to get ancestors for.
            backend_node_id: Identifier of the backend node to get ancestors for.
            object_id: JavaScript object id of the node wrapper to get
                ancestors for.

        Returns:
            GetAXNodeAndAncestorsCommand: CDP command to get a node and its ancestors.
        """
        params = GetAXNodeAndAncestorsParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=AccessibilityMethod.GET_AX_NODE_AND_ANCESTORS, params=params)

    @staticmethod
    def get_child_ax_nodes(
        id: AXNodeId,
        frame_id: Optional[str] = None,
    ) -> GetChildAXNodesCommand:
        """
        Fetches a particular accessibility node by AXNodeId.

        Args:
            id: The AXNodeId of the node whose children should be retrieved.
            frame_id: The frame in whose document the node resides. If omitted,
                the root frame is used.

        Returns:
            GetChildAXNodesCommand: CDP command to get child AX nodes.
        """
        params = GetChildAXNodesParams(id=id)
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_CHILD_AX_NODES, params=params)

    @staticmethod
    def query_ax_tree(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        accessible_name: Optional[str] = None,
        role: Optional[str] = None,
    ) -> QueryAXTreeCommand:
        """
        Queries the accessibility tree for a DOM subtree for nodes with a
        given name and/or role.

        Args:
            node_id: Identifier of the node for the root of the subtree to
                search in.
            backend_node_id: Identifier of the backend node for the root of
                the subtree to search in.
            object_id: JavaScript object id of the node wrapper for the root
                of the subtree to search in.
            accessible_name: Find nodes with this computed name.
            role: Find nodes with this computed role.

        Returns:
            QueryAXTreeCommand: CDP command to query the AX tree.
        """
        params = QueryAXTreeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if accessible_name is not None:
            params['accessibleName'] = accessible_name
        if role is not None:
            params['role'] = role
        return Command(method=AccessibilityMethod.QUERY_AX_TREE, params=params)
