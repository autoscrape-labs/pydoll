"""Real-Firefox (WebDriver BiDi) integration tests for network introspection.

tab.get_network_logs() captures requests (subscribing + starting a response data
collector on first use); tab.get_network_response_body() reads bodies back from
that collector. The BiDi counterpart of CDP's network log / getResponseBody.
"""

from __future__ import annotations

import asyncio
import json as jsonlib
import socket
import threading
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio

from pydoll.exceptions import NetworkEventsNotEnabled

_API_PAYLOAD = {'msg': 'Hello from introspection'}

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
            body, ctype = _PAGE_HTML.encode(), 'text/html'
        elif self.path == '/api/data':
            body, ctype = jsonlib.dumps(_API_PAYLOAD).encode(), 'application/json'
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
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


async def _wait_for_page_fetch_done(tab, timeout: float = 10.0):
    """Poll the page until its on-load fetch settled (#status == 'done')."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        status = await tab.execute_script(
            "return document.getElementById('status')?.textContent"
        )
        if status == 'done':
            return
        await asyncio.sleep(0.1)


@pytest.mark.asyncio(loop_scope='module')
async def test_get_network_logs_captures_requests(served_tab):
    tab, base = served_tab
    await tab.get_network_logs()  # enable capture before the traffic
    await tab.go_to(f'{base}/')
    await _wait_for_page_fetch_done(tab)

    logs = await tab.get_network_logs()
    urls = [log['params']['request']['url'] for log in logs]
    assert any('/api/data' in u for u in urls)


@pytest.mark.asyncio(loop_scope='module')
async def test_get_network_logs_filter(served_tab):
    tab, base = served_tab
    await tab.get_network_logs()
    await tab.go_to(f'{base}/')
    await _wait_for_page_fetch_done(tab)

    logs = await tab.get_network_logs(filter='/api/data')
    assert logs
    assert all('/api/data' in log['params']['request']['url'] for log in logs)


@pytest.mark.asyncio(loop_scope='module')
async def test_get_network_response_body(served_tab):
    tab, base = served_tab
    await tab.get_network_logs()  # enables the response data collector too
    await tab.go_to(f'{base}/')
    await _wait_for_page_fetch_done(tab)

    logs = await tab.get_network_logs(filter='/api/data')
    request_id = logs[0]['params']['request']['request']
    body = await tab.get_network_response_body(request_id)
    assert 'Hello from introspection' in body


@pytest.mark.asyncio(loop_scope='module')
async def test_get_network_response_body_requires_enable(served_tab):
    tab, _ = served_tab
    with pytest.raises(NetworkEventsNotEnabled):
        await tab.get_network_response_body('no-such-request')
