from abc import ABC, abstractmethod


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


class BrowserOptionsManager(ABC):
    @abstractmethod
    def initialize_options(self) -> Options:
        pass

    @abstractmethod
    def add_default_arguments(self):
        pass
