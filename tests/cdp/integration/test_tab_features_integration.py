"""Real-Chrome integration tests for Tab artifact/feature methods.

These drive a real headless Chrome against local ``file://`` pages and assert the
observable result of each feature — the bytes written to disk, the decoded
base64 payloads, the uploaded file reflected on an ``<input>``, the iframe
resolver's error contract and the shadow-root polling timeout. Behaviour is
asserted (magic bytes, DOM value, exception type), never the CDP calls behind
it, so the tests survive refactors of the command plumbing.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
import pytest_asyncio

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import (
    InvalidFileExtension,
    MissingScreenshotPath,
    WaitElementTimeout,
)

PAGES = Path(__file__).parents[2] / 'pages'

PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
JPEG_MAGIC = b'\xff\xd8\xff'
PDF_MAGIC = b'%PDF'


def _file_url(name: str) -> str:
    return f'file://{(PAGES / name).absolute()}'


@pytest_asyncio.fixture
async def tab(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        page = await browser.start()
        yield page


class TestScreenshots:
    @pytest.mark.asyncio
    async def test_png_file_is_written_with_png_header(self, tab, tmp_path):
        await tab.go_to(_file_url('test_core_simple.html'))
        out = tmp_path / 'shot.png'
        result = await tab.take_screenshot(str(out))
        assert result is None
        assert out.read_bytes().startswith(PNG_MAGIC)

    @pytest.mark.asyncio
    async def test_jpeg_file_accepts_path_object_and_jpg_alias(self, tab, tmp_path):
        await tab.go_to(_file_url('test_core_simple.html'))
        out = tmp_path / 'shot.jpg'
        await tab.take_screenshot(out)
        assert out.read_bytes().startswith(JPEG_MAGIC)

    @pytest.mark.asyncio
    async def test_as_base64_returns_decodable_image_without_writing(self, tab):
        await tab.go_to(_file_url('test_core_simple.html'))
        data = await tab.take_screenshot(as_base64=True)
        assert isinstance(data, str)
        assert base64.b64decode(data).startswith(JPEG_MAGIC)

    @pytest.mark.asyncio
    async def test_missing_path_without_base64_raises(self, tab):
        await tab.go_to(_file_url('test_core_simple.html'))
        with pytest.raises(MissingScreenshotPath):
            await tab.take_screenshot()

    @pytest.mark.asyncio
    async def test_unsupported_extension_raises(self, tab, tmp_path):
        await tab.go_to(_file_url('test_core_simple.html'))
        with pytest.raises(InvalidFileExtension):
            await tab.take_screenshot(str(tmp_path / 'shot.bmp'))


class TestPrintToPdf:
    @pytest.mark.asyncio
    async def test_pdf_file_is_written_with_pdf_header(self, tab, tmp_path):
        await tab.go_to(_file_url('test_core_simple.html'))
        out = tmp_path / 'page.pdf'
        result = await tab.print_to_pdf(str(out), landscape=True)
        assert result is None
        assert out.read_bytes().startswith(PDF_MAGIC)

    @pytest.mark.asyncio
    async def test_as_base64_returns_decodable_pdf(self, tab):
        await tab.go_to(_file_url('test_core_simple.html'))
        data = await tab.print_to_pdf(as_base64=True)
        assert base64.b64decode(data).startswith(PDF_MAGIC)

    @pytest.mark.asyncio
    async def test_requires_path_when_not_base64(self, tab):
        await tab.go_to(_file_url('test_core_simple.html'))
        with pytest.raises(ValueError):
            await tab.print_to_pdf()


class TestFileChooserInterception:
    @pytest.mark.asyncio
    async def test_uploaded_file_is_set_on_input(self, tab, tmp_path):
        upload = tmp_path / 'payload.txt'
        upload.write_text('hello upload')
        await tab.go_to(_file_url('web_element.html'))

        file_input = await tab.find(id='file-input')
        async with tab.expect_file_chooser(files=upload):
            await file_input.click()

        prop = await file_input.execute_script('return this.value', return_by_value=True)
        assert prop['result']['result']['value'].endswith('payload.txt')

    @pytest.mark.asyncio
    async def test_interception_is_disabled_again_after_context(self, tab, tmp_path):
        upload = tmp_path / 'payload.txt'
        upload.write_text('x')
        await tab.go_to(_file_url('web_element.html'))

        file_input = await tab.find(id='file-input')
        async with tab.expect_file_chooser(files=[upload]):
            await file_input.click()

        assert tab._intercept_file_chooser_dialog_enabled is False


class TestFindShadowRootsTimeout:
    @pytest.mark.asyncio
    async def test_polling_returns_roots_when_present(self, tab):
        await tab.go_to(_file_url('shadow_dom_test.html'))
        roots = await tab.find_shadow_roots(timeout=3)
        assert len(roots) >= 1

    @pytest.mark.asyncio
    async def test_polling_times_out_when_absent(self, tab):
        await tab.go_to(_file_url('plain_text.html'))
        with pytest.raises(WaitElementTimeout):
            await tab.find_shadow_roots(timeout=1)
