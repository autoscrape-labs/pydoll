from pydoll.protocol.browser.events import BrowserEvent
from pydoll.protocol.dom.events import DomEvent
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.input.events import InputEvent
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.runtime.events import RuntimeEvent
from pydoll.protocol.storage.events import StorageEvent
from pydoll.protocol.target.events import TargetEvent


def test_browser_events():
    """Test all BrowserEvent enum values."""
    assert BrowserEvent.DOWNLOAD_PROGRESS == 'Browser.downloadProgress'
    assert BrowserEvent.DOWNLOAD_WILL_BEGIN == 'Browser.downloadWillBegin'


def test_dom_events():
    """Test all DomEvent enum values."""
    assert DomEvent.ATTRIBUTE_MODIFIED == 'DOM.attributeModified'
    assert DomEvent.ATTRIBUTE_REMOVED == 'DOM.attributeRemoved'
    assert DomEvent.CHARACTER_DATA_MODIFIED == 'DOM.characterDataModified'
    assert DomEvent.CHILD_NODE_COUNT_UPDATED == 'DOM.childNodeCountUpdated'
    assert DomEvent.CHILD_NODE_INSERTED == 'DOM.childNodeInserted'
    assert DomEvent.CHILD_NODE_REMOVED == 'DOM.childNodeRemoved'
    assert DomEvent.DOCUMENT_UPDATED == 'DOM.documentUpdated'
    assert DomEvent.SET_CHILD_NODES == 'DOM.setChildNodes'
    assert DomEvent.DISTRIBUTED_NODES_UPDATED == 'DOM.distributedNodesUpdated'
    assert DomEvent.INLINE_STYLE_INVALIDATED == 'DOM.inlineStyleInvalidated'
    assert DomEvent.PSEUDO_ELEMENT_ADDED == 'DOM.pseudoElementAdded'
    assert DomEvent.PSEUDO_ELEMENT_REMOVED == 'DOM.pseudoElementRemoved'
    assert DomEvent.SCROLLABLE_FLAG_UPDATED == 'DOM.scrollableFlagUpdated'
    assert DomEvent.SHADOW_ROOT_POPPED == 'DOM.shadowRootPopped'
    assert DomEvent.SHADOW_ROOT_PUSHED == 'DOM.shadowRootPushed'
    assert DomEvent.TOP_LAYER_ELEMENTS_UPDATED == 'DOM.topLayerElementsUpdated'


def test_fetch_events():
    """Test all FetchEvent enum values."""
    assert FetchEvent.AUTH_REQUIRED == 'Fetch.authRequired'
    assert FetchEvent.REQUEST_PAUSED == 'Fetch.requestPaused'


def test_input_events():
    """Test all InputEvent enum values."""
    assert InputEvent.DRAG_INTERCEPTED == 'Input.dragIntercepted'


