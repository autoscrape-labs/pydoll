from enum import Enum


class TargetEvent(str, Enum):
    """
    Events from the Target domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Target-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about target creation, destruction, and communication between targets.
    """

    RECEIVED_MESSAGE_FROM_TARGET = 'Target.receivedMessageFromTarget'
    """
    Notifies about a new protocol message received from the session
    (as reported in attachedToTarget event).

    Args:
        sessionId (SessionID): Identifier of a session which sends a message.
        message (str): The message content.
        targetId (TargetID): Deprecated.
    """

    TARGET_CRASHED = 'Target.targetCrashed'
    """
    Issued when a target has crashed.

    Args:
        targetId (TargetID): Identifier of the crashed target.
        status (str): Termination status type.
        errorCode (int): Termination error code.
    """

    TARGET_CREATED = 'Target.targetCreated'
    """
    Issued when a possible inspection target is created.

    Args:
        targetInfo (TargetInfo): Information about the created target.
    """

    TARGET_DESTROYED = 'Target.targetDestroyed'
    """
    Issued when a target is destroyed.

    Args:
        targetId (TargetID): Identifier of the destroyed target.
    """

    TARGET_INFO_CHANGED = 'Target.targetInfoChanged'
    """
    Issued when some information about a target has changed.
    This only happens between targetCreated and targetDestroyed.

    Args:
        targetInfo (TargetInfo): Updated information about the target.
    """

    ATTACHED_TO_TARGET = 'Target.attachedToTarget'
    """
    Issued when attached to target because of auto-attach or attachToTarget command.

    Args:
        sessionId (SessionID): Identifier assigned to the session used to send/receive messages.
        targetInfo (TargetInfo): Information about the target.
        waitingForDebugger (bool): Whether the target is waiting for debugger to attach.
    """

    DETACHED_FROM_TARGET = 'Target.detachedFromTarget'
    """
    Issued when detached from target for any reason (including detachFromTarget command).
    Can be issued multiple times per target if multiple sessions have been attached to it.

    Args:
        sessionId (SessionID): Detached session identifier.
        targetId (TargetID): Deprecated.
    """
