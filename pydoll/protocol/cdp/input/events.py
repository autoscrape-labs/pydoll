from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.cdp.base import CDPEvent
from pydoll.protocol.cdp.input.types import DragData


class InputEvent(str, Enum):
    """
    Events from the Input domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Input-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about user input interactions that can be intercepted or simulated.
    """

    DRAG_INTERCEPTED = 'Input.dragIntercepted'
    """
    Emitted only when Input.setInterceptDrags is enabled. Use this data with
    Input.dispatchDragEvent to restore normal drag and drop behavior.

    Args:
        data (DragData): Contains information about the dragged data.
    """


class DragInterceptedEventParams(TypedDict):
    """Parameters for dragIntercepted event."""

    data: DragData


DragInterceptedEvent = CDPEvent[DragInterceptedEventParams]
