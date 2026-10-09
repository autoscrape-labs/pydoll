from __future__ import annotations

from typing import TYPE_CHECKING

from pydoll.protocol.bidi.base import Command
from pydoll.protocol.bidi.web_extension.methods import (
    InstallParameters,
    UninstallParameters,
    WebExtensionMethod,
)
from pydoll.protocol.bidi.web_extension.types import ExtensionData

if TYPE_CHECKING:
    from pydoll.protocol.bidi.web_extension.methods import (
        InstallCommand,
        UninstallCommand,
    )


class WebExtensionCommands:
    """Command builders for the BiDi webExtension module."""

    @staticmethod
    def install(extension_data: ExtensionData) -> InstallCommand:
        """Generates a command to install a web extension."""
        return Command(
            method=WebExtensionMethod.INSTALL,
            params=InstallParameters(extensionData=extension_data),
        )

    @staticmethod
    def uninstall(extension: str) -> UninstallCommand:
        """Generates a command to uninstall a web extension."""
        return Command(
            method=WebExtensionMethod.UNINSTALL,
            params=UninstallParameters(extension=extension),
        )
