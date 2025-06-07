"""
Tests for NetworkCommands class.

This module contains comprehensive tests for all NetworkCommands methods,
verifying that they generate the correct CDP commands with proper parameters.
"""

from pydoll.commands.network_commands import NetworkCommands
from pydoll.constants import (
    ConnectionType,
    ContentEncoding,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
)
from pydoll.protocol.network.methods import NetworkMethod


def test_clear_browser_cache():
    """Test clear_browser_cache method generates correct command."""
    result = NetworkCommands.clear_browser_cache()
    assert result['method'] == NetworkMethod.CLEAR_BROWSER_CACHE
    assert 'params' not in result


def test_clear_browser_cookies():
    """Test clear_browser_cookies method generates correct command."""
    result = NetworkCommands.clear_browser_cookies()
    assert result['method'] == NetworkMethod.CLEAR_BROWSER_COOKIES
    assert 'params' not in result


def test_delete_cookies_minimal():
    """Test delete_cookies with minimal parameters."""
    result = NetworkCommands.delete_cookies(name='test_cookie')
    assert result['method'] == NetworkMethod.DELETE_COOKIES
    assert result['params']['name'] == 'test_cookie'


def test_delete_cookies_with_url():
    """Test delete_cookies with URL parameter."""
    result = NetworkCommands.delete_cookies(
        name='test_cookie',
        url='https://example.com'
    )
    assert result['method'] == NetworkMethod.DELETE_COOKIES
    assert result['params']['name'] == 'test_cookie'
    assert result['params']['url'] == 'https://example.com'


def test_delete_cookies_with_all_params():
    """Test delete_cookies with all parameters."""
    partition_key = {
        'topLevelSite': 'https://example.com',
        'hasCrossSiteAncestor': False
    }
    result = NetworkCommands.delete_cookies(
        name='test_cookie',
        url='https://example.com',
        domain='example.com',
        path='/test',
        partition_key=partition_key
    )
    assert result['method'] == NetworkMethod.DELETE_COOKIES
    assert result['params']['name'] == 'test_cookie'
    assert result['params']['url'] == 'https://example.com'
    assert result['params']['domain'] == 'example.com'
    assert result['params']['path'] == '/test'
    assert result['params']['partitionKey'] == partition_key


def test_disable():
    """Test disable method generates correct command."""
    result = NetworkCommands.disable()
    assert result['method'] == NetworkMethod.DISABLE
    assert 'params' not in result


def test_enable_minimal():
    """Test enable with minimal parameters."""
    result = NetworkCommands.enable()
    assert result['method'] == NetworkMethod.ENABLE
    assert result['params'] == {}


def test_enable_with_buffer_sizes():
    """Test enable with buffer size parameters."""
    result = NetworkCommands.enable(
        max_total_buffer_size=1024000,
        max_resource_buffer_size=512000,
        max_post_data_size=65536
    )
    assert result['method'] == NetworkMethod.ENABLE
    assert result['params']['maxTotalBufferSize'] == 1024000
    assert result['params']['maxResourceBufferSize'] == 512000
    assert result['params']['maxPostDataSize'] == 65536


def test_get_cookies_minimal():
    """Test get_cookies with minimal parameters."""
    result = NetworkCommands.get_cookies()
    assert result['method'] == NetworkMethod.GET_COOKIES
    assert result['params'] == {}


def test_get_cookies_with_urls():
    """Test get_cookies with URLs parameter."""
    urls = ['https://example.com', 'https://test.com']
    result = NetworkCommands.get_cookies(urls=urls)
    assert result['method'] == NetworkMethod.GET_COOKIES
    assert result['params']['urls'] == urls


def test_get_request_post_data():
    """Test get_request_post_data method."""
    result = NetworkCommands.get_request_post_data(request_id='12345')
    assert result['method'] == NetworkMethod.GET_REQUEST_POST_DATA
    assert result['params']['requestId'] == '12345'


def test_get_response_body():
    """Test get_response_body method."""
    result = NetworkCommands.get_response_body(request_id='12345')
    assert result['method'] == NetworkMethod.GET_RESPONSE_BODY
    assert result['params']['requestId'] == '12345'


def test_set_cache_disabled_true():
    """Test set_cache_disabled with cache disabled."""
    result = NetworkCommands.set_cache_disabled(cache_disabled=True)
    assert result['method'] == NetworkMethod.SET_CACHE_DISABLED
    assert result['params']['cacheDisabled'] is True


