"""Real-Chrome integration tests for Tab.request (HTTP via the browser).

tab.request executes fetch in the page's JavaScript context, so these tests
navigate to a local HTTP server (same origin) and issue real requests against
it, asserting the resulting Response — status, json, text, headers, ok and
raise_for_status. No mocks: the browser really performs the request.
"""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from _waits import wait_until

from pydoll.browser.chromium import Chrome
from pydoll.browser.requests.response import Response
from pydoll.exceptions import HTTPError

PNG_1PX = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44,
        0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F,
        0x15, 0xC4, 0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0xF8,
        0xCF, 0xC0, 0xF0, 0x1F, 0x00, 0x05, 0x00, 0x01, 0xFF, 0xD6, 0xDC, 0x6E, 0x00, 0x00, 0x00,
        0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def _read_body(handler: BaseHTTPRequestHandler) -> bytes:
    length = int(handler.headers.get('Content-Length', 0))
    return handler.rfile.read(length) if length else b''


class _RequestHandler(BaseHTTPRequestHandler):
    """Deterministic HTTP endpoints for the request integration tests."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/':
            self._respond(200, 'text/html', '<!DOCTYPE html><html><body>home</body></html>')
        elif path == '/json':
            self._respond(
                200, 'application/json', json.dumps({'message': 'hello'}), {'X-Custom': 'pydoll'}
            )
        elif path == '/params':
            query = parse_qs(parsed.query)
            flat = {key: values[0] for key, values in query.items()}
            self._respond(200, 'application/json', json.dumps({'args': flat}))
        elif path == '/echo-headers':
            seen = {
                'x-token': self.headers.get('X-Token'),
                'x-trace': self.headers.get('X-Trace'),
            }
            self._respond(200, 'application/json', json.dumps({'headers': seen}))
        elif path == '/text-is-json':
            self._respond(200, 'text/plain', json.dumps({'served': 'as-text'}))
        elif path == '/plain':
            self._respond(200, 'text/plain', 'just text, not json')
        elif path == '/binary':
            self._respond_bytes(200, 'image/png', PNG_1PX)
        elif path == '/set-cookie':
            self._respond(
                200,
                'application/json',
                json.dumps({'ok': True}),
                {'Set-Cookie': 'session=abc123; Path=/; HttpOnly'},
            )
        elif path == '/set-cookie-malformed':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Set-Cookie', 'good=value1; Path=/')
            self.send_header('Set-Cookie', 'novalue')
            self.send_header('Set-Cookie', '=emptyname; Path=/')
            self.send_header('Set-Cookie', 'second=value2; Path=/')
            body = json.dumps({'ok': True}).encode()
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        elif path == '/missing':
            self._respond(404, 'text/plain', 'nope')
        elif path == '/boom':
            self._respond(500, 'text/plain', 'server error')
        else:
            self._respond(404, 'text/plain', 'not found')

    def do_POST(self):
        if self.path == '/echo':
            body = _read_body(self).decode()
            payload = json.loads(body) if body else None
            self._respond(200, 'application/json', json.dumps({'echo': payload}))
        elif self.path == '/form':
            body = _read_body(self).decode()
            self._respond(
                200,
                'application/json',
                json.dumps(
                    {
                        'content_type': self.headers.get('Content-Type'),
                        'raw': body,
                    }
                ),
            )
        else:
            self._respond(404, 'text/plain', 'not found')

    def do_PUT(self):
        body = _read_body(self).decode()
        payload = json.loads(body) if body else None
        self._respond(200, 'application/json', json.dumps({'put': payload}))

    def do_PATCH(self):
        body = _read_body(self).decode()
        payload = json.loads(body) if body else None
        self._respond(200, 'application/json', json.dumps({'patch': payload}))

    def do_DELETE(self):
        self._respond(200, 'application/json', json.dumps({'deleted': self.path}))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Head', 'yes')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Allow', 'GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def _respond(self, status, content_type, body, extra=None):
        self._respond_bytes(status, content_type, body.encode(), extra)

    def _respond_bytes(self, status, content_type, body, extra=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest_asyncio.fixture
async def request_tab(ci_chrome_options):
    port = _find_free_port()
    server = HTTPServer(('127.0.0.1', port), _RequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{port}'
    try:
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(f'{base}/')
            yield tab, base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_get_returns_json_status_and_ok(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/json')
    assert response.status_code == 200
    assert response.ok is True
    assert response.json() == {'message': 'hello'}


@pytest.mark.asyncio
async def test_get_text_returns_body(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/json')
    assert 'hello' in response.text


@pytest.mark.asyncio
async def test_response_exposes_server_headers(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/json')
    header_names = {header['name'].lower() for header in response.headers}
    assert 'x-custom' in header_names


@pytest.mark.asyncio
async def test_post_sends_json_body_and_receives_echo(request_tab):
    tab, base = request_tab
    response = await tab.request.post(f'{base}/echo', json={'a': 1})
    assert response.status_code == 200
    assert response.json() == {'echo': {'a': 1}}


@pytest.mark.asyncio
async def test_not_found_sets_status_and_raise_for_status(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/missing')
    assert response.status_code == 404
    assert response.ok is False
    with pytest.raises(HTTPError):
        response.raise_for_status()


@pytest.mark.asyncio
async def test_get_with_query_params_appends_to_url(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/params', params={'q': 'pydoll', 'page': '2'})
    assert response.status_code == 200
    assert response.json() == {'args': {'q': 'pydoll', 'page': '2'}}


@pytest.mark.asyncio
async def test_get_params_merge_with_existing_query_string(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/params?existing=1', params={'added': '2'})
    assert response.json() == {'args': {'existing': '1', 'added': '2'}}


@pytest.mark.asyncio
async def test_custom_request_headers_are_sent(request_tab):
    tab, base = request_tab
    response = await tab.request.get(
        f'{base}/echo-headers',
        headers=[
            {'name': 'X-Token', 'value': 'secret'},
            {'name': 'X-Trace', 'value': 'trace-42'},
        ],
    )
    assert response.json() == {'headers': {'x-token': 'secret', 'x-trace': 'trace-42'}}


@pytest.mark.asyncio
async def test_post_form_data_dict_is_url_encoded(request_tab):
    tab, base = request_tab
    response = await tab.request.post(f'{base}/form', data={'name': 'ada', 'lang': 'py'})
    payload = response.json()
    assert payload['content_type'] == 'application/x-www-form-urlencoded'
    assert parse_qs(payload['raw']) == {'name': ['ada'], 'lang': ['py']}


@pytest.mark.asyncio
async def test_post_form_data_list_of_tuples_is_url_encoded(request_tab):
    tab, base = request_tab
    response = await tab.request.post(
        f'{base}/form', data=[('tag', 'a'), ('tag', 'b'), ('x', '1')]
    )
    payload = response.json()
    assert payload['content_type'] == 'application/x-www-form-urlencoded'
    assert parse_qs(payload['raw']) == {'tag': ['a', 'b'], 'x': ['1']}


@pytest.mark.asyncio
async def test_post_raw_string_body_sent_as_is(request_tab):
    tab, base = request_tab
    response = await tab.request.post(f'{base}/form', data='raw-payload-string')
    payload = response.json()
    assert payload['raw'] == 'raw-payload-string'


@pytest.mark.asyncio
async def test_put_sends_json_and_receives_echo(request_tab):
    tab, base = request_tab
    response = await tab.request.put(f'{base}/resource/1', json={'value': 'updated'})
    assert response.status_code == 200
    assert response.json() == {'put': {'value': 'updated'}}


@pytest.mark.asyncio
async def test_patch_sends_json_and_receives_echo(request_tab):
    tab, base = request_tab
    response = await tab.request.patch(f'{base}/resource/1', json={'value': 'patched'})
    assert response.status_code == 200
    assert response.json() == {'patch': {'value': 'patched'}}


@pytest.mark.asyncio
async def test_delete_returns_confirmation(request_tab):
    tab, base = request_tab
    response = await tab.request.delete(f'{base}/resource/9')
    assert response.status_code == 200
    assert response.json() == {'deleted': '/resource/9'}


@pytest.mark.asyncio
async def test_head_returns_headers_without_body(request_tab):
    tab, base = request_tab
    response = await tab.request.head(f'{base}/json')
    assert response.status_code == 200
    assert response.text == ''
    header_names = {header['name'].lower() for header in response.headers}
    assert 'x-head' in header_names


@pytest.mark.asyncio
async def test_options_returns_allowed_methods(request_tab):
    tab, base = request_tab
    response = await tab.request.options(f'{base}/json')
    assert response.status_code == 204
    header_names = {header['name'].lower() for header in response.headers}
    assert 'access-control-allow-methods' in header_names


@pytest.mark.asyncio
async def test_redirect_is_followed_to_final_url(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/redirect')
    assert response.status_code == 200
    assert response.json() == {'message': 'hello'}
    assert response.url.endswith('/json')


@pytest.mark.asyncio
async def test_set_cookie_is_extracted_into_response(request_tab):
    tab, base = request_tab
    response = await _get_until_cookies(tab, f'{base}/set-cookie')
    assert response.status_code == 200
    cookie_pairs = {(cookie['name'], cookie['value']) for cookie in response.cookies}
    assert ('session', 'abc123') in cookie_pairs


async def _get_until_cookies(tab, url):
    """Re-issue an idempotent GET until Set-Cookie extraction yields cookies.

    The cookies surface via the asynchronous responseReceivedExtraInfo CDP
    event, which can arrive after the fetch promise resolves. Rather than a
    fixed sleep, poll by retrying the (idempotent) request until the response
    carries cookies, then return that response.
    """
    captured: dict[str, object] = {}

    async def attempt() -> bool:
        response = await tab.request.get(url)
        captured['response'] = response
        return bool(response.cookies)

    await wait_until(attempt, timeout=10, message=f'no cookies extracted from {url}')
    return captured['response']


@pytest.mark.asyncio
async def test_malformed_set_cookie_lines_are_skipped(request_tab):
    tab, base = request_tab
    response = await _get_until_cookies(tab, f'{base}/set-cookie-malformed')
    assert response.status_code == 200
    cookie_pairs = {(cookie['name'], cookie['value']) for cookie in response.cookies}
    assert ('good', 'value1') in cookie_pairs
    assert ('second', 'value2') in cookie_pairs
    cookie_names = {cookie['name'] for cookie in response.cookies}
    assert '' not in cookie_names
    assert 'novalue' not in cookie_names


@pytest.mark.asyncio
async def test_binary_response_exposes_content_bytes(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/binary')
    assert response.status_code == 200
    assert isinstance(response.content, bytes)
    assert len(response.content) > 0
    assert response.content == response.text.encode('utf-8')


@pytest.mark.asyncio
async def test_request_headers_are_exposed(request_tab):
    tab, base = request_tab
    response = await tab.request.get(
        f'{base}/json', headers=[{'name': 'X-Token', 'value': 'abc'}]
    )
    sent = {(header['name'].lower(), header['value']) for header in response.request_headers}
    assert ('x-token', 'abc') in sent


@pytest.mark.asyncio
async def test_json_lazy_parse_on_text_content_type(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/text-is-json')
    assert response.json() == {'served': 'as-text'}


@pytest.mark.asyncio
async def test_json_on_non_json_text_raises_value_error(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/plain')
    assert response.text == 'just text, not json'
    with pytest.raises(ValueError):
        response.json()


@pytest.mark.asyncio
async def test_server_error_raise_for_status(request_tab):
    tab, base = request_tab
    response = await tab.request.get(f'{base}/boom')
    assert response.status_code == 500
    assert response.ok is False
    with pytest.raises(HTTPError):
        response.raise_for_status()


@pytest.mark.asyncio
async def test_network_failure_raises_http_error(request_tab):
    tab, _ = request_tab
    closed_port = _find_free_port()
    with pytest.raises(HTTPError):
        await tab.request.get(f'http://127.0.0.1:{closed_port}/never')


@pytest.mark.asyncio
async def test_non_serializable_option_raises_http_error(request_tab):
    tab, base = request_tab
    with pytest.raises(HTTPError):
        await tab.request.get(f'{base}/json', cache=object())


@pytest.mark.asyncio
async def test_record_captures_request_as_har(request_tab):
    tab, base = request_tab
    async with tab.request.record() as capture:
        await tab.go_to(f'{base}/json')
    urls = [entry['request']['url'] for entry in capture.entries]
    assert any(url.endswith('/json') for url in urls)


def test_response_text_lazy_decodes_from_content_when_text_empty():
    response = Response(status_code=200, content=b'lazy-bytes', text='')
    assert response.text == 'lazy-bytes'
