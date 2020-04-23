from typing import Union, List

import data_preprocessor.data as data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.operation import Operation


class InputOperation(Operation):
    """
    Base class for operations to be used to provide input
    These operations must not change the shape
    """

    def __init__(self):
        super().__init__()
        self._workbench = None

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def getOutputShape(self) -> Union[data.Shape, None]:
        return self._shape

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
