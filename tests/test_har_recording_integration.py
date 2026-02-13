"""Integration tests for HAR recording feature.

These tests open a real browser, serve a test page with JS-initiated
fetch requests via a local HTTP server, and verify the recorded HAR entries.
"""

import asyncio
import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.requests.har_recorder import HarCapture


def _find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _TestAPIHandler(BaseHTTPRequestHandler):
    """Deterministic HTTP handler for HAR integration tests."""

    def do_GET(self):
        if self.path == '/api/users':
            self._respond(
                200,
                'application/json',
                json.dumps([{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]),
            )
        elif self.path == '/api/data':
            self._respond(200, 'text/plain', 'Hello from the test server')
        else:
            self._respond(404, 'text/plain', 'Not Found')

    def do_POST(self):
        if self.path == '/api/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            self._respond(
                201,
                'application/json',
                json.dumps({
                    'status': 'created',
                    'received': json.loads(body.decode()) if body else None,
                }),
            )
        else:
            self._respond(404, 'text/plain', 'Not Found')

    def _respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope='module')
def api_server():
    """Start a local HTTP server for the test module."""
    port = _find_free_port()
    server = HTTPServer(('127.0.0.1', port), _TestAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{port}'
    server.shutdown()


@pytest.fixture(scope='module')
def test_page_path():
    """Path to the HAR recording test HTML page."""
    return Path(__file__).parent / 'pages' / 'test_har_recording.html'


async def _wait_for_requests_done(tab, timeout=15):
    """Poll the page until status shows 'done'."""
    for _ in range(int(timeout / 0.5)):
        await asyncio.sleep(0.5)
        status_el = await tab.find(id='status')
        text = await status_el.text
        if text == 'done':
            return True
    return False


class TestHarRecordIntegration:
    """Integration tests for tab.request.record()."""

    @pytest.mark.asyncio
    async def test_record_captures_page_load(self, ci_chrome_options, api_server, test_page_path):
        """Recording captures the document load event."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            assert isinstance(recording, HarCapture)
            entries = recording.entries
            assert len(entries) >= 1

            # First entry should be the document load
            doc_entries = [
                e for e in entries if e['request']['url'].startswith('file://')
            ]
            assert len(doc_entries) >= 1
            assert doc_entries[0]['response']['status'] == 200
            assert doc_entries[0]['response']['content']['mimeType'] == 'text/html'

    @pytest.mark.asyncio
    async def test_record_captures_fetch_requests(
        self, ci_chrome_options, api_server, test_page_path
    ):
        """Recording captures JS fetch() requests with correct URLs and methods."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            entries = recording.entries
            api_entries = [e for e in entries if '/api/' in e['request']['url']]
            # 3 API requests + possible OPTIONS preflight for POST
            assert len(api_entries) >= 3

            urls = [e['request']['url'] for e in api_entries]
            assert any('/api/users' in u for u in urls)
            assert any('/api/data' in u for u in urls)
            assert any('/api/submit' in u for u in urls)

    @pytest.mark.asyncio
    async def test_record_captures_response_bodies(
        self, ci_chrome_options, api_server, test_page_path
    ):
        """Recording captures response bodies for each request."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            entries = recording.entries
            users_entry = next(
                (e for e in entries if '/api/users' in e['request']['url']), None
            )
            assert users_entry is not None
            body_text = users_entry['response']['content'].get('text', '')
            assert 'Alice' in body_text
            assert 'Bob' in body_text

            data_entry = next(
                (e for e in entries if '/api/data' in e['request']['url']), None
            )
            assert data_entry is not None
            assert 'Hello from the test server' in data_entry['response']['content'].get('text', '')

    @pytest.mark.asyncio
    async def test_record_captures_post_request(
        self, ci_chrome_options, api_server, test_page_path
    ):
        """Recording captures POST requests with body data."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            entries = recording.entries
            post_entry = next(
                (
                    e
                    for e in entries
                    if '/api/submit' in e['request']['url']
                    and e['request']['method'] == 'POST'
                ),
                None,
            )
            assert post_entry is not None
            assert post_entry['response']['status'] == 201

            # POST body should be captured
            post_data = post_entry['request'].get('postData')
            assert post_data is not None
            assert '"key"' in post_data['text']

            # Response body should contain what the server echoed back
            resp_text = post_entry['response']['content'].get('text', '')
            assert 'created' in resp_text

    @pytest.mark.asyncio
    async def test_record_correct_status_codes(
        self, ci_chrome_options, api_server, test_page_path
    ):
        """Recording captures correct HTTP status codes."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            entries = recording.entries
            users_entry = next(
                (e for e in entries if '/api/users' in e['request']['url']), None
            )
            assert users_entry is not None
            assert users_entry['response']['status'] == 200

            submit_entry = next(
                (
                    e
                    for e in entries
                    if '/api/submit' in e['request']['url']
                    and e['request']['method'] == 'POST'
                ),
                None,
            )
            assert submit_entry is not None
            assert submit_entry['response']['status'] == 201

    @pytest.mark.asyncio
    async def test_record_body_sizes(self, ci_chrome_options, api_server, test_page_path):
        """Recording reports correct body sizes from dataReceived events."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            entries = recording.entries
            users_entry = next(
                (e for e in entries if '/api/users' in e['request']['url']), None
            )
            assert users_entry is not None
            # bodySize should be > 0 for successful requests with body
            assert users_entry['response']['bodySize'] > 0
            # content.size should match the decoded body length
            assert users_entry['response']['content']['size'] > 0


class TestHarSaveIntegration:
    """Integration tests for saving and loading HAR files."""

    @pytest.mark.asyncio
    async def test_save_produces_valid_har(
        self, ci_chrome_options, api_server, test_page_path, tmp_path
    ):
        """Saved HAR file is valid JSON with HAR 1.2 structure."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            har_path = tmp_path / 'test_output.har'
            recording.save(har_path)

            assert har_path.exists()
            with open(har_path, encoding='utf-8') as f:
                har = json.load(f)

            assert har['log']['version'] == '1.2'
            assert har['log']['creator']['name'] == 'pydoll'
            assert isinstance(har['log']['pages'], list)
            assert isinstance(har['log']['entries'], list)
            assert len(har['log']['entries']) >= 4

    @pytest.mark.asyncio
    async def test_save_entries_sorted_by_time(
        self, ci_chrome_options, api_server, test_page_path, tmp_path
    ):
        """Saved entries are sorted by startedDateTime."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            har_path = tmp_path / 'test_sorted.har'
            recording.save(har_path)

            with open(har_path, encoding='utf-8') as f:
                har = json.load(f)

            dates = [e['startedDateTime'] for e in har['log']['entries']]
            assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_save_entries_have_required_fields(
        self, ci_chrome_options, api_server, test_page_path, tmp_path
    ):
        """Every entry has required HAR 1.2 fields."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                await _wait_for_requests_done(tab)
                await asyncio.sleep(1)

            har_path = tmp_path / 'test_fields.har'
            recording.save(har_path)

            with open(har_path, encoding='utf-8') as f:
                har = json.load(f)

            for entry in har['log']['entries']:
                # Required entry fields
                assert 'startedDateTime' in entry
                assert 'time' in entry
                assert 'request' in entry
                assert 'response' in entry
                assert 'cache' in entry
                assert 'timings' in entry

                # Required request fields
                req = entry['request']
                assert 'method' in req
                assert 'url' in req
                assert 'httpVersion' in req
                assert 'cookies' in req
                assert 'headers' in req
                assert 'queryString' in req
                assert 'headersSize' in req
                assert 'bodySize' in req

                # Required response fields
                resp = entry['response']
                assert 'status' in resp
                assert 'statusText' in resp
                assert 'httpVersion' in resp
                assert 'cookies' in resp
                assert 'headers' in resp
                assert 'content' in resp
                assert 'redirectURL' in resp
                assert 'headersSize' in resp
                assert 'bodySize' in resp

                # Required timings fields
                timings = entry['timings']
                for field in ('blocked', 'dns', 'connect', 'ssl', 'send', 'wait', 'receive'):
                    assert field in timings
