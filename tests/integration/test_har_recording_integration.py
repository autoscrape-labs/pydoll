"""Integration tests for HAR recording feature.

These tests open a real browser, serve a test page with JS-initiated
fetch requests via a local HTTP server, and verify the recorded HAR entries.
"""

import asyncio
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.requests.har_recorder import HarCapture
from pydoll.protocol.network.types import ResourceType

from _waits import wait_until


def _find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


_TINY_PNG = bytes.fromhex(
    '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4'
    '890000000d49444154789c63f8cfc0f01f0005000fff03d2c4d2700000000049454e44ae426082'
)


def _fetch_page(*fetch_calls):
    """Build an HTML page served from the API origin that runs same-origin fetches.

    Each entry in ``fetch_calls`` is a JS fetch() argument string. The page sets
    ``#status`` to 'done' once every fetch settles, so tests can poll for it.
    """
    body = '\n'.join(f'      await fetch({call}).catch(() => {{}});' for call in fetch_calls)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>HAR same-origin</title></head>
<body>
  <div id="status">waiting</div>
  <script>
    async function run() {{
{body}
      document.getElementById('status').textContent = 'done';
    }}
    window.addEventListener('load', run);
  </script>
</body></html>"""


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
        elif self.path == '/large':
            self._respond(200, 'text/plain', 'x' * 200_000)
        elif self.path == '/large-page':
            self._respond(200, 'text/html', _fetch_page("'/large'"))
        elif self.path == '/cookies-page':
            self._respond(
                200, 'text/html', _fetch_page("'/set-cookie'", "'/needs-cookie'")
            )
        elif self.path == '/redirect-page':
            self._respond(200, 'text/html', _fetch_page("'/redirect'"))
        elif self.path == '/filtered-page':
            self._respond(
                200, 'text/html', _fetch_page("'/api/data'", "'http://127.0.0.1:1/blocked'")
            )
        elif self.path.startswith('/image-page'):
            self._respond(
                200,
                'text/html',
                '<!DOCTYPE html><html><body><div id="status">waiting</div>'
                '<img id="pic" src="/cacheable.png">'
                '<script>const i=document.getElementById("pic");'
                'i.addEventListener("load",()=>{document.getElementById("status")'
                '.textContent="done";});'
                'i.addEventListener("error",()=>{document.getElementById("status")'
                '.textContent="done";});</script></body></html>',
            )
        elif self.path == '/pending-page':
            self._respond(
                200,
                'text/html',
                '<!DOCTYPE html><html><body><div id="status">started</div>'
                '<script>fetch("/slow").catch(()=>{});</script></body></html>',
            )
        elif self.path == '/set-cookie':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Set-Cookie', 'har_session=abc123; Path=/; HttpOnly')
            self.send_header(
                'Set-Cookie', 'har_secure=xyz789; Domain=127.0.0.1; Path=/; Secure'
            )
            self.end_headers()
            self.wfile.write(b'cookie set')
        elif self.path == '/needs-cookie':
            cookie = self.headers.get('Cookie', '')
            self._respond(200, 'text/plain', f'cookie={cookie}')
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/api/data')
            self.end_headers()
        elif self.path == '/cacheable.png':
            if self.headers.get('If-None-Match') == '"png-v1"':
                self.send_response(304)
                self.send_header('ETag', '"png-v1"')
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('ETag', '"png-v1"')
                self.send_header('Cache-Control', 'max-age=0, must-revalidate')
                self.end_headers()
                self.wfile.write(_TINY_PNG)
        elif self.path == '/slow':
            self._sleep_then_respond()
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

    def _sleep_then_respond(self):
        try:
            time.sleep(30)
            self._respond(200, 'text/plain', 'slow')
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        try:
            self.wfile.write(body.encode())
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

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
    """Start a local threaded HTTP server for the test module.

    Threaded so a deliberately hung endpoint (``/slow``) cannot block other
    requests or the shutdown handshake.
    """
    port = _find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), _TestAPIHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{port}'
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


@pytest.fixture(scope='module')
def test_page_path():
    """Path to the HAR recording test HTML page."""
    return Path(__file__).parent / 'pages' / 'test_har_recording.html'


async def _wait_for_requests_done(tab, timeout=15):
    """Poll the page until status shows 'done'. Checks first, then sleeps."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        status_el = await tab.find(id='status', timeout=5)
        text = await status_el.text
        if text == 'done':
            return True
        if loop.time() >= deadline:
            return False
        await asyncio.sleep(0.5)


