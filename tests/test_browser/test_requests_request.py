"""
Tests for pydoll.browser.requests.request module.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import urlencode

from pydoll.browser.requests.request import Request
from pydoll.browser.requests.response import Response
from pydoll.exceptions import HTTPError
from pydoll.protocol.fetch.types import HeaderEntry
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.network.types import CookieParam


@pytest_asyncio.fixture
async def mock_tab():
    """Create a mock Tab instance for testing."""
    tab = Mock()
    tab.network_events_enabled = False
    tab.enable_network_events = AsyncMock()
    tab.disable_network_events = AsyncMock()
    tab.clear_callbacks = AsyncMock()
    tab.on = AsyncMock()
    tab._execute_command = AsyncMock()
    return tab


@pytest_asyncio.fixture
async def request_instance(mock_tab):
    """Create a Request instance for testing."""
    return Request(mock_tab)


class TestRequestInitialization:
    """Test Request class initialization."""

    def test_request_initialization(self, mock_tab):
        """Test Request initialization with tab."""
        request = Request(mock_tab)
        
        assert request.tab == mock_tab
        assert request._network_events_enabled is False
        assert request._requests_sent == []
        assert request._requests_received == []

    def test_request_initialization_preserves_tab_reference(self, mock_tab):
        """Test that Request maintains reference to provided tab."""
        request = Request(mock_tab)
        assert request.tab is mock_tab


class TestRequestMethods:
    """Test HTTP method convenience functions."""

    @pytest.mark.asyncio
    async def test_get_method(self, request_instance):
        """Test GET request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.get('https://example.com', params={'q': 'test'})
            
            mock_request.assert_called_once_with(
                'GET', 'https://example.com', params={'q': 'test'}
            )

    @pytest.mark.asyncio
    async def test_post_method(self, request_instance):
        """Test POST request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.post(
                'https://example.com', 
                data={'key': 'value'}, 
                json={'json_key': 'json_value'}
            )
            
            mock_request.assert_called_once_with(
                'POST', 
                'https://example.com', 
                data={'key': 'value'}, 
                json={'json_key': 'json_value'}
            )

    @pytest.mark.asyncio
    async def test_put_method(self, request_instance):
        """Test PUT request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.put('https://example.com', json={'update': 'data'})
            
            mock_request.assert_called_once_with(
                'PUT', 'https://example.com', data=None, json={'update': 'data'}
            )

    @pytest.mark.asyncio
    async def test_patch_method(self, request_instance):
        """Test PATCH request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.patch('https://example.com', data='patch_data')
            
            mock_request.assert_called_once_with(
                'PATCH', 'https://example.com', data='patch_data', json=None
            )

    @pytest.mark.asyncio
    async def test_delete_method(self, request_instance):
        """Test DELETE request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.delete('https://example.com')
            
            mock_request.assert_called_once_with('DELETE', 'https://example.com')

    @pytest.mark.asyncio
    async def test_head_method(self, request_instance):
        """Test HEAD request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.head('https://example.com')
            
            mock_request.assert_called_once_with('HEAD', 'https://example.com')

    @pytest.mark.asyncio
    async def test_options_method(self, request_instance):
        """Test OPTIONS request method."""
        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            
            await request_instance.options('https://example.com')
            
            mock_request.assert_called_once_with('OPTIONS', 'https://example.com')


class TestRequestMainMethod:
    """Test main request method functionality."""

    @pytest.mark.asyncio
    async def test_request_success_flow(self, request_instance, mock_tab):
        """Test successful request execution flow."""
        # Mock execute_command response
        mock_result = {
            'result': {
                'result': {
                    'value': {
                        'status': 200,
                        'content': [72, 101, 108, 108, 111],  # "Hello" as bytes
                        'text': 'Hello',
                        'json': {'message': 'success'},
                        'url': 'https://example.com'
                    }
                }
            }
        }
        mock_tab._execute_command.return_value = mock_result
        
        # Mock helper methods
        with patch.object(request_instance, '_extract_received_headers') as mock_extract_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_extract_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_extract_cookies:
            
            mock_extract_headers.return_value = [HeaderEntry(name='Content-Type', value='application/json')]
            mock_extract_sent.return_value = [HeaderEntry(name='User-Agent', value='Test-Agent')]
            mock_extract_cookies.return_value = [CookieParam(name='session', value='abc123')]
            
            response = await request_instance.request('GET', 'https://example.com')
            
            assert isinstance(response, Response)
            assert response.status_code == 200
            assert response.text == 'Hello'
            assert response.json() == {'message': 'success'}
            assert response.url == 'https://example.com'

    @pytest.mark.asyncio
    async def test_request_with_params(self, request_instance):
        """Test request with query parameters."""
        with patch.object(request_instance, '_build_url_with_params') as mock_build_url, \
             patch.object(request_instance, '_execute_fetch_request') as mock_execute, \
             patch.object(request_instance, '_extract_received_headers') as mock_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_cookies, \
             patch.object(request_instance, '_build_response') as mock_build_response, \
             patch.object(request_instance, '_clear_callbacks') as mock_clear:
            
            mock_build_url.return_value = 'https://example.com?q=test'
            mock_execute.return_value = {'result': {'result': {'value': {}}}}
            mock_headers.return_value = []
            mock_sent.return_value = []
            mock_cookies.return_value = []
            mock_build_response.return_value = Mock()
            
            await request_instance.request('GET', 'https://example.com', params={'q': 'test'})
            
            mock_build_url.assert_called_once_with('https://example.com', {'q': 'test'})

    @pytest.mark.asyncio
    async def test_request_with_json_data(self, request_instance):
        """Test request with JSON data."""
        with patch.object(request_instance, '_build_request_options') as mock_build_options, \
             patch.object(request_instance, '_execute_fetch_request') as mock_execute, \
             patch.object(request_instance, '_extract_received_headers') as mock_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_cookies, \
             patch.object(request_instance, '_build_response') as mock_build_response, \
             patch.object(request_instance, '_clear_callbacks') as mock_clear:
            
            mock_execute.return_value = {'result': {'result': {'value': {}}}}
            mock_headers.return_value = []
            mock_sent.return_value = []
            mock_cookies.return_value = []
            mock_build_response.return_value = Mock()
            
            json_data = {'key': 'value'}
            await request_instance.request('POST', 'https://example.com', json=json_data)
            
            mock_build_options.assert_called_once_with(
                'POST', None, json_data, None
            )

    @pytest.mark.asyncio
    async def test_request_failure_raises_http_error(self, request_instance, mock_tab):
        """Test that request failures raise HTTPError."""
        mock_tab._execute_command.side_effect = Exception("Network error")
        
        with pytest.raises(HTTPError, match="Request failed: Network error"):
            await request_instance.request('GET', 'https://example.com')

    @pytest.mark.asyncio
    async def test_request_always_clears_callbacks(self, request_instance, mock_tab):
        """Test that callbacks are always cleared, even on error."""
        mock_tab._execute_command.side_effect = Exception("Network error")
        
        with patch.object(request_instance, '_clear_callbacks') as mock_clear:
            with pytest.raises(HTTPError):
                await request_instance.request('GET', 'https://example.com')
            
            mock_clear.assert_called_once()


class TestRequestHelperMethods:
    """Test Request helper methods."""

    def test_build_url_with_params_no_params(self, request_instance):
        """Test URL building without parameters."""
        url = 'https://example.com'
        result = request_instance._build_url_with_params(url, None)
        assert result == url

    def test_build_url_with_params_simple(self, request_instance):
        """Test URL building with simple parameters."""
        url = 'https://example.com'
        params = {'q': 'test', 'page': '1'}
        result = request_instance._build_url_with_params(url, params)
        
        assert 'https://example.com?' in result
        assert 'q=test' in result
        assert 'page=1' in result

    def test_build_url_with_params_existing_query(self, request_instance):
        """Test URL building with existing query string."""
        url = 'https://example.com?existing=param'
        params = {'new': 'value'}
        result = request_instance._build_url_with_params(url, params)
        
        assert 'existing=param' in result
        assert 'new=value' in result

    def test_build_request_options_basic(self, request_instance):
        """Test basic request options building."""
        options = request_instance._build_request_options(
            'GET', None, None, None
        )
        
        assert options['method'] == 'GET'
        assert options['headers'] == {}

    def test_build_request_options_with_headers(self, request_instance):
        """Test request options building with headers."""
        headers = [HeaderEntry(name='Authorization', value='Bearer token')]
        
        with patch.object(request_instance, '_convert_header_entries_to_dict') as mock_convert:
            mock_convert.return_value = {'Authorization': 'Bearer token'}
            
            options = request_instance._build_request_options(
                'POST', headers, None, None
            )
            
            assert options['headers'] == {'Authorization': 'Bearer token'}
            mock_convert.assert_called_once_with(headers)

    def test_handle_json_options(self, request_instance):
        """Test JSON data handling."""
        options = {'headers': {}}
        json_data = {'key': 'value'}
        
        request_instance._handle_json_options(options, json_data)
        
        assert options['body'] == json.dumps(json_data)
        assert options['headers']['Content-Type'] == 'application/json'

    def test_handle_data_options_form_data(self, request_instance):
        """Test form data handling."""
        options = {'headers': {}}
        data = {'key': 'value', 'key2': 'value2'}
        
        request_instance._handle_data_options(options, data)
        
        assert options['body'] == urlencode(data, doseq=True)
        assert options['headers']['Content-Type'] == 'application/x-www-form-urlencoded'

    def test_handle_data_options_raw_data(self, request_instance):
        """Test raw data handling."""
        options = {'headers': {}}
        data = 'raw string data'
        
        request_instance._handle_data_options(options, data)
        
        assert options['body'] == data
        assert 'Content-Type' not in options['headers']

    def test_convert_header_entries_to_dict(self, request_instance):
        """Test header entries conversion to dictionary."""
        headers = [
            HeaderEntry(name='Content-Type', value='application/json'),
            HeaderEntry(name='Authorization', value='Bearer token')
        ]
        
        result = request_instance._convert_header_entries_to_dict(headers)
        
        expected = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
        }
        assert result == expected

    def test_convert_dict_to_header_entries(self, request_instance):
        """Test dictionary conversion to header entries."""
        headers_dict = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
        }
        
        result = request_instance._convert_dict_to_header_entries(headers_dict)
        
        assert len(result) == 2
        # Check that each result is a dictionary with the expected keys
        for header in result:
            assert 'name' in header
            assert 'value' in header
        assert {header['name']: header['value'] for header in result} == headers_dict


class TestRequestCallbackManagement:
    """Test callback registration and management."""

    @pytest.mark.asyncio
    async def test_register_callbacks_enables_network_events(self, request_instance, mock_tab):
        """Test that registering callbacks enables network events."""
        mock_tab.network_events_enabled = False
        
        await request_instance._register_callbacks()
        
        mock_tab.enable_network_events.assert_called_once()
        assert request_instance._network_events_enabled is True

    @pytest.mark.asyncio
    async def test_register_callbacks_skips_if_already_enabled(self, request_instance, mock_tab):
        """Test that network events are not re-enabled if already active."""
        mock_tab.network_events_enabled = True
        
        await request_instance._register_callbacks()
        
        mock_tab.enable_network_events.assert_not_called()
        assert request_instance._network_events_enabled is False

    @pytest.mark.asyncio
    async def test_register_callbacks_subscribes_to_events(self, request_instance, mock_tab):
        """Test that all required network events are subscribed to."""
        await request_instance._register_callbacks()
        
        expected_events = [
            NetworkEvent.REQUEST_WILL_BE_SENT,
            NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO,
            NetworkEvent.RESPONSE_RECEIVED,
            NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO
        ]
        
        assert mock_tab.on.call_count == len(expected_events)
        called_events = [call[0][0] for call in mock_tab.on.call_args_list]
        
        for event in expected_events:
            assert event in called_events

    @pytest.mark.asyncio
    async def test_clear_callbacks_disables_network_events(self, request_instance, mock_tab):
        """Test that clearing callbacks disables network events if they were enabled."""
        request_instance._network_events_enabled = True
        
        await request_instance._clear_callbacks()
        
        mock_tab.disable_network_events.assert_called_once()
        mock_tab.clear_callbacks.assert_called_once()
        assert request_instance._network_events_enabled is False

    @pytest.mark.asyncio
    async def test_clear_callbacks_skips_disable_if_not_enabled(self, request_instance, mock_tab):
        """Test that network events are not disabled if not enabled by request."""
        request_instance._network_events_enabled = False
        
        await request_instance._clear_callbacks()
        
        mock_tab.disable_network_events.assert_not_called()
        mock_tab.clear_callbacks.assert_called_once()


class TestRequestCookieExtraction:
    """Test cookie extraction functionality."""

    def test_parse_cookie_line_valid(self, request_instance):
        """Test parsing valid cookie line."""
        line = 'session_id=abc123; Path=/; HttpOnly'
        
        result = request_instance._parse_cookie_line(line)
        
        assert result is not None
        assert result['name'] == 'session_id'
        assert result['value'] == 'abc123'

    def test_parse_cookie_line_invalid(self, request_instance):
        """Test parsing invalid cookie line."""
        line = 'invalid_cookie_without_equals'
        
        result = request_instance._parse_cookie_line(line)
        
        assert result is None

    def test_parse_cookie_line_with_complex_value(self, request_instance):
        """Test parsing cookie with complex value."""
        line = 'complex=value=with=equals; Secure'
        
        result = request_instance._parse_cookie_line(line)
        
        assert result is not None
        assert result['name'] == 'complex'
        assert result['value'] == 'value=with=equals'

    def test_add_unique_cookies_no_duplicates(self, request_instance):
        """Test adding unique cookies without duplicates."""
        existing_cookies = [CookieParam(name='existing', value='value1')]
        new_cookies = [
            CookieParam(name='new', value='value2'),
            CookieParam(name='existing', value='value1')  # Duplicate
        ]
        
        request_instance._add_unique_cookies(existing_cookies, new_cookies)
        
        assert len(existing_cookies) == 2
        cookie_names = [cookie['name'] for cookie in existing_cookies]
        assert 'existing' in cookie_names
        assert 'new' in cookie_names

    def test_parse_set_cookie_header_multiline(self, request_instance):
        """Test parsing multi-line Set-Cookie header."""
        header = 'cookie1=value1; Path=/\ncookie2=value2; Secure'
        
        result = request_instance._parse_set_cookie_header(header)
        
        assert len(result) == 2
        assert result[0]['name'] == 'cookie1'
        assert result[1]['name'] == 'cookie2'


class TestRequestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_request_with_empty_url(self, request_instance):
        """Test request with empty URL."""
        with patch.object(request_instance, '_execute_fetch_request') as mock_execute, \
             patch.object(request_instance, '_extract_received_headers') as mock_headers, \
             patch.object(request_instance, '_extract_sent_headers') as mock_sent, \
             patch.object(request_instance, '_extract_set_cookies') as mock_cookies, \
             patch.object(request_instance, '_build_response') as mock_build_response, \
             patch.object(request_instance, '_clear_callbacks') as mock_clear:
            
            mock_execute.return_value = {'result': {'result': {'value': {}}}}
            mock_headers.return_value = []
            mock_sent.return_value = []
            mock_cookies.return_value = []
            mock_build_response.return_value = Mock()
            
            await request_instance.request('GET', '')
            
            mock_execute.assert_called_once()

    def test_build_url_with_special_characters(self, request_instance):
        """Test URL building with special characters in parameters."""
        url = 'https://example.com'
        params = {'q': 'hello world', 'special': 'value&with=chars'}
        
        result = request_instance._build_url_with_params(url, params)
        
        assert 'hello+world' in result or 'hello%20world' in result
        assert 'value%26with%3Dchars' in result

    def test_handle_data_options_with_bytes(self, request_instance):
        """Test handling raw bytes data."""
        options = {'headers': {}}
        data = b'binary data'
        
        request_instance._handle_data_options(options, data)
        
        assert options['body'] == data
        assert 'Content-Type' not in options['headers']

    def test_convert_header_entries_empty_list(self, request_instance):
        """Test converting empty header entries list."""
        result = request_instance._convert_header_entries_to_dict([])
        assert result == {}

    def test_convert_dict_to_header_entries_empty_dict(self, request_instance):
        """Test converting empty dictionary to header entries."""
        result = request_instance._convert_dict_to_header_entries({})
        assert result == []


class TestRequestHeaderExtraction:
    """Test header extraction methods from network events."""

    def test_extract_received_headers(self, request_instance):
        """Test _extract_received_headers method."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock network events with response headers
        mock_response_event = {
            'method': NetworkEvent.RESPONSE_RECEIVED,
            'params': {
                'response': {
                    'headers': {
                        'Content-Type': 'application/json',
                        'Content-Length': '100',
                        'Server': 'nginx/1.18.0'
                    }
                }
            }
        }
        
        mock_response_extra_event = {
            'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
            'params': {
                'blockedCookies': [],
                'headers': {
                    'Set-Cookie': 'session=abc123; Path=/',
                    'X-Custom-Header': 'custom-value'
                }
            }
        }
        
        # Set up mock events
        request_instance._requests_received = [mock_response_event, mock_response_extra_event]
        
        # Extract headers
        headers = request_instance._extract_received_headers()
        
        # Verify headers were extracted
        assert len(headers) >= 3  # At least Content-Type, Content-Length, Server
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert 'Content-Type' in header_dict
        assert header_dict['Content-Type'] == 'application/json'
        assert 'Content-Length' in header_dict
        assert header_dict['Content-Length'] == '100'
        assert 'Server' in header_dict
        assert header_dict['Server'] == 'nginx/1.18.0'

    def test_extract_sent_headers(self, request_instance):
        """Test _extract_sent_headers method."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock network events with request headers
        mock_request_event = {
            'method': NetworkEvent.REQUEST_WILL_BE_SENT,
            'params': {
                'request': {
                    'headers': {
                        'User-Agent': 'PyDoll/1.0',
                        'Accept': 'application/json',
                        'Authorization': 'Bearer token123'
                    }
                }
            }
        }
        
        mock_request_extra_event = {
            'method': NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO,
            'params': {
                'associatedCookies': [],
                'headers': {
                    'X-Forwarded-For': '192.168.1.1',
                    'X-Custom-Request': 'test-value'
                }
            }
        }
        
        # Set up mock events
        request_instance._requests_sent = [mock_request_event, mock_request_extra_event]
        
        # Extract headers
        headers = request_instance._extract_sent_headers()
        
        # Verify headers were extracted
        assert len(headers) >= 3  # At least User-Agent, Accept, Authorization
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert 'User-Agent' in header_dict
        assert header_dict['User-Agent'] == 'PyDoll/1.0'
        assert 'Accept' in header_dict
        assert header_dict['Accept'] == 'application/json'
        assert 'Authorization' in header_dict
        assert header_dict['Authorization'] == 'Bearer token123'

    def test_extract_headers_from_events_with_response_events(self, request_instance):
        """Test _extract_headers_from_events with response events."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock response events
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {
                    'response': {
                        'headers': {
                            'Content-Type': 'text/html',
                            'Cache-Control': 'no-cache'
                        }
                    }
                }
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'blockedCookies': [],
                    'headers': {
                        'X-Frame-Options': 'DENY',
                        'Strict-Transport-Security': 'max-age=31536000'
                    }
                }
            }
        ]
        
        # Define extractors for response events
        event_extractors = {
            'response': request_instance._extract_response_received_headers,
            'blockedCookies': request_instance._extract_response_received_extra_info_headers,
        }
        
        # Extract headers from events
        headers = request_instance._extract_headers_from_events(events, event_extractors)
        
        # Verify headers were extracted and deduplicated
        assert len(headers) == 4  # Content-Type, Cache-Control, X-Frame-Options, Strict-Transport-Security
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['Content-Type'] == 'text/html'
        assert header_dict['Cache-Control'] == 'no-cache'
        assert header_dict['X-Frame-Options'] == 'DENY'
        assert header_dict['Strict-Transport-Security'] == 'max-age=31536000'

    def test_extract_headers_from_events_with_request_events(self, request_instance):
        """Test _extract_headers_from_events with request events."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock request events
        events = [
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT,
                'params': {
                    'request': {
                        'headers': {
                            'Host': 'api.example.com',
                            'Connection': 'keep-alive'
                        }
                    }
                }
            },
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO,
                'params': {
                    'associatedCookies': [],
                    'headers': {
                        'Accept-Encoding': 'gzip, deflate',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                }
            }
        ]
        
        # Define extractors for request events
        event_extractors = {
            'request': request_instance._extract_request_sent_headers,
            'associatedCookies': request_instance._extract_request_sent_extra_info_headers,
        }
        
        # Extract headers from events
        headers = request_instance._extract_headers_from_events(events, event_extractors)
        
        # Verify headers were extracted
        assert len(headers) == 4  # Host, Connection, Accept-Encoding, Accept-Language
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['Host'] == 'api.example.com'
        assert header_dict['Connection'] == 'keep-alive'
        assert header_dict['Accept-Encoding'] == 'gzip, deflate'
        assert header_dict['Accept-Language'] == 'en-US,en;q=0.9'

    def test_extract_headers_from_events_deduplication(self, request_instance):
        """Test that _extract_headers_from_events deduplicates headers correctly."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events with duplicate headers
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {
                    'response': {
                        'headers': {
                            'Content-Type': 'application/json',
                            'Server': 'nginx'
                        }
                    }
                }
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'blockedCookies': [],
                    'headers': {
                        'Content-Type': 'application/json',  # Duplicate
                        'X-Custom': 'value'
                    }
                }
            }
        ]
        
        event_extractors = {
            'response': request_instance._extract_response_received_headers,
            'blockedCookies': request_instance._extract_response_received_extra_info_headers,
        }
        
        # Extract headers
        headers = request_instance._extract_headers_from_events(events, event_extractors)
        
        # Verify deduplication - Content-Type should appear only once
        header_names = [h['name'] for h in headers]
        assert header_names.count('Content-Type') == 1
        assert len(headers) == 3  # Content-Type (deduplicated), Server, X-Custom

    def test_extract_headers_from_events_empty_events(self, request_instance):
        """Test _extract_headers_from_events with empty events list."""
        event_extractors = {
            'response': request_instance._extract_response_received_headers,
        }
        
        # Extract headers from empty events
        headers = request_instance._extract_headers_from_events([], event_extractors)
        
        # Should return empty list
        assert headers == []

    def test_extract_headers_from_events_no_matching_keys(self, request_instance):
        """Test _extract_headers_from_events when no event keys match extractors."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with keys that don't match extractors
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {
                    'someOtherKey': {
                        'headers': {
                            'Content-Type': 'application/json'
                        }
                    }
                }
            }
        ]
        
        event_extractors = {
            'response': request_instance._extract_response_received_headers,
        }
        
        # Extract headers
        headers = request_instance._extract_headers_from_events(events, event_extractors)
        
        # Should return empty list since no keys match
        assert headers == []

    def test_extract_request_sent_headers(self, request_instance):
        """Test _extract_request_sent_headers method."""
        # Mock request params
        params = {
            'request': {
                'headers': {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': '*/*',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer secret-token'
                }
            },
            'otherData': 'should be ignored'
        }
        
        # Extract headers
        headers = request_instance._extract_request_sent_headers(params)
        
        # Verify headers were extracted correctly
        assert len(headers) == 4
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['User-Agent'] == 'Mozilla/5.0'
        assert header_dict['Accept'] == '*/*'
        assert header_dict['Content-Type'] == 'application/json'
        assert header_dict['Authorization'] == 'Bearer secret-token'

    def test_extract_request_sent_headers_empty_headers(self, request_instance):
        """Test _extract_request_sent_headers with empty headers."""
        params = {
            'request': {
                'headers': {}
            }
        }
        
        headers = request_instance._extract_request_sent_headers(params)
        assert headers == []

    def test_extract_request_sent_headers_missing_headers_key(self, request_instance):
        """Test _extract_request_sent_headers when headers key is missing."""
        params = {
            'request': {
                'url': 'https://example.com',
                'method': 'GET'
            }
        }
        
        headers = request_instance._extract_request_sent_headers(params)
        assert headers == []

    def test_extract_request_sent_extra_info_headers(self, request_instance):
        """Test _extract_request_sent_extra_info_headers method."""
        # Mock extra info params
        params = {
            'headers': {
                'X-Forwarded-For': '10.0.0.1',
                'X-Real-IP': '192.168.1.100',
                'X-Custom-Header': 'extra-info-value'
            },
            'associatedCookies': [],
            'otherData': 'should be ignored'
        }
        
        # Extract headers
        headers = request_instance._extract_request_sent_extra_info_headers(params)
        
        # Verify headers were extracted correctly
        assert len(headers) == 3
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['X-Forwarded-For'] == '10.0.0.1'
        assert header_dict['X-Real-IP'] == '192.168.1.100'
        assert header_dict['X-Custom-Header'] == 'extra-info-value'

    def test_extract_request_sent_extra_info_headers_empty(self, request_instance):
        """Test _extract_request_sent_extra_info_headers with empty headers."""
        params = {
            'headers': {},
            'associatedCookies': []
        }
        
        headers = request_instance._extract_request_sent_extra_info_headers(params)
        assert headers == []

    def test_extract_request_sent_extra_info_headers_missing_headers(self, request_instance):
        """Test _extract_request_sent_extra_info_headers when headers key is missing."""
        params = {
            'associatedCookies': [],
            'otherData': 'value'
        }
        
        headers = request_instance._extract_request_sent_extra_info_headers(params)
        assert headers == []

    def test_extract_response_received_headers(self, request_instance):
        """Test _extract_response_received_headers method."""
        # Mock response params
        params = {
            'response': {
                'headers': {
                    'Content-Type': 'text/html; charset=utf-8',
                    'Content-Length': '1024',
                    'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT',
                    'ETag': '"33a64df551425fcc55e4d42a148795d9f25f89d4"'
                }
            },
            'otherData': 'should be ignored'
        }
        
        # Extract headers
        headers = request_instance._extract_response_received_headers(params)
        
        # Verify headers were extracted correctly
        assert len(headers) == 4
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['Content-Type'] == 'text/html; charset=utf-8'
        assert header_dict['Content-Length'] == '1024'
        assert header_dict['Last-Modified'] == 'Wed, 21 Oct 2015 07:28:00 GMT'
        assert header_dict['ETag'] == '"33a64df551425fcc55e4d42a148795d9f25f89d4"'

    def test_extract_response_received_extra_info_headers(self, request_instance):
        """Test _extract_response_received_extra_info_headers method."""
        # Mock response extra info params
        params = {
            'headers': {
                'Set-Cookie': 'sessionid=abc123; HttpOnly; Secure',
                'X-Content-Type-Options': 'nosniff',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            },
            'blockedCookies': [],
            'otherData': 'should be ignored'
        }
        
        # Extract headers
        headers = request_instance._extract_response_received_extra_info_headers(params)
        
        # Verify headers were extracted correctly
        assert len(headers) == 4
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert header_dict['Set-Cookie'] == 'sessionid=abc123; HttpOnly; Secure'
        assert header_dict['X-Content-Type-Options'] == 'nosniff'
        assert header_dict['X-XSS-Protection'] == '1; mode=block'
        assert header_dict['Referrer-Policy'] == 'strict-origin-when-cross-origin'

    def test_header_extraction_with_complex_values(self, request_instance):
        """Test header extraction with complex header values."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with complex header values
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {
                    'response': {
                        'headers': {
                            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                            'Link': '</css/style.css>; rel=preload; as=style, </js/app.js>; rel=preload; as=script',
                            'Cache-Control': 'public, max-age=3600, s-maxage=7200, must-revalidate',
                        }
                    }
                }
            }
        ]
        
        event_extractors = {
            'response': request_instance._extract_response_received_headers,
        }
        
        # Extract headers
        headers = request_instance._extract_headers_from_events(events, event_extractors)
        
        # Verify complex values are preserved
        header_dict = {h['name']: h['value'] for h in headers}
        
        assert 'Content-Security-Policy' in header_dict
        assert "default-src 'self'" in header_dict['Content-Security-Policy']
        assert 'Link' in header_dict
        assert 'rel=preload' in header_dict['Link']
        assert 'Cache-Control' in header_dict
        assert 'must-revalidate' in header_dict['Cache-Control']

    def test_header_extraction_integration_flow(self, request_instance):
        """Test complete header extraction flow for both sent and received headers."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Set up complete request/response flow
        request_instance._requests_sent = [
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT,
                'params': {
                    'request': {
                        'headers': {
                            'Host': 'api.example.com',
                            'User-Agent': 'PyDoll/1.0',
                            'Accept': 'application/json'
                        }
                    }
                }
            }
        ]
        
        request_instance._requests_received = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {
                    'response': {
                        'headers': {
                            'Content-Type': 'application/json',
                            'Server': 'nginx/1.18.0',
                            'Content-Length': '256'
                        }
                    }
                }
            }
        ]
        
        # Extract both sent and received headers
        sent_headers = request_instance._extract_sent_headers()
        received_headers = request_instance._extract_received_headers()
        
        # Verify sent headers
        sent_dict = {h['name']: h['value'] for h in sent_headers}
        assert sent_dict['Host'] == 'api.example.com'
        assert sent_dict['User-Agent'] == 'PyDoll/1.0'
        assert sent_dict['Accept'] == 'application/json'
        
        # Verify received headers
        received_dict = {h['name']: h['value'] for h in received_headers}
        assert received_dict['Content-Type'] == 'application/json'
        assert received_dict['Server'] == 'nginx/1.18.0'
        assert received_dict['Content-Length'] == '256'
        
        # Verify they are separate
        assert len(sent_headers) == 3
        assert len(received_headers) == 3
        assert sent_headers != received_headers

    def test_filter_response_extra_info_events(self, request_instance):
        """Test _filter_response_extra_info_events method."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events with different types
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {'response': {'headers': {}}}
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {'Set-Cookie': 'session=abc123; Path=/'},
                    'blockedCookies': []
                }
            },
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT,
                'params': {'request': {'headers': {}}}
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {'Set-Cookie': 'token=xyz789; Secure'},
                    'blockedCookies': []
                }
            }
        ]
        
        # Set up mock requests_received with the events
        request_instance._requests_received = events
        
        # Filter for response extra info events
        filtered_events = request_instance._filter_response_extra_info_events()
        
        # Should only return RESPONSE_RECEIVED_EXTRA_INFO events
        assert len(filtered_events) == 2
        
        for event in filtered_events:
            assert event['method'] == NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO
            assert 'headers' in event['params']
            assert 'Set-Cookie' in event['params']['headers']

    def test_filter_response_extra_info_events_empty(self, request_instance):
        """Test _filter_response_extra_info_events with no matching events."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events without RESPONSE_RECEIVED_EXTRA_INFO
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {'response': {'headers': {}}}
            },
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT,
                'params': {'request': {'headers': {}}}
            }
        ]
        
        request_instance._requests_received = events
        
        # Filter for response extra info events
        filtered_events = request_instance._filter_response_extra_info_events()
        
        # Should return empty list
        assert filtered_events == []

    def test_filter_response_extra_info_events_no_events(self, request_instance):
        """Test _filter_response_extra_info_events with empty events list."""
        request_instance._requests_received = []
        
        # Filter for response extra info events
        filtered_events = request_instance._filter_response_extra_info_events()
        
        # Should return empty list
        assert filtered_events == []

    def test_extract_set_cookies_basic(self, request_instance):
        """Test _extract_set_cookies method with basic cookies."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events with Set-Cookie headers
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'sessionid=abc123; Path=/; HttpOnly',
                        'Content-Type': 'application/json'
                    },
                    'blockedCookies': []
                }
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'userid=456; Domain=.example.com; Secure',
                        'X-Custom': 'value'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should have 2 cookies
        assert len(cookies) == 2
        
        # Check first cookie (only name and value are extracted)
        cookie1 = next(c for c in cookies if c['name'] == 'sessionid')
        assert cookie1['value'] == 'abc123'
        
        # Check second cookie (only name and value are extracted)
        cookie2 = next(c for c in cookies if c['name'] == 'userid')
        assert cookie2['value'] == '456'

    def test_extract_set_cookies_multiple_cookies_same_header(self, request_instance):
        """Test _extract_set_cookies with multiple cookies in same Set-Cookie header."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with multiple cookies in one header (newline-separated, not comma)
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'cookie1=value1; Path=/\ncookie2=value2; HttpOnly\ncookie3=value3; Secure'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should have 3 cookies (split by newline)
        assert len(cookies) == 3
        
        cookie_names = [c['name'] for c in cookies]
        assert 'cookie1' in cookie_names
        assert 'cookie2' in cookie_names
        assert 'cookie3' in cookie_names
        
        # Check values (attributes are ignored)
        cookie1 = next(c for c in cookies if c['name'] == 'cookie1')
        assert cookie1['value'] == 'value1'
        
        cookie2 = next(c for c in cookies if c['name'] == 'cookie2')
        assert cookie2['value'] == 'value2'
        
        cookie3 = next(c for c in cookies if c['name'] == 'cookie3')
        assert cookie3['value'] == 'value3'

    def test_extract_set_cookies_duplicate_names(self, request_instance):
        """Test _extract_set_cookies with duplicate cookie names (should be deduplicated)."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events with duplicate cookie names
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'sessionid=first_value; Path=/admin'
                    },
                    'blockedCookies': []
                }
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'sessionid=second_value; Path=/user'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should have 2 cookies (different values, so not deduplicated by object equality)
        assert len(cookies) == 2
        cookie_names = [c['name'] for c in cookies]
        assert cookie_names.count('sessionid') == 2
        
        # Both cookies should be present with different values
        values = [c['value'] for c in cookies if c['name'] == 'sessionid']
        assert 'first_value' in values
        assert 'second_value' in values

    def test_extract_set_cookies_complex_values(self, request_instance):
        """Test _extract_set_cookies with complex cookie values and attributes."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with complex cookie attributes
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9; Domain=api.example.com; Path=/api; Secure; HttpOnly; SameSite=Strict; Max-Age=3600'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should have 1 cookie (only name and value extracted)
        assert len(cookies) == 1
        cookie = cookies[0]
        
        assert cookie['name'] == 'auth_token'
        assert cookie['value'] == 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        # Attributes like domain, path, secure, etc. are ignored by the implementation

    def test_extract_set_cookies_no_set_cookie_headers(self, request_instance):
        """Test _extract_set_cookies when no Set-Cookie headers are present."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock events without Set-Cookie headers
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-Custom-Header': 'value'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should return empty list
        assert cookies == []

    def test_extract_set_cookies_empty_events(self, request_instance):
        """Test _extract_set_cookies with empty events list."""
        request_instance._requests_received = []
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should return empty list
        assert cookies == []

    def test_extract_set_cookies_malformed_cookies(self, request_instance):
        """Test _extract_set_cookies with malformed cookie strings."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with malformed cookies (newline-separated to match implementation)
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'valid_cookie=value123; Path=/\nmalformed_cookie_no_value\n=empty_name_cookie; HttpOnly\nanother_valid=test'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should only extract valid cookies (2 valid ones - those with non-empty names)
        # The implementation rejects cookies with empty names
        assert len(cookies) == 2
        
        cookie_names = [c['name'] for c in cookies]
        assert 'valid_cookie' in cookie_names
        assert 'another_valid' in cookie_names
        
        # Verify values
        valid_cookie = next(c for c in cookies if c['name'] == 'valid_cookie')
        assert valid_cookie['value'] == 'value123'
        
        another_valid = next(c for c in cookies if c['name'] == 'another_valid')
        assert another_valid['value'] == 'test'

    def test_extract_set_cookies_edge_case_attributes(self, request_instance):
        """Test _extract_set_cookies with edge case cookie attributes."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with edge case attributes
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'test_cookie=value; Expires=Wed, 09 Jun 2021 10:18:14 GMT; Max-Age=0; SameSite=None; Priority=High'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should have 1 cookie (only name and value extracted)
        assert len(cookies) == 1
        cookie = cookies[0]
        
        assert cookie['name'] == 'test_cookie'
        assert cookie['value'] == 'value'
        # All attributes like expires, maxAge, sameSite, etc. are ignored by the implementation

    def test_extract_set_cookies_integration_with_filter(self, request_instance):
        """Test integration between _extract_set_cookies and _filter_response_extra_info_events."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock mixed events (some relevant, some not)
        events = [
            {
                'method': NetworkEvent.REQUEST_WILL_BE_SENT,
                'params': {'request': {'headers': {}}}
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {'Set-Cookie': 'filtered_cookie=should_be_extracted; Path=/'},
                    'blockedCookies': []
                }
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED,
                'params': {'response': {'headers': {}}}
            },
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {'Set-Cookie': 'another_cookie=also_extracted; HttpOnly'},
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies (should use filtering internally)
        cookies = request_instance._extract_set_cookies()
        
        # Should have 2 cookies from the 2 RESPONSE_RECEIVED_EXTRA_INFO events
        assert len(cookies) == 2
        
        cookie_names = [c['name'] for c in cookies]
        assert 'filtered_cookie' in cookie_names
        assert 'another_cookie' in cookie_names

    def test_extract_set_cookies_empty_name_rejection(self, request_instance):
        """Test that _extract_set_cookies rejects cookies with empty names."""
        from pydoll.protocol.network.events import NetworkEvent
        
        # Mock event with various invalid cookie formats
        events = [
            {
                'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                'params': {
                    'headers': {
                        'Set-Cookie': 'valid_cookie=value\n=empty_name_value\n =space_only_name_value\n\t=tab_only_name_value'
                    },
                    'blockedCookies': []
                }
            }
        ]
        
        request_instance._requests_received = events
        
        # Extract cookies
        cookies = request_instance._extract_set_cookies()
        
        # Should only extract the valid cookie, rejecting all empty/whitespace-only names
        assert len(cookies) == 1
        assert cookies[0]['name'] == 'valid_cookie'
        assert cookies[0]['value'] == 'value'

    def test_parse_cookie_line_empty_name_validation(self, request_instance):
        """Test _parse_cookie_line directly with empty names."""
        # Test various forms of empty names
        assert request_instance._parse_cookie_line('=value') is None
        assert request_instance._parse_cookie_line(' =value') is None
        assert request_instance._parse_cookie_line('\t=value') is None
        assert request_instance._parse_cookie_line('  \t  =value') is None
        
        # Test valid names
        result = request_instance._parse_cookie_line('name=value')
        assert result is not None
        assert result['name'] == 'name'
        assert result['value'] == 'value'
        
        # Test whitespace around valid names (should be trimmed)
        result = request_instance._parse_cookie_line('  name  =  value  ')
        assert result is not None
        assert result['name'] == 'name'
        assert result['value'] == 'value'