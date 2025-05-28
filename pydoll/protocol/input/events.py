from enum import Enum


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
