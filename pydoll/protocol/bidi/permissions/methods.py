from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.permissions.types import PermissionDescriptor


class PermissionsMethod(str, Enum):
    """permissions module method names."""

    SET_PERMISSION = 'permissions.setPermission'


class SetPermissionParameters(TypedDict):
    """Parameters for permissions.setPermission command."""

    descriptor: PermissionDescriptor
    state: str
    origin: str
    userContext: NotRequired[str]


SetPermissionCommand = Command[SetPermissionParameters, CommandResponse[EmptyResult]]
SetPermissionResponse = CommandResponse[EmptyResult]
