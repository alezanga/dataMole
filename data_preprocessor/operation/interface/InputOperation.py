from abc import abstractmethod
from typing import Union, List

import data_preprocessor.data as data
from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.operation.interface.Operation import Operation


class InputOperation(Operation):
    """
    Base class for operations to be used to provide input
    These operations must not change the shape
    """

    def __init__(self, w: Workbench = None):
        super().__init__()
        self._workbench = w

    @abstractmethod
    def inferInputShape(self) -> None:
        """ This method must be reimplemented to set the input shape after the options have been set """
        pass

    def addInputShape(self, shape: data.Shape, pos: int) -> None:
        # This method should do nothing for input operations
        pass

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape[0]

    def unsetOptions(self) -> None:
        pass

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 0

    @staticmethod
    def maxInputNumber() -> int:
        return 0

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1
