from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.base import CDPEvent, EmptyParams


class InspectorEvent(str, Enum):
    """
    Events from the Inspector domain of the Chrome DevTools Protocol.

    Chrome sends them on a page target's own session, without
    ``Inspector.enable``, to report what happened to the page's renderer.
    """

    DETACHED = 'Inspector.detached'
    """
    Fired when the remote debugging connection is about to be terminated.

    Args:
        reason (str): The reason why the connection is being terminated.
    """

    TARGET_CRASHED = 'Inspector.targetCrashed'
    """
    Fired when the debugging target's renderer process has crashed.

    Chrome stops answering every command that needs the renderer until a
    navigation or a reload starts a new one.
    """

    TARGET_RELOADED_AFTER_CRASH = 'Inspector.targetReloadedAfterCrash'
    """
    Fired when the debugging target has reloaded after a crash, once a
    navigation or a reload started a new renderer.
    """


class DetachedEventParams(TypedDict):
    """Parameters for the `detached` event."""

    reason: str


DetachedEvent = CDPEvent[DetachedEventParams]
TargetCrashedEvent = CDPEvent[EmptyParams]
TargetReloadedAfterCrashEvent = CDPEvent[EmptyParams]