def test_network_events():
    """Test all NetworkEvent enum values."""
    assert NetworkEvent.DATA_RECEIVED == 'Network.dataReceived'
    assert NetworkEvent.EVENT_SOURCE_MESSAGE_RECEIVED == 'Network.eventSourceMessageReceived'
    assert NetworkEvent.LOADING_FAILED == 'Network.loadingFailed'
    assert NetworkEvent.LOADING_FINISHED == 'Network.loadingFinished'
    assert NetworkEvent.REQUEST_SERVED_FROM_CACHE == 'Network.requestServedFromCache'
    assert NetworkEvent.REQUEST_WILL_BE_SENT == 'Network.requestWillBeSent'
    assert NetworkEvent.RESPONSE_RECEIVED == 'Network.responseReceived'
    assert NetworkEvent.WEBSOCKET_CLOSED == 'Network.webSocketClosed'
    assert NetworkEvent.WEBSOCKET_CREATED == 'Network.webSocketCreated'
    assert NetworkEvent.WEBSOCKET_FRAME_ERROR == 'Network.webSocketFrameError'
    assert NetworkEvent.WEBSOCKET_FRAME_RECEIVED == 'Network.webSocketFrameReceived'
    assert NetworkEvent.WEBSOCKET_FRAME_SENT == 'Network.webSocketFrameSent'
    assert NetworkEvent.WEBSOCKET_HANDSHAKE_RESPONSE_RECEIVED == 'Network.webSocketHandshakeResponseReceived'
    assert NetworkEvent.WEBSOCKET_WILL_SEND_HANDSHAKE_REQUEST == 'Network.webSocketWillSendHandshakeRequest'
    assert NetworkEvent.WEBTRANSPORT_CLOSED == 'Network.webTransportClosed'
    assert NetworkEvent.WEBTRANSPORT_CONNECTION_ESTABLISHED == 'Network.webTransportConnectionEstablished'
    assert NetworkEvent.WEBTRANSPORT_CREATED == 'Network.webTransportCreated'
    assert NetworkEvent.DIRECT_TCP_SOCKET_ABORTED == 'Network.directTCPSocketAborted'
    assert NetworkEvent.DIRECT_TCP_SOCKET_CHUNK_RECEIVED == 'Network.directTCPSocketChunkReceived'
    assert NetworkEvent.DIRECT_TCP_SOCKET_CHUNK_SENT == 'Network.directTCPSocketChunkSent'
    assert NetworkEvent.DIRECT_TCP_SOCKET_CLOSED == 'Network.directTCPSocketClosed'
    assert NetworkEvent.DIRECT_TCP_SOCKET_CREATED == 'Network.directTCPSocketCreated'
    assert NetworkEvent.DIRECT_TCP_SOCKET_OPENED == 'Network.directTCPSocketOpened'
    assert NetworkEvent.DIRECT_UDP_SOCKET_ABORTED == 'Network.directUDPSocketAborted'
    assert NetworkEvent.DIRECT_UDP_SOCKET_CHUNK_RECEIVED == 'Network.directUDPSocketChunkReceived'
    assert NetworkEvent.DIRECT_UDP_SOCKET_CHUNK_SENT == 'Network.directUDPSocketChunkSent'
    assert NetworkEvent.DIRECT_UDP_SOCKET_CLOSED == 'Network.directUDPSocketClosed'
    assert NetworkEvent.DIRECT_UDP_SOCKET_CREATED == 'Network.directUDPSocketCreated'
    assert NetworkEvent.DIRECT_UDP_SOCKET_OPENED == 'Network.directUDPSocketOpened'
    assert NetworkEvent.POLICY_UPDATED == 'Network.policyUpdated'
    assert NetworkEvent.REPORTING_API_ENDPOINTS_CHANGED_FOR_ORIGIN == 'Network.reportingApiEndpointsChangedForOrigin'
    assert NetworkEvent.REPORTING_API_REPORT_ADDED == 'Network.reportingApiReportAdded'
    assert NetworkEvent.REPORTING_API_REPORT_UPDATED == 'Network.reportingApiReportUpdated'
    assert NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO == 'Network.requestWillBeSentExtraInfo'
    assert NetworkEvent.RESOURCE_CHANGED_PRIORITY == 'Network.resourceChangedPriority'
    assert NetworkEvent.RESPONSE_RECEIVED_EARLY_HINTS == 'Network.responseReceivedEarlyHints'
    assert NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO == 'Network.responseReceivedExtraInfo'
    assert NetworkEvent.SIGNED_EXCHANGE_RECEIVED == 'Network.signedExchangeReceived'
    assert NetworkEvent.SUBRESOURCE_WEB_BUNDLE_INNER_RESPONSE_ERROR == 'Network.subresourceWebBundleInnerResponseError'
    assert NetworkEvent.SUBRESOURCE_WEB_BUNDLE_INNER_RESPONSE_PARSED == 'Network.subresourceWebBundleInnerResponseParsed'
    assert NetworkEvent.SUBRESOURCE_WEB_BUNDLE_METADATA_ERROR == 'Network.subresourceWebBundleMetadataError'
    assert NetworkEvent.SUBRESOURCE_WEB_BUNDLE_METADATA_RECEIVED == 'Network.subresourceWebBundleMetadataReceived'
    assert NetworkEvent.TRUST_TOKEN_OPERATION_DONE == 'Network.trustTokenOperationDone'


