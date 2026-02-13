"""Tests for pydoll.browser.requests.har_recorder module."""

import json
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from pydoll.browser.requests.har_recorder import HarRecorder, HarCapture
from pydoll.browser.requests.request import Request
from pydoll.exceptions import HarReplayError
from pydoll.protocol.network.events import NetworkEvent


@pytest_asyncio.fixture
async def mock_tab():
    """Create a mock Tab instance for testing."""
    tab = Mock()
    tab.network_events_enabled = False
    tab.enable_network_events = AsyncMock()
    tab.disable_network_events = AsyncMock()
    tab.on = AsyncMock(side_effect=lambda *a, **kw: len(tab.on.call_args_list))
    tab.remove_callback = AsyncMock()
    tab.clear_callbacks = AsyncMock()
    tab._execute_command = AsyncMock(
        return_value={'result': {'body': '', 'base64Encoded': False}}
    )
    return tab


@pytest_asyncio.fixture
async def recorder(mock_tab):
    """Create a HarRecorder instance for testing."""
    return HarRecorder(mock_tab)


@pytest_asyncio.fixture
async def request_instance(mock_tab):
    """Create a Request instance for testing."""
    return Request(mock_tab)


def _make_request_will_be_sent_event(
    request_id='req-1',
    url='https://example.com',
    method='GET',
    wall_time=1700000000.0,
    resource_type='Document',
    redirect_response=None,
):
    """Helper to build a requestWillBeSent CDP event."""
    event = {
        'method': NetworkEvent.REQUEST_WILL_BE_SENT,
        'params': {
            'requestId': request_id,
            'request': {
                'url': url,
                'method': method,
                'headers': {'User-Agent': 'TestBrowser'},
            },
            'wallTime': wall_time,
            'timestamp': 12345.0,
            'type': resource_type,
            'loaderId': 'loader-1',
            'documentURL': url,
            'initiator': {'type': 'other'},
            'redirectHasExtraInfo': False,
        },
    }
    if redirect_response:
        event['params']['redirectResponse'] = redirect_response
    return event


def _make_request_extra_info_event(request_id='req-1'):
    """Helper to build a requestWillBeSentExtraInfo CDP event."""
    return {
        'method': NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO,
        'params': {
            'requestId': request_id,
            'headers': {'Cookie': 'session=abc123'},
            'associatedCookies': [],
            'connectTiming': {'requestTime': 12345.0},
        },
    }


def _make_response_received_event(
    request_id='req-1',
    status=200,
    status_text='OK',
    mime_type='text/html',
    protocol='h2',
    timing=None,
    remote_ip='93.184.216.34',
):
    """Helper to build a responseReceived CDP event."""
    response = {
        'url': 'https://example.com',
        'status': status,
        'statusText': status_text,
        'headers': {'Content-Type': 'text/html'},
        'mimeType': mime_type,
        'charset': 'utf-8',
        'connectionReused': False,
        'connectionId': 42,
        'encodedDataLength': 1234,
        'securityState': 'secure',
    }
    if protocol:
        response['protocol'] = protocol
    if timing:
        response['timing'] = timing
    if remote_ip:
        response['remoteIPAddress'] = remote_ip
    return {
        'method': NetworkEvent.RESPONSE_RECEIVED,
        'params': {
            'requestId': request_id,
            'loaderId': 'loader-1',
            'timestamp': 12346.0,
            'type': 'Document',
            'response': response,
            'hasExtraInfo': True,
        },
    }


def _make_response_extra_info_event(request_id='req-1'):
    """Helper to build a responseReceivedExtraInfo CDP event."""
    return {
        'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
        'params': {
            'requestId': request_id,
            'headers': {'Content-Type': 'text/html', 'Set-Cookie': 'id=val'},
            'blockedCookies': [],
            'resourceIPAddressSpace': 'Public',
            'statusCode': 200,
        },
    }


def _make_data_received_event(request_id='req-1', encoded_data_length=500):
    """Helper to build a dataReceived CDP event."""
    return {
        'method': NetworkEvent.DATA_RECEIVED,
        'params': {
            'requestId': request_id,
            'timestamp': 12346.5,
            'dataLength': encoded_data_length,
            'encodedDataLength': encoded_data_length,
        },
    }


def _make_loading_finished_event(request_id='req-1', encoded_data_length=1234):
    """Helper to build a loadingFinished CDP event."""
    return {
        'method': NetworkEvent.LOADING_FINISHED,
        'params': {
            'requestId': request_id,
            'timestamp': 12347.0,
            'encodedDataLength': float(encoded_data_length),
        },
    }


def _make_loading_failed_event(
    request_id='req-1', error_text='net::ERR_FAILED', canceled=False
):
    """Helper to build a loadingFailed CDP event."""
    return {
        'method': NetworkEvent.LOADING_FAILED,
        'params': {
            'requestId': request_id,
            'timestamp': 12347.0,
            'type': 'Document',
            'errorText': error_text,
            'canceled': canceled,
        },
    }


class TestHarRecorderStart:
    """Test HarRecorder.start()."""

    @pytest.mark.asyncio
    async def test_start_registers_six_callbacks(self, recorder, mock_tab):
        await recorder.start()
        assert mock_tab.on.call_count == 7

    @pytest.mark.asyncio
    async def test_start_stores_callback_ids(self, recorder, mock_tab):
        await recorder.start()
        assert len(recorder._callback_ids) == 7

    @pytest.mark.asyncio
    async def test_start_enables_network_events_if_not_enabled(self, recorder, mock_tab):
        mock_tab.network_events_enabled = False
        await recorder.start()
        mock_tab.enable_network_events.assert_called_once()
        assert recorder._network_was_enabled is True

    @pytest.mark.asyncio
    async def test_start_skips_network_enable_if_already_enabled(self, recorder, mock_tab):
        mock_tab.network_events_enabled = True
        await recorder.start()
        mock_tab.enable_network_events.assert_not_called()
        assert recorder._network_was_enabled is False

    @pytest.mark.asyncio
    async def test_start_registers_correct_events(self, recorder, mock_tab):
        await recorder.start()
        registered_events = [call.args[0] for call in mock_tab.on.call_args_list]
        assert NetworkEvent.REQUEST_WILL_BE_SENT in registered_events
        assert NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO in registered_events
        assert NetworkEvent.RESPONSE_RECEIVED in registered_events
        assert NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO in registered_events
        assert NetworkEvent.DATA_RECEIVED in registered_events
        assert NetworkEvent.LOADING_FINISHED in registered_events
        assert NetworkEvent.LOADING_FAILED in registered_events

    @pytest.mark.asyncio
    async def test_start_sets_start_time(self, recorder, mock_tab):
        assert recorder._start_time is None
        await recorder.start()
        assert recorder._start_time is not None


