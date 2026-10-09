"""Real-Firefox (WebDriver BiDi) integration tests for tab.request.record() (HAR).

A throwaway HTTP/1.1 server serves a page that fires a same-origin fetch on load.
Recording captures both the navigation and the fetch as HAR entries, including
response bodies (via a BiDi data collector) and Set-Cookie. The BiDi counterpart
of tests/cdp/integration/test_har_recording_integration.py.
"""

from __future__ import annotations

import asyncio
import base64
import json as jsonlib
import socket
import threading
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio

from pydoll.browser.requests import HarCapture

_API_PAYLOAD = {'msg': 'Hello from BiDi', 'items': ['Alice', 'Bob']}

_PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body><div id="status">waiting</div>
<script>
  window.addEventListener('load', async () => {
    await fetch('/api/data').catch(() => {});
    document.getElementById('status').textContent = 'done';
  });
</script></body></html>"""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        if self.path == '/':
            self._send('text/html', _PAGE_HTML.encode())
        elif self.path == '/api/data':
            self._send(
                'application/json',
                jsonlib.dumps(_API_PAYLOAD).encode(),
                extra=[('Set-Cookie', 'har=1; Path=/; HttpOnly')],
            )
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()

    def _send(self, content_type, body, extra=None):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        for name, value in (extra or []):
            self.send_header(name, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest_asyncio.fixture(loop_scope='module')
async def served_tab(firefox_browser):
    port = _free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{port}'
    context_id = await firefox_browser.create_browser_context()
    tab = await firefox_browser.new_tab(browser_context_id=context_id)
    try:
        yield tab, base
    finally:
        with suppress(Exception):
            await firefox_browser.delete_browser_context(context_id)
        server.shutdown()
        server.server_close()


async def _wait_for_entry(capture: HarCapture, substring: str, timeout: float = 10.0):
    """Poll the recording until an entry's URL contains substring (or time out)."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        match = next((e for e in capture.entries if substring in e['request']['url']), None)
        if match:
            return match
        await asyncio.sleep(0.1)
    return None


def _entry_text(entry: dict) -> str:
    content = entry['response']['content']
    text = content.get('text', '')
    if content.get('encoding') == 'base64':
        return base64.b64decode(text).decode('utf-8', 'replace')
    return text


@pytest.mark.asyncio(loop_scope='module')
async def test_record_captures_navigation_and_fetch(served_tab):
    tab, base = served_tab
    async with tab.request.record() as capture:
        await tab.go_to(f'{base}/')
        assert await _wait_for_entry(capture, '/api/data') is not None

    urls = [e['request']['url'] for e in capture.entries]
    assert any(u.rstrip('/') == base for u in urls)
    assert any('/api/data' in u for u in urls)


@pytest.mark.asyncio(loop_scope='module')
async def test_record_captures_response_body(served_tab):
    tab, base = served_tab
    async with tab.request.record() as capture:
        await tab.go_to(f'{base}/')
        await _wait_for_entry(capture, '/api/data')

    api_entry = next(e for e in capture.entries if '/api/data' in e['request']['url'])
    assert api_entry['response']['status'] == 200
    assert 'Hello from BiDi' in _entry_text(api_entry)


@pytest.mark.asyncio(loop_scope='module')
async def test_record_captures_set_cookie(served_tab):
    tab, base = served_tab
    async with tab.request.record() as capture:
        await tab.go_to(f'{base}/')
        await _wait_for_entry(capture, '/api/data')

    api_entry = next(e for e in capture.entries if '/api/data' in e['request']['url'])
    cookie_names = {c['name'] for c in api_entry['response']['cookies']}
    assert 'har' in cookie_names


@pytest.mark.asyncio(loop_scope='module')
async def test_save_writes_valid_har_file(served_tab, tmp_path):
    tab, base = served_tab
    async with tab.request.record() as capture:
        await tab.go_to(f'{base}/')
        await _wait_for_entry(capture, '/api/data')

    out = tmp_path / 'flow.har'
    capture.save(out)
    har = jsonlib.loads(out.read_text())
    assert har['log']['version'] == '1.2'
    assert har['log']['creator']['name'] == 'pydoll'
    assert len(har['log']['entries']) >= 1