def test_page_events():
    """Test all PageEvent enum values."""
    assert PageEvent.DOM_CONTENT_EVENT_FIRED == 'Page.domContentEventFired'
    assert PageEvent.FILE_CHOOSER_OPENED == 'Page.fileChooserOpened'
    assert PageEvent.FRAME_ATTACHED == 'Page.frameAttached'
    assert PageEvent.FRAME_DETACHED == 'Page.frameDetached'
    assert PageEvent.FRAME_NAVIGATED == 'Page.frameNavigated'
    assert PageEvent.INTERSTITIAL_HIDDEN == 'Page.interstitialHidden'
    assert PageEvent.INTERSTITIAL_SHOWN == 'Page.interstitialShown'
    assert PageEvent.JAVASCRIPT_DIALOG_CLOSED == 'Page.javascriptDialogClosed'
    assert PageEvent.JAVASCRIPT_DIALOG_OPENING == 'Page.javascriptDialogOpening'
    assert PageEvent.LIFECYCLE_EVENT == 'Page.lifecycleEvent'
    assert PageEvent.LOAD_EVENT_FIRED == 'Page.loadEventFired'
    assert PageEvent.WINDOW_OPEN == 'Page.windowOpen'
    assert PageEvent.BACK_FORWARD_CACHE_NOT_USED == 'Page.backForwardCacheNotUsed'
    assert PageEvent.COMPILATION_CACHE_PRODUCED == 'Page.compilationCacheProduced'
    assert PageEvent.DOCUMENT_OPENED == 'Page.documentOpened'
    assert PageEvent.FRAME_REQUESTED_NAVIGATION == 'Page.frameRequestedNavigation'
    assert PageEvent.FRAME_RESIZED == 'Page.frameResized'
    assert PageEvent.FRAME_STARTED_LOADING == 'Page.frameStartedLoading'
    assert PageEvent.FRAME_STARTED_NAVIGATING == 'Page.frameStartedNavigating'
    assert PageEvent.FRAME_STOPPED_LOADING == 'Page.frameStoppedLoading'
    assert PageEvent.FRAME_SUBTREE_WILL_BE_DETACHED == 'Page.frameSubtreeWillBeDetached'
    assert PageEvent.NAVIGATED_WITHIN_DOCUMENT == 'Page.navigatedWithinDocument'
    assert PageEvent.SCREENCAST_FRAME == 'Page.screencastFrame'
    assert PageEvent.SCREENCAST_VISIBILITY_CHANGED == 'Page.screencastVisibilityChanged'


def test_runtime_events():
    """Test all RuntimeEvent enum values."""
    assert RuntimeEvent.CONSOLE_API_CALLED == 'Runtime.consoleAPICalled'
    assert RuntimeEvent.EXCEPTION_REVOKED == 'Runtime.exceptionRevoked'
    assert RuntimeEvent.EXCEPTION_THROWN == 'Runtime.exceptionThrown'
    assert RuntimeEvent.EXECUTION_CONTEXT_CREATED == 'Runtime.executionContextCreated'
    assert RuntimeEvent.EXECUTION_CONTEXT_DESTROYED == 'Runtime.executionContextDestroyed'
    assert RuntimeEvent.EXECUTION_CONTEXTS_CLEARED == 'Runtime.executionContextsCleared'
    assert RuntimeEvent.INSPECT_REQUESTED == 'Runtime.inspectRequested'
    assert RuntimeEvent.BINDING_CALLED == 'Runtime.bindingCalled'


def test_storage_events():
    """Test all StorageEvent enum values."""
    assert StorageEvent.CACHE_STORAGE_CONTENT_UPDATED == 'Storage.cacheStorageContentUpdated'
    assert StorageEvent.CACHE_STORAGE_LIST_UPDATED == 'Storage.cacheStorageListUpdated'
    assert StorageEvent.INDEXED_DB_CONTENT_UPDATED == 'Storage.indexedDBContentUpdated'
    assert StorageEvent.INDEXED_DB_LIST_UPDATED == 'Storage.indexedDBListUpdated'
    assert StorageEvent.INTEREST_GROUP_ACCESSED == 'Storage.interestGroupAccessed'
    assert StorageEvent.INTEREST_GROUP_AUCTION_EVENT_OCCURRED == 'Storage.interestGroupAuctionEventOccurred'
    assert StorageEvent.INTEREST_GROUP_AUCTION_NETWORK_REQUEST_CREATED == 'Storage.interestGroupAuctionNetworkRequestCreated'
    assert StorageEvent.SHARED_STORAGE_ACCESSED == 'Storage.sharedStorageAccessed'
    assert StorageEvent.SHARED_STORAGE_WORKLET_OPERATION_EXECUTION_FINISHED == 'Storage.sharedStorageWorkletOperationExecutionFinished'
    assert StorageEvent.STORAGE_BUCKET_CREATED_OR_UPDATED == 'Storage.storageBucketCreatedOrUpdated'
    assert StorageEvent.STORAGE_BUCKET_DELETED == 'Storage.storageBucketDeleted'
    assert StorageEvent.ATTRIBUTION_REPORTING_REPORT_SENT == 'Storage.attributionReportingReportSent'
    assert StorageEvent.ATTRIBUTION_REPORTING_SOURCE_REGISTERED == 'Storage.attributionReportingSourceRegistered'
    assert StorageEvent.ATTRIBUTION_REPORTING_TRIGGER_REGISTERED == 'Storage.attributionReportingTriggerRegistered'


