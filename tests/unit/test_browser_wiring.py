"""Cross-module wiring tests: Browser with real ChromiumOptions and OptionsManager.

These exercise how Browser, ChromiumOptionsManager and ChromiumOptions integrate
during construction — real objects, no browser process and no I/O — so they run
with the fast unit suite while still covering the seams between modules.
"""

from __future__ import annotations

import os

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.managers import BrowserProcessManager, TempDirectoryManager
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.browser.tab import Tab
from pydoll.exceptions import (
    BrowserNotRunning,
    ConnectionFailed,
    FailedToStartBrowser,
    InvalidOptionsObject,
)
from pydoll.protocol.browser.methods import BrowserMethod
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.target.methods import TargetMethod
from tests.unit.conftest import FakeConnection


class _FakeProcess:
    """Stand-in for the spawned browser subprocess (nothing really runs)."""

    def __init__(self, exit_code: int | None = None):
        self.pid = 4242
        self.terminated = False
        self.exit_code = exit_code
        self.signals: list[int] = []

    def poll(self):
        return self.exit_code

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True

    def send_signal(self, signal_number):
        self.signals.append(signal_number)


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
    """A connection whose endpoint never answers, counting the attempts to reach it.

    Like a real handler on a closed port, a ping reports False and a command
    raises ConnectionFailed.
    """

    def __init__(self):
        super().__init__()
        self.attempts = 0

    async def ping(self, timeout: float = 5) -> bool:
        self.attempts += 1
        return False

    async def execute_command(self, command: dict, timeout: int = 60) -> dict:
        self.attempts += 1
        raise ConnectionFailed('Could not connect to the browser')


@pytest.mark.asyncio
async def test_readiness_poll_backs_off_so_a_dead_browser_costs_few_attempts():
    """``stop()`` and ``__aexit__`` poll the endpoint through this check; a fixed
    20 ms pause made a browser that was already gone cost hundreds of connects."""
    connection = _DeadConnection()
    browser = Chrome()
    browser._connection_handler = connection
    assert await browser._is_browser_running(timeout=0.5) is False
    assert 2 <= connection.attempts <= 10


def _launched_browser(process: _FakeProcess, connection: FakeConnection) -> Chrome:
    """A Chrome whose process was launched (as a fake) and whose profile is a real temp dir."""
    browser = Chrome()
    browser._connection_handler = connection
    browser._temp_directory_manager = TempDirectoryManager()
    browser._browser_process_manager = BrowserProcessManager(
        process_creator=lambda command: process
    )
    browser._browser_process_manager.start_browser_process('/usr/bin/true', 9222, [])
    return browser


@pytest.mark.asyncio
async def test_stop_cleans_up_a_browser_that_already_exited_without_cdp(fake_conn):
    browser = _launched_browser(_FakeProcess(exit_code=-9), fake_conn)
    profile = browser._temp_directory_manager.create_temp_dir().name

    await browser.stop()

    assert fake_conn.commands == []
    assert not os.path.isdir(profile)


@pytest.mark.asyncio
async def test_stop_ends_the_process_when_browser_close_fails(fake_conn):
    process = _FakeProcess()
    browser = _launched_browser(process, fake_conn)
    profile = browser._temp_directory_manager.create_temp_dir().name
    fake_conn.set_failure(BrowserMethod.CLOSE, -32000, 'Browser.close failed')

    await browser.stop()

    assert process.terminated is True
    assert not os.path.isdir(profile)


@pytest.mark.asyncio
async def test_stop_without_a_launched_process_or_a_browser_to_reach_raises():
    browser = Chrome()
    browser._connection_handler = _DeadConnection()
    with pytest.raises(BrowserNotRunning):
        await browser.stop()


@pytest.mark.asyncio
async def test_deleting_a_context_forgets_only_its_tabs_and_closes_their_connections(fake_conn):
    browser = Chrome()
    browser._connection_handler = fake_conn
    in_context = FakeConnection()
    elsewhere = FakeConnection()
    for target_id, context_id, connection in (
        ('tab-a', 'ctx-1', in_context),
        ('tab-b', 'ctx-2', elsewhere),
    ):
        browser._tabs_opened[target_id] = Tab(
            browser,
            target_id=target_id,
            browser_context_id=context_id,
            connection_handler=connection,
        )
    await in_context.register_callback(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)
    await elsewhere.register_callback(NetworkEvent.REQUEST_WILL_BE_SENT, lambda _event: None)

    await browser.delete_browser_context('ctx-1')

    assert list(browser._tabs_opened) == ['tab-b']
    assert in_context.callbacks_for(NetworkEvent.REQUEST_WILL_BE_SENT) == []
    assert len(elsewhere.callbacks_for(NetworkEvent.REQUEST_WILL_BE_SENT)) == 1
    assert fake_conn.last_command(TargetMethod.DISPOSE_BROWSER_CONTEXT)['params'] == {
        'browserContextId': 'ctx-1'
    }
