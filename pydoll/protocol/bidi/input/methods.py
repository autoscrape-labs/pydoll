from enum import Enum

from typing_extensions import TypedDict

from pydoll.protocol.bidi.base import Command, CommandResponse, EmptyResult
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.input.types import SourceActions
from pydoll.protocol.bidi.script.types import SharedReference


class InputMethod(str, Enum):
    """Input module method names."""

    PERFORM_ACTIONS = 'input.performActions'
    RELEASE_ACTIONS = 'input.releaseActions'
    SET_FILES = 'input.setFiles'


class PerformActionsParameters(TypedDict):
    """Parameters for input.performActions command."""

    context: BrowsingContext
    actions: list[SourceActions]


class ReleaseActionsParameters(TypedDict):
    """Parameters for input.releaseActions command."""

    context: BrowsingContext


class SetFilesParameters(TypedDict):
    """Parameters for input.setFiles command."""

    context: BrowsingContext
    element: SharedReference
    files: list[str]


PerformActionsCommand = Command[PerformActionsParameters, CommandResponse[EmptyResult]]
PerformActionsResponse = CommandResponse[EmptyResult]

ReleaseActionsCommand = Command[ReleaseActionsParameters, CommandResponse[EmptyResult]]
ReleaseActionsResponse = CommandResponse[EmptyResult]

SetFilesCommand = Command[SetFilesParameters, CommandResponse[EmptyResult]]
SetFilesResponse = CommandResponse[EmptyResult]