class TestHarRecorderStop:
    """Test HarRecorder.stop()."""

    @pytest.mark.asyncio
    async def test_stop_removes_all_callbacks(self, recorder, mock_tab):
        await recorder.start()
        await recorder.stop()
        assert mock_tab.remove_callback.call_count == 7

    @pytest.mark.asyncio
    async def test_stop_clears_callback_ids(self, recorder, mock_tab):
        await recorder.start()
        await recorder.stop()
        assert recorder._callback_ids == []

    @pytest.mark.asyncio
    async def test_stop_disables_network_events_if_we_enabled(self, recorder, mock_tab):
        mock_tab.network_events_enabled = False
        await recorder.start()
        await recorder.stop()
        mock_tab.disable_network_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_does_not_disable_network_events_if_not_ours(self, recorder, mock_tab):
        mock_tab.network_events_enabled = True
        await recorder.start()
        await recorder.stop()
        mock_tab.disable_network_events.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_flushes_pending_entries(self, recorder, mock_tab):
        await recorder.start()
        recorder._pending['req-1'] = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
        }
        await recorder.stop()
        assert len(recorder._entries) == 1
        assert recorder._pending == {}


class TestHarRecorderEventHandlers:
    """Test individual event handler methods."""

    @pytest.mark.asyncio
    async def test_request_will_be_sent_creates_pending(self, recorder):
        event = _make_request_will_be_sent_event()
        recorder._on_request_will_be_sent(event)
        assert 'req-1' in recorder._pending
        assert recorder._pending['req-1']['url'] == 'https://example.com'
        assert recorder._pending['req-1']['method'] == 'GET'

    @pytest.mark.asyncio
    async def test_request_extra_info_merges_headers(self, recorder):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_request_extra_info(_make_request_extra_info_event())
        assert 'request_headers_extra' in recorder._pending['req-1']
        assert recorder._pending['req-1']['request_headers_extra']['Cookie'] == 'session=abc123'

    @pytest.mark.asyncio
    async def test_request_extra_info_skips_unknown_request(self, recorder):
        recorder._on_request_extra_info(_make_request_extra_info_event('unknown-req'))
        assert 'unknown-req' not in recorder._pending

    @pytest.mark.asyncio
    async def test_response_received_stores_data(self, recorder):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_received(_make_response_received_event())
        pending = recorder._pending['req-1']
        assert pending['status'] == 200
        assert pending['status_text'] == 'OK'
        assert pending['mime_type'] == 'text/html'
        assert pending['protocol'] == 'h2'
        assert pending['remote_ip'] == '93.184.216.34'

    @pytest.mark.asyncio
    async def test_response_received_skips_unknown_request(self, recorder):
        recorder._on_response_received(_make_response_received_event('unknown-req'))
        assert 'unknown-req' not in recorder._pending

    @pytest.mark.asyncio
    async def test_response_extra_info_merges_headers(self, recorder):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_extra_info(_make_response_extra_info_event())
        assert 'response_headers_extra' in recorder._pending['req-1']

    @pytest.mark.asyncio
    async def test_loading_finished_creates_entry(self, recorder, mock_tab):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_received(_make_response_received_event())
        recorder._on_loading_finished(_make_loading_finished_event())

        # Wait for the background task to complete
        if recorder._body_tasks:
            import asyncio
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert len(recorder._entries) == 1
        assert 'req-1' not in recorder._pending
        entry = recorder._entries[0]
        assert entry['request']['url'] == 'https://example.com'
        assert entry['response']['status'] == 200

    @pytest.mark.asyncio
    async def test_loading_finished_skips_unknown_request(self, recorder):
        recorder._on_loading_finished(_make_loading_finished_event('unknown-req'))
        assert len(recorder._entries) == 0

    @pytest.mark.asyncio
    async def test_loading_failed_creates_entry(self, recorder):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_loading_failed(_make_loading_failed_event())
        assert len(recorder._entries) == 1
        assert 'req-1' not in recorder._pending
        entry = recorder._entries[0]
        assert entry['response']['status'] == 0
        assert entry['response']['statusText'] == 'net::ERR_FAILED'

    @pytest.mark.asyncio
    async def test_loading_failed_skips_unknown_request(self, recorder):
        recorder._on_loading_failed(_make_loading_failed_event('unknown-req'))
        assert len(recorder._entries) == 0

    @pytest.mark.asyncio
    async def test_redirect_handling(self, recorder, mock_tab):
        redirect_response = {
            'url': 'https://example.com',
            'status': 301,
            'statusText': 'Moved Permanently',
            'headers': {'Location': 'https://www.example.com'},
            'mimeType': 'text/html',
            'charset': 'utf-8',
            'connectionReused': False,
            'connectionId': 42,
            'encodedDataLength': 200,
            'securityState': 'secure',
        }
        event1 = _make_request_will_be_sent_event(request_id='req-1')
        recorder._on_request_will_be_sent(event1)

        event2 = _make_request_will_be_sent_event(
            request_id='req-1',
            url='https://www.example.com',
            redirect_response=redirect_response,
        )
        recorder._on_request_will_be_sent(event2)

        # First entry is the redirect
        assert len(recorder._entries) == 1
        assert recorder._entries[0]['response']['status'] == 301

        # req-1 still pending for the final URL
        assert 'req-1' in recorder._pending
        assert recorder._pending['req-1']['url'] == 'https://www.example.com'


