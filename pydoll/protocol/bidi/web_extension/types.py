from typing_extensions import TypedDict

Extension = str
"""Unique identifier for a web extension."""


class ExtensionPath(TypedDict):
    """Extension data from a directory path."""

    type: str  # "path"
    path: str


class ExtensionArchivePath(TypedDict):
    """Extension data from a zip archive path."""

    type: str  # "archivePath"
    path: str


class ExtensionBase64Encoded(TypedDict):
    """Extension data from base64-encoded zip."""

    type: str  # "base64"
    value: str


ExtensionData = ExtensionPath | ExtensionArchivePath | ExtensionBase64Encoded
