"""Cross-module wiring tests: Browser with real ChromiumOptions and OptionsManager.

These exercise how Browser, ChromiumOptionsManager and ChromiumOptions integrate
during construction — real objects, no browser process and no I/O — so they run
with the fast unit suite while still covering the seams between modules.
"""

from __future__ import annotations

import pytest

from pydoll.browser.chromium import Chrome
from pydoll.browser.managers.browser_options_manager import ChromiumOptionsManager
from pydoll.browser.options import ChromiumOptions
from pydoll.exceptions import InvalidOptionsObject


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
