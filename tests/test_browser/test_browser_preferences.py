import pytest
from typing import Any, cast

from pydoll.browser.options import ChromiumOptions
from pydoll.browser.preference_types import BrowserPreferences
from pydoll.exceptions import InvalidPreferencePath, InvalidPreferenceValue, WrongPrefsDict


def test_validate_pref_path_valid():
    """Test that valid preference paths are accepted."""
    options = ChromiumOptions()
    # Should not raise
    options._validate_pref_path(['download', 'default_directory'])
    options._validate_pref_path(['profile', 'password_manager_enabled'])
    options._validate_pref_path(['plugins', 'always_open_pdf_externally'])


def test_validate_pref_path_invalid():
    """Test that invalid preference paths raise InvalidPreferencePath."""
    options = ChromiumOptions()
    with pytest.raises(InvalidPreferencePath):
        options._validate_pref_path(['invalid', 'path'])
    with pytest.raises(InvalidPreferencePath):
        options._validate_pref_path(['download', 'invalid_key'])


def test_validate_pref_value_valid():
    """Test that valid preference values are accepted."""
    options = ChromiumOptions()
    # Should not raise
    options._validate_pref_value(['download', 'default_directory'], '/path/to/dir')
    options._validate_pref_value(['profile', 'password_manager_enabled'], True)
    options._validate_pref_value(['profile', 'default_content_setting_values', 'popups'], 1)


def test_validate_pref_value_invalid():
    """Test that invalid preference values raise InvalidPreferenceValue."""
    options = ChromiumOptions()
    with pytest.raises(InvalidPreferenceValue):
        options._validate_pref_value(['download', 'default_directory'], True)  # should be str
    with pytest.raises(InvalidPreferenceValue):
        options._validate_pref_value(['profile', 'password_manager_enabled'], 'true')  # should be bool


def test_browser_preferences_setter_valid():
    """Test setting valid browser preferences."""
    options = ChromiumOptions()
    prefs: BrowserPreferences = {
        'download': {
            'default_directory': '/downloads',
            'prompt_for_download': True
        },
        'profile': {
            'password_manager_enabled': False,
            'default_content_setting_values': {
                'popups': 0,
                'notifications': 2
            }
        }
    }
    options.browser_preferences = prefs
    assert options.browser_preferences == prefs


def test_browser_preferences_setter_invalid_type():
    """Test setting browser preferences with invalid type."""
    options = ChromiumOptions()
    with pytest.raises(ValueError):
        # type: ignore[arg-type]
        options.browser_preferences = ['not', 'a', 'dict']


def test_browser_preferences_setter_invalid_prefs():
    """Test setting browser preferences with invalid prefs key."""
    options = ChromiumOptions()
    with pytest.raises(WrongPrefsDict):
        invalid_prefs = cast(BrowserPreferences, {'prefs': {'some': 'value'}})
        options.browser_preferences = invalid_prefs


def test_browser_preferences_merge():
    """Test that browser preferences are properly merged."""
    options = ChromiumOptions()
    initial_prefs: BrowserPreferences = {
        'download': {
            'default_directory': '/downloads',
            'prompt_for_download': True
        },
        'profile': {
            'password_manager_enabled': True,
            'default_content_setting_values': {
                'popups': 0
            }
        }
    }
    additional_prefs: BrowserPreferences = {
        'profile': {
            'password_manager_enabled': False,
            'default_content_setting_values': {
                'notifications': 2
            }
        }
    }
    
    options.browser_preferences = initial_prefs
    options.browser_preferences = additional_prefs
    
    expected: BrowserPreferences = {
        'download': {
            'default_directory': '/downloads',
            'prompt_for_download': True
        },
        'profile': {
            'password_manager_enabled': False,
            'default_content_setting_values': {
                'notifications': 2
            }
        }
    }
    assert options.browser_preferences == expected


def test_get_pref_path_existing():
    """Test getting existing preference paths."""
    options = ChromiumOptions()
    prefs: BrowserPreferences = {
        'download': {
            'default_directory': '/downloads',
        },
        'profile': {
            'password_manager_enabled': True,
            'default_content_setting_values': {}
        }
    }
    options.browser_preferences = prefs
    assert options._get_pref_path(['download', 'default_directory']) == '/downloads'


def test_get_pref_path_nonexistent():
    """Test getting nonexistent preference paths returns None."""
    options = ChromiumOptions()
    with pytest.raises(InvalidPreferencePath):
        options._get_pref_path(['download', 'nonexistent'])


def test_set_pref_path_creates_structure():
    """Test that setting a preference path creates the necessary structure."""
    options = ChromiumOptions()
    options.browser_preferences = cast(BrowserPreferences, {
        'profile': {
            'password_manager_enabled': True,
            'default_content_setting_values': {}
        }
    })
    options._set_pref_path(['profile', 'default_content_setting_values', 'popups'], 0)
    assert cast(Any, options.browser_preferences)['profile']['default_content_setting_values']['popups'] == 0