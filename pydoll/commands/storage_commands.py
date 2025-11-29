from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.protocol.base import Command
from pydoll.protocol.storage.methods import (
    ClearCookiesParams,
    ClearDataForOriginParams,
    ClearDataForStorageKeyParams,
    ClearSharedStorageEntriesParams,
    ClearTrustTokensParams,
    DeleteSharedStorageEntryParams,
    DeleteStorageBucketParams,
    GetAffectedUrlsForThirdPartyCookieMetadataParams,
    GetCookiesParams,
    GetInterestGroupDetailsParams,
    GetSharedStorageEntriesParams,
    GetSharedStorageMetadataParams,
    GetStorageKeyForFrameParams,
    GetUsageAndQuotaParams,
    OverrideQuotaForOriginParams,
    ResetSharedStorageBudgetParams,
    SetAttributionReportingLocalTestingModeParams,
    SetAttributionReportingTrackingParams,
    SetCookiesParams,
    SetInterestGroupAuctionTrackingParams,
    SetInterestGroupTrackingParams,
    SetProtectedAudienceKAnonymityParams,
    SetSharedStorageEntryParams,
    SetSharedStorageTrackingParams,
    SetStorageBucketTrackingParams,
    StorageMethod,
    TrackCacheStorageForOriginParams,
    TrackCacheStorageForStorageKeyParams,
    TrackIndexedDBForOriginParams,
    TrackIndexedDBForStorageKeyParams,
    UntrackCacheStorageForOriginParams,
    UntrackCacheStorageForStorageKeyParams,
    UntrackIndexedDBForOriginParams,
    UntrackIndexedDBForStorageKeyParams,
)

if TYPE_CHECKING:
    from pydoll.protocol.network.types import CookieParam
    from pydoll.protocol.storage.methods import (
        ClearCookiesCommand,
        ClearDataForOriginCommand,
        ClearDataForStorageKeyCommand,
        ClearSharedStorageEntriesCommand,
        ClearTrustTokensCommand,
        DeleteSharedStorageEntryCommand,
        DeleteStorageBucketCommand,
        GetAffectedUrlsForThirdPartyCookieMetadataCommand,
        GetCookiesCommand,
        GetInterestGroupDetailsCommand,
        GetRelatedWebsiteSetsCommand,
        GetSharedStorageEntriesCommand,
        GetSharedStorageMetadataCommand,
        GetStorageKeyForFrameCommand,
        GetTrustTokensCommand,
        GetUsageAndQuotaCommand,
        OverrideQuotaForOriginCommand,
        ResetSharedStorageBudgetCommand,
        RunBounceTrackingMitigationsCommand,
        SendPendingAttributionReportsCommand,
        SetAttributionReportingLocalTestingModeCommand,
        SetAttributionReportingTrackingCommand,
        SetCookiesCommand,
        SetInterestGroupAuctionTrackingCommand,
        SetInterestGroupTrackingCommand,
        SetProtectedAudienceKAnonymityCommand,
        SetSharedStorageEntryCommand,
        SetSharedStorageTrackingCommand,
        SetStorageBucketTrackingCommand,
        TrackCacheStorageForOriginCommand,
        TrackCacheStorageForStorageKeyCommand,
        TrackIndexedDBForOriginCommand,
        TrackIndexedDBForStorageKeyCommand,
        UntrackCacheStorageForOriginCommand,
        UntrackCacheStorageForStorageKeyCommand,
        UntrackIndexedDBForOriginCommand,
        UntrackIndexedDBForStorageKeyCommand,
    )
    from pydoll.protocol.storage.types import StorageBucket


