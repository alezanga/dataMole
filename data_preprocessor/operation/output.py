from typing import Optional, Iterable

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget

from data_preprocessor import data, flogging
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface.graph import OutputGraphOperation
from ..gui import widgetutils as opw


class ToVariableOp(OutputGraphOperation, flogging.Loggable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__var_name: Optional[str] = None

    def execute(self, df: data.Frame) -> None:
        self._workbench.setDataframeByName(self.__var_name, df)
        # Reset since now that variable is taken
        self.__var_name = None

    @staticmethod
    def name() -> str:
        return 'To variable'

    def shortDescription(self) -> str:
        return 'Save the output as a variable in the workbench with the given name'

    def hasOptions(self) -> bool:
        return bool(self.__var_name)

    def setOptions(self, var_name: Optional[str]) -> None:
        self.__var_name = var_name

    def needsOptions(self) -> bool:
        return True

    def getOptions(self) -> Iterable:
        return [self.__var_name]

    def getEditor(self) -> AbsOperationEditor:
        class WriteEditor(AbsOperationEditor):
            def editorBody(self) -> QWidget:
                self.__write_box = opw.TextOptionWidget()
                return self.__write_box

            def getOptions(self) -> Iterable:
                text = self.__write_box.getData()
                return [text]

            def setOptions(self, var_name: str) -> None:
                self.__write_box.widget.textChanged.connect(self.testInput)
                if var_name:
                    self.__write_box.setData(var_name)

            @Slot(str)
            def testInput(self, new_text: str):
                if new_text not in self.workbench.names:
                    self.__write_box.unsetError()
                    self.enableOkButton()
                else:
                    self.__write_box.setError('Variable name is already present')
                    self.disableOkButton()

        return WriteEditor()

    def injectEditor(self, editor: 'AbsOperationEditor') -> None:
        editor.workbench = self._workbench


export = ToVariableOp