class TestHarRecorderHelpers:
    """Test static helper methods."""

    def test_headers_dict_to_list(self):
        headers = {'Content-Type': 'text/html', 'Accept': '*/*'}
        result = HarRecorder._headers_dict_to_list(headers)
        assert len(result) == 2
        assert {'name': 'Content-Type', 'value': 'text/html'} in result
        assert {'name': 'Accept', 'value': '*/*'} in result

    def test_headers_dict_to_list_empty(self):
        assert HarRecorder._headers_dict_to_list({}) == []

    def test_parse_query_string(self):
        url = 'https://example.com/search?q=test&page=1'
        result = HarRecorder._parse_query_string(url)
        assert len(result) == 2
        names = [p['name'] for p in result]
        assert 'q' in names
        assert 'page' in names

    def test_parse_query_string_no_query(self):
        assert HarRecorder._parse_query_string('https://example.com') == []

    def test_parse_query_string_empty_values(self):
        url = 'https://example.com?flag='
        result = HarRecorder._parse_query_string(url)
        assert len(result) == 1
        assert result[0]['name'] == 'flag'
        assert result[0]['value'] == ''

    def test_wall_time_to_iso(self):
        result = HarRecorder._wall_time_to_iso(1700000000.0)
        assert '2023-11-14' in result
        assert '+00:00' in result or 'Z' in result

    def test_wall_time_to_iso_zero(self):
        result = HarRecorder._wall_time_to_iso(0)
        # Should return current time ISO string
        assert 'T' in result

    def test_build_har_timings_none(self):
        result = HarRecorder._build_har_timings(None)
        assert result['blocked'] == -1
        assert result['dns'] == -1
        assert result['connect'] == -1
        assert result['ssl'] == -1
        assert result['send'] == 0
        assert result['wait'] == 0
        assert result['receive'] == 0

    def test_build_har_timings_with_data(self):
        timing = {
            'requestTime': 12345.0,
            'proxyStart': -1,
            'proxyEnd': -1,
            'dnsStart': 0.5,
            'dnsEnd': 5.0,
            'connectStart': 5.0,
            'connectEnd': 50.0,
            'sslStart': 10.0,
            'sslEnd': 45.0,
            'workerStart': -1,
            'workerReady': -1,
            'workerFetchStart': -1,
            'workerRespondWithSettled': -1,
            'sendStart': 50.0,
            'sendEnd': 51.0,
            'pushStart': 0,
            'pushEnd': 0,
            'receiveHeadersStart': 100.0,
            'receiveHeadersEnd': 105.0,
        }
        result = HarRecorder._build_har_timings(timing)
        assert result['dns'] == 4.5
        assert result['connect'] == 45.0
        assert result['ssl'] == 35.0
        assert result['send'] == 1.0
        assert result['wait'] == 49.0
        # receive defaults to 0 when no receive_ms is provided
        assert result['receive'] == 0

    def test_build_har_timings_with_receive_ms(self):
        timing = {
            'requestTime': 12345.0,
            'proxyStart': -1,
            'proxyEnd': -1,
            'dnsStart': 0.5,
            'dnsEnd': 5.0,
            'connectStart': 5.0,
            'connectEnd': 50.0,
            'sslStart': 10.0,
            'sslEnd': 45.0,
            'workerStart': -1,
            'workerReady': -1,
            'workerFetchStart': -1,
            'workerRespondWithSettled': -1,
            'sendStart': 50.0,
            'sendEnd': 51.0,
            'pushStart': 0,
            'pushEnd': 0,
            'receiveHeadersStart': 100.0,
            'receiveHeadersEnd': 105.0,
        }
        # Providing receive_ms overrides any header-based calculation
        result = HarRecorder._build_har_timings(timing, receive_ms=250.5)
        assert result['receive'] == 250.5
        assert result['dns'] == 4.5
        assert result['send'] == 1.0

    def test_build_har_timings_no_ssl(self):
        timing = {
            'requestTime': 12345.0,
            'proxyStart': -1,
            'proxyEnd': -1,
            'dnsStart': -1,
            'dnsEnd': -1,
            'connectStart': -1,
            'connectEnd': -1,
            'sslStart': -1,
            'sslEnd': -1,
            'workerStart': -1,
            'workerReady': -1,
            'workerFetchStart': -1,
            'workerRespondWithSettled': -1,
            'sendStart': 10.0,
            'sendEnd': 11.0,
            'pushStart': 0,
            'pushEnd': 0,
            'receiveHeadersStart': 50.0,
            'receiveHeadersEnd': 55.0,
        }
        result = HarRecorder._build_har_timings(timing, receive_ms=500.0)
        assert result['dns'] == -1
        assert result['connect'] == -1
        assert result['ssl'] == -1
        assert result['send'] == 1.0
        assert result['wait'] == 39.0
        assert result['receive'] == 500.0


