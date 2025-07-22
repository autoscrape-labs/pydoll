import pytest

from pydoll.browser.options import ChromiumOptions as Options

from pydoll.exceptions import ArgumentAlreadyExistsInOptions, WrongPrefsDict


def test_initial_arguments():
    options = Options()
    assert options.arguments == []


def test_initial_binary_location():
    options = Options()
    assert not options.binary_location


def test_set_binary_location():
    options = Options()
    options.binary_location = '/path/to/browser'
    assert options.binary_location == '/path/to/browser'


def test_set_start_timeout():
    options = Options()
    options.start_timeout = 30
    assert options.start_timeout == 30


def test_add_argument():
    options = Options()
    options.add_argument('--headless')
    assert options.arguments == ['--headless']


def test_add_duplicate_argument():
    options = Options()
    options.add_argument('--headless')
    with pytest.raises(ArgumentAlreadyExistsInOptions, match='Argument already exists: --headless'):
        options.add_argument('--headless')


def test_add_multiple_arguments():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    assert options.arguments == ['--headless', '--no-sandbox']


def test_set_default_download_directory():
    options = Options()
    options.set_default_download_directory('/tmp/downloads')
    assert options.browser_preferences['download']['default_directory'] == '/tmp/downloads'


def test_set_prompt_for_download():
    options = Options()
    options.prompt_for_download = False
    assert options.browser_preferences['download']['prompt_for_download'] is False
    assert options.prompt_for_download is False


def test_set_block_popups():
    options = Options()
    options.block_popups = True
    assert options.browser_preferences['profile']['default_content_setting_values']['popups'] == 0
    assert options.block_popups == True


def test_set_password_manager_enabled():
    options = Options()
    options.password_manager_enabled = False
    assert options.browser_preferences['profile']['password_manager_enabled'] is False
    assert options.password_manager_enabled is False


def test_set_block_notifications():
    options = Options()
    options.block_notifications = True
    assert (
        options.browser_preferences['profile']['default_content_setting_values']['notifications']
        == 2
    )
    assert options.block_notifications == True


def test_set_allow_automatic_downloads():
    options = Options()
    options.allow_automatic_downloads = True
    assert (
        options.browser_preferences['profile']['default_content_setting_values'][
            'automatic_downloads'
        ]
        == 1
    )
    assert options.allow_automatic_downloads == True


def test_set_open_pdf_externally():
    options = Options()
    options.open_pdf_externally = True
    assert options.browser_preferences['plugins']['always_open_pdf_externally'] is True
    assert options.open_pdf_externally is True



def test_set_accept_languages():
    options = Options()
    options.set_accept_languages('pt-BR,pt,en-US,en')
    assert options.browser_preferences['intl']['accept_languages'] == 'pt-BR,pt,en-US,en'


def test_set_multiple_prefs():
    options = Options()
    options.set_default_download_directory('/tmp/all')
    options.prompt_for_download = False
    options.block_popups = True
    options.password_manager_enabled = False
    options.block_notifications = True
    options.allow_automatic_downloads = True
    options.open_pdf_externally = True
    options.set_accept_languages('pt-BR,pt,en-US,en')

    assert options.browser_preferences['download']['default_directory'] == '/tmp/all'
    assert options.browser_preferences['download']['prompt_for_download'] is False
    assert options.browser_preferences['profile']['default_content_setting_values']['popups'] == 0
    assert options.browser_preferences['profile']['password_manager_enabled'] is False
    assert (
        options.browser_preferences['profile']['default_content_setting_values']['notifications']
        == 2
    )
    assert (
        options.browser_preferences['profile']['default_content_setting_values'][
            'automatic_downloads'
        ]
        == 1
    )
    assert options.browser_preferences['plugins']['always_open_pdf_externally'] is True
    assert options.browser_preferences['intl']['accept_languages'] == 'pt-BR,pt,en-US,en'


def test_dict_prefs():
    options = Options()
    options.browser_preferences = {
        "download": {"directory_upgrade": True},
    }
    assert options.browser_preferences['download']['directory_upgrade'] == True


def test_not_dict_prefs_error():
    with pytest.raises(ValueError, match='The experimental options value must be a dict.'):
        options = Options()
        options.browser_preferences = ["download", "directory_upgrade"]


def test_wrong_dict_prefs_error():
    with pytest.raises(WrongPrefsDict):
        options = Options()
        options.browser_preferences = {
            'prefs': {
                "download": {"directory_upgrade": True},
            }
        }
