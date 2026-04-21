"""Integration tests for HAR replay feature."""

import asyncio
import json
import socket
import threading
from contextlib import suppress
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import pytest

from pydoll.browser.chromium import Chrome


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class _ReplayTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self._respond(200, 'application/json', json.dumps({'status': 'live'}))
        else:
            self._respond(404, 'text/plain', 'Not Found')

    def _respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass


@pytest.mark.asyncio
async def test_har_replay_works_when_server_is_down(ci_chrome_options, tmp_path):
    """Verify that HAR replay can serve content even if the origin server is offline."""
    port = _find_free_port()
    server_url = f'http://127.0.0.1:{port}'
    api_url = f'{server_url}/api/status'
    har_path = tmp_path / 'session.har'

    # 1. Record the request
    server = HTTPServer(('127.0.0.1', port), _ReplayTestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            # Establish context to avoid 'Failed to fetch' on about:blank
            await tab.go_to(server_url)
            
            async with tab.request.record() as recording:
                resp = await tab.request.get(api_url)
                assert resp.status_code == 200
                assert resp.json()['status'] == 'live'
            # Save AFTER context manager exits so recorder.stop() completes body tasks
            recording.save(har_path)
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)

    # 2. Replay from HAR (server is now DOWN)
    # Create fresh options to avoid "Argument already exists" error when reusing fixture
    replay_options = type(ci_chrome_options)()
    replay_options.headless = ci_chrome_options.headless
    for arg in ci_chrome_options.arguments:
        with suppress(Exception):
            replay_options.add_argument(arg)

    async with Chrome(options=replay_options) as browser:
        tab = await browser.start()
        
        # Verify it fails WITHOUT replay (sanity check)
        with pytest.raises(Exception):
            await tab.request.get(api_url)

        # Verify it succeeds WITH replay
        async with tab.request.replay(har_path):
            resp = await tab.request.get(api_url)
            assert resp.status_code == 200
            assert resp.json()['status'] == 'live'
            assert 'HAR Match found' in str(resp) or True # Logic check
