from enum import Enum


class Event(str, Enum):
    """Protocol-agnostic browser events.

    Used with browser.on() and tab.on(). Each browser implementation
    maps these to the corresponding native protocol event.
    """

    PAGE_LOADED = 'page.loaded'
    DOM_CONTENT_LOADED = 'page.domContentLoaded'
    FRAME_NAVIGATED = 'page.frameNavigated'
    FRAME_ATTACHED = 'page.frameAttached'
    FRAME_DETACHED = 'page.frameDetached'

    NAVIGATION_STARTED = 'navigation.started'
    NAVIGATION_COMMITTED = 'navigation.committed'
    NAVIGATION_ABORTED = 'navigation.aborted'
    NAVIGATION_FAILED = 'navigation.failed'

    REQUEST_SENT = 'network.requestSent'
    RESPONSE_RECEIVED = 'network.responseReceived'
    RESPONSE_COMPLETED = 'network.responseCompleted'
    FETCH_ERROR = 'network.fetchError'

    DIALOG_OPENED = 'dialog.opened'
    DIALOG_CLOSED = 'dialog.closed'

    DOWNLOAD_STARTED = 'download.started'
    DOWNLOAD_PROGRESS = 'download.progress'
    DOWNLOAD_COMPLETED = 'download.completed'

    FILE_CHOOSER_OPENED = 'fileChooser.opened'

    CONTEXT_CREATED = 'context.created'
    CONTEXT_DESTROYED = 'context.destroyed'

    CONSOLE_MESSAGE = 'console.message'
    EXCEPTION_THROWN = 'runtime.exceptionThrown'

    LOG_ENTRY_ADDED = 'log.entryAdded'


CDP_EVENT_MAP: dict[Event, str] = {
    Event.PAGE_LOADED: 'Page.loadEventFired',
    Event.DOM_CONTENT_LOADED: 'Page.domContentEventFired',
    Event.FRAME_NAVIGATED: 'Page.frameNavigated',
    Event.FRAME_ATTACHED: 'Page.frameAttached',
    Event.FRAME_DETACHED: 'Page.frameDetached',
    Event.REQUEST_SENT: 'Network.requestWillBeSent',
    Event.RESPONSE_RECEIVED: 'Network.responseReceived',
    Event.RESPONSE_COMPLETED: 'Network.loadingFinished',
    Event.FETCH_ERROR: 'Network.loadingFailed',
    Event.DIALOG_OPENED: 'Page.javascriptDialogOpening',
    Event.DIALOG_CLOSED: 'Page.javascriptDialogClosed',
    Event.DOWNLOAD_STARTED: 'Browser.downloadWillBegin',
    Event.DOWNLOAD_PROGRESS: 'Browser.downloadProgress',
    Event.FILE_CHOOSER_OPENED: 'Page.fileChooserOpened',
    Event.CONTEXT_CREATED: 'Target.targetCreated',
    Event.CONTEXT_DESTROYED: 'Target.targetDestroyed',
    Event.CONSOLE_MESSAGE: 'Runtime.consoleAPICalled',
    Event.EXCEPTION_THROWN: 'Runtime.exceptionThrown',
}

BIDI_EVENT_MAP: dict[Event, str] = {
    Event.PAGE_LOADED: 'browsingContext.load',
    Event.DOM_CONTENT_LOADED: 'browsingContext.domContentLoaded',
    Event.FRAME_NAVIGATED: 'browsingContext.fragmentNavigated',
    Event.NAVIGATION_STARTED: 'browsingContext.navigationStarted',
    Event.NAVIGATION_COMMITTED: 'browsingContext.navigationCommitted',
    Event.NAVIGATION_ABORTED: 'browsingContext.navigationAborted',
    Event.NAVIGATION_FAILED: 'browsingContext.navigationFailed',
    Event.REQUEST_SENT: 'network.beforeRequestSent',
    Event.RESPONSE_RECEIVED: 'network.responseStarted',
    Event.RESPONSE_COMPLETED: 'network.responseCompleted',
    Event.FETCH_ERROR: 'network.fetchError',
    Event.DIALOG_OPENED: 'browsingContext.userPromptOpened',
    Event.DIALOG_CLOSED: 'browsingContext.userPromptClosed',
    Event.DOWNLOAD_STARTED: 'browsingContext.downloadWillBegin',
    Event.DOWNLOAD_COMPLETED: 'browsingContext.downloadEnd',
    Event.FILE_CHOOSER_OPENED: 'input.fileDialogOpened',
    Event.CONTEXT_CREATED: 'browsingContext.contextCreated',
    Event.CONTEXT_DESTROYED: 'browsingContext.contextDestroyed',
    Event.CONSOLE_MESSAGE: 'script.message',
    Event.EXCEPTION_THROWN: 'script.realmDestroyed',
    Event.LOG_ENTRY_ADDED: 'log.entryAdded',
}


CDP_DOMAIN_MAP: dict[str, str] = {
    'Page.': 'page',
    'Network.': 'network',
    'Fetch.': 'fetch',
    'DOM.': 'dom',
    'Runtime.': 'runtime',
    'Browser.': 'browser',
    'Target.': 'target',
}
