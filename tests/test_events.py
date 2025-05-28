from pydoll.protocol.events import (
    BrowserEvents,
    DomEvents,
    FetchEvents,
    NetworkEvents,
    PageEvents,
)


def test_browser_events():
    assert BrowserEvents.DOWNLOAD_PROGRESS == 'Browser.downloadProgress'
    assert BrowserEvents.DOWNLOAD_WILL_BEGIN == 'Browser.downloadWillBegin'


def test_dom_events():
    assert DomEvents.ATTRIBUTE_MODIFIED == 'DOM.attributeModified'
    assert DomEvents.ATTRIBUTE_REMOVED == 'DOM.attributeRemoved'
    assert DomEvents.CHARACTER_DATA_MODIFIED == 'DOM.characterDataModified'
    assert DomEvents.CHILD_NODE_COUNT_UPDATED == 'DOM.childNodeCountUpdated'
    assert DomEvents.CHILD_NODE_INSERTED == 'DOM.childNodeInserted'
    assert DomEvents.CHILD_NODE_REMOVED == 'DOM.childNodeRemoved'
    assert DomEvents.DOCUMENT_UPDATED == 'DOM.documentUpdated'
    assert DomEvents.SCROLLABLE_FLAG_UPDATED == 'DOM.scrollableFlagUpdated'
    assert DomEvents.SHADOW_ROOT_POPPED == 'DOM.shadowRootPopped'
    assert DomEvents.SHADOW_ROOT_PUSHED == 'DOM.shadowRootPushed'
    assert (
        DomEvents.TOP_LAYER_ELEMENTS_UPDATED == 'DOM.topLayerElementsUpdated'
    )


def test_fetch_events():
    assert FetchEvents.AUTH_REQUIRED == 'Fetch.authRequired'
    assert FetchEvents.REQUEST_PAUSED == 'Fetch.requestPaused'


def test_network_events():
    assert NetworkEvents.DATA_RECEIVED == 'Network.dataReceived'
    assert NetworkEvents.REQUEST_WILL_BE_SENT == 'Network.requestWillBeSent'
    assert NetworkEvents.RESPONSE_RECEIVED == 'Network.responseReceived'
    assert NetworkEvents.WEB_SOCKET_CLOSED == 'Network.webSocketClosed'
    assert NetworkEvents.WEB_SOCKET_CREATED == 'Network.webSocketCreated'
    assert (
        NetworkEvents.WEB_SOCKET_FRAME_ERROR == 'Network.webSocketFrameError'
    )
    assert (
        NetworkEvents.WEB_SOCKET_FRAME_RECEIVED
        == 'Network.webSocketFrameReceived'
    )
    assert NetworkEvents.WEB_SOCKET_FRAME_SENT == 'Network.webSocketFrameSent'
    assert NetworkEvents.WEB_TRANSPORT_CLOSED == 'Network.webTransportClosed'
    assert NetworkEvents.WEB_TRANSPORT_CONNECTION_ESTABLISHED == (
        'Network.webTransportConnectionEstablished'
    )
    assert NetworkEvents.WEB_TRANSPORT_CREATED == 'Network.webTransportCreated'
    assert NetworkEvents.POLICY_UPDATED == 'Network.policyUpdated'
    assert NetworkEvents.REQUEST_INTERCEPTED == 'Network.requestIntercepted'
    assert (
        NetworkEvents.REQUEST_SERVED_FROM_CACHE
        == 'Network.requestServedFromCache'
    )
    assert NetworkEvents.LOADING_FAILED == 'Network.loadingFailed'
    assert NetworkEvents.LOADING_FINISHED == 'Network.loadingFinished'
    assert (
        NetworkEvents.EVENT_SOURCE_MESSAGE_RECEIVED
        == 'Network.eventSourceMessageReceived'
    )


def test_page_events():
    assert PageEvents.PAGE_LOADED == 'Page.loadEventFired'
    assert PageEvents.DOM_CONTENT_LOADED == 'Page.domContentEventFired'
    assert PageEvents.FRAME_ATTACHED == 'Page.frameAttached'
    assert PageEvents.FRAME_DETACHED == 'Page.frameDetached'
    assert PageEvents.FRAME_NAVIGATED == 'Page.frameNavigated'
    assert PageEvents.FRAME_STARTED_LOADING == 'Page.frameStartedLoading'
    assert PageEvents.FRAME_STOPPED_LOADING == 'Page.frameStoppedLoading'
    assert PageEvents.JS_DIALOG_CLOSED == 'Page.javascriptDialogClosed'
    assert PageEvents.JS_DIALOG_OPENING == 'Page.javascriptDialogOpening'
    assert (
        PageEvents.NAVIGATED_WITHIN_DOCUMENT == 'Page.navigatedWithinDocument'
    )
    assert PageEvents.DOWNLOAD_PROGRESS == 'Page.downloadProgress'
    assert PageEvents.DOWNLOAD_WILL_BEGIN == 'Page.downloadWillBegin'
    assert PageEvents.LIFECYCLE_EVENT == 'Page.lifecycleEvent'
    assert PageEvents.WINDOW_OPENED == 'Page.windowOpen'
    assert PageEvents.DOCUMENT_OPENED == 'Page.documentOpened'
    assert PageEvents.FILE_CHOOSER_OPENED == 'Page.fileChooserOpened'


def test_page_events_all_events():
    assert PageEvents.PAGE_LOADED in PageEvents.ALL_EVENTS
    assert PageEvents.DOM_CONTENT_LOADED in PageEvents.ALL_EVENTS
    assert PageEvents.FILE_CHOOSER_OPENED in PageEvents.ALL_EVENTS
    assert PageEvents.FRAME_ATTACHED in PageEvents.ALL_EVENTS
    assert PageEvents.FRAME_DETACHED in PageEvents.ALL_EVENTS
    assert PageEvents.FRAME_NAVIGATED in PageEvents.ALL_EVENTS
    assert PageEvents.JS_DIALOG_CLOSED in PageEvents.ALL_EVENTS
    assert PageEvents.JS_DIALOG_OPENING in PageEvents.ALL_EVENTS
    assert PageEvents.LIFECYCLE_EVENT in PageEvents.ALL_EVENTS
    assert PageEvents.WINDOW_OPENED in PageEvents.ALL_EVENTS
    assert PageEvents.DOCUMENT_OPENED in PageEvents.ALL_EVENTS
    assert PageEvents.FRAME_STARTED_LOADING in PageEvents.ALL_EVENTS
    assert PageEvents.FRAME_STOPPED_LOADING in PageEvents.ALL_EVENTS
    assert PageEvents.DOWNLOAD_PROGRESS in PageEvents.ALL_EVENTS
    assert PageEvents.DOWNLOAD_WILL_BEGIN in PageEvents.ALL_EVENTS
    assert PageEvents.NAVIGATED_WITHIN_DOCUMENT in PageEvents.ALL_EVENTS
    assert len(PageEvents.ALL_EVENTS) == 16
