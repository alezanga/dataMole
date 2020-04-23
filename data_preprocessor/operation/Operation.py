from abc import ABC, abstractmethod
from typing import Union, Any

from data_preprocessor import data
from data_preprocessor.gui import AbsOperationEditor


# TODO: see https://realpython.com/python-interface/#using-metaclasses


class Operation(ABC):
    """
    Base interface of every operation
    """

    @abstractmethod
    def __init__(self):
        """
        Build an operation as a command

        :param shape: the input shape of the frame given in input
        """
        # Holds the shape of the working frame
        self._shape: data.Frame = None
        # self._result: data.Frame = None

    # def compute(self) -> None:
    #     self._result = self.execute()

    @abstractmethod
    def execute(self, df: data.Frame) -> data.Frame:
        pass

    @abstractmethod
    def name(self) -> str:
        """
        The name of the step
        """
        pass

    @abstractmethod
    def info(self) -> str:
        """
        Provide some information to show for a step
        """
        pass

    def setInputShape(self, shape: data.Frame) -> None:
        self._shape = shape

    @abstractmethod
    def setOptions(self, *args, **kwargs) -> None:
        """
        Called to configure a step with the required data.
        Typically must be called after the user set parameters in the configuration dialog
        """
        pass

    @abstractmethod
    def getOptions(self) -> Any:
        """
        Called to get current options for the operation. Typically called to get the
        existing configuration when an editor is opended

        :return: the configuration object
        """
        pass

    @abstractmethod
    def getEditor(self) -> AbsOperationEditor:
        """
        Return the editor panel to configure the step

        :return: The widget editor
        """
        pass

    @abstractmethod
    def getOutputShape(self) -> Union[data.Shape, None]:
        """
        Computes what will the frame shape be after execution of the step.
        If the shape cannot be predicted (for every column) it must return
        None
        """
        pass

    @staticmethod
    @abstractmethod
    def isOutputShapeKnown() -> bool:
        """
        Must return true iff the number of columns and their types can be inferred with
        'getOutputShape'. Thus if this function returns false 'getOutputShape' must return None
        """
        pass

    @staticmethod
    def isInputOperation() -> bool:
        """
        Tell if the operation can be used as the first one

        :return: true iff can be used as the first one
        """
        return False
