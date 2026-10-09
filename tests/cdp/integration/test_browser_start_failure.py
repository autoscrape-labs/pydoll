"""What ``Chrome.start()`` reports when the browser process cannot come up.

The browser binary is replaced by a small script, so the failure is real
(a spawned process that exits, or one that never answers) without depending
on a broken Chrome.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

from pydoll import Chrome, ChromiumOptions
from pydoll.exceptions import FailedToStartBrowser

pytestmark = pytest.mark.skipif(
    sys.platform == 'win32', reason='shebang scripts need a POSIX shell'
)


def _script(tmp_path, name: str, body: str) -> str:
    path = tmp_path / name
    path.write_text(f'#!/bin/sh\n{body}\n')
    os.chmod(path, 0o755)
    return str(path)


def _options(binary: str, start_timeout: int) -> ChromiumOptions:
    options = ChromiumOptions()
    options.binary_location = binary
    options.headless = True
    options.start_timeout = start_timeout
    return options


@pytest.mark.asyncio
async def test_a_browser_that_exits_reports_its_code_and_stderr_without_waiting(tmp_path):
    binary = _script(
        tmp_path, 'exits.sh', 'echo "cannot open display :0" >&2\necho "giving up" >&2\nexit 3'
    )
    browser = Chrome(options=_options(binary, start_timeout=30))
    started = time.monotonic()
    with pytest.raises(FailedToStartBrowser) as raised:
        await browser.start()
    message = str(raised.value)
    assert time.monotonic() - started < 5
    assert 'exited with code 3 before answering on port' in message
    assert 'cannot open display :0' in message
    assert message.rstrip().endswith('giving up')


@pytest.mark.asyncio
async def test_a_browser_that_never_answers_is_stopped_and_reports_the_timeout(tmp_path):
    binary = _script(tmp_path, 'hangs.sh', 'echo "still starting" >&2\nsleep 60')
    browser = Chrome(options=_options(binary, start_timeout=1))
    with pytest.raises(FailedToStartBrowser) as raised:
        await browser.start()
    message = str(raised.value)
    assert 'did not answer on port' in message
    assert 'within 1s' in message
    assert 'still starting' in message
    process = browser._browser_process_manager._process
    assert process is not None
    assert process.poll() is not None


@pytest.mark.asyncio
async def test_a_missing_binary_is_reported_as_a_start_failure():
    browser = Chrome(options=_options('/nonexistent/chrome', start_timeout=1))
    with pytest.raises(FailedToStartBrowser, match='Could not launch /nonexistent/chrome'):
        await browser.start()
