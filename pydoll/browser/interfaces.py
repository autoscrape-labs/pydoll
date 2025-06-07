from abc import ABC, abstractmethod
from typing import List


class Options(ABC):
    @property
    @abstractmethod
    def arguments(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def binary_location(self) -> str:
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
