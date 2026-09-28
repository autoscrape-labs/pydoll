"""Cross-module wiring tests: Browser with real ChromiumOptions and OptionsManager.

These exercise how Browser, ChromiumOptionsManager and ChromiumOptions integrate
during construction — real objects, no browser process and no I/O — so they run
with the fast unit suite while still covering the seams between modules.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.managers import BrowserProcessManager
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.exceptions import FailedToStartBrowser, InvalidOptionsObject
from tests.unit.conftest import FakeConnection


class _FakeProcess:
    """Stand-in for the spawned browser subprocess (nothing really runs)."""

    def __init__(self, exit_code: int | None = None):
        self.pid = 4242
        self.terminated = False
        self.exit_code = exit_code

    def poll(self):
        return self.exit_code

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


def test_chrome_applies_default_arguments_to_real_options():
    options = ChromiumOptions()
    browser = Chrome(options=options)
    assert browser.options is options
    assert '--no-first-run' in options.arguments
    assert '--no-default-browser-check' in options.arguments


def test_chrome_preserves_user_supplied_options():
    options = ChromiumOptions()
    options.add_argument('--window-size=800,600')
    options.headless = True
    browser = Chrome(options=options)
    assert browser.options.headless is True
    assert '--window-size=800,600' in browser.options.arguments


def test_options_manager_creates_defaults_when_none():
    options = ChromiumOptionsManager(None).initialize_options()
    assert isinstance(options, ChromiumOptions)
    assert '--no-first-run' in options.arguments


def test_options_manager_applies_defaults_to_supplied_options():
    given = ChromiumOptions()
    returned = ChromiumOptionsManager(given).initialize_options()
    assert returned is given
    assert '--no-default-browser-check' in returned.arguments


def test_options_manager_rejects_non_chromium_options():
    with pytest.raises(InvalidOptionsObject):
        ChromiumOptionsManager('not-options').initialize_options()


@pytest.mark.asyncio
async def test_browser_start_and_stop_orchestrate_process_and_connection(fake_conn):
    fake_process = _FakeProcess()
    browser = Chrome()
    browser.options.binary_location = '/usr/bin/true'
    browser._connection_handler = fake_conn
    browser._browser_process_manager = BrowserProcessManager(
        process_creator=lambda command: fake_process
    )
    fake_conn.set_response(
        'Target.getTargets',
        {'targetInfos': [{'targetId': 'tab-1', 'type': 'page', 'url': 'about:blank'}]},
    )

    tab = await browser.start()
    assert isinstance(tab, Tab)
    assert tab._target_id == 'tab-1'

    await browser.stop()
    assert fake_process.terminated is True


@pytest.mark.asyncio
async def test_a_browser_that_exits_before_answering_fails_at_once_with_its_exit_code():
    fake_process = _FakeProcess(exit_code=3)
    browser = Chrome()
    browser.options.binary_location = '/usr/bin/true'
    browser.options.start_timeout = 30
    browser._connection_handler = _DeadConnection()
    browser._browser_process_manager = BrowserProcessManager(
        process_creator=lambda command: fake_process
    )

    with pytest.raises(FailedToStartBrowser, match='exited with code 3 before answering on port'):
        await browser.start()
    assert fake_process.terminated is False


@pytest.mark.asyncio
async def test_a_browser_that_never_answers_is_stopped_and_reported_with_the_timeout():
    fake_process = _FakeProcess()
    browser = Chrome()
    browser.options.binary_location = '/usr/bin/true'
    browser.options.start_timeout = 0.2
    browser._connection_handler = _DeadConnection()
    browser._browser_process_manager = BrowserProcessManager(
        process_creator=lambda command: fake_process
    )

    with pytest.raises(FailedToStartBrowser, match='did not answer on port .* within 0.2s'):
        await browser.start()
    assert fake_process.terminated is True


class _DeadConnection(FakeConnection):
    """A connection whose endpoint never answers, counting the attempts."""

    def __init__(self):
        super().__init__()
        self.pings = 0

    async def ping(self) -> bool:
        self.pings += 1
        return False


@pytest.mark.asyncio
async def test_readiness_poll_backs_off_so_a_dead_browser_costs_few_attempts():
    """``stop()`` and ``__aexit__`` poll the endpoint through this check; a fixed
    20 ms pause made a browser that was already gone cost hundreds of connects."""
    connection = _DeadConnection()
    browser = Chrome()
    browser._connection_handler = connection
    assert await browser._is_browser_running(timeout=0.5) is False
    assert 2 <= connection.pings <= 10
