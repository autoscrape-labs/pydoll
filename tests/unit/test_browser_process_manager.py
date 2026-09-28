"""The browser process must never block on its own output pipes."""

from __future__ import annotations

import logging
import os
import sys
import time

import pytest

from pydoll.browser.managers.browser_process_manager import BrowserProcessManager
from pydoll.exceptions import FailedToStartBrowser

CHATTY = (
    "import sys\nfor i in range(4000):\n    sys.stderr.write('line %d ' % i + 'x' * 60 + '\\n')\n"
)


def test_process_writing_more_than_a_pipe_buffer_to_stderr_still_exits():
    """A child that writes 250 KB to stderr exits instead of blocking on a full pipe."""
    process = BrowserProcessManager()._default_process_creator([sys.executable, '-c', CHATTY])
    assert process.wait(timeout=10) == 0


def test_stderr_lines_reach_the_debug_log(caplog):
    logger_name = 'pydoll.browser.managers.browser_process_manager'
    with caplog.at_level(logging.DEBUG, logger=logger_name):
        process = BrowserProcessManager()._default_process_creator([
            sys.executable,
            '-c',
            "import sys; sys.stderr.write('hello from chrome\\n')",
        ])
        assert process.wait(timeout=10) == 0
        deadline = time.monotonic() + 5
        while 'hello from chrome' not in caplog.text and time.monotonic() < deadline:
            time.sleep(0.02)
    assert 'hello from chrome' in caplog.text


def _script(tmp_path, body: str) -> str:
    path = tmp_path / 'browser.sh'
    path.write_text(f'#!/bin/sh\n{body}\n')
    os.chmod(path, 0o755)
    return str(path)


@pytest.mark.skipif(sys.platform == 'win32', reason='shebang scripts need a POSIX shell')
def test_a_process_that_exits_leaves_its_code_and_last_stderr_lines_behind(tmp_path):
    manager = BrowserProcessManager()
    manager.start_browser_process(
        _script(tmp_path, 'echo "cannot open display" >&2\necho exiting >&2\nexit 3'), 9222, []
    )
    assert manager._process is not None
    manager._process.wait(timeout=10)
    assert manager.exit_code() == 3
    assert manager.recent_stderr().splitlines() == ['cannot open display', 'exiting']


@pytest.mark.skipif(sys.platform == 'win32', reason='shebang scripts need a POSIX shell')
def test_the_tail_keeps_only_the_last_lines(tmp_path):
    manager = BrowserProcessManager()
    manager.start_browser_process(
        _script(tmp_path, 'i=0\nwhile [ $i -lt 100 ]; do echo "line $i" >&2; i=$((i+1)); done'),
        9222,
        [],
    )
    assert manager._process is not None
    manager._process.wait(timeout=10)
    lines = manager.recent_stderr().splitlines()
    assert len(lines) == 40
    assert lines[-1] == 'line 99'


def test_a_missing_executable_is_a_start_failure_not_an_os_error():
    with pytest.raises(FailedToStartBrowser, match='Could not launch /nonexistent/chrome'):
        BrowserProcessManager().start_browser_process('/nonexistent/chrome', 9222, [])
