from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.permissions.methods import (
    PermissionsMethod,
    SetPermissionParameters,
)

if TYPE_CHECKING:
    from pydoll.protocol.bidi.permissions.methods import SetPermissionCommand
    from pydoll.protocol.bidi.permissions.types import PermissionDescriptor


class PermissionsCommands:
    """Command builders for the BiDi permissions module."""

    @staticmethod
    def set_permission(
        descriptor: PermissionDescriptor,
        state: str,
        origin: str,
        user_context: Optional[str] = None,
    ) -> SetPermissionCommand:
        """Generates a command to set a permission state for an origin."""
        params = SetPermissionParameters(
            descriptor=descriptor,
            state=state,
            origin=origin,
        )
        if user_context is not None:
            params['userContext'] = user_context
        return Command(method=PermissionsMethod.SET_PERMISSION, params=params)
