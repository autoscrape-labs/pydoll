"""Real-Firefox (WebDriver BiDi) integration tests for tab.request.

A throwaway HTTP/1.1 server backs the browser-context fetch client: requests run
in the page's fetch context (reusing cookies/session), the body comes from the
fetch result, and headers + Set-Cookie come from BiDi network events. The BiDi
counterpart of tests/cdp/integration/test_tab_request_integration.py. Assertions
look at the Response (status, json, headers, cookies), not the BiDi commands.
"""

from __future__ import annotations

import json as jsonlib
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio

from pydoll.browser import Firefox


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _send_json(self, payload: dict, extra_headers=None):
        body = jsonlib.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('X-Custom-Resp', 'resp-value')
        for name, value in (extra_headers or []):
            self.send_header(name, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            body = b'<!DOCTYPE html><html><body>home</body></html>'
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/json':
            self._send_json(
                {'method': 'GET', 'ok': True},
                extra_headers=[('Set-Cookie', 'sid=xyz; Path=/; HttpOnly')],
            )
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length).decode() if length else ''
        self._send_json({'method': 'POST', 'received': raw})

    def log_message(self, *args):
        pass


@pytest_asyncio.fixture
async def served_tab(ci_firefox_options):
    port = _free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{port}'
    try:
        async with Firefox(options=ci_firefox_options) as browser:
            tab = await browser.start()
            await tab.go_to(f'{base}/')
            yield tab, base
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.asyncio
async def test_get_returns_status_and_json(served_tab):
    tab, base = served_tab
    response = await tab.request.get(f'{base}/json')
    assert response.status_code == 200
    assert response.ok
    assert response.json() == {'method': 'GET', 'ok': True}


@pytest.mark.asyncio
async def test_post_json_body_reaches_server(served_tab):
    tab, base = served_tab
    response = await tab.request.post(f'{base}/json', json={'hello': 'world'})
    assert response.status_code == 200
    assert response.json()['method'] == 'POST'
    assert jsonlib.loads(response.json()['received']) == {'hello': 'world'}


@pytest.mark.asyncio
async def test_response_headers_captured_from_network_events(served_tab):
    tab, base = served_tab
    response = await tab.request.get(f'{base}/json')
    header_names = {h['name'].lower() for h in response.headers}
    assert 'x-custom-resp' in header_names


@pytest.mark.asyncio
async def test_set_cookie_captured_including_httponly(served_tab):
    tab, base = served_tab
    response = await tab.request.get(f'{base}/json')
    assert any(c['name'] == 'sid' and c['value'] == 'xyz' for c in response.cookies)


@pytest.mark.asyncio
async def test_request_reuses_browser_session_cookies(served_tab):
    tab, base = served_tab
    await tab.request.get(f'{base}/json')  # server sets sid cookie
    sent = await tab.request.get(f'{base}/json')
    sent_cookie_headers = [
        h['value'] for h in sent.request_headers if h['name'].lower() == 'cookie'
    ]
    assert any('sid=xyz' in value for value in sent_cookie_headers)