def test_set_cache_disabled_false():
    """Test set_cache_disabled with cache enabled."""
    result = NetworkCommands.set_cache_disabled(cache_disabled=False)
    assert result['method'] == NetworkMethod.SET_CACHE_DISABLED
    assert result['params']['cacheDisabled'] is False


def test_set_cookie_minimal():
    """Test set_cookie with minimal parameters."""
    result = NetworkCommands.set_cookie(name='test', value='value')
    assert result['method'] == NetworkMethod.SET_COOKIE
    assert result['params']['name'] == 'test'
    assert result['params']['value'] == 'value'


def test_set_cookie_with_url():
    """Test set_cookie with URL parameter."""
    result = NetworkCommands.set_cookie(
        name='test',
        value='value',
        url='https://example.com'
    )
    assert result['method'] == NetworkMethod.SET_COOKIE
    assert result['params']['name'] == 'test'
    assert result['params']['value'] == 'value'
    assert result['params']['url'] == 'https://example.com'


def test_set_cookie_with_all_params():
    """Test set_cookie with all parameters."""
    partition_key = {
        'topLevelSite': 'https://example.com',
        'hasCrossSiteAncestor': False
    }
    result = NetworkCommands.set_cookie(
        name='test',
        value='value',
        url='https://example.com',
        domain='example.com',
        path='/test',
        secure=True,
        http_only=True,
        same_site=CookieSameSite.STRICT,
        expires=1234567890.0,
        priority=CookiePriority.HIGH,
        same_party=True,
        source_scheme=CookieSourceScheme.SECURE,
        source_port=443,
        partition_key=partition_key
    )
    assert result['method'] == NetworkMethod.SET_COOKIE
    assert result['params']['name'] == 'test'
    assert result['params']['value'] == 'value'
    assert result['params']['url'] == 'https://example.com'
    assert result['params']['domain'] == 'example.com'
    assert result['params']['path'] == '/test'
    assert result['params']['secure'] is True
    assert result['params']['httpOnly'] is True
    assert result['params']['sameSite'] == CookieSameSite.STRICT
    assert result['params']['expires'] == 1234567890.0
    assert result['params']['priority'] == CookiePriority.HIGH
    assert result['params']['sameParty'] is True
    assert result['params']['sourceScheme'] == CookieSourceScheme.SECURE
    assert result['params']['sourcePort'] == 443
    assert result['params']['partitionKey'] == partition_key


def test_set_cookies():
    """Test set_cookies method."""
    cookies = [
        {
            'name': 'cookie1',
            'value': 'value1',
            'url': 'https://example.com'
        },
        {
            'name': 'cookie2',
            'value': 'value2',
            'domain': 'example.com'
        }
    ]
    result = NetworkCommands.set_cookies(cookies=cookies)
    assert result['method'] == NetworkMethod.SET_COOKIES
    assert result['params']['cookies'] == cookies


def test_set_extra_http_headers():
    """Test set_extra_http_headers method."""
    headers = [
        {'name': 'Authorization', 'value': 'Bearer token123'},
        {'name': 'X-Custom-Header', 'value': 'custom-value'}
    ]
    result = NetworkCommands.set_extra_http_headers(headers=headers)
    assert result['method'] == NetworkMethod.SET_EXTRA_HTTP_HEADERS
    assert result['params']['headers'] == headers


def test_set_useragent_override_minimal():
    """Test set_useragent_override with minimal parameters."""
    user_agent = 'Mozilla/5.0 (Custom Browser)'
    result = NetworkCommands.set_useragent_override(user_agent=user_agent)
    assert result['method'] == NetworkMethod.SET_USER_AGENT_OVERRIDE
    assert result['params']['userAgent'] == user_agent


def test_set_useragent_override_with_all_params():
    """Test set_useragent_override with all parameters."""
    user_agent = 'Mozilla/5.0 (Custom Browser)'
    accept_language = 'en-US,en;q=0.9'
    platform = 'Linux x86_64'
    user_agent_metadata = {
        'brands': [{'brand': 'Custom', 'version': '1.0'}],
        'fullVersionList': [{'brand': 'Custom', 'version': '1.0.0'}],
        'platform': 'Linux',
        'platformVersion': '5.4.0',
        'architecture': 'x86',
        'model': '',
        'mobile': False,
        'bitness': '64',
        'wow64': False
    }
    result = NetworkCommands.set_useragent_override(
        user_agent=user_agent,
        accept_language=accept_language,
        platform=platform,
        user_agent_metadata=user_agent_metadata
    )
    assert result['method'] == NetworkMethod.SET_USER_AGENT_OVERRIDE
    assert result['params']['userAgent'] == user_agent
    assert result['params']['acceptLanguage'] == accept_language
    assert result['params']['platform'] == platform
    assert result['params']['userAgentMetadata'] == user_agent_metadata


