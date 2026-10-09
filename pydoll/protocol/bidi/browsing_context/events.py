from enum import Enum

from typing_extensions import NotRequired, TypedDict

from pydoll.protocol.bidi.base import BiDiEvent
from pydoll.protocol.bidi.browser.types import UserContext
from pydoll.protocol.bidi.browsing_context.types import (
    BrowsingContext,
    Info,
    Navigation,
    NavigationInfo,
    UserPromptType,
)
from pydoll.protocol.bidi.session.types import UserPromptHandlerType


class BrowsingContextEvent(str, Enum):
    """browsingContext module event names."""

    CONTEXT_CREATED = 'browsingContext.contextCreated'
    CONTEXT_DESTROYED = 'browsingContext.contextDestroyed'
    NAVIGATION_STARTED = 'browsingContext.navigationStarted'
    FRAGMENT_NAVIGATED = 'browsingContext.fragmentNavigated'
    HISTORY_UPDATED = 'browsingContext.historyUpdated'
    DOM_CONTENT_LOADED = 'browsingContext.domContentLoaded'
    LOAD = 'browsingContext.load'
    DOWNLOAD_WILL_BEGIN = 'browsingContext.downloadWillBegin'
    DOWNLOAD_END = 'browsingContext.downloadEnd'
    NAVIGATION_ABORTED = 'browsingContext.navigationAborted'
    NAVIGATION_COMMITTED = 'browsingContext.navigationCommitted'
    NAVIGATION_FAILED = 'browsingContext.navigationFailed'
    USER_PROMPT_CLOSED = 'browsingContext.userPromptClosed'
    USER_PROMPT_OPENED = 'browsingContext.userPromptOpened'


class HistoryUpdatedParameters(TypedDict):
    """Parameters for browsingContext.historyUpdated event."""

    context: BrowsingContext
    timestamp: int
    url: str
    userContext: NotRequired[UserContext]


class DownloadWillBeginParameters(TypedDict):
    """Parameters for browsingContext.downloadWillBegin event."""

    context: BrowsingContext
    navigation: Navigation | None
    timestamp: int
    url: str
    suggestedFilename: str
    userContext: NotRequired[UserContext]


class DownloadCompleteParameters(TypedDict):
    """Parameters for browsingContext.downloadEnd event (complete)."""

    status: str  # "complete"
    context: BrowsingContext
    navigation: Navigation | None
    timestamp: int
    url: str
    filepath: str | None
    userContext: NotRequired[UserContext]


class DownloadCanceledParameters(TypedDict):
    """Parameters for browsingContext.downloadEnd event (canceled)."""

    status: str  # "canceled"
    context: BrowsingContext
    navigation: Navigation | None
    timestamp: int
    url: str
    userContext: NotRequired[UserContext]


DownloadEndParameters = DownloadCompleteParameters | DownloadCanceledParameters


class UserPromptClosedParameters(TypedDict):
    """Parameters for browsingContext.userPromptClosed event."""

    context: BrowsingContext
    accepted: bool
    type: UserPromptType
    userContext: NotRequired[UserContext]
    userText: NotRequired[str]


class UserPromptOpenedParameters(TypedDict):
    """Parameters for browsingContext.userPromptOpened event."""

    context: BrowsingContext
    handler: UserPromptHandlerType
    message: str
    type: UserPromptType
    userContext: NotRequired[UserContext]
    defaultValue: NotRequired[str]


ContextCreatedEvent = BiDiEvent[Info]
ContextDestroyedEvent = BiDiEvent[Info]
NavigationStartedEvent = BiDiEvent[NavigationInfo]
FragmentNavigatedEvent = BiDiEvent[NavigationInfo]
HistoryUpdatedEvent = BiDiEvent[HistoryUpdatedParameters]
DomContentLoadedEvent = BiDiEvent[NavigationInfo]
LoadEvent = BiDiEvent[NavigationInfo]
DownloadWillBeginEvent = BiDiEvent[DownloadWillBeginParameters]
DownloadEndEvent = BiDiEvent[DownloadEndParameters]
NavigationAbortedEvent = BiDiEvent[NavigationInfo]
NavigationCommittedEvent = BiDiEvent[NavigationInfo]
NavigationFailedEvent = BiDiEvent[NavigationInfo]
UserPromptClosedEvent = BiDiEvent[UserPromptClosedParameters]
UserPromptOpenedEvent = BiDiEvent[UserPromptOpenedParameters]
