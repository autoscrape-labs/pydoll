from __future__ import annotations

from pydoll.browser.interfaces import Options
from pydoll.constants import PageLoadState
from pydoll.exceptions import ArgumentAlreadyExistsInOptions, ArgumentNotFoundInOptions


class FirefoxOptions(Options):
    """
    Manages command-line options for a Firefox browser instance using WebDriver BiDi.
    """

    def __init__(self):
        self._arguments: list[str] = []
        self._binary_location = ''
        self._start_timeout = 30
        self._browser_preferences: dict = {}
        self._headless = False
        self._page_load_state = PageLoadState.COMPLETE

    @property
    def arguments(self) -> list[str]:
        return self._arguments

    @arguments.setter
    def arguments(self, args_list: list[str]):
        self._arguments = args_list

    @property
    def binary_location(self) -> str:
        return self._binary_location

    @binary_location.setter
    def binary_location(self, location: str):
        self._binary_location = location

    @property
    def start_timeout(self) -> int:
        return self._start_timeout

    @start_timeout.setter
    def start_timeout(self, timeout: int):
        self._start_timeout = timeout

    @property
    def browser_preferences(self) -> dict:
        return self._browser_preferences

    @browser_preferences.setter
    def browser_preferences(self, preferences: dict):
        if not isinstance(preferences, dict):
            raise ValueError('browser_preferences must be a dict.')
        self._browser_preferences = {**self._browser_preferences, **preferences}

    def add_argument(self, argument: str):
        if argument in self._arguments:
            raise ArgumentAlreadyExistsInOptions(f'Argument already exists: {argument}')
        self._arguments.append(argument)

    def remove_argument(self, argument: str):
        if argument not in self._arguments:
            raise ArgumentNotFoundInOptions(f'Argument not found: {argument}')
        self._arguments.remove(argument)

    @property
    def headless(self) -> bool:
        return self._headless

    @headless.setter
    def headless(self, headless: bool):
        self._headless = headless
        has_argument = '--headless' in self._arguments
        if headless == has_argument:
            return
        if headless:
            self.add_argument('--headless')
        else:
            self.remove_argument('--headless')

    @property
    def page_load_state(self) -> PageLoadState:
        return self._page_load_state

    @page_load_state.setter
    def page_load_state(self, state: PageLoadState):
        self._page_load_state = state
