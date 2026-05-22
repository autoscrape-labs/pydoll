"""Deterministic unit tests for Request Set-Cookie extraction.

``tab.request`` fills ``Response.cookies`` from the CDP
``responseReceivedExtraInfo`` events captured during the fetch, but that event's
delivery of ``Set-Cookie`` is unreliable in headless CI — a real-browser
assertion on extracted cookies is therefore inherently flaky. The extraction and
parsing path is exercised here by feeding the helper the events a browser would
emit, which is deterministic and faithful to the real code path.
"""

from __future__ import annotations

from pydoll.browser.requests.request import Request
from pydoll.protocol.network.events import NetworkEvent


def _extra_info_event(set_cookie_value):
    return {
        'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
        'params': {'headers': {'Set-Cookie': set_cookie_value}},
    }


def test_extract_set_cookies_parses_name_and_value():
    request = Request(tab=None)
    request._requests_received = [_extra_info_event('session=abc123; Path=/; HttpOnly')]
    cookies = request._extract_set_cookies()
    assert {(c['name'], c['value']) for c in cookies} == {('session', 'abc123')}


def test_extract_set_cookies_skips_malformed_lines():
    request = Request(tab=None)
    request._requests_received = [
        _extra_info_event('good=value1; Path=/\nnovalue\n=emptyname; Path=/\nsecond=value2')
    ]
    names = {c['name'] for c in request._extract_set_cookies()}
    assert {'good', 'second'} <= names
    assert '' not in names
    assert 'novalue' not in names


def test_extract_set_cookies_ignores_non_extra_info_events():
    request = Request(tab=None)
    request._requests_received = [
        {'method': 'Network.responseReceived', 'params': {'headers': {'Set-Cookie': 'x=1'}}}
    ]
    assert request._extract_set_cookies() == []


def test_extract_set_cookies_empty_without_events():
    assert Request(tab=None)._extract_set_cookies() == []