def test_clear_accepted_encodings_override():
    """Test clear_accepted_encodings_override method."""
    result = NetworkCommands.clear_accepted_encodings_override()
    assert result['method'] == NetworkMethod.CLEAR_ACCEPTED_ENCODINGS_OVERRIDE
    assert 'params' not in result


def test_enable_reporting_api():
    """Test enable_reporting_api method."""
    result = NetworkCommands.enable_reporting_api(enabled=True)
    assert result['method'] == NetworkMethod.ENABLE_REPORTING_API
    assert result['params']['enabled'] is True


def test_search_in_response_body_minimal():
    """Test search_in_response_body with minimal parameters."""
    result = NetworkCommands.search_in_response_body(
        request_id='12345',
        query='test'
    )
    assert result['method'] == NetworkMethod.SEARCH_IN_RESPONSE_BODY
    assert result['params']['requestId'] == '12345'
    assert result['params']['query'] == 'test'
    assert result['params']['caseSensitive'] is False
    assert result['params']['isRegex'] is False


def test_search_in_response_body_with_options():
    """Test search_in_response_body with all options."""
    result = NetworkCommands.search_in_response_body(
        request_id='12345',
        query='test.*pattern',
        case_sensitive=True,
        is_regex=True
    )
    assert result['method'] == NetworkMethod.SEARCH_IN_RESPONSE_BODY
    assert result['params']['requestId'] == '12345'
    assert result['params']['query'] == 'test.*pattern'
    assert result['params']['caseSensitive'] is True
    assert result['params']['isRegex'] is True


def test_set_blocked_urls():
    """Test set_blocked_urls method."""
    urls = ['https://ads.example.com', 'https://tracker.com']
    result = NetworkCommands.set_blocked_urls(urls=urls)
    assert result['method'] == NetworkMethod.SET_BLOCKED_URLS
    assert result['params']['urls'] == urls


def test_set_bypass_service_worker():
    """Test set_bypass_service_worker method."""
    result = NetworkCommands.set_bypass_service_worker(bypass=True)
    assert result['method'] == NetworkMethod.SET_BYPASS_SERVICE_WORKER
    assert result['params']['bypass'] is True


def test_get_certificate():
    """Test get_certificate method."""
    result = NetworkCommands.get_certificate(origin='https://example.com')
    assert result['method'] == NetworkMethod.GET_CERTIFICATE
    assert result['params']['origin'] == 'https://example.com'


def test_get_response_body_for_interception():
    """Test get_response_body_for_interception method."""
    result = NetworkCommands.get_response_body_for_interception(
        interception_id='interception123'
    )
    assert result['method'] == NetworkMethod.GET_RESPONSE_BODY_FOR_INTERCEPTION
    assert result['params']['interceptionId'] == 'interception123'


def test_set_accepted_encodings():
    """Test set_accepted_encodings method."""
    encodings = [ContentEncoding.GZIP, ContentEncoding.BR]
    result = NetworkCommands.set_accepted_encodings(encodings=encodings)
    assert result['method'] == NetworkMethod.SET_ACCEPTED_ENCODINGS
    assert result['params']['encodings'] == encodings


def test_set_attach_debug_stack():
    """Test set_attach_debug_stack method."""
    result = NetworkCommands.set_attach_debug_stack(enabled=True)
    assert result['method'] == NetworkMethod.SET_ATTACH_DEBUG_STACK
    assert result['params']['enabled'] is True


def test_set_cookie_controls_minimal():
    """Test set_cookie_controls with minimal parameters."""
    result = NetworkCommands.set_cookie_controls(
        enable_third_party_cookie_restriction=True
    )
    assert result['method'] == NetworkMethod.SET_COOKIE_CONTROLS
    assert result['params']['enableThirdPartyCookieRestriction'] is True