async def _wait_for_network_idle(tab, idle_for=0.6, timeout=15):
    """Return once the count of performance resource entries stops growing for idle_for seconds."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    last_count, stable_since = -1, loop.time()
    while True:
        res = await tab.execute_script(
            'return performance.getEntriesByType("resource").length', return_by_value=True
        )
        count = res['result']['result']['value']
        now = loop.time()
        if count != last_count:
            last_count, stable_since = count, now
        elif now - stable_since >= idle_for:
            return
        if now >= deadline:
            return
        await asyncio.sleep(0.1)


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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

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


def _origin_entry(recording, path_suffix, method='GET', status=None):
    """Return the first recorded entry whose URL ends with *path_suffix*."""
    for entry in recording.entries:
        if not entry['request']['url'].endswith(path_suffix):
            continue
        if entry['request']['method'] != method:
            continue
        if status is not None and entry['response']['status'] != status:
            continue
        return entry
    return None


async def _coro(value):
    """Wrap a synchronous boolean in a coroutine for wait_until predicates."""
    return value


class TestHarRedirectIntegration:
    """Recording captures redirect entries and the final destination."""

    @pytest.mark.asyncio
    async def test_record_captures_redirect_chain(self, ci_chrome_options, api_server):
        """A 302 redirect produces a separate entry with redirectURL set."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(f'{api_server}/redirect-page')
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

            redirect_entry = _origin_entry(recording, '/redirect', status=302)
            assert redirect_entry is not None
            assert redirect_entry['response']['redirectURL'] == '/api/data'

            final_entry = _origin_entry(recording, '/api/data', status=200)
            assert final_entry is not None
            assert 'Hello from the test server' in final_entry['response']['content'].get(
                'text', ''
            )


class TestHarResourceTypeFilter:
    """Recording with resource_types only captures matching requests."""

    @pytest.mark.asyncio
    async def test_record_filters_by_resource_type(self, ci_chrome_options, api_server):
        """Only Fetch/XHR requests are recorded; the document load is skipped."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record(
                resource_types=[ResourceType.FETCH, ResourceType.XHR]
            ) as recording:
                await tab.go_to(f'{api_server}/filtered-page')
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

            entries = recording.entries
            assert len(entries) >= 1

            # The document navigation (Document type) must not be recorded.
            assert not any(e['request']['url'].endswith('/filtered-page') for e in entries)
            # The fetch() to /api/data (Fetch type) must be recorded.
            assert _origin_entry(recording, '/api/data', status=200) is not None
            # Every recorded entry is a fetch/xhr resource type.
            for entry in entries:
                assert entry.get('_resourceType') in {'Fetch', 'XHR'}


class TestHarNotModifiedIntegration:
    """Recording captures 304 Not Modified responses with bodySize 0."""

    @pytest.mark.asyncio
    async def test_record_304_has_zero_body_size(self, ci_chrome_options, api_server):
        """Re-requesting a cacheable image yields a 304 entry with bodySize 0."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(f'{api_server}/image-page')
                assert await _wait_for_requests_done(tab), 'First image load did not complete'
                await _wait_for_network_idle(tab)
                await tab.go_to(f'{api_server}/image-page?again')
                assert await _wait_for_requests_done(tab), 'Second image load did not complete'
                await _wait_for_network_idle(tab)

            png_entries = [
                e for e in recording.entries if e['request']['url'].endswith('/cacheable.png')
            ]
            assert len(png_entries) >= 2

            statuses = [e['response']['status'] for e in png_entries]
            assert 200 in statuses
            assert 304 in statuses

            not_modified = next(e for e in png_entries if e['response']['status'] == 304)
            assert not_modified['response']['bodySize'] == 0


class TestHarPendingAndFailedIntegration:
    """Recording finalizes in-flight and failed requests at stop time."""

    @pytest.mark.asyncio
    async def test_record_captures_failed_request(self, ci_chrome_options, api_server):
        """A request that fails (blocked port) is recorded with status 0."""
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(f'{api_server}/filtered-page')
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

            failed_entry = _origin_entry(recording, '/blocked', status=0)
            assert failed_entry is not None
            assert failed_entry['response']['status'] == 0

    @pytest.mark.asyncio
    async def test_record_captures_large_response_body(self, ci_chrome_options, api_server):
        """A large response body is fetched asynchronously and captured in the HAR.

        The body arrives via an async getResponseBody round-trip after
        loadingFinished, so the entry only appears once that task completes. Poll
        the live recording until it does — racing context exit against the
        internal finalize is inherently flaky across environments.
        """
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(f'{api_server}/large-page')
                await wait_until(
                    lambda: _coro(_origin_entry(recording, '/large', status=200) is not None),
                    message='/large entry not finalized in HAR',
                )

            large_entry = _origin_entry(recording, '/large', status=200)
            assert large_entry is not None
            assert large_entry['response']['status'] == 200
            assert large_entry['response']['content']['size'] > 0


class TestHarToDictIntegration:
    """The HarCapture.to_dict() export mirrors the saved HAR structure."""

    @pytest.mark.asyncio
    async def test_to_dict_matches_saved_file(
        self, ci_chrome_options, api_server, test_page_path, tmp_path
    ):
        """to_dict() returns the same HAR 1.2 structure that save() writes."""
        page_url = f'file://{test_page_path.absolute()}?base={api_server}'

        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()

            async with tab.request.record() as recording:
                await tab.go_to(page_url)
                assert await _wait_for_requests_done(tab), 'Page requests did not complete'
                await _wait_for_network_idle(tab)

            har_dict = recording.to_dict()
            assert har_dict['log']['version'] == '1.2'
            assert har_dict['log']['creator']['name'] == 'pydoll'
            assert isinstance(har_dict['log']['creator']['version'], str)
            assert har_dict['log']['creator']['version']

            har_path = tmp_path / 'roundtrip.har'
            recording.save(har_path)
            with open(har_path, encoding='utf-8') as f:
                saved = json.load(f)

            in_memory_urls = [e['request']['url'] for e in har_dict['log']['entries']]
            saved_urls = [e['request']['url'] for e in saved['log']['entries']]
            assert in_memory_urls == saved_urls
