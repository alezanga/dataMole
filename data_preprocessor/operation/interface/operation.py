from abc import abstractmethod, ABC
from typing import Any

from data_preprocessor import data


class Operation(ABC):
    """ Base class of every operation. Allows to set up a command giving arguments and executing it
    over a data.Frame """

    @abstractmethod
    def execute(self, *df: data.Frame) -> Any:
        """ Contains the logic of the operations

        :param df: any number of input dataframes
        :return the result (any type)
        """
        pass

    @abstractmethod
    def setOptions(self, *args) -> None:
        """
        Called to configure a step with the required data. If necessary it may validate the passed
        options. In order to comunicate a specific error to a widget it should use
        :class:`~data_preprocessor.operation.interface.exceptions.OptionValidationError`

        :raise OperationError: if options are not valid
        """
        pass