class TestHarRecorderBuildEntry:
    """Test the entry building logic."""

    @pytest.mark.asyncio
    async def test_build_entry_basic(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {'User-Agent': 'Test'},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {'Content-Type': 'text/html'},
            'mime_type': 'text/html',
            'protocol': 'h2',
        }
        entry = recorder._build_entry(pending)
        assert entry['request']['method'] == 'GET'
        assert entry['request']['url'] == 'https://example.com'
        assert entry['response']['status'] == 200

    @pytest.mark.asyncio
    async def test_build_entry_with_post_data(self, recorder):
        pending = {
            'url': 'https://example.com/api',
            'method': 'POST',
            'request_headers': {'Content-Type': 'application/json'},
            'post_data': '{"key": "value"}',
            'wall_time': 1700000000.0,
            'status': 201,
            'status_text': 'Created',
            'response_headers': {},
            'mime_type': 'application/json',
            'protocol': 'h2',
        }
        entry = recorder._build_entry(pending)
        assert 'postData' in entry['request']
        assert entry['request']['postData']['text'] == '{"key": "value"}'
        assert entry['request']['postData']['mimeType'] == 'application/json'
        assert entry['request']['bodySize'] == len('{"key": "value"}')

    @pytest.mark.asyncio
    async def test_build_entry_with_response_body(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'protocol': 'h2',
            'response_body': '<html></html>',
            'response_body_base64': False,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['content']['text'] == '<html></html>'
        assert 'encoding' not in entry['response']['content']

    @pytest.mark.asyncio
    async def test_build_entry_with_base64_body(self, recorder):
        pending = {
            'url': 'https://example.com/image.png',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'image/png',
            'protocol': 'h2',
            'response_body': 'iVBORw0KGgo=',
            'response_body_base64': True,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['content']['encoding'] == 'base64'

    @pytest.mark.asyncio
    async def test_build_entry_with_server_ip(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'remote_ip': '93.184.216.34',
        }
        entry = recorder._build_entry(pending)
        assert entry['serverIPAddress'] == '93.184.216.34'

    @pytest.mark.asyncio
    async def test_build_entry_with_resource_type(self, recorder):
        pending = {
            'url': 'https://example.com/style.css',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/css',
            'resource_type': 'Stylesheet',
        }
        entry = recorder._build_entry(pending)
        assert entry['_resourceType'] == 'Stylesheet'

    @pytest.mark.asyncio
    async def test_build_entry_uses_extra_headers_when_available(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {'User-Agent': 'original'},
            'request_headers_extra': {'User-Agent': 'actual', 'Cookie': 'x=1'},
            'response_headers': {'Content-Type': 'text/html'},
            'response_headers_extra': {'Content-Type': 'text/html', 'Set-Cookie': 'y=2'},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        req_header_names = [h['name'] for h in entry['request']['headers']]
        assert 'Cookie' in req_header_names
        resp_header_names = [h['name'] for h in entry['response']['headers']]
        assert 'Set-Cookie' in resp_header_names


class TestHarCapture:
    """Test HarCapture user-facing class."""

    @pytest.mark.asyncio
    async def test_entries_returns_copy(self, recorder):
        recorder._entries.append(
            {
                'startedDateTime': '2023-01-01T00:00:00+00:00',
                'time': 100.0,
                'request': {},
                'response': {},
                'timings': {},
            }
        )
        recording = HarCapture(recorder)
        entries = recording.entries
        assert len(entries) == 1
        entries.clear()
        # Original entries should not be affected
        assert len(recording.entries) == 1

    @pytest.mark.asyncio
    async def test_to_dict_structure(self, recorder):
        recording = HarCapture(recorder)
        har = recording.to_dict()
        assert 'log' in har
        assert har['log']['version'] == '1.2'
        assert har['log']['creator']['name'] == 'pydoll'
        assert isinstance(har['log']['pages'], list)
        assert isinstance(har['log']['entries'], list)

    @pytest.mark.asyncio
    async def test_to_dict_includes_entries(self, recorder):
        recorder._entries.append(
            {
                'startedDateTime': '2023-01-01T00:00:00+00:00',
                'time': 100.0,
                'request': {'method': 'GET', 'url': 'https://example.com'},
                'response': {'status': 200},
                'timings': {},
            }
        )
        recording = HarCapture(recorder)
        har = recording.to_dict()
        assert len(har['log']['entries']) == 1

    @pytest.mark.asyncio
    async def test_save_writes_json_file(self, recorder, tmp_path):
        recorder._entries.append(
            {
                'startedDateTime': '2023-01-01T00:00:00+00:00',
                'time': 100.0,
                'request': {'method': 'GET', 'url': 'https://example.com'},
                'response': {'status': 200},
                'timings': {},
            }
        )
        recording = HarCapture(recorder)
        file_path = tmp_path / 'test.har'
        recording.save(file_path)

        assert file_path.exists()
        with open(file_path) as f:
            data = json.load(f)
        assert data['log']['version'] == '1.2'
        assert len(data['log']['entries']) == 1

    @pytest.mark.asyncio
    async def test_save_with_string_path(self, recorder, tmp_path):
        recording = HarCapture(recorder)
        file_path = str(tmp_path / 'test.har')
        recording.save(file_path)
        assert Path(file_path).exists()

    @pytest.mark.asyncio
    async def test_save_creates_parent_directories(self, recorder, tmp_path):
        recording = HarCapture(recorder)
        file_path = tmp_path / 'sub' / 'dir' / 'test.har'
        recording.save(file_path)
        assert file_path.exists()


class TestRequestRecord:
    """Test Request.record() context manager."""

    @pytest.mark.asyncio
    async def test_record_yields_har_recording(self, request_instance):
        async with request_instance.record() as recording:
            assert isinstance(recording, HarCapture)

    @pytest.mark.asyncio
    async def test_record_enables_network_events(self, request_instance, mock_tab):
        mock_tab.network_events_enabled = False
        async with request_instance.record():
            pass
        mock_tab.enable_network_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_registers_and_removes_callbacks(self, request_instance, mock_tab):
        async with request_instance.record():
            assert mock_tab.on.call_count == 7
        assert mock_tab.remove_callback.call_count == 7

    @pytest.mark.asyncio
    async def test_record_cleans_up_on_exception(self, request_instance, mock_tab):
        with pytest.raises(ValueError, match='test error'):
            async with request_instance.record():
                raise ValueError('test error')
        # Cleanup should still happen
        assert mock_tab.remove_callback.call_count == 7

    @pytest.mark.asyncio
    async def test_record_disables_network_events_if_enabled_by_recorder(
        self, request_instance, mock_tab
    ):
        mock_tab.network_events_enabled = False
        async with request_instance.record():
            pass
        mock_tab.disable_network_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_does_not_disable_network_events_if_already_enabled(
        self, request_instance, mock_tab
    ):
        mock_tab.network_events_enabled = True
        async with request_instance.record():
            pass
        mock_tab.disable_network_events.assert_not_called()


class TestResourceTypeFiltering:
    """Test resource type filtering in HarRecorder."""

    @pytest.mark.asyncio
    async def test_filter_skips_non_matching_types(self, mock_tab):
        from pydoll.protocol.network.types import ResourceType
        recorder = HarRecorder(mock_tab, resource_types=[ResourceType.FETCH])
        await recorder.start()

        event = {
            'params': {
                'requestId': 'req1',
                'request': {'url': 'https://example.com', 'method': 'GET', 'headers': {}},
                'wallTime': 1000.0,
                'timestamp': 100.0,
                'type': 'Document',
            }
        }
        recorder._on_request_will_be_sent(event)
        assert 'req1' not in recorder._pending

    @pytest.mark.asyncio
    async def test_filter_accepts_matching_types(self, mock_tab):
        from pydoll.protocol.network.types import ResourceType
        recorder = HarRecorder(mock_tab, resource_types=[ResourceType.FETCH])
        await recorder.start()

        event = {
            'params': {
                'requestId': 'req1',
                'request': {'url': 'https://example.com/api', 'method': 'GET', 'headers': {}},
                'wallTime': 1000.0,
                'timestamp': 100.0,
                'type': 'Fetch',
            }
        }
        recorder._on_request_will_be_sent(event)
        assert 'req1' in recorder._pending

    @pytest.mark.asyncio
    async def test_no_filter_accepts_all(self, mock_tab):
        recorder = HarRecorder(mock_tab)
        await recorder.start()

        event = {
            'params': {
                'requestId': 'req1',
                'request': {'url': 'https://example.com', 'method': 'GET', 'headers': {}},
                'wallTime': 1000.0,
                'timestamp': 100.0,
                'type': 'Document',
            }
        }
        recorder._on_request_will_be_sent(event)
        assert 'req1' in recorder._pending

    @pytest.mark.asyncio
    async def test_record_passes_resource_types(self, request_instance, mock_tab):
        from pydoll.protocol.network.types import ResourceType
        async with request_instance.record(
            resource_types=[ResourceType.XHR, ResourceType.FETCH]
        ) as capture:
            assert isinstance(capture, HarCapture)


class TestRequestReplay:
    """Test Request.replay() method."""

    @pytest.mark.asyncio
    async def test_replay_sends_requests(self, request_instance, mock_tab, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [
                    {
                        'request': {
                            'method': 'GET',
                            'url': 'https://example.com',
                            'headers': [{'name': 'Accept', 'value': 'text/html'}],
                        },
                        'response': {'status': 200},
                    }
                ],
            }
        }
        file_path = tmp_path / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            responses = await request_instance.replay(file_path)
            assert len(responses) == 1
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.kwargs['method'] == 'GET'
            assert call_args.kwargs['url'] == 'https://example.com'

    @pytest.mark.asyncio
    async def test_replay_preserves_method_and_headers(self, request_instance, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [
                    {
                        'request': {
                            'method': 'POST',
                            'url': 'https://example.com/api',
                            'headers': [
                                {'name': 'Content-Type', 'value': 'application/json'},
                                {'name': 'Authorization', 'value': 'Bearer token123'},
                            ],
                        },
                        'response': {'status': 201},
                    }
                ],
            }
        }
        file_path = tmp_path / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            await request_instance.replay(file_path)
            call_args = mock_request.call_args
            assert call_args.kwargs['method'] == 'POST'
            headers = call_args.kwargs['headers']
            assert len(headers) == 2
            header_names = [h['name'] for h in headers]
            assert 'Content-Type' in header_names
            assert 'Authorization' in header_names

    @pytest.mark.asyncio
    async def test_replay_with_post_data(self, request_instance, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [
                    {
                        'request': {
                            'method': 'POST',
                            'url': 'https://example.com/api',
                            'headers': [],
                            'postData': {
                                'mimeType': 'application/json',
                                'text': '{"key": "value"}',
                            },
                        },
                        'response': {'status': 201},
                    }
                ],
            }
        }
        file_path = tmp_path / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            await request_instance.replay(file_path)
            call_args = mock_request.call_args
            assert call_args.kwargs['data'] == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_replay_invalid_har_file(self, request_instance, tmp_path):
        file_path = tmp_path / 'invalid.har'
        with open(file_path, 'w') as f:
            f.write('not valid json')

        with pytest.raises(HarReplayError, match='Failed to read HAR file'):
            await request_instance.replay(file_path)

    @pytest.mark.asyncio
    async def test_replay_nonexistent_file(self, request_instance, tmp_path):
        file_path = tmp_path / 'nonexistent.har'
        with pytest.raises(HarReplayError, match='Failed to read HAR file'):
            await request_instance.replay(file_path)

    @pytest.mark.asyncio
    async def test_replay_empty_entries(self, request_instance, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [],
            }
        }
        file_path = tmp_path / 'empty.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            responses = await request_instance.replay(file_path)
            assert responses == []
            mock_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_replay_skips_entries_without_url(self, request_instance, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [
                    {
                        'request': {'method': 'GET', 'url': '', 'headers': []},
                        'response': {'status': 200},
                    },
                    {
                        'request': {
                            'method': 'GET',
                            'url': 'https://example.com',
                            'headers': [],
                        },
                        'response': {'status': 200},
                    },
                ],
            }
        }
        file_path = tmp_path / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            responses = await request_instance.replay(file_path)
            assert len(responses) == 1

    @pytest.mark.asyncio
    async def test_replay_invalid_entries_type(self, request_instance, tmp_path):
        har_data = {'log': {'entries': 'not-a-list'}}
        file_path = tmp_path / 'invalid.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with pytest.raises(HarReplayError, match='entries is not a list'):
            await request_instance.replay(file_path)

    @pytest.mark.asyncio
    async def test_replay_multiple_entries(self, request_instance, tmp_path):
        entries = [
            {
                'request': {
                    'method': 'GET',
                    'url': f'https://example.com/page{i}',
                    'headers': [],
                },
                'response': {'status': 200},
            }
            for i in range(3)
        ]
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': entries,
            }
        }
        file_path = tmp_path / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            responses = await request_instance.replay(file_path)
            assert len(responses) == 3
            assert mock_request.call_count == 3

    @pytest.mark.asyncio
    async def test_replay_with_path_object(self, request_instance, tmp_path):
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'test', 'version': '1.0'},
                'pages': [],
                'entries': [],
            }
        }
        file_path = Path(tmp_path) / 'test.har'
        with open(file_path, 'w') as f:
            json.dump(har_data, f)

        with patch.object(request_instance, 'request', new_callable=AsyncMock):
            responses = await request_instance.replay(file_path)
            assert responses == []


