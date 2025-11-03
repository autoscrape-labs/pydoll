from contextlib import suppress
from typing import Any, Optional, cast

from pydoll.browser.interfaces import Options
from pydoll.browser.preference_types import PREFERENCE_SCHEMA, BrowserPreferences
from pydoll.constants import PageLoadState
from pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    InvalidPreferencePath,
    InvalidPreferenceValue,
    WrongPrefsDict,
)


class ChromiumOptions(Options):
    """
    A class to manage command-line options for a browser instance.

    This class allows the user to specify command-line arguments and
    the binary location of the browser executable.
    """

    def __init__(self):
        """
        Initializes the Options instance.

        Sets up an empty list for command-line arguments and a string
        for the binary location of the browser.
        """
        self._arguments: list[str] = []
        self._binary_location: str = ''
        self._start_timeout: int = 10
        self._browser_preferences: dict[str, Any] = {}
        self._headless: bool = False
        self._page_load_state: PageLoadState = PageLoadState.COMPLETE

    @property
    def arguments(self) -> list[str]:
        """
        Gets the list of command-line arguments.

        Returns:
            list: A list of command-line arguments added to the options.
        """
        return self._arguments

    @arguments.setter
    def arguments(self, args_list: list[str]):
        """
        Sets the list of command-line arguments.

        Args:
            args_list (list): A list of command-line arguments.
        """
        self._arguments = args_list

    @property
    def binary_location(self) -> str:
        """
        Gets the location of the browser binary.

        Returns:
            str: The file path to the browser executable.
        """
        return self._binary_location

    @binary_location.setter
    def binary_location(self, location: str):
        """
        Sets the location of the browser binary.

        Args:
            location (str): The file path to the browser executable.
        """
        self._binary_location = location

    @property
    def start_timeout(self) -> int:
        """
        Gets the timeout to verify the browser's running state.

        Returns:
            int: The timeout in seconds.
        """
        return self._start_timeout

    @start_timeout.setter
    def start_timeout(self, timeout: int):
        """
        Sets the timeout to verify the browser's running state.

        Args:
            timeout (int): The timeout in seconds.
        """
        self._start_timeout = timeout

    def add_argument(self, argument: str):
        """
        Adds a command-line argument to the options.

        Args:
            argument (str): The command-line argument to be added.

        Raises:
            ArgumentAlreadyExistsInOptions: If the argument is already in the list of arguments.
        """
        if argument not in self._arguments:
            self._arguments.append(argument)
        else:
            raise ArgumentAlreadyExistsInOptions(f'Argument already exists: {argument}')

    def remove_argument(self, argument: str):
        """
        Removes a command-line argument from the options.

        Args:
            argument (str): The command-line argument to be removed.

        Raises:
            ArgumentNotFoundInOptions: If the argument is not in the list of arguments.
        """
        if argument not in self._arguments:
            raise ArgumentNotFoundInOptions(f'Argument not found: {argument}')
        self._arguments.remove(argument)

    @property
    def browser_preferences(self) -> BrowserPreferences:
        return cast(BrowserPreferences, self._browser_preferences)

    @browser_preferences.setter
    def browser_preferences(self, preferences: BrowserPreferences):
        if not isinstance(preferences, dict):
            raise ValueError('The experimental options value must be a dict.')

        if preferences.get('prefs'):
            # deixar o WrongPrefsDict, mas com mensagem para ficar menos genérico
            raise WrongPrefsDict("Top-level key 'prefs' is not allowed in browser preferences.")
        # merge com preferências existentes
        self._browser_preferences = {**self._browser_preferences, **preferences}

    def _set_pref_path(self, path: list, value):
        """
        Safely sets a nested value in self._browser_preferences,
        creating intermediate dicts as needed.

        Arguments:
            path -- List of keys representing the nested
                    path (e.g., ['plugins', 'always_open_pdf_externally'])
            value -- The value to set at the given path
        """
        # validation will be handled in the updated implementation below
        # (kept for backward-compatibility if callers rely on signature)
        self._validate_pref_path(path)
        self._validate_pref_value(path, value)

        d = cast(dict[str, Any], self._browser_preferences)
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    @staticmethod
    def _validate_pref_path(path: list[str]) -> None:
        """
        Validate that the provided path exists in the PREFERENCE_SCHEMA.
        Raises InvalidPreferencePath when any segment is invalid.
        """
        node = PREFERENCE_SCHEMA
        for key in path:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                raise InvalidPreferencePath(f'Invalid preference path: {".".join(path)}')

    @staticmethod
    def _validate_pref_value(path: list[str], value: Any) -> None:
        """
        Validate the value type for the final segment in path against PREFERENCE_SCHEMA.
        Supports recursive validation for nested dictionaries.
        Raises InvalidPreferenceValue or InvalidPreferencePath on validation failure.
        """
        node = PREFERENCE_SCHEMA
        # Walk to the parent node (assumes path is valid from _validate_pref_path)
        for key in path[:-1]:
            node = node[key]

        final_key = path[-1]
        expected = node[final_key]

        if isinstance(expected, dict):
            # Expected is a subschema dict; value must be a dict and match the schema
            if not isinstance(value, dict):
                raise InvalidPreferenceValue(
                    f'Invalid value type for {".".join(path)}: '
                    f'expected dict, got {type(value).__name__}'
                )
            # Recursively validate each key-value in the value dict
            for k, v in value.items():
                if k not in expected:
                    raise InvalidPreferencePath(
                        f'Invalid key "{k}" in preference path {".".join(path)}'
                    )
                ChromiumOptions._validate_pref_value(path + [k], v)
        elif not isinstance(value, expected):
            # Expected is a primitive type; check isinstance
            raise InvalidPreferenceValue(
                f'Invalid value type for {".".join(path)}: '
                f'expected {expected.__name__}, got {type(value).__name__}'
            )

    def _get_pref_path(self, path: list):
        """
        Safely gets a nested value from self._browser_preferences.

        Arguments:
            path -- List of keys representing the nested
                    path (e.g., ['plugins', 'always_open_pdf_externally'])

        Returns:
            The value at the given path, or None if path doesn't exist
        """
        # validate path structure first; if invalid, raise a clear exception
        try:
            self._validate_pref_path(path)
        except InvalidPreferencePath:
            raise

        nested_preferences = self._browser_preferences
        with suppress(KeyError, TypeError):
            for key in path:
                nested_preferences = nested_preferences[key]
            return nested_preferences
        return None

    def set_default_download_directory(self, path: str):
        """
        Set the default directory where downloaded files will be saved.

        Usage: Sets the 'download.default_directory' preference for Chrome.

        Arguments:
            path: Absolute path to the download destination folder.
        """
        self._set_pref_path(['download', 'default_directory'], path)

    def set_accept_languages(self, languages: str):
        """
        Set the accepted languages for the browser.

        Usage: Sets the 'intl.accept_languages' preference.

        Arguments:
            languages: A comma-separated string of language codes (e.g., 'pt-BR,pt,en-US,en').
        """
        self._set_pref_path(['intl', 'accept_languages'], languages)

    @property
    def prompt_for_download(self) -> Optional[bool]:
        val = self._get_pref_path(['download', 'prompt_for_download'])
        return val if isinstance(val, bool) else None

    @prompt_for_download.setter
    def prompt_for_download(self, enabled: bool):
        """
        Enable or disable download prompt confirmation.

        Usage: Sets the 'download.prompt_for_download' preference.

        Arguments:
            enabled: If True, Chrome will ask for confirmation before downloading.
        """
        self._set_pref_path(['download', 'prompt_for_download'], enabled)

    @property
    def block_popups(self) -> bool:
        return self._get_pref_path(['profile', 'default_content_setting_values', 'popups']) == 0

    @block_popups.setter
    def block_popups(self, block: bool):
        """
        Block or allow pop-up windows.

        Usage: Sets the 'profile.default_content_setting_values.popups' preference.

        Arguments:
            block: If True, pop-ups will be blocked (value = 0); otherwise allowed (value = 1).
        """
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'popups'], 0 if block else 1
        )

    @property
    def password_manager_enabled(self) -> Optional[bool]:
        val = self._get_pref_path(['profile', 'password_manager_enabled'])
        return val if isinstance(val, bool) else None

    @password_manager_enabled.setter
    def password_manager_enabled(self, enabled: bool):
        """
        Enable or disable Chrome's password manager.

        Usage: Sets the 'profile.password_manager_enabled' preference.

        Arguments:
            enabled: If True, the password manager is active.
        """
        self._set_pref_path(['profile', 'password_manager_enabled'], enabled)
        self._browser_preferences['credentials_enable_service'] = enabled

    @property
    def block_notifications(self) -> bool:
        block_notifications_true_value = 2
        return (
            self._get_pref_path(['profile', 'default_content_setting_values', 'notifications'])
            == block_notifications_true_value
        )

    @block_notifications.setter
    def block_notifications(self, block: bool):
        """
        Block or allow site notifications.

        Usage: Sets the 'profile.default_content_setting_values.notifications' preference.

        Arguments:
            block: If True, notifications will be blocked (value = 2);
            otherwise allowed (value = 1).
        """
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'notifications'],
            2 if block else 1,
        )

    @property
    def allow_automatic_downloads(self) -> bool:
        return (
            self._get_pref_path([
                'profile',
                'default_content_setting_values',
                'automatic_downloads',
            ])
            == 1
        )

    @allow_automatic_downloads.setter
    def allow_automatic_downloads(self, allow: bool):
        """
        Allow or block automatic multiple downloads.

        Usage: Sets the 'profile.default_content_setting_values.automatic_downloads' preference.

        Arguments:
            allow: If True, automatic downloads are allowed (value = 1);
            otherwise blocked (value = 2).
        """
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'automatic_downloads'],
            1 if allow else 2,
        )

    @property
    def open_pdf_externally(self) -> Optional[bool]:
        val = self._get_pref_path(['plugins', 'always_open_pdf_externally'])
        return val if isinstance(val, bool) else None

    @open_pdf_externally.setter
    def open_pdf_externally(self, enabled: bool):
        """
        Block or allow geolocation access.

        Usage: Sets the 'profile.managed_default_content_settings.geolocation' preference.

        Arguments:
            block: If True, location access is blocked (value = 2); otherwise allowed (value = 1).
        """
        self._set_pref_path(['plugins', 'always_open_pdf_externally'], enabled)

    @property
    def headless(self) -> bool:
        return self._headless

    @headless.setter
    def headless(self, headless: bool):
        self._headless = headless
        has_argument = '--headless' in self.arguments
        methods_map = {True: self.add_argument, False: self.remove_argument}
        if headless != has_argument:
            methods_map[headless]('--headless')

    @property
    def page_load_state(self) -> PageLoadState:
        return self._page_load_state

    @page_load_state.setter
    def page_load_state(self, state: PageLoadState):
        self._page_load_state = state
