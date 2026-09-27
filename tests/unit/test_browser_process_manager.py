"""The browser process must never block on its own output pipes."""

from __future__ import annotations

import logging
import sys
import time

from pydoll.browser.managers.browser_process_manager import BrowserProcessManager

CHATTY = (
    'import sys\n'
    'for i in range(4000):\n'
    "    sys.stderr.write('line %d ' % i + 'x' * 60 + '\\n')\n"
)


def test_process_writing_more_than_a_pipe_buffer_to_stderr_still_exits():
    """A child that writes 250 KB to stderr exits instead of blocking on a full pipe."""
    process = BrowserProcessManager._default_process_creator([sys.executable, '-c', CHATTY])
    assert process.wait(timeout=10) == 0


def test_stderr_lines_reach_the_debug_log(caplog):
    logger_name = 'pydoll.browser.managers.browser_process_manager'
    with caplog.at_level(logging.DEBUG, logger=logger_name):
        process = BrowserProcessManager._default_process_creator(
            [sys.executable, '-c', "import sys; sys.stderr.write('hello from chrome\\n')"]
        )
        assert process.wait(timeout=10) == 0
        deadline = time.monotonic() + 5
        while 'hello from chrome' not in caplog.text and time.monotonic() < deadline:
            time.sleep(0.02)
    assert 'hello from chrome' in caplog.text
