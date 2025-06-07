"""
Tests for StorageCommands class.

This module contains comprehensive tests for all StorageCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.storage_commands import StorageCommands
from pydoll.protocol.storage.methods import StorageMethod


def test_clear_cookies_minimal():
    """Test clear_cookies with minimal parameters."""
    result = StorageCommands.clear_cookies()
    assert result['method'] == StorageMethod.CLEAR_COOKIES
    assert result['params'] == {}


def test_clear_cookies_with_context():
    """Test clear_cookies with browser context ID."""
    result = StorageCommands.clear_cookies(browser_context_id='context123')
    assert result['method'] == StorageMethod.CLEAR_COOKIES
    assert result['params']['browserContextId'] == 'context123'


def test_clear_data_for_origin():
    """Test clear_data_for_origin method."""
    result = StorageCommands.clear_data_for_origin(
        origin='https://example.com',
        storage_types='cookies,local_storage'
    )
    assert result['method'] == StorageMethod.CLEAR_DATA_FOR_ORIGIN
    assert result['params']['origin'] == 'https://example.com'
    assert result['params']['storageTypes'] == 'cookies,local_storage'


def test_clear_data_for_storage_key():
    """Test clear_data_for_storage_key method."""
    result = StorageCommands.clear_data_for_storage_key(
        storage_key='storage_key_123',
        storage_types='indexeddb,cache_storage'
    )
    assert result['method'] == StorageMethod.CLEAR_DATA_FOR_STORAGE_KEY
    assert result['params']['storageKey'] == 'storage_key_123'
    assert result['params']['storageTypes'] == 'indexeddb,cache_storage'


def test_get_cookies_minimal():
    """Test get_cookies with minimal parameters."""
    result = StorageCommands.get_cookies()
    assert result['method'] == StorageMethod.GET_COOKIES
    assert result['params'] == {}


def test_get_cookies_with_context():
    """Test get_cookies with browser context ID."""
    result = StorageCommands.get_cookies(browser_context_id='context456')
    assert result['method'] == StorageMethod.GET_COOKIES
    assert result['params']['browserContextId'] == 'context456'


def test_get_storage_key_for_frame():
    """Test get_storage_key_for_frame method."""
    result = StorageCommands.get_storage_key_for_frame(frame_id='frame123')
    assert result['method'] == StorageMethod.GET_STORAGE_KEY_FOR_FRAME
    assert result['params']['frameId'] == 'frame123'


def test_get_usage_and_quota():
    """Test get_usage_and_quota method."""
    result = StorageCommands.get_usage_and_quota(origin='https://example.com')
    assert result['method'] == StorageMethod.GET_USAGE_AND_QUOTA
    assert result['params']['origin'] == 'https://example.com'


def test_set_cookies_minimal():
    """Test set_cookies with minimal parameters."""
    cookies = [
        {'name': 'cookie1', 'value': 'value1', 'domain': 'example.com'},
        {'name': 'cookie2', 'value': 'value2', 'domain': 'example.com'}
    ]
    result = StorageCommands.set_cookies(cookies=cookies)
    assert result['method'] == StorageMethod.SET_COOKIES
    assert result['params']['cookies'] == cookies


def test_set_cookies_with_context():
    """Test set_cookies with browser context ID."""
    cookies = [{'name': 'test', 'value': 'value', 'domain': 'test.com'}]
    result = StorageCommands.set_cookies(
        cookies=cookies,
        browser_context_id='context789'
    )
    assert result['method'] == StorageMethod.SET_COOKIES
    assert result['params']['cookies'] == cookies
    assert result['params']['browserContextId'] == 'context789'


def test_set_protected_audience_k_anonymity():
    """Test set_protected_audience_k_anonymity method."""
    hashes = ['hash1', 'hash2', 'hash3']
    result = StorageCommands.set_protected_audience_k_anonymity(
        owner='https://example.com',
        name='test_group',
        hashes=hashes
    )
    assert result['method'] == StorageMethod.SET_PROTECTED_AUDIENCE_K_ANONYMITY
    assert result['params']['owner'] == 'https://example.com'
    assert result['params']['name'] == 'test_group'
    assert result['params']['hashes'] == hashes


def test_track_cache_storage_for_origin():
    """Test track_cache_storage_for_origin method."""
    result = StorageCommands.track_cache_storage_for_origin(origin='https://example.com')
    assert result['method'] == StorageMethod.TRACK_CACHE_STORAGE_FOR_ORIGIN
    assert result['params']['origin'] == 'https://example.com'


def test_track_cache_storage_for_storage_key():
    """Test track_cache_storage_for_storage_key method."""
    result = StorageCommands.track_cache_storage_for_storage_key(storage_key='key123')
    assert result['method'] == StorageMethod.TRACK_CACHE_STORAGE_FOR_STORAGE_KEY
    assert result['params']['storageKey'] == 'key123'


def test_track_indexed_db_for_origin():
    """Test track_indexed_db_for_origin method."""
    result = StorageCommands.track_indexed_db_for_origin(origin='https://test.com')
    assert result['method'] == StorageMethod.TRACK_INDEXED_DB_FOR_ORIGIN
    assert result['params']['origin'] == 'https://test.com'


def test_track_indexed_db_for_storage_key():
    """Test track_indexed_db_for_storage_key method."""
    result = StorageCommands.track_indexed_db_for_storage_key(storage_key='key456')
    assert result['method'] == StorageMethod.TRACK_INDEXED_DB_FOR_STORAGE_KEY
    assert result['params']['storageKey'] == 'key456'


def test_untrack_cache_storage_for_origin():
    """Test untrack_cache_storage_for_origin method."""
    result = StorageCommands.untrack_cache_storage_for_origin(origin='https://example.org')
    assert result['method'] == StorageMethod.UNTRACK_CACHE_STORAGE_FOR_ORIGIN
    assert result['params']['origin'] == 'https://example.org'


def test_untrack_cache_storage_for_storage_key():
    """Test untrack_cache_storage_for_storage_key method."""
    result = StorageCommands.untrack_cache_storage_for_storage_key(storage_key='key789')
    assert result['method'] == StorageMethod.UNTRACK_CACHE_STORAGE_FOR_STORAGE_KEY
    assert result['params']['storageKey'] == 'key789'


def test_untrack_indexed_db_for_origin():
    """Test untrack_indexed_db_for_origin method."""
    result = StorageCommands.untrack_indexed_db_for_origin(origin='https://test.org')
    assert result['method'] == StorageMethod.UNTRACK_INDEXED_DB_FOR_ORIGIN
    assert result['params']['origin'] == 'https://test.org'


def test_untrack_indexed_db_for_storage_key():
    """Test untrack_indexed_db_for_storage_key method."""
    result = StorageCommands.untrack_indexed_db_for_storage_key(storage_key='key000')
    assert result['method'] == StorageMethod.UNTRACK_INDEXED_DB_FOR_STORAGE_KEY
    assert result['params']['storageKey'] == 'key000'


def test_clear_shared_storage_entries():
    """Test clear_shared_storage_entries method."""
    result = StorageCommands.clear_shared_storage_entries(owner_origin='https://owner.com')
    assert result['method'] == StorageMethod.CLEAR_SHARED_STORAGE_ENTRIES
    assert result['params']['ownerOrigin'] == 'https://owner.com'


def test_clear_trust_tokens():
    """Test clear_trust_tokens method."""
    result = StorageCommands.clear_trust_tokens(issuer_origin='https://issuer.com')
    assert result['method'] == StorageMethod.CLEAR_TRUST_TOKENS
    assert result['params']['issuerOrigin'] == 'https://issuer.com'


def test_delete_shared_storage_entry():
    """Test delete_shared_storage_entry method."""
    result = StorageCommands.delete_shared_storage_entry(
        owner_origin='https://owner.com',
        key='test_key'
    )
    assert result['method'] == StorageMethod.DELETE_SHARED_STORAGE_ENTRY
    assert result['params']['ownerOrigin'] == 'https://owner.com'
    assert result['params']['key'] == 'test_key'


def test_delete_storage_bucket():
    """Test delete_storage_bucket method."""
    bucket = {
        'storageKey': 'key123',
        'name': 'test_bucket'
    }
    result = StorageCommands.delete_storage_bucket(bucket=bucket)
    assert result['method'] == StorageMethod.DELETE_STORAGE_BUCKET
    assert result['params']['bucket'] == bucket


def test_get_affected_urls_for_third_party_cookie_metadata():
    """Test get_affected_urls_for_third_party_cookie_metadata method."""
    third_party_urls = ['https://third1.com', 'https://third2.com']
    result = StorageCommands.get_affected_urls_for_third_party_cookie_metadata(
        first_party_url='https://first.com',
        third_party_urls=third_party_urls
    )
    assert result['method'] == StorageMethod.GET_AFFECTED_URLS_FOR_THIRD_PARTY_COOKIE_METADATA
    assert result['params']['firstPartyUrl'] == 'https://first.com'
    assert result['params']['thirdPartyUrls'] == third_party_urls


def test_get_interest_group_details():
    """Test get_interest_group_details method."""
    result = StorageCommands.get_interest_group_details(
        owner_origin='https://owner.com',
        name='interest_group_1'
    )
    assert result['method'] == StorageMethod.GET_INTEREST_GROUP_DETAILS
    assert result['params']['ownerOrigin'] == 'https://owner.com'
    assert result['params']['name'] == 'interest_group_1'


def test_get_related_website_sets():
    """Test get_related_website_sets method."""
    sets = [
        {
            'primarySites': ['https://primary.com'],
            'associatedSites': ['https://associated.com']
        }
    ]
    result = StorageCommands.get_related_website_sets(sets=sets)
    assert result['method'] == StorageMethod.GET_RELATED_WEBSITE_SETS
    assert result['params']['sets'] == sets


def test_get_shared_storage_entries():
    """Test get_shared_storage_entries method."""
    result = StorageCommands.get_shared_storage_entries(owner_origin='https://shared.com')
    assert result['method'] == StorageMethod.GET_SHARED_STORAGE_ENTRIES
    assert result['params']['ownerOrigin'] == 'https://shared.com'


def test_get_shared_storage_metadata():
    """Test get_shared_storage_metadata method."""
    result = StorageCommands.get_shared_storage_metadata(owner_origin='https://metadata.com')
    assert result['method'] == StorageMethod.GET_SHARED_STORAGE_METADATA
    assert result['params']['ownerOrigin'] == 'https://metadata.com'


def test_get_trust_tokens():
    """Test get_trust_tokens method."""
    result = StorageCommands.get_trust_tokens()
    assert result['method'] == StorageMethod.GET_TRUST_TOKENS
    assert result['params'] == {}


def test_override_quota_for_origin_minimal():
    """Test override_quota_for_origin with minimal parameters."""
    result = StorageCommands.override_quota_for_origin(origin='https://quota.com')
    assert result['method'] == StorageMethod.OVERRIDE_QUOTA_FOR_ORIGIN
    assert result['params']['origin'] == 'https://quota.com'


def test_override_quota_for_origin_with_size():
    """Test override_quota_for_origin with quota size."""
    result = StorageCommands.override_quota_for_origin(
        origin='https://quota.com',
        quota_size=1024000.0
    )
    assert result['method'] == StorageMethod.OVERRIDE_QUOTA_FOR_ORIGIN
    assert result['params']['origin'] == 'https://quota.com'
    assert result['params']['quotaSize'] == 1024000.0


def test_reset_shared_storage_budget():
    """Test reset_shared_storage_budget method."""
    result = StorageCommands.reset_shared_storage_budget(owner_origin='https://budget.com')
    assert result['method'] == StorageMethod.RESET_SHARED_STORAGE_BUDGET
    assert result['params']['ownerOrigin'] == 'https://budget.com'


def test_run_bounce_tracking_mitigations():
    """Test run_bounce_tracking_mitigations method."""
    result = StorageCommands.run_bounce_tracking_mitigations()
    assert result['method'] == StorageMethod.RUN_BOUNCE_TRACKING_MITIGATIONS
    assert result['params'] == {}


def test_send_pending_attribution_reports():
    """Test send_pending_attribution_reports method."""
    result = StorageCommands.send_pending_attribution_reports()
    assert result['method'] == StorageMethod.SEND_PENDING_ATTRIBUTION_REPORTS
    assert result['params'] == {}


def test_set_attribution_reporting_local_testing_mode():
    """Test set_attribution_reporting_local_testing_mode method."""
    result = StorageCommands.set_attribution_reporting_local_testing_mode(enable=True)
    assert result['method'] == StorageMethod.SET_ATTRIBUTION_REPORTING_LOCAL_TESTING_MODE
    assert result['params']['enable'] is True


def test_set_attribution_reporting_tracking():
    """Test set_attribution_reporting_tracking method."""
    result = StorageCommands.set_attribution_reporting_tracking(enable=False)
    assert result['method'] == StorageMethod.SET_ATTRIBUTION_REPORTING_TRACKING
    assert result['params']['enable'] is False


def test_set_interest_group_auction_tracking():
    """Test set_interest_group_auction_tracking method."""
    result = StorageCommands.set_interest_group_auction_tracking(enable=True)
    assert result['method'] == StorageMethod.SET_INTEREST_GROUP_AUCTION_TRACKING
    assert result['params']['enable'] is True


def test_set_interest_group_tracking():
    """Test set_interest_group_tracking method."""
    result = StorageCommands.set_interest_group_tracking(enable=False)
    assert result['method'] == StorageMethod.SET_INTEREST_GROUP_TRACKING
    assert result['params']['enable'] is False


def test_set_shared_storage_entry_minimal():
    """Test set_shared_storage_entry with minimal parameters."""
    result = StorageCommands.set_shared_storage_entry(
        owner_origin='https://storage.com',
        key='test_key',
        value='test_value'
    )
    assert result['method'] == StorageMethod.SET_SHARED_STORAGE_ENTRY
    assert result['params']['ownerOrigin'] == 'https://storage.com'
    assert result['params']['key'] == 'test_key'
    assert result['params']['value'] == 'test_value'


def test_set_shared_storage_entry_with_ignore():
    """Test set_shared_storage_entry with ignore_if_present parameter."""
    result = StorageCommands.set_shared_storage_entry(
        owner_origin='https://storage.com',
        key='test_key',
        value='test_value',
        ignore_if_present=True
    )
    assert result['method'] == StorageMethod.SET_SHARED_STORAGE_ENTRY
    assert result['params']['ownerOrigin'] == 'https://storage.com'
    assert result['params']['key'] == 'test_key'
    assert result['params']['value'] == 'test_value'
    assert result['params']['ignoreIfPresent'] is True


def test_set_shared_storage_tracking():
    """Test set_shared_storage_tracking method."""
    result = StorageCommands.set_shared_storage_tracking(enable=True)
    assert result['method'] == StorageMethod.SET_SHARED_STORAGE_TRACKING
    assert result['params']['enable'] is True


def test_set_storage_bucket_tracking():
    """Test set_storage_bucket_tracking method."""
    result = StorageCommands.set_storage_bucket_tracking(
        storage_key='bucket_key_123',
        enable=False
    )
    assert result['method'] == StorageMethod.SET_STORAGE_BUCKET_TRACKING
    assert result['params']['storageKey'] == 'bucket_key_123'
    assert result['params']['enable'] is False


def test_clear_data_for_origin_all_types():
    """Test clear_data_for_origin with all storage types."""
    result = StorageCommands.clear_data_for_origin(
        origin='https://example.com',
        storage_types='all'
    )
    assert result['method'] == StorageMethod.CLEAR_DATA_FOR_ORIGIN
    assert result['params']['origin'] == 'https://example.com'
    assert result['params']['storageTypes'] == 'all'


def test_set_cookies_complex():
    """Test set_cookies with complex cookie parameters."""
    cookies = [
        {
            'name': 'session_id',
            'value': 'abc123',
            'domain': 'example.com',
            'path': '/',
            'secure': True,
            'httpOnly': True,
            'sameSite': 'Strict'
        }
    ]
    result = StorageCommands.set_cookies(cookies=cookies)
    assert result['method'] == StorageMethod.SET_COOKIES
    assert result['params']['cookies'] == cookies
