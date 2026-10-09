"""Real-Firefox (WebDriver BiDi) integration tests for Tab.expect_download.

A throwaway ``ThreadingHTTPServer`` serves a page with a downloadable attachment.
Clicking the link inside the ``expect_download`` block must route the file to the
managed directory and expose it through the handle — the BiDi counterpart of
tests/cdp/integration/test_tab_io_integration.py::TestExpectDownload. Assertions
look at the downloaded bytes and the saved file, not the BiDi commands used.
"""

from __future__ import annotations

import base64
import socket
import threading
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import pytest_asyncio

DOWNLOAD_BODY = b'downloaded content from server'

_INDEX_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
    '<body><a id="download-link" href="/download" download="hello.txt">download</a>'
    '</body></html>'
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


class _DownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            body = _INDEX_HTML.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/download':
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', 'attachment; filename="hello.txt"')
            self.send_header('Content-Length', str(len(DOWNLOAD_BODY)))
            self.end_headers()
            self.wfile.write(DOWNLOAD_BODY)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


@pytest_asyncio.fixture(loop_scope='module')
async def served_tab(firefox_browser):
    port = _find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), _DownloadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{port}'
    context_id = await firefox_browser.create_browser_context()
    tab = await firefox_browser.new_tab(browser_context_id=context_id)
    try:
        await tab.go_to(f'{base}/')
        yield tab, base
    finally:
        with suppress(Exception):
            await firefox_browser.delete_browser_context(context_id)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio(loop_scope='module')
async def test_download_to_temp_dir_is_readable_inside_context(served_tab):
    tab, _ = served_tab
    async with tab.expect_download(timeout=30) as handle:
        link = await tab.find(id='download-link')
        await link.click()
        data = await handle.read_bytes()
        assert data == DOWNLOAD_BODY
        assert handle.file_path is not None


@pytest.mark.asyncio(loop_scope='module')
async def test_download_base64_matches_bytes(served_tab):
    tab, _ = served_tab
    async with tab.expect_download(timeout=30) as handle:
        link = await tab.find(id='download-link')
        await link.click()
        b64 = await handle.read_base64()
    assert base64.b64decode(b64) == DOWNLOAD_BODY


@pytest.mark.asyncio(loop_scope='module')
async def test_keep_file_at_persists_after_context(served_tab, tmp_path):
    tab, _ = served_tab
    target = tmp_path / 'downloads'
    async with tab.expect_download(keep_file_at=target, timeout=30) as handle:
        link = await tab.find(id='download-link')
        await link.click()
        await handle.wait_finished()

    saved = target / 'hello.txt'
    assert saved.exists()
    assert saved.read_bytes() == DOWNLOAD_BODY