class TestHarRecorderFetchResponseBody:
    """Test response body fetching."""

    @pytest.mark.asyncio
    async def test_fetch_response_body_success(self, recorder, mock_tab):
        mock_tab._execute_command.return_value = {
            'result': {'body': '<html>Hello</html>', 'base64Encoded': False}
        }
        body, is_base64 = await recorder._fetch_response_body('req-1')
        assert body == '<html>Hello</html>'
        assert is_base64 is False

    @pytest.mark.asyncio
    async def test_fetch_response_body_base64(self, recorder, mock_tab):
        mock_tab._execute_command.return_value = {
            'result': {'body': 'aW1hZ2VkYXRh', 'base64Encoded': True}
        }
        body, is_base64 = await recorder._fetch_response_body('req-1')
        assert body == 'aW1hZ2VkYXRh'
        assert is_base64 is True

    @pytest.mark.asyncio
    async def test_fetch_response_body_failure(self, recorder, mock_tab):
        mock_tab._execute_command.side_effect = Exception('Network error')
        body, is_base64 = await recorder._fetch_response_body('req-1')
        assert body == ''
        assert is_base64 is False


class TestHarRecorderEndToEnd:
    """End-to-end tests simulating full request lifecycle."""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self, recorder, mock_tab):
        mock_tab._execute_command.return_value = {
            'result': {'body': '<html>Test</html>', 'base64Encoded': False}
        }

        # Simulate a full request lifecycle
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_request_extra_info(_make_request_extra_info_event())
        recorder._on_response_received(_make_response_received_event())
        recorder._on_response_extra_info(_make_response_extra_info_event())
        recorder._on_loading_finished(_make_loading_finished_event())

        # Wait for async body fetch
        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert len(recorder._entries) == 1
        entry = recorder._entries[0]
        assert entry['request']['method'] == 'GET'
        assert entry['request']['url'] == 'https://example.com'
        assert entry['response']['status'] == 200
        assert entry['response']['content']['text'] == '<html>Test</html>'
        assert entry['_resourceType'] == 'Document'
        assert entry['serverIPAddress'] == '93.184.216.34'
        # Extra headers should be preferred
        req_headers = {h['name']: h['value'] for h in entry['request']['headers']}
        assert 'Cookie' in req_headers

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, recorder, mock_tab):
        mock_tab._execute_command.return_value = {
            'result': {'body': '', 'base64Encoded': False}
        }

        # Two concurrent requests
        recorder._on_request_will_be_sent(
            _make_request_will_be_sent_event('req-1', 'https://example.com/a')
        )
        recorder._on_request_will_be_sent(
            _make_request_will_be_sent_event('req-2', 'https://example.com/b')
        )
        recorder._on_response_received(_make_response_received_event('req-1'))
        recorder._on_response_received(_make_response_received_event('req-2'))
        recorder._on_loading_finished(_make_loading_finished_event('req-1'))
        recorder._on_loading_finished(_make_loading_finished_event('req-2'))

        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert len(recorder._entries) == 2
        urls = [e['request']['url'] for e in recorder._entries]
        assert 'https://example.com/a' in urls
        assert 'https://example.com/b' in urls


