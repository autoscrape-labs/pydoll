"""Unit tests for FirefoxOptions (the BiDi counterpart of test_browser_options).

Pure option state: arguments, binary location, timeout, headless arg sync, prefs,
page-load state, user-agent, protocol conformance and the manager's validation.
"""

from __future__ import annotations

import pytest

from pydoll.browser.firefox.options import FirefoxOptions, FirefoxOptionsManager
from pydoll.browser.protocols import OptionsProtocol
from pydoll.constants import PageLoadState
from pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    InvalidOptionsObject,
)


def test_initial_state():
    options = FirefoxOptions()
    assert options.arguments == []
    assert options.binary_location == ''
    assert options.page_load_state == PageLoadState.COMPLETE
    assert options.user_agent is None


def test_arguments_setter_and_binary_location():
    options = FirefoxOptions()
    options.arguments = ['--foo']
    options.binary_location = '/path/to/firefox'
    options.start_timeout = 42
    assert options.arguments == ['--foo']
    assert options.binary_location == '/path/to/firefox'
    assert options.start_timeout == 42


def test_add_argument_rejects_duplicate():
    options = FirefoxOptions()
    options.add_argument('--headless')
    with pytest.raises(ArgumentAlreadyExistsInOptions):
        options.add_argument('--headless')


def test_remove_argument_success_and_missing():
    options = FirefoxOptions()
    options.add_argument('--x')
    options.remove_argument('--x')
    assert options.arguments == []
    with pytest.raises(ArgumentNotFoundInOptions):
        options.remove_argument('--missing')


def test_headless_syncs_argument_both_ways():
    options = FirefoxOptions()
    options.headless = True
    assert options.headless is True
    assert '--headless' in options.arguments
    options.headless = False
    assert options.headless is False
    assert '--headless' not in options.arguments


def test_browser_preferences_merge_and_page_load_state():
    options = FirefoxOptions()
    options.browser_preferences = {'a': 1}
    options.browser_preferences = {'b': 2}
    assert options.browser_preferences == {'a': 1, 'b': 2}
    options.page_load_state = PageLoadState.INTERACTIVE
    assert options.page_load_state == PageLoadState.INTERACTIVE


def test_options_protocol_compliance():
    assert isinstance(FirefoxOptions(), OptionsProtocol)


def test_manager_returns_existing_options():
    options = FirefoxOptions()
    assert FirefoxOptionsManager(options).initialize_options() is options


def test_manager_creates_default_when_none():
    assert isinstance(FirefoxOptionsManager().initialize_options(), FirefoxOptions)


def test_manager_rejects_wrong_type():
    with pytest.raises(InvalidOptionsObject):
        FirefoxOptionsManager(object()).initialize_options()
