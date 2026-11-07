"""stop() and async with end what start() launched, whether or not the browser answers.

A crashed browser cannot take ``Browser.close`` and a frozen one never answers
it, but the process start() launched still has to end and its temporary
profile has to go, or a long-running program keeps one of each per crash.
"""

from __future__ import annotations

import os
import signal
import sys
import time

import pytest

from pydoll.browser.chromium import Chrome


def _profile_of(browser: Chrome) -> str:
    """The --user-data-dir start() created for the browser."""
    prefix = '--user-data-dir='
    return next(arg[len(prefix) :] for arg in browser.options.arguments if arg.startswith(prefix))


@pytest.mark.asyncio
async def test_stop_cleans_up_a_browser_whose_process_was_killed(ci_chrome_options):
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    process = browser._browser_process_manager._process
    profile = _profile_of(browser)
    process.kill()
    process.wait(timeout=10)

    started = time.monotonic()
    await browser.stop()

    assert time.monotonic() - started < 5
    assert not os.path.isdir(profile)


@pytest.mark.asyncio
async def test_async_with_cleans_up_a_browser_whose_process_was_killed(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as browser:
        await browser.start()
        process = browser._browser_process_manager._process
        profile = _profile_of(browser)
        process.kill()
        process.wait(timeout=10)

    assert not os.path.isdir(profile)


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == 'win32', reason='SIGSTOP is a POSIX signal')
async def test_stop_ends_a_frozen_browser_and_removes_its_profile(ci_chrome_options):
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    process = browser._browser_process_manager._process
    profile = _profile_of(browser)
    os.kill(process.pid, signal.SIGSTOP)
    try:
        started = time.monotonic()
        await browser.stop()
        elapsed = time.monotonic() - started
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGCONT)
            process.kill()
            process.wait(timeout=10)

    assert elapsed < 10
    assert process.poll() is not None
    assert not os.path.isdir(profile)
