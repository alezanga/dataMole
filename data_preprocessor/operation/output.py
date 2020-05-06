from typing import Optional, Iterable

from PySide2.QtCore import QObject, Slot
from PySide2.QtGui import QValidator
from PySide2.QtWidgets import QWidget, QLineEdit

import data_preprocessor.gui.workbench as wb
from data_preprocessor import data
from data_preprocessor.gui.editor.interface import AbsOperationEditor
from .interface import OutputOperation


class ToVariableOp(OutputOperation):
    def __init__(self, w: wb.WorkbenchModel):
        super().__init__(w)
        self.__var_name: Optional[str] = None

    def execute(self, df: data.Frame) -> None:
        self._workbench.appendNewRow(self.__var_name, df)

    @staticmethod
    def name() -> str:
        return 'To variable'

    def info(self) -> str:
        return 'Save the output as a variable in the workbench with the given name'

    def setOptions(self, var_name: Optional[str]) -> None:
        self.__var_name = var_name

    def needsOptions(self) -> bool:
        return False

    def getOptions(self) -> Iterable:
        return [self.__var_name, self._workbench]

    def getEditor(self) -> AbsOperationEditor:
        class Validator(QValidator):
            def __init__(self, workbench: wb.WorkbenchModel, parent: QObject):
                super().__init__(parent)
                self.__w = workbench

            def validate(self, input: str, pos: int) -> QValidator.State:
                if input in self.__w.keys:
                    return QValidator.Intermediate
                return QValidator.Acceptable

        class WriteEditor(AbsOperationEditor):
            def editorBody(self) -> QWidget:
                self.__write_box = QLineEdit()
                self.__validator = None
                return self.__write_box

            def getOptions(self) -> Iterable:
                text = self.__write_box.text()
                if text:
                    return [text]
                return [None]

            def setOptions(self, var_name: str, workbench: wb.WorkbenchModel) -> None:
                if var_name:
                    self.__write_box.setText(var_name)
                if not self.__validator:
                    self.__validator = Validator(workbench, self)
                    self.__write_box.setValidator(self.__validator)
                    self.__write_box.textEdited.connect(self.testInput)

            @Slot(str)
            def testInput(self, new_text: str):
                if self.__validator.validate(new_text, 0) == QValidator.Acceptable:
                    self.__write_box.setStyleSheet('')
                    self.__write_box.setToolTip('')
                    self.enableOkButton()
                else:
                    self.__write_box.setStyleSheet('border: 1px solid red')
                    self.__write_box.setToolTip('Variable name is already present')
                    self.disableOkButton()

        return WriteEditor()


export = ToVariableOp
