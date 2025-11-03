from abc import ABC, abstractmethod

from pydoll.constants import PageLoadState

from pydoll.browser.preference_types import BrowserPreferences


class Options(ABC):
    @property
    @abstractmethod
    def arguments(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def binary_location(self) -> str:
        pass

    @property
    @abstractmethod
    def start_timeout(self) -> int:
        pass

    @abstractmethod
    def add_argument(self, argument: str):
        pass

    @property
    @abstractmethod
    def browser_preferences(self) -> BrowserPreferences:
        pass

    @property
    @abstractmethod
    def headless(self) -> bool:
        pass

    @headless.setter
    @abstractmethod
    def headless(self, headless: bool):
        pass

    @property
    @abstractmethod
    def page_load_state(self) -> PageLoadState:
        pass

    @page_load_state.setter
    @abstractmethod
    def page_load_state(self, state: PageLoadState):
        pass


class BrowserOptionsManager(ABC):
    @abstractmethod
    def initialize_options(self) -> Options:
        pass

    @abstractmethod
    def add_default_arguments(self):
        pass
