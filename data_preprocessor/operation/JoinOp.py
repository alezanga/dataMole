from enum import Enum, unique
from typing import List, Tuple, Optional

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import GraphOperation


@unique
class JoinType(Enum):
    Left = 'left'
    Right = 'right'
    Inner = 'inner'
    Outer = 'outer'


jt = JoinType


class JoinOp(GraphOperation):
    def __init__(self):
        super().__init__()
        self.__lsuffix: str = '_l'
        self.__rsuffix: str = '_r'
        self.__on_index: bool = True
        self.__left_on: int = None
        self.__right_on: int = None
        self.__type: JoinType = jt.Left

    def execute(self, dfl: data.Frame, dfr: data.Frame) -> data.Frame:
        if self.__on_index:
            return data.Frame(dfl.getRawFrame().join(dfr.getRawFrame(), how=self.__type.value,
                                                     lsuffix=self.__lsuffix,
                                                     rsuffix=self.__rsuffix))
        else:
            # onleft and onright must be set
            suffixes = (self.__lsuffix, self.__rsuffix)
            l_col = dfl.shape.col_names[self.__left_on]
            r_col = dfl.shape.col_names[self.__right_on]
            return data.Frame(dfl.getRawFrame().merge(dfr.getRawFrame(), how=self.__type.value,
                                                      left_on=l_col,
                                                      right_on=r_col,
                                                      suffixes=suffixes))

    @staticmethod
    def name() -> str:
        return 'Join operation'

    def shortDescription(self) -> str:
        return 'Allows to join two tables. Can handle four type of join: left, right, outer and inner'

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def setOptions(self, ls: str, rs: str, onindex: bool, onleft: int, onright: int,
                   join_type: JoinType) -> None:
        self.__lsuffix = ls
        self.__rsuffix = rs
        self.__on_index = onindex
        self.__left_on = onleft
        self.__right_on = onright
        self.__type = join_type

    def unsetOptions(self) -> None:
        self.__left_on: int = None
        self.__right_on: int = None

    def getOptions(self) -> Tuple[str, str, bool, int, int, JoinType, List[Optional[data.Shape]]]:
        return (self.__lsuffix, self.__rsuffix, self.__on_index, self.__left_on, self.__right_on,
                self.__type, self._shape)

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        # TODO: editor here must ensure types of selected columns match
        pass

    def hasOptions(self) -> bool:
        on = self.__on_index is True or (self.__left_on is not None and self.__right_on is not None)
        return self.__lsuffix and self.__rsuffix and on and self.__type in JoinType

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    @staticmethod
    def minInputNumber() -> int:
        return 2

    @staticmethod
    def maxInputNumber() -> int:
        return 2

    @staticmethod
    def minOutputNumber() -> int:
        return 1

    @staticmethod
    def maxOutputNumber() -> int:
        return -1


export = JoinOp
