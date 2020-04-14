from typing import Union, Iterable, Dict

from data_preprocessor import data
from data_preprocessor.gui.generic.AbsStepEditor import AbsStepEditor
from data_preprocessor.operation import AttributeOperation


class RenameOp(AttributeOperation):
    # Dict with format {pos: new_name}
    __names: Dict[int, str] = None

    def execute(self, df: data.Frame) -> data.Frame:
        pass

    def name(self) -> str:
        return 'Rename operation'

    def setOptions(self, names: Dict[int, str]) -> None:
        self.__names = names

    def getEditor(self) -> AbsStepEditor:
        # TODO
        pass

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.__names:
            raise ValueError('Method {}.getOutputShape must be called with non null arguments, '
                             'instead \'names\' is None'.format(self.__class__.__name__))

        # Shape is the same as before with name changed
        s = self._shape
        for index, name in self.__names.items():
            s.col_names[index] = name

        return s

    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True