class StorageCommands:  # noqa: PLR0904
    """
    A class for interacting with browser storage using Chrome DevTools Protocol (CDP).

    The Storage domain of CDP allows managing various types of browser storage, including:
    - Cookies
    - Cache Storage
    - IndexedDB
    - Web Storage (localStorage/sessionStorage)
    - Shared Storage
    - Storage Buckets
    - Trust Tokens
    - Interest Groups
    - Attribution Reporting

    This class provides static methods that generate CDP commands to manage these types
    of storage without the need for traditional webdrivers.
    """

    @staticmethod
    def clear_cookies(browser_context_id: Optional[str] = None) -> ClearCookiesCommand:
        """
        Generates a command to clear all browser cookies.

        Args:
            browser_context_id: Browser context ID (optional). Useful when working
                               with multiple contexts (e.g., multiple windows or tabs).

        Returns:
            ClearCookiesCommand: The CDP command to clear all cookies.
        """
        params = ClearCookiesParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.CLEAR_COOKIES, params=params)

    @staticmethod
    def clear_data_for_origin(origin: str, storage_types: str) -> ClearDataForOriginCommand:
        """
        Generates a command to clear storage data for a specific origin.

        Args:
            origin: The security origin (e.g., "https://example.com").
            storage_types: Comma-separated list of storage types to clear.
                          Possible values include: "cookies", "local_storage", "indexeddb",
                          "cache_storage", etc. Use "all" to clear all types.

        Returns:
            ClearDataForOriginCommand: The CDP command to clear data for the specified origin.
        """
        params = ClearDataForOriginParams(origin=origin, storageTypes=storage_types)
        return Command(method=StorageMethod.CLEAR_DATA_FOR_ORIGIN, params=params)

    @staticmethod
    def clear_data_for_storage_key(
        storage_key: str, storage_types: str
    ) -> ClearDataForStorageKeyCommand:
        """
        Generates a command to clear data for a specific storage key.

        Args:
            storage_key: The storage key for which to clear data.
                        Unlike origin, a storage key is a more specific identifier
                        that may include partition isolation.
            storage_types: Comma-separated list of storage types to clear.
                          Possible values include: "cookies", "local_storage", "indexeddb",
                          "cache_storage", etc. Use "all" to clear all types.

        Returns:
            ClearDataForStorageKeyCommand: The CDP command to clear data for the specified storage
                key.
        """
        params = ClearDataForStorageKeyParams(storageKey=storage_key, storageTypes=storage_types)
        return Command(method=StorageMethod.CLEAR_DATA_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def get_cookies(browser_context_id: Optional[str] = None) -> GetCookiesCommand:
        """
        Generates a command to get all browser cookies.

        Args:
            browser_context_id: Browser context ID (optional). Useful when working
                               with multiple contexts (e.g., multiple windows or tabs).

        Returns:
            GetCookiesCommand: The CDP command to get all cookies, which will return an array
                of Cookie objects.
        """
        params = GetCookiesParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.GET_COOKIES, params=params)

    @staticmethod
    def get_storage_key_for_frame(frame_id: str) -> GetStorageKeyForFrameCommand:
        """
        Generates a command to get the storage key for a specific frame.

        Storage keys are used to isolate data between different origins or
        partitions in the browser.

        Args:
            frame_id: The ID of the frame for which to get the storage key.

        Returns:
            GetStorageKeyForFrameCommand: The CDP command to get the storage key for the specified
                frame.
        """
        params = GetStorageKeyForFrameParams(frameId=frame_id)
        return Command(method=StorageMethod.GET_STORAGE_KEY_FOR_FRAME, params=params)

    @staticmethod
    def get_usage_and_quota(origin: str) -> GetUsageAndQuotaCommand:
        """
        Generates a command to get storage usage and quota information for an origin.

        Useful for monitoring or debugging storage consumption of a site.

        Args:
            origin: The security origin (e.g., "https://example.com") for which to get information.

        Returns:
            GetUsageAndQuotaCommand: The CDP command that will return:
                - usage: Storage usage in bytes
                - quota: Storage quota in bytes
                - usageBreakdown: Breakdown of usage by storage type
                - overrideActive: Whether there is an active quota override
        """
        params = GetUsageAndQuotaParams(origin=origin)
        return Command(method=StorageMethod.GET_USAGE_AND_QUOTA, params=params)

    @staticmethod
    def set_cookies(
        cookies: list[CookieParam], browser_context_id: Optional[str] = None
    ) -> SetCookiesCommand:
        """
        Generates a command to set browser cookies.

        Args:
            cookies: list of Cookie objects to set.
            browser_context_id: Browser context ID (optional). Useful when working
                               with multiple contexts (e.g., multiple windows or tabs).

        Returns:
            SetCookiesCommand: The CDP command to set the specified cookies.
        """
        params = SetCookiesParams(cookies=cookies)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.SET_COOKIES, params=params)

    @staticmethod
    def set_protected_audience_k_anonymity(
        owner: str, name: str, hashes: list[str]
    ) -> SetProtectedAudienceKAnonymityCommand:
        """
        Generates a command to set K-anonymity for protected audience.

        This command is used to configure anonymity in privacy-preserving advertising
        systems (part of Google's Privacy Sandbox).

        Args:
            owner: Owner of the K-anonymity configuration.
            name: Name of the K-anonymity configuration.
            hashes: list of hashes for the configuration.

        Returns:
            SetProtectedAudienceKAnonymityCommand: The CDP command to set protected audience
                K-anonymity.
        """
        params = SetProtectedAudienceKAnonymityParams(owner=owner, name=name, hashes=hashes)
        return Command(method=StorageMethod.SET_PROTECTED_AUDIENCE_K_ANONYMITY, params=params)

    @staticmethod
    def track_cache_storage_for_origin(origin: str) -> TrackCacheStorageForOriginCommand:
        """
        Generates a command to register an origin to receive notifications about changes
        to its Cache Storage.

        Cache Storage is primarily used by Service Workers to store resources for offline use.

        Args:
            origin: The security origin (e.g., "https://example.com") to monitor.

        Returns:
            TrackCacheStorageForOriginCommand: The CDP command to register monitoring of the
                origin's Cache Storage.
        """
        params = TrackCacheStorageForOriginParams(origin=origin)
        return Command(method=StorageMethod.TRACK_CACHE_STORAGE_FOR_ORIGIN, params=params)

    @staticmethod
    def track_cache_storage_for_storage_key(
        storage_key: str,
    ) -> TrackCacheStorageForStorageKeyCommand:
        """
        Generates a command to register a storage key to receive notifications
        about changes to its Cache Storage.

        Similar to track_cache_storage_for_origin, but uses the storage key
        for more precise isolation.

        Args:
            storage_key: The storage key to monitor.

        Returns:
            TrackCacheStorageForStorageKeyCommand: The CDP command to register monitoring of
                the key's Cache Storage.
        """
        params = TrackCacheStorageForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.TRACK_CACHE_STORAGE_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def track_indexed_db_for_origin(origin: str) -> TrackIndexedDBForOriginCommand:
        """
        Generates a command to register an origin to receive notifications about changes
        to its IndexedDB.

        IndexedDB is a NoSQL database system in the browser for storing
        large amounts of structured data.

        Args:
            origin: The security origin (e.g., "https://example.com") to monitor.

        Returns:
            TrackIndexedDBForOriginCommand: The CDP command to register monitoring of
                the origin's IndexedDB.
        """
        params = TrackIndexedDBForOriginParams(origin=origin)
        return Command(method=StorageMethod.TRACK_INDEXED_DB_FOR_ORIGIN, params=params)

    @staticmethod
    def track_indexed_db_for_storage_key(storage_key: str) -> TrackIndexedDBForStorageKeyCommand:
        """
        Generates a command to register a storage key to receive notifications
        about changes to its IndexedDB.

        Similar to track_indexed_db_for_origin, but uses the storage key
        for more precise isolation.

        Args:
            storage_key: The storage key to monitor.

        Returns:
            TrackIndexedDBForStorageKeyCommand: The CDP command to register monitoring of
                the key's IndexedDB.
        """
        params = TrackIndexedDBForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.TRACK_INDEXED_DB_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def untrack_cache_storage_for_origin(origin: str) -> UntrackCacheStorageForOriginCommand:
        """
        Generates a command to unregister an origin from receiving notifications
        about changes to its Cache Storage.

        Use this method to stop monitoring Cache Storage after using track_cache_storage_for_origin.

        Args:
            origin: The security origin (e.g., "https://example.com") to stop monitoring.

        Returns:
            UntrackCacheStorageForOriginCommand: The CDP command to cancel monitoring of the
                origin's Cache Storage.
        """
        params = UntrackCacheStorageForOriginParams(origin=origin)
        return Command(method=StorageMethod.UNTRACK_CACHE_STORAGE_FOR_ORIGIN, params=params)

    @staticmethod
    def untrack_cache_storage_for_storage_key(
        storage_key: str,
    ) -> UntrackCacheStorageForStorageKeyCommand:
        """
        Generates a command to unregister a storage key from receiving notifications
        about changes to its Cache Storage.

        Use this method to stop monitoring Cache Storage after using
        track_cache_storage_for_storage_key.

        Args:
            storage_key: The storage key to stop monitoring.

        Returns:
            UntrackCacheStorageForStorageKeyCommand: The CDP command to cancel monitoring of
                the key's Cache Storage.
        """
        params = UntrackCacheStorageForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.UNTRACK_CACHE_STORAGE_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def untrack_indexed_db_for_origin(origin: str) -> UntrackIndexedDBForOriginCommand:
        """
        Generates a command to unregister an origin from receiving notifications
        about changes to its IndexedDB.

        Use this method to stop monitoring IndexedDB after using track_indexed_db_for_origin.

        Args:
            origin: The security origin (e.g., "https://example.com") to stop monitoring.

        Returns:
            UntrackIndexedDBForOriginCommand: The CDP command to cancel monitoring of
                the origin's IndexedDB.
        """
        params = UntrackIndexedDBForOriginParams(origin=origin)
        return Command(method=StorageMethod.UNTRACK_INDEXED_DB_FOR_ORIGIN, params=params)

    @staticmethod
    def untrack_indexed_db_for_storage_key(
        storage_key: str,
    ) -> UntrackIndexedDBForStorageKeyCommand:
        """
        Generates a command to unregister a storage key from receiving notifications
        about changes to its IndexedDB.

        Use this method to stop monitoring IndexedDB after using track_indexed_db_for_storage_key.

        Args:
            storage_key: The storage key to stop monitoring.

        Returns:
            UntrackIndexedDBForStorageKeyCommand: The CDP command to cancel monitoring
                of the key's IndexedDB.
        """
        params = UntrackIndexedDBForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.UNTRACK_INDEXED_DB_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def clear_shared_storage_entries(owner_origin: str) -> ClearSharedStorageEntriesCommand:
        """
        Generates a command to clear all Shared Storage entries for a specific origin.

        Shared Storage is an experimental API that allows cross-origin shared storage
        with privacy protections.

        Args:
            owner_origin: The owner origin of the Shared Storage to clear.

        Returns:
            ClearSharedStorageEntriesCommand: The CDP command to clear the Shared Storage entries.
        """
        params = ClearSharedStorageEntriesParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.CLEAR_SHARED_STORAGE_ENTRIES, params=params)

    @staticmethod
    def clear_trust_tokens(issuer_origin: str) -> ClearTrustTokensCommand:
        """
        Generates a command to remove all Trust Tokens issued by the specified origin.

        Trust Tokens are an experimental API for combating fraud while preserving user
        privacy. This command keeps other stored data, including the issuer's redemption
        records, intact.

        Args:
            issuer_origin: The issuer origin of the tokens to remove.

        Returns:
            ClearTrustTokensCommand: The CDP command to clear Trust Tokens, which will return:
                - didDeleteTokens: True if any tokens were deleted, False otherwise.
        """
        params = ClearTrustTokensParams(issuerOrigin=issuer_origin)
        return Command(method=StorageMethod.CLEAR_TRUST_TOKENS, params=params)

    @staticmethod
    def delete_shared_storage_entry(owner_origin: str, key: str) -> DeleteSharedStorageEntryCommand:
        """
        Generates a command to delete a specific Shared Storage entry.

        Args:
            owner_origin: The owner origin of the Shared Storage.
            key: The key of the entry to delete.

        Returns:
            DeleteSharedStorageEntryCommand: The CDP command to delete the Shared Storage entry.
        """
        params = DeleteSharedStorageEntryParams(ownerOrigin=owner_origin, key=key)
        return Command(method=StorageMethod.DELETE_SHARED_STORAGE_ENTRY, params=params)

    @staticmethod
    def delete_storage_bucket(bucket: StorageBucket) -> DeleteStorageBucketCommand:
        """
        Generates a command to delete a Storage Bucket with the specified key and name.

        Storage Buckets are an experimental API for managing storage data with
        greater granularity and expiration control.

        Args:
            bucket: A StorageBucket object containing the storageKey and name of the bucket
                to delete.

        Returns:
            DeleteStorageBucketCommand: The CDP command to delete the Storage Bucket.
        """
        params = DeleteStorageBucketParams(bucket=bucket)
        return Command(method=StorageMethod.DELETE_STORAGE_BUCKET, params=params)

    @staticmethod
    def get_affected_urls_for_third_party_cookie_metadata(
        first_party_url: str, third_party_urls: list[str]
    ) -> GetAffectedUrlsForThirdPartyCookieMetadataCommand:
        """
        Generates a command to get the list of URLs from a page and its embedded resources
        that match existing grace period URL pattern rules.

        This command is useful for monitoring which URLs would be affected by the
        Privacy Sandbox's third-party cookie policies.

        Args:
            first_party_url: The URL of the page being visited (first-party).
            third_party_urls: Optional list of embedded third-party resource URLs.

        Returns:
            GetAffectedUrlsForThirdPartyCookieMetadataCommand: The CDP command to get URLs
                affected by third-party cookie metadata.
        """
        params = GetAffectedUrlsForThirdPartyCookieMetadataParams(
            firstPartyUrl=first_party_url, thirdPartyUrls=third_party_urls
        )
        return Command(
            method=StorageMethod.GET_AFFECTED_URLS_FOR_THIRD_PARTY_COOKIE_METADATA, params=params
        )

    @staticmethod
    def get_interest_group_details(owner_origin: str, name: str) -> GetInterestGroupDetailsCommand:
        """
        Generates a command to get details of a specific interest group.

        Interest Groups are part of the FLEDGE/Protected Audience API for privacy-preserving
        advertising, enabling in-browser ad auctions.

        Args:
            owner_origin: The owner origin of the interest group.
            name: The name of the interest group.

        Returns:
            GetInterestGroupDetailsCommand: The CDP command to get interest group details.
        """
        params = GetInterestGroupDetailsParams(ownerOrigin=owner_origin, name=name)
        return Command(method=StorageMethod.GET_INTEREST_GROUP_DETAILS, params=params)

    @staticmethod
    def get_related_website_sets() -> GetRelatedWebsiteSetsCommand:
        """
        Generates a command to get related website sets.

        Related Website Sets are an API that allows sites under the same entity
        to share some data, despite third-party cookie restrictions.

        Returns:
            GetRelatedWebsiteSetsCommand: The CDP command to get related website sets.
        """
        return Command(method=StorageMethod.GET_RELATED_WEBSITE_SETS)

    @staticmethod
    def get_shared_storage_entries(owner_origin: str) -> GetSharedStorageEntriesCommand:
        """
        Generates a command to get all Shared Storage entries for an origin.

        Args:
            owner_origin: The owner origin of the Shared Storage.

        Returns:
            GetSharedStorageEntriesCommand: The CDP command to get the Shared Storage entries.
        """
        params = GetSharedStorageEntriesParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.GET_SHARED_STORAGE_ENTRIES, params=params)

    @staticmethod
    def get_shared_storage_metadata(owner_origin: str) -> GetSharedStorageMetadataCommand:
        """
        Generates a command to get Shared Storage metadata for an origin.

        Metadata includes information such as usage, budget, and creation time.

        Args:
            owner_origin: The owner origin of the Shared Storage.

        Returns:
            GetSharedStorageMetadataCommand: The CDP command to get Shared Storage metadata.
        """
        params = GetSharedStorageMetadataParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.GET_SHARED_STORAGE_METADATA, params=params)

    @staticmethod
    def get_trust_tokens() -> GetTrustTokensCommand:
        """
        Generates a command to get all available Trust Tokens.

        Returns:
            GetTrustTokensCommand: The CDP command to get Trust Tokens, which will return pairs
                    of issuer origin and count of available tokens.
        """
        return Command(method=StorageMethod.GET_TRUST_TOKENS, params={})

    @staticmethod
    def override_quota_for_origin(
        origin: str, quota_size: Optional[float] = None
    ) -> OverrideQuotaForOriginCommand:
        """
        Generates a command to override the storage quota for a specific origin.

        This command is useful for storage exhaustion testing or simulating
        different storage conditions.

        Args:
            origin: The origin for which to override the quota.
            quota_size: The size of the new quota in bytes (optional).
                       If not specified, any existing override will be removed.

        Returns:
            OverrideQuotaForOriginCommand: The CDP command to override the origin's quota.
        """
        params = OverrideQuotaForOriginParams(origin=origin)
        if quota_size is not None:
            params['quotaSize'] = quota_size
        return Command(method=StorageMethod.OVERRIDE_QUOTA_FOR_ORIGIN, params=params)

    @staticmethod
    def reset_shared_storage_budget(owner_origin: str) -> ResetSharedStorageBudgetCommand:
        """
        Generates a command to reset the Shared Storage budget for an origin.

        Shared Storage uses a budget system to limit the amount of operations
        or specific operations to preserve user privacy.

        Args:
            owner_origin: The owner origin of the Shared Storage.

        Returns:
            ResetSharedStorageBudgetCommand: The CDP command to reset the Shared Storage budget.
        """
        params = ResetSharedStorageBudgetParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.RESET_SHARED_STORAGE_BUDGET, params=params)

    @staticmethod
    def run_bounce_tracking_mitigations() -> RunBounceTrackingMitigationsCommand:
        """
        Generates a command to run bounce tracking mitigations.

        Bounce tracking is a tracking technique that involves redirecting users
        through intermediate URLs to establish tracking cookies.
        This command activates protections against this technique.

        Returns:
            RunBounceTrackingMitigationsCommand: The CDP command to run bounce tracking mitigations.
        """
        return Command(method=StorageMethod.RUN_BOUNCE_TRACKING_MITIGATIONS, params={})

    @staticmethod
    def send_pending_attribution_reports() -> SendPendingAttributionReportsCommand:
        """
        Generates a command to send pending attribution reports.

        Attribution Reporting is an API that allows measuring conversions while
        preserving user privacy. This command forces sending reports that
        are waiting to be sent.

        Returns:
            SendPendingAttributionReportsCommand: The CDP command to send pending attribution
                reports.
        """
        return Command(method=StorageMethod.SEND_PENDING_ATTRIBUTION_REPORTS, params={})

    @staticmethod
    def set_attribution_reporting_local_testing_mode(
        enabled: bool,
    ) -> SetAttributionReportingLocalTestingModeCommand:
        """
        Generates a command to enable or disable local testing mode for Attribution Reporting.

        Testing mode makes it easier to develop and test the Attribution Reporting API
        by removing restrictions like delays and rate limits that would normally apply.

        Args:
            enabled: True to enable local testing mode, False to disable it.

        Returns:
            SetAttributionReportingLocalTestingModeCommand: The CDP command to set Attribution
                Reporting local testing mode.
        """
        params = SetAttributionReportingLocalTestingModeParams(enabled=enabled)
        return Command(
            method=StorageMethod.SET_ATTRIBUTION_REPORTING_LOCAL_TESTING_MODE, params=params
        )

    @staticmethod
    def set_attribution_reporting_tracking(enable: bool) -> SetAttributionReportingTrackingCommand:
        """
        Generates a command to enable or disable Attribution Reporting tracking.

        Args:
            enable: True to enable tracking, False to disable it.

        Returns:
            SetAttributionReportingTrackingCommand: The CDP command to set Attribution
                Reporting tracking.
        """
        params = SetAttributionReportingTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_ATTRIBUTION_REPORTING_TRACKING, params=params)

    @staticmethod
    def set_interest_group_auction_tracking(enable: bool) -> SetInterestGroupAuctionTrackingCommand:
        """
        Generates a command to enable or disable interest group auction tracking.

        Interest group auctions are part of the FLEDGE/Protected Audience API and
        allow for in-browser ad auctions in a privacy-preserving way.

        Args:
            enable: True to enable tracking, False to disable it.

        Returns:
            SetInterestGroupAuctionTrackingCommand: The CDP command to set interest group
                auction tracking.
        """
        params = SetInterestGroupAuctionTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_INTEREST_GROUP_AUCTION_TRACKING, params=params)

    @staticmethod
    def set_interest_group_tracking(enable: bool) -> SetInterestGroupTrackingCommand:
        """
        Generates a command to enable or disable interest group tracking.

        Args:
            enable: True to enable tracking, False to disable it.

        Returns:
            SetInterestGroupTrackingCommand: The CDP command to set interest group tracking.
        """
        params = SetInterestGroupTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_INTEREST_GROUP_TRACKING, params=params)

    @staticmethod
    def set_shared_storage_entry(
        owner_origin: str, key: str, value: str, ignore_if_present: Optional[bool] = None
    ) -> SetSharedStorageEntryCommand:
        """
        Generates a command to set an entry in Shared Storage.

        Args:
            owner_origin: The owner origin of the Shared Storage.
            key: The key of the entry to set.
            value: The value of the entry to set.
            ignore_if_present: If True, won't replace an existing entry with the same key.

        Returns:
            SetSharedStorageEntryCommand: The CDP command to set a Shared Storage entry.
        """
        params = SetSharedStorageEntryParams(ownerOrigin=owner_origin, key=key, value=value)
        if ignore_if_present is not None:
            params['ignoreIfPresent'] = ignore_if_present
        return Command(method=StorageMethod.SET_SHARED_STORAGE_ENTRY, params=params)

    @staticmethod
    def set_shared_storage_tracking(enable: bool) -> SetSharedStorageTrackingCommand:
        """
        Generates a command to enable or disable Shared Storage tracking.

        When enabled, events related to Shared Storage usage will be emitted.

        Args:
            enable: True to enable tracking, False to disable it.

        Returns:
            SetSharedStorageTrackingCommand: The CDP command to set Shared Storage tracking.
        """
        params = SetSharedStorageTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_SHARED_STORAGE_TRACKING, params=params)

    @staticmethod
    def set_storage_bucket_tracking(
        storage_key: str, enable: bool
    ) -> SetStorageBucketTrackingCommand:
        """
        Generates a command to enable or disable Storage Bucket tracking.

        When enabled, events related to changes in storage buckets will be emitted.

        Args:
            storage_key: The storage key for which to set tracking.
            enable: True to enable tracking, False to disable it.

        Returns:
            SetStorageBucketTrackingCommand: The CDP command to set Storage Bucket tracking.
        """
        params = SetStorageBucketTrackingParams(storageKey=storage_key, enable=enable)
        return Command(method=StorageMethod.SET_STORAGE_BUCKET_TRACKING, params=params)
