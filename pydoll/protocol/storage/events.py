from enum import Enum


class StorageEvent(str, Enum):
    """
    Events from the Storage domain of the Chrome DevTools Protocol.

    This enumeration contains the names of Storage-related events that can be
    received from the Chrome DevTools Protocol. These events provide information
    about changes to various browser storage mechanisms including Cache Storage,
    IndexedDB, Interest Groups, Shared Storage, and Storage Buckets.
    """

    CACHE_STORAGE_CONTENT_UPDATED = 'Storage.cacheStorageContentUpdated'
    """
    A cache's contents have been modified.

    Args:
        origin (str): Origin to update.
        storageKey (str): Storage key to update.
        bucketId (str): Storage bucket to update.
        cacheName (str): Name of cache in origin.
    """

    CACHE_STORAGE_LIST_UPDATED = 'Storage.cacheStorageListUpdated'
    """
    A cache has been added/deleted.

    Args:
        origin (str): Origin to update.
        storageKey (str): Storage key to update.
        bucketId (str): Storage bucket to update.
    """

    INDEXED_DB_CONTENT_UPDATED = 'Storage.indexedDBContentUpdated'
    """
    The origin's IndexedDB object store has been modified.

    Args:
        origin (str): Origin to update.
        storageKey (str): Storage key to update.
        bucketId (str): Storage bucket to update.
        databaseName (str): Database to update.
        objectStoreName (str): ObjectStore to update.
    """

    INDEXED_DB_LIST_UPDATED = 'Storage.indexedDBListUpdated'
    """
    The origin's IndexedDB database list has been modified.

    Args:
        origin (str): Origin to update.
        storageKey (str): Storage key to update.
        bucketId (str): Storage bucket to update.
    """

    INTEREST_GROUP_ACCESSED = 'Storage.interestGroupAccessed'
    """
    One of the interest groups was accessed. Note that these events are global
    to all targets sharing an interest group store.

    Args:
        accessTime (Network.TimeSinceEpoch): Time of the access.
        type (InterestGroupAccessType): Type of access.
        ownerOrigin (str): Owner origin.
        name (str): Name of the interest group.
        componentSellerOrigin (str): For topLevelBid/topLevelAdditionalBid, and when
            appropriate, win and additionalBidWin.
        bid (number): For bid or somethingBid event, if done locally and not on a server.
        bidCurrency (str): Currency of the bid.
        uniqueAuctionId (InterestGroupAuctionId): For non-global events --- links
            to interestGroupAuctionEvent.
    """

    INTEREST_GROUP_AUCTION_EVENT_OCCURRED = 'Storage.interestGroupAuctionEventOccurred'
    """
    An auction involving interest groups is taking place. These events are target-specific.

    Args:
        eventTime (Network.TimeSinceEpoch): Time of the event.
        type (InterestGroupAuctionEventType): Type of auction event.
        uniqueAuctionId (InterestGroupAuctionId): Unique identifier for the auction.
        parentAuctionId (InterestGroupAuctionId): Set for child auctions.
        auctionConfig (object): Set for started and configResolved.
    """

    INTEREST_GROUP_AUCTION_NETWORK_REQUEST_CREATED = (
        'Storage.interestGroupAuctionNetworkRequestCreated'
    )
    """
    Specifies which auctions a particular network fetch may be related to, and in what role.
    Note that it is not ordered with respect to Network.requestWillBeSent (but will happen
    before loadingFinished loadingFailed).

    Args:
        type (InterestGroupAuctionFetchType): Type of fetch.
        requestId (Network.RequestId): Request identifier.
        auctions (array[InterestGroupAuctionId]): This is the set of the auctions using the
            worklet that issued this request. In the case of trusted signals, it's possible
            that only some of them actually care about the keys being queried.
    """

    SHARED_STORAGE_ACCESSED = 'Storage.sharedStorageAccessed'
    """
    Shared storage was accessed by the associated page. The following parameters
    are included in all events.

    Args:
        accessTime (Network.TimeSinceEpoch): Time of the access.
        scope (SharedStorageAccessScope): Enum value indicating the access scope.
        method (SharedStorageAccessMethod): Enum value indicating the Shared Storage API
            method invoked.
        mainFrameId (Page.FrameId): DevTools Frame Token for the primary frame tree's root.
        ownerOrigin (str): Serialization of the origin owning the Shared Storage data.
        ownerSite (str): Serialization of the site owning the Shared Storage data.
        params (SharedStorageAccessParams): The sub-parameters wrapped by params are all
            optional and their presence/absence depends on type.
    """

    SHARED_STORAGE_WORKLET_OPERATION_EXECUTION_FINISHED = (
        'Storage.sharedStorageWorkletOperationExecutionFinished'
    )
    """
    A shared storage run or selectURL operation finished its execution.
    The following parameters are included in all events.

    Args:
        finishedTime (Network.TimeSinceEpoch): Time that the operation finished.
        executionTime (int): Time, in microseconds, from start of shared storage JS API
            call until end of operation execution in the worklet.
        method (SharedStorageAccessMethod): Enum value indicating the Shared Storage API
            method invoked.
        operationId (str): ID of the operation call.
        workletTargetId (Target.TargetID): Hex representation of the DevTools token used
            as the TargetID for the associated shared storage worklet.
        mainFrameId (Page.FrameId): DevTools Frame Token for the primary frame tree's root.
        ownerOrigin (str): Serialization of the origin owning the Shared Storage data.
    """

    STORAGE_BUCKET_CREATED_OR_UPDATED = 'Storage.storageBucketCreatedOrUpdated'
    """
    Fired when a storage bucket is created or updated.

    Args:
        bucketInfo (StorageBucketInfo): Information about the storage bucket.
    """

    STORAGE_BUCKET_DELETED = 'Storage.storageBucketDeleted'
    """
    Fired when a storage bucket is deleted.

    Args:
        bucketId (str): ID of the deleted storage bucket.
    """

    ATTRIBUTION_REPORTING_REPORT_SENT = 'Storage.attributionReportingReportSent'
    """
    Fired when an attribution report is sent.

    Args:
        url (str): URL the report was sent to.
        body (object): Body of the report.
        result (AttributionReportingReportResult): Result of the report sending.
        netError (int): If result is sent, populated with net/HTTP status.
        netErrorName (str): Name of the network error if any.
        httpStatusCode (int): HTTP status code if available.
    """

    ATTRIBUTION_REPORTING_SOURCE_REGISTERED = 'Storage.attributionReportingSourceRegistered'
    """
    Fired when an attribution source is registered.

    Args:
        registration (AttributionReportingSourceRegistration): Registration details.
        result (AttributionReportingSourceRegistrationResult): Result of the registration.
    """

    ATTRIBUTION_REPORTING_TRIGGER_REGISTERED = 'Storage.attributionReportingTriggerRegistered'
    """
    Fired when an attribution trigger is registered.

    Args:
        registration (AttributionReportingTriggerRegistration): Registration details.
        eventLevel (AttributionReportingEventLevelResult): Event level result.
        aggregatable (AttributionReportingAggregatableResult): Aggregatable result.
    """
