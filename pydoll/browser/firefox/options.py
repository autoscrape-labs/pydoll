from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydoll.constants import PageLoadState
from pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    InvalidOptionsObject,
)

if TYPE_CHECKING:
    from pydoll.browser.protocols import OptionsProtocol


class FirefoxOptions:
    """Firefox-specific browser options."""

    def __init__(self):
        self._arguments: list[str] = []
        self._binary_location = ''
        self._start_timeout = 10
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

    def add_argument(self, argument: str):
        if argument in self._arguments:
            raise ArgumentAlreadyExistsInOptions(
                f'Argument already exists: {argument}'
            )
        self._arguments.append(argument)

    def remove_argument(self, argument: str):
        if argument not in self._arguments:
            raise ArgumentNotFoundInOptions(
                f'Argument not found: {argument}'
            )
        self._arguments.remove(argument)

    @property
    def browser_preferences(self) -> dict:
        return self._browser_preferences

    @browser_preferences.setter
    def browser_preferences(self, preferences: dict):
        self._browser_preferences = {**self._browser_preferences, **preferences}

    @property
    def headless(self) -> bool:
        return self._headless

    @headless.setter
    def headless(self, headless: bool):
        self._headless = headless
        has_argument = '--headless' in self.arguments
        if headless and not has_argument:
            self.add_argument('--headless')
        elif not headless and has_argument:
            self.remove_argument('--headless')

    @property
    def page_load_state(self) -> PageLoadState:
        return self._page_load_state

    @page_load_state.setter
    def page_load_state(self, state: PageLoadState):
        self._page_load_state = state


class FirefoxOptionsManager:
    """Manages browser options configuration for Firefox."""

    def __init__(self, options: Optional[OptionsProtocol] = None):
        self.options = options

    def initialize_options(self) -> FirefoxOptions:
        """Initialize and validate Firefox options."""
        if self.options is None:
            self.options = FirefoxOptions()

        if not isinstance(self.options, FirefoxOptions):
            raise InvalidOptionsObject(
                f'Expected FirefoxOptions, got {type(self.options)}'
            )

        self.add_default_arguments()
        return self.options

    def add_default_arguments(self):
        """Add default arguments for Firefox with BiDi support."""
        pass
