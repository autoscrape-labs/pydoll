"""
Tests for pydoll.browser.requests.response module.
"""

import json
import pytest

from pydoll.browser.requests.response import Response, STATUS_CODE_RANGE_OK
from pydoll.exceptions import HTTPError
from pydoll.protocol.fetch.types import HeaderEntry
from pydoll.protocol.network.types import CookieParam


class TestResponseInitialization:
    """Test Response class initialization."""

    def test_response_initialization_minimal(self):
        """Test Response initialization with minimal parameters."""
        response = Response(status_code=200)
        
        assert response.status_code == 200
        assert response.content == b''
        assert response.text == ''
        assert response.headers == []
        assert response.request_headers == []
        assert response.cookies == []
        assert response.ok is True

    def test_response_initialization_full(self):
        """Test Response initialization with all parameters."""
        headers = [HeaderEntry(name='Content-Type', value='application/json')]
        request_headers = [HeaderEntry(name='User-Agent', value='Test-Agent')]
        cookies = [CookieParam(name='session', value='abc123')]
        json_data = {'message': 'success'}
        
        response = Response(
            status_code=201,
            content=b'{"message": "success"}',
            text='{"message": "success"}',
            json=json_data,
            response_headers=headers,
            request_headers=request_headers,
            cookies=cookies,
            url='https://example.com'
        )
        
        assert response.status_code == 201
        assert response.content == b'{"message": "success"}'
        assert response.text == '{"message": "success"}'
        assert response.headers == headers
        assert response.request_headers == request_headers
        assert response.cookies == cookies
        assert response.ok is True

    def test_response_initialization_with_none_values(self):
        """Test Response initialization handles None values correctly."""
        response = Response(
            status_code=200,
            response_headers=None,
            request_headers=None,
            cookies=None
        )
        
        assert response.headers == []
        assert response.request_headers == []
        assert response.cookies == []


class TestResponseProperties:
    """Test Response properties."""

    def test_ok_property_success_codes(self):
        """Test ok property returns True for success status codes."""
        success_codes = [200, 201, 204, 299, 300, 301, 302, 399]
        
        for code in success_codes:
            response = Response(status_code=code)
            assert response.ok is True, f"Status code {code} should be ok"

    def test_ok_property_error_codes(self):
        """Test ok property returns False for error status codes."""
        error_codes = [400, 401, 403, 404, 500, 502, 503]
        
        for code in error_codes:
            response = Response(status_code=code)
            assert response.ok is False, f"Status code {code} should not be ok"

    def test_status_code_property(self):
        """Test status_code property."""
        response = Response(status_code=404)
        assert response.status_code == 404

    def test_content_property(self):
        """Test content property returns bytes."""
        content = b'Hello, World!'
        response = Response(status_code=200, content=content)
        assert response.content == content
        assert isinstance(response.content, bytes)

    def test_text_property_provided(self):
        """Test text property when text is provided."""
        text = 'Hello, World!'
        response = Response(status_code=200, text=text)
        assert response.text == text

    def test_text_property_decoded_from_content(self):
        """Test text property decodes from content when not provided."""
        content = b'Hello, World!'
        response = Response(status_code=200, content=content)
        assert response.text == 'Hello, World!'

    def test_text_property_handles_encoding_errors(self):
        """Test text property handles encoding errors gracefully."""
        # Invalid UTF-8 sequence
        content = b'\xff\xfe\xfd'
        response = Response(status_code=200, content=content)
        
        # Should not raise exception and should have some text
        text = response.text
        assert isinstance(text, str)
        assert len(text) > 0

    def test_text_property_empty_content(self):
        """Test text property with empty content."""
        response = Response(status_code=200, content=b'')
        assert response.text == ''

    def test_headers_property(self):
        """Test headers property returns response headers."""
        headers = [
            HeaderEntry(name='Content-Type', value='application/json'),
            HeaderEntry(name='Content-Length', value='100')
        ]
        response = Response(status_code=200, response_headers=headers)
        assert response.headers == headers

    def test_request_headers_property(self):
        """Test request_headers property returns request headers."""
        headers = [
            HeaderEntry(name='User-Agent', value='Test-Agent'),
            HeaderEntry(name='Accept', value='application/json')
        ]
        response = Response(status_code=200, request_headers=headers)
        assert response.request_headers == headers

    def test_cookies_property(self):
        """Test cookies property returns cookies."""
        cookies = [
            CookieParam(name='session', value='abc123'),
            CookieParam(name='csrf', value='token456')
        ]
        response = Response(status_code=200, cookies=cookies)
        assert response.cookies == cookies

    def test_url_property(self):
        """Test url property returns final URL."""
        url = 'https://api.example.com/data'
        response = Response(status_code=200, url=url)
        assert response.url == url

    def test_url_property_empty(self):
        """Test url property with empty URL."""
        response = Response(status_code=200, url='')
        assert response.url == ''


