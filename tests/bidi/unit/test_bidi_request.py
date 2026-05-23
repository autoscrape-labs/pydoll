"""Deterministic unit tests for BiDiRequest metadata extraction.

The fetch itself needs a real browser (covered in tests/bidi/integration), but the
parsing of BiDi network events — unwrapping BytesValue headers, pulling Set-Cookie
out of response.headers, and filtering events by the request URL — is exercised
here by feeding the helper the events Firefox would emit.
"""

from __future__ import annotations

from pydoll.browser.requests.bidi.request import BiDiRequest

URL = 'http://127.0.0.1:9999/api'


def _bytes(value: str) -> dict:
    """A BiDi BytesValue (string variant)."""
    return {'type': 'string', 'value': value}


def _response_event(url: str, headers: list[dict]) -> dict:
    return {
        'method': 'network.responseCompleted',
        'params': {'response': {'url': url, 'headers': headers}},
    }


def _request_event(url: str, headers: list[dict]) -> dict:
    return {
        'method': 'network.beforeRequestSent',
        'params': {'request': {'url': url, 'headers': headers}},
    }


def _request_for(url: str = URL) -> BiDiRequest:
    request = BiDiRequest(tab=None)
    request._target_url = url
    return request


def test_extract_received_headers_unwraps_bytes_value():
    request = _request_for()
    request._requests_received = [
        _response_event(URL, [
            {'name': 'Content-Type', 'value': _bytes('application/json')},
            {'name': 'X-Custom', 'value': _bytes('v')},
        ])
    ]
    headers = request._extract_received_headers()
    assert {(h['name'], h['value']) for h in headers} == {
        ('Content-Type', 'application/json'),
        ('X-Custom', 'v'),
    }


def test_extract_sent_headers_unwraps_bytes_value():
    request = _request_for()
    request._requests_sent = [
        _request_event(URL, [{'name': 'X-Req', 'value': _bytes('req-value')}])
    ]
    headers = request._extract_sent_headers()
    assert {(h['name'], h['value']) for h in headers} == {('X-Req', 'req-value')}


def test_extract_set_cookies_parses_name_and_value():
    request = _request_for()
    request._requests_received = [
        _response_event(URL, [
            {'name': 'Set-Cookie', 'value': _bytes('session=abc123; Path=/; HttpOnly')},
            {'name': 'Content-Type', 'value': _bytes('text/html')},
        ])
    ]
    cookies = request._extract_set_cookies()
    assert {(c['name'], c['value']) for c in cookies} == {('session', 'abc123')}


def test_extraction_ignores_events_for_other_urls():
    request = _request_for()
    request._requests_received = [
        _response_event('http://other/', [
            {'name': 'Set-Cookie', 'value': _bytes('leak=1')},
            {'name': 'X-Leak', 'value': _bytes('1')},
        ])
    ]
    assert request._extract_received_headers() == []
    assert request._extract_set_cookies() == []


def test_build_request_options_sets_json_body_and_content_type():
    request = _request_for()
    options = request._build_request_options('post', None, {'a': 1}, None)
    assert options['method'] == 'POST'
    assert options['body'] == '{"a": 1}'
    assert options['headers']['Content-Type'] == 'application/json'