class TestHarRecorderCookieParsing:
    """Test cookie parsing from headers."""

    def test_parse_request_cookies(self):
        headers = {'Cookie': 'session=abc123; user=john; theme=dark'}
        result = HarRecorder._parse_request_cookies(headers)
        assert len(result) == 3
        names = [c['name'] for c in result]
        assert 'session' in names
        assert 'user' in names
        assert 'theme' in names

    def test_parse_request_cookies_empty(self):
        assert HarRecorder._parse_request_cookies({}) == []

    def test_parse_request_cookies_lowercase_header(self):
        headers = {'cookie': 'token=xyz'}
        result = HarRecorder._parse_request_cookies(headers)
        assert len(result) == 1
        assert result[0]['name'] == 'token'

    def test_parse_response_cookies(self):
        headers = {'Set-Cookie': 'id=val; Path=/; HttpOnly; Secure'}
        result = HarRecorder._parse_response_cookies(headers)
        assert len(result) == 1
        assert result[0]['name'] == 'id'
        assert result[0]['value'] == 'val'
        assert result[0].get('httpOnly') is True
        assert result[0].get('secure') is True
        assert result[0].get('path') == '/'

    def test_parse_response_cookies_multiple(self):
        headers = {'Set-Cookie': 'a=1; Path=/\nb=2; Domain=.example.com'}
        result = HarRecorder._parse_response_cookies(headers)
        assert len(result) == 2
        names = [c['name'] for c in result]
        assert 'a' in names
        assert 'b' in names

    def test_parse_response_cookies_empty(self):
        assert HarRecorder._parse_response_cookies({}) == []

    def test_parse_response_cookies_with_domain(self):
        headers = {'Set-Cookie': 'sess=abc; Domain=.example.com; Path=/api'}
        result = HarRecorder._parse_response_cookies(headers)
        assert len(result) == 1
        assert result[0].get('domain') == '.example.com'
        assert result[0].get('path') == '/api'


