import pytest

from pydoll.browser.interfaces import Options as OptionsInterface
from pydoll.browser.options import ChromiumOptions as Options
from pydoll.constants import PageLoadState
from pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    WrongPrefsDict,
)


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


def test_initial_page_load_state():
    options = Options()
    assert options.page_load_state == PageLoadState.COMPLETE


def test_set_page_load_state():
    options = Options()
    options.page_load_state = PageLoadState.INTERACTIVE
    assert options.page_load_state == PageLoadState.INTERACTIVE


def test_add_argument():
    options = Options()
    options.add_argument('--headless')
    assert options.arguments == ['--headless']


def test_add_duplicate_argument():
    options = Options()
    options.add_argument('--headless')
    with pytest.raises(ArgumentAlreadyExistsInOptions, match='Argument already exists: --headless'):
        options.add_argument('--headless')


def test_remove_argument():
    options = Options()
    options.add_argument('--headless')
    options.remove_argument('--headless')
    assert options.arguments == []


def test_remove_argument_not_exists():
    options = Options()
    with pytest.raises(ArgumentNotFoundInOptions, match='Argument not found: --headless'):
        options.remove_argument('--headless')


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


def test_set_arguments():
    options = Options()
    options.arguments = ['--headless']
    assert options.arguments == ['--headless']


def test_get_pref_path():
    options = Options()
    options.set_default_download_directory('/tmp/downloads')
    assert options._get_pref_path(['download', 'default_directory']) == '/tmp/downloads'


def test_get_pref_path_none():
    options = Options()
    assert options._get_pref_path(['download', 'default_directory']) is None


def test_options_interface_enforcement():
    with pytest.raises(TypeError):
        OptionsInterface()

    class IncompleteOptions(OptionsInterface):
        pass

    with pytest.raises(TypeError):
        IncompleteOptions()

    class CompleteOptions(OptionsInterface):
        @property
        def arguments(self):
            return []

        @property
        def binary_location(self):
            return ''

        @property
        def start_timeout(self):
            return 0

        def add_argument(self, argument):
            pass

        @property
        def browser_preferences(self):
            return {}

        @property
        def headless(self):
            return False

        @property
        def max_parallel_tasks(self):
            return 1
        
        @property
        def page_load_state(self):
            return PageLoadState.COMPLETE

        @page_load_state.setter
        def page_load_state(self, state):
            pass

    CompleteOptions()


def test_set_headless():
    options = Options()
    options.headless = True
    assert options.headless is True
    assert options.arguments == ['--headless']


def test_set_headless_false():
    options = Options()
    options.headless = True
    assert options.headless is True
    assert options.arguments == ['--headless']
    options.headless = False
    assert options.headless is False
    assert options.arguments == []


def test_set_headless_true_twice():
    options = Options()
    options.headless = True
    assert options.headless is True
    assert options.arguments == ['--headless']
    options.headless = True
    assert options.headless is True
    assert options.arguments == ['--headless']


def test_set_headless_false_twice():
    options = Options()
    options.headless = False
    assert options.headless is False
    assert options.arguments == []
    options.headless = False
    assert options.headless is False
    assert options.arguments == []


def test_set_max_parallel_tasks():
    options = Options()
    options.max_parallel_tasks = 2
    assert options.max_parallel_tasks == 2


def test_set_max_parallel_tasks_error():
    options = Options()
    with pytest.raises(ValueError, match='max_parallel_tasks must be greater than 0'):
        options.max_parallel_tasks = 0
