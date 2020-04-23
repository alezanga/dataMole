from typing import Union, Dict
import copy

from data_preprocessor import data
from data_preprocessor.gui.editor.RenameEditor import RenameEditor
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import AttributeOperation


class RenameOp(AttributeOperation):
    def __init__(self):
        super().__init__()
        # Dict with format {pos: new_name}
        self.__names: Dict[int, str] = dict()

    def execute(self, df: data.Frame) -> data.Frame:
        pass

    def name(self) -> str:
        return 'Rename operation'

    def info(self) -> str:
        return 'This operation can rename the attributes'

    def getOptions(self) -> (Dict[int, str], data.Frame):
        return copy.copy(self.__names), copy.copy(self._shape)

    def setOptions(self, names: Dict[int, str]) -> None:
        self.__names = names

    def getEditor(self) -> AbsOperationEditor:
        return RenameEditor()

    def getOutputShape(self) -> Union[data.Frame, None]:
        if not self.__names:
            raise ValueError('Method {}.getOutputShape must be called with non null arguments, '
                             'instead \'names\' is None'.format(self.__class__.__name__))

        # Shape is the same as before with name changed
        s = self._shape
        for index, name in self.__names.items():
            s.shape.col_names[index] = name

        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True
