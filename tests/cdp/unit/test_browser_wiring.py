"""Cross-module wiring tests: Browser with real ChromiumOptions and OptionsManager.

These exercise how Browser, ChromiumOptionsManager and ChromiumOptions integrate
during construction — real objects, no browser process and no I/O — so they run
with the fast unit suite while still covering the seams between modules.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.managers import BrowserProcessManager
from pydoll.browser.chromium.options import ChromiumOptionsManager
from pydoll.browser.chromium.options import ChromiumOptions
from pydoll.browser.chromium.tab import Tab
from pydoll.exceptions import InvalidOptionsObject


class _FakeProcess:
    """Stand-in for the spawned browser subprocess (nothing really runs)."""

    def __init__(self):
        self.pid = 4242
        self.terminated = False

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
