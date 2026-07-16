"""Real-Chrome integration tests for Tab I/O over a local HTTP server.

A throwaway ``ThreadingHTTPServer`` serves a small page wired to external assets (CSS with
a ``url()`` background, JS and images) plus a downloadable attachment. Against it
we exercise the heavy I/O paths that need a real origin and real network
fetches: ``save_bundle`` (both rewrite and inline modes), ``expect_download``
with its file handle, and the cookie round-trip. Assertions look at the produced
artifacts — the contents of the zip, the downloaded bytes, the cookies returned
— not the CDP commands used to obtain them.
"""

from __future__ import annotations

import base64
import io
import socket
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import InvalidFileExtension

PNG_1PX = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)
APP_JS = 'window.__loaded = true;'
STYLE_CSS = 'body { margin: 0; background-image: url("/bg.png"); }'
DOWNLOAD_BODY = b'downloaded content from server'


def _index_html(base: str, *, absolute_assets: bool) -> str:
    prefix = base if absolute_assets else ''
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<link rel="stylesheet" href="{prefix}/style.css"></head>'
        '<body><h1>Bundle me</h1>'
        f'<img id="pic" src="{prefix}/img.png" alt="pic">'
        '<a id="download-link" href="/download" download="hello.txt">download</a>'
        f'<script src="{prefix}/app.js"></script></body></html>'
    )


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def _make_handler(*, absolute_assets: bool):
    class _AssetHandler(BaseHTTPRequestHandler):
        def _send(self, content_type, body):
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            base = f'http://{self.headers["Host"]}'
            if self.path == '/':
                self._send('text/html', _index_html(base, absolute_assets=absolute_assets).encode())
            elif self.path == '/style.css':
                self._send('text/css', STYLE_CSS.encode())
            elif self.path == '/app.js':
                self._send('text/javascript', APP_JS.encode())
            elif self.path in ('/img.png', '/bg.png'):
                self._send('image/png', PNG_1PX)
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

    return _AssetHandler


def _serve(handler_cls):
    port = _find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f'http://127.0.0.1:{port}'


@pytest_asyncio.fixture
async def served_tab(ci_chrome_options):
    server, thread, base = _serve(_make_handler(absolute_assets=True))
    try:
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(f'{base}/')
            yield tab, base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest_asyncio.fixture
async def relative_served_tab(ci_chrome_options):
    server, thread, base = _serve(_make_handler(absolute_assets=False))
    try:
        async with Chrome(options=ci_chrome_options) as browser:
            tab = await browser.start()
            await tab.go_to(f'{base}/')
            yield tab, base
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _zip_names(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.namelist()


def _zip_read(data: bytes, name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read(name)


class TestSaveBundle:
    @pytest.mark.asyncio
    async def test_rewrite_mode_writes_index_and_assets(self, served_tab, tmp_path):
        tab, _ = served_tab
        out = tmp_path / 'bundle.zip'
        await tab.save_bundle(str(out))

        data = out.read_bytes()
        names = _zip_names(data)
        assert 'index.html' in names
        assert [n for n in names if n.startswith('assets/')]

        index = _zip_read(data, 'index.html').decode()
        assert 'assets/' in index
        assert 'http://127.0.0.1' not in index

    @pytest.mark.asyncio
    async def test_rewrite_mode_bundles_css_referenced_background(self, served_tab, tmp_path):
        tab, _ = served_tab
        out = tmp_path / 'bundle.zip'
        await tab.save_bundle(str(out))

        data = out.read_bytes()
        css_entries = [n for n in _zip_names(data) if n.endswith('.css')]
        assert css_entries
        css = _zip_read(data, css_entries[0]).decode()
        assert 'url("/bg.png")' not in css

    @pytest.mark.asyncio
    async def test_inline_mode_embeds_everything_in_index(self, served_tab, tmp_path):
        tab, _ = served_tab
        out = tmp_path / 'inline.zip'
        await tab.save_bundle(str(out), inline_assets=True)

        data = out.read_bytes()
        assert _zip_names(data) == ['index.html']

        index = _zip_read(data, 'index.html').decode()
        assert '<style>' in index
        assert 'data:image/png;base64,' in index
        assert 'window.__loaded' in index

    @pytest.mark.asyncio
    async def test_non_zip_extension_is_rejected(self, served_tab, tmp_path):
        tab, _ = served_tab
        with pytest.raises(InvalidFileExtension):
            await tab.save_bundle(str(tmp_path / 'bundle.tar'))

    @pytest.mark.xfail(
        reason='BUG: rewrite_html_urls does a literal string replace of absolute resource '
        'URLs, so relative/root-relative HTML asset refs are bundled but never rewritten, '
        'leaving index.html pointing at the original (broken offline) URLs.',
        strict=True,
    )
    @pytest.mark.asyncio
    async def test_relative_html_urls_are_rewritten(self, relative_served_tab, tmp_path):
        tab, _ = relative_served_tab
        out = tmp_path / 'bundle.zip'
        await tab.save_bundle(str(out))

        index = _zip_read(out.read_bytes(), 'index.html').decode()
        assert '/style.css' not in index
        assert 'assets/' in index


class TestExpectDownload:
    @pytest.mark.asyncio
    async def test_download_to_temp_dir_is_readable_inside_context(self, served_tab):
        tab, _ = served_tab
        async with tab.expect_download(timeout=30) as handle:
            link = await tab.find(id='download-link')
            await link.click()
            data = await handle.read_bytes()
            assert data == DOWNLOAD_BODY
            assert handle.file_path is not None

    @pytest.mark.asyncio
    async def test_download_base64_matches_bytes(self, served_tab):
        tab, _ = served_tab
        async with tab.expect_download(timeout=30) as handle:
            link = await tab.find(id='download-link')
            await link.click()
            b64 = await handle.read_base64()
        assert base64.b64decode(b64) == DOWNLOAD_BODY

    @pytest.mark.asyncio
    async def test_keep_file_at_persists_after_context(self, served_tab, tmp_path):
        tab, _ = served_tab
        target = tmp_path / 'downloads'
        async with tab.expect_download(keep_file_at=target, timeout=30) as handle:
            link = await tab.find(id='download-link')
            await link.click()
            await handle.wait_finished()

        saved = target / 'hello.txt'
        assert saved.exists()
        assert saved.read_bytes() == DOWNLOAD_BODY


class TestCookies:
    @pytest.mark.asyncio
    async def test_set_get_and_delete_round_trip(self, served_tab):
        tab, base = served_tab
        await tab.set_cookies([{'name': 'session', 'value': 'abc123', 'url': base}])

        cookies = await tab.get_cookies()
        assert any(c['name'] == 'session' and c['value'] == 'abc123' for c in cookies)

        await tab.delete_all_cookies()
        remaining = await tab.get_cookies()
        assert not any(c['name'] == 'session' for c in remaining)
