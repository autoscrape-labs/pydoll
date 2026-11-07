"""What a tab command raises once the browser it talks to is gone.

Code that catches ``PydollException`` or ``ConnectionException`` to notice a
lost browser has to see a Pydoll exception here, not the socket layer's
``OSError``.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import time

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.tab import Tab
from pydoll.commands import TargetCommands
from pydoll.exceptions import ConnectionException, ConnectionFailed, PydollException


@pytest.mark.asyncio
async def test_tab_commands_after_the_browser_died_raise_connection_failed(
    ci_chrome_options, tmp_path
):
    ci_chrome_options.add_argument(f'--user-data-dir={tmp_path}')
    browser = Chrome(options=ci_chrome_options)
    tab = await browser.start()
    try:
        await tab.execute_script('return 1')
        process = browser._browser_process_manager._process
        process.kill()
        process.wait(timeout=10)
        await asyncio.wait_for(tab._connection_handler.wait_disconnected(), timeout=5)
        for _ in range(3):
            with pytest.raises(ConnectionFailed) as raised:
                await tab.execute_script('return 1 + 1')
            assert isinstance(raised.value, PydollException)
            assert isinstance(raised.value.__cause__, OSError)
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_tab_for_a_target_that_does_not_exist_raises_connection_failed(browser):
    tab = Tab(browser, target_id='0' * 32, connection_port=browser._connection_port)
    with pytest.raises(ConnectionFailed):
        await tab.execute_script('return 1')


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == 'win32', reason='SIGSTOP is a POSIX signal')
async def test_a_command_that_must_reconnect_to_a_frozen_browser_fails_in_bounded_time(
    ci_chrome_options,
):
    """A stopped Chrome still accepts TCP connections, so the address lookup
    and the handshake must time out instead of waiting for an answer."""
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    pid = browser._browser_process_manager._process.pid
    await browser.close()
    os.kill(pid, signal.SIGSTOP)
    try:
        started = time.monotonic()
        with pytest.raises(ConnectionException):
            await browser.execute_command(TargetCommands.get_targets(), timeout=5)
        elapsed = time.monotonic() - started
    finally:
        os.kill(pid, signal.SIGCONT)
        await browser.stop()

    assert elapsed < 20
