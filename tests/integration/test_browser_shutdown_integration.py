"""stop() and async with end what start() launched, whether or not the browser answers.

A crashed browser cannot take ``Browser.close`` and a frozen one never answers
it, but the process start() launched still has to end and its temporary
profile has to go, or a long-running program keeps one of each per crash.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import time
from contextlib import suppress

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.exceptions import BrowserNotRunning, FailedToStartBrowser, PydollException
from pydoll.protocol.page.events import PageEvent
from pydoll.utils import get_browser_ws_address
from tests.browser_options import ci_options


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


@pytest.mark.asyncio
async def test_a_second_start_is_refused_and_stop_ends_the_first_browser(ci_chrome_options):
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    process = browser._browser_process_manager._process
    profile = _profile_of(browser)
    try:
        with pytest.raises(FailedToStartBrowser, match='already running'):
            await browser.start()
    finally:
        await browser.stop()

    assert process.poll() is not None
    assert not os.path.isdir(profile)


@pytest.mark.asyncio
async def test_a_start_that_fails_after_the_port_opens_ends_the_process_and_profile(
    ci_chrome_options,
):
    browser = Chrome(options=ci_chrome_options)
    list_targets = browser.get_targets

    async def get_targets_of_a_browser_that_just_died():
        """Kill Chrome between the start check and Target.getTargets."""
        process = browser._browser_process_manager._process
        process.kill()
        process.wait(timeout=10)
        return await list_targets()

    browser.get_targets = get_targets_of_a_browser_that_just_died
    with pytest.raises(PydollException):
        await browser.start()

    assert browser._browser_process_manager._process.poll() is not None
    assert not os.path.isdir(_profile_of(browser))


@pytest.mark.asyncio
async def test_a_start_cut_short_by_a_timeout_leaves_no_browser_behind(ci_chrome_options):
    browser = Chrome(options=ci_chrome_options)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(browser.start(), 0.3)

    process = browser._browser_process_manager._process
    assert process is None or process.poll() is not None
    assert not os.path.isdir(_profile_of(browser))


@pytest.mark.asyncio
async def test_a_cancelled_stop_still_ends_the_process_and_removes_the_profile(
    ci_chrome_options,
):
    """Where the browser stops faster than the cancellation lands (Windows), stop()
    simply completes; either way nothing is left behind."""
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    process = browser._browser_process_manager._process
    profile = _profile_of(browser)
    stopping = asyncio.create_task(browser.stop())
    await asyncio.sleep(0.02)
    stopping.cancel()
    with suppress(asyncio.CancelledError):
        await stopping

    assert process.poll() is not None
    assert not os.path.isdir(profile)


@pytest.mark.asyncio
async def test_close_closes_the_connections_of_the_tabs_it_handed_out(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as owner:
        await owner.start()
        client = Chrome(options=ci_options())
        tab = await client.connect(await get_browser_ws_address(owner._connection_port))
        await tab.execute_script('return 1')
        callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, lambda _event: None)

        await client.close()

        assert await tab.remove_callback(callback_id) is False


@pytest.mark.asyncio
async def test_start_refuses_a_port_another_browser_already_answers_on(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as first:
        tab = await first.start()
        second = Chrome(options=ci_options(), connection_port=first._connection_port)

        with pytest.raises(FailedToStartBrowser, match='already in use'):
            await second.start()

        assert second._browser_process_manager._process is None
        response = await tab.execute_script('return 1 + 1')
        assert response['result']['result']['value'] == 2


@pytest.mark.asyncio
async def test_a_refused_start_leaves_the_browser_on_the_port_running(ci_chrome_options):
    async with Chrome(options=ci_chrome_options) as first:
        tab = await first.start()
        async with Chrome(options=ci_options(), connection_port=first._connection_port) as second:
            with pytest.raises(FailedToStartBrowser, match='already in use'):
                await second.start()
            with pytest.raises(BrowserNotRunning):
                await second.stop()

        response = await tab.execute_script('return 1 + 1')
        assert response['result']['result']['value'] == 2


@pytest.mark.asyncio
async def test_the_same_browser_starts_again_on_its_port_after_stop(ci_chrome_options):
    """The stopped browser leaves its port in TIME_WAIT, which no longer listens."""
    browser = Chrome(options=ci_chrome_options)
    await browser.start()
    await browser.stop()
    try:
        tab = await browser.start()
        response = await tab.execute_script('return 1 + 1')
    finally:
        await browser.stop()

    assert response['result']['result']['value'] == 2

