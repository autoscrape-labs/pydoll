from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import BiDiEvent
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import BrowsingContext
from pydoll.protocol.bidi.script.types import SharedReference


class InputEvent(str, Enum):
    """Input module event names."""

    FILE_DIALOG_OPENED = 'input.fileDialogOpened'


class FileDialogInfo(TypedDict):
    """Parameters for input.fileDialogOpened event."""

    context: BrowsingContext
    userContext: NotRequired[UserContext]
    element: NotRequired[SharedReference]
    multiple: bool


FileDialogOpenedEvent = BiDiEvent[FileDialogInfo]