def test_set_cookie_controls_with_all_params():
    """Test set_cookie_controls with all parameters."""
    result = NetworkCommands.set_cookie_controls(
        enable_third_party_cookie_restriction=True,
        disable_third_party_cookie_metadata=False,
        disable_third_party_cookie_heuristics=True
    )
    assert result['method'] == NetworkMethod.SET_COOKIE_CONTROLS
    assert result['params']['enableThirdPartyCookieRestriction'] is True
    assert result['params']['disableThirdPartyCookieMetadata'] is False
    assert result['params']['disableThirdPartyCookieHeuristics'] is True


def test_stream_resource_content():
    """Test stream_resource_content method."""
    result = NetworkCommands.stream_resource_content(request_id='12345')
    assert result['method'] == NetworkMethod.STREAM_RESOURCE_CONTENT
    assert result['params']['requestId'] == '12345'


def test_take_response_body_for_interception_as_stream():
    """Test take_response_body_for_interception_as_stream method."""
    result = NetworkCommands.take_response_body_for_interception_as_stream(
        interception_id='interception123'
    )
    assert result['method'] == NetworkMethod.TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM
    assert result['params']['interceptionId'] == 'interception123'


def test_emulate_network_conditions_minimal():
    """Test emulate_network_conditions with minimal parameters."""
    result = NetworkCommands.emulate_network_conditions(
        offline=False,
        latency=100.0,
        download_throughput=1000000.0,
        upload_throughput=500000.0
    )
    assert result['method'] == NetworkMethod.EMULATE_NETWORK_CONDITIONS
    assert result['params']['offline'] is False
    assert result['params']['latency'] == 100.0
    assert result['params']['downloadThroughput'] == 1000000.0
    assert result['params']['uploadThroughput'] == 500000.0


def test_emulate_network_conditions_with_all_params():
    """Test emulate_network_conditions with all parameters."""
    result = NetworkCommands.emulate_network_conditions(
        offline=False,
        latency=200.0,
        download_throughput=2000000.0,
        upload_throughput=1000000.0,
        connection_type=ConnectionType.CELLULAR4G,
        packet_loss=0.1,
        packet_queue_length=100,
        packet_reordering=True
    )
    assert result['method'] == NetworkMethod.EMULATE_NETWORK_CONDITIONS
    assert result['params']['offline'] is False
    assert result['params']['latency'] == 200.0
    assert result['params']['downloadThroughput'] == 2000000.0
    assert result['params']['uploadThroughput'] == 1000000.0
    assert result['params']['connectionType'] == ConnectionType.CELLULAR4G
    assert result['params']['packetLoss'] == 0.1
    assert result['params']['packetQueueLength'] == 100
    assert result['params']['packetReordering'] is True


def test_get_security_isolation_status_minimal():
    """Test get_security_isolation_status with minimal parameters."""
    result = NetworkCommands.get_security_isolation_status()
    assert result['method'] == NetworkMethod.GET_SECURITY_ISOLATION_STATUS
    assert result['params'] == {}


def test_get_security_isolation_status_with_frame_id():
    """Test get_security_isolation_status with frame ID."""
    result = NetworkCommands.get_security_isolation_status(frame_id='frame123')
    assert result['method'] == NetworkMethod.GET_SECURITY_ISOLATION_STATUS
    assert result['params']['frameId'] == 'frame123'


def test_load_network_resource():
    """Test load_network_resource method."""
    options = {
        'disableCache': True,
        'includeCredentials': False
    }
    result = NetworkCommands.load_network_resource(
        url='https://example.com/resource',
        options=options
    )
    assert result['method'] == NetworkMethod.LOAD_NETWORK_RESOURCE
    assert result['params']['url'] == 'https://example.com/resource'
    assert result['params']['options'] == options


def test_load_network_resource_with_frame_id():
    """Test load_network_resource with frame ID."""
    options = {
        'disableCache': False,
        'includeCredentials': True
    }
    result = NetworkCommands.load_network_resource(
        url='https://example.com/resource',
        options=options,
        frame_id='frame123'
    )
    assert result['method'] == NetworkMethod.LOAD_NETWORK_RESOURCE
    assert result['params']['url'] == 'https://example.com/resource'
    assert result['params']['options'] == options
    assert result['params']['frameId'] == 'frame123'


def test_replay_xhr():
    """Test replay_xhr method."""
    result = NetworkCommands.replay_xhr(request_id='12345')
    assert result['method'] == NetworkMethod.REPLAY_XHR
    assert result['params']['requestId'] == '12345'
