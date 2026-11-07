"""Whether the browser is reported alive when its process is frozen.

A stopped process keeps its TCP socket open, so sending a ping frame succeeds;
only waiting for the pong tells a frozen browser from a responsive one.
"""

from __future__ import annotations

import os
import signal
import sys
import time

import pytest

from pydoll.browser.chromium import Chrome

pytestmark = pytest.mark.skipif(
    sys.platform == 'win32', reason='SIGSTOP and SIGCONT are POSIX signals'
)


@pytest.mark.asyncio
async def test_frozen_browser_is_not_reported_as_running(ci_chrome_options):
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    pid = browser._browser_process_manager._process.pid
    try:
        os.kill(pid, signal.SIGSTOP)
        started = time.monotonic()
        assert await browser._connection_handler.ping(timeout=1) is False
        assert time.monotonic() - started < 3
        assert await browser._is_browser_running(timeout=1) is False
    finally:
        os.kill(pid, signal.SIGCONT)

    assert await browser._is_browser_running(timeout=5) is True
    await browser.stop()
