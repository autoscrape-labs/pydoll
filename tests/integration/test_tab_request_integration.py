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

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import HTTPError


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


class _RequestHandler(BaseHTTPRequestHandler):
    """Deterministic HTTP endpoints for the request integration tests."""

    def do_GET(self):
        if self.path == '/':
            self._respond(200, 'text/html', '<!DOCTYPE html><html><body>home</body></html>')
        elif self.path == '/json':
            self._respond(
                200, 'application/json', json.dumps({'message': 'hello'}), {'X-Custom': 'pydoll'}
            )
        elif self.path == '/missing':
            self._respond(404, 'text/plain', 'nope')
        else:
            self._respond(404, 'text/plain', 'not found')

    def do_POST(self):
        if self.path == '/echo':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode() if length else ''
            payload = json.loads(body) if body else None
            self._respond(200, 'application/json', json.dumps({'echo': payload}))
        else:
            self._respond(404, 'text/plain', 'not found')

    def _respond(self, status, content_type, body, extra=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body.encode())

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