class TestResponseJSONMethod:
    """Test Response json() method."""

    def test_json_method_with_provided_json(self):
        """Test json() method when JSON data is provided."""
        json_data = {'message': 'success', 'code': 200}
        response = Response(status_code=200, json=json_data)
        
        result = response.json()
        assert result == json_data

    def test_json_method_parses_from_text(self):
        """Test json() method parses JSON from text."""
        json_text = '{"message": "success", "code": 200}'
        response = Response(status_code=200, text=json_text)
        
        result = response.json()
        assert result == {'message': 'success', 'code': 200}

    def test_json_method_caches_result(self):
        """Test json() method caches parsed result."""
        json_text = '{"message": "success"}'
        response = Response(status_code=200, text=json_text)
        
        # First call should parse
        result1 = response.json()
        # Second call should return cached result
        result2 = response.json()
        
        assert result1 == result2
        assert result1 is result2  # Same object instance

    def test_json_method_invalid_json_raises_error(self):
        """Test json() method raises ValueError for invalid JSON."""
        response = Response(status_code=200, text='invalid json')
        
        with pytest.raises(ValueError, match='Response is not valid JSON'):
            response.json()

    def test_json_method_empty_text(self):
        """Test json() method with empty text."""
        response = Response(status_code=200, text='')
        
        with pytest.raises(ValueError, match='Response is not valid JSON'):
            response.json()

    def test_json_method_with_array(self):
        """Test json() method with JSON array."""
        json_text = '[{"id": 1}, {"id": 2}]'
        response = Response(status_code=200, text=json_text)
        
        result = response.json()
        assert result == [{'id': 1}, {'id': 2}]

    def test_json_method_with_primitive_values(self):
        """Test json() method with primitive JSON values."""
        test_cases = [
            ('true', True),
            ('false', False),
            ('null', None),
            ('42', 42),
            ('"string"', 'string')
        ]
        
        for json_text, expected in test_cases:
            response = Response(status_code=200, text=json_text)
            result = response.json()
            assert result == expected


class TestResponseRaiseForStatus:
    """Test Response raise_for_status() method."""

    def test_raise_for_status_success_codes(self):
        """Test raise_for_status() does not raise for success codes."""
        success_codes = [200, 201, 204, 299, 300, 301, 302, 399]
        
        for code in success_codes:
            response = Response(status_code=code, url='https://example.com')
            # Should not raise any exception
            response.raise_for_status()

    def test_raise_for_status_client_error(self):
        """Test raise_for_status() raises for client error codes."""
        error_codes = [400, 401, 403, 404, 422, 499]
        
        for code in error_codes:
            response = Response(status_code=code, url='https://example.com')
            with pytest.raises(HTTPError, match=f'{code} Client Error'):
                response.raise_for_status()

    def test_raise_for_status_server_error(self):
        """Test raise_for_status() raises for server error codes."""
        error_codes = [500, 502, 503, 504, 599]
        
        for code in error_codes:
            response = Response(status_code=code, url='https://example.com')
            with pytest.raises(HTTPError, match=f'{code} Client Error'):
                response.raise_for_status()

    def test_raise_for_status_includes_url(self):
        """Test raise_for_status() includes URL in error message."""
        url = 'https://api.example.com/endpoint'
        response = Response(status_code=404, url=url)
        
        with pytest.raises(HTTPError, match=f'for url {url}'):
            response.raise_for_status()

    def test_raise_for_status_empty_url(self):
        """Test raise_for_status() works with empty URL."""
        response = Response(status_code=500, url='')
        
        with pytest.raises(HTTPError, match='500 Client Error: for url'):
            response.raise_for_status()


class TestHTTPErrorException:
    """Test HTTPError exception class."""

    def test_http_error_creation(self):
        """Test HTTPError can be created with message."""
        error = HTTPError('Test error message')
        assert str(error) == 'Test error message'

    def test_http_error_inheritance(self):
        """Test HTTPError inherits from Exception."""
        error = HTTPError('Test error')
        assert isinstance(error, Exception)

    def test_http_error_with_format_string(self):
        """Test HTTPError with formatted message."""
        status_code = 404
        url = 'https://example.com'
        error = HTTPError(f'{status_code} Client Error: for url {url}')
        
        expected_message = '404 Client Error: for url https://example.com'
        assert str(error) == expected_message


