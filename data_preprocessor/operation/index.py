from typing import Iterable, List, Union, Optional

from PySide2.QtWidgets import QWidget

import data_preprocessor.gui.editor.optionwidget as opw
from data_preprocessor import data
from data_preprocessor.data.types import Types, ALL_TYPES
from data_preprocessor.gui import AbsOperationEditor
from data_preprocessor.operation.interface.graph import GraphOperation


class SetIndexOp(GraphOperation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__index_col: int = None

    def execute(self, df: data.Frame) -> data.Frame:
        return df.setIndex(self.__index_col)

    @staticmethod
    def name() -> str:
        return 'Set index'

    def shortDescription(self) -> str:
        return 'Sets the column index of a table'

    def longDescription(self) -> str:
        return 'Some operations like Join does not preserve the index, so you may want to ' \
               'set it again if it is required. Setting it twice does nothing. '

    def acceptedTypes(self) -> List[Types]:
        return ALL_TYPES

    def hasOptions(self) -> bool:
        return self.__index_col is not None

    def setOptions(self, col: int) -> None:
        self.__index_col = col

    def unsetOptions(self) -> None:
        self.__index_col = None

    def needsOptions(self) -> bool:
        return True

    def getOutputShape(self) -> Union[data.Shape, None]:
        if not self.hasOptions() or not self._shapes[0]:
            return None
        s = self._shapes[0].copy()
        s.index = s.col_names[self.__index_col]
        return s

    def getOptions(self) -> Iterable:
        return [self.__index_col]

    def getEditor(self) -> AbsOperationEditor:
        class Editor(AbsOperationEditor):
            def editorBody(self) -> QWidget:
                self.attributeComboBox = opw.AttributeComboBox(None, None, 'Select an attribute')
                return self.attributeComboBox

            def getOptions(self) -> Iterable:
                return [self.attributeComboBox.getData()]

            def setOptions(self, index: Optional[int]) -> None:
                self.attributeComboBox.setData(index)

        return Editor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.inputShapes = self.shapes
        editor.acceptedTypes = self.acceptedTypes()
        editor.attributeComboBox.refresh(shape=self.shapes[0], typesFilter=self.acceptedTypes())

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
