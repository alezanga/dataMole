from typing import Iterable, List, Union

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface import Operation


class SetIndexOp(Operation):
    def __init__(self):
        super().__init__()
        self.__index_col: int = None

    def execute(self, df: data.Frame) -> data.Frame:
        return df.setIndex(self.__index_col)

    @staticmethod
    def name() -> str:
        return 'Set index'

    def info(self) -> str:
        return 'Sets the column index of a table'

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def setOptions(self, col: int) -> None:
        self.__index_col = col

    def unsetOptions(self) -> None:
        self.__index_col = None

    def needsOptions(self) -> bool:
        return True

    def getOutputShape(self) -> Union[data.Shape, None]:
        if self.__index_col is None or not self._shape[0]:
            return None
        s = self._shape[0].copy()
        s.index = s.col_names[self.__index_col]
        return s

    def getOptions(self) -> Iterable:
        return self.__index_col, self._shape[0]

    def getEditor(self) -> AbsOperationEditor:
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
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


export = SetIndexOp
