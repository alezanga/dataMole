from typing import List, Union

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.operation.Operation import Operation


class OutputOperation(Operation):
    """
    Base class for operations that persist the output of a pipeline.
    These operations must not change the shape
    """

    def __init__(self):
        super().__init__()
        self._workbench = None

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
        return 1

    @staticmethod
    def maxInputNumber() -> int:
        return 1

    @staticmethod
    def minOutputNumber() -> int:
        return 0

    @staticmethod
    def maxOutputNumber() -> int:
        return 0