class TestResponseEdgeCases:
    """Test Response edge cases and unusual scenarios."""

    def test_response_with_binary_content(self):
        """Test Response with binary content."""
        binary_data = bytes(range(256))  # All possible byte values
        response = Response(status_code=200, content=binary_data)
        
        assert response.content == binary_data
        assert isinstance(response.content, bytes)

    def test_response_with_unicode_text(self):
        """Test Response with Unicode text."""
        unicode_text = '🌟 Hello, 世界! 🚀'
        response = Response(status_code=200, text=unicode_text)
        
        assert response.text == unicode_text

    def test_response_text_lazy_decoding(self):
        """Test that text decoding is lazy and cached."""
        content = 'Hello, World!'.encode('utf-8')
        response = Response(status_code=200, content=content)
        
        # Access text multiple times
        text1 = response.text
        text2 = response.text
        
        assert text1 == text2
        assert text1 == 'Hello, World!'

    def test_response_with_large_content(self):
        """Test Response with large content."""
        large_content = b'x' * 1000000  # 1MB of data
        response = Response(status_code=200, content=large_content)
        
        assert len(response.content) == 1000000
        assert response.content == large_content

    def test_response_status_code_boundary_values(self):
        """Test Response with boundary status code values."""
        boundary_codes = [100, 199, 200, 299, 300, 399, 400, 499, 500, 599]
        
        for code in boundary_codes:
            response = Response(status_code=code)
            assert response.status_code == code
            
            # Check ok property boundary
            if code in STATUS_CODE_RANGE_OK:
                assert response.ok is True
            else:
                assert response.ok is False

    def test_response_with_complex_headers(self):
        """Test Response with complex header scenarios."""
        headers = [
            HeaderEntry(name='Set-Cookie', value='session=abc; Path=/'),
            HeaderEntry(name='Set-Cookie', value='csrf=xyz; HttpOnly'),
            HeaderEntry(name='Content-Type', value='application/json; charset=utf-8'),
            HeaderEntry(name='X-Custom-Header', value='custom value with spaces')
        ]
        
        response = Response(status_code=200, response_headers=headers)
        assert len(response.headers) == 4
        assert response.headers == headers

    def test_response_with_empty_json_object(self):
        """Test Response with empty JSON object."""
        response = Response(status_code=200, text='{}')
        result = response.json()
        assert result == {}

    def test_response_with_nested_json(self):
        """Test Response with deeply nested JSON."""
        nested_json = {
            'level1': {
                'level2': {
                    'level3': {
                        'data': ['item1', 'item2'],
                        'metadata': {'count': 2, 'type': 'array'}
                    }
                }
            }
        }
        
        response = Response(status_code=200, json=nested_json)
        result = response.json()
        assert result == nested_json
        assert result['level1']['level2']['level3']['data'] == ['item1', 'item2']


class TestResponseIntegration:
    """Test Response integration scenarios."""

    def test_complete_response_workflow(self):
        """Test complete response workflow with all components."""
        # Simulate a complete API response
        headers = [
            HeaderEntry(name='Content-Type', value='application/json'),
            HeaderEntry(name='Content-Length', value='45'),
            HeaderEntry(name='Server', value='nginx/1.18.0')
        ]
        
        request_headers = [
            HeaderEntry(name='User-Agent', value='PyDoll/1.0'),
            HeaderEntry(name='Accept', value='application/json'),
            HeaderEntry(name='Authorization', value='Bearer token123')
        ]
        
        cookies = [
            CookieParam(name='session_id', value='sess_abc123'),
            CookieParam(name='preferences', value='theme=dark')
        ]
        
        json_data = {
            'status': 'success',
            'data': {'id': 1, 'name': 'Test Item'},
            'timestamp': '2023-12-01T10:00:00Z'
        }
        
        response = Response(
            status_code=200,
            content=json.dumps(json_data).encode('utf-8'),
            text=json.dumps(json_data),
            json=json_data,
            response_headers=headers,
            request_headers=request_headers,
            cookies=cookies,
            url='https://api.example.com/items/1'
        )
        
        # Test all aspects
        assert response.ok is True
        assert response.status_code == 200
        assert response.json() == json_data
        assert len(response.headers) == 3
        assert len(response.request_headers) == 3
        assert len(response.cookies) == 2
        
        # Should not raise
        response.raise_for_status()

    def test_error_response_workflow(self):
        """Test error response workflow."""
        error_json = {
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'code': 404
        }
        
        response = Response(
            status_code=404,
            text=json.dumps(error_json),
            url='https://api.example.com/items/999'
        )
        
        assert response.ok is False
        assert response.status_code == 404
        assert response.json() == error_json
        
        with pytest.raises(HTTPError):
            response.raise_for_status()