def test_target_events():
    """Test all TargetEvent enum values."""
    assert TargetEvent.RECEIVED_MESSAGE_FROM_TARGET == 'Target.receivedMessageFromTarget'
    assert TargetEvent.TARGET_CRASHED == 'Target.targetCrashed'
    assert TargetEvent.TARGET_CREATED == 'Target.targetCreated'
    assert TargetEvent.TARGET_DESTROYED == 'Target.targetDestroyed'
    assert TargetEvent.TARGET_INFO_CHANGED == 'Target.targetInfoChanged'
    assert TargetEvent.ATTACHED_TO_TARGET == 'Target.attachedToTarget'
    assert TargetEvent.DETACHED_FROM_TARGET == 'Target.detachedFromTarget'


def test_event_enums_integrity():
    """Test that all event enums are properly structured and have no duplicates."""
    # Test that all enums inherit from str and Enum
    event_classes = [
        BrowserEvent, DomEvent, FetchEvent, InputEvent, NetworkEvent,
        PageEvent, RuntimeEvent, StorageEvent, TargetEvent
    ]
    
    # Map class names to their correct domain prefixes
    domain_mapping = {
        'BrowserEvent': 'Browser',
        'DomEvent': 'DOM',
        'FetchEvent': 'Fetch',
        'InputEvent': 'Input',
        'NetworkEvent': 'Network',
        'PageEvent': 'Page',
        'RuntimeEvent': 'Runtime',
        'StorageEvent': 'Storage',
        'TargetEvent': 'Target'
    }
    
    for event_class in event_classes:
        # Check that all values are strings
        for event in event_class:
            assert isinstance(event.value, str), f"{event_class.__name__}.{event.name} should be a string"
            
        # Check that all values start with the correct domain prefix
        domain_name = domain_mapping[event_class.__name__]
        for event in event_class:
            assert event.value.startswith(f'{domain_name}.'), \
                f"{event_class.__name__}.{event.name} should start with '{domain_name}.'"


def test_no_duplicate_events():
    """Test that there are no duplicate event values across all enums."""
    all_events = []

    event_classes = [
        BrowserEvent, DomEvent, FetchEvent, InputEvent, NetworkEvent,
        PageEvent, RuntimeEvent, StorageEvent, TargetEvent
    ]

    for event_class in event_classes:
        for event in event_class:
            all_events.append(event.value)

    assert len(all_events) == len(set(all_events)), "Found duplicate event values"


def test_event_enum_completeness():
    """Test that each event enum has at least one event defined."""
    event_classes = [
        BrowserEvent, DomEvent, FetchEvent, InputEvent, NetworkEvent,
        PageEvent, RuntimeEvent, StorageEvent, TargetEvent
    ]
    
    for event_class in event_classes:
        assert len(list(event_class)) > 0, f"{event_class.__name__} should have at least one event"


def test_event_naming_convention():
    """Test that all event names follow the correct naming convention."""
    event_classes = [
        BrowserEvent, DomEvent, FetchEvent, InputEvent, NetworkEvent,
        PageEvent, RuntimeEvent, StorageEvent, TargetEvent
    ]

    for event_class in event_classes:
        for event in event_class:
            # Event names should be UPPER_CASE
            assert event.name.isupper(), f"{event_class.__name__}.{event.name} should be uppercase"
            # Event names should not contain lowercase letters
            assert not any(c.islower() for c in event.name), \
                f"{event_class.__name__}.{event.name} should not contain lowercase letters"

