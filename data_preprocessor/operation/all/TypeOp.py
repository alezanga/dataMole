from copy import copy
from typing import Union, Any, List, Dict

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES, inv_type_dict
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import Operation


class TypeOp(Operation):
    def __init__(self):
        super().__init__()
        self.__types: Dict[int, Types] = dict()

    def execute(self, df: data.Frame) -> data.Frame:
        """ Changes type """
        # Deep copy
        raw_df = df.getRawFrame().copy(deep=True)
        colnames = df.colnames
        for k, v in self.__types.items():
            # Change type in-place (since raw_df is a deep copy)
            raw_df[colnames[k]] = raw_df[colnames[k]].astype(dtype=inv_type_dict[v], copy=False,
                                                             errors='raise')
        return data.Frame(raw_df)

    def name(self) -> str:
        return 'Change column type'

    def info(self) -> str:
        return 'Change type of data columns'

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def setOptions(self, new_types: Dict[int, Types]) -> None:
        self.__types = new_types

    def getOptions(self) -> Any:
        pass

    def getEditor(self) -> AbsOperationEditor:
        pass

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.__types:
            return None
        s = copy(self._shape)
        for k, v in self.__types.items():
            s.col_types[k] = v
        return s

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
