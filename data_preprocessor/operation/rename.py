import copy
from typing import Union, Dict, List

from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui.editor.RenameEditor import RenameEditor
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import GraphOperation


class RenameOp(GraphOperation):

    def __init__(self):
        super().__init__()
        # Dict with format {pos: new_name}
        self.__names: Dict[int, str] = dict()

    def execute(self, df: data.Frame) -> data.Frame:
        """ Set new names for columns """

        if not self.__names:
            return df

        names: List[str] = df.colnames
        for k, v in self.__names.items():
            names[k] = v
        new_df = df.getRawFrame().copy(deep=False)
        new_df.columns = names
        return data.Frame(new_df)

    @staticmethod
    def name() -> str:
        return 'Rename operation'

    def shortDescription(self) -> str:
        return 'This operation can rename the attributes'

    def hasOptions(self) -> bool:
        return bool(self.__names)

    def getOptions(self) -> List[Dict[int, str]]:
        return [copy.deepcopy(self.__names)]

    def setOptions(self, names: Dict[int, str]) -> None:
        self.__names = names

    def unsetOptions(self) -> None:
        self.__names = dict()

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        return RenameEditor()

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions():
            return None

        # Shape is the same as before with name changed
        s = copy.deepcopy(self._shape[0])
        for index, name in self.__names.items():
            s.col_names[index] = name

        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

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


export = RenameOp
