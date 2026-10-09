"""Deterministic unit tests for BiDiHarRecorder's BiDi-specific conversions.

The full event->entry->body flow needs a real browser (tests/bidi/integration),
but the pure conversions — unwrapping BytesValue headers and mapping BiDi's
absolute-millisecond FetchTimingInfo to HAR phase durations — are exercised here.
"""

from __future__ import annotations

import asyncio

import pytest

from pydoll.browser.requests.bidi.har_recorder import BiDiHarRecorder


def _bytes(value: str) -> dict:
    return {'type': 'string', 'value': value}


def _request_event(request_id: str, url: str) -> dict:
    return {'params': {
        'timestamp': 1_700_000_000_000,
        'request': {
            'request': request_id, 'url': url, 'method': 'GET',
            'headers': [{'name': 'Accept', 'value': _bytes('text/html')}],
            'timings': {},
        },
    }}


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


@pytest.mark.asyncio
async def test_before_request_sent_opens_pending_and_builds_request(fake_bidi_tab):
    recorder = BiDiHarRecorder(fake_bidi_tab)
    recorder._on_before_request_sent(_request_event('r1', 'http://x/a'))
    assert 'r1' in recorder._pending
    entry = recorder._build_entry(recorder._pending['r1'])
    assert entry['request']['url'] == 'http://x/a'
    assert entry['request']['method'] == 'GET'
    assert any(h['name'] == 'Accept' for h in entry['request']['headers'])


@pytest.mark.asyncio
async def test_fetch_error_records_failed_entry(fake_bidi_tab):
    recorder = BiDiHarRecorder(fake_bidi_tab)
    recorder._on_before_request_sent(_request_event('r1', 'http://x/a'))
    recorder._on_fetch_error({'params': {'request': {'request': 'r1'}, 'errorText': 'boom'}})
    assert len(recorder._entries) == 1
    assert recorder._entries[0]['response']['status'] == 0


@pytest.mark.asyncio
async def test_response_completed_fetches_body_and_finalizes(fake_bidi_conn, fake_bidi_tab):
    recorder = BiDiHarRecorder(fake_bidi_tab)
    recorder._collector_id = 'col-1'
    recorder._on_before_request_sent(_request_event('r1', 'http://x/a'))
    fake_bidi_conn.set_result('network.getData', {'bytes': _bytes('hello body')})
    recorder._on_response_completed({'params': {
        'request': {'request': 'r1', 'timings': {}},
        'response': {
            'status': 200, 'statusText': 'OK',
            'headers': [{'name': 'Content-Type', 'value': _bytes('text/plain')}],
            'mimeType': 'text/plain', 'protocol': 'http/1.1', 'bodySize': 10,
        },
    }})
    await asyncio.gather(*recorder._body_tasks)

    assert len(recorder._entries) == 1
    entry = recorder._entries[0]
    assert entry['response']['status'] == 200
    assert entry['response']['content']['text'] == 'hello body'


@pytest.mark.asyncio
async def test_teardown_removes_collector(fake_bidi_conn, fake_bidi_tab):
    recorder = BiDiHarRecorder(fake_bidi_tab)
    recorder._collector_id = 'col-1'
    await recorder._teardown()
    assert fake_bidi_conn.commands_for('network.removeDataCollector')
    assert recorder._collector_id is None
