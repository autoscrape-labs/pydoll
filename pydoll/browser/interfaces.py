from abc import ABC, abstractmethod

from pydoll.constants import DEFAULT_MAX_MESSAGE_SIZE, PageLoadState


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

    @property
    def max_message_size(self) -> int | None:
        """Largest CDP message, in bytes, a connection accepts (None means no limit).

        Not abstract, so an Options implementation written before the limit
        existed keeps working with the default.
        """
        return DEFAULT_MAX_MESSAGE_SIZE

    @abstractmethod
    def add_argument(self, argument: str):
        pass

    @property
    @abstractmethod
    def browser_preferences(self) -> dict:
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
