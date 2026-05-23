"""Real-Firefox (WebDriver BiDi) integration tests for file upload.

Drives a headless Firefox over BiDi and asserts the observable result — the file
reflected on an ``<input type=file>`` — for both upload paths: the proactive
``WebElement.set_input_files`` (``input.setFiles``) and the reactive
``Tab.expect_file_chooser`` (``input.fileDialogOpened`` -> ``input.setFiles`` on
the click that opens the dialog).
"""

from __future__ import annotations

import asyncio

import pytest

PAGE = "data:text/html,<input type='file' id='file-input'>"
_FILES_LEN = "document.getElementById('file-input').files.length"
_FILE_NAME = (
    "(() => { const f = document.getElementById('file-input');"
    " return f.files.length ? f.files[0].name : null; })()"
)


async def _wait_file_set(tab, timeout: float = 5.0) -> None:
    """Poll until the input reports a file (the dialog handler runs asynchronously)."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if (await tab.execute_script(_FILES_LEN) or 0) >= 1:
            return
        await asyncio.sleep(0.1)


class TestFileUpload:
    @pytest.mark.asyncio
    async def test_set_input_files_sets_file_on_input(self, tab, tmp_path):
        upload = tmp_path / 'proactive.txt'
        upload.write_text('payload')
        await tab.go_to(PAGE)

        file_input = await tab.find(id='file-input')
        await file_input.set_input_files(str(upload))

        assert await tab.execute_script(_FILES_LEN) == 1
        assert await tab.execute_script(_FILE_NAME) == 'proactive.txt'

    @pytest.mark.asyncio
    async def test_expect_file_chooser_fills_input_on_click(self, tab, tmp_path):
        upload = tmp_path / 'reactive.txt'
        upload.write_text('payload')
        await tab.go_to(PAGE)

        file_input = await tab.find(id='file-input')
        async with tab.expect_file_chooser(files=upload):
            await file_input.click()
            await _wait_file_set(tab)

        assert await tab.execute_script(_FILES_LEN) == 1
        assert await tab.execute_script(_FILE_NAME) == 'reactive.txt'
