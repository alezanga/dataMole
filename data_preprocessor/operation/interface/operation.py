from abc import abstractmethod, ABC
from typing import Any

from data_preprocessor import data


class Operation(ABC):
    """ Base class of every operation. Allows to set up a command giving arguments and executing it
    over a data.Frame """

    @abstractmethod
    def execute(self, *df: data.Frame) -> Any:
        pass

    @abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        pass
