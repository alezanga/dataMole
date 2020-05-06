from typing import Union, Iterable, List, Any

import numpy as np

from data_preprocessor import data
from data_preprocessor.data.types import Types
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface import Operation


class MergeValuesOp(Operation):
    """ Merge values of one attribute into a single value """
    Nan = np.nan

    def __init__(self):
        super().__init__()
        self.__attribute: str = None
        self.__values_to_merge: List = list()
        self.__merge_val: Any = None

    def execute(self, df: data.Frame) -> data.Frame:
        pd_df = df.getRawFrame().copy()
        pd_df[self.__attribute] = pd_df[self.__attribute].replace(to_replace=self.__values_to_merge,
                                                                  value=self.__merge_val, inplace=False)
        return data.Frame(pd_df)

    @staticmethod
    def name() -> str:
        return 'Merge values'

    def info(self) -> str:
        return 'Substitute all specified values in a attribute and substitute them with a single value'

    def acceptedTypes(self) -> List[Types]:
        return [Types.String, Types.Categorical, Types.Numeric]

    def setOptions(self, attribute: str, values_to_merge: List, value: Any) -> None:
        self.__attribute = attribute
        self.__values_to_merge = values_to_merge
        self.__merge_val = value  # could be Nan

    def unsetOptions(self) -> None:
        self.__attribute = None
        self.__values_to_merge = list()
        self.__merge_val = None

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return self.__values_to_merge, self.__merge_val

    def getEditor(self) -> AbsOperationEditor:
        pass

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not (self.__attribute and self.__values_to_merge and self.__merge_val) or not self._shape[0]:
            return None
        toy_frame = data.Frame.fromShape(self._shape[0])
        toy_res = self.execute(toy_frame)
        return toy_res.shape

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
