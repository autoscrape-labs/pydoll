from enum import Enum


class PageEvent(str, Enum):
    """
    Events from the Page domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Page-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about page lifecycle, frame navigation, JavaScript dialogs, and other
    page-related activities.
    """

    DOM_CONTENT_EVENT_FIRED = 'Page.domContentEventFired'
    """
    Fired when DOMContentLoaded event is fired.

    Args:
        timestamp (Network.MonotonicTime): Timestamp when the event occurred.
    """

    FILE_CHOOSER_OPENED = 'Page.fileChooserOpened'
    """
    Emitted only when page.interceptFileChooser is enabled.

    Args:
        frameId (FrameId): Id of the frame containing input node.
        mode (str): Input mode. Allowed Values: selectSingle, selectMultiple
        backendNodeId (DOM.BackendNodeId): Input node id. Only present for file choosers
            opened via an <input type="file"> element.
    """

    FRAME_ATTACHED = 'Page.frameAttached'
    """
    Fired when frame has been attached to its parent.

    Args:
        frameId (FrameId): Id of the frame that has been attached.
        parentFrameId (FrameId): Parent frame identifier.
        stack (Runtime.StackTrace): JavaScript stack trace of when frame was attached,
            only set if frame initiated from script.
    """

    FRAME_DETACHED = 'Page.frameDetached'
    """
    Fired when frame has been detached from its parent.

    Args:
        frameId (FrameId): Id of the frame that has been detached.
        reason (str): Reason why the frame was detached.
            Allowed Values: remove, swap
    """

    FRAME_NAVIGATED = 'Page.frameNavigated'
    """
    Fired once navigation of the frame has completed. Frame is now associated with the new loader.

    Args:
        frame (Frame): Frame object.
        type (NavigationType): Type of navigation.
    """

    INTERSTITIAL_HIDDEN = 'Page.interstitialHidden'
    """
    Fired when interstitial page was hidden.
    """

    INTERSTITIAL_SHOWN = 'Page.interstitialShown'
    """
    Fired when interstitial page was shown.
    """

    JAVASCRIPT_DIALOG_CLOSED = 'Page.javascriptDialogClosed'
    """
    Fired when a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload)
    has been closed.

    Args:
        frameId (FrameId): Frame id.
        result (bool): Whether dialog was confirmed.
        userInput (str): User input in case of prompt.
    """

    JAVASCRIPT_DIALOG_OPENING = 'Page.javascriptDialogOpening'
    """
    Fired when a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload)
    is about to open.

    Args:
        url (str): Frame url.
        frameId (FrameId): Frame id.
        message (str): Message that will be displayed by the dialog.
        type (DialogType): Dialog type.
        hasBrowserHandler (bool): True if browser is capable showing or acting on the given dialog.
            When browser has no dialog handler for given target, calling alert while Page domain
            is engaged will stall the page execution. Execution can be resumed via calling
            Page.handleJavaScriptDialog.
        defaultPrompt (str): Default dialog prompt.
    """

    LIFECYCLE_EVENT = 'Page.lifecycleEvent'
    """
    Fired for lifecycle events (navigation, load, paint, etc) in the current target
    (including local frames).

    Args:
        frameId (FrameId): Id of the frame.
        loaderId (Network.LoaderId): Loader identifier. Empty string if the request is
            fetched from worker.
        name (str): Lifecycle event name.
        timestamp (Network.MonotonicTime): Timestamp when the event occurred.
    """

    LOAD_EVENT_FIRED = 'Page.loadEventFired'
    """
    Fired when the page load event has fired.

    Args:
        timestamp (Network.MonotonicTime): Timestamp when the event occurred.
    """

    WINDOW_OPEN = 'Page.windowOpen'
    """
    Fired when a new window is going to be opened, via window.open(), link click,
    form submission, etc.

    Args:
        url (str): The URL for the new window.
        windowName (str): Window name.
        windowFeatures (array[str]): An array of enabled window features.
        userGesture (bool): Whether or not it was triggered by user gesture.
    """

    BACK_FORWARD_CACHE_NOT_USED = 'Page.backForwardCacheNotUsed'
    """
    Fired for failed bfcache history navigations if BackForwardCache feature is enabled.
    Do not assume any ordering with the Page.frameNavigated event. This event is fired
    only for main-frame history navigation where the document changes (non-same-document
    navigations), when bfcache navigation fails.

    Args:
        loaderId (Network.LoaderId): The loader id for the associated navigation.
        frameId (FrameId): The frame id of the associated frame.
        notRestoredExplanations (array[BackForwardCacheNotRestoredExplanation]): Array of reasons
            why the page could not be cached. This must not be empty.
        notRestoredExplanationsTree (BackForwardCacheNotRestoredExplanationTree): Tree structure
            of reasons why the page could not be cached for each frame.
    """

    COMPILATION_CACHE_PRODUCED = 'Page.compilationCacheProduced'
    """
    Issued for every compilation cache generated. Is only available if
    Page.setGenerateCompilationCache is enabled.

    Args:
        url (str): The URL of the document whose compilation cache was produced.
        data (str): Base64-encoded data (Encoded as a base64 string when passed over JSON).
    """

    DOCUMENT_OPENED = 'Page.documentOpened'
    """
    Fired when opening document to write to.

    Args:
        frame (Frame): Frame object.
    """

    FRAME_REQUESTED_NAVIGATION = 'Page.frameRequestedNavigation'
    """
    Fired when a renderer-initiated navigation is requested.
    Navigation may still be cancelled after the event is issued.

    Args:
        frameId (FrameId): Id of the frame that is being navigated.
        reason (ClientNavigationReason): The reason for the navigation.
        url (str): The destination URL for the requested navigation.
        disposition (ClientNavigationDisposition): The disposition for the navigation.
    """

    FRAME_RESIZED = 'Page.frameResized'
    """
    Fired when frame has been resized.
    """

    FRAME_STARTED_LOADING = 'Page.frameStartedLoading'
    """
    Fired when frame has started loading.

    Args:
        frameId (FrameId): Id of the frame that has started loading.
    """

    FRAME_STARTED_NAVIGATING = 'Page.frameStartedNavigating'
    """
    Fired when a navigation starts. This event is fired for both renderer-initiated
    and browser-initiated navigations. For renderer-initiated navigations, the event
    is fired after frameRequestedNavigation. Navigation may still be cancelled after
    the event is issued. Multiple events can be fired for a single navigation, for example,
    when a same-document navigation becomes a cross-document navigation (such as in the
    case of a frameset).

    Args:
        frameId (FrameId): ID of the frame that is being navigated.
        url (str): The URL the navigation started with. The final URL can be different.
        loaderId (Network.LoaderId): Loader identifier. Even though it is present in case
            of same-document navigation, the previously committed loaderId would not change
            unless the navigation changes from a same-document to a cross-document navigation.
        navigationType (str): Type of navigation.
            Allowed Values: reload, reloadBypassingCache, restore, restoreWithPost,
            historySameDocument, historyDifferentDocument, sameDocument, differentDocument
    """

    FRAME_STOPPED_LOADING = 'Page.frameStoppedLoading'
    """
    Fired when frame has stopped loading.

    Args:
        frameId (FrameId): Id of the frame that has stopped loading.
    """

    FRAME_SUBTREE_WILL_BE_DETACHED = 'Page.frameSubtreeWillBeDetached'
    """
    Fired before frame subtree is detached. Emitted before any frame of the subtree
    is actually detached.

    Args:
        frameId (FrameId): Id of the frame that is the root of the subtree that will be detached.
    """

    NAVIGATED_WITHIN_DOCUMENT = 'Page.navigatedWithinDocument'
    """
    Fired when same-document navigation happens, e.g. due to history API usage or anchor navigation.

    Args:
        frameId (FrameId): Id of the frame.
        url (str): Frame's new url.
        navigationType (str): Navigation type.
            Allowed Values: fragment, historyApi, other
    """

    SCREENCAST_FRAME = 'Page.screencastFrame'
    """
    Compressed image data requested by the startScreencast.

    Args:
        data (str): Base64-encoded compressed image.
        metadata (ScreencastFrameMetadata): Screencast frame metadata.
        sessionId (int): Frame number.
    """

    SCREENCAST_VISIBILITY_CHANGED = 'Page.screencastVisibilityChanged'
    """
    Fired when the page with currently enabled screencast was shown or hidden.

    Args:
        visible (bool): True if the page is visible.
    """
