from enum import Enum

from typing_extensions import NotRequired, TypedDict

ClientWindow = str
"""Unique identifier for a client window."""

UserContext = str
"""Unique identifier for a user context."""


class ClientWindowState(str, Enum):
    """Possible states of a client window."""

    FULLSCREEN = 'fullscreen'
    MAXIMIZED = 'maximized'
    MINIMIZED = 'minimized'
    NORMAL = 'normal'


class ClientWindowInfo(TypedDict):
    """Properties of a client window."""

    active: bool
    clientWindow: ClientWindow
    height: int
    state: ClientWindowState
    width: int
    x: int
    y: int


class UserContextInfo(TypedDict):
    """Properties of a user context."""

    userContext: UserContext


class DownloadBehaviorAllowed(TypedDict):
    """Download behavior that allows downloads to a destination folder."""

    type: str  # "allowed"
    destinationFolder: str


class DownloadBehaviorDenied(TypedDict):
    """Download behavior that denies downloads."""

    type: str  # "denied"


DownloadBehavior = DownloadBehaviorAllowed | DownloadBehaviorDenied
