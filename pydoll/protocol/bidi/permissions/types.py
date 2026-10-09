from enum import Enum

from typing_extensions import TypedDict


class PermissionState(str, Enum):
    """Permission states accepted by permissions.setPermission."""

    GRANTED = 'granted'
    DENIED = 'denied'
    PROMPT = 'prompt'


class PermissionDescriptor(TypedDict):
    """W3C PermissionDescriptor identifying the permission to set."""

    name: str
