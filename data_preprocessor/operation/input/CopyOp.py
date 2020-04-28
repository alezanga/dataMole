from typing import Any, Optional

from PySide2.QtWidgets import QComboBox

from data_preprocessor import data
from data_preprocessor.data.Workbench import Workbench
from data_preprocessor.gui.generic.AbsOperationEditor import AbsOperationEditor
from data_preprocessor.operation import InputOperation


class CopyOp(InputOperation):
    def __init__(self, workbench: Workbench):
        super().__init__(workbench)
        self._frame_name: Optional[str] = None

    def execute(self) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench[self._frame_name]

    def name(self) -> str:
        return 'Copy operation'

    def info(self) -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def setOptions(self, selected_frame: str) -> None:
        self._frame_name = selected_frame

    def getOptions(self) -> Any:
        return self._frame_name, self._workbench

    def inferInputShape(self) -> None:
        self._shape = [self._workbench[self._frame_name].shape]

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        class SelectFrame(AbsOperationEditor):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.__selection_box = QComboBox(self)

            def getOptions(self) -> str:
                return self.__selection_box.currentText()

            def setOptions(self, selected_name: Optional[str], workbench: Workbench) -> None:
                model = None  # TODO: create workbenchmodel
                self.__selection_box.setModel(model)
                if selected_name:
                    self.__selection_box.setCurrentText(selected_name)
                else:
                    self.__selection_box.setCurrentIndex(0)

        return SelectFrame()
