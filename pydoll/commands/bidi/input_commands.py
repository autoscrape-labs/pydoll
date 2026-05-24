from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.input.methods import (
    InputMethod,
    PerformActionsParameters,
    ReleaseActionsParameters,
    SetFilesParameters,
)
from pydoll.protocol.bidi.input.types import SourceActions
from pydoll.protocol.bidi.script.types import SharedReference

if TYPE_CHECKING:
    from pydoll.protocol.bidi.input.methods import (
        PerformActionsCommand,
        ReleaseActionsCommand,
        SetFilesCommand,
    )


class InputCommands:
    """Command builders for the BiDi input module."""

    @staticmethod
    def perform_actions(
        context: str,
        actions: list[SourceActions],
    ) -> PerformActionsCommand:
        """Generates a command to perform input actions."""
        return Command(
            method=InputMethod.PERFORM_ACTIONS,
            params=PerformActionsParameters(context=context, actions=actions),
        )

    @staticmethod
    def release_actions(context: str) -> ReleaseActionsCommand:
        """Generates a command to release all input actions."""
        return Command(
            method=InputMethod.RELEASE_ACTIONS,
            params=ReleaseActionsParameters(context=context),
        )

    @staticmethod
    def set_files(
        context: str,
        element: SharedReference,
        files: list[str],
    ) -> SetFilesCommand:
        """Generates a command to set files on a file input element."""
        return Command(
            method=InputMethod.SET_FILES,
            params=SetFilesParameters(
                context=context, element=element, files=files,
            ),
        )