class TestHarRecorderBodySizes:
    """Test correct body size calculations."""

    @pytest.mark.asyncio
    async def test_response_body_size_uses_data_received_bytes(self, recorder):
        """bodySize should come from dataReceived chunks, not transfer_size."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'response_body': '<html>Hello</html>',
            'response_body_base64': False,
            'body_bytes': 3200,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['bodySize'] == 3200

    @pytest.mark.asyncio
    async def test_response_body_size_unknown_returns_negative_one(self, recorder):
        """bodySize should be -1 when no dataReceived data is available."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['bodySize'] == -1

    @pytest.mark.asyncio
    async def test_response_body_size_304_is_zero(self, recorder):
        """For 304 (cache hit), bodySize must be 0 per HAR spec."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 304,
            'status_text': 'Not Modified',
            'response_headers': {},
            'mime_type': 'text/html',
            'body_bytes': 100,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['bodySize'] == 0

    @pytest.mark.asyncio
    async def test_content_size_base64_decoded(self, recorder):
        import base64
        original = b'binary data here'
        b64_body = base64.b64encode(original).decode()
        pending = {
            'url': 'https://example.com/img.png',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'image/png',
            'response_body': b64_body,
            'response_body_base64': True,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['content']['size'] == len(original)
        assert entry['response']['content']['encoding'] == 'base64'

    @pytest.mark.asyncio
    async def test_request_body_size_bytes(self, recorder):
        pending = {
            'url': 'https://example.com/api',
            'method': 'POST',
            'request_headers': {'Content-Type': 'application/json'},
            'post_data': '{"emoji": "\u2764"}',
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'application/json',
        }
        entry = recorder._build_entry(pending)
        # UTF-8 encoded size, not len(str)
        expected = len('{"emoji": "\u2764"}'.encode('utf-8'))
        assert entry['request']['bodySize'] == expected


class TestHarRecorderCacheField:
    """Test that entries include the cache field."""

    @pytest.mark.asyncio
    async def test_entry_has_cache_field(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        assert 'cache' in entry
        assert entry['cache'] == {}


class TestHarRecorderCookiesInEntries:
    """Test that cookies are populated from headers in entries."""

    @pytest.mark.asyncio
    async def test_request_cookies_from_cookie_header(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {'Cookie': 'session=abc; user=john'},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        assert len(entry['request']['cookies']) == 2
        names = [c['name'] for c in entry['request']['cookies']]
        assert 'session' in names
        assert 'user' in names

    @pytest.mark.asyncio
    async def test_response_cookies_from_set_cookie(self, recorder):
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {'Set-Cookie': 'id=val; HttpOnly'},
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        assert len(entry['response']['cookies']) == 1
        assert entry['response']['cookies'][0]['name'] == 'id'
        assert entry['response']['cookies'][0].get('httpOnly') is True


class TestHarRecorderDataReceived:
    """Test Network.dataReceived handling for accurate bodySize."""

    def test_data_received_accumulates_bytes(self, recorder):
        recorder._on_data_received(_make_data_received_event('req-1', 500))
        recorder._on_data_received(_make_data_received_event('req-1', 300))
        assert recorder._data_received_sizes['req-1'] == 800

    def test_data_received_separate_requests(self, recorder):
        recorder._on_data_received(_make_data_received_event('req-1', 500))
        recorder._on_data_received(_make_data_received_event('req-2', 700))
        assert recorder._data_received_sizes['req-1'] == 500
        assert recorder._data_received_sizes['req-2'] == 700

    @pytest.mark.asyncio
    async def test_loading_finished_consumes_data_received(self, recorder, mock_tab):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_received(_make_response_received_event())
        recorder._on_data_received(_make_data_received_event('req-1', 1000))
        recorder._on_data_received(_make_data_received_event('req-1', 500))
        recorder._on_loading_finished(_make_loading_finished_event())

        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert 'req-1' not in recorder._data_received_sizes
        assert len(recorder._entries) == 1
        assert recorder._entries[0]['response']['bodySize'] == 1500

    def test_loading_failed_cleans_up_data_received(self, recorder):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_data_received(_make_data_received_event('req-1', 200))
        recorder._on_loading_failed(_make_loading_failed_event())
        assert 'req-1' not in recorder._data_received_sizes


class TestHarRecorderExtraStatusCode:
    """Test that responseReceivedExtraInfo statusCode overrides responseReceived status."""

    @pytest.mark.asyncio
    async def test_extra_status_code_overrides_response_status(self, recorder, mock_tab):
        """For cached requests, extraInfo statusCode (304) should win over responseReceived (200)."""
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_received(_make_response_received_event(status=200))

        # extraInfo says the real status is 304
        extra_event = {
            'method': NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
            'params': {
                'requestId': 'req-1',
                'headers': {'Content-Type': 'text/html'},
                'blockedCookies': [],
                'resourceIPAddressSpace': 'Public',
                'statusCode': 304,
            },
        }
        recorder._on_response_extra_info(extra_event)
        recorder._on_loading_finished(_make_loading_finished_event())

        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert len(recorder._entries) == 1
        assert recorder._entries[0]['response']['status'] == 304
        assert recorder._entries[0]['response']['bodySize'] == 0

    @pytest.mark.asyncio
    async def test_normal_status_when_no_extra(self, recorder, mock_tab):
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        recorder._on_response_received(_make_response_received_event(status=200))
        recorder._on_loading_finished(_make_loading_finished_event())

        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        assert recorder._entries[0]['response']['status'] == 200


class TestHarRecorderReceiveTiming:
    """Test that receive timing uses monotonic timestamps."""

    @pytest.mark.asyncio
    async def test_receive_from_monotonic_timestamps(self, recorder, mock_tab):
        """receive = (loadingFinished.timestamp - responseReceived.timestamp) * 1000."""
        recorder._on_request_will_be_sent(_make_request_will_be_sent_event())
        # responseReceived has timestamp=12346.0 (from helper)
        recorder._on_response_received(_make_response_received_event())
        # loadingFinished has timestamp=12347.0 (from helper)
        recorder._on_loading_finished(_make_loading_finished_event())

        import asyncio
        if recorder._body_tasks:
            await asyncio.gather(*recorder._body_tasks, return_exceptions=True)

        entry = recorder._entries[0]
        # (12347.0 - 12346.0) * 1000 = 1000ms
        assert entry['timings']['receive'] == 1000.0

    def test_receive_fallback_zero_without_timestamps(self, recorder):
        """When no timestamps available, receive should be 0."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
        }
        entry = recorder._build_entry(pending)
        assert entry['timings']['receive'] == 0


