from typing import Optional, List, Tuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QWidget

import data_preprocessor.gui.workbench as wb
from data_preprocessor import data
from data_preprocessor.gui.editor.AbsOperationEditor import AbsOperationEditor
from .interface import InputOperation


class CopyOp(InputOperation):
    def __init__(self, workbench: wb.WorkbenchModel):
        super().__init__(workbench)
        self._frame_name: Optional[str] = None

    def execute(self) -> data.Frame:
        """ Get selected dataframe from workbench """
        return self._workbench.getDataframeByName(self._frame_name)

    @staticmethod
    def name() -> str:
        return 'Copy operation'

    def info(self) -> str:
        return 'Copy existing dataframe. Should be used as first operation in a pipeline'

    def setOptions(self, selected_frame: str) -> None:
        self._frame_name = selected_frame

    def getOptions(self) -> Tuple[Optional[str], wb.WorkbenchModel]:
        return self._frame_name, self._workbench

    def checkOptions(self) -> Optional[str]:
        if self._frame_name is None:
            return None
        return 'Selection is not valid'

    def inferInputShape(self) -> None:
        if self._frame_name is None:
            self._shape = [None]
        else:
            self._shape = [self._workbench.getDataframeByName(self._frame_name).shape]

    def needsOptions(self) -> bool:
        return True

    def getEditor(self) -> AbsOperationEditor:
        class SelectFrame(AbsOperationEditor):
            def getOptions(self) -> List[str]:
                name = self.__selection_box.currentText() if self.__selection_box.currentText() else None
                return [name]

            def setOptions(self, selected_name: Optional[str], workbench: wb.WorkbenchModel) -> None:
                self.__selection_box.setModel(workbench)
                if selected_name is not None:
                    self.__selection_box.setCurrentIndex(
                        self.__selection_box.findText(selected_name, Qt.MatchExactly))
                else:
                    self.__selection_box.setCurrentIndex(0)

            def editorBody(self) -> QWidget:
                self.__selection_box = QComboBox(self)
                return self.__selection_box

        return SelectFrame()


export = CopyOp
