"""Deterministic unit tests for BiDiHarRecorder's BiDi-specific conversions.

The full event->entry->body flow needs a real browser (tests/bidi/integration),
but the pure conversions — unwrapping BytesValue headers and mapping BiDi's
absolute-millisecond FetchTimingInfo to HAR phase durations — are exercised here.
"""

from __future__ import annotations

from pydoll.browser.requests.bidi.har_recorder import BiDiHarRecorder


def _bytes(value: str) -> dict:
    return {'type': 'string', 'value': value}


def test_headers_to_dict_unwraps_bytes_value():
    headers = [
        {'name': 'Content-Type', 'value': _bytes('application/json')},
        {'name': 'X-Custom', 'value': _bytes('v')},
    ]
    assert BiDiHarRecorder._headers_to_dict(headers) == {
        'Content-Type': 'application/json',
        'X-Custom': 'v',
    }


def test_headers_to_dict_joins_duplicate_set_cookie_with_newline():
    headers = [
        {'name': 'Set-Cookie', 'value': _bytes('a=1')},
        {'name': 'Set-Cookie', 'value': _bytes('b=2')},
    ]
    assert BiDiHarRecorder._headers_to_dict(headers)['Set-Cookie'] == 'a=1\nb=2'


def test_build_har_timings_maps_fetch_timing_phases():
    recorder = BiDiHarRecorder(tab=None)
    timing = {
        'requestTime': 1000.0,
        'fetchStart': 1005.0,
        'dnsStart': 1005.0,
        'dnsEnd': 1010.0,
        'connectStart': 1010.0,
        'connectEnd': 1012.0,
        'tlsStart': 0,
        'tlsEnd': 1012.0,
        'requestStart': 1015.0,
        'responseStart': 1020.0,
        'responseEnd': 1025.0,
    }
    timings = recorder._build_har_timings({'timing': timing})
    assert timings['blocked'] == 5
    assert timings['dns'] == 5
    assert timings['connect'] == 2
    assert timings['ssl'] == -1  # tlsStart == 0 -> unavailable
    assert timings['send'] == 3
    assert timings['wait'] == 5
    assert timings['receive'] == 5


def test_build_har_timings_without_timing_is_all_unavailable():
    recorder = BiDiHarRecorder(tab=None)
    timings = recorder._build_har_timings({})
    assert timings['blocked'] == -1
    assert timings['dns'] == -1
    assert timings['send'] == 0
    assert timings['receive'] == 0