class TestHarRecorderEntryTimeSslExclusion:
    """Test that entry.time excludes ssl from sum (connect includes it)."""

    def test_entry_time_excludes_ssl(self, recorder):
        timing = {
            'requestTime': 12345.0,
            'proxyStart': -1,
            'proxyEnd': -1,
            'dnsStart': 0.5,
            'dnsEnd': 5.0,
            'connectStart': 5.0,
            'connectEnd': 50.0,
            'sslStart': 10.0,
            'sslEnd': 45.0,
            'workerStart': -1,
            'workerReady': -1,
            'workerFetchStart': -1,
            'workerRespondWithSettled': -1,
            'sendStart': 50.0,
            'sendEnd': 51.0,
            'pushStart': 0,
            'pushEnd': 0,
            'receiveHeadersStart': 100.0,
            'receiveHeadersEnd': 105.0,
        }
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'timing': timing,
            'response_timestamp': 12346.0,
            'finished_timestamp': 12346.5,
        }
        entry = recorder._build_entry(pending)
        timings = entry['timings']
        # ssl=35.0, connect=45.0 (connect includes ssl time)
        # entry.time should NOT include ssl separately
        expected = (
            timings['blocked']
            + timings['dns']
            + timings['connect']
            + timings['send']
            + timings['wait']
            + timings['receive']
        )
        assert entry['time'] == round(expected, 2)
        # Verify ssl is NOT counted in total
        assert timings['ssl'] == 35.0
        assert timings['ssl'] not in (
            entry['time'] - timings['blocked'] - timings['dns']
            - timings['connect'] - timings['send'] - timings['wait']
            - timings['receive'],
        )


class TestHarRecorderEntryOrdering:
    """Test that entries are sorted by startedDateTime."""

    @pytest.mark.asyncio
    async def test_entries_sorted_by_started_date_time(self, recorder):
        recorder._entries.append({
            'startedDateTime': '2023-11-14T12:00:02+00:00',
            'time': 100.0,
            'request': {'method': 'GET', 'url': 'https://example.com/second'},
            'response': {'status': 200},
            'cache': {},
            'timings': {},
        })
        recorder._entries.append({
            'startedDateTime': '2023-11-14T12:00:01+00:00',
            'time': 50.0,
            'request': {'method': 'GET', 'url': 'https://example.com/first'},
            'response': {'status': 200},
            'cache': {},
            'timings': {},
        })
        recording = HarCapture(recorder)

        # entries property should be sorted
        entries = recording.entries
        assert entries[0]['request']['url'] == 'https://example.com/first'
        assert entries[1]['request']['url'] == 'https://example.com/second'

        # to_dict() should also be sorted
        har = recording.to_dict()
        assert har['log']['entries'][0]['request']['url'] == 'https://example.com/first'
        assert har['log']['entries'][1]['request']['url'] == 'https://example.com/second'


class TestHarRecorderBodySizeFallback:
    """Test bodySize fallback to content_size when body_bytes is 0."""

    @pytest.mark.asyncio
    async def test_body_size_falls_back_to_content_size(self, recorder):
        """When body_bytes=0 but content exists (e.g. file://), use content_size."""
        pending = {
            'url': 'file:///page.html',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'response_body': '<html>Hello World</html>',
            'response_body_base64': False,
            'body_bytes': 0,
        }
        entry = recorder._build_entry(pending)
        expected_size = len('<html>Hello World</html>'.encode('utf-8'))
        assert entry['response']['bodySize'] == expected_size
        assert entry['response']['content']['size'] == expected_size

    @pytest.mark.asyncio
    async def test_body_size_negative_one_when_no_body_and_no_bytes(self, recorder):
        """When body_bytes=-1 and no content, bodySize should be -1."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'body_bytes': -1,
        }
        entry = recorder._build_entry(pending)
        assert entry['response']['bodySize'] == -1


class TestHarRecorderHttpVersionNormalization:
    """Test httpVersion normalization for HAR compatibility."""

    def test_h2_stays_lowercase(self):
        assert HarRecorder._normalize_http_version('h2') == 'h2'

    def test_h3_stays_lowercase(self):
        assert HarRecorder._normalize_http_version('h3') == 'h3'

    def test_http_1_1_uppercased(self):
        assert HarRecorder._normalize_http_version('http/1.1') == 'HTTP/1.1'

    def test_http_1_0_uppercased(self):
        assert HarRecorder._normalize_http_version('http/1.0') == 'HTTP/1.0'

    def test_already_uppercase(self):
        assert HarRecorder._normalize_http_version('HTTP/1.1') == 'HTTP/1.1'

    def test_file_protocol_returns_empty(self):
        assert HarRecorder._normalize_http_version('file') == ''

    def test_empty_string(self):
        assert HarRecorder._normalize_http_version('') == ''

    def test_unknown_protocol_returns_empty(self):
        assert HarRecorder._normalize_http_version('blob') == ''

    def test_entry_uses_normalized_version(self, recorder):
        """Entry httpVersion should be normalized."""
        pending = {
            'url': 'https://example.com',
            'method': 'GET',
            'request_headers': {},
            'wall_time': 1700000000.0,
            'status': 200,
            'status_text': 'OK',
            'response_headers': {},
            'mime_type': 'text/html',
            'protocol': 'http/1.1',
        }
        entry = recorder._build_entry(pending)
        assert entry['request']['httpVersion'] == 'HTTP/1.1'
        assert entry['response']['httpVersion'] == 'HTTP/1.1'
