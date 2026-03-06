from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.accessibility.types import AXNode
from pydoll.protocol.base import CDPEvent


class AccessibilityEvent(str, Enum):
    """
    Events from the Accessibility domain of the Chrome DevTools Protocol.

    See https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/
    """

    LOAD_COMPLETE = 'Accessibility.loadComplete'
    """
    Mirrors the load complete event sent by the browser to assistive technology
    when the web page has finished loading.

    Args:
        root (AXNode): New document root node.
    """

    NODES_UPDATED = 'Accessibility.nodesUpdated'
    """
    Fired when a node is updated in the accessibility tree.

    Args:
        nodes (list[AXNode]): Updated nodes.
    """


class LoadCompleteEventParams(TypedDict):
    """Parameters for the loadComplete event."""

    root: AXNode


class NodesUpdatedEventParams(TypedDict):
    """Parameters for the nodesUpdated event."""

    nodes: list[AXNode]


LoadCompleteEvent = CDPEvent[LoadCompleteEventParams]
NodesUpdatedEvent = CDPEvent[NodesUpdatedEventParams]
