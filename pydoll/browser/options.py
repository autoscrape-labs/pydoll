from pydoll.browser.interfaces import Options
from pydoll.exceptions import ArgumentAlreadyExistsInOptions, WrongPrefsDict


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
        self._arguments = []
        self._binary_location = ''
        self._start_timeout = 10
        self._browser_preferences = {}
        self._prompt_for_download = True
        self._block_popups = False
        self._password_manager_enabled = True
        self._block_notifications = False
        self._allow_automatic_downloads = False
        self._open_pdf_externally = False

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

    @property
    def browser_preferences(self) -> dict:
        return self._browser_preferences

    @browser_preferences.setter
    def browser_preferences(self, preferences: dict):
        if not isinstance(preferences, dict):
            raise ValueError("The experimental options value must be a dict.")

        if preferences.get('prefs'):
            raise WrongPrefsDict
        self._browser_preferences = {**self._browser_preferences, **preferences}

    def _set_pref_path(self, path: list, value):
        """
        Safely sets a nested value in self._browser_preferences, creating intermediate dicts as needed.

        Arguments:
            path -- List of keys representing the nested
                    path (e.g., ['plugins', 'always_open_pdf_externally'])
            value -- The value to set at the given path
        """
        d = self._browser_preferences
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def set_default_download_directory(self, path: str):
        """
        Set the default directory where downloaded files will be saved.

        Usage: Sets the 'download.default_directory' preference for Chrome.

        Arguments:
            path -- Absolute path to the download destination folder.
        """
        self._set_pref_path(['download', 'default_directory'], path)

    def set_accept_languages(self, languages: str):
        """
        Set the accepted languages for the browser.

        Usage: Sets the 'intl.accept_languages' preference.

        Arguments:
            languages -- A comma-separated string of language codes (e.g., 'pt-BR,pt,en-US,en').
        """
        self._set_pref_path(['intl', 'accept_languages'], languages)

    @property
    def prompt_for_download(self) -> bool:
        return self._prompt_for_download

    @prompt_for_download.setter
    def prompt_for_download(self, enabled: bool):
        """
        Enable or disable download prompt confirmation.

        Usage: Sets the 'download.prompt_for_download' preference.

        Arguments:
            enabled -- If True, Chrome will ask for confirmation before downloading.
        """
        self._prompt_for_download = enabled
        self._set_pref_path(['download', 'prompt_for_download'], self._prompt_for_download)

    @property
    def block_popups(self) -> bool:
        return self._block_popups == 0

    @block_popups.setter
    def block_popups(self, block: bool):
        """
        Block or allow pop-up windows.

        Usage: Sets the 'profile.default_content_setting_values.popups' preference.

        Arguments:
            block -- If True, pop-ups will be blocked (value = 0); otherwise allowed (value = 1).
        """
        self._block_popups = 0 if block else 1
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'popups'], self._block_popups
        )

    @property
    def password_manager_enabled(self) -> bool:
        return self._password_manager_enabled

    @password_manager_enabled.setter
    def password_manager_enabled(self, enabled: bool):
        """
        Enable or disable Chrome's password manager.

        Usage: Sets the 'profile.password_manager_enabled' preference.

        Arguments:
            enabled -- If True, the password manager is active.
        """
        self._password_manager_enabled = enabled
        self._set_pref_path(['profile', 'password_manager_enabled'], self._password_manager_enabled)
        self._set_pref_path(['credentials_enable_service'], self._password_manager_enabled) # todo: colocar em outra propriedade

    @property
    def block_notifications(self) -> bool:
        block_notifications_true_value = 2
        return self._block_notifications == block_notifications_true_value

    @block_notifications.setter
    def block_notifications(self, block: bool):
        """
        Block or allow site notifications.

        Usage: Sets the 'profile.default_content_setting_values.notifications' preference.

        Arguments:
            block -- If True, notifications will be blocked (value = 2);
            otherwise allowed (value = 1).
        """
        self._block_notifications = 2 if block else 1
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'notifications'],
            self._block_notifications,
        )

    @property
    def allow_automatic_downloads(self) -> bool:
        return self._allow_automatic_downloads == 1

    @allow_automatic_downloads.setter
    def allow_automatic_downloads(self, allow: bool):
        """
        Allow or block automatic multiple downloads.

        Usage: Sets the 'profile.default_content_setting_values.automatic_downloads' preference.

        Arguments:
            allow -- If True, automatic downloads are allowed (value = 1);
            otherwise blocked (value = 2).
        """
        self._allow_automatic_downloads = 1 if allow else 2
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'automatic_downloads'],
            self._allow_automatic_downloads,
        )

    @property
    def open_pdf_externally(self) -> bool:
        return self._open_pdf_externally

    @open_pdf_externally.setter
    def open_pdf_externally(self, enabled: bool):
        """
        Block or allow geolocation access.

        Usage: Sets the 'profile.managed_default_content_settings.geolocation' preference.

        Arguments:
            block -- If True, location access is blocked (value = 2); otherwise allowed (value = 1).
        """
        self._open_pdf_externally = enabled
        self._set_pref_path(['plugins', 'always_open_pdf_externally'], self._open_pdf_externally)
