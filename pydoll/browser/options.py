from pydoll.browser.interfaces import Options
from pydoll.exceptions import ArgumentAlreadyExistsInOptions


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
        self._enable_fingerprint_spoofing = False
        self._fingerprint_config = None

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

    @property
    def enable_fingerprint_spoofing(self) -> bool:
        """
        Gets whether fingerprint spoofing is enabled.

        Returns:
            bool: True if fingerprint spoofing is enabled, False otherwise.
        """
        return self._enable_fingerprint_spoofing

    @enable_fingerprint_spoofing.setter
    def enable_fingerprint_spoofing(self, enabled: bool):
        """
        Sets whether fingerprint spoofing is enabled.

        Args:
            enabled (bool): True to enable fingerprint spoofing, False to disable.
        """
        self._enable_fingerprint_spoofing = enabled

    @property
    def fingerprint_config(self):
        """
        Gets the fingerprint configuration.

        Returns:
            The fingerprint configuration object or None if not set.
        """
        return self._fingerprint_config

    @fingerprint_config.setter
    def fingerprint_config(self, config):
        """
        Sets the fingerprint configuration.

        Args:
            config: The fingerprint configuration object.
        """
        self._fingerprint_config = config

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

    def enable_fingerprint_spoofing_mode(self, config=None):
        """
        Enable fingerprint spoofing with optional configuration.

        Args:
            config: Optional fingerprint configuration object.
        """
        self._enable_fingerprint_spoofing = True
        if config is not None:
            self._fingerprint_config = config
