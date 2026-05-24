"""Deterministic unit tests for HAR cookie parsing.

The recorder fills response/request cookies from the CDP
``responseReceivedExtraInfo`` / ``requestWillBeSentExtraInfo`` events, whose
delivery (carrying ``Set-Cookie`` / ``Cookie``) is unreliable in headless CI —
a real-browser assertion on captured cookies is therefore inherently flaky.
The parsing contract is the part worth pinning, so it is tested here directly
against header dicts: deterministic and faithful to what the recorder runs.
"""

from __future__ import annotations

from pydoll.browser.requests.cdp.har_recorder import HarRecorder


def test_parse_request_cookies_splits_cookie_header():
    cookies = HarRecorder._parse_request_cookies({'Cookie': 'a=1; b=2; c=hello'})
    assert {c['name']: c['value'] for c in cookies} == {'a': '1', 'b': '2', 'c': 'hello'}


def test_parse_request_cookies_handles_missing_lowercase_and_malformed():
    assert HarRecorder._parse_request_cookies({}) == []
    assert HarRecorder._parse_request_cookies({'cookie': ''}) == []
    # a segment without '=' is skipped; the valid one is kept
    cookies = HarRecorder._parse_request_cookies({'cookie': 'valid=1; broken'})
    assert [c['name'] for c in cookies] == ['valid']


def test_parse_response_cookies_extracts_value_and_attributes():
    headers = {
        'Set-Cookie': (
            'har_session=abc123; Path=/; HttpOnly\nhar_secure=xyz789; Secure; Domain=127.0.0.1'
        )
    }
    by_name = {c['name']: c for c in HarRecorder._parse_response_cookies(headers)}

    assert by_name['har_session']['value'] == 'abc123'
    assert by_name['har_session']['path'] == '/'
    assert by_name['har_session']['httpOnly'] is True

    assert by_name['har_secure']['value'] == 'xyz789'
    assert by_name['har_secure']['secure'] is True
    assert by_name['har_secure']['domain'] == '127.0.0.1'


def test_parse_response_cookies_handles_missing_and_malformed():
    assert HarRecorder._parse_response_cookies({}) == []
    # a line without '=' and a line with an empty name are skipped; the valid one is kept
    cookies = HarRecorder._parse_response_cookies({'set-cookie': 'good=1\nbroken\n=novalue'})
    assert [c['name'] for c in cookies] == ['good']
