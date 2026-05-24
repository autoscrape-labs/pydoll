from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.web_extension.types import Extension, ExtensionData


class WebExtensionMethod(str, Enum):
    """webExtension module method names."""

    INSTALL = 'webExtension.install'
    UNINSTALL = 'webExtension.uninstall'


class InstallParameters(TypedDict):
    """Parameters for webExtension.install command."""

    extensionData: ExtensionData


class InstallResult(TypedDict):
    """Result for webExtension.install command."""

    extension: Extension


class UninstallParameters(TypedDict):
    """Parameters for webExtension.uninstall command."""

    extension: Extension


InstallCommand = Command[InstallParameters, CommandResponse[InstallResult]]
InstallResponse = CommandResponse[InstallResult]

UninstallCommand = Command[UninstallParameters, CommandResponse[EmptyResult]]
UninstallResponse = CommandResponse[EmptyResult]